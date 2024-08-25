# from PIL import Image
import logging

from flask import Blueprint
from flask import current_app
from flask import render_template
from flask import request
import pprint
from flask_login import login_required
import re

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

settings = Blueprint('settings', __name__)

log = logging.getLogger(__name__)


@settings.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_index():
    film_allowed_extensions = current_app.config["AdminHTTPGenFuncs"].get_allowed_extensions_string(
        1
    )
    film_ignored_extensions = current_app.config["AdminHTTPGenFuncs"].get_allowed_extensions_string(
        1, 1
    )
    tv_allowed_extensions = current_app.config["AdminHTTPGenFuncs"].get_allowed_extensions_string(
        2
    )
    tv_ignored_extensions = current_app.config["AdminHTTPGenFuncs"].get_allowed_extensions_string(
        2, 1
    )

    return render_template('settings/index.html',
                           film_allowed_extensions=film_allowed_extensions,
                           film_ignored_extensions=film_ignored_extensions,
                           tv_allowed_extensions=tv_allowed_extensions,
                           tv_ignored_extensions=tv_ignored_extensions
                           )


@settings.route('/settings/user', methods=['GET', 'POST'])
@login_required
def user():
    user_dict = current_app.config["AdminHTTPGenFuncs"].get_user_dict()
    if request.method == 'POST':
        post_data = request.form
        if post_data['type'] == 'add':
            current_app.config["AdminHTTPGenFuncs"].add_user(
                post_data['username'],
                post_data['password'],
                post_data['template'],
                post_data['lang']
            )
            for zp_process_id in [5,14]:
                current_app.config["AdminHTTPGenFuncs"].set_process_force_run(zp_process_id)
        elif post_data['type'] == 'edit':
            user_update_dict = {}
            for key in post_data:
                match = re.match(r'''^(?P<zp_user_id>\d+)_(?P<section>template|password|lang)$''', key)
                if match:
                    match_group_dict = match.groupdict()
                    if post_data[key]:
                        if post_data[key] != str(user_dict[int(match_group_dict['zp_user_id'])][match_group_dict['section']]):
                            if match_group_dict['zp_user_id'] not in user_update_dict:
                                user_update_dict[match_group_dict['zp_user_id']] = {}
                            user_update_dict[match_group_dict['zp_user_id']][match_group_dict['section']] = post_data[key]
            for user in user_update_dict:
                clear_renders = current_app.config["AdminHTTPGenFuncs"].update_user(
                    user,
                    user_update_dict[user]['password'] if 'password' in user_update_dict[user] else None,
                    user_update_dict[user]['template'] if 'template' in user_update_dict[user] else None,
                    user_update_dict[user]['lang'] if 'lang' in user_update_dict[user] else None
                )
                if clear_renders is True:
                    current_app.config["AdminHTTPGenFuncs"].clear_user_renders(user)
            for zp_process_id in [5, 14]:
                current_app.config["AdminHTTPGenFuncs"].set_process_force_run(zp_process_id)
            log.error('user_update_dict %s', user_update_dict)
    user_dict = current_app.config["AdminHTTPGenFuncs"].get_user_dict()
    template_list = current_app.config["AdminHTTPGenFuncs"].get_template_list()
    user_keys = ['username',
                 'password',
                 'template',
                 'lang']
    user_title_dict = {'username': 'Username',
                       'password': 'Password',
                       'template': 'Template',
                       'lang': 'Language'}
    user_add_dict = {'username': 'text',
                       'password': 'password',
                      'template': 'select',
                      'lang': 'select'}
    user_edit_dict = {'password': 'password',
                      'template': 'select',
                      'lang': 'select'}
    select_dict = {'template': template_list,
                   # todo get a subset of zp_lang
                   'lang': [{'id': 1823, 'ref_name': 'English'},
                            {'id': 1942, 'ref_name': 'Francais'},
                            {'id': 1539, 'ref_name': 'Deutsche'}]
                   }

    return render_template('settings/user.html',
                           user_dict=user_dict,
                           user_keys=user_keys,
                           user_edit_dict=user_edit_dict,
                           user_title_dict=user_title_dict,
                           select_dict=select_dict,
                           user_add_dict=user_add_dict)


