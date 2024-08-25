# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import itertools
import json
import logging
import re
import sys
import time
from datetime import datetime
from datetime import timedelta

from sqlalchemy import func, orm

import zerrphix.constants
from zerrphix.db import flush, commit
from zerrphix.db.tables import TABLES
from zerrphix.film.util import update_film_last_mod
from zerrphix.plugin import load_plugins
from zerrphix.util.numbers import seconds_to_hours
from zerrphix.util.plugin import create_eapi_plugins_list, create_eapi_dict
from zerrphix.util.text import conform_title, sanitise_film_filename, date_time
#from zerrphix.util import set_retry, check_can_retry
#from types import MethodType
from zerrphix.film.base import FilmBase

## regex info http://stackoverflow.com/questions/2824302/how-to-make-regular-expression-into-non-greedy
log = logging.getLogger(__name__)


# TODO: eapi get alternative titles in search
class Identify(FilmBase):
    """Identify films against eapi's (e.g. tmdb, imdb)
    """

    def __init__(self, **kwargs):
        super(Identify, self).__init__(**kwargs)
        """Identify __init__

            Args:
                | args (list): Passed through args from the command line.
                | Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.

            Attributes:
                | args (list): Passed through args from the command line.
                | Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.
                | eapi_dict (dict): See zerrphix.util.plugin.create_eapi_dict
                | result_title_variation_sub_options (list): text manipulation \
                functions used with result_title_variation_master_options for \
                eapi results to try and get the best match against search title
                | result_title_variation_master_options (list): text manipulation \
                functions for eapi results to try and get the best match \
                against search title
                | search_title_variation_options (list): text manipulation \
                functions to try and get the best match against eapi \
                result title
        """
        session = self.Session()
        self, self.eapi_plugins_access_list, loaded_plugins = create_eapi_plugins_list('film', sys.modules,
                                                                                       load_plugins(self.args), self)
        if not self.eapi_plugins_access_list:
            raise Exception('There not any entries in eapi_plugins_access_list therefore scanning is pointless')
        self.eapi_dict = create_eapi_dict(session)
        self.result_title_variation_sub_options = ['replace_invalid_words_with_spaces',
                                                   'replace_int_with_roman_numerals',
                                                   'replace_roman_numerals_with_int',
                                                   'replace_roman_numerals_with_space',
                                                   'replace_int_with_space',
                                                   'non_word_chars_to_spaces']

        self.result_title_variation_master_options = ['replace_optional_words_with_spaces',
                                                      'replace_symbols_with_words',
                                                      'accent_to_asscii',
                                                      'remove_non_alnum_near_alnum',
                                                      'non_alnum_to_spaces']

        self.search_title_variation_master_options = ['replace_optional_words_with_spaces',
                                                      'accent_to_asscii']

        self.search_title_variation_sub_options = ['replace_roman_numerals_with_space',
                                                   'replace_int_with_space',
                                                   'remove_underscore',
                                                   'remove_spaces_between_uppercase_letters',
                                                   'remove_spaces',
                                                   'replace_space_with_dot']

        # self.search_title_variation_options = ['replace_roman_numerals_with_space',
        #									'replace_int_with_space',
        #									'accent_to_asscii',
        #									'replace_optional_words_with_spaces',
        #									'remove_underscore',
        #									'remove_spaces_between_uppercase_letters',
        #									'remove_spaces',
        #									'replace_space_with_dot']

        # self.result_title_variation_master_options

        release_pattern_name_list = ['pattern_video_source',
                                     'pattern_video_tags',
                                     'pattern_video_s3d',
                                     'pattern_video_repack',
                                     'pattern_subtitle_tags',
                                     'pattern_video_format',
                                     'pattern_unkown']
        self.release_patterns_combined = '(?:'
        for pattern in release_pattern_name_list:
            self.release_patterns_combined += '{0}|'.format(getattr(zerrphix.constants, pattern))
        self.release_patterns_combined = self.release_patterns_combined.rstrip('|')
        self.release_patterns_combined += ')'
        self.filenameroot_title_regex_dict = {
            'title_year_a': r"""(?P<title>[\w\d'`\-\s]+?)[^\w\d'`\-\s]?\b(?:[1-2][0-9]{3})\b[\w\d'`\-\s]\b(?P<year>[1-2][0-9]{3})\b""",
            'title_year_b': r"""(?P<title>[\w\d'`\-\s]+?)[^\w\d'`\-\s]?\b(?P<year>[1-2][0-9]{3})\b""",
            'title_only_a': r"""(?P<title>[\w\d'`\-\s]+?){0}""".format(self.release_patterns_combined),
            'title_only_b': r"""(?P<title>[\w\d'`\-\s]+)"""
        }
        session.close()
        self.library = 'film'
        #self.set_retry = MethodType(set_retry, self)
        #self.check_can_retry = MethodType(check_can_retry, self)

    def idenfity(self):
        """Initiate the identififcation process.
        """
        log.warning(date_time())
        processing_complete = False
        session = self.Session()
        max_ZP_FILM_FILEFOLDER_ID = session.query(func.max(TABLES.ZP_FILM_FILEFOLDER.ID)).one()[0]
        session.close()
        if isinstance(max_ZP_FILM_FILEFOLDER_ID, int):
            ZP_FILM_FILEFOLDER_ID = max_ZP_FILM_FILEFOLDER_ID + 1
            while processing_complete == False:
                session = self.Session()
                qry_unidentified_filefolder = session.query(
                    TABLES.ZP_FILM_FILEFOLDER).filter(
                    TABLES.ZP_FILM_FILEFOLDER.ID < ZP_FILM_FILEFOLDER_ID,
                    TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == None,
                    ~TABLES.ZP_FILM_FILEFOLDER.ID.in_(session.query(
                        TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                        TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 1
                    ))
                )
                # for unidenttified_filefolder in _yield_limit(qry_unidentified_filefolder, TABLES.ZP_FILM_FILEFOLDER.ID, maxrq=100, order='desc'):
                ZP_FILM_FILEFOLDER = qry_unidentified_filefolder.order_by(TABLES.ZP_FILM_FILEFOLDER.ID.desc()).first()
                if ZP_FILM_FILEFOLDER is not None:
                    session.close()
                    ZP_FILM_FILEFOLDER_ID = ZP_FILM_FILEFOLDER.ID
                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                 4,
                                                                 'Identifying: Film %s/%s' %
                                                                 (ZP_FILM_FILEFOLDER_ID, max_ZP_FILM_FILEFOLDER_ID))
                    ZP_FILM_FILEFOLDER_TITLE_LIST = ZP_FILM_FILEFOLDER.TITLE_LIST
                    filename_root_list = json.loads(
                        ZP_FILM_FILEFOLDER_TITLE_LIST.decode('base64_codec').decode('zlib_codec').decode('utf-8'))
                    self._identify_filefolder(filename_root_list, ZP_FILM_FILEFOLDER_ID)
                else:
                    # if there are no more resutls stop processing
                    session.close()
                    processing_complete = True
            if self.check_can_retry(1) is True:
                log.debug('Retrying FIlm Identify')
                processing_complete = False
                ZP_FILM_FILEFOLDER_ID = max_ZP_FILM_FILEFOLDER_ID + 1
                while processing_complete == False:
                    session = self.Session()
                    qry_unidentified_filefolder_retry = session.query(
                        TABLES.ZP_FILM_FILEFOLDER.ID, TABLES.ZP_FILM_FILEFOLDER.TITLE_LIST, TABLES.ZP_RETRY_COUNT.DELAY,
                        TABLES.ZP_RETRY.DATETIME, TABLES.ZP_RETRY.COUNT).filter(
                        TABLES.ZP_FILM_FILEFOLDER.ID < ZP_FILM_FILEFOLDER_ID,
                        TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == TABLES.ZP_RETRY_COUNT.ZP_RETRY_TYPE_ID,
                        TABLES.ZP_FILM_FILEFOLDER.ID == TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID,
                        TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 1,
                        TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == 1,
                        TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == None,
                        TABLES.ZP_RETRY_COUNT.COUNT == session.query(
                            func.max(TABLES.ZP_RETRY_COUNT.COUNT)
                        ).filter(
                            TABLES.ZP_RETRY.COUNT >= TABLES.ZP_RETRY_COUNT.COUNT).order_by(
                            TABLES.ZP_RETRY_COUNT.COUNT.desc()).correlate(TABLES.ZP_RETRY).as_scalar()
                    )
                    """
                    select *
                    from ZP_RETRY, ZP_RETRY_COUNT
                    where ZP_RETRY.ZP_RETRY_TYPE_ID = ZP_RETRY_COUNT.ZP_RETRY_TYPE_ID
                    and ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID = 1
                    and ZP_RETRY.ZP_RETRY_TYPE_ID = 1
                    and ZP_RETRY_COUNT.COUNT = (select max(ZP_RETRY_COUNT.COUNT)
                    from ZP_RETRY_COUNT
                    where ZP_RETRY_COUNT.ZP_RETRY_TYPE_ID
                    and ZP_RETRY.COUNT >= ZP_RETRY_COUNT.COUNT
                    order by ZP_RETRY_COUNT.COUNT desc)
                    """
                    # for unidenttified_filefolder in _yield_limit(qry_unidentified_filefolder, TABLES.ZP_FILM_FILEFOLDER.ID, maxrq=100, order='desc'):
                    qry_unidentified_filefolder_retry_count = qry_unidentified_filefolder_retry.count()
                    if qry_unidentified_filefolder_retry_count > 0:
                        filfolders = qry_unidentified_filefolder_retry.order_by(
                            TABLES.ZP_FILM_FILEFOLDER.ID.desc()).limit(100)
                        session.close()
                        result_dict = {}
                        for filfolder in filfolders:
                            result_dict[filfolder.ID] = {}
                            result_dict[filfolder.ID]['datetime'] = filfolder.DATETIME
                            result_dict[filfolder.ID]['count'] = filfolder.COUNT
                            result_dict[filfolder.ID]['delay'] = filfolder.DELAY
                            result_dict[filfolder.ID][
                                'title_list'] = filfolder.TITLE_LIST
                        for _ID in reversed(sorted(result_dict)):
                            ZP_FILM_FILEFOLDER_ID = _ID
                            self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                         4,
                                                                         'Retry Identifying: Film %s/%s' %
                                                                    (ZP_FILM_FILEFOLDER_ID, max_ZP_FILM_FILEFOLDER_ID))
                            log.warning('ZP_FILM_FILEFOLDER_ID %s, datetime %s, count %s, delay %s', ZP_FILM_FILEFOLDER_ID,
                                        result_dict[ZP_FILM_FILEFOLDER_ID]['datetime'],
                                        result_dict[ZP_FILM_FILEFOLDER_ID]['count'],
                                        result_dict[ZP_FILM_FILEFOLDER_ID]['delay'])
                            if result_dict[ZP_FILM_FILEFOLDER_ID]['datetime'] + timedelta(
                                days=result_dict[ZP_FILM_FILEFOLDER_ID]['delay']) <= datetime.now():
                                log.warning('dt %s, plus %s is %s which is than than now %s',
                                            result_dict[ZP_FILM_FILEFOLDER_ID]['datetime'],
                                            result_dict[ZP_FILM_FILEFOLDER_ID]['delay'],
                                            result_dict[ZP_FILM_FILEFOLDER_ID]['datetime'] + timedelta(
                                                days=result_dict[ZP_FILM_FILEFOLDER_ID]['delay']), datetime.now())
                                filename_root_list = json.loads(
                                    result_dict[ZP_FILM_FILEFOLDER_ID]['title_list'].decode('base64_codec').decode(
                                        'zlib_codec').decode('utf-8'))
                                self._identify_filefolder(filename_root_list, ZP_FILM_FILEFOLDER_ID)
                            else:
                                log.warning('dt %s, plus %s is %s which is not less than now %s',
                                            result_dict[ZP_FILM_FILEFOLDER_ID]['datetime'],
                                            result_dict[ZP_FILM_FILEFOLDER_ID]['delay'],
                                            result_dict[ZP_FILM_FILEFOLDER_ID]['datetime'] + timedelta(
                                                days=result_dict[ZP_FILM_FILEFOLDER_ID]['delay']), datetime.now())
                                # raise SystemExit
                    else:
                        session.close()
                        processing_complete = True

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
        eids_to_find = list(set(self.eapi_dict.keys()) - set(eapi_dict.keys()))
        log.debug('eids_to_find: {0} are not in self.eapi_dict: {1}'.format(eids_to_find, self.eapi_dict))
        for eapi in self.eapi_plugins_access_list:
            if hasattr(getattr(self, eapi), 'available_eid'):
                for have_eapi in eapi_dict.keys():
                    for want_eapi in eids_to_find:
                        if getattr(self, eapi).available_eid(have_eapi, want_eapi, self.library) == True:
                            log.debug('eapi: {0} can get want_eapi: {1} using have_eapi: {2}'.format(
                                eapi,
                                want_eapi,
                                have_eapi))
                            want_eapi_eid = getattr(self, eapi).get_eapi_eid(have_eapi, eapi_dict[have_eapi],
                                                                             want_eapi, self.library)
                            if want_eapi is not None:
                                eapi_dict[want_eapi] = want_eapi_eid
            else:
                log.debug('self.{0} does not have attribute available_eid'.format(
                    eapi))
        return eapi_dict

    def add_film_to_db(self, ZP_FILM_FILEFOLDER_ID, eapi_dict):
        """Add film to the database

            Note: A check is done to see if the film allready
            exists in the db (via eapi_eid). If so the the SCORE
            of the currently processing filefolder that is
            assocated is higher than the currently assocaited
            one then the film filefolder then the currently
            processing filefolder is assocaited with the film

            Args:
                ZP_FILM_FILEFOLDER_ID (int): the identified eapi_eid
        """
        session = self.Session()
        ZP_FILM_ID = None
        if not eapi_dict:
            raise Exception('eapi_dict: {0} is empty for ZP_FILM_FILEFOLDER_ID'.format(eapi_dict,
                                                                                       ZP_FILM_FILEFOLDER_ID))
        for eapi in eapi_dict:
            try:
                ZP_FILM_ID = session.query(TABLES.ZP_FILM_EAPI_EID).filter(
                    TABLES.ZP_FILM_EAPI_EID.ZP_EAPI_EID == eapi_dict[eapi],
                    TABLES.ZP_FILM_EAPI_EID.ZP_EAPI_ID == self.eapi_dict[eapi]).one().ZP_FILM_ID
            except orm.exc.NoResultFound:
                pass

        if not ZP_FILM_ID:
            ADDED_DATE_TIME = date_time()
            add_film = TABLES.ZP_FILM(ADDED_DATE_TIME=ADDED_DATE_TIME,
                                      ZP_FILM_FILEFOLDER_ID=ZP_FILM_FILEFOLDER_ID,
                                      LAST_EDIT_DATETIME=ADDED_DATE_TIME)
            session.add(add_film)
            log.debug(('Inserted ADDED_DATE_TIME: {0},'
                       ' ZP_FILM_FILEFOLDER_ID:{1}, LAST_EDIT_DATETIME: {0} into ZP_FILM').format(
                ADDED_DATE_TIME,
                ZP_FILM_FILEFOLDER_ID))
            flush(session)
            ZP_FILM_ID = add_film.ID
            film_filfolder = session.query(TABLES.ZP_FILM_FILEFOLDER).filter(
                TABLES.ZP_FILM_FILEFOLDER.ID == ZP_FILM_FILEFOLDER_ID).one()
            film_filfolder.ZP_FILM_ID = ZP_FILM_ID
            eapi_dict = self.get_eapi_list(eapi_dict)
            log.debug('eapi_dict: {0}'.format(eapi_dict))
            for eapi in eapi_dict:
                log.debug('eapi: {0}, eapi_eid, {1}'.format(eapi, eapi_dict[eapi]))
                if eapi_dict[eapi]:
                    add_film_eapi_eid = TABLES.ZP_FILM_EAPI_EID(ZP_FILM_ID=ZP_FILM_ID,
                                                                ZP_EAPI_EID=eapi_dict[eapi],
                                                                ZP_EAPI_ID=self.eapi_dict[eapi])
                    log.debug(('Inserted ZP_FILM_ID {0}, ZP_EAPI_EID: {1}, ZP_EAPI_ID: {2} into ZP_FILM_EAPI').format(
                        ZP_FILM_ID,
                        eapi_dict[eapi],
                        self.eapi_dict[eapi]))
                    session.add(add_film_eapi_eid)
                else:
                    log.debug('not adding eapi: {0}, eapi_eid, {1} to ZP_FILM_EAPI_EID'.format(eapi, eapi_dict[eapi]))
        else:
            film_filfolder = session.query(TABLES.ZP_FILM_FILEFOLDER).filter(
                TABLES.ZP_FILM_FILEFOLDER.ID == ZP_FILM_FILEFOLDER_ID).one()
            film_filfolder.ZP_FILM_ID = ZP_FILM_ID
            assocaited_film_query = session.query(TABLES.ZP_FILM).filter(
                TABLES.ZP_FILM.ID == ZP_FILM_ID)
            try:
                assocaited_film_filmfolder_id_score = session.query(TABLES.ZP_FILM_FILEFOLDER_SCORE).filter(
                TABLES.ZP_FILM_FILEFOLDER_SCORE.ZP_FILM_FILEFOLDER_ID == assocaited_film_query.one().ZP_FILM_FILEFOLDER_ID).one().SCORE
                detecting_film_filmfolder_id_score = session.query(TABLES.ZP_FILM_FILEFOLDER_SCORE).filter(
                TABLES.ZP_FILM_FILEFOLDER_SCORE.ZP_FILM_FILEFOLDER_ID == ZP_FILM_FILEFOLDER_ID).one().SCORE
            except orm.exc.NoResultFound:
                log.warning('no results found for assocaited_film_filmfolder_id_score and or '
                            'detecting_film_filmfolder_id_score cannot determine if this film is better than the'
                            ' current filefolder associated with this film')
            else:
                if detecting_film_filmfolder_id_score > assocaited_film_filmfolder_id_score:
                    assocaited_film_query.update({"ZP_FILM_FILEFOLDER_ID": ZP_FILM_FILEFOLDER_ID})
                    commit(session)
                    update_film_last_mod(self.Session, ZP_FILM_ID)

        # For when filefolder has been incorrectly identified before and now a new film has been found for the
        # filefolder we need to remove assocaiton from the other film(s)
        session.query(TABLES.ZP_FILM).filter(
            TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == ZP_FILM_FILEFOLDER_ID,
            TABLES.ZP_FILM.ID != ZP_FILM_ID).delete()
        commit(session)
        session.close()

    def _identify_filefolder(self, filename_root_list, ZP_FILM_FILEFOLDER_ID):
        """Start filefolder identififcation process

             Args:
                | filename_root_list: list of filenames/folders one of which \
                hopefully contains the film title and year
                | ZP_FILM_FILEFOLDER_ID: ID of the file/folder
        """
        title_year_list = self._extract_title_year(filename_root_list)
        log.debug('title_year_list: {0} for filename_root_list: {1}'.format(
            title_year_list,
            filename_root_list))
        if title_year_list:
            processed_search_results = self._process_search_results(title_year_list)
            log.debug('processed_search_results: {0}'.format(processed_search_results))
            if processed_search_results['best_match']['accuracy'] == 0:
                log.warning(
                    ('''processed_search_results['best_match']['accuracy'] {0} == 0 for filename_root_list: {1}'''
                     ''' - ZP_FILM_FILEFOLDER_ID {2}''').format(
                        processed_search_results['best_match']['accuracy'],
                        filename_root_list,
                        ZP_FILM_FILEFOLDER_ID))
                self.set_retry(1, 1, ZP_FILM_FILEFOLDER_ID)
            else:
                self.add_film_to_db(ZP_FILM_FILEFOLDER_ID,
                                    {processed_search_results['best_match']['eapi']:
                                         processed_search_results['best_match']['id']}
                                    )
        else:
            log.warning(('title_year_list: {0} empty for filename_root: {1}'
                         ' for ZP_FILM_FILEFOLDER_ID: {2}').format(
                title_year_list,
                filename_root_list,
                ZP_FILM_FILEFOLDER_ID))

    def _process_search_results(self, title_year_list):
        """Process seach results

            Args:
                | title_year_list: list of processed
                | list of filenames/folders

            Returns:
                | dict: If no results found
                | {'best_match': {'accuracy': 0}}
                | if result(s) found:
                |	{u'tmdb':
                |		{u'best_match':
                |			{u'title_list': [u'Some Film Name'],
                |			u'year': 0000,
                |			u'id': 0,
                |			u'timings': {},
                |			u'accuracy': 100}
                |		},
                |	u'best_match':
                |		{u'title_list': [u'Some Film Name'],
                |		u'year': 0000,
                |		u'id': 0,
                |		u'timings': {},
                |		u'accuracy': 100}
                |	}
        """
        # Setup return dict incase not results are found
        best_processed_search_results = {'best_match': {'accuracy': 0}}
        # for each title_year
        for title_year in title_year_list:
            title = title_year['title']
            year = title_year['year']
            search_title_list = [title]
            # create some variations to help with getting a accurate result. see self.search_title_variation_options
            # for options used
            # search_title_variation_list = self.construct_title_variation_list(title, self.search_title_variation_options)
            search_title_variation_list = self.construct_title_variation_list(title,
                                                                              self.search_title_variation_master_options,
                                                                              self.search_title_variation_sub_options)
            log.debug('search_title_variation_list: {0} for title {1}'.format(
                search_title_variation_list,
                title))
            for title_variation in search_title_variation_list:
                if title_variation not in search_title_list:
                    log.debug(('title_variation: {0} not in search_title_list: {0} '
                               'therefore adding title_variation to search_title_list').format(
                        title_variation,
                        search_title_list))
                    search_title_list.append(title_variation)
                else:
                    log.debug(('title_variation: {0} not in search_title_list: {0} '
                               'therefore adding title_variation to search_title_list').format(
                        title_variation,
                        search_title_list))
            log.debug(('search_title_list: {0} for title: {1}').format(
                search_title_list,
                title))
            for title in search_title_list:
                log.debug(('using title: {0} searching').format(title))
                processed_search_results = self._get_search_results_accuracy(self._external_source_search(title, year))
                if processed_search_results['best_match']['accuracy'] == 100:
                    return processed_search_results
                elif processed_search_results['best_match']['accuracy'] > best_processed_search_results['best_match'][
                    'accuracy']:
                    best_processed_search_results = processed_search_results
        return best_processed_search_results

    def _external_source_search(self, title, year):
        """Search external sources (e.g tmdb)

            Args:
                | title (string): film title
                | year (int): film year

            Returns:
                | dict:
                | If no results found
                | 	{u'lookup_params':
                | 		{u'year': 0000,
                | 		u'title': u'Some Film'},
                | 	}
                | if result(s) found:
                | 	{u'lookup_params':
                | 		{u'year': 0000,
                | 		u'title': u'Some Film'},
                | 	u'lookup_results':
                | 		{u'tmdb':
                | 			[{u'title_list': [u'Some Film'], u'id': 0, u'year': 0000}]}
                | 	}
        """
        results_dict = {}
        results_dict['lookup_params'] = {}
        results_dict['lookup_params']['title'] = title
        results_dict['lookup_params']['year'] = year
        results_dict['lookup_results'] = {}
        # for external_source in self.external_sources:
        for external_source in self.eapi_plugins_access_list:
            log.debug('current external_source: {0} for title {1} and year {2}'.format(external_source, title, year))
            external_source_time_begin = time.time()
            log.debug('use external_source: {0} for title {1} and year {2}'.format(external_source, title, year))
            search_results = getattr(self, external_source).find_film(title, year)
            external_source_time_end = time.time()
            log.debug('Total time for for external_source {0} and title {1} and year {2} took: {3}'.format(
                external_source,
                title,
                year,
                seconds_to_hours(external_source_time_end - external_source_time_begin)))
            log.debug(
                'adding search_results: {0} to results_dict {1} for external_source {2} and title {3} and year {4}'.format(
                    search_results, results_dict, external_source, title, year))
            results_dict['lookup_results'][external_source] = search_results
            log.debug('results_dict: {0}'.format(results_dict))
        return results_dict

    def _get_search_results_accuracy(self, search_results):
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
        search_year = search_results['lookup_params']['year']
        # todo: do some test cases for this to verify nothing unintended happens
        for external_source in search_results['lookup_results']:
            calcualte_search_results_accuracy_dict[external_source] = {}
            calcualte_search_results_accuracy_dict[external_source][
                'best_match'] = self._get_best_result_external_source(
                search_results['lookup_results'][external_source],
                external_source,
                search_title,
                search_year)
            if calcualte_search_results_accuracy_dict[external_source]['best_match']['accuracy'] > \
                calcualte_search_results_accuracy_dict['best_match']['accuracy']:
                calcualte_search_results_accuracy_dict['best_match'] = \
                    calcualte_search_results_accuracy_dict[external_source]['best_match']
        return calcualte_search_results_accuracy_dict

    def _get_best_result_external_source(self, external_source_search_result_list, external_source,
                                         search_title, search_year):
        """For each result in external source find the best one
        
            Args:
                | external_source_search_result_list : list
                | external_source : basestring
                | search_title : basestring
                | search_year : int

            Returns:
                | dict:
                | If no results over 0 accuracy
                | 	{u'accuracy': 0}}
                | if result(s) found:
                | 	{u'title_list': [u'Some Film'],
                | 	u'year': 0000,
                | 	u'id': 0,
                | 	u'timings': {},
                | 	u'accuracy': 100}
        """
        best_result_dict = {}
        best_result_dict['accuracy'] = 0
        best_result_dict['timings'] = {}
        log.debug('external_source_search_result_list: {0}'.format(
            external_source_search_result_list))
        for external_source_result in external_source_search_result_list:
            log.debug('external_source_result: {0}'.format(external_source_result))
            result_dect_accuracy = 0
            external_source_result_title_list = []
            log.debug("""external_source_result['title_list']: {0}""".format(
                external_source_result['title_list']))
            for result_title in external_source_result['title_list']:
                external_source_result_title_variation_list_time_begin = time.time()
                external_source_result_title_variation_list = self.construct_title_variation_list(result_title,
                                                                                                  self.result_title_variation_master_options,
                                                                                                  self.result_title_variation_sub_options)

                external_source_result_title_variation_list_time_end = time.time()
                external_source_result_title_variation_list_duration = seconds_to_hours(
                    external_source_result_title_variation_list_time_end - external_source_result_title_variation_list_time_begin)
                log.debug('external_source_result_title_variation_list: {0} for result_title: {1} took: {2}'.format(
                    external_source_result_title_variation_list,
                    result_title,
                    external_source_result_title_variation_list_duration))
                for title_variation in external_source_result_title_variation_list:
                    if title_variation not in external_source_result_title_list:
                        log.debug(('title_variation: {0} not in external_source_result_title_list: {0} '
                                   'therefore adding title_variation to external_source_result_title_list').format(
                            title_variation,
                            external_source_result_title_list))
                        external_source_result_title_list.append(title_variation)
                    else:
                        log.debug(('title_variation: {0} not in external_source_result_title_list: {0} '
                                   'therefore adding title_variation to external_source_result_title_list').format(
                            title_variation,
                            external_source_result_title_list))
            log.debug('external_source_result_title_list: {0}'.format(external_source_result_title_list))
            external_source_result_id = external_source_result['id']
            external_source_result_year = external_source_result['year']

            search_title_variation_list = [search_title]
            for variation_type in ['non_alnum_to_spaces']:
                search_title_conformed = conform_title(search_title, variation_type)
                if search_title_conformed not in search_title_variation_list:
                    search_title_variation_list.append(search_title_conformed)
            log.debug('search_title_variation_list: {0}'.format(search_title_conformed))
            for search_title_variation in search_title_variation_list:
                # to relpace some of this with title as regex pattern and convert non aplpha into "\.?" ??
                regex_exact_title_match = re.compile(r"""^(a |the )?{0}$""".format(search_title_variation),
                                                     re.I | re.UNICODE)
                regex_match_from_title_start = re.compile(r"""^(a |the )?{0}""".format(search_title_variation),
                                                          re.I | re.UNICODE)
                regex_title_match_within = re.compile(r"""(a |the )?{0}""".format(search_title_variation),
                                                      re.I | re.UNICODE)
                if external_source_result['year'] >= 1800 and search_year >= 1800:
                    match_year = True
                else:
                    match_year = False
                if [m for l in external_source_result_title_list for m in [regex_exact_title_match.match(l)] if m]:
                    if match_year == True:
                        if search_year == external_source_result_year:
                            result_dect_accuracy = 100
                        elif (external_source_result_year - 1) <= search_year <= (external_source_result_year + 1):
                            result_dect_accuracy = 94
                        elif (external_source_result_year - 2) <= search_year <= (external_source_result_year + 2):
                            result_dect_accuracy = 92
                        else:
                            result_dect_accuracy = 61
                    else:
                        result_dect_accuracy = 60
                elif [m for l in external_source_result_title_list for m in [regex_match_from_title_start.match(l)] if
                      m]:
                    if match_year == True:
                        if search_year == external_source_result_year:
                            result_dect_accuracy = 89
                        elif (external_source_result_year - 1) <= search_year <= (external_source_result_year + 1):
                            result_dect_accuracy = 88
                        else:
                            result_dect_accuracy = 51
                    else:
                        result_dect_accuracy = 40
                        # do search other way around as well i.e. search result external_source_result_title_list within query search_title
                elif [m for l in external_source_result_title_list for m in
                      [re.search("{0}".format(re.escape(l)), search_title_variation, re.I | re.UNICODE)] if m]:
                    if match_year == True:
                        if search_year == external_source_result_year:
                            result_dect_accuracy = 79
                        elif (external_source_result_year - 1) <= search_year <= (external_source_result_year + 1):
                            result_dect_accuracy = 78
                        else:
                            result_dect_accuracy = 41
                    else:
                        result_dect_accuracy = 40
                elif [m for l in external_source_result_title_list for m in [regex_title_match_within.search(l)] if m]:
                    if match_year == True:
                        if search_year == external_source_result_year:
                            result_dect_accuracy = 73
                        elif (external_source_result_year - 1) <= search_year <= (external_source_result_year + 1):
                            result_dect_accuracy = 72
                        else:
                            result_dect_accuracy = 31
                    else:
                        result_dect_accuracy = 30
                elif match_year == True:
                    if len(external_source_search_result_list) == 1:
                        if search_year == external_source_result_year:
                            result_dect_accuracy = 85
                        elif (external_source_result_year - 1) <= search_year <= (external_source_result_year + 1):
                            result_dect_accuracy = 80
                elif len(external_source_search_result_list) == 1:
                    result_dect_accuracy = 70
                log.debug(('result_dect_accuracy: {0} for external_source: {1} and external_source_result: {2}'
                           ' and external_source_result_title_list: {3} and search_title_variation {4} and search_year {5}').format(
                    result_dect_accuracy,
                    external_source,
                    external_source_result,
                    external_source_result_title_list,
                    search_title_variation,
                    search_year))
                if result_dect_accuracy > 0:
                    log.debug(('result_dect_accuracy: {0} > 0 for external_source: {1} and external_source_result: {2}'
                               ' and external_source_result_title_list: {3} and search_title_variation {4} and search_year {5}').format(
                        result_dect_accuracy,
                        external_source,
                        external_source_result,
                        external_source_result_title_list,
                        search_title_variation,
                        search_year))
                    if result_dect_accuracy > best_result_dict['accuracy']:
                        best_result_dict['accuracy'] = result_dect_accuracy
                        best_result_dict['id'] = external_source_result_id
                        best_result_dict['title_list'] = external_source_result_title_list
                        best_result_dict['year'] = external_source_result_year
                        best_result_dict['eapi'] = external_source
                        if result_dect_accuracy == 100:
                            return best_result_dict
        return best_result_dict

    def _process_title_variation_options_permutations(self, title, options_list, title_variation_list):
        """Create title variations list

            Args:
                | title (basestring): film titile
                | options_list (list): film title variations options
                | title_variation_list (list): film title variations

            Returns:
                list: film title variations
        """
        log.debug('title: {0}, options_list: {1}, title_variation_list: {2}'.format(
            title,
            options_list,
            title_variation_list))
        title_variation_options_permutations_lists = itertools.permutations(options_list)
        if title not in title_variation_list:
            log.debug('title: {0} not in title_variation_list: {1} '.format(
                title,
                title_variation_list))
            title_variation_list.append(title)
        for title_variation_options_permutations_list in title_variation_options_permutations_lists:
            title_variation = title
            variation_optoins_processed = []
            for title_variation_option in title_variation_options_permutations_list:
                variation_optoins_processed.append(title_variation_option)
                pre_conform_title = title_variation
                title_variation = conform_title(title_variation, title_variation_option)
                # log.debug('title_variation: {0} for title_variation_option: {1} pre_conform_title: {2}'.format(
                #																			title_variation,
                #																			title_variation_option,
                #																			pre_conform_title))
                if title_variation not in title_variation_list and title_variation and title_variation != title:
                    log.debug(('title_variation: {0} not in title_variation_list: {1} with'
                               ' variation_optoins_processed: {2} for title: {3} using:'
                               ' title_variation_option: {4}').format(
                        title_variation,
                        title_variation_list,
                        variation_optoins_processed,
                        pre_conform_title,
                        title_variation_option))
                    title_variation_list.append(title_variation)
        return title_variation_list

    def construct_title_variation_list(self, title, master_option_list, sub_option_list=False):
        """Kick off construct title variation list process

            Args:
                | title (basestring): film title
                | master_option_list (list): title variation options
                | sub_option_list (list) (optional): title variation options

            Returns:
                | list:
                | film title variations
        """
        log.debug('title: {0}, master_option_list: {1}, sub_option_list: {2}'.format(
            title,
            master_option_list,
            sub_option_list))
        title_variation_list = []
        log.debug('Appended title: {0} to title_variation_list: {1}'.format(
            title,
            title_variation_list))
        title_variation_list.append(title)
        if sub_option_list == False:
            log.debug('sub_option_list: {0} == False'.format(sub_option_list))
            return self._process_title_variation_options_permutations(title, master_option_list, title_variation_list)
        else:
            log.debug('sub_option_list: {0} != False'.format(sub_option_list))
            for master_option in master_option_list:
                log.debug('master_option: {0}'.format(master_option))
                title_variation_list = self._process_title_variation_options_permutations(
                    conform_title(title, master_option), sub_option_list, title_variation_list)

        return title_variation_list

    def _detect_title_year(self, filename_root, regex):
        """Detect the film title and year from filename_root
        
            Args:
                | filename_root (basestring): the file/folder name
                | regex (list): key(s) in self.filenameroot_title_regex_dict
        
            Returns
                | basestring: is regex match
                | false: if no regex match
        """
        title = False
        year = False
        regex_search = re.search(self.filenameroot_title_regex_dict[regex], filename_root, re.I | re.U)
        if regex_search:
            groupdict = regex_search.groupdict()
            log.debug('regex_search on {0} with {1} resulted in {2}'.format(
                filename_root,
                self.filenameroot_title_regex_dict[regex],
                groupdict))
            if 'title' in groupdict:
                title = groupdict['title']
            if 'year' in groupdict:
                year = int(groupdict['year'])
        log.debug('regex_search on {0} with {1} has not results'.format(
            filename_root,
            self.filenameroot_title_regex_dict[regex]))

        return title, year

    def _extract_title_year(self, filename_root_list):
        """Extract title and year from filename_root_list
        
            Args:
                filename_root_list : List
            
            Returns:
                list: title_year_list
        """
        title_year_list = []
        for filename_root in filename_root_list:
            filename_root_pruned = sanitise_film_filename(filename_root)
            for title_year_regex in ['title_year_a', 'title_year_b']:
                title, year = self._detect_title_year(filename_root_pruned, title_year_regex)
                log.debug('title: {0}, year: {1} from filename_root: {2} using {3}'.format(
                    title,
                    year,
                    filename_root,
                    title_year_regex))
                if title != False and year != False:
                    log.debug(
                        'returning title: {0}, year: {1} for filename_root: {2} from filename_root_list: {3}'.format(
                            title,
                            year,
                            filename_root,
                            filename_root_list))
                    return [{'title': title.strip(), 'year': year}]

            if title == False:
                log.debug('title: {0} is False from filename_root: {2} using title_year_a'.format(
                    title,
                    year,
                    filename_root))
                title_only_regex_list = ['title_only_a', 'title_only_b']
                for title_only_regex in title_only_regex_list:
                    title, year = self._detect_title_year(filename_root_pruned, title_only_regex)
                    log.debug('title: {0}, year: {1} from filename_root: {2} using {3}'.format(
                        title,
                        year,
                        filename_root,
                        title_only_regex))
                    if title != False:
                        title_year_list.append({'title': title.strip(), 'year': year})
                        # Why did i put break here
                        break
        log.debug('title_year_list: {0} for filename_root_list: {1}'.format(
            title_year_list,
            filename_root_list))
        return title_year_list
