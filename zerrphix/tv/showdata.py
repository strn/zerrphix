# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

from datetime import datetime
from datetime import timedelta
import logging
import sys

from sqlalchemy import func, orm

from zerrphix.db import flush, commit
from zerrphix.db.tables import TABLES
from zerrphix.plugin import load_plugins
from zerrphix.tv.util import update_tv_last_mod
from zerrphix.util.plugin import create_eapi_plugins_list, create_eapi_dict
from zerrphix.util.text import date_time
from six import string_types
#from zerrphix.util import set_retry
#from zerrphix.util import get_user_langs, check_can_retry
#from types import MethodType
#from zerrphix.util import iso_639_part1_from_zp_lang_id
from zerrphix.tv.base import TVBase
log = logging.getLogger(__name__)


class ShowData(TVBase):
    """Get Data for tvs (actors, runtime, synop etc...)
    """

    def __init__(self, **kwargs):
        """Data __init__

            Args:
                | args (list): Passed through args from the command line.
                | Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.
        """
        super(ShowData, self).__init__(**kwargs)
        self, self.eapi_tv_plugins_access_list, loaded_plugins = create_eapi_plugins_list(
            'tv', sys.modules, load_plugins(self.args), self)
        if not self.eapi_tv_plugins_access_list:
            raise Exception(('There not any entries in eapi_tv_plugins_access_list'
                             ' therefore scanning is pointless'))
        session = self.Session()
        self.eapi_dict = create_eapi_dict(session)
        #self.set_retry = MethodType(set_retry, self)
        #self.iso_639_part1_from_zp_lang_id = MethodType(iso_639_part1_from_zp_lang_id, self)
        self.library = 'TV'
        session.close()
        self.data_keys = ['genres', 'name', 'original_name',
                         'overview', 'first_air_date',
                         'rating', 'credits']
        #self.get_user_langs = MethodType(get_user_langs, self)
        #self.check_can_retry = MethodType(check_can_retry, self)

    def get_show_data_processing_no_retry(self, zp_tv_id, eapi, zp_lang_id):
        return_list = []
        session = self.Session()
        qry_tv_missing_data = session.query(
            TABLES.ZP_TV).filter(
            TABLES.ZP_TV.ID < zp_tv_id,
            (~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_ROLE_XREF.ZP_TV_ID)) |
            ~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_GENRE_XREF.ZP_TV_ID)) |
            ~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_RATING.ZP_TV_ID)) |
            ~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_OVERVIEW.ZP_TV_ID).filter(
                        TABLES.ZP_TV_OVERVIEW.ZP_LANG_ID == zp_lang_id,
                        TABLES.ZP_TV_OVERVIEW.ZP_EAPI_ID == self.eapi_dict[eapi]
                    )) |
            ~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_TITLE.ZP_TV_ID).filter(
                        TABLES.ZP_TV_TITLE.ZP_LANG_ID == zp_lang_id,
                        TABLES.ZP_TV_TITLE.ZP_EAPI_ID == self.eapi_dict[eapi]
                    )) |
            ~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_RELEASE.ZP_TV_ID))),
            TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_EAPI_EID.ZP_TV_ID)),
            ~TABLES.ZP_TV.ID.in_(session.query(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 4,
                TABLES.ZP_RETRY.ZP_LANG_ID == zp_lang_id,
                TABLES.ZP_RETRY.ZP_EAPI_ID == self.eapi_dict[eapi]
            ))
        )
        if qry_tv_missing_data.count() > 0:
            tvs_missing_data = qry_tv_missing_data.order_by(TABLES.ZP_TV.ID.desc()).limit(50)
            # TODO: Parental Rating
            for tv in tvs_missing_data:
                return_list.append(tv.ID)
        session.close()
        return return_list

    def get_show_data_processing_retry(self, zp_tv_id, eapi, zp_lang_id):
        return_dict = {}
        session = self.Session()
        qry_tv_missing_data = session.query(
            TABLES.ZP_TV.ID, TABLES.ZP_RETRY_COUNT.DELAY,
            TABLES.ZP_RETRY.DATETIME, TABLES.ZP_RETRY.COUNT).filter(
            TABLES.ZP_TV.ID < zp_tv_id,
            (~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_ROLE_XREF.ZP_TV_ID)) |
            ~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_GENRE_XREF.ZP_TV_ID)) |
            ~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_RATING.ZP_TV_ID)) |
            ~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_OVERVIEW.ZP_TV_ID).filter(
                        TABLES.ZP_TV_OVERVIEW.ZP_LANG_ID == zp_lang_id,
                        TABLES.ZP_TV_OVERVIEW.ZP_EAPI_ID == self.eapi_dict[eapi]
                    )) |
            ~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_TITLE.ZP_TV_ID).filter(
                        TABLES.ZP_TV_TITLE.ZP_LANG_ID == zp_lang_id,
                        TABLES.ZP_TV_TITLE.ZP_EAPI_ID == self.eapi_dict[eapi]
                    )) |
            ~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_RELEASE.ZP_TV_ID))),
            TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_EAPI_EID.ZP_TV_ID)),
            TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == TABLES.ZP_RETRY_COUNT.ZP_RETRY_TYPE_ID,
            TABLES.ZP_FILM.ID == TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID,
            TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 4,
            TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == 1,
            TABLES.ZP_RETRY.ZP_LANG_ID == zp_lang_id,
            TABLES.ZP_RETRY.ZP_EAPI_ID == self.eapi_dict[eapi],
            TABLES.ZP_RETRY_COUNT.COUNT == session.query(
                func.max(TABLES.ZP_RETRY_COUNT.COUNT)
            ).filter(
                TABLES.ZP_RETRY.COUNT >= TABLES.ZP_RETRY_COUNT.COUNT).order_by(
                TABLES.ZP_RETRY_COUNT.COUNT.desc()).correlate(TABLES.ZP_RETRY).as_scalar()
        )
        if qry_tv_missing_data.count() > 0:
            tvs_missing_data = qry_tv_missing_data.order_by(TABLES.ZP_TV.ID.desc()).limit(50)
            # TODO: Parental Rating
            for result in tvs_missing_data:
                return_dict[result.ID] = {}
                return_dict[result.ID]['datetime'] = result.DATETIME
                return_dict[result.ID]['count'] = result.COUNT
                return_dict[result.ID]['delay'] = result.DELAY
        session.close()
        return return_dict

    def acquire(self):
        """Kick of the process of gathering tv data

            Attributes dict:
            | tv_data:
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
        # Get tvs that do not exist in any of the tables
        # order by tv ID desc (prcessed newly added tvs first)
        # TODO: update tv update_datetime
        user_langs = self.get_all_user_library_langs(2)
         # todo optionise adding english as a fallback when user specifics are done
        if 1823 not in user_langs:
             user_langs[1823] = 'English'
        self.user_langs = user_langs
        session = self.Session()
        max_tv_id = session.query(func.max(TABLES.ZP_TV.ID)).one()[0]
        session.close()
        if isinstance(max_tv_id, int):
            for zp_lang_id in self.user_langs:
                self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                             14,
                                                             'LANG: %s' % self.user_langs[zp_lang_id])
                for eapi in self.eapi_tv_plugins_access_list:
                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                14,
                                                                 'LANG: %s, EAPI: %s' % (
                                                                     self.user_langs[zp_lang_id],
                                                                     eapi
                                                                 ))
                    if hasattr(getattr(self, eapi), 'get_tv_show_data'):
                        zp_tv_id = max_tv_id + 1
                        lang_processing_complete = False
                        while lang_processing_complete is False:
                            show_data_missing_list = self.get_show_data_processing_no_retry(zp_tv_id, eapi, zp_lang_id)
                            #raise SystemExit
                            if show_data_missing_list:
                                for show_data_missing_id in show_data_missing_list:
                                    zp_tv_id = show_data_missing_id
                                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                                 14,
                                                                                 'LANG: %s EAPI: %s TV: %s/%s' % (
                                                                                     self.user_langs[zp_lang_id],
                                                                                     eapi,
                                                                                     zp_tv_id,
                                                                                     max_tv_id
                                                                                 ))
                                    self.get_showdata(zp_tv_id, eapi, zp_lang_id)
                                    # raise SystemExit
                            else:
                                lang_processing_complete = True
                    else:
                        log.info('eapi %s does not have get_tv_show_data', eapi)
            if self.check_can_retry(1) is True:
                log.debug('Retrying Show Data')
                for zp_lang_id in self.user_langs:
                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                 14,
                                                                 'LANG: %s' % self.user_langs[zp_lang_id])
                    for eapi in self.eapi_tv_plugins_access_list:
                        self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                    14,
                                                                     'LANG: %s EAPI: %s' % (
                                                                         self.user_langs[zp_lang_id],
                                                                         eapi
                                                                     ))
                        if hasattr(getattr(self, eapi), 'get_tv_show_data'):
                            zp_tv_id = max_tv_id + 1
                            lang_processing_complete = False
                            while lang_processing_complete is False:
                                show_data_missing_dict = self.get_show_data_processing_retry(zp_tv_id, eapi, zp_lang_id)
                                if show_data_missing_dict:
                                    for show_data_missing_id in show_data_missing_dict:
                                        zp_tv_id = show_data_missing_id
                                        if show_data_missing_dict[zp_tv_id]['datetime'] + timedelta(
                                            days=show_data_missing_dict[zp_tv_id]['delay']) <= datetime.now():
                                            log.debug('dt %s, plus %s is %s which is less than than now %s',
                                                      show_data_missing_dict[zp_tv_id]['datetime'],
                                                      show_data_missing_dict[zp_tv_id]['delay'],
                                                      show_data_missing_dict[zp_tv_id]['datetime'] + timedelta(
                                                          days=show_data_missing_dict[zp_tv_id]['delay']), datetime.now())
                                            self.set_current_library_process_desc_detail(
                                                self.library_config_dict['id'],
                                                14,
                                                'LANG: %s EAPI: %s TV: %s/%s. Retrying.' % (
                                                    self.user_langs[
                                                        zp_lang_id],
                                                    eapi,
                                                    zp_tv_id,
                                                    max_tv_id
                                                ))
                                            self.get_showdata(zp_tv_id, eapi, zp_lang_id)
                                        else:
                                            self.set_current_library_process_desc_detail(
                                                self.library_config_dict['id'],
                                                14,
                                                'LANG: %s EAPI: %s TV: %s/%s. To soon to retry.' % (
                                                    self.user_langs[
                                                        zp_lang_id],
                                                    eapi,
                                                    zp_tv_id,
                                                    max_tv_id
                                                ))
                                            log.debug('dt %s, plus %s is %s which is not less than now %s',
                                                      show_data_missing_dict[zp_tv_id]['datetime'],
                                                      show_data_missing_dict[zp_tv_id]['delay'],
                                                      show_data_missing_dict[zp_tv_id]['datetime'] + timedelta(
                                                          days=show_data_missing_dict[zp_tv_id]['delay']), datetime.now())
                                else:
                                    lang_processing_complete = True
                        else:
                            log.info('eapi %s does not have get_tv_show_data', eapi)

    def get_showdata(self, zp_tv_id, eapi, zp_lang_id):
        if zp_lang_id is None:
            iso_639_part1 = None
        else:
            iso_639_part1 = self.iso_639_part1_from_zp_lang_id(zp_lang_id)
        try:
            tv_eapi_eid = self.eapi_eid_from_zp_tv_id(self.eapi_dict[eapi], zp_tv_id)
        except orm.exc.NoResultFound as e:
            log.debug(('zp_tv_id: {0} with self.eapi_dict[eapi]: {1} not in ZP_TV_EAPI_EID').format(
                zp_tv_id,
                self.eapi_dict[eapi]))
        else:
            tv_data = getattr(self, eapi).get_tv_show_data(tv_eapi_eid, iso_639_part1)
            # print(tv_data)
            # raise SystemExit
            if isinstance(tv_data, dict):
                for key in tv_data:
                    # print(key)
                    if tv_data[key]:
                        if key in self.data_keys:
                            getattr(self, 'process_{0}'.format(key))(eapi,
                                                                     zp_tv_id,
                                                                     zp_lang_id,
                                                                     tv_data[key])
                    else:
                        log.warning(
                            'No {0}: {1} type: {2} found for ZP_EAPI_EID: {3} from ZP_EAPI_ID: {4}'.format(
                                key,
                                tv_data[key],
                                type(tv_data[key]),
                                tv_eapi_eid,
                                self.eapi_dict[eapi]))
            else:
                log.warning('tv data: {0} type: {1} is not dict'.format(tv_data,
                                                                        type(tv_data)))
        if self.showdata_missing_data_check(zp_tv_id, eapi, zp_lang_id) is True:
            #log.error('missing data zp_tv_id %s, eapi %s, zp_lang_id %s', zp_tv_id, eapi, zp_lang_id)
            #raise SystemExit
            self.set_retry(1, 4, zp_tv_id, self.eapi_dict[eapi], zp_lang_id)
        #raise SystemExit

    def showdata_missing_data_check(self, zp_tv_id, eapi, zp_lang_id):
        session = self.Session()
        try:
            session.query(
                TABLES.ZP_TV).filter(
                TABLES.ZP_TV.ID == zp_tv_id,
                (~TABLES.ZP_TV.ID.in_(
                    session.query(
                        TABLES.ZP_TV_ROLE_XREF.ZP_TV_ID)) |
                ~TABLES.ZP_TV.ID.in_(
                    session.query(
                        TABLES.ZP_TV_GENRE_XREF.ZP_TV_ID)) |
                ~TABLES.ZP_TV.ID.in_(
                    session.query(
                        TABLES.ZP_TV_RATING.ZP_TV_ID)) |
                ~TABLES.ZP_TV.ID.in_(
                    session.query(
                        TABLES.ZP_TV_OVERVIEW.ZP_TV_ID).filter(
                        TABLES.ZP_TV_OVERVIEW.ZP_LANG_ID == zp_lang_id,
                        TABLES.ZP_TV_OVERVIEW.ZP_EAPI_ID == self.eapi_dict[eapi]
                    )) |
                ~TABLES.ZP_TV.ID.in_(
                    session.query(
                        TABLES.ZP_TV_TITLE.ZP_TV_ID).filter(
                        TABLES.ZP_TV_TITLE.ZP_LANG_ID == zp_lang_id,
                        TABLES.ZP_TV_TITLE.ZP_EAPI_ID == self.eapi_dict[eapi]
                    )) |
                ~TABLES.ZP_TV.ID.in_(
                    session.query(
                        TABLES.ZP_TV_RELEASE.ZP_TV_ID))),
                TABLES.ZP_TV.ID.in_(
                    session.query(
                        TABLES.ZP_TV_EAPI_EID.ZP_TV_ID))
            ).one()
        except orm.exc.NoResultFound:
            session.close()
            return False
        session.close()
        return True

    def process_genres(self, eapi, zp_tv_id, zp_lang_id, genres):
        """Process genres

            Args:
                | eapi (str): the dune id
                | zp_tv_id (int): The tv id
                | zp_lang_id (int): The language id
                | genres (list): [{'name':'genre'}]

        """
        session = self.Session()
        #log.warning(genres)
        for zp_genre_id in genres:
            try:
                 session.query(
                     TABLES.ZP_TV_GENRE_XREF).filter(
                     TABLES.ZP_TV_GENRE_XREF.ZP_TV_ID == zp_tv_id,
                     TABLES.ZP_TV_GENRE_XREF.ZP_GENRE_ID == zp_genre_id).one()
            except orm.exc.NoResultFound as e:
                 add_genre_xref = TABLES.ZP_TV_GENRE_XREF(ZP_TV_ID=zp_tv_id,
                                                            ZP_GENRE_ID=zp_genre_id)
                 session.add(add_genre_xref)
                 commit(session)
                 update_tv_last_mod(self.Session, zp_tv_id)
            else:
                pass
        session.close()
    # TODO: Manage multiple titles how to choose which to display on ui (there are more than one title for
    # each tv in ZP_TV_TITLE) prob add lang and title_type (origional .....) and how to deal with
    # multiple languages and what happens if not specific title is aquired. Use all langs currently
    # used for all users and which they prefer title or origional title

    def process_name(self, eapi, zp_tv_id, zp_lang_id, title, ZP_TV_TITLE_TYPE_ID=1):
        """Process title

            Args:
                | eapi (str): the dune id
                | zp_tv_id (int): The tv id
                | zp_lang_id (int): The language id
                | title (list): title
                | ZP_TV_TITLE_TYPE_ID (int): title type id

        """
        session = self.Session()
        try:
            session.query(
                TABLES.ZP_TV_TITLE).filter(
                TABLES.ZP_TV_TITLE.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_TV_TITLE.ZP_EAPI_ID == self.eapi_dict[eapi],
                TABLES.ZP_TV_TITLE.ZP_LANG_ID == zp_lang_id,
                TABLES.ZP_TV_TITLE.ZP_TV_TITLE_TYPE_ID == ZP_TV_TITLE_TYPE_ID).one()
        except orm.exc.NoResultFound:
            add_tv_title = TABLES.ZP_TV_TITLE(ZP_TV_ID=zp_tv_id,
                                                  TITLE=title,
                                                  ZP_LANG_ID=zp_lang_id,
                                                  ZP_TV_TITLE_TYPE_ID=ZP_TV_TITLE_TYPE_ID,
                                                  ZP_EAPI_ID=self.eapi_dict[eapi])
            session.add(add_tv_title)
            commit(session)
            update_tv_last_mod(self.Session, zp_tv_id)
        session.close()

    def process_original_name(self, eapi, zp_tv_id, zp_lang_id, title):
        """Process origional_title

            Args:
                | eapi (str): the dune id
                | zp_tv_id (int): The tv id
                | zp_lang_id (int): The language id
                | title (str): origional_title

        """
        self.process_name(eapi, zp_tv_id, zp_lang_id, title, 2)

    def process_overview(self, eapi, zp_tv_id, zp_lang_id, overview):
        """Process overview

            Args:
                | eapi (str): the dune id
                | zp_tv_id (int): The tv id
                | zp_lang_id (int): The language id
                | overview (str): overview

        """
        session = self.Session()
        try:
            session.query(
                TABLES.ZP_TV_OVERVIEW).filter(
                TABLES.ZP_TV_OVERVIEW.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_TV_OVERVIEW.ZP_EAPI_ID == self.eapi_dict[eapi],
                TABLES.ZP_TV_OVERVIEW.ZP_LANG_ID == zp_lang_id).one()
        except orm.exc.NoResultFound:
            add_tv_overview = TABLES.ZP_TV_OVERVIEW(ZP_TV_ID=zp_tv_id,
                                                        OVERVIEW=overview,
                                                        ZP_LANG_ID=zp_lang_id,
                                                        ZP_EAPI_ID=self.eapi_dict[eapi])

            session.add(add_tv_overview)
            commit(session)
            update_tv_last_mod(self.Session, zp_tv_id)
        session.close()

    def process_first_air_date(self, eapi, zp_tv_id, zp_lang_id, release_date):
        """Process release_date

            Args:
                | eapi (str): the dune id
                | zp_tv_id (int): The tv id
                | zp_lang_id (int): The language id
                | release_date (str): release_date

        """
        session = self.Session()
        try:
            session.query(
                TABLES.ZP_TV_RELEASE).filter(
                TABLES.ZP_TV_RELEASE.ZP_TV_ID == zp_tv_id).one()
        except orm.exc.NoResultFound as e:
            add_tv_release_date = TABLES.ZP_TV_RELEASE(ZP_TV_ID=zp_tv_id,
                                                       RELEASE_DATE=release_date)
            session.add(add_tv_release_date)
            commit(session)
            update_tv_last_mod(self.Session, zp_tv_id)
        session.close()

    def process_rating(self, eapi, zp_tv_id, zp_lang_id, rating):
        """Process rating

            Args:
                | eapi (str): the dune id
                | zp_tv_id (int): The tv id
                | zp_lang_id (int): The language id
                | rating (int): rating

        """
        session = self.Session()
        try:
            log.debug('Looking see if zp_tv_id: {0} and RATING: {1} in ZP_TV_RATING'.format(
                zp_tv_id,
                rating))
            session.query(
                TABLES.ZP_TV_RATING).filter(
                TABLES.ZP_TV_RATING.ZP_TV_ID == zp_tv_id).one()
        except orm.exc.NoResultFound as e:
            log.debug('zp_tv_id: {0} and RATING: {1} NOT in ZP_TV_RATING'.format(
                zp_tv_id,
                rating))
            add_tv_missing_rating = TABLES.ZP_TV_RATING(ZP_TV_ID=zp_tv_id,
                                                        RATING=rating)
            session.add(add_tv_missing_rating)
            commit(session)
            update_tv_last_mod(self.Session, zp_tv_id)
        session.close()

    def process_credits(self, eapi, zp_tv_id, zp_lang_id, credits):
        """Process credits

            Args:
                | eapi (str): the dune id
                | zp_tv_id (int): The tv id
                | zp_lang_id (int): The language id
                | credits (dict): credits

        """
        if credits['crew']:
            self.process_crew(eapi, zp_tv_id, zp_lang_id, credits['crew'])

        if credits['cast']:
            self.process_cast(eapi, zp_tv_id, zp_lang_id, credits['cast'])

    def process_crew(self, eapi, zp_tv_id, zp_lang_id, crew):
        """Process crew

            Args:
                | eapi (str): the dune id
                | zp_tv_id (int): The tv id
                | zp_lang_id (int): The language id
                | crew (list): [{'job':'Director',
                |					'id':0}]

        """
        session = self.Session()
        if session.query(TABLES.ZP_TV_ROLE_XREF).filter(
                TABLES.ZP_TV_ROLE_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_TV_ROLE_XREF.ZP_ROLE_ID == 2).count() == 0:
            for person in crew:
                if person['job'] == 'Director':
                    eapi_person_eid = person['id']
                    zp_people_id = self.get_zp_people_id(eapi, eapi_person_eid)
                    if zp_people_id:
                        try:
                            session.query(
                                TABLES.ZP_TV_ROLE_XREF).filter(
                                TABLES.ZP_TV_ROLE_XREF.ZP_TV_ID == zp_tv_id,
                                TABLES.ZP_TV_ROLE_XREF.ZP_PEOPLE_ID == zp_people_id,
                                TABLES.ZP_TV_ROLE_XREF.ZP_ROLE_ID == 2).one().ZP_PEOPLE_ID
                        except orm.exc.NoResultFound as e:
                            tv_role_xref = TABLES.ZP_TV_ROLE_XREF(ZP_TV_ID=zp_tv_id,
                                                                  ZP_PEOPLE_ID=zp_people_id,
                                                                  ZP_ROLE_ID=2)
                            session.add(tv_role_xref)
                            commit(session)
                            update_tv_last_mod(self.Session, zp_tv_id)
        session.close()

    def process_cast(self, eapi, zp_tv_id, zp_lang_id, cast):
        """Process cast

            Args:
                | eapi (str): the dune id
                | zp_tv_id (int): The tv id
                | zp_lang_id (int): The language id
                | cast (list): [{'id':0}]

        """
        session = self.Session()
        if session.query(TABLES.ZP_TV_ROLE_XREF).filter(
                TABLES.ZP_TV_ROLE_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_TV_ROLE_XREF.ZP_ROLE_ID == 1).count() == 0:
            for person in cast:
                role_order = None
                if 'order' in person:
                    if isinstance(person['order'], int):
                        role_order = person['order']
                eapi_person_eid = person['id']
                zp_people_id = self.get_zp_people_id(eapi, eapi_person_eid)
                if zp_people_id:
                    try:
                        session.query(
                            TABLES.ZP_TV_ROLE_XREF).filter(
                            TABLES.ZP_TV_ROLE_XREF.ZP_TV_ID == zp_tv_id,
                            TABLES.ZP_TV_ROLE_XREF.ZP_PEOPLE_ID == zp_people_id,
                            TABLES.ZP_TV_ROLE_XREF.ZP_ROLE_ID == 1).one().ZP_PEOPLE_ID
                    except orm.exc.NoResultFound as e:
                        tv_role_xref = TABLES.ZP_TV_ROLE_XREF(ZP_TV_ID=zp_tv_id,
                                                              ZP_PEOPLE_ID=zp_people_id,
                                                              ZP_ROLE_ID=1,
                                                              ROLE_ORDER=role_order)
                        session.add(tv_role_xref)
                        commit(session)
                        update_tv_last_mod(self.Session, zp_tv_id)
        session.close()

    # todo merge this with the one in film
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
