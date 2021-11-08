# MIT License
#
# (C) Copyright [2020] Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
""" Logging for UAS operations.  Import `logger` from here to get logging in your code.

"""
import os
import sys
import logging

# Learn any environment setting that might be presented for logging level.  Default to
# 'info' and use 'info' if a bad setting is requested.  If a bad level is requested,
# capture the level and log it once we have logging set up.
__LEVEL_MAP = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
}
#pylint: disable=invalid-name
env_level = os.environ.get("UAS_LOGGING_LEVEL", 'info')
#pylint: disable=invalid-name
bad_env_level = None if env_level in __LEVEL_MAP else env_level
#pylint: disable=invalid-name
env_level = env_level if not bad_env_level else 'info'

# pylint: disable=invalid-name
logger = logging.getLogger('uas_mgr')
logger.setLevel(__LEVEL_MAP[env_level])
# pylint: disable=invalid-name
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(__LEVEL_MAP[env_level])
# pylint: disable=invalid-name
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Determine and log the setting of the log level so that developers can
# see if their attempts to change the log level worked and so that the
# expected level of logging will be known.
__BAD_LEVEL_LOG = (
    "UAS_LOGGING_LEVEL set to invalid log level '%s' ignoring that value "
    "and using '%s'" % (bad_env_level, env_level)
)
__GOOD_LEVEL_LOG = "setting logging level to '%s'" % env_level
__LOG_LEVEL_LOG = (
    __GOOD_LEVEL_LOG if bad_env_level is None else __BAD_LEVEL_LOG
)
logger.info(__LOG_LEVEL_LOG)

def set_log_level(level):
    """ Set the logging level to a new value.

    """
    # pylint: disable=invalid-name
    handler.setLevel(level)


def get_log_level():
    """Get the current logging level.

    """
    return handler.level
