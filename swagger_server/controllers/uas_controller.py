#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#
"""UAS Server Controller

"""

from flask import abort

from swagger_server import version
from swagger_server.uas_lib.uai_mgr import UaiManager
from swagger_server.uas_lib.uas_cfg import UasCfg


uas_cfg = UasCfg()  # pylint: disable=invalid-name


def create_uai(publickey=None, imagename=None, ports=None):  # noqa: E501
    """Create a new UAI for user

    Create a new UAI for the user # noqa: E501

    :param publickey: Public ssh key for the user
    :type publickey: werkzeug.datastructures.FileStorage
    :param imagename: Image to use for UAI
    :type imagename: str
    :param ports: Comma-separated list of ports to expose from the UAI
    :type imagename: str

    :rtype: UAI
    """
    uai_response = UaiManager().create_uai(publickey, imagename, ports)
    return uai_response


def delete_uai_by_name(uai_list):  # noqa: E501
    """Delete UAIs in uai_list

    Delete a list of UAIs having names in uai_list. # noqa: E501

    :param uai_list:
    :type uai_list: List[str]

    :rtype: UAI
    """
    if not uai_list:
        return "Must provide a list of UAI names to delete."
    uai_resp = UaiManager().delete_uais(uai_list)
    return uai_resp


def get_uais_for_user():  # noqa: E501
    """List all UAIs for user

    List all available UAIs for user # noqa: E501

    :rtype: List[UAI]
    """
    uai_resp = UaiManager().list_uais('')
    return uai_resp


def get_uas_images():  # noqa: E501
    """List available UAS images

    List available UAS images # noqa: E501

    :rtype: object
    """
    uas_img_info = {
        'default_image': uas_cfg.get_default_image(),
        'image_list': uas_cfg.get_images()
    }
    return uas_img_info


def get_uas_mgr_info():  # noqa: E501
    """List uas-mgr service info

    List uas-mgr service info # noqa: E501

    :rtype: object
    """
    uas_mgr_info = {
        'service_name': 'cray-uas-mgr',
        'version': version
    }
    return uas_mgr_info


def get_all_uais(username=None, host=None):  # noqa: E501
    """List all UAIs matching optional parameters

    :param username:
    :type username: str
    :param host:
    :type host: str

    :rtype: List[UAI]
    """
    label = 'uas=managed'

    if username:
        label += ',user=%s' % username

    uai_resp = UaiManager().list_uais(label, host)
    return uai_resp


def delete_all_uais(username=None):  # noqa: E501
    """Delete all UAIs

    :param username: username to delete UAIs for if specified
    :type username: str
    :rtype: UAI
    """
    uai_mgr = UaiManager()
    uai_list = []

    if username:
        for uai in uai_mgr.list_uais('uas=managed,user=%s' % username):
            uai_list.append(uai.uai_name)

    uai_resp = uai_mgr.delete_uais(uai_list)
    return uai_resp

# pylint: disable=unused-argument
def delete_uas_image_deprecated(imagename):  # noqa: E501
    """Deprecated and never implemented - see /admin/config/images/{imagename}

    Deprecated and never implemented # noqa: E501

    :param imagename:
    :type imagename: str

    :rtype: None
    """
    # This was never implemented at this path and is deprecated
    abort(501, "Not implemented")


# pylint: disable=unused-argument
def create_uas_image_deprecated(imagename, default=None):  # noqa: E501
    """Deprecated and never implemented  - see /admin/config/images

    Deprecated and never implemented # noqa: E501

    :param imagename: Image to create
    :type imagename: str

    :param default: default image (true/false)
    :type default: bool

    :rtype: object
    """
    # This was never implemented at this path and is deprecated
    abort(501, "Not implemented")


# pylint: disable=unused-argument
def update_uas_image_deprecated(imagename, default=None):  # noqa: E501
    """Deprecated and never implemented  - see /admin/config/images/{imagename}

    Deprecated and never implemented # noqa: E501

    :param imagename: Image to update
    :type imagename: str
    :param default: default image (true/false)
    :type default: bool

    :rtype: object
    """
    # This was never implemented at this path and is deprecated
    abort(501, "Not implemented")


