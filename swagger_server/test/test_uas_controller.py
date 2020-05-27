#!/usr/bin/python3

#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#
# pylint: disable=missing-docstring

import unittest
import os
import flask
import werkzeug

import swagger_server.controllers.uas_controller as uas_ctl
from swagger_server import version
from swagger_server.uas_lib.uas_cfg import UasCfg
from swagger_server.uas_lib.uai_mgr import UaiManager

app = flask.Flask(__name__)  # pylint: disable=invalid-name


# pylint: disable=too-many-public-methods
class TestUasController(unittest.TestCase):
    """Tester for the UasController Class

    """
    os.environ["KUBERNETES_SERVICE_PORT"] = "443"
    os.environ["KUBERNETES_SERVICE_HOST"] = "127.0.0.1"
    uas_ctl.uas_cfg = UasCfg(uas_cfg='swagger_server/test/cray-uas-mgr.yaml')
    with app.test_request_context('/'):
        uas_ctl.uas_mgr = UaiManager()

    # pylint: disable=missing-docstring
    def test_delete_uai_by_name(self):
        resp = uas_ctl.delete_uai_by_name([])
        self.assertEqual(resp, "Must provide a list of UAI names to delete.")

    # pylint: disable=missing-docstring
    def test_get_uas_images(self):
        images = uas_ctl.get_uas_images()
        self.assertEqual(images,
                         {'default_image':
                          'dtr.dev.cray.com:443/cray/cray-uas-sles15:latest',
                          'image_list':
                          ['dtr.dev.cray.com:443/cray/cray-uas-sles15:latest']})

    # pylint: disable=missing-docstring
    def test_get_uas_mgr_info(self):
        info = uas_ctl.get_uas_mgr_info()
        self.assertEqual(info,
                         {'service_name': 'cray-uas-mgr',
                          'version': version})

    # pylint: disable=missing-docstring
    def test_delete_uas_image(self):
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            uas_ctl.delete_uas_image_deprecated("fred")

    # pylint: disable=missing-docstring
    def test_create_uas_image(self):
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            uas_ctl.create_uas_image_deprecated(None, None)
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            uas_ctl.create_uas_image_deprecated("fred", None)
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            uas_ctl.create_uas_image_deprecated("fred", False)

    # pylint: disable=missing-docstring
    def test_update_uas_image(self):
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            uas_ctl.update_uas_image_deprecated(None, None)
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            uas_ctl.update_uas_image_deprecated("fred", None)
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            uas_ctl.update_uas_image_deprecated("fred", False)

    # pylint: disable=missing-docstring
    def test_get_uas_image(self):
        resp = uas_ctl.get_uas_image(None)
        self.assertEqual(resp, "Must provide imagename to get.")

    # pylint: disable=missing-docstring
    def test_delete_uas_volume(self):
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            uas_ctl.delete_uas_volume_deprecated(None)

    # pylint: disable=missing-docstring
    def test_create_uas_volume(self):
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            uas_ctl.create_uas_volume_deprecated(None, None)
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            uas_ctl.create_uas_volume_deprecated("fred", None)

    # pylint: disable=missing-docstring
    def test_update_uas_volume(self):
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            uas_ctl.update_uas_volume_deprecated(None, None)
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            uas_ctl.update_uas_volume_deprecated("fred", None)

    # pylint: disable=missing-docstring
    def test_get_uas_volume(self):
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            uas_ctl.get_uas_volume_deprecated(None)

    # pylint: disable=missing-docstring
    def test_get_uas_images_admin(self):
        imgs = uas_ctl.get_uas_images_admin()
        self.assertIsInstance(imgs, list)

    # pylint: disable=missing-docstring
    def test_create_uas_image_admin(self):
        ret = uas_ctl.create_uas_image_admin(None)
        self.assertEqual(ret, "Must provide imagename to create.")
        ret = uas_ctl.create_uas_image_admin("")
        self.assertEqual(ret, "Must provide imagename to create.")
        ret = uas_ctl.create_uas_image_admin("first_image")
        self.assertIsInstance(ret, dict)
        ret = uas_ctl.create_uas_image_admin("second-image", default=False)
        self.assertIsInstance(ret, dict)

    # pylint: disable=missing-docstring
    def test_get_uas_image_admin(self):
        ret = uas_ctl.get_uas_image_admin(None)
        self.assertEqual(ret, "Must provide imagename to get.")
        ret = uas_ctl.get_uas_image_admin("")
        self.assertEqual(ret, "Must provide imagename to get.")
        with self.assertRaises(werkzeug.exceptions.NotFound):
            _ = uas_ctl.get_uas_image_admin("not-there")

    # pylint: disable=missing-docstring
    def test_update_uas_image_admin(self):
        ret = uas_ctl.update_uas_image_admin(None)
        self.assertEqual(ret, "Must provide imagename to update.")
        ret = uas_ctl.update_uas_image_admin("")
        self.assertEqual(ret, "Must provide imagename to update.")
        with self.assertRaises(werkzeug.exceptions.NotFound):
            _ = uas_ctl.update_uas_image_admin("not-there")

    # pylint: disable=missing-docstring
    def test_delete_uas_image_admin(self):
        ret = uas_ctl.delete_uas_image_admin(None)
        self.assertEqual(ret, "Must provide imagename to delete.")
        ret = uas_ctl.delete_uas_image_admin("")
        self.assertEqual(ret, "Must provide imagename to delete.")
        with self.assertRaises(werkzeug.exceptions.NotFound):
            _ = uas_ctl.delete_uas_image_admin("not-there")

    # pylint: disable=missing-docstring
    def test_get_uas_volumes_admin(self):
        vols = uas_ctl.get_uas_volumes_admin()
        self.assertIsInstance(vols, list)

    # pylint: disable=missing-docstring
    def test_create_uas_volume_admin(self):
        ret = uas_ctl.create_uas_volume_admin(
            None,
            mount_path=None,
            volume_description=None
        )
        self.assertEqual(ret, "Must provide volumename to create.")
        ret = uas_ctl.create_uas_volume_admin(
            "",
            mount_path=None,
            volume_description=None
        )
        self.assertEqual(ret, "Must provide volumename to create.")
        ret = uas_ctl.create_uas_volume_admin(
            "my-volume",
            mount_path=None,
            volume_description=None
        )
        self.assertEqual(ret, "Must provide mount_path.")
        ret = uas_ctl.create_uas_volume_admin(
            "my-volume",
            mount_path="/var/mnt",
            volume_description=None
        )
        self.assertEqual(ret, "Must provide volume_description.")
        ret = uas_ctl.create_uas_volume_admin(
            "my-volume",
            mount_path="/var/mnt",
            volume_description={
                'secret': {
                    'secretname': "my-little-secret"
                }
            }
        )
        self.assertIsInstance(ret, dict)

    # pylint: disable=missing-docstring
    def test_get_uas_volume_admin(self):
        ret = uas_ctl.get_uas_volume_admin(None)
        self.assertEqual(ret, "Must provide volumename to get.")
        ret = uas_ctl.get_uas_volume_admin("")
        self.assertEqual(ret, "Must provide volumename to get.")
        with self.assertRaises(werkzeug.exceptions.NotFound):
            _ = uas_ctl.get_uas_volume_admin("not-there")

    # pylint: disable=missing-docstring
    def test_update_uas_volume_admin(self):
        ret = uas_ctl.update_uas_volume_admin(None)
        self.assertEqual(ret, "Must provide volumename to update.")
        ret = uas_ctl.update_uas_volume_admin("")
        self.assertEqual(ret, "Must provide volumename to update.")
        with self.assertRaises(werkzeug.exceptions.NotFound):
            _ = uas_ctl.update_uas_volume_admin("not-there")

    # pylint: disable=missing-docstring
    def delete_uas_volume_admin(self):
        ret = uas_ctl.delete_uas_volume_admin(None)
        self.assertEqual(ret, "Must provide volumename to delete.")
        ret = uas_ctl.delete_uas_volume_admin("")
        self.assertEqual(ret, "Must provide volumename to delete.")
        with self.assertRaises(werkzeug.exceptions.NotFound):
            _ = uas_ctl.delete_uas_volume_admin("not-there")


if __name__ == '__main__':
    unittest.main()
