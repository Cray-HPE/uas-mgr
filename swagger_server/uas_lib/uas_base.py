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
"""
Base Class for User Access Service Operations

Copyright 2020 Hewlett Packard Enterprise Development LP
"""

import time
from datetime import datetime, timezone
from flask import abort
from kubernetes import config, client
from kubernetes.client.rest import ApiException
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from swagger_server.uas_lib.uas_logging import logger
from swagger_server.models import UAI
from swagger_server.uas_lib.uas_cfg import UasCfg

# picking 40 seconds so that it's under the gateway timeout
UAI_IP_TIMEOUT = 40


class UasBase:
    """Base class used for any class implementing UAS API functionality.
    Takes care of common activities like K8s client setup, loading UAS
    configuration from the default configmap and so forth.

    """
    def __init__(self):
        """ Constructor """
        config.load_incluster_config()
        try:
            k8s_config = Configuration().get_default_copy()
        except AttributeError:
            k8s_config = Configuration()
            k8s_config.assert_hostname = False
        Configuration.set_default(k8s_config)
        self.api = core_v1_api.CoreV1Api()
        self.batch_v1 = client.BatchV1Api()
        self.uas_cfg = UasCfg()

    @staticmethod
    def get_pod_age(start_time):
        """
        given a start time as an RFC3339 datetime object, return the difference
        in time between that time and the current time, in a k8s format
        of dDhHmM - ie: 3d7h5m or 6h9m or 19m

        :return a string representing the delta between pod start and now.
        :rtype string
        """
        # on new UAI start the start_time can be None
        if start_time is None:
            logger.info("No start time provided from pod")
            return None

        try:
            now = datetime.now(timezone.utc)
            delta = now - start_time
        except Exception as err:  # pylint: disable=broad-except
            logger.warning("Unable to convert pod start time - %s", err)
            return None

        # build the output string
        retstr = ""
        days, remainder = divmod(delta.total_seconds(), 60*60*24)
        if days != 0:
            retstr += "{:d}d".format(int(days))

        hours, remainder = divmod(remainder, 60*60)
        if hours != 0:
            retstr += "{:d}h".format(int(hours))

        # always show minutes, even if 0, but only if < 1 day old
        if days == 0:
            minutes = remainder / 60
            retstr += "{:d}m".format(int(minutes))
        return retstr

    def create_service(self, service_name, service_body, namespace):
        """Create the service

        """
        resp = None
        try:
            logger.info(
                "getting service %s in namespace %s",
                service_name,
                namespace
            )
            resp = self.api.read_namespaced_service(
                name=service_name,
                namespace=namespace
            )
        except ApiException as err:
            if err.status != 404:
                logger.error(
                    "Failed to get service info while "
                    "creating UAI: %s",
                    err.reason
                )
                abort(
                    err.status,
                    "Failed to get service info while creating "
                    "UAI: %s" % err.reason
                )
        if not resp:
            try:
                logger.info(
                    "creating service %s in namespace %s",
                    service_name,
                    namespace
                )
                resp = self.api.create_namespaced_service(
                    body=service_body,
                    namespace=namespace
                )
            except ApiException as err:
                logger.info(
                    "Failed to create service\n %s",
                    (str(service_body))
                )

                logger.error(
                    "Failed to create service %s: %s",
                    service_name,
                    err.reason
                )
                resp = None
        return resp

    def delete_service(self, service_name, namespace):
        """Delete the service

        """
        resp = None
        try:
            logger.info(
                "deleting service %s in namespace %s",
                service_name,
                namespace
            )
            resp = self.api.delete_namespaced_service(
                name=service_name,
                namespace=namespace,
                body=client.V1DeleteOptions(
                    propagation_policy='Background',
                    grace_period_seconds=5
                )
            )
        except ApiException as err:
            # if we get 404 we don't want to abort because it's possible that
            # other parts are still laying around (job for example)
            if err.status != 404:
                logger.error(
                    "Failed to delete service %s: %s",
                    service_name,
                    err.reason
                )
                abort(
                    err.status, "Failed to delete service %s: %s" % (
                        service_name,
                        err.reason
                    )
                )
        return resp

    def create_job(self, job, namespace):
        """Create a UAI job

        """
        resp = None
        try:
            logger.info(
                "creating job %s in namespace %s",
                job.metadata.name,
                namespace
            )
            resp = self.batch_v1.create_namespaced_job(
                body=job,
                namespace=namespace
            )
        except ApiException as err:
            logger.error(
                "Failed to create job %s: %s",
                job.metadata.name,
                err.reason
            )
            logger.debug("namespace = %s, job = \n%s", namespace, job)
            abort(
                err.status,
                "Failed to create job %s: %s" % (
                    job.metadata.name, err.reason
                )
            )
        return resp

    def delete_job(self, job_name, namespace):
        """Delete a UAI job

        """
        resp = None
        try:
            logger.info(
                "delete job %s in namespace %s",
                job_name,
                namespace
            )
            resp = self.batch_v1.delete_namespaced_job(
                name=job_name,
                namespace=namespace,
                body=client.V1DeleteOptions(
                    propagation_policy='Background',
                    grace_period_seconds=5
                )
            )
        except ApiException as err:
            if err.status != 404:
                logger.error(
                    "Failed to delete job %s: %s",
                    job_name,
                    err.reason
                )
                abort(
                    err.status,
                    "Failed to delete job %s: %s" % (
                        job_name,
                        err.reason
                    )
                )
            # if we get 404 we don't want to abort because it's possible that
            # other parts are still laying around (services for example)
        return resp

    @staticmethod
    def gen_connection_string(username, ip_addr, tcp_port):
        """
        This function generates the uai.uai_connect_string for creating a
        ssh connection to the uai.

        The string will look like:
          ssh uai.username@uai.uai_ip -p uai.uai_port
        """
        uai_port = str(tcp_port) if tcp_port is not None else "<pending port>"
        uai_ip = ip_addr if ip_addr else "<pending IP Address>"
        port_string = (" -p %s" % uai_port) if tcp_port != 22 else ""
        user_string = ("%s@" % username) if username is not None else ""
        return "ssh %s%s%s" % (
            user_string,
            uai_ip,
            port_string
        )

    def compose_uai_from_pod(self, pod):
        """ Compose a UAI Model object from the data in a pod returned from k8s

        """
        username = pod.metadata.labels.get("user", None)
        uai_name = pod.metadata.labels.get(
            "app",
            "<internal error getting UAI name>"
        )
        opt_ports = pod.metadata.labels.get(
            "uas-uai-opt-ports",
            ""
        )
        uai_portmap = {
            int(port): int(port) for port in opt_ports.split('-')
        } if opt_ports else {}
        uai_host = pod.spec.node_name
        uai_age = self.get_pod_age(pod.status.start_time)
        uai_img = [
            ctr.image
            for ctr in pod.spec.containers
            if ctr.name == uai_name
        ][0]
        if pod.status.phase == 'Pending':
            uai_status = 'Pending'
        status_list = (
            []
            if not pod.status.container_statuses
            else pod.status.container_statuses
        )
        status_list = [
            status
            for status in status_list
            if status.name == uai_name
        ]
        uai_msg = ""
        for status in status_list:
            if status.state.running:
                ready_list = [
                    cond
                    for cond in pod.status.conditions
                    if cond.type == 'Ready'
                ]
                for cond in ready_list:
                    if pod.metadata.deletion_timestamp:
                        uai_status = 'Terminating'
                    elif cond.status == 'True':
                        uai_status = 'Running: Ready'
                    else:
                        uai_status = 'Running: Not Ready'
                        uai_msg = cond.message
            if status.state.terminated:
                uai_status = 'Terminated'
            if status.state.waiting:
                uai_status = 'Waiting'
                uai_msg = status.state.waiting.reason
        return UAI(
            username=username,
            uai_name=uai_name,
            uai_portmap=uai_portmap,
            uai_host=uai_host,
            uai_age=uai_age,
            uai_img=uai_img,
            uai_status=uai_status,
            uai_msg=uai_msg
        )

    def get_pod_info(self, job_name):
        """Retrieve pod information for a UAI pod from configuration.

        """
        pod_resp = None
        try:
            logger.info(
                "getting pod info %s",
                job_name
            )
            pod_resp = self.api.list_pod_for_all_namespaces(
                label_selector="app=%s" % job_name,
            )
        except ApiException as err:
            logger.error(
                "Failed to get pod info %s: %s",
                job_name,
                err.reason
            )
            abort(
                err.status,
                "Failed to get pod info %s: %s" % (
                    job_name,
                    err.reason
                )
            )
        # Handle the case where we got no results gracefully.  It
        # should not happen but it is better to fail cleanly.
        if not pod_resp.items:
            return None
        if len(pod_resp.items) > 1:
            logger.warning(
                "Oddly found more than one pod in "
                "job %s",
                job_name
            )
        # Only take the first one (there should only ever be one)
        pod = pod_resp.items[0]
        uai = self.compose_uai_from_pod(pod)
        srv_resp = None
        try:
            logger.info(
                "getting service info for %s-ssh in "
                "namespace %s",
                job_name,
                pod.metadata.namespace
            )
            srv_resp = self.api.read_namespaced_service(
                name=job_name + "-ssh",
                namespace=pod.metadata.namespace
            )
        except ApiException as err:
            if err.status != 404:
                logger.error(
                    "Failed to get service info for "
                    "%s-ssh: %s",
                    job_name,
                    err.reason
                )
                abort(
                    err.status,
                    "Failed to get service info for %s-ssh: %s" % (
                        job_name,
                        err.reason
                    )
                )
        # Might not have gotten service information.  If we did,
        # fill out the rest of the UAI information.  If not, then
        # return back an incomplete UAI, since there is something
        # out there.
        uai.uai_port = None
        if srv_resp:
            ports = srv_resp.spec.ports if srv_resp.spec.ports else []
            svc_type = self.uas_cfg.get_svc_type('ssh')
            public_ip = srv_resp.metadata.labels.get('uas-public-ip', "True") == "True"
            if svc_type['svc_type'] == "LoadBalancer" and public_ip:
                # There is a race condition that can lead 'ingress' to be
                # None at this point, in which case we crash when we try to
                # get the UAI info.  If ingress is None or empty, skip this
                # for now.
                if srv_resp.status.load_balancer.ingress:
                    uai.uai_ip = srv_resp.status.load_balancer.ingress[0].ip
                    uai.uai_port = 22
            elif public_ip:
                uai.uai_ip = self.uas_cfg.get_external_ip()
            else:
                uai.uai_ip = (
                    srv_resp.spec.cluster_ip
                    if srv_resp.spec.cluster_ip
                    else None
                )
            # Skip the loop below if we already know the UAI port
            ports = ports if uai.uai_port is None else []
            for srv_port in ports:
                # There should be one port that is not in the
                # optional ports, which is the port that K8s
                # assigned to this service.  It will be the one
                # not found in the UAI portmap (which was derived
                # from the 'uas-uai-opt-ports' label on the pod).
                # That is the SSH port and should go in
                # uai.uai_port.
                uai.uai_port = (
                    srv_port.port
                    if srv_port.port not in uai.uai_portmap
                    else uai.uai_port
                )
        uai.uai_connect_string = self.gen_connection_string(
            uai.username,
            uai.uai_ip,
            uai.uai_port
        )
        return uai

    def deploy_uai(self, uai_class, uai_instance, uas_cfg):
        """Deploy a UAI from a UAI Class, UAI Instance specific information,
        and the current UAS Configuration.

        """
        service_name = uai_instance.get_service_name()
        job = uai_instance.create_job_object(
            uai_class=uai_class,
            uas_cfg=uas_cfg
        )
        # Create a service for the UAI
        uas_ssh_svc = uai_instance.create_service_object(
            uai_class,
            uas_cfg
        )
        # Make sure the UAI job is created
        job_resp = None
        try:
            logger.info(
                "getting job %s in namespace %s",
                uai_instance.job_name,
                uai_class.namespace
            )
            job_resp = self.batch_v1.read_namespaced_job(
                uai_instance.job_name,
                uai_class.namespace
            )
        except ApiException as err:
            if err.status != 404:
                logger.error(
                    "Failed to read job %s: %s",
                    uai_instance.job_name,
                    err.reason
                )
                abort(
                    err.status,
                    "Failed to read job %s: %s" % (
                        uai_instance.job_name,
                        err.reason
                    )
                )
        if not job_resp:
            job_resp = self.create_job(job, uai_class.namespace)

        # Start the UAI services
        logger.info("creating the UAI service %s", service_name)
        svc_resp = self.create_service(
            service_name,
            uas_ssh_svc,
            uai_class.namespace
        )
        if not svc_resp:
            # Clean up the UAI
            logger.error(
                "failed to create service, deleting UAI %s",
                uai_instance.job_name
            )
            self.remove_uais([uai_instance.job_name])
            abort(
                404,
                "Failed to create service: %s" % service_name
            )

        # Wait for the UAI IP to be set
        total_wait = 0.0
        delay = 0.5
        while True:
            uai_info = self.get_pod_info(
                job_resp.metadata.name
            )
            if uai_info and uai_info.uai_ip:
                break
            if total_wait >= UAI_IP_TIMEOUT:
                abort(
                    504,
                    "Failed to get IP for service: %s" % service_name
                )
            time.sleep(delay)
            total_wait += delay
            logger.info(
                "waiting for uai_ip %s seconds",
                str(total_wait)
            )
        return uai_info

    def select_jobs(self, labels=None, host=None):
        """Get a list of UAI names from the specified host (if any) that meet
        the criteria in the specified labels (if any).

        """
        labels = [] if labels is None else labels
        # Has to be a UAI (uas=managed) at least, along with any other
        # labels specified.
        label_selector = "uas=managed"
        if labels:
            label_selector = "%s,%s" % (label_selector, ','.join(labels))
        try:
            logger.info(
                "listing jobs matching: host %s,"
                " labels %s",
                host,
                label_selector
            )
            resp = self.batch_v1.list_job_for_all_namespaces(
                label_selector=label_selector
            )
        except ApiException as err:
            if err.status != 404:
                logger.error(
                    "Failed to get job list: %s",
                    err.reason
                )
                abort(err.status, "Failed to get job list")
        return [job.metadata.name for job in resp.items]

    def get_uai_namespace(self, job_name):
        """Determine the namespace a named UAI is deployed in.

        """
        resp = self.batch_v1.list_job_for_all_namespaces(
            label_selector="app=%s" % job_name
        )
        if resp is None or not resp.items:
            return None
        if len(resp.items) > 1:
            logger.warning(
                "Oddly found more than one job named %s",
                job_name
            )
        return resp.items[0].metadata.namespace

    def get_uai_list(self, job_names):
        """Get a list of UAIs from the specified host (if any)
        that meet the criteria in the specified label (if any).

        """
        uai_list = []
        for job_name in job_names:
            uai = self.get_pod_info(job_name)
            if uai is not None:
                uai_list.append(uai)
        return uai_list

    def remove_uais(self, job_names):
        """Remove a list of UAIs by their names from the specified
        namespace.

        """
        resp_list = []
        for job_name in job_names:
            namespace = self.get_uai_namespace(job_name)
            if namespace is None:
                # This job doesn't exist or doesn't have a namespace
                # (I dont think the latter is possible).  Skip it.
                continue

            # Do services first so that we don't orphan one if they abort
            service_resp = self.delete_service(
                job_name + "-ssh",
                namespace
            )
            job_resp = self.delete_job(
                job_name,
                namespace
            )
            if job_resp is None and service_resp is None:
                message = "Failed to delete %s - Not found" % job_name
            else:
                message = "Successfully deleted %s" % job_name
            resp_list.append(message)
        return resp_list
