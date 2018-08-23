#
# Copyright 2018, Cray Inc.  All Rights Reserved.
#
# Description:
#   Manages Cray User Access Node instances.
#

import logging

from kubernetes import config, client
from kubernetes.client import Configuration
from kubernetes.client.apis import core_v1_api
from kubernetes.client.rest import ApiException
from swagger_server.models.uan import UAN


UAN_LOGGER = logging.getLogger('uas_mgr')


class UanManager(object):

    def __init__(self, cfg_file='/etc/kubernetes/admin.conf'):
        config.load_kube_config(cfg_file)
        self.c = Configuration()
        self.c.assert_hostname = False
        Configuration.set_default(self.c)
        self.api = core_v1_api.CoreV1Api()
        self.extensions_v1beta1 = client.ExtensionsV1beta1Api()

    def get_user_credentials(self, username):
        """
        Returns the output of 'getent passwd username'.

        :param username:
        :type username: str
        :return: output of 'getent passwd username'
        :type return: str
        """
        # TODO: Hardcoded to crayadm for testing
        return 'crayadm:x:12795:14901:crayadm:/home/crayadm:/bin/bash'

    def create_service_object(self, deployment_name):
        """
        Create a service object for the deployment of the UAN.

        :param deployment_name:
        :type deployment_name: str
        :return: service object
        """
        spec = client.V1ServiceSpec(
            selector={'app': deployment_name},
            type="NodePort",
            ports=[client.V1ServicePort(name=deployment_name,
                                        port=30123,
                                        protocol="TCP")]
        )
        service = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=deployment_name),
            spec=spec
        )
        return service

    def create_service(self, service, namespace):
        # Create the service
        resp = None
        try:
            resp = self.api.create_namespaced_service(body=service,
                                                      namespace=namespace)
        except ApiException as e:
            if e.status != 404:
                UAN_LOGGER.error("Unknown error: %s" % e)
        return resp

    def delete_service(self, service, namespace):
        # Delete the service
        resp = None
        try:
            resp = self.api.delete_namespaced_service(
                    name=service,
                    namespace=namespace,
                    body=client.V1DeleteOptions(
                        propagation_policy='Foreground',
                        grace_period_seconds=5))
        except ApiException as e:
            if e.status != 404:
                UAN_LOGGER.error("Unknown error: %s" % e)
        return resp

    def create_deployment_object(self, username, deployment_name, imagename,
                                 usersshpubkey):
        # Configure Pod template container
        container = client.V1Container(
            name=deployment_name,
            image=imagename,
            env=[client.V1EnvVar(
                     name='UAN_PASSWD',
                     value=self.get_user_credentials(username)),
                 client.V1EnvVar(
                     name='UAN_PUBKEY',
                     value=usersshpubkey.read().decode())],
            ports=[client.V1ContainerPort(container_port=30123)])
        # Create and configure a spec section
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": deployment_name}),
            spec=client.V1PodSpec(containers=[container]))
        # Create the specification of deployment
        spec = client.ExtensionsV1beta1DeploymentSpec(
            replicas=1,
            template=template)
        # Instantiate the deployment object
        deployment = client.ExtensionsV1beta1Deployment(
            api_version="extensions/v1beta1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=deployment_name),
            spec=spec)
        return deployment

    def create_deployment(self, deployment, namespace):
        # Create deployment
        try:
            resp = self.extensions_v1beta1.create_namespaced_deployment(
                body=deployment,
                namespace=namespace)
        except ApiException as e:
            if e.status != 404:
                UAN_LOGGER.error("Unknown error: %s" % e)
        return resp

    def update_deployment(self, deployment, deployment_name, imagename, namespace):
        # Update container image
        deployment.spec.template.spec.containers[0].image = imagename
        # Update the deployment
        try:
            resp = self.extensions_v1beta1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=deployment)
        except ApiException as e:
            if e.status != 404:
                UAN_LOGGER.error("Unknown error: %s" % e)
        return resp

    def delete_deployment(self, deployment_name, namespace):
        # Delete deployment
        resp = None
        try:
            resp = self.extensions_v1beta1.delete_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=client.V1DeleteOptions(
                    propagation_policy='Foreground',
                    grace_period_seconds=5))
        except ApiException as e:
            if e.status != 404:
                UAN_LOGGER.error("Unknown error: %s" % e)
        return resp

    def get_pod_info(self, pod_prefix, namespace='default'):
        pod_resp = None
        uan = UAN()
        uan.username = pod_prefix.split('-')[0]
        try:
            pod_resp = self.api.list_namespaced_pod(namespace=namespace,
                                                    include_uninitialized=True)
        except ApiException as e:
            if e.status != 404:
                UAN_LOGGER.error("Unknown error: %s" % e)
        for pod in pod_resp.items:
            if pod.metadata.name.startswith(pod_prefix + "-"):
                uan.uan_name = pod_prefix
                for ctr in pod.spec.containers:
                    if ctr.name == pod_prefix:
                        uan.uan_img = ctr.image
                uan.uan_ip = pod.status.host_ip
                uan.uan_status = pod.status.phase
                uan.uan_msg = pod.status.reason
                srv_resp = None
                try:
                    srv_resp = self.api.read_namespaced_service(name=pod_prefix,
                                                                namespace=namespace)
                except ApiException as e:
                    if e.status != 404:
                        UAN_LOGGER.error("Unknown error: %s" % e)
                if srv_resp:
                    uan.uan_port = srv_resp.spec.ports[0].node_port
                uan = self.gen_connection_string(uan)
        return uan

    def gen_connection_string(self, uan):
        """
        This function generates the uan.uan_connect_string for creating a
        ssh connection to the uan.

        The string will look like:
          ssh uan.username@uan.uan_ip -p uan.uan_port -i ~/.ssh/id_rsa

        :param uan:
        :type uan: uan
        :return: uan:
        """
        uan.uan_connect_string = ("ssh %s@%s -p %s -i ~/.ssh/id_rsa" %
                                  (uan.username,
                                   uan.uan_ip,
                                   uan.uan_port))
        return uan

    def create_uan(self, username, usersshpubkey, imagename, namespace='default'):
        deployment_image = imagename
        for i in [':', '/', '.']:
            if i in deployment_image:
                deployment_image = deployment_image.replace(i, '-')
        deployment_name = username + '-' + deployment_image
        deployment = self.create_deployment_object(username, deployment_name,
                                                   imagename, usersshpubkey)
        service = self.create_service_object(deployment_name)
        deploy_resp = None
        try:
            deploy_resp = self.extensions_v1beta1.read_namespaced_deployment(deployment_name, namespace)
        except ApiException as e:
            if e.status != 404:
                UAN_LOGGER.error("Unknown error: %s" % e)
        if not deploy_resp:
            deploy_resp = self.create_deployment(deployment, namespace)
        srv_resp = None
        try:
            srv_resp = self.api.read_namespaced_service(name=deployment_name,
                                                        namespace=namespace)
        except ApiException as e:
            if e.status != 404:
                UAN_LOGGER.error("Unknown error: %s" % e)
        if not srv_resp:
            srv_resp = self.api.create_namespaced_service(body=service,
                                                          namespace=namespace)
        uan_info = self.get_pod_info(deploy_resp.metadata.name, namespace)
        while not uan_info.uan_ip:
            uan_info = self.get_pod_info(deploy_resp.metadata.name, namespace)
        return uan_info

    def list_uans_for_user(self, username, namespace='default'):
        resp = None
        uan_list = []
        try:
            resp = self.extensions_v1beta1.list_namespaced_deployment(namespace=namespace,
                                                 include_uninitialized=True)
        except ApiException as e:
            if e.status != 404:
                UAN_LOGGER.error("Unknown error: %s" % e)
        for deployment in resp.items:
            if deployment.metadata.name.startswith(username + "-"):
                uan_list.append(self.get_pod_info(deployment.metadata.name))
        return uan_list

    def delete_uans(self, deployment_list, namespace='default'):
        resp_list = []
        for d in deployment_list:
            self.delete_deployment(d, namespace)
            resp_list.append(self.get_pod_info(d, namespace))
        return resp_list
