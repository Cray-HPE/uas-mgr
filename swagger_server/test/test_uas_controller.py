#!/usr/bin/python3

import unittest
import os

import swagger_server.controllers.uas_controller as uas_ctl
from swagger_server import version
from swagger_server.uas_lib.uas_cfg import UasCfg
from swagger_server.uas_lib.uan_mgr import UanManager


class TestUasController(unittest.TestCase):

    os.environ["KUBERNETES_SERVICE_PORT"]="443"
    os.environ["KUBERNETES_SERVICE_HOST"]="127.0.0.1"
    uas_ctl.uas_cfg = UasCfg(uas_cfg='swagger_server/test/cray-uas-mgr.yaml')
    uas_ctl.uas_mgr = UanManager()

    def test_get_uas_images(self):
        images = uas_ctl.get_uas_images()
        self.assertEqual(images,
                         {'default_image': 'dtr.dev.cray.com:443/cray/cray-uas-img:latest',
                          'image_list': ['dtr.dev.cray.com:443/cray/cray-uas-img:latest']})

    def test_get_uas_mgr_info(self):
        info = uas_ctl.get_uas_mgr_info()
        self.assertEqual(info,
                         {'service_name': 'cray-uas-mgr',
                          'version': version})

if __name__ == '__main__':
    unittest.main()