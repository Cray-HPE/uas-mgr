#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#
"""
The top level Swagger Server Application for UAS Manager

"""
from etcd3_model import create_instance

version = open('.version', 'r').read().rstrip() # pylint: disable=invalid-name
ETCD_PREFIX = "/cray/uas_mgr/config"
ETCD_INSTANCE = create_instance()
