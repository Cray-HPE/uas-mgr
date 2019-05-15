#
# Copyright 2018, Cray Inc.  All Rights Reserved.
#
# Description:
#   Manages Cray User Access Node instances.
#

import logging
import sshpubkeys
import sshpubkeys.exceptions as sshExceptions
import sys
import yaml

from flask import abort
from kubernetes import client

UAS_CFG_LOGGER = logging.getLogger('uas_cfg')
UAS_CFG_LOGGER.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s"
                              " - %(message)s")
handler.setFormatter(formatter)
UAS_CFG_LOGGER.addHandler(handler)
UAS_CFG_DEFAULT_PORT = 30123
UAS_CFG_OPTIONAL_PORTS = [80, 443]


class UasCfg(object):
    """
    The UasCfg class provides the site configuration data to the
    User Access Services.
    """

    def __init__(self, uas_cfg='/etc/uas/cray-uas-mgr.yaml'):
        self.uas_cfg = uas_cfg

    def get_config(self):
        try:
            with open(self.uas_cfg) as uascfg:
                return yaml.load(uascfg, Loader=yaml.FullLoader)
        except (TypeError, IOError):
            abort(404, "configmap %s not found" % self.uas_cfg)

    def get_images(self):
        cfg = self.get_config()
        if not cfg:
            return None
        try:
            return cfg['uas_images']['images']
        except (TypeError, KeyError):
            return None

    def get_default_image(self):
        cfg = self.get_config()
        if not cfg:
            return None
        try:
            return cfg['uas_images']['default_image']
        except (TypeError, KeyError):
            return None

    def validate_image(self, imagename):
        image_list = self.get_images()
        if image_list:
            if imagename in image_list:
                return True
            else:
                return False
        else:
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

    def gen_volume_mounts(self):
        cfg = self.get_config()
        volume_mount_list = []
        if not cfg:
            return volume_mount_list
        try:
            volume_mounts = cfg['volume_mounts']
        except KeyError:
            volume_mounts = []
        for mnt in volume_mounts:
            if mnt:
                volume_mount_list.append(client.V1VolumeMount(name=mnt['name'],
                                                        mount_path=mnt['mount_path']))
        return volume_mount_list

    def gen_volumes(self):
        cfg = self.get_config()
        volume_list = []
        if not cfg:
            return volume_list
        try:
            volume_mounts = cfg['volume_mounts']
        except KeyError:
            volume_mounts = []
        for vol in volume_mounts:
            if vol:
                if vol.get('host_path', None):
                    # support for an optional type attribute for host_path mounts
                    # if this attribute is unset we assume original behavior
                    # which is DirectoryOrCreate
                    mount_type = vol.get('type', 'DirectoryOrCreate')
                    if not self.is_valid_host_path_mount_type(mount_type):
                        raise ValueError("%s mount_type is not supported - \
                                         please refer to the Kubernetes docs \
                                         for a list of supported host_path \
                                         mount types")
                    volume_list.append(client.V1Volume(name=vol['name'],
                                        host_path=client.V1HostPathVolumeSource(
                                        path=vol['host_path'],
                                        type=mount_type
                                        )))
                if vol.get('config_map', None):
                    volume_list.append(client.V1Volume(name=vol['name'],
                                       config_map=client.V1ConfigMapVolumeSource(
                                       name=vol['config_map']
                                       )))
                if vol.get('secret_name', None):
                    volume_list.append(client.V1Volume(name=vol['name'],
                                       secret=client.V1SecretVolumeSource(
                                       secret_name=vol['secret_name']
                                       )))
        return volume_list

    def gen_port_entry(self, port, service):
        # Generate a port entry for the service object
        if service:
            return client.V1ServicePort(name='port' + str(port),
                                        port=port,
                                        protocol="TCP")
        else:
            return client.V1ContainerPort(container_port=port)

    def gen_port_list(self, service_type=None, service=False, optional_ports=[]):
        """
        gen_port_list creates a list of kubernetes port entry objects.
        The type of the port entry object depends on whether the service_type
        is "ssh" or "service", the latter being used for inter-shasta service
        connections.

        :param: service_type: one of either "ssh" or "service"
        :type service_type: str
        :param service: True creates a ServicePort object, False creates a ContainerPort object
        :type service: bool
        :param optional_ports: An optional list of ports to project in addition to the port used for SSH to the UAI
        :type optional_ports: list
        :return port_list: A list of kubernetes port entry objects
        :rtype list
        """
        UAS_CFG_LOGGER.info("optional_ports: %s" % optional_ports)
        cfg = self.get_config()
        port_list = []
        if not cfg:
            return port_list
        if service_type == "service":
            # Read the configmap for uas_svc_ports (ports to project to other services)
            # cfg_port_list is a list of port numbers to be processed into kubernetes port entry objects
            try:
                cfg_port_list = cfg['uas_svc_ports']
                if optional_ports:
                    # Add any optional ports to the cfg_port_list
                    for port in optional_ports:
                        cfg_port_list.append(port)
            except KeyError:
                cfg_port_list = optional_ports
        else:
            # Read the configmap for uas_ports (ports to project to the customer network)
            # cfg_port_list is a list of port numbers to be processed into kubernetes port entry objects
            try:
                cfg_port_list = cfg['uas_ports']
                if optional_ports:
                    # Add any optional ports to the cfg_port_list
                    for port in optional_ports:
                        cfg_port_list.append(port)
                for port in cfg_port_list:
                    # check if a port range was given
                    if isinstance(port, str):
                        raise ValueError("uas_ports does not support ranges")
            except KeyError:
                cfg_port_list = self.get_default_port()
                if optional_ports:
                    # Add any optional ports to the cfg_port_list
                    for port in optional_ports:
                        cfg_port_list.append(port)

        UAS_CFG_LOGGER.info("cfg_port_list: %s" % cfg_port_list)
        for port in cfg_port_list:
            # check if a port range was given
            if isinstance(port, str):
                port_range = port.split(':')
                # build entries for all ports between port_range[0] and port_range[1]
                for i in range(int(port_range[0]), int(port_range[1])+1):
                    port_list.append(self.gen_port_entry(i, service))
            else:
                port_list.append(self.gen_port_entry(port, service))
        return port_list

    def get_svc_type(self, service_type=None):
        cfg = self.get_config()
        svc_type = {'svc_type': None, 'ip_pool': None, 'valid': False}
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
        if svc_type['svc_type'] in ['NodePort', 'ClusterIP', 'LoadBalancer']:
            svc_type['valid'] = True
        else:
            # Invalid svc_type given
            svc_type['valid'] = False
        return svc_type

    def get_default_port(self):
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
            cfg_port_list = cfg['uas_ports']
        except KeyError:
            cfg_port_list = self.get_default_port()
        # XXX - pick first port, switch when the uas_ports type is changed
        socket = client.V1TCPSocketAction(port=cfg_port_list[0])
        return client.V1Probe(initial_delay_seconds=2,
                              period_seconds=3,
                              tcp_socket=socket)

    def is_valid_host_path_mount_type(self, mount_type):
        """
        checks whether the mount_type is a valid one or not
        :return: returns True if the passed in mount type
        :rtype bool
        """
        return mount_type in ("DirectoryOrCreate", "Directory", "FileOrCreate", "File", "Socket", "CharDevice", "BlockDevice")

    def validate_ssh_key(self, ssh_key):
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
        except sshExceptions.InvalidKeyError as err:
            UAS_CFG_LOGGER.error("Unknown key type: ", err)
        except (NotImplementedError, sshExceptions.MalformedDataError) as err:
            UAS_CFG_LOGGER.error("Invalid key: ", err)
        except Exception as err:
            UAS_CFG_LOGGER.error("Invalid non-key input: ", err)
        return False

    def get_valid_optional_ports(self):
        """
        Return list of valid optional ports.
        :return: List of valid optional ports.
        :rtype list
        """
        return UAS_CFG_OPTIONAL_PORTS