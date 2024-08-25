# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import re
import sys
import time

from sqlalchemy import func, orm
from datetime import datetime
from datetime import timedelta

from zerrphix.db import flush, commit
from zerrphix.db.tables import TABLES
from zerrphix.plugin import load_plugins
from zerrphix.util import list1_not_in_list2
from zerrphix.util.numbers import seconds_to_hours
from zerrphix.util.plugin import create_eapi_plugins_list, create_eapi_dict
from zerrphix.util.text import conform_title, date_time
from types import MethodType
#from zerrphix.util import set_retry, check_can_retry
from zerrphix.tv.base import TVBase

## regex info http://stackoverflow.com/questions/2824302/how-to-make-regular-expression-into-non-greedy
log = logging.getLogger(__name__)


# TODO: eapi get alternative titles in search
class Identify(TVBase):
    """Identify films against eapi's (e.g. tmdb, imdb)
    """

    def __init__(self, **kwargs):
        """Identify __init__

            Args:
                | args (list): Passed through args from the command line.
                | Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.

            Attributes:
                | args (list): Passed through args from the command line.
                | Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.
                | eapi_dict (dict): See zerrphix.util.plugin.create_eapi_dict

        """
        super(Identify, self).__init__(**kwargs)
        session = self.Session()
        self, self.eapi_plugins_access_list, loaded_plugins = create_eapi_plugins_list('tv', sys.modules,
                                                                                       load_plugins(self.args), self)
        if not self.eapi_plugins_access_list:
            raise Exception('There not any entries in eapi_plugins_access_list therefore scanning is pointless')
        self.eapi_dict = create_eapi_dict(session)
        session.close()

        self.search_title_variation_options = ['replace_non_alnum_with_spaces',
                                               'remove_non_alnum',
                                               'remove_country_identifier',
                                               'replace_symbols_with_words',
                                               'remove_year']
        self.result_title_variation_options = ['replace_non_alnum_with_spaces',
                                               'remove_non_alnum',
                                               'replace_symbols_with_words']
        self.library = 'tv'
        #self.set_retry = MethodType(set_retry, self)
        #self.check_can_retry = MethodType(check_can_retry, self)

    def idenfity(self):
        """Initiate the identififcation process.
        """
        processing_complete = False
        session = self.Session()
        max_ZP_TV_FILEFOLDER_ID = session.query(func.max(TABLES.ZP_TV_FILEFOLDER.ID)).one()[0]
        session.close()
        if isinstance(max_ZP_TV_FILEFOLDER_ID, int):
            session.close()
            ZP_TV_FILEFOLDER_ID = max_ZP_TV_FILEFOLDER_ID + 1
            while processing_complete == False:
                session = self.Session()
                qry_unidentified_filefolder = session.query(
                    TABLES.ZP_TV_FILEFOLDER
                ).filter(
                    TABLES.ZP_TV_FILEFOLDER.ID < ZP_TV_FILEFOLDER_ID,
                    TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == None,
                    ~TABLES.ZP_TV_FILEFOLDER.ID.in_(
                        session.query(
                            TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID
                        ).filter(
                            TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 5
                        )
                    )
                )
                # for unidenttified_filefolder in _yield_limit(qry_unidentified_filefolder, TABLES.ZP_TV_FILEFOLDER.ID, maxrq=100, order='desc'):
                ZP_TV_FILEFOLDER = qry_unidentified_filefolder.order_by(
                    TABLES.ZP_TV_FILEFOLDER.ID.desc()
                ).first()
                if ZP_TV_FILEFOLDER is not None:
                    session.close()
                    # if any(char.isdigit() for char in ZP_TV_FILEFOLDER.LAST_PATH):
                    # if ZP_TV_FILEFOLDER.LAST_PATH not in ['W1A', '''That 70's Show''', 'Stargate SG-1']:
                    #print(ZP_TV_FILEFOLDER.LAST_PATH)
                    title = conform_title(ZP_TV_FILEFOLDER.LAST_PATH, 'extract_year_from_bracket_contents')
                    #print(title)
                    year = None
                    year_search = re.search(r"""\b(\d{4})\b[^\w]*$""", title, flags=re.I | re.U)
                    if year_search:
                        year = int(year_search.group(1))
                        log.debug('detected year %s from foldername %s', year, title)
                        # raise SystemExit
                        # raise SystemExit
                    ZP_TV_FILEFOLDER_ID = ZP_TV_FILEFOLDER.ID
                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                 4,
                                                                 'Identifying: TV %s/%s' %
                                                                 (ZP_TV_FILEFOLDER_ID, max_ZP_TV_FILEFOLDER_ID))
                    # ZP_TV_FILEFOLDER_LAST_PATH = ZP_TV_FILEFOLDER.LAST_PATH
                    best_processed_search_results = self._identify_filefolder(title, year, ZP_TV_FILEFOLDER_ID)
                    # print(best_processed_search_results)
                    # raise SystemExit
                    # if best_processed_search_results['best_match']['accuracy'] < 90:
                    # raise SystemExit
                    # else:
                    # raise SystemExit
                    if best_processed_search_results['best_match']['accuracy'] > 0:
                        log.debug('using best result %s to add to db', best_processed_search_results['best_match'])
                        log.debug('all restuls %s', best_processed_search_results)
                        self.add_tv_to_db(ZP_TV_FILEFOLDER_ID,
                                          {best_processed_search_results['best_match']['eapi']:
                                               best_processed_search_results['best_match']['eapi_eid']}
                                          )
                        # raise SystemExit
                    else:
                        self.set_retry(1, 5, ZP_TV_FILEFOLDER_ID)
                    if best_processed_search_results['best_match']['accuracy'] < 100:
                        # raise SystemExit
                        log.warning('best_processed_search_results %s accuracy %s not 100%%',
                                    best_processed_search_results,
                                    best_processed_search_results['best_match']['accuracy'])

                        # time.sleep(3)
                        # raise SystemExit
                else:
                    processing_complete = True
                    session.close()

            if self.check_can_retry(1) is True:
                log.debug('Retrying TV Identify')
                processing_complete = False
                ZP_TV_FILEFOLDER_ID = max_ZP_TV_FILEFOLDER_ID + 1
                while processing_complete == False:
                    session = self.Session()
                    qry_unidentified_filefolder = session.query(
                        TABLES.ZP_TV_FILEFOLDER.ID, TABLES.ZP_TV_FILEFOLDER.LAST_PATH, TABLES.ZP_RETRY_COUNT.DELAY,
                        TABLES.ZP_RETRY.DATETIME, TABLES.ZP_RETRY.COUNT).filter(
                        TABLES.ZP_TV_FILEFOLDER.ID < ZP_TV_FILEFOLDER_ID,
                        TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 5,
                        TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == 1,
                        TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == None,
                        TABLES.ZP_RETRY_COUNT.COUNT == session.query(
                            func.max(TABLES.ZP_RETRY_COUNT.COUNT)
                        ).filter(
                            TABLES.ZP_RETRY.COUNT >= TABLES.ZP_RETRY_COUNT.COUNT).order_by(
                            TABLES.ZP_RETRY_COUNT.COUNT.desc()).correlate(TABLES.ZP_RETRY).as_scalar()
                    )
                    # for unidenttified_filefolder in _yield_limit(qry_unidentified_filefolder, TABLES.ZP_TV_FILEFOLDER.ID, maxrq=100, order='desc'):
                    ZP_TV_FILEFOLDER = qry_unidentified_filefolder.order_by(TABLES.ZP_TV_FILEFOLDER.ID.desc()).first()
                    if ZP_TV_FILEFOLDER is not None:
                        ZP_TV_FILEFOLDER_ID = ZP_TV_FILEFOLDER.ID
                        if ZP_TV_FILEFOLDER.DATETIME + timedelta(
                            days=ZP_TV_FILEFOLDER.DELAY) <= datetime.now():
                            log.debug('dt %s, plus %s is %s which is less than than now %s',
                                      '{:%Y-%m-%d %H:%M:%S}'.format(ZP_TV_FILEFOLDER.DATETIME),
                                      ZP_TV_FILEFOLDER.DELAY,
                                      '{:%Y-%m-%d %H:%M:%S}'.format(ZP_TV_FILEFOLDER.DATETIME + timedelta(
                                          days=ZP_TV_FILEFOLDER.DELAY)), '{:%Y-%m-%d %H:%M:%S}'.format(datetime.now()))
                            # if any(char.isdigit() for char in ZP_TV_FILEFOLDER.LAST_PATH):
                            # if ZP_TV_FILEFOLDER.LAST_PATH not in ['W1A', '''That 70's Show''', 'Stargate SG-1']:
                            #print(ZP_TV_FILEFOLDER.LAST_PATH)
                            title = conform_title(ZP_TV_FILEFOLDER.LAST_PATH, 'extract_year_from_bracket_contents')
                            #print(title)
                            year = None
                            year_search = re.search(r"""\b(\d{4})\b[^\w]*$""", title, flags=re.I | re.U)
                            if year_search:
                                year = int(year_search.group(1))
                                print(title)
                                # raise SystemExit
                                # raise SystemExit
                            # ZP_TV_FILEFOLDER_LAST_PATH = ZP_TV_FILEFOLDER.LAST_PATH
                            session.close()
                            best_processed_search_results = self._identify_filefolder(title, year, ZP_TV_FILEFOLDER_ID)
                            # print(best_processed_search_results)
                            # raise SystemExit
                            # if best_processed_search_results['best_match']['accuracy'] < 90:
                            # raise SystemExit
                            # else:
                            # raise SystemExit
                            if best_processed_search_results['best_match']['accuracy'] > 0:
                                self.add_tv_to_db(ZP_TV_FILEFOLDER_ID,
                                                  {best_processed_search_results['best_match']['eapi']:
                                                       best_processed_search_results['best_match']['eapi_eid']}
                                                  )
                                # raise SystemExit
                            if best_processed_search_results['best_match']['accuracy'] < 100:
                                # raise SystemExit
                                log.warning('best_processed_search_results %s accuracy %s not 100%%',
                                            best_processed_search_results,
                                            best_processed_search_results['best_match']['accuracy'])
                                self.set_retry(1, 5, ZP_TV_FILEFOLDER_ID)
                                # time.sleep(3)
                                # raise SystemExit

                        else:
                            log.debug('dt %s, plus %s is %s which is not less than now %s',
                                      '{:%Y-%m-%d %H:%M:%S}'.format(ZP_TV_FILEFOLDER.DATETIME),
                                      ZP_TV_FILEFOLDER.DELAY,
                                      '{:%Y-%m-%d %H:%M:%S}'.format(ZP_TV_FILEFOLDER.DATETIME + timedelta(
                                          days=ZP_TV_FILEFOLDER.DELAY)), '{:%Y-%m-%d %H:%M:%S}'.format(datetime.now()))
                    else:
                        processing_complete = True
                        session.close()

    def set_retry(self, ZP_RETRY_TYPE_ID, ZP_RETRY_ENTITY_TYPE_ID, ZP_RETRY_ENTITY_ID):
        session = self.Session()
        max_count = session.query(TABLES.ZP_RETRY_TYPE).filter(TABLES.ZP_RETRY_TYPE.ID == 1).one().MAX_COUNT
        try:
            ZP_RETRY = session.query(TABLES.ZP_RETRY).filter(
                TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == ZP_RETRY_TYPE_ID,
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == ZP_RETRY_ENTITY_TYPE_ID,
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID == ZP_RETRY_ENTITY_ID).one()
        except orm.exc.NoResultFound:
            add_ZP_RETRY = TABLES.ZP_RETRY(ZP_RETRY_TYPE_ID=ZP_RETRY_TYPE_ID,
                                           ZP_RETRY_ENTITY_TYPE_ID=ZP_RETRY_ENTITY_TYPE_ID,
                                           ZP_RETRY_ENTITY_ID=ZP_RETRY_ENTITY_ID,
                                           DATETIME=date_time(),
                                           COUNT=1)
            session.add(add_ZP_RETRY)
            commit(session)
        else:
            if ZP_RETRY.COUNT < max_count:
                ZP_RETRY.COUNT = ZP_RETRY.COUNT + 1
            ZP_RETRY.DATETIME = date_time()
            commit(session)
        session.close()

    def add_tv_to_db(self, ZP_TV_FILEFOLDER_ID, eapi_dict):
        session = self.Session()

        if not eapi_dict:
            log.error('eapi_dict: {0} is empty for ZP_TV_FILEFOLDER_ID: {1}'.format(eapi_dict,
                                                                                          ZP_TV_FILEFOLDER_ID))
            return False

        zp_tv_id = None
        while zp_tv_id is None:
            for eapi in eapi_dict:
                try:
                    zp_tv_eapi_eid_rslt = session.query(
                        TABLES.ZP_TV_EAPI_EID
                    ).filter(
                        TABLES.ZP_TV_EAPI_EID.ZP_EAPI_EID == eapi_dict[eapi],
                        TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID == self.eapi_dict[eapi]
                    ).one()
                except orm.exc.NoResultFound:
                    log.error('Multiple results found for ZP_EAPI_EID %s ZP_EAPI_ID %s',
                              eapi_dict[eapi], self.eapi_dict[eapi])
                else:
                    log.info('eapi_dict[eapi]: {0} for self.eapi_dict[eapi] {1} allready in db no need to add.'
                             ' ZP_TV_FILEFOLDER_ID {2}'.format(
                        eapi_dict[eapi],
                        self.eapi_dict[eapi],
                        ZP_TV_FILEFOLDER_ID))
                    zp_tv_id = zp_tv_eapi_eid_rslt.ZP_TV_ID
                    #raise SystemExit
                    #return False

        ADDED_DATE_TIME = date_time()
        if zp_tv_id is None:
            add_tv = TABLES.ZP_TV(
                ADDED_DATE_TIME=ADDED_DATE_TIME,
                LAST_EDIT_DATETIME=ADDED_DATE_TIME
            )
            session.add(add_tv)
            flush(session)
            zp_tv_id = add_tv.ID
            log.debug(('Inserted ADDED_DATE_TIME: {0},'
                       ' ZP_TV_FILEFOLDER_ID:{1}, LAST_EDIT_DATETIME: {0} into ZP_TV').format(
                ADDED_DATE_TIME,
                ZP_TV_FILEFOLDER_ID))
            eapi_dict = self.get_eapi_list(eapi_dict)
            log.debug('eapi_dict: {0}'.format(eapi_dict))
            for eapi in eapi_dict:
                log.debug('eapi: {0}, eapi_eid, {1}'.format(eapi, eapi_dict[eapi]))
                if eapi_dict[eapi]:
                    add_tv_eapi_eid = TABLES.ZP_TV_EAPI_EID(
                        ZP_TV_ID=ZP_TV_ID,
                        ZP_EAPI_EID=eapi_dict[eapi],
                        ZP_EAPI_ID=self.eapi_dict[eapi]
                    )
                    log.debug(('Inserted ZP_TV_ID {0}, ZP_EAPI_EID: {1}, ZP_EAPI_ID: {2} into ZP_TV_EAPI_EID').format(
                        ZP_TV_ID,
                        eapi_dict[eapi],
                        self.eapi_dict[eapi]))
                    session.add(add_tv_eapi_eid)
                    flush(session)
                else:
                    log.debug('not adding eapi: {0}, eapi_eid, {1} to ZP_FILM_EAPI_EID'.format(eapi, eapi_dict[eapi]))

        add_tv_xref = TABLES.ZP_TV_FILEFOLDER_XREF(
            ZP_TV_ID=zp_tv_id,
            ADDED_DATE_TIME=ADDED_DATE_TIME,
            ZP_TV_FILEFOLDER_ID=ZP_TV_FILEFOLDER_ID
        )
        session.add(add_tv_xref)
        flush(session)
        tv_filefolder = session.query(
            TABLES.ZP_TV_FILEFOLDER
        ).filter(
            TABLES.ZP_TV_FILEFOLDER.ID == ZP_TV_FILEFOLDER_ID
        ).one()
        tv_filefolder.ZP_TV_ID = zp_tv_id
        commit(session)

    def get_eapi_list(self, eapi_dict):
        """Get eapi_eid's using the identified eapi_eid

            Args:
                | eapi_dict (dict): the identified eapi_eid
                | {u'tmdb': 00000}

            Returns:
                | dict: all eapi_eid's found
                | {u'tmdb': 00000,
                | u'imdb': u'tt0000000'}

        """
        # see if there are any eapis we do not have an id for yet
        # TODO allow multiple epids from one epid in single request
        # TODO loop through eapis as some may depend on a later eapi resquest results
        eids_to_find = list(set(self.eapi_dict.keys()) - set(eapi_dict.keys()))
        log.debug('eids_to_find: {0} are not in self.eapi_dict: {1}'.format(eids_to_find, self.eapi_dict))
        for eapi in self.eapi_plugins_access_list:
            if hasattr(getattr(self, eapi), 'available_eid'):
                for have_eapi in eapi_dict.keys():
                    if eapi_dict[have_eapi]:
                        for want_eapi in eids_to_find:
                            if getattr(self, eapi).available_eid(have_eapi, want_eapi, self.library) == True:
                                log.debug('eapi: {0} can get want_eapi: {1} using have_eapi: {2}'.format(
                                    eapi,
                                    want_eapi,
                                    have_eapi))
                                log.debug('have_eapi: {0}, eapi_dict[have_eapi]: {1}, want_eapi: {2}'.format(
                                    have_eapi,
                                    eapi_dict[have_eapi],
                                    want_eapi))
                                log.debug('eapi_dict: {0}'.format(eapi_dict))
                                want_eapi_eid = getattr(self, eapi).get_eapi_eid(have_eapi, eapi_dict[have_eapi],
                                                                                 want_eapi, self.library)
                                if want_eapi is not None:
                                    eapi_dict[want_eapi] = want_eapi_eid
                    else:
                        log.warning('eapi_dict[have_eapi]: {0}, have_eapi: {1}'.format(eapi_dict[have_eapi],
                                                                                       have_eapi))
            else:
                log.debug('self.{0} does not have attribute available_eid'.format(
                    eapi))
        return eapi_dict

    def _identify_filefolder(self, search_title, search_year, ZP_TV_FILEFOLDER_ID):
        search_title_list = self.construct_conformed_title_list([search_title], self.search_title_variation_options)
        episode_dict = self.episode_dict(ZP_TV_FILEFOLDER_ID)
        best_processed_search_results = {'best_match': {'accuracy': 0}}
        for search_title in search_title_list:
            processed_search_results = self._get_search_results_accuracy(self._external_source_search(search_title),
                                                                         search_year, episode_dict, search_title_list)
            if processed_search_results['best_match']['accuracy'] >= 100:
                return processed_search_results
            elif processed_search_results['best_match']['accuracy'] > best_processed_search_results['best_match'][
                'accuracy']:
                best_processed_search_results = processed_search_results
        return best_processed_search_results

    def episode_dict(self, ZP_TV_FILEFOLDER_ID):
        return_dict = {'season_list': []}
        session = self.Session()
        #episodes = session.query(TABLES.ZP_TV_EPISODE.EPISODE.distinct().label('EP_COUNT'),
        #                         TABLES.ZP_TV_EPISODE.SEASON).filter(
        #    TABLES.ZP_TV_EPISODE.ZP_TV_EPISODE_FILEFOLDER_ID == TABLES.ZP_TV_EPISODE_FILEFOLDER.ID,
        #    TABLES.ZP_TV_EPISODE_FILEFOLDER.ZP_TV_FILEFOLDER_ID == ZP_TV_FILEFOLDER_ID,
        #    TABLES.ZP_TV_EPISODE.SEASON > 0).group_by(TABLES.ZP_TV_EPISODE.SEASON).all()
        episodes = session.query(TABLES.ZP_TV_EPISODE_FILEFOLDER).filter(
            TABLES.ZP_TV_EPISODE_FILEFOLDER.ZP_TV_FILEFOLDER_ID == ZP_TV_FILEFOLDER_ID
        )
        for episode in episodes:
            if episode.SEASON not in return_dict['season_list']:
                return_dict['season_list'].append(episode.SEASON)
                return_dict[episode.SEASON] = {'episodes': []}
            for ep_num in range(episode.FIRST_EPISODE, episode.LAST_EPISODE+1):
                if ep_num not in return_dict[episode.SEASON]['episodes']:
                    return_dict[episode.SEASON]['episodes'].append(ep_num)
        for season in  return_dict['season_list']:
            return_dict[season]['ep_count'] = len(return_dict[season]['episodes'])
        session.close()
        # raise SystemExit
        return return_dict

    def _external_source_search(self, title):
        results_dict = {}
        results_dict['lookup_params'] = {}
        results_dict['lookup_params']['title'] = title
        results_dict['lookup_results'] = {}
        for external_source in self.eapi_plugins_access_list:
            log.debug('current external_source: {0} for title {1}'.format(external_source, title))
            external_source_time_begin = time.time()
            log.debug('use external_source: {0} for title {1}'.format(external_source, title))
            if hasattr(getattr(self, external_source), 'find_tv_show'):
                search_results = getattr(self, external_source).find_tv_show(title)
                external_source_time_end = time.time()
                log.debug('Total time for for external_source {0} and title {1} took: {2}'.format(
                    external_source,
                    title,
                    seconds_to_hours(external_source_time_end - external_source_time_begin)))
                log.debug('adding search_results: {0} to results_dict {1} for external_source {2} and title {3}'.format(
                    search_results, results_dict, external_source, title))
                results_dict['lookup_results'][external_source] = search_results
                log.debug('results_dict: {0}'.format(results_dict))
            else:
                log.debug('self.{0} does not have attribute find_tv_show'.format(external_source))
        return results_dict

    def _get_search_results_accuracy(self, search_results, search_year, episode_dict, search_title_list):
        """Determine accuracy of search results

            Args:
                search_results (dict): dict # search results from _external_source_search

            Returns:
                | dict:
                | If no results over 0 accuracy
                | 	{u'best_match': {u'accuracy': 0}}
                | if result(s) found:
                | 	{u'tmdb':
                | 		{u'best_match':
                | 			{u'title_list': [u'Some Film'],
                | 			u'year': 0000,
                | 			u'id': 0,
                | 			u'timings': {},
                | 			u'accuracy': 100
                | 		}
                | 	},
                | 	u'best_match':
                | 		{u'title_list':
                | 			[u'Some Film'],
                | 			u'year': 0000,
                | 			u'id': 0,
                | 			u'timings': {},
                | 			u'accuracy': 100
                | 		}
                | 	}
        """
        log.debug('start processing results for search_results {0}'.format(search_results))
        calcualte_search_results_accuracy_dict = {}
        calcualte_search_results_accuracy_dict['best_match'] = {}
        calcualte_search_results_accuracy_dict['best_match']['accuracy'] = 0
        search_title = search_results['lookup_params']['title']
        # todo: do some test cases for this to verify nothing unintended happens
        for external_source in search_results['lookup_results']:
            calcualte_search_results_accuracy_dict[external_source] = {}
            calcualte_search_results_accuracy_dict[external_source][
                'best_match'] = self._get_best_result_external_source(
                search_results['lookup_results'][external_source],
                external_source,
                search_title,
                search_year,
                episode_dict,
                search_title_list)
            if calcualte_search_results_accuracy_dict[external_source]['best_match']['accuracy'] > \
                calcualte_search_results_accuracy_dict['best_match']['accuracy']:
                calcualte_search_results_accuracy_dict['best_match'] = \
                calcualte_search_results_accuracy_dict[external_source]['best_match']
        return calcualte_search_results_accuracy_dict

    def _get_best_result_external_source(self, external_source_search_result_list, external_source,
                                         search_title, search_year, episode_dict, search_title_list):

        # print(episode_dict)
        best_result_dict = {}
        best_result_dict['accuracy'] = 0
        log.debug('external_source_search_result_list: {0}'.format(
            external_source_search_result_list))
        for external_source_search_result in external_source_search_result_list:
            log.debug('external_source %s, search_title %s,'
                      ' search_year %s, external_source_search_result %s',
                      external_source,
                      search_title,
                      search_year,
                      external_source_search_result)
            #time.sleep(500)
            current_result_dict = {}
            current_result_dict['seasons_match_count'] = 0
            current_result_dict['seasons_mismatch_count'] = 0
            current_result_dict['name_match_accuracy'] = 0
            current_result_dict['name_match_search_title'] = ''
            current_result_dict['name_match_result_title'] = ''
            current_result_dict['eapi_season_list'] = []
            current_result_dict['eapi_season_missing_count'] = 0
            current_result_dict['search_season_list'] = episode_dict['season_list']
            current_result_dict['eapi_eid'] = external_source_search_result['id']
            current_result_dict['accuracy'] = 0
            current_result_dict['eapi'] = external_source

            log.debug('episode_dict %s' % episode_dict)

            result_title_list = self.construct_conformed_title_list(external_source_search_result['title_list'],
                                                                    self.result_title_variation_options)
            log.debug('result_title_list: {0}'.format(result_title_list))
            for result_title in result_title_list:
                for search_title in search_title_list:
                    log.debug('result_title %s, search_title %s', result_title, search_title)
                    if re.match(r"""^(a |the )?{0}$""".format(re.escape(search_title)), result_title, re.I | re.UNICODE):
                        current_result_dict['name_match_accuracy'] = 100
                        current_result_dict['name_match_search_title'] = search_title
                        current_result_dict['name_match_result_title'] = result_title
                    elif re.match(r"""^(a |the )?{0}""".format(re.escape(search_title)), result_title, re.I | re.UNICODE):
                        if current_result_dict['name_match_accuracy'] < 90:
                            current_result_dict['name_match_accuracy'] = 90
                            current_result_dict['name_match_search_title'] = search_title
                            current_result_dict['name_match_result_title'] = result_title
                    elif re.search(r"""(a |the )?{0}""".format(re.escape(search_title)), result_title, re.I | re.UNICODE):
                        if current_result_dict['name_match_accuracy'] < 50:
                            current_result_dict['name_match_accuracy'] = 50
                            current_result_dict['name_match_search_title'] = search_title
                            current_result_dict['name_match_result_title'] = result_title

            # this needs work to properly set a accuraty for seasons existing
            for season in external_source_search_result['seasons']:
                eapi_season_number = int(season['season_number'])
                if eapi_season_number > 0:
                    current_result_dict['eapi_season_list'].append(eapi_season_number)
                    if eapi_season_number in episode_dict['season_list']:
                        if season['episode_count'] >= episode_dict[eapi_season_number]['ep_count']:
                            current_result_dict['seasons_match_count'] += 1
                        elif season['episode_count'] <= episode_dict[eapi_season_number]['ep_count']:
                            current_result_dict['seasons_mismatch_count'] += 1
                        else:
                            current_result_dict['seasons_match_count'] += 1
                    else:
                        current_result_dict['seasons_mismatch_count'] += 1

            if list1_not_in_list2(episode_dict['season_list'], current_result_dict['eapi_season_list']):
                current_result_dict['eapi_season_missing_count'] += 1

            # For when shows with simillar/same name. Try and match against number of seasons in the show
            if len(episode_dict['season_list']) == len(current_result_dict['eapi_season_list']):
                exact_season_count_match = True
            else:
                exact_season_count_match = False
                # if current_result_dict['accuracy'] <= 80:
                # print(current_result_dict)
                # time.sleep(1)
            if current_result_dict['name_match_accuracy'] > 0:
                if current_result_dict['eapi_season_missing_count']:
                    current_result_dict['accuracy'] = current_result_dict['name_match_accuracy'] / 2
                else:
                    current_result_dict['accuracy'] = current_result_dict['name_match_accuracy']

            if current_result_dict['accuracy'] <= 80:
                if len(episode_dict['season_list']) == len(current_result_dict['eapi_season_list']):
                    current_result_dict['accuracy'] += 20

            if 'first_air_year' in external_source_search_result and isinstance(search_year, int):
                if search_year and external_source_search_result['first_air_year']:
                    log.debug('''search_year %s, external_source_search_result['first_air_year'] %s''',
                             search_year, external_source_search_result['first_air_year'])
                    if search_year == external_source_search_result['first_air_year']:
                        if current_result_dict['accuracy'] <= 80:
                            current_result_dict['accuracy'] += 20
                            #print('e')
                    elif search_year - 1 == external_source_search_result['first_air_year']:
                        current_result_dict['accuracy'] += 20
                       # print('m1')
                    elif search_year + 1 == external_source_search_result['first_air_year']:
                        current_result_dict['accuracy'] += 20
                       # print('p1')
                    elif re.search(r'{0}$'.format(search_year), current_result_dict['name_match_result_title'], flags=re.I):
                        # if year dectected is actually part of the tv name not not the year it was released
                        pass
                    else:
                        current_result_dict['accuracy'] = 50
            else:
                log.debug('first_air_year not in external_source_search_result or search_year not an int')

                    # print('eapi_id', current_result_dict['eapi_eid'])
                    # print('search_title', search_title)
                    # print('result_title_list', result_title_list)
                    # print('eapi_season_list', current_result_dict['eapi_season_list'])
                    # print('search_season_list', current_result_dict['search_season_list'])
                    # print('search_year', search_year)
                    # print('eapi_year', external_source_search_result['first_air_year'])
            log.debug('external_source %s, search_title %s,'
                      ' search_year %s, accuracy %s',
                      external_source,
                      search_title,
                      search_year,
                      current_result_dict['accuracy'])
            # print(current_result_dict['accuracy'])
            if current_result_dict['accuracy'] > best_result_dict['accuracy']:
                log.debug('current_result_dict %s is better than best_result_dict %s',
                          current_result_dict, best_result_dict)
                #current_result_dict['accuracy'] = 100
                if exact_season_count_match:
                    return current_result_dict
                else:
                    best_result_dict = current_result_dict
            elif current_result_dict['accuracy'] > best_result_dict['accuracy']:
                best_result_dict = current_result_dict
        return best_result_dict

    def construct_conformed_title_list(self, title_list, variations):
        return_list = []
        for title in title_list:
            if title not in return_list:
                return_list.append(title)
            for variation in variations:
                conformed_title = conform_title(title, variation)
                if conformed_title not in return_list:
                    return_list.append(conformed_title)
        return return_list
