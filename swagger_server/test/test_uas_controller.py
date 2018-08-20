# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.uan import UAN  # noqa: E501
from swagger_server.test import BaseTestCase


class TestUASController(BaseTestCase):
    """UASController integration test stubs"""

    def test_create_uan(self):
        """Test case for create_uan

        Create a new UAN for username
        """
        query_string = [('username', 'username_example'),
                        ('imagename', 'uan-default-image')]
        data = dict(usersshpubkey=(BytesIO(b'some file data'), 'file.txt'))
        response = self.client.open(
            '/v1/uan',
            method='POST',
            data=data,
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_all_uans(self):
        """Test case for delete_all_uans

        Delete all UANs
        """
        response = self.client.open(
            '/v1/uans',
            method='DELETE',
            content_type='application/json')
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

    def test_delete_uan_by_name(self):
        """Test case for delete_uan_by_name

        Delete UAN with uan_name
        """
        query_string = [('uan_list', 'uan_list_example')]
        response = self.client.open(
            '/v1/uan',
            method='DELETE',
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_all_uans(self):
        """Test case for get_all_uans

        List UANs
        """
        response = self.client.open(
            '/v1/uans',
            method='GET',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_uan_by_name(self):
        """Test case for get_uan_by_name

        List UAN info by uan_name
        """
        query_string = [('uan_name', 'uan_name_example')]
        response = self.client.open(
            '/v1/uan',
            method='GET',
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_uans_for_username(self):
        """Test case for get_uans_for_username

        List all UANs for username
        """
        response = self.client.open(
            '/v1/uans/{username}'.format(username='username_example'),
            method='GET',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_uas_delete_handler(self):
        """Test case for uas_delete_handler

        Handle UAS delete form
        """
        query_string = [('uan_list', 'uan_list_example')]
        response = self.client.open(
            '/v1/uas_access',
            method='DELETE',
            content_type='application/x-www-form-urlencoded',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_uas_request_handler(self):
        """Test case for uas_request_handler

        Handle UAS request forms
        """
        data = dict(username='username_example',
                    usersshpubkey=(BytesIO(b'some file data'), 'file.txt'),
                    uas_request='uas_request_example',
                    uan_image='uan_image_example')
        response = self.client.open(
            '/v1/uas_access',
            method='POST',
            data=data,
            content_type='multipart/form-data')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_uas_request_home(self):
        """Test case for uas_request_home

        UAS home page
        """
        query_string = [('uas_request', 'uas_request_example'),
                        ('uan_list', 'uan_list_example')]
        response = self.client.open(
            '/v1/uas_access',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
