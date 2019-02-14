#!/usr/bin/python3

import unittest

from swagger_server.uas_lib.uas_cfg import UasCfg

class TestUasCfg(unittest.TestCase):

    uas_cfg = UasCfg(uas_cfg='swagger_server/test/cray-uas-mgr.yaml')
    uas_cfg_empty = UasCfg(uas_cfg='swagger_server/test/cray-uas-mgr-empty.yaml')
    uas_cfg_svc = UasCfg(uas_cfg='swagger_server/test/cray-uas-mgr-svc.yaml')

    def test_get_config(self):
        cfg = self.uas_cfg.get_config()
        cfg_empty = self.uas_cfg_empty.get_config()
        cfg_svc = self.uas_cfg_svc.get_config()

    def test_get_images(self):
        images = self.uas_cfg.get_images()
        self.assertEqual(images, ['dtr.dev.cray.com:443/cray/cray-uas-img:latest'])
        images = self.uas_cfg_empty.get_images()
        self.assertEqual(images, None)

    def test_get_default_image(self):
        image = self.uas_cfg.get_default_image()
        self.assertEqual(image, 'dtr.dev.cray.com:443/cray/cray-uas-img:latest')
        image = self.uas_cfg_empty.get_default_image()
        self.assertEqual(image, None)

    def test_validate_image_true(self):
        self.assertEqual(True, self.uas_cfg.validate_image('dtr.dev.cray.com:443/cray/cray-uas-img:latest'))

    def test_validate_image_false(self):
        self.assertEqual(False, self.uas_cfg.validate_image('not-an-image'))

    def test_get_external_ips(self):
        self.assertEqual(['10.100.240.14'],
                         self.uas_cfg.get_external_ips("NodePort"))
        self.assertEqual(['10.100.240.24'],
                         self.uas_cfg_svc.get_external_ips("ClusterIP"))
        self.assertEqual(None, self.uas_cfg.get_external_ips("FooBar"))

    def test_gen_volume_mounts(self):
        try:
            self.uas_cfg_svc.gen_volume_mounts()
        except ExceptionType:
            self.fail("gen_volume_mounts() raised ExceptionType")
        try:
            self.uas_cfg_empty.gen_volume_mounts()
        except ExceptionType:
            self.fail("gen_volume_mounts() raised ExceptionType on empty comfig")

    def test_get_volumes(self):
        try:
            self.uas_cfg_svc.gen_volumes()
        except ExceptionType:
            self.fail("gen_volumes() raised ExceptionType")
        try:
            self.uas_cfg_empty.gen_volumes()
        except ExceptionType:
            self.fail("gen_volumes() raised ExceptionType on empty config")

    def test_gen_port_entry(self):
        try:
            self.uas_cfg.gen_port_entry(30123, False)
        except ExceptionType:
            self.fail("gen_port_entry() for container port raised ExceptionType")
        try:
            self.uas_cfg.gen_port_entry(30123, True)
        except ExceptionType:
            self.fail("gen_port_entry() for service port raised ExceptionType")

    def test_gen_port_list(self):
        try:
            self.uas_cfg.gen_port_list(service_type="ssh", service=False)
        except ExceptionType:
            self.fail("gen_port_list() for container ssh raised ExceptionType")
        try:
            self.uas_cfg.gen_port_list(service_type="ssh", service=True)
        except ExceptionType:
            self.fail("gen_port_list() for service ssh raised ExceptionType")
        try:
            self.uas_cfg.gen_port_list(service_type="service", service=False)
        except ExceptionType:
            self.fail("gen_port_list() for container service raised ExceptionType")
        try:
            self.uas_cfg.gen_port_list(service_type="service", service=True)
        except ExceptionType:
            self.fail("gen_port_list() for service raised ExceptionType")
        try:
            self.uas_cfg.gen_port_list()
        except ExceptionType:
            self.fail("gen_port_list() raised ExceptionType")

    def test_get_service_type(self):
        svc_type = self.uas_cfg.get_svc_type(service_type="ssh")
        self.assertEqual(svc_type['svc_type'], "NodePort")
        self.assertEqual(svc_type['ip_pool'], None)
        svc_type = self.uas_cfg_empty.get_svc_type(service_type="ssh")
        self.assertEqual(svc_type['svc_type'], "NodePort")
        self.assertEqual(svc_type['ip_pool'], None)
        svc_type = self.uas_cfg.get_svc_type(service_type="service")
        self.assertEqual(svc_type['svc_type'], "ClusterIP")
        self.assertEqual(svc_type['ip_pool'], None)
        svc_type = self.uas_cfg_empty.get_svc_type(service_type="service")
        self.assertEqual(svc_type['ip_pool'], None)
        self.assertEqual(svc_type['svc_type'], "ClusterIP")
        svc_type = self.uas_cfg_svc.get_svc_type(service_type="ssh")
        self.assertEqual(svc_type['ip_pool'], "ssh_ip_pool")
        self.assertEqual(svc_type['svc_type'], "LoadBalancer")
        svc_type = self.uas_cfg_svc.get_svc_type(service_type="service")
        self.assertEqual(svc_type['svc_type'], "LoadBalancer")
        self.assertEqual(svc_type['ip_pool'], "svc_ip_pool")

if __name__ == '__main__':
    unittest.main()
