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
                cfg = yaml.load(uascfg)
        except IOError as e:
            abort(404, "configmap %s not found" % self.uas_cfg)
        return cfg

    def get_images(self):
        cfg = self.get_config()
        if cfg['uas_images']:
            try:
                images = cfg['uas_images']['images']
            except KeyError:
                images = None
        else:
            images = None
        return images

    def get_default_image(self):
        cfg = self.get_config()
        if cfg['uas_images']:
            try:
                image = cfg['uas_images']['default_image']
            except KeyError:
                image = None
        else:
            image = None
        return image

    def validate_image(self, imagename):
        image_list = self.get_images()
        if image_list:
            if imagename in self.get_images():
                retval = True
            else:
                retval = False
        else:
            retval = False
        return retval

    def get_external_ips(self):
        cfg = self.get_config()
        try:
            ext_ip = cfg['uas_ips']
        except KeyError:
            ext_ip = None
        return ext_ip

    def gen_volume_mounts(self):
        cfg = self.get_config()
        volume_mount_list = []
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
        try:
            volume_mounts = cfg['volume_mounts']
        except KeyError:
            volume_mounts = []
        for vol in volume_mounts:
            if vol:
                volume_list.append(client.V1Volume(name=vol['name'],
                                    host_path=client.V1HostPathVolumeSource(
                                    path=vol['host_path'],
                                    type='DirectoryOrCreate')))
        return volume_list
