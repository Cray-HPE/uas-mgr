"""Data Model for UAI Images

Copyright 2020 Hewlett Packard Enterprise Development LP
"""
from __future__ import absolute_import
from etcd3_model import Etcd3Attr
from swagger_server import ETCD_INSTANCE, ETCD_PREFIX, version
from swagger_server.uas_data_model.uas_data_model import UASDataModel


#pylint: disable=too-few-public-methods
class UAIResource(UASDataModel):
    """
    UAI Resource Data Model

        Fields:
            imagename: the name of the docker image (string)
            kind: "UAIImage"
            data_version: the data model version for this instance
            default: whether or not this is the default image to use
                     for a UAI (boolean)
    """
    etcd_instance = ETCD_INSTANCE
    model_prefix = "%s/%s" % (ETCD_PREFIX, "UAIResource")

    # The Object ID used to locate each UAI Resource configuration instance
    resource_id = Etcd3Attr(is_object_id=True)  # Read-only after creation

    # The kind of object that the data here represent.  Should always
    # contain "UAIResource".  Protects against stray data
    # types.
    kind = Etcd3Attr(default="UAIResource")  # Read only

    # The Data Model version corresponding to this UAI Resource's data.
    # Will always be equal to the UAS Manager service version
    # under which the data were stored in ETCD.  Protects against
    # incompatible data.
    api_version = Etcd3Attr(default=version)  # Read only

    # A comment describing what this resource configuration is used
    # for.
    comment = Etcd3Attr(default=None)

    # Resource limit JSON string, see Kubernetes documentation for
    # details.
    limit = Etcd3Attr(default=None)

    # Resource request JSON string, see Kubernetes documentation for
    # details.
    request = Etcd3Attr(default=None)

    def expand(self):
        """Produce a dictionary of the publicly viewable elements of the
        object.

        """
        return {
            'resource_id': self.resource_id,
            'comment': self.comment,
            'limit': self.limit,
            'request': self.request
        }
