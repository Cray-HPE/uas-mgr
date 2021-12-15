#!/usr/bin/python3
# MIT License
#
# (C) Copyright [2020] Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# pylint: disable=missing-docstring

import os
import json
import unittest
import yaml
import requests_mock
from kubernetes import client
import werkzeug
from swagger_server.uas_lib.uas_cfg import UasCfg
from swagger_server.uas_lib.uai_instance import UAIInstance
from swagger_server.uas_data_model.uai_volume import UAIVolume
from swagger_server.uas_data_model.uai_image import UAIImage
from swagger_server.uas_data_model.populated_config import PopulatedConfig
from swagger_server.uas_data_model.uas_data_model import ExpandableStub


# pylint: disable=too-many-public-methods
@requests_mock.Mocker()
class TestUasCfg(unittest.TestCase):
    """Tester for the UasCfg class

    """
    uas_cfg = UasCfg(uas_cfg='swagger_server/test/cray-uas-mgr.yaml')
    uas_cfg_empty = UasCfg(
        uas_cfg='swagger_server/test/cray-uas-mgr-empty.yaml'
    )
    uas_cfg_svc = UasCfg(uas_cfg='swagger_server/test/cray-uas-mgr-svc.yaml')
    uas_cfg_svc_customer_access = UasCfg(
        uas_cfg='swagger_server/test/cray-uas-mgr-svc-customer-access.yaml'
    )

    @classmethod
    def __reset_runtime_config(cls, new_config=None):
        """Reset the stored (etcd) configuration that results from actions on
        a given configuration.  This module acts on several different
        configurations expecting different results from each, so
        residual runtime configuration from a previous test can cause
        test failures.  This clears out runtime configuration to
        permit clean starting conditions for each new configuration
        test.

        """
        vols = UAIVolume.get_all()
        if vols is not None:
            for vol in vols:
                vol.remove()
        imgs = UAIImage.get_all()
        if imgs is not None:
            for img in imgs:
                img.remove()
        configs = PopulatedConfig.get_all()
        if configs is not None:
            for cfg in configs:
                cfg.remove()
        if new_config is not None:
            new_config.get_config()

    # pylint: disable=missing-docstring,unused-argument
    def test_get_config(self, mocker):
        # Just make sure calling get_config() doesn't die on all the
        # configs...
        self.__reset_runtime_config()
        _ = self.uas_cfg.get_config()
        self.__reset_runtime_config()
        _ = self.uas_cfg_empty.get_config()
        self.__reset_runtime_config()
        _ = self.uas_cfg_svc.get_config()
        self.__reset_runtime_config()

    # pylint: disable=missing-docstring,unused-argument
    def test_get_images(self, mocker):
        self.__reset_runtime_config(self.uas_cfg)
        images = self.uas_cfg.get_images()
        self.assertIsNone(images)
        self.__reset_runtime_config(self.uas_cfg_empty)
        images = self.uas_cfg_empty.get_images()
        self.__reset_runtime_config()
        self.assertEqual(images, None)
        self.__reset_runtime_config()

    # pylint: disable=missing-docstring,unused-argument
    def test_get_default_image(self, mocker):
        self.__reset_runtime_config(self.uas_cfg)
        image = self.uas_cfg.get_default_image()
        self.assertIsNone(image)
        self.__reset_runtime_config(self.uas_cfg_empty)
        image = self.uas_cfg_empty.get_default_image()
        self.assertIsNone(image)
        self.__reset_runtime_config()

    # pylint: disable=missing-docstring,unused-argument
    def test_validate_image_no_defaults(self, mocker):
        self.__reset_runtime_config(self.uas_cfg)
        self.assertFalse(
            self.uas_cfg.validate_image(
                'dtr.dev.cray.com:443/cray/cray-uas-sles15:latest'
            )
        )
        self.__reset_runtime_config()

    # pylint: disable=missing-docstring,unused-argument
    def test_validate_image_false(self, mocker):
        self.__reset_runtime_config(self.uas_cfg)
        self.assertFalse(self.uas_cfg.validate_image('not-an-image'))
        self.assertFalse(self.uas_cfg.validate_image(''))
        self.__reset_runtime_config()

    # pylint: disable=missing-docstring,unused-argument
    def test_get_external_ip(self, mocker):
        self.__reset_runtime_config(self.uas_cfg)
        self.assertEqual('10.100.240.14',
                         self.uas_cfg.get_external_ip())
        self.__reset_runtime_config(self.uas_cfg_empty)
        self.assertEqual(self.uas_cfg_empty.get_external_ip(), None)
        self.__reset_runtime_config()

    # pylint: disable=missing-docstring,unused-argument
    def test_gen_volume_mounts(self, mocker):
        self.__reset_runtime_config(self.uas_cfg_svc)
        volumes = UAIVolume.get_all()
        volumes = [] if volumes is None else volumes
        # pylint: disable=no-member
        volume_list = [volume.volume_id for volume in volumes]
        self.assertEqual(
            5,
            len(self.uas_cfg_svc.gen_volume_mounts(volume_list))
        )
        self.__reset_runtime_config(self.uas_cfg_empty)
        volumes = UAIVolume.get_all()
        volumes = [] if volumes is None else volumes
        # pylint: disable=no-member
        volume_list = [volume.volume_id for volume in volumes]
        self.assertEqual(
            [],
            self.uas_cfg_empty.gen_volume_mounts(volume_list)
        )
        self.__reset_runtime_config()

    # pylint: disable=missing-docstring,unused-argument
    def test_get_volumes(self, mocker):
        self.__reset_runtime_config(self.uas_cfg_svc)
        volumes = UAIVolume.get_all()
        volumes = [] if volumes is None else volumes
        # pylint: disable=no-member
        volume_list = [volume.volume_id for volume in volumes]
        vols = self.uas_cfg_svc.gen_volumes(volume_list)
        for vol in vols:  # pylint: disable=invalid-name
            if hasattr(vol, 'host_path'):
                if vol.host_path:
                    if vol.name == 'time':
                        self.assertEqual('FileOrCreate', vol.host_path.type)
                    else:
                        self.assertEqual('DirectoryOrCreate',
                                         vol.host_path.type)
        self.assertEqual(5, len(vols))
        self.__reset_runtime_config(self.uas_cfg_empty)
        volumes = UAIVolume.get_all()
        volumes = [] if volumes is None else volumes
        # pylint: disable=no-member
        volume_list = [volume.volume_id for volume in volumes]
        self.assertEqual([], self.uas_cfg_empty.gen_volumes(volume_list))
        self.__reset_runtime_config()

    # pylint: disable=missing-docstring,unused-argument
    def test_gen_port_entry(self, mocker):
        self.__reset_runtime_config(self.uas_cfg)
        dcp = self.uas_cfg.gen_port_entry(
            self.uas_cfg.get_default_port(),
            False
        )
        self.assertEqual(dcp.container_port, self.uas_cfg.get_default_port())
        self.assertIsInstance(dcp, client.V1ContainerPort)
        self.__reset_runtime_config(self.uas_cfg)

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
        self.__reset_runtime_config()

    # pylint: disable=missing-docstring,unused-argument
    def test_uas_cfg_gen_port_list(self, mocker):
        self.__reset_runtime_config(self.uas_cfg)
        port_list = self.uas_cfg.gen_port_list(
            service_type="ssh",
            service=False
        )
        self.assertEqual(1, len(port_list))
        self.assertEqual(30123, port_list[0].container_port)

        port_list = self.uas_cfg.gen_port_list(service_type="ssh", service=True)
        self.assertEqual(1, len(port_list))
        self.assertEqual(30123, port_list[0].port)

        opt_ports = [80, 443]
        port_list = self.uas_cfg.gen_port_list(
            service_type="ssh",
            service=False,
            opt_ports=opt_ports
        )
        self.assertEqual(3, len(port_list))
        for port in port_list:
            self.assertIn(port.container_port, [30123, 80, 443])

        port_list = self.uas_cfg.gen_port_list(
            service_type="service",
            service=False
        )
        self.assertEqual(1, len(port_list))
        self.assertEqual(30123, port_list[0].container_port)

        port_list = self.uas_cfg.gen_port_list(
            service_type="service",
            service=True
        )
        self.assertEqual(1, len(self.uas_cfg.gen_port_list()))
        self.__reset_runtime_config()

    # pylint: disable=missing-docstring,unused-argument
    def test_uas_cfg_svc_gen_port_list(self, mocker):
        # a slightly different way of testing from above
        self.__reset_runtime_config(self.uas_cfg_svc)
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
        self.__reset_runtime_config()

    # pylint: disable=missing-docstring,unused-argument
    def test_create_readiness_probe(self, mocker):
        self.__reset_runtime_config(self.uas_cfg)
        probe = self.uas_cfg.create_readiness_probe()
        self.assertIsInstance(probe, client.V1Probe)
        self.assertIsInstance(probe.tcp_socket, client.V1TCPSocketAction)
        self.__reset_runtime_config()

    # pylint: disable=missing-docstring,unused-argument
    def test_get_valid_optional_ports(self, mocker):
        self.__reset_runtime_config(self.uas_cfg)
        port_list = self.uas_cfg.get_valid_optional_ports()
        self.assertListEqual(port_list, [80, 443, 8888])
        self.__reset_runtime_config()

    # pylint: disable=missing-docstring,unused-argument
    def test_get_service_type(self, mocker):
        self.__reset_runtime_config(self.uas_cfg)
        svc_type = self.uas_cfg.get_svc_type(service_type="ssh")
        self.assertEqual(svc_type['svc_type'], "NodePort")
        self.assertEqual(svc_type['ip_pool'], None)
        self.__reset_runtime_config(self.uas_cfg_empty)
        svc_type = self.uas_cfg_empty.get_svc_type(service_type="ssh")
        self.assertEqual(svc_type['svc_type'], "NodePort")
        self.assertEqual(svc_type['ip_pool'], None)
        self.__reset_runtime_config(self.uas_cfg_svc)
        svc_type = self.uas_cfg_svc.get_svc_type(service_type="ssh")
        self.assertEqual(svc_type['ip_pool'], "customer")
        self.assertEqual(svc_type['svc_type'], "LoadBalancer")
        self.__reset_runtime_config(self.uas_cfg_svc_customer_access)
        svc_type = self.uas_cfg_svc_customer_access.get_svc_type(
            service_type="ssh"
        )
        self.assertEqual(svc_type['ip_pool'], "customer-access")
        self.assertEqual(svc_type['svc_type'], "LoadBalancer")
        self.__reset_runtime_config()

    @staticmethod
    # pylint: disable=missing-docstring
    def __load_bican_cases():
        require_bican = os.environ.get('REQUIRE_BICAN', "false").lower()
        expected_key = (
            'expected_pool_soft' if  require_bican == "false"
            else 'expected_pool_hard'
        )
        bican_cases = "swagger_server/test/bican_cases.yaml"
        with open(bican_cases, 'r', encoding='utf-8') as infile:
            cases = yaml.load(infile, Loader=yaml.FullLoader)['bican_cases']
        return [
            (
                case[expected_key],
                case['expected_subdomain'],
                case['networks']
            )
            for case in cases
        ]

    # pylint: disable=missing-docstring
    def __get_service_types_bican(self, mocker):
        bican_cases = self.__load_bican_cases()
        self.assertTrue(bican_cases) # not empty or None to be sure test is run
        self.__reset_runtime_config(self.uas_cfg_svc_customer_access)
        for expected_pool, expected_subdomain, networks in bican_cases:
            mocker.get(
                "http://cray-sls/v1/networks",
                text=json.dumps(networks),
                status_code=200
            )
            if expected_pool is None:
                with self.assertRaises(werkzeug.exceptions.BadRequest):
                    svc_type = self.uas_cfg_svc_customer_access.get_svc_type(
                        service_type="ssh"
                    )
            else:
                svc_type = self.uas_cfg_svc_customer_access.get_svc_type(
                    service_type="ssh"
                )
                self.assertEqual(svc_type['ip_pool'], expected_pool)
                self.assertEqual(svc_type['svc_type'], "LoadBalancer")
                self.assertEqual(svc_type['subdomain'], expected_subdomain)
        self.__reset_runtime_config()

    # pylint: disable=missing-docstring
    def test_get_service_type_bican_no_require(self, mocker):
        if 'REQUIRE_BICAN' in os.environ:
            del os.environ['REQUIRE_BICAN']
        self.__get_service_types_bican(mocker)

    # pylint: disable=missing-docstring
    def test_get_service_type_bican_require_false(self, mocker):
        os.environ['REQUIRE_BICAN'] = "False" # use weird case to test lower
        self.__get_service_types_bican(mocker)

    # pylint: disable=missing-docstring
    def test_get_service_type_bican_require_true(self, mocker):
        os.environ['REQUIRE_BICAN'] = "True" # use weird case to test lower
        self.__get_service_types_bican(mocker)

    # pylint: disable=missing-docstring,unused-argument
    def test_is_valid_host_path_mount_type(self, mocker):
        self.assertTrue(UAIVolume.is_valid_host_path_mount_type('FileOrCreate'))
        self.assertTrue(UAIVolume.is_valid_host_path_mount_type('DirectoryOrCreate'))
        self.assertFalse(UAIVolume.is_valid_host_path_mount_type('Wrong'))
        self.assertFalse(UAIVolume.is_valid_host_path_mount_type(''))
        self.assertFalse(UAIVolume.is_valid_host_path_mount_type(None))

    # pylint: disable=missing-docstring,unused-argument
    def test_validate_ssh_key(self, mocker):
        self.__reset_runtime_config(self.uas_cfg)
        self.assertFalse(UAIInstance.validate_ssh_key(None))
        self.assertFalse(UAIInstance.validate_ssh_key(""))
        self.assertFalse(UAIInstance.validate_ssh_key("cray"))
        self.assertFalse(UAIInstance.validate_ssh_key("\n"))
        self.assertFalse(UAIInstance.validate_ssh_key("   \t\n"))

        # try a random non-key file
        # pylint: disable=invalid-name
        with open(
                "/usr/src/app/swagger_server/test/version-check.sh",
                "r",
                encoding='utf-8'
        ) as f:
            nonKey = f.read()
            self.assertFalse(UAIInstance.validate_ssh_key(nonKey))

        # pylint: disable=invalid-name
        with open(
                "/usr/src/app/swagger_server/test/test_rsa.pub",
                "r",
                encoding='utf-8'
        ) as f:
            publicKey = f.read()
            self.assertTrue(UAIInstance.validate_ssh_key(publicKey))
            # pick some random substrings from the key - it should only
            # validate a full key and not a partial one
            self.assertFalse(UAIInstance.validate_ssh_key(publicKey[3:56]))
            self.assertFalse(UAIInstance.validate_ssh_key(publicKey[0:58]))

        # pylint: disable=invalid-name
        with open(
                "/usr/src/app/swagger_server/test/test_rsa",
                "r",
                encoding='utf-8'
        ) as f:
            privateKey = f.read()
            self.assertFalse(UAIInstance.validate_ssh_key(privateKey))
        self.__reset_runtime_config()

    # pylint: disable=missing-docstring,unused-argument
    def test_is_valid_volume_name(self, mocker):
        # Capital letters are bad
        self.assertFalse(UAIVolume.is_valid_volume_name('NoCaps'))
        # can't have some of these
        special_chars = ["*", "$", "%", "'", "!"]
        # pylint: disable=invalid-name
        for sc in special_chars:
            self.assertFalse(UAIVolume.is_valid_volume_name(sc+'foo'))

        # - is legal
        self.assertTrue(UAIVolume.is_valid_volume_name('my-name-is'))
        # numbers are ok
        self.assertTrue(UAIVolume.is_valid_volume_name('jenny8675309'))
        # although I think all numbers are okay with DNS-1123, k8s doesn't
        # allow it
        self.assertFalse(UAIVolume.is_valid_volume_name('8675309'))
        # lower case letters & numbers are ok
        self.assertTrue(UAIVolume.is_valid_volume_name('99something'))
        # can't end with a -
        self.assertFalse(UAIVolume.is_valid_volume_name('dashnotatend-'))
        # can't start with a -
        self.assertFalse(UAIVolume.is_valid_volume_name('-dashnotatstart'))
        # has to be <= 63 chars
        self.assertFalse(
            UAIVolume.is_valid_volume_name(
                'mercury-venus-earth-asteroid-belt-mars-jupiter-saturn-uranus-neptune'
            )
        )
        # 0 length not allowed
        self.assertFalse(UAIVolume.is_valid_volume_name(''))

    # pylint: disable=missing-docstring,unused-argument
    def test_vol_desc_errors(self, mocker):
        # No Source Type Specified
        err = UAIVolume.vol_desc_errors({})
        self.assertEqual(
            err,
            "Volume Description has no source type (e.g. 'config_map')"
        )
        # Invalid source type specified
        err = UAIVolume.vol_desc_errors(
            {
                'no_such_source': {
                    'not': "happening",
                    'never': 'will'
                }
            }
        )
        self.assertIn(
            "Volume description invalid source type:",
            err
        )
        # Host Path with no path
        err = UAIVolume.vol_desc_errors(
            {
                'host_path': {
                    'type': "DirectoryOrCreate"
                }
            }
        )
        self.assertEqual(
            err,
            "Host path specification missing required 'path'"
        )
        # Host Path with no type
        err = UAIVolume.vol_desc_errors(
            {
                'host_path': {
                    'path': "/var/mnt"
                }
            }
        )
        self.assertIn(
            err,
            "Host path specification missing required 'type'"
        )
        # Host Path with bad type
        err = UAIVolume.vol_desc_errors(
            {
                'host_path': {
                    'path': "/var/mnt",
                    'type': "not a valid host path type"
                }
            }
        )
        self.assertIn(
            "Volume has invalid host_path mount type",
            err
        )
        # Configmap with no configmap name
        err = UAIVolume.vol_desc_errors(
            {
                'config_map': {}
            }
        )
        self.assertIn(
            "Config map specification missing required",
            err
        )
        # Configmap with extra junk
        err = UAIVolume.vol_desc_errors(
            {
                'config_map': {
                    'name': "my-config-map",
                    'other': "stuff"
                }
            }
        )
        self.assertIn(
            "Config map specification has unrecognized",
            err
        )
        # Secret with no secret name
        err = UAIVolume.vol_desc_errors(
            {
                'secret': {}
            }
        )
        self.assertIn(
            "Secret specification missing required",
            err
        )
        # Secret with extra junk
        err = UAIVolume.vol_desc_errors(
            {
                'secret': {
                    'secret_name': "my-little-secret",
                    'other': "stuff"
                }
            }
        )
        self.assertIn(
            "Secret specification has unrecognized",
            err
        )
        # Valid config map
        err = UAIVolume.vol_desc_errors(
            {
                'config_map': {
                    'name': "my-config-map",
                }
            }
        )
        self.assertIs(err, None)

    # pylint: disable=missing-docstring,unused-argument
    def test_get_uai_namespace(self, mocker):
        self.__reset_runtime_config(self.uas_cfg)
        self.assertEqual(self.uas_cfg.get_uai_namespace(), "somens")
        self.__reset_runtime_config(self.uas_cfg_svc)
        self.assertEqual(self.uas_cfg_svc.get_uai_namespace(), "default")
        self.__reset_runtime_config()

    # pylint: disable=missing-docstring,unused-argument
    def test_data_model_expandable_get(self, mocker):
        bad_id = 'invalid-object-id'
        ret = UAIImage.get(bad_id)
        self.assertIs(ret, None)
        ret = UAIImage.get(bad_id, expandable=True)
        self.assertIsInstance(ret, ExpandableStub)
        desc = ret.expand()
        self.assertIsInstance(desc, str)
        self.assertIn("<unknown ", desc)
        self.assertIn(UAIImage.kind.default, desc)
        self.assertEqual(UAIImage.kind.default, "UAIImage")
        self.assertIn(bad_id, desc)


if __name__ == '__main__':
    unittest.main()
