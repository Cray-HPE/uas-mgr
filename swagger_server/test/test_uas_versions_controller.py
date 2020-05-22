#!/usr/bin/python3
#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#
"""Version Controller Test

"""

import unittest

import swagger_server.controllers.versions_controller as versions_ctl


class TestUasVersionsController(unittest.TestCase):
    """Test the version controller.

    """
    def test_root_get(self):
        """Test getting the 'v1' root path.

        """
        self.assertEqual('v1', versions_ctl.root_get())


if __name__ == '__main__':
    unittest.main()
