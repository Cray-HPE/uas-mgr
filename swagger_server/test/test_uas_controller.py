#!/usr/bin/python3

#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#
# pylint: disable=missing-docstring

import unittest
import os
import flask

import swagger_server.controllers.uas_controller as uas_ctl
from swagger_server import version
from swagger_server.uas_lib.uas_cfg import UasCfg
from swagger_server.uas_lib.uai_mgr import UaiManager

app = flask.Flask(__name__)  # pylint: disable=invalid-name


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
        resp = uas_ctl.delete_uas_image(None)
        self.assertEqual(resp, "Must provide imagename to delete.")

    # pylint: disable=missing-docstring
    def test_create_uas_image(self):
        resp = uas_ctl.create_uas_image(None, None)
        self.assertEqual(resp, "Must provide imagename to create.")
        resp = uas_ctl.create_uas_image("fred", None)
        self.assertEqual(resp, "Must provide true/false for default image.")

    # pylint: disable=missing-docstring
    def test_update_uas_image(self):
        resp = uas_ctl.update_uas_image(None, None)
        self.assertEqual(resp, "Must provide imagename to update.")
        resp = uas_ctl.update_uas_image("fred", None)
        self.assertEqual(resp, "Must provide true/false for default image.")

    # pylint: disable=missing-docstring
    def test_get_uas_image(self):
        resp = uas_ctl.get_uas_image(None)
        self.assertEqual(resp, "Must provide imagename to get.")

    # pylint: disable=missing-docstring
    def test_delete_uas_volume(self):
        resp = uas_ctl.delete_uas_volume(None)
        self.assertEqual(resp, "Must provide volumename to delete.")

    # pylint: disable=missing-docstring
    def test_create_uas_volume(self):
        resp = uas_ctl.create_uas_volume(None, None)
        self.assertEqual(resp, "Must provide volumename to create.")
        resp = uas_ctl.create_uas_volume("fred", None)
        self.assertEqual(resp, "Must provide type to create.")

    # pylint: disable=missing-docstring
    def test_update_uas_volume(self):
        resp = uas_ctl.update_uas_volume(None, None)
        self.assertEqual(resp, "Must provide volumename to update.")
        resp = uas_ctl.update_uas_volume("fred", None)
        self.assertEqual(resp, "Must provide type to update.")

    # pylint: disable=missing-docstring
    def test_get_uas_volume(self):
        resp = uas_ctl.get_uas_volume(None)
        self.assertEqual(resp, "Must provide volumename to get.")


if __name__ == '__main__':
    unittest.main()
