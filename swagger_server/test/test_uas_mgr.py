#!/usr/bin/python3

#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#
# pylint: disable=missing-docstring

import unittest
import os
from datetime import datetime, timezone, timedelta
import werkzeug
import flask
from swagger_server.uas_lib.uai_mgr import UaiManager
from swagger_server.models.uai import UAI

app = flask.Flask(__name__)  # pylint: disable=invalid-name


class TestUasMgr(unittest.TestCase):
    """Tester for the UasMgr Class

    """
    os.environ["KUBERNETES_SERVICE_PORT"] = "443"
    os.environ["KUBERNETES_SERVICE_HOST"] = "127.0.0.1"
    deployment_name = "hal-234a85"
    with app.test_request_context('/'):
        uas_mgr = UaiManager()

    # pylint: disable=missing-docstring,no-self-use
    def test_uas_mgr_init(self):
        return

    # pylint: disable=missing-docstring
    def test_gen_labels(self):
        labels = self.uas_mgr.gen_labels(self.deployment_name)
        self.assertEqual(labels, {"app": self.deployment_name,
                                  "uas": "managed",
                                  "user": None})

    # pylint: disable=missing-docstring
    def test_gen_connection_string(self):
        uai = UAI()
        uai.username = "testuser"
        uai.uai_port = 12345
        uai.uai_ip = "1.2.3.4"
        uai.uai_connect_string = self.uas_mgr.gen_connection_string(uai)

        self.assertEqual("ssh testuser@1.2.3.4 -p 12345 -i ~/.ssh/id_rsa",
                         uai.uai_connect_string)

    # pylint: disable=missing-docstring
    def test_gen_connection_string_no_port(self):
        uai = UAI()
        uai.username = "testuser"
        uai.uai_port = 22
        uai.uai_ip = "1.2.3.4"
        uai.uai_connect_string = self.uas_mgr.gen_connection_string(uai)

        self.assertEqual("ssh testuser@1.2.3.4 -i ~/.ssh/id_rsa",
                         uai.uai_connect_string)

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
            vol_desc=vol_desc_1
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
            vol_desc=vol_desc_2
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
        self.assertEqual(UaiManager.get_pod_age(None), None)
        self.assertEqual(UaiManager.get_pod_age("wrong"), None)

        now = datetime.now(timezone.utc)
        self.assertEqual(UaiManager.get_pod_age(now), "0m")
        self.assertEqual(UaiManager.get_pod_age(now-timedelta(hours=1)),
                         "1h0m")
        self.assertEqual(UaiManager.get_pod_age(now-timedelta(hours=25)),
                         "1d1h")
        self.assertEqual(UaiManager.get_pod_age(now-timedelta(minutes=25)),
                         "25m")
        self.assertEqual(UaiManager.get_pod_age(now-timedelta(days=89)),
                         "89d")
        # for days > 0, don't print minutes
        self.assertEqual(UaiManager.get_pod_age(now-timedelta(minutes=1442)),
                         "1d")
        self.assertEqual(UaiManager.get_pod_age(now-timedelta(minutes=1501)),
                         "1d1h")


if __name__ == '__main__':
    unittest.main()
