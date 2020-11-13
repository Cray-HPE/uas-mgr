# Copyright 2020 Hewlett Packard Enterprise Development LP#
#
"""
Base Class for User Access Service Operations

Copyright 2020 Hewlett Packard Enterprise Development LP
"""

import os
import json
import uuid
import time
from datetime import datetime, timezone
from flask import abort
import sshpubkeys
import sshpubkeys.exceptions as sshExceptions
from kubernetes import config, client
from kubernetes.client.rest import ApiException
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from swagger_server.uas_lib.uas_logging import logger
from swagger_server.models import UAI
from swagger_server.uas_lib.uas_cfg import UasCfg
from swagger_server.uas_data_model.uai_resource import UAIResource
from swagger_server.uas_data_model.uai_image import UAIImage
# For now because the testing seems to need it, pull in UAS_AUTH_LOGGER
from swagger_server.uas_lib.uas_auth import UAS_AUTH_LOGGER

# picking 40 seconds so that it's under the gateway timeout
UAI_IP_TIMEOUT = 40

class UasBase:
    """Base class used for any class implementing UAS API functionality.
    Takes care of common activities like K8s client setup, loading UAS
    configuration from the default configmap and so forth.

    """
    def __init__(self):
        """ Constructor """
        config.load_incluster_config()
        k8s_config = Configuration()
        k8s_config.assert_hostname = False
        Configuration.set_default(k8s_config)
        self.api = core_v1_api.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.uas_cfg = UasCfg()

    @staticmethod
    def get_pod_age(start_time):
        """
        given a start time as an RFC3339 datetime object, return the difference
        in time between that time and the current time, in a k8s format
        of dDhHmM - ie: 3d7h5m or 6h9m or 19m

        :return a string representing the delta between pod start and now.
        :rtype string
        """
        # on new UAI start the start_time can be None
        if start_time is None:
            logger.info("No start time provided from pod")
            return None

        try:
            now = datetime.now(timezone.utc)
            delta = now - start_time
        except Exception as err:  # pylint: disable=broad-except
            logger.warning("Unable to convert pod start time - %s", err)
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

    def create_service(self, service_name, service_body, namespace):
        """Create the service

        """
        resp = None
        try:
            logger.info(
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
                logger.error(
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
                logger.info(
                    "creating service %s in namespace %s",
                    service_name,
                    namespace
                )
                resp = self.api.create_namespaced_service(
                    body=service_body,
                    namespace=namespace
                )
            except ApiException as err:
                logger.info(
                    "Failed to create service\n %s",
                    (str(service_body))
                )

                logger.error(
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
            logger.info(
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
                logger.error(
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

    def create_deployment(self, deployment, namespace):
        """Create a UAI deployment

        """
        resp = None
        try:
            logger.info(
                "creating deployment %s in namespace %s",
                deployment.metadata.name,
                namespace
            )
            resp = self.apps_v1.create_namespaced_deployment(
                body=deployment,
                namespace=namespace
            )
        except ApiException as err:
            logger.error(
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
            logger.info(
                "delete deployment %s in namespace %s",
                deployment_name,
                namespace
            )
            resp = self.apps_v1.delete_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=client.V1DeleteOptions(
                    propagation_policy='Background',
                    grace_period_seconds=5
                )
            )
        except ApiException as err:
            if err.status != 404:
                logger.error(
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

    @staticmethod
    def gen_connection_string(username, ip_addr, tcp_port):
        """
        This function generates the uai.uai_connect_string for creating a
        ssh connection to the uai.

        The string will look like:
          ssh uai.username@uai.uai_ip -p uai.uai_port
        """
        uai_port = str(tcp_port) if tcp_port is not None else "<pending port>"
        uai_ip = ip_addr if ip_addr else "<pending IP Address>"
        port_string = (" -p %s" % uai_port) if tcp_port != 22 else ""
        user_string = ("%s@" % username) if username is not None else ""
        return "ssh %s%s%s" % (
            user_string,
            uai_ip,
            port_string
        )

    def compose_uai_from_pod(self, pod):
        """ Compose a UAI Model object from the data in a pod returned from k8s

        """
        username = pod.metadata.labels.get("user", None)
        uai_name = pod.metadata.labels.get(
            "app",
            "<internal error getting deployment name>"
        )
        opt_ports = pod.metadata.labels.get(
            "uas-uai-opt-ports",
            ""
        )
        uai_portmap = {
            int(port): int(port) for port in opt_ports.split('-')
        } if opt_ports else {}
        uai_host = pod.spec.node_name
        uai_age = self.get_pod_age(pod.status.start_time)
        uai_img = [
            ctr.image
            for ctr in pod.spec.containers
            if ctr.name == uai_name
        ][0]
        if pod.status.phase == 'Pending':
            uai_status = 'Pending'
        status_list = (
            []
            if not pod.status.container_statuses
            else pod.status.container_statuses
        )
        status_list = [
            status
            for status in status_list
            if status.name == uai_name
        ]
        uai_msg = ""
        for status in status_list:
            if status.state.running:
                ready_list = [
                    cond
                    for cond in pod.status.conditions
                    if cond.type == 'Ready'
                ]
                for cond in ready_list:
                    if pod.metadata.deletion_timestamp:
                        uai_status = 'Terminating'
                    elif cond.status == 'True':
                        uai_status = 'Running: Ready'
                    else:
                        uai_status = 'Running: Not Ready'
                        uai_msg = cond.message
            if status.state.terminated:
                uai_status = 'Terminated'
            if status.state.waiting:
                uai_status = 'Waiting'
                uai_msg = status.state.waiting.reason
        return UAI(
            username=username,
            uai_name=uai_name,
            uai_portmap=uai_portmap,
            uai_host=uai_host,
            uai_age=uai_age,
            uai_img=uai_img,
            uai_status=uai_status,
            uai_msg=uai_msg
        )

    def get_pod_info(self, deployment_name):
        """Retrieve pod information for a UAI pod from configuration.

        """
        pod_resp = None
        try:
            logger.info(
                "getting pod info %s",
                deployment_name
            )
            pod_resp = self.api.list_pod_for_all_namespaces(
                label_selector="app=%s" % deployment_name,
            )
        except ApiException as err:
            logger.error(
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
        # Handle the case where we got no results gracefully.  It
        # should not happen but it is better to fail cleanly.
        if not pod_resp.items:
            return None
        if len(pod_resp.items) > 1:
            logger.warning(
                "Oddly found more than one pod in "
                "deployment %s",
                deployment_name
            )
        # Only take the first one (there should only ever be one)
        pod = pod_resp.items[0]
        uai = self.compose_uai_from_pod(pod)
        srv_resp = None
        try:
            logger.info(
                "getting service info for %s-ssh in "
                "namespace %s",
                deployment_name,
                pod.metadata.namespace
            )
            srv_resp = self.api.read_namespaced_service(
                name=deployment_name + "-ssh",
                namespace=pod.metadata.namespace
            )
        except ApiException as err:
            if err.status != 404:
                logger.error(
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
        # Might not have gotten service information.  If we did,
        # fill out the rest of the UAI information.  If not, then
        # return back an incomplete UAI, since there is something
        # out there.
        uai.uai_port = None
        if srv_resp:
            ports = srv_resp.spec.ports if srv_resp.spec.ports else []
            svc_type = self.uas_cfg.get_svc_type('ssh')
            public_ip = srv_resp.metadata.labels.get('uas-public-ip', "True") == "True"
            if svc_type['svc_type'] == "LoadBalancer" and public_ip:
                # There is a race condition that can lead 'ingress' to be
                # None at this point, in which case we crash when we try to
                # get the UAI info.  If ingress is None or empty, skip this
                # for now.
                if srv_resp.status.load_balancer.ingress:
                    uai.uai_ip = srv_resp.status.load_balancer.ingress[0].ip
                    uai.uai_port = 22
            elif public_ip:
                uai.uai_ip = self.uas_cfg.get_external_ip()
            else:
                uai.uai_ip = (
                    srv_resp.spec.cluster_ip
                    if srv_resp.spec.cluster_ip
                    else None
                )
            # Skip the loop below if we already know the UAI port
            ports = ports if uai.uai_port is None else []
            for srv_port in ports:
                # There should be one port that is not in the
                # optional ports, which is the port that K8s
                # assigned to this service.  It will be the one
                # not found in the UAI portmap (which was derived
                # from the 'uas-uai-opt-ports' label on the pod).
                # That is the SSH port and should go in
                # uai.uai_port.
                uai.uai_port = (
                    srv_port.port
                    if srv_port.port not in uai.uai_portmap
                    else uai.uai_port
                )
        uai.uai_connect_string = self.gen_connection_string(
            uai.username,
            uai.uai_ip,
            uai.uai_port
        )
        return uai

    def deploy_uai(self, uai_class, uai_instance, uas_cfg):
        """Deploy a UAI from a UAI Class, UAI Instance specific information,
        and the current UAS Configuration.

        """
        service_name = uai_instance.get_service_name()
        deployment = uai_instance.create_deployment_object(
            uai_class=uai_class,
            uas_cfg=uas_cfg
        )
        # Create a service for the UAI
        uas_ssh_svc = uai_instance.create_service_object(
            uai_class,
            uas_cfg
        )
        # Make sure the UAI deployment is created
        deploy_resp = None
        try:
            logger.info(
                "getting deployment %s in namespace %s",
                uai_instance.deployment_name,
                uai_class.namespace
            )
            deploy_resp = self.apps_v1.read_namespaced_deployment(
                uai_instance.deployment_name,
                uai_class.namespace
            )
        except ApiException as err:
            if err.status != 404:
                logger.error(
                    "Failed to read deployment %s: %s",
                    uai_instance.deployment_name,
                    err.reason
                )
                abort(
                    err.status,
                    "Failed to read deployment %s: %s" % (
                        uai_instance.deployment_name,
                        err.reason
                    )
                )
        if not deploy_resp:
            deploy_resp = self.create_deployment(
                deployment,
                uai_class.namespace
            )

        # Start the UAI services
        logger.info("creating the UAI service %s", service_name)
        svc_resp = self.create_service(
            service_name,
            uas_ssh_svc,
            uai_class.namespace
        )
        if not svc_resp:
            # Clean up the deployment
            logger.error(
                "failed to create service, deleting UAI %s",
                uai_instance.deployment_name
            )
            self.remove_uais([uai_instance.deployment_name])
            abort(
                404,
                "Failed to create service: %s" % service_name
            )

        # Wait for the UAI IP to be set
        total_wait = 0.0
        delay = 0.5
        while True:
            uai_info = self.get_pod_info(
                deploy_resp.metadata.name
            )
            if uai_info and uai_info.uai_ip:
                break
            if total_wait >= UAI_IP_TIMEOUT:
                abort(
                    504,
                    "Failed to get IP for service: %s" % service_name
                )
            time.sleep(delay)
            total_wait += delay
            logger.info(
                "waiting for uai_ip %s seconds",
                str(total_wait)
            )
        return uai_info

    def select_deployments(self, labels=None, host=None):
        """Get a list of UAI names from the specified host (if any) that meet
        the criteria in the specified labels (if any).

        """
        labels = [] if labels is None else labels
        # Has to be a UAI (uas=managed) at least, along with any other
        # labels specified.
        label_selector = "uas=managed"
        if labels:
            label_selector = "%s,%s" % (label_selector, ','.join(labels))
        try:
            logger.info(
                "listing deployments matching: host %s,"
                " labels %s",
                host,
                label_selector
            )
            resp = self.apps_v1.list_deployment_for_all_namespaces(
                label_selector=label_selector
            )
        except ApiException as err:
            if err.status != 404:
                logger.error(
                    "Failed to get deployment list: %s",
                    err.reason
                )
                abort(err.status, "Failed to get deployment list")
        return [deployment.metadata.name for deployment in resp.items]

    def get_uai_namespace(self, deployment_name):
        """Determine the namespace a named UAI deployment is deployed in.

        """
        resp = self.apps_v1.list_deployment_for_all_namespaces(
            label_selector="app=%s" % deployment_name
        )
        if resp is None or not resp.items:
            return None
        if len(resp.items) > 1:
            logger.warning(
                "Oddly found more than one deployment named %s",
                deployment_name
            )
        return resp.items[0].metadata.namespace

    def get_uai_list(self, deploy_names):
        """Get a list of UAIs from the specified host (if any)
        that meet the criteria in the specified label (if any).

        """
        uai_list = []
        for deployment_name in deploy_names:
            uai = self.get_pod_info(deployment_name)
            if uai is not None:
                uai_list.append(uai)
        return uai_list

    def remove_uais(self, deploy_names):
        """Remove a list of UAIs by their deployment names from the specified
        namespace.

        """
        resp_list = []
        for deployment_name in deploy_names:
            namespace = self.get_uai_namespace(deployment_name)
            if namespace is None:
                # This deployment doesn't exist or doesn't have a
                # namespace (I dont think the latter is possible).
                # Skip it.
                continue

            # Do services first so that we don't orphan one if they abort
            service_resp = self.delete_service(
                deployment_name + "-ssh",
                namespace
            )
            deploy_resp = self.delete_deployment(
                deployment_name,
                namespace
            )
            if deploy_resp is None and service_resp is None:
                message = "Failed to delete %s - Not found" % deployment_name
            else:
                message = "Successfully deleted %s" % deployment_name
            resp_list.append(message)
        return resp_list


class UAIInstance:
    """This class carries information about individual UAI instances used
    in creating UAIs that does not belong in a UAIClass.  It provides
    a convenient container for information that is only known at UAI
    creation time.

    """
    @staticmethod
    def validate_ssh_key(ssh_key):
        """
        checks whether the ssh_key is a valid public key
        ssh_key input is expected to be a string
        :return: returns True if valid public key
        :rtype bool
        """
        try:
            ssh = sshpubkeys.SSHKey(ssh_key, strict=False,
                                    skip_option_parsing=True)
            ssh.parse()
            return True
        except (NotImplementedError, sshExceptions.MalformedDataError) as err:
            UAS_AUTH_LOGGER.error("Invalid key: %s", err)
        except sshExceptions.InvalidKeyError as err:
            UAS_AUTH_LOGGER.error("Unknown key type: %s", err)
        except Exception as err:  # pylint: disable=broad-except
            UAS_AUTH_LOGGER.error("Invalid non-key input: %s", err)
        return False

    def get_public_key_str(self, public_key):
        """Extract a public SSH key from its packing and verify that it looks
        like a public SSH key (and not a private one in particular).

        """
        public_key_str = None
        if public_key:
            try:
                # Depending on the API call, the public key may come
                # in as an 'io.Bytes' object or as a string.  If it is
                # an 'io.Bytes' object it needs to be turned into a
                # string.  Otherwise, it can be used as is.
                if isinstance(public_key, str):
                    public_key_str = public_key
                else:
                    public_key_str = public_key.read().decode()
                if not self.validate_ssh_key(public_key_str):
                    # do not log the key here even if it's invalid, it
                    # could be a private key accidentally passed in
                    logger.info("create_uai - invalid ssh public key")
                    abort(400, "Invalid ssh public key.")
            except Exception:  # pylint: disable=broad-except
                logger.info("create_uai - invalid ssh public key")
                abort(400, "Invalid ssh public key.")
        return public_key_str

    def __init__(self, owner=None, public_key=None, passwd_str=None):
        """Constructor

        """
        self.owner = owner
        if isinstance(public_key, str):
            self.public_key_str = public_key
        else:
            self.public_key_str = self.get_public_key_str(public_key)
        self.passwd_str = passwd_str
        dep_id = str(uuid.uuid4().hex[:8])
        dep_owner = "no-owner" if owner is None else self.owner
        self.deployment_name = 'uai-' + dep_owner + '-' + dep_id
        # If we are using macvlans then we will set that up in an
        # annotation in the metadata of the deployment, otherwise, the
        # annotations will be None.  USE_MACVLAN is based on
        # configuration from the Helm chart that can be set at service
        # deployment time.
        self.meta_annotations = None
        if os.environ.get('USE_MACVLAN', 'true').lower() == 'true':
            self.meta_annotations = {
                'k8s.v1.cni.cncf.io/networks': 'macvlan-uas-nmn-conf@nmn1'
            }

    def get_service_name(self):
        """ Compute the service name of a UAI based on UAI parameters.

        """
        return self.deployment_name + "-ssh"

    def get_env(self, uai_class=None):
        """ Compute a K8s environment block for use in the UAI deployment

        """
        env = [
            client.V1EnvVar(
                name='UAS_NAME',
                value=self.get_service_name()
            ),
            client.V1EnvVar(
                name='UAS_PASSWD',
                value=self.passwd_str
            ),
            client.V1EnvVar(
                name='UAS_PUBKEY',
                value=self.public_key_str
            )
        ]
        if uai_class.uai_creation_class is not None:
            env.append(
                client.V1EnvVar(
                    name='UAI_CREATION_CLASS',
                    value=uai_class.uai_creation_class
                )
            )
        return env

    def gen_labels(self, uai_class=None):
        """Generate labels for a UAI Deployment

        """
        ret = {
            "app": self.deployment_name,
            "uas": "managed"
        }
        if self.owner is not None:
            ret['user'] = self.owner
        if uai_class is not None:
            if uai_class.uai_creation_class is not None:
                ret['uas-uai-creation-class'] = uai_class.uai_creation_class
            if uai_class.opt_ports is not None:
                ret['uas-uai-opt-ports'] = "-".join(uai_class.opt_ports)
            ret['uas-public-ip'] = str(uai_class.public_ip)
            ret['uas-class-id'] = uai_class.class_id
        return ret

    # pylint: disable=too-many-locals
    def create_deployment_object(self, uai_class, uas_cfg):
        """Construct a deployment for a UAI or Broker

        """
        pod_metadata = client.V1ObjectMeta(
            labels=self.gen_labels(uai_class),
            annotations=self.meta_annotations
        )
        deploy_metadata = client.V1ObjectMeta(
            name=self.deployment_name,
            labels=self.gen_labels(uai_class)
        )
        volume_list = uai_class.volume_list
        resources = None
        if uai_class.resource_id is not None:
            resources = {}
            limit_json = UAIResource.get(uai_class.resource_id).limit
            request_json = UAIResource.get(uai_class.resource_id).request
            if limit_json:
                resources['limits'] = json.loads(limit_json)
            if request_json:
                resources['requests'] = json.loads(request_json)
        if not resources:
            resources = None
        container_ports = uas_cfg.gen_port_list(
            service=False,
            opt_ports=[
                int(port) for port in uai_class.opt_ports
            ] if uai_class.opt_ports is not None else None
        )
        logger.info(
            "UAI Name: %s; Container ports: %s; Optional ports: %s",
            self.deployment_name,
            container_ports,
            uai_class.opt_ports
        )

        # Configure Pod template container
        container = client.V1Container(
            name=self.deployment_name,
            image=UAIImage.get(uai_class.image_id).imagename,
            resources=resources,
            env=self.get_env(uai_class),
            ports=container_ports,
            volume_mounts=uas_cfg.gen_volume_mounts(volume_list),
            readiness_probe=uas_cfg.create_readiness_probe()
        )

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
        priority_class_name = 'uai-priority'
        if uai_class.priority_class_name is not None:
            priority_class_name = uai_class.priority_class_name
        template = client.V1PodTemplateSpec(
            metadata=pod_metadata,
            spec=client.V1PodSpec(
                priority_class_name=priority_class_name,
                containers=[container],
                affinity=affinity,
                volumes=uas_cfg.gen_volumes(volume_list)
            )
        )

        # Create the specification of deployment
        spec = client.V1DeploymentSpec(
            replicas=1,
            selector={
                'matchLabels': {
                    'app': self.deployment_name
                }
            },
            template=template
        )
        # Instantiate the deployment object
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=deploy_metadata,
            spec=spec
        )
        return deployment

    def create_service_object(self, uai_class, uas_cfg):
        """
        Create a service object for the deployment of the UAI.

        """
        # Pick the service type based on the value of 'public_ip' in
        # the UAI Class.  This is a lot simpler than it looks if you
        # delve into it, but I am using the code that was here to do
        # this. That code bases the service class (SSH point of
        # access) on two strings: "service" (which basically means an
        # internal ClusterIP) and "ssh" (which basically means a
        # LoadBalncer IP or a NodePort).  Instead of reworking all
        # that logic, I am picking one or the other here based on
        # whether 'public_ip' is true or false.
        service_type = "ssh" if uai_class.public_ip else "service"
        metadata = client.V1ObjectMeta(
            name=self.get_service_name(),
            labels=self.gen_labels(uai_class),
        )
        ports = uas_cfg.gen_port_list(
            service_type,
            service=True,
            opt_ports=[
                int(port) for port in uai_class.opt_ports
            ] if uai_class.opt_ports is not None else None
        )

        # svc_type is a dict with the following fields:
        #   'svc_type': (NodePort, ClusterIP, or LoadBalancer)
        #   'ip_pool': (None, or a specific pool)  Valid only for LoadBalancer.
        #   'valid': (True or False) is svc_type is valid or not
        svc_type = uas_cfg.get_svc_type(service_type)
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
            # A specific IP pool is given, update the metadata with
            # annotations
            metadata.annotations = {
                "metallb.universe.tf/address-pool": svc_type['ip_pool']
            }
        spec = client.V1ServiceSpec(
            selector={'app': self.deployment_name},
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
