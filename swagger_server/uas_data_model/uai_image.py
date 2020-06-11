"""Data Model for UAI Images

Copyright 2020, Cray Inc. All rights reserved.

"""
from __future__ import absolute_import
from etcd3_model import Etcd3Attr
from swagger_server import ETCD_INSTANCE, ETCD_PREFIX, version
from swagger_server.uas_data_model.uas_data_model import UASDataModel


#pylint: disable=too-few-public-methods
class UAIImage(UASDataModel):
    """
    UAI Image Data Model

        Fields:
            imagename: the name of the docker image (string)
            kind: "UAIImage"
            data_version: the data model version for this instance
            default: whether or not this is the default image to use
                     for a UAI (boolean)
    """
    etcd_instance = ETCD_INSTANCE
    model_prefix = "%s/%s" % (ETCD_PREFIX, "UAIImage")

    # The Object ID used to locate each UAI Image instance
    image_id = Etcd3Attr(is_object_id=True)  # Read-only after creation

    # The kind of object that the data here represent.  Should always
    # contain "UAIImage".  Protects against stray data
    # types.
    kind = Etcd3Attr(default="UAIImage")  # Read only

    # The Data Model version corresponding to this UAI Image's data.
    # Will always be equal to the UAS Manager service version version
    # under which the data were stored in ETCD.  Protects against
    # incompatible data.
    api_version = Etcd3Attr(default=version)  # Read only

    # The image name for the image
    imagename = Etcd3Attr(default=None)

    # Is this the default image to be used for UAIs?
    default = Etcd3Attr(default=False)

    @classmethod
    def get_by_name(cls, imagename):
        """Query images by name.  If an image of the given name exists,
        return it, otherwise return None.

        """
        imgs = cls.get_all()
        img_dict = {img.imagename: img for img in imgs}
        return img_dict.get(imagename, None)
