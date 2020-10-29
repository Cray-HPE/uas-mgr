#
# Copyright 2018, Cray Inc.  All Rights Reserved.
#
"""
Class that implements UAS operations that require user attributes
"""

from flask import abort, request
from swagger_server.uas_lib.uas_logging import logger
from swagger_server.uas_lib.uas_base import UasBase
from swagger_server.uas_lib.uas_base import UAIInstance
from swagger_server.uas_lib.uas_auth import UasAuth
from swagger_server.uas_data_model.uai_image import UAIImage
from swagger_server.uas_data_model.uai_volume import UAIVolume
from swagger_server.uas_data_model.uai_class import UAIClass


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
                logger.info("UAS request for: %s", self.username)
            else:
                missing = uas_auth.missingAttributes(userinfo)
                logger.info(
                    "Token not valid for UAS. Attributes "
                    "missing: %s",
                    missing
                )
                abort(
                    400,
                    "Token not valid for UAS. Attributes "
                    "missing: %s" %  missing
                )


    def _construct_uai_class(self, imagename, namespace, opt_ports):
        """Make a UAI class on which to base a User Workflow style UAI.  This
        will use a default UAI Class if there is one, otherwise, it
        will build a temporary UAI Class on which to base the proposed
        UAI.

        """
        uai_class = UAIClass.get_default()
        if uai_class is None:
            if not imagename:
                imagename = self.uas_cfg.get_default_image()
                logger.info(
                    "create_uai - no image name provided, "
                    "using default %s",
                    imagename
                )
                if not self.uas_cfg.validate_image(imagename):
                    logger.error(
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
            image_id = UAIImage.get_by_name(imagename).image_id
            volumes = UAIVolume.get_all()
            volumes = [] if volumes is None else volumes
            volume_list = [ vol.volume_id for vol in volumes]
            uai_class = UAIClass(
                comment=None,
                default=False,
                public_ssh=True,
                image_id=image_id,
                resource_id=None,
                volume_list=volume_list,
                namespace=namespace,
                opt_ports=opt_ports
            )
        elif imagename is not None:
            abort(
                400,
                "imagename cannot be specified when a default "
                "UAI Class is defined"
            )
        return uai_class

    # pylint: disable=too-many-branches,too-many-statements,too-many-locals
    def create_uai(self, public_key, imagename, opt_ports, namespace=None):
        """Create a new UAI

        """
        opt_ports_list = []
        if not public_key:
            logger.warning("create_uai - missing public key")
            abort(400, "Missing ssh public key.")
        namespace = self.uas_cfg.get_uai_namespace()
        if opt_ports:
            opt_ports_list = [int(i) for i in opt_ports.split(',')]
        # Restrict ports to valid_ports
        if opt_ports_list:
            for port in opt_ports_list:
                if port not in self.uas_cfg.get_valid_optional_ports():
                    logger.error(
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
        uai_class = self._construct_uai_class(imagename, namespace, opt_ports_list)
        uai_instance = UAIInstance(
            owner=self.username,
            public_key=public_key,
            passwd_str=self.passwd
        )
        return self.deploy_uai(uai_class, uai_instance, self.uas_cfg)


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
        if not namespace:
            namespace = self.uas_cfg.get_uai_namespace()
            logger.info(
                "list_uais - UAI will be listed from"
                " the %s namespace.",
                namespace
            )

        if not label:
            label = 'user=' + self.username
        return self.get_uai_list(label, host, namespace)

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
        if not namespace:
            namespace = self.uas_cfg.get_uai_namespace()
            logger.info(
                "delete_uais - UAI will be deleted from"
                " the %s namespace.",
                namespace
            )

        uai_list = []
        if not deployment_list:
            for uai in self.list_uais('uas=managed'):
                uai_list.append(uai.uai_name)
        else:
            uai_list = [uai for uai in deployment_list if
                        'uai-'+self.username+'-' in uai]
        resp_list = self.remove_uais(
            [dep.strip() for dep in uai_list],
            namespace
        )
        return resp_list
