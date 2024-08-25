# -*- coding: utf-8 
from __future__ import unicode_literals, division, absolute_import, print_function

import json
import os
import time
from six import string_types
try:
    from SocketServer import ThreadingMixIn
except ImportError:
    from socketserver import ThreadingMixIn

import xmltodict
try:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
except ImportError:
    from http.server import BaseHTTPRequestHandler, HTTPServer

import zerrphix.template

try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse, parse_qs
import imghdr
# from PIL import Image
import mimetypes
import shutil
import requests
from PIL import Image, ImageDraw, ImageFont
from zerrphix.util.image import text_line
from zerrphix.httpserver.dune.film import *
# from zerrphix.httpserver.film_collection import *
from zerrphix.httpserver.dune.base import *
from zerrphix.httpserver.dune.tv import *
from sqlalchemy import orm
from zerrphix.util.text import xml_to_dict
import pprint

log = logging.getLogger(__name__)

_template_json = None


class DuneHTTPSvr(object):
    def __init__(self, Session, global_config_dict):
        # logging.config.dictConfig(LOG_SETTINGS)
        global _Session
        _Session = Session
        global _global_config_dict
        _global_config_dict = global_config_dict

    def run(self):
        hostName = _global_config_dict['dune_http_server_listen_ip']
        hostPort = _global_config_dict['dune_http_server_listen_port']

        # log.debug(_template_json)

        class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
            pass

        class MyServer(BaseHTTPRequestHandler):

            def __init__(self, request, client_address, server):
                # self.session = _session
                # extend the init from BaseHTTPRequestHandler
                # super(self.__class__, self).__init__(*args, **kwargs)
                # super(MyServer, self).__init__(*args, **kwargs)
                # httpdkenlogger = logging.getLogger('httpp')
                # fh = logging.FileHandler(os.path.join(tempfile.gettempdir(), 'zerrphix_http.log'))
                # fh.setLevel(logging.DEBUG)
                # ch = logging.StreamHandler()
                # ch.setLevel(logging.DEBUG)
                # frmt = logging.Formatter('%(asctime)s %(levelname)8s:%(name)s:%(filename)s:%(funcName)s:%(lineno)d:%(message)s')
                # fh.setFormatter(frmt)
                # ch.setFormatter(frmt)
                # httpdkenlogger.addHandler(fh)
                # httpdkenlogger.addHandler(ch)
                # self.httpdkenlogger = httpdkenlogger
                # The below init has to be done last. http://stackoverflow.com/questions/25975452/i-cant-access-member-from-inheriting-basehttpserver-in-python-why
                BaseHTTPRequestHandler.__init__(self, request, client_address, server)
                self.global_config_dict = _global_config_dict

            def sub(self, string, _replace_dict):
                for replace in _replace_dict:
                    string = re.sub(replace, _replace_dict[replace], string)
                return string

            def get_image_sub_type_dict(self):
                return {1 : '',
                        2: '_sel',
                        3: '_watched',
                        4: '_watched_sel',
                        5: '_favourite',
                        6: '_favourite_sel',
                        7: '_to_watch',
                        8: '_to_watch_sel'}

            def evaluate_dune_id(self, dune_id):
                session = _Session()
                zp_dune_id = dune_id
                zp_dune = session.query(TABLES.ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF).filter(
                    TABLES.ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF.ZP_DUNE_ID == dune_id
                ).one()
                if zp_dune.ZP_DUNE_UI_IMAGE_STORE_TYPE_ID < 2:
                    zp_dune_id = '0'
                session.close()
                return zp_dune_id

            def get_ui_template(self, templates_dict):
                for template in templates_dict['templates']['template']:
                    if template['@space'] == 'ui':
                        return template

            def get_ui_temaplte_var_dict(self, template_xml_path):
                templates_dict = xml_to_dict(template_xml_path)
                ui_template = self.get_ui_template(templates_dict)
                ui_fonts_string = ui_template['@fonts']
                return_dict = {'fonts': {}}
                for ui_font_split in ui_fonts_string.split(','):
                    ui_font_sub_split = ui_font_split.split('=')
                    return_dict['fonts'][ui_font_sub_split[0]] = ui_font_sub_split[1]
                return_dict['film_search_bg'] = ui_template['@film_search_bg']
                return_dict['tv_search_bg'] = ui_template['@tv_search_bg']
                return_dict['search_font_size'] = int(ui_template['@search_font_size'])
                return_dict['search_font_spacing'] = int(ui_template['@search_font_spacing'])
                log.debug('return_dict %s', pprint.pformat(return_dict))
                return return_dict

            def get_template_path(self, zp_temaplte_id):
                session = _Session()
                try:
                    zp_temaplte = session.query(TABLES.ZP_TEMPLATE).filter(
                        TABLES.ZP_TEMPLATE.ID == zp_temaplte_id
                    ).one()
                except orm.exc.NoResultFound:
                    path = None
                else:
                    if zp_temaplte.PATH_TYPE == 1:
                        path = os.path.join(zerrphix.template.__path__[0], zp_temaplte.PATH,
                                     'template.xml')
                    else:
                        path = os.path.join(zp_temaplte.PATH,
                                     'template.xml')
                session.close()
                return path

            def get_ui_temaplte(self, temapltes_dict):
                for template in  temapltes_dict['templates']['template']:
                    if template['@space'] == 'ui':
                        return template
                return None

            def get_user_template_id(self, zp_user_id):
                try:
                    zp_user_template = self.session.query(
                        TABLES.ZP_USER_TEMPLATE_XREF.ZP_TEMPLATE_ID,
                        TABLES.ZP_TEMPLATE.REF_NAME
                    ).join(
                        TABLES.ZP_TEMPLATE, TABLES.ZP_USER_TEMPLATE_XREF.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
                    ).filter(
                        TABLES.ZP_USER_TEMPLATE_XREF.ZP_USER_ID == zp_user_id
                    ).one()
                except orm.exc.NoResultFound:
                    zp_template_id = 1
                else:
                    zp_template_id = zp_user_template.ZP_TEMPLATE_ID
                return zp_template_id

            def dune_ui(self):
                self.session = _Session()
                self.session.query(TABLES.ZP_DUNE).all()
                self.session.close()
                self.session = _Session()
                # TODO: sanitise user inputs
                # print(self.render_root_dir)
                self.send_response(200)
                self.send_header('Content-type', 'text/plain; charset="utf-8"')
                self.end_headers()
                # ui NON root structure url should be of format http://hostname/ip:port/m/ZP_DUNE_ID/ZP_USER_ID/ZP_TEMAPLTE_ID/menu?foo=bar
                # ui root structure url should be of format http://hostname/ip:port/m/ZP_DUNE_ID/root
                template_menu_user_dune_pattern = r"^/m/([\d]+)/(\d+)/(\d+)/([a-z_]+)"
                template_menu_user_dune_match = re.match(template_menu_user_dune_pattern, self.path, flags=re.I)
                template_root_menu_dune_pattern = r"^/m/([\d]+)/root"
                template_root_menu_dune_match = re.match(template_root_menu_dune_pattern, self.path, flags=re.I)

                # TODO: Template name should not be obtained form url but db
                if template_menu_user_dune_match or template_root_menu_dune_match:
                    #dune_id = self.evaluate_dune_id(template_menu_user_dune_match.group(1))
                    dune_id = template_menu_user_dune_match.group(1)
                    #template_id = template_menu_user_dune_match.group(3)
                    ZP_USER_ID = None
                    if template_menu_user_dune_match:
                        ZP_USER_ID = template_menu_user_dune_match.group(2)
                        template_id = str(self.get_user_template_id(ZP_USER_ID))
                        menu_name = template_menu_user_dune_match.group(4)
                    else:
                        # todo get this from the db
                        template_id = str(1)
                        menu_name = 'root'
                    template_xml_filename = self.get_template_path(template_id)
                    template_folder = os.path.dirname(template_xml_filename)
                    if os.path.isfile(template_xml_filename):
                        with open(template_xml_filename) as fd:
                            _template_json = json.loads(json.dumps(xmltodict.parse(fd.read())))

                        ui_template = self.get_ui_temaplte(_template_json)
                        if isinstance(ui_template, dict):
                            # ZP_USER_ID = ZP_USER_ID
                            # get url query
                            # add as kwargs to getattr(self, virtual_item['@special'])()
                            # convert query (?var=boo&foo=bar) in request url to dict
                            request_query_kwargs = parse_qs(urlparse(self.path)[4])

                            # if request_query_kwargs:
                            request_query_kwargs['ZP_USER_ID'] = ZP_USER_ID
                            request_query_kwargs['ZP_DUNE_ID'] = dune_id
                            if ui_template['ui'].has_key(menu_name):
                                host = self.headers.get('Host')
                                _replace_dict = {r'::root_url::': 'http://{0}/'.format(host),
                                                 r'::root_url_dhttp::': 'dune_http://{0}'.format(host),
                                                 r'::root_menu_dhttp::': 'dune_http://{0}/m/{1}'.format(host, dune_id),
                                                 r'::root_user_url_dhttp::': 'dune_http://{0}/m/{1}/{2}'.format(
                                                     host, dune_id, ZP_USER_ID),
                                                 r'::root_template_url_dhttp::': 'dune_http://{0}/m/{1}/{2}/{3}'.format(
                                                     host, dune_id, ZP_USER_ID, template_id),
                                                 r'::root_template_url_http::': 'http://{0}/m/{1}/{2}/{3}'.format(
                                                     host, dune_id, ZP_USER_ID, template_id),
                                                 r'::root_template_image_url_http::': 'http://{0}/i/t/{1}'.format(
                                                     host, template_id),
                                                 r'::root_dynamic_image_url_http::': 'http://{0}/i/d/{1}'.format(
                                                     host, template_id),
                                                 r'::root_render_image_url_http::': 'http://{0}/i/r'.format(host),
                                                 r'::template_name::': template_id,
                                                 # This needs to be got from the ZP_USER_ID specific render images exenstion type setting
                                                 r'::img_extension::': '.png',
                                                 r'::lang::': 'en',
                                                 r'::ZP_USER_ID::': str(ZP_USER_ID)}

                                _ui_defaults = ui_template['ui']['default']
                                #if menu_name == 'main':
                                #    r = requests.get(
                                #        'http://192.168.0.72/zerrphix/dhttp/index.php?dune_id=1&gid=1&menu=main&user_id={0}'.format(
                                #            ZP_USER_ID))
                                #    # print(r.content)
                                #    _replace_dict[r'::ZP_SHOW_ID::'] = re.search(
                                #        r'''item\.0\.media_url=dune_http://192\.168\.0\.72/zerrphix/dhttp/index\.php\?dune_id=1&gid=1&user_id=\d+&menu=tv_synop&tv_show_id=(\d+)''',
                                #        r.content).group(1)
                                #    # if request_query_kwargs:

                                session = _Session()
                                try:
                                    ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF = session.query(
                                        TABLES.ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF).filter(
                                        TABLES.ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF.ZP_DUNE_ID == dune_id).one()
                                except orm.exc.NoResultFound:
                                    pass
                                else:
                                # print(ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF.ZP_DUNE_UI_IMAGE_STORE_TYPE_ID)
                                    if ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF.ZP_DUNE_UI_IMAGE_STORE_TYPE_ID == 2:
                                        _replace_dict['::root_render_image_url_http::'] = '{0}/rendered'.format(
                                            ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF.DUNE_LOCAL_REF.rstrip('/'))
                                        _replace_dict[r'::root_template_image_url_http::'] = '{0}/template/{1}'.format(
                                            ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF.DUNE_LOCAL_REF.rstrip('/'), template_id)
                                session.close()
                                request_query_kwargs['root_render_image_url_http'] = _replace_dict[
                                    '::root_render_image_url_http::']
                                request_query_kwargs['root_template_image_url_http'] = _replace_dict[
                                    '::root_template_image_url_http::']
                                request_query_kwargs['root_user_url_dhttp'] = _replace_dict[
                                    '::root_user_url_dhttp::']
                                # print(request_query_kwargs.keys())
                                get_list = ['ZP_FILM_ID', 'ZP_TV_ID', 'SEASON', 'EPISODE', 'ZP_TV_EPISODE_ID',
                                            'search_type', 'search_string', 'ZP_FILM_COLLECTION_ID']
                                for get in get_list:
                                    if get in request_query_kwargs.keys():
                                        _replace_dict[r'::{0}::'.format(get)] = request_query_kwargs[get][0]
                                        # print(r'::{0}::'.format(get), request_query_kwargs[get][0])
                                if 'search_string' not in request_query_kwargs.keys():
                                    _replace_dict[r'::search_string::'] = ''
                                    # if '@get' in ui_template['ui'][menu_name]['main'].keys():
                                #	get_list = ui_template['ui'][menu_name]['main']['@get'].split(',')
                                #	#print(get_list)
                                #	#print(request_query_kwargs)
                                #	# TODO: This needs to be done better
                                #	for get in get_list:
                                #		if get in ['ZP_FILM_ID', 'ZP_TV_ID', 'SEASON', 'EPISODE']:
                                #			#print(request_query_kwargs)
                                #			_replace_dict[r'::{0}::'.format(get)] = request_query_kwargs[get][0]
                                #		elif get == 'search_type':
                                #			_replace_dict[r'::search_type::'] = request_query_kwargs['search_type'][0]
                                #		elif get == 'search_string':
                                #			try:
                                #				_replace_dict[r'::search_string::'] = request_query_kwargs['search_string'][0]
                                #			except KeyError:
                                #				_replace_dict[r'::search_string::'] = ''
                                # TODO: This needs to be done better (more dynamic)
                                if '@req' in ui_template['ui'][menu_name]['main'].keys():
                                    # print(ui_template['ui'][menu_name]['main'])
                                    req_list = ui_template['ui'][menu_name]['main']['@req'].split(',')
                                    # print(req_list)
                                    for req in req_list:
                                        if req == 'film_synopsis_bg_url':
                                            _replace_dict[r'::film_synopsis_bg_url::'] = film_synopsis_bg_image_path(
                                                self, _replace_dict['::ZP_FILM_ID::'],
                                                ZP_USER_ID,
                                                dune_id,
                                                'http://{0}/i/r'.format(host))
                                        elif req == 'film_fav_bg_url':
                                            _replace_dict[r'::addrm::'] = film_fav_bg_image_path(
                                                self, _replace_dict['::ZP_FILM_ID::'],ZP_USER_ID)
                                        elif req == 'film_tow_bg_url':
                                            _replace_dict[r'::addrm::'] = film_tow_bg_image_path(
                                                self,_replace_dict['::ZP_FILM_ID::'],ZP_USER_ID)
                                        elif req == 'tv_synopsis_bg_url':
                                            _replace_dict[r'::tv_synopsis_bg_url::'] = tv_synopsis_bg_image_path(
                                                self, _replace_dict['::ZP_TV_ID::'], ZP_USER_ID, dune_id,
                                                'http://{0}/i/r'.format(host))
                                        elif req == 'tv_fav_bg_url':
                                            _replace_dict[r'::addrm::'] = tv_fav_bg_image_path(self, _replace_dict[
                                                '::ZP_TV_ID::'], ZP_USER_ID)
                                        elif req == 'tv_tow_bg_url':
                                            _replace_dict[r'::addrm::'] = tv_tow_bg_image_path(self, _replace_dict[
                                                '::ZP_TV_ID::'], ZP_USER_ID)
                                if '@image_type' in ui_template['ui'][menu_name]['main'] and '@image_sub_type' in \
                                    ui_template['ui'][menu_name]['main'] and '@library' in ui_template['ui'][menu_name]['main']:
                                    entity_id = ''
                                    if ui_template['ui'][menu_name]['main']['@library'] == 'tv':
                                        entity_id = request_query_kwargs['ZP_TV_ID'][0]
                                    elif ui_template['ui'][menu_name]['main']['@library'] == 'film':
                                        entity_id = request_query_kwargs['ZP_FILM_ID'][0]
                                    elif ui_template['ui'][menu_name]['main']['@library'] == 'film_collection':
                                        entity_id = request_query_kwargs['ZP_FILM_COLLECTION_ID'][0]
                                    _replace_dict[r'::image_url::'] = get_redered_image_url(
                                        self,
                                        ui_template['ui'][menu_name]['main']['@library'],
                                        ui_template['ui'][menu_name]['main']['@image_type'],
                                        ui_template['ui'][menu_name]['main']['@image_sub_type'],
                                        entity_id,
                                        **request_query_kwargs
                                    )

                                for main_parameter in ui_template['ui'][menu_name]['main']:
                                    if not main_parameter.startswith('@'):
                                        if ui_template['ui'][menu_name]['main'][main_parameter] is None:
                                            self.wfile.write('{0}={1}\n'.format(
                                                main_parameter,
                                                self.sub(ui_template['ui']['default'][main_parameter],
                                                         _replace_dict)).encode("utf-8"))
                                        else:
                                            self.wfile.write('{0}={1}\n'.format(
                                                main_parameter,
                                                self.sub(ui_template['ui'][menu_name]['main'][main_parameter],
                                                         _replace_dict)).encode("utf-8"))
                                self.wfile.write('\n')
                                virtual_item_number = 0
                                if 'item' in ui_template['ui'][menu_name].keys():
                                    log.debug('''ui_template['ui'][menu_name]['item']: {0}'''.format(
                                        ui_template['ui'][menu_name]['item']))
                                    # print(type(ui_template['ui'][menu_name]['item']))
                                    if isinstance(ui_template['ui'][menu_name]['item'], dict):
                                        ui_template['ui'][menu_name]['item'] = [
                                            ui_template['ui'][menu_name]['item']]
                                    for virtual_item in ui_template['ui'][menu_name]['item']:
                                        #log.error('virtual_item %s', pprint.pformat(virtual_item))
                                        try:
                                            for optional_item_key in {'image_type', 'alt_icon', 'alt_icon_sel'}:
                                                if '@%s' % optional_item_key in virtual_item:
                                                    request_query_kwargs[optional_item_key] = \
                                                        virtual_item['@%s' % optional_item_key]
                                            log.debug('virtual_item %s', pprint.pformat(virtual_item))
                                            log.debug('request_query_kwargs %s', pprint.pformat(request_query_kwargs))
                                            if 'image_type' not in request_query_kwargs:
                                                request_query_kwargs['image_type'] = 'icon'
                                            if '@special' in virtual_item:
                                                # if hasattr(self, virtual_item['@special']):
                                                #log.warning(dir(globals()))
                                                if virtual_item['@special'] in globals():
                                                    # if virtual_item['@special'] == 'film_list':
                                                    # (self.eapi_order,
                                                    # self.title_type_order,
                                                    # self.lang_list) = user_prefs(self.session, ZP_USER_ID)
                                                    # print(self.eapi_order,
                                                    # self.title_type_order,
                                                    # self.lang_list)
                                                    if request_query_kwargs:
                                                        # special_replace_dicts = getattr(self, virtual_item['@special'])()
                                                        special_replace_dicts = globals()[virtual_item['@special']](
                                                            self, **request_query_kwargs)
                                                    else:
                                                        # special_replace_dicts = getattr(self, virtual_item['@special'])()
                                                        special_replace_dicts = globals()[virtual_item['@special']]()
                                                    if isinstance(special_replace_dicts, list):
                                                        for special_replace_dict in special_replace_dicts:
                                                            _replace_dict = self.merge_two_dicts(_replace_dict,
                                                                                                 special_replace_dict)
                                                            # print(_replace_dict)
                                                            virtual_item_number = self.process_virtual_items(
                                                                virtual_item['ui'],
                                                                virtual_item_number,
                                                                _replace_dict, ui_template)
                                                    else:
                                                        log.warning(
                                                            'special_replace_dicts: {0} type: {1} is not list. This is normal e.g. for when a user has not watched a film yet'.format(
                                                                special_replace_dicts,
                                                                type(special_replace_dicts)))
                                                else:
                                                    log.warning(
                                                        '''virtual_item['@special']: {0} not an attribute of self: {1}'''.format(
                                                            virtual_item['@special'], dir(self)))
                                            else:
                                                virtual_item_number = self.process_virtual_items(virtual_item['ui'],
                                                                                                 virtual_item_number,
                                                                                                 _replace_dict,
                                                                                                 ui_template)
                                        except AttributeError as e:
                                            log.debug('AttributeError: {0}. virtual_item: {1}'.format(e, virtual_item),
                                                      exc_info=True)
                            elif menu_name.lower() == 'film_play':
                                film_play(self, request_query_kwargs['ZP_FILM_ID'][0], ZP_USER_ID, dune_id)
                            elif menu_name.lower() == 'tv_episode_play':
                                tv_episode_play(self, **request_query_kwargs)
                            elif menu_name.lower() == 'tv_watch_next':
                                tv_watch_next(self, **request_query_kwargs)
                            elif menu_name.lower() == 'tv_continue':
                                tv_continue(self, **request_query_kwargs)
                            else:
                                log.critical('{0}: is not in ui_template.keys(): {1}'.format(
                                    menu_name, ui_template['ui'].keys()))
                        else:
                            self.wfile.write('Cannot find ui @space in _template_json \n')
                    else:
                        self.wfile.write('Cannot load temaplte from %s \n' % template_xml_filename)
                        log.critical('template_xml_filename: {0} is not a file or does not exist'.format(
                            template_xml_filename))
                else:
                    self.wfile.write( 'template_menu_user_dune_match: {0} with template_menu_user_pattern:'
                                      ' {1} on self.path: {2}\n'.format(
                            template_menu_user_dune_match, template_menu_user_dune_pattern, self.path))
                    log.critical(
                        'template_menu_user_dune_match: {0} with template_menu_user_pattern: {1} on self.path: {2}'.format(
                            template_menu_user_dune_match, template_menu_user_dune_pattern, self.path))
                self.session.close()

            def image(self):
                self.send_response(200)
                image_request_url_pattern = r"""^(/i/([tdr])/([0-9a-z_]+)/)(.*)"""
                image_request_url_match = re.match(image_request_url_pattern, self.path, flags=re.I)
                if image_request_url_match:
                    request_type = image_request_url_match.group(2)
                    template_id = image_request_url_match.group(3)
                    image_last_path = image_request_url_match.group(4)
                    if request_type == 't':
                        temaplte_dir = os.path.dirname(self.get_template_path(template_id))
                        if isinstance(temaplte_dir, string_types):
                            # remove multiple / next to each other i.e. //// becomes /
                            # remove first pat of path we are not interested in
                            # split each path section and put then in a list for use with os.path.join
                            temp_image_last_path_list = re.sub(r'/+', '/',
                                                               self.path[len(image_request_url_match.group(1)):]).split(
                                '/')
                            log.debug('temp_image_last_path_list: {0}'.format(temp_image_last_path_list))
                            temp_image_path = os.path.join(temaplte_dir, 'ui',
                                                           *temp_image_last_path_list)
                            log.debug('temp_image_path: {0}'.format(temp_image_path))
                            self.send_image(temp_image_path)
                        else:
                            log.warning('template: {0} not found'.format(template_id))
                    elif request_type == 'r':
                        log.warning(_global_config_dict)
                        #raise SystemExit
                        render_root_dir = _global_config_dict['rendered_image_root_path']
                        log.debug('render_root_dir: {0}'.format(render_root_dir))
                        # temp_image_last_path_list = re.sub(r'/+', '/', self.path[len(image_request_url_match.group(1)):]).split('/')
                        # temp_image_path = os.path.join(render_root_dir, *temp_image_last_path_list)
                        # TODO: sanitise properly
                        temp_image_path = os.path.join(render_root_dir, template_id.encode('ascii', errors='ignore'),
                                                       image_last_path.encode('ascii', errors='ignore'))
                        self.send_image(temp_image_path)
                    elif request_type == 'd':
                        log.debug('self.path %s', self.path)
                        log.debug('request_type %s', request_type)
                        log.debug('template_id %s', template_id)
                        log.debug('image_last_path %s', image_last_path)
                        template_path = self.get_template_path(template_id)
                        temaplte_dir = os.path.dirname(template_path)
                        ui_temaplte_var_dict = self.get_ui_temaplte_var_dict(template_path)
                        search_string_font_file = os.path.join(temaplte_dir, ui_temaplte_var_dict['fonts']['search_string'])
                        search_string_font_type = 'truetype'
                        log.debug('search_string_font_file %s', search_string_font_file)
                        search_results_font_file = os.path.join(temaplte_dir, ui_temaplte_var_dict['fonts']['search_results'])
                        log.debug('search_results_font_file %s', search_results_font_file)
                        search_results_font_type = 'truetype'
                        search_type_font_file = os.path.join(temaplte_dir, ui_temaplte_var_dict['fonts']['search_type'])
                        search_type_font_type = 'truetype'
                        log.debug('search_type_font_file %s', search_type_font_file)
                        serach_params_pattern = r"""^([0-9]+)/([0-9]+)/([a-z]+)/([a-z ]+)"""
                        serach_params_match = re.match(serach_params_pattern, urllib.unquote(image_last_path),
                                                       flags=re.I)
                        log.debug(urllib.unquote(image_last_path).split('/'))
                        zp_library_id = urllib.unquote(image_last_path).split('/')[0]
                        img = Image.new('RGBA', (1920, 1080), color=(0, 0, 0, 255))
                        log.debug('zp_library_id %s', zp_library_id)
                        if zp_library_id == '1':
                            serach_bg_file_path = os.path.join(temaplte_dir,
                                                               *ui_temaplte_var_dict['film_search_bg'].split('/'))
                        else:
                            serach_bg_file_path = os.path.join(temaplte_dir,
                                                               *ui_temaplte_var_dict['tv_search_bg'].split('/'))
                        log.debug('serach_bg_file_path %s', serach_bg_file_path)
                        search_bg_image = Image.open(serach_bg_file_path)
                        img.paste(search_bg_image, (0, 0), search_bg_image.convert('RGBA'))
                        search_bg_image.close()
                        draw = ImageDraw.Draw(img)
                        #cord = (50, 180, 1290, 1020)
                        #PILWhite = (255, 255, 255)
                        #draw.rectangle(cord, fill=PILWhite)
                        # TODO: make this dynamic
                        #font_folder = '/home/anon/scripts/zerrphix_v2/zerrphix/template/film/default/'
                        #font_path = os.path.join(temaplte_dir, 'ui', 'fonts', 'AlteHaasGroteskBold.ttf')
                        font_size = ui_temaplte_var_dict['search_font_size']
                        font_width = 1500
                        font_height = 100
                        spacing = ui_temaplte_var_dict['search_font_spacing']
                        #search_type_font = ImageFont.truetype(search_type_font_file, font_size)
                        #search_results_font = ImageFont.truetype(search_results_font_file, font_size)
                        #search_string_font = ImageFont.truetype(search_string_font_file, 120)
                        if serach_params_match:
                            self.session = _Session()
                            self.session.query(TABLES.ZP_DUNE).all()
                            self.session.close()
                            ZP_USER_ID = serach_params_match.group(2)
                            zp_library_id = serach_params_match.group(1)
                            search_type = serach_params_match.group(3)
                            search_string = serach_params_match.group(4)
                            log.debug('ZP_USER_ID %s', ZP_USER_ID)
                            log.debug('zp_library_id %s', zp_library_id)
                            log.debug('search_type %s', search_type)
                            log.debug('search_string %s', search_string)
                            text_line(draw, 50, 40, " ".join(search_string), search_string_font_file,
                                      search_string_font_type, 120, 120,
                                      '#ffa500', 'left', 'top', font_width, font_height, None)
                            if zp_library_id == '1':
                                if search_type == 'a':
                                    text_line(draw, 50, 1028, 'Searching at the end', search_type_font_file,
                                              search_type_font_type, font_size, font_size,
                                              '#ffa500', 'left', 'top', font_width, font_height, None)
                                    y = 190
                                    films = self.session.query(
                                        TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID.distinct(),
                                        TABLES.ZP_FILM_TITLE.TITLE
                                    ).filter(
                                        TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID == TABLES.ZP_FILM_TITLE.ID,
                                        TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID,
                                        TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1,
                                        TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                                        TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID,
                                        TABLES.ZP_FILM_TITLE.TITLE.like(r"""%{0}%""".format(search_string))).order_by(
                                        asc(TABLES.ZP_FILM_TITLE.TITLE)).limit(14)
                                    for film in films:
                                        text_line(draw, 65, y, film.TITLE, search_results_font_file,
                                                  search_results_font_type, font_size, font_size,
                                                  '#000', 'left', 'top', font_width, font_height, None)
                                        y += font_size + spacing
                                if search_type == 'b':
                                    text_line(draw, 50, 1028, 'Searching at the end', search_type_font_file,
                                              search_type_font_type, font_size, font_size,
                                              '#ffa500', 'left', 'top', font_width, font_height, None)
                                    y = 190
                                    films = self.session.query(
                                        TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID.distinct(),
                                        TABLES.ZP_FILM_TITLE.TITLE
                                    ).filter(
                                        TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID == TABLES.ZP_FILM_TITLE.ID,
                                        TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID,
                                        TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1,
                                        TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                                        TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID,
                                        TABLES.ZP_FILM_TITLE.TITLE.like(r"""{0}%""".format(search_string))).order_by(
                                        asc(TABLES.ZP_FILM_TITLE.TITLE)).limit(14)
                                    for film in films:
                                        text_line(draw, 65, y, film.TITLE, search_results_font_file,
                                                  search_results_font_type, font_size, font_size,
                                                  '#000', 'left', 'top', font_width, font_height, None)
                                        y += font_size + spacing
                                if search_type == 'e':
                                    text_line(draw, 50, 1028, 'Searching at the end', search_type_font_file,
                                              search_type_font_type, font_size, font_size,
                                              '#ffa500', 'left', 'top', font_width, font_height, None)
                                    y = 190
                                    films = self.session.query(
                                        TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID.distinct(),
                                        TABLES.ZP_FILM_TITLE.TITLE
                                    ).filter(
                                        TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID == TABLES.ZP_FILM_TITLE.ID,
                                        TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID,
                                        TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1,
                                        TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                                        TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID,
                                        TABLES.ZP_FILM_TITLE.TITLE.like(r"""%{0}""".format(search_string))).order_by(
                                        asc(TABLES.ZP_FILM_TITLE.TITLE)).limit(14)
                                    for film in films:
                                        text_line(draw, 65, y, film.TITLE, search_results_font_file,
                                                  search_results_font_type, font_size, font_size,
                                                  '#000', 'left', 'top', font_width, font_height, None)
                                        y += font_size + spacing
                            elif zp_library_id == '2':
                                if search_type == 'a':
                                    text_line(draw, 50, 1028, 'Searching at the end', search_type_font_file,
                                              search_type_font_type, font_size, font_size,
                                              '#ffa500', 'left', 'top', font_width, font_height, None)
                                    y = 190
                                    tvs = self.session.query(
                                        TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID.distinct(),
                                        TABLES.ZP_TV_TITLE.TITLE
                                    ).filter(
                                        TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_ID == TABLES.ZP_TV_TITLE.ID,
                                        TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID,
                                        TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1,
                                        TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
                                        TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID,
                                        TABLES.ZP_TV_TITLE.TITLE.like(r"""%{0}%""".format(search_string))
                                    ).order_by(
                                        asc(TABLES.ZP_TV_TITLE.TITLE)
                                    ).limit(14)
                                    for tv in tvs:
                                        text_line(draw, 65, y, tv.TITLE, search_results_font_file,
                                                  search_results_font_type, font_size, font_size,
                                                  '#000', 'left', 'top', font_width, font_height, None)
                                        y += font_size + spacing
                                if search_type == 'b':
                                    text_line(draw, 50, 1028, 'Searching at the end', search_type_font_file,
                                              search_type_font_type, font_size, font_size,
                                              '#ffa500', 'left', 'top', font_width, font_height, None)
                                    y = 190
                                    tvs = self.session.query(
                                        TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID.distinct(),
                                        TABLES.ZP_TV_TITLE.TITLE
                                    ).filter(
                                        TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_ID == TABLES.ZP_TV_TITLE.ID,
                                        TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID,
                                        TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1,
                                        TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
                                        TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID,
                                        TABLES.ZP_TV_TITLE.TITLE.like(r"""{0}%""".format(search_string))
                                    ).order_by(
                                        asc(TABLES.ZP_TV_TITLE.TITLE)
                                    ).limit(14)
                                    for tv in tvs:
                                        text_line(draw, 65, y, tv.TITLE, search_results_font_file,
                                                  search_results_font_type, font_size, font_size,
                                                  '#000', 'left', 'top', font_width, font_height, None)
                                        y += font_size + spacing
                                if search_type == 'e':
                                    text_line(draw, 50, 1028, 'Searching at the end', search_type_font_file,
                                              search_type_font_type, font_size, font_size,
                                              '#ffa500', 'left', 'top', font_width, font_height, None)
                                    y = 200
                                    tvs = self.session.query(
                                        TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID.distinct(),
                                        TABLES.ZP_TV_TITLE.TITLE
                                    ).filter(
                                        TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_ID == TABLES.ZP_TV_TITLE.ID,
                                        TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID,
                                        TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1,
                                        TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
                                        TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID,
                                        TABLES.ZP_TV_TITLE.TITLE.like(r"""%{0}""".format(search_string))).order_by(
                                        asc(TABLES.ZP_TV_TITLE.TITLE)
                                    ).limit(14)
                                    for tv in tvs:
                                        text_line(draw, 65, y, tv.TITLE, search_results_font_file,
                                                  search_results_font_type, font_size, font_size,
                                                  '#000', 'left', 'top', font_width, font_height, None)
                                        y += font_size + spacing
                        self.send_header("Content-type", "image/png")
                        self.end_headers()
                        img.save(self.wfile, format='PNG')
                else:
                    log.critical(
                        ('image_request_url_match: {0} with image_request_url_pattern: {1} on self.path: {2}').format(
                            image_request_url_match, image_request_url_pattern, self.path))

            def send_image(self, image_path):
                if os.path.isfile(image_path):
                    try:
                        temp_image_mime = mimetypes.types_map['.{0}'.format(imghdr.what(image_path))]
                        self.send_header("Content-type", temp_image_mime)
                    except:
                        pass
                    self.end_headers()
                    with open(image_path, 'rb') as temp_image:
                        shutil.copyfileobj(temp_image, self.wfile)
                else:
                    log.critical('image_path: {0} does not exist or is not a file'.format(
                        image_path))

            def do_GET(self):
                # This is to get around mysql has gone away
                # need to find a better way of handling this
                if self.path not in ['/favicon.ico']:
                    if self.path.startswith('/m'):
                        self.dune_ui()
                    elif self.path.startswith('/i'):
                        self.image()
                    else:
                        log.critical('self.path: {0} does not start with /m or /i')
                else:
                    # keep the browsers happy
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write("""<link rel="icon" href="data:;base64,=">""".encode("utf-8"))
                self.finish()
                self.connection.close()

            def log_message(self, format, *args):
                log.info("{0} - [{1}] {2}\n".format(self.address_string(), self.log_date_time_string(), format % args))

            def process_virtual_items(self, virtual_item_ui, virtual_item_number, _replace_dict, ui_template):
                for virtual_item_parameter in virtual_item_ui:
                    if not virtual_item_parameter.startswith('@'):
                        if isinstance(virtual_item_ui[virtual_item_parameter], basestring) or virtual_item_ui[
                            virtual_item_parameter] is None:
                            if virtual_item_ui[virtual_item_parameter] is None:
                                self.wfile.write('item.{0}.{1}={2}\n'.format(
                                    virtual_item_number, virtual_item_parameter,
                                    self.sub(ui_template['ui']['default'][virtual_item_parameter],
                                             _replace_dict)).encode("utf-8"))
                            else:
                                self.wfile.write('item.{0}.{1}={2}\n'.format(
                                    virtual_item_number, virtual_item_parameter,
                                    self.sub(virtual_item_ui[virtual_item_parameter], _replace_dict)).encode("utf-8"))
                        elif isinstance(virtual_item_ui[virtual_item_parameter], dict):
                            print(virtual_item_ui[virtual_item_parameter])
                        else:
                            log.warning(('''item['ui'][virtual_item_parameter]: {0} type: {1} for'''
                                         ''' virtual_item_parameter: {2} is not basestring or dict''').format(
                                virtual_item_ui[virtual_item_parameter], type(virtual_item_ui[virtual_item_parameter]),
                                virtual_item_parameter))
                self.wfile.write('\n')
                virtual_item_number += 1
                return virtual_item_number

            def merge_two_dicts(self, x, y):
                """Given two dicts, merge them into a new dict as a shallow copy."""
                z = x.copy()
                z.update(y)
                return z

            # Single threaded http server
            # myServer = HTTPServer((hostName, hostPort), MyServer)

        # Multi threaded http server
        myServer = ThreadedHTTPServer((hostName, hostPort), MyServer)
        #print(time.asctime(), "Dune HTTP Server Starts - %s:%s" % (hostName, hostPort))

        try:
            myServer.serve_forever()
        except KeyboardInterrupt:
            pass

        myServer.server_close()
        #print(time.asctime(), "Dune HTTP Server Stops - %s:%s" % (hostName, hostPort))
