import imghdr
# from PIL import Image
import logging
import os
import re
import uuid

from flask import Blueprint
from flask import Response
from flask import abort
from flask import current_app
from flask import escape
from flask import render_template
from flask import request
from flask import send_file
from flask_login import current_user
from flask_login import login_required
from zerrphix.util.filesystem import execute

from zerrphix.util.filesystem import get_file_extension
from zerrphix.util.filesystem import make_dir
from zerrphix.util.image import resize_and_crop

import json
import mimetypes
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

scan_paths = Blueprint('scan_paths', __name__)

log = logging.getLogger(__name__)

@scan_paths.route('/scan_path/test_new', methods=['POST'])
@login_required
def scan_path_test():
    if request.method == 'POST':
        post_data = request.form
        path = post_data['path']
        # do removign of .././ etc
        if path[:1] != '/':
            path = '/%s' % path
        if post_data['fs_type'] == '2':
            zp_share_id = post_data['zp_share_id']
            zp_share_server_id = post_data['zp_share_server_id']
            zp_share_credential_id = post_data['zp_share_credential_id']
            can_connect, is_dir, is_file, num_filefolders, error_text = current_app.config["AdminHTTPScanPathFuncs"].test_new_share(
                post_data['path'],
                post_data['zp_share_id'],
                post_data['zp_share_server_id'],
                post_data['zp_share_credential_id']
            )
            #log.error(error_text)
            #error_text = escape(error_text)

            share_reference_name = current_app.config["AdminHTTPScanPathFuncs"].get_share_reference_name(zp_share_id)
            share_credential_reference_name = current_app.config["AdminHTTPScanPathFuncs"].get_share_credential_reference_name(zp_share_credential_id)
            share_server_reference_name = current_app.config["AdminHTTPScanPathFuncs"].get_share_server_reference_name(zp_share_server_id)

            if is_dir is True:
                message = escape('REMOTE path %s on share %s, server %s, using credential %s '
                                 'is a dir and has %s filefolders' % (path, share_reference_name,
                                share_server_reference_name, share_credential_reference_name, num_filefolders))
                return Response('{"success":true,"error":null,"message": %s}' % json.dumps(message),
                                mimetype='text/plain')
            elif is_file is True:
                message = escape('An error occured')
                error = escape('REMOTE path %s on share %s, server %s, using credential %s '
                               'is a file not a dir. \n%s' % (path, share_reference_name,
                                share_server_reference_name, share_credential_reference_name, error_text))
                return Response('{"success":false,"error":%s,"message": %s}' % (json.dumps(error),
                                                                                  json.dumps(message)),
                                mimetype='text/plain')
            elif can_connect is True:
                message = escape('An error occured')
                error = escape('REMOTE path %s on share %s, server %s, using credential %s '
                               'is not a file or dir. If you believe this is incorrect please check the'
                               ' host username and password are correct\n%s' % (path, share_reference_name,
                                share_server_reference_name, share_credential_reference_name, error_text))
                return Response('{"success":false,"error":%s,"message": %s}' % (json.dumps(error),
                                                                                  json.dumps(message)),
                                mimetype='text/plain')
            else:
                message = escape('An error occured')
                error = escape('REMOTE Cannot connect to share %s, server %s, using credential %s.\n%s' % (share_reference_name,
                                share_server_reference_name, share_credential_reference_name, error_text))
                return Response('{"success":false,"error":%s,"message": %s}' % (json.dumps(error),
                                                                                  json.dumps(message)),
                                mimetype='text/plain')
        else:
            if os.path.isdir(path):
                exception_text = ''
                numfilefolders = None
                try:
                    numfilefolders = len(os.listdir(path))
                except Exception as e:
                    exception_text = str(e)
                    log.error(exception_text)
                if isinstance(numfilefolders, int):
                    message = escape('LOCAL path %s is a dir with %s filefolders' % (path, numfilefolders))
                    return Response('{"success":true,"error":null,"message": %s}' % json.dumps(message))
                else:
                    message = escape('LOCAL path %s is a dir but cannot list its contents due to %s' % (
                        path, exception_text))
                    return Response('{"success":true,"error":null,"message": %s}' % json.dumps(message))
            else:
                message = escape('An error occured')
                error = escape('LOCAL path %s is not a dir' % path)
                return Response('{"success":true,"error":%s,"message": %s}' % (json.dumps(error),
                                                                               json.dumps(message)
                                                                               ))


