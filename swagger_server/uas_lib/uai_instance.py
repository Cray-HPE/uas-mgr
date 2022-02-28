# MIT License
#
# (C) Copyright [2021-2022] Hewlett Packard Enterprise Development LP
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
"""
Container class for UAI Instances

"""
import os
import json
import uuid
import re
from flask import abort
import sshpubkeys
import sshpubkeys.exceptions as sshExceptions
from kubernetes import client
from swagger_server.uas_lib.uas_logging import logger
from swagger_server.uas_lib.uas_auth import UAS_AUTH_LOGGER
from swagger_server.uas_lib.vault import get_vault_path
from swagger_server.uas_data_model.uai_resource import UAIResource
from swagger_server.uas_data_model.uai_image import UAIImage

# All UAIs have the following toleration to allow them to run
# on nodes that are tainted against non-UAI activity.  The list
# can be extended using UAI Class toleration lists.
BASE_UAI_TOLERATIONS = [client.V1Toleration(key="uai_only", operator="Exists")]


class UAIInstance:
    """This class carries information about individual UAI instances used
    in creating UAIs that does not belong in a UAIClass.  It provides
    a convenient container for information that is only known at UAI
    creation time.

    """
    @staticmethod
    def validate_ssh_key(ssh_key):
        """
        checks whether the ssh_key is a valid public key
        ssh_key input is expected to be a string
        :return: returns True if valid public key
        :rtype bool
        """
        try:
            ssh = sshpubkeys.SSHKey(ssh_key, strict=False,
                                    skip_option_parsing=True)
            ssh.parse()
            return True
        except (NotImplementedError, sshExceptions.MalformedDataError) as err:
            UAS_AUTH_LOGGER.error("Invalid key: %s", err)
        except sshExceptions.InvalidKeyError as err:
            UAS_AUTH_LOGGER.error("Unknown key type: %s", err)
        except Exception as err:  # pylint: disable=broad-except
            UAS_AUTH_LOGGER.error("Invalid non-key input: %s", err)
        return False

    def get_public_key_str(self, public_key):
        """Extract a public SSH key from its packing and verify that it looks
        like a public SSH key (and not a private one in particular).

        """
        public_key_str = None
        if public_key:
            try:
                # Depending on the API call, the public key may come
                # in as an 'io.Bytes' object or as a string.  If it is
                # an 'io.Bytes' object it needs to be turned into a
                # string.  Otherwise, it can be used as is.
                if isinstance(public_key, str):
                    public_key_str = public_key
                else:
                    public_key_str = public_key.read().decode()
                if not self.validate_ssh_key(public_key_str):
                    # do not log the key here even if it's invalid, it
                    # could be a private key accidentally passed in
                    logger.info("create_uai - invalid ssh public key")
                    abort(400, "Invalid ssh public key.")
            except Exception:  # pylint: disable=broad-except
                logger.info("create_uai - invalid ssh public key")
                abort(400, "Invalid ssh public key.")
        return public_key_str

    def __init__(self, owner=None, public_key=None, passwd_str=None,
                 uai_name=None):
        """Constructor

        """
        self.owner = owner
        if isinstance(public_key, str):
            self.public_key_str = public_key
        else:
            self.public_key_str = self.get_public_key_str(public_key)
        self.passwd_str = passwd_str
        dep_id = str(uuid.uuid4().hex[:8])
        dep_owner = "no-owner" if owner is None else self.owner
        self.job_name = (
            uai_name if uai_name else
            'uai-' + dep_owner + '-' + dep_id
        )
        regex = re.compile('^(?![0-9]+$)(?!-)[a-z0-9-]{1,63}(?<!-)$')
        if not regex.match(self.job_name):
            abort(400, "'%s' is not a valid UAI name" % self.job_name)


    def get_service_name(self):
        """ Compute the service name of a UAI based on UAI parameters.

        """
        return self.job_name + "-ssh"

    def get_env(self, uai_class=None):
        """ Compute a K8s environment block for use in the UAI

        """
        env = [
            client.V1EnvVar(
                name='UAS_NAME',
                value=self.get_service_name()
            ),
            client.V1EnvVar(
                name='UAS_PASSWD',
                value=self.passwd_str
            ),
            client.V1EnvVar(
                name='UAS_PUBKEY',
                value=self.public_key_str
            )
        ]
        if uai_class.uai_creation_class is not None:
            env.append(
                client.V1EnvVar(
                    name='UAI_CREATION_CLASS',
                    value=uai_class.uai_creation_class
                )
            )
            env.append(
                client.V1EnvVar(
                    name='UAI_SHARED_SECRET_PATH',
                    value=get_vault_path(uai_class.uai_creation_class)
                )
            )
        if uai_class.replicas is not None:
            env.append(
                client.V1EnvVar(
                    name='UAI_REPLICAS',
                    value=str(uai_class.replicas)
                )
            )
        timeout = (
            uai_class.timeout if uai_class.timeout is not None
            else {}
        )
        soft = timeout.get('soft', None)
        if soft is not None:
            env.append(
                client.V1EnvVar(
                    name='UAI_SOFT_TIMEOUT',
                    value=soft
                )
            )
        hard = timeout.get('hard', None)
        if hard is not None:
            env.append(
                client.V1EnvVar(
                    name='UAI_HARD_TIMEOUT',
                    value=hard
                )
            )
        warning = timeout.get('warning', None)
        if warning is not None:
            env.append(
                client.V1EnvVar(
                    name='UAI_HARD_TIMEOUT_WARNING',
                    value=warning
                )
            )
        return env

    def gen_labels(self, uai_class=None):
        """Generate labels for a UAI

        """
        ret = {
            "app": self.job_name,
            "uas": "managed"
        }
        if self.owner is not None:
            ret['user'] = self.owner
        if uai_class is not None:
            if uai_class.uai_creation_class is not None:
                ret['uas-uai-creation-class'] = uai_class.uai_creation_class
            if uai_class.opt_ports is not None:
                ret['uas-uai-opt-ports'] = "-".join(uai_class.opt_ports)
            ret['uas-uai-has-timeout'] = str(bool(uai_class.timeout))
            ret['uas-public-ip'] = str(uai_class.public_ip)
            ret['uas-class-id'] = uai_class.class_id
        return ret

    # pylint: disable=too-many-locals
    def create_pod_template(self, uai_class, uas_cfg):
        """Construct a pod template specification for a UAI of the given class.

        """
        # If we are using macvlan then set that up in an annotation in
        # the metadata of the job, otherwise, the annotations will be
        # None. USE_MACVLAN comes from config in the Helm chart.  We
        # only set this up in UAIs also have the 'uai_compute_network'
        # flag. Some UAIs aren't on that network.
        meta_annotations = None
        if os.environ.get('USE_MACVLAN', 'true').lower() == 'true' and \
           uai_class.uai_compute_network:
            meta_annotations = {
                'k8s.v1.cni.cncf.io/networks': 'macvlan-uas-nmn-conf@nmn1'
            }

        pod_metadata = client.V1ObjectMeta(
            labels=self.gen_labels(uai_class),
            annotations=meta_annotations
        )
        volume_list = uai_class.volume_list
        resources = {}
        if uai_class.resource_id is not None:
            limit_json = UAIResource.get(uai_class.resource_id).limit
            request_json = UAIResource.get(uai_class.resource_id).request
            if limit_json:
                resources['limits'] = json.loads(limit_json)
            if request_json:
                resources['requests'] = json.loads(request_json)
        container_ports = uas_cfg.gen_port_list(
            service=False,
            opt_ports=[
                int(port) for port in uai_class.opt_ports
            ] if uai_class.opt_ports is not None else None
        )
        logger.info(
            "UAI Name: %s; Container ports: %s; Optional ports: %s",
            self.job_name,
            container_ports,
            uai_class.opt_ports
        )

        # Configure Pod template container
        container = client.V1Container(
            name=self.job_name,
            image=UAIImage.get(uai_class.image_id).imagename,
            resources=resources or None,
            env=self.get_env(uai_class),
            ports=container_ports,
            volume_mounts=uas_cfg.gen_volume_mounts(volume_list),
            readiness_probe=uas_cfg.create_readiness_probe()
        )

        # Create and configure affinity
        node_selector_terms = [
            client.V1NodeSelectorTerm(
                match_expressions=[
                    client.V1NodeSelectorRequirement(
                        key='node-role.kubernetes.io/master',
                        operator='DoesNotExist'
                    ),
                    client.V1NodeSelectorRequirement(
                        key='uas',
                        operator='NotIn',
                        values=['False', 'false', 'FALSE']
                    )
                ]
            )
        ]
        node_selector = client.V1NodeSelector(node_selector_terms)
        node_affinity = client.V1NodeAffinity(
            required_during_scheduling_ignored_during_execution=node_selector
        )
        # pylint: disable=unnecessary-comprehension
        tolerations = [toleration for toleration in BASE_UAI_TOLERATIONS]
        if uai_class.tolerations is not None:
            toleration_list = json.loads(uai_class.tolerations)
            for toleration in toleration_list:
                tolerations.append(client.V1Toleration(**toleration))
        return client.V1PodTemplateSpec(
            metadata=pod_metadata,
            spec=client.V1PodSpec(
                affinity=client.V1Affinity(node_affinity=node_affinity),
                containers=[container],
                priority_class_name=(
                    uai_class.priority_class_name or 'uai-priority'
                ),
                restart_policy='OnFailure',
                service_account=uai_class.service_account or 'default',
                service_account_name=uai_class.service_account or 'default',
                tolerations=tolerations,
                volumes=uas_cfg.gen_volumes(volume_list)
            )
        )

    def create_job_object(self, uai_class, uas_cfg):
        """Construct a job for a UAI or Broker

        """
        # Make the template for the pod that will be the UAI
        template = self.create_pod_template(uai_class, uas_cfg)

        # Put together a job to manage the pod
        job_metadata = client.V1ObjectMeta(
            name=self.job_name,
            labels=self.gen_labels(uai_class)
        )
        spec = client.V1JobSpec(
            backoff_limit=1000000000,
            parallelism=uai_class.replicas,
            template=template
        )
        # Instantiate the job object
        return client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=job_metadata,
            spec=spec
        )

    def create_service_object(self, uai_class, uas_cfg):
        """
        Create a service object for the deployment of the UAI.

        """
        # Pick the service type based on the value of 'public_ip' in
        # the UAI Class.  This is a lot simpler than it looks if you
        # delve into it, but I am using the code that was here to do
        # this. That code bases the service class (SSH point of
        # access) on two strings: "service" (which basically means an
        # internal ClusterIP) and "ssh" (which basically means a
        # LoadBalncer IP or a NodePort).  Instead of reworking all
        # that logic, I am picking one or the other here based on
        # whether 'public_ip' is true or false.
        service_type = "ssh" if uai_class.public_ip else "service"

        metadata = client.V1ObjectMeta(
            name=self.get_service_name(),
            labels=self.gen_labels(uai_class),
        )
        ports = uas_cfg.gen_port_list(
            service_type,
            service=True,
            opt_ports=[
                int(port) for port in uai_class.opt_ports
            ] if uai_class.opt_ports is not None else None
        )

        # svc_type is a dict with the following fields:
        #   'svc_type': (NodePort, ClusterIP, or LoadBalancer)
        #   'ip_pool': (None, or a specific pool)  Valid only for LoadBalancer.
        #   'subdomain': the externaldns sub-domain that matches the ip-pool.  Valid
        #                only for LoadBalancer.
        #   'valid': (True or False) is svc_type is valid or not
        svc_type = uas_cfg.get_svc_type(service_type)
        if not svc_type['valid']:
            # Invalid svc_type given.
            msg = (
                "Unsupported service type '{}' configured, "
                "contact sysadmin. Valid service types are "
                "NodePort, ClusterIP, and LoadBalancer.".format(
                    svc_type['svc_type']
                )
            )
            abort(400, msg)
        # Check if LoadBalancer and whether an IP pool is set
        if svc_type['svc_type'] == "LoadBalancer" and svc_type['ip_pool']:
            # A specific IP pool is given, update the metadata with
            # annotations
            hostname = self.job_name + '.' + svc_type['subdomain']
            metadata.annotations = {
                "metallb.universe.tf/address-pool": svc_type['ip_pool'],
                "external-dns.alpha.kubernetes.io/hostname": hostname,
            }
        spec = client.V1ServiceSpec(
            selector={'app': self.job_name},
            type=svc_type['svc_type'],
            ports=ports
        )
        service = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=metadata,
            spec=spec
        )
        return service
