#!/usr/bin/python3

import unittest
import os

import swagger_server.controllers.uas_controller as uas_ctl
from swagger_server import version
from swagger_server.uas_lib.uas_cfg import UasCfg
from swagger_server.uas_lib.uan_mgr import UanManager
from werkzeug.exceptions import BadRequest


class TestUasController(unittest.TestCase):

    os.environ["KUBERNETES_SERVICE_PORT"]="443"
    os.environ["KUBERNETES_SERVICE_HOST"]="127.0.0.1"
    uas_ctl.uas_cfg = UasCfg(uas_cfg='swagger_server/test/cray-uas-mgr.yaml')
    uas_ctl.uas_mgr = UanManager()

    def test_create_uan(self):
        resp = uas_ctl.create_uan(None)
        self.assertEqual(resp, "Must supply username for UAN creation.")

    def test_delete_uan_by_name(self):
        resp = uas_ctl.delete_uan_by_name([])
        self.assertEqual(resp, "Must provide a list of UAI names to delete.")

    def test_get_uans_for_username(self):
        resp = uas_ctl.get_uans_for_username(None)
        self.assertEqual(resp, "Must provide username to list UAIs for user.")

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