def get_uas_image(imagename):  # noqa: E501
    """Get UAS image

    :param imagename:
    :type imagename: str

    :rtype: object
    """
    if not imagename:
        return "Must provide imagename to get."
    return UaiManager().get_image(imagename)


# pylint: disable=unused-argument
def delete_uas_volume_deprecated(volumename):  # noqa: E501
    """Deprecated and never implemented - see /admin/config/volumes/{volumename}

    Deprecated and never implemented # noqa: E501

    :param volumename:
    :type volumename: str

    :rtype: None
    """
    # This was never implemented at this path and is deprecated
    abort(501, "Not implemented")


# pylint: disable=unused-argument,redefined-builtin,too-many-arguments
def create_uas_volume_deprecated(volumename, type=None, mount_path=None,
                                 host_path=None, secret_name=None,
                                 config_map=None):  # noqa: E501
    """Deprecated and never implemented - see /admin/config/volumes

    Deprecated and never implemented # noqa: E501

    :param volumename:
    :type volumename: str

    :param type: Valid types: DirectoryOrCreate, Directory, FileOrCreate, File,
                              Socket, CharDevice, BlockDevice
    :type type: str

    :param mount_path:
    :type mount_path: str

    :param host_path:
    :type host_path: str

    :param secret_name:
    :type secret_name: str

    :param config_map:
    :type config_map: str

    :rtype: object
    """
    # This was never implemented at this path and is deprecated
    abort(501, "Not implemented")


# pylint: disable=unused-argument,redefined-builtin,too-many-arguments
def update_uas_volume_deprecated(volumename, type=None, mount_path=None,
                                 host_path=None, secret_name=None,
                                 config_map=None):  # noqa: E501
    """Deprecated and never implemented - see /admin/config/volumes/{volumename}

    Deprecated and never implemented # noqa: E501

    :param volumename:
    :type volumename: str

    :param type: Valid types: DirectoryOrCreate, Directory, FileOrCreate,
                              File, Socket, CharDevice, BlockDevice
    :type type: str

    :param mount_path:
    :type mount_path: str

    :param host_path:
    :type host_path: str

    :param secret_name:
    :type secret_name: str

    :param config_map:
    :type config_map: str

    :rtype: object
    """
    # This was never implemented at this path and is deprecated
    abort(501, "Not implemented")


# pylint: disable=unused-argument
def get_uas_volume_deprecated(volumename):  # noqa: E501
    """Deprecated and never implemented - see /admin/config/volumes/{volumename}

    :param volumename:
    :type volumename: str

    :rtype: object
    """
    # This was never implemented at this path and is deprecated
    abort(501, "Not implemented")


# pylint: disable=unused-argument
def get_uas_volumes_deprecated():  # noqa: E501
    """Deprecated and never implemented - see /admin/config/volumes

    :rtype: object
    """
    # This was never implemented at this path and is deprecated
    abort(501, "Not implemented")


# Admin API
#
# Images...
def create_uas_image_admin(imagename, default=None):  # noqa: E501
    """Add an image

    Add valid image name to configuration. Does not create or upload
    container image.  Optionally, set default.  # noqa: E501

    :param imagename: Image to create
    :type imagename: str
    :param default: default image (true/false)
    :type default: bool

    :rtype: Image

    """
    if not imagename:
        return "Must provide imagename to create."
    if default is None:
        default = False
    return UaiManager().create_image(imagename, default)


def get_uas_images_admin():  # noqa: E501
    """List UAS images

    List all available UAS images. # noqa: E501


    :rtype: Image
    """
    return UaiManager().get_images()


def get_uas_image_admin(imagename):  # noqa: E501
    """Get image info

    Get a description of the named image # noqa: E501

    :param imagename:
    :type imagename: str

    :rtype: Image
    """
    if not imagename:
        return "Must provide imagename to get."
    return UaiManager().get_image(imagename)


def update_uas_image_admin(imagename, default=None):  # noqa: E501
    """Update an image

    Update an image, specifically this can set or unset the 'default'
    flag. # noqa: E501

    :param imagename: Image to update
    :type imagename: str
    :param default: default image (true/false)
    :type default: bool

    :rtype: Image
    """
    if not imagename:
        return "Must provide imagename to update."
    return UaiManager().update_image(imagename, default)