@settings.route('/settings/user/dune', methods=['GET', 'POST'])
@login_required
def user_dune_assigment():
    if request.method == 'POST':
        post_data = request.form
        if post_data['type'] == 'edit':
            #log.error(post_data)
            #assigment_dict = {}
            current_app.config["AdminHTTPDuneFuncs"].clear_dune_assigments()
            for key in post_data:
                match = re.match(r'''^(?P<zp_user_id>\d+)_(?P<zp_dune_id>\d+)$''', key)
                if match:
                    match_group = match.groupdict()
                    current_app.config["AdminHTTPDuneFuncs"].add_dune_assigments(match_group['zp_user_id'],
                                                                                 match_group['zp_dune_id'])
            current_app.config["AdminHTTPGenFuncs"].set_process_force_run(6)
            current_app.config["AdminHTTPGenFuncs"].set_process_force_run(16)
                #log.error(key)


    dune_list = current_app.config["AdminHTTPDuneFuncs"].get_dune_list()
    dune_assigment_dict = current_app.config["AdminHTTPDuneFuncs"].get_dune_assigment_dict()
    user_dict = current_app.config["AdminHTTPGenFuncs"].get_user_dict()
    dune_keys = []
    dune_title_dict = {}
    dune_edit_dict = {}
    for dune in dune_list:
        dune_keys.append(dune['id'])
        dune_title_dict[dune['id']] = dune['name']
        dune_edit_dict[dune['id']] = 'check'

    return render_template('settings/user_dune.html',
                           dune_keys=dune_keys,
                           dune_title_dict=dune_title_dict,
                           user_dict=user_dict,
                           dune_edit_dict=dune_edit_dict,
                           dune_assigment_dict=dune_assigment_dict,
                           dune_list=dune_list)


@settings.route('/settings/fileExtensions', methods=['GET', 'POST'])
@login_required
def file_extensions():
    if request.method == 'POST':
        post_data = request.form
        if post_data['type'] == 'add':
            current_app.config["AdminHTTPGenFuncs"].add_file_extensions(post_data['extension'])
        elif post_data['type'] == 'edit':
            valid_entry_pattern = r'''(?P<zp_file_extension_id>\d+)_(?P<section>extension)'''
            for post_data_key in post_data:
                match = re.match(valid_entry_pattern, post_data_key)
                if match:
                    zp_file_extension_id =  match.groupdict()['zp_file_extension_id']
                    current_app.config["AdminHTTPGenFuncs"].set_file_extensions(zp_file_extension_id,
                                                                                post_data[post_data_key])
    file_extension_list = current_app.config["AdminHTTPGenFuncs"].get_file_extensions()
    file_extension_keys = ['extension']
    file_extension_title_dict = {'extension': 'Extension'}
    file_extension_edit_dict = {'extension': 'text'}

    return render_template('settings/file_extension.html',
                           file_extension_list=file_extension_list,
                           file_extension_keys=file_extension_keys,
                           file_extension_title_dict=file_extension_title_dict,
                           file_extension_edit_dict=file_extension_edit_dict,
                           )

@settings.route('/settings/fileExtensions/<regex("1|2"):zp_library_id>', methods=['GET', 'POST'])
@login_required
def file_extensions_library(zp_library_id):
    if request.method == 'POST':
        post_data = request.form
        log.debug('post_data %s', pprint.pformat(post_data))
        valid_entry_pattern = r'''(?P<zp_file_extension_id>\d+)_(?P<section>extension|ignore)'''
        file_extension_set_dict = {}
        for post_data_key in post_data:
            match = re.match(valid_entry_pattern, post_data_key)
            if match:
                group_dict = match.groupdict()
                if group_dict['section'] == 'extension':
                    file_extension_set_dict[group_dict['zp_file_extension_id']] = 0

        for post_data_key in post_data:
            match = re.match(valid_entry_pattern, post_data_key)
            if match:
                group_dict = match.groupdict()
                if group_dict['zp_file_extension_id'] in file_extension_set_dict:
                    if group_dict['section'] == 'ignore':
                        file_extension_set_dict[group_dict['zp_file_extension_id']] = 1

        log.debug('file_extension_set_dict %s', pprint.pformat(file_extension_set_dict))
        current_app.config["AdminHTTPGenFuncs"].set_library_file_extensions(
            zp_library_id,
            file_extension_set_dict)
    library_dict = {'1':'Film', '2':'TV'}
    file_extension_list = current_app.config["AdminHTTPGenFuncs"].get_file_extensions()
    library_extension_dict = current_app.config["AdminHTTPGenFuncs"].get_library_file_extensions(zp_library_id)
    file_extension_keys = ['extension', 'ignore']
    file_extension_title_dict = {'extension': 'Enabled',
                                 'ignore': 'Ignore (must be enabled to ignore)'}
    file_extension_edit_dict = {'extension': 'check',
                                'ignore': 'check'}

    return render_template('settings/file_extension_library.html',
                           file_extension_list=file_extension_list,
                           file_extension_keys=file_extension_keys,
                           file_extension_title_dict=file_extension_title_dict,
                           file_extension_edit_dict=file_extension_edit_dict,
                           library_extension_dict=library_extension_dict,
                           library=zp_library_id,
                           library_dict=library_dict
                           )
