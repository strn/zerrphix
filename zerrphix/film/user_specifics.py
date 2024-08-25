# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging

from sqlalchemy import func, orm

from zerrphix.db import commit
from zerrphix.db.tables import TABLES
from zerrphix.film.util import user_film_title, user_film_collection_title, user_film_raw_image, \
    user_film_overview, user_film_collection_overview, user_film_collection_raw_image
from zerrphix.util.text import date_time
from zerrphix.film.base import FilmBase

import copy
log = logging.getLogger(__name__)


class User_Specifics(FilmBase):
    """
    """

    def __init__(self, **kwargs):
        super(User_Specifics, self).__init__(**kwargs)

    def get_user_processing_list(self, zp_user_id):
        return_list = []
        session = self.Session()
        qry_users = session.query(TABLES.ZP_USER).filter(
            TABLES.ZP_USER.ID < zp_user_id,
            TABLES.ZP_USER.ENABLED == 1)
        if qry_users.count() > 0:
            users = qry_users.order_by(TABLES.ZP_USER.ID.desc()).limit(1)
            for user in users:
                return_list.append(user.ID)
        session.close()
        return return_list

    def get_film_processing_list(self, zp_user_id, zp_film_id, zp_film_entity_type):
        return_list = []
        session = self.Session()
        qry_film = session.query(TABLES.ZP_FILM).filter(
            TABLES.ZP_FILM.ID < zp_film_id,
            ~TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID
                ).filter(
                    TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                    TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == zp_film_entity_type,
                    TABLES.ZP_USER_FILM_ENTITY_XREF.LAST_UPDATE_DATETIME >= TABLES.ZP_FILM.LAST_EDIT_DATETIME
                )),
            ~TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID
                ).filter(
                    TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                    TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == zp_film_entity_type,
                    TABLES.ZP_USER_FILM_ENTITY_XREF.FORCED == 1
                ))
        )
        if qry_film.count() > 0:
            films = qry_film.order_by(TABLES.ZP_FILM.ID.desc()).limit(100)
            for film in films:
                return_list.append(film.ID)
        session.close()
        return return_list

    def get_film_collection_processing_list(self, zp_user_id, zp_film_collection_id, zp_film_entity_type):
        return_list = []
        session = self.Session()
        qry_film_collection = session.query(TABLES.ZP_FILM_COLLECTION).filter(
            TABLES.ZP_FILM_COLLECTION.ID < zp_film_collection_id,
            TABLES.ZP_FILM_COLLECTION.ID.in_(
                session.query(
                    TABLES.ZP_FILM.ZP_FILM_COLLECTION_ID)
            ),
            ~TABLES.ZP_FILM_COLLECTION.ID.in_(
                session.query(
                    TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ID
                ).filter(
                    TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                    TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_TYPE_ID == zp_film_entity_type,
                    TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.LAST_UPDATE_DATETIME >=
                    TABLES.ZP_FILM_COLLECTION.LAST_EDIT_DATETIME)),
            ~TABLES.ZP_FILM_COLLECTION.ID.in_(
                session.query(
                    TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ID
                ).filter(
                    TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                    TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_TYPE_ID == zp_film_entity_type,
                    TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.FORCED == 1
                ))
        )
        if qry_film_collection.count() > 0:
            films = qry_film_collection.order_by(TABLES.ZP_FILM_COLLECTION.ID.desc()).limit(100)
            for film in films:
                return_list.append(film.ID)
        session.close()
        return return_list

    def process_user(self, zp_user_id):
        session = self.Session()
        eapi_order, title_type_order, lang_list = self.user_prefs(self.library_config_dict['id'], zp_user_id)
        log.debug('process_user_film')
        self.process_user_film(zp_user_id, eapi_order, title_type_order, lang_list)
        log.debug('process_user_film_collection')
        self.process_user_film_collection(zp_user_id, eapi_order, title_type_order, lang_list)
        session.close()

    def process_user_film(self, zp_user_id, eapi_order, title_type_order, lang_list):
        session = self.Session()
        max_film_id = session.query(func.max(TABLES.ZP_FILM.ID)).one()[0]
        session.close()
        zp_film_entity_type_list = [1,2,3,4]
        if isinstance(max_film_id, int):
            for zp_film_entity_type_id in zp_film_entity_type_list:
                zp_film_id = max_film_id + 1
                self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                             6,
                                                             'User %s, Film %s/%s' % (
                                                                 zp_user_id, zp_film_id, max_film_id
                                                             ))
                user_film_processing_complete = False
                while user_film_processing_complete is False:
                    film_processing_list = self.get_film_processing_list(zp_user_id, zp_film_id,
                                                                         zp_film_entity_type_id)
                    if film_processing_list:
                        for film_processing_id in film_processing_list:
                            zp_film_id = film_processing_id
                            self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                             6,
                                                             'User %s, Film %s/%s' % (
                                                                 zp_user_id, zp_film_id, max_film_id
                                                             ))
                            if zp_film_entity_type_id == 1:
                                self.process_user_film_title(zp_user_id, zp_film_id, eapi_order, title_type_order,
                                                             lang_list, zp_film_entity_type_id)
                            elif zp_film_entity_type_id == 2:
                                self.process_user_film_overview(zp_user_id, zp_film_id, eapi_order, title_type_order,
                                                             lang_list, zp_film_entity_type_id)
                            elif zp_film_entity_type_id == 3:
                                self.process_user_film_raw_image(zp_user_id, zp_film_id, eapi_order, lang_list,
                                                                 1, zp_film_entity_type_id)
                            elif zp_film_entity_type_id == 4:
                                self.process_user_film_raw_image(zp_user_id, zp_film_id, eapi_order, lang_list,
                                                                 2, zp_film_entity_type_id)
                    else:
                        user_film_processing_complete = True

    def process_user_film_raw_image(self, zp_user_id, zp_film_id, eapi_order, lang_list, image_type_id,
                                    zp_film_entity_type_id):
        session = self.Session()
        zp_raw_image_id = user_film_raw_image(session, zp_film_id, eapi_order,
                                           lang_list, zp_user_id, image_type_id)
        session.close()
        self.set_zp_film_entity_type(zp_user_id, zp_film_id, zp_raw_image_id, zp_film_entity_type_id)

    def set_zp_film_entity_type(self, zp_user_id, zp_film_id, zp_film_entity_id, zp_film_entity_type_id):
        session = self.Session()
        if not isinstance(zp_film_entity_id, int) or zp_film_entity_id < 1:
            log.warning('zp_film_entity_id %s is not int and greater than 0', zp_film_entity_id)
            zp_film_entity_id = None
        try:
            zp_user_film_title_xref = session.query(TABLES.ZP_USER_FILM_ENTITY_XREF).filter(
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == zp_film_id,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == zp_film_entity_type_id
            ).one()
        except orm.exc.NoResultFound:
            add_zp_user_film_title_xref = TABLES.ZP_USER_FILM_ENTITY_XREF(
                ZP_FILM_ID=zp_film_id,
                ZP_USER_ID=zp_user_id,
                ZP_FILM_ENTITY_ID=zp_film_entity_id,
                ZP_FILM_ENTITY_TYPE_ID = zp_film_entity_type_id,
                LAST_UPDATE_DATETIME=date_time())
            session.add(add_zp_user_film_title_xref)
            commit(session)
        else:
            if zp_user_film_title_xref.ZP_FILM_ENTITY_ID != zp_film_entity_id:
                zp_user_film_title_xref.ZP_FILM_ENTITY_ID = zp_film_entity_id
            zp_user_film_title_xref.LAST_UPDATE_DATETIME = date_time()
            commit(session)
        session.close()

    def process_user_film_title(self, zp_user_id, zp_film_id, eapi_order, title_type_order, lang_list,
                                zp_film_entity_type_id):
        session = self.Session()
        zp_film_title_id = user_film_title(session, zp_film_id, eapi_order,
                                           title_type_order, lang_list, zp_user_id)
        session.close()
        self.set_zp_film_entity_type(zp_user_id, zp_film_id, zp_film_title_id, zp_film_entity_type_id)
    def process_user_film_overview(self, zp_user_id, zp_film_id, eapi_order, title_type_order, lang_list,
                                zp_film_entity_type_id):
        session = self.Session()
        zp_film_title_id = user_film_overview(session, zp_film_id, eapi_order,
                                           title_type_order, lang_list, zp_user_id)
        session.close()
        self.set_zp_film_entity_type(zp_user_id, zp_film_id, zp_film_title_id, zp_film_entity_type_id)

    def process_user_film_synopsis(self, zp_user_id, zp_film_id):
        pass

    def process_user_film_image(self, zp_user_id, zp_film_id):
        pass

    def process_user_film_collection(self, zp_user_id, eapi_order, title_type_order, lang_list):
        log.debug('process_user_film_collection')
        session = self.Session()
        max_film_collection_id = session.query(func.max(TABLES.ZP_FILM_COLLECTION.ID)).one()[0]
        session.close()
        zp_film_collection_entity_type_list = [1,2,3,4]
        if isinstance(max_film_collection_id, int):
            log.debug('max_film_collection_id %s', max_film_collection_id)
            for zp_film_collection_entity_type in zp_film_collection_entity_type_list:
                log.debug('zp_film_collection_entity_type %s', zp_film_collection_entity_type)
                zp_film_collection_id = max_film_collection_id + 1
                self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                             6,
                                                             'User %s, Film Collection %s/%s' % (
                                                                 zp_user_id, zp_film_collection_id,
                                                                 max_film_collection_id
                                                             ))
                user_film_collection_processing_complete = False
                while user_film_collection_processing_complete is False:
                    film_collection_processing_list = self.get_film_collection_processing_list(zp_user_id,
                                                                                               zp_film_collection_id,
                                                                                        zp_film_collection_entity_type)
                    log.debug('zp_user_id %s, film_collection_processing_list %s,'
                              'zp_film_collection_id %s, zp_film_collection_entity_type %s',
                              zp_user_id,
                              film_collection_processing_list,
                              zp_film_collection_id,
                              zp_film_collection_entity_type)
                    if film_collection_processing_list:
                        for film_collection_processing_id in film_collection_processing_list:
                            zp_film_collection_id = film_collection_processing_id
                            if zp_film_collection_entity_type == 1:
                                self.process_user_film_collection_title(zp_user_id, zp_film_collection_id,
                                                                    eapi_order, title_type_order, lang_list)
                            elif zp_film_collection_entity_type == 2:
                                self.process_user_film_collection_overview(zp_user_id, zp_film_collection_id,
                                                                    eapi_order, lang_list)
                            elif zp_film_collection_entity_type == 3:
                                self.process_user_film_collection_raw_image(zp_user_id, zp_film_collection_id,
                                                                            eapi_order, lang_list,
                                                                 1, zp_film_collection_entity_type)
                            elif zp_film_collection_entity_type == 4:
                                self.process_user_film_collection_raw_image(zp_user_id, zp_film_collection_id,
                                                                            eapi_order, lang_list,
                                                                 2, zp_film_collection_entity_type)
                    else:
                        user_film_collection_processing_complete = True

    def process_user_film_collection_raw_image(self, zp_user_id, zp_film_collection_id, eapi_order, lang_list,
                                               image_type_id,
                                    zp_film_entity_type_id):
        session = self.Session()
        zp_raw_image_id = user_film_collection_raw_image(session, zp_film_collection_id, eapi_order,
                                           lang_list, zp_user_id, image_type_id)
        session.close()
        self.set_zp_film_collection_entity_type(zp_user_id, zp_film_collection_id, zp_raw_image_id,
                                                zp_film_entity_type_id)

    def set_zp_film_collection_entity_type(self, zp_user_id, zp_film_collection_id, zp_film_entity_id,
                                           zp_film_entity_type_id):
        session = self.Session()
        if not isinstance(zp_film_entity_id, int) or zp_film_entity_id < 1:
            log.warning('zp_film_entity_id %s is not int and greater than 0', zp_film_entity_id)
            zp_film_entity_id = None
        try:
            zp_user_film_title_xref = session.query(TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF).filter(
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ID == zp_film_collection_id,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_TYPE_ID == zp_film_entity_type_id
            ).one()
        except orm.exc.NoResultFound:
            add_zp_user_film_title_xref = TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF(
                ZP_FILM_COLLECTION_ID=zp_film_collection_id,
                ZP_USER_ID=zp_user_id,
                ZP_FILM_COLLECTION_ENTITY_ID=zp_film_entity_id,
                ZP_FILM_COLLECTION_ENTITY_TYPE_ID = zp_film_entity_type_id,
                LAST_UPDATE_DATETIME=date_time())
            session.add(add_zp_user_film_title_xref)
            commit(session)
        else:
            if zp_user_film_title_xref.ZP_FILM_COLLECTION_ENTITY_ID != zp_film_entity_id:
                zp_user_film_title_xref.ZP_FILM_COLLECTION_ENTITY_ID = zp_film_entity_id
            zp_user_film_title_xref.LAST_UPDATE_DATETIME = date_time()
            commit(session)
        session.close()

    def process_user_film_collection_title(self, zp_user_id, zp_film_collection_id, eapi_order, title_type_order,
                                           lang_list):
        session = self.Session()
        zp_film_collection_title_id = user_film_collection_title(session,
                                                                 zp_film_collection_id,
                                                                 eapi_order,
                                                                 title_type_order,
                                                                 lang_list,
                                                                 zp_user_id)
        if not isinstance(zp_film_collection_title_id, int) or zp_film_collection_title_id < 1:
            log.warning('zp_film_collection_title_id %s is not int and greater than 0', zp_film_collection_title_id)
            zp_film_collection_title_id = None
        try:
            zp_user_film_collection_title_xref = session.query(TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF).filter(
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ID == zp_film_collection_id,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_TYPE_ID == 1).one()
        except orm.exc.NoResultFound:
            add_zp_user_film_collection_title_xref = TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF(
                ZP_FILM_COLLECTION_ID=zp_film_collection_id,
                ZP_USER_ID=zp_user_id,
                ZP_FILM_COLLECTION_ENTITY_ID=zp_film_collection_title_id,
                ZP_FILM_COLLECTION_ENTITY_TYPE_ID = 1,
                LAST_UPDATE_DATETIME=date_time())
            session.add(add_zp_user_film_collection_title_xref)
            commit(session)
        else:
            if zp_user_film_collection_title_xref.ZP_FILM_COLLECTION_ENTITY_ID != zp_film_collection_title_id:
                zp_user_film_collection_title_xref.ZP_FILM_COLLECTION_ENTITY_ID = zp_film_collection_title_id
            zp_user_film_collection_title_xref.LAST_UPDATE_DATETIME = date_time()
            commit(session)
        session.close()

    def process_user_film_collection_overview(self, zp_user_id, zp_film_collection_id, eapi_order,
                                           lang_list):
        session = self.Session()
        zp_film_collection_title_id = user_film_collection_overview(session,
                                                                 zp_film_collection_id,
                                                                 eapi_order,
                                                                 lang_list,
                                                                 zp_user_id)
        if not isinstance(zp_film_collection_title_id, int) or zp_film_collection_title_id < 1:
            log.warning('zp_film_collection_title_id %s is not int and greater than 0', zp_film_collection_title_id)
            zp_film_collection_title_id = None
        try:
            zp_user_film_collection_title_xref = session.query(TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF).filter(
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ID == zp_film_collection_id,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_TYPE_ID == 2).one()
        except orm.exc.NoResultFound:
            add_zp_user_film_collection_title_xref = TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF(
                ZP_FILM_COLLECTION_ID=zp_film_collection_id,
                ZP_USER_ID=zp_user_id,
                ZP_FILM_COLLECTION_ENTITY_ID=zp_film_collection_title_id,
                ZP_FILM_COLLECTION_ENTITY_TYPE_ID = 2,
                LAST_UPDATE_DATETIME=date_time())
            session.add(add_zp_user_film_collection_title_xref)
            commit(session)
        else:
            if zp_user_film_collection_title_xref.ZP_FILM_COLLECTION_ENTITY_ID != zp_film_collection_title_id:
                zp_user_film_collection_title_xref.ZP_FILM_COLLECTION_ENTITY_ID = zp_film_collection_title_id
            zp_user_film_collection_title_xref.LAST_UPDATE_DATETIME = date_time()
            commit(session)
        session.close()

    def process(self):
        session = self.Session()
        max_user_id = session.query(func.max(TABLES.ZP_USER.ID)).filter(
            TABLES.ZP_USER.ENABLED == 1).one()[0]
        session.close()
        user_processing_complete = False
        if isinstance(max_user_id, int):
            zp_user_id = max_user_id + 1
            while user_processing_complete is False:
                user_processing_list = self.get_user_processing_list(zp_user_id)
                if user_processing_list:
                    for user_processing_id in user_processing_list:
                        zp_user_id = user_processing_id
                        self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                     6,
                                                                     'User %s/%s' % (
                                                                         zp_user_id, max_user_id
                                                                     ))
                        self.process_user(zp_user_id)
                else:
                    user_processing_complete = True