@scan_paths.route('/scan_path', methods=['GET', 'POST'])
@login_required
def scan_path_index():
    scan_path_editable_dict = {'path':'text',
                               'fs_type': 'select',
                               'force_full_scan': 'bool',
                               'always_full_scan': 'bool',
                               'zp_share_id': 'select',
                               'zp_share_server_id': 'select',
                               'zp_share_credential_id': 'select',
                               'enabled': 'bool',
                               'verify': 'bool'
                               }
    scan_path_add_dict = {'path':'text',
                          'fs_type': 'select',
                          'zp_library_id': 'select',
                          'force_full_scan': 'bool',
                          'always_full_scan': 'bool',
                          'zp_share_id': 'select',
                          'zp_share_server_id': 'select',
                          'zp_share_credential_id': 'select',
                               'enabled': 'bool',
                               'verify': 'bool'
                          }
    if request.method == 'POST':
        # log.warning(request.form['tv_genre_list'])
        # pass
        # log.warning(dir(request.form))
        #log.error('request.form %s', request.form)
        valid_entry_regex = r'''^(?P<zp_scan_path_id>\d+)_(?P<section>path|fs_type|zp_share_id|zp_share_server_id|zp_share_credential_id|last_mod|force_full_scan|always_full_scan|enabled|verify)$'''
        #valid_edit_entry_regex = r'''^(?P<zp_scan_path_id>\d+)_(?P<section>path|fs_type|zp_share_id|zp_share_server_id|zp_share_credential_id|last_mod|force_full_scan|always_full_scan|ost_data)$'''
        # todo check paths exist
        post_data = request.form
        #log.error(post_data.keys())
        if post_data:
            if post_data['type'] == 'add':
                path = post_data['path']
                zp_library_id = int(post_data['zp_library_id'])
                fs_type = int(post_data['fs_type'])
                force_full_scan = int(post_data['force_full_scan'])
                always_full_scan = int(post_data['always_full_scan'])
                zp_share_id = int(post_data['zp_share_id'])
                zp_share_server_id = int(post_data['zp_share_server_id'])
                zp_share_credential_id = int(post_data['zp_share_credential_id'])
                enabled = int(post_data['enabled'])
                verify = int(post_data['verify'])
                if fs_type == 2:
                    if zp_share_id > 0 and zp_share_server_id > 0 and zp_share_credential_id > 0:
                        current_app.config["AdminHTTPScanPathFuncs"].add_scan_path(
                            path, zp_library_id, fs_type, force_full_scan, always_full_scan,
                            zp_share_id=zp_share_id, zp_share_server_id=zp_share_server_id,
                            zp_share_credential_id=zp_share_credential_id
                        )
                    else:
                        log.error('zp_share_id and zp_share_server_id and zp_share_credential_id must all be > 0')
                else:
                    current_app.config["AdminHTTPScanPathFuncs"].add_scan_path(
                        path, zp_library_id, fs_type, force_full_scan, always_full_scan, enabled, verify
                    )
            elif post_data['type'] == 'edit':
                processing_dict = {}
                for post_data_key in post_data:
                    log.debug('post_data_key %s', post_data_key)
                    log.debug('post_data[post_data_key] %s', post_data[post_data_key])
                    post_data_key_match = re.match(valid_entry_regex, post_data_key)
                    if post_data_key_match:
                        post_data_key_match_group_dict = post_data_key_match.groupdict()
                        if post_data_key_match_group_dict['zp_scan_path_id'] not in processing_dict:
                            processing_dict[post_data_key_match_group_dict['zp_scan_path_id']] = {}
                        if scan_path_editable_dict[post_data_key_match_group_dict['section']] == 'text':
                            processing_dict[post_data_key_match_group_dict['zp_scan_path_id']][
                                post_data_key_match_group_dict['section']] = post_data[post_data_key]
                        else:
                            processing_dict[post_data_key_match_group_dict['zp_scan_path_id']][
                                post_data_key_match_group_dict['section']] = int(post_data[post_data_key])
                    elif post_data_key not in ['type']:
                        log.error('post_data_key %s failed to match valid_entry_regex %s', post_data_key,
                                  valid_entry_regex)
                for zp_scan_path_id in processing_dict:
                    log.trace(processing_dict[zp_scan_path_id])
                    #log.error(processing_dict[zp_scan_path_id])
                    if processing_dict[zp_scan_path_id]['fs_type'] == 2 and 'zp_share_id' in processing_dict[zp_scan_path_id]:
                        current_app.config["AdminHTTPScanPathFuncs"].update_scan_path(
                            zp_scan_path_id,
                            processing_dict[zp_scan_path_id]['path'],
                            processing_dict[zp_scan_path_id]['fs_type'],
                            processing_dict[zp_scan_path_id]['force_full_scan'],
                            processing_dict[zp_scan_path_id]['always_full_scan'],
                            processing_dict[zp_scan_path_id]['enabled'],
                            processing_dict[zp_scan_path_id]['verify'],
                            zp_share_id=processing_dict[zp_scan_path_id]['zp_share_id'],
                            zp_share_server_id=processing_dict[zp_scan_path_id]['zp_share_server_id'],
                            zp_share_credential_id=processing_dict[zp_scan_path_id]['zp_share_credential_id'],
                        )
                    else:
                        current_app.config["AdminHTTPScanPathFuncs"].update_scan_path(
                            zp_scan_path_id,
                            processing_dict[zp_scan_path_id]['path'],
                            processing_dict[zp_scan_path_id]['fs_type'],
                            processing_dict[zp_scan_path_id]['force_full_scan'],
                            processing_dict[zp_scan_path_id]['always_full_scan'],
                            processing_dict[zp_scan_path_id]['enabled'],
                            processing_dict[zp_scan_path_id]['verify']
                        )
            current_app.config["AdminHTTPGenFuncs"].set_process_force_run(1)
            current_app.config["AdminHTTPGenFuncs"].set_process_force_run(9)
        else:
            log.error('post_data %s empty', post_data)
        #if 'tv_genre_list' in request.form:
    scan_path_list = current_app.config["AdminHTTPScanPathFuncs"].scan_path_list()
    share_dict = current_app.config["AdminHTTPScanPathFuncs"].get_share_dict()
    share_server_dict = current_app.config["AdminHTTPScanPathFuncs"].get_share_server_dict()
    share_credential_dict = current_app.config["AdminHTTPScanPathFuncs"].get_share_credential_dict()
    share_fs_type_dict = {1: {'name': 'local'},
                    2: {'name': 'smb'},}
    share_library_dict = {1:{'name':'film'},
                    2: {'name': 'tv'},
                    }
    scan_path_keys = [
        'path',
        'zp_library_id',
        'fs_type',
        'zp_share_id',
        'zp_share_server_id',
        'zp_share_credential_id',
        'last_mod' ,
        'force_full_scan',
        'always_full_scan',
         'enabled',
         'verify'
    ]
    scan_path_title_dict = {'path': 'Path',
                            'zp_library_id': 'Library',
                            'fs_type': 'Filesystem',
                            'zp_share_id': 'Share Name *',
                            'zp_share_server_id': 'Server **',
                            'zp_share_credential_id': 'Credential ****',
                            'last_mod': 'Last Mod *****',
                            'force_full_scan': 'Force Full Scan',
                            'always_full_scan': 'Always Full Scan',
                               'enabled': 'Enabled',
                               'verify': 'Verify'
                            }
    scan_path_add_keys = [
        'path',
        'zp_library_id',
        'fs_type',
        'zp_share_id',
        'zp_share_server_id',
        'zp_share_credential_id',
        'force_full_scan',
        'always_full_scan',
         'enabled',
         'verify'
    ]
    log.debug('share_dict', share_dict)
    log.debug('share_server_dict', share_server_dict)
    log.debug('share_credential_dict', share_credential_dict)
    return render_template('scan_paths/index.html', scan_path_list=scan_path_list,
                           scan_path_keys=scan_path_keys,
                           scan_path_editable_dict=scan_path_editable_dict,
                           share_dict=share_dict,
                           share_server_dict=share_server_dict,
                           share_credential_dict=share_credential_dict,
                           share_fs_type_dict=share_fs_type_dict,
                           share_library_dict=share_library_dict,
                           scan_path_title_dict=scan_path_title_dict,
                           scan_path_add_keys=scan_path_add_keys,
                           scan_path_add_dict=scan_path_add_dict)



