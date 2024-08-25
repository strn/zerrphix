# from PIL import Image
import logging
import re

from flask import Blueprint
from flask import current_app
from flask import render_template
from flask import request
from flask import escape
from flask import Response
from flask import send_file
from flask_login import login_required
from flask import make_response
from io import BytesIO

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

dunes = Blueprint('dunes', __name__)

log = logging.getLogger(__name__)


@dunes.route('/dunes', methods=['GET', 'POST'])
@login_required
def dunes_index():
    if request.method == 'POST':
        post_data = request.form
        current_app.config["AdminHTTPDuneFuncs"].add_dune(post_data['dune_name'])
    dune_list = current_app.config["AdminHTTPDuneFuncs"].get_dune_list()

    return render_template('dunes/index.html',
                           dune_list=dune_list)


@dunes.route('/dunes/scanPathMap/<regex("[1-9]([0-9]+)?"):zp_dune_id>/', methods=['GET', 'POST'])
@login_required
def map_scan_paths(zp_dune_id):
    if request.method == 'POST':
        post_data = request.form
        log.debug('post_data %s', post_data)
        valid_entry_regex = r'''(?P<zp_scan_path_id>\d+)_play_path'''
        for zp_scan_path in post_data:
            match = re.match(valid_entry_regex, zp_scan_path)
            if match:
                zp_scan_path_id = match.groupdict()['zp_scan_path_id']
                log.debug('zp_scan_path_id %s, play_path %s', zp_scan_path_id, post_data[zp_scan_path])
                dune_play_path = post_data[zp_scan_path]
                if len(dune_play_path) > 0:
                    current_app.config["AdminHTTPDuneFuncs"].set_dune_play_path(zp_dune_id, zp_scan_path_id,
                                                                                dune_play_path)
    dune_name = current_app.config["AdminHTTPDuneFuncs"].get_dune_name(zp_dune_id)
    scan_path_map_list = current_app.config["AdminHTTPDuneFuncs"].get_scan_path_map_list(zp_dune_id)
    scan_path_map_keys = ['library', 'scan_path', 'play_path']
    scan_path_map_title_dict = {'library': 'Library',
                                'scan_path': 'Scan Path',
                                'play_path': 'Play Path'
                                }
    scan_path_map_edit_dict = {'play_path': 'text'}
    log.debug('scan_path_map_list %s', scan_path_map_list)
    return render_template('dunes/scan_path_mapping.html',
                           dune_name=dune_name,
                           scan_path_map_list=scan_path_map_list,
                           scan_path_map_keys=scan_path_map_keys,
                           scan_path_map_title_dict=scan_path_map_title_dict,
                           scan_path_map_edit_dict=scan_path_map_edit_dict
                           )


@dunes.route('/dunes/manage/<regex("[1-9]([0-9]+)?"):zp_dune_id>/', methods=['GET', 'POST'])
@login_required
def manage(zp_dune_id):
    if request.method == 'POST':
        post_data = request.form
        ui_store_type_id = int(post_data['ui_store_type_id'])
        ui_share_xref_id = int(post_data['ui_share_xref_id'])
        ui_root = post_data['ui_root']
        ui_dune_ref = post_data['ui_dune_ref']
        current_app.config["AdminHTTPDuneFuncs"].set_ui_store(zp_dune_id,
                                                              ui_store_type_id,
                                                              ui_share_xref_id,
                                                              ui_root,
                                                              ui_dune_ref,
                                                              )

    dune_name = current_app.config["AdminHTTPDuneFuncs"].get_dune_name(zp_dune_id)
    share_dict = current_app.config["AdminHTTPScanPathFuncs"].get_share_dict()
    share_server_dict = current_app.config["AdminHTTPScanPathFuncs"].get_share_server_dict()
    share_credential_dict = current_app.config["AdminHTTPScanPathFuncs"].get_share_credential_dict()
    ui_store_dict = current_app.config["AdminHTTPDuneFuncs"].get_dune_ui_store_dict(zp_dune_id)
    ui_store_keys = ['ui_store_type_id', 'ui_share_xref_id', 'ui_root', 'ui_dune_ref']
    ui_store_title_dict = {'ui_store_type_id': 'UI Store Type',
                           'ui_share_xref_id': 'Share',
                           'ui_root': 'Share Root Path',
                           'ui_dune_ref': 'Dune Local Root Path'
                           }
    ui_store_select_dict = {'ui_share_xref_id': current_app.config["AdminHTTPDuneFuncs"].get_share_xref_dict()}
    ui_store_edit_dict = {'ui_store_type_id': 'text',
                          'ui_share_xref_id': 'select',
                          'ui_root': 'text',
                          'ui_dune_ref': 'text'}

    return render_template('dunes/manage.html',
                           dune_name=dune_name,
                           ui_store_keys=ui_store_keys,
                           ui_store_title_dict=ui_store_title_dict,
                           ui_store_edit_dict=ui_store_edit_dict,
                           ui_store_select_dict=ui_store_select_dict,
                           ui_store_dict=ui_store_dict,
                           share_dict=share_dict,
                           share_server_dict=share_server_dict,
                           share_credential_dict=share_credential_dict
                           )


