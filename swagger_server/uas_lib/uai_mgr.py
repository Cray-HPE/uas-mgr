#
# Copyright 2018, Cray Inc.  All Rights Reserved.
#
"""
Class that implements UAS operations that require user attributes
"""

import time
import uuid
from flask import abort, request
from kubernetes.client.rest import ApiException
from swagger_server.uas_lib.uas_base import UasBase
from swagger_server.uas_lib.uas_auth import UasAuth

# picking 40 seconds so that it's under the gateway timeout
UAI_IP_TIMEOUT = 40


class UaiManager(UasBase):
    """UAI Manager - manages UAI resources and allocates and controls UAIs

    """
    def __init__(self):
        """ Constructor """
        UasBase.__init__(self)
        self.passwd = None
        self.username = None
        self.check_authorization()

    def check_authorization(self):
        """Check authorization based on request headers for the requested
        action and extract user credentials to for use in UAIs.

        """
        if 'Authorization' in request.headers:
            uas_auth = UasAuth()
            userinfo = uas_auth.userinfo(
                request.headers['Host'],
                request.headers['Authorization']
            )
            if uas_auth.validUserinfo(userinfo):
                self.passwd = uas_auth.createPasswd(userinfo)
                self.username = userinfo[uas_auth.username]
                self.logger.info("UAS request for: %s", self.username)
            else:
                missing = uas_auth.missingAttributes(userinfo)
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

    # pylint: disable=too-many-branches,too-many-statements,too-many-locals
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
            self.username,
            imagename,
            public_key_str,
            self.passwd,
            opt_ports_list
        )
        # Create a service for the UAI
        uas_ssh_svc_name = deployment_name + '-ssh'
        uas_ssh_svc = self.create_service_object(
            uas_ssh_svc_name,
            "ssh",
            opt_ports_list,
            deployment_name,
            self.username
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
