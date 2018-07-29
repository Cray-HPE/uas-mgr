# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.uan import UAN  # noqa: E501
from swagger_server.test import BaseTestCase


class TestUANController(BaseTestCase):
    """UANController integration test stubs"""

    def test_create_uan(self):
        """Test case for create_uan

        Create a new UAN for username
        """
        query_string = [('username', 'username_example'),
                        ('imagename', 'uan-default-image')]
        response = self.client.open(
            '/v1/uan',
            method='POST',
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_all_uans_for_user(self):
        """Test case for delete_all_uans_for_user

        Delete all UANs for username
        """
        response = self.client.open(
            '/v1/uans/{username}'.format(username='username_example'),
            method='DELETE',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_uan_by_id(self):
        """Test case for delete_uan_by_id

        Delete UAN with uan_id
        """
        query_string = [('uan_id', 'uan_id_example')]
        response = self.client.open(
            '/v1/uan',
            method='DELETE',
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_uan_by_id(self):
        """Test case for get_uan_by_id

        List UAN by uan_id
        """
        query_string = [('uan_id', 'uan_id_example')]
        response = self.client.open(
            '/v1/uan',
            method='GET',
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
