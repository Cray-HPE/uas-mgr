#!/usr/bin/python3

# MIT License
#
# (C) Copyright [2020-2022] Hewlett Packard Enterprise Development LP
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

import unittest
import os
import io
from datetime import datetime, timezone, timedelta
import json
import uuid
import werkzeug
import flask
from swagger_server.uas_lib.uai_mgr import UaiManager
from swagger_server.uas_lib.uas_mgr import UasManager
from swagger_server.uas_lib.uai_instance import UAIInstance
from swagger_server.uas_lib.vault import get_vault_path
from swagger_server.uas_data_model.uai_class import UAIClass
from swagger_server.uas_data_model.uai_image import UAIImage


app = flask.Flask(__name__)  # pylint: disable=invalid-name


class TestUasMgr(unittest.TestCase):
    """Tester for the UasMgr Class

    """
    os.environ["KUBERNETES_SERVICE_PORT"] = "443"
    os.environ["KUBERNETES_SERVICE_HOST"] = "127.0.0.1"
    public_key_str = (
        "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCzpYg4QF8sj479"
        "cBdhLf6qyZPSueaQ9T7r96ejD7TUpwrjDxZFneZGm6dbFIRBR1P5"
        "/0TYbGBWvvHGZvunsp+wjVx6MlpUmaC4oQlPS9Re01NI60zI6den"
        "RofAGa2hlCRq6CtEX7IG2r8uKJa7intjQmyeUKCju6HKjZbamYBx"
        "7kxSdaKbsIzwwURL7g7od6dVh+R3XaFHLDWbS52wwsD09T4mIiUB"
        "O3wvs/ShApFsUmuG1DFgUfdCV+m2S67gr2VDUwmeZeV7mPDZRmCS"
        "UNCTuRM5RNjYBtaRPb6POl/wDKQQz3Q0hdlzg0jxiID//C3BASfK"
        "9i+UNWq7o3BSHNSj test-user@host.mydomain.com"
    )
    public_key = io.BytesIO()
    public_key.write(
        bytes(public_key_str, encoding='utf8')
    )
    with app.test_request_context('/'):
        uai_mgr = UaiManager()
        uas_mgr = UasManager()

    # pylint: disable=missing-docstring,no-self-use
    def test_uas_mgr_init(self):
        return

    def __compare_dicts(self, expected, actual):
        """ Compare two dictionaries and fail if they are different.

        """
        for key in expected:
            self.assertIn(key, actual)
            if isinstance(expected[key], dict):
                self.assertIsInstance(actual[key], dict)
                self.__compare_dicts(expected[key], actual[key])
            else:
                self.assertEqual(expected[key], actual[key])
        for key in actual:
            # If the key is in expected we have already checked that
            # it is correct in actual.  If not, we will fail here.
            self.assertIn(key, expected)

    # pylint: disable=missing-docstring
    def test_construct_uai_class(self):
        uai_image = UAIImage(imagename="my-image-name", default=False)
        image_id= uai_image.image_id
        uai_image.put()
        uai_class = self.uai_mgr.construct_uai_class(
            imagename=uai_image.imagename,
            namespace="my-namespace",
            opt_ports=[1, 2, 3, 4]
        )
        self.assertEqual(image_id, uai_class.image_id)
        self.assertEqual("my-namespace", uai_class.namespace)
        self.assertEqual([1, 2, 3, 4], uai_class.opt_ports)
        self.assertEqual(False, uai_class.default)
        self.assertEqual(True, uai_class.public_ip)
        uai_image.remove()

    # pylint: disable=missing-docstring
    def test_gen_labels(self):
        uai_instance = UAIInstance()
        labels = uai_instance.gen_labels()
        self.__compare_dicts(
            {
                "app": uai_instance.job_name,
                "uas": "managed"
            },
            labels
        )
        labels = uai_instance.gen_labels()
        self.__compare_dicts(
            {
                "app": uai_instance.job_name,
                "uas": "managed"
            },
            labels
        )
        uai_instance = UAIInstance(owner="test-user")
        labels = uai_instance.gen_labels()
        self.__compare_dicts(
            {
                "app": uai_instance.job_name,
                "uas": "managed",
                "user": uai_instance.owner
            },
            labels
        )
        uai_class = UAIClass(
            uai_creation_class=str(uuid.uuid4()),
            public_ip=True
        )
        labels = uai_instance.gen_labels(uai_class)
        self.__compare_dicts(
            {
                "app": uai_instance.job_name,
                "uas": "managed",
                "user": uai_instance.owner,
                "uas-uai-creation-class": uai_class.uai_creation_class,
                "uas-public-ip": str(uai_class.public_ip),
                "uas-class-id": uai_class.class_id,
                "uas-uai-has-timeout": str(bool(uai_class.timeout))
            },
            labels
        )

    def __check_env(self, expected, env):
        """ Verify that, given a K8s environment list, the items in the list
        are the expected ones and have the expected values.

        """
        found = []
        # Make sure everything in the environment is expected and has
        # the right value
        for item in env:
            self.assertIn(item.name, expected)
            self.assertEqual(item.value, expected[item.name])
            found.append(item.name)
        # Make sure everything expected was in the environment
        for key in expected:
            self.assertIn(key, found)

    #pylint: disable=missing-docstring
    def test_uai_instance(self):
        passwd_str = "test-user::1234:5678:User Name:/user/home/directory:/user/shell"
        # Test with an io.Bytes() public key
        self.public_key.seek(0)
        uai_instance = UAIInstance(
            owner="test-user",
            passwd_str=passwd_str,
            public_key=self.public_key
        )
        self.assertEqual(uai_instance.owner, "test-user")
        self.assertEqual(uai_instance.passwd_str, passwd_str)
        self.assertEqual(uai_instance.public_key_str, self.public_key_str)
        # Test with a string public key
        uai_instance = UAIInstance(
            owner="test-user",
            passwd_str=passwd_str,
            public_key=self.public_key_str
        )
        self.assertEqual(uai_instance.owner, "test-user")
        self.assertEqual(uai_instance.passwd_str, passwd_str)
        self.assertEqual(uai_instance.public_key_str, self.public_key_str)

    #pylint: disable=missing-docstring
    def test_get_env(self):
        self.public_key.seek(0)
        uai_instance = UAIInstance(
            owner="test-user",
            passwd_str="test-user::1234:5678:User Name:/user/home/directory:/user/shell",
            public_key=self.public_key
        )
        uai_class = UAIClass(
            uai_creation_class=str(uuid.uuid4())
        )
        env = uai_instance.get_env(uai_class)
        vault_path = get_vault_path(uai_class.uai_creation_class)
        self.__check_env(
            {
                'UAS_NAME': uai_instance.get_service_name(),
                'UAS_PASSWD': uai_instance.passwd_str,
                'UAS_PUBKEY': uai_instance.public_key_str,
                'UAI_CREATION_CLASS': uai_class.uai_creation_class,
                'UAI_REPLICAS': str(uai_class.replicas),
                'UAI_SHARED_SECRET_PATH': vault_path,
            },
            env
        )

    #pylint: disable=missing-docstring
    def test_create_job_object(self):
        self.uai_mgr.uas_cfg.get_config()
        image = UAIImage(imagename="my-image-name", default=False)
        image_id = image.image_id
        image.put()
        self.public_key.seek(0)
        uai_instance = UAIInstance(
            owner="test-user",
            passwd_str="test-user::1234:5678:User Name:/user/home/directory:/user/shell",
            public_key=self.public_key
        )
        uai_class = UAIClass(
            comment="A Class to test deployment object creation",
            default=False,
            public_ip=False,
            namespace="my-namespace",
            uai_creation_class=None,
            image_id=image_id,
            priority_class_name="my-priority-class",
            resource_id=None,
            volume_list=[]
        )
        obj = uai_instance.create_job_object(
            uai_class,
            self.uai_mgr.uas_cfg
        )
        image.remove()
        # Spot check the deployment, since exhaustive checking is
        # probably impractical
        self.assertEqual(obj.api_version, "batch/v1")
        self.assertEqual(obj.kind, "Job")
        metadata = obj.metadata
        spec = obj.spec
        template=spec.template
        self.assertEqual(
            uai_class.priority_class_name,
            template.spec.priority_class_name
        )
        self.assertEqual(
            [],
            template.spec.volumes
        )
        self.assertEqual(
            uai_instance.job_name,
            template.spec.containers[0].name
        )
        self.__check_env(
            {
                'UAS_NAME': uai_instance.get_service_name(),
                'UAS_PASSWD': uai_instance.passwd_str,
                'UAS_PUBKEY': uai_instance.public_key_str,
                'UAI_REPLICAS': str(uai_class.replicas),
            },
            template.spec.containers[0].env
        )
        self.assertEqual(
            [],
            template.spec.containers[0].volume_mounts
        )
        self.__compare_dicts(
            uai_instance.gen_labels(uai_class),
            metadata.labels
        )
        self.assertEqual(
            uai_instance.job_name,
            metadata.name
        )
        self.__compare_dicts(
            uai_instance.gen_labels(uai_class),
            template.metadata.labels
        )

    #pylint: disable=missing-docstring
    def test_create_service_object(self):
        self.public_key.seek(0)
        uai_instance = UAIInstance(
            owner="test-user",
            passwd_str="test-user::1234:5678:User Name:/user/home/directory:/user/shell",
            public_key=self.public_key
        )
        uai_class = UAIClass(
            comment="A Class to test service object creation",
            default=False,
            public_ip=False,
            namespace="my-namespace",
            uai_creation_class=None,
            image_id=str(uuid.uuid4()),
            priority_class_name="my-priority-class",
            resource_id=None,
            volume_list=[]
        )
        obj = uai_instance.create_service_object(
            uai_class,
            self.uai_mgr.uas_cfg
        )
        # Spot check the deployment, since exhaustive checking is
        # probably impractical
        self.assertEqual(obj.api_version, "v1")
        self.assertEqual(obj.kind, "Service")
        metadata = obj.metadata
        spec = obj.spec
        self.__compare_dicts(
            {
                'app': uai_instance.job_name
            },
            spec.selector
        )
        self.assertEqual(
            uai_instance.get_service_name(),
            metadata.name
        )
        self.__compare_dicts(
            uai_instance.gen_labels(uai_class),
            metadata.labels
        )

    # pylint: disable=missing-docstring
    def test_gen_connection_string(self):
        username = "testuser"
        uai_port = 12345
        uai_ip = "1.2.3.4"
        uai_connect_string = self.uai_mgr.gen_connection_string(
            username,
            uai_ip,
            uai_port
        )
        self.assertEqual("ssh testuser@1.2.3.4 -p 12345",
                         uai_connect_string)

    # pylint: disable=missing-docstring
    def test_gen_connection_string_no_port(self):
        username = "testuser"
        uai_port = 22
        uai_ip = "1.2.3.4"
        uai_connect_string = self.uai_mgr.gen_connection_string(
            username,
            uai_ip,
            uai_port
        )
        self.assertEqual("ssh testuser@1.2.3.4",
                         uai_connect_string)

    def test_image_lifecycle(self):
        """Test create_image, get_image, get_images, update_image,
        delete_image lifecycle to make sure it all works properly.
        This is intended as a more comprehensive test of images than
        could be done with individual calls tested separately.

        """
        img_name = "testimage"
        # Make the image and verify that the right result is returned
        expected_result = {'imagename': img_name, 'default': False}
        img = self.uas_mgr.create_image(imagename=img_name, default=None)
        self.assertIn('image_id', img)
        image_id = img['image_id']
        expected_result['image_id'] = image_id
        self.assertEqual(img, expected_result)
        # Get the image and verify that the right result is returned
        img = self.uas_mgr.get_image(image_id=image_id)
        self.assertEqual(img, expected_result)
        # Update the image and verify that the right result is returned
        img = self.uas_mgr.update_image(
            image_id,
            imagename=img_name,
            default=True
        )
        expected_result['default'] = True
        self.assertEqual(img, expected_result)
        # Get a list of images and make sure ours is in it
        imgs = self.uas_mgr.get_images()
        self.assertIsInstance(imgs, list)
        self.assertTrue(imgs)
        names_found = []
        for img in imgs:
            self.assertIsInstance(img, dict)
            self.assertIn('imagename', img)
            names_found.append(img['imagename'])
        self.assertIn(img_name, names_found)
        # Delete the image and make sure the right result is returned
        img = self.uas_mgr.delete_image(image_id=image_id)
        self.assertEqual(img, expected_result)
        # Get the list of images and make sure ours is no longer in it
        imgs = self.uas_mgr.get_images()
        self.assertIsInstance(imgs, list)
        names_found = []
        for img in imgs:
            self.assertIsInstance(img, dict)
            self.assertIn('imagename', img)
            names_found.append(img['imagename'])
        self.assertNotIn(img_name, names_found)

    # pylint: disable=too-many-arguments
    def __volume_lifecycle(
            self,
            volume_name,
            mount_path_1,
            mount_path_2,
            vol_desc_1,
            vol_desc_2
    ):
        """Common function for testing volume lifecycle operations.  This is
        more holistic testing of volumes, as opposed to testing each
        operation in a vaccuum, so that each operation can be tested
        with actual data behind it and actual results other than "not
        found".

        """
        # Set up the expected return
        expected_result = {
            'volumename': volume_name,
            'mount_path': mount_path_1,
            'volume_description': vol_desc_1,
        }
        # Create the volume and verify we see the expected results...
        vol = self.uas_mgr.create_volume(
            volume_name,
            mount_path=mount_path_1,
            vol_desc=json.dumps(vol_desc_1)
        )
        self.assertIn('volume_id', vol)
        volume_id = vol['volume_id']
        expected_result['volume_id'] = volume_id
        self.assertEqual(vol, expected_result)
        # Retrieve the volume and verify that we see the same results...
        vol = self.uas_mgr.get_volume(volume_id)
        self.assertEqual(vol, expected_result)
        # Modify the mount path with an update and verify we get the
        # expected result
        vol = self.uas_mgr.update_volume(
            volume_id=volume_id,
            volumename=volume_name,
            mount_path=mount_path_2
        )
        expected_result['mount_path'] = mount_path_2
        self.assertEqual(vol, expected_result)
        # Modify the source description with an update and verify we
        # get the expected result
        vol = self.uas_mgr.update_volume(
            volume_id=volume_id,
            volumename=volume_name,
            vol_desc=json.dumps(vol_desc_2)
        )
        expected_result['volume_description'] = vol_desc_2
        self.assertEqual(vol, expected_result)
        # Get the volume and verify that it contains the most recent state
        vol = self.uas_mgr.get_volume(volume_id)
        self.assertEqual(vol, expected_result)
        # List the volumes we have and make sure this one is in it
        vols = self.uas_mgr.get_volumes()
        self.assertIsInstance(vols, list)
        self.assertTrue(vols)  # not empty
        names_found = []
        for vol in vols:
            self.assertIsInstance(vol, dict)
            self.assertIn('volumename', vol)
            names_found.append(vol['volumename'])
        self.assertIn(volume_name, names_found)
        # Delete the volume and verify we get the last known state as a result.
        vol = self.uas_mgr.delete_volume(volume_id)
        self.assertEqual(vol, expected_result)
        # Verify that the volume is actually gone from the config
        with self.assertRaises(werkzeug.exceptions.NotFound):
            vol = self.uas_mgr.get_volume(volume_id)
        # List the volumes we have and make sure this one is not in it
        vols = self.uas_mgr.get_volumes()
        self.assertIsInstance(vols, list)
        names_found = []
        for vol in vols:
            self.assertIsInstance(vol, dict)
            self.assertIn('volumename', vol)
            names_found.append(vol['volumename'])
        self.assertNotIn(volume_name, names_found)

    # pylint: disable=missing-docstring
    def test_host_path_lifecycle(self):
        host_path_desc_1 = {
            'host_path': {
                'type': "DirectoryOrCreate",
                'path': "/host/var/stuff"
            }
        }
        host_path_desc_2 = {
            'host_path': {
                'type': "DirectoryOrCreate",
                'path': "/host/var/other_stuff"
            }
        }
        self.__volume_lifecycle(
            "host-path-volume-uas-mgr",
            "/var/mount_1",
            "/var/mount_2",
            host_path_desc_1,
            host_path_desc_2
        )

    # pylint: disable=missing-docstring
    def test_config_map_lifecycle(self):
        configmap_desc_1 = {
            'config_map': {
                'name': "my-funny-configmap"
            }
        }
        configmap_desc_2 = {
            'config_map': {
                'name': "my-funny-configmap",
                'default_mode': int("777", 8)
            }
        }
        self.__volume_lifecycle(
            "config-map-volume-uas-mgr",
            "/var/mount_1",
            "/var/mount_2",
            configmap_desc_1,
            configmap_desc_2
        )

    # pylint: disable=missing-docstring
    def test_secret_lifecycle(self):
        secret_desc_1 = {
            'secret': {
                'secret_name': "my-little-secret"
            }
        }
        secret_desc_2 = {
            'secret': {
                'secret_name': "my-little-secret",
                'default_mode': int("777", 8)
            }
        }
        self.__volume_lifecycle(
            "secret-volume-uas-mgr",
            "/var/mount_1",
            "/var/mount_2",
            secret_desc_1,
            secret_desc_2
        )

    # pylint: disable=missing-docstring
    def test_get_pod_age(self):
        self.assertEqual(self.uas_mgr.get_pod_age(None), None)
        self.assertEqual(self.uas_mgr.get_pod_age("wrong"), None)

        now = datetime.now(timezone.utc)
        self.assertEqual(self.uas_mgr.get_pod_age(now), "0m")
        self.assertEqual(self.uas_mgr.get_pod_age(now-timedelta(hours=1)),
                         "1h0m")
        self.assertEqual(self.uas_mgr.get_pod_age(now-timedelta(hours=25)),
                         "1d1h")
        self.assertEqual(self.uas_mgr.get_pod_age(now-timedelta(minutes=25)),
                         "25m")
        self.assertEqual(self.uas_mgr.get_pod_age(now-timedelta(days=89)),
                         "89d")
        # for days > 0, don't print minutes
        self.assertEqual(self.uas_mgr.get_pod_age(now-timedelta(minutes=1442)),
                         "1d")
        self.assertEqual(self.uas_mgr.get_pod_age(now-timedelta(minutes=1501)),
                         "1d1h")


if __name__ == '__main__':
    unittest.main()
