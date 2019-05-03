#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#
# Description:
#   Authentication methods for cray-uas-mgr
#

import requests
import logging
import sys

from flask import abort

UAS_AUTH_LOGGER = logging.getLogger('uas_auth')
UAS_AUTH_LOGGER.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s"
                              " - %(message)s")
handler.setFormatter(formatter)
UAS_AUTH_LOGGER.addHandler(handler)

class UasAuth(object):

    """
    The UasAuth class makes requests to Keycloak with a user's 
    JWT to find information like uid, gid, home directory, and
    preferred shell.
    """

    def __init__(self, cacert='/mnt/ca-vol/certificate_authority.crt',
                 endpoint='https://api-gw-service-nmn.local/keycloak/realms/shasta/protocol/openid-connect/userinfo'):

        self.cacert = cacert
        self.endpoint = endpoint

    def authError(self, err, type, e):

        UAS_MGR_LOGGER.error('UasAuth %s:%s', type, e)
        abort(err, 'UasAuth %s: %s' % type, e)

    def createPasswd(self, uid, gid, username, name, homeDirectory, loginShell):

        fmt = '%s::%s:%s:%s:%s:%s'
        return fmt % (username, uid, gid, name, homeDirectory, loginShell)

    def validateUserinfo(self, userinfo):

        attributes = ['uidNumber', 'gidNumber', 'preferred_username', 'homeDirectory', 'loginShell']
        if all (field in userinfo for field in attributes):
          return True
        else:
          return [False,list(set(attributes).difference(userinfo))]

    def userinfo(self, token):

        headers = {'Authorization': 'Bearer '+token}
        try:
          response = requests.post(self.endpoint, verify=self.cacert, headers=headers)
        except requests.exceptions.HTTPError as e:
          self.authError(e.response.status_code, 'HTTPError', e)
        except requests.exceptions.ConnectionError as e:
          self.authError(500, 'ConnectionError', e)
        except requests.exceptions.Timeout as e:
          self.authError(500, 'Timeout', e)
        except requests.exceptions.RequestException as e:
          self.authError(500, 'RequestException', e)

        try:
          userinfo = response.json()
        except JSONDecodeError:
          self.authError(500, 'json', 'Failed to decode /userinfo response')

        return userinfo