@scan_paths.route('/scan_path/share', methods=['GET', 'POST'])
@login_required
def scan_path_share():
    share_editable_dict = {'ref_name': 'text',
        'share_name': 'text',
                           'domain': 'text'}
    valid_entry_regex = r'''^(?P<zp_share>\d+)_(?P<section>ref_name|share_name|domain)$'''
    # valid_edit_entry_regex = r'''^(?P<zp_scan_path_id>\d+)_(?P<section>path|fs_type|zp_share_id|zp_share_server_id|zp_share_credential_id|last_mod|force_full_scan|always_full_scan|ost_data)$'''
    # todo check paths exist
    post_data = request.form
    # log.error(post_data.keys())
    if post_data:
        if post_data['type'] == 'add':
            if len(post_data['ref_name']) >= 1 and len(post_data['share_name']) >= 1:
                current_app.config["AdminHTTPScanPathFuncs"].add_share(
                    post_data['ref_name'], post_data['share_name'], post_data['domain']
                )
        elif post_data['type'] == 'edit':
            processing_dict = {}
            for post_data_key in post_data:
                log.debug('post_data_key %s', post_data_key)
                log.debug('post_data[post_data_key] %s', post_data[post_data_key])
                post_data_key_match = re.match(valid_entry_regex, post_data_key)
                if post_data_key_match:
                    post_data_key_match_group_dict = post_data_key_match.groupdict()
                    if post_data_key_match_group_dict['zp_share'] not in processing_dict:
                        processing_dict[post_data_key_match_group_dict['zp_share']] = {}
                    if share_editable_dict[post_data_key_match_group_dict['section']] == 'text':
                        processing_dict[post_data_key_match_group_dict['zp_share']][
                            post_data_key_match_group_dict['section']] = post_data[post_data_key]
                elif post_data_key != 'type':
                    log.error('post_data_key %s failed to match valid_entry_regex %s', post_data_key,
                          valid_entry_regex)
            for zp_share_id in processing_dict:
                # log.error(processing_dict[zp_scan_path_id])
                current_app.config["AdminHTTPScanPathFuncs"].update_share(
                    zp_share_id,
                    processing_dict[zp_share_id]['ref_name'],
                    processing_dict[zp_share_id]['share_name'],
                    processing_dict[zp_share_id]['domain']
                )
    share_list = current_app.config["AdminHTTPScanPathFuncs"].get_share_list()
    share_title_dict = {'ref_name': 'Reference Name',
        'share_name': 'Share Name',
                        'domain': 'Domain'}
    share_keys = [
        'ref_name',
        'share_name',
        'domain']
    return render_template('scan_paths/share.html', share_list=share_list,
                           share_editable_dict=share_editable_dict,
                           share_keys=share_keys,
                           share_title_dict=share_title_dict,
                           share_add_keys=share_keys,
                           share_add_dict = share_editable_dict)