@dunes.route('/dunes/shareXref/', methods=['GET', 'POST'])
@login_required
def shareXref():
    if request.method == 'POST':
        post_data = request.form
        if post_data['type'] == 'add':
            current_app.config["AdminHTTPDuneFuncs"].add_share_xref(
                post_data['ref_name'],
                post_data['zp_share_id'],
                post_data['zp_share_server_id'],
                post_data['zp_share_credential_id']
            )
        elif post_data['type'] == 'edit':
            processing_dict = {}
            valid_entry_regex = r'''^(?P<zp_dune_share_xref_id>\d+)_(?P<section>ref_name|zp_share_id|zp_share_server_id|zp_share_credential_id)$'''
            log.error(post_data)
            for post_data_key in post_data:
                match = re.match(valid_entry_regex, post_data_key)
                if match:
                    groupdict = match.groupdict()
                    zp_dune_share_xref_id = groupdict['zp_dune_share_xref_id']
                    section = groupdict['section']
                    if zp_dune_share_xref_id not in processing_dict:
                        processing_dict[zp_dune_share_xref_id] = {}
                    processing_dict[zp_dune_share_xref_id][section] = post_data[post_data_key]
            for zp_dune_share_xref_id in processing_dict:
                log.error(zp_dune_share_xref_id)
                log.error(processing_dict[zp_dune_share_xref_id])
                log.error(processing_dict)
                current_app.config["AdminHTTPDuneFuncs"].set_share_xref(
                    zp_dune_share_xref_id,
                    processing_dict[zp_dune_share_xref_id]['ref_name'],
                    processing_dict[zp_dune_share_xref_id]['zp_share_id'],
                    processing_dict[zp_dune_share_xref_id]['zp_share_server_id'],
                    processing_dict[zp_dune_share_xref_id]['zp_share_credential_id']
                )

    share_dict = current_app.config["AdminHTTPScanPathFuncs"].get_share_dict()
    share_server_dict = current_app.config["AdminHTTPScanPathFuncs"].get_share_server_dict()
    share_credential_dict = current_app.config["AdminHTTPScanPathFuncs"].get_share_credential_dict()
    share_xref_list = current_app.config["AdminHTTPDuneFuncs"].get_share_xref_list()
    share_xref_keys = ['ref_name', 'zp_share_id', 'zp_share_server_id', 'zp_share_credential_id']
    share_xref_title_dict = {'ref_name': 'Reference Name',
                             'zp_share_id': 'Share',
                             'zp_share_server_id': 'Server',
                             'zp_share_credential_id': 'Credential'
                             }
    share_xref_select_dict = {'zp_share_id': share_dict,
                              'zp_share_server_id': share_server_dict,
                              'zp_share_credential_id': share_credential_dict
                              }
    share_xref_edit_dict = {'ref_name': 'text',
                            'zp_share_id': 'select',
                            'zp_share_server_id': 'select',
                            'zp_share_credential_id': 'select'}

    return render_template('dunes/share.html',
                           share_xref_list=share_xref_list,
                           share_xref_keys=share_xref_keys,
                           share_xref_select_dict=share_xref_select_dict,
                           share_xref_title_dict=share_xref_title_dict,
                           share_xref_edit_dict=share_xref_edit_dict,
                           )


