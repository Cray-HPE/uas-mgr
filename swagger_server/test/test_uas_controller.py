#!/usr/bin/python3

#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#
# pylint: disable=missing-docstring

import unittest
import os
import io
from uuid import uuid4
import json
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
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            uas_ctl.get_uas_image_deprecated(None)

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
    def test_get_uas_volumes(self):
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            uas_ctl.get_uas_volumes_deprecated()

    # pylint: disable=missing-docstring
    def test_get_uas_images_admin(self):
        with app.test_request_context('/'):
            imgs = uas_ctl.get_uas_images_admin()
        self.assertIsInstance(imgs, list)

    def __create_test_image(self, name, default=None):
        """Create an image with a given name and default setting and return
        its image_id.

        """
        resp = uas_ctl.create_uas_image_admin(imagename=name, default=default)
        self.assertIsInstance(resp, dict)
        self.assertIn('image_id', resp)
        return resp['image_id']

    def __delete_test_image(self, image_id):
        """ Delete an image based on its image ID and verify the result.

        """
        resp = uas_ctl.delete_uas_image_admin(image_id=image_id)
        self.assertIsInstance(resp, dict)
        self.assertIn('image_id', resp)
        self.assertEqual(image_id, resp['image_id'])

    # pylint: disable=missing-docstring
    def test_create_uas_image_admin(self):
        with app.test_request_context('/'):
            resp = uas_ctl.create_uas_image_admin(imagename=None)
            self.assertEqual(resp, "Must provide imagename to create.")
            resp = uas_ctl.create_uas_image_admin(imagename="")
            self.assertEqual(resp, "Must provide imagename to create.")
            image_id = self.__create_test_image("first_image")
            self.__delete_test_image(image_id)
            image_id = self.__create_test_image(
                name="second-image",
                default=False
            )
            self.__delete_test_image(image_id)

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

    def __create_test_volume(self):
        """Create a test volume through the API and make sure that works,
        return the volume ID so that it can be used for subsequent
        activities.

        """
        vol_desc = io.BytesIO()
        vol_desc.write(
            bytes(
                json.dumps(
                    {
                        'secret': {
                            'secret_name': "my-little-secret"
                        }
                    }
                ),
                encoding='utf8'
            )
        )
        resp = uas_ctl.create_uas_volume_admin(
            volumename="my-volume",
            mount_path="/var/mnt",
            volume_description=vol_desc
        )
        self.assertIsInstance(resp, dict)
        self.assertIn('volume_id', resp)
        return resp['volume_id']

    def __delete_test_volume(self, volume_id):
        """Delete a volume by its volume_id and verify the result.

        """
        resp = uas_ctl.delete_uas_volume_admin(volume_id=volume_id)
        self.assertIn('volume_id', resp)
        self.assertEqual(volume_id, resp['volume_id'])

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
            volume_id = self.__create_test_volume()
            self.__delete_test_volume(volume_id)

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
            volume_id = self.__create_test_volume()
            vol_desc = io.BytesIO()
            vol_desc.write(
                bytes(
                    json.dumps(
                        {
                            'secret': {
                                'secret_name': "my-other-little-secret"
                            }
                        }
                    ),
                    encoding='utf8'
                )
            )
            resp = uas_ctl.update_uas_volume_admin(
                volume_id=volume_id,
                volume_description=vol_desc
            )
            self.assertIsInstance(resp, dict)
            self.assertIn('volume_id', resp)
            self.assertEqual(volume_id, resp['volume_id'])
            self.assertIn('volume_description', resp)
            self.assertIn('secret', resp['volume_description'])
            secret = resp['volume_description']['secret']
            self.assertIn('secret_name', secret)
            self.assertEqual(
                secret['secret_name'],
                "my-other-little-secret"
            )
            self.__delete_test_volume(volume_id)

    # pylint: disable=missing-docstring
    def test_delete_uas_volume_admin(self):
        with app.test_request_context('/'):
            resp = uas_ctl.delete_uas_volume_admin(volume_id=None)
            self.assertEqual(resp, "Must provide volume_id to delete.")
            resp = uas_ctl.delete_uas_volume_admin(volume_id="")
            self.assertEqual(resp, "Must provide volume_id to delete.")
            with self.assertRaises(werkzeug.exceptions.NotFound):
                _ = uas_ctl.delete_uas_volume_admin(volume_id=str(uuid4()))

    # pylint: disable=missing-docstring
    def test_delete_local_config_admin(self):
        with app.test_request_context('/'):
            # Make sure there is something in the local configuration
            volume_id = self.__create_test_volume()
            resp = uas_ctl.get_uas_volume_admin(volume_id=volume_id)
            self.assertIn('volume_id', resp)
            self.assertEqual(volume_id, resp['volume_id'])
            image_id = self.__create_test_image("locally_configured_image")
            resp = uas_ctl.get_uas_image_admin(image_id=image_id)
            self.assertIn('image_id', resp)
            self.assertEqual(image_id, resp['image_id'])
            resp = uas_ctl.delete_local_config_admin()
            with self.assertRaises(werkzeug.exceptions.NotFound):
                _ = uas_ctl.get_uas_volume_admin(volume_id=volume_id)
            with self.assertRaises(werkzeug.exceptions.NotFound):
                _ = uas_ctl.get_uas_image_admin(image_id=image_id)


if __name__ == '__main__':
    unittest.main()
