# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import sys
from datetime import datetime
from datetime import timedelta

from sqlalchemy import func, orm

from zerrphix.db import flush, commit
from zerrphix.db.tables import TABLES
from zerrphix.film.util import update_film_last_mod, update_film_collection_last_mod
from zerrphix.plugin import load_plugins
from zerrphix.util import list1_not_in_list2
from zerrphix.util.plugin import create_eapi_plugins_list, create_eapi_dict
from zerrphix.util.text import date_time
from six import string_types
from six import text_type
from types import MethodType

#from zerrphix.util import iso_639_part1_from_zp_lang_id
#from zerrphix.util import set_retry, get_user_langs, check_can_retry
from zerrphix.film.base import FilmBase

log = logging.getLogger(__name__)


class Data(FilmBase):
    """Get Data for films (actors, runtime, synop etc...)
    """

    def __init__(self, **kwargs):
        super(Data, self).__init__(**kwargs)
        """Data __init__

            Args:
                | args (list): Passed through args from the command line.
                | Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.
        """
        self, self.eapi_film_plugins_access_list, loaded_plugins = create_eapi_plugins_list(
            'film', sys.modules, load_plugins(self.args), self)
        if not self.eapi_film_plugins_access_list:
            raise Exception(('There not any entries in eapi_film_plugins_access_list'
                             ' therefore scanning is pointless'))
        session = self.Session()
        self.eapi_dict = create_eapi_dict(session)
        session.close()
        #self.iso_639_part1_from_zp_lang_id = MethodType(iso_639_part1_from_zp_lang_id, self)
        self.data_keys = ['genres', 'title', 'original_title',
                          'overview', 'release_date', 'runtime',
                          'rating', 'credits', 'belongs_to_collection']
        #self.get_user_langs = MethodType(get_user_langs, self)
        #self.set_retry = MethodType(set_retry, self)
        #self.check_can_retry = MethodType(check_can_retry, self)

    def acquire(self):
        user_langs = self.get_all_user_library_langs(1)
        # todo optionise adding english as a fallback when user specifics are done
        if 1823 not in user_langs:
            user_langs[1823] = 'English'
        self.user_langs = user_langs
        self.acquire_film_data()
        self.acquire_film_collection_data()

    def acquire_film_data(self):
        """Kick of the process of gathering film data

            Attributes:
            | film_data:
            | 	{
            | 		"adult":true|false,
            | 		"genres":[
            | 					{
            | 						"id": unicode,
            | 						"Name": unicode
            | 					}
            | 				],
            | 		"title": unicode,
            | 		"original_title": unicode,
            | 		"overview": unicode,
            | 		"release_date": YYYY-MM-DD
            | 		"runtime": int
            | 		"rating": int (min 1 max 10)
            | 		"credits": {
            | 						"cast":
            | 								[
            | 									{
            | 										"id": unicode,
            | 										"name": unicode,
            | 										"character": unicode,
            | 										"order": int
            | 									}
            | 								],
            | 						"crew":
            | 								[
            | 									{
            | 										"id": unicode,
            | 										"name": unicode,
            | 										"job": unicode,
            | 										"order": int
            | 									}
            | 								]
            | 					}
            | 	}

        """
        # Get films that do not exist in any of the tables
        # order by film ID desc (prcessed newly added films first)
        # TODO: update film update_datetime
        session = self.Session()
        max_film_id = session.query(func.max(TABLES.ZP_FILM.ID)).one()[0]
        session.close()
        if isinstance(max_film_id, int):
            for zp_lang_id in self.user_langs:
                self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                             5,
                                                             'LANG: %s' % self.user_langs[zp_lang_id])
                for eapi in self.eapi_film_plugins_access_list:
                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                5,
                                                                 'LANG: %s, EAPI: %s' % (
                                                                     self.user_langs[zp_lang_id],
                                                                     eapi
                                                                 ))
                    log.debug('eapi %s', eapi)
                    if hasattr(getattr(self, eapi), 'get_film_data'):
                        log.debug('zp_lang_id %s', zp_lang_id)
                        ZP_FILM_ID = max_film_id + 1
                        lang_processing_complete = False
                        while lang_processing_complete is False:
                            entity_processing_list = self.get_film_data_processing_no_retry(ZP_FILM_ID,
                                                                                            eapi, zp_lang_id)

                            log.debug('eapi %s, zp_lang_id %s, entity_processing_list %s',
                                      eapi, zp_lang_id, entity_processing_list)
                            if entity_processing_list:
                                for enitity_id in entity_processing_list:
                                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                                 5,
                                                                                 'LANG: %s EAPI: %s FILM: %s/%s' % (
                                                                                     self.user_langs[zp_lang_id],
                                                                                     eapi,
                                                                                     enitity_id,
                                                                                     max_film_id
                                                                                 ))
                                    ZP_FILM_ID = enitity_id
                                    log.debug('getting film data for ZP_FILM_ID %s, eapi %s, lang %s',
                                              ZP_FILM_ID, eapi, zp_lang_id)
                                    self.process_entity(ZP_FILM_ID, eapi, zp_lang_id)
                                    # print(ZP_FILM_ID)
                            # raise SystemExit
                            else:
                                lang_processing_complete = True
                    else:
                        log.info('eapi %s does not have get_film_data', eapi)
            # raise SystemExit
            if self.check_can_retry(1) is True:
                log.debug('Retrying Film Data')
                for zp_lang_id in self.user_langs:
                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                 5,
                                                                 'LANG: %s' % self.user_langs[zp_lang_id])
                    for eapi in self.eapi_film_plugins_access_list:
                        self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                    5,
                                                                     'LANG: %s EAPI: %s' % (
                                                                         self.user_langs[zp_lang_id],
                                                                         eapi
                                                                     ))
                        if hasattr(getattr(self, eapi), 'get_film_data'):
                            ZP_FILM_ID = max_film_id + 1
                            lang_processing_complete = False
                            while lang_processing_complete is False:
                                entity_processing_dict = self.get_film_data_processing_retry(ZP_FILM_ID,
                                                                                             eapi, zp_lang_id)
                                if entity_processing_dict:
                                    for enitity_id in entity_processing_dict:
                                        ZP_FILM_ID = enitity_id
                                        if entity_processing_dict[ZP_FILM_ID]['datetime'] + timedelta(
                                            days=entity_processing_dict[ZP_FILM_ID]['delay']) <= datetime.now():
                                            log.debug('dt %s, plus %s is %s which is less than than now %s',
                                                      entity_processing_dict[ZP_FILM_ID]['datetime'],
                                                      entity_processing_dict[ZP_FILM_ID]['delay'],
                                                      entity_processing_dict[ZP_FILM_ID]['datetime'] + timedelta(
                                                          days=entity_processing_dict[ZP_FILM_ID]['delay']),
                                                      datetime.now())
                                            self.set_current_library_process_desc_detail(
                                                self.library_config_dict['id'],
                                                5,
                                                'LANG: %s EAPI: %s FILM: %s/%s. Retrying.' % (
                                                    self.user_langs[
                                                        zp_lang_id],
                                                    eapi,
                                                    enitity_id,
                                                    max_film_id
                                                ))
                                            self.process_entity(ZP_FILM_ID, eapi, zp_lang_id)
                                        else:
                                            self.set_current_library_process_desc_detail(
                                                self.library_config_dict['id'],
                                                5,
                                                'LANG: %s, EAPI: %s FILM: %s/%s. To soon to retry.' % (
                                                    self.user_langs[
                                                        zp_lang_id],
                                                    eapi,
                                                    enitity_id,
                                                    max_film_id
                                                ))
                                            log.debug('dt %s, plus %s is %s which is not less than now %s',
                                                      entity_processing_dict[ZP_FILM_ID]['datetime'],
                                                      entity_processing_dict[ZP_FILM_ID]['delay'],
                                                      entity_processing_dict[ZP_FILM_ID]['datetime'] + timedelta(
                                                          days=entity_processing_dict[ZP_FILM_ID]['delay']),
                                                      datetime.now())
                                            # print(ZP_FILM_ID)
                                # raise SystemExit
                                else:
                                    lang_processing_complete = True
                        else:
                            log.info('eapi %s does not have get_film_data', eapi)

    def acquire_film_collection_data(self):
        """Kick of the process of gathering film data

            Attributes:
            | film_data:
            | 	{
            | 		"adult":true|false,
            | 		"genres":[
            | 					{
            | 						"id": unicode,
            | 						"Name": unicode
            | 					}
            | 				],
            | 		"title": unicode,
            | 		"original_title": unicode,
            | 		"overview": unicode,
            | 		"release_date": YYYY-MM-DD
            | 		"runtime": int
            | 		"rating": int (min 1 max 10)
            | 		"credits": {
            | 						"cast":
            | 								[
            | 									{
            | 										"id": unicode,
            | 										"name": unicode,
            | 										"character": unicode,
            | 										"order": int
            | 									}
            | 								],
            | 						"crew":
            | 								[
            | 									{
            | 										"id": unicode,
            | 										"name": unicode,
            | 										"job": unicode,
            | 										"order": int
            | 									}
            | 								]
            | 					}
            | 	}

        """
        # Get films that do not exist in any of the tables
        # order by film ID desc (prcessed newly added films first)
        # TODO: update film update_datetime
        log.debug('start acquire_film_collection_data')
        session = self.Session()
        max_film_collection_id = session.query(func.max(TABLES.ZP_FILM.ID)).one()[0]
        session.close()
        if isinstance(max_film_collection_id, int):
            for zp_lang_id in self.user_langs:
                self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                             5,
                                                             'LANG: %s' % self.user_langs[zp_lang_id])
                for eapi in self.eapi_film_plugins_access_list:
                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                5,
                                                                 'LANG: %s, EAPI: %s' % (
                                                                     self.user_langs[zp_lang_id],
                                                                     eapi
                                                                 ))
                    if hasattr(getattr(self, eapi), 'get_collection_data'):
                        lang_processing_complete = False
                        zp_film_collection_id = max_film_collection_id + 1
                        while lang_processing_complete is False:
                            entity_processing_list = self.get_film_collection_data_processing_no_retry(
                                zp_film_collection_id, eapi, zp_lang_id
                            )
                            if entity_processing_list:
                                for enitity_id in entity_processing_list:
                                    self.set_current_library_process_desc_detail(
                                        self.library_config_dict['id'],
                                        5,
                                        'LANG: %s, EAPI: %s FILM_COLLECTION: %s/%s' % (
                                            self.user_langs[
                                                zp_lang_id],
                                            eapi,
                                            enitity_id,
                                            max_film_collection_id
                                        ))
                                    zp_film_collection_id = enitity_id
                                    log.debug('getting film collection data for zp_film_collection_id %s, '
                                              'eapi %s, lang %s',
                                              zp_film_collection_id, eapi, zp_lang_id)
                                    self.process_film_collection_data(zp_film_collection_id, eapi, zp_lang_id)
                            else:
                                    lang_processing_complete = True
                    else:
                        log.info('eapi %s does not have get_collection_data', eapi)
            # raise SystemExit
            if self.check_can_retry(1) is True:
                # if 1 == 1:
                log.debug('Retrying Film Collection Data')
                for zp_lang_id in self.user_langs:
                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                             5,
                                                             'LANG: %s' % self.user_langs[zp_lang_id])
                    for eapi in self.eapi_film_plugins_access_list:
                        if hasattr(getattr(self, eapi), 'get_collection_data'):
                            lang_processing_complete = False
                            zp_film_collection_id = max_film_collection_id + 1
                            while lang_processing_complete is False:
                                entity_processing_dict = self.get_film_collection_data_processing_retry(
                                    zp_film_collection_id, eapi, zp_lang_id
                                )
                                if entity_processing_dict:
                                    for enitity_id in entity_processing_dict:
                                        zp_film_collection_id = enitity_id
                                        self.set_current_library_process_desc_detail(
                                            self.library_config_dict['id'],
                                            5,
                                            'LANG: %s, EAPI: %s FILM_COLLECTION: %s/%s' % (
                                                self.user_langs[
                                                    zp_lang_id],
                                                eapi,
                                                enitity_id,
                                                max_film_collection_id
                                            ))
                                        if entity_processing_dict[zp_film_collection_id]['datetime'] + timedelta(
                                            days=entity_processing_dict[zp_film_collection_id][
                                                'delay']) <= datetime.now():
                                            log.debug('dt %s, plus %s is %s which is less than than now %s',
                                                      entity_processing_dict[zp_film_collection_id]['datetime'],
                                                      entity_processing_dict[zp_film_collection_id]['delay'],
                                                      entity_processing_dict[zp_film_collection_id][
                                                          'datetime'] + timedelta(
                                                          days=entity_processing_dict[zp_film_collection_id]['delay']),
                                                      datetime.now())
                                            self.process_film_collection_data(zp_film_collection_id, eapi, zp_lang_id)
                                        else:
                                            log.debug('dt %s, plus %s is %s which is not less than now %s',
                                                      entity_processing_dict[zp_film_collection_id]['datetime'],
                                                      entity_processing_dict[zp_film_collection_id]['delay'],
                                                      entity_processing_dict[zp_film_collection_id][
                                                          'datetime'] + timedelta(
                                                          days=entity_processing_dict[zp_film_collection_id]['delay']),
                                                      datetime.now())
                                else:
                                    lang_processing_complete = True
                        else:
                            log.info('eapi %s does not have get_collection_data', eapi)
                            # print(ZP_FILM_ID)
                            # raise SystemExit

    def get_film_data_processing_retry(self, ZP_FILM_ID, eapi, zp_lang_id):
        session = self.Session()
        return_dict = {}
        qry_film_missing_data = session.query(
            TABLES.ZP_FILM.ID, TABLES.ZP_RETRY_COUNT.DELAY,
            TABLES.ZP_RETRY.DATETIME, TABLES.ZP_RETRY.COUNT).filter(
            TABLES.ZP_FILM.ID < ZP_FILM_ID,
            (~TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_FILM_ROLE_XREF.ZP_FILM_ID)) |
             ~TABLES.ZP_FILM.ID.in_(
                 session.query(
                     TABLES.ZP_FILM_GENRE_XREF.ZP_FILM_ID)) |
             ~TABLES.ZP_FILM.ID.in_(
                 session.query(
                     TABLES.ZP_FILM_RATING.ZP_FILM_ID)) |
             ~TABLES.ZP_FILM.ID.in_(
                 session.query(
                     TABLES.ZP_FILM_OVERVIEW.ZP_FILM_ID).filter(
                     TABLES.ZP_FILM_OVERVIEW.ZP_LANG_ID == zp_lang_id,
                     TABLES.ZP_FILM_OVERVIEW.ZP_EAPI_ID == self.eapi_dict[eapi]
                 )) |
             ~TABLES.ZP_FILM.ID.in_(
                 session.query(
                     TABLES.ZP_FILM_RUNTIME.ZP_FILM_ID)) |
             ~TABLES.ZP_FILM.ID.in_(
                 session.query(
                     TABLES.ZP_FILM_TITLE.ZP_FILM_ID).filter(
                     TABLES.ZP_FILM_TITLE.ZP_LANG_ID == zp_lang_id,
                     TABLES.ZP_FILM_TITLE.ZP_EAPI_ID == self.eapi_dict[eapi]
                 )) |
             ~TABLES.ZP_FILM.ID.in_(
                 session.query(
                     TABLES.ZP_FILM_RELEASE.ZP_FILM_ID))),
            TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_FILM_EAPI_EID.ZP_FILM_ID)),
            TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == TABLES.ZP_RETRY_COUNT.ZP_RETRY_TYPE_ID,
            TABLES.ZP_FILM.ID == TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID,
            TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 2,
            TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == 1,
            TABLES.ZP_RETRY.ZP_LANG_ID == zp_lang_id,
            TABLES.ZP_RETRY.ZP_EAPI_ID == self.eapi_dict[eapi],
            TABLES.ZP_RETRY_COUNT.COUNT == session.query(
                func.max(TABLES.ZP_RETRY_COUNT.COUNT)
            ).filter(
                TABLES.ZP_RETRY.COUNT >= TABLES.ZP_RETRY_COUNT.COUNT).order_by(
                TABLES.ZP_RETRY_COUNT.COUNT.desc()).correlate(TABLES.ZP_RETRY).as_scalar()
        )

        qry_film_missing_data_count = qry_film_missing_data.count()
        log.debug('qry_film_missing_data_count: %s', qry_film_missing_data_count)
        if qry_film_missing_data_count > 0:
            films_missing_data = qry_film_missing_data.order_by(TABLES.ZP_FILM.ID.desc()).limit(100)
            for result in films_missing_data:
                return_dict[result.ID] = {}
                return_dict[result.ID]['datetime'] = result.DATETIME
                return_dict[result.ID]['count'] = result.COUNT
                return_dict[result.ID]['delay'] = result.DELAY
        session.close()
        log.debug(return_dict)
        return return_dict

    def get_film_collection_data_processing_retry(self, zp_film_collection_id, eapi, zp_lang_id):
        # log.error(locals())
        session = self.Session()
        return_dict = {}
        qry_film_missing_data = session.query(
            TABLES.ZP_FILM_COLLECTION.ID, TABLES.ZP_RETRY_COUNT.DELAY,
            TABLES.ZP_RETRY.DATETIME, TABLES.ZP_RETRY.COUNT).filter(
            TABLES.ZP_FILM_COLLECTION.ID < zp_film_collection_id,
            (~TABLES.ZP_FILM_COLLECTION.ID.in_(
                session.query(
                    TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_ID).filter(
                    TABLES.ZP_FILM_COLLECTION_TITLE.ZP_LANG_ID == zp_lang_id,
                    TABLES.ZP_FILM_COLLECTION_TITLE.ZP_EAPI_ID == self.eapi_dict[eapi],
                )) |
             ~TABLES.ZP_FILM_COLLECTION.ID.in_(
                 session.query(
                     TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_FILM_COLLECTION_ID).filter(
                     TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_LANG_ID == zp_lang_id,
                     TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_EAPI_ID == self.eapi_dict[eapi],
                 ))
             ),
            TABLES.ZP_FILM_COLLECTION.ID.in_(
                session.query(
                    TABLES.ZP_FILM_COLLECTION_EAPI_EID.ZP_FILM_COLLECTION_ID).filter(
                    TABLES.ZP_FILM_COLLECTION_EAPI_EID.ZP_EAPI_ID == self.eapi_dict[eapi]
                )),
            TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == TABLES.ZP_RETRY_COUNT.ZP_RETRY_TYPE_ID,
            TABLES.ZP_FILM_COLLECTION.ID == TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID,
            TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 7,
            TABLES.ZP_RETRY.ZP_LANG_ID == zp_lang_id,
            TABLES.ZP_RETRY.ZP_EAPI_ID == self.eapi_dict[eapi],
            TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == 1,
            TABLES.ZP_RETRY_COUNT.COUNT == session.query(
                func.max(TABLES.ZP_RETRY_COUNT.COUNT)
            ).filter(
                TABLES.ZP_RETRY.COUNT >= TABLES.ZP_RETRY_COUNT.COUNT).order_by(
                TABLES.ZP_RETRY_COUNT.COUNT.desc()).correlate(TABLES.ZP_RETRY).as_scalar()
        )

        qry_film_missing_data_count = qry_film_missing_data.count()
        log.debug('qry_film_missing_data_count: %s', qry_film_missing_data_count)
        if qry_film_missing_data_count > 0:
            films_missing_data = qry_film_missing_data.order_by(TABLES.ZP_FILM_COLLECTION.ID.desc()).limit(100)
            for result in films_missing_data:
                return_dict[result.ID] = {}
                return_dict[result.ID]['datetime'] = result.DATETIME
                return_dict[result.ID]['count'] = result.COUNT
                return_dict[result.ID]['delay'] = result.DELAY
        session.close()
        log.debug(return_dict)
        return return_dict

    def get_film_collection_data_processing_no_retry(self, zp_film_collection_id, eapi, zp_lang_id):
        # log.error(locals())
        session = self.Session()
        return_list = []
        qry_film_missing_data = session.query(
            TABLES.ZP_FILM_COLLECTION).filter(
            TABLES.ZP_FILM_COLLECTION.ID < zp_film_collection_id,
            (~TABLES.ZP_FILM_COLLECTION.ID.in_(
                session.query(
                    TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_ID).filter(
                    TABLES.ZP_FILM_COLLECTION_TITLE.ZP_LANG_ID == zp_lang_id,
                    TABLES.ZP_FILM_COLLECTION_TITLE.ZP_EAPI_ID == self.eapi_dict[eapi],
                )) |
             ~TABLES.ZP_FILM_COLLECTION.ID.in_(
                 session.query(
                     TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_FILM_COLLECTION_ID).filter(
                     TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_LANG_ID == zp_lang_id,
                     TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_EAPI_ID == self.eapi_dict[eapi],
                 ))
             ),
            TABLES.ZP_FILM_COLLECTION.ID.in_(
                session.query(
                    TABLES.ZP_FILM_COLLECTION_EAPI_EID.ZP_FILM_COLLECTION_ID).filter(
                    TABLES.ZP_FILM_COLLECTION_EAPI_EID.ZP_EAPI_ID == self.eapi_dict[eapi]
                )),
            ~TABLES.ZP_FILM_COLLECTION.ID.in_(session.query(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 7,
                TABLES.ZP_RETRY.ZP_LANG_ID == zp_lang_id,
                TABLES.ZP_RETRY.ZP_EAPI_ID == self.eapi_dict[eapi]
            ))
        )

        qry_film_missing_data_count = qry_film_missing_data.count()
        log.debug('qry_film_missing_data_count: %s', qry_film_missing_data_count)
        if qry_film_missing_data_count > 0:
            films_missing_data = qry_film_missing_data.order_by(TABLES.ZP_FILM_COLLECTION.ID.desc()).limit(100)
            for film in films_missing_data:
                return_list.append(film.ID)
        session.close()
        return return_list
        # TODO: Parental Rating

    def get_film_data_processing_no_retry(self, ZP_FILM_ID, eapi, zp_lang_id):
        session = self.Session()
        return_list = []
        qry_film_missing_data = session.query(
            TABLES.ZP_FILM).filter(
            TABLES.ZP_FILM.ID < ZP_FILM_ID,
            ~TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_FILM_ROLE_XREF.ZP_FILM_ID)) |
            ~TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_FILM_GENRE_XREF.ZP_FILM_ID)) |
            ~TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_FILM_RATING.ZP_FILM_ID)) |
            ~TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_FILM_OVERVIEW.ZP_FILM_ID).filter(
                    TABLES.ZP_FILM_OVERVIEW.ZP_LANG_ID == zp_lang_id,
                    TABLES.ZP_FILM_OVERVIEW.ZP_EAPI_ID == self.eapi_dict[eapi]
                )) |
            ~TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_FILM_RUNTIME.ZP_FILM_ID)) |
            ~TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_FILM_TITLE.ZP_FILM_ID).filter(
                    TABLES.ZP_FILM_TITLE.ZP_LANG_ID == zp_lang_id,
                    TABLES.ZP_FILM_TITLE.ZP_EAPI_ID == self.eapi_dict[eapi]
                )) |
            ~TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_FILM_RELEASE.ZP_FILM_ID)),
            TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_FILM_EAPI_EID.ZP_FILM_ID)),
            ~TABLES.ZP_FILM.ID.in_(session.query(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 2,
                TABLES.ZP_RETRY.ZP_LANG_ID == zp_lang_id,
                TABLES.ZP_RETRY.ZP_EAPI_ID == self.eapi_dict[eapi]
            ))
        )

        qry_film_missing_data_count = qry_film_missing_data.count()
        log.debug('qry_film_missing_data_count: %s', qry_film_missing_data_count)
        if qry_film_missing_data_count > 0:
            films_missing_data = qry_film_missing_data.order_by(TABLES.ZP_FILM.ID.desc()).limit(100)
            for film in films_missing_data:
                return_list.append(film.ID)
        session.close()
        return return_list
        # TODO: Parental Rating

    def process_entity(self, ZP_FILM_ID, eapi, zp_lang_id):
        if zp_lang_id is None:
            iso_639_part1 = None
        else:
            iso_639_part1 = self.iso_639_part1_from_zp_lang_id(zp_lang_id)
        try:
            film_eapi_eid = self.eapi_eid_from_zp_film_id(self.eapi_dict[eapi], ZP_FILM_ID)
            # print(film_eapi_eid)
        except orm.exc.NoResultFound:
            log.warning(
                'ZP_FILM_ID: {0} with self.eapi_dict[eapi]: {1} not in ZP_FILM_EAPI_EID'.format(
                    ZP_FILM_ID,
                    self.eapi_dict[eapi]))
        else:
            # log.warning(dir(getattr(self, eapi)))
            film_data = getattr(self, eapi).get_film_data(film_eapi_eid, language=iso_639_part1)
            if isinstance(film_data, dict):
                log.debug('film_data %s', film_data)
                for key in film_data:
                    if film_data[key]:
                        if key in self.data_keys:
                            getattr(self, 'process_{0}'.format(key))(eapi,
                                                                     ZP_FILM_ID,
                                                                     zp_lang_id,
                                                                     film_data[key])
                        else:
                            log.debug('key %s not in data_keys %s', key, self.data_keys)
                    elif key not in ['belongs_to_collection']:
                        log.warning(
                            'No {0}: {1} type: {2} found for ZP_EAPI_EID: {3} from ZP_EAPI_ID: {4}'.format(
                                key,
                                film_data[key],
                                type(film_data[key]),
                                film_eapi_eid,
                                self.eapi_dict[eapi]))
            else:
                log.warning('film data: {0} type: {1} is not dict'.format(film_data,
                                                                          type(film_data)))
        if self.film_missing_data_check(ZP_FILM_ID, eapi, zp_lang_id) is True:
            log.debug('set film data collection retry for ZP_FILM_ID %s', ZP_FILM_ID)
            self.set_retry(1, 2, ZP_FILM_ID, self.eapi_dict[eapi], zp_lang_id)

    def process_film_collection_data(self, zp_film_collection_id, eapi, zp_lang_id):
        ZP_FILM_COLLECTION_TITLE_TYPE_ID = 1
        if zp_lang_id is None:
            iso_639_part1 = None
        else:
            iso_639_part1 = self.iso_639_part1_from_zp_lang_id(zp_lang_id)
        try:
            film_collection_eapi_eid = self.eapi_eid_from_zp_film_collection_id(self.eapi_dict[eapi],
                                                                                zp_film_collection_id)
            # print(film_eapi_eid)
        except orm.exc.NoResultFound:
            log.warning(
                'ZP_FILM_ID: {0} with self.eapi_dict[eapi]: {1} not in ZP_FILM_EAPI_EID'.format(
                    zp_film_collection_id,
                    self.eapi_dict[eapi]))
        else:
            # log.warning(dir(getattr(self, eapi)))
            film_collection_data = getattr(self, eapi).get_collection_data(film_collection_eapi_eid, iso_639_part1)
            if isinstance(film_collection_data, dict):
                log.debug(film_collection_data)
                if 'name' in film_collection_data:
                    if isinstance(film_collection_data['name'], string_types) or \
                        isinstance(film_collection_data['name'], text_type):
                        self.process_collection_name(eapi, zp_film_collection_id, ZP_FILM_COLLECTION_TITLE_TYPE_ID,
                                                     zp_lang_id, film_collection_data['name'])
                    else:
                        log.warning('''film_collection_data['name'] %s is not string_types or text_type but %s''',
                                    film_collection_data['name'], type(film_collection_data['name']))
                else:
                    log.warning('name not in film_collection_data.keys() %s', film_collection_data.keys())
                if 'overview' in film_collection_data:
                    if isinstance(film_collection_data['overview'], string_types) or \
                        isinstance(film_collection_data['overview'], text_type):
                        self.process_collection_overview(eapi, zp_film_collection_id,
                                                         zp_lang_id, film_collection_data['overview'])
                    else:
                        log.warning('''film_collection_data['overview'] %s is not string_types or text_type but %s''',
                                    film_collection_data['overview'], type(film_collection_data['overview']))
                else:
                    log.warning('name not in film_collection_data.keys() %s', film_collection_data.keys())
            else:
                log.warning('film_collection_data: %s type: %s is not dict for zp_film_collection_id %s'
                            ' film_collection_eapi_eid %s',
                            film_collection_data, type(film_collection_data), zp_film_collection_id,
                            film_collection_eapi_eid)
        if self.film_collection_missing_data_check(zp_film_collection_id, eapi, zp_lang_id) is True:
            log.debug('set film collection data collection retry for ZP_FILM_ID %s', zp_film_collection_id)
            self.set_retry(1, 7, zp_film_collection_id, self.eapi_dict[eapi], zp_lang_id)

    def film_missing_data_check(self, ZP_FILM_ID, eapi, zp_lang_id):
        session = self.Session()
        try:
            session.query(
                TABLES.ZP_FILM).filter(
                TABLES.ZP_FILM.ID == ZP_FILM_ID,
                (~TABLES.ZP_FILM.ID.in_(
                    session.query(
                        TABLES.ZP_FILM_ROLE_XREF.ZP_FILM_ID)) |
                 ~TABLES.ZP_FILM.ID.in_(
                     session.query(
                         TABLES.ZP_FILM_GENRE_XREF.ZP_FILM_ID)) |
                 ~TABLES.ZP_FILM.ID.in_(
                     session.query(
                         TABLES.ZP_FILM_RATING.ZP_FILM_ID)) |
                 ~TABLES.ZP_FILM.ID.in_(
                     session.query(
                         TABLES.ZP_FILM_OVERVIEW.ZP_FILM_ID).filter(
                         TABLES.ZP_FILM_OVERVIEW.ZP_LANG_ID == zp_lang_id,
                         TABLES.ZP_FILM_OVERVIEW.ZP_EAPI_ID == self.eapi_dict[eapi]
                     )) |
                 ~TABLES.ZP_FILM.ID.in_(
                     session.query(
                         TABLES.ZP_FILM_RUNTIME.ZP_FILM_ID)) |
                 ~TABLES.ZP_FILM.ID.in_(
                     session.query(
                         TABLES.ZP_FILM_TITLE.ZP_FILM_ID).filter(
                         TABLES.ZP_FILM_TITLE.ZP_LANG_ID == zp_lang_id,
                         TABLES.ZP_FILM_TITLE.ZP_EAPI_ID == self.eapi_dict[eapi]
                     )) |
                 ~TABLES.ZP_FILM.ID.in_(
                     session.query(
                         TABLES.ZP_FILM_RELEASE.ZP_FILM_ID))),
                TABLES.ZP_FILM.ID.in_(
                    session.query(
                        TABLES.ZP_FILM_EAPI_EID.ZP_FILM_ID))
            ).one()
        except orm.exc.NoResultFound:
            session.close()
            return False
        session.close()
        return True

    def film_collection_missing_data_check(self, zp_film_collection_id, eapi, zp_lang_id):
        # log.error('film_collection_missing_data_check function start')
        session = self.Session()
        try:
            session.query(
                TABLES.ZP_FILM_COLLECTION).filter(
                TABLES.ZP_FILM_COLLECTION.ID == zp_film_collection_id,
                (~TABLES.ZP_FILM_COLLECTION.ID.in_(
                    session.query(TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_ID).filter(
                        TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_ID == TABLES.ZP_FILM_COLLECTION.ID,
                        TABLES.ZP_FILM_COLLECTION_TITLE.ZP_LANG_ID == zp_lang_id,
                        TABLES.ZP_FILM_COLLECTION_TITLE.ZP_EAPI_ID == self.eapi_dict[eapi]
                    )) |
                 ~TABLES.ZP_FILM_COLLECTION.ID.in_(
                     session.query(TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_FILM_COLLECTION_ID).filter(
                         TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_FILM_COLLECTION_ID == TABLES.ZP_FILM_COLLECTION.ID,
                         TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_LANG_ID == zp_lang_id,
                         TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_EAPI_ID == self.eapi_dict[eapi]
                     ))
                 )
            ).one()
        except orm.exc.NoResultFound:
            session.close()
            return False
        session.close()
        # log.error('film_collection_missing_data_check function end')
        return True

    def check_for_eapi_collection_eid(self, eapi, eapi_eid):
        session = self.Session()
        try:
            zp_film_collection_eapi_eid = session.query(TABLES.ZP_FILM_COLLECTION_EAPI_EID).filter(
                TABLES.ZP_FILM_COLLECTION_EAPI_EID.ZP_EAPI_ID == self.eapi_dict[eapi],
                TABLES.ZP_FILM_COLLECTION_EAPI_EID.ZP_EAPI_COLLECTION_EID == eapi_eid
            ).one()
        except orm.exc.NoResultFound:
            zp_film_collection_id = False
        else:
            zp_film_collection_id = zp_film_collection_eapi_eid.ZP_FILM_COLLECTION_ID
        session.close()
        return zp_film_collection_id

    def set_zp_film_zp_film_collection_id(self, zp_film_id, zp_film_collection_id):
        session = self.Session()
        try:
            zp_film_collection_xref = session.query(TABLES.ZP_FILM_COLLECTION_XREF).filter(
                TABLES.ZP_FILM_COLLECTION_XREF.ZP_FILM_ID == zp_film_id
            ).one()
        except orm.exc.NoResultFound:
            add_zp_film_collection_xref = TABLES.ZP_FILM_COLLECTION_XREF(ZP_FILM_COLLECTION_ID=zp_film_collection_id,
                                                                         ZP_FILM_ID=zp_film_id)
            session.add(add_zp_film_collection_xref)
            commit(session)
        else:
            if zp_film_collection_xref.ZP_FILM_COLLECTION_ID != zp_film_collection_id:
                log.warning('there is allready an entry in ZP_FILM_COLLECTION_XREF for'
                            ' zp_film_id %s but it is zp_film_collection_id %s not the'
                            'zp_film_collection_id %s that was given to this function.'
                            'Setting zp_film_collection_id %s for zp_film_id %s',
                            zp_film_id, zp_film_collection_xref.ZP_FILM_COLLECTION_ID,
                            zp_film_collection_id, zp_film_id, zp_film_collection_id)
                zp_film_collection_xref.ZP_FILM_COLLECTION_ID = zp_film_collection_id
                commit(session)
        session.query(
            TABLES.ZP_FILM
        ).filter(
            TABLES.ZP_FILM.ID == zp_film_id,
            TABLES.ZP_FILM.ZP_FILM_COLLECTION_ID == None
        ).update(
            {"ZP_FILM_COLLECTION_ID": zp_film_collection_id}
        )
        commit(session)
        session.close()

    def new_collection(self, eapi, eapi_eid):
        session = self.Session()
        add_ZP_FILM_COLLECTION = TABLES.ZP_FILM_COLLECTION(
            LAST_EDIT_DATETIME=date_time())
        session.add(add_ZP_FILM_COLLECTION)
        flush(session)
        ZP_FILM_COLLECTION_ID = add_ZP_FILM_COLLECTION.ID
        add_ZP_FILM_COLLECTION_EAPI_EID = TABLES.ZP_FILM_COLLECTION_EAPI_EID(
            ZP_FILM_COLLECTION_ID=ZP_FILM_COLLECTION_ID,
            ZP_EAPI_ID = self.eapi_dict[eapi],
            ZP_EAPI_COLLECTION_EID = eapi_eid
        )
        session.add(add_ZP_FILM_COLLECTION_EAPI_EID)
        commit(session)
        session.close()
        return ZP_FILM_COLLECTION_ID

    # todo make this function better
    def process_belongs_to_collection(self, eapi, zp_film_id, zp_lang_id, collection_dict):
        # we assume a film cannot be in more then one collection
        # no idea how to match collection between eapis, there does not seem to be a api that has
        # reference to external eapi eids
        if isinstance(collection_dict, dict):
            if 'id' in collection_dict:
                eapi_eid = collection_dict['id']
                zp_film_collection_id = self.check_for_eapi_collection_eid(eapi, eapi_eid)
                if zp_film_collection_id is False:
                    zp_film_collection_id = self.new_collection(eapi, eapi_eid)
                if zp_film_collection_id > 0:
                    self.set_zp_film_zp_film_collection_id(zp_film_id, zp_film_collection_id)
            else:
                log.warning('id not in collection_dict.leys() %s', collection_dict.keys())
        else:
            log.warning('collection_dict %s is not dict but %s', collection_dict, type(collection_dict))

    def process_collection_name(self, eapi, zp_film_collection_id, ZP_FILM_COLLECTION_TITLE_TYPE_ID, ZP_LANG_ID, name):
        session = self.Session()
        try:
            session.query(
                TABLES.ZP_FILM_COLLECTION_TITLE).filter(
                TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_ID == zp_film_collection_id,
                TABLES.ZP_FILM_COLLECTION_TITLE.ZP_EAPI_ID == self.eapi_dict[eapi],
                TABLES.ZP_FILM_COLLECTION_TITLE.ZP_LANG_ID == ZP_LANG_ID,
                TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_TITLE_TYPE_ID == ZP_FILM_COLLECTION_TITLE_TYPE_ID
            ).one()
        except orm.exc.NoResultFound as e:
            add_zp_film_collection_title = TABLES.ZP_FILM_COLLECTION_TITLE(ZP_FILM_COLLECTION_ID=zp_film_collection_id,
                                                                           ZP_EAPI_ID=self.eapi_dict[eapi],
                                                                           ZP_LANG_ID=ZP_LANG_ID,
                                                                           ZP_FILM_COLLECTION_TITLE_TYPE_ID=
                                                                           ZP_FILM_COLLECTION_TITLE_TYPE_ID,
                                                                           TITLE=name)
            session.add(add_zp_film_collection_title)
            commit(session)
            update_film_collection_last_mod(self.Session, zp_film_collection_id)
        else:
            log.warning('There is allready an entry in ZP_FILM_COLLECTION_TITLE for ZP_FILM_COLLECTION_ID %s'
                        ' ZP_EAPI_ID %s, ZP_LANG_ID %s, ZP_FILM_COLLECTION_TITLE_TYPE_ID %s', zp_film_collection_id,
                        self.eapi_dict[eapi], ZP_LANG_ID, ZP_FILM_COLLECTION_TITLE_TYPE_ID)
        session.close()

    def process_collection_overview(self, eapi, zp_film_collection_id, ZP_LANG_ID, name):
        session = self.Session()
        try:
            session.query(
                TABLES.ZP_FILM_COLLECTION_OVERVIEW).filter(
                TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_FILM_COLLECTION_ID == zp_film_collection_id,
                TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_EAPI_ID == self.eapi_dict[eapi],
                TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_LANG_ID == ZP_LANG_ID
            ).one()
        except orm.exc.NoResultFound as e:
            add_zp_film_collection_overview = TABLES.ZP_FILM_COLLECTION_OVERVIEW(
                ZP_FILM_COLLECTION_ID=zp_film_collection_id,
                ZP_EAPI_ID=self.eapi_dict[eapi],
                ZP_LANG_ID=ZP_LANG_ID,
                OVERVIEW=name)
            session.add(add_zp_film_collection_overview)
            commit(session)
            update_film_collection_last_mod(self.Session, zp_film_collection_id)
        else:
            log.warning('There is allready an entry in ZP_FILM_COLLECTION_OVERVIEW for ZP_FILM_COLLECTION_ID %s'
                        ' ZP_EAPI_ID %s, ZP_LANG_ID %s, ZP_FILM_COLLECTION_OVERVIEW %s', zp_film_collection_id,
                        self.eapi_dict[eapi], ZP_LANG_ID)
        session.close()

    def process_genres(self, eapi, ZP_FILM_ID, ZP_LANG_ID, genres):
        """Process genres

            Args:
                | eapi (str): the dune id
                | ZP_FILM_ID (int): The film id
                | ZP_LANG_ID (int): The language id
                | genres (list): [{'name':'genre'}]

        """
        session = self.Session()
        for zp_genre_id in genres:
            try:
                session.query(
                    TABLES.ZP_FILM_GENRE_XREF).filter(
                    TABLES.ZP_FILM_GENRE_XREF.ZP_FILM_ID == ZP_FILM_ID,
                    TABLES.ZP_FILM_GENRE_XREF.ZP_GENRE_ID == zp_genre_id).one()
            except orm.exc.NoResultFound as e:
                add_film_genre_xref = TABLES.ZP_FILM_GENRE_XREF(ZP_FILM_ID=ZP_FILM_ID,
                                                                ZP_GENRE_ID=zp_genre_id)
                session.add(add_film_genre_xref)
                commit(session)
                update_film_last_mod(self.Session, ZP_FILM_ID)
            else:
                pass
        session.close()

    # TODO: Manage multiple titles how to choose which to display on ui (there are more than one title for
    # each film in ZP_FILM_TITLE) prob add lang and title_type (origional .....) and how to deal with
    # multiple languages and what happens if not specific title is aquired. Use all langs currently
    # used for all users and which they prefer title or origional title

    def process_title(self, eapi, ZP_FILM_ID, ZP_LANG_ID, title, ZP_FILM_TITLE_TYPE_ID=1):
        """Process title

            Args:
                | eapi (str): the dune id
                | ZP_FILM_ID (int): The film id
                | ZP_LANG_ID (int): The language id
                | title (list): title
                | ZP_FILM_TITLE_TYPE_ID (int): title type id

        """
        session = self.Session()
        try:
            session.query(
                TABLES.ZP_FILM_TITLE).filter(
                TABLES.ZP_FILM_TITLE.ZP_FILM_ID == ZP_FILM_ID,
                TABLES.ZP_FILM_TITLE.ZP_EAPI_ID == self.eapi_dict[eapi],
                TABLES.ZP_FILM_TITLE.ZP_LANG_ID == ZP_LANG_ID,
                TABLES.ZP_FILM_TITLE.ZP_FILM_TITLE_TYPE_ID == ZP_FILM_TITLE_TYPE_ID).one()
        except orm.exc.NoResultFound as e:
            add_film_title = TABLES.ZP_FILM_TITLE(ZP_FILM_ID=ZP_FILM_ID,
                                                  TITLE=title,
                                                  ZP_LANG_ID=ZP_LANG_ID,
                                                  ZP_FILM_TITLE_TYPE_ID=ZP_FILM_TITLE_TYPE_ID,
                                                  ZP_EAPI_ID=self.eapi_dict[eapi])
            session.add(add_film_title)
            commit(session)
            update_film_last_mod(self.Session, ZP_FILM_ID)
        session.close()

    def process_original_title(self, eapi, ZP_FILM_ID, ZP_LANG_ID, title):
        """Process origional_title

            Args:
                | eapi (str): the dune id
                | ZP_FILM_ID (int): The film id
                | ZP_LANG_ID (int): The language id
                | title (str): origional_title

        """
        self.process_title(eapi, ZP_FILM_ID, ZP_LANG_ID, title, 2)

    def process_overview(self, eapi, ZP_FILM_ID, ZP_LANG_ID, overview):
        """Process overview

            Args:
                | eapi (str): the dune id
                | ZP_FILM_ID (int): The film id
                | ZP_LANG_ID (int): The language id
                | overview (str): overview

        """
        session = self.Session()
        try:
            session.query(
                TABLES.ZP_FILM_OVERVIEW).filter(
                TABLES.ZP_FILM_OVERVIEW.ZP_FILM_ID == ZP_FILM_ID,
                TABLES.ZP_FILM_OVERVIEW.ZP_EAPI_ID == self.eapi_dict[eapi],
                TABLES.ZP_FILM_OVERVIEW.ZP_LANG_ID == ZP_LANG_ID).one()
        except orm.exc.NoResultFound as e:
            add_film_overview = TABLES.ZP_FILM_OVERVIEW(ZP_FILM_ID=ZP_FILM_ID,
                                                        OVERVIEW=overview,
                                                        ZP_LANG_ID=ZP_LANG_ID,
                                                        ZP_EAPI_ID=self.eapi_dict[eapi])

            session.add(add_film_overview)
            commit(session)
            update_film_last_mod(self.Session, ZP_FILM_ID)
        session.close()

    def process_release_date(self, eapi, ZP_FILM_ID, ZP_LANG_ID, release_date):
        """Process release_date

            Args:
                | eapi (str): the dune id
                | ZP_FILM_ID (int): The film id
                | ZP_LANG_ID (int): The language id
                | release_date (str): release_date

        """
        session = self.Session()
        try:
            session.query(
                TABLES.ZP_FILM_RELEASE).filter(
                TABLES.ZP_FILM_RELEASE.ZP_FILM_ID == ZP_FILM_ID).one()
        except orm.exc.NoResultFound as e:
            add_film_release_date = TABLES.ZP_FILM_RELEASE(ZP_FILM_ID=ZP_FILM_ID,
                                                           RELEASE_DATE=release_date)
            session.add(add_film_release_date)
            commit(session)
            update_film_last_mod(self.Session, ZP_FILM_ID)
        session.close()

    def process_runtime(self, eapi, ZP_FILM_ID, ZP_LANG_ID, runtime):
        session = self.Session()
        try:
            session.query(
                TABLES.ZP_FILM_RUNTIME).filter(
                TABLES.ZP_FILM_RUNTIME.ZP_FILM_ID == ZP_FILM_ID).one()
        except orm.exc.NoResultFound as e:
            add_film_missing_runtime = TABLES.ZP_FILM_RUNTIME(ZP_FILM_ID=ZP_FILM_ID,
                                                              RUNTIME=runtime)
            session.add(add_film_missing_runtime)
            commit(session)
            update_film_last_mod(self.Session, ZP_FILM_ID)
        session.close()

    def process_rating(self, eapi, ZP_FILM_ID, ZP_LANG_ID, rating):
        """Process rating

            Args:
                | eapi (str): the dune id
                | ZP_FILM_ID (int): The film id
                | ZP_LANG_ID (int): The language id
                | rating (int): rating

        """
        session = self.Session()
        try:
            log.debug('Looking see if ZP_FILM_ID: {0} and RATING: {1} in ZP_FILM_RATING'.format(
                ZP_FILM_ID,
                rating))
            session.query(
                TABLES.ZP_FILM_RATING).filter(
                TABLES.ZP_FILM_RATING.ZP_FILM_ID == ZP_FILM_ID).one()
        except orm.exc.NoResultFound as e:
            log.debug('ZP_FILM_ID: {0} and RATING: {1} NOT in ZP_FILM_RATING'.format(
                ZP_FILM_ID,
                rating))
            add_film_missing_rating = TABLES.ZP_FILM_RATING(ZP_FILM_ID=ZP_FILM_ID,
                                                            RATING=rating)
            session.add(add_film_missing_rating)
            commit(session)
            update_film_last_mod(self.Session, ZP_FILM_ID)
        session.close()

    def process_credits(self, eapi, ZP_FILM_ID, ZP_LANG_ID, credits):
        """Process credits

            Args:
                | eapi (str): the dune id
                | ZP_FILM_ID (int): The film id
                | ZP_LANG_ID (int): The language id
                | credits (dict): credits

        """
        if credits['crew']:
            self.process_crew(eapi, ZP_FILM_ID, ZP_LANG_ID, credits['crew'])

        if credits['cast']:
            self.process_cast(eapi, ZP_FILM_ID, ZP_LANG_ID, credits['cast'])

    def process_crew(self, eapi, ZP_FILM_ID, ZP_LANG_ID, crew):
        """Process crew

            Args:
                | eapi (str): the dune id
                | ZP_FILM_ID (int): The film id
                | ZP_LANG_ID (int): The language id
                | crew (list): [{'job':'Director',
                |					'id':0}]

        """
        session = self.Session()
        if session.query(TABLES.ZP_FILM_ROLE_XREF).filter(
                TABLES.ZP_FILM_ROLE_XREF.ZP_FILM_ID == ZP_FILM_ID,
                TABLES.ZP_FILM_ROLE_XREF.ZP_ROLE_ID == 2).count() == 0:
            for person in crew:
                if person['job'] == 'Director':
                    eapi_person_eid = person['id']
                    zp_people_id = self.get_zp_people_id(eapi, eapi_person_eid)
                    if isinstance(zp_people_id, int) and zp_people_id > 0:
                        try:
                            session.query(
                                TABLES.ZP_FILM_ROLE_XREF).filter(
                                TABLES.ZP_FILM_ROLE_XREF.ZP_FILM_ID == ZP_FILM_ID,
                                TABLES.ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID == zp_people_id,
                                TABLES.ZP_FILM_ROLE_XREF.ZP_ROLE_ID == 2).one().ZP_PEOPLE_ID
                        except orm.exc.NoResultFound as e:
                            film_role_xref = TABLES.ZP_FILM_ROLE_XREF(ZP_FILM_ID=ZP_FILM_ID,
                                                                      ZP_PEOPLE_ID=zp_people_id,
                                                                      ZP_ROLE_ID=2)
                            session.add(film_role_xref)
                            commit(session)
                            update_film_last_mod(self.Session, ZP_FILM_ID)
                    else:
                        log.warning('zp_people_id %s is not int or > 0 but %s', zp_people_id, type(zp_people_id))
        session.close()

    def process_cast(self, eapi, ZP_FILM_ID, ZP_LANG_ID, cast):
        """Process cast

            Args:
                | eapi (str): the dune id
                | ZP_FILM_ID (int): The film id
                | ZP_LANG_ID (int): The language id
                | cast (list): [{'id':0}]

        """
        # log.warning(cast)
        # raise SystemExit
        session = self.Session()
        if session.query(TABLES.ZP_FILM_ROLE_XREF).filter(
                TABLES.ZP_FILM_ROLE_XREF.ZP_FILM_ID == ZP_FILM_ID,
                TABLES.ZP_FILM_ROLE_XREF.ZP_ROLE_ID == 1).count() == 0:
            for person in cast:
                role_order = None
                if 'order' in person:
                    if isinstance(person['order'], int):
                        role_order = person['order']
                eapi_person_eid = person['id']
                zp_people_id = self.get_zp_people_id(eapi, eapi_person_eid)
                if isinstance(zp_people_id, int) and zp_people_id > 0:
                    try:
                        session.query(
                            TABLES.ZP_FILM_ROLE_XREF).filter(
                            TABLES.ZP_FILM_ROLE_XREF.ZP_FILM_ID == ZP_FILM_ID,
                            TABLES.ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID == zp_people_id,
                            TABLES.ZP_FILM_ROLE_XREF.ZP_ROLE_ID == 1).one().ZP_PEOPLE_ID
                    except orm.exc.NoResultFound as e:
                        film_role_xref = TABLES.ZP_FILM_ROLE_XREF(ZP_FILM_ID=ZP_FILM_ID,
                                                                  ZP_PEOPLE_ID=zp_people_id,
                                                                  ZP_ROLE_ID=1,
                                                                  ROLE_ORDER=role_order)
                        session.add(film_role_xref)
                        commit(session)
                        update_film_last_mod(self.Session, ZP_FILM_ID)
                else:
                    log.warning('zp_people_id %s is not int or > 0 but %s', zp_people_id, type(zp_people_id))
        session.close()

    def get_zp_people_id(self, eapi, eapi_person_eid):
        """Get zp_people_id from eapi_person_eid

            Note:
                If the eapi persion does not exist a new entry will de added to
                the db

            Args:
                | eapi: tmdb, imdb
                | eapi_person_eid: eapi person id
        """
        session = self.Session()
        zp_person_id = None
        try:
            zp_person_id = session.query(
                TABLES.ZP_PEOPLE_EAPI_XREF).filter(
                TABLES.ZP_PEOPLE_EAPI_XREF.ZP_EAPI_ID == self.eapi_dict[eapi],
                TABLES.ZP_PEOPLE_EAPI_XREF.ZP_EAPI_EID == eapi_person_eid).one().ZP_PEOPLE_ID
        except orm.exc.NoResultFound as e:
            log.debug('ZP_PEOPLE_ID not found in ZP_PEOPLE_EAPI_XREF with ZP_EAPI_ID: {0} and ZP_EAPI_EID: {1}'.format(
                self.eapi_dict[eapi],
                eapi_person_eid))
            person_data = getattr(self, eapi).get_person_info(eapi_person_eid)
            # todo rework this to use eapi eids as there now looks to be imdb id in people api responses from tmdb
            if isinstance(person_data, dict):
                if 'name' in person_data:
                    if isinstance(person_data['name'], string_types):
                        if 'birthday' in person_data:
                            if isinstance(person_data['birthday'], string_types):
                                if self.validate_date_text(person_data['birthday']) == False:
                                    person_data['birthday'] = None
                            elif person_data['birthday'] is not None:
                                person_data['birthday'] = None
                        else:
                            person_data['birthday'] = None
                        try:
                            # if dob is null but there is allready a person in ZP_PEOPLE with the same name that also has
                            # a null dob then we need to exclude any current ZP_PEOPLE_EAPI_XREF with ZP_EAPI_ID of
                            # current eapi

                            zp_people_id = session.query(
                                TABLES.ZP_PEOPLE).filter(
                                TABLES.ZP_PEOPLE.DOB == person_data['birthday'],
                                TABLES.ZP_PEOPLE.NAME == person_data['name']).filter(
                                ~TABLES.ZP_PEOPLE.ID.in_(
                                    session.query(
                                        TABLES.ZP_PEOPLE_EAPI_XREF.ZP_PEOPLE_ID).filter(
                                        TABLES.ZP_PEOPLE_EAPI_XREF.ZP_EAPI_ID == self.eapi_dict[eapi]))).one().ID
                        except orm.exc.NoResultFound as e:
                            log.debug('ZP_PEOPLE_ID not found in ZP_PEOPLE with DOB: {0} and NAME: {1}'.format(
                                person_data['birthday'],
                                person_data['name']))
                            person = TABLES.ZP_PEOPLE(DOB=person_data['birthday'],
                                                      NAME=person_data['name'])
                            session.add(person)
                            flush(session)
                            zp_person_id = person.ID
                            if zp_person_id > 0:
                                people_eapi_xref = TABLES.ZP_PEOPLE_EAPI_XREF(ZP_PEOPLE_ID=zp_person_id,
                                                                              ZP_EAPI_ID=self.eapi_dict[eapi],
                                                                              ZP_EAPI_EID=eapi_person_eid)
                                session.add(people_eapi_xref)
                                commit(session)
                            else:
                                log.error('''zp_people_id is null when after adding person_data['birthday'] %s'''
                                          ''' and person_data['name'] %s. This should not happen.''',
                                          person_data['birthday'],
                                          person_data['name'])
                                session.rollback()
                        else:
                            if zp_person_id > 0:
                                people_eapi_xref = TABLES.ZP_PEOPLE_EAPI_XREF(ZP_PEOPLE_ID=zp_person_id,
                                                                              ZP_EAPI_ID=self.eapi_dict[eapi],
                                                                              ZP_EAPI_EID=eapi_person_eid)
                                session.add(people_eapi_xref)
                                commit(session)
                            else:
                                log.error('ZP_PEOPLE_ID %s found in ZP_PEOPLE but is not > 0 (this should not happen) '
                                          'with DOB: {0} and NAME: {1}'.format(zp_person_id,
                                                                               person_data['birthday'],
                                                                               person_data['name']))
                    else:
                        log.warning('''person_data['name'] is not string but %s''', type(person_data['name']))
                else:
                    log.warning('name not in person_data.keys() %s or ', person_data.keys())
            else:
                log.warning('person_data not dict but %s', type(person_data))
                zp_person_id = None
        session.close()
        return zp_person_id

    def validate_date_text(self, date_text):
        """Validate text is date string YYYY-MM-DD

            Args:
                date_text (string): 'YYYY-MM-DD'
        """
        try:
            datetime.strptime(date_text, '%Y-%m-%d')
        except ValueError:
            return False
        else:
            return True

    def eapi_eid_from_zp_film_id(self, eapi_id, zp_film_id):
        """Get eapi_id from zp_film_id

            Args:
                | eapi_id (int): 0
                | zp_film_id (int): 0
        """
        session = self.Session()
        ZP_EAPI_EID = session.query(TABLES.ZP_FILM_EAPI_EID).filter(
            TABLES.ZP_FILM_EAPI_EID.ZP_FILM_ID == zp_film_id,
            TABLES.ZP_FILM_EAPI_EID.ZP_EAPI_ID == eapi_id).one().ZP_EAPI_EID
        session.close()
        return ZP_EAPI_EID

    def eapi_eid_from_zp_film_collection_id(self, eapi_id, zp_film_collection_id):
        """Get eapi_id from zp_film_id

            Args:
                | eapi_id (int): 0
                | zp_film_id (int): 0
        """
        session = self.Session()
        ZP_EAPI_EID = session.query(TABLES.ZP_FILM_COLLECTION_EAPI_EID).filter(
            TABLES.ZP_FILM_COLLECTION_EAPI_EID.ZP_FILM_COLLECTION_ID == zp_film_collection_id,
            TABLES.ZP_FILM_COLLECTION_EAPI_EID.ZP_EAPI_ID == eapi_id).one().ZP_EAPI_COLLECTION_EID
        session.close()
        return ZP_EAPI_EID
