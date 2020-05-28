"""Data Model for Tracking Etcd3 Backed Config exists

Copyright 2020, Cray Inc. All rights reserved.

"""
from __future__ import absolute_import
from etcd3_model import (
    Etcd3Model,
    Etcd3Attr
)
from swagger_server import ETCD_PREFIX, ETCD_INSTANCE, version


#pylint: disable=too-few-public-methods
class PopulatedConfig(Etcd3Model):
    """
    A Populated Configuration Table

        Fields:
            config_name: the name of the configuration table
            kind: "PopulatedConfig"
            data_version: the data model version for this instance
    """
    etcd_instance = ETCD_INSTANCE
    model_prefix = "%s/%s" % (ETCD_PREFIX, "PopulatedConfig")

    # The Object ID used to locate each Populated Config instance
    config_name = Etcd3Attr(is_object_id=True)  # Read-only after creation

    # The kind of object that the data here represent.  Should always
    # contain "PoulatedConfig".  Protects against stray data types.
    kind = Etcd3Attr(default="PopulatedConfig")  # Read only

    # The Data Model version corresponding to this Populated Configdata.
    # Will always be equal to the UAS Manager service version version
    # under which the data were stored in ETCD.  Protects against
    # incompatible data.
    api_version = Etcd3Attr(default=version)  # Read only
