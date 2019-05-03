#!/usr/bin/python3

import unittest

from swagger_server.uas_lib.uas_cfg import UasCfg
from kubernetes import client

class TestUasCfg(unittest.TestCase):

    uas_cfg = UasCfg(uas_cfg='swagger_server/test/cray-uas-mgr.yaml')
    uas_cfg_empty = UasCfg(uas_cfg='swagger_server/test/cray-uas-mgr-empty.yaml')
    uas_cfg_svc = UasCfg(uas_cfg='swagger_server/test/cray-uas-mgr-svc.yaml')
    uas_cfg_port_range = UasCfg(uas_cfg='swagger_server/test/cray-uas-mgr-port-range.yaml')

    def test_get_config(self):
        cfg = self.uas_cfg.get_config()
        cfg_empty = self.uas_cfg_empty.get_config()
        cfg_svc = self.uas_cfg_svc.get_config()

    def test_get_images(self):
        images = self.uas_cfg.get_images()
        self.assertEqual(images, ['dtr.dev.cray.com:443/cray/cray-uas-sles15:latest',
                                  'dtr.dev.cray.com:443/cray/cray-uas-centos75:latest'])
        images = self.uas_cfg_empty.get_images()
        self.assertEqual(images, None)

    def test_get_default_image(self):
        image = self.uas_cfg.get_default_image()
        self.assertEqual(image, 'dtr.dev.cray.com:443/cray/cray-uas-sles15:latest')
        image = self.uas_cfg_empty.get_default_image()
        self.assertEqual(image, None)

    def test_validate_image_true(self):
        self.assertTrue(self.uas_cfg.validate_image('dtr.dev.cray.com:443/cray/cray-uas-sles15:latest'))
        self.assertTrue(self.uas_cfg.validate_image('dtr.dev.cray.com:443/cray/cray-uas-centos75:latest'))

    def test_validate_image_false(self):
        self.assertFalse(self.uas_cfg.validate_image('not-an-image'))
        self.assertFalse(self.uas_cfg.validate_image(''))

    def test_get_external_ip(self):
        self.assertEqual('10.100.240.14',
                         self.uas_cfg.get_external_ip())
        self.assertEqual(self.uas_cfg_empty.get_external_ip(), None)

    def test_gen_volume_mounts(self):
        self.assertEqual(5, len(self.uas_cfg_svc.gen_volume_mounts()))
        self.assertEqual([], self.uas_cfg_empty.gen_volume_mounts())

    def test_get_volumes(self):
        vs = self.uas_cfg_svc.gen_volumes()
        for v in vs:
            if hasattr(v, 'host_path'):
                if v.host_path:
                    if v.name == 'time':
                        self.assertEqual('FileOrCreate', v.host_path.type)
                    else:
                        self.assertEqual('DirectoryOrCreate', v.host_path.type)
        self.assertEqual(5, len(vs))
        self.assertEqual([], self.uas_cfg_empty.gen_volumes())

    def test_gen_port_entry(self):
        dcp = self.uas_cfg.gen_port_entry(self.uas_cfg.get_default_port(), False)
        self.assertEqual(dcp.container_port, self.uas_cfg.get_default_port())
        self.assertIsInstance(dcp, client.V1ContainerPort)

        cp = self.uas_cfg.gen_port_entry(12345, False)
        self.assertEqual(cp.container_port, 12345)
        self.assertIsInstance(cp, client.V1ContainerPort)

        sp = self.uas_cfg.gen_port_entry(12345, True)
        self.assertEqual(sp.port, 12345)
        self.assertEqual(sp.name, "port12345")
        self.assertEqual(sp.protocol, "TCP")
        self.assertIsInstance(sp, client.V1ServicePort)

    def test_uas_cfg_gen_port_list(self):
        port_list = self.uas_cfg.gen_port_list(service_type="ssh", service=False)
        self.assertEqual(1, len(port_list))
        self.assertEqual(30123, port_list[0].container_port)

        port_list = self.uas_cfg.gen_port_list(service_type="ssh", service=True)
        self.assertEqual(1, len(port_list))
        self.assertEqual(30123, port_list[0].port)

        port_list = self.uas_cfg.gen_port_list(service_type="service", service=False)
        self.assertEqual([], port_list)

        port_list = self.uas_cfg.gen_port_list(service_type="service", service=True)
        self.assertEqual([], port_list)

        self.assertEqual(1, len(self.uas_cfg.gen_port_list()))

    def test_uas_cfg_svc_gen_port_list(self):
        # a slightly different way of testing from above
        port_list = self.uas_cfg_svc.gen_port_list(service_type="ssh", service=False)
        self.assertEqual(1, len(port_list))
        for pl in port_list:
            self.assertIsInstance(pl, client.V1ContainerPort)
            self.assertEqual(30123, pl.container_port)
        port_list = self.uas_cfg_svc.gen_port_list(service_type="ssh", service=True)
        self.assertEqual(1, len(port_list))
        for pl in port_list:
            self.assertEqual(30123, pl.port)
            self.assertIsInstance(pl, client.V1ServicePort)

        # equivalent to service_type=None, service=False
        port_list = self.uas_cfg_svc.gen_port_list()
        self.assertEqual(1, len(port_list))
        for pl in port_list:
            self.assertIsInstance(pl, client.V1ContainerPort)
            self.assertEqual(30123, pl.container_port)

    def test_uas_ports_range_gen_port_list(self):
        with self.assertRaises(ValueError):
            self.uas_cfg_port_range.gen_port_list(service_type="ssh",
                                                  service=False)

    def test_create_readiness_probe(self):
        probe = self.uas_cfg.create_readiness_probe()
        self.assertIsInstance(probe, client.V1Probe)
        self.assertIsInstance(probe.tcp_socket, client.V1TCPSocketAction)

    def test_get_service_type(self):
        svc_type = self.uas_cfg.get_svc_type(service_type="ssh")
        self.assertEqual(svc_type['svc_type'], "NodePort")
        self.assertEqual(svc_type['ip_pool'], None)
        svc_type = self.uas_cfg_empty.get_svc_type(service_type="ssh")
        self.assertEqual(svc_type['svc_type'], "NodePort")
        self.assertEqual(svc_type['ip_pool'], None)
        svc_type = self.uas_cfg_svc.get_svc_type(service_type="ssh")
        self.assertEqual(svc_type['ip_pool'], "customer")
        self.assertEqual(svc_type['svc_type'], "LoadBalancer")

    def test_is_valid_host_path_mount_type(self):
        self.assertTrue(self.uas_cfg.is_valid_host_path_mount_type('FileOrCreate'))
        self.assertTrue(self.uas_cfg.is_valid_host_path_mount_type('DirectoryOrCreate'))
        self.assertFalse(self.uas_cfg.is_valid_host_path_mount_type('Wrong'))
        self.assertFalse(self.uas_cfg.is_valid_host_path_mount_type(''))
        self.assertFalse(self.uas_cfg.is_valid_host_path_mount_type(None))


if __name__ == '__main__':
    unittest.main()
