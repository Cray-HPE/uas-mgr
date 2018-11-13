#
# Copyright 2018, Cray Inc.  All Rights Reserved.
#
# Description:
#   Dispatches requests for Cray User Access Node instances.
#

from flask import request, jsonify, render_template
from swagger_server.uas_lib.uas_cfg import UasCfg
from swagger_server.uas_lib.uan_mgr import UanManager


def request_wants_json():
    best = request.accept_mimetypes.best_match(['application/json',
                                                'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > request.accept_mimetypes['text/html']


class DispatchManager(object):

    def __init__(self):
        self.uan_mgr = UanManager()
        self.uas_cfg = UasCfg()

    def create_uan(self, uan_args):
        username = uan_args['username']
        usersshpubkey = uan_args['usersshpubkey']
        if not username or not usersshpubkey:
            err_msg = 'No username or ssh public key path given.'
            return render_template('uas_error_response.html',
                                   error_msg=err_msg)
        if uan_args['uan_image']:
            # There is only one uan_image allowed, so take the first element
            # of the uan_image list.
            uan_image = uan_args['uan_image']
        else:
            uan_image = self.uas_cfg.get_default_image()
        if not self.uas_cfg.validate_image(uan_image):
            err_msg = ('Invalid image requested. Valid images are: %s. ' 
                       'Default image is: %s' %
                       (self.uas_cfg.get_images(),
                        self.uas_cfg.get_default_image()))
            return render_template('uas_error_response.html',
                                    error_msg=err_msg)
        if not self.uas_cfg.get_external_ips():
            err_msg = ('UAS misconfigured (uas_ips not set). Please contact '
                       'your system administrator.')
            return render_template('uas_error_response.html',
                                   error_msg=err_msg)

        uan = self.uan_mgr.create_uan(username, usersshpubkey, uan_image)
        return render_template('uan_create_response.html',
                               username=username, imagename=uan_image,
                               uan_name=uan.uan_name,
                               host_ip=uan.uan_ip, phase=uan.uan_status,
                               reason=uan.uan_msg,
                               uan_port=uan.uan_port)

    def list_uans(self, uan_args):
        username = uan_args['username']
        resp = self.uan_mgr.list_uans_for_user(username, namespace='default')
        return render_template('uan_list_response.html', username=username,
                               uan_list=resp)

    def delete_uan_request(self, uan_args):
        username = uan_args['username']
        resp = self.uan_mgr.list_uans_for_user(username, namespace='default')
        return render_template('uan_delete_select.html', username=username,
                               uan_list=resp)

    def delete_uans(self, uan_list):
        resp_list = self.uan_mgr.delete_uans(uan_list)
        return render_template('uan_delete_response.html', uan_list=resp_list)
