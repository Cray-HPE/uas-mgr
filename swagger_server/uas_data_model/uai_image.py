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
    imageid = Etcd3Attr(is_object_id=True)  # Read-only after creation

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

    # The orverridden method here has 'object_id' instead of
    # 'imagename' in the second parameter.  Not something I care about
    # here (though I see why it might be a problem for KW arg calls).
    # Silencing the lint warning for that.
    #
    # pylint: disable=arguments-differ
    @classmethod
    def get(cls, imagename):
        """For images, the service wants to look them up by name not by id,
        and I am okay with that, though it costs a bit here and we
        aren't using the full power of 'etcd3-model'.  In reality we
        aren't going to be looking at tens of thousands of images, so
        searching is not too much of a problem.  This overrides the
        'etcd3-model' get which would be by image_id and returns the
        image config requested or None.

        """
        imgs = super().get_all()
        img_dict = {img.imagename: img for img in imgs}
        return img_dict.get(imagename, None)
