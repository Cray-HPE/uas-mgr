# Copyright 2020 Hewlett Packard Enterprise Development LP#
#
""" Logging for UAS operations.  Import `logger` from here to get logging in your code.

"""
import sys
import logging

logger = logging.getLogger('uas_mgr')
logger.setLevel(logging.INFO)
# pylint: disable=invalid-name
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
# pylint: disable=invalid-name
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

def set_log_level(level):
    """ Set the logging level to a new value.

    """
    # pylint: disable=invalid-name
    handler.setLevel(level)


def get_log_level():
    """Get the current logging level.

    """
    return handler.level
