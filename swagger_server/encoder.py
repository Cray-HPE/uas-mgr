#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#
"""
JSON Encoder to support UAS
"""

import six
from connexion.apps.flask_app import FlaskJSONEncoder

from swagger_server.models.base_model_ import Model


class JSONEncoder(FlaskJSONEncoder):  # pylint: disable=too-few-public-methods
    """Encoder Class for UAS

    """
    include_nulls = False

    def default(self, o):  # pylint: disable=invalid-name
        """Default encoder

        """
        if isinstance(o, Model):
            dikt = {}
            for attr, _ in six.iteritems(o.swagger_types):
                value = getattr(o, attr)
                if value is None and not self.include_nulls:
                    continue
                attr = o.attribute_map[attr]
                dikt[attr] = value
            return dikt
        return FlaskJSONEncoder.default(self, o)
