#!/usr/bin/python3
#
# MIT License
#
# (C) Copyright 2020, 2022 Hewlett Packard Enterprise Development LP
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
from uuid import uuid4
import json
import flask
import werkzeug

import swagger_server.controllers.uas_controller as uas_ctl
from swagger_server.uas_lib.uas_cfg import UasCfg

app = flask.Flask(__name__)  # pylint: disable=invalid-name


# pylint: disable=too-many-public-methods
class TestUasController(unittest.TestCase):
    """Tester for the UasController Class

    """
    os.environ["KUBERNETES_SERVICE_PORT"] = "443"
    os.environ["KUBERNETES_SERVICE_HOST"] = "127.0.0.1"
    uas_ctl.uas_cfg = UasCfg(uas_cfg='swagger_server/test/cray-uas-mgr.yaml')

    # pylint: disable=missing-docstring
    def test_delete_uai_by_name(self):
        with app.test_request_context('/'):
            resp = uas_ctl.delete_uai_by_name([])
        self.assertEqual(resp, "Must provide a list of UAI names to delete.")

    # pylint: disable=missing-docstring
    def test_get_uas_images(self):
        with app.test_request_context('/'):
            images = uas_ctl.get_uas_images()
        self.assertEqual(
            images,
            {
                'default_image': None,
                'image_list': None
            }
        )

    # pylint: disable=missing-docstring
    def test_get_uas_images_admin(self):
        with app.test_request_context('/'):
            imgs = uas_ctl.get_uas_images_admin()
        self.assertIsInstance(imgs, list)

    def __create_test_image(self, name, default=None):
        """Create an image with a given name and default setting and return
        its image_id.

        """
        with app.test_request_context('/'):
            resp = uas_ctl.create_uas_image_admin(imagename=name, default=default)
        self.assertIsInstance(resp, dict)
        self.assertIn('image_id', resp)
        return resp['image_id']

    def __delete_test_image(self, image_id):
        """ Delete an image based on its image ID and verify the result.

        """
        with app.test_request_context('/'):
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

    def __create_test_volume(self, volume_name=None):
        """Create a test volume through the API and make sure that works,
        return the volume ID so that it can be used for subsequent
        activities.

        """
        volume_name = "my-volume" if volume_name is None else volume_name
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
        vol_desc.seek(0)
        with app.test_request_context('/'):
            resp = uas_ctl.create_uas_volume_admin(
                volumename=volume_name,
                mount_path="/var/mnt",
                volume_description=vol_desc
            )
        self.assertIsInstance(resp, dict)
        self.assertIn('volume_id', resp)
        return resp['volume_id']

    def __delete_test_volume(self, volume_id):
        """Delete a volume by its volume_id and verify the result.

        """
        with app.test_request_context('/'):
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
    def test_get_uas_resources_admin(self):
        with app.test_request_context('/'):
            resources = uas_ctl.get_uas_resources_admin()
        self.assertIsInstance(resources, list)

    def __create_test_resource(self):
        """Create a test resource through the API and make sure that works,
        return the resource ID so that it can be used for subsequent
        activities.

        """
        limit = json.dumps(
            {
                'cpu': "200m",
                'memory': "500Mi"
            }
        )
        request = json.dumps(
            {
                'cpu': "100m",
                'memory': "200Mi"
            }
        )
        with app.test_request_context('/'):
            resp = uas_ctl.create_uas_resource_admin(
                comment="test comment",
                limit=limit,
                request=request
            )
        self.assertIsInstance(resp, dict)
        self.assertIn('resource_id', resp)
        return resp['resource_id']

    def __delete_test_resource(self, resource_id):
        """Delete a resource by its resource_id and verify the result.

        """
        with app.test_request_context('/'):
            resp = uas_ctl.delete_uas_resource_admin(resource_id=resource_id)
        self.assertIn('resource_id', resp)
        self.assertEqual(resource_id, resp['resource_id'])

    # pylint: disable=missing-docstring
    def test_get_uas_resource_admin(self):
        with app.test_request_context('/'):
            resp = uas_ctl.get_uas_resource_admin(resource_id=None)
            self.assertEqual(resp, "Must provide resource_id to get.")
            with self.assertRaises(werkzeug.exceptions.NotFound):
                _ = uas_ctl.get_uas_resource_admin(resource_id=str(uuid4()))

    # pylint: disable=missing-docstring
    def test_update_uas_resource_admin(self):
        with app.test_request_context('/'):
            resp = uas_ctl.update_uas_resource_admin(resource_id=None)
            self.assertEqual(resp, "Must provide resource_id to update.")
            with self.assertRaises(werkzeug.exceptions.NotFound):
                _ = uas_ctl.update_uas_resource_admin(resource_id=str(uuid4()))
            resource_id = self.__create_test_resource()
            limit = json.dumps(
                {
                    'cpu': "200m",
                    'memory': "500Mi"
                }
            )
            resp = uas_ctl.update_uas_resource_admin(
                resource_id=resource_id,
                limit=limit
            )
            self.assertIsInstance(resp, dict)
            self.assertIn('resource_id', resp)
            self.assertEqual(resource_id, resp['resource_id'])
            self.assertIn('limit', resp)
            self.assertIn("cpu", resp['limit'])
            self.assertIn("200m", resp['limit'])
            request = json.dumps(
                {
                    'cpu': "100m",
                    'memory': "200Mi"
                }
            )
            resp = uas_ctl.update_uas_resource_admin(
                resource_id=resource_id,
                request=request
            )
            self.assertIsInstance(resp, dict)
            self.assertIn('resource_id', resp)
            self.assertEqual(resource_id, resp['resource_id'])
            self.assertIn('request', resp)
            self.assertIn("cpu", resp['request'])
            self.assertIn("100m", resp['request'])
            self.__delete_test_resource(resource_id)

    # pylint: disable=missing-docstring
    def test_delete_uas_resource_admin(self):
        with app.test_request_context('/'):
            resp = uas_ctl.delete_uas_resource_admin(resource_id=None)
            self.assertEqual(resp, "Must provide resource_id to delete.")
            resp = uas_ctl.delete_uas_resource_admin(resource_id="")
            self.assertEqual(resp, "Must provide resource_id to delete.")
            with self.assertRaises(werkzeug.exceptions.NotFound):
                _ = uas_ctl.delete_uas_resource_admin(resource_id=str(uuid4()))

    # pylint: disable=too-many-locals
    def __create_test_uai_class(self):
        """Create a test class through the API that is set up for
        creating UAIs and make sure that works, return the class ID
        so that it can be used for subsequent activities.

        """
        comment = "Test UAI Class"
        default = True
        public_ip = False
        image_id = self.__create_test_image("Test image for test class")
        priority_class_name = "test-priority-class"
        namespace = "test-namespace"
        uai_creation_class = None
        uai_compute_network = True
        resource_id = self.__create_test_resource()
        volume_list = [self.__create_test_volume("my-uai-volume")]
        tolerations = '[{"key": "gpu_uais_only", "operator": "Exists"}]'
        timeout = '{"soft": "600", "hard": "3600", "warning": "60"}'
        service_account = "my-service-account"
        replicas = "1"
        with app.test_request_context('/'):
            resp = uas_ctl.create_uas_class_admin(
                comment=comment,
                default=default,
                public_ip=public_ip,
                image_id=image_id,
                priority_class_name=priority_class_name,
                namespace=namespace,
                uai_creation_class=uai_creation_class,
                uai_compute_network=uai_compute_network,
                resource_id=resource_id,
                volume_list=volume_list,
                tolerations=tolerations,
                timeout=timeout,
                service_account=service_account,
                replicas=replicas
            )
        self.assertIsInstance(resp, dict)
        self.assertIn('class_id', resp)
        return resp['class_id']

    # pylint: disable=too-many-locals
    def __create_test_broker_class(self):
        """Create a test class through the API that is set up for
        creating Brokers and make sure that works, return the class ID
        so that it can be used for subsequent activities.

        """
        comment = "Test Broker Class"
        default = False
        public_ip = True
        image_id = self.__create_test_image("Test image for broker class")
        priority_class_name = "test-broker-priority-class"
        namespace = "test-broker-namespace"
        uai_creation_class = self.__create_test_uai_class()
        uai_compute_network = False
        resource_id = self.__create_test_resource()
        volume_list = [self.__create_test_volume("my-broker-volume")]
        tolerations = '[{"key": "gpu_uais_only", "operator": "Exists"}]'
        timeout = None
        service_account = None
        replicas = "3"
        with app.test_request_context('/'):
            resp = uas_ctl.create_uas_class_admin(
                comment=comment,
                default=default,
                public_ip=public_ip,
                image_id=image_id,
                priority_class_name=priority_class_name,
                namespace=namespace,
                uai_creation_class=uai_creation_class,
                uai_compute_network=uai_compute_network,
                resource_id=resource_id,
                volume_list=volume_list,
                tolerations=tolerations,
                timeout=timeout,
                service_account=service_account,
                replicas=replicas
            )
        self.assertIsInstance(resp, dict)
        self.assertIn('class_id', resp)
        return resp['class_id']

    def __delete_test_class(self, class_id):
        """Delete a class by its class_id and verify the result.

        """
        with app.test_request_context('/'):
            resp = uas_ctl.delete_uas_class_admin(class_id=class_id)
            self.assertIn('class_id', resp)
            self.assertEqual(class_id, resp['class_id'])
            uai_creation_class = resp.get('uai_creation_class', None)
            self.assertIn('uai_compute_network', resp)
            resource_id = resp.get('resource_id', None)
            volume_list = resp.get('volume_list', [])
            image_id = resp.get("image_id", None)
            if uai_creation_class:
                self.__delete_test_class(uai_creation_class)
            if resource_id:
                self.__delete_test_resource(resource_id)
            if image_id:
                self.__delete_test_image(image_id)
            for volume_id in volume_list:
                self.__delete_test_volume(volume_id)

    # pylint: disable=missing-docstring
    def test_get_uas_class_admin(self):
        with app.test_request_context('/'):
            resp = uas_ctl.get_uas_class_admin(class_id=None)
            self.assertEqual(resp, "Must provide class_id (UUID) to get.")
            with self.assertRaises(werkzeug.exceptions.NotFound):
                _ = uas_ctl.get_uas_class_admin(class_id=str(uuid4()))

    # pylint: disable=missing-docstring
    def test_update_uas_class_admin(self):
        with app.test_request_context('/'):
            resp = uas_ctl.update_uas_class_admin(class_id=None)
            self.assertEqual(resp, "Must provide class_id of the UAI Class to update.")
            with self.assertRaises(werkzeug.exceptions.NotFound):
                _ = uas_ctl.update_uas_class_admin(class_id=str(uuid4()))
            class_id = self.__create_test_broker_class()
            comment = "Test Broker Class -- edited comment"
            default = False
            public_ip = True
            priority_class_name = "test-broker-priority-other-class"
            namespace = "test-broker--other-namespace"
            resp = uas_ctl.update_uas_class_admin(
                class_id=class_id,
                comment=comment,
                default=default,
                public_ip=public_ip,
                priority_class_name=priority_class_name,
                namespace=namespace,
                service_account="service-account"
            )
            self.assertIsInstance(resp, dict)
            self.assertIn('class_id', resp)
            self.assertEqual(class_id, resp['class_id'])
            self.assertIn('comment', resp)
            self.assertEqual(comment, resp['comment'])
            self.assertIn('default', resp)
            self.assertEqual(default, resp['default'])
            self.assertIn('public_ip', resp)
            self.assertEqual(public_ip, resp['public_ip'])
            self.assertIn('priority_class_name', resp)
            self.assertEqual(
                priority_class_name,
                resp['priority_class_name']
            )
            self.assertIn('namespace', resp)
            self.assertEqual(namespace, resp['namespace'])
            self.assertIn('service_account', resp)
            self.assertEqual('service-account', resp['service_account'])
            self.__delete_test_class(class_id)

    # pylint: disable=missing-docstring
    def test_delete_uas_class_admin(self):
        with app.test_request_context('/'):
            resp = uas_ctl.delete_uas_class_admin(class_id=None)
            self.assertEqual(resp, "Must provide class_id of UAI Class to delete.")
            resp = uas_ctl.delete_uas_class_admin(class_id="")
            self.assertEqual(resp, "Must provide class_id of UAI Class to delete.")
            with self.assertRaises(werkzeug.exceptions.NotFound):
                _ = uas_ctl.delete_uas_class_admin(class_id=str(uuid4()))

    # There is currently no kubernetes API mocking available to allow me
    # to run this test.  Add this back if we ever get kubernetes API mocking
    # that permits mock jobs to be found in a mock Kubernetes cluster.
    #
    # pylint: disable=missing-docstring
    def disabled_test_delete_local_config_admin(self):
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
            resource_id = self.__create_test_resource()
            resp = uas_ctl.get_uas_resource_admin(resource_id=resource_id)
            self.assertIn('resource_id', resp)
            self.assertEqual(resource_id, resp['resource_id'])
            class_id = self.__create_test_uai_class()
            resp = uas_ctl.get_uas_class_admin(class_id=class_id)
            self.assertIn('class_id', resp)
            self.assertEqual(class_id, resp['class_id'])
            resp = uas_ctl.delete_local_config_admin()
            with self.assertRaises(werkzeug.exceptions.NotFound):
                _ = uas_ctl.get_uas_volume_admin(volume_id=volume_id)
            with self.assertRaises(werkzeug.exceptions.NotFound):
                _ = uas_ctl.get_uas_image_admin(image_id=image_id)
            with self.assertRaises(werkzeug.exceptions.NotFound):
                _ = uas_ctl.get_uas_resource_admin(resource_id=resource_id)
            with self.assertRaises(werkzeug.exceptions.NotFound):
                _ = uas_ctl.get_uas_class_admin(class_id=class_id)


if __name__ == '__main__':
    unittest.main()
