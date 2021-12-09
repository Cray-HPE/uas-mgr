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
"""UAS Server Controller

"""

import io

from swagger_server import version
from swagger_server.uas_lib.uai_mgr import UaiManager
from swagger_server.uas_lib.uas_mgr import UasManager
from swagger_server.uas_lib.uas_cfg import UasCfg


uas_cfg = UasCfg()  # pylint: disable=invalid-name


def create_uai(publickey=None, imagename=None, ports=None, uai_name=None):
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
    uai_response = UaiManager().create_uai(public_key=publickey,
                                           imagename=imagename,
                                           opt_ports=ports,
                                           uai_name=uai_name)
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
    uai_resp = UaiManager().delete_uais(job_list=uai_list)
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
    # This API call is used as a readiness check which provides a sort
    # of heartbeat for UAS, and we need a background activity to check
    # for stale UAIs and reap them.  The following provides the hook
    # for that and avoids the need for threading.  For now we will
    # reap the default number of UAIs at a go.  In the future this may
    # want to be configurable.
    UaiManager().reap_uais()
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

    uai_resp = UaiManager().list_uais(label=label, host=host)
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
        uai_list = uai_mgr.select_jobs(
            labels='uas=managed,user=%s' % username
        )
        if not uai_list:
            return "User %s has no UAIs, none deleted"
    uai_resp = uai_mgr.delete_uais(job_list=uai_list)
    return uai_resp


# Admin API
#
# UAIs
def create_uai_admin(class_id=None,
                     owner=None,
                     passwd_str=None,
                     publickey_str=None,
                     uai_name=None):
    """ Create a UAI Administratively

    :param class_id: the ID (UUID) of the class used to create the UAI
    :type class_id: str
    :param owner: the optional username of the owner of the UAI
    :type owner: str
    :param passwd_str: the optional /etc/passwd style string describing this owner of the UAI
    :type passwd_str: str
    :param publickey: Public ssh key for the user
    :type publickey: werkzeug.datastructures.FileStorage
    :rtype: AdminUAI
    """
    return UasManager().create_uai(
        class_id=class_id,
        owner=owner,
        passwd_str=passwd_str,
        public_key_str=publickey_str,
        uai_name=uai_name
    )


def delete_uais_admin(class_id=None, owner=None, uai_list=None):
    """ Delete UAIs, optionally by class or by owner or both

    :param class_id: the optional ID (UUID) of the class by which to select targets
    :type class_id: str
    :param owner: the optional username of the UAI owner by which to select targets
    :type owner: str
    :rtype: AdminUAI List
    """
    return UasManager().delete_uais(
        class_id=class_id,
        owner=owner,
        uai_list=uai_list
    )


def get_uais_admin(class_id=None, owner=None):
    """ List UAIs, optionally by class or by owner

    :param class_id: the optional ID (UUID) of the class by which to filter the results
    :type class_id: str
    :param owner: the optional username of the UAI owner by which to filter the results
    :type owner: str
    :rtype: AdminUAI List
    """
    return UasManager().get_uais(
        class_id=class_id,
        owner=owner
    )


def get_uai_admin(uai_name=None):
    """ Retrieve a UAI by its name

    :param uai_name: the name of the UAI to be retrieved
    :type uai_name: str
    :rtype: AdminUAI
    """
    return UasManager().get_uai(
        uai_name=uai_name
    )


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
    return UasManager().create_image(imagename=imagename,
                                     default=default)


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
    return UasManager().get_image(image_id=image_id)


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
    return UasManager().update_image(image_id=image_id,
                                     imagename=imagename,
                                     default=default)

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
    return UasManager().delete_image(image_id=image_id)

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
        volumename=volumename,
        mount_path=mount_path,
        vol_desc=volume_description
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
    return UasManager().get_volume(volume_id=volume_id)


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
        volume_id=volume_id,
        volumename=volumename,
        mount_path=mount_path,
        vol_desc=volume_description
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
    return UasManager().delete_volume(volume_id=volume_id)

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
    return UasManager().create_resource(comment=comment,
                                        limit=limit,
                                        request=request)


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
    return UasManager().get_resource(resource_id=resource_id)


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
    return UasManager().update_resource(resource_id=resource_id,
                                        comment=comment,
                                        limit=limit,
                                        request=request)

def delete_uas_resource_admin(resource_id):
    """Remove the specified resource limit / request configuration

    :param resource_id:
    :type resource_id: str

    :rtype: Resource

    """
    if not resource_id:
        return "Must provide resource_id to delete."
    return UasManager().delete_resource(resource_id=resource_id)

