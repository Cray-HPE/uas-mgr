# MIT License
#
# (C) Copyright [2020-2022] Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
"""
Class that implements UAS operations that require user attributes
"""

import random
from flask import abort, request
from swagger_server.uas_lib.uas_logging import logger
from swagger_server.uas_lib.uas_base import UasBase
from swagger_server.uas_lib.uai_instance import UAIInstance
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


    def construct_uai_class(self, imagename, namespace, opt_ports):
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
            # pylint: disable=no-member
            volume_list = [ vol.volume_id for vol in volumes]
            uai_class = UAIClass(
                comment=None,
                default=False,
                public_ip=True,
                image_id=image_id,
                resource_id=None,
                volume_list=volume_list,
                namespace=namespace,
                opt_ports=opt_ports,
                tolerations=None,
                timeout=None,
                service_account=None,
                replicas=1
            )
        elif imagename is not None:
            abort(
                400,
                "imagename cannot be specified when a default "
                "UAI Class is defined"
            )
        return uai_class

    # pylint: disable=too-many-branches,too-many-statements,too-many-locals
    def create_uai(self, public_key, imagename, opt_ports, uai_name):
        """Create a new UAI

        """
        logger.debug(
            "creating a new UAI, legacy mode, public_key = %s, "
            "image_name = %s, opt_port = %s, uai_name = '%s'",
            public_key, imagename, opt_ports, uai_name
        )
        if not public_key:
            logger.warning("create_uai - missing public key")
            abort(400, "Missing ssh public key.")
        namespace = self.uas_cfg.get_uai_namespace()
        opt_ports_list = [
            port.strip()
            for port in opt_ports.split(',')
        ] if opt_ports else []
        try:
            _ = [int(port) for port in opt_ports_list]
        except ValueError:
            abort(
                400,
                "illegal port number in '%s', "
                "all optional port values must be integers"
                % (opt_ports)
            )
        # Restrict ports to valid_ports
        if opt_ports_list:
            for port in opt_ports_list:
                if int(port) not in self.uas_cfg.get_valid_optional_ports():
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
        uai_class = self.construct_uai_class(imagename, namespace, opt_ports_list)
        uai_instance = UAIInstance(
            owner=self.username,
            public_key=public_key,
            passwd_str=self.passwd,
            uai_name=uai_name
        )
        ret = self.deploy_uai(uai_class, uai_instance, self.uas_cfg)
        logger.debug("created UAI (legacy mode): %s", ret)
        return ret


    def list_uais(self, label=None, host=None):
        """
        Lists the UAIs based on a label and/or field selector and namespace

        :param label: Label selector. If empty, use self.username
        :param host: Used to select pods by host, if set,
            If unset, the default of None will select all.
        :return: List of UAI information.
        :rtype: list
        """
        logger.debug("listing UAIs legacy mode")
        if not label:
            labels = ['user=%s' % self.username]
        else:
            labels = label.split(',')
        job_names = self.select_jobs(
            labels=labels,
            host=host,
        )
        ret = self.get_uai_list(job_names=job_names)
        logger.debug("Got UAI list (legacy mode): %s", ret)
        return ret

    def delete_uais(self, job_list):
        """
        Deletes the UAIs named in job_list.
        If job_list is empty, it will delete all UAIs.

        :param job_list: List of UAI names to delete.
                                If empty, delete all UAIs.
        :type job_list: list
        :return: List of UAIs deleted.
        :rtype: list
        """
        logger.debug(
            "deleting UAIs legacy mode job_list = %s",
            job_list
        )
        uai_list = []
        if not job_list:
            uai_list = self.select_jobs()
        else:
            user_uais = self.select_jobs(
                labels=["user=%s" % self.username]
            )
            uai_list = [
                uai.strip() for uai in job_list
                if uai.strip() in user_uais
            ]
        resp_list = self.remove_uais(uai_list)
        logger.debug("deleted UAIs legacy mode: %s", resp_list)
        return resp_list

    def reap_uais(self, count=5):
        """Find up to 'count' uais that have completed and clean up their
        resources.  If there are more than 'count' UAIs to choose
        from, select them randomly from the overall list to make it
        less likely that other UAS instances are reaping the same
        UAIs.  There are no serious negative effects of collisions
        here, just inefficiency.

        """
        uai_list = self.select_jobs(fields=["status.successful!=0"])
        count = len(uai_list) if len(uai_list) < count else count
        random.sample(uai_list, count)
        resp_list = self.remove_uais(uai_list)
        return resp_list
