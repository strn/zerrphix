# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import os
import re
import tempfile

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

from zerrphix.exceptions import GetConfigPath

log = logging.getLogger(__name__)

user_home_dir = os.path.expanduser('~')

# TODO: remove def_

def_config_filename = 'zerrphix.ini'
def_config_paths = []
def_config_paths.append(os.path.join(user_home_dir, def_config_filename))
def_config_paths.append(os.path.join(user_home_dir, '.config', def_config_filename))
def_config_paths.append(os.path.join(user_home_dir, '.zerrphix', def_config_filename))


def load_config(args):
    log.debug('args: {0}'.format(args))
    config_file_path = _get_config_paths(args)
    if config_file_path['config_file_path'] is None:
        message = 'Cannot find a config file to use for zerrphix in any of the following paths {0}. Has' \
                  ' zerrrphix install been run ??'.format(
            config_file_path['checked_paths'])
        log.critical(message)
        raise GetConfigPath(message)
    else:
        config = ConfigParser()
        config.read(config_file_path['config_file_path'])
        return config, os.path.dirname(config_file_path['config_file_path'])


def get_global_config_dict(args):
    config, config_dirname = load_config(args)
    config_dict = {}
    #config_dict['keep_downloaded_images'] = True if config.get('global', 'keep_downloaded_images') == '1' else False
    # config_dict['log_to_file'] = config.get('logging', 'log_to_file')
    config_dict['config_dirname'] = config_dirname
    config_dict['flask_secret'] = config.get('flask', 'holder')
    config_dict['log_file_path'] = config.get('logging', 'log_file_path')
    config_dict['log_file_maxbytes'] = int(config.get('logging', 'log_file_maxbytes'))
    config_dict['log_file_backupCount'] = int(config.get('logging', 'log_file_backupCount'))
    config_dict['log_file_level'] = config.get('logging', 'log_file_level')
    config_dict['log_to_file_compression'] = int(config.get('logging', 'log_to_file_compression'))
    if config.get('logging', 'log_to_console') == '1':
        config_dict['log_to_console'] = True
        config_dict['log_to_console_level'] = config.get('logging', 'log_to_console_level')
    else:
        config_dict['log_to_console_level'] = 'info'
        config_dict['log_to_console'] = False
    config_dict['downloaded_images_root_path'] = config.get('global', 'downloaded_images_root_path')
    config_dict['downloaded_images_root_path'] = re.sub(r'::config_root::',
                                                             config_dirname,
                                                             config_dict['downloaded_images_root_path'])
    config_dict['downloaded_images_root_path'] = re.sub(r'''::sep::''',
                                                             os.sep,
                                                             config_dict['downloaded_images_root_path'])
    config_dict['rendered_image_root_path'] = config.get('global', 'rendered_image_root_path')
    config_dict['rendered_image_root_path'] = re.sub(r'::config_root::', config_dirname,
                                                     config_dict['rendered_image_root_path'])
    config_dict['rendered_image_root_path'] = re.sub(r'::sep::', os.sep, config_dict['rendered_image_root_path'])
    config_dict['template_store_path'] = re.sub(r'::config_root::', config_dirname,
                                                config.get('global', 'template_store_path'))
    config_dict['holder'] = config.get('global', 'holder')
    config_dict['dune_http_server_listen_ip'] = config.get('httpserver', 'dune_http_server_listen_ip')
    config_dict['dune_http_server_listen_port'] = int(config.get('httpserver', 'dune_http_server_listen_port'))
    config_dict['admin_http_server_listen_ip'] = config.get('httpserver', 'admin_http_server_listen_ip')
    config_dict['admin_http_server_listen_port'] = int(config.get('httpserver', 'admin_http_server_listen_port'))
    config_dict['admin_http_server_debug'] = True if \
        config.get('httpserver', 'admin_http_server_debug').lower() == 'true' else False
    return config_dict


def get_user_plugins_dir(args):
    config_file_path = _get_config_paths(args)['config_file_path']
    if config_file_path is not None:
        user_plugins_dir = os.path.join(os.path.dirname(config_file_path), 'plugins')
        if os.path.isdir(user_plugins_dir):
            return user_plugins_dir
    return None


def _get_config_paths(args):
    return_dict = {'config_file_path': None, 'checked_paths': []}
    if isinstance(args, list):
        log.debug('args: {0} is list'.format(args))
        if '--config' in args or '-c' in args:
            log.debug('--config or -c in args ({0})'.format(args))
            config_arg_position_list = [i for i, x in enumerate(args) if x == '--config' or x == '-c']
            log.debug('config_arg_position_list: ({0})'.format(config_arg_position_list))
            if isinstance(config_arg_position_list, list):
                log.debug('isinstance(config_arg_position_list, list) is true. config_arg_position_list {0}'.format(
                    config_arg_position_list))
                config_arg_position_list_len = len(config_arg_position_list)
                if config_arg_position_list_len == 1:
                    config_arg_position = config_arg_position_list[0]
                    log.debug('config_arg_position: ({0})'.format(config_arg_position))
                    config_arg_path_position = config_arg_position + 1
                    args_len = len(args)
                    if args_len >= config_arg_path_position:
                        log.debug('len(args) {0} is greater than or equal to config_arg_position {1}'.format(args_len,
                                                                                                 config_arg_position))
                        config_file_path = args[config_arg_path_position]
                        log.debug('config_file_path: {0}'.format(config_file_path))
                        return_dict['checked_paths'].append(config_file_path)
                        if os.path.isfile(config_file_path):
                            return_dict['config_file_path'] = config_file_path
                            return return_dict
                        else:
                            log.warning(
                                'config_file_path: {0} does not exist or is not a file'.format(config_file_path))
                    else:
                        log.debug(
                            'len(args) {0} is NOT greater than or equal to config_arg_position {1}'.format(args_len,
                                                                                                config_arg_position))
                else:
                    log.debug(
                        'config_arg_position_list_len {0} is NOT 1'.format(config_arg_position_list_len))
            else:
                log.warning('isinstance(config_arg_position_list, list) is false. config_arg_position {0}'.format(
                    config_arg_position_list))
    else:
        log.debug('args: {0} is not list'.format(args))
    for path in def_config_paths:
        return_dict['checked_paths'].append(path)
        if os.path.isfile(path):
            return_dict['config_file_path'] = path
            return return_dict
    return return_dict
