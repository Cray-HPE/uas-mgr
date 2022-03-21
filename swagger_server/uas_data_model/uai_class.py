# MIT License
#
# (C) Copyright [2020-2022] Hewlett Packard Enterprise Development LP
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
"""Data Model for UAI Classes
"""
from __future__ import absolute_import
from etcd3_model import Etcd3Attr
from swagger_server import ETCD_INSTANCE, ETCD_PREFIX, version
from swagger_server.uas_data_model.uas_data_model import UASDataModel


#pylint: disable=too-few-public-methods
class UAIClass(UASDataModel):
    """
    UAI Class Data Model

        Fields:
            imagename: the name of the docker image (string)
            kind: "UAIImage"
            data_version: the data model version for this instance
            default: whether or not this is the default image to use
                     for a UAI (boolean)
    """
    etcd_instance = ETCD_INSTANCE
    model_prefix = "%s/%s" % (ETCD_PREFIX, "UAIClass")

    # The Object ID used to locate each UAI Class configuration instance
    class_id = Etcd3Attr(is_object_id=True)  # Read-only after creation

    # The kind of object that the data here represent.  Should always
    # contain "UAIClass".  Protects against stray data
    # types.
    kind = Etcd3Attr(default="UAIClass")  # Read only

    # The Data Model version corresponding to this UAI Class's data.
    # Will always be equal to the UAS Manager service version
    # under which the data were stored in ETCD.  Protects against
    # incompatible data.
    api_version = Etcd3Attr(default=version)  # Read only

    # A comment describing what this UAI Class is used for.
    comment = Etcd3Attr(default=None)

    # A flag indicating whether the UAI Class is the default UAI Class.
    default = Etcd3Attr(default=False)

    # A flag indicating whether UAIs created using this class have ports
    # open on a public IP address or a cluster-only IP address.
    public_ip = Etcd3Attr(default=False)

    # The namespace UAIs of this class will be placed in when created.
    namespace = Etcd3Attr(default=None)

    # The list of optional additional ports that UAIs of this class
    # will listen on when created.
    opt_ports = Etcd3Attr(default=None)

    # The class that UAIs created by a Broker of this class will be
    # created with.  This is for broker UAIs only and has no meaning
    # for non-broker UAIs.
    uai_creation_class = Etcd3Attr(default=None)

    # A flag indicating whether UAIs should be given a compute network
    # route for job launch capabilities
    uai_compute_network = Etcd3Attr(default=True)

    # The UAI Image ID of the UAI Image to be used by UAIs created
    # using the UAI Class.
    image_id = Etcd3Attr(default=None)

    # The K8s priority class name that UAIs or Brokers created using
    # this UAI Class run with.  This determines which set of resource
    # quotas are assigned to the UAI or Broker and what the scheduling
    # priorities of its pods are relative to other pods on the system.
    priority_class_name = Etcd3Attr(default=None)

    # The UAI Resource Configuration ID of the Resource Limit /
    # Request Configuration to be used by UAIs created using the UAI
    # Class.
    resource_id = Etcd3Attr(default=None)

    # The list of Volume Mount IDs identifying volumes to be mounted
    # in UAIs created using the UAI Class.
    volume_list = Etcd3Attr(default=None)

    # The list of tolerations beyond the default UAI toleration to
    # be applied to UAI pods of this class
    tolerations = Etcd3Attr(default=None)

    # A timeout description in the form of a dictionary consisting of,
    # potentially, a 'soft' valued and a 'hard' value, both in
    # seconds.  Both settings are optional.  If the timeout is present
    # and one or the other timeouts is not in it, that timeout is
    # indefinite.
    timeout = Etcd3Attr(default=None)

    # A Kubernetes service account to be applied to UAIs created from
    # this class to confer specific Kubernetes RBAC to the UAI
    # pod.
    service_account = Etcd3Attr(default=None)

    # The number of replicas of this UAI to run when it is launched.
    # This allows the UAI to run as a load-balanced set of pods under
    # a single service instead of just one pod.  Default value is 1.
    replicas = Etcd3Attr(default=1)

    @staticmethod
    def get_default():
        """ Retrieve the current default UAI / Broker Class, if any.

        """
        uai_classes = UAIClass.get_all()
        if uai_classes is not None:
            for uai_class in uai_classes:
                if uai_class.default:  # pylint: disable=no-member
                    return uai_class
        return None

    def expand(self):
        """Produce a dictionary of the publicly viewable elements of the
        object.

        """
        return {
            'class_id': self.class_id,
            'comment': self.comment,
            'default': self.default,
            'public_ip': self.public_ip,
            'namespace': self.namespace,
            'opt_ports': self.opt_ports,
            'uai_creation_class': self.uai_creation_class,
            'uai_compute_network': self.uai_compute_network,
            'image_id': self.image_id,
            'priority_class_name': self.priority_class_name,
            'resource_id': self.resource_id,
            'volume_list': self.volume_list,
            'tolerations': self.tolerations,
            'timeout': self.timeout,
            'service_account': self.service_account,
            'replicas': self.replicas
        }
