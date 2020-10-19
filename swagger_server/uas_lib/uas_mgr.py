# Copyright 2020 Hewlett Packard Enterprise Development LP#
#
"""
Class that implements UAS functions not requiring user attributes
"""
#pylint: disable=too-many-lines

import json
from flask import abort
from swagger_server.uas_lib.uas_base import UasBase
from swagger_server.uas_data_model.uai_image import UAIImage
from swagger_server.uas_data_model.uai_volume import UAIVolume
from swagger_server.uas_data_model.uai_resource import UAIResource
from swagger_server.uas_data_model.uai_class import UAIClass
from swagger_server.uas_data_model.populated_config import PopulatedConfig

# pylint: disable=too-many-public-methods
class UasManager(UasBase):
    """UAS Manager - manages UAS administrative resources

    """
    def __init__(self):
        """ Constructor """
        UasBase.__init__(self)

    def delete_image(self, image_id):
        """Delete a UAI image from the config

        """
        self.uas_cfg.get_config()

        # Make sure the image ID is not in use by any classes, and, if
        # it is, get a list of them to complain about.
        uai_classes = UAIClass.get_all()
        uai_classes = [] if uai_classes is None else uai_classes
        in_use = [
            uai_class.class_id
            for uai_class in uai_classes if uai_class.image_id == image_id
        ]
        if in_use:
            abort(
                409,
                "Image ID %s is in use by the following UAI Classes %s" %
                (image_id, str(in_use))
            )
        img = UAIImage.get(image_id)
        if img is None:
            abort(404, "image '%s' does not exist" % image_id)
        img.remove() # don't use img.delete() you actually want it removed
        return {
            'image_id': img.image_id,
            'imagename': img.imagename,
            'default': img.default
        }

    def create_image(self, imagename, default):
        """Create a new UAI image in the config

        """
        self.uas_cfg.get_config()
        if UAIImage.get_by_name(imagename):
            abort(409, "image named '%s' already exists" % imagename)
        # Create it and store it...
        if default is None:
            default = False
        if default:
            # This is the default image. Check for any other image
            # that is currently default and make it no longer default.
            imgs = UAIImage.get_all()
            imgs = [] if imgs is None else imgs
            for img in imgs:
                if img.default:
                    img.default = False
                    img.put()
        # Now create the new image...
        img = UAIImage(imagename=imagename, default=default)
        img.put()
        return {
            'image_id': img.image_id,
            'imagename': img.imagename,
            'default': img.default
        }


    def update_image(self, image_id, imagename, default):
        """Update a UAI image in the config

        """
        self.uas_cfg.get_config()
        img = UAIImage.get(image_id)
        if img is None:
            abort(404, "image '%s' does not exist" % image_id)
        changed = False
        # Is the image name changing?
        if imagename is None:
            imagename = img.imagename
        if imagename != img.imagename:
            # Going to change the image name, make sure it is unique...
            tmp = UAIImage.get_by_name(imagename)
            if tmp is not None:
                abort(409, "image named '%s' already exists" % imagename)
            # A value is specified to update...
            img.imagename = imagename
            changed = True
        # Is the default settting changing?
        if default is None:
            default = img.default
        if default != img.default:
            # A value is specified to update...
            img.default = default
            changed = True
        if changed:
            if default:
                # This will be the default image. If there is another
                # image that is default right now, make it no longer
                # default.
                imgs = UAIImage.get_all()
                imgs = [] if imgs is None else imgs
                for tmp in imgs:
                    if tmp.image_id == image_id:
                        continue
                    if tmp.default:
                        tmp.default = False
                        tmp.put()
            img.put()
        return {
            'image_id': img.image_id,
            'imagename': img.imagename,
            'default': img.default
        }

    def get_image(self, image_id):
        """Retrieve a UAI image from the config

        """
        self.uas_cfg.get_config()
        img = UAIImage.get(image_id)
        if img is None:
            abort(404, "image '%s' does not exist" % image_id)
        return {
            'image_id': img.image_id,
            'imagename': img.imagename,
            'default': img.default
        }

    def get_images(self):
        """Get the list of UAI images in the config

        """
        self.uas_cfg.get_config()
        imgs = UAIImage.get_all()
        imgs = [] if imgs is None else imgs
        return [
            {
                'image_id': img.image_id,
                'imagename': img.imagename,
                'default': img.default
            }
            for img in imgs
        ]

    def delete_volume(self, volume_id):
        """Delete a UAI volume from the config

        """
        self.uas_cfg.get_config()
        # Make sure the volume ID is not in use by any classes, and, if
        # it is, get a list of them to complain about.
        uai_classes = UAIClass.get_all()
        uai_classes = [] if uai_classes is None else uai_classes
        in_use = [
            uai_class.class_id
            for uai_class in uai_classes if volume_id in uai_class.volume_list
        ]
        if in_use:
            abort(
                409,
                "Volume ID %s is in use by the following UAI Classes %s" %
                (volume_id, str(in_use))
            )
        vol = UAIVolume.get(volume_id)
        if vol is None:
            abort(404, "volume '%s' does not exist" % volume_id)
        vol.remove() # don't use vol.delete() you actually want it removed
        return {
            'volume_id': vol.volume_id,
            'volumename': vol.volumename,
            'mount_path': vol.mount_path,
            'volume_description': vol.volume_description
        }

    def create_volume(self, volumename, mount_path, vol_desc):
        """Create a UAI volume in the config

        """
        self.uas_cfg.get_config()
        if not UAIVolume.is_valid_volume_name(volumename):
            abort(
                400,
                "Invalid volume name - names must consist of lower case"
                " alphanumeric characters or '-', and must start and"
                " end with an alphanumeric character. Refer to the "
                "Kubernetes documentation for more information."
            )
        if not mount_path:
            abort(400, "No mount path specified for volume")
        if vol_desc is None:
            abort(400, "No volume description provided for volume")
        # Convert vol_desc from a JSON string to a dictionary
        try:
            vol_desc = json.loads(vol_desc)
        except json.decoder.JSONDecodeError as err:
            abort(
                400,
                "Volume description failed JSON decoding - %s" % str(err)
            )
        err = UAIVolume.vol_desc_errors(vol_desc)
        if err is not None:
            abort(
                400,
                "Volume has a malformed volume description - %s" % err
            )
        if UAIVolume.get_by_name(volumename) is not None:
            abort(409, "volume named '%s' already exists" % volumename)
        # Create it and store it...
        vol = UAIVolume(
            volumename=volumename,
            mount_path=mount_path,
            volume_description=vol_desc
        )
        vol.put()
        return {
            'volume_id': vol.volume_id,
            'volumename': vol.volumename,
            'mount_path': vol.mount_path,
            'volume_description': vol.volume_description
        }

    def update_volume(self, volume_id,
                      volumename=None, mount_path=None, vol_desc=None):
        """Update a UAI volume in the config

        """
        self.uas_cfg.get_config()
        vol = UAIVolume.get(volume_id)
        if vol is None:
            abort(
                404,
                "Volume %s not found" % volume_id
            )
        changed = False
        if volumename is not None:
            if not volumename:
                abort(400, "invalid (empty) volume name specified")
                if not UAIVolume.is_valid_volume_name(volumename):
                    abort(
                        400,
                        "Invalid volume name - names must consist of lower "
                        "case alphanumeric characters or '-', and must start "
                        "and end with an alphanumeric character. Refer to the "
                        "Kubernetes documentation for more information."
                    )
            tmp = UAIVolume.get_by_name(volumename)
            if tmp is not None and tmp.volume_id != vol.volume_id:
                abort(409, "volume named '%s' already exists" % volumename)
            vol.volumename = volumename
            changed = True
        if mount_path is not None:
            if not mount_path:
                abort(400, "invalid (empty) mount_path specified")
            vol.mount_path = mount_path
            changed = True
        if vol_desc is not None:
            # Convert vol_desc from a JSON string to a dictionary
            try:
                vol_desc = json.loads(vol_desc)
            except json.decoder.JSONDecodeError as err:
                abort(
                    400,
                    "Volume description failed JSON decoding - %s" % str(err)
                )
            err = UAIVolume.vol_desc_errors(vol_desc)
            if err is not None:
                abort(
                    400,
                    "Volume has a malformed volume description - %s" % err
                )
            vol.volume_description = vol_desc
            changed = True
        if changed:
            vol.put()
        return {
            'volume_id': vol.volume_id,
            'volumename': vol.volumename,
            'mount_path': vol.mount_path,
            'volume_description': vol.volume_description
        }

    def get_volume(self, volume_id):
        """Get info on a specific volume from the config

        """
        self.uas_cfg.get_config()
        vol = UAIVolume.get(volume_id)
        if vol is None:
            abort(
                404,
                "Unknown volume '%s'" % volume_id
            )
        return {
            'volume_id': vol.volume_id,
            'volumename': vol.volumename,
            'mount_path': vol.mount_path,
            'volume_description': vol.volume_description
        }

    def get_volumes(self):
        """Get info on all volumes in the config

        """
        self.uas_cfg.get_config()
        vols = UAIVolume.get_all()
        vols = [] if vols is None else vols
        return [
            {
                'volume_id': vol.volume_id,
                'volumename': vol.volumename,
                'mount_path': vol.mount_path,
                'volume_description': vol.volume_description
            }
            for vol in vols
        ]

    def delete_resource(self, resource_id):
        """Delete resource limit / request config

        """
        self.uas_cfg.get_config()

        # Make sure the resource is not in use by any classes, and, if
        # it is, get a list of them to complain about.
        uai_classes = UAIClass.get_all()
        uai_classes = [] if uai_classes is None else uai_classes
        in_use = [
            uai_class.class_id
            for uai_class in uai_classes
            if uai_class.resource_id == resource_id
        ]
        if in_use:
            abort(
                409,
                "Resouce ID %s is in use by the following UAI Classes %s" %
                (resource_id, str(in_use))
            )

        resource = UAIResource.get(resource_id)
        if resource is None:
            abort(404, "resource config '%s' does not exist" % resource_id)

        # Good to go...
        resource.remove() # don't use x.delete() you actually want it removed
        return {
            'resource_id': resource.resource_id,
            'comment': resource.comment,
            'limit': resource.limit,
            'request': resource.request
        }

    def create_resource(self, comment=None, limit=None, request=None):
        """Create a UAI resource limit / request config

        """
        self.uas_cfg.get_config()
        # If 'limit' is specified convert it from a JSON string to a dictionary
        if limit is not None:
            try:
                _ = json.loads(limit)
            except json.decoder.JSONDecodeError as err:
                abort(
                    400,
                    "Resource limit '%s' failed JSON decoding "
                    "- %s" % (limit, str(err))
                )
        # If 'request' is specified convert it from a JSON string to a
        # dictionary
        if request is not None:
            try:
                _ = json.loads(request)
            except json.decoder.JSONDecodeError as err:
                abort(
                    400,
                    "Resource request '%s' failed JSON decoding "
                    "- %s" % (request, str(err))
                )
        # Create it and store it...
        resource = UAIResource(
            comment=comment,
            limit=limit,
            request=request
        )
        resource.put()
        return {
            'resource_id': resource.resource_id,
            'comment': resource.comment,
            'limit': resource.limit,
            'request': resource.request
        }

    def update_resource(self, resource_id,
                        comment=None,
                        limit=None,
                        request=None):
        """Update a resource limit / request config

        """
        self.uas_cfg.get_config()
        resource = UAIResource.get(resource_id)
        if resource is None:
            abort(
                404,
                "Resource %s not found" % resource_id
            )
        changed = False
        if comment is not None:
            resource.comment = comment
            changed = True
        if limit is not None:
            try:
                _ = json.loads(limit)
            except json.decoder.JSONDecodeError as err:
                abort(
                    400,
                    "Resource limit '%s' failed JSON decoding "
                    "- %s" % (limit, str(err))
                )
            resource.limit = limit
            changed = True
        if request is not None:
            try:
                _ = json.loads(request)
            except json.decoder.JSONDecodeError as err:
                abort(
                    400,
                    "Resource request '%s' failed JSON decoding "
                    "- %s" % (request, str(err))
                )
            resource.request = request
            changed = True
        if changed:
            resource.put()
        return {
            'resource_id': resource.resource_id,
            'comment': resource.comment,
            'limit': resource.limit,
            'request': resource.request
        }

    def get_resource(self, resource_id):
        """Get info on a specific resource limit / request config

        """
        self.uas_cfg.get_config()
        resource = UAIResource.get(resource_id)
        if resource is None:
            abort(
                404,
                "Unknown resource '%s'" % resource_id
            )
        return {
            'resource_id': resource.resource_id,
            'comment': resource.comment,
            'limit': resource.limit,
            'request': resource.request
        }

    def get_resources(self):
        """Get info on all resource limit / request configs

        """
        self.uas_cfg.get_config()
        resources = UAIResource.get_all()
        resources = [] if resources is None else resources
        return [
            {
                'resource_id': resource.resource_id,
                'comment': resource.comment,
                'limit': resource.limit,
                'request': resource.request
            }
            for resource in resources
        ]

    @staticmethod
    def _validate_volume_list(volume_list):
        """ Verify that a volume list is a list and all the elements exist.

        """
        try:
            missing_vols = ""
            for volume_id in volume_list:
                if UAIVolume.get(volume_id) is None:
                    if missing_vols:
                        missing_vols += ", "
                    missing_vols += volume_id
            if missing_vols:
                abort(
                    400,
                    "Unknown volume(s) [%s] specified for UAI Class" %
                    (missing_vols)
                )
        except TypeError as err:
            abort(400, "Validation of volume list failed - %s" % str(err))

    @staticmethod
    def _expanded_uai_class(uai_class):
        """Fully expand a UAI Class object and all of its sub-objects.  This
        differs from the object based `expand` method used elsewhere
        in that it knows how to dig into the sub-objects.

        """
        comment = "" if uai_class.comment is None else uai_class.comment
        default = False if uai_class.default is None else uai_class.default
        public_ssh = (
            False if uai_class.public_ssh is None
            else uai_class.public_ssh
        )
        volume_mounts = (
            [] if uai_class.volume_list is None
            else [
                    UAIVolume.get(vol).expand()
                    for vol in uai_class.volume_list
            ]
        )
        resource_config = (
            None if uai_class.resource_id is None
            else UAIResource.get(uai_class.resource_id).expand()
        )
        return {
            'class_id': uai_class.class_id,
            'comment': comment,
            'default': default,
            'public_ssh': public_ssh,
            'priority_class_name': uai_class.priority_class_name,
            'namespace': uai_class.namespace,
            'uai_creation_class': uai_class.uai_creation_class,
            'uai_image': UAIImage.get(uai_class.image_id).expand(),
            'resource_config': resource_config,
            'volume_mounts': volume_mounts
        }

    def delete_class(self, class_id):
        """Delete a UAI Class

        """
        self.uas_cfg.get_config()
        uai_class = UAIClass.get(class_id)
        if uai_class is None:
            abort(404, "UAI Class '%s' does not exist" % class_id)
        uai_class.remove() # don't use x.delete() you actually want it removed
        return self._expanded_uai_class(uai_class)

    #pylint: disable=too-many-arguments
    def create_class(self,
                     comment=None,
                     default=None,
                     public_ssh=None,
                     image_id=None,
                     priority_class_name=None,
                     namespace=None,
                     uai_creation_class=None,
                     resource_id=None,
                     volume_list=None):
        """Create a UAI Class

        """
        self.uas_cfg.get_config()
        if image_id is None:
            abort(400, "Must specify an image ID when creating a UAI Class")
        if UAIImage.get(image_id) is None:
            abort(
                400,
                "Unkown UAI Image '%s' specified for UAI Class" % image_id
            )
        if resource_id is not None and UAIResource.get(resource_id) is None:
            abort(
                400,
                "Unkown Resource Config '%s' specified for UAI "
                "Class" % resource_id
            )
        if uai_creation_class is not None and UAIClass.get(uai_creation_class) is None:
            abort(
                400,
                "Unknown UAI creation class ID %s"
                % (uai_creation_class)
            )
        if volume_list:
            self._validate_volume_list(volume_list)
        volume_list = [] if volume_list is None else volume_list
        comment = "" if comment is None else comment
        default = False if default is None else default
        public_ssh = False if public_ssh is None else public_ssh
        priority_class_name = ("uai-priority"
                               if priority_class_name is None
                               else priority_class_name)
        namespace = (
            self.uas_cfg.get_uai_namespace()
            if namespace is None
            else namespace
        )
        # Create it and store it...
        uai_class = UAIClass(
            comment=comment,
            default=default,
            public_ssh=public_ssh,
            image_id=image_id,
            priority_class_name=priority_class_name,
            namespace=namespace,
            uai_creation_class=uai_creation_class,
            resource_id=resource_id,
            volume_list=volume_list
        )
        if default:
            default_class = UAIClass.get_default()
            if default_class is not None:
                # There was a previously default class, this class is
                # usurping that, so set the previously default class
                # no longer default.
                default_class.default = False
                default_class.put()
        uai_class.put()
        return self._expanded_uai_class(uai_class)

    # pylint: disable=too-many-branches
    def update_class(self,
                     class_id,
                     comment=None,
                     default=None,
                     public_ssh=None,
                     image_id=None,
                     priority_class_name=None,
                     namespace=None,
                     uai_creation_class=None,
                     resource_id=None,
                     volume_list=None):
        """Update a UAI Class

        """
        self.uas_cfg.get_config()
        uai_class = UAIClass.get(class_id)
        if uai_class is None:
            abort(
                404,
                "Class %s not found" % class_id
            )
        changed = False
        if comment is not None:
            uai_class.comment = comment
            changed = True
        if default is not None:
            uai_class.default = default
            changed = True
        if public_ssh is not None:
            uai_class.public_ssh = public_ssh
            changed = True
        if priority_class_name is not None:
            uai_class.priority_class_name = priority_class_name
            changed = True
        if namespace is not None:
            uai_class.namespace = namespace
            changed = True
        if uai_creation_class is not None:
            if UAIClass.get(uai_creation_class) is None:
                abort(
                    400,
                    "Unknown UAI creation class ID %s given for UAI Class %s "
                    % (uai_creation_class, class_id)
                )
            uai_class.uai_creation_class = uai_creation_class
            changed = True
        if image_id is not None:
            if UAIImage.get(image_id) is None:
                abort(
                    400,
                    "Unknown image-id %s supplied for UAI Class %s "
                    % (image_id, class_id)
                )
            uai_class.image_id = image_id
            changed = True
        if resource_id is not None:
            if UAIResource.get(resource_id) is None:
                abort(
                    400,
                    "Unknown resource-id %s supplied for UAI Class %s "
                    % (resource_id, class_id)
                )
            uai_class.resource_id = resource_id
            changed = True
        if volume_list is not None:
            self._validate_volume_list(volume_list)
            uai_class.volume_list = volume_list
            changed = True
        if changed:
            if default:  # this implies that default is not None
                default_class = UAIClass.get_default()
                if default_class is not None:
                    # There was a previously default class, this class is
                    # usurping that, so set the previously default class
                    # no longer default.
                    default_class.default = False
                    default_class.put()
            uai_class.put()
        return self._expanded_uai_class(uai_class)

    def get_class(self, class_id):
        """Get info on a specific class limit / request config

        """
        self.uas_cfg.get_config()
        uai_class = UAIClass.get(class_id)
        if uai_class is None:
            abort(
                404,
                "Unknown class '%s'" % class_id
            )
        return self._expanded_uai_class(uai_class)

    def get_classes(self):
        """Get info on all class limit / request configs

        """
        self.uas_cfg.get_config()
        uai_classes = UAIClass.get_all()
        uai_classes = [] if uai_classes is None else uai_classes
        return [
            self._expanded_uai_class(uai_class)
            for uai_class in uai_classes
        ]

    def factory_reset(self):
        """Delete all the local configuration so that the next operation
        reloads config from the configmap configuration.

        """
        self.uas_cfg.get_config()
        vols = UAIVolume.get_all()
        vols = [] if vols is None else vols
        for vol in vols:
            vol.remove()
        imgs = UAIImage.get_all()
        imgs = [] if imgs is None else imgs
        for img in imgs:
            img.remove()
        resources = UAIResource.get_all()
        resources = [] if resources is None else resources
        for resource in resources:
            resource.remove()
        uai_classes = UAIClass.get_all()
        uai_classes = [] if uai_classes is None else uai_classes
        for uai_class in uai_classes:
            uai_class.remove()
        cfgs = PopulatedConfig.get_all()
        cfgs = [] if cfgs is None else cfgs
        for cfg in cfgs:
            cfg.remove()
