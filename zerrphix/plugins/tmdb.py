# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import cgi
import logging
from datetime import datetime

import requests
import tmdbsimple as tmdb
from six import string_types
from zerrphix.util.text import mk_int
from zerrphix.util import rate_limited

log = logging.getLogger(__name__)

_version_ = "0.1"
_libraries_ = ['film', 'tv']
_types_ = {'eapi':
               {'film':
                    {'class': 'TMDB'},
                'film_collection':
                    {'class': 'TMDB'},
                'tv':
                    {'class': 'TMDB'}
                }
           }
_available_eids_ = {'film': [{'want': 'imdb', 'have': 'tmdb'},
                             {'want': 'tmdb', 'have': 'imdb'}],
                    'tv': [{'want': 'imdb', 'have': 'tmdb'}]}
_eapi_name_ = "tmdb"
tmdb_base_image_url = "https://image.tmdb.org/t/p/original/"

# https://developers.themoviedb.org/3
def available_eid(have_eapi, want_eapi, library):
    for available_eid in _available_eids_[library]:
        if available_eid['want'] == want_eapi and available_eid['have'] == have_eapi:
            log.debug('available_eid: {0} have_eapi: {1} want_eapi: {2}'.format(
                available_eid,
                have_eapi,
                want_eapi))
            return True
    return False


