#
# Copyright 2018, Cray Inc.  All Rights Reserved.
#
# Description:
#   Manages Cray User Access Node instances.
#

import logging
import sys
import time
import uuid
from flask import abort, request
from kubernetes import config, client
from kubernetes.client import Configuration
from kubernetes.client.apis import core_v1_api
from kubernetes.client.rest import ApiException
from swagger_server.models import UAI
from swagger_server.uas_lib.uas_cfg import UasCfg
from swagger_server.uas_lib.uas_auth import UasAuth


UAS_MGR_LOGGER = logging.getLogger('uas_mgr')
UAS_MGR_LOGGER.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s"
                              " - %(message)s")
handler.setFormatter(formatter)
UAS_MGR_LOGGER.addHandler(handler)

# picking 40 seconds so that it's under the gateway timeout
UAI_IP_TIMEOUT = 40


class UaiManager(object):

    def __init__(self):
        config.load_incluster_config()
        self.c = Configuration()
        self.c.assert_hostname = False
        Configuration.set_default(self.c)
        self.api = core_v1_api.CoreV1Api()
        self.extensions_v1beta1 = client.ExtensionsV1beta1Api()
        self.uas_cfg = UasCfg()
        self.uas_auth = UasAuth()
        self.userinfo = None
        self.passwd = None
        self.username = None
        self.check_authorization()

    def check_authorization(self):

        if 'Authorization' in request.headers:
            self.userinfo = self.uas_auth.userinfo(request.headers['Authorization'])
            if self.uas_auth.validUserinfo(self.userinfo):
                self.passwd = self.uas_auth.createPasswd(self.userinfo)
                self.username = self.userinfo[self.uas_auth.username]
                UAS_MGR_LOGGER.info("UAS request for: %s" % self.username)
            else:
                missing = self.uas_auth.missingAttributes(self.userinfo)
                UAS_MGR_LOGGER.info("Token not valid for UAS. Attributes "
                                    "missing: %s" % missing)
                abort(400, "Token not valid for UAS. Attributes missing: "
                           "%s" % missing)

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
            msg = ("Unsupported service type '{}' configured, "
                   "contact sysadmin. Valid service types are "
                   "NodePort, ClusterIP, and LoadBalancer.".format(svc_type['svc_type'])
                   )
            abort(400, msg)
        # Check if LoadBalancer and whether an IP pool is set
        if svc_type['svc_type'] == "LoadBalancer" and svc_type['ip_pool']:
            # A specific IP pool is given, create new metadata with annotations
            metadata = client.V1ObjectMeta(
                name=service_name,
                labels=self.gen_labels(deployment_name),
                annotations={"metallb.universe.tf/address-pool": svc_type['ip_pool']}
            )
        spec = client.V1ServiceSpec(selector={'app': deployment_name},
                                    type=svc_type['svc_type'],
                                    ports=ports
                                    )
        service = client.V1Service(api_version="v1",
                                   kind="Service",
                                   metadata=metadata,
                                   spec=spec
                                   )
        return service

    def create_service(self, service_name, service_body, namespace):
        # Create the service
        resp = None
        try:
            UAS_MGR_LOGGER.info("getting service %s in namespace %s" %
                                (service_name, namespace))
            resp = self.api.read_namespaced_service(name=service_name,
                                                    namespace=namespace)
        except ApiException as e:
            if e.status != 404:
                UAS_MGR_LOGGER.error("Failed to get service info while "
                                     "creating UAI: %s" % e.reason)
                abort(e.status, "Failed to get service info while creating "
                      "UAI: %s" % e.reason)
        if not resp:
            try:
                UAS_MGR_LOGGER.info("creating service %s in namespace %s" %
                                    (service_name, namespace))
                resp = self.api.create_namespaced_service(body=service_body,
                                                          namespace=namespace)
            except ApiException as e:
                UAS_MGR_LOGGER.error("Failed to create service %s: %s" %
                                     (service_name, e.reason))
                resp = None
        return resp

    def delete_service(self, service_name, namespace):
        # Delete the service
        resp = None
        try:
            UAS_MGR_LOGGER.info("deleting service %s in namespace %s" %
                                (service_name, namespace))
            resp = self.api.delete_namespaced_service(
                    name=service_name,
                    namespace=namespace,
                    body=client.V1DeleteOptions(
                        propagation_policy='Background',
                        grace_period_seconds=5))
        except ApiException as e:
            if e.status != 404:
                UAS_MGR_LOGGER.error("Failed to delete service %s: %s" %
                                     (service_name, e.reason))
                abort(e.status, "Failed to delete service %s: %s" %
                      (service_name, e.reason))
            # if we get 404 we don't want to abort because it's possible that
            # other parts are still laying around (deployment for example)
        return resp

    def create_deployment_object(self, deployment_name, imagename,
                                 publickeyStr, opt_ports_list, namespace):

        container_ports = self.uas_cfg.gen_port_list(service=False,
                                                     optional_ports=opt_ports_list)
        UAS_MGR_LOGGER.info("UAI Name: %s; Container ports: %s; Optional ports: %s"
                            % (deployment_name, container_ports, opt_ports_list))

        # Configure Pod template container
        container = client.V1Container(
            name=deployment_name,
            image=imagename,
            env=[client.V1EnvVar(
                    name='UAS_NAME',
                    value=deployment_name + "-ssh"),
                 client.V1EnvVar(
                     name='UAS_PASSWD',
                     value=self.passwd),
                 client.V1EnvVar(
                     name='UAS_PUBKEY',
                     value=publickeyStr)],
            ports=container_ports,
            volume_mounts=self.uas_cfg.gen_volume_mounts(),
            readiness_probe=self.uas_cfg.create_readiness_probe())
        # Create a volumes template
        volumes = self.uas_cfg.gen_volumes()

        # Create and configure affinity
        node_selector_terms = [
            client.V1NodeSelectorTerm(match_expressions=[
                client.V1NodeSelectorRequirement(key='uas',
                                                 operator='In',
                                                 values=['True', 'true', 'TRUE'])
                                                 ])]
        node_selector = client.V1NodeSelector(node_selector_terms)
        node_affinity = client.V1NodeAffinity(required_during_scheduling_ignored_during_execution=node_selector)
        affinity = client.V1Affinity(node_affinity=node_affinity)

        # Create and configure a spec section
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels=self.gen_labels(deployment_name),
                                         annotations={'k8s.v1.cni.cncf.io/networks': 'macvlan-uas-nmn-conf@nmn1'}),
            spec=client.V1PodSpec(containers=[container],
                                  affinity=affinity,
                                  volumes=volumes))
        # Create the specification of deployment
        spec = client.ExtensionsV1beta1DeploymentSpec(
            replicas=1,
            template=template)
        # Instantiate the deployment object
        deployment = client.ExtensionsV1beta1Deployment(
            api_version="extensions/v1beta1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=deployment_name,
                                         labels=self.gen_labels(deployment_name)),
            spec=spec)
        return deployment

    def create_deployment(self, deployment, namespace):
        # Create deployment
        resp = None
        try:
            UAS_MGR_LOGGER.info("creating deployment %s in namespace %s" %
                                 (deployment.metadata.name, namespace))
            resp = self.extensions_v1beta1.create_namespaced_deployment(
                body=deployment,
                namespace=namespace)
        except ApiException as e:
            UAS_MGR_LOGGER.error("Failed to create deployment %s: %s"
                                 % (deployment.metadata.name, e.reason))
            abort(e.status, "Failed to create deployment %s: %s"
                  % (deployment.metadata.name, e.reason))
        return resp

    def delete_deployment(self, deployment_name, namespace):
        # Delete deployment
        resp = None
        try:
            UAS_MGR_LOGGER.info("delete deployment %s in namespace %s" %
                                 (deployment_name, namespace))
            resp = self.extensions_v1beta1.delete_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=client.V1DeleteOptions(
                    propagation_policy='Background',
                    grace_period_seconds=5))
        except ApiException as e:
            if e.status != 404:
                UAS_MGR_LOGGER.error("Failed to delete deployment %s: %s" %
                                     (deployment_name, e.reason))
                abort(e.status, "Failed to delete deployment %s: %s" %
                      (deployment_name, e.reason))
            # if we get 404 we don't want to abort because it's possible that
            # other parts are still laying around (services for example)
        return resp

    def get_pod_info(self, deployment_name, namespace='default', host=None):  # noqa E501
        pod_resp = None

        try:
            UAS_MGR_LOGGER.info("getting pod info %s in namespace %s"
                                " on host %s" % (deployment_name, namespace,
                                                 host))
            if host:
                pod_resp = self.api.list_namespaced_pod(namespace=namespace,
                                                        include_uninitialized=True,
                                                        label_selector="app=%s" % deployment_name,
                                                        field_selector="spec.nodeName=%s" % host)
            else:
                pod_resp = self.api.list_namespaced_pod(namespace=namespace,
                                                        include_uninitialized=True,
                                                        label_selector="app=%s" % deployment_name)
        except ApiException as e:
            UAS_MGR_LOGGER.error("Failed to get pod info %s: %s" %
                                 (deployment_name, e.reason))
            abort(e.status, "Failed to get pod info %s: %s" %
                  (deployment_name, e.reason))

        # previously this code could return an empty UAI object,
        # but with the host filter, we could legitimately get 0
        # results and returning an empty object puts an empty object
        # into the return list.
        if len(pod_resp.items) == 0:
            return None
        elif len(pod_resp.items) > 1:
            UAS_MGR_LOGGER.warning("Oddly found more than one pod in "
                                   "deployment %s" % deployment_name)

        pod = pod_resp.items[0]

        uai = UAI()
        uai.uai_portmap = {}
        uai.uai_name = deployment_name
        uai.uai_host = pod.spec.node_name
        age_str = self.uas_cfg.get_pod_age(pod.status.start_time)
        if age_str:
            uai.uai_age = age_str
        uai.username = deployment_name.split('-')[1]
        for ctr in pod.spec.containers:
            if ctr.name == deployment_name:
                uai.uai_img = ctr.image
        if pod.status.phase == 'Pending':
            uai.uai_status = 'Pending'
        if pod.status.container_statuses:
            for s in pod.status.container_statuses:
                if s.name == deployment_name:
                    if s.state.running:
                        for c in pod.status.conditions:
                            if c.type == 'Ready':
                                if pod.metadata.deletion_timestamp:
                                    uai.uai_status = 'Terminating'
                                elif c.status == 'True':
                                    uai.uai_status = 'Running: Ready'
                                else:
                                    uai.uai_status = 'Running: Not Ready'
                                    uai.uai_msg = c.message
                    if s.state.terminated:
                        uai.uai_status = 'Terminated'
                    if s.state.waiting:
                        uai.uai_status = 'Waiting'
                        uai.uai_msg = s.state.waiting.reason
        srv_resp = None
        try:
            UAS_MGR_LOGGER.info("getting service info for %s-ssh in "
                                "namespace %s" % (deployment_name,
                                                  namespace))
            srv_resp = self.api.read_namespaced_service(name=deployment_name + "-ssh",
                                                        namespace=namespace)
        except ApiException as e:
            if e.status != 404:
                UAS_MGR_LOGGER.error("Failed to get service info for "
                                     "%s-ssh: %s" % (deployment_name,
                                                     e.reason))
                abort(e.status, "Failed to get service info for "
                                "%s-ssh: %s" % (deployment_name,
                                                e.reason))
        if srv_resp:
            uai.uai_ip = self.uas_cfg.get_external_ip()
            for srv_port in srv_resp.spec.ports:
                if srv_port.port in self.uas_cfg.get_valid_optional_ports():
                    uai.uai_portmap[srv_port.port] = srv_port.node_port
                else:
                    uai.uai_port = srv_port.node_port
        uai.uai_connect_string = self.gen_connection_string(uai)
        return uai

    def gen_connection_string(self, uai):
        """
        This function generates the uai.uai_connect_string for creating a
        ssh connection to the uai.

        The string will look like:
          ssh uai.username@uai.uai_ip -p uai.uai_port -i ~/.ssh/id_rsa

        :param uai:
        :type uai: uai
        :return: uai:
        """
        return "ssh %s@%s -p %s -i ~/.ssh/id_rsa" % (uai.username,
                                                     uai.uai_ip,
                                                     uai.uai_port)

    def gen_labels(self, deployment_name):
        return {"app": deployment_name,
                "uas": "managed",
                "user": self.username}

    def create_uai(self, publickey, imagename, opt_ports, namespace='default'):
        opt_ports_list = []
        if not publickey:
            UAS_MGR_LOGGER.warn("create_uai - missing publickey")
            abort(400, "Missing ssh public key.")
        else:
            try:
                publickeyStr = publickey.read().decode()
                if not self.uas_cfg.validate_ssh_key(publickeyStr):
                    # do not log the key here even if it's invalid, it
                    # could be a private key accidentally passed in
                    UAS_MGR_LOGGER.info("create_uai - invalid ssh public key")
                    abort(400, "Invalid ssh public key.")
            except Exception as e:
                UAS_MGR_LOGGER.info("create_uai - invalid ssh public key")
                abort(400, "Invalid ssh public key.")

        if not imagename:
            imagename = self.uas_cfg.get_default_image()
            UAS_MGR_LOGGER.info("create_uai - no image name provided, "
                                "using default %s" % imagename)
        if not self.uas_cfg.validate_image(imagename):
            UAS_MGR_LOGGER.error("create_uai - image %s is invalid"
                                 % imagename)
            abort(400, "Invalid image (%s). Valid images: %s. Default: %s"
                  % (imagename, self.uas_cfg.get_images(),
                     self.uas_cfg.get_default_image()))
        if opt_ports:
            opt_ports_list = [int(i) for i in opt_ports.split(',')]

        # Restrict ports to valid_ports
        if opt_ports_list:
            for port in opt_ports_list:
                if port not in self.uas_cfg.get_valid_optional_ports():
                    UAS_MGR_LOGGER.error("create_uai - invalid port requested (%s). "
                                         "Valid ports are %s."
                                         % (port, self.uas_cfg.get_valid_optional_ports()))
                    abort(400, "Invalid port requested (%s). Valid ports are: %s."
                                % (port, self.uas_cfg.get_valid_optional_ports()))

        deployment_id = uuid.uuid4().hex[:8]
        deployment_name = 'uai-' + self.username + '-' + str(deployment_id)
        deployment = self.create_deployment_object(deployment_name,
                                                   imagename, publickeyStr, opt_ports_list,
                                                   namespace)
        # Create a service for the UAI
        uas_ssh_svc_name = deployment_name + '-ssh'
        uas_ssh_svc = self.create_service_object(uas_ssh_svc_name, "ssh",  opt_ports_list, deployment_name)

        # Make sure the UAI deployment is created
        deploy_resp = None
        try:
            UAS_MGR_LOGGER.info("getting deployment %s in namespace %s" %
                                (deployment_name, namespace))
            deploy_resp = self.extensions_v1beta1.read_namespaced_deployment(deployment_name, namespace)
        except ApiException as e:
            if e.status != 404:
                UAS_MGR_LOGGER.error("Failed to create deployment %s: %s" %
                                     (deployment_name, e.reason))
                abort(e.status, "Failed to create deployment %s: %s" %
                      (deployment_name, e.reason))
        if not deploy_resp:
            deploy_resp = self.create_deployment(deployment, namespace)

        # Start the UAI services
        UAS_MGR_LOGGER.info("creating the UAI service %s" %
                            uas_ssh_svc_name)
        svc_resp = self.create_service(uas_ssh_svc_name, uas_ssh_svc, namespace)
        if not svc_resp:
            # Clean up the deployment
            UAS_MGR_LOGGER.error("failed to create service, deleting UAI %s" %
                                 (deployment_name))
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
                abort(504, "Failed to get IP for service: %s" %
                      uas_ssh_svc_name)
            time.sleep(delay)
            total_wait += delay
            UAS_MGR_LOGGER.info("waiting for uai_ip %s seconds" %
                                str(total_wait))
        return uai_info

    def list_uais(self, label, host=None, namespace='default'):
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
        if not label:
            label = 'user=' + self.username
        try:
            UAS_MGR_LOGGER.info("listing deployments matching: namespace %s,"
                                " label %s" % (namespace, label))
            resp = self.extensions_v1beta1.list_namespaced_deployment(namespace=namespace,
                                                label_selector=label,
                                                include_uninitialized=True)

        except ApiException as e:
            if e.status != 404:
                UAS_MGR_LOGGER.error("Failed to get deployment list: %s",
                                     e.reason)
                abort(e.status, "Failed to get deployment list")
        for deployment in resp.items:
            uai = self.get_pod_info(deployment.metadata.name, namespace, host)
            if uai:
                uai_list.append(uai)
        return uai_list

    def delete_uais(self, deployment_list, namespace='default'):
        """
        Deletes the UAIs named in deployment_list.
        If deployment_list is empty, it will delete all UAIs.

        :param deployment_list: List of UAI names to delete. If empty, delete all UAIs.
        :type deployment_list: list
        :return: List of UAIs deleted.
        :rtype: list
        """
        resp_list = []
        uai_list = []
        if not deployment_list:
            for uai in self.list_uais('uas=managed'):
                uai_list.append(uai.uai_name)
        else:
            uai_list = [uai for uai in deployment_list if
                        'uai-'+self.username+'-' in uai]
        for d in [d.strip() for d in uai_list]:
            # Do services first so that we don't orphan one if they abort
            service_resp = self.delete_service(d + "-ssh", namespace)
            deploy_resp = self.delete_deployment(d, namespace)

            if deploy_resp is None and service_resp is None:
                message = "Failed to delete %s - Not found" % d
            else:
                message = "Successfully deleted %s" % d
            resp_list.append(message)
        return resp_list

    def delete_image(self, imagename):
        # Delete the image
        resp = None
        abort(501, "Not implemented")
        return resp

    def create_image(self, imagename, default):
        # Create the image
        resp = None
        abort(501, "Not implemented")
        return resp

    def update_image(self, imagename, default):
        # Update the image
        resp = None
        abort(501, "Not implemented")
        return resp

    def get_image(self, imagename):
        # Get image info
        resp = None
        abort(501, "Not implemented")
        return resp

    def delete_volume(self, volumename):
        # Delete the volume
        resp = None
        abort(501, "Not implemented")
        return resp

    def create_volume(self, volumename, type, mount_path=None, host_path=None,
                      secret_name=None, config_map=None):
        # Create the volume

        if not self.uas_cfg.is_valid_host_path_mount_type(type):
            abort(400, "Invalid type - please refer to the Kubernetes volume"
                  " documentation for valid types")

        if not self.uas_cfg.is_valid_volume_name(volumename):
            abort(400, "Invalid volume name - names must consist of lower case"
                       " alphanumeric characters or '-', and must start and"
                       " end with an alphanumeric character. Refer to the "
                       "Kubernetes documentation for more information.")

        resp = None
        abort(501, "Not implemented")
        return resp

    def update_volume(self, volumename, type, mount_path=None, host_path=None,
                      secret_name=None, config_map=None):
        # Update the volume

        if not self.uas_cfg.is_valid_host_path_mount_type(type):
            abort(400, "Invalid type - please refer to the Kubernetes volume"
                       " documentation for valid types")

        if not self.uas_cfg.is_valid_volume_name(volumename):
            abort(400, "Invalid volume name - names must consist of lower case"
                       " alphanumeric characters or '-', and must start and"
                       " end with an alphanumeric character. Refer to the "
                       "Kubernetes documentation for more information.")

        resp = None
        abort(501, "Not implemented")
        return resp

    def get_volume(self, volumename):
        # Get info on a specific volume
        resp = None
        abort(501, "Not implemented")
        return resp

    def get_volumes(self):
        # Get all volumes
        resp = None
        abort(501, "Not implemented")
        return resp
