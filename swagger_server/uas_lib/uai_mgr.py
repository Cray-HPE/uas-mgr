#
# Copyright 2018, Cray Inc.  All Rights Reserved.
#
# Description:
#   Manages Cray User Access Node instances.
#

import logging
import sys
import uuid
from flask import abort, request
from kubernetes import config, client
from kubernetes.client import Configuration
from kubernetes.client.apis import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream
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

        # Until Authorization is required, optionally gather user 
        # information from Keycloak if a Bearer token is provided
        # with the request.
        if 'Authorization' in request.headers:
            self.userinfo = self.uas_auth.userinfo(request.headers['Authorization'])
            if self.uas_auth.validUserinfo(self.userinfo):
                self.passwd = self.uas_auth.createPasswd(self.userinfo)
                self.username = self.userinfo[self.uas_auth.username]
                UAS_MGR_LOGGER.info("UAS request for: %s" % self.username)
            else:
                missing = self.uas_auth.missingAttributes(self.userinfo)
                UAS_MGR_LOGGER.info("Token not valid for UAS. Attributes missing: "
                                    "%s" % missing)
                abort(400, "Token not valid for UAS. Attributes missing: "
                                    "%s" % missing)

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
            if item.status.container_statuses:
                # CASMUSER-1266 - if the pod is not ready, we get an error
                # when we try to exec into it. There's only 1 container
                # so no need to iterate the conditions.
                if item.status.container_statuses[0].ready:
                    uas_id_pod = item.metadata.name

        if not uas_id_pod:
            abort(503, 'uas-id service not available.')

        # Exec the command in uas_id_pod.
        exec_command = [
            'chroot',
            '/host',
            'getent',
            'passwd',
            username
        ]
        try:
            uas_id = stream(self.api.connect_get_namespaced_pod_exec,
                            uas_id_pod, namespace, command=exec_command,
                            stdout=True, stdin=False, tty=False)
        except ApiException:
            abort(500, 'error connecting to uas-id service')

        if not uas_id:
            abort(400, 'user not found. (%s)' % username)
        return uas_id.rstrip()

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
                        propagation_policy='Foreground',
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

    def create_deployment_object(self, username, deployment_name, imagename,
                                 publickeyStr, opt_ports_list, namespace):

        container_ports = self.uas_cfg.gen_port_list(service=False,
                                                     optional_ports=opt_ports_list)
        UAS_MGR_LOGGER.info("UAI Name: %s; Container ports: %s; Optional ports: %s" 
                            % (deployment_name, container_ports, opt_ports_list))
        # Use passwd derived from the Auth token if present.
        # CASMUSER-1460 tracks making this the only allowable passwd 
        if not self.passwd:
            passwd = self.get_user_account_info(username, namespace)
        else:
            passwd = self.passwd

        UAS_MGR_LOGGER.info("Optional ports: %s" % opt_ports_list)
        container_ports = self.uas_cfg.gen_port_list(service=False,
                                                     optional_ports=opt_ports_list)
        UAS_MGR_LOGGER.info("Container ports: %s" % container_ports)
        # Configure Pod template container
        container = client.V1Container(
            name=deployment_name,
            image=imagename,
            env=[client.V1EnvVar(
                    name='UAS_NAME',
                    value=deployment_name + "-ssh"),
                 client.V1EnvVar(
                     name='UAS_PASSWD',
                     value=passwd),
                 client.V1EnvVar(
                     name='UAS_PUBKEY',
                     value=publickeyStr)],
            ports=container_ports,
            volume_mounts=self.uas_cfg.gen_volume_mounts(),
            readiness_probe=self.uas_cfg.create_readiness_probe())
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
                    propagation_policy='Foreground',
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

    def get_pod_info(self, deployment_name, namespace='default'):
        pod_resp = None
        uai = UAI()
        uai.uai_portmap = {}
        uai.username = deployment_name.split('-')[1]
        try:
            UAS_MGR_LOGGER.info("getting pod info %s in namespace %s" %
                                 (deployment_name, namespace))
            pod_resp = self.api.list_namespaced_pod(namespace=namespace,
                                                    include_uninitialized=True)
        except ApiException as e:
            UAS_MGR_LOGGER.error("Failed to get pod info %s: %s" %
                                 (deployment_name, e.reason))
            abort(e.status, "Failed to get pod info %s: %s" %
                  (deployment_name, e.reason))
        for pod in pod_resp.items:
            if pod.metadata.name.startswith(deployment_name):
                uai.uai_name = deployment_name
                for ctr in pod.spec.containers:
                    if ctr.name == deployment_name:
                        uai.uai_img = ctr.image
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

                uai = self.gen_connection_string(uai)
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
        uai.uai_connect_string = ("ssh %s@%s -p %s -i ~/.ssh/id_rsa" %
                                  (uai.username,
                                   uai.uai_ip,
                                   uai.uai_port))
        return uai

    def gen_labels(self, deployment_name):
        return {"app": deployment_name, "uas": "managed"}

    def create_uai(self, username, publickey, imagename, opt_ports, namespace='default'):
        # Use the username derived from the Auth token if present.
        # CASMUSER-1460 tracks making this the only allowable username
        if self.username:
            if not username == self.username:
                UAS_MGR_LOGGER.error("Username '%s' does not match "
                                     "token username '%s'" %
                                     (username, self.username))
                abort(400, "Username '%s' does not match "
                      "token username '%s'" %
                      (username, self.username))
            username = self.username
        opt_ports_list = []
        if not username:
            UAS_MGR_LOGGER.warn("create_uai - missing username")
            abort(400, "Missing username.")

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
        deployment_name = 'uai-' + username + '-' + str(deployment_id)
        deployment = self.create_deployment_object(username, deployment_name,
                                                   imagename, publickey, opt_ports_list,
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
        uai_info = self.get_pod_info(deploy_resp.metadata.name, namespace)
        while not uai_info.uai_ip:
            uai_info = self.get_pod_info(deploy_resp.metadata.name, namespace)
        return uai_info

    def list_uais_for_user(self, username, namespace='default'):
        """
        Lists the UAIs for the given username.
        If username is None, it will list all UAIs.

        :param username: username of UAIs to list. If None, list all UAIs.
        :type username: str
        :return: List of UAI information.
        :rtype: list
        """
        resp = None
        uai_list = []
        # Use the username derived from the Auth token if present.
        # CASMUSER-1460 tracks making this the only allowable username
        if self.username:
            if not username == self.username:
                UAS_MGR_LOGGER.error("Username '%s' does not match "
                                     "token username '%s'" %
                                     (username, self.username))
                abort(400, "Username '%s' does not match "
                     "token username '%s'" %
                     (username, self.username))
            username = self.username
        try:
            UAS_MGR_LOGGER.info("listing deployments in namespace %s" %
                                namespace)
            resp = self.extensions_v1beta1.list_namespaced_deployment(namespace=namespace,
                                                 include_uninitialized=True)
        except ApiException as e:
            if e.status != 404:
                UAS_MGR_LOGGER.error("Failed to get deployment list")
                abort(e.status, "Failed to get deployment list")
        for deployment in resp.items:
            if not username:
                if "uas" in deployment.metadata.labels:
                    if deployment.metadata.labels['uas'] == "managed":
                        uai_list.append(self.get_pod_info(deployment.metadata.name))
            else:
                if deployment.metadata.name.startswith("uai-" + username + "-"):
                    uai_list.append(self.get_pod_info(deployment.metadata.name))
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
        if len(deployment_list) == 0:
            uai_list = self.list_uais_for_user(None)
            for uai in uai_list:
                deployment_list.append(uai.uai_name)
        for d in [d.strip() for d in deployment_list]:
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

        resp = None
        abort(501, "Not implemented")
        return resp

    def update_volume(self, volumename, type, mount_path=None, host_path=None,
                      secret_name=None, config_map=None):
        # Update the volume
        if not self.uas_cfg.is_valid_host_path_mount_type(type):
            abort(400, "Invalid type - please refer to the Kubernetes volume"
                       " documentation for valid types")

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