def delete_uas_image_admin(imagename):  # noqa: E501
    """Remove the imagename from set of valid images

    Delete the named image from the set of valid UAI container
    images. # noqa: E501

    :param imagename:
    :type imagename: str

    :rtype: None

    """
    if not imagename:
        return "Must provide imagename to delete."
    return UaiManager().delete_image(imagename)

# Volumes...
def create_uas_volume_admin(volumename, mount_path,
                            volume_description):  # noqa: E501
    """Add a volume

    Add a volume to the volume list in the configuration.  The volume
    list is used during UAI creation, so this request only applies to
    UAIs subsequently created.  Modifying the volume list does not
    affect existing UAIs.  # noqa: E501

    :param volumename: Volume to create
    :type volumename: str
    :param mount_path: Mount path inside the UAI
    :type mount_path: str
    :param volume_description:
        JSON description of a Kubernetes volume to be mounted in UAI
        containers.  This is the JSON equivalent of whatever YAML you
        would normally apply to Kubernetes to attach the kind of
        volume you want to a pod.  There are many kinds of volumes,
        the examples given here illustrate some options:


          { "hostPath": { "path": "/data", "type": "DirectoryOrCreate" } }

          or

          { "secret": { "secretName": "my-secret" } }

          or

          { "configMap": { "name": "my-configmap", "items": { "key": "flaps",
            "path": "flaps" } } }
    :type volume_description: str

    :rtype: AdminVolume

    """
    if not volumename:
        return "Must provide volumename to create."
    if not mount_path:
        return "Must provide mount_path."
    if not volume_description:
        return "Must provide volume_description."
    return UaiManager().create_volume(
        volumename,
        mount_path,
        volume_description
    )


def get_uas_volumes_admin():  # noqa: E501
    """List volumes

    The volume list in the configuration is used during UAI
    creation. This list does not necessarily relate to UAIs previously
    created. This call does not affect the k8s volume itself.  # noqa: E501


    :rtype: List[AdminVolume]

    """
    return UaiManager().get_volumes()


def get_uas_volume_admin(volumename):  # noqa: E501
    """Get volume info for volumename

    Get volume info for volumename # noqa: E501

    :param volumename:
    :type volumename: str

    :rtype: AdminVolume
    """
    if not volumename:
        return "Must provide volumename to get."
    return UaiManager().get_volume(volumename)


def update_uas_volume_admin(volumename, mount_path=None,
                            volume_description=None):  # noqa: E501
    """Update a volume

    Update a volume to be mounted in UAS images. This has no effect on
    running UAIs and does not change the volume itself in any way, but
    it can modify the relationship between future UAI containers and
    the volume.  # noqa: E501

    :param volumename: Volume to update
    :type volumename: str
    :param mount_path: Mount path inside the UAI
    :type mount_path: str
    :param volume_description:
        JSON description of a Kubernetes volume to be mounted in UAI
        containers.  This is the JSON equivalent of whatever YAML you
        would normally apply to Kubernetes to attach the kind of
        volume you want to a pod.  There are many kinds of volumes,
        the examples given here illustrate some options:


          { "hostPath": { "path": "/data", "type": "DirectoryOrCreate" } }

          or

          { "secret": { "secretName": "my-secret" } }

          or

          { "configMap": { "name": "my-configmap", "items": { "key": "flaps",
            "path": "flaps" } } }
    :type volume_description: str

    :rtype: AdminVolume

    """
    if not volumename:
        return "Must provide volumename to update."
    return UaiManager().update_volume(
        volumename,
        mount_path,
        volume_description
    )


def delete_uas_volume_admin(volumename):  # noqa: E501
    """Remove volume from the volume list

    Does not affect existing UAIs. Remove the volume from the list of
    valid volumes. The actual volume itself is not affected in any
    way.  # noqa: E501

    :param volumename:
    :type volumename: str

    :rtype: None

    """
    if not volumename:
        return "Must provide volumename to delete."
    return UaiManager().delete_volume(volumename)
