#!/usr/bin/python3

import json
import unittest

from swagger_server.uas_lib.uas_cfg import UasCfg

class TestUasCfg(unittest.TestCase):

    uas_cfg = UasCfg(uas_cfg='swagger_server/test/cray-uas-mgr.yaml')

    def test_get_config(self):
        cfg = self.uas_cfg.get_config()

    def test_get_images(self):
        images = self.uas_cfg.get_images()
        self.assertEqual( images, ['dtr.dev.cray.com:443/cray/cray-uas-img:latest'] )

    def test_get_default_image(self):
        image = self.uas_cfg.get_default_image()
        self.assertEqual( image, 'dtr.dev.cray.com:443/cray/cray-uas-img:latest' )

    def test_validate_image_true(self):
        self.assertEqual( True, self.uas_cfg.validate_image('dtr.dev.cray.com:443/cray/cray-uas-img:latest') )

    def test_validate_image_false(self):
        self.assertEqual( False, self.uas_cfg.validate_image('not-an-image') )

    def test_get_external_ips(self):
        self.assertEqual( ['10.100.240.14'], self.uas_cfg.get_external_ips() )

    def test_gen_volume_mounts(self):
        try:
            self.uas_cfg.gen_volume_mounts()
        except ExeptionType:
            self.fail("gen_volume_mounts() raised ExceptionType")

    def test_get_volumes(self):
        try:
            self.uas_cfg.gen_volumes()
        except ExeptionType:
            self.fail("gen_volumes() raised ExceptionType")

if __name__ == '__main__':
    unittest.main()