# UAI Classes
#pylint: disable=too-many-arguments,too-many-locals
def create_uas_class_admin(comment=None,
                           default=None,
                           public_ip=None,
                           image_id=None,
                           priority_class_name=None,
                           namespace=None,
                           opt_ports=None,
                           uai_creation_class=None,
                           uai_compute_network=None,
                           resource_id=None,
                           volume_list=None,
                           tolerations=None,
                           timeout=None,
                           service_account=None,
                           replicas="1"):
    """Add a UAI Class

    Add a UAI Class to the UAS configuration

    :param comment: Comment describing UAI Class (optional)
    :type comment: str
    :param default: Is this the default UAI Class?
    :type default: bool
    :param public_ip: Are UAIs  from this class on a public IP?
    :type public_ip: bool
    :param image_id: Image ID (UUID) to use creating UAIs  of this class
    :type image_id: str
    :param priority_class_name: K8s priority class name to give UAIs  of this class
    :type priority_class_name: str
    :param namespace: K8s namespace where  of this class run
    :type namespace: str
    :param opt_ports: Comma separated list of optional additional port numbers
    :type opt_ports: str
    :param uai_creation_class: Class ID (UUID) of UAIs created by this Broker
    :type uai_creation_class: str
    :param uai_compute_network: Does this Class require a compute network route?
    :type uai_compute_network: bool
    :param resource_id: Resource ID (UUID)  to use in UAIs  of this class
    :type resource_id: str
    :param volume_list: List of Volume IDs (UUIDs) mounted in UAIs  of this class
    :type volume_list: list
    :param tolerations: JSON list of tolerations for UAIs of this class
    :type tolerations: str
    :param timeout: JSON map of timeout settings for UAIs of this class
    :type timeout: str
    :param service_account: name of a K8s service account for UAIs of this class
    :type service_account: str
    :param replicas: the number of UAI replicas created for a UAI of this class
    :type replicas: str
    :rtype: UAIClass

    """
    return UasManager().create_class(comment=comment,
                                     default=default,
                                     public_ip=public_ip,
                                     image_id=image_id,
                                     resource_id=resource_id,
                                     namespace=namespace,
                                     opt_ports=opt_ports,
                                     uai_creation_class=uai_creation_class,
                                     uai_compute_network=uai_compute_network,
                                     priority_class_name=priority_class_name,
                                     volume_list=volume_list,
                                     tolerations=tolerations,
                                     timeout=timeout,
                                     service_account=service_account,
                                     replicas=replicas)


def get_uas_classes_admin():
    """List UAI Classes

    List all available UAI Classes

    :rtype: UAIClass
    """
    return UasManager().get_classes()


def get_uas_class_admin(class_id=None):
    """Get the specified UAI Class

    Get a description of the specified UAI Class

    :param class_id:
    :type class_id: str

    :rtype: Resource
    """
    if not class_id:
        return "Must provide class_id (UUID) to get."
    return UasManager().get_class(class_id=class_id)


#pylint: disable=too-many-arguments,too-many-locals
def update_uas_class_admin(class_id=None,
                           comment=None,
                           default=None,
                           public_ip=None,
                           image_id=None,
                           priority_class_name=None,
                           namespace=None,
                           opt_ports=None,
                           uai_creation_class=None,
                           uai_compute_network=None,
                           resource_id=None,
                           volume_list=None,
                           tolerations=None,
                           timeout=None,
                           service_account=None,
                           replicas=None):
    """Update the specified UAI Class

    Update the specified UAI Class with new values.  This can set the
    comment, default setting, image_id, resource_id and volume_list of
    the UAI class.

    :param comment: Comment describing UAI Class (optional)
    :type comment: str
    :param default: Is this the default UAI Class?
    :type default: bool
    :param public_ip: Are UAIs  from this class on a public IP?
    :type public_ip: bool
    :param image_id: Image ID (UUID) to use creating UAIs  of this class
    :type image_id: str
    :param priority_class_name: K8s priority class name to give UAIs  of this class
    :type priority_class_name: str
    :param namespace: K8s namespace where  of this class run
    :type namespace: str
    :param opt_ports: Comma separated list of optional additional port numbers
    :type opt_ports: str
    :param uai_creation_class: Class ID (UUID) of UAIs created by this Broker
    :type uai_creation_class: str
    :param uai_compute_network: Does this Class require a compute network route?
    :type uai_compute_network: bool
    :param resource_id: Resource ID (UUID)  to use in UAIs  of this class
    :type resource_id: str
    :param volume_list: List of Volume IDs (UUIDs) useed in UAIs of this class
    :type volume_list: list
    :param tolerations: JSON list of tolerations for UAIs of this class
    :type tolerations: str
    :param timeout: JSON map of timeout settings for UAIs of this class
    :type timeout: str
    :param service_account: name of a K8s service account for UAIs of this class
    :type service_account: str
    :param replicas: the number of UAI replicas created for a UAI of this class
    :type replicas: str
    :rtype: UAIClass
    """
    if not class_id:
        return "Must provide class_id of the UAI Class to update."
    return UasManager().update_class(class_id=class_id,
                                     comment=comment,
                                     default=default,
                                     public_ip=public_ip,
                                     image_id=image_id,
                                     priority_class_name=priority_class_name,
                                     namespace=namespace,
                                     opt_ports=opt_ports,
                                     uai_creation_class=uai_creation_class,
                                     uai_compute_network=uai_compute_network,
                                     resource_id=resource_id,
                                     volume_list=volume_list,
                                     tolerations=tolerations,
                                     timeout=timeout,
                                     service_account=service_account,
                                     replicas=replicas)

def delete_uas_class_admin(class_id):
    """Remove the specified UAI Class

    :param class_id:
    :type class_id: str

    :rtype: UAIClass

    """
    if not class_id:
        return "Must provide class_id of UAI Class to delete."
    return UasManager().delete_class(class_id=class_id)