class TMDB(object):
    def __init__(self, API_KEY='358fe7c3ed6975dc06f3e7a3b0152173'):
        # self.tmdb_origional_image_url = "https://image.tmdb.org/t/p/original/"
        tmdb.API_KEY = API_KEY
        self.tmdb_max_pages = 1
        self.tmdb_film_title_key_list = ['title', 'original_title']
        self.tmdb_tv_title_key_list = ['name', 'original_name']
        self.available_eid = available_eid
        self.eapi_name = 'tmdb'
        self._supported_source_eapi_ = {'film': {'want': 'imdb', 'have': 'tmdb'},
                                        'tv': {'want': ['imdb'], 'have': ['tmdb']}}

        self.film_genre_map = {28: {"zp_genre_id": 1, "name": "Action"},
                               12: {"zp_genre_id": 2, "name": "Adventure"},
                               16: {"zp_genre_id": 3, "name": "Animation"},
                               35: {"zp_genre_id": 5, "name": "Comedy"},
                               80: {"zp_genre_id": 6, "name": "Crime"},
                               99: {"zp_genre_id": 7, "name": "Documentary"},
                               18: {"zp_genre_id": 8, "name": "Drama"},
                               10751: {"zp_genre_id": 13, "name": "Family"},
                               14: {"zp_genre_id": 20, "name": "Fantasy"},
                               36: {"zp_genre_id": 10, "name": "History"},
                               27: {"zp_genre_id": 11, "name": "Horror"},
                               10402: {"zp_genre_id": 14, "name": "Music"},
                               9648: {"zp_genre_id": 21, "name": "Mystery"},
                               10749: {"zp_genre_id": 15, "name": "Romance"},
                               878: {"zp_genre_id": 16, "name": "Science Fiction"},
                               10770: {"zp_genre_id": 23, "name": "TV Movie"},
                               53: {"zp_genre_id": 17, "name": "Thriller"},
                               10752: {"zp_genre_id": 18, "name": "War"},
                               37: {"zp_genre_id": 22, "name": "Western"}}

        self.tv_genre_map = {10759: {"zp_genre_id": [1, 2], "name": "Action & Adventure"},
                             16: {"zp_genre_id": 3, "name": "Animation"},
                             35: {"zp_genre_id": 5, "name": "Comedy"},
                             80: {"zp_genre_id": 6, "name": "Crime"},
                             99: {"zp_genre_id": 7, "name": "Documentary"},
                             18: {"zp_genre_id": 8, "name": "Drama"},
                             10751: {"zp_genre_id": 13, "name": "Family"},
                             10762: {"zp_genre_id": 29, "name": "Kids"},
                             9648: {"zp_genre_id": 21, "name": "Mystery"},
                             10763: {"zp_genre_id": 32, "name": "News"},
                             10764: {"zp_genre_id": 33, "name": "Reality"},
                             10765: {"zp_genre_id": [16, 20], "name": "Sci-Fi & Fantasy"},
                             10766: {"zp_genre_id": 26, "name": "Soap"},
                             10767: {"zp_genre_id": 27, "name": "Talk"},
                             10768: {"zp_genre_id": [18, 31], "name": "War & Politics"},
                             37: {"zp_genre_id": 22, "name": "Western"}}

        self.supported_tv_images = {'show': ['poster', 'backdrop'],
                                    'season': ['poster'],
                                    'episode': []}
        self.supported_tv_image_langs = True

    def acquire_external_eid(self, eapi_have, eapi_have_eid, library):
        kwargs = None
        return_dict = {}
        if library == 'tv':
            if eapi_have == 'tmdb':
                eid = self.get_eapi_eid(eapi_have, eapi_have_eid, 'imdb', library)
                if eid is not None:
                    return_dict['imdb'] = eid
        return return_dict

    def setup_tmdb_get(self, get, tmdb_eid=False, **kwargs):
        if tmdb_eid == False:
            return getattr(tmdb, get)()
        else:
            try:
                return getattr(tmdb, get)(tmdb_eid, **kwargs)
            except tmdb.base.APIKeyError as e:
                log.debug('API KEY Error:: %s' % (e))
        return False

    @rate_limited(10, 1.0)
    def tmdb_get_section(self, tmdb_eid, get, section, retry_count=2, season_number=0, episode_number=0, **kwargs):
        get_tmdb_failed_count = 0
        retry_count = 2
        while get_tmdb_failed_count <= retry_count:
            try:
                if season_number > 0 and episode_number > 0:
                    return getattr(self.setup_tmdb_get(get, tmdb_eid,
                                                       season_number=season_number,
                                                       episode_number=episode_number), section)(**kwargs)
                elif season_number > 0:
                    return getattr(self.setup_tmdb_get(get, tmdb_eid,
                                                       season_number=season_number), section)(**kwargs)
                else:
                    return getattr(self.setup_tmdb_get(get, tmdb_eid), section)(**kwargs)
            except tmdb.base.APIKeyError as e:
                log.debug('API KEY Error:: %s' % (e))
            except requests.exceptions.HTTPError as e:
                log.debug('requests.exceptions.HTTPError: %s' % (e))
            except requests.packages.urllib3.exceptions.ProtocolError as e:
                log.debug('requests.packages.urllib3.exceptions.ProtocolError: %s' % (e))
            get_tmdb_failed_count += 1
        log.debug(
            'failed to getattr(self.setup_tmdb_get(tmdb_eid, get), section)(**kwargs) tpid: %s get: %s section: %s kwargs: %s tries %s' % (
                tmdb_eid, get, section, kwargs, (get_tmdb_failed_count + 1)))
        return None

    def get_eapi_eid(self, have_eapi, have_eapi_eid, want_eapi, library):
        if library == 'film':
            if have_eapi == 'tmdb' and want_eapi == 'imdb':
                return self.get_imdb_id(have_eapi_eid)
            elif have_eapi == 'imdb' and want_eapi == 'tmdb':
                return self.get_tmdbid_from_imdbid(have_eapi_eid)
        elif library == 'tv':
            if have_eapi == 'tmdb' and want_eapi == 'imdb':
                external_ids = self.external_ids(have_eapi_eid, library)
                if 'imdb_id' in external_ids.keys():
                    return external_ids['imdb_id']
        return None

    def _do_tmdb_search_movie(self, tmdb_search, query, page=1, year=False):
        get_tmdb_failed_count = 0
        retry_count = 2
        while get_tmdb_failed_count <= retry_count:
            try:
                log.debug(
                    'try #{0} for query: {1} and page {2} and year {3}'.format(get_tmdb_failed_count + 1, query, page,
                                                                               year))
                if year != False:
                    tmdb_search.movie(query=query, page=page, year=year)
                else:
                    tmdb_search.movie(query=query, page=page)
                return tmdb_search
            except tmdb.base.APIKeyError as e:
                log.debug('API KEY Error:: {0}'.format(e))
            except requests.exceptions.HTTPError as e:
                log.debug('requests.exceptions.HTTPError: {0}'.format(e))
            except requests.packages.urllib3.exceptions.ProtocolError as e:
                log.debug('requests.packages.urllib3.exceptions.ProtocolError: {0}'.format(e))
            get_tmdb_failed_count += 1
        log.debug('failed to tmdb_search.movie query {query} page {page} tries {tries}'.format(
            query=query,
            page=page,
            tries=(get_tmdb_failed_count + 1)))
        return tmdb_search

    def _do_tmdb_search_tv_show(self, tmdb_search, query, page=1):
        get_tmdb_failed_count = 0
        retry_count = 2
        while get_tmdb_failed_count <= retry_count:
            try:
                log.debug('try #{0} for query: {1} and page {2}'.format(get_tmdb_failed_count + 1, query, page))
                tmdb_search.tv(query=query, page=page)
                return tmdb_search
            except tmdb.base.APIKeyError as e:
                log.debug('API KEY Error:: {0}'.format(e))
            except requests.exceptions.HTTPError as e:
                log.debug('requests.exceptions.HTTPError: {0}'.format(e))
            except requests.packages.urllib3.exceptions.ProtocolError as e:
                log.debug('requests.packages.urllib3.exceptions.ProtocolError: {0}'.format(e))
            get_tmdb_failed_count += 1
        log.debug('failed to tmdb_search.movie query {query} page {page} tries {tries}'.format(
            query=query,
            page=page,
            tries=(get_tmdb_failed_count + 1)))
        return tmdb_search

    # todo how did this function ever work ????
    def get_tmdbid_from_imdbid(self, imdb_id, retry_count=2):
        tmdb_film_id = None
        get_tmdb_failed_count = 0
        retry_count = 2
        while get_tmdb_failed_count <= retry_count:
            try:
                tmdb_find_info = tmdb_find.info(imdb_id, external_source='imdb_id')
                if isinstance(tmdb_find_info, dict):
                    if tmdb_find_info.has_key('movie_results'):
                        if len(tmdb_find_info['movie_results']) == 1:
                            return tmdb_find_info['movie_results'][0]['id']
            except tmdb.base.APIKeyError as e:
                log.debug("tmdb API KEY missing %s" % e)
            except requests.exceptions.HTTPError as e:
                log.debug("requests.exceptions.HTTPError: %s" % e)
            except requests.packages.urllib3.exceptions.ProtocolError as e:
                log.debug("requests.packages.urllib3.exceptions.ProtocolError: %s" % e)
            get_tmdb_failed_count += 1
        log.debug("After %s retries failed to process %s" % (
            retry_count, "tmdb_find.info - external_source='imdb_id' " + str(imdb_id)))
        return None

    def _tmdb_search_movie(self, title_cgi_escape, year, pages):
        result_list = []
        for page in range(1, pages):
            log.debug('page: {page} for title_cgi_escape: {title_cgi_escape} and year: {year}'.format(
                title_cgi_escape=title_cgi_escape,
                page=page,
                year=year))
            tmdb_search = self._do_tmdb_search_movie(self.setup_tmdb_get('Search'), title_cgi_escape, page, year)
            if hasattr(tmdb_search, 'results'):
                log.debug(('tmdb_search does have attribute results and tmdb_search.results:'
                           'is type {tmdb_search_results_type} for page: {page} and '
                           'title_cgi_escape: {title_cgi_escape} '
                           'and year: {year}').format(
                    tmdb_search_results_type=type(tmdb_search.results),
                    title_cgi_escape=title_cgi_escape,
                    page=page,
                    year=year))
                log.debug('tmdb_search.results {0}'.format(tmdb_search.results))
                if tmdb_search.results:
                    log.debug('tmdb_search.results not empty')
                    for result in tmdb_search.results:
                        conformed_result = {}
                        if result.has_key('id'):
                            conformed_result['id'] = result['id']
                        if result.has_key('release_date'):
                            conformed_result['year'] = mk_int(result['release_date'][:4])
                        title_list = []

                        for title_key in self.tmdb_film_title_key_list:
                            if result.has_key(title_key):
                                if result[title_key] not in title_list:
                                    title_list.append(result[title_key])
                        alternative_titles = self.alternative_titles(result['id'], 'Movies')
                        log.debug('alternative_titles: {0}'.format(alternative_titles))
                        for alternative_title in alternative_titles:
                            if alternative_title['title'] not in title_list:
                                title_list.append(alternative_title['title'])
                        if title_list:
                            conformed_result['title_list'] = title_list
                        if (conformed_result.has_key('year')
                            and conformed_result.has_key('title_list')
                            and conformed_result.has_key('id')):
                            result_list.append(conformed_result)
                else:
                    log.debug('tmdb_search.results {0} empty breaking out of page incremnt'.format(tmdb_search.results))
                    return result_list
            else:
                log.debug('tmdb_search does NOT have attribute results')
                return result_list
        log.debug('result_list: {0}'.format(result_list))
        return result_list

    def _tmdb_search_tv_show(self, title_cgi_escape, pages):
        result_list = []
        for page in range(1, pages):
            log.debug('page: {page} for title_cgi_escape: {title_cgi_escape}'.format(
                title_cgi_escape=title_cgi_escape,
                page=page))
            tmdb_search = self._do_tmdb_search_tv_show(self.setup_tmdb_get('Search'), title_cgi_escape, page)
            if hasattr(tmdb_search, 'results'):
                log.debug(('tmdb_search does have attribute results and tmdb_search.results:'
                           'is type {tmdb_search_results_type} for page: {page} and '
                           'title_cgi_escape: {title_cgi_escape}').format(
                    tmdb_search_results_type=type(tmdb_search.results),
                    title_cgi_escape=title_cgi_escape,
                    page=page))
                log.debug('tmdb_search.results {0}'.format(tmdb_search.results))
                if tmdb_search.results:
                    log.debug('tmdb_search.results not empty')
                    for result in tmdb_search.results:
                        conformed_result = {}
                        if result.has_key('id'):
                            conformed_result['id'] = result['id']
                        title_list = []
                        for title_key in self.tmdb_tv_title_key_list:
                            # print(title_key, result[title_key])
                            if title_key in result.keys():
                                if result[title_key] not in title_list:
                                    title_list.append(result[title_key])

                        alternative_titles = self.alternative_titles(result['id'], 'TV')
                        # print(title_list)
                        log.debug('alternative_titles: {0}'.format(alternative_titles))
                        for alternative_title in alternative_titles:
                            if alternative_title['title'] not in title_list:
                                title_list.append(alternative_title['title'])
                        if title_list:
                            conformed_result['title_list'] = title_list
                            # print(title_list)
                            # raise SystemExit

                        if 'first_air_date' in result.keys():
                            try:
                                dt = datetime.strptime(result['first_air_date'], '%Y-%m-%d')
                            except:
                                pass
                            else:
                                conformed_result['first_air_year'] = dt.year

                        tv_show_info = self.tmdb_get_section_attr(result['id'], 'TV', 'info')
                        if tv_show_info:
                            if isinstance(tv_show_info, dict):
                                if 'seasons' in tv_show_info.keys():
                                    if tv_show_info['seasons']:
                                        conformed_result['seasons'] = tv_show_info['seasons']

                        if (conformed_result.has_key('title_list')
                            and conformed_result.has_key('id')
                            and 'seasons' in conformed_result.keys()):
                            result_list.append(conformed_result)
                else:
                    log.debug('tmdb_search.results {0} empty breaking out of page incremnt'.format(tmdb_search.results))
                    return result_list
            else:
                log.debug('tmdb_search does NOT have attribute results')
                return result_list
        log.debug('result_list: {0}'.format(result_list))
        return result_list

    def tmdb_get_section_attr(self, _id, section, attribute, keys=None):
        section_attr = self.tmdb_get_section(_id, section, attribute)
        log.debug("_id: {0}, section: {1}, attribute: {2}".format(_id,
                                                                  section,
                                                                  attribute))
        if section_attr is not None:
            if any(section_attr):
                return section_attr
            else:
                log.debug("section_attr empty")
        else:
            log.debug("section_attr is None")
        return None

    def alternative_titles(self, tmdb_eid, library):
        tmdb_alternative_titles = self.tmdb_get_section(tmdb_eid, library, 'alternative_titles')
        log.debug("tmdb_alternative_titles %s" % tmdb_alternative_titles)
        if tmdb_alternative_titles is not None:
            if any(tmdb_alternative_titles):
                if library == 'TV':
                    if tmdb_alternative_titles.has_key('results'):
                        log.debug("---end tmdb film tmdb_alternative_titles ---")
                        return tmdb_alternative_titles['results']
                    else:
                        log.debug(
                            "tmdb_alternative_titles keys %s does not have results" % tmdb_alternative_titles.keys())
                elif library == 'FILM':
                    if tmdb_alternative_titles.has_key('titles'):
                        log.debug("---end tmdb film tmdb_alternative_titles ---")
                        return tmdb_alternative_titles['titles']
                    else:
                        log.debug(
                            "tmdb_alternative_titles keys %s does not have titles" % tmdb_alternative_titles.keys())
            else:
                log.debug("tmdb_alternative_titles empty")
        else:
            log.debug("tmdb_alternative_titles is None")
        log.debug("---end tmdb film tmdb_alternative_titles ---")
        return []

    def external_ids(self, tmdb_eid, library):
        external_ids = None
        if library == 'tv':
            external_ids = self.tmdb_get_section(tmdb_eid, 'TV', 'external_ids')
        log.debug("external_ids %s" % external_ids)
        # print(external_ids)
        if external_ids is not None:
            if any(external_ids):
                if isinstance(external_ids, dict):
                    log.debug("---end tmdb film external_ids ---")
                    return external_ids
                else:
                    log.debug("type(external_ids) %s is not dict", type(external_ids))
            else:
                log.debug("tmdb_movie_info empty")
        else:
            log.debug("tmdb_movie_info is None")
        log.debug("---end tmdb film external_ids ---")
        return {}

    def find_film(self, title, year=None):
        title_cgi_escape = cgi.escape(title)
        log.debug('title_cgi_escape: {title_cgi_escape} for title: {title} and year: {year}'.format(
            title_cgi_escape=title_cgi_escape,
            title=title,
            year=year))

        result_list = self._tmdb_search_movie(title_cgi_escape, False, self.tmdb_max_pages + 1)
        return result_list

    def find_tv_show(self, title, year=None):
        title_cgi_escape = cgi.escape(title)
        log.debug('title_cgi_escape: {title_cgi_escape} for title: {title}'.format(
            title_cgi_escape=title_cgi_escape,
            title=title,
            year=year))

        result_list = self._tmdb_search_tv_show(title_cgi_escape, self.tmdb_max_pages + 1)
        return result_list

    def get_film_data(self, tmdb_eid, language='en'):
        raw_movie_data = self.get_tmdb_movie_info(tmdb_eid, language=language)
        log.debug('raw_movie_data: {0}'.format(raw_movie_data))
        film_data = None
        compatiable_keys = ['overview',
                            'genres',
                            'title',
                            'original_title',
                            'release_date',
                            'runtime',
                            'belongs_to_collection']
        film_data = {}
        if isinstance(raw_movie_data, dict):
            for key in compatiable_keys:
                if key in raw_movie_data:
                    if key == 'genres':
                        film_data[key] = []
                        for genre in raw_movie_data['genres']:
                            if genre['id'] in self.film_genre_map:
                                if isinstance(self.film_genre_map[genre['id']]['zp_genre_id'], list):
                                    for zp_genre_id in self.tv_genre_map[genre['id']]['zp_genre_id']:
                                        film_data['genres'].append(zp_genre_id)
                                else:
                                    film_data['genres'].append(self.film_genre_map[genre['id']]['zp_genre_id'])
                    else:
                        film_data[key] = raw_movie_data[key]
                else:
                    log.warning('%s not in raw_movie_data %s', key, raw_movie_data.keys())
            if 'vote_average' in raw_movie_data:
                film_data['rating'] = int(raw_movie_data['vote_average'])
            else:
                log.warning('rating not in raw_movie_data %s', raw_movie_data.keys())
            movie_credits = self.get_tmdb_movie_credits(tmdb_eid, language=language)
            log.debug('movie_credits: {0}'.format(movie_credits))
            if isinstance(movie_credits, dict):
                film_data['credits'] = {}
                if 'cast' in movie_credits:
                    film_data['credits']['cast'] = movie_credits['cast']
                if 'crew' in movie_credits:
                    film_data['credits']['crew'] = movie_credits['crew']
            else:
                log.warning('movie_credits %s is not dict but %s', movie_credits, type(movie_credits))
        else:
            log.warning('raw_movie_data %s is not dict but %s', raw_movie_data, type(raw_movie_data))
        log.debug('film_data: {0}'.format(film_data))
        return film_data

    def get_tmdb_tv_info(self, tmdb_eid, **kwargs):
        return self.tmdb_get_section(tmdb_eid, 'TV', 'info', **kwargs)

    def get_tmdb_tv_credits(self, tmdb_eid, **kwargs):
        return self.tmdb_get_section(tmdb_eid, 'TV', 'credits', **kwargs)

    def get_tv_episode_data(self, tmdb_eid, season_number=0, episode_number=0, **kwargs):
        return self.tmdb_get_section(tmdb_eid, 'TV_Episodes', 'info',
                                     season_number=season_number,
                                     episode_number=episode_number, **kwargs)

    def get_tmdb_tv_seasn_info(self, tmdb_eid, season_number, **kwargs):
        return self.tmdb_get_section(tmdb_eid, 'TV_Seasons', 'info',
                                     season_number=season_number, **kwargs)

    def get_tv_show_data(self, tmdb_eid, language='en'):
        raw_tv_data = self.get_tmdb_tv_info(tmdb_eid, language=language)
        log.debug('raw_tv_data: {0}'.format(raw_tv_data))
        tv_data = None
        compatiable_keys = ['overview',
                            'genres',
                            'name',
                            'original_name',
                            'first_air_date']
        if isinstance(raw_tv_data, dict):
            tv_data = {}
            for key in compatiable_keys:
                if key == 'genres':
                    tv_data[key] = []
                    for genre in raw_tv_data['genres']:
                        if genre['id'] in self.tv_genre_map:
                            if isinstance(self.tv_genre_map[genre['id']]['zp_genre_id'], list):
                                for zp_genre_id in self.tv_genre_map[genre['id']]['zp_genre_id']:
                                    tv_data['genres'].append(zp_genre_id)
                            else:
                                tv_data['genres'].append(self.tv_genre_map[genre['id']]['zp_genre_id'])
                else:
                    tv_data[key] = raw_tv_data[key]
            tv_data['rating'] = int(raw_tv_data['vote_average'])
            tv_credits = self.get_tmdb_tv_credits(tmdb_eid, language=language)
            log.debug('tv_credits: {0}'.format(tv_credits))
            tv_data['credits'] = {}
            tv_data['credits']['cast'] = tv_credits['cast']
            tv_data['credits']['crew'] = tv_credits['crew']
            log.debug('tv_data: {0}'.format(tv_data))
        return tv_data

    def get_tv_season_data(self, tmdb_eid, season, language='en'):
        raw_tv_season_data = self.get_tmdb_tv_seasn_info(tmdb_eid, season, language=language)
        tv_data = None
        if isinstance(raw_tv_season_data, dict):
            if 'episodes' in raw_tv_season_data.keys():
                if isinstance(raw_tv_season_data['episodes'], list):
                    tv_data = raw_tv_season_data
                else:
                    log.warning(
                        ('''raw_tv_season_data['episodes']: {0} is empty''').format(raw_tv_season_data['episodes']))
            else:
                log.warning(('episodes not in raw_tv_season_data.keys(): {0}').format(raw_tv_season_data.keys()))
        else:
            log.warning('raw_tv_season_data is not dict but {0}'.format(type(raw_tv_season_data)))
        return tv_data

    def get_imdb_id(self, tmdb_eid):
        log.debug("---start tmdb film get_imdb_id ---")
        tmdb_movie_info = self.tmdb_get_section(tmdb_eid, 'Movies', 'info')
        log.debug("tmdb_movie_info %s" % tmdb_movie_info)
        if tmdb_movie_info is not None:
            if any(tmdb_movie_info):
                if tmdb_movie_info.has_key('imdb_id'):
                    log.debug("---end tmdb film get_imdb_id ---")
                    return tmdb_movie_info['imdb_id']
                else:
                    log.debug("tmdb_movie_info keys %s does not have imdb_id" % tmdb_movie_info.keys())
            else:
                log.debug("tmdb_movie_info empty")
        else:
            log.debug("tmdb_movie_info is None")
        log.debug("---end tmdb film get_imdb_id ---")
        return None

    def get_person_info(self, tmdb_person_id):
        person_info = self.tmdb_get_section(tmdb_person_id, 'People', 'info')
        if person_info:
            if isinstance(person_info, dict):
                if 'birthday' in person_info.keys():
                    return person_info
        return None

    def get_tmdb_movie_info(self, tmdb_eid, **kwargs):
        return self.tmdb_get_section(tmdb_eid, 'Movies', 'info', **kwargs)

    def get_tmdb_movie_credits(self, tmdb_eid, **kwargs):
        return self.tmdb_get_section(tmdb_eid, 'Movies', 'credits', **kwargs)

    def get_poster_url(self, tmdb_eid, **kwargs):
        log.debug("---start tmdb film get_poster_url ---")
        tmdb_movie_info = self.tmdb_get_section(tmdb_eid, 'Movies', 'info', **kwargs)
        log.debug("tmdb_movie_info %s" % tmdb_movie_info)
        if tmdb_movie_info:
            if any(tmdb_movie_info):
                if tmdb_movie_info.has_key('poster_path'):
                    log.debug("---end tmdb film get_poster_url ---")
                    if isinstance(tmdb_movie_info['poster_path'], basestring):
                        poster_filename = tmdb_movie_info['poster_path'].strip('/')
                        return '{0}{1}'.format(tmdb_base_image_url, tmdb_movie_info['poster_path']), poster_filename
                    else:
                        return None, None
                else:
                    log.debug("tmdb_movie_info keys %s does not have poster_path" % tmdb_movie_info.keys())
            else:
                log.debug("tmdb_movie_info empty")
        else:
            log.warning(
                'tmdb_movie_info: {0} type: {1} for tmdb_eid: {2}. Has the movie id been removed from tmdb? It does happen.'.format(
                    tmdb_movie_info, type(tmdb_movie_info), tmdb_eid))
        log.debug("---end tmdb film get_poster_url ---")
        return None, None

    def get_film_raw_images(self, tmdb_eid, lang, highest_rating=True):
        log.debug("---start get_film_raw_images ---")
        if lang is None:
            kwargs = {'language': 'null'}
        else:
            kwargs = {'language': lang}
        tmdb_film_raw_images = self.tmdb_get_section(tmdb_eid, 'Movies', 'images', **kwargs)
        return_dict = {'poster': None,
                       'backdrop': None}
        if isinstance(tmdb_film_raw_images, dict):
            if 'posters' in tmdb_film_raw_images:
                if any(tmdb_film_raw_images['posters']):
                    highest_rating_poster = tmdb_film_raw_images['posters'][0]
                    if isinstance(highest_rating_poster, dict):
                        if 'file_path' in highest_rating_poster:
                            if isinstance(highest_rating_poster['file_path'], string_types):
                                return_dict['poster'] = {}
                                return_dict['poster']['image_reference'] = \
                                    highest_rating_poster['file_path'].strip('/')
                                return_dict['poster']['image_url'] = '{0}{1}'.format(tmdb_base_image_url,
                                                                                     highest_rating_poster[
                                                                                         'file_path'].strip('/'))
                            else:
                                log.warning('''highest_rating_poster['file_path'] not sting_types''')
                        else:
                            log.warning('''file_path not in highest_rating_poster''')
                    else:
                        log.warning('''highest_rating_poster is %s not dict''', type(highest_rating_poster))
                else:
                    log.warning('''tmdb_film_raw_images['posters'] is empty''')
            else:
                log.warning('posters not in tmdb_film_raw_images')
            if 'backdrops' in tmdb_film_raw_images:
                if any(tmdb_film_raw_images['backdrops']):
                    highest_rating_backdrop = tmdb_film_raw_images['backdrops'][0]
                    if isinstance(highest_rating_backdrop, dict):
                        if 'file_path' in highest_rating_backdrop:
                            if isinstance(highest_rating_backdrop['file_path'], string_types):
                                return_dict['backdrop'] = {}
                                return_dict['backdrop']['image_reference'] = \
                                    highest_rating_backdrop['file_path'].strip('/')
                                return_dict['backdrop']['image_url'] = '{0}{1}'.format(tmdb_base_image_url,
                                                                                       highest_rating_backdrop[
                                                                                           'file_path'].strip('/'))
                            else:
                                log.warning('''highest_rating_backdrop['file_path'] not sting_types''')
                        else:
                            log.warning('''file_path not in highest_rating_backdrop''')
                    else:
                        log.warning('''highest_rating_backdrop is %s not dict''', type(highest_rating_backdrop))
                else:
                    log.warning('''tmdb_film_raw_images['backdrops'] is empty''')
            else:
                log.warning('backdrops not in tmdb_film_raw_images')

        else:
            log.warning('tmdb_film_raw_images is %s not dict', type(tmdb_film_raw_images))
        log.debug("---end get_film_raw_images ---")
        return return_dict

    def get_film_collection_raw_images(self, tmdb_eid, lang, highest_rating=True):
        log.debug("---start get_film_raw_images ---")
        if lang is None:
            kwargs = {'language': 'null'}
        else:
            kwargs = {'language': lang}
        tmdb_film_raw_images = self.tmdb_get_section(tmdb_eid, 'Collections', 'images', **kwargs)
        return_dict = {'poster': None,
                       'backdrop': None}
        if isinstance(tmdb_film_raw_images, dict):
            if 'posters' in tmdb_film_raw_images:
                if any(tmdb_film_raw_images['posters']):
                    highest_rating_poster = tmdb_film_raw_images['posters'][0]
                    if isinstance(highest_rating_poster, dict):
                        if 'file_path' in highest_rating_poster:
                            if isinstance(highest_rating_poster['file_path'], string_types):
                                return_dict['poster'] = {}
                                return_dict['poster']['image_reference'] = \
                                    highest_rating_poster['file_path'].strip('/')
                                return_dict['poster']['image_url'] = '{0}{1}'.format(tmdb_base_image_url,
                                                                                     highest_rating_poster[
                                                                                         'file_path'].strip('/'))
                            else:
                                log.warning('''highest_rating_poster['file_path'] not sting_types''')
                        else:
                            log.warning('''file_path not in highest_rating_poster''')
                    else:
                        log.warning('''highest_rating_poster is %s not dict''', type(highest_rating_poster))
                else:
                    log.warning('''tmdb_film_raw_images['posters'] is empty''')
            else:
                log.warning('posters not in tmdb_film_raw_images')
            if 'backdrops' in tmdb_film_raw_images:
                if any(tmdb_film_raw_images['backdrops']):
                    highest_rating_backdrop = tmdb_film_raw_images['backdrops'][0]
                    if isinstance(highest_rating_backdrop, dict):
                        if 'file_path' in highest_rating_backdrop:
                            if isinstance(highest_rating_backdrop['file_path'], string_types):
                                return_dict['backdrop'] = {}
                                return_dict['backdrop']['image_reference'] = \
                                    highest_rating_backdrop['file_path'].strip('/')
                                return_dict['backdrop']['image_url'] = '{0}{1}'.format(tmdb_base_image_url,
                                                                                       highest_rating_backdrop[
                                                                                           'file_path'].strip('/'))
                            else:
                                log.warning('''highest_rating_backdrop['file_path'] not sting_types''')
                        else:
                            log.warning('''file_path not in highest_rating_backdrop''')
                    else:
                        log.warning('''highest_rating_backdrop is %s not dict''', type(highest_rating_backdrop))
                else:
                    log.warning('''tmdb_film_raw_images['backdrops'] is empty''')
            else:
                log.warning('backdrops not in tmdb_film_raw_images')

        else:
            log.warning('tmdb_film_raw_images is %s not dict', type(tmdb_film_raw_images))
        log.debug("---end get_film_raw_images ---")

        #raise SystemExit
        return return_dict

    def get_tv_season_raw_images(self, tmdb_eid, zp_tv_season_list, lang, seasons_image_type_dict, highest_rating=True):
        log.debug("---start get_tv_season_raw_images ---")
        return_dict = {}
        if lang is None:
            kwargs = {'language': 'null'}
        else:
            kwargs = {'language': lang}
        log.debug('zp_tv_season_list %s', zp_tv_season_list)
        #log.debug('image_types %s', image_types)
        for zp_tv_season in zp_tv_season_list:
            tmdb_tv_raw_images = self.tmdb_get_section(tmdb_eid, 'TV_Seasons', 'images', season_number=zp_tv_season,
                                                       **kwargs)
            # log.error('tmdb_tv_raw_images %s', tmdb_tv_raw_images)
            if isinstance(tmdb_tv_raw_images, dict):
                if 'posters' in tmdb_tv_raw_images:
                    if any(tmdb_tv_raw_images['posters']):
                        highest_rating_poster = tmdb_tv_raw_images['posters'][0]
                        if isinstance(highest_rating_poster, dict):
                            if 'file_path' in highest_rating_poster:
                                if isinstance(highest_rating_poster['file_path'], string_types):
                                    if zp_tv_season not in return_dict:
                                        return_dict[zp_tv_season] = {}
                                    return_dict[zp_tv_season]['poster'] = {}
                                    return_dict[zp_tv_season]['poster']['image_reference'] = \
                                        highest_rating_poster['file_path'].strip('/')
                                    return_dict[zp_tv_season]['poster']['image_url'] = '{0}{1}'.format(
                                        tmdb_base_image_url,
                                        highest_rating_poster[
                                            'file_path'].strip('/'))
                                else:
                                    log.warning('''highest_rating_poster['file_path'] not sting_types''')
                            else:
                                log.warning('''file_path not in highest_rating_poster''')
                        else:
                            log.warning('''highest_rating_poster is %s not dict''', type(highest_rating_poster))
                    else:
                        log.warning('''tmdb_tv_raw_images['posters'] is empty''')
                else:
                    log.warning('posters not in tmdb_tv_raw_images')
        log.debug('return_dict %s', return_dict)
        return return_dict

    def get_tv_episode_raw_images(self, tmdb_eid, zp_tv_episode_dict, lang, seasons_image_type_dict, highest_rating=True):
        log.debug("---start get_tv_season_raw_images ---")
        return_dict = {}
        log.debug('zp_tv_episode_dict %s', zp_tv_episode_dict)
        #raise SystemExit
        #log.debug('image_types %s', image_types)

        image_type_reference_dict = {'screenshot': 'stills'}
        for zp_tv_season in zp_tv_episode_dict:
            for episode in zp_tv_episode_dict[zp_tv_season]:
                tmdb_tv_raw_images = self.tmdb_get_section(tmdb_eid, 'TV_Episodes', 'images', season_number=zp_tv_season,
                                                           episode_number=episode)
                log.debug('tmdb_tv_raw_images %s', tmdb_tv_raw_images)
                #raise SystemExit
                if isinstance(tmdb_tv_raw_images, dict):
                    for image_type in image_type_reference_dict:
                        if image_type_reference_dict[image_type] in tmdb_tv_raw_images:
                            if any(tmdb_tv_raw_images[image_type_reference_dict[image_type]]):
                                highest_rating_poster = tmdb_tv_raw_images[image_type_reference_dict[image_type]][0]
                                if isinstance(highest_rating_poster, dict):
                                    if 'file_path' in highest_rating_poster:
                                        if isinstance(highest_rating_poster['file_path'], string_types):
                                            if zp_tv_season not in return_dict:
                                                return_dict[zp_tv_season] = {}
                                            if episode not in return_dict[zp_tv_season]:
                                                return_dict[zp_tv_season][episode] = {}
                                            return_dict[zp_tv_season][episode][image_type] = {}
                                            return_dict[zp_tv_season][episode][image_type]['image_reference'] = \
                                                highest_rating_poster['file_path'].strip('/')
                                            return_dict[zp_tv_season][episode][image_type]['image_url'] = '{0}{1}'.format(
                                                tmdb_base_image_url,
                                                highest_rating_poster[
                                                    'file_path'].strip('/'))
                                        else:
                                            log.warning('''highest_rating_poster['file_path'] not sting_types''')
                                    else:
                                        log.warning('''file_path not in highest_rating_poster''')
                                else:
                                    log.warning('''highest_rating_poster is %s not dict''', type(highest_rating_poster))
                            else:
                                log.warning('''tmdb_tv_raw_images['posters'] is empty''')
                        else:
                            log.warning('posters not in tmdb_tv_raw_images')
                #log.error('tmdb_tv_raw_images %s', tmdb_tv_raw_images)
            #log.error('return_dict %s', return_dict)
        log.debug('return_dict %s', return_dict)
        return return_dict

    def get_tv_show_raw_images(self, tmdb_eid, lang, image_types, highest_rating=True):
        log.debug("---start get_tv_raw_images ---")
        if lang is None:
            kwargs = {'language': 'null'}
        else:
            kwargs = {'language': lang}
        tmdb_tv_raw_images = self.tmdb_get_section(tmdb_eid, 'TV', 'images', **kwargs)
        return_dict = {'poster': None,
                       'backdrop': None}
        if isinstance(tmdb_tv_raw_images, dict):
            if 'posters' in tmdb_tv_raw_images:
                if any(tmdb_tv_raw_images['posters']):
                    highest_rating_poster = tmdb_tv_raw_images['posters'][0]
                    if isinstance(highest_rating_poster, dict):
                        if 'file_path' in highest_rating_poster:
                            if isinstance(highest_rating_poster['file_path'], string_types):
                                return_dict['poster'] = {}
                                return_dict['poster']['image_reference'] = \
                                    highest_rating_poster['file_path'].strip('/')
                                return_dict['poster']['image_url'] = '{0}{1}'.format(tmdb_base_image_url,
                                                                                     highest_rating_poster[
                                                                                         'file_path'].strip('/'))
                            else:
                                log.warning('''highest_rating_poster['file_path'] not sting_types''')
                        else:
                            log.warning('''file_path not in highest_rating_poster''')
                    else:
                        log.warning('''highest_rating_poster is %s not dict''', type(highest_rating_poster))
                else:
                    log.warning('''tmdb_tv_raw_images['posters'] is empty''')
            else:
                log.warning('posters not in tmdb_tv_raw_images')
            if 'backdrops' in tmdb_tv_raw_images:
                if any(tmdb_tv_raw_images['backdrops']):
                    highest_rating_backdrop = tmdb_tv_raw_images['backdrops'][0]
                    if isinstance(highest_rating_backdrop, dict):
                        if 'file_path' in highest_rating_backdrop:
                            if isinstance(highest_rating_backdrop['file_path'], string_types):
                                return_dict['backdrop'] = {}
                                return_dict['backdrop']['image_reference'] = \
                                    highest_rating_backdrop['file_path'].strip('/')
                                return_dict['backdrop']['image_url'] = '{0}{1}'.format(tmdb_base_image_url,
                                                                                       highest_rating_backdrop[
                                                                                           'file_path'].strip('/'))
                            else:
                                log.warning('''highest_rating_backdrop['file_path'] not sting_types''')
                        else:
                            log.warning('''file_path not in highest_rating_backdrop''')
                    else:
                        log.warning('''highest_rating_backdrop is %s not dict''', type(highest_rating_backdrop))
                else:
                    log.warning('''tmdb_tv_raw_images['backdrops'] is empty''')
            else:
                log.warning('backdrops not in tmdb_tv_raw_images')

        else:
            log.warning('tmdb_tv_raw_images is %s not dict', type(tmdb_tv_raw_images))
        log.debug("---end get_tv_raw_images ---")
        return return_dict

    def get_backdrop_url(self, tmdb_eid, **kwargs):
        # TODO What to do when movie id has been removed
        log.debug("---start tmdb film get_backdrop_url ---")
        tmdb_movie_info = self.tmdb_get_section(tmdb_eid, 'Movies', 'info', **kwargs)
        log.debug("tmdb_movie_info %s" % tmdb_movie_info)
        if tmdb_movie_info:
            if any(tmdb_movie_info):
                if tmdb_movie_info.has_key('backdrop_path'):
                    log.debug("---end tmdb film get_backdrop_url ---")
                    if isinstance(tmdb_movie_info['backdrop_path'], basestring):
                        backdrop_filename = tmdb_movie_info['backdrop_path'].strip('/')
                        return '{0}{1}'.format(tmdb_base_image_url, backdrop_filename), backdrop_filename
                    else:
                        return None, None
                else:
                    log.debug("tmdb_movie_info keys {0} does not have backdrop_path for tmdb_eid: {1}".format(
                        tmdb_movie_info.keys(), tmdb_eid))
            else:
                log.debug("tmdb_movie_info empty for tmdb_eid: {0}".format(tmdb_eid))
        else:
            log.warning(
                'tmdb_movie_info: {0} type: {1} for tmdb_eid: {2}. Has the movie id been removed from tmdb? It does happen.'.format(
                    tmdb_movie_info, type(tmdb_movie_info), tmdb_eid))
        log.debug("---end tmdb film get_backdrop_url ---")
        return None, None

    def get_collection_data(self, tmdb_eid, language='en'):
        log.debug("---start tmdb film get_poster_url ---")
        kwargs = {'language': language}
        tmdb_movie_info = self.tmdb_get_section(tmdb_eid, 'Collections', 'info', **kwargs)
        log.debug("tmdb_movie_info %s" % tmdb_movie_info)
        if tmdb_movie_info:
            log.debug(tmdb_movie_info)
            if isinstance(tmdb_movie_info, dict):
                return tmdb_movie_info
            else:
                log.debug("tmdb_movie_info not dict")
        else:
            log.warning(
                'tmdb_movie_info: {0} type: {1} for tmdb_eid: {2}. Has the movie id been removed from tmdb? It does happen.'.format(
                    tmdb_movie_info, type(tmdb_movie_info), tmdb_eid))
        log.debug("---end tmdb collection data ---")
        return None

    def get_collection_poster(self, tmdb_eid, **kwargs):
        log.debug("---start tmdb film get_poster_url ---")
        tmdb_movie_info = self.tmdb_get_section(tmdb_eid, 'Collections', 'info', **kwargs)
        log.debug("tmdb_movie_info %s" % tmdb_movie_info)
        if tmdb_movie_info:
            if any(tmdb_movie_info):
                if tmdb_movie_info.has_key('poster_path'):
                    log.debug("---end tmdb film get_poster_url ---")
                    if isinstance(tmdb_movie_info['poster_path'], basestring):
                        poster_filename = tmdb_movie_info['poster_path'].strip('/')
                        return '{0}{1}'.format(tmdb_base_image_url, tmdb_movie_info['poster_path']), poster_filename
                    else:
                        return None, None
                else:
                    log.debug("tmdb_movie_info keys %s does not have poster_path" % tmdb_movie_info.keys())
            else:
                log.debug("tmdb_movie_info empty")
        else:
            log.warning(
                'tmdb_movie_info: {0} type: {1} for tmdb_eid: {2}. Has the movie id been removed from tmdb? It does happen.'.format(
                    tmdb_movie_info, type(tmdb_movie_info), tmdb_eid))
        log.debug("---end tmdb film get_poster_url ---")
        return None, None

    def get_tv_backdrop_url(self, tmdb_eid, **kwargs):
        # TODO What to do when movie id has been removed
        log.debug("---start tmdb film get_backdrop_url ---")
        tmdb_movie_info = self.tmdb_get_section(tmdb_eid, 'TV', 'info', **kwargs)
        log.debug("tmdb_movie_info %s" % tmdb_movie_info)
        if tmdb_movie_info:
            if any(tmdb_movie_info):
                if tmdb_movie_info.has_key('backdrop_path'):
                    log.debug("---end tmdb film get_backdrop_url ---")
                    if isinstance(tmdb_movie_info['backdrop_path'], basestring):
                        backdrop_filename = tmdb_movie_info['backdrop_path'].strip('/')
                        return '{0}{1}'.format(tmdb_base_image_url, backdrop_filename), backdrop_filename
                    else:
                        return None, None
                else:
                    log.debug("tmdb_movie_info keys {0} does not have backdrop_path for tmdb_eid: {1}".format(
                        tmdb_movie_info.keys(), tmdb_eid))
            else:
                log.debug("tmdb_movie_info empty for tmdb_eid: {0}".format(tmdb_eid))
        else:
            log.warning(
                'tmdb_movie_info: {0} type: {1} for tmdb_eid: {2}. Has the movie id been removed from tmdb? It does happen.'.format(
                    tmdb_movie_info, type(tmdb_movie_info), tmdb_eid))
        log.debug("---end tmdb film get_backdrop_url ---")
        return None, None
