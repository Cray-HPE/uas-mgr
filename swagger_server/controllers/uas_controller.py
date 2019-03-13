#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#

from swagger_server.models.uan import UAN  # noqa: E501
from swagger_server import version
from swagger_server.uas_lib.uan_mgr import UanManager
from swagger_server.uas_lib.uas_cfg import UasCfg


uas_cfg = UasCfg()

def create_uan(username, usersshpubkey=None, imagename=None):  # noqa: E501
    """Create a new UAN for username

    Create a new UAN for the username # noqa: E501

    :param username: Create UAN for username
    :type username: str
    :param usersshpubkey: Public ssh key for the user
    :type usersshpubkey: werkzeug.datastructures.FileStorage
    :param imagename: Image to use for UAN
    :type imagename: str

    :rtype: UAN
    """
    uan_mgr = UanManager()
    if not username:
        return "Must supply username for UAN creation."

    uan_response = uan_mgr.create_uan(username, usersshpubkey, imagename)
    return uan_response

def delete_uan_by_name(uan_list):  # noqa: E501
    """Delete UANs in uan_list

    Delete a list of UANs having names in uan_list. # noqa: E501

    :param uan_list: 
    :type uan_list: List[str]

    :rtype: UAN
    """
    uan_mgr = UanManager()
    uan_resp = uan_mgr.delete_uans(uan_list)
    return uan_resp

def get_uans_for_username(username):  # noqa: E501
    """List all UANs for username

    List all available UANs for username # noqa: E501

    :param username: 
    :type username: str

    :rtype: List[UAN]
    """
    uan_mgr = UanManager()
    uan_resp = uan_mgr.list_uans_for_user(username)
    return uan_resp

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
    :rtype: List[UAN]
    """
    username = "all_uais"
    uan_mgr = UanManager()
    uan_resp = uan_mgr.list_uans_for_user(username)
    return uan_resp

def delete_all_uais():  # noqa: E501
    """Delete all UAIs
    :rtype: UAN
    """
    uan_list = []
    uan_mgr = UanManager()
    uan_resp = uan_mgr.delete_uans(uan_list)
    return uan_resp
