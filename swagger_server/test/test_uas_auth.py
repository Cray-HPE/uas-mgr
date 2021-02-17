#!/usr/bin/python3

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
#
# pylint: disable=missing-docstring

import json
import unittest
from unittest import mock

import requests
import werkzeug

from swagger_server.uas_lib.uas_auth import UasAuth

host = 'shasta.grapenehi.dev.cray.com'  # pylint: disable=invalid-name

class TestUasAuth(unittest.TestCase):
    """Tester for the UasAuth Class

    """
    uas_auth = UasAuth()
    uid = 1234
    gid = 4321
    username = 'hal'
    name = 'Hal Gorithm'
    loginShell = '/bin/bash'
    homeDirectory = '/users/home/hal'
    userinfo = {
        'sub': '60d2b60d-4d0d-4561-ac74-4b579c34fb3f',
        'loginShell': loginShell,
        'email_verified': False,
        'homeDirectory': homeDirectory,
        'uidNumber': uid,
        'gidNumber': gid,
        'name': name,
        'preferred_username': username,
        'given_name': name
    }

    # pylint: disable=missing-docstring,invalid-name
    def test_UasAuth(self):
        auth = UasAuth(endpoint='https://sms-1.craydev.com/apis/keycloak',
                       cacert='/foo')
        self.assertEqual(auth.endpoint,
                         'https://sms-1.craydev.com/apis/keycloak')
        self.assertEqual(auth.cacert, '/foo')

    # pylint: disable=missing-docstring,invalid-name
    def test_createPasswd(self):
        passwd = self.uas_auth.createPasswd(self.userinfo)
        self.assertEqual('hal::1234:4321:Hal Gorithm'
                         ':/users/home/hal:/bin/bash', passwd)

    # pylint: disable=missing-docstring,invalid-name
    def test_missingAttributes(self):
        userinfo = dict(self.userinfo)
        self.assertEqual([], self.uas_auth.missingAttributes(userinfo))
        del userinfo[self.uas_auth.uid]
        self.assertEqual([self.uas_auth.uid],
                         self.uas_auth.missingAttributes(userinfo))

    # pylint: disable=missing-docstring,invalid-name
    def test_validUserinfo(self):
        userinfo = dict(self.userinfo)
        self.assertEqual(True, self.uas_auth.validUserinfo(userinfo))
        del userinfo[self.uas_auth.uid]
        self.assertEqual(False,
                         self.uas_auth.validUserinfo(userinfo))

    # pylint: disable=missing-docstring
    def test_user_info(self):
        auth = UasAuth(endpoint='http://localhost', cacert='/foo')
        with self.assertRaises(werkzeug.exceptions.InternalServerError):
            auth.userinfo(host=host, token="myawesometoken")
        with self.assertRaises(werkzeug.exceptions.InternalServerError):
            auth.userinfo(host=host, token=None)
        with self.assertRaises(werkzeug.exceptions.InternalServerError):
            auth.userinfo(host=host, token="")


@mock.patch("swagger_server.uas_lib.uas_auth.UAS_AUTH_LOGGER")
@mock.patch("swagger_server.uas_lib.uas_auth.requests.post")
class TestKeycloakErrorLogging(unittest.TestCase):
    """ Keycloak error logging tester class """
    def test_timeout(self, mock_post, mock_logger):
        """Ensure we properly catch timeout exceptions."""
        mock_post.side_effect = requests.exceptions.Timeout()

        auth = UasAuth(
            endpoint="https://sms-1.craydev.com/apis/keycloak", cacert="/foo"
        )
        with self.assertRaises(werkzeug.exceptions.InternalServerError):
            auth.userinfo(host=host, token="")
        mock_logger.error.assert_called_with(
            mock.ANY,
            "Timeout",
            mock_post.side_effect
        )

    def test_connection_error(self, mock_post, mock_logger):
        """Ensure we properly catch connection errors."""
        mock_post.side_effect = requests.exceptions.ConnectionError()

        auth = UasAuth(
            endpoint="https://sms-1.craydev.com/apis/keycloak", cacert="/foo"
        )
        with self.assertRaises(werkzeug.exceptions.InternalServerError):
            auth.userinfo(host=host, token="")
        mock_logger.error.assert_called_with(
            mock.ANY, "ConnectionError", mock_post.side_effect
        )

    # pylint: disable=unused-argument
    def tests_requests(self, mock_post, mock_logger):
        """Tests the requests behavior.

        Ensure that requests is working how we expect. This doesn't
        directly test uas-mgr code. It tests assumptions that are made
        about the implementation of requests.

        """
        resp = requests.Response()
        resp.status_code = 500  # Simulate an error being returned
        with self.assertRaises(requests.exceptions.HTTPError):
            resp.raise_for_status()

        # Empty content raises an exception
        with self.assertRaises(json.decoder.JSONDecodeError):
            resp.json()

        # Broken content raises an exception
        # pylint: disable=protected-access
        resp._content = b"{"
        with self.assertRaises(json.decoder.JSONDecodeError):
            resp.json()

        # Correct content works as expected
        # pylint: disable=protected-access
        resp._content = b'{"status": "success"}'
        assert resp.json() == {"status": "success"}

        # Status code ends up on the string output for the log
        try:
            resp.raise_for_status()
        except Exception as err:  # pylint: disable=broad-except
            assert "500" in str(err)

    def test_500(self, mock_post, mock_logger):
        """Ensure a 500 response is handled properly.

        In requests the 500 responses are not raises as exceptions by default.
        """
        mock_post.return_value = requests.Response()
        mock_post.return_value.status_code = 500

        auth = UasAuth(
            endpoint="https://sms-1.craydev.com/apis/keycloak", cacert="/foo"
        )
        with self.assertRaises(werkzeug.exceptions.InternalServerError):
            auth.userinfo(host=host, token="")
        mock_logger.error.assert_called_with(mock.ANY, "HTTPError", mock.ANY)
        assert isinstance(
            mock_logger.error.call_args[0][-1], requests.exceptions.HTTPError
        )

    def test_404(self, mock_post, mock_logger):
        """Ensure a 404 response is handled properly.

        In requests the 404 responses are not raises as exceptions by default.
        """
        mock_post.return_value = requests.Response()
        mock_post.return_value.status_code = 404

        auth = UasAuth(
            endpoint="https://sms-1.craydev.com/apis/keycloak", cacert="/foo"
        )
        with self.assertRaises(werkzeug.exceptions.InternalServerError):
            auth.userinfo(host=host, token="")
        mock_logger.error.assert_called_with(mock.ANY, "HTTPError", mock.ANY)
        assert isinstance(
            mock_logger.error.call_args[0][-1], requests.exceptions.HTTPError
        )

    def test_invalid_json_returned(self, mock_post, mock_logger):
        """Ensure invalid JSON is properly handled."""
        mock_post.return_value = requests.Response()
        # pylint: disable=protected-access
        mock_post.return_value._content = b"{"
        mock_post.return_value.status_code = 200

        auth = UasAuth(
            endpoint="https://sms-1.craydev.com/apis/keycloak", cacert="/foo"
        )
        with self.assertRaises(werkzeug.exceptions.InternalServerError):
            auth.userinfo(host=host, token="")
        mock_logger.error.assert_called_with(
            mock.ANY,
            "JSONDecodeError",
            mock.ANY
        )
        assert isinstance(
            mock_logger.error.call_args[0][-1], json.decoder.JSONDecodeError
        )


if __name__ == '__main__':
    unittest.main()
