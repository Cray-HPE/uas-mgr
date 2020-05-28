"""Data Model for UAI Volumes

Copyright 2020, Cray Inc. All rights reserved.

"""
from __future__ import absolute_import
import re
from etcd3_model import Etcd3Attr
from swagger_server import ETCD_PREFIX, version
from swagger_server.uas_data_model.uas_data_model import UASDataModel
from kubernetes import client


class UAIVolume(UASDataModel):
    """
    UAI Volume Data Model

    NOTE: This corresponds to the AdminVolume object type in the API spec.  The
          Volume object type can be derived from this, but that is done at the
          API paths that reflect Volume objects not in the data model.

        Fields:
            volumename: the name of the volume (string)
            kind: "UAIVolume"
            data_version: the data model version for this instance
            mount_path: the mount path to the volume within the UAI container
            volume_description: the JSON K8s description of the underlying
                                volume
    """
    model_prefix = "%s/%s" % (ETCD_PREFIX, "UAIVolume")

    # The Object ID used to locate each volume instance
    volumename = Etcd3Attr(is_object_id=True)  # Read-only after creation

    # The kind of object that the data here represent.  Should always
    # contain "UAIVolume".  Protects against stray data types.
    kind = Etcd3Attr(default="UAIVolume")  # Read only

    # The Data Model version corresponding to this UAI Volume data.
    # Will always be equal to the UAS Manager service version version
    # under which the data were stored in ETCD.  Protects against
    # incompatible data.
    api_version = Etcd3Attr(default=version)  # Read only

    # The path within the UAI container where the volume is mounted.
    mount_path = Etcd3Attr(default=None)

    # The K8s description (JSON string) of what the volume is.
    volume_description = Etcd3Attr(default=None)

    # Some data validation and interrogation methods having to do with
    # Volumes to help with managing them.
    @staticmethod
    def get_volume_source_type(vol_desc):
        """Return the key used to identify the type of volume source provided
        by a volume description.  This is the key (one and only one)
        in the outermost dictionary containing the volume description.

        """
        keys = list(vol_desc.keys())
        if not keys:
            return None
        return keys[0]

    @staticmethod
    def is_valid_volume_source_type(vol_desc):
        """Check the source type in the volume description provided against
        the current set of valid source type accepted by
        client.V1Volume() and make sure it is valid.

        """
        tmp_dict = client.V1Volume(name="empty_source").to_dict()
        # All but one of the elements in the dictionary returned from
        # above is a valid type name / value pair.  Since no source
        # was given, all of the valid type names are keys with a value
        # of None.  The name is a key with a non-None value.
        valid_types = [key for key in tmp_dict if tmp_dict[key] is None]
        type_under_test = UAIVolume.get_volume_source_type(vol_desc)
        return type_under_test in valid_types

    @staticmethod
    def is_valid_volume_name(volume_name):
        """
        checks whether the passed in volume name is valid or not
        k8s volume names need to be valid DNS-1123 name, which means
        lower case alphanumeric characters or '-', and must start
        and end with an alphanumeric character.

        :return: returns True if volume name is valid, False if not.
        :rtype bool
        """
        regex = re.compile('^(?![0-9]+$)(?!-)[a-z0-9-]{1,63}(?<!-)$')
        return regex.match(volume_name) is not None

    @staticmethod
    def is_valid_host_path_mount_type(mount_type):
        """
        checks whether the mount_type is a valid one or not
        :return: returns True if the passed in mount type
        :rtype bool
        """
        return mount_type in ("DirectoryOrCreate",
                              "Directory",
                              "FileOrCreate",
                              "File",
                              "Socket",
                              "CharDevice",
                              "BlockDevice")

    @staticmethod
    def host_path_errors(vol_desc):
        """Sanity check a Host Path volume description and return a string for
        the first problem found.  Return None if no problem is found.

        """
        required_fields = ['path', 'type']
        accepted_fields = ['path', 'type']
        host_path = vol_desc.get('host_path', None)
        if host_path is None:
            return "No host_path specification in host_path volume description"
        for field in required_fields:
            if field not in host_path.keys():
                return "Host path specification missing required '%s'" % field
        for field in host_path.keys():
            if field not in accepted_fields:
                return "Host path specification has unrecognized '%s'" % field
        if not UAIVolume.is_valid_host_path_mount_type(host_path['type']):
            return "Host path has invalid mount type: %s" % host_path['type']
        return None

    @staticmethod
    def config_map_errors(vol_desc):
        """Sanity check a Config Map volume description and return a string
        for the first problem found.  Return None if no problem is
        found.

        """
        required_fields = ['name']
        accepted_fields = ['name', 'items', 'default_mode', 'optional']
        config_map = vol_desc.get('config_map', None)
        if config_map is None:
            return "No config_map specification in config_map volume description"
        for field in required_fields:
            if field not in config_map.keys():
                return "Config map specification missing required '%s'" % field
        for field in config_map.keys():
            if field not in accepted_fields:
                return "Config map specification has unrecognized '%s'" % field
        return None

    @staticmethod
    def secret_errors(vol_desc):
        """Sanity check a Secret volume description and return a string for
        the first problem found.  Return None if no problem is found.

        """
        required_fields = ['secret_name']
        accepted_fields = ['secret_name', 'items', 'default_mode', 'optional']
        secret = vol_desc.get('secret', None)
        if secret is None:
            return "No secret specification in secret volume description"
        for field in required_fields:
            if field not in secret.keys():
                return "Secret specification missing required '%s'" % field
        for field in secret.keys():
            if field not in accepted_fields:
                return "Secret specification has unrecognized '%s'" % field
        return None

    @staticmethod
    def vol_desc_errors(vol_desc):
        """Sanity check a volume description and return a string for
        the first problem found.  Return None if no problem is found.

        """
        checkers = {
            'host_path': UAIVolume.host_path_errors,
            'config_map': UAIVolume.config_map_errors,
            'secret': UAIVolume.secret_errors
        }
        source_type = UAIVolume.get_volume_source_type(vol_desc)
        if not source_type:
            return "Volume Description has no source type (e.g. 'configmap')"
        if not UAIVolume.is_valid_volume_source_type(vol_desc):
            return "Volume description invalid source type: %s" % source_type
        if source_type in checkers:
            return checkers[source_type]
        # We have no explicit checker for this particular source type, so the
        # volume description can't be further verified.  Treat it as okay.
        #
        # XXX - Expand understanding of source type validity eventually to
        #       cover other source types (i.e. add more / better checkers).
        return None
