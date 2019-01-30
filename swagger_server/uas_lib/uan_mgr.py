#
# Copyright 2018, Cray Inc.  All Rights Reserved.
#
# Description:
#   Manages Cray User Access Node instances.
#

import logging
import uuid

from flask import abort
from kubernetes import config, client
from kubernetes.client import Configuration
from kubernetes.client.apis import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream
from swagger_server.models.uan import UAN
from swagger_server.uas_lib.uas_cfg import UasCfg


UAS_MGR_LOGGER = logging.getLogger('uas_mgr')


class UanManager(object):

    def __init__(self):
        config.load_incluster_config()
        self.c = Configuration()
        self.c.assert_hostname = False
        Configuration.set_default(self.c)
        self.api = core_v1_api.CoreV1Api()
        self.extensions_v1beta1 = client.ExtensionsV1beta1Api()
        self.uas_cfg = UasCfg()

    def get_user_account_info(self, username, namespace):
        """
        This function locates the uas-id service pod and performs
        an exec of 'getent passwd <username>' via the kubernetes api to
        retrieve the user's credentials.

        Returns the output of 'getent passwd username'.

        :param username: username to search for with getent
        :type username: str
        :param: namespace: kubernetes namespace
        :return: output of 'getent passwd username'
        :type return: str
        """
        # Find the pod name for the uas-id app.
        resp = self.api.list_namespaced_pod(namespace,
                                            label_selector='app=cray-uas-id')
        uas_id_pod = None
        for item in resp.items:
            uas_id_pod = item.metadata.name
        if not uas_id_pod:
            abort(404, 'UAS ID service not found.')
        # Exec the command in uas_id_pod.
        exec_command = [
            'chroot',
            '/host',
            'getent',
            'passwd',
            username
        ]
        uas_id = stream(self.api.connect_get_namespaced_pod_exec, uas_id_pod,
                        namespace, command=exec_command, stdout=True,
                        stdin=False, tty=False)
        if not uas_id:
            abort(404, 'user not found. (%s)' % username)
        return uas_id

    def create_service_object(self, service_name, service_type, deployment_name):
        """
        Create a service object for the deployment of the UAN.

        :param service_name:
        :type service_name: str
        :param service_type:
        :type service_type: str
        :return: service object
        """
        if not self.uas_cfg.get_external_ips("NodePort"):
            # external gateway IP is not set.  This is an error.
            abort(404, "UAS misconfigured (uas_ips not set). Please contact "
                       "your system administrator.")

        external_ips = self.uas_cfg.get_external_ips(service_type)
        ports = self.uas_cfg.gen_port_list(service_type, service=True)
        if external_ips:
            spec = client.V1ServiceSpec(
                selector={'app': deployment_name},
                type=service_type,
                external_i_ps=external_ips,
                ports=ports
            )
        else:
            spec = client.V1ServiceSpec(
                selector={'app': deployment_name},
                type=service_type,
                external_i_ps=external_ips,
                ports=ports
            )
        service = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=service_name,
                                         labels={"uai_svc": deployment_name.split("-")[0]}),
            spec=spec
        )
        return service

    def create_service(self, service_name, service_body, namespace):
        # Create the service
        resp = None
        try:
            resp = self.api.read_namespaced_service(name=service_name,
                                                    namespace=namespace)
        except ApiException as e:
            if e.status != 404:
                abort(e.status, "Failed to get service info while creating UAN")
        if not resp:
            try:
                resp = self.api.create_namespaced_service(body=service_body,
                                                          namespace=namespace)
            except ApiException as e:
                resp = None
        return resp

    def delete_service(self, service_name, namespace):
        # Delete the service
        resp = None
        try:
            resp = self.api.delete_namespaced_service(
                    name=service_name,
                    namespace=namespace,
                    body=client.V1DeleteOptions(
                        propagation_policy='Foreground',
                        grace_period_seconds=5))
        except ApiException as e:
            if e.status != 404:
                abort(e.status, "Failed in delete_service")
        return resp

    def create_deployment_object(self, username, deployment_name, imagename,
                                 usersshpubkey, namespace):
        # Configure Pod template container
        container = client.V1Container(
            name=deployment_name,
            image=imagename,
            env=[client.V1EnvVar(
                    name='UAS_NAME',
                    value=deployment_name + "np"),
                 client.V1EnvVar(
                     name='UAS_PASSWD',
                     value=self.get_user_account_info(username, namespace)),
                 client.V1EnvVar(
                     name='UAS_PUBKEY',
                     value=usersshpubkey.read().decode())],
            ports=self.uas_cfg.gen_port_list(service=False),
            volume_mounts=self.uas_cfg.gen_volume_mounts())
        # Create a volumes template
        volumes = self.uas_cfg.gen_volumes()

        # Create and configure affinity
        node_selector_terms = [client.V1NodeSelectorTerm(match_expressions=[client.V1NodeSelectorRequirement(
                                                                       key='uas', operator='Exists')])]
        node_selector = client.V1NodeSelector(node_selector_terms)
        node_affinity = client.V1NodeAffinity(required_during_scheduling_ignored_during_execution=node_selector)
        affinity = client.V1Affinity(node_affinity=node_affinity)

        # Create and configure a spec section
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": deployment_name}),
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
            metadata=client.V1ObjectMeta(name=deployment_name),
            spec=spec)
        return deployment

    def create_deployment(self, deployment, namespace):
        # Create deployment
        resp = None
        try:
            resp = self.extensions_v1beta1.create_namespaced_deployment(
                body=deployment,
                namespace=namespace)
        except ApiException as e:
            abort(e.status, "Failed in create_deployment")
        return resp

    def update_deployment(self, deployment, deployment_name, imagename, namespace):
        # Update container image
        deployment.spec.template.spec.containers[0].image = imagename
        # Update the deployment
        resp = None
        try:
            resp = self.extensions_v1beta1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=deployment)
        except ApiException as e:
            abort(e.status, "Failed in update deployment")
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
                abort(e.status, "Failed in delete_deployment")
        return resp

    def get_pod_info(self, deployment_name, namespace='default'):
        pod_resp = None
        uan = UAN()
        uan.username = deployment_name.split('-')[0]
        try:
            pod_resp = self.api.list_namespaced_pod(namespace=namespace,
                                                    include_uninitialized=True)
        except ApiException as e:
            abort(e.status, "Failed to get pod info")
        for pod in pod_resp.items:
            if pod.metadata.name.startswith(deployment_name):
                uan.uan_name = deployment_name
                for ctr in pod.spec.containers:
                    if ctr.name == deployment_name:
                        uan.uan_img = ctr.image
                if pod.status.container_statuses:
                    for s in pod.status.container_statuses:
                        if s.name == deployment_name:
                            if s.state.running:
                                for c in pod.status.conditions:
                                    if c.type == 'Ready':
                                        if c.status == 'True':
                                            uan.uan_status = 'Running: Ready'
                                        else:
                                            uan.uan_status = 'Running: Not Ready'
                                            uan.uan_msg = c.message
                            if s.state.terminated:
                                uan.uan_status = 'Terminated'
                            if s.state.waiting:
                                uan.uan_status = 'Waiting'
                                uan.uan_msg = s.state.waiting.reason
                uan.uan_ip = self.uas_cfg.get_external_ips("NodePort")[0]
                srv_resp = None
                try:
                    srv_resp = self.api.read_namespaced_service(name=deployment_name + "np",
                                                                namespace=namespace)
                except ApiException as e:
                    if e.status != 404:
                        abort(e.status, "Failed to get service info")
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
        if not username:
            abort(400, "Missing username.")
        if not usersshpubkey:
            abort(400, "Missing ssh public key.")
        if not imagename:
            imagename = self.uas_cfg.get_default_image()
        if not self.uas_cfg.validate_image(imagename):
            abort(400, "Invalid image (%s). Valid images: %s. Default: %s"
                  % (imagename, self.uas_cfg.get_images(),
                     self.uas_cfg.get_default_image()))
        deployment_id = uuid.uuid4().hex[:8]
        deployment_name = username + '-' + str(deployment_id)
        deployment = self.create_deployment_object(username, deployment_name,
                                                   imagename, usersshpubkey,
                                                   namespace)
        # Create a NodePort service on the uas_access_port
        node_port_svc_name = deployment_name + "np"
        node_port_svc = self.create_service_object(node_port_svc_name, "NodePort", deployment_name)
        # Create a ClusterIP service on additional ports for other services to
        # access.
        cfg = self.uas_cfg.get_config()
        cluster_ip_svc_name = None
        cluster_ip_svc = None
        if cfg:
            try:
                if cfg['uas_svc_ports']:
                    cluster_ip_svc_name = deployment_name + "cip"
                    cluster_ip_svc = self.create_service_object(cluster_ip_svc_name, "ClusterIP", deployment_name)
            except KeyError:
                cluster_ip_svc = None
        deploy_resp = None
        try:
            deploy_resp = self.extensions_v1beta1.read_namespaced_deployment(deployment_name, namespace)
        except ApiException as e:
            if e.status != 404:
                abort(e.status, "Failed to create deployment")
        if not deploy_resp:
            deploy_resp = self.create_deployment(deployment, namespace)
        # Start the NodePort service
        svc_resp = self.create_service(node_port_svc_name, node_port_svc, namespace)
        if not svc_resp:
            abort(404, "Failed to create node port service {}".format(node_port_svc_name))
        # Start the ClusterIP service
        if cluster_ip_svc:
            svc_resp = self.create_service(cluster_ip_svc_name, cluster_ip_svc, namespace)
            if not svc_resp:
                abort(404, "Failed to create cluster IP service {}".format(cluster_ip_svc_name))
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
                abort(e.status, "Failed to get deployment list")
        for deployment in resp.items:
            if deployment.metadata.name.startswith(username + "-"):
                uan_list.append(self.get_pod_info(deployment.metadata.name))
        return uan_list

    def delete_uans(self, deployment_list, namespace='default'):
        resp_list = []
        for d in deployment_list:
            self.delete_deployment(d, namespace)
            self.delete_service(d + "np", namespace)
            self.delete_service(d + "cip", namespace)
            resp_list.append(d)
        return resp_list
