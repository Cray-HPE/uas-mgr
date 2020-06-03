#
# Copyright 2018, Cray Inc.  All Rights Reserved.
#
"""
   Manages Cray User Access Node instances.
"""


import logging
import sys
import yaml
from flask import abort
import sshpubkeys
import sshpubkeys.exceptions as sshExceptions
from kubernetes import client
from swagger_server.uas_data_model.uai_volume import UAIVolume
from swagger_server.uas_data_model.uai_image import UAIImage


UAS_CFG_LOGGER = logging.getLogger('uas_cfg')
UAS_CFG_LOGGER.setLevel(logging.INFO)
# pylint: disable=invalid-name
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
# pylint: disable=invalid-name
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s"
                              " - %(message)s")
handler.setFormatter(formatter)
UAS_CFG_LOGGER.addHandler(handler)
UAS_CFG_DEFAULT_PORT = 30123
UAS_CFG_OPTIONAL_PORTS = [80, 443, 8888]
UAS_CFG_DEFAULT_UAI_NAMESPACE = "default"


class UasCfg:
    """
    The UasCfg class provides the site configuration data to the
    User Access Services.
    """
    def __init__(self, uas_cfg='/etc/uas/cray-uas-mgr.yaml'):
        """Constructor

        """
        self.uas_cfg = uas_cfg

    def get_config(self):
        """Load the configuration from the configmap.

        This loads in the UAS Manager configmap to obtain the
        configuration settings for the UAS Manager.  For items that
        are managed under ETCD, the configmap is used the first time
        UAS Manager runs on a new system to load the initial settings
        into ETCD and then ignored from then on.  For items that are
        only configured in the configmap, updates to the configmap
        will be read in each time this is called.

        """
        cfg = {}
        try:
            with open(self.uas_cfg) as uascfg:
                # pylint: disable=no-member
                cfg = yaml.load(uascfg, Loader=yaml.FullLoader)
        except (TypeError, IOError):
            abort(404, "configmap %s not found" % self.uas_cfg)
        # The empty case can be parsed as None, fix that...
        if cfg is None:
            cfg = {}

        # We have the configmap contents, now, populate any ETCD
        # tables that need populating...
        if UAIImage.get_all() is None:
            # There are no UAI Image objects in ETCD, populate that
            # table now.
            UAIImage.register()
            uas_imgs = cfg.get('uas_images', {})
            default_name = uas_imgs.get('default_image', None)
            if default_name is not None:
                UAIImage(imagename=default_name, default=True).put()
            imgs = uas_imgs.get('images', [])
            for name in imgs:
                # The default (if any) has already been added, don't duplicate it here.
                if name != default_name:
                    UAIImage(imagename=name, default=False).put()
        if UAIVolume.get_all() is None:
            # There are no UAI Volume objects in ETCD, populate that
            # table now.
            UAIVolume.register()
            for vol in cfg.get('volume_mounts', []):
                UAIVolume.add_etcd_volume(vol)
        return cfg

    def get_images(self):
        """ Retrieve a list of image names.
        """
        _ = self.get_config()
        imgs = UAIImage.get_all()
        if not imgs:
            return None
        images = []
        for img in imgs:
            images.append(img.imagename)
        return images

    def get_default_image(self):
        """Retrieve the name of the default image.

        """
        _ = self.get_config()
        imgs = UAIImage.get_all()
        for img in imgs:
            if img.default:
                return img.imagename
        return None

    def validate_image(self, imagename):
        """Determine whether the specified imagename is a known image name.

        """
        _ = self.get_config()
        imgs = UAIImage.get_all()
        for img in imgs:
            if imagename == img.imagename:
                return True
        return False

    def get_external_ip(self):
        """
        This function returns external ip for UAI ssh access
        :return: external IP address
        :rtype str
        """
        cfg = self.get_config()
        ext_ip = None
        if not cfg:
            return ext_ip
        try:
            ext_ip = cfg['uas_ip']
        except KeyError:
            ext_ip = None
        return ext_ip

    def gen_volume_mounts(self):
        """Generate a list of volume mounts from the configuration.  Return
        the K8s volume mount for each.

        """
        _ = self.get_config()
        volume_mount_list = []
        volume_mounts = UAIVolume.get_all()
        for mnt in volume_mounts:
            volume_mount_list.append(
                client.V1VolumeMount(
                    name=mnt.volumename,
                    mount_path=mnt.mount_path
                )
            )
        return volume_mount_list

    def gen_volumes(self):
        """Generate a list of volumes from the configuration.  Return the K8s
        volume definitions for each.

        """
        _ = self.get_config()
        volume_list = []
        volume_mounts = UAIVolume.get_all()
        for vol in volume_mounts:
            # Okay, this is magic, so it requires a bit of
            # explanation. The 'client.V1Volume()' call takes a long
            # list of different arguments, one for each supported type
            # of volume source.  Since our volume storage source is
            # already encapsulated in a volume description which
            # identifies the source type and the source parameters,
            # what we want to do is construct a dictionary using the
            # top-level key from the volume description (which
            # identifies the source type) as the name of the argument
            # to be assigned into, and the name of the volume to be
            # defined, then pass the dictionary instead of explicit
            # arguments.
            volume_args = {}
            volume_args['name'] = vol.volumename
            volume_source_key = list(vol.volume_description.keys())[0]
            volume_args[volume_source_key] = UAIVolume.get_volume_source(
                vol.volume_description
            )
            volume_list.append(client.V1Volume(**volume_args))
        return volume_list

    def gen_port_entry(self, port, service):
        """Generate a port entry for the service object """
        svc_type = self.get_svc_type(service_type="ssh")
        if service:
            if svc_type['svc_type'] == "LoadBalancer":
                target_port = port
                if port == UAS_CFG_DEFAULT_PORT:
                    port = 22
                    target_port = UAS_CFG_DEFAULT_PORT
                return client.V1ServicePort(name='port' + str(port),
                                            port=port,
                                            target_port=target_port,
                                            protocol="TCP")
            return client.V1ServicePort(name='port' + str(port),
                                        port=port,
                                        protocol="TCP")
        return client.V1ContainerPort(container_port=port)

    # pylint: disable=too-many-branches
    def gen_port_list(self,
                      service_type=None,
                      service=False,
                      optional_ports=None):
        """
        gen_port_list creates a list of kubernetes port entry objects.
        The type of the port entry object depends on whether the service_type
        is "ssh" or "service", the latter being used for inter-shasta service
        connections.

        :param: service_type: one of either "ssh" or "service"
        :type service_type: str
        :param service: True creates a ServicePort object, False creates a
                        ContainerPort object
        :type service: bool
        :param optional_ports: An optional list of ports to project in
                               addition to the port used for SSH to the UAI
        :type optional_ports: list
        :return port_list: A list of kubernetes port entry objects
        :rtype list
        """
        # Avoid using a default value of [] in the call because that can
        # result in modification of the empty-list for the call if the
        # argument is ever modified.
        if optional_ports is None:
            optional_ports = []
        UAS_CFG_LOGGER.info("optional_ports: %s", optional_ports)
        cfg = self.get_config()
        port_list = []
        if not cfg:
            return port_list
        if service_type == "service":
            # Read the configmap for uas_svc_ports (ports to project
            # to other services) cfg_port_list is a list of port
            # numbers to be processed into kubernetes port entry
            # objects
            try:
                cfg_port_list = cfg['uas_svc_ports']
                if optional_ports:
                    # Add any optional ports to the cfg_port_list
                    for port in optional_ports:
                        cfg_port_list.append(port)
            except KeyError:
                cfg_port_list = optional_ports
        else:
            # Read the configmap for uas_ports (ports to project to
            # the customer network) cfg_port_list is a list of port
            # numbers to be processed into kubernetes port entry
            # objects
            try:
                cfg_port_list = cfg['uas_ports']
                if optional_ports:
                    # Add any optional ports to the cfg_port_list
                    for port in optional_ports:
                        cfg_port_list.append(port)
                for port in cfg_port_list:
                    # check if a port range was given
                    if isinstance(port, str):
                        raise ValueError("uas_ports does not support ranges")
            except KeyError:
                cfg_port_list = [self.get_default_port()]
                if optional_ports:
                    # Add any optional ports to the cfg_port_list
                    for port in optional_ports:
                        cfg_port_list.append(port)

        UAS_CFG_LOGGER.info("cfg_port_list: %s", cfg_port_list)
        for port in cfg_port_list:
            # check if a port range was given
            if isinstance(port, str):
                # Lint thinks port is an 'int' but we know (because we
                # checked) that its a string.
                #
                # pylint: disable=no-member
                port_range = port.split(':')
                # build entries for all ports between port_range[0]
                # and port_range[1]
                for i in range(int(port_range[0]), int(port_range[1])+1):
                    port_list.append(self.gen_port_entry(i, service))
            else:
                port_list.append(self.gen_port_entry(port, service))
        return port_list

    def get_svc_type(self, service_type=None):
        """Get the service type for UAIs from the config.

        """
        cfg = self.get_config()
        svc_type = {'svc_type': None, 'ip_pool': None, 'valid': False}
        if not cfg:
            # Return defaults if no configuration exists
            if service_type == "service":
                svc_type['svc_type'] = 'ClusterIP'
            if service_type == "ssh":
                svc_type['svc_type'] = 'NodePort'
        else:
            if service_type == "service":
                svc_type['svc_type'] = cfg.get('uas_svc_type', 'ClusterIP')
                if svc_type['svc_type'] == "LoadBalancer":
                    svc_type['ip_pool'] = cfg.get('uas_svc_lb_pool', None)
            if service_type == "ssh":
                svc_type['svc_type'] = cfg.get('uas_ssh_type', 'NodePort')
                if svc_type['svc_type'] == "LoadBalancer":
                    svc_type['ip_pool'] = cfg.get('uas_ssh_lb_pool', None)
        svc_type['valid'] = svc_type['svc_type'] in ['NodePort',
                                                     'ClusterIP',
                                                     'LoadBalancer']
        return svc_type

    @staticmethod
    def get_default_port():
        """
        getter for the default UAS port
        :return: UAS default port
        :rtype int
        """
        return UAS_CFG_DEFAULT_PORT

    def create_readiness_probe(self):
        """
        Creates a k8s readiness check object for use during container launch
        :return: k8s V1Probe
        :rtype object
        """
        cfg = self.get_config()
        try:
            cfg_port_list = cfg['uas_ports']
        except KeyError:
            cfg_port_list = self.get_default_port()
        # XXX - pick first port, switch when the uas_ports type is changed
        socket = client.V1TCPSocketAction(port=cfg_port_list[0])
        return client.V1Probe(initial_delay_seconds=2,
                              period_seconds=3,
                              tcp_socket=socket)

    @staticmethod
    def validate_ssh_key(ssh_key):
        """
        checks whether the ssh_key is a valid public key
        ssh_key input is expected to be a string
        :return: returns True if valid public key
        :rtype bool
        """
        try:
            ssh = sshpubkeys.SSHKey(ssh_key, strict=False,
                                    skip_option_parsing=True)
            ssh.parse()
            return True
        except (NotImplementedError, sshExceptions.MalformedDataError) as err:
            UAS_CFG_LOGGER.error("Invalid key: %s", err)
        except sshExceptions.InvalidKeyError as err:
            UAS_CFG_LOGGER.error("Unknown key type: %s", err)
        except Exception as err:  # pylint: disable=broad-except
            UAS_CFG_LOGGER.error("Invalid non-key input: %s", err)
        return False

    @staticmethod
    def get_valid_optional_ports():
        """
        Return list of valid optional ports.
        :return: List of valid optional ports.
        :rtype list
        """
        return UAS_CFG_OPTIONAL_PORTS

    def get_uai_namespace(self):
        """
        Gets the namespace in which UAIs will be created. This namespace is
        assumed to have been created by the installation process. Defaults
        to UAS_CFG_DEFAULT_UAI_NAMESPACE if unset.
        :return: k8s namespace
        :rtype string
        """
        cfg = self.get_config()
        if not cfg:
            return None
        try:
            return cfg['uai_namespace']
        except (TypeError, KeyError):
            UAS_CFG_LOGGER.info("configuration uai_namespace not found, "
                                "using %s namespace for UAIs",
                                UAS_CFG_DEFAULT_UAI_NAMESPACE)
            return UAS_CFG_DEFAULT_UAI_NAMESPACE
