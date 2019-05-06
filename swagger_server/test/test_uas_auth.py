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

    def test_UasAuth(self):
        auth = UasAuth(endpoint='https://sms-1.craydev.com/apis/keycloak', cacert='/foo')
        self.assertEqual(auth.endpoint, 'https://sms-1.craydev.com/apis/keycloak')
        self.assertEqual(auth.cacert, '/foo')

    def test_createPasswd(self):

        passwd = self.uas_auth.createPasswd(self.uid, self.gid, self.username, 
                                            self.name, self.homeDirectory, self.loginShell) 

        self.assertEqual('hal::1234:4321:Hal Gorithm:/users/home/hal:/bin/bash', passwd)

    def test_validateUserinfo(self):

        userinfo={'sub': '60d2b60d-4d0d-4561-ac74-4b579c34fb3f', 'loginShell': self.loginShell, 
                  'email_verified': False, 'homeDirectory': self.homeDirectory, 'uidNumber': self.uid, 
                  'gidNumber': self.gid, 'name': self.name, 'preferred_username': self.username, 
                  'given_name': self.name}
        
        self.assertEqual(True, self.uas_auth.validateUserinfo(userinfo))
        del userinfo['uidNumber']
        self.assertEqual([False, ['uidNumber']] , self.uas_auth.validateUserinfo(userinfo))
                         

if __name__ == '__main__':
    unittest.main()
