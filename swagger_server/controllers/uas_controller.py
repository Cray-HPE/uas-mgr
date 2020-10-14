#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#
"""UAS Server Controller

"""

import io

from swagger_server import version
from swagger_server.uas_lib.uai_mgr import UaiManager
from swagger_server.uas_lib.uas_mgr import UasManager
from swagger_server.uas_lib.uas_cfg import UasCfg


uas_cfg = UasCfg()  # pylint: disable=invalid-name


def create_uai(publickey=None, imagename=None, ports=None):
    """Create a new UAI for user

    Create a new UAI for the user

    :param publickey: Public ssh key for the user
    :type publickey: werkzeug.datastructures.FileStorage
    :param imagename: Image to use for UAI
    :type imagename: str
    :param ports: Comma-separated list of ports to expose from the UAI
    :type imagename: str

    :rtype: UAI
    """
    uai_response = UaiManager().create_uai(publickey, imagename, ports)
    return uai_response


def delete_uai_by_name(uai_list):
    """Delete UAIs in uai_list

    Delete a list of UAIs having names in uai_list.

    :param uai_list:
    :type uai_list: List[str]

    :rtype: UAI
    """
    if not uai_list:
        return "Must provide a list of UAI names to delete."
    uai_resp = UaiManager().delete_uais(uai_list)
    return uai_resp


def get_uais_for_user():
    """List all UAIs for user

    List all available UAIs for user

    :rtype: List[UAI]
    """
    uai_resp = UaiManager().list_uais('')
    return uai_resp


def get_uas_images():
    """List available UAS images

    List available UAS images

    :rtype: object
    """
    uas_img_info = {
        'default_image': uas_cfg.get_default_image(),
        'image_list': uas_cfg.get_images()
    }
    return uas_img_info


def get_uas_mgr_info():
    """List uas-mgr service info

    List uas-mgr service info

    :rtype: object
    """
    uas_mgr_info = {
        'service_name': 'cray-uas-mgr',
        'version': version
    }
    return uas_mgr_info


def get_all_uais(username=None, host=None):
    """List all UAIs matching optional parameters

    :param username:
    :type username: str
    :param host:
    :type host: str

    :rtype: List[UAI]
    """
    label = 'uas=managed'

    if username:
        label += ',user=%s' % username

    uai_resp = UaiManager().list_uais(label, host)
    return uai_resp


def delete_all_uais(username=None):
    """Delete all UAIs

    :param username: username to delete UAIs for if specified
    :type username: str
    :rtype: UAI
    """
    uai_mgr = UaiManager()
    uai_list = []

    if username:
        for uai in uai_mgr.list_uais('uas=managed,user=%s' % username):
            uai_list.append(uai.uai_name)

    uai_resp = uai_mgr.delete_uais(uai_list)
    return uai_resp


# Admin API
#
# Images...
def create_uas_image_admin(imagename, default=None):
    """Add an image

    Add valid image name to configuration. Does not create or upload
    container image.  Optionally, set default.

    :param imagename: Image to create
    :type imagename: str
    :param default: default image (true/false)
    :type default: bool

    :rtype: Image

    """
    if not imagename:
        return "Must provide imagename to create."
    if default is None:
        default = False
    return UasManager().create_image(imagename, default)


def get_uas_images_admin():
    """List UAS images

    List all available UAS images.


    :rtype: Image
    """
    return UasManager().get_images()


def get_uas_image_admin(image_id):
    """Get image info

    Get a description of the named image

    :param image_id:
    :type image_id: str

    :rtype: Image
    """
    if not image_id:
        return "Must provide image_id to get."
    return UasManager().get_image(image_id)


def update_uas_image_admin(image_id, imagename=None, default=None):
    """Update an image

    Update an image, specifically this can set the image name and set
    or unset the 'default' flag.

    :param image_id: The ID of the image to update
    :type image_id: str
    :param imagename: New Image Name for the Image
    :type imagename: str
    :param default: default image (true/false)
    :type default: bool

    :rtype: Image

    """
    if not image_id:
        return "Must provide image_id to update."
    return UasManager().update_image(image_id, imagename, default)

def delete_uas_image_admin(image_id):
    """Remove the imagename from set of valid images

    Delete the named image from the set of valid UAI container
    images.

    :param image_id:
    :type image_id: str

    :rtype: None

    """
    if not image_id:
        return "Must provide image_id to delete."
    return UasManager().delete_image(image_id)

# Volumes...
def create_uas_volume_admin(volumename, mount_path,
                            volume_description):
    """Add a volume

    Add a volume to the volume list in the configuration.  The volume
    list is used during UAI creation, so this request only applies to
    UAIs subsequently created.  Modifying the volume list does not
    affect existing UAIs.

    :param volumename: Volume to create
    :type volumename: str
    :param mount_path: Mount path inside the UAI
    :type mount_path: str
    :param volume_description:
        Desscription of a Kubernetes volume to be mounted in UAI
        containers.  This is the equivalent of whatever YAML you
        would normally apply to Kubernetes to attach the kind of
        volume you want to a pod.  There are many kinds of volumes,
        the examples given here illustrate some options:


          { "hostPath": { "path": "/data", "type": "DirectoryOrCreate" } }

          or

          { "secret": { "secretName": "my-secret" } }

          or

          { "configMap": { "name": "my-configmap", "items": { "key": "flaps",
            "path": "flaps" } } }
    :type volume_description: str

    :rtype: AdminVolume

    """
    if not volumename:
        return "Must provide volumename to create."
    if not mount_path:
        return "Must provide mount_path."
    if not volume_description:
        return "Must provide volume_description."
    if not isinstance(volume_description, io.BytesIO):
        if not isinstance(volume_description, str):
            return (
                "Volume description must be either a JSON string or a "
                "request body containing a JSON string"
            )
    else:
        # It is an io.BytesIO, get the value as a string
        volume_description = volume_description.getvalue()
    return UasManager().create_volume(
        volumename,
        mount_path,
        volume_description
    )


