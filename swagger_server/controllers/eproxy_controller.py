import connexion
import six

from swagger_server.models.eproxy import EPROXY  # noqa: E501
from swagger_server import util


def uas_exec_eproxy(user_and_command=None):  # noqa: E501
    """Execute proxied command

    Execute command on proper service container # noqa: E501

    :param user_and_command: Execute command for username
    :type user_and_command: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        user_and_command = EPROXY.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
