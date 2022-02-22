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
""" Vault operations to support managing shared secrets associated with UAI
Classes.

"""

import os
import json
import requests
from swagger_server.uas_lib.uas_logging import logger


def get_vault_path(uai_class_id):
    """Compute and return the path within vault used by Broker UAIs to
       store keys and other data pertaining to UAIs of the specified
       UAI Class.

    """
    return os.path.join("secret/broker-uai", uai_class_id)


def remove_vault_data(uai_class_id):
    """Remove all Broker UAI data from vault pertaining to the specified
       UAI class.
    """
    client_token = __vault_authenticate()
    if client_token is None:
        return
    __remove_vault_subtree(get_vault_path(uai_class_id), client_token)


def __vault_authenticate():
    """Authenticate with vault using the namespace service account for this
    pod.

    """
    sa_token_file = "/run/secrets/kubernetes.io/serviceaccount/token"
    login_url = "http://cray-vault.vault:8200/v1/auth/kubernetes/login"
    with open(sa_token_file, 'r', encoding='utf-8') as token_file:
        sa_token = token_file.read()
    login_payload = {
        'jwt': sa_token,
        'role': "services"
    }
    try:
        response = requests.post(login_url, data=login_payload)
            # raise exception for 4XX and 5XX errors
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        logger.warning(
            "authentication with vault failed, "
            "secrets won't be cleaned up - %s",
            str(err)
        )
        return None
    try:
        token_data = response.json()
    except json.decoder.JSONDecodeError as err:
        logger.warning(
            "authentication with vault could not decode auth token, "
            "secrets won't be cleaned up - %s",
            str(err)
        )
        return None
    auth = token_data.get('auth', {})
    token = auth.get('client_token', None)
    if token is None:
        logger.warning(
            "authentication with vault returned no token "
            "secrets won't be cleaned up."
        )
    return token


def __get_vault_children(path, client_token):
    """Retrieve the children (sub-paths) found at a given path in vault.
    One layer deep.

    """
    print("get_vault_children: %s" % path)
    headers = {"X-Vault-Token": "%s" % client_token }
    url = os.path.join("http://cray-vault.vault:8200/v1", path)
    params = {"list": "true"}
    try:
        response = requests.get(url, headers=headers, params=params)
            # raise exception for 4XX and 5XX errors
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        logger.warning(
            "getting children at vault path '%s' failed - %s",
            path,
            str(err)
        )
    try:
        child_data = response.json()
    except json.decoder.JSONDecodeError as err:
        logger.warning(
            "decoding JSON with children at path '%s'  failed - %s",
            path,
            str(err)
        )
    data = child_data.get('data', {})
    return data.get('keys', [])


def __delete_vault_path(path, client_token):
    """Delete a single node from vault at the specified path.

    """
    print("delete_vault_path: %s" % path)
    logger.debug("removing vault path '%s'", path)
    headers = {"X-Vault-Token": "%s" % client_token }
    url = os.path.join("http://cray-vault.vault:8200/v1", path)
    try:
        response = requests.delete(url, headers=headers)
            # raise exception for 4XX and 5XX errors
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        logger.warning(
            "deleting vault secret or node at path '%s' failed - %s",
            path,
            str(err)
        )


def __remove_vault_subtree(path, client_token):
    """Recursively remove the tree found at the specified path in vault.

    """
    print("remove_vault_subtree: '%s'" % path)
    # Depth first, remove the kids...
    for child in __get_vault_children(path, client_token):
        child_path = os.path.join(path, child)
        __remove_vault_subtree(child_path, client_token)
    __delete_vault_path(path, client_token)
