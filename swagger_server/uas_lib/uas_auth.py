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
"""
Authentication methods for cray-uas-mgr
"""

import sys
import logging
import json
import requests

from flask import abort

UAS_AUTH_LOGGER = logging.getLogger('uas_auth')
UAS_AUTH_LOGGER.setLevel(logging.INFO)

# pylint: disable=invalid-name
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
# pylint: disable=invalid-name
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s"
                              " - %(message)s")
handler.setFormatter(formatter)
UAS_AUTH_LOGGER.addHandler(handler)


class UasAuth:
    """
    The UasAuth class makes requests to Keycloak with a user's
    JWT to find information like uid, gid, home directory, and
    preferred shell.
    """

    def __init__(self, cacert='/mnt/ca-vol/certificate_authority.crt',
                 endpoint='/keycloak/realms/shasta/protocol/'
                          'openid-connect/userinfo'):
        """ Constructor """
        self.cacert = cacert
        self.endpoint = endpoint
        self.uid = 'uidNumber'
        self.gid = 'gidNumber'
        self.username = 'preferred_username'
        self.name = 'name'
        self.home = 'homeDirectory'
        self.shell = 'loginShell'
        self.attributes = [self.uid, self.gid, self.username, self.name,
                           self.home, self.shell]

    # pylint: disable=invalid-name
    @staticmethod
    def authError(status_code, exc):
        """Raise and log an authentication error

        """
        UAS_AUTH_LOGGER.error('UasAuth %s:%s', exc.__class__.__name__, exc)
        abort(status_code, 'An error was encountered while accessing Keycloak')

    # pylint: disable=invalid-name
    def createPasswd(self, userinfo):
        """Format user information into an /etc/passwd structured string.

        """
        fmt = '%s::%s:%s:%s:%s:%s'
        return fmt % (userinfo[self.username], userinfo[self.uid],
                      userinfo[self.gid], userinfo[self.name],
                      userinfo[self.home], userinfo[self.shell])

    # pylint: disable=invalid-name
    def validUserinfo(self, userinfo):
        """Verify that the specified user informatino is complete.

        """
        if all(field in userinfo for field in self.attributes):
            return True
        return False

    # pylint: disable=invalid-name
    def missingAttributes(self, userinfo):
        """Detect and list missing attributes in the specified user
        information.

        """
        return list(set(self.attributes).difference(userinfo))

    def userinfo(self, host, token):
        """Get user information from the specified host using the specified
        auth token.

        """
        headers = {'Authorization': token}
        url = 'https://' + host + self.endpoint
        try:
            response = requests.post(url, verify=self.cacert,
                                     headers=headers)
            # raise exception for 4XX and 5XX errors
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            UAS_AUTH_LOGGER.error("%r %r", type(e), e)
            status_code = e.response.status_code if e.response else 500
            self.authError(status_code, e)
        except Exception as e:  # pylint: disable=broad-except
            self.authError(500, e)

        try:
            userinfo = response.json()
        except json.decoder.JSONDecodeError as e:
            self.authError(500, e)

        if self.username in userinfo:
            UAS_AUTH_LOGGER.info(
                "UasAuth lookup complete for user %s",
                userinfo[self.username]
            )
        return userinfo
