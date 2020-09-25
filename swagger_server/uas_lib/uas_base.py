#
# Copyright 2020, Cray Inc.  All Rights Reserved.
#
"""
Manages Cray User Access Node instances.
"""

import logging
import sys
from kubernetes import config, client
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from swagger_server.uas_lib.uas_cfg import UasCfg


#pylint: disable=too-few-public-methods
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
