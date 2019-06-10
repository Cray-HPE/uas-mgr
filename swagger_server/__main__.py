#!/usr/bin/env python3

import connexion

from swagger_server import encoder


def main():
    app = connexion.App(__name__)
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('swagger.yaml', arguments={'title': 'Cray User Access Service'}, base_path='/v1')
    app.run(port=8088)


if __name__ == '__main__':
    main()
