import logging
import sys

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

    def create_deployment_object(self, deployment_name, imagename):
        # Configure Pod template container
        container = client.V1Container(
            name=deployment_name,
            image=imagename,
            args=["/bin/sh", "-c", "while true;do date;sleep 5; done"],
            ports=[client.V1ContainerPort(container_port=80)])
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
                sys.exit(1)
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
                sys.exit(1)
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
                sys.exit(1)
        return resp

    def get_pod_info(self, pod_prefix, namespace='default'):
        resp = None
        uan = UAN()
        try:
            resp = self.api.list_namespaced_pod(namespace=namespace,
                                                include_uninitialized=True)
        except ApiException as e:
            if e.status != 404:
                UAN_LOGGER.error("Unknown error: %s" % e)
                sys.exit(1)
        for pod in resp.items:
            if pod.metadata.name.startswith(pod_prefix + "-"):
                uan.uan_name = pod_prefix
                uan.uan_ip = pod.status.host_ip
                uan.uan_status = pod.status.phase
                uan.uan_msg = pod.status.reason
        return uan

    def create_uan(self, username, imagename, namespace='default'):
        deployment_image = imagename
        for i in [':', '/', '.']:
            if i in deployment_image:
                deployment_image = deployment_image.replace(i, '-')
        deployment_name = username + '-' + deployment_image
        deployment = self.create_deployment_object(deployment_name, imagename)
        resp = None
        try:
            resp = self.extensions_v1beta1.read_namespaced_deployment(deployment_name, namespace)
        except ApiException as e:
            if e.status != 404:
                UAN_LOGGER.error("Unknown error: %s" % e)
                sys.exit(1)
        if not resp:
            resp = self.create_deployment(deployment, namespace)
        uan_info = self.get_pod_info(resp.metadata.name, namespace)
        while not uan_info.uan_ip:
            uan_info = self.get_pod_info(resp.metadata.name, namespace)
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
                sys.exit(1)
        for deployment in resp.items:
            if deployment.metadata.name.startswith(username + "-"):
                uan_list.append(self.get_pod_info(deployment.metadata.name))
        if not uan_list:
            uan_list.append('No UANs found for %s' % (username))
        return uan_list

    def delete_uans(self, deployment_list, namespace='default'):
        resp_list = []
        for d in deployment_list:
            self.delete_deployment(d, namespace)
            resp_list.append(self.get_pod_info(d, namespace))
        return resp_list
