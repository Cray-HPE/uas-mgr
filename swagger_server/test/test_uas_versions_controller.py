#!/usr/bin/python3

import unittest

import swagger_server.controllers.versions_controller as versions_ctl


class TestUasVersionsController(unittest.TestCase):

    def test_root_get(self):
        self.assertEqual('v1', versions_ctl.root_get())


if __name__ == '__main__':
    unittest.main()