@scan_paths.route('/scan_path/server', methods=['GET', 'POST'])
@login_required
def scan_path_share_server():
    share_server_editable_dict = {
        'ref_name': 'text',
        'remote_name': 'text',
        'hostname': 'text',
                           'port': 'text'}
    valid_entry_regex = r'''^(?P<zp_share_server>\d+)_(?P<section>remote_name|hostname|port|ref_name)$'''
    # valid_edit_entry_regex = r'''^(?P<zp_scan_path_id>\d+)_(?P<section>path|fs_type|zp_share_server_id|zp_share_server_server_id|zp_share_server_credential_id|last_mod|force_full_scan|always_full_scan|ost_data)$'''
    # todo check paths exist
    post_data = request.form
    # log.error(post_data.keys())
    if post_data:
        if post_data['type'] == 'add':
            if len(post_data['remote_name']) >= 1 and len(post_data['hostname']) >= 1 and len(post_data['port']) >= 1:
                current_app.config["AdminHTTPScanPathFuncs"].add_share_server(
                    post_data['ref_name'], post_data['remote_name'], post_data['hostname'], post_data['port']
                )
        elif post_data['type'] == 'edit':
            processing_dict = {}
            for post_data_key in post_data:
                log.debug('post_data_key %s', post_data_key)
                log.debug('post_data[post_data_key] %s', post_data[post_data_key])
                post_data_key_match = re.match(valid_entry_regex, post_data_key)
                if post_data_key_match:
                    post_data_key_match_group_dict = post_data_key_match.groupdict()
                    if post_data_key_match_group_dict['zp_share_server'] not in processing_dict:
                        processing_dict[post_data_key_match_group_dict['zp_share_server']] = {}
                    if share_server_editable_dict[post_data_key_match_group_dict['section']] == 'text':
                        processing_dict[post_data_key_match_group_dict['zp_share_server']][
                            post_data_key_match_group_dict['section']] = post_data[post_data_key]
                elif post_data_key != 'type':
                    log.error('post_data_key %s failed to match valid_entry_regex %s', post_data_key,
                          valid_entry_regex)
            for zp_share_server_id in processing_dict:
                # log.error(processing_dict[zp_scan_path_id])
                current_app.config["AdminHTTPScanPathFuncs"].update_share_server(
                    zp_share_server_id,
                    processing_dict[zp_share_server_id]['ref_name'],
                    processing_dict[zp_share_server_id]['remote_name'],
                    processing_dict[zp_share_server_id]['hostname'],
                    processing_dict[zp_share_server_id]['port']
                )
    share_server_list = current_app.config["AdminHTTPScanPathFuncs"].get_server_list()
    share_server_title_dict = {
        'ref_name': 'Reference Name',
        'remote_name': 'Remote Name',
        'hostname': 'Hostname',
                        'port': 'Port'}
    share_server_keys = [
        'ref_name',
        'remote_name',
        'hostname',
        'port']
    return render_template('scan_paths/share_server.html', share_server_list=share_server_list,
                           share_server_editable_dict=share_server_editable_dict,
                           share_server_keys=share_server_keys,
                           share_server_title_dict=share_server_title_dict,
                           share_server_add_keys=share_server_keys,
                           share_server_add_dict = share_server_editable_dict)


