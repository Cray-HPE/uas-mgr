import connexion
import six

from swagger_server.models.versions import Versions  # noqa: E501
from swagger_server import util


def root_get():  # noqa: E501
    """List supported UAS API versions

    Returns supported UAS API versions # noqa: E501


    :rtype: Versions
    """
    return 'do some magic!'
