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
"""Data Model for Tracking Etcd3 Backed Config exists
"""
from __future__ import absolute_import
from etcd3_model import (
    Etcd3Model,
    Etcd3Attr
)
from swagger_server import ETCD_PREFIX, ETCD_INSTANCE, version


#pylint: disable=too-few-public-methods
class PopulatedConfig(Etcd3Model):
    """
    A Populated Configuration Table

        Fields:
            config_name: the name of the configuration table
            kind: "PopulatedConfig"
            data_version: the data model version for this instance
    """
    etcd_instance = ETCD_INSTANCE
    model_prefix = "%s/%s" % (ETCD_PREFIX, "PopulatedConfig")

    # The kind of object that the data here represent.  Should always
    # contain "PoulatedConfig".  Protects against stray data types.
    kind = Etcd3Attr(default="PopulatedConfig")  # Read only

    # The Data Model version corresponding to this Populated Configdata.
    # Will always be equal to the UAS Manager service version version
    # under which the data were stored in ETCD.  Protects against
    # incompatible data.
    api_version = Etcd3Attr(default=version)  # Read only

    # The configuration object name stored in etcd
    config_name = Etcd3Attr(is_object_id=True)  # Read-only
