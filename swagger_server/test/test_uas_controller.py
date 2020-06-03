#!/usr/bin/python3

#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#
# pylint: disable=missing-docstring

import unittest
import os
from uuid import uuid4
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
        print("images = %s" % str(images))
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
        with app.test_request_context('/'):
            imgs = uas_ctl.get_uas_images_admin()
        self.assertIsInstance(imgs, list)

    # pylint: disable=missing-docstring
    def test_create_uas_image_admin(self):
        with app.test_request_context('/'):
            resp = uas_ctl.create_uas_image_admin(imagename=None)
            self.assertEqual(resp, "Must provide imagename to create.")
            resp = uas_ctl.create_uas_image_admin(imagename="")
            self.assertEqual(resp, "Must provide imagename to create.")
            resp = uas_ctl.create_uas_image_admin(imagename="first_image")
            self.assertIsInstance(resp, dict)
            self.assertIn('image_id', resp)
            _ = uas_ctl.delete_uas_image_admin(image_id=resp['image_id'])
            resp = uas_ctl.create_uas_image_admin(imagename="second-image",
                                                  default=False)
            self.assertIsInstance(resp, dict)
            self.assertIn('image_id', resp)
            _ = uas_ctl.delete_uas_image_admin(image_id=resp['image_id'])

    # pylint: disable=missing-docstring
    def test_get_uas_image_admin(self):
        with app.test_request_context('/'):
            resp = uas_ctl.get_uas_image_admin(image_id=None)
            self.assertEqual(resp, "Must provide image_id to get.")
            resp = uas_ctl.get_uas_image_admin(image_id="")
            self.assertEqual(resp, "Must provide image_id to get.")
            with self.assertRaises(werkzeug.exceptions.NotFound):
                _ = uas_ctl.get_uas_image_admin(image_id=str(uuid4()))

    # pylint: disable=missing-docstring
    def test_update_uas_image_admin(self):
        with app.test_request_context('/'):
            resp = uas_ctl.update_uas_image_admin(image_id=None)
            self.assertEqual(resp, "Must provide image_id to update.")
            resp = uas_ctl.update_uas_image_admin(image_id="")
            self.assertEqual(resp, "Must provide image_id to update.")
            with self.assertRaises(werkzeug.exceptions.NotFound):
                _ = uas_ctl.update_uas_image_admin(image_id=str(uuid4()))

    # pylint: disable=missing-docstring
    def test_delete_uas_image_admin(self):
        with app.test_request_context('/'):
            resp = uas_ctl.delete_uas_image_admin(image_id=None)
            self.assertEqual(resp, "Must provide image_id to delete.")
            resp = uas_ctl.delete_uas_image_admin(image_id="")
            self.assertEqual(resp, "Must provide image_id to delete.")
            with self.assertRaises(werkzeug.exceptions.NotFound):
                _ = uas_ctl.delete_uas_image_admin(image_id=str(uuid4()))

    # pylint: disable=missing-docstring
    def test_get_uas_volumes_admin(self):
        with app.test_request_context('/'):
            vols = uas_ctl.get_uas_volumes_admin()
        self.assertIsInstance(vols, list)

    # pylint: disable=missing-docstring
    def test_create_uas_volume_admin(self):
        with app.test_request_context('/'):
            resp = uas_ctl.create_uas_volume_admin(
                volumename=None,
                mount_path=None,
                volume_description=None
            )
            self.assertEqual(resp, "Must provide volumename to create.")
            resp = uas_ctl.create_uas_volume_admin(
                volumename="",
                mount_path=None,
                volume_description=None
            )
            self.assertEqual(resp, "Must provide volumename to create.")
            resp = uas_ctl.create_uas_volume_admin(
                volumename="my-volume",
                mount_path=None,
                volume_description=None
            )
            self.assertEqual(resp, "Must provide mount_path.")
            resp = uas_ctl.create_uas_volume_admin(
                volumename="my-volume",
                mount_path="/var/mnt",
                volume_description=None
            )
            self.assertEqual(resp, "Must provide volume_description.")
            resp = uas_ctl.create_uas_volume_admin(
                volumename="my-volume",
                mount_path="/var/mnt",
                volume_description={
                    'secret': {
                        'secret_name': "my-little-secret"
                    }
                }
            )
            self.assertIsInstance(resp, dict)

    # pylint: disable=missing-docstring
    def test_get_uas_volume_admin(self):
        with app.test_request_context('/'):
            resp = uas_ctl.get_uas_volume_admin(volume_id=None)
            self.assertEqual(resp, "Must provide volume_id to get.")
            resp = uas_ctl.get_uas_volume_admin(volume_id="")
            self.assertEqual(resp, "Must provide volume_id to get.")
            with self.assertRaises(werkzeug.exceptions.NotFound):
                _ = uas_ctl.get_uas_volume_admin(volume_id=str(uuid4()))

    # pylint: disable=missing-docstring
    def test_update_uas_volume_admin(self):
        with app.test_request_context('/'):
            resp = uas_ctl.update_uas_volume_admin(volume_id=None)
            self.assertEqual(resp, "Must provide volume_id to update.")
            resp = uas_ctl.update_uas_volume_admin(volume_id="")
            self.assertEqual(resp, "Must provide volume_id to update.")
            with self.assertRaises(werkzeug.exceptions.NotFound):
                _ = uas_ctl.update_uas_volume_admin(volume_id=str(uuid4()))

    # pylint: disable=missing-docstring
    def delete_uas_volume_admin(self):
        with app.test_request_context('/'):
            resp = uas_ctl.delete_uas_volume_admin(volume_id=None)
            self.assertEqual(resp, "Must provide volume_id to delete.")
            resp = uas_ctl.delete_uas_volume_admin(volume_id="")
            self.assertEqual(resp, "Must provide volume_id to delete.")
            with self.assertRaises(werkzeug.exceptions.NotFound):
                _ = uas_ctl.delete_uas_volume_admin(volume_id=str(uuid4()))


if __name__ == '__main__':
    unittest.main()
