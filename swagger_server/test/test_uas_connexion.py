#!/usr/bin/env python3

#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#

import connexion
import unittest

from swagger_server import encoder


class TestUasConnexion(unittest.TestCase):
    app = connexion.App(__name__)
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('/usr/src/app/swagger_server/swagger.yaml', arguments={'title': 'Cray User Access Service'}, base_path='/v1')

if __name__ == '__main__':
    unittest.main()