@scan_paths.route('/scan_path/credential', methods=['GET', 'POST'])
@login_required
def scan_path_credential():
    share_credential_editable_dict = {'ref_name': 'text',
        'zp_cred_u': 'text',
                           'zp_cred_p': 'password'}
    valid_entry_regex = r'''^(?P<zp_share_credential>\d+)_(?P<section>ref_name|zp_cred_u|zp_cred_p)$'''
    # valid_edit_entry_regex = r'''^(?P<zp_scan_path_id>\d+)_(?P<section>path|fs_type|zp_share_credential_id|zp_share_credential_credential_id|zp_share_credential_credential_id|last_mod|force_full_scan|always_full_scan|ost_data)$'''
    # todo check paths exist
    post_data = request.form
    # log.error(post_data.keys())
    if post_data:
        log.debug('post_data %s', post_data)
        if post_data['type'] == 'add':
            if len(post_data['ref_name']) >= 1 and len(post_data['zp_cred_u']) >= 1:
                current_app.config["AdminHTTPScanPathFuncs"].add_share_credential(
                    post_data['ref_name'], post_data['zp_cred_u'], post_data['zp_cred_p']
                )
        elif post_data['type'] == 'edit':
            processing_dict = {}
            for post_data_key in post_data:
                log.debug('post_data_key %s', post_data_key)
                log.debug('post_data[post_data_key] %s', post_data[post_data_key])
                post_data_key_match = re.match(valid_entry_regex, post_data_key)
                if post_data_key_match:
                    post_data_key_match_group_dict = post_data_key_match.groupdict()
                    if post_data_key_match_group_dict['zp_share_credential'] not in processing_dict:
                        processing_dict[post_data_key_match_group_dict['zp_share_credential']] = {}
                    if share_credential_editable_dict[post_data_key_match_group_dict['section']] in ['text', 'password']:
                        processing_dict[post_data_key_match_group_dict['zp_share_credential']][
                            post_data_key_match_group_dict['section']] = post_data[post_data_key]
                elif post_data_key != 'type':
                    log.error('post_data_key %s failed to match valid_entry_regex %s', post_data_key,
                          valid_entry_regex)
            for zp_share_credential_id in processing_dict:
                # log.error(processing_dict[zp_scan_path_id])
                current_app.config["AdminHTTPScanPathFuncs"].update_share_credential(
                    zp_share_credential_id,
                    processing_dict[zp_share_credential_id]['ref_name'],
                    processing_dict[zp_share_credential_id]['zp_cred_u'],
                    processing_dict[zp_share_credential_id]['zp_cred_p']
                )
    share_credential_list = current_app.config["AdminHTTPScanPathFuncs"].get_credential_list()
    share_credential_title_dict = {'ref_name': 'Reference Name',
        'zp_cred_u': 'Username',
                        'zp_cred_p': 'Password'}
    share_credential_keys = [
        'ref_name',
        'zp_cred_u',
        'zp_cred_p']
    return render_template('scan_paths/share_credential.html', share_credential_list=share_credential_list,
                           share_credential_editable_dict=share_credential_editable_dict,
                           share_credential_keys=share_credential_keys,
                           share_credential_title_dict=share_credential_title_dict,
                           share_credential_add_keys=share_credential_keys,
                           share_credential_add_dict = share_credential_editable_dict)


# https://technet.microsoft.com/en-us/library/cc959336.aspx
@scan_paths.route('/scan_path/netbios/getName/<regex("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"):ip_address>', methods=['GET'])
@login_required
def netbois_name_from_ip(ip_address):
    exitCode, output = execute(['nmblookup',
                                '-A',
                                ip_address])
    output = re.sub(r'''[\t]+''', '', output)
    output = re.sub(r'''[\r\n]+''', '\n', output)
    return_dict = {'status':'success',
                   'data':{'output': output.split('\n')}}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')


# https://technet.microsoft.com/en-us/library/cc959336.aspx
@scan_paths.route('/scan_path/netbios/getIp/<regex("[\w!@#$%^()\-\'{}\.~]{1,15}"):netbios_name>', methods=['GET'])
@login_required
def ip_from_netbois_name(netbios_name):
    exitCode, output = execute(['nmblookup',
                                netbios_name])
    output = re.sub(r'''[\t]+''', '', output)
    output = re.sub(r'''[\r\n]+''', '\n', output)
    return_dict = {'status':'success',
                   'data':{'output': output.split('\n')}}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')
