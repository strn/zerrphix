# -*- coding: utf-8 
from __future__ import unicode_literals, division, absolute_import, print_function

try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse, parse_qs
from sqlalchemy import orm, and_, func, update
import logging
from zerrphix.db.tables import TABLES
from zerrphix.db import commit, flush
from zerrphix.util.plugin import create_eapi_dict
from zerrphix.template import tempalte_icon_sub_type_list_convert
from sqlalchemy import or_
import os
import base64
import math
import bcrypt
from zerrphix.base import Base
from datetime import timedelta, datetime
from zerrphix.util.text import date_time

# https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-ii-templates
# https://stackoverflow.com/questions/10946795/render-multiple-templates-at-once-in-flask
# https://www.w3schools.com/w3css/tryw3css_templates_analytics.htm
# http://fontawesome.io/cheatsheet/
# https://github.com/jpercent/flask-control
# http://code.nabla.net/doc/jinja2/api/jinja2/jinja2.filters.html
log = logging.getLogger(__name__)


class AdminHTTPGenFuncs(Base):
    def __init__(self, Session, global_config_dict):
        args = []
        library_config_dict = {}
        super(AdminHTTPGenFuncs, self).__init__(args, Session, global_config_dict, library_config_dict)
        # logging.config.dictConfig(LOG_SETTINGS)
        self.eapi_dict = create_eapi_dict(Session)

    def get_library_evaluated_templates_dict(self, zp_user_id, library):
        zp_template_id = self.get_user_template_id(zp_user_id)
        template_xml_path = self.get_template_path(zp_template_id)
        templates_dict = self.get_templates_dict(zp_template_id, template_xml_path)
        evaluated_templates = self.get_evaluate_temapltes_dict(templates_dict)
        return evaluated_templates['library'][library]

    def get_library_render_templates_display_dict(self, zp_user_id, library, restrict_list=None):
        library_evaluated_templates_dict = self.get_library_evaluated_templates_dict(zp_user_id, library)
        return_dict = {}
        all_image_types_dict = self.get_image_type_dict_by_name()
        for image_type in library_evaluated_templates_dict:
            if image_type in all_image_types_dict:
                image_type_allowed = False
                if isinstance(restrict_list, list):
                    if image_type in restrict_list:
                        image_type_allowed = True
                else:
                    image_type_allowed = True
                if image_type_allowed is True:
                    return_dict[all_image_types_dict[image_type]] = self.create_render_template_display_dict(
                        {'template': library_evaluated_templates_dict[image_type]}, image_type
                    )
        return return_dict

    def create_render_template_display_dict(self, render_template_dict, image_type):
        return_dict = {'name': image_type}
        if isinstance(render_template_dict['template']['item'], dict):
            render_template_dict['template']['item'] = [render_template_dict['template']['item']]
        icon_sub_type_require_list, render_template_dict = tempalte_icon_sub_type_list_convert(
            render_template_dict)
        #render_template_dict['template']['icon_sub_type_require_list'] = icon_sub_type_require_list
        return_dict['icon_sub_type_list'] = {}
        for icon_sub_type in icon_sub_type_require_list:
            return_dict['icon_sub_type_list'][icon_sub_type] = {'sub_type_name':
                                                                    self.image_sub_type_dict_by_id[icon_sub_type]}
        return return_dict

    def process_pagiation(self, page, limit, total):
        last_page = int(math.ceil(total / limit))
        # deal with user change url manually
        offset = (page - 1) * limit
        return offset, last_page

    def get_eapi_list(self, zp_library_id):
        session = self.Session()
        zp_eapi_result = session.query(TABLES.ZP_EAPI).join(
            TABLES.ZP_EAPI_LIBRARY_XREF, and_(
                TABLES.ZP_EAPI.ID == TABLES.ZP_EAPI_LIBRARY_XREF.ZP_EAPI_ID,
                TABLES.ZP_EAPI_LIBRARY_XREF.ZP_LIBRARY_ID == zp_library_id
            )
        ).all()
        zp_eapi_list = []
        for zp_eapi in zp_eapi_result:
            zp_eapi_list.append({'id': zp_eapi.ID,
                                 'name': zp_eapi.NAME})
        session.close()
        return zp_eapi_list

    def get_eapi_dict(self, zp_library_id):
        session = self.Session()
        zp_eapi_result = session.query(TABLES.ZP_EAPI).join(
            TABLES.ZP_EAPI_LIBRARY_XREF, and_(
                TABLES.ZP_EAPI.ID == TABLES.ZP_EAPI_LIBRARY_XREF.ZP_EAPI_ID,
                TABLES.ZP_EAPI_LIBRARY_XREF.ZP_LIBRARY_ID == zp_library_id
            )
        ).all()
        zp_eapi_dict = {}
        for zp_eapi in zp_eapi_result:
            zp_eapi_dict[zp_eapi.ID] = zp_eapi.NAME
        session.close()
        return zp_eapi_dict

    def get_lang_name_dict(self, zp_library_id):
        session = self.Session()
        zp_eapi_result = session.query(TABLES.ZP_LANG).join(
            TABLES.ZP_USER_LIBRARY_LANG, and_(
                TABLES.ZP_LANG.ID == TABLES.ZP_USER_LIBRARY_LANG.ZP_LANG_ID,
                TABLES.ZP_USER_LIBRARY_LANG.ZP_LIBRARY_ID == zp_library_id
            )
        ).all()
        zp_lang_name_dict = {1823: 'English'}
        for zp_eapi in zp_eapi_result:
            zp_lang_name_dict[zp_eapi.ID] = zp_eapi.Ref_Name
        session.close()
        return zp_lang_name_dict

    def get_file_extensions(self):
        session = self.Session()
        zp_file_extension_result = session.query(TABLES.ZP_FILE_EXTENSION).all()
        zp_file_extension_list = []
        for zp_file_extension in zp_file_extension_result:
            zp_file_extension_list.append({'zp_file_extension_id': zp_file_extension.ID,
                                           'extension': zp_file_extension.EXTENSION})
        session.close()
        return zp_file_extension_list

    def get_library_file_extensions(self, zp_library_id):
        session = self.Session()
        zp_file_extension_result = session.query(TABLES.ZP_LIBRARY_FILE_EXTENSION).filter(
            TABLES.ZP_LIBRARY_FILE_EXTENSION.ZP_LIBRARY_ID == zp_library_id
        ).all()
        zp_file_extension_dict = {}
        for zp_file_extension in zp_file_extension_result:
            zp_file_extension_dict[zp_file_extension.ZP_FILE_EXTENSION_ID] = zp_file_extension.IGNORE_EXTENSION
        session.close()
        return zp_file_extension_dict

    def set_library_file_extensions(self, zp_library_id, file_extension_set_dict):
        session = self.Session()
        session.query(
            TABLES.ZP_LIBRARY_FILE_EXTENSION
        ).filter(
            TABLES.ZP_LIBRARY_FILE_EXTENSION.ZP_LIBRARY_ID == zp_library_id
        ).delete()
        flush(session)
        for zp_file_extension in file_extension_set_dict:
            add_zp_library_film_extension = TABLES.ZP_LIBRARY_FILE_EXTENSION(
                ZP_LIBRARY_ID=zp_library_id,
                ZP_FILE_EXTENSION_ID=zp_file_extension,
                IGNORE_EXTENSION=file_extension_set_dict[zp_file_extension]
            )
            session.add(add_zp_library_film_extension)
            flush(session)
        commit(session)
        session.close()

    def add_file_extensions(self, extension):
        session = self.Session()
        add_zp_file_extensions = TABLES.ZP_FILE_EXTENSION(EXTENSION=extension)
        session.add(add_zp_file_extensions)
        commit(session)
        session.close()

    def set_file_extensions(self, zp_file_extension_id, extension):
        session = self.Session()
        session.query(TABLES.ZP_FILE_EXTENSION).filter(TABLES.ZP_FILE_EXTENSION.ID == zp_file_extension_id).update(
            {"EXTENSION": extension})
        commit(session)
        session.close()

    def get_allowed_extensions_string(self, zp_library_id, ignored_only=0):
        session = self.Session()
        allowed_extensions = ''
        allowed_extensions_result = session.query(
            TABLES.ZP_FILE_EXTENSION
        ).join(
            TABLES.ZP_LIBRARY_FILE_EXTENSION,
            TABLES.ZP_LIBRARY_FILE_EXTENSION.ZP_FILE_EXTENSION_ID == TABLES.ZP_FILE_EXTENSION.ID
        ).filter(
            TABLES.ZP_LIBRARY_FILE_EXTENSION.ZP_LIBRARY_ID == zp_library_id,
            TABLES.ZP_LIBRARY_FILE_EXTENSION.IGNORE_EXTENSION == ignored_only
        ).all()
        session.close()
        for allowed_extension in allowed_extensions_result:
            allowed_extensions += '%s, ' % allowed_extension.EXTENSION
        allowed_extensions = allowed_extensions.strip(' ,')
        return allowed_extensions

    def get_total_invalid_filefolders(self, zp_library_id):
        session = self.Session()
        rslt_invalid_filefolder_count = session.query(
            TABLES.ZP_INVALID_FILEFOLDER
        ).filter(
            TABLES.ZP_INVALID_FILEFOLDER.ZP_SCAN_PATH_ID == TABLES.ZP_SCAN_PATH.ID,
            TABLES.ZP_INVALID_FILEFOLDER.ZP_LIBRARY_ID == zp_library_id,
            TABLES.ZP_INVALID_FILEFOLDER.LAST_OCCURANCE_DATETIME > TABLES.ZP_SCAN_PATH.LAST_SCAN_DATETIME
        ).count()
        session.close()
        #).order_by(TABLES.ZP_INVALID_FILEFOLDER.ZP_SCAN_PATH_ID.asc()).limit(limit).offset(offset)
        return rslt_invalid_filefolder_count

    def zp_scan_path_string(self, zp_scan_path_id):
        session = self.Session()
        try:
            rslt_scan_path = session.query(
                TABLES.ZP_SCAN_PATH.PATH,
                TABLES.ZP_SCAN_PATH.ZP_SCAN_PATH_FS_TYPE_ID,
                TABLES.ZP_SHARE.SHARE_NAME,
                TABLES.ZP_SHARE_SERVER.REMOTE_NAME,
                TABLES.ZP_SHARE_SERVER.HOSTNAME,
                TABLES.ZP_SHARE_SERVER.PORT,
                TABLES.ZP_SHARE_CREDENTIAL.USERNAME
            ).outerjoin(
                TABLES.ZP_SCAN_PATH_SHARE_XREF, TABLES.ZP_SCAN_PATH.ID == TABLES.ZP_SCAN_PATH_SHARE_XREF.ZP_SCAN_PATH_ID
            ).outerjoin(
                TABLES.ZP_SHARE, TABLES.ZP_SHARE.ID == TABLES.ZP_SCAN_PATH_SHARE_XREF.ZP_SHARE_ID
            ).outerjoin(
                TABLES.ZP_SHARE_SERVER,
                TABLES.ZP_SHARE_SERVER.ID == TABLES.ZP_SCAN_PATH_SHARE_XREF.ZP_SHARE_SERVER_ID
            ).outerjoin(
                TABLES.ZP_SHARE_CREDENTIAL,
                TABLES.ZP_SHARE_CREDENTIAL.ID == TABLES.ZP_SCAN_PATH_SHARE_XREF.ZP_SHARE_CREDENTIAL_ID
            ).filter(
                TABLES.ZP_SCAN_PATH.ID == zp_scan_path_id
            ).one()
        except orm.exc.NoResultFound:
            path = ''
        else:
            if rslt_scan_path.ZP_SCAN_PATH_FS_TYPE_ID == 1:
                path = rslt_scan_path.PATH
            else:
                path = 'smb://%s@%s[%s]:%s/%s/%s' % (rslt_scan_path.USERNAME,
                                   rslt_scan_path.HOSTNAME,
                                   rslt_scan_path.REMOTE_NAME,
                                   rslt_scan_path.PORT,
                                   rslt_scan_path.SHARE_NAME,
                                   rslt_scan_path.PATH)
        return path

    def set_process_force_run(self, zp_process_id):
        session = self.Session()
        session.query(TABLES.ZP_PROCESS_RUN).filter(TABLES.ZP_PROCESS_RUN.ZP_PROCESS_ID == zp_process_id).update(
            {"FORCE_RUN": 1,
             "FORCE_RUN_REQUEST_DATE_TIME": date_time()})
        commit(session)
        session.close()

    def get_invalid_filefolders(self, zp_library_id, limit=50, offset=1):
        return_list = []
        session = self.Session()
        zp_invalid_filefolder = session.query(
            TABLES.ZP_INVALID_FILEFOLDER,
            TABLES.ZP_INVALID_FILEFOLDER_SOURCE
        ).filter(
            TABLES.ZP_INVALID_FILEFOLDER.ZP_SCAN_PATH_ID == TABLES.ZP_SCAN_PATH.ID,
            TABLES.ZP_INVALID_FILEFOLDER.ZP_LIBRARY_ID == zp_library_id,
            TABLES.ZP_INVALID_FILEFOLDER.LAST_OCCURANCE_DATETIME > TABLES.ZP_SCAN_PATH.LAST_SCAN_DATETIME,
            TABLES.ZP_INVALID_FILEFOLDER_SOURCE.ID == TABLES.ZP_INVALID_FILEFOLDER.SOURCE_ID
        ).order_by(
            TABLES.ZP_INVALID_FILEFOLDER.ZP_SCAN_PATH_ID.asc()
        ).limit(limit).offset(offset)
        session.close()
        for invalid_filefolder in zp_invalid_filefolder:
            return_list.append({'id': invalid_filefolder.ZP_INVALID_FILEFOLDER.ID,
                                'source': invalid_filefolder.ZP_INVALID_FILEFOLDER.SOURCE_ID,
                                'scan_path_json': invalid_filefolder.ZP_INVALID_FILEFOLDER.SCAN_PATH_JSON,
                                'added': invalid_filefolder.ZP_INVALID_FILEFOLDER.ADDED_DATETIME,
                                'last_ocurrance': invalid_filefolder.ZP_INVALID_FILEFOLDER.LAST_OCCURANCE_DATETIME,
                                'path': invalid_filefolder.ZP_INVALID_FILEFOLDER.PATH,
                                'path_extra': invalid_filefolder.ZP_INVALID_FILEFOLDER.PATH_EXTRA,
                                'reason': invalid_filefolder.ZP_INVALID_FILEFOLDER.REASON
                                })
        return return_list

    def veryify_uanme_pass(self, username, password):
        valid_uname_pass = False
        session = self.Session()
        try:
            zp_user = session.query(TABLES.ZP_USER).filter(
                TABLES.ZP_USER.USERNAME == username,
                #TABLES.ZP_USER.ENABLED == 1
            ).one()
        except orm.exc.NoResultFound:
            pass
        else:
            db_pass_hashed = zp_user.PASSWORD
            if bcrypt.checkpw(password.encode('utf8'), db_pass_hashed.encode('utf8')) is True:
                valid_uname_pass = zp_user.ID
        session.close()
        return valid_uname_pass

    def get_user_dict(self):
        session = self.Session()
        return_dict = {}
        users = session.query(
            TABLES.ZP_USER.USERNAME,
            TABLES.ZP_USER.ENABLED,
            TABLES.ZP_USER.ID,
            TABLES.ZP_USER_TEMPLATE_XREF.ZP_TEMPLATE_ID,
            TABLES.ZP_USER_LIBRARY_LANG.ZP_LANG_ID
        ).outerjoin(
            TABLES.ZP_USER_LIBRARY_LANG, and_(
                TABLES.ZP_USER_LIBRARY_LANG.ZP_USER_ID == \
                TABLES.ZP_USER.ID,
                TABLES.ZP_USER_LIBRARY_LANG.ZP_LIBRARY_ID == 1
            )
        ).outerjoin(
            TABLES.ZP_USER_TEMPLATE_XREF, TABLES.ZP_USER_TEMPLATE_XREF.ZP_USER_ID == \
            TABLES.ZP_USER.ID
        ).all()
        session.close()
        for user in users:
            return_dict[user.ID] = {'username': user.USERNAME,
                                'enabled': user.ENABLED,
                                'id': user.ID,
                                'template': user.ZP_TEMPLATE_ID if user.ZP_TEMPLATE_ID > 0 else 0,
                                'lang': user.ZP_LANG_ID}
        return return_dict

    def update_user(self, zp_user_id, password, zp_temaplte_id, zp_lang_id):
        session = self.Session()
        if password:
            session.query(TABLES.ZP_USER).filter(TABLES.ZP_USER.ID == zp_user_id).update(
                {"PASSWORD": bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())}
            )
            commit(session)
        if zp_temaplte_id:
            session.query(TABLES.ZP_USER_TEMPLATE_XREF).filter(TABLES.ZP_USER_TEMPLATE_XREF.ZP_USER_ID == zp_user_id).update(
                {"ZP_TEMPLATE_ID": zp_temaplte_id}
            )
        if zp_lang_id:
            session.query(TABLES.ZP_USER_LIBRARY_LANG).filter(TABLES.ZP_USER_LIBRARY_LANG.ZP_USER_ID == zp_user_id).update(
                {"ZP_LANG_ID": zp_lang_id}
            )
        commit(session)
        session.close()
        if zp_lang_id or zp_temaplte_id:
            return True
        return False

    def clear_template_renders(self, zp_template_id):
        session = self.Session()
        users = session.query(TABLES.ZP_USER_TEMPLATE_XREF).filter(
            TABLES.ZP_USER_TEMPLATE_XREF.ZP_TEMPLATE_ID == zp_template_id
        ).all()
        session.close()
        #for user in users:
            #self.clear_user_renders(user.ZP_USER_ID)

    def clear_user_renders(self, zp_user_id):
        # todo move this to a seperate thread i.e. not run via the ui action
        session = self.Session()
        min_film_collection_date_time = session.query(func.min(TABLES.ZP_FILM_COLLECTION.LAST_EDIT_DATETIME)).one()[0]
        log.debug('min_film_collection_date_time %s type %s', min_film_collection_date_time,
                  type(min_film_collection_date_time))
        if isinstance(min_film_collection_date_time, datetime):
            #session.execute(update(TABLES.ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF).where(
            #    TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH_ID == \
            #    TABLES.ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH_ID,
            #    TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == zp_user_id
            #).values(
            #    RENDER_DATETIME=(min_film_collection_date_time - timedelta(days=1)
            #                              ).strftime("%Y-%m-%d %H:%M:%S")
            #))
            session.query(
                TABLES.ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF
            ).filter(
                TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH_ID == \
                TABLES.ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH_ID,
                TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == zp_user_id
            ).update({TABLES.ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.RENDER_DATETIME:
                                      (min_film_collection_date_time - timedelta(days=1)
                                          ).strftime("%Y-%m-%d %H:%M:%S")},
                     synchronize_session=False)
            commit(session)
        min_film_date_time = session.query(func.min(TABLES.ZP_FILM.LAST_EDIT_DATETIME)).one()[0]
        log.debug('min_film_date_time %s type %s', min_film_date_time,
                  type(min_film_date_time))
        if isinstance(min_film_date_time, datetime):
            session.query(
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF
            ).filter(
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID == \
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID,
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == zp_user_id
            ).update({TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.RENDER_DATETIME:
                                      (min_film_date_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")},
                     synchronize_session=False)
            commit(session)
        min_tv_date_time = session.query(func.min(TABLES.ZP_TV.LAST_EDIT_DATETIME)).one()[0]
        log.debug('min_tv_date_time %s type %s', min_tv_date_time,
                  type(min_tv_date_time))
        if isinstance(min_tv_date_time, datetime):
            session.query(
                TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF
            ).filter(
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID == \
                TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID,
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == zp_user_id
            ).update({TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.RENDER_DATETIME:
            (min_tv_date_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")},
                     synchronize_session=False)
            commit(session)
        min_tv_episode_date_time = session.query(func.min(TABLES.ZP_TV_EPISODE.LAST_EDIT_DATETIME)).one()[0]
        log.debug('min_tv_episode_date_time %s type %s', min_tv_episode_date_time,
                  type(min_tv_episode_date_time))
        if isinstance(min_tv_episode_date_time, datetime):
            session.query(
                TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF
            ).filter(
                TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID == \
                TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID,
                TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == zp_user_id
            ).update({TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.RENDER_DATETIME:
                                      (min_tv_episode_date_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")},
                     synchronize_session=False)
            commit(session)
        #session.query(
        #    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF
        #).filter(
        #    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == zp_user_id
        #).delete(synchronize_session='fetch')
        #commit(session)
        #session.query(
        #    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF
        #).filter(
        #    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == zp_user_id
        #).delete(synchronize_session='fetch')
        #commit(session)
        #session.query(
        #    TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF
        #).filter(
        #    TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == zp_user_id
        #).delete(synchronize_session='fetch')
        #commit(session)
        #session.query(
        #    TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF
        #).filter(
        #    TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == zp_user_id
        #).delete(synchronize_session='fetch')
        #commit(session)
        #session.query(
        #    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF
        #).filter(
        #    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == zp_user_id
        #).delete(synchronize_session='fetch')
        #commit(session)
        #session.query(
        #    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF
        #).filter(
        #    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == zp_user_id
        #).delete(synchronize_session='fetch')
        #commit(session)
        #session.query(
        #    TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF
        #).filter(
        #    TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == zp_user_id
        #).delete(synchronize_session='fetch')
        #commit(session)
        session.close()

    def add_user(self, username, password, zp_template_id, zp_lang_id):
        session = self.Session()
        try:
            session.query(TABLES.ZP_USER).filter(
                TABLES.ZP_USER.USERNAME == username
            ).one()
        except orm.exc.NoResultFound:
            add_zp_user = TABLES.ZP_USER(
                USERNAME = username,
                PASSWORD = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()),
                ENABLED = 1,
                LAST_EDIT_DATETIME = date_time()
            )
            session.add(add_zp_user)
            # we need to flush here to get the id for the new user entry/row
            flush(session)
            add_zp_user_temaplte_xref = TABLES.ZP_USER_TEMPLATE_XREF(
                ZP_USER_ID = add_zp_user.ID,
                ZP_TEMPLATE_ID = zp_template_id
            )
            session.add(add_zp_user_temaplte_xref)
            add_zp_user_library_lang_film = TABLES.ZP_USER_LIBRARY_LANG(
                ZP_USER_ID = add_zp_user.ID,
                ZP_LANG_ID = zp_lang_id,
                ZP_LIBRARY_ID = 1
            )
            session.add(add_zp_user_library_lang_film)
            add_zp_user_library_lang_tv = TABLES.ZP_USER_LIBRARY_LANG(
                ZP_USER_ID = add_zp_user.ID,
                ZP_LANG_ID = zp_lang_id,
                ZP_LIBRARY_ID = 2
            )
            session.add(add_zp_user_library_lang_tv)
            commit(session)
        session.close()


    def get_templates_info_dict(self):
        session = self.Session()
        return_dict = {}
        temapltes = session.query(TABLES.ZP_TEMPLATE).all()
        session.close()
        for template in temapltes:
            return_dict[template.ID] = {'ref_name': template.REF_NAME,
                                        'path_type': template.PATH_TYPE,
                                        'path': template.PATH,
                                        'zip_file': None}
        return return_dict

    def get_template_dict(self, zp_template_id):
        session = self.Session()
        template = session.query(
            TABLES.ZP_TEMPLATE
        ).filter(
            TABLES.ZP_TEMPLATE.ID == zp_template_id
        ).one()
        session.close()
        return_dict = {'ref_name': template.REF_NAME,
                      'path_type': template.PATH_TYPE,
                      'path': template.PATH,
                      'zip_file': None}
        return return_dict

    def get_template_list(self):
        session = self.Session()
        return_list = []
        temapltes = session.query(TABLES.ZP_TEMPLATE).all()
        session.close()
        for template in temapltes:
            return_list.append({'id': template.ID,
                                'ref_name': template.REF_NAME,
                                'path_type': template.PATH_TYPE})
        return return_list

    def get_user_template_id(self, zp_user_id):
        session = self.Session()
        zp_template_id = session.query(
            TABLES.ZP_USER_TEMPLATE_XREF
        ).filter(
            TABLES.ZP_USER_TEMPLATE_XREF.ZP_USER_ID == zp_user_id
        ).one().ZP_TEMPLATE_ID
        return zp_template_id

    def genre_by_name(self):
        session = self.Session()
        genre_dict = {}
        genres = session.query(TABLES.ZP_GENRE).all()
        session.close()
        for genre in genres:
            genre_dict[genre.GENRE] = genre.ID
        return genre_dict

    def genre_by_id(self):
        session = self.Session()
        genre_dict = {}
        genres = session.query(TABLES.ZP_GENRE).all()
        session.close()
        for genre in genres:
            genre_dict[genre.ID] = genre.GENRE
        return genre_dict

