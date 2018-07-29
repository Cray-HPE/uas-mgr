# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.eproxy import EPROXY  # noqa: E501
from swagger_server.test import BaseTestCase


class TestEPROXYController(BaseTestCase):
    """EPROXYController integration test stubs"""

    def test_uas_exec_eproxy(self):
        """Test case for uas_exec_eproxy

        Execute proxied command
        """
        user_and_command = EPROXY()
        response = self.client.open(
            '/v1/eproxy',
            method='POST',
            data=json.dumps(user_and_command),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
