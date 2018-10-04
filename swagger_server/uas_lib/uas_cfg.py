#
# Copyright 2018, Cray Inc.  All Rights Reserved.
#
# Description:
#   Manages Cray User Access Node instances.
#

import logging
import yaml

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
        with open(self.uas_cfg) as uascfg:
            cfg = yaml.load(uascfg)
        return cfg

    def get_images(self):
        cfg = self.get_config()
        return cfg['uas_images']['images']

    def get_default_image(self):
        cfg = self.get_config()
        return cfg['uas_images']['default_image']

    def validate_image(self, imagename):
        if imagename in self.get_images():
            return True
        else:
            return False

    def get_external_ips(self):
        cfg = self.get_config()
        return cfg['uas_ips']

    def gen_volume_mounts(self):
        cfg = self.get_config()
        volume_mount_list = []
        for mnt in cfg['volume_mounts']:
            volume_mount_list.append(client.V1VolumeMount(name=mnt['name'],
                                                    mount_path=mnt['mount_path']))
        return volume_mount_list

    def gen_volumes(self):
        cfg = self.get_config()
        volume_list = []
        for vol in cfg['volume_mounts']:
            volume_list.append(client.V1Volume(name=vol['name'],
                                   host_path=client.V1HostPathVolumeSource(
                                   path=vol['host_path'],
                                   type='DirectoryOrCreate')))
        return volume_list
