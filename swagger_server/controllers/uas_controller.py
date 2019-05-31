#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#

from swagger_server import version
from swagger_server.uas_lib.uai_mgr import UaiManager
from swagger_server.uas_lib.uas_cfg import UasCfg


uas_cfg = UasCfg()


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
    uai_mgr = UaiManager()
    uai_response = uai_mgr.create_uai(publickey, imagename, ports)
    return uai_response


def delete_uai_by_name(uai_list):  # noqa: E501
    """Delete UAIs in uai_list

    Delete a list of UAIs having names in uai_list. # noqa: E501

    :param uai_list:
    :type uai_list: List[str]

    :rtype: UAI
    """
    if len(uai_list) == 0:
        return "Must provide a list of UAI names to delete."
    uai_mgr = UaiManager()
    uai_resp = uai_mgr.delete_uais(uai_list)
    return uai_resp


def get_uais_for_user():  # noqa: E501
    """List all UAIs for user

    List all available UAIs for user # noqa: E501

    :rtype: List[UAI]
    """
    uai_mgr = UaiManager()
    uai_resp = uai_mgr.list_uais('')
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


def get_all_uais():  # noqa: E501
    """List all UAIs
    :rtype: List[UAI]
    """
    uai_mgr = UaiManager()
    uai_resp = uai_mgr.list_uais('uas=managed')
    return uai_resp


def delete_all_uais():  # noqa: E501
    """Delete all UAIs
    :rtype: UAI
    """
    uai_list = []
    uai_mgr = UaiManager()
    uai_resp = uai_mgr.delete_uais(uai_list)
    return uai_resp


def delete_uas_image(imagename):  # noqa: E501
    """Delete UAS image

    :param imagename:
    :type imagename: str

    :rtype: object
    """
    if not imagename:
        return "Must provide imagename to delete."
    uai_mgr = UaiManager()
    return uai_mgr.delete_image(imagename)


def create_uas_image(imagename, default):  # noqa: E501
    """Create UAS image

    :param imagename:
    :type imagename: str

    :param default:
    :type default: bool

    :rtype: object
    """
    if not imagename:
        return "Must provide imagename to create."
    if not default:
        return "Must provide true/false for default image."
    uai_mgr = UaiManager()
    return uai_mgr.create_image(imagename, default)


def update_uas_image(imagename, default):  # noqa: E501
    """Update UAS image

    :param imagename:
    :type imagename: str

    :param default:
    :type default: bool

    :rtype: object
    """
    if not imagename:
        return "Must provide imagename to update."
    if not default:
        return "Must provide true/false for default image."
    uai_mgr = UaiManager()
    return uai_mgr.update_image(imagename, default)


def get_uas_image(imagename):  # noqa: E501
    """Get UAS image

    :param imagename:
    :type imagename: str

    :rtype: object
    """
    if not imagename:
        return "Must provide imagename to get."
    uai_mgr = UaiManager()
    return uai_mgr.get_image(imagename)


def delete_uas_volume(volumename):  # noqa: E501
    """Delete UAS volume

    :param volumename:
    :type volumename: str

    :rtype: object
    """
    if not volumename:
        return "Must provide volumename to delete."
    uai_mgr = UaiManager()
    return uai_mgr.delete_volume(volumename)


def create_uas_volume(volumename, type, mount_path=None, host_path=None,
                      secret_name=None, config_map=None):  # noqa: E501
    """Create UAS volume

    :param volumename:
    :type volumename: str

    :param type:
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
    if not volumename:
        return "Must provide volumename to create."
    if not type:
        return "Must provide type to create."
    uai_mgr = UaiManager()
    return uai_mgr.create_volume(volumename, type, mount_path, host_path,
                                 secret_name, config_map)


def update_uas_volume(volumename, type, mount_path=None, host_path=None,
                      secret_name=None, config_map=None):  # noqa: E501
    """Update UAS volume

    :param volumename:
    :type volumename: str

    :param type:
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
    if not volumename:
        return "Must provide volumename to update."
    if not type:
        return "Must provide type to update."
    uai_mgr = UaiManager()
    return uai_mgr.update_volume(volumename, type, mount_path, host_path,
                                 secret_name, config_map)


def get_uas_volume(volumename):  # noqa: E501
    """Get UAS volume

    :param volumename:
    :type volumename: str

    :rtype: object
    """
    if not volumename:
        return "Must provide volumename to get."
    uai_mgr = UaiManager()
    return uai_mgr.get_volume(volumename)


def get_uas_volumes():  # noqa: E501
    """Get all volumes

    :rtype: object
    """
    uai_mgr = UaiManager()
    return uai_mgr.get_volumes()
