import logging
import re

from sqlalchemy import case
from sqlalchemy import func
# from PIL import Image
from sqlalchemy import orm, and_

from zerrphix.db import commit
from zerrphix.db import flush
from zerrphix.db.tables import TABLES
from zerrphix.film.util import update_film_last_mod
from zerrphix.util.plugin import create_eapi_dict
from zerrphix.util.text import date_time
import os

log = logging.getLogger(__name__)


class AdminHTTPFilmFuncs(object):
    def __init__(self, Session, global_config_dict):
        # logging.config.dictConfig(LOG_SETTINGS)
        self.Session = Session
        self.global_config_dict = global_config_dict
        self.eapi_dict = create_eapi_dict(Session)
        self.image_type_id_dict = {'poster': 1, 'backdrop': 2}
        self.image_film_entity_type_id_dict = {'poster': 3, 'backdrop': 4}

    def check_zp_film_id_exists(self, zp_film_id):
        session = self.Session()
        try:
            session.query(TABLES.ZP_FILM).filter(TABLES.ZP_FILM.ID == zp_film_id).one()
        except orm.exc.NoResultFound:
            film_exists = False
        else:
            film_exists = True
        session.close()
        return film_exists

    def get_filfolder_from_film(self, zp_film_id):
        session = self.Session()
        try:
            zp_film = session.query(TABLES.ZP_FILM).filter(TABLES.ZP_FILM.ID == zp_film_id).one()
        except orm.exc.NoResultFound:
            zp_filefolder_id = None
        else:
            zp_filefolder_id = zp_film.ZP_FILM_FILEFOLDER_ID
        session.close()
        return zp_filefolder_id

    def film_rendered_image(self, zp_film_id, image_type_id, zp_icon_sub_type_id, zp_user_id):
        session = self.Session()
        rendered_image_id = None
        try:
            rendered_image_id = session.query(
                TABLES.ZP_FILM_IMAGE_RENDER_HASH
            ).join(
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF,
                and_(
                    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID ==
                    TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID,
                    TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE ==
                    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_IMAGE_SUB_TYPE,
                    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID ==
                    TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID,
                    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID ==
                    TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID,
                    TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID ==
                    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID
                )
            ).filter(
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID == image_type_id,
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID == zp_film_id,
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE == zp_icon_sub_type_id
            ).one().ID
        except orm.exc.NoResultFound:
            log.warning('could not find entry in ZP_FILM_IMAGE_RENDER_HASH for zp_user_id %s, zp_film_id %s,'
                      ' image_type_id %s, zp_icon_sub_type_id %s', zp_user_id, zp_film_id, image_type_id,
                        zp_icon_sub_type_id)
        session.close()
        return rendered_image_id

    def film_raw_image_list(self, zp_film_id, image_type_id):
        session = self.Session()
        raw_image_list = []
        try:
            raw_images = session.query(TABLES.ZP_FILM_RAW_IMAGE).filter(
                TABLES.ZP_FILM_RAW_IMAGE.ZP_ENTITY_ID == zp_film_id,
                TABLES.ZP_FILM_RAW_IMAGE.ZP_ENTITY_TYPE_ID == image_type_id
            ).order_by(TABLES.ZP_FILM_RAW_IMAGE.ZP_EAPI_ID.asc(),
                       TABLES.ZP_FILM_RAW_IMAGE.ZP_USER_ID.asc()).all()
        except orm.exc.NoResultFound:
            log.debug('no images for zp_film_id %s, image_type_id %s found in ZP_FILM_RAW_IMAGE',
                      zp_film_id, image_type_id)
        else:
            for raw_image in raw_images:
                raw_image_list.append({'image_url': '/i/raw/film/%s' % (raw_image.ID),
                                       'source_type': 'eapi' if raw_image.ZP_EAPI_ID > 0 else 'user',
                                       'zp_eapi_id': raw_image.ZP_EAPI_ID,
                                       'zp_film_raw_image_id': raw_image.ID})
        log.debug(raw_image_list)
        session.close()
        return raw_image_list

    def get_film_raw_image_filename(self, zp_film_raw_image_id):
        session = self.Session()
        raw_image_filename = None
        zp_film_id = None
        try:
            zp_film_raw_image = session.query(TABLES.ZP_FILM_RAW_IMAGE).filter(
                TABLES.ZP_FILM_RAW_IMAGE.ID == zp_film_raw_image_id).one()
        except orm.exc.NoResultFound:
            log.error('no entry for zp_film_raw_image_id %s, ZP_FILM_RAW_IMAGE',
                      zp_film_raw_image_id)
        else:
            raw_image_filename = zp_film_raw_image.FILENAME
            zp_film_id = zp_film_raw_image.ZP_ENTITY_ID
        session.close()
        return raw_image_filename, zp_film_id

    def get_film_rendered_image_filename(self, zp_film_rendered_image_id):
        session = self.Session()
        rendered_image_filename = None
        zp_film_id = None
        template_name = None
        image_type_by_id_dict = {1: 'icon', 2: 'synopsis', 3: 'poster', 4:'backdrop'}
        image_sub_type_by_id_dict = {1: '',
                                     2: '_sel',
                                     3: '_watched',
                                     4: '_watched_sel'}
        try:
            zp_film_rendered_image = session.query(
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID,
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID,
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.HASH,
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.EXT,
                TABLES.ZP_TEMPLATE.REF_NAME
            ).join(
                TABLES.ZP_TEMPLATE, TABLES.ZP_TEMPLATE.ID == TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID
            ).join(
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF,
                and_(
                    TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID ==
                    TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID,
                    TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == 1
                )
            ).filter(
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID == zp_film_rendered_image_id
            ).one()
        except orm.exc.NoResultFound:
            log.error('no entry for zp_film_rendered_image_id %s, ZP_FILM_IMAGE_RENDER_HASH',
                      zp_film_rendered_image_id)
        else:
            rendered_image_filename = '.%s%s.%s.%s' % (
            image_type_by_id_dict[zp_film_rendered_image.ZP_FILM_IMAGE_TYPE_ID],
            image_sub_type_by_id_dict[zp_film_rendered_image.ZP_IMAGE_SUB_TYPE],
            zp_film_rendered_image.HASH,
            zp_film_rendered_image.EXT
            )
            zp_film_id = zp_film_rendered_image.ZP_FILM_ID
            template_name = zp_film_rendered_image.REF_NAME
        session.close()
        return rendered_image_filename, template_name, zp_film_id

    def add_new_film_raw_image(self, zp_film_id, zp_user_id, zp_entity_type_id, new_film_image_filename,
                               image_reference):
        session = self.Session()
        add_zp_film_raw_image = TABLES.ZP_FILM_RAW_IMAGE(ZP_EAPI_ID=0,
                                                         ZP_EAPI_IMAGE_REF=image_reference,
                                                         ZP_ENTITY_TYPE_ID=zp_entity_type_id,
                                                         ZP_ENTITY_ID=zp_film_id,
                                                         ZP_USER_ID=zp_user_id,
                                                         FILENAME=new_film_image_filename)
        session.add(add_zp_film_raw_image)
        commit(session)
        session.close()
        return True

    def film_list(self, limit=50, offset=0, sort_type='alpha', search=None):
        film_list = []
        session = self.Session()
        if search:
            films = session.query(TABLES.ZP_FILM.ID,
                                  TABLES.ZP_FILM_TITLE.TITLE).join(
                TABLES.ZP_FILM_TITLE, TABLES.ZP_FILM_TITLE.ID == session.query(TABLES.ZP_FILM_TITLE.ID).filter(
                    TABLES.ZP_FILM_TITLE.ZP_FILM_ID == TABLES.ZP_FILM.ID).limit(1).correlate(TABLES.ZP_FILM)
            ).filter(
                TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID != None,
                TABLES.ZP_FILM_TITLE.TITLE.like('%%%s%%' % search)
            ).order_by(TABLES.ZP_FILM_TITLE.TITLE.asc()).limit(limit).offset(offset)
        elif sort_type == 'added_desc':
            films = session.query(TABLES.ZP_FILM.ID,
                                  TABLES.ZP_FILM_TITLE.TITLE).join(
                TABLES.ZP_FILM_TITLE, TABLES.ZP_FILM_TITLE.ID == session.query(TABLES.ZP_FILM_TITLE.ID).filter(
                    TABLES.ZP_FILM_TITLE.ZP_FILM_ID == TABLES.ZP_FILM.ID).limit(1).correlate(TABLES.ZP_FILM)
            ).filter(
                TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID != None
            ).order_by(TABLES.ZP_FILM.ADDED_DATE_TIME.desc()).limit(limit).offset(offset)
        elif sort_type == 'added_asc':
            films = session.query(TABLES.ZP_FILM.ID,
                                  TABLES.ZP_FILM_TITLE.TITLE).join(
                TABLES.ZP_FILM_TITLE, TABLES.ZP_FILM_TITLE.ID == session.query(TABLES.ZP_FILM_TITLE.ID).filter(
                    TABLES.ZP_FILM_TITLE.ZP_FILM_ID == TABLES.ZP_FILM.ID).limit(1).correlate(TABLES.ZP_FILM)
            ).filter(
                TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID != None
            ).order_by(TABLES.ZP_FILM.ADDED_DATE_TIME.asc()).limit(limit).offset(offset)
        elif sort_type == 'alpha_desc':
            films = session.query(TABLES.ZP_FILM.ID,
                                  TABLES.ZP_FILM_TITLE.TITLE).join(
                TABLES.ZP_FILM_TITLE, TABLES.ZP_FILM_TITLE.ID == session.query(TABLES.ZP_FILM_TITLE.ID).filter(
                    TABLES.ZP_FILM_TITLE.ZP_FILM_ID == TABLES.ZP_FILM.ID).limit(1).correlate(TABLES.ZP_FILM)
            ).filter(
                TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID != None
            ).order_by(TABLES.ZP_FILM_TITLE.TITLE.desc()).limit(limit).offset(offset)
        else:
            films = session.query(TABLES.ZP_FILM.ID,
                                  TABLES.ZP_FILM_TITLE.TITLE).join(
                TABLES.ZP_FILM_TITLE, TABLES.ZP_FILM_TITLE.ID == session.query(TABLES.ZP_FILM_TITLE.ID).filter(
                    TABLES.ZP_FILM_TITLE.ZP_FILM_ID == TABLES.ZP_FILM.ID).limit(1).correlate(TABLES.ZP_FILM)
            ).filter(
                TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID != None
            ).order_by(TABLES.ZP_FILM_TITLE.TITLE.asc()).limit(limit).offset(offset)

        for film in films:
            film_list.append({'title': film.TITLE,
                              'id': film.ID})
        session.close()
        return film_list

    def film_overview(self, zp_film_id, zp_user_id):
        session = self.Session()
        try:
            film_overview = session.query(TABLES.ZP_FILM_OVERVIEW).filter(
                TABLES.ZP_FILM_OVERVIEW.ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == zp_film_id,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 2).one().OVERVIEW
        except orm.exc.NoResultFound:
            film_overview = 'No Overview Found or User Specifics is yet to run'
        session.close()
        return film_overview

    def film_title(self, zp_film_id, zp_user_id, strict=False):
        session = self.Session()
        try:
            film_title = session.query(TABLES.ZP_FILM_TITLE).filter(
                TABLES.ZP_FILM_TITLE.ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == zp_film_id,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1).one().TITLE
        except orm.exc.NoResultFound:
            # if there is not a title for a user but one exists we should try and use one
            # to show on the admin web interface to show which film is being edited
            if strict is True:
                film_title = 'No Title Found or User Specifics is yet to run'
            else:
                try:
                    film_title = session.query(TABLES.ZP_FILM_TITLE).filter(
                        TABLES.ZP_FILM_TITLE.ZP_FILM_ID == zp_film_id).limit(1).one().TITLE
                except orm.exc.NoResultFound:
                    film_title = 'No Title Found or User Specifics is yet to run'
        session.close()
        return film_title

    def get_user_film_raw_image_id(self, zp_film_id, zp_film_entity_type_id, zp_user_id):
        session = self.Session()
        zp_film_raw_image_id = None
        try:
            zp_film_raw_image_id = session.query(TABLES.ZP_USER_FILM_ENTITY_XREF).filter(
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == zp_film_id,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == zp_film_entity_type_id).one(
            ).ZP_FILM_ENTITY_ID
        except orm.exc.NoResultFound:
            log.debug('no result found for zp_film_id %s, zp_user_id %s, zp_film_entity_type_id %s',
                      zp_film_id, zp_user_id, zp_film_entity_type_id)
        session.close()
        return zp_film_raw_image_id

    def film_title_list(self, zp_film_id, zp_user_id):
        session = self.Session()
        film_title_dict = {}
        main_default_present = False
        lang_default_present = False
        user_override = False
        id_inc = 1
        try:
            zp_film_title = session.query(TABLES.ZP_FILM_TITLE).filter(
                TABLES.ZP_FILM_TITLE.ZP_FILM_ID == zp_film_id).order_by(
                TABLES.ZP_FILM_TITLE.ZP_EAPI_ID.asc(), TABLES.ZP_FILM_TITLE.ZP_FILM_TITLE_TYPE_ID.asc(),
                TABLES.ZP_FILM_TITLE.ZP_LANG_ID.desc()
            ).all()
        except orm.exc.NoResultFound:
            film_title_dict = None
        else:
            for film_title in zp_film_title:
                zp_eapi_id = film_title.ZP_EAPI_ID
                zp_lang_id = film_title.ZP_LANG_ID
                zp_film_title_type_id = film_title.ZP_FILM_TITLE_TYPE_ID
                zp_film_title_id = film_title.ID
                title = film_title.TITLE
                main_default = film_title.MAIN_DEFAULT
                lang_default = film_title.LANG_DEFAULT
                zp_film_title_user_id = film_title.ZP_USER_ID
                if main_default == 1:
                    main_default_present = True
                if lang_default == 1:
                    lang_default_present = True
                if zp_film_title_user_id == zp_user_id:
                    user_override = True
                if zp_eapi_id not in film_title_dict:
                    film_title_dict[zp_eapi_id] = {'titles': []}
                log.debug('zp_film_title_user_id %s type %s and zp_user_id %s type %s, user_override %s',
                          zp_film_title_user_id, type(zp_film_title_user_id), zp_user_id,
                          type(zp_user_id), user_override)
                film_title_dict[zp_eapi_id]['titles'].append({'zp_film_title_id': zp_film_title_id,
                                                              'zp_lang_id': zp_lang_id,
                                                              'zp_film_title_type_id': zp_film_title_type_id,
                                                              'title': title,
                                                              'main_default': main_default,
                                                              'lang_default': lang_default,
                                                              'zp_user_id': zp_film_title_user_id,
                                                              'id_inc': id_inc})
                id_inc += 1
        if main_default_present is False:
            if 0 not in film_title_dict:
                film_title_dict[0] = {'titles': []}
            film_title_dict[0]['titles'].append({'zp_film_title_id': None,
                                                 'zp_lang_id': None,
                                                 'zp_film_title_type_id': None,
                                                 'title': '',
                                                 'main_default': 1,
                                                 'lang_default': None,
                                                 'zp_user_id': None,
                                                 'id_inc': id_inc})
            id_inc += 1
        if lang_default_present is False:
            if 0 not in film_title_dict:
                film_title_dict[0] = {'titles': []}
            film_title_dict[0]['titles'].append({'zp_film_title_id': None,
                                                 'zp_lang_id': None,
                                                 'zp_film_title_type_id': None,
                                                 'title': '',
                                                 'main_default': None,
                                                 'lang_default': 1,
                                                 'zp_user_id': None,
                                                 'id_inc': id_inc})
            id_inc += 1
        if user_override is False:
            if 0 not in film_title_dict:
                film_title_dict[0] = {'titles': []}
            film_title_dict[0]['titles'].append({'zp_film_title_id': None,
                                                 'zp_lang_id': None,
                                                 'zp_film_title_type_id': None,
                                                 'title': '',
                                                 'main_default': None,
                                                 'lang_default': None,
                                                 'zp_user_id': zp_user_id,
                                                 'id_inc': id_inc})
            id_inc += 1
        session.close()
        return film_title_dict

    def film_overview_list(self, zp_film_id, zp_user_id):
        session = self.Session()
        film_overview_text = None
        film_overview_dict = {}
        main_default_present = False
        lang_default_present = False
        user_override = False
        id_inc = 1
        try:
            zp_film_overview = session.query(TABLES.ZP_FILM_OVERVIEW).filter(
                TABLES.ZP_FILM_OVERVIEW.ZP_FILM_ID == zp_film_id).order_by(
                TABLES.ZP_FILM_OVERVIEW.ZP_EAPI_ID.asc(),
                TABLES.ZP_FILM_OVERVIEW.ZP_LANG_ID.desc()
            ).all()
        except orm.exc.NoResultFound:
            film_overview_dict = None
        else:
            for film_overview in zp_film_overview:
                zp_eapi_id = film_overview.ZP_EAPI_ID
                zp_lang_id = film_overview.ZP_LANG_ID
                zp_film_overview_id = film_overview.ID
                overview = film_overview.OVERVIEW
                main_default = film_overview.MAIN_DEFAULT
                lang_default = film_overview.LANG_DEFAULT
                zp_film_overview_user_id = film_overview.ZP_USER_ID
                if main_default == 1:
                    main_default_present = True
                if lang_default == 1:
                    lang_default_present = True
                if zp_film_overview_user_id == zp_user_id:
                    user_override = True
                if zp_eapi_id not in film_overview_dict:
                    film_overview_dict[zp_eapi_id] = {'overviews': []}
                log.debug('zp_film_overview_user_id %s type %s and zp_user_id %s type %s, user_override %s',
                          zp_film_overview_user_id, type(zp_film_overview_user_id), zp_user_id,
                          type(zp_user_id), user_override)
                film_overview_dict[zp_eapi_id]['overviews'].append({'zp_film_overview_id': zp_film_overview_id,
                                                                    'zp_lang_id': zp_lang_id,
                                                                    'overview': overview,
                                                                    'main_default': main_default,
                                                                    'lang_default': lang_default,
                                                                    'zp_user_id': zp_film_overview_user_id,
                                                                    'id_inc': id_inc})
                id_inc += 1
                if film_overview_text is None:
                    film_overview_text = overview
        if main_default_present is False:
            if 0 not in film_overview_dict:
                film_overview_dict[0] = {'overviews': []}
            film_overview_dict[0]['overviews'].append({'zp_film_overview_id': None,
                                                       'zp_lang_id': None,
                                                       'overview': '',
                                                       'main_default': 1,
                                                       'lang_default': None,
                                                       'zp_user_id': None,
                                                       'id_inc': id_inc})
            id_inc += 1
        if lang_default_present is False:
            if 0 not in film_overview_dict:
                film_overview_dict[0] = {'overviews': []}
            film_overview_dict[0]['overviews'].append({'zp_film_overview_id': None,
                                                       'zp_lang_id': None,
                                                       'overview': '',
                                                       'main_default': None,
                                                       'lang_default': 1,
                                                       'zp_user_id': None,
                                                       'id_inc': id_inc})
            id_inc += 1
        if user_override is False:
            if 0 not in film_overview_dict:
                film_overview_dict[0] = {'overviews': []}
            film_overview_dict[0]['overviews'].append({'zp_film_overview_id': None,
                                                       'zp_lang_id': None,
                                                       'overview': '',
                                                       'main_default': None,
                                                       'lang_default': None,
                                                       'zp_user_id': zp_user_id,
                                                       'id_inc': id_inc})
            id_inc += 1
        session.close()
        return film_overview_dict

    def get_user_film_title_id(self, zp_film_id, zp_user_id):
        session = self.Session()
        zp_film_title_id = None
        try:
            zp_film_title_id = session.query(TABLES.ZP_USER_FILM_ENTITY_XREF).filter(
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == zp_film_id,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1
            ).one().ZP_FILM_ENTITY_ID
        except orm.exc.NoResultFound:
            zp_film_title_id = None
        session.close()
        return zp_film_title_id

    def get_user_film_overview_id(self, zp_film_id, zp_user_id):
        session = self.Session()
        zp_film_title_id = None
        try:
            zp_film_title_id = session.query(TABLES.ZP_USER_FILM_ENTITY_XREF).filter(
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == zp_film_id,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 2
            ).one().ZP_FILM_ENTITY_ID
        except orm.exc.NoResultFound:
            zp_film_title_id = None
        session.close()
        return zp_film_title_id

    def get_lang_default_film_title_id(self, zp_film_id):
        session = self.Session()
        zp_lang_ids = session.query(TABLES.ZP_USER_LIBRARY_LANG.ZP_LANG_ID.distinct.label('ZP_LANG_ID')).filter(
            TABLES.ZP_USER_LIBRARY_LANG.ZP_LIBRARY_ID == 1
        ).all()
        zp_lang_id_list = []
        for zp_lang_id in zp_lang_ids:
            zp_lang_id_list.append(zp_lang_id)
        session.close()
        session = self.Session()
        lang_default_film_title_id_dict = {}
        for zp_lang_id in zp_lang_id_list:
            lang_default_film_title_id_dict[zp_lang_id] = {}
            try:
                zp_film_title_id = session.query(TABLES.ZP_USER_FILM_ENTITY_XREF).filter(
                    TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == zp_film_id,
                    TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1,
                    TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_LANG_ID == zp_film_id,
                    TABLES.ZP_USER_FILM_ENTITY_XREF.LANG_DEFAULT == 1
                ).one().ZP_FILM_ENTITY_ID
            except orm.exc.NoResultFound:
                lang_default_film_title_id_dict[zp_lang_id]['zp_film_title_id'] = None
            else:
                lang_default_film_title_id_dict[zp_lang_id]['zp_film_title_id'] = zp_film_title_id
        session.close()
        return zp_lang_id_list

    def get_main_default_film_title_id(self, zp_film_id):
        session = self.Session()
        main_default_film_title_id = None
        try:
            zp_film_title_id = session.query(TABLES.ZP_USER_FILM_ENTITY_XREF).filter(
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == zp_film_id,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1,
                TABLES.ZP_USER_FILM_ENTITY_XREF.MAIN_DEFAULT == 1
            ).one().ZP_FILM_ENTITY_ID
        except orm.exc.NoResultFound:
            main_default_film_title_id = None
        else:
            main_default_film_title_id = zp_film_title_id
        session.close()
        return main_default_film_title_id

    def get_user_lang(self, zp_user_id):
        session = self.Session()
        zp_lang_id = session.query(TABLES.ZP_USER_LIBRARY_LANG).filter(
            TABLES.ZP_USER_LIBRARY_LANG.ZP_USER_ID == zp_user_id,
            TABLES.ZP_USER_LIBRARY_LANG.ZP_LIBRARY_ID == 1
        ).one().ZP_LANG_ID
        session.close()
        return zp_lang_id

    def update_film_overview(self, zp_film_id, zp_user_id, zp_overview_ident,
                             overview):
        session = self.Session()
        if overview:
            zp_user_lang = self.get_user_lang(zp_user_id)
            overview_ident_regex = r'^(?P<zp_film_overview_id>\d+|None)_(?P<zp_lang_id>\d+|None)_' \
                                   r'(?P<main_default>\d+|None)_' \
                                   r'(?P<lang_default>\d+|None)_(?P<zp_user_id>\d+|None)$'
            match = re.match(overview_ident_regex, zp_overview_ident)
            if match:
                match_groupdict = match.groupdict()
                zp_film_overview_id = match_groupdict['zp_film_overview_id']
                zp_lang_id = match_groupdict['zp_lang_id']
                main_default = match_groupdict['main_default']
                lang_default = match_groupdict['lang_default']
                zp_overview_user_id = match_groupdict['zp_user_id']
                log.debug('zp_overview_ident %s', zp_overview_ident)
                log.debug('zp_film_overview_id %s, zp_lang_id %s, lang_default %s,'
                          ' main_default %s, zp_user_id %s', zp_film_overview_id, zp_lang_id,
                          lang_default, main_default, zp_overview_user_id)
                if zp_film_overview_id.isdigit():
                    zp_film_overview_id = int(zp_film_overview_id)
                    if zp_film_overview_id > 0:
                        try:
                            zp_film_overview = session.query(TABLES.ZP_FILM_OVERVIEW).filter(
                                TABLES.ZP_FILM_OVERVIEW.ID == zp_film_overview_id,
                                TABLES.ZP_FILM_OVERVIEW.ZP_FILM_ID == zp_film_id
                            ).one()
                        except orm.exc.NoResultFound:
                            log.error('could not find entry in ZP_FILM_OVERVIEW with ID %s and ZP_FILM_ID %s',
                                      zp_film_overview_id, zp_film_id)
                        else:
                            # todo add more logic here for authorised edits
                            if not (zp_film_overview.ZP_USER_ID > 0 and
                                        (zp_film_overview.ZP_USER_ID != int(zp_overview_user_id))):
                                zp_film_overview.OVERVIEW = overview
                                if commit(session):
                                    update_film_last_mod(self.Session, zp_film_id)
                                    self.set_user_zp_film_entity_xref(zp_user_id, zp_film_id, 2, zp_film_overview_id)
                elif zp_film_overview_id == 'None':
                    zp_film_overview_id = None
                    if main_default == '1':
                        zp_film_overview_id = self.add_film_overview(zp_film_id, zp_user_lang, 0, 0,
                                                                     0, 1, overview)
                    elif lang_default == '1':
                        zp_film_overview_id = self.add_film_overview(zp_film_id, zp_user_lang, 0, 0,
                                                                     1, 0, overview)
                    elif zp_overview_user_id.isdigit():
                        zp_film_overview_id = self.add_film_overview(zp_film_id, zp_user_lang, 0, zp_user_id,
                                                                     0, 0, overview)
                    if zp_film_overview_id > 0:
                        log.debug('zp_overview_user_id %s is digit', zp_overview_user_id)
                        self.set_user_zp_film_entity_xref(zp_user_id, zp_film_id, 2, zp_film_overview_id)
                        update_film_last_mod(self.Session, zp_film_id)
            else:
                log.error('zp_overview_ident %s failed to match overview_ident_regex %s', zp_overview_ident,
                          overview_ident_regex)
        # todo remove overview by sending empty overview
        session.close()

    def update_film_title(self, zp_film_id, zp_user_id, zp_title_ident,
                          title):
        session = self.Session()
        if title:
            zp_user_lang = self.get_user_lang(zp_user_id)
            title_ident_regex = r'^(?P<zp_film_title_id>\d+|None)_(?P<zp_lang_id>\d+|None)_' \
                                r'(?P<zp_film_title_type_id>\d+|None)_(?P<main_default>\d+|None)_' \
                                r'(?P<lang_default>\d+|None)_(?P<zp_user_id>\d+|None)$'
            match = re.match(title_ident_regex, zp_title_ident)
            if match:
                match_groupdict = match.groupdict()
                zp_film_title_id = match_groupdict['zp_film_title_id']
                zp_lang_id = match_groupdict['zp_lang_id']
                zp_film_title_type_id = match_groupdict['zp_film_title_type_id']
                main_default = match_groupdict['main_default']
                lang_default = match_groupdict['lang_default']
                zp_title_user_id = match_groupdict['zp_user_id']
                log.debug('zp_title_ident %s', zp_title_ident)
                log.debug('zp_film_title_id %s, zp_lang_id %s, zp_film_title_type_id %s, lang_default %s,'
                          ' main_default %s, zp_user_id %s', zp_film_title_id, zp_lang_id,
                          zp_film_title_type_id, lang_default, main_default, zp_title_user_id)
                if zp_film_title_id.isdigit():
                    zp_film_title_id = int(zp_film_title_id)
                    if zp_film_title_id > 0:
                        try:
                            zp_film_title = session.query(TABLES.ZP_FILM_TITLE).filter(
                                TABLES.ZP_FILM_TITLE.ID == zp_film_title_id,
                                TABLES.ZP_FILM_TITLE.ZP_FILM_ID == zp_film_id
                            ).one()
                        except orm.exc.NoResultFound:
                            log.error('could not find entry in ZP_FILM_TITLE with ID %s and ZP_FILM_ID %s',
                                      zp_film_title_id, zp_film_id)
                        else:
                            # todo add more logic here for authorised edits
                            if not (zp_film_title.ZP_USER_ID > 0 and
                                        (zp_film_title.ZP_USER_ID != int(zp_title_user_id))):
                                zp_film_title.TITLE = title
                                if commit(session):
                                    update_film_last_mod(self.Session, zp_film_id)
                                    self.set_user_zp_film_entity_xref(zp_user_id, zp_film_id, 1, zp_film_title_id)
                elif zp_film_title_id == 'None':
                    zp_film_title_id = None
                    if main_default == '1':
                        zp_film_title_id = self.add_film_title(zp_film_id, 1, zp_user_lang, 0, 0,
                                                               0, 1, title)
                    elif lang_default == '1':
                        zp_film_title_id = self.add_film_title(zp_film_id, 1, zp_user_lang, 0, 0,
                                                               1, 0, title)
                    elif zp_title_user_id.isdigit():
                        zp_film_title_id = self.add_film_title(zp_film_id, 1, zp_user_lang, 0, zp_user_id,
                                                               0, 0, title)
                    if zp_film_title_id > 0:
                        self.set_user_zp_film_entity_xref(zp_user_id, zp_film_id, 1, zp_film_title_id)
                        update_film_last_mod(self.Session, zp_film_id)
                        log.debug('zp_title_user_id %s is digit', zp_title_user_id)
            else:
                log.error('zp_title_ident %s failed to match title_ident_regex %s', zp_title_ident,
                          title_ident_regex)
        # todo remove title by sending empty title
        session.close()

    def set_user_zp_film_entity_xref(self, zp_user_id, zp_film_id, zp_film_entity_type_id, zp_film_entity_id):
        session = self.Session()
        try:
            zp_user_film_entity_xref = session.query(TABLES.ZP_USER_FILM_ENTITY_XREF).filter(
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == zp_film_id,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == zp_film_entity_type_id
            ).one()
        except orm.exc.NoResultFound:
            log.error('there should allready be a entry here unless a film and been added'
                      ' but not yet gone through data and user specifics')
            add_zp_user_film_entity_xref = TABLES.ZP_USER_FILM_ENTITY_XREF(ZP_USER_ID=zp_user_id,
                                                                           ZP_FILM_ID=zp_film_id,
                                                                           ZP_FILM_ENTITY_TYPE_ID=zp_film_entity_type_id,
                                                                           ZP_FILM_ENTITY_ID=zp_film_entity_id,
                                                                           FORCED=1,
                                                                           LAST_UPDATE_DATETIME=date_time())
            session.add(add_zp_user_film_entity_xref)
            commit(session)
        else:
            zp_user_film_entity_xref.ZP_FILM_ENTITY_ID = zp_film_entity_id
            zp_user_film_entity_xref.FORCED = 1
            zp_user_film_entity_xref.LAST_UPDATE_DATETIME = date_time()
            commit(session)
        session.close()

    def add_film_title(self, zp_film_id, zp_film_title_type_id, zp_lang_id, zp_eapi_id, zp_user_id,
                       lang_default, main_default, title):
        session = self.Session()
        zp_film_title_id = None
        add_zp_film_title = TABLES.ZP_FILM_TITLE(ZP_FILM_ID=zp_film_id,
                                                 ZP_FILM_TITLE_TYPE_ID=zp_film_title_type_id,
                                                 ZP_LANG_ID=zp_lang_id,
                                                 ZP_EAPI_ID=zp_eapi_id,
                                                 ZP_USER_ID=zp_user_id,
                                                 LANG_DEFAULT=lang_default,
                                                 MAIN_DEFAULT=main_default,
                                                 TITLE=title)
        session.add(add_zp_film_title)
        if commit(session):
            zp_film_title_id = add_zp_film_title.ID
        session.close()
        return zp_film_title_id

    def add_film_overview(self, zp_film_id, zp_lang_id, zp_eapi_id, zp_user_id,
                          lang_default, main_default, overview):
        session = self.Session()
        zp_film_overview_id = None
        add_zp_film_overview = TABLES.ZP_FILM_OVERVIEW(ZP_FILM_ID=zp_film_id,
                                                       ZP_LANG_ID=zp_lang_id,
                                                       ZP_EAPI_ID=zp_eapi_id,
                                                       ZP_USER_ID=zp_user_id,
                                                       LANG_DEFAULT=lang_default,
                                                       MAIN_DEFAULT=main_default,
                                                       OVERVIEW=overview)
        session.add(add_zp_film_overview)
        if commit(session):
            zp_film_overview_id = add_zp_film_overview.ID
        session.close()
        return zp_film_overview_id

    def film_rating(self, zp_film_id):
        session = self.Session()
        try:
            film_rating = session.query(TABLES.ZP_FILM_RATING).filter(
                TABLES.ZP_FILM_RATING.ZP_FILM_ID == zp_film_id).one().RATING
        except orm.exc.NoResultFound:
            film_rating = 5
        session.close()
        return film_rating

    def update_rating(self, zp_film_id, rating):
        session = self.Session()
        result = True
        try:
            film_rating = session.query(TABLES.ZP_FILM_RATING).filter(
                TABLES.ZP_FILM_RATING.ZP_FILM_ID == zp_film_id).one()
        except orm.exc.NoResultFound:
            result = False
        else:
            film_rating.RATING = rating
            commit(session)
            update_film_last_mod(self.Session, zp_film_id)
        session.close()
        return result

    def film_genres(self, zp_film_id):
        session = self.Session()
        film_genre_list = []
        film_genres = session.query(TABLES.ZP_FILM_GENRE_XREF.ZP_GENRE_ID).filter(
            TABLES.ZP_FILM_GENRE_XREF.ZP_FILM_ID == zp_film_id).all()
        session.close()
        for film in film_genres:
            film_genre_list.append(film.ZP_GENRE_ID)
        return film_genre_list

    def set_user_film_raw_image(self, zp_film_id, image_type, zp_film_raw_image_id, zp_user_id):
        success = False
        session = self.Session()
        try:
            session.query(TABLES.ZP_FILM_RAW_IMAGE).filter(
                TABLES.ZP_FILM_RAW_IMAGE.ZP_ENTITY_ID == zp_film_id,
                TABLES.ZP_FILM_RAW_IMAGE.ZP_ENTITY_TYPE_ID == self.image_type_id_dict[image_type],
                TABLES.ZP_FILM_RAW_IMAGE.ID == zp_film_raw_image_id
            ).one()
        except orm.exc.NoResultFound:
            log.error('could not find entry in ZP_FILM_RAW_IMAGE for ZP_ENTITY_ID %s,'
                      'ZP_ENTITY_TYPE_ID %s, ID %s', zp_film_id, self.image_type_id_dict[image_type],
                      zp_film_raw_image_id)
        else:
            try:
                zp_user_film_entity_xref = session.query(TABLES.ZP_USER_FILM_ENTITY_XREF).filter(
                    TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                    TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == zp_film_id,
                    TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == self.image_film_entity_type_id_dict[
                        image_type]
                ).one()
            except orm.exc.NoResultFound:
                add_zp_user_film_entity_xref = TABLES.ZP_USER_FILM_ENTITY_XREF(
                    ZP_USER_ID=zp_user_id,
                    ZP_FILM_ID=zp_film_id,
                    ZP_FILM_ENTITY_TYPE_ID=self.image_film_entity_type_id_dict[image_type],
                    ZP_FILM_ENTITY_ID=zp_film_raw_image_id,
                    FORCED=1,
                    LAST_UPDATE_DATETIME=date_time()
                )
                session.add(add_zp_user_film_entity_xref)
                if commit(session):
                    update_film_last_mod(self.Session, zp_film_id)
                    success = True
            else:
                zp_user_film_entity_xref.FORCED = 1
                zp_user_film_entity_xref.ZP_FILM_ENTITY_ID = zp_film_raw_image_id
                zp_user_film_entity_xref.LAST_UPDATE_DATETIME = date_time()
                if commit(session):
                    update_film_last_mod(self.Session, zp_film_id)
                    success = True
        session.close()
        return success

    def clear_genres(self, zp_film_id):
        session = self.Session()
        session.query(TABLES.ZP_FILM_GENRE_XREF).filter(
            TABLES.ZP_FILM_GENRE_XREF.ZP_FILM_ID == zp_film_id).delete()
        commit(session)
        session.close()
        return True

    def add_genre(self, zp_film_id, genre):
        session = self.Session()
        add_ZP_FILM_GENRE_XREF = TABLES.ZP_FILM_GENRE_XREF(ZP_FILM_ID=zp_film_id,
                                                           ZP_GENRE_ID=genre)
        session.add(add_ZP_FILM_GENRE_XREF)
        commit(session)
        update_film_last_mod(self.Session, zp_film_id)
        session.close()
        return True

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
                path = 'smb://%s@%s{%s}:%s/%s/%s' % (rslt_scan_path.USERNAME,
                                   rslt_scan_path.HOSTNAME,
                                   rslt_scan_path.REMOTE_NAME,
                                   rslt_scan_path.PORT,
                                   rslt_scan_path.SHARE_NAME,
                                   rslt_scan_path.PATH)
        return path

    def get_film_filefolder_id(self, zp_film_id):
        session = self.Session()
        try:
            zp_film_filefolder = session.query(
                TABLES.ZP_FILM
            ).filter(
                TABLES.ZP_FILM.ID == zp_film_id
            ).one()
        except orm.exc.NoResultFound:
            zp_film_filefolder_id = 0
        else:
            zp_film_filefolder_id = zp_film_filefolder.ZP_FILM_FILEFOLDER_ID
        return zp_film_filefolder_id

    def film_path(self, zp_film_filefolder_id):
        session = self.Session()
        try:
            zp_film_filefolder = session.query(TABLES.ZP_FILM_FILEFOLDER).filter(
                TABLES.ZP_FILM_FILEFOLDER.ID == zp_film_filefolder_id
            ).one()
        except orm.exc.NoResultFound:
            path = 'Path not found'
        else:
            zp_scan_path_id = zp_film_filefolder.ZP_SCAN_PATH_ID
            scan_path = self.zp_scan_path_string(zp_scan_path_id)
            path = '%s/%s' % (scan_path, os.path.join(
                zp_film_filefolder.SCAN_PATH_SUB_DIR,
                zp_film_filefolder.LAST_PATH
                )
            )
        session.close()
        return path

    def film_cast(self, zp_film_id):
        session = self.Session()
        film_cast_list = []

        subq = session.query(TABLES.ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID,
                             func.count(TABLES.ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID).label('pcount')).group_by(
            TABLES.ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID).subquery()
        film_cast = session.query(TABLES.ZP_PEOPLE.NAME, TABLES.ZP_PEOPLE.ID, subq.c.pcount).join(
            TABLES.ZP_FILM_ROLE_XREF, TABLES.ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID == TABLES.ZP_PEOPLE.ID).join(
            subq, subq.c.ZP_PEOPLE_ID == TABLES.ZP_PEOPLE.ID).filter(
            TABLES.ZP_FILM_ROLE_XREF.ZP_FILM_ID == zp_film_id,
            TABLES.ZP_FILM_ROLE_XREF.ZP_ROLE_ID == 1,
        ).order_by(case([(TABLES.ZP_FILM_ROLE_XREF.ROLE_ORDER == None, 1)], else_=0),
                   TABLES.ZP_FILM_ROLE_XREF.ROLE_ORDER.asc(), subq.c.pcount.desc()).all()
        session.close()
        for cast in film_cast:
            film_cast_list.append({'id': cast.ID,
                                   'name': cast.NAME})
        return film_cast_list

    def get_actors(self, name):
        session = self.Session()
        actor_list = []
        subq = session.query(TABLES.ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID,
                             case([(func.count(TABLES.ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID) == None, 0)],
                                  else_=func.count(TABLES.ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID)).label('pcount')).group_by(
            TABLES.ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID).subquery()
        actors = session.query(TABLES.ZP_PEOPLE.NAME, TABLES.ZP_PEOPLE.ID, subq.c.pcount).outerjoin(
            subq, subq.c.ZP_PEOPLE_ID == TABLES.ZP_PEOPLE.ID).filter(
            TABLES.ZP_PEOPLE.NAME.like('%%%s%%' % name)
        ).order_by(subq.c.pcount.desc()).limit(50)
        session.close()
        for actor in actors:
            actor_list.append({'id': actor.ID,
                               'name': actor.NAME})
        return actor_list

    def clear_cast(self, zp_film_id):
        session = self.Session()
        session.query(TABLES.ZP_FILM_ROLE_XREF).filter(
            TABLES.ZP_FILM_ROLE_XREF.ZP_FILM_ID == zp_film_id,
            TABLES.ZP_FILM_ROLE_XREF.ZP_ROLE_ID == 1).delete()
        commit(session)
        session.close()
        return True

    def add_cast(self, zp_film_id, people_id):
        # todo check is not allready assigned to film
        session = self.Session()
        add_ZP_FILM_ROLE_XREF = TABLES.ZP_FILM_ROLE_XREF(ZP_FILM_ID=zp_film_id,
                                                         ZP_ROLE_ID=1,
                                                         ZP_PEOPLE_ID=people_id)
        session.add(add_ZP_FILM_ROLE_XREF)
        commit(session)
        update_film_last_mod(self.Session, zp_film_id)
        session.close()
        return True

    def get_unidentified_films(self):
        return_list = []
        session = self.Session()
        unidentified = session.query(
            TABLES.ZP_FILM_FILEFOLDER
        ).filter(
            TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == None,
            TABLES.ZP_FILM_FILEFOLDER.ID.in_(session.query(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 1
            ))
        ).all()
        for filefolder in unidentified:
            path = os.path.join(filefolder.SCAN_PATH_SUB_DIR, filefolder.LAST_PATH)
            temp_dict = {'path': path, 'id': filefolder.ID}
            return_list.append(temp_dict)
        session.close()
        return return_list

    def get_total_num_films(self):
        session = self.Session()
        # todo where fill is not hidden for a number of reasons
        num_films = session.query(TABLES.ZP_FILM).count()
        session.close()
        return num_films

    def set_filefolder_eapieid(self, eapi_id, eapi_eid, zp_filefolder_id):
        session = self.Session()
        try:
            zp_film_eapi_eid = session.query(TABLES.ZP_FILM_EAPI_EID).filter(
                TABLES.ZP_FILM_EAPI_EID.ZP_EAPI_ID == eapi_id,
                TABLES.ZP_FILM_EAPI_EID.ZP_EAPI_EID == eapi_eid
            ).one()
        except orm.exc.NoResultFound:
            # todo verify tmdbid
            ADDED_DATE_TIME = date_time()
            add_film = TABLES.ZP_FILM(ADDED_DATE_TIME=ADDED_DATE_TIME,
                                      ZP_FILM_FILEFOLDER_ID=zp_filefolder_id,
                                      LAST_EDIT_DATETIME=ADDED_DATE_TIME)
            session.add(add_film)
            log.debug(('Inserted ADDED_DATE_TIME: {0},'
                       ' ZP_FILM_FILEFOLDER_ID:{1}, LAST_EDIT_DATETIME: {0} into ZP_FILM').format(
                ADDED_DATE_TIME,
                zp_filefolder_id))
            flush(session)
            zp_film_id = add_film.ID
            film_filfolder = session.query(TABLES.ZP_FILM_FILEFOLDER).filter(
                TABLES.ZP_FILM_FILEFOLDER.ID == zp_filefolder_id).one()
            film_filfolder.ZP_FILM_ID = zp_film_id
            add_film_eapi_eid = TABLES.ZP_FILM_EAPI_EID(ZP_FILM_ID=zp_film_id,
                                                        ZP_EAPI_EID=eapi_eid,
                                                        ZP_EAPI_ID=eapi_id)
            session.add(add_film_eapi_eid)
            flush(session)
            commit(session)
        else:
            session.query(TABLES.ZP_FILM_FILEFOLDER).filter(
                TABLES.ZP_FILM_FILEFOLDER.ID == zp_filefolder_id).update({'ZP_FILM_ID': zp_film_eapi_eid.ZP_FILM_ID})
            commit(session)
        session.close()
        return True

    def reset_film_filefolder(self, eapi_id, eapi_eid, zp_film_id):
        session = self.Session()
        try:
            zp_film = session.query(TABLES.ZP_FILM).filter(
                TABLES.ZP_FILM.ID == zp_film_id
            ).one()
        except orm.exc.NoResultFound:
            log.error('ZP_FILM does not exsist with ID %s cannot reset film', zp_film_id)
        else:
            zp_film_filefolder_id = zp_film.ZP_FILM_FILEFOLDER_ID
            zp_film.ZP_FILM_FILEFOLDER_ID = None
            try:
                zp_film_eapi_eid = session.query(TABLES.ZP_FILM_EAPI_EID).filter(
                    TABLES.ZP_FILM_EAPI_EID.ZP_EAPI_ID == eapi_id,
                    TABLES.ZP_FILM_EAPI_EID.ZP_EAPI_EID == eapi_eid
                ).one()
            except orm.exc.NoResultFound:
                # todo verify tmdbid
                ADDED_DATE_TIME = date_time()
                add_film = TABLES.ZP_FILM(ADDED_DATE_TIME=ADDED_DATE_TIME,
                                          ZP_FILM_FILEFOLDER_ID=zp_film_filefolder_id,
                                          LAST_EDIT_DATETIME=ADDED_DATE_TIME)
                session.add(add_film)
                log.debug(('Inserted ADDED_DATE_TIME: {0},'
                           ' ZP_FILM_FILEFOLDER_ID:{1}, LAST_EDIT_DATETIME: {0} into ZP_FILM').format(
                    ADDED_DATE_TIME,
                    zp_film_filefolder_id))
                flush(session)
                zp_film_id = add_film.ID
                film_filfolder = session.query(TABLES.ZP_FILM_FILEFOLDER).filter(
                    TABLES.ZP_FILM_FILEFOLDER.ID == zp_film_filefolder_id).one()
                film_filfolder.ZP_FILM_ID = zp_film_id
                add_film_eapi_eid = TABLES.ZP_FILM_EAPI_EID(ZP_FILM_ID=zp_film_id,
                                                            ZP_EAPI_EID=eapi_eid,
                                                            ZP_EAPI_ID=eapi_id)
                session.add(add_film_eapi_eid)
                flush(session)
                commit(session)
            else:
                session.query(TABLES.ZP_FILM_FILEFOLDER).filter(
                    TABLES.ZP_FILM_FILEFOLDER.ID == zp_film_filefolder_id).update(
                    {'ZP_FILM_ID': zp_film_eapi_eid.ZP_FILM_ID})
                commit(session)
        session.close()
        return True

    def check_zp_filefolder_id_exists(self, zp_filefolder_id):
        session = self.Session()
        try:
            session.query(TABLES.ZP_FILM_FILEFOLDER).filter(
                TABLES.ZP_FILM_FILEFOLDER.ID == zp_filefolder_id).one()
        except orm.exc.NoResultFound:
            exists = False
        else:
            exists = True
        session.close()
        return exists

    def check_unidentified(self, zp_filefolder_id):
        return_dict = {'unidentified': False, 'title': ''}
        session = self.Session()
        ZP_FILM_FILEFOLDER = session.query(TABLES.ZP_FILM_FILEFOLDER).filter(
            TABLES.ZP_FILM_FILEFOLDER.ID == zp_filefolder_id).one()
        path = os.path.join(ZP_FILM_FILEFOLDER.SCAN_PATH_SUB_DIR, ZP_FILM_FILEFOLDER.LAST_PATH)
        return_dict['title'] = path
        if ZP_FILM_FILEFOLDER.ZP_FILM_ID is None:
            return_dict['unidentified'] = True
        session.close()
        return return_dict

    def genre_by_name(self):
        session = self.Session
        genre_dict = {}
        genres = session.query(TABLES.ZP_GENRE).all()
        session.close()
        for genre in genres:
            genre_dict[genre.GENRE] = genre.ID
        return genre_dict

    def genre_by_id(self):
        session = self.Session
        genre_dict = {}
        genres = session.query(TABLES.ZP_GENRE).all()
        session.close()
        for genre in genres:
            genre_dict[genre.ID] = genre.GENRE
        return genre_dict
