#!/usr/bin/python3

import unittest
import os
import werkzeug
import flask
from swagger_server.uas_lib.uai_mgr import UaiManager
from swagger_server.models.uai import UAI

app = flask.Flask(__name__)


class TestUasMgr(unittest.TestCase):

    os.environ["KUBERNETES_SERVICE_PORT"] = "443"
    os.environ["KUBERNETES_SERVICE_HOST"] = "127.0.0.1"
    deployment_name = "hal-234a85"
    with app.test_request_context('/'):
        uas_mgr = UaiManager()

    def test_uas_mgr_init(self):
        return

    def test_gen_labels(self):
        labels = self.uas_mgr.gen_labels(self.deployment_name)
        self.assertEqual(labels, {"app": self.deployment_name,
                                  "uas": "managed",
                                  "user": None})
        return

    def test_gen_connection_string(self):
        uai = UAI()
        uai.username = "testuser"
        uai.uai_port = 12345
        uai.uai_ip = "1.2.3.4"
        self.uas_mgr.gen_connection_string(uai)

        self.assertEqual("ssh testuser@1.2.3.4 -p 12345 -i ~/.ssh/id_rsa",
                         uai.uai_connect_string)

    def test_create_image(self):
        self.assertRaises(TypeError, self.uas_mgr.create_image, "test123")
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.create_image("test123", default=True)
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.create_image("colons:and/slashes:5000", default=True)
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.create_image("walleye:5000/repo/image:tag",
                                      default=False)
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.create_image("", default=False)
        # XXX - to implement after the underlying code works
        #       - test duplicate image
        #       - test duplicate with same default setting
        #       - test with empty list
        #       - test default false
        #       - test default true

    def test_update_image(self):
        self.assertRaises(TypeError, self.uas_mgr.update_image, "test123")
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.update_image("test123", default=True)
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.update_image("colons:and/slashes:5000", default=True)
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.update_image("walleye:5000/repo/image:tag",
                                      default=False)
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.update_image("", default=False)
        # XXX - to implement after the underlying code works
        #       - test duplicate image
        #       - test duplicate with default=True
        #       - test with empty list
        #       - test default false
        #       - test default true
        #       - update image not in the list

    def test_delete_image(self):
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.delete_image("colons:and/slashes:5000")
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.delete_image("")
        # XXX - to implement after the underlying code works
        #       - test delete image not in images list
        #       - test delete the default image
        #       - test delete the last image
        #       - test delete the first image
        #       - test delete all in a loop

    def test_get_image(self):
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.get_image("colons:and/slashes:5000")
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.get_image("")
        # XXX - to implement after the underlying code works
        #       - test get image not in images list
        #       - test get the last image
        #       - test get the first image
        #       - test get all images in a loop

    def test_create_volume(self):
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.create_volume("test123", type='FileOrCreate',
                                       mount_path='/var/foobar')
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.create_volume("test124", type='DirectoryOrCreate',
                                       host_path='/var/foobar')
        with self.assertRaises(werkzeug.exceptions.BadRequest):
            self.uas_mgr.create_volume("test123", type='ketchup',
                                       mount_path='/var/foobar')
        with self.assertRaises(werkzeug.exceptions.BadRequest):
            self.uas_mgr.create_volume("test124", type='',
                                       host_path='/var/foobar')
        with self.assertRaises(werkzeug.exceptions.BadRequest):
            self.uas_mgr.create_volume("abadname-", type='DirectoryOrCreate',
                                       host_path='/var/foobar')
        with self.assertRaises(werkzeug.exceptions.BadRequest):
            self.uas_mgr.create_volume("BaDName", type='DirectoryOrCreate',
                                       host_path='/var/foobar')
        # XXX - to implement after the underlying code works
        #       - test duplicate volume
        #       - test with empty volume list
        #       - test different types

    def test_update_volume(self):
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.update_volume("test123", type='FileOrCreate',
                                       mount_path='/var/foobar')
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.update_volume("test124", type='DirectoryOrCreate',
                                       host_path='/var/foobar')
        with self.assertRaises(werkzeug.exceptions.BadRequest):
            self.uas_mgr.update_volume("test123", type='walleye',
                                       mount_path='/var/foobar')
        with self.assertRaises(werkzeug.exceptions.BadRequest):
            self.uas_mgr.update_volume("test124", type='',
                                       host_path='/var/foobar')
        with self.assertRaises(werkzeug.exceptions.BadRequest):
            self.uas_mgr.update_volume("abadname-", type='DirectoryOrCreate',
                                       host_path='/var/foobar')
        with self.assertRaises(werkzeug.exceptions.BadRequest):
            self.uas_mgr.update_volume("BaDName", type='DirectoryOrCreate',
                                       host_path='/var/foobar')
        # XXX - to implement after the underlying code works
        #       - test with empty volume list
        #       - test with volume not in list
        #       - test different types

    def test_delete_volume(self):
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.delete_volume("volume_that_exists")
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.delete_volume("volume_that_doesnt_exist")
        # XXX - to implement after the underlying code works
        #       - test delete volume not in volumes list
        #       - test delete the last volume
        #       - test delete the first volume
        #       - test delete all in a loop

    def test_get_volume(self):
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.get_volume("volume_1")
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.get_volume("")
        # XXX - to implement after the underlying code works
        #       - test get volume not in volumes list
        #       - test get the last volume
        #       - test get the first volume
        #       - test get all volumes in a loop

    def test_get_volumes(self):
        with self.assertRaises(werkzeug.exceptions.NotImplemented):
            self.uas_mgr.get_volumes()

if __name__ == '__main__':
    unittest.main()
