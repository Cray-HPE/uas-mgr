#
# Copyright 2018, Cray Inc.  All Rights Reserved.
#
"""
Manages Cray User Access Node instances.
"""
#pylint: disable=too-many-lines

import os
import time
import uuid
import json
from datetime import datetime, timezone
from flask import abort, request
from kubernetes import client
from kubernetes.client.rest import ApiException
from swagger_server.models import UAI
from swagger_server.uas_lib.uas_base import UasBase
from swagger_server.uas_lib.uas_auth import UasAuth
from swagger_server.uas_data_model.uai_image import UAIImage
from swagger_server.uas_data_model.uai_volume import UAIVolume
from swagger_server.uas_data_model.populated_config import PopulatedConfig

# picking 40 seconds so that it's under the gateway timeout
UAI_IP_TIMEOUT = 40


# pylint: disable=too-many-public-methods
class UaiManager(UasBase):
    """UAI Manager - manages UAI resources and allocates and controls UAIs

    """
    def __init__(self):
        """ Constructor """
        UasBase.__init__(self)
        self.uas_auth = UasAuth()
        self.userinfo = None
        self.passwd = None
        self.username = None
        self.check_authorization()

    def check_authorization(self):
        """Check authorization based on request headers for the requested
        action and extract user credentials to for use in UAIs.

        """
        if 'Authorization' in request.headers:
            self.userinfo = self.uas_auth.userinfo(
                request.headers['Host'],
                request.headers['Authorization']
            )
            if self.uas_auth.validUserinfo(self.userinfo):
                self.passwd = self.uas_auth.createPasswd(self.userinfo)
                self.username = self.userinfo[self.uas_auth.username]
                self.logger.info("UAS request for: %s", self.username)
            else:
                missing = self.uas_auth.missingAttributes(self.userinfo)
                self.logger.info(
                    "Token not valid for UAS. Attributes "
                    "missing: %s",
                    missing
                )
                abort(
                    400,
                    "Token not valid for UAS. Attributes "
                    "missing: %s" %  missing
                )

    def get_pod_age(self, start_time):
        """
        given a start time as an RFC3339 datetime object, return the difference
        in time between that time and the current time, in a k8s format
        of dDhHmM - ie: 3d7h5m or 6h9m or 19m

        :return a string representing the delta between pod start and now.
        :rtype string
        """
        # on new UAI start the start_time can be None
        if start_time is None:
            return None

        try:
            now = datetime.now(timezone.utc)
            delta = now - start_time
        except Exception as err:  # pylint: disable=broad-except
            self.logger.warning("Unable to convert pod start time - %s", err)
            return None

        # build the output string
        retstr = ""
        days, remainder = divmod(delta.total_seconds(), 60*60*24)
        if days != 0:
            retstr += "{:d}d".format(int(days))

        hours, remainder = divmod(remainder, 60*60)
        if hours != 0:
            retstr += "{:d}h".format(int(hours))

        # always show minutes, even if 0, but only if < 1 day old
        if days == 0:
            minutes = remainder / 60
            retstr += "{:d}m".format(int(minutes))

        return retstr

    def create_service_object(self, service_name, service_type, opt_ports_list,
                              deployment_name):
        """
        Create a service object for the deployment of the UAI.

        :param service_name: Name of the service
        :type service_name: str
        :param service_type: One of "ssh" or "service"
        :type service_type: str
        :param opt_ports_list: List of optional ports to project
        :type opt_ports_list: list
        :return: service object
        """
        metadata = client.V1ObjectMeta(
            name=service_name,
            labels=self.gen_labels(deployment_name),
        )
        ports = self.uas_cfg.gen_port_list(service_type, service=True,
                                           optional_ports=opt_ports_list)

        # svc_type is a dict with the following fields:
        #   'svc_type': (NodePort, ClusterIP, or LoadBalancer)
        #   'ip_pool': (None, or a specific pool)  Valid only for LoadBalancer.
        #   'valid': (True or False) is svc_type is valid or not
        svc_type = self.uas_cfg.get_svc_type(service_type)
        if not svc_type['valid']:
            # Invalid svc_type given.
            msg = (
                "Unsupported service type '{}' configured, "
                "contact sysadmin. Valid service types are "
                "NodePort, ClusterIP, and LoadBalancer.".format(
                    svc_type['svc_type']
                )
            )
            abort(400, msg)
        # Check if LoadBalancer and whether an IP pool is set
        if svc_type['svc_type'] == "LoadBalancer" and svc_type['ip_pool']:
            # A specific IP pool is given, create new metadata with annotations
            metadata = client.V1ObjectMeta(
                name=service_name,
                labels=self.gen_labels(deployment_name),
                annotations={
                    "metallb.universe.tf/address-pool": svc_type['ip_pool']
                }
            )
        spec = client.V1ServiceSpec(
            selector={'app': deployment_name},
            type=svc_type['svc_type'],
            ports=ports
        )
        service = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=metadata,
            spec=spec
        )
        return service

    def create_service(self, service_name, service_body, namespace):
        """Create the service

        """
        resp = None
        try:
            self.logger.info(
                "getting service %s in namespace %s",
                service_name,
                namespace
            )
            resp = self.api.read_namespaced_service(
                name=service_name,
                namespace=namespace
            )
        except ApiException as err:
            if err.status != 404:
                self.logger.error(
                    "Failed to get service info while "
                    "creating UAI: %s",
                    err.reason
                )
                abort(
                    err.status,
                    "Failed to get service info while creating "
                    "UAI: %s" % err.reason
                )
        if not resp:
            try:
                self.logger.info(
                    "creating service %s in namespace %s",
                    service_name,
                    namespace
                )
                resp = self.api.create_namespaced_service(
                    body=service_body,
                    namespace=namespace
                )
            except ApiException as err:
                self.logger.error(
                    "Failed to create service %s: %s",
                    service_name,
                    err.reason
                )
                resp = None
        return resp

    def delete_service(self, service_name, namespace):
        """Delete the service

        """
        resp = None
        try:
            self.logger.info(
                "deleting service %s in namespace %s",
                service_name,
                namespace
            )
            resp = self.api.delete_namespaced_service(
                name=service_name,
                namespace=namespace,
                body=client.V1DeleteOptions(
                    propagation_policy='Background',
                    grace_period_seconds=5
                )
            )
        except ApiException as err:
            # if we get 404 we don't want to abort because it's possible that
            # other parts are still laying around (deployment for example)
            if err.status != 404:
                self.logger.error(
                    "Failed to delete service %s: %s",
                    service_name,
                    err.reason
                )
                abort(
                    err.status, "Failed to delete service %s: %s" % (
                        service_name,
                        err.reason
                    )
                )
        return resp

    # pylint: disable=too-many-arguments,too-many-locals
    def create_deployment_object(self, deployment_name, imagename,
                                 public_key_str, opt_ports_list):
        """Construct a deployment for a UAI

        """
        container_ports = self.uas_cfg.gen_port_list(
            service=False,
            optional_ports=opt_ports_list
        )
        self.logger.info(
            "UAI Name: %s; Container ports: %s; Optional ports: %s",
            deployment_name,
            container_ports,
            opt_ports_list
        )

        # Configure Pod template container
        container = client.V1Container(
            name=deployment_name,
            image=imagename,
            env=[
                client.V1EnvVar(
                    name='UAS_NAME',
                    value=deployment_name + "-ssh"
                ),
                client.V1EnvVar(
                    name='UAS_PASSWD',
                    value=self.passwd
                ),
                client.V1EnvVar(
                    name='UAS_PUBKEY',
                    value=public_key_str
                )
            ],
            ports=container_ports,
            volume_mounts=self.uas_cfg.gen_volume_mounts(),
            readiness_probe=self.uas_cfg.create_readiness_probe()
        )
        # Create a volumes template
        volumes = self.uas_cfg.gen_volumes()

        # Create and configure affinity
        node_selector_terms = [
            client.V1NodeSelectorTerm(
                match_expressions=[
                    client.V1NodeSelectorRequirement(
                        key='node-role.kubernetes.io/master',
                        operator='DoesNotExist'
                    ),
                    client.V1NodeSelectorRequirement(
                        key='uas',
                        operator='NotIn',
                        values=['False', 'false', 'FALSE']
                    )
                ]
            )
        ]
        node_selector = client.V1NodeSelector(node_selector_terms)
        node_affinity = client.V1NodeAffinity(
            required_during_scheduling_ignored_during_execution=node_selector
        )
        affinity = client.V1Affinity(node_affinity=node_affinity)

        # Create and configure a spec section.  If we are using
        # macvlans then we will set that up in an annotation in the
        # metadata, otherwise, the annotations will be None.
        # USE_MACVLAN is based on configuration from the Helm chart
        # that can be set at service deployment time.
        meta_annotations = None
        if os.environ.get('USE_MACVLAN', 'true').lower() == 'true':
            meta_annotations = {
                'k8s.v1.cni.cncf.io/networks': 'macvlan-uas-nmn-conf@nmn1'
            }
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                labels=self.gen_labels(deployment_name),
                annotations=meta_annotations
            ),
            spec=client.V1PodSpec(
                priority_class_name='uai-priority',
                containers=[container],
                affinity=affinity,
                volumes=volumes
            )
        )
        # Create the specification of deployment
        spec = client.V1DeploymentSpec(
            replicas=1,
            selector={'matchLabels': {'app': deployment_name}},
            template=template)
        # Instantiate the deployment object
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(
                name=deployment_name,
                labels=self.gen_labels(deployment_name)
            ),
            spec=spec)
        return deployment

    def create_deployment(self, deployment, namespace):
        """Create a UAI deployment

        """
        resp = None
        try:
            self.logger.info(
                "creating deployment %s in namespace %s",
                deployment.metadata.name,
                namespace
            )
            resp = self.apps_v1.create_namespaced_deployment(
                body=deployment,
                namespace=namespace
            )
        except ApiException as err:
            self.logger.error(
                "Failed to create deployment %s: %s",
                deployment.metadata.name,
                err.reason
            )
            abort(
                err.status,
                "Failed to create deployment %s: %s" % (
                    deployment.metadata.name, err.reason
                )
            )
        return resp

    def delete_deployment(self, deployment_name, namespace):
        """Delete a UAI deployment

        """
        resp = None
        try:
            self.logger.info(
                "delete deployment %s in namespace %s",
                deployment_name,
                namespace
            )
            resp = self.apps_v1.delete_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=client.V1DeleteOptions(
                    propagation_policy='Background',
                    grace_period_seconds=5))
        except ApiException as err:
            if err.status != 404:
                self.logger.error(
                    "Failed to delete deployment %s: %s",
                    deployment_name,
                    err.reason
                )
                abort(
                    err.status,
                    "Failed to delete deployment %s: %s" % (
                        deployment_name,
                        err.reason
                    )
                )
            # if we get 404 we don't want to abort because it's possible that
            # other parts are still laying around (services for example)
        return resp

    # pylint: disable=too-many-branches,too-many-statements
    def get_pod_info(
            self,
            deployment_name,
            namespace=None,
            host=None
    ):
        """Retrieve pod information for a UAI pod from configuration.

        """
        pod_resp = None

        if not namespace:
            namespace = self.uas_cfg.get_uai_namespace()
            self.logger.info(
                "get_pod_info - UAIs will be gathered from"
                " the %s namespace.",
                namespace
            )
        try:
            self.logger.info(
                "getting pod info %s in namespace %s"
                " on host %s",
                deployment_name,
                namespace,
                host
            )
            if host:
                pod_resp = self.api.list_namespaced_pod(
                    namespace=namespace,
                    label_selector="app=%s" % deployment_name,
                    field_selector="spec.nodeName=%s" % host)
            else:
                pod_resp = self.api.list_namespaced_pod(
                    namespace=namespace,
                    label_selector="app=%s" % deployment_name
                )
        except ApiException as err:
            self.logger.error(
                "Failed to get pod info %s: %s",
                deployment_name,
                err.reason
            )
            abort(
                err.status,
                "Failed to get pod info %s: %s" % (
                    deployment_name,
                    err.reason
                )
            )

        # previously this code could return an empty UAI object,
        # but with the host filter, we could legitimately get 0
        # results and returning an empty object puts an empty object
        # into the return list.
        if not pod_resp.items:
            return None
        if len(pod_resp.items) > 1:
            self.logger.warning(
                "Oddly found more than one pod in "
                "deployment %s",
                deployment_name
            )
        pod = pod_resp.items[0]

        uai = UAI()
        uai.uai_portmap = {}
        uai.uai_name = deployment_name
        uai.uai_host = pod.spec.node_name
        age_str = self.get_pod_age(pod.status.start_time)
        if age_str:
            uai.uai_age = age_str
        uai.username = deployment_name.split('-')[1]
        for ctr in pod.spec.containers:
            if ctr.name == deployment_name:
                uai.uai_img = ctr.image
        if pod.status.phase == 'Pending':
            uai.uai_status = 'Pending'
        # pylint: disable=too-many-nested-blocks
        if pod.status.container_statuses:
            for status in pod.status.container_statuses:
                if status.name == deployment_name:
                    if status.state.running:
                        for cond in pod.status.conditions:
                            if cond.type == 'Ready':
                                if pod.metadata.deletion_timestamp:
                                    uai.uai_status = 'Terminating'
                                elif cond.status == 'True':
                                    uai.uai_status = 'Running: Ready'
                                else:
                                    uai.uai_status = 'Running: Not Ready'
                                    uai.uai_msg = cond.message
                    if status.state.terminated:
                        uai.uai_status = 'Terminated'
                    if status.state.waiting:
                        uai.uai_status = 'Waiting'
                        uai.uai_msg = status.state.waiting.reason
        srv_resp = None
        try:
            self.logger.info(
                "getting service info for %s-ssh in "
                "namespace %s",
                deployment_name,
                namespace
            )
            srv_resp = self.api.read_namespaced_service(
                name=deployment_name + "-ssh",
                namespace=namespace
            )
        except ApiException as err:
            if err.status != 404:
                self.logger.error(
                    "Failed to get service info for "
                    "%s-ssh: %s",
                    deployment_name,
                    err.reason
                )
                abort(
                    err.status,
                    "Failed to get service info for %s-ssh: %s" % (
                        deployment_name,
                        err.reason
                    )
                )
            return uai

        if srv_resp:
            svc_type = self.uas_cfg.get_svc_type('ssh')
            if svc_type['svc_type'] == "LoadBalancer":
                uai.uai_ip = srv_resp.status.load_balancer.ingress[0].ip
                uai.uai_port = 22
            else:
                uai.uai_ip = self.uas_cfg.get_external_ip()
                for srv_port in srv_resp.spec.ports:
                    if srv_port.port in self.uas_cfg.get_valid_optional_ports():
                        uai.uai_portmap[srv_port.port] = srv_port.node_port
                    else:
                        uai.uai_port = srv_port.node_port

        uai.uai_connect_string = self.gen_connection_string(uai)
        return uai

    @staticmethod
    def gen_connection_string(uai):
        """
        This function generates the uai.uai_connect_string for creating a
        ssh connection to the uai.

        The string will look like:
          ssh uai.username@uai.uai_ip -p uai.uai_port -i ~/.ssh/id_rsa

        :param uai:
        :type uai: uai
        :return: uai:
        """
        port_string = " -p " + str(uai.uai_port) if uai.uai_port != 22 else ""

        return "ssh %s@%s%s -i ~/.ssh/id_rsa" % (
            uai.username,
            uai.uai_ip,
            port_string
        )

    def gen_labels(self, deployment_name):
        """Generate labels for a UAI Deployment

        """
        return {
            "app": deployment_name,
            "uas": "managed",
            "user": self.username
        }

    # pylint: disable=too-many-branches,too-many-statements
    def create_uai(self, public_key, imagename, opt_ports, namespace=None):
        """Create a new UAI

        """
        opt_ports_list = []
        if not public_key:
            self.logger.warning("create_uai - missing public key")
            abort(400, "Missing ssh public key.")
        else:
            try:
                public_key_str = public_key.read().decode()
                if not self.uas_cfg.validate_ssh_key(public_key_str):
                    # do not log the key here even if it's invalid, it
                    # could be a private key accidentally passed in
                    self.logger.info("create_uai - invalid ssh public key")
                    abort(400, "Invalid ssh public key.")
            except Exception:  # pylint: disable=broad-except
                self.logger.info("create_uai - invalid ssh public key")
                abort(400, "Invalid ssh public key.")

        if not namespace:
            namespace = self.uas_cfg.get_uai_namespace()
            self.logger.info(
                "create_uai - UAI will be created in"
                " the %s namespace.",
                namespace
            )

        if not imagename:
            imagename = self.uas_cfg.get_default_image()
            self.logger.info(
                "create_uai - no image name provided, "
                "using default %s",
                imagename
            )

        if not self.uas_cfg.validate_image(imagename):
            self.logger.error(
                "create_uai - image %s is invalid",
                imagename
            )
            abort(
                400,
                "Invalid image (%s). Valid images: %s. Default: %s" % (
                    imagename,
                    self.uas_cfg.get_images(),
                    self.uas_cfg.get_default_image()
                )
            )
        if opt_ports:
            opt_ports_list = [int(i) for i in opt_ports.split(',')]

        # Restrict ports to valid_ports
        if opt_ports_list:
            for port in opt_ports_list:
                if port not in self.uas_cfg.get_valid_optional_ports():
                    self.logger.error(
                        "create_uai - invalid port requested (%s). "
                        "Valid ports are %s.",
                        port,
                        self.uas_cfg.get_valid_optional_ports()
                    )
                    abort(
                        400,
                        "Invalid port requested (%s). Valid ports are: %s." % (
                            port,
                            self.uas_cfg.get_valid_optional_ports()
                        )
                    )

        deployment_id = uuid.uuid4().hex[:8]
        deployment_name = 'uai-' + self.username + '-' + str(deployment_id)
        deployment = self.create_deployment_object(
            deployment_name,
            imagename,
            public_key_str,
            opt_ports_list
        )
        # Create a service for the UAI
        uas_ssh_svc_name = deployment_name + '-ssh'
        uas_ssh_svc = self.create_service_object(
            uas_ssh_svc_name,
            "ssh",
            opt_ports_list,
            deployment_name
        )

        # Make sure the UAI deployment is created
        deploy_resp = None
        try:
            self.logger.info(
                "getting deployment %s in namespace %s",
                deployment_name,
                namespace
            )
            deploy_resp = self.apps_v1.read_namespaced_deployment(
                deployment_name,
                namespace
            )
        except ApiException as err:
            if err.status != 404:
                self.logger.error(
                    "Failed to create deployment %s: %s",
                    deployment_name,
                    err.reason
                )
                abort(
                    err.status,
                    "Failed to create deployment %s: %s" % (
                        deployment_name,
                        err.reason
                    )
                )
        if not deploy_resp:
            deploy_resp = self.create_deployment(deployment, namespace)

        # Start the UAI services
        self.logger.info("creating the UAI service %s", uas_ssh_svc_name)
        svc_resp = self.create_service(
            uas_ssh_svc_name,
            uas_ssh_svc,
            namespace
        )
        if not svc_resp:
            # Clean up the deployment
            self.logger.error(
                "failed to create service, deleting UAI %s",
                deployment_name
            )
            self.delete_uais([deployment_name], namespace)
            abort(404, "Failed to create service: %s" % uas_ssh_svc_name)

        # Wait for the UAI IP to be set
        total_wait = 0.0
        delay = 0.5
        while True:
            uai_info = self.get_pod_info(deploy_resp.metadata.name, namespace)
            if uai_info and uai_info.uai_ip:
                break
            if total_wait >= UAI_IP_TIMEOUT:
                abort(
                    504,
                    "Failed to get IP for service: %s" % uas_ssh_svc_name
                )
            time.sleep(delay)
            total_wait += delay
            self.logger.info(
                "waiting for uai_ip %s seconds",
                str(total_wait)
            )
        return uai_info

    def list_uais(self, label, host=None, namespace=None):
        """
        Lists the UAIs based on a label and/or field selector and namespace

        :param label: Label selector. If empty, use self.username
        :param host: Used to select pods by host, if set,
            If unset, the default of an empty string will select all.
            Passed through to get_pod_info().
        :param namespace: Filters results by a specific namespace
        :return: List of UAI information.
        :rtype: list
        """
        resp = None
        uai_list = []

        if not namespace:
            namespace = self.uas_cfg.get_uai_namespace()
            self.logger.info(
                "list_uais - UAI will be listed from"
                " the %s namespace.",
                namespace
            )

        if not label:
            label = 'user=' + self.username
        try:
            self.logger.info(
                "listing deployments matching: namespace %s,"
                " label %s",
                namespace,
                label
            )
            resp = self.apps_v1.list_namespaced_deployment(
                namespace=namespace,
                label_selector=label
            )
        except ApiException as err:
            if err.status != 404:
                self.logger.error(
                    "Failed to get deployment list: %s",
                    err.reason
                )
                abort(err.status, "Failed to get deployment list")
        for deployment in resp.items:
            uai = self.get_pod_info(deployment.metadata.name, namespace, host)
            if uai:
                uai_list.append(uai)
        return uai_list

    def delete_uais(self, deployment_list, namespace=None):
        """
        Deletes the UAIs named in deployment_list.
        If deployment_list is empty, it will delete all UAIs.

        :param deployment_list: List of UAI names to delete.
                                If empty, delete all UAIs.
        :type deployment_list: list
        :return: List of UAIs deleted.
        :rtype: list
        """
        resp_list = []
        uai_list = []

        if not namespace:
            namespace = self.uas_cfg.get_uai_namespace()
            self.logger.info(
                "delete_uais - UAI will be deleted from"
                " the %s namespace.",
                namespace
            )

        if not deployment_list:
            for uai in self.list_uais('uas=managed'):
                uai_list.append(uai.uai_name)
        else:
            uai_list = [uai for uai in deployment_list if
                        'uai-'+self.username+'-' in uai]
        for uai_dep in [dep.strip() for dep in uai_list]:
            # Do services first so that we don't orphan one if they abort
            service_resp = self.delete_service(uai_dep + "-ssh", namespace)
            deploy_resp = self.delete_deployment(uai_dep, namespace)

            if deploy_resp is None and service_resp is None:
                message = "Failed to delete %s - Not found" % uai_dep
            else:
                message = "Successfully deleted %s" % uai_dep
            resp_list.append(message)
        return resp_list

    def delete_image(self, image_id):
        """Delete a UAI image from the config

        """
        self.uas_cfg.get_config()
        img = UAIImage.get(image_id)
        if img is None:
            abort(404, "image '%s' does not exist" % image_id)
        img.remove() # don't use img.delete() you actually want it removed
        return {
            'image_id': img.image_id,
            'imagename': img.imagename,
            'default': img.default
        }

    def create_image(self, imagename, default):
        """Create a new UAI image in the config

        """
        self.uas_cfg.get_config()
        if UAIImage.get_by_name(imagename):
            abort(409, "image named '%s' already exists" % imagename)
        # Create it and store it...
        if default is None:
            default = False
        if default:
            # This is the default image. Check for any other image
            # that is currently default and make it no longer default.
            imgs = UAIImage.get_all()
            for img in imgs:
                if img.default:
                    img.default = False
                    img.put()
        # Now create the new image...
        img = UAIImage(imagename=imagename, default=default)
        img.put()
        return {
            'image_id': img.image_id,
            'imagename': img.imagename,
            'default': img.default
        }


    def update_image(self, image_id, imagename, default):
        """Update a UAI image in the config

        """
        self.uas_cfg.get_config()
        img = UAIImage.get(image_id)
        if img is None:
            abort(404, "image '%s' does not exist" % image_id)
        changed = False
        # Is the image name changing?
        if imagename is None:
            imagename = img.imagename
        if imagename != img.imagename:
            # Going to change the image name, make sure it is unique...
            tmp = UAIImage.get_by_name(imagename)
            if tmp is not None:
                abort(409, "image named '%s' already exists" % imagename)
            # A value is specified to update...
            img.imagename = imagename
            changed = True
        # Is the default settting changing?
        if default is None:
            default = img.default
        if default != img.default:
            # A value is specified to update...
            img.default = default
            changed = True
        if changed:
            if default:
                # This will be the default image. If there is another
                # image that is default right now, make it no longer
                # default.
                imgs = UAIImage.get_all()
                for tmp in imgs:
                    if tmp.image_id == image_id:
                        continue
                    if tmp.default:
                        tmp.default = False
                        tmp.put()
            img.put()
        return {
            'image_id': img.image_id,
            'imagename': img.imagename,
            'default': img.default
        }

    def get_image(self, image_id):
        """Retrieve a UAI image from the config

        """
        self.uas_cfg.get_config()
        img = UAIImage.get(image_id)
        if img is None:
            abort(404, "image '%s' does not exist" % image_id)
        return {
            'image_id': img.image_id,
            'imagename': img.imagename,
            'default': img.default
        }

    def get_images(self):
        """Get the list of UAI images in the config

        """
        self.uas_cfg.get_config()
        imgs = UAIImage.get_all()
        return [
            {
                'image_id': img.image_id,
                'imagename': img.imagename,
                'default': img.default
            }
            for img in imgs
        ]

    def delete_volume(self, volume_id):
        """Delete a UAI volume from the config

        """
        self.uas_cfg.get_config()
        vol = UAIVolume.get(volume_id)
        if vol is None:
            abort(404, "volume '%s' does not exist" % volume_id)
        vol.remove() # don't use vol.delete() you actually want it removed
        return {
            'volume_id': vol.volume_id,
            'volumename': vol.volumename,
            'mount_path': vol.mount_path,
            'volume_description': vol.volume_description
        }

    def create_volume(self, volumename, mount_path, vol_desc):
        """Create a UAI volume in the config

        """
        self.uas_cfg.get_config()
        if not UAIVolume.is_valid_volume_name(volumename):
            abort(
                400,
                "Invalid volume name - names must consist of lower case"
                " alphanumeric characters or '-', and must start and"
                " end with an alphanumeric character. Refer to the "
                "Kubernetes documentation for more information."
            )
        if not mount_path:
            abort(400, "No mount path specified for volume")
        if vol_desc is None:
            abort(400, "No volume description provided for volume")
        # Convert vol_desc from a JSON string to a dictionary
        try:
            vol_desc = json.loads(vol_desc)
        except json.decoder.JSONDecodeError as err:
            abort(
                400,
                "Volume description failed JSON decoding - %s" % str(err)
            )
        err = UAIVolume.vol_desc_errors(vol_desc)
        if err is not None:
            abort(
                400,
                "Volume has a malformed volume description - %s" % err
            )
        if UAIVolume.get_by_name(volumename) is not None:
            abort(409, "volume named '%s' already exists" % volumename)
        # Create it and store it...
        vol = UAIVolume(
            volumename=volumename,
            mount_path=mount_path,
            volume_description=vol_desc
        )
        vol.put()
        return {
            'volume_id': vol.volume_id,
            'volumename': vol.volumename,
            'mount_path': vol.mount_path,
            'volume_description': vol.volume_description
        }

    def update_volume(self, volume_id,
                      volumename=None, mount_path=None, vol_desc=None):
        """Update a UAI volume in the config

        """
        self.uas_cfg.get_config()
        vol = UAIVolume.get(volume_id)
        if vol is None:
            abort(
                404,
                "Volume %s not found" % volume_id
            )
        changed = False
        if volumename is not None:
            if not volumename:
                abort(400, "invalid (empty) volume name specified")
                if not UAIVolume.is_valid_volume_name(volumename):
                    abort(
                        400,
                        "Invalid volume name - names must consist of lower "
                        "case alphanumeric characters or '-', and must start "
                        "and end with an alphanumeric character. Refer to the "
                        "Kubernetes documentation for more information."
                    )
            tmp = UAIVolume.get_by_name(volumename)
            if tmp is not None and tmp.volume_id != vol.volume_id:
                abort(409, "volume named '%s' already exists" % volumename)
            vol.volumename = volumename
            changed = True
        if mount_path is not None:
            if not mount_path:
                abort(400, "invalid (empty) mount_path specified")
            vol.mount_path = mount_path
            changed = True
        if vol_desc is not None:
            # Convert vol_desc from a JSON string to a dictionary
            try:
                vol_desc = json.loads(vol_desc)
            except json.decoder.JSONDecodeError as err:
                abort(
                    400,
                    "Volume description failed JSON decoding - %s" % str(err)
                )
            err = UAIVolume.vol_desc_errors(vol_desc)
            if err is not None:
                abort(
                    400,
                    "Volume has a malformed volume description - %s" % err
                )
            vol.volume_description = vol_desc
            changed = True
        if changed:
            vol.put()
        return {
            'volume_id': vol.volume_id,
            'volumename': vol.volumename,
            'mount_path': vol.mount_path,
            'volume_description': vol.volume_description
        }

    def get_volume(self, volume_id):
        """Get info on a specific volume from the config

        """
        self.uas_cfg.get_config()
        vol = UAIVolume.get(volume_id)
        if vol is None:
            abort(
                404,
                "Unknown volume '%s'" % volume_id
            )
        return {
            'volume_id': vol.volume_id,
            'volumename': vol.volumename,
            'mount_path': vol.mount_path,
            'volume_description': vol.volume_description
        }

    def get_volumes(self):
        """Get info on all volumes in the config

        """
        self.uas_cfg.get_config()
        vols = UAIVolume.get_all()
        return [
            {
                'volume_id': vol.volume_id,
                'volumename': vol.volumename,
                'mount_path': vol.mount_path,
                'volume_description': vol.volume_description
            }
            for vol in vols
        ]

    def factory_reset(self):
        """Delete all the local configuration so that the next operation
        reloads config from the configmap configuration.

        """
        self.uas_cfg.get_config()
        vols = UAIVolume.get_all()
        for vol in vols:
            vol.remove()
        imgs = UAIImage.get_all()
        for img in imgs:
            img.remove()
        cfgs = PopulatedConfig.get_all()
        for cfg in cfgs:
            cfg.remove()