@dunes.route('/dunes/playPath/<regex("[1-9]([0-9]+)?"):zp_dune_id>', methods=['GET', 'POST'])
@login_required
def play_path(zp_dune_id):
    check_dune_exists = current_app.config["AdminHTTPDuneFuncs"].check_dune_exists(zp_dune_id)
    if check_dune_exists is True:
        if request.method == 'POST':
            post_data = request.form
            if post_data['type'] == 'edit':
                for post_data_key in post_data:
                    match = re.match(r'''^(?P<zp_scan_path_id>\d+)_(?P<section>play_path)$''', post_data_key)
                    if match:
                        match_group_dict = match.groupdict()
                        if match_group_dict['section'] == 'play_path' and post_data[post_data_key]:
                            current_app.config["AdminHTTPDuneFuncs"].set_play_path(
                                zp_dune_id,
                                match_group_dict['zp_scan_path_id'],
                                post_data[post_data_key])
        play_path_dict = current_app.config["AdminHTTPDuneFuncs"].get_play_path_dict(zp_dune_id)
        play_path_keys = ['scan_path', 'play_path']
        play_path_edit_dict = {'play_path': 'text'}
        play_path_title_dict = {'scan_path': 'Scan Path',
                                'play_path': 'Dune Play Path'}

        return render_template('dunes/play_path.html',
                               play_path_dict=play_path_dict,
                               play_path_keys=play_path_keys,
                               play_path_edit_dict=play_path_edit_dict,
                               play_path_title_dict=play_path_title_dict
                               )
    else:
        return Response(escape('Dune %s does not exist' % zp_dune_id),
                 mimetype='text/html')


@dunes.route('/dunes/duneFolderTxt/<regex("[1-9]([0-9]+)?"):zp_dune_id>', methods=['GET'])
@login_required
def dune_folder_txt(zp_dune_id):
    check_dune_exists = current_app.config["AdminHTTPDuneFuncs"].check_dune_exists(zp_dune_id)
    if check_dune_exists is True:
        host_split = request.host.split(':')
        host = host_split[0]
        dport = current_app.config["global_config_dict"]['dune_http_server_listen_port']
        aport = current_app.config["global_config_dict"]['admin_http_server_listen_port']
        dune_folder_txt = """background_order=before_all\r
content_box_y=100\r
content_box_x=20\r
paint_path_box=no\r
paint_widget=no\r
paint_help_line=no\r
content_box_padding_bottom=0\r
num_rows=2\r
num_cols=1\r
paint_scrollbar=no\r
paint_captions=yes\r
paint_content_box_background=no\r
media_action=browse\r
content_box_padding_top=0\r
content_box_padding_right=0\r
use_icon_view=yes\r
background_width=1920\r
content_box_height=800\r
paint_icon_selection_box=yes\r
num_cols=1\r
background_height=1080\r
content_box_width=1880\r
content_box_padding_left=0\r
\r
item.0.icon_valign=center\r
item.0.media_action=browse\r
item.0.caption=Zerrphix\r
item.0.icon_scale_factor=0.6\r
item.0.icon_sel_scale_factor=0.8\r
item.0.icon_path=http://{host}:{aport}/logo.png\r
item.0.icon_sel_path=http://{host}:{aport}/logo.png\r
item.0.media_url=dune_http://{host}:{dport}/m/1/{zp_dune_id}/1/root\r
\r
""".format(host=host, dport=dport, aport=aport, zp_dune_id=zp_dune_id)
        buffer = BytesIO()
        buffer.write(dune_folder_txt)
        buffer.seek(0)
        log.debug("".join("{:02x}".format(ord(c)) for c in '\n\r'))
        log.debug("".join("{:02x}".format(ord(c)) for c in buffer.read()))
        buffer.seek(0)
        respoonse = make_response(send_file(buffer, as_attachment=True,
                         attachment_filename='dune_folder.txt',
                         mimetype='text/plain'))
        respoonse.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return respoonse
        #return Response(dune_folder_txt, mimetype='text/plain')
    else:
        Response(escape('Dune %s does not exist' % zp_dune_id),
                 mimetype='text/html')