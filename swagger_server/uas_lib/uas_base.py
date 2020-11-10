# Copyright 2020 Hewlett Packard Enterprise Development LP#
#
"""
Base Class for User Access Service Operations
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
                    grace_period_seconds=5))
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
    def gen_connection_string(uai):
        """
        This function generates the uai.uai_connect_string for creating a
        ssh connection to the uai.

        The string will look like:
          ssh uai.username@uai.uai_ip -p uai.uai_port

        :param uai:
        :type uai: uai
        :return: uai:
        """
        port_string = " -p " + str(uai.uai_port) if uai.uai_port != 22 else ""

        return "ssh %s@%s%s" % (
            uai.username,
            uai.uai_ip,
            port_string
        )

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
            logger.info(
                "get_pod_info - UAIs will be gathered from"
                " the %s namespace.",
                namespace
            )
        try:
            logger.info(
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

        # previously this code could return an empty UAI object,
        # but with the host filter, we could legitimately get 0
        # results and returning an empty object puts an empty object
        # into the return list.
        if not pod_resp.items:
            return None
        if len(pod_resp.items) > 1:
            logger.warning(
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
            logger.info(
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
                    "Failed to create deployment %s: %s",
                    uai_instance.deployment_name,
                    err.reason
                )
                abort(
                    err.status,
                    "Failed to create deployment %s: %s" % (
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
            self.remove_uais(
                [uai_instance.deployment_name],
                uai_class.namespace
            )
            abort(
                404,
                "Failed to create service: %s" % service_name
            )

        # Wait for the UAI IP to be set
        total_wait = 0.0
        delay = 0.5
        while True:
            uai_info = self.get_pod_info(
                deploy_resp.metadata.name,
                uai_class.namespace
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

    def get_uai_list(self, label=None, host=None, namespace=None):
        """Get a list of UAIs from the specified namespace and host (if any)
        that meet the criteria in the specified label.

        """
        uai_list = []
        try:
            logger.info(
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
                logger.error(
                    "Failed to get deployment list: %s",
                    err.reason
                )
                abort(err.status, "Failed to get deployment list")
        for deployment in resp.items:
            uai = self.get_pod_info(deployment.metadata.name, namespace, host)
            if uai:
                uai_list.append(uai)
        return uai_list

    def remove_uais(self, deploy_names, namespace):
        """Remove a list of UAIs by their deployment names from the specified
        namespace.

        """
        resp_list = []
        for uai_dep in deploy_names:
            # Do services first so that we don't orphan one if they abort
            service_resp = self.delete_service(uai_dep + "-ssh", namespace)
            deploy_resp = self.delete_deployment(uai_dep, namespace)
            if deploy_resp is None and service_resp is None:
                message = "Failed to delete %s - Not found" % uai_dep
            else:
                message = "Successfully deleted %s" % uai_dep
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
            ret['uas-public-ssh'] = str(uai_class.public_ssh)
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
            optional_ports=uai_class.opt_ports
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
        # Pick the service type based on the value of 'public_ssh' in
        # the UAI Class.  This is a lot simpler than it looks if you
        # delve into it, but I am using the code that was here to do
        # this. That code bases the service class (SSH point of
        # access) on two strings: "service" (which basically means an
        # internal ClusterIP) and "ssh" (which basically means a
        # LoadBalncer IP or a NodePort).  Instead of reworking all
        # that logic, I am picking one or the other here based on
        # whether 'public_ssh' is true or false.
        service_type = "ssh" if uai_class.public_ssh else "service"
        metadata = client.V1ObjectMeta(
            name=self.get_service_name(),
            labels=self.gen_labels(uai_class),
        )
        ports = uas_cfg.gen_port_list(
            service_type,
            service=True,
            optional_ports=uai_class.opt_ports
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
