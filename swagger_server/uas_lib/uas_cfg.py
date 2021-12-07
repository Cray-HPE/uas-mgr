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
"""
   Manages Cray User Access Node instances.
"""

import os
import json
import yaml
from flask import abort
from kubernetes import client
import requests
from swagger_server.uas_lib.uas_logging import logger
from swagger_server.uas_data_model.uai_volume import UAIVolume
from swagger_server.uas_data_model.uai_image import UAIImage


UAS_CFG_DEFAULT_PORT = 30123
UAS_CFG_OPTIONAL_PORTS = [80, 443, 8888]
UAS_CFG_DEFAULT_UAI_NAMESPACE = "default"


class UasCfg:
    """
    The UasCfg class provides the site configuration data to the
    User Access Services.
    """
    def __init__(self, uas_cfg='/etc/uas/cray-uas-mgr.yaml'):
        """Constructor

        """
        self.uas_cfg = uas_cfg

    def get_config(self):
        """Load the configuration from the configmap.

        This loads in the UAS Manager configmap to obtain the
        configuration settings for the UAS Manager.  For items that
        are managed under ETCD, the configmap is used the first time
        UAS Manager runs on a new system to load the initial settings
        into ETCD and then ignored from then on.  For items that are
        only configured in the configmap, updates to the configmap
        will be read in each time this is called.

        """
        cfg = {}
        try:
            with open(self.uas_cfg, encoding='utf-8') as uascfg:
                # pylint: disable=no-member
                cfg = yaml.load(uascfg, Loader=yaml.FullLoader)
        except (TypeError, IOError):
            abort(404, "configmap %s not found" % self.uas_cfg)
        # The empty case can be parsed as None, fix that...
        if cfg is None:
            cfg = {}

        # We have the configmap contents, now, populate any ETCD
        # tables that need populating...
        if UAIImage.get_all() is None:
            # There are no UAI Image objects in ETCD.  Just register
            # the empty table.  We no longer populate UAI images from
            # a chart supplied configuration.
            UAIImage.register()
        if UAIVolume.get_all() is None:
            # There are no UAI Volume objects in ETCD, populate that
            # table now.
            UAIVolume.register()
            for vol in cfg.get('volume_mounts', []):
                UAIVolume.add_etcd_volume(vol)
        return cfg

    def get_images(self):
        """ Retrieve a list of image names.
        """
        _ = self.get_config()
        imgs = UAIImage.get_all()
        if not imgs:
            return None
        return [img.imagename for img in imgs]   # pylint: disable=no-member

    def get_default_image(self):
        """Retrieve the name of the default image.

        """
        _ = self.get_config()
        imgs = UAIImage.get_all()
        imgs = [] if imgs is None else imgs
        for img in imgs:
            if img.default:  # pylint: disable=no-member
                return img.imagename  # pylint: disable=no-member
        return None

    def validate_image(self, imagename):
        """Determine whether the specified imagename is a known image name.

        """
        _ = self.get_config()
        imgs = UAIImage.get_all()
        imgs = [] if imgs is None else imgs
        # pylint: disable=no-member
        for img in imgs:
            if imagename == img.imagename:
                return True
        return False

    def get_external_ip(self):
        """
        This function returns external ip for UAI ssh access
        :return: external IP address
        :rtype str
        """
        cfg = self.get_config()
        ext_ip = None
        if not cfg:
            return ext_ip
        try:
            ext_ip = cfg['uas_ip']
        except KeyError:
            ext_ip = None
        return ext_ip

    def gen_volume_mounts(self, volume_list):
        """Generate a list of volume mounts from the configuration.  Return
        the K8s volume mount for each.

        """
        _ = self.get_config()
        volume_mounts = [UAIVolume.get(volume_id) for volume_id in volume_list]
        volume_mount_list = [
            client.V1VolumeMount(name=mnt.volumename,
                                 mount_path=mnt.mount_path)
            for mnt in volume_mounts
        ]
        return volume_mount_list

    def gen_volumes(self, volume_list):
        """Generate a list of volumes from the configuration.  Return the K8s
        volume definitions for each.

        """
        _ = self.get_config()
        volume_mounts = [UAIVolume.get(volume_id) for volume_id in volume_list]
        ret = []
        for volume_mount in volume_mounts:
            # Okay, this is magic, so it requires a bit of
            # explanation. The 'client.V1Volume()' call takes a long
            # list of different arguments, one for each supported type
            # of volume source.  Since our volume storage source is
            # already encapsulated in a volume description which
            # identifies the source type and the source parameters,
            # what we want to do is construct a dictionary using the
            # top-level key from the volume description (which
            # identifies the source type) as the name of the argument
            # to be assigned into, and the name of the volume to be
            # defined, then pass the dictionary instead of explicit
            # arguments.
            volume_args = {}
            volume_args['name'] = volume_mount.volumename
            volume_source_key = list(volume_mount.volume_description.keys())[0]
            volume_args[volume_source_key] = UAIVolume.get_volume_source(
                volume_mount.volume_description
            )
            ret.append(client.V1Volume(**volume_args))
        return ret

    def gen_port_entry(self, port, service):
        """Generate a port entry for the service object """
        if service:
            svc_type = self.get_svc_type(service_type="ssh")
            target_port = None
            if svc_type['svc_type'] == "LoadBalancer":
                target_port = port
                if port == UAS_CFG_DEFAULT_PORT:
                    port = 22
                    target_port = UAS_CFG_DEFAULT_PORT
            return client.V1ServicePort(
                name='port' + str(port),
                port=port,
                target_port=target_port,
                protocol="TCP"
            )
        # Not a service, compose a container port instead...
        return client.V1ContainerPort(
            name='port' + str(port),
            container_port=port,
            protocol="TCP"
        )

    # pylint: disable=too-many-branches
    def gen_port_list(self,
                      service_type=None,
                      service=False,
                      opt_ports=None):
        """
        gen_port_list creates a list of kubernetes port entry objects.
        The type of the port entry object depends on whether the service_type
        is "ssh" or "service", the latter being used for inter-shasta service
        connections.

        :param: service_type: one of either "ssh" or "service"
        :type service_type: str
        :param service: True creates a ServicePort object, False creates a
                        ContainerPort object
        :type service: bool
        :param opt_ports: An optional list of ports to project in
                               addition to the port used for SSH to the UAI
        :type opt_ports: list
        :return port_list: A list of kubernetes port entry objects
        :rtype list
        """
        # Avoid using a default value of [] in the call because that can
        # result in modification of the empty-list for the call if the
        # argument is ever modified.
        opt_ports = [] if opt_ports is None else opt_ports
        logger.info("opt_ports: %s", opt_ports)
        cfg = self.get_config()
        port_list = []
        if not cfg:
            return port_list
        default_port = self.get_default_port()
        cfg_ports = cfg.get('uas_ports', [])
        cfg_ports += [
            port
            for port in opt_ports
            if port != default_port
        ]
        if service_type != "service" and default_port not in cfg_ports:
            # Read the configmap for uas_ports (ports to project to
            # the customer network) cfg_ports is a list of port
            # numbers to be processed into kubernetes port entry
            # objects
            cfg_ports.append(default_port)
        logger.info("cfg_ports: %s", cfg_ports)
        return [
            self.gen_port_entry(port, service)
            for port in cfg_ports
        ]

    @staticmethod
    def __get_sls_networks():
        """Call into the SLS to get the list of configured networks

        """
        logger.debug("retrieving SLS network data")
        try:
            response = requests.get("http://cray-sls/v1/networks")
            # raise exception for 4XX and 5XX errors
            response.raise_for_status()
        except requests.exceptions.RequestException as err:
            logger.warning(
                "retrieving BICAN information %r %r", type(err), err
            )
            return []
        except Exception as err:  # pylint: disable=broad-except
            logger.warning(
                "retrieving BICAN information %r %r", type(err), err
            )
            return []
        try:
            ret = response.json() or []
        except json.decoder.JSONDecodeError as err:
            logger.warning(
                "decoding BICAN information %r %r", type(err), err
            )
            return []
        logger.debug("retrieved SLS network data: %s", ret)
        return ret

    @classmethod
    def __get_bican_pool(cls):
        """Learn the Bifurcated CAN address pool to be
        used (CHN or CAN) for user access.  If the pool can't be
        learned, then either use a default of 'customer_access' if
        REQUIRE_BICAN is false or not set, or fail with an informative
        error message.

        """
        # Declare a default BiCAN setting to use if none can be found.
        # Note that the SystemDefaultRoute (which would normally be
        # 'CAN' or 'CHN' is None here, that signals that no BiCAN
        # config was found in case we are enforcing BiCAN existence.
        default_props = {
            'SystemDefaultRoute': None
        }
        default_bican = {
            'Name': "BICAN",
            'ExtraProperties': default_props,
        }
        pool_map = {
            'CAN': "customer-access",
            'CHN': "customer-high-speed",
            'CMN': "customer-access",
        }
        logger.debug("getting require_bican")
        require_bican = os.environ.get('REQUIRE_BICAN', 'false').lower()
        logger.debug("require_bican = %s", require_bican)
        default_pool = (
            "customer-access" if require_bican == 'false'
            else None
        )
        logger.debug("default_pool = %s", default_pool)
        networks = cls.__get_sls_networks()
        bican_list = [net for net in networks if net['Name'] == "BICAN"]
        bican = bican_list[0] if bican_list else default_bican
        bican_props = bican.get('ExtraProperties', default_props)
        logger.debug("bican_props: %s", bican_props)
        pool = pool_map.get(bican_props['SystemDefaultRoute'], default_pool)
        logger.debug("pool = %s", pool)
        if pool is None:
            # Didn't find a pool and this system doesn't allow a
            # default pool so fail here.
            logger.error(
                "can't find valid BiCAN config in SLS: networks = %s",
                networks
            )
            msg = (
                "Bifurcated CAN configuration is required on the host system "
                "and could not be found.  If there is no Bifurcated "
                "CAN on this platform, ask your system administrator "
                "to set 'require_bican' to false in the site "
                "customizations for cray-uas-mgr."
            )
            abort(400, msg)
        return pool

    def get_svc_type(self, service_type=None):
        """Get the service type for UAIs from the config.

        """
        subdomain_map = {}
        domain = "local"
        cfg = self.get_config()
        svc_type = {'svc_type': None, 'ip_pool': None, 'valid': False, 'sub_domain': None}
        if not cfg:
            # Return defaults if no configuration exists
            if service_type == "service":
                svc_type['svc_type'] = 'ClusterIP'
            if service_type == "ssh":
                svc_type['svc_type'] = 'NodePort'
        else:
            if service_type == "service":
                svc_type['svc_type'] = cfg.get('uas_svc_type', 'ClusterIP')
                if svc_type['svc_type'] == "LoadBalancer":
                    svc_type['ip_pool'] = cfg.get('uas_svc_lb_pool', None)
            if service_type == "ssh":
                svc_type['svc_type'] = cfg.get('uas_ssh_type', 'NodePort')
                if svc_type['svc_type'] == "LoadBalancer":
                    svc_type['ip_pool'] = cfg.get('uas_ssh_lb_pool', None)
            domain = cfg.get('dns_domain', 'local')
            subdomain_map = {
                'customer-access': 'can' + '.' + domain,
                'customer-high-speed': 'chn' + '.' + domain,
                'customer-management': 'cmn' + '.' + domain,
            }
        svc_type['valid'] = svc_type['svc_type'] in ['NodePort',
                                                     'ClusterIP',
                                                     'LoadBalancer']
        # Automatic switching between CHN and CAN for Bifurcated CAN support.
        # If the configuration says `customer_access` for the LB IP Pool, then
        # set it based on what the BICAN configuration says.  Otherwise, leave
        # it alone because someone actually bothered to make it something
        # else (or we aren't on the LB at all).
        svc_type['ip_pool'] = (
            svc_type['ip_pool'] if svc_type['ip_pool'] != 'customer-access'
            else self.__get_bican_pool()
        )

        # Based on the IP pool requested, set up a DNS sub-domain for the UAI to
        # reside on.  This is used for external DNS if the UAI has a public IP
        # address.
        svc_type['subdomain'] = subdomain_map.get(svc_type['ip_pool'], None)

        return svc_type

    @staticmethod
    def get_default_port():
        """
        getter for the default UAS port
        :return: UAS default port
        :rtype int
        """
        return UAS_CFG_DEFAULT_PORT

    def create_readiness_probe(self):
        """
        Creates a k8s readiness check object for use during container launch
        :return: k8s V1Probe
        :rtype object
        """
        cfg = self.get_config()
        try:
            cfg_ports = cfg['uas_ports']
        except KeyError:
            cfg_ports = self.get_default_port()
        # XXX - pick first port, switch when the uas_ports type is changed
        socket = client.V1TCPSocketAction(port=cfg_ports[0])
        return client.V1Probe(initial_delay_seconds=2,
                              period_seconds=3,
                              tcp_socket=socket)

    @staticmethod
    def get_valid_optional_ports():
        """
        Return list of valid optional ports.
        :return: List of valid optional ports.
        :rtype list
        """
        return UAS_CFG_OPTIONAL_PORTS

    def get_uai_namespace(self):
        """
        Gets the namespace in which UAIs will be created. This namespace is
        assumed to have been created by the installation process. Defaults
        to UAS_CFG_DEFAULT_UAI_NAMESPACE if unset.
        :return: k8s namespace
        :rtype string
        """
        cfg = self.get_config()
        if not cfg:
            return None
        try:
            return cfg['uai_namespace']
        except (TypeError, KeyError):
            logger.info(
                "configuration uai_namespace not found, "
                "using %s namespace for UAIs",
                UAS_CFG_DEFAULT_UAI_NAMESPACE
            )
            return UAS_CFG_DEFAULT_UAI_NAMESPACE
