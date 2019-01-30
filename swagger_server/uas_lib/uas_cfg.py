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

    def get_external_ips(self, service_type):
        """
        This function returns external ips for either the "NodePort" or
        ClusterIP service types.
        :param service_type: Either "NodePort" or "ClusterIP"
        :type service_type: str
        :return: external IP address
        :rtype str
        """
        cfg = self.get_config()
        ext_ip = None
        if not cfg:
            return ext_ip
        try:
            if service_type == "NodePort":
                ext_ip = cfg['uas_ips']
            if service_type == "ClusterIP":
                ext_ip = cfg['uas_svc_ips']
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
        if service_type == "ClusterIP":
            try:
                cfg_port_list = cfg['uas_svc_ports']
            except KeyError:
                cfg_port_list = []
        else:
            try:
                cfg_port_list = cfg['uas_ports']
            except KeyError:
                cfg_port_list = [30123]
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

