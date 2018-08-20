# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server import util


class UAN(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, uan_name: str=None, username: str=None, usersshpubkey: str=None, uan_img: str=None, uan_ip: str=None, uan_status: str=None, uan_msg: str=None, uan_port: str=None, uan_connect_string: str=None):  # noqa: E501
        """UAN - a model defined in Swagger

        :param uan_name: The uan_name of this UAN.  # noqa: E501
        :type uan_name: str
        :param username: The username of this UAN.  # noqa: E501
        :type username: str
        :param usersshpubkey: The usersshpubkey of this UAN.  # noqa: E501
        :type usersshpubkey: str
        :param uan_img: The uan_img of this UAN.  # noqa: E501
        :type uan_img: str
        :param uan_ip: The uan_ip of this UAN.  # noqa: E501
        :type uan_ip: str
        :param uan_status: The uan_status of this UAN.  # noqa: E501
        :type uan_status: str
        :param uan_msg: The uan_msg of this UAN.  # noqa: E501
        :type uan_msg: str
        :param uan_port: The uan_port of this UAN.  # noqa: E501
        :type uan_port: str
        :param uan_connect_string: The uan_connect_string of this UAN.  # noqa: E501
        :type uan_connect_string: str
        """
        self.swagger_types = {
            'uan_name': str,
            'username': str,
            'usersshpubkey': str,
            'uan_img': str,
            'uan_ip': str,
            'uan_status': str,
            'uan_msg': str,
            'uan_port': str,
            'uan_connect_string': str
        }

        self.attribute_map = {
            'uan_name': 'uan_name',
            'username': 'username',
            'usersshpubkey': 'usersshpubkey',
            'uan_img': 'uan_img',
            'uan_ip': 'uan_ip',
            'uan_status': 'uan_status',
            'uan_msg': 'uan_msg',
            'uan_port': 'uan_port',
            'uan_connect_string': 'uan_connect_string'
        }

        self._uan_name = uan_name
        self._username = username
        self._usersshpubkey = usersshpubkey
        self._uan_img = uan_img
        self._uan_ip = uan_ip
        self._uan_status = uan_status
        self._uan_msg = uan_msg
        self._uan_port = uan_port
        self._uan_connect_string = uan_connect_string

    @classmethod
    def from_dict(cls, dikt) -> 'UAN':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The UAN of this UAN.  # noqa: E501
        :rtype: UAN
        """
        return util.deserialize_model(dikt, cls)

    @property
    def uan_name(self) -> str:
        """Gets the uan_name of this UAN.


        :return: The uan_name of this UAN.
        :rtype: str
        """
        return self._uan_name

    @uan_name.setter
    def uan_name(self, uan_name: str):
        """Sets the uan_name of this UAN.


        :param uan_name: The uan_name of this UAN.
        :type uan_name: str
        """

        self._uan_name = uan_name

    @property
    def username(self) -> str:
        """Gets the username of this UAN.


        :return: The username of this UAN.
        :rtype: str
        """
        return self._username

    @username.setter
    def username(self, username: str):
        """Sets the username of this UAN.


        :param username: The username of this UAN.
        :type username: str
        """

        self._username = username

    @property
    def usersshpubkey(self) -> str:
        """Gets the usersshpubkey of this UAN.


        :return: The usersshpubkey of this UAN.
        :rtype: str
        """
        return self._usersshpubkey

    @usersshpubkey.setter
    def usersshpubkey(self, usersshpubkey: str):
        """Sets the usersshpubkey of this UAN.


        :param usersshpubkey: The usersshpubkey of this UAN.
        :type usersshpubkey: str
        """

        self._usersshpubkey = usersshpubkey

    @property
    def uan_img(self) -> str:
        """Gets the uan_img of this UAN.


        :return: The uan_img of this UAN.
        :rtype: str
        """
        return self._uan_img

    @uan_img.setter
    def uan_img(self, uan_img: str):
        """Sets the uan_img of this UAN.


        :param uan_img: The uan_img of this UAN.
        :type uan_img: str
        """

        self._uan_img = uan_img

    @property
    def uan_ip(self) -> str:
        """Gets the uan_ip of this UAN.


        :return: The uan_ip of this UAN.
        :rtype: str
        """
        return self._uan_ip

    @uan_ip.setter
    def uan_ip(self, uan_ip: str):
        """Sets the uan_ip of this UAN.


        :param uan_ip: The uan_ip of this UAN.
        :type uan_ip: str
        """

        self._uan_ip = uan_ip

    @property
    def uan_status(self) -> str:
        """Gets the uan_status of this UAN.


        :return: The uan_status of this UAN.
        :rtype: str
        """
        return self._uan_status

    @uan_status.setter
    def uan_status(self, uan_status: str):
        """Sets the uan_status of this UAN.


        :param uan_status: The uan_status of this UAN.
        :type uan_status: str
        """

        self._uan_status = uan_status

    @property
    def uan_msg(self) -> str:
        """Gets the uan_msg of this UAN.


        :return: The uan_msg of this UAN.
        :rtype: str
        """
        return self._uan_msg

    @uan_msg.setter
    def uan_msg(self, uan_msg: str):
        """Sets the uan_msg of this UAN.


        :param uan_msg: The uan_msg of this UAN.
        :type uan_msg: str
        """

        self._uan_msg = uan_msg

    @property
    def uan_port(self) -> str:
        """Gets the uan_port of this UAN.


        :return: The uan_port of this UAN.
        :rtype: str
        """
        return self._uan_port

    @uan_port.setter
    def uan_port(self, uan_port: str):
        """Sets the uan_port of this UAN.


        :param uan_port: The uan_port of this UAN.
        :type uan_port: str
        """

        self._uan_port = uan_port

    @property
    def uan_connect_string(self) -> str:
        """Gets the uan_connect_string of this UAN.


        :return: The uan_connect_string of this UAN.
        :rtype: str
        """
        return self._uan_connect_string

    @uan_connect_string.setter
    def uan_connect_string(self, uan_connect_string: str):
        """Sets the uan_connect_string of this UAN.


        :param uan_connect_string: The uan_connect_string of this UAN.
        :type uan_connect_string: str
        """

        self._uan_connect_string = uan_connect_string
