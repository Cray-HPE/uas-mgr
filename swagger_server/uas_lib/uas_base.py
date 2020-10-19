# Copyright 2020 Hewlett Packard Enterprise Development LP#
#
"""
Base Class for User Access Service Operations
"""

import logging
import sys
import json
from datetime import datetime, timezone
from flask import abort
from kubernetes import config, client
from kubernetes.client.rest import ApiException
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from swagger_server.models import UAI
from swagger_server.uas_lib.uas_cfg import UasCfg
from swagger_server.uas_data_model.uai_resource import UAIResource
from swagger_server.uas_data_model.uai_image import UAIImage

class UasBase:
    """Base class used for any class implementing UAS API functionality.
    Takes care of common activities like K8s client setup, loading UAS
    configuration from the default configmap and so forth.

    """
    def __init__(self):
        """ Constructor """
        self.logger = logging.getLogger('uas_mgr')
        self.logger.setLevel(logging.INFO)
        # pylint: disable=invalid-name
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        # pylint: disable=invalid-name
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        config.load_incluster_config()
        self.c = Configuration()
        self.c.assert_hostname = False
        Configuration.set_default(self.c)
        self.api = core_v1_api.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.uas_cfg = UasCfg()

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

    @staticmethod
    def gen_labels(deployment_name, user_name=None, uai_class=None):
        """Generate labels for a UAI Deployment

        """
        ret = {
            "app": deployment_name,
            "uas": "managed"
        }
        if user_name is not None:
            ret['user'] = user_name
        if uai_class is not None:
            if uai_class.uai_creation_class is not None:
                ret['uas-uai-creation-class'] = uai_class.uai_creation_class
            ret['uas-public-ssh'] = str(uai_class.public_ssh)
            ret['uas-class-id'] = uai_class.class_id
        return ret

    # pylint: disable=too-many-arguments,too-many-locals
    def create_deployment_object(self,
                                 uai_class,
                                 deployment_name,
                                 env,
                                 pod_metadata,
                                 deploy_metadata,
                                 opt_ports_list):
        """Construct a deployment for a UAI or Broker

        """
        imagename = UAIImage.get(uai_class.image_id).imagename
        volume_list = uai_class.volume_list
        resource_id = uai_class.resource_id
        resources = None
        if resource_id is not None:
            resources = {}
            limit_json = UAIResource.get(resource_id).limit
            request_json = UAIResource.get(resource_id).request
            if limit_json:
                resources['limits'] = json.loads(limit_json)
            if request_json:
                resources['requests'] = json.loads(request_json)
        if not resources:
            resources = None
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
            resources=resources,
            env=env,
            ports=container_ports,
            volume_mounts=self.uas_cfg.gen_volume_mounts(volume_list),
            readiness_probe=self.uas_cfg.create_readiness_probe()
        )
        # Create a volumes template
        volumes = self.uas_cfg.gen_volumes(volume_list)

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
                volumes=volumes
            )
        )

        # Create the specification of deployment
        spec = client.V1DeploymentSpec(
            replicas=1,
            selector={
                'matchLabels': {
                    'app': deployment_name
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

    def create_service_object(self, service_type, opt_ports_list,
                              deployment_name, metadata):
        """
        Create a service object for the deployment of the UAI.

        :param service_type: One of "ssh" or "service"
        :type service_type: str
        :param opt_ports_list: List of optional ports to project
        :type opt_ports_list: list
        :param deployment_name: The name of the UAI / Broker deployment
        :type deployment_name: str
        :param metadata: The service metadata to use
        :type metadata: K8s metadata object
        :return: service object
        """
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
            # A specific IP pool is given, update the metadata with
            # annotations
            metadata.annotations = {
                "metallb.universe.tf/address-pool": svc_type['ip_pool']
            }
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
                self.logger.info(
                    "Failed to create service\n %s",
                    (str(service_body))
                )

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
