#!/usr/bin/python3
#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#
# pylint: disable=missing-docstring

import unittest

from datetime import datetime, timedelta, timezone
from swagger_server.uas_lib.uas_cfg import UasCfg
from kubernetes import client  # pylint: disable=no-name-in-module

class TestUasCfg(unittest.TestCase):
    """Tester for the UasCfg class

    """
    uas_cfg = UasCfg(uas_cfg='swagger_server/test/cray-uas-mgr.yaml')
    uas_cfg_empty = UasCfg(
        uas_cfg='swagger_server/test/cray-uas-mgr-empty.yaml'
    )
    uas_cfg_svc = UasCfg(uas_cfg='swagger_server/test/cray-uas-mgr-svc.yaml')
    uas_cfg_port_range = UasCfg(
        uas_cfg='swagger_server/test/cray-uas-mgr-port-range.yaml'
    )

    # pylint: disable=missing-docstring
    def test_get_config(self):
        # Just make sure calling get_config() doesn't die on all the
        # configs...
        _ = self.uas_cfg.get_config()
        _ = self.uas_cfg_empty.get_config()
        _ = self.uas_cfg_svc.get_config()

    # pylint: disable=missing-docstring
    def test_get_images(self):
        images = self.uas_cfg.get_images()
        self.assertEqual(
            images,
            ['dtr.dev.cray.com:443/cray/cray-uas-sles15:latest']
        )
        images = self.uas_cfg_empty.get_images()
        self.assertEqual(images, None)

    # pylint: disable=missing-docstring
    def test_get_default_image(self):
        image = self.uas_cfg.get_default_image()
        self.assertEqual(
            image,
            'dtr.dev.cray.com:443/cray/cray-uas-sles15:latest'
        )
        image = self.uas_cfg_empty.get_default_image()
        self.assertEqual(image, None)

    # pylint: disable=missing-docstring
    def test_validate_image_true(self):
        self.assertTrue(
            self.uas_cfg.validate_image(
                'dtr.dev.cray.com:443/cray/cray-uas-sles15:latest'
            )
        )

    # pylint: disable=missing-docstring
    def test_validate_image_false(self):
        self.assertFalse(self.uas_cfg.validate_image('not-an-image'))
        self.assertFalse(self.uas_cfg.validate_image(''))

    # pylint: disable=missing-docstring
    def test_get_external_ip(self):
        self.assertEqual('10.100.240.14',
                         self.uas_cfg.get_external_ip())
        self.assertEqual(self.uas_cfg_empty.get_external_ip(), None)

    # pylint: disable=missing-docstring
    def test_gen_volume_mounts(self):
        self.assertEqual(5, len(self.uas_cfg_svc.gen_volume_mounts()))
        self.assertEqual([], self.uas_cfg_empty.gen_volume_mounts())

    # pylint: disable=missing-docstring
    def test_get_volumes(self):
        vs = self.uas_cfg_svc.gen_volumes()  # pylint: disable=invalid-name
        for v in vs:  # pylint: disable=invalid-name
            if hasattr(v, 'host_path'):
                if v.host_path:
                    if v.name == 'time':
                        self.assertEqual('FileOrCreate', v.host_path.type)
                    else:
                        self.assertEqual('DirectoryOrCreate', v.host_path.type)
        self.assertEqual(5, len(vs))
        self.assertEqual([], self.uas_cfg_empty.gen_volumes())

    # pylint: disable=missing-docstring
    def test_gen_port_entry(self):
        dcp = self.uas_cfg.gen_port_entry(
            self.uas_cfg.get_default_port(),
            False
        )
        self.assertEqual(dcp.container_port, self.uas_cfg.get_default_port())
        self.assertIsInstance(dcp, client.V1ContainerPort)

        # pylint: disable=invalid-name
        cp = self.uas_cfg.gen_port_entry(12345, False)
        self.assertEqual(cp.container_port, 12345)
        self.assertIsInstance(cp, client.V1ContainerPort)

        # pylint: disable=invalid-name
        sp = self.uas_cfg.gen_port_entry(12345, True)
        self.assertEqual(sp.port, 12345)
        self.assertEqual(sp.name, "port12345")
        self.assertEqual(sp.protocol, "TCP")
        self.assertIsInstance(sp, client.V1ServicePort)

    # pylint: disable=missing-docstring
    def test_uas_cfg_gen_port_list(self):
        port_list = self.uas_cfg.gen_port_list(
            service_type="ssh",
            service=False
        )
        self.assertEqual(1, len(port_list))
        self.assertEqual(30123, port_list[0].container_port)

        port_list = self.uas_cfg.gen_port_list(service_type="ssh", service=True)
        self.assertEqual(1, len(port_list))
        self.assertEqual(30123, port_list[0].port)

        optional_ports = [80, 443]
        port_list = self.uas_cfg.gen_port_list(
            service_type="ssh",
            service=False,
            optional_ports=optional_ports
        )
        self.assertEqual(3, len(port_list))
        for port in port_list:
            self.assertIn(port.container_port, [30123, 80, 443])

        port_list = self.uas_cfg.gen_port_list(
            service_type="service",
            service=False
        )
        self.assertEqual([], port_list)

        port_list = self.uas_cfg.gen_port_list(
            service_type="service",
            service=True
        )
        self.assertEqual([], port_list)

        self.assertEqual(1, len(self.uas_cfg.gen_port_list()))

    # pylint: disable=missing-docstring
    def test_uas_cfg_svc_gen_port_list(self):
        # a slightly different way of testing from above
        port_list = self.uas_cfg_svc.gen_port_list(
            service_type="ssh",
            service=False
        )
        self.assertEqual(1, len(port_list))
        # pylint: disable=invalid-name
        for pl in port_list:
            self.assertIsInstance(pl, client.V1ContainerPort)
            self.assertEqual(30123, pl.container_port)
        port_list = self.uas_cfg_svc.gen_port_list(service_type="ssh", service=True)
        self.assertEqual(1, len(port_list))
        # pylint: disable=invalid-name
        for pl in port_list:
            self.assertEqual(22, pl.port)
            self.assertIsInstance(pl, client.V1ServicePort)

        # equivalent to service_type=None, service=False
        port_list = self.uas_cfg_svc.gen_port_list()
        self.assertEqual(1, len(port_list))
        # pylint: disable=invalid-name
        for pl in port_list:
            self.assertIsInstance(pl, client.V1ContainerPort)
            self.assertEqual(30123, pl.container_port)

    # pylint: disable=missing-docstring
    def test_uas_ports_range_gen_port_list(self):
        with self.assertRaises(ValueError):
            self.uas_cfg_port_range.gen_port_list(service_type="ssh",
                                                  service=False)

    # pylint: disable=missing-docstring
    def test_create_readiness_probe(self):
        probe = self.uas_cfg.create_readiness_probe()
        self.assertIsInstance(probe, client.V1Probe)
        self.assertIsInstance(probe.tcp_socket, client.V1TCPSocketAction)

    # pylint: disable=missing-docstring
    def test_get_valid_optional_ports(self):
        port_list = self.uas_cfg.get_valid_optional_ports()
        self.assertListEqual(port_list, [80, 443, 8888])

    # pylint: disable=missing-docstring
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

    # pylint: disable=missing-docstring
    def test_is_valid_host_path_mount_type(self):
        self.assertTrue(self.uas_cfg.is_valid_host_path_mount_type('FileOrCreate'))
        self.assertTrue(self.uas_cfg.is_valid_host_path_mount_type('DirectoryOrCreate'))
        self.assertFalse(self.uas_cfg.is_valid_host_path_mount_type('Wrong'))
        self.assertFalse(self.uas_cfg.is_valid_host_path_mount_type(''))
        self.assertFalse(self.uas_cfg.is_valid_host_path_mount_type(None))

    # pylint: disable=missing-docstring
    def test_validate_ssh_key(self):
        self.assertFalse(self.uas_cfg.validate_ssh_key(None))
        self.assertFalse(self.uas_cfg.validate_ssh_key(""))
        self.assertFalse(self.uas_cfg.validate_ssh_key("cray"))
        self.assertFalse(self.uas_cfg.validate_ssh_key("\n"))
        self.assertFalse(self.uas_cfg.validate_ssh_key("   \t\n"))

        # try a random non-key file
        # pylint: disable=invalid-name
        with open(
                "/usr/src/app/swagger_server/test/version-check.sh", "r"
        ) as f:
            nonKey = f.read()
            self.assertFalse(self.uas_cfg.validate_ssh_key(nonKey))

        # pylint: disable=invalid-name
        with open("/usr/src/app/swagger_server/test/test_rsa.pub", "r") as f:
            publicKey = f.read()
            self.assertTrue(self.uas_cfg.validate_ssh_key(publicKey))
            # pick some random substrings from the key - it should only
            # validate a full key and not a partial one
            self.assertFalse(self.uas_cfg.validate_ssh_key(publicKey[3:56]))
            self.assertFalse(self.uas_cfg.validate_ssh_key(publicKey[0:58]))

        # pylint: disable=invalid-name
        with open("/usr/src/app/swagger_server/test/test_rsa", "r") as f:
            privateKey = f.read()
            self.assertFalse(self.uas_cfg.validate_ssh_key(privateKey))

    # pylint: disable=missing-docstring
    def test_is_valid_volume_name(self):
        # Capital letters are bad
        self.assertFalse(self.uas_cfg.is_valid_volume_name('NoCaps'))
        # can't have some of these
        special_chars = ["*", "$", "%", "'", "!"]
        # pylint: disable=invalid-name
        for sc in special_chars:
            self.assertFalse(self.uas_cfg.is_valid_volume_name(sc+'foo'))

        # - is legal
        self.assertTrue(self.uas_cfg.is_valid_volume_name('my-name-is'))
        # numbers are ok
        self.assertTrue(self.uas_cfg.is_valid_volume_name('jenny8675309'))
        # although I think all numbers are okay with DNS-1123, k8s doesn't
        # allow it
        self.assertFalse(self.uas_cfg.is_valid_volume_name('8675309'))
        # lower case letters & numbers are ok
        self.assertTrue(self.uas_cfg.is_valid_volume_name('99something'))
        # can't end with a -
        self.assertFalse(self.uas_cfg.is_valid_volume_name('dashnotatend-'))
        # can't start with a -
        self.assertFalse(self.uas_cfg.is_valid_volume_name('-dashnotatstart'))
        # has to be <= 63 chars
        self.assertFalse(
            self.uas_cfg.is_valid_volume_name(
                'mercury-venus-earth-asteroid-belt-mars-jupiter-saturn-uranus-neptune'
            )
        )  # noqa E501
        # 0 length not allowed
        self.assertFalse(self.uas_cfg.is_valid_volume_name(''))

    # pylint: disable=missing-docstring
    def test_get_pod_age(self):
        self.assertEqual(self.uas_cfg.get_pod_age(None), None)

        with self.assertRaises(TypeError):
            self.assertEqual(self.uas_cfg.get_pod_age("wrong"), None)

        now = datetime.now(timezone.utc)
        self.assertEqual(self.uas_cfg.get_pod_age(now), "0m")
        self.assertEqual(self.uas_cfg.get_pod_age(now-timedelta(hours=1)),
                         "1h0m")
        self.assertEqual(self.uas_cfg.get_pod_age(now-timedelta(hours=25)),
                         "1d1h")
        self.assertEqual(self.uas_cfg.get_pod_age(now-timedelta(minutes=25)),
                         "25m")
        self.assertEqual(self.uas_cfg.get_pod_age(now-timedelta(days=89)),
                         "89d")
        # for days > 0, don't print minutes
        self.assertEqual(self.uas_cfg.get_pod_age(now-timedelta(minutes=1442)),
                         "1d")
        self.assertEqual(self.uas_cfg.get_pod_age(now-timedelta(minutes=1501)),
                         "1d1h")

    # pylint: disable=missing-docstring
    def test_get_uai_namespace(self):
        self.assertEqual(self.uas_cfg.get_uai_namespace(), "somens")
        self.assertEqual(self.uas_cfg_svc.get_uai_namespace(), "default")


if __name__ == '__main__':
    unittest.main()
