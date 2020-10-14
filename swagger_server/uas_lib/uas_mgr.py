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
from swagger_server.uas_data_model.populated_config import PopulatedConfig

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
        resource = UAIResource.get(resource_id)
        if resource is None:
            abort(404, "resource config '%s' does not exist" % resource_id)
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
        return [
            {
                'resource_id': resource.resource_id,
                'comment': resource.comment,
                'limit': resource.limit,
                'request': resource.request
            }
            for resource in resources
        ]

    def factory_reset(self):
        """Delete all the local configuration so that the next operation
        reloads config from the configmap configuration.

        """
        self.uas_cfg.get_config()
        vols = UAIVolume.get_all()
        for vol in vols:
            vol.remove()
        imgs = UAIImage.get_all()
        for img in imgs:
            img.remove()
        resources = UAIResource.get_all()
        for resource in resources:
            resource.remove()
        cfgs = PopulatedConfig.get_all()
        for cfg in cfgs:
            cfg.remove()
