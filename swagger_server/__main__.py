#!/usr/bin/env python3

#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#
"""
Main entrypoint for UAS Manager
"""

import connexion

from swagger_server import encoder


def main():
    """Main entrypoint for UAS Manager

    """
    app = connexion.App(__name__)
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api(
        'swagger.yaml',
        arguments={
            'title': 'Cray User Access Service'
        },
        base_path='/v1'
    )
    app.run(port=8088)


if __name__ == '__main__':
    main()
