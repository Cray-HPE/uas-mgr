#!/usr/bin/python3

# MIT License
#
# (C) Copyright [2022] Hewlett Packard Enterprise Development LP
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
import unittest
import json
from unittest import mock
from unittest.mock import mock_open
import requests
from swagger_server.uas_lib.vault import (
    get_vault_path,
    remove_vault_data,
)

# Load a map of vault URLs and responses to use for
# mocking vault requests.
vault_url_map = {}
VAULT_URLS = "swagger_server/test/vault_urls.json"
with open(VAULT_URLS, 'r', encoding='utf-8') as vault_file:
    vault_url_map = json.loads(vault_file.read())


class MockResponse:  # pylint: disable=too-few-public-methods
    """Mock Requests Response Class.

    """
    def __init__(self, json_data, status_code, url):
        self.json_data = json_data
        self.status_code = status_code
        self.url = url

    def json(self):
        return self.json_data

    def raise_for_status(self):
        # Kind of cheating, but the failure codes we are going to see are
        # 400s and 500s
        if self.status_code > 399:
            msg = "failure: status=%d, url=%s" % (self.status_code, self.url)
            raise requests.exceptions.RequestException(msg)


# This will be used by the mock to replace requests.get
def mocked_requests_get(*args, **kwargs):
    url = args[0]
    nodata = {"errors": []}
    match = vault_url_map['get'].get(url, None)
    if match is None:
        return MockResponse(None, 404, url)
    response = match["response"]
    if "params" in match and "params" in kwargs:
        response = (
            match["response"] if match["params"] == match["params"]
            else nodata
        )
    return MockResponse(response, 200, url)


# This will be used by the mock to replace requests.post
def mocked_requests_post(*args, **kwargs):
    url = args[0]
    match = vault_url_map['post'].get(url, None)
    if match is None:
        return MockResponse(None, 404, url)
    if 'data' not in kwargs or kwargs['data']['jwt'] != "VALID SA TOKEN":
        return MockResponse({"errors":["not a compact JWS"]}, 505, url)
    return MockResponse(match["response"], 200, url)


# This will be used by the mock to replace requests.delete
#
#  pylint: disable=unused-argument,unused-private-member,no-self-use
def mocked_requests_delete(*args, **kwargs):
    return MockResponse(None, 204, args[0])


class TestVault(unittest.TestCase):
    """Tester for the Vault Package

    """
    def test_get_vault_path(self):
        """Verify that the getVaultPath() function returns the correct
        path for the specified class ID.

        """
        test_path = get_vault_path("my-class-id")
        self.assertEqual(test_path, "secret/broker-uai/my-class-id")

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    @mock.patch('requests.post', side_effect=mocked_requests_post)
    @mock.patch('requests.delete', side_effect=mocked_requests_delete)
    @mock.patch('builtins.open', mock_open(read_data="VALID SA TOKEN"))
    #pylint: disable=no-self-use,unused-argument
    def test_remove_vault_data(self, m_get, m_post, m_delete):
        """Verify that the happy path for removing data from vault doesn't
        crash.  It can fail, because there is very little checking inside to
        make sure it doesn't, but it shouldn't crash.

        """
        remove_vault_data("90328aa4-7628-40d9-8a98-6589d794b782")

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    @mock.patch('requests.post', side_effect=mocked_requests_post)
    @mock.patch('requests.delete', side_effect=mocked_requests_delete)
    @mock.patch('builtins.open', mock_open(read_data="VALID SA TOKEN"))
    #pylint: disable=no-self-use,unused-argument
    def test_remove_vault_data_bad_path(self, m_get, m_post, m_delete):
        """Verify that the case where we pass a non-existent path to vault
        when removing data doesn't crash.  It can fail, because there
        is very little checking inside to make sure it doesn't, but it
        shouldn't crash.

        """
        remove_vault_data("90328aa4-7628-40d9-8a98-6589d794b782")

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    @mock.patch('requests.post', side_effect=mocked_requests_post)
    @mock.patch('requests.delete', side_effect=mocked_requests_delete)
    @mock.patch('builtins.open', mock_open(read_data="INVALID SA TOKEN"))
    # pylint: disable=no-self-use,unused-argument
    def test_remove_vault_data_bad_sa_token(self, m_get, m_post, m_delete):
        """Verify that the case where we can't log into vault when removing
        data doesn't crash.  It can fail, because there is very little
        checking inside to make sure it doesn't, but it shouldn't
        crash.

        """
        remove_vault_data("90328aa4-7628-40d9-8a98-6589d794b782")
