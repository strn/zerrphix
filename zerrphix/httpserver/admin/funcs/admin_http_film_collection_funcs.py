import logging

# from PIL import Image
from sqlalchemy import orm

from zerrphix.db.tables import TABLES
from zerrphix.util.plugin import create_eapi_dict
from sqlalchemy import case
from sqlalchemy import func
# from PIL import Image
from sqlalchemy import orm, exc, and_
from zerrphix.film.util import update_film_collection_last_mod
import re
from zerrphix.util.text import date_time
from zerrphix.db import commit
from zerrphix.db import flush
log = logging.getLogger(__name__)


class AdminHTTPFilmCollectionFuncs(object):
    def __init__(self, Session, global_config_dict):
        # logging.config.dictConfig(LOG_SETTINGS)
        self.Session = Session
        self.global_config_dict = global_config_dict
        self.eapi_dict = create_eapi_dict(Session)
        self.image_type_id_dict = {'poster': 1, 'backdrop': 2}
        self.image_film_collection_entity_type_id_dict = {'poster': 3, 'backdrop': 4}

    def get_total_num_collections(self):
        session = self.Session()
        collection_count = session.query(
            TABLES.ZP_FILM_COLLECTION.ID
        ).join(
            TABLES.ZP_FILM_COLLECTION_TITLE,
            TABLES.ZP_FILM_COLLECTION_TITLE.ID == session.query(
                TABLES.ZP_FILM_COLLECTION_TITLE.ID
            ).filter(
                TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_ID == TABLES.ZP_FILM_COLLECTION.ID
            ).limit(1).correlate(TABLES.ZP_FILM_COLLECTION)
        ).count()
        session.close()
        return collection_count

    def film_collection_list(self, limit=50, offset=0, sort_type='alpha', search=None):
        film_collection_list = []
        session = self.Session()
        if search:
            films = session.query(
                TABLES.ZP_FILM_COLLECTION.ID,
                TABLES.ZP_FILM_COLLECTION_TITLE.TITLE
            ).join(
                TABLES.ZP_FILM_COLLECTION_TITLE,
                TABLES.ZP_FILM_COLLECTION_TITLE.ID == session.query(
                    TABLES.ZP_FILM_COLLECTION_TITLE.ID
                ).filter(
                    TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_ID == TABLES.ZP_FILM_COLLECTION.ID
                ).limit(1).correlate(TABLES.ZP_FILM_COLLECTION)
            ).filter(
                TABLES.ZP_FILM_COLLECTION_TITLE.TITLE.like('%%%s%%' % search)
            ).order_by(TABLES.ZP_FILM_COLLECTION_TITLE.TITLE.asc()).limit(limit).offset(offset)
        elif sort_type == 'alpha_desc':
            films = session.query(
                TABLES.ZP_FILM_COLLECTION.ID,
                TABLES.ZP_FILM_COLLECTION_TITLE.TITLE
            ).join(
                TABLES.ZP_FILM_COLLECTION_TITLE,
                TABLES.ZP_FILM_COLLECTION_TITLE.ID == session.query(
                    TABLES.ZP_FILM_COLLECTION_TITLE.ID
                ).filter(
                    TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_ID == TABLES.ZP_FILM_COLLECTION.ID
                ).limit(1).correlate(TABLES.ZP_FILM_COLLECTION)
            ).order_by(TABLES.ZP_FILM_COLLECTION_TITLE.TITLE.desc()).limit(limit).offset(offset)
        else:
            films = session.query(
                TABLES.ZP_FILM_COLLECTION.ID,
                TABLES.ZP_FILM_COLLECTION_TITLE.TITLE
            ).join(
                TABLES.ZP_FILM_COLLECTION_TITLE,
                TABLES.ZP_FILM_COLLECTION_TITLE.ID == session.query(
                    TABLES.ZP_FILM_COLLECTION_TITLE.ID
                ).filter(
                    TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_ID == TABLES.ZP_FILM_COLLECTION.ID
                ).limit(1).correlate(TABLES.ZP_FILM_COLLECTION)
            ).order_by(TABLES.ZP_FILM_COLLECTION_TITLE.TITLE.asc()).limit(limit).offset(offset)

        for film in films:
            film_collection_list.append({'title': film.TITLE,
                                         'id': film.ID})
        session.close()
        return film_collection_list

    def film_list(self, search_text):
        film_list = []
        session = self.Session()
        films = session.query(TABLES.ZP_FILM.ID,
                               TABLES.ZP_FILM_TITLE.TITLE).join(
             TABLES.ZP_FILM_TITLE, TABLES.ZP_FILM_TITLE.ID ==
                                              session.query(TABLES.ZP_FILM_TITLE.ID).filter(
                                                  TABLES.ZP_FILM_TITLE.ZP_FILM_ID ==
                                                  TABLES.ZP_FILM.ID).limit(
                                                  1).correlate(TABLES.ZP_FILM)
        ).filter(
            TABLES.ZP_FILM_TITLE.TITLE.like('%%%s%%' % search_text)
        ).order_by(TABLES.ZP_FILM_TITLE.TITLE.asc()).limit(50)

        for film in films:
            film_list.append({'title': film.TITLE,
                                         'id': film.ID})
        session.close()
        return film_list

    def clear_films(self, zp_film_collection_id):
        session = self.Session()
        session.query(TABLES.ZP_FILM_COLLECTION_XREF).filter(
            TABLES.ZP_FILM_COLLECTION_XREF.ZP_FILM_COLLECTION_ID == zp_film_collection_id).delete()
        commit(session)
        session.close()
        return True

    def create_collection(self, title, overview, zp_lang_id):
        session = self.Session()
        add_ZP_FILM_COLLECTION = TABLES.ZP_FILM_COLLECTION(LAST_EDIT_DATETIME=date_time())
        session.add(add_ZP_FILM_COLLECTION)
        flush(session)
        zp_film_collection_id = add_ZP_FILM_COLLECTION.ID
        add_ZP_FILM_COLLECTION_TITLE = TABLES.ZP_FILM_COLLECTION_TITLE(ZP_FILM_COLLECTION_ID=zp_film_collection_id,
                                                                       ZP_FILM_COLLECTION_TITLE_TYPE_ID=1,
                                                                       ZP_LANG_ID=zp_lang_id,
                                                                       ZP_EAPI_ID=0,
                                                                       ZP_USER_ID=0,
                                                                       LANG_DEFAULT=0,
                                                                       MAIN_DEFAULT=1,
                                                                       TITLE=title)
        session.add(add_ZP_FILM_COLLECTION_TITLE)
        flush(session)
        add_ZP_FILM_COLLECTION_OVERVIEW = TABLES.ZP_FILM_COLLECTION_OVERVIEW(
            ZP_FILM_COLLECTION_ID=zp_film_collection_id,
            ZP_LANG_ID=zp_lang_id,
            ZP_EAPI_ID=0,
            ZP_USER_ID=0,
            LANG_DEFAULT=0,
            MAIN_DEFAULT=1,
            OVERVIEW=overview)
        session.add(add_ZP_FILM_COLLECTION_OVERVIEW)
        commit(session)
        session.close()
        return zp_film_collection_id

    def add_film(self, zp_film_collection_id, zp_film_id):
        # todo check is not allready assigned to film
        session = self.Session()
        add_ZP_FILM_COLLECTION_XREF = TABLES.ZP_FILM_COLLECTION_XREF(ZP_FILM_ID=zp_film_id,
                                                                     ZP_FILM_COLLECTION_ID=zp_film_collection_id)
        session.add(add_ZP_FILM_COLLECTION_XREF)
        commit(session)
        update_film_collection_last_mod(self.Session, zp_film_collection_id)
        session.close()
        return True

    def film_collection_overview(self, zp_film_collection_id, zp_user_id):
        session = self.Session()
        try:
            film_collection_overview = session.query(TABLES.ZP_FILM_COLLECTION_OVERVIEW).filter(
                TABLES.ZP_FILM_COLLECTION_OVERVIEW.ID ==
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_ID,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ID == zp_film_collection_id,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_TYPE_ID == 2).one().OVERVIEW
        except orm.exc.NoResultFound:
            film_collection_overview = 'No Overview Found or User Specifics is yet to run'
        session.close()
        return film_collection_overview

    def film_collection_title(self, zp_film_collection_id, zp_user_id, strict=False):
        session = self.Session()
        try:
            film_collection_title = session.query(TABLES.ZP_FILM_COLLECTION_TITLE).filter(
                TABLES.ZP_FILM_COLLECTION_TITLE.ID ==
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_ID,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ID == zp_film_collection_id,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_TYPE_ID == 1).one().TITLE
        except orm.exc.NoResultFound:
            # if there is not a title for a user but one exists we should try and use one
            # to show on the admin web interface to show which film is being edited
            if strict is True:
                film_collection_title = 'No Title Found or User Specifics is yet to run'
            else:
                try:
                    film_collection_title = session.query(TABLES.ZP_FILM_COLLECTION_TITLE).filter(
                        TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_ID == zp_film_collection_id).limit(
                        1).one().TITLE
                except orm.exc.NoResultFound:
                    film_collection_title = 'No Title Found or User Specifics is yet to run'
        session.close()
        return film_collection_title

    def get_user_film_collection_raw_image_id(self, zp_film_collection_id, zp_film_collection_entity_type_id,
                                              zp_user_id):
        session = self.Session()
        zp_film_collection_raw_image_id = None
        try:
            zp_film_collection_raw_image_id = session.query(TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF).filter(
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ID == zp_film_collection_id,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_TYPE_ID ==
                zp_film_collection_entity_type_id).one(
            ).ZP_FILM_COLLECTION_ENTITY_ID
        except orm.exc.NoResultFound:
            log.debug(
                'no result found for zp_film_collection_id %s, zp_user_id %s, zp_film_collection_entity_type_id %s',
                zp_film_collection_id, zp_user_id, zp_film_collection_entity_type_id)
        session.close()
        return zp_film_collection_raw_image_id

    def film_collection_rendered_image(self, zp_film_id, image_type_id, zp_icon_sub_type_id, zp_user_id):
        session = self.Session()
        rendered_image_id = None
        try:
            rendered_image_id = session.query(
                TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH
            ).join(
                TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF,
                and_(
                    TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_ID ==
                    TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ZP_FILM_COLLECTION_ID,
                    TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE ==
                    TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_IMAGE_SUB_TYPE,
                    TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_ID ==
                    TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ZP_FILM_COLLECTION_ID,
                    TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH_ID ==
                    TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ID,
                    TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ZP_FILM_COLLECTION_IMAGE_TYPE_ID ==
                    TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_IMAGE_TYPE_ID
                )
            ).filter(
                TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_IMAGE_TYPE_ID == image_type_id,
                TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_ID == zp_film_id,
                TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE == zp_icon_sub_type_id
            ).one().ID
        except orm.exc.NoResultFound:
            log.warning('could not find entry in ZP_FILM_IMAGE_RENDER_HASH for zp_user_id %s, zp_film_id %s,'
                      ' image_type_id %s, zp_icon_sub_type_id %s', zp_user_id, zp_film_id, image_type_id,
                        zp_icon_sub_type_id)
        session.close()
        return rendered_image_id

    def film_collection_title_list(self, zp_film_collection_id, zp_user_id):
        session = self.Session()
        film_collection_title_dict = {}
        main_default_present = False
        lang_default_present = False
        user_override = False
        id_inc = 1
        try:
            zp_film_collection_title = session.query(TABLES.ZP_FILM_COLLECTION_TITLE).filter(
                TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_ID == zp_film_collection_id).order_by(
                TABLES.ZP_FILM_COLLECTION_TITLE.ZP_EAPI_ID.asc(), TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_TITLE_TYPE_ID.asc(),
                TABLES.ZP_FILM_COLLECTION_TITLE.ZP_LANG_ID.desc()
            ).all()
        except orm.exc.NoResultFound:
            film_collection_title_dict = None
        else:
            for film_collection_title in zp_film_collection_title:
                zp_eapi_id = film_collection_title.ZP_EAPI_ID
                zp_lang_id = film_collection_title.ZP_LANG_ID
                zp_film_collection_title_type_id = film_collection_title.ZP_FILM_COLLECTION_TITLE_TYPE_ID
                zp_film_collection_title_id = film_collection_title.ID
                title = film_collection_title.TITLE
                main_default = film_collection_title.MAIN_DEFAULT
                lang_default = film_collection_title.LANG_DEFAULT
                zp_film_collection_title_user_id = film_collection_title.ZP_USER_ID
                if main_default == 1:
                    main_default_present = True
                if lang_default == 1:
                    lang_default_present = True
                if zp_film_collection_title_user_id == zp_user_id:
                    user_override = True
                if zp_eapi_id not in film_collection_title_dict:
                    film_collection_title_dict[zp_eapi_id] = {'titles': []}
                log.debug('zp_film_collection_title_user_id %s type %s and zp_user_id %s type %s, user_override %s',
                          zp_film_collection_title_user_id, type(zp_film_collection_title_user_id), zp_user_id,
                          type(zp_user_id), user_override)
                film_collection_title_dict[zp_eapi_id]['titles'].append({'zp_film_collection_title_id':
                                                                             zp_film_collection_title_id,
                                                              'zp_lang_id': zp_lang_id,
                                                              'zp_film_collection_title_type_id':
                                                                             zp_film_collection_title_type_id,
                                                              'title': title,
                                                              'main_default': main_default,
                                                              'lang_default': lang_default,
                                                              'zp_user_id': zp_film_collection_title_user_id,
                                                              'id_inc': id_inc})
                id_inc += 1
        if main_default_present is False:
            if 0 not in film_collection_title_dict:
                film_collection_title_dict[0] = {'titles': []}
            film_collection_title_dict[0]['titles'].append({'zp_film_collection_title_id': None,
                                                 'zp_lang_id': None,
                                                 'zp_film_collection_title_type_id': None,
                                                 'title': '',
                                                 'main_default': 1,
                                                 'lang_default': None,
                                                 'zp_user_id': None,
                                                 'id_inc': id_inc})
            id_inc += 1
        if lang_default_present is False:
            if 0 not in film_collection_title_dict:
                film_collection_title_dict[0] = {'titles': []}
            film_collection_title_dict[0]['titles'].append({'zp_film_collection_title_id': None,
                                                 'zp_lang_id': None,
                                                 'zp_film_collection_title_type_id': None,
                                                 'title': '',
                                                 'main_default': None,
                                                 'lang_default': 1,
                                                 'zp_user_id': None,
                                                 'id_inc': id_inc})
            id_inc += 1
        if user_override is False:
            if 0 not in film_collection_title_dict:
                film_collection_title_dict[0] = {'titles': []}
            film_collection_title_dict[0]['titles'].append({'zp_film_collection_title_id': None,
                                                 'zp_lang_id': None,
                                                 'zp_film_collection_title_type_id': None,
                                                 'title': '',
                                                 'main_default': None,
                                                 'lang_default': None,
                                                 'zp_user_id': zp_user_id,
                                                 'id_inc': id_inc})
            id_inc += 1
        session.close()
        return film_collection_title_dict

    def film_collection_overview_list(self, zp_film_collection_id, zp_user_id):
        session = self.Session()
        film_collection_overview_text = None
        film_collection_overview_dict = {}
        main_default_present = False
        lang_default_present = False
        user_override = False
        id_inc = 1
        try:
            zp_film_collection_overview = session.query(TABLES.ZP_FILM_COLLECTION_OVERVIEW).filter(
                TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_FILM_COLLECTION_ID == zp_film_collection_id).order_by(
                TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_EAPI_ID.asc(),
                TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_LANG_ID.desc()
            ).all()
        except orm.exc.NoResultFound:
            film_collection_overview_dict = None
        else:
            for film_collection_overview in zp_film_collection_overview:
                zp_eapi_id = film_collection_overview.ZP_EAPI_ID
                zp_lang_id = film_collection_overview.ZP_LANG_ID
                zp_film_collection_overview_id = film_collection_overview.ID
                overview = film_collection_overview.OVERVIEW
                main_default = film_collection_overview.MAIN_DEFAULT
                lang_default = film_collection_overview.LANG_DEFAULT
                zp_film_collection_overview_user_id = film_collection_overview.ZP_USER_ID
                if main_default == 1:
                    main_default_present = True
                if lang_default == 1:
                    lang_default_present = True
                if zp_film_collection_overview_user_id == zp_user_id:
                    user_override = True
                if zp_eapi_id not in film_collection_overview_dict:
                    film_collection_overview_dict[zp_eapi_id] = {'overviews': []}
                log.debug('zp_film_collection_overview_user_id %s type %s and zp_user_id %s type %s, user_override %s',
                          zp_film_collection_overview_user_id, type(zp_film_collection_overview_user_id), zp_user_id,
                          type(zp_user_id), user_override)
                film_collection_overview_dict[zp_eapi_id]['overviews'].append({'zp_film_collection_overview_id':
                                                                                   zp_film_collection_overview_id,
                                                                    'zp_lang_id': zp_lang_id,
                                                                    'overview': overview,
                                                                    'main_default': main_default,
                                                                    'lang_default': lang_default,
                                                                    'zp_user_id': zp_film_collection_overview_user_id,
                                                                    'id_inc': id_inc})
                id_inc += 1
                if film_collection_overview_text is None:
                    film_collection_overview_text = overview
        if main_default_present is False:
            if 0 not in film_collection_overview_dict:
                film_collection_overview_dict[0] = {'overviews': []}
            film_collection_overview_dict[0]['overviews'].append({'zp_film_collection_overview_id': None,
                                                       'zp_lang_id': None,
                                                       'overview': '',
                                                       'main_default': 1,
                                                       'lang_default': None,
                                                       'zp_user_id': None,
                                                       'id_inc': id_inc})
            id_inc += 1
        if lang_default_present is False:
            if 0 not in film_collection_overview_dict:
                film_collection_overview_dict[0] = {'overviews': []}
            film_collection_overview_dict[0]['overviews'].append({'zp_film_collection_overview_id': None,
                                                                  'zp_lang_id': None,
                                                                  'overview': '',
                                                                  'main_default': None,
                                                                  'lang_default': 1,
                                                                  'zp_user_id': None,
                                                                  'id_inc': id_inc})
            id_inc += 1
        if user_override is False:
            if 0 not in film_collection_overview_dict:
                film_collection_overview_dict[0] = {'overviews': []}
            film_collection_overview_dict[0]['overviews'].append({'zp_film_collection_overview_id': None,
                                                                  'zp_lang_id': None,
                                                                  'overview': '',
                                                                  'main_default': None,
                                                                  'lang_default': None,
                                                                  'zp_user_id': zp_user_id,
                                                                  'id_inc': id_inc})
            id_inc += 1
        session.close()
        return film_collection_overview_dict

    def get_user_film_collection_title_id(self, zp_film_collection_id, zp_user_id):
        session = self.Session()
        zp_film_collection_title_id = None
        try:
            zp_film_collection_title_id = session.query(TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF).filter(
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ID == zp_film_collection_id,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_TYPE_ID == 1
            ).one().ZP_FILM_COLLECTION_ENTITY_ID
        except orm.exc.NoResultFound:
            zp_film_collection_title_id = None
        session.close()
        return zp_film_collection_title_id

    def get_user_film_collection_overview_id(self, zp_film_collection_id, zp_user_id):
        session = self.Session()
        zp_film_collection_title_id = None
        try:
            zp_film_collection_title_id = session.query(TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF).filter(
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ID == zp_film_collection_id,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_TYPE_ID == 2
            ).one().ZP_FILM_COLLECTION_ENTITY_ID
        except orm.exc.NoResultFound:
            zp_film_collection_title_id = None
        session.close()
        return zp_film_collection_title_id

    def get_lang_default_film_collection_title_id(self, zp_film_collection_id):
        session = self.Session()
        zp_lang_ids = session.query(TABLES.ZP_USER_LIBRARY_LANG.ZP_LANG_ID.distinct.label('ZP_LANG_ID')).filter(
            TABLES.ZP_USER_LIBRARY_LANG.ZP_LIBRARY_ID == 1
        ).all()
        zp_lang_id_list = []
        for zp_lang_id in zp_lang_ids:
            zp_lang_id_list.append(zp_lang_id)
        session.close()
        session = self.Session()
        lang_default_film_collection_title_id_dict = {}
        for zp_lang_id in zp_lang_id_list:
            lang_default_film_collection_title_id_dict[zp_lang_id] = {}
            try:
                zp_film_collection_title_id = session.query(TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF).filter(
                    TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ID == zp_film_collection_id,
                    TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_TYPE_ID == 1,
                    TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_LANG_ID == zp_film_collection_id,
                    TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.LANG_DEFAULT == 1
                ).one().ZP_FILM_COLLECTION_ENTITY_ID
            except orm.exc.NoResultFound:
                lang_default_film_collection_title_id_dict[zp_lang_id]['zp_film_collection_title_id'] = None
            else:
                lang_default_film_collection_title_id_dict[zp_lang_id]['zp_film_collection_title_id'] = \
                    zp_film_collection_title_id
        session.close()
        return zp_lang_id_list

    def get_main_default_film_collection_title_id(self, zp_film_collection_id):
        session = self.Session()
        main_default_film_collection_title_id = None
        try:
            zp_film_collection_title_id = session.query(TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF).filter(
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ID == zp_film_collection_id,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_TYPE_ID == 1,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.MAIN_DEFAULT == 1
            ).one().ZP_FILM_COLLECTION_ENTITY_ID
        except orm.exc.NoResultFound:
            main_default_film_collection_title_id = None
        else:
            main_default_film_collection_title_id = zp_film_collection_title_id
        session.close()
        return main_default_film_collection_title_id


    def get_user_lang(self, zp_user_id):
        session = self.Session()
        zp_lang_id = session.query(TABLES.ZP_USER_LIBRARY_LANG).filter(
            TABLES.ZP_USER_LIBRARY_LANG.ZP_USER_ID == zp_user_id,
            TABLES.ZP_USER_LIBRARY_LANG.ZP_LIBRARY_ID == 2
        ).one().ZP_LANG_ID
        session.close()
        return zp_lang_id

    def update_film_collection_overview(self, zp_film_collection_id, zp_user_id, zp_overview_ident,
                             overview):
        session = self.Session()
        if overview:
            zp_user_lang = self.get_user_lang(zp_user_id)
            overview_ident_regex = r'^(?P<zp_film_collection_overview_id>\d+|None)_(?P<zp_lang_id>\d+|None)_' \
                                   r'(?P<main_default>\d+|None)_' \
                                   r'(?P<lang_default>\d+|None)_(?P<zp_user_id>\d+|None)$'
            match = re.match(overview_ident_regex, zp_overview_ident)
            if match:
                match_groupdict = match.groupdict()
                zp_film_collection_overview_id = match_groupdict['zp_film_collection_overview_id']
                zp_lang_id = match_groupdict['zp_lang_id']
                main_default = match_groupdict['main_default']
                lang_default = match_groupdict['lang_default']
                zp_overview_user_id = match_groupdict['zp_user_id']
                log.debug('zp_overview_ident %s', zp_overview_ident)
                log.debug('zp_film_collection_overview_id %s, zp_lang_id %s, lang_default %s,'
                          ' main_default %s, zp_user_id %s', zp_film_collection_overview_id, zp_lang_id,
                          lang_default, main_default, zp_overview_user_id)
                if zp_film_collection_overview_id.isdigit():
                    zp_film_collection_overview_id = int(zp_film_collection_overview_id)
                    if zp_film_collection_overview_id > 0:
                        try:
                            zp_film_collection_overview = session.query(TABLES.ZP_FILM_COLLECTION_OVERVIEW).filter(
                                TABLES.ZP_FILM_COLLECTION_OVERVIEW.ID == zp_film_collection_overview_id,
                                TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_FILM_COLLECTION_ID == zp_film_collection_id
                            ).one()
                        except orm.exc.NoResultFound:
                            log.error('could not find entry in ZP_FILM_COLLECTION_OVERVIEW with ID %s and ZP_FILM_COLLECTION_ID %s',
                                      zp_film_collection_overview_id, zp_film_collection_id)
                        else:
                            # todo add more logic here for authorised edits
                            if not (zp_film_collection_overview.ZP_USER_ID > 0 and
                                        (zp_film_collection_overview.ZP_USER_ID != int(zp_overview_user_id))):
                                zp_film_collection_overview.OVERVIEW = overview
                                if commit(session):
                                    update_film_collection_last_mod(self.Session, zp_film_collection_id)
                                    self.set_user_zp_film_collection_entity_xref(zp_user_id, zp_film_collection_id, 2, zp_film_collection_overview_id)
                elif zp_film_collection_overview_id == 'None':
                    if main_default == '1':
                        log.debug('main default == 1')
                    elif lang_default == '1':
                        log.debug('lang_default == 1')
                    elif zp_overview_user_id.isdigit():
                        zp_film_collection_overview_id = self.add_film_collection_overview(zp_film_collection_id, zp_user_lang, 0, zp_user_id,
                                                                     0, 0, overview)
                        if zp_film_collection_overview_id > 0:
                            self.set_user_zp_film_collection_entity_xref(zp_user_id, zp_film_collection_id, 2, zp_film_collection_overview_id)
                            update_film_collection_last_mod(self.Session, zp_film_collection_id)
                        log.debug('zp_overview_user_id %s is digit', zp_overview_user_id)
            else:
                log.error('zp_overview_ident %s failed to match overview_ident_regex %s', zp_overview_ident,
                          overview_ident_regex)
        # todo remove overview by sending empty overview
        session.close()

    def update_film_collection_title(self, zp_film_collection_id, zp_user_id, zp_title_ident,
                          title):
        session = self.Session()
        if title:
            zp_user_lang = self.get_user_lang(zp_user_id)
            title_ident_regex = r'^(?P<zp_film_collection_title_id>\d+|None)_(?P<zp_lang_id>\d+|None)_' \
                                r'(?P<zp_film_collection_title_type_id>\d+|None)_(?P<main_default>\d+|None)_' \
                                r'(?P<lang_default>\d+|None)_(?P<zp_user_id>\d+|None)$'
            match = re.match(title_ident_regex, zp_title_ident)
            if match:
                match_groupdict = match.groupdict()
                zp_film_collection_title_id = match_groupdict['zp_film_collection_title_id']
                zp_lang_id = match_groupdict['zp_lang_id']
                zp_film_collection_title_type_id = match_groupdict['zp_film_collection_title_type_id']
                main_default = match_groupdict['main_default']
                lang_default = match_groupdict['lang_default']
                zp_title_user_id = match_groupdict['zp_user_id']
                log.debug('zp_title_ident %s', zp_title_ident)
                log.debug('zp_film_collection_title_id %s, zp_lang_id %s, zp_film_collection_title_type_id %s, lang_default %s,'
                          ' main_default %s, zp_user_id %s', zp_film_collection_title_id, zp_lang_id,
                          zp_film_collection_title_type_id, lang_default, main_default, zp_title_user_id)
                if zp_film_collection_title_id.isdigit():
                    zp_film_collection_title_id = int(zp_film_collection_title_id)
                    if zp_film_collection_title_id > 0:
                        try:
                            zp_film_collection_title = session.query(TABLES.ZP_FILM_COLLECTION_TITLE).filter(
                                TABLES.ZP_FILM_COLLECTION_TITLE.ID == zp_film_collection_title_id,
                                TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_ID == zp_film_collection_id
                            ).one()
                        except orm.exc.NoResultFound:
                            log.error('could not find entry in ZP_FILM_COLLECTION_TITLE with ID %s and ZP_FILM_COLLECTION_ID %s',
                                      zp_film_collection_title_id, zp_film_collection_id)
                        else:
                            # todo add more logic here for authorised edits
                            if not (zp_film_collection_title.ZP_USER_ID > 0 and
                                        (zp_film_collection_title.ZP_USER_ID != int(zp_title_user_id))):
                                zp_film_collection_title.TITLE = title
                                if commit(session):
                                    update_film_collection_last_mod(self.Session, zp_film_collection_id)
                                    self.set_user_zp_film_collection_entity_xref(zp_user_id, zp_film_collection_id, 1, zp_film_collection_title_id)
                elif zp_film_collection_title_id == 'None':
                    if main_default == '1':
                        log.debug('main default == 1')
                    elif lang_default == '1':
                        log.debug('lang_default == 1')
                    elif zp_title_user_id.isdigit():
                        zp_film_collection_title_id = self.add_film_collection_title(zp_film_collection_id, 1, zp_user_lang, 0, zp_user_id,
                                                               0, 0, title)
                        if zp_film_collection_title_id > 0:
                            self.set_user_zp_film_collection_entity_xref(zp_user_id, zp_film_collection_id, 1, zp_film_collection_title_id)
                            update_film_collection_last_mod(self.Session, zp_film_collection_id)
                        log.debug('zp_title_user_id %s is digit', zp_title_user_id)
            else:
                log.error('zp_title_ident %s failed to match title_ident_regex %s', zp_title_ident,
                          title_ident_regex)
        # todo remove title by sending empty title
        session.close()

    def set_user_zp_film_collection_entity_xref(self, zp_user_id, zp_film_collection_id, zp_film_collection_entity_type_id, zp_film_collection_entity_id):
        session = self.Session()
        try:
            zp_user_film_collection_entity_xref = session.query(TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF).filter(
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ID == zp_film_collection_id,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_TYPE_ID == zp_film_collection_entity_type_id
            ).one()
        except orm.exc.NoResultFound:
            log.error('there should allready be a entry here unless a film_collection and been added'
                      ' but not yet gone through data and user specifics')
            add_zp_user_film_collection_entity_xref = TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF(ZP_USER_ID=zp_user_id,
                                                                           ZP_FILM_COLLECTION_ID=zp_film_collection_id,
                                                                           ZP_FILM_COLLECTION_ENTITY_TYPE_ID=zp_film_collection_entity_type_id,
                                                                           ZP_FILM_COLLECTION_ENTITY_ID=zp_film_collection_entity_id,
                                                                           FORCED=1,
                                                                           LAST_UPDATE_DATETIME=date_time())
            session.add(add_zp_user_film_collection_entity_xref)
            commit(session)
        else:
            zp_user_film_collection_entity_xref.ZP_FILM_COLLECTION_ENTITY_ID = zp_film_collection_entity_id
            zp_user_film_collection_entity_xref.FORCED = 1
            zp_user_film_collection_entity_xref.LAST_UPDATE_DATETIME = date_time()
            commit(session)
        session.close()

    def add_film_collection_title(self, zp_film_collection_id, zp_film_collection_title_type_id, zp_lang_id, zp_eapi_id, zp_user_id,
                       lang_default, main_default, title):
        session = self.Session()
        zp_film_collection_title_id = None
        add_zp_film_collection_title = TABLES.ZP_FILM_COLLECTION_TITLE(ZP_FILM_COLLECTION_ID=zp_film_collection_id,
                                                 ZP_FILM_COLLECTION_TITLE_TYPE_ID=zp_film_collection_title_type_id,
                                                 ZP_LANG_ID=zp_lang_id,
                                                 ZP_EAPI_ID=zp_eapi_id,
                                                 ZP_USER_ID=zp_user_id,
                                                 LANG_DEFAULT=lang_default,
                                                 MAIN_DEFAULT=main_default,
                                                 TITLE=title)
        session.add(add_zp_film_collection_title)
        if commit(session):
            zp_film_collection_title_id = add_zp_film_collection_title.ID
        session.close()
        return zp_film_collection_title_id

    def add_film_collection_overview(self, zp_film_collection_id, zp_lang_id, zp_eapi_id, zp_user_id,
                          lang_default, main_default, overview):
        session = self.Session()
        zp_film_collection_overview_id = None
        add_zp_film_collection_overview = TABLES.ZP_FILM_COLLECTION_OVERVIEW(ZP_FILM_COLLECTION_ID=zp_film_collection_id,
                                                       ZP_LANG_ID=zp_lang_id,
                                                       ZP_EAPI_ID=zp_eapi_id,
                                                       ZP_USER_ID=zp_user_id,
                                                       LANG_DEFAULT=lang_default,
                                                       MAIN_DEFAULT=main_default,
                                                       OVERVIEW=overview)
        session.add(add_zp_film_collection_overview)
        if commit(session):
            zp_film_collection_overview_id = add_zp_film_collection_overview.ID
        session.close()
        return zp_film_collection_overview_id

    def set_user_film_collection_raw_image(self, zp_film_collection_id, image_type, zp_film_collection_raw_image_id, zp_user_id):
        success = False
        session = self.Session()
        try:
            session.query(TABLES.ZP_FILM_COLLECTION_RAW_IMAGE).filter(
                TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_ID == zp_film_collection_id,
                TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_TYPE_ID == self.image_type_id_dict[image_type],
                TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ID == zp_film_collection_raw_image_id
            ).one()
        except orm.exc.NoResultFound:
            log.error('could not find entry in ZP_FILM_COLLECTION_RAW_IMAGE for ZP_ENTITY_ID %s,'
                      'ZP_ENTITY_TYPE_ID %s, ID %s', zp_film_collection_id, self.image_type_id_dict[image_type],
                      zp_film_collection_raw_image_id)
        else:
            try:
                zp_user_film_collection_entity_xref = session.query(TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF).filter(
                    TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                    TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ID == zp_film_collection_id,
                    TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_TYPE_ID == self.image_film_collection_entity_type_id_dict[
                        image_type]
                ).one()
            except orm.exc.NoResultFound:
                add_zp_user_film_collection_entity_xref = TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF(
                    ZP_USER_ID=zp_user_id,
                    ZP_FILM_COLLECTION_ID=zp_film_collection_id,
                    ZP_FILM_COLLECTION_ENTITY_TYPE_ID=self.image_film_collection_entity_type_id_dict[image_type],
                    ZP_FILM_COLLECTION_ENTITY_ID=zp_film_collection_raw_image_id,
                    FORCED=1,
                    LAST_UPDATE_DATETIME=date_time()
                )
                session.add(add_zp_user_film_collection_entity_xref)
                if commit(session):
                    update_film_collection_last_mod(self.Session, zp_film_collection_id)
                    success = True
            else:
                zp_user_film_collection_entity_xref.FORCED = 1
                zp_user_film_collection_entity_xref.ZP_FILM_COLLECTION_ENTITY_ID = zp_film_collection_raw_image_id
                zp_user_film_collection_entity_xref.LAST_UPDATE_DATETIME = date_time()
                if commit(session):
                    update_film_collection_last_mod(self.Session, zp_film_collection_id)
                    success = True
        session.close()
        return success

    def film_collection_raw_image_list(self, zp_film_collection_id, image_type_id):
        session = self.Session()
        raw_image_list = []
        try:
            raw_images = session.query(TABLES.ZP_FILM_COLLECTION_RAW_IMAGE).filter(
                TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_ID == zp_film_collection_id,
                TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_TYPE_ID == image_type_id
            ).order_by(TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_EAPI_ID.asc(),
                       TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_USER_ID.asc()).all()
        except orm.exc.NoResultFound:
            log.debug('no images for zp_film_collection_id %s, image_type_id %s found in ZP_FILM_COLLECTION_RAW_IMAGE',
                      zp_film_collection_id, image_type_id)
        else:
            for raw_image in raw_images:
                raw_image_list.append({'image_url': '/i/raw/film_collection/%s' % (raw_image.ID),
                                       'source_type': 'eapi' if raw_image.ZP_EAPI_ID > 0 else 'user',
                                       'zp_eapi_id': raw_image.ZP_EAPI_ID,
                                       'zp_film_collection_raw_image_id': raw_image.ID})
        log.debug(raw_image_list)
        session.close()
        return raw_image_list

    def get_film_collection_raw_image_filename(self, zp_film_collection_raw_image_id):
        session = self.Session()
        raw_image_filename = None
        zp_film_collection_id = None
        try:
            zp_film_collection_raw_image = session.query(TABLES.ZP_FILM_COLLECTION_RAW_IMAGE).filter(
                TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ID == zp_film_collection_raw_image_id).one()
        except orm.exc.NoResultFound:
            log.error('no entry for zp_film_collection_raw_image_id %s, ZP_FILM_COLLECTION_RAW_IMAGE',
                      zp_film_collection_raw_image_id)
        else:
            raw_image_filename = zp_film_collection_raw_image.FILENAME
            zp_film_collection_id = zp_film_collection_raw_image.ZP_ENTITY_ID
        session.close()
        return raw_image_filename, zp_film_collection_id

    def get_film_collection_rendered_image_filename(self, zp_film_collection_rendered_image_id):
        session = self.Session()
        rendered_image_filename = None
        zp_film_collection_id = None
        template_name = None
        image_type_by_id_dict = {1: 'icon', 2: 'synopsis', 3: 'poster', 4:'backdrop'}
        image_sub_type_by_id_dict = {1: '',
                                     2: '_sel',
                                     3: '_watched',
                                     4: '_watched_sel'}
        try:
            zp_film_collection_rendered_image = session.query(
                TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ZP_FILM_COLLECTION_IMAGE_TYPE_ID,
                TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ZP_FILM_COLLECTION_ID,
                TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
                TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.HASH,
                TABLES.ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.EXT,
                TABLES.ZP_TEMPLATE.REF_NAME
            ).join(
                TABLES.ZP_TEMPLATE, TABLES.ZP_TEMPLATE.ID == TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID
            ).join(
                TABLES.ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF,
                and_(
                    TABLES.ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH_ID ==
                    TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ID,
                    TABLES.ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == 1
                )
            ).filter(
                TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ID == zp_film_collection_rendered_image_id
            ).one()
        except orm.exc.NoResultFound:
            log.debug('no entry for zp_film_collection_rendered_image_id %s, ZP_FILM_COLLECTION_IMAGE_RENDER_HASH',
                      zp_film_collection_rendered_image_id)
        else:
            rendered_image_filename = '.%s%s.%s.%s' % (
            image_type_by_id_dict[zp_film_collection_rendered_image.ZP_FILM_COLLECTION_IMAGE_TYPE_ID],
            image_sub_type_by_id_dict[zp_film_collection_rendered_image.ZP_IMAGE_SUB_TYPE],
            zp_film_collection_rendered_image.HASH,
            zp_film_collection_rendered_image.EXT)
            zp_film_collection_id = zp_film_collection_rendered_image.ZP_FILM_COLLECTION_ID
            template_name = zp_film_collection_rendered_image.REF_NAME
        session.close()
        return rendered_image_filename, template_name, zp_film_collection_id

    def add_new_film_collection_raw_image(self, zp_film_collection_id, zp_user_id, zp_entity_type_id,
                                          new_film_collection_image_filename,
                               image_reference):
        session = self.Session()
        add_zp_film_collection_raw_image = TABLES.ZP_FILM_COLLECTION_RAW_IMAGE(ZP_EAPI_ID=0,
                                                         ZP_EAPI_IMAGE_REF=image_reference,
                                                         ZP_ENTITY_TYPE_ID=zp_entity_type_id,
                                                         ZP_ENTITY_ID=zp_film_collection_id,
                                                         ZP_USER_ID=zp_user_id,
                                                         FILENAME=new_film_collection_image_filename)
        session.add(add_zp_film_collection_raw_image)
        commit(session)
        session.close()
        return True

    def film_collection_films(self, zp_film_collection_id, zp_user_id):
        session = self.Session()
        film_list = []
        films = session.query(TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                      TABLES.ZP_FILM_TITLE.TITLE
        ).join(
            TABLES.ZP_FILM_COLLECTION_XREF,
            TABLES.ZP_FILM_COLLECTION_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID
        ).join(
            TABLES.ZP_USER_FILM_ENTITY_XREF,
            and_(TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                 TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1,
                 TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID == TABLES.ZP_FILM_TITLE.ID)
        ).filter(
            TABLES.ZP_FILM_COLLECTION_XREF.ZP_FILM_COLLECTION_ID == zp_film_collection_id,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == zp_user_id
        ).order_by(
            TABLES.ZP_FILM_TITLE.TITLE.asc()
        ).all()
        session.close()
        if films is not None:
            for film in films:
                film_list.append({'zp_film_id':film.ZP_FILM_ID,
                                  'title': film.TITLE})
        return film_list