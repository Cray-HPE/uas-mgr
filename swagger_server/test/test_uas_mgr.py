#!/usr/bin/python3

import unittest
import os

from swagger_server.uas_lib.uan_mgr import UanManager
from swagger_server.models.uan import UAN

class TestUasMgr(unittest.TestCase):

    os.environ["KUBERNETES_SERVICE_PORT"]="443"
    os.environ["KUBERNETES_SERVICE_HOST"]="127.0.0.1"
    deployment_name = "hal-234a85"
    uas_mgr = UanManager()

    def test_uas_mgr_init(self):
        return

    def test_gen_labels(self):
        labels = self.uas_mgr.gen_labels(self.deployment_name)
        self.assertEqual(labels, {"app": self.deployment_name, "uas": "managed"})
        return

    def test_gen_connection_string(self):
        uan = UAN()
        uan.username = "testuser"
        uan.uan_port = 12345
        uan.uan_ip = "1.2.3.4"
        self.uas_mgr.gen_connection_string(uan)

        self.assertEqual("ssh testuser@1.2.3.4 -p 12345 -i ~/.ssh/id_rsa",
                         uan.uan_connect_string)


if __name__ == '__main__':
    unittest.main()
