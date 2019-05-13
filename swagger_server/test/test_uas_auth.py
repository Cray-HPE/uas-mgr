#!/usr/bin/python3

import unittest

from swagger_server.uas_lib.uas_auth import UasAuth


class TestUasAuth(unittest.TestCase):

    uas_auth = UasAuth()
    uid = 1234
    gid = 4321
    username = 'hal'
    name = 'Hal Gorithm'
    loginShell = '/bin/bash'
    homeDirectory = '/users/home/hal'
    userinfo = {'sub': '60d2b60d-4d0d-4561-ac74-4b579c34fb3f',
                'loginShell': loginShell, 'email_verified': False,
                'homeDirectory': homeDirectory, 'uidNumber': uid,
                'gidNumber': gid, 'name': name,
                'preferred_username': username, 'given_name': name}

    def test_UasAuth(self):
        auth = UasAuth(endpoint='https://sms-1.craydev.com/apis/keycloak',
                       cacert='/foo')
        self.assertEqual(auth.endpoint,
                         'https://sms-1.craydev.com/apis/keycloak')
        self.assertEqual(auth.cacert, '/foo')

    def test_createPasswd(self):
        passwd = self.uas_auth.createPasswd(self.userinfo)
        self.assertEqual('hal::1234:4321:Hal Gorithm'
                         ':/users/home/hal:/bin/bash', passwd)

    def test_missingAttributes(self):
        userinfo = dict(self.userinfo)
        self.assertEqual([], self.uas_auth.missingAttributes(userinfo))
        del userinfo[self.uas_auth.uid]
        self.assertEqual([self.uas_auth.uid],
                         self.uas_auth.missingAttributes(userinfo))

if __name__ == '__main__':
    unittest.main()
