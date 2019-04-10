#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#

from swagger_server.models.uai import UAI  # noqa: E501
from swagger_server import version
from swagger_server.uas_lib.uai_mgr import UaiManager
from swagger_server.uas_lib.uas_cfg import UasCfg


uas_cfg = UasCfg()

def create_uai(username, usersshpubkey=None, imagename=None):  # noqa: E501
    """Create a new UAI for username

    Create a new UAI for the username # noqa: E501

    :param username: Create UAI for username
    :type username: str
    :param usersshpubkey: Public ssh key for the user
    :type usersshpubkey: werkzeug.datastructures.FileStorage
    :param imagename: Image to use for UAI
    :type imagename: str

    :rtype: UAI
    """
    uai_mgr = UaiManager()
    if not username:
        return "Must supply username for UAI creation."

    uai_response = uai_mgr.create_uai(username, usersshpubkey, imagename)
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

def get_uais_for_username(username):  # noqa: E501
    """List all UAIs for username

    List all available UAIs for username # noqa: E501

    :param username:
    :type username: str

    :rtype: List[UAI]
    """
    if not username:
        return "Must provide username to list UAIs for user."
    uai_mgr = UaiManager()
    uai_resp = uai_mgr.list_uais_for_user(username)
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
    username = None
    uai_mgr = UaiManager()
    uai_resp = uai_mgr.list_uais_for_user(username)
    return uai_resp

def delete_all_uais():  # noqa: E501
    """Delete all UAIs
    :rtype: UAI
    """
    uai_list = []
    uai_mgr = UaiManager()
    uai_resp = uai_mgr.delete_uais(uai_list)
    return uai_resp
