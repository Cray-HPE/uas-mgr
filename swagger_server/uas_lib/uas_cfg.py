#
# Copyright 2018, Cray Inc.  All Rights Reserved.
#
# Description:
#   Manages Cray User Access Node instances.
#

import logging
import yaml

from flask import abort

from kubernetes import client

UAS_CFG_LOGGER = logging.getLogger('uas_cfg')
UAS_CFG_DEFAULT_PORT = 30123


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
                return yaml.load(uascfg)
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
        This function returns external ip for "NodePort" services
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
                    volume_list.append(client.V1Volume(name=vol['name'],
                                        host_path=client.V1HostPathVolumeSource(
                                        path=vol['host_path'],
                                        type='DirectoryOrCreate'
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

    def gen_port_list(self, service_type=None, service=False):
        cfg = self.get_config()
        port_list = []
        if not cfg:
            return port_list
        if service_type == "service":
            try:
                cfg_port_list = cfg['uas_svc_ports']
            except KeyError:
                cfg_port_list = []
        else:
            try:
                cfg_port_list = cfg['uas_ports']
                for port in cfg_port_list:
                    # check if a port range was given
                    if isinstance(port, str):
                        raise ValueError("uas_ports does not support ranges")
            except KeyError:
                cfg_port_list = self.get_default_port()

        for port in cfg_port_list:
            # check if a port range was given
            if isinstance(port, str):
                port_range = port.split(':')
                # build entries for all ports between port_range[0] and port_range[1]
                for i in range(int(port_range[0]), int(port_range[1])+1):
                    # Only allow ports greater than 1024
                    if i > 1024:
                        port_list.append(self.gen_port_entry(i, service))
            else:
                if port > 1024:
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