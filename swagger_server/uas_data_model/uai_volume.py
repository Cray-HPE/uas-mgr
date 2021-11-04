# MIT License
#
# (C) Copyright [2020] Hewlett Packard Enterprise Development LP
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
"""Data Model for UAI Volumes
"""
from __future__ import absolute_import
import re
from etcd3_model import Etcd3Attr
from kubernetes import client
from swagger_server.uas_lib.uas_logging import logger
from swagger_server import ETCD_INSTANCE, ETCD_PREFIX, version
from swagger_server.uas_data_model.uas_data_model import UASDataModel

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
        ret = (
            "Volume has invalid host_path mount type '%s' "
            "- please refer to the Kubernetes docs for "
            "a list of supported host_path mount types" % (
                host_path['type']
            )
        )
        return ret
    return None


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


# A dictionary of known kubernetes volume source types.  The keys
# are the source type names we expect to see in a volume
# description for a volume.  The values are tuples of class that
# handles each source type (for use in constructing) and an
# optional checker function that will validate the contents.
# Kubernetes does not supply the checker, so we need to implement
# these here.  If no checker has been implemented, the source type
# will have None for a checker.
#
# XXX -- Need to implement more checkers and register them here...
SOURCE_TYPES = {
    'aws_elastic_block_store': (
        client.V1AWSElasticBlockStoreVolumeSource,
        None
    ),
    'azure_disk': (
        client.V1AzureDiskVolumeSource,
        None
    ),
    'azure_file': (
        client.V1AzureFileVolumeSource,
        None
    ),
    'cephfs': (
        client.V1CephFSVolumeSource,
        None
    ),
    'cinder': (
        client.V1CinderVolumeSource,
        None
    ),
    'config_map': (
        client.V1ConfigMapVolumeSource,
        config_map_errors
    ),
    'csi': (
        client.V1CSIVolumeSource,
        None
    ),
    'downward_api': (
        client.V1DownwardAPIVolumeSource,
        None
    ),
    'empty_dir': (
        client.V1EmptyDirVolumeSource,
        None
    ),
    'fc': (
        client.V1FCVolumeSource,
        None
    ),
    'flex_volume': (
        client.V1FlexVolumeSource,
        None
    ),
    'flocker': (
        client.V1FlockerVolumeSource,
        None
    ),
    'gce_persistent_disk': (
        client.V1GCEPersistentDiskVolumeSource,
        None
    ),
    'git_repo': (
        client.V1GitRepoVolumeSource,
        None
    ),
    'glusterfs': (
        client.V1GlusterfsVolumeSource,
        None
    ),
    'host_path': (
        client.V1HostPathVolumeSource,
        host_path_errors
    ),
    'iscsi': (
        client.V1ISCSIVolumeSource,
        None
    ),
    'nfs': (
        client.V1NFSVolumeSource,
        None
    ),
    'persistent_volume_claim': (
        client.V1PersistentVolumeClaimVolumeSource,
        None
    ),
    'photon_persistent_disk': (
        client.V1PhotonPersistentDiskVolumeSource,
        None
    ),
    'portworx_volume': (
        client.V1PortworxVolumeSource,
        None
    ),
    'projected': (
        client.V1ProjectedVolumeSource,
        None
    ),
    'quobyte': (
        client.V1QuobyteVolumeSource,
        None
    ),
    'rbd': (
        client.V1RBDVolumeSource,
        None
    ),
    'scale_io': (
        client.V1ScaleIOVolumeSource,
        None
    ),
    'secret': (
        client.V1SecretVolumeSource,
        secret_errors
    ),
    'storageos': (
        client.V1StorageOSVolumeSource,
        None
    ),
    'vsphere_volume': (
        client.V1VsphereVirtualDiskVolumeSource,
        None
    )
}

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
    etcd_instance = ETCD_INSTANCE
    model_prefix = "%s/%s" % (ETCD_PREFIX, "UAIVolume")

    # The Object ID used to locate each volume instance
    volume_id = Etcd3Attr(is_object_id=True)  # Read-only after creation

    # The kind of object that the data here represent.  Should always
    # contain "UAIVolume".  Protects against stray data types.
    kind = Etcd3Attr(default="UAIVolume")  # Read only

    # The Data Model version corresponding to this UAI Volume data.
    # Will always be equal to the UAS Manager service version version
    # under which the data were stored in ETCD.  Protects against
    # incompatible data.
    api_version = Etcd3Attr(default=version)  # Read only

    # The name of the volume
    volumename = Etcd3Attr(default=None)

    # The path within the UAI container where the volume is mounted.
    mount_path = Etcd3Attr(default=None)

    # The K8s description (JSON string) of what the volume is.
    volume_description = Etcd3Attr(default=None)

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
        return UAIVolume.get_volume_source_type(vol_desc) in SOURCE_TYPES

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
    def vol_desc_errors(vol_desc):
        """Sanity check a volume description and return a string for
        the first problem found.  Return None if no problem is found.

        """
        if len(vol_desc.keys()) > 1:
            return "Volume Description has more than one source type."
        source_type = UAIVolume.get_volume_source_type(vol_desc)
        if not source_type:
            return "Volume Description has no source type (e.g. 'config_map')"
        if not UAIVolume.is_valid_volume_source_type(vol_desc):
            return "Volume description invalid source type: %s" % source_type
        checker = SOURCE_TYPES[source_type][1]
        if checker is not None:
            return checker(vol_desc)
        # We have no explicit checker for this particular source type, so the
        # volume description can't be further verified.  Treat it as okay.
        #
        # XXX - Expand understanding of source type validity eventually to
        #       cover other source types (i.e. add more / better checkers).
        return None

    @staticmethod
    def add_etcd_volume(vol):
        """Compose and store an ETCD UAIVolume object based on the contents
        found in the configmap.

        """
        vol_desc = {}
        name = vol.get('name', None)
        if name is None:
            logger.error(
                "Volume with no name (skipped): %s",
                str(vol)
            )
            return
        if not UAIVolume.is_valid_volume_name(name):
            logger.error(
                "Volume '%s' has invalid name (skipped) "
                "- Names must consist of "
                "lower case alphanumeric characters or '-', and "
                "must start and end with an alphanumeric character. "
                "Refer to the Kubernetes documentation for more "
                "information.",
                name
            )
            return
        mount_path = vol.get('mount_path', None)
        if mount_path is None:
            logger.error(
                "Volume '%s' has no mount path (skipped)",
                name
            )
            return
        host_path = vol.get('host_path', None)
        if host_path is not None:
            mount_type = vol.get('type', None)
            if mount_type is None:
                mount_type = 'DirectoryOrCreate'
            vol_desc['host_path'] = client.V1HostPathVolumeSource(
                path=host_path,
                type=mount_type
            ).to_dict()
        config_map = vol.get('config_map', None)
        if config_map is not None:
            vol_desc['config_map'] = client.V1ConfigMapVolumeSource(
                name=config_map
            ).to_dict()
        secret_name = vol.get('secret_name', None)
        if secret_name is not None:
            vol_desc['secret'] = client.V1SecretVolumeSource(
                secret_name=secret_name
            ).to_dict()
        if vol.get('vol_desc', None) is not None:
            desc = vol['vol_desc']
            for source in desc:
                vol_desc[source] = desc[source]
        err = UAIVolume.vol_desc_errors(vol_desc)
        if err is not None:
            logger.error(
                "Volume '%s' has an invalid source type or volume description (skipped) - %s",
                name,
                err
            )
            return
        UAIVolume(
            volumename=name,
            mount_path=mount_path,
            volume_description=vol_desc
        ).put()

    @staticmethod
    def get_volume_source(vol_desc):
        """Compose a K8s Volume Source object based on this volume's
        'volume_description' member.

        """
        src_type = UAIVolume.get_volume_source_type(vol_desc)
        return SOURCE_TYPES[src_type][0](**vol_desc[src_type])

    @classmethod
    def get_by_name(cls, volumename):
        """Query volumes by volume name.  If a matching volume is found,
        return it, if not return None.

        """
        vols = cls.get_all()
        vols = [] if vols is None else vols
        # pylint: disable=no-member
        vol_dict = {vol.volumename: vol for vol in vols}
        return vol_dict.get(volumename, None)

    def expand(self):
        """Produce a dictionary of the publicly viewable elements of the
        object.

        """
        return {
            'volume_id': self.volume_id,
            'volumename': self.volumename,
            'mount_path': self.mount_path,
            'volume_description': self.volume_description
        }
