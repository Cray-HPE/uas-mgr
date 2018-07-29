import connexion
import six

from flask import render_template
from swagger_server.models.uan import UAN  # noqa: E501
from swagger_server import util
from swagger_server.uas_lib.uan_mgr import UanManager
from swagger_server.uas_lib.uas_dispatcher import DispatchManager


uan_mgr = UanManager()
dm = DispatchManager()

uas_dispatch = {
    'create_uan': dm.create_uan,
    'list_uans': dm.list_uans,
    'delete_uan_request': dm.delete_uan_request,
    'delete_uans': dm.delete_uans,
}


def create_uan(username, imagename=None):  # noqa: E501
    """Create a new UAN for username

    Create a new UAN for the username # noqa: E501

    :param username: Create UAN for username
    :type username: str
    :param imagename: Image to use for UAN
    :type imagename: str

    :rtype: UAN
    """
    if not username:
        return "Must supply username for UAN creation."

    uan_response = dm.uan_mgr.create_uan(username, imagename)
    return uan_response


def delete_all_uans():  # noqa: E501
    """Delete all UANs

    Delete all available UANs # noqa: E501


    :rtype: None
    """
    return 'do some magic!'


def delete_all_uans_for_user(username):  # noqa: E501
    """Delete all UANs for username

    Delete all UANs for username # noqa: E501

    :param username: 
    :type username: str

    :rtype: List[UAN]
    """
    return 'do some magic!'


def delete_uan_by_name(uan_list):  # noqa: E501
    """Delete UANs in uan_list

    Delete a list of UANs having names in uan_list. # noqa: E501

    :param uan_list: 
    :type uan_list: List[str]

    :rtype: UAN
    """
    uan_resp = dm.uan_mgr.delete_uans(uan_list)
    return uan_resp


def get_all_uans():  # noqa: E501
    """List UANs

    List all available UANs. # noqa: E501


    :rtype: List[UAN]
    """
    return 'do some magic!'


def get_uan_by_name(uan_name):  # noqa: E501
    """List UAN info by uan_name

    List UAN info by uan_name # noqa: E501

    :param uan_name: 
    :type uan_name: str

    :rtype: UAN
    """
    return 'do some magic!'


def get_uans_for_username(username):  # noqa: E501
    """List all UANs for username

    List all available UANs for username # noqa: E501

    :param username: 
    :type username: str

    :rtype: List[UAN]
    """
    uan_resp = dm.uan_mgr.list_uans_for_user(username)
    return uan_resp


def uas_delete_handler(uan_list):  # noqa: E501
    """Handle UAS delete form

    Handle form data from UAS delete page # noqa: E501

    :param uan_list: List of UANs to delete
    :type uan_list: List[str]

    :rtype: str
    """
    resp = dm.delete_uans(uan_list)
    return resp


def uas_request_handler(username=None, uas_request=None, uan_image=None):  # noqa: E501
    """Handle UAS request forms

    Handle form data from the UAS home page # noqa: E501

    :param username: Users name
    :type username: str
    :param uas_request: User request
    :type uas_request: str
    :param uan_image: User requested UAN image
    :type uan_image: str

    :rtype: str
    """
    uan_args = {'username': username, 'uas_request': uas_request,
                'uan_image': uan_image}
    return uas_dispatch[uas_request](uan_args)


def uas_request_home(uas_request=None, uan_list=None):  # noqa: E501
    """UAS home page

    Request UAS home page # noqa: E501

    :param uas_request: User request
    :type uas_request: str
    :param uan_list: List of UANs to delete
    :type uan_list: List[str]

    :rtype: str
    """
    if uas_request == 'delete_uans':
        return uas_delete_handler(uan_list)
    return render_template('index.html')
