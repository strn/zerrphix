# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import os
import re
import sys
import math
from types import MethodType

from PIL import Image, ImageDraw, ImageFont

import zerrphix.template
from zerrphix.plugin import load_plugins
from zerrphix.template import tempalte_icon_sub_type_list_convert
#from zerrphix.util.db import DBCommon
from zerrphix.util.filesystem import make_dir, get_file_extension, check_for_exisiting_default_image
from zerrphix.util.image import text_box, text_line, download_and_resize_image
#from zerrphix.util.image_store import create_dune_render_store_dict
from zerrphix.util.plugin import create_eapi_plugins_list
from zerrphix.util.text import xml_to_dict
from zerrphix.base import Base
from zerrphix.util.filesystem import smbfs
from zerrphix.db.tables import TABLES
from zerrphix.util.image import resize_and_crop
from six import string_types
from sqlalchemy import orm
import time
import socket
import pprint
from smb import base as smb_base
from zerrphix.util.filesystem import SMBConnectionAssertionError
from zerrphix.constants import dune_supported_images
from zerrphix.util.numbers import get_rating_image_number

log = logging.getLogger(__name__)

# text stroke
# https://mail.python.org/pipermail/image-sig/2009-May/005681.html

class ArtworkBase(Base):
    def __init__(self, **kwargs):

        super(ArtworkBase, self).__init__(**kwargs)
        # todo make this better
        #self.dbcommon = DBCommon(**kwargs)
        #self.create_dune_render_store_dict = MethodType(create_dune_render_store_dict, self)
        log.debug(self.library_config_dict)
        #if self.library_config_dict['name'] == 'film_collection':
        #    eapi_library_name = 'film'
        #else:
        #    eapi_library_name = self.library_config_dict['name']
        #log.error('eapi_library_name %s' % eapi_library_name)
        self, self.eapi_plugins_access_list, loaded_plugins = create_eapi_plugins_list(
            self.library_config_dict['name'], sys.modules,
            load_plugins(self.args),
            self)
        if not self.eapi_plugins_access_list and self.library_config_dict['name'] != 'user':
            log.error('There not any entries in eapi_film_plugins_access_list therefore trying to do artwork is pointless')
            raise Exception('There not any entries in eapi_film_plugins_access_list therefore trying to do artwork is pointless')

        self.collection = False
        self.all_image_types_dict = self.get_image_type_dict_by_name()
        self.dune_name_by_id_dict = self.get_dune_name_by_id_dict()

    def process_dunes(self):
        rendering_complete = False
        ZP_DUNE_ID = 0
        kwargs = {}
        processed_http_dune = False
        while rendering_complete == False:
            dunes = self.get_dunes(ZP_DUNE_ID)
            if processed_http_dune == False:
                # we only need to process dune that use http images once per user
                dunes[1] = {}
                dunes[1]['ZP_DUNE_UI_IMAGE_STORE_TYPE_ID'] = 1
                dunes[1]['ZP_DUNE_UI_IMAGE_STORE_ROOT'] = ''
                dunes[1]['ZP_DUNE_SHARE_XREF_ID'] = None
            log.debug('dunes %s', dunes)
            if dunes:
                # log.debug('dunes %s', dunes)
                # raise SystemExit
                for _ZP_DUNE_ID in sorted(dunes):
                    # TODO move then smcon init here rather in artwork
                    log.debug('_ZP_DUNE_ID %s', _ZP_DUNE_ID)
                    ZP_DUNE_ID = _ZP_DUNE_ID
                    kwargs['ZP_DUNE_UI_IMAGE_STORE_TYPE_ID'] = dunes[ZP_DUNE_ID]['ZP_DUNE_UI_IMAGE_STORE_TYPE_ID']
                    kwargs['ZP_DUNE_UI_IMAGE_STORE_ROOT'] = dunes[ZP_DUNE_ID]['ZP_DUNE_UI_IMAGE_STORE_ROOT']
                    kwargs['ZP_DUNE_SHARE_XREF_ID'] = dunes[ZP_DUNE_ID]['ZP_DUNE_SHARE_XREF_ID']
                    kwargs['ZP_DUNE_ID'] = ZP_DUNE_ID
                    try:
                        kwargs['dune_render_store_dict'] = self.create_dune_render_store_dict(
                            kwargs['ZP_DUNE_ID'],
                            kwargs['ZP_DUNE_UI_IMAGE_STORE_TYPE_ID'],
                            kwargs['ZP_DUNE_UI_IMAGE_STORE_ROOT'],
                            kwargs['ZP_DUNE_SHARE_XREF_ID'])
                    except (OSError, IOError, AttributeError) as e:
                        self.add_excpetion_raised_to_db(1, e)
                    except socket.error as e:
                        self.add_excpetion_raised_to_db(1, e)
                    except smb_base.NotConnectedError as e:
                        self.add_excpetion_raised_to_db(1, e)
                    except smb_base.NotReadyError as e:
                        self.add_excpetion_raised_to_db(1, e)
                    except smb_base.SMBTimeout as e:
                        self.add_excpetion_raised_to_db(1, e)
                    except SMBConnectionAssertionError as e:
                        self.add_excpetion_raised_to_db(1, e)
                    else:
                        try:
                            log.debug('_ZP_DUNE_ID %s got to process_users', _ZP_DUNE_ID)
                            self.process_users(**kwargs)
                        except socket.error as e:
                            self.add_excpetion_raised_to_db(1, e)
                        except smb_base.NotConnectedError as e:
                            self.add_excpetion_raised_to_db(1, e)
                        except smb_base.NotReadyError as e:
                            self.add_excpetion_raised_to_db(1, e)
                        except smb_base.SMBTimeout as e:
                            self.add_excpetion_raised_to_db(1, e)
                        except SMBConnectionAssertionError as e:
                            self.add_excpetion_raised_to_db(1, e)
                    if ZP_DUNE_ID == 1:
                        processed_http_dune = True
            else:
                rendering_complete = True

    def create_image_type_dict(self, *args, **kwargs):
        pass

    def process_users(self, **kwargs):
        kwargs['ZP_USER_ID'] = 0
        users_procesed = False
        while users_procesed == False:
            users = self.get_users(kwargs['ZP_USER_ID'], kwargs['ZP_DUNE_ID'])
            log.debug('users %s', users)
            # log.warning('''kwargs['ZP_USER_ID'] %s''', kwargs['ZP_USER_ID'])
            if users:
                for _ZP_USER_ID in users:
                    if kwargs['ZP_DUNE_UI_IMAGE_STORE_TYPE_ID'] == 2:
                        self.smbcon = smbfs(kwargs['dune_render_store_dict']['connection_dict'])
                    log.debug('_ZP_USER_ID %s', _ZP_USER_ID)
                    kwargs['ZP_USER_ID'] = _ZP_USER_ID
                    # We need the the +1 to not skip the last ZP_TV_ID
                    # We are using desc to process the last tv added first
                    kwargs['zp_template_id'], kwargs['template_name'] = \
                        self.get_user_template_info(kwargs['ZP_USER_ID'])
                    image_tv_user_temaplte_save_folder_exists = self.crate_template_folders(
                        kwargs['template_name'],
                        kwargs['dune_render_store_dict'])
                    if image_tv_user_temaplte_save_folder_exists is True:
                        template_xml_path = self.get_template_path(kwargs['zp_template_id'])
                        templates_dict = self.get_templates_dict(kwargs['zp_template_id'], template_xml_path)
                        evaluated_templates = self.get_evaluate_temapltes_dict(templates_dict)
                        kwargs['template_folder'] = os.path.abspath(os.path.dirname(template_xml_path))
                        # todo get this from db
                        user_library_langs = self.get_user_library_langs(self.library_config_dict['id'],
                                                                        kwargs['ZP_USER_ID'])
                        user_library_eapi_order = self.user_library_eapi_order(self.library_config_dict['id'],
                                                                               kwargs['ZP_USER_ID'])
                        kwargs['ZP_EAPI_ID_REQ'] = user_library_eapi_order[0]
                        kwargs['ZP_LANG_ID_REQ'] = user_library_langs[0]
                        #kwargs['image_extension'] = 'png'
                        #templates_dict = self.get_templates_dict(kwargs['ZP_USER_ID'])
                        #image_type_dict = self.create_image_type_dict(**kwargs)
                        #pprint.pprint(evaluated_templates)
                        log.debug('evaluated_templates %s', pprint.pformat(evaluated_templates))
                        #time.sleep(84600)
                        for image_type in evaluated_templates['library'][self.library_config_dict['name']]:
                            if image_type in self.all_image_types_dict:
                                log.debug('library: %s, image_type: %s, zp_user_id: %s, zp_dune_id: %s',
                                          self.library_config_dict['name'],
                                          image_type,
                                          kwargs['ZP_USER_ID'],
                                          kwargs['ZP_DUNE_ID']
                                          )
                                kwargs['template_version'] = '1.0'
                                try:
                                    kwargs['zp_image_type_id'] = self.all_image_types_dict[image_type]
                                except KeyError as e:
                                    log_message = '''image_type %s not in self.all_image_types_dict %s''' % (
                                        image_type,
                                        str(self.all_image_types_dict)
                                    )
                                    log.error(log_message)
                                    self.add_error_raised_to_db(11, log_message)
                                else:
                                    kwargs['image_type'] = image_type
                                    kwargs['template_dict'] = {'template':
                                            evaluated_templates['library'][self.library_config_dict['name']][image_type]}
                                    kwargs['image_extension'] = 'png'
                                    if kwargs['ZP_DUNE_ID'] == 1:
                                        if '@http_extension' in kwargs['template_dict']['template']:
                                            #kwargs['image_extension'] = 'png'
                                            if kwargs['template_dict']['template']['@http_extension'].lower() in \
                                                dune_supported_images:
                                                kwargs['image_extension'] = \
                                                    kwargs['template_dict']['template']['@http_extension'].lower()
                                    elif kwargs['ZP_DUNE_ID'] > 1:
                                        if '@dune_local_extension' in kwargs['template_dict']['template']:
                                            #kwargs['image_extension'] = 'png'
                                            if kwargs['template_dict']['template']['@dune_local_extension'].lower() in \
                                                dune_supported_images:
                                                kwargs['image_extension'] = \
                                                    kwargs['template_dict']['template']['@dune_local_extension'].lower()
                                    if isinstance(kwargs['template_dict']['template']['item'], dict):
                                        kwargs['template_dict']['template']['item'] = \
                                            [kwargs['template_dict']['template']['item']]
                                    kwargs['icon_sub_type_require_list'], kwargs['template_dict'] = \
                                        tempalte_icon_sub_type_list_convert(kwargs['template_dict'])

                                    #kwargs['template_folder'] =
                                    #kwargs['image_type'] = image_type
                                    #kwargs['template_name'], kwargs['template_version'], kwargs['template_dict'], \
                                    #kwargs['icon_sub_type_require_list'],  kwargs['template_folder'] \
                                    #    = self.template_prep(kwargs['zp_template_id'], image_type)
                                    #pprint.pprint(kwargs)
                                    log.debug('kwargs %s', pprint.pformat(kwargs))
                                    #time.sleep(84600)
                                    self.porcess_entity(**kwargs)
                            else:
                                log.error('image_type %s not in self.all_image_types_dict %s',
                                          image_type,
                                          self.all_image_types_dict)
                    else:
                        log.critical('''image_tv_user_temaplte_save_folder does not exist''')

                    if hasattr(self.smbcon, 'close'):
                        self.smbcon.close()
                    self.smbcon = None
            else:
                users_procesed = True

    #def get_user_template(self, ZP_USER_ID):

        #return 'default'

    def crate_template_folders(self, template_name, dune_render_store_dict):
        # print(locals())
        image_tv_user_temaplte_save_folder_exists = False
        if dune_render_store_dict['render_root_library_dir']:
            image_user_temaplte_save_folder = os.path.join(
                dune_render_store_dict['render_root_library_dir'], template_name)
            if dune_render_store_dict['type'] == 'local':
                if make_dir(image_user_temaplte_save_folder):
                    image_tv_user_temaplte_save_folder_exists = True
            elif dune_render_store_dict['type'] == 'smb':
                # smbcon = smbfs(dune_render_store_dict['connection_dict'])
                if self.smbcon.mkdir(image_user_temaplte_save_folder):
                    image_tv_user_temaplte_save_folder_exists = True
                    # smbcon.close()
                else:
                    log.error('failed to make folder image_tv_user_temaplte_save_folder')
            else:
                log.error('''dune_render_store_dict['type']: {0} not valid'''.format(
                    dune_render_store_dict['type']))
            if 'render_root_library_collection_dir' in dune_render_store_dict:
                image_tv_user_temaplte_save_folder_exists = False
                image_user_collection_temaplte_save_folder = os.path.join(
                    dune_render_store_dict['render_root_library_collection_dir'], template_name)
                if dune_render_store_dict['type'] == 'local':
                    if make_dir(image_user_collection_temaplte_save_folder):
                        image_tv_user_temaplte_save_folder_exists = True
                elif dune_render_store_dict['type'] == 'smb':
                    # smbcon = smbfs(dune_render_store_dict['connection_dict'])
                    if self.smbcon.mkdir(image_user_collection_temaplte_save_folder):
                        image_tv_user_temaplte_save_folder_exists = True
                        # smbcon.close()
                    else:
                        log.error('failed to make folder image_tv_user_temaplte_save_folder')
                else:
                    log.error('''dune_render_store_dict['type']: {0} not valid'''.format(
                        dune_render_store_dict['type']))

        else:
            log.error('''dune_render_store_dict['render_root_library_dir'] %s is empty''',
                        dune_render_store_dict['render_root_library_dir'])
        return image_tv_user_temaplte_save_folder_exists

    def template_prep(self, user_template, image_type):
        template_name = None
        template_version = None
        icon_sub_type_require_list = None
        if self.collection is True:
            space = '%s_collection_%s' % (self.library_config_dict['name'], image_type)
            #template_xml_path = os.path.join(zerrphix.template.__path__[0],
            #                                 self.library_config_dict['name'],
            #                                 user_template,
            #                                 '%s_%s.xml' % ('collection', image_type))
        else:
            space = '%s_%s' % (self.library_config_dict['name'], image_type)
            #template_xml_path = os.path.join(zerrphix.template.__path__[0],
            #                                 self.library_config_dict['name'],
            #                                 user_template,
            #                                 '{0}.xml'.format(image_type))
        template_xml_path = self.get_template_path(user_template)
        log.debug('space %s', space)
        template_dict = None
        template_root_dir = None
        if os.path.isfile(template_xml_path):
            templates_dict = xml_to_dict(template_xml_path)
            template_dict = {'template' : self.get_space_template(templates_dict, space)}
            template_root_dir = os.path.dirname(template_xml_path)
            if isinstance(template_dict, dict):
                if (template_dict['template'].has_key('@width') and
                        template_dict['template'].has_key('@height') and
                        template_dict['template'].has_key('@library') and
                        template_dict['template'].has_key('@type') and
                        template_dict['template'].has_key('@name') and
                        template_dict['template'].has_key('@version') and
                        template_dict['template'].has_key('@icon_sub_type_list')):

                    template_name = template_dict['template']['@name']
                    template_version = template_dict['template']['@version']
                    if isinstance(template_dict['template']['item'], dict):
                        template_dict['template']['item'] = [template_dict['template']['item']]
                    icon_sub_type_require_list, template_dict = tempalte_icon_sub_type_list_convert(
                        template_dict)
                else:
                    log.error('''template_dict['template'].keys() %s have one or more missing from: @width,
                     @height, @library, @type, @name, @version, @icon_sub_type_list''',
                              template_dict['template'].keys())
            else:
                log.error('template_dict is not dict but %s', type(templates_dict))
        else:
            error_message = 'Template path %s is not a file or does not exist' % template_xml_path
            log.critical(error_message)
            self.add_error_raised_to_db(7, error_message)
        return template_name, template_version, template_dict, icon_sub_type_require_list, template_root_dir

    def process_template(self, template_dict, template_folder, **kwargs):
        # print(locals())
        """Use the template to create the image type

            Args:
                | template_dict (dict): template xml converted to a dict
                | specials (object)

        """
        aplha = False
        if '@alpha' in template_dict['template']:
            if template_dict['template']['@alpha'].lower().strip() == 'true':
                aplha = True
        if aplha is True:
            img = Image.new('RGBA', (int(template_dict['template']['@width']),
                                 int(template_dict['template']['@height'])), color=(0, 0, 0, 0))
        else:
            img = Image.new('RGB', (int(template_dict['template']['@width']),
                                 int(template_dict['template']['@height'])), color=(0, 0, 0))
        specials_dict = {}
        for item in template_dict['template']['item']:
            for _type in item:
                int_var_dict = {}
                for int_var in {'width', 'height', 'font_size', 'font_min_size',
                                'font_max_size', 'x', 'y', 'line_spacing',
                                'use_sentences'}:
                    item_key = '@%s' % int_var
                    int_var_dict[int_var] = None
                    if item_key in item[_type]:
                        if item[_type][item_key].isdigit():
                            int_var_dict[int_var] = int(item[_type][item_key])
                log.debug('int_var_dict %s', pprint.pformat(int_var_dict))
                if (isinstance(int_var_dict['x'], int) and isinstance(int_var_dict['y'], int) or
                    ('@alpha_composite' in item[_type] and item[_type]['@alpha_composite'].lower().strip() == 'true')):
                    # TODO: Manage multiple titles how to choose which to display on ui (there are more than one title for
                    # each tv in ZP_TV_TITLE) prob add lang and title_type (origional .....) and how to deal with
                    # multiple languages and what happens if not specific title is aquired. Use all langs currently
                    # used for all users and which they prefer title or origional title
                    if ((kwargs['ZP_IMAGE_SUB_TYPE'] > 0 and '@icon_sub_type_list' in item[_type].keys()
                         and kwargs['ZP_IMAGE_SUB_TYPE'] in item[_type]['@icon_sub_type_list'])
                        or '@icon_sub_type_list' not in item[_type].keys()):
                        # print(kwargs['ZP_IMAGE_SUB_TYPE'], item[_type])
                        if _type == 'text':
                            draw_type = 'text_box'
                            if '@draw_type' in item[_type]:
                                if item[_type]['@draw_type'].lower() == 'text_line':
                                    draw_type = 'text_line'
                                    log.debug('text_line')
                            if item[_type].has_key('@special'):
                                if hasattr(self.specials, item[_type]['@special']) or item[_type]['@special'] in ['season',
                                                                                                                  'episode']:
                                    if item[_type].has_key('@pre_append'):
                                        text = item[_type]['@pre_append']
                                    else:
                                        text = ''
                                    if item[_type]['@special'] in ['title','overview']:
                                        special_text, TITLE_ID = getattr(self.specials, item[_type]['@special'])(**kwargs)
                                        specials_dict[
                                            self.specials.special_type_dict_by_special[item[_type]['@special']]['ID']] = {}
                                        specials_dict[
                                            self.specials.special_type_dict_by_special[item[_type]['@special']]['ID']][
                                            item[_type]['@special']] = TITLE_ID
                                    elif item[_type]['@special'] == 'season':
                                        special_text = str(kwargs['SEASON'])
                                    elif item[_type]['@special'] == 'episode':
                                        if kwargs['FIRST_EPISODE'] == kwargs['LAST_EPISODE']:
                                            special_text = str(kwargs['FIRST_EPISODE'])
                                        else:
                                            special_text = '%s-%s' % (
                                                str(kwargs['FIRST_EPISODE']), str(kwargs['LAST_EPISODE']))
                                    elif item[_type]['@special'] in {'audio_channels', 'video_resolution',
                                                                     'aspect_ratio', 'format', 'audio_language',
                                                                     'subtitle_language', 'video_codec',
                                                                     'audio_codec', 'video_frame_rate'}:
                                        special_text = str(getattr(self.specials, item[_type]['@special'])(**kwargs)).upper()
                                    else:
                                        specials_dict[
                                            self.specials.special_type_dict_by_special[item[_type]['@special']]['ID']] = {}
                                        if self.specials.special_type_dict_by_special[item[_type]['@special']][
                                            'USES_LANG'] == 1:
                                            special_text, ZP_EAPI_ID_ACT, ZP_LANG_ID_ACT = getattr(self.specials,
                                                                                                   item[_type]['@special'])(
                                                **kwargs)
                                            specials_dict[
                                                self.specials.special_type_dict_by_special[item[_type]['@special']]['ID']][
                                                'ZP_LANG_ID_ACT'] = ZP_LANG_ID_ACT
                                            specials_dict[
                                                self.specials.special_type_dict_by_special[item[_type]['@special']]['ID']][
                                                'ZP_LANG_ID_REQ'] = kwargs['ZP_LANG_ID_REQ']
                                        else:
                                            special_text, ZP_EAPI_ID_ACT = getattr(self.specials, item[_type]['@special'])(
                                                **kwargs)
                                            specials_dict[
                                                self.specials.special_type_dict_by_special[item[_type]['@special']]['ID']][
                                                'ZP_LANG_ID_ACT'] = 0
                                            specials_dict[
                                                self.specials.special_type_dict_by_special[item[_type]['@special']]['ID']][
                                                'ZP_LANG_ID_REQ'] = 0
                                        specials_dict[
                                            self.specials.special_type_dict_by_special[item[_type]['@special']]['ID']][
                                            'ZP_EAPI_ID_ACT'] = ZP_EAPI_ID_ACT
                                        specials_dict[
                                            self.specials.special_type_dict_by_special[item[_type]['@special']]['ID']][
                                            'ZP_EAPI_ID_REQ'] = kwargs['ZP_EAPI_ID_REQ']
                                    if not isinstance(special_text, string_types):
                                        if isinstance(special_text, int) and item[_type].has_key('@max_rating'):
                                            special_text = int((special_text / 10) * int(item[_type]['@max_rating']))
                                        special_text = str(special_text)
                                    text += special_text
                                    if item[_type].has_key('@post_append'):
                                        text += item[_type]['@post_append']
                                    if text:
                                        if item[_type].has_key('@case'):
                                            if item[_type]['@case'].lower() == 'upper':
                                                text = text.upper()
                                            elif item[_type]['@case'].lower() == 'lower':
                                                text = text.lower()
                                        # TODO: deal with multiple font types
                                        if draw_type == 'text_line':
                                            font_path = None
                                            if item[_type]['@font_type'] == 'truetype':
                                                #font_path = ImageFont.truetype(os.path.join(template_folder,
                                                #                                       item[_type]['@font']),
                                                #                          int(item[_type]['@font_size']))
                                                font_path = os.path.join(template_folder, item[_type]['@font'])
                                                font_type = 'truetype'
                                            if font_path:
                                                if os.path.isfile(font_path):
                                                    use_dotdotdot = False
                                                    if '@use_dotdotdot' in item[_type]:
                                                        if item[_type]['@use_dotdotdot'].lower() == 'true':
                                                            use_dotdotdot = True
                                                    log.debug('font_min_size %s, font_max_size %s, font_size %s',
                                                              int_var_dict['font_min_size'],
                                                              int_var_dict['font_max_size'],
                                                              int_var_dict['font_size']
                                                              )
                                                    if (isinstance(int_var_dict['x'], int) and
                                                        isinstance(int_var_dict['y'], int)):
                                                        log.debug('font_min_size %s, font_max_size %s, font_size %s',
                                                                  int_var_dict['font_min_size'],
                                                                  int_var_dict['font_max_size'],
                                                                  int_var_dict['font_size']
                                                                  )
                                                        if (int_var_dict['font_min_size'] is None or
                                                            int_var_dict['font_max_size'] is None) \
                                                            and isinstance(int_var_dict['font_size'], int):
                                                            int_var_dict['font_min_size'] = int_var_dict['font_size']
                                                            int_var_dict['font_max_size'] = int_var_dict['font_size']
                                                            log.debug(
                                                                'font_min_size %s, font_max_size %s, font_size %s',
                                                                int_var_dict['font_min_size'],
                                                                int_var_dict['font_max_size'],
                                                                int_var_dict['font_size']
                                                                )
                                                        elif (int_var_dict['font_min_size'] is None or
                                                            int_var_dict['font_max_size'] is None):
                                                            if isinstance(int_var_dict['font_min_size'], int):
                                                                int_var_dict['font_max_size'] = int_var_dict['font_min_size']
                                                                int_var_dict['font_size'] = int_var_dict['font_min_size']
                                                                log.debug(
                                                                    'font_min_size %s, font_max_size %s, font_size %s',
                                                                    int_var_dict['font_min_size'],
                                                                    int_var_dict['font_max_size'],
                                                                    int_var_dict['font_size']
                                                                    )
                                                            elif isinstance(int_var_dict['font_max_size'], int):
                                                                int_var_dict['font_min_size'] = int_var_dict['font_max_size']
                                                                int_var_dict['font_size'] = int_var_dict['font_max_size']
                                                                log.debug(
                                                                    'font_min_size %s, font_max_size %s, font_size %s',
                                                                    int_var_dict['font_min_size'],
                                                                    int_var_dict['font_max_size'],
                                                                    int_var_dict['font_size']
                                                                    )
                                                            else:
                                                                int_var_dict['font_min_size'] = 30
                                                                int_var_dict['font_max_size'] = 30
                                                                log.debug(
                                                                    'font_min_size %s, font_max_size %s, font_size %s',
                                                                    int_var_dict['font_min_size'],
                                                                    int_var_dict['font_max_size'],
                                                                    int_var_dict['font_size']
                                                                    )
                                                        log.debug(
                                                            'font_min_size %s, font_max_size %s, font_size %s',
                                                            int_var_dict['font_min_size'],
                                                            int_var_dict['font_max_size'],
                                                            int_var_dict['font_size']
                                                        )
                                                        #log.debug(pprint.pformat(item[_type]))
                                                        log.debug(pprint.pformat(int_var_dict))
                                                        text_line(
                                                            ImageDraw.Draw(img),
                                                            int_var_dict['x'],
                                                            int_var_dict['y'],
                                                            text,
                                                            font_path,
                                                            font_type,
                                                            int_var_dict['font_min_size'], int_var_dict['font_max_size'],
                                                            item[_type]['@colour'] if item[_type].has_key('@colour') else '#FFF',
                                                            item[_type]['@halign'] if item[_type].has_key('@halign') else '',
                                                            item[_type]['@valign'] if item[_type].has_key('@valign') else '',
                                                            int_var_dict['width'], int_var_dict['height'],
                                                            use_dotdotdot=use_dotdotdot
                                                        )
                                                    else:
                                                        log.debug("int_var_dict['x'] %s or int_var_dict['y'] is not int %s"
                                                                  "%s %s", int_var_dict['x'], int_var_dict['y'],
                                                                  pprint.pformat(item[_type]), pprint.pformat(int_var_dict))
                                                else:
                                                    log.error('font path %s does not exist', font_path)
                                            else:
                                                log.error('font_path is empty %s', font_path)
                                        else:
                                            log.debug('text_box')
                                            log.debug(pprint.pformat(item[_type]))
                                            font_file_path = os.path.join(template_folder, item[_type]['@font'])
                                            lines, line_spacing, font = text_box(ImageDraw.Draw(img),
                                                                                 text,
                                                                                 font_file_path,
                                                                                 int_var_dict['width'],
                                                                                 int_var_dict['height'],
                                                                                 int_var_dict['font_min_size'],
                                                                                 int_var_dict['font_max_size'],
                                                                                 int_var_dict['x'],
                                                                                 int_var_dict['y'],
                                                                                 int_var_dict['line_spacing'],
                                                                                 item[_type]['@split_char'] if item[
                                                                                     _type].has_key('@split_char') else ' ',
                                                                                 int_var_dict['use_sentences'] if item[
                                                                                     _type].has_key(
                                                                                     '@use_sentences') else 0)
                                            if isinstance(lines, list):
                                                y = int_var_dict['y']
                                                for line in lines:
                                                    line_size_offset = font.getoffset(line)
                                                    line_size_with_offset = ImageDraw.Draw(img).textsize(line, font)
                                                    line_height_withmax_ratingfset = line_size_with_offset[1] - \
                                                                                 line_size_offset[1]
                                                    y_minus_y_line_font_offset = y - line_size_offset[1]
                                                    #log.warning('line %s', line)
                                                    #log.warning(('y %s, line_size_offset %s, line_size_with_offset %s,'
                                                    #             ' line_height_withmax_ratingfset %s, '
                                                    #             ' y_minus_y_line_font_offset %s'), y,
                                                    #            line_size_offset, line_size_with_offset,
                                                    #            line_height_withmax_ratingfset, y_minus_y_line_font_offset)
                                                    ImageDraw.Draw(img).text(
                                                        (int_var_dict['x'], y_minus_y_line_font_offset), line,
                                                        font=font, fill=item[_type]['@colour'] if item[
                                                            _type].has_key('@colour') else '#FFF')
                                                    y += line_spacing + line_height_withmax_ratingfset
                                else:
                                    log.debug('specials does not have attribute: {0}'.format(item[_type]['@special']))
                            elif item[_type].has_key('print'):
                                text = item[_type]['print']
                                if text:
                                    if item[_type].has_key('@case'):
                                        if item[_type]['@case'].lower() == 'upper':
                                            text = text.upper()
                                        elif item[_type]['@case'].lower() == 'lower':
                                            text = text.lower()
                                    if item[_type]['@font_type'] == 'truetype':
                                        #font_path = ImageFont.truetype(os.path.join(template_folder,
                                        #                                       item[_type]['@font']),
                                        #                          int(item[_type]['@font_size']))
                                        font_path = os.path.join(template_folder, item[_type]['@font'])
                                        font_type = 'truetype'
                                    if font_path:
                                        if os.path.isfile(font_path):
                                            log.debug(pprint.pformat(int_var_dict))
                                            if (isinstance(int_var_dict['x'], int) and
                                                isinstance(int_var_dict['y'], int)):
                                                if (int_var_dict['font_min_size'] is None or
                                                    int_var_dict['font_max_size'] is None) \
                                                    and isinstance(int_var_dict['font_size'], int):
                                                    int_var_dict['font_min_size'] = int_var_dict['font_size']
                                                    int_var_dict['font_max_size'] = int_var_dict['font_size']
                                                else:
                                                    if isinstance(int_var_dict['font_min_size'], int):
                                                        int_var_dict['font_max_size'] = int_var_dict['font_min_size']
                                                        int_var_dict['font_size'] = int_var_dict['font_min_size']
                                                    elif isinstance(int_var_dict['font_max_size'], int):
                                                        int_var_dict['font_min_size'] = int_var_dict['font_max_size']
                                                        int_var_dict['font_size'] = int_var_dict['font_max_size']
                                                    else:
                                                        int_var_dict['font_min_size'] = 30
                                                        int_var_dict['font_max_size'] = 30
                                                log.debug('int_var_dict %s', pprint.pformat(int_var_dict))
                                                text_line(ImageDraw.Draw(img),
                                                          int_var_dict['x'],
                                                          int_var_dict['y'],
                                                          text,
                                                          font_path,
                                                          font_type,
                                                          int_var_dict['font_min_size'], int_var_dict['font_max_size'],
                                                          item[_type]['@colour'] if item[_type].has_key('@colour') else '#FFF',
                                                          item[_type]['@halign'] if item[_type].has_key('@halign') else '',
                                                          item[_type]['@valign'] if item[_type].has_key('@valign') else '',
                                                          int_var_dict['width'], int_var_dict['height'],
                                                          )
                                else:
                                    log.warning('item[_type]["print"] is empty',
                                            pprint.pformat(item[_type]))
                            else:
                                log.warning('item[_type] does not have key @special or print',
                                            pprint.pformat(item[_type]))
                        elif _type == 'graphic':
                            if item[_type].has_key('@special'):
                                log.debug('item[_type]: {0} has key @special'.format(
                                    item[_type]))
                                if item[_type]['@special'] in ['backdrop', 'poster', 'banner', 'collection_poster',
                                                               'screenshot']:
                                    log.debug('_type: {0} @special is backdrop: {1}'.format(
                                        _type,
                                        item[_type]['@special']))
                                    # get_eapi_image(Session, image_type, width, height, **kwargs)
                                    temp_image, zp_raw_image_id = self.get_resized_raw_image(item[_type]['@special'],
                                                                                     int_var_dict['width'],
                                                                                     int_var_dict['height'], **kwargs)
                                    specials_dict[
                                        self.specials.special_type_dict_by_special[item[_type]['@special']]['ID']] = {}
                                    specials_dict[
                                        self.specials.special_type_dict_by_special[item[_type]['@special']]['ID']][
                                        'ZP_RAW_IMAGE_ID'] = zp_raw_image_id
                                    if temp_image is not None:
                                        img.paste(temp_image, (int_var_dict['x'], int_var_dict['y']),
                                                  temp_image.convert('RGBA'))
                                        temp_image.close()
                                        log.debug('''img paste complete for item[_type]['@special']: {0}'''.format(
                                            item[_type]['@special']))
                                    else:
                                        log.warning(
                                            '''temp_image is type: {0} and not <class 'PIL.Image.Image'> item[_type]: {1}'''.format(
                                                type(temp_image),
                                                item[_type]))
                                        # raise SystemExit
                                elif item[_type]['@special'] == 'rating':
                                    if item[_type].has_key('@format'):
                                        rating, ZP_EAPI_ID_ACT = self.specials.rating(**kwargs)
                                        specials_dict[
                                            self.specials.special_type_dict_by_special[item[_type]['@special']]['ID']] = {}
                                        specials_dict[
                                            self.specials.special_type_dict_by_special[item[_type]['@special']]['ID']][
                                            'ZP_EAPI_ID_ACT'] = ZP_EAPI_ID_ACT
                                        specials_dict[
                                            self.specials.special_type_dict_by_special[item[_type]['@special']]['ID']][
                                            'ZP_EAPI_ID_REQ'] = kwargs['ZP_EAPI_ID_REQ']
                                        max_rating = 10
                                        if item[_type].has_key('@max_rating'):
                                            max_rating = int(item[_type]['@max_rating'])
                                        #rating = int((rating / 10) * int(item[_type]['@max_rating']))
                                        image_rating = get_rating_image_number(rating, max_rating)
                                        if image_rating is None:
                                            # if there is no rating set it to average
                                            image_rating = int(math.ceil(max_rating/2))
                                        temp_image_path = os.path.join(template_folder,
                                                                       re.sub(r'::rating::', str(image_rating),
                                                                              item[_type]['@format']))
                                        # TODO: Put this into a function as repeated below
                                        if os.path.isfile(temp_image_path):
                                            temp_image = Image.open(temp_image_path)
                                            if item[_type].has_key('@alpha_composite') and item[_type][
                                                '@alpha_composite'].lower() == 'true' and aplha is True:
                                                log.debug('pasting: {0} with alpha_composite'.format(temp_image_path))
                                                img = Image.alpha_composite(img, temp_image)
                                                log.debug(
                                                    '''img paste complete for item[_type]: {0}'''.format(item[_type]))
                                            else:
                                                log.debug(
                                                    'pasting: {0} without alpha_composite'.format(temp_image_path))
                                                img.paste(temp_image, (int_var_dict['x'], int_var_dict['y']),
                                                          temp_image.convert('RGBA'))
                                                log.debug(
                                                    '''img paste complete for item[_type]: {0}'''.format(item[_type]))
                                                temp_image.close()
                                        else:
                                            log.warning('temp_image_path: {0} does not exist or is not a file'.format(
                                                temp_image_path))

                                    else:
                                        log.warning(
                                            'item[_type].keys(): {0} does not have all the keys @format, @path'.format(
                                                item[_type].keys()))
                                elif item[_type]['@special'] == 'vcodec':
                                    if item[_type].has_key('@format'):
                                        vcodec = self.specials.video_codec(**kwargs)
                                        log.debug('vcodec: {0} for kwargs: {1}'.format(
                                            vcodec, kwargs))
                                        vcodec_image_file = re.sub('::vcodec::', str(vcodec), item[_type]['@format'])
                                        vcodec_image_file_path = os.path.join(template_folder,
                                                                              vcodec_image_file)
                                        if os.path.isfile(vcodec_image_file_path):
                                            # print(score_image_file_path)
                                            temp_image = Image.open(vcodec_image_file_path)
                                            log.debug('alpha %s', aplha)
                                            log.debug('item %s', pprint.pformat(item[_type]))
                                            if item[_type].has_key('@alpha_composite') and item[_type][
                                                '@alpha_composite'].lower() == 'true' and aplha is True:
                                                log.debug('pasting: {0} with alpha_composite'.format(
                                                    vcodec_image_file_path))
                                                img = Image.alpha_composite(img, temp_image)
                                                log.debug('''img paste complete for item[_type]: {0}'''.format(
                                                    item[_type]))
                                            else:
                                                log.debug('pasting: {0} without alpha_composite'.format(
                                                    vcodec_image_file_path))
                                                img.paste(temp_image,
                                                          (int_var_dict['x'], int_var_dict['y']),
                                                          temp_image.convert('RGBA'))
                                                log.debug('''img paste complete for item[_type]: {0}'''.format(
                                                    item[_type]))
                                                temp_image.close()
                                        else:
                                            log.error('score file: {0} is not a file or does not exist'.format(
                                                vcodec_image_file_path))
                                elif item[_type]['@special'] == 'acodec':
                                    if item[_type].has_key('@format'):
                                        acodec = self.specials.audio_codec(**kwargs)
                                        log.debug('acodec: {0} for kwargs: {1}'.format(
                                            acodec, kwargs))
                                        acodec_image_file = re.sub('::acodec::', str(acodec), item[_type]['@format'])
                                        acodec_image_file_path = os.path.join(template_folder,
                                                                              acodec_image_file)
                                        if os.path.isfile(acodec_image_file_path):
                                            # print(score_image_file_path)
                                            temp_image = Image.open(acodec_image_file_path)
                                            log.debug('alpha %s', aplha)
                                            log.debug('item %s', pprint.pformat(item[_type]))
                                            if item[_type].has_key('@alpha_composite') and item[_type][
                                                '@alpha_composite'].lower() == 'true' and aplha is True:
                                                log.debug('pasting: {0} with alpha_composite'.format(
                                                    acodec_image_file_path))
                                                img = Image.alpha_composite(img, temp_image)
                                                log.debug('''img paste complete for item[_type]: {0}'''.format(
                                                    item[_type]))
                                            else:
                                                log.debug('pasting: {0} without alpha_composite'.format(
                                                    acodec_image_file_path))
                                                img.paste(temp_image,
                                                          (int_var_dict['x'], int_var_dict['y']),
                                                          temp_image.convert('RGBA'))
                                                log.debug('''img paste complete for item[_type]: {0}'''.format(
                                                    item[_type]))
                                                temp_image.close()
                                        else:
                                            log.error('score file: {0} is not a file or does not exist'.format(
                                                acodec_image_file_path))
                                elif item[_type]['@special'] == 'format':
                                    if item[_type].has_key('@format'):
                                        format = self.specials.format(**kwargs)
                                        format_image_file = re.sub('::format::', str(format), item[_type]['@format'])
                                        format_image_file_path = os.path.join(template_folder,
                                                                              format_image_file)
                                        if os.path.isfile(format_image_file_path):
                                            # print(score_image_file_path)
                                            temp_image = Image.open(format_image_file_path)
                                            log.debug('alpha %s', aplha)
                                            log.debug('item %s', pprint.pformat(item[_type]))
                                            if item[_type].has_key('@alpha_composite') and item[_type][
                                                '@alpha_composite'].lower() == 'true' and aplha is True:
                                                log.debug('pasting: {0} with alpha_composite'.format(
                                                    format_image_file_path))
                                                img = Image.alpha_composite(img, temp_image)
                                                log.debug('''img paste complete for item[_type]: {0}'''.format(
                                                    item[_type]))
                                            else:
                                                log.debug('pasting: {0} without alpha_composite'.format(
                                                    format_image_file_path))
                                                img.paste(temp_image,
                                                          (int_var_dict['x'], int_var_dict['y']),
                                                          temp_image.convert('RGBA'))
                                                log.debug('''img paste complete for item[_type]: {0}'''.format(
                                                    item[_type]))
                                                temp_image.close()
                                        else:
                                            log.error('score file: {0} is not a file or does not exist'.format(
                                                format_image_file_path))
                                elif item[_type]['@special'] == 'audio_channels':
                                    if item[_type].has_key('@format'):
                                        channel_identifier = self.specials.audio_channels(**kwargs)
                                        channel_identifier_image_file = re.sub('::channels::', str(channel_identifier), item[_type]['@format'])
                                        channel_identifier_image_file_path = os.path.join(template_folder,
                                                                              channel_identifier_image_file)
                                        if os.path.isfile(channel_identifier_image_file_path):
                                            # print(score_image_file_path)
                                            temp_image = Image.open(channel_identifier_image_file_path)
                                            log.debug('alpha %s', aplha)
                                            log.debug('item %s', pprint.pformat(item[_type]))
                                            if item[_type].has_key('@alpha_composite') and item[_type][
                                                '@alpha_composite'].lower() == 'true' and aplha is True:
                                                log.debug('pasting: {0} with alpha_composite'.format(
                                                    channel_identifier_image_file_path))
                                                img = Image.alpha_composite(img, temp_image)
                                                log.debug('''img paste complete for item[_type]: {0}'''.format(
                                                    item[_type]))
                                            else:
                                                log.debug('pasting: {0} without alpha_composite'.format(
                                                    channel_identifier_image_file_path))
                                                img.paste(temp_image,
                                                          (int_var_dict['x'], int_var_dict['y']),
                                                          temp_image.convert('RGBA'))
                                                log.debug('''img paste complete for item[_type]: {0}'''.format(
                                                    item[_type]))
                                                temp_image.close()
                                        else:
                                            log.error('score file: {0} is not a file or does not exist'.format(
                                                channel_identifier_image_file_path))
                                elif item[_type]['@special'] == 'score':
                                    if item[_type].has_key('@format'):
                                        score = self.specials.score(**kwargs)
                                        log.debug('score: {0} for kwargs: {1}'.format(
                                            score, kwargs))
                                        if isinstance(score, dict):
                                            replace_dict = {r'::res::': 'ZP_RES_ID', r'::source::': 'ZP_SOURCE_ID',
                                                            r'::disc::': 'DISC'}
                                            score_image_file = item[_type]['@format']
                                            for replace in replace_dict:
                                                score_image_file = re.sub(replace, str(score[replace_dict[replace]]),
                                                                          score_image_file)
                                            score_image_file_path = os.path.join(template_folder,
                                                                                 score_image_file)
                                            log.debug('score_image_file_path: {0} for kwargs: {1}'.format(
                                                score_image_file_path, kwargs))
                                            if os.path.isfile(score_image_file_path):
                                                # print(score_image_file_path)
                                                temp_image = Image.open(score_image_file_path)
                                                log.debug('alpha %s', aplha)
                                                log.debug('item %s', pprint.pformat(item[_type]))
                                                if item[_type].has_key('@alpha_composite') and item[_type][
                                                    '@alpha_composite'].lower() == 'true' and aplha is True:
                                                    log.debug('pasting: {0} with alpha_composite'.format(
                                                        score_image_file_path))
                                                    img = Image.alpha_composite(img, temp_image)
                                                    log.debug('''img paste complete for item[_type]: {0}'''.format(
                                                        item[_type]))
                                                else:
                                                    log.debug('pasting: {0} without alpha_composite'.format(
                                                        score_image_file_path))
                                                    img.paste(temp_image,
                                                              (int_var_dict['x'], int_var_dict['y']),
                                                              temp_image.convert('RGBA'))
                                                    log.debug('''img paste complete for item[_type]: {0}'''.format(
                                                        item[_type]))
                                                    temp_image.close()
                                            else:
                                                log.error('score file: {0} is not a file or does not exist'.format(
                                                    score_image_file_path))
                                                #raise SystemExit
                                        else:
                                            log.warning('score: {0} is not dict for kwargs: {1}. item[_type]: {0}'.format(
                                                score,
                                                kwargs,
                                                item[_type]))
                                    else:
                                        log.warning(
                                            'item[_type].keys(): {0} does not have all the keys @format, @path'.format(
                                                item[_type].keys()))

                                else:
                                    log.warning('''item[_type]['@special']: {0} not currently supported'''.format(
                                        item[_type]['@special']))
                            elif item[_type].has_key('@file'):
                                log.debug('item[_type]: {0} has key @file'.format(
                                    item[_type]))
                                temp_image_path = os.path.join(template_folder,
                                                               item[_type]['@file'])
                                log.debug('temp_image_path: {0}'.format(temp_image_path))
                                temp_image = Image.open(temp_image_path)
                                if item[_type].has_key('@alpha_composite') and item[_type][
                                    '@alpha_composite'].lower() == 'true' and aplha is True:
                                    log.debug('pasting: {0} with alpha_composite'.format(temp_image_path))
                                    img = Image.alpha_composite(img, temp_image)
                                    log.debug('''img paste complete for item[_type]['@file']: {0}'''.format(
                                        item[_type]['@file']))
                                else:
                                    log.debug('pasting: {0} without alpha_composite'.format(temp_image_path))
                                    img.paste(temp_image, (int_var_dict['x'], int_var_dict['y']),
                                              temp_image.convert('RGBA'))
                                    log.debug('''img paste complete for item[_type]['@file']: {0}'''.format(
                                        item[_type]['@file']))
                                temp_image.close()
                        else:
                            log.debug('_type:{0} not supported'.format(_type))
                else:
                    log.error('x and y not ints %s', pprint.pformat(item[_type]))
        return specials_dict, img