def get_uas_volumes_admin():
    """List volumes

    The volume list in the configuration is used during UAI
    creation. This list does not necessarily relate to UAIs previously
    created. This call does not affect the k8s volume itself.


    :rtype: List[AdminVolume]

    """
    return UasManager().get_volumes()


def get_uas_volume_admin(volume_id):
    """Get volume info for volume ID

    Get volume info for volume_id

    :param volume_id:
    :type volume_id: str

    :rtype: AdminVolume
    """
    if not volume_id:
        return "Must provide volume_id to get."
    return UasManager().get_volume(volume_id)


def update_uas_volume_admin(volume_id, volumename=None, mount_path=None,
                            volume_description=None):
    """Update a volume

    Update a volume to be mounted in UAS images. This has no effect on
    running UAIs and does not change the volume itself in any way, but
    it can modify the relationship between future UAI containers and
    the volume.

    :param volume_id: Volume to update
    :type volume_id: str
    :param volumename: New volume name for volume
    :type volumename: str
    :param mount_path: Mount path inside the UAI
    :type mount_path: str
    :param volume_description:
        Description of a Kubernetes volume to be mounted in UAI
        containers.  This is the equivalent of whatever YAML you
        would normally apply to Kubernetes to attach the kind of
        volume you want to a pod.  There are many kinds of volumes,
        the examples given here illustrate some options:


          { "hostPath": { "path": "/data", "type": "DirectoryOrCreate" } }

          or

          { "secret": { "secretName": "my-secret" } }

          or

          { "configMap": { "name": "my-configmap", "items": { "key": "flaps",
            "path": "flaps" } } }
    :type volume_description: str

    :rtype: AdminVolume

    """
    if not volume_id:
        return "Must provide volume_id to update."
    if volume_description is not None:
        if not isinstance(volume_description, io.BytesIO):
            if not isinstance(volume_description, str):
                return (
                    "Volume description must be either a JSON string or a "
                    "request body containing a JSON string"
                )
        else:
            # It is an io.BytesIO, get the value as a string
            volume_description = volume_description.getvalue()
    return UasManager().update_volume(
        volume_id,
        volumename,
        mount_path,
        volume_description
    )


def delete_uas_volume_admin(volume_id):
    """Remove volume from the volume list

    Does not affect existing UAIs. Remove the volume from the list of
    valid volumes. The actual volume itself is not affected in any
    way.

    :param volume_id:
    :type volume_id: str

    :rtype: None

    """
    if not volume_id:
        return "Must provide volume_id to delete."
    return UasManager().delete_volume(volume_id)

def delete_local_config_admin():
    """Remove all local configuration and reset to defaults

    Removes all locally applied configuration, leaving the UAS in its
    default configuration.

    :rtype: None
    """
    return UasManager().factory_reset()

# Resource Configs...
def create_uas_resource_admin(comment=None, limit=None, request=None):
    """Add a resource limit / request configuration item

    Add a resource limit / request configuration to configuration.

    :param comment: Comment describing Resource Config to Create (optional)
    :type comment: str
    :param limit: K8s resource limit JSON string
    :type limit: str
    :param request: K8s resource request JSON string
    :type request: str

    :rtype: Resource

    """
    return UasManager().create_resource(comment, limit, request)


def get_uas_resources_admin():
    """List UAS resource limit / request config items

    List all available UAS resource limit / request config items.


    :rtype: Resource
    """
    return UasManager().get_resources()


def get_uas_resource_admin(resource_id):
    """Get the specified resource limit / request configuration item

    Get a description of the named resource limit / request config item

    :param resource_id:
    :type resource_id: str

    :rtype: Resource
    """
    if not resource_id:
        return "Must provide resource_id to get."
    return UasManager().get_resource(resource_id)


def update_uas_resource_admin(resource_id,
                              comment=None,
                              limit=None,
                              request=None):
    """Update a resource limit / request configuration item

    Update an resource, specifically this can set the 'comment',
    'limit' or 'request' fields of the resource configuration.

    :param resource_id: The ID of the resource to update
    :type resource_id: str
    :param comment: new comment for the resource request / limit config
    :type comment: str
    :param limit: K8s resource limit JSON string
    :type default: str
    :param request: K8s resource request JSON string
    :type default: str

    :rtype: Resource

    """
    if not resource_id:
        return "Must provide resource_id to update."
    return UasManager().update_resource(resource_id, comment, limit, request)

def delete_uas_resource_admin(resource_id):
    """Remove the specified resource limit / request configuration

    :param resource_id:
    :type resource_id: str

    :rtype: Resource

    """
    if not resource_id:
        return "Must provide resource_id to delete."
    return UasManager().delete_resource(resource_id)
