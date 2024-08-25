# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging

import tvdbsimple as tvdb
import requests
# import urllib3
from six import string_types
from zerrphix.util.text import mk_int
from zerrphix.util import rate_limited

log = logging.getLogger(__name__)

_version_ = "0.1"
_libraries_ = ['tv']
_types_ = {'eapi':
               {'tv':
                    {'class': 'TVDB'}
                }
           }
_available_eids_ = {}
_eapi_name_ = "thetvdb"
# tvdb_image_url = "https://image.tvdb.org/t/p/original/"
tvdb_base_image_url = "https://thetvdb.com/banners/"



# https://api.thetvdb.com/swagger#/
class TVDB(object):
    def __init__(self, API_KEY='1AAFBE3AF72BE9A9'):
        self.supported_tv_images = {'show': ['banner', 'poster', 'backdrop'],
                                    'season': ['poster'],
                                    'episode': ['screenshot']}
        self.supported_tv_image_langs = True
        tvdb.KEYS.API_KEY = API_KEY
        # self.tvm = pytvmaze.TVMaze()
        # self.available_eid = available_eid

    def setup_tvdb_get(self, get, tvdb_eid=False, **kwargs):
        if tvdb_eid == False:
            return getattr(tvdb, get)()
        else:
            try:
                return getattr(tvdb, get)(tvdb_eid, **kwargs)
            except tvdb.base.APIKeyError as e:
                log.debug('API KEY Error:: %s' % (e))
        return False

    @rate_limited(10, 1.0)
    def tvdb_get_section(self, tvdb_eid, get, section, retry_count=2, season_number=0, episode_number=0, **kwargs):
        get_tvdb_failed_count = 0
        retry_count = 2
        while get_tvdb_failed_count <= retry_count:
            try:
                if get in ['poster', 'fanart', 'series']:
                    return getattr(self.setup_tvdb_get(get, tvdb_eid, **kwargs), section)(language=kwargs['language'])
                else:
                    #return getattr(self.setup_tvdb_get(get, tvdb_eid, **kwargs), section)()
                    if get == 'Series_Episodes':
                        tvdb_episode_series = self.setup_tvdb_get(get, tvdb_eid, **kwargs)
                        tvdb_episode_series._FILTERS = {}
                        tvdb_episode_series._PAGES = -1
                        tvdb_episode_series._PAGES_LIST = {}
                        return getattr(tvdb_episode_series, section)()
                    else:
                        return getattr(self.setup_tvdb_get(get, tvdb_eid, **kwargs), section)()
            except tvdb.base.APIKeyError as e:
                log.debug('API KEY Error:: %s' % (e))
            except requests.exceptions.HTTPError as e:
                log.debug('requests.exceptions.HTTPError: %s' % (e))
            except requests.packages.urllib3.exceptions.ProtocolError as e:
                log.debug('requests.packages.urllib3.exceptions.ProtocolError: %s' % (e))
            get_tvdb_failed_count += 1
        log.debug(
            'failed to getattr(self.setup_tvdb_get(tvdb_eid, get), section)(**kwargs) tpid: %s get: %s section: %s kwargs: %s tries %s' % (
                tvdb_eid, get, section, kwargs, (get_tvdb_failed_count + 1)))
        return None

    def get_tv_episode_raw_images(self, tvdb_eid, zp_tv_episode_dict, lang, seasons_image_type_dict,
                                  highest_rating=True):
        tvdb_episodes = self.tvdb_get_section(tvdb_eid, 'Series_Episodes', 'all')
        #log.debug('episodes %s, len %s', episodes[0], len(episodes))
        image_type_reference_dict = {'screenshot': 'filename'}
        log.debug('tvdb_eid %s', tvdb_eid)
        return_dict = {}
        log.debug('len(tvdb_episodes) %s ', len(tvdb_episodes))
        if isinstance(tvdb_episodes, list):
            if tvdb_episodes:
                for episode in tvdb_episodes:
                    if isinstance(episode, dict):
                        if 'id' in episode and 'airedEpisodeNumber' in episode and 'airedEpisodeNumber' in episode:
                            tvdb_episode_num = episode['airedEpisodeNumber']
                            tvdb_season_num = episode['airedSeason']
                            episode_id = episode['id']
                            if tvdb_season_num > 0 and tvdb_season_num > 0 and episode_id > 0:
                                if tvdb_season_num in zp_tv_episode_dict:
                                    if tvdb_episode_num in zp_tv_episode_dict[tvdb_season_num]:
                                        if tvdb_season_num not in return_dict:
                                            return_dict[tvdb_season_num] = {}
                                        if tvdb_episode_num not in return_dict[tvdb_season_num]:
                                            tvdb_episode_info = self.tvdb_get_section(episode_id, 'Episode', 'info')
                                            if isinstance(tvdb_episode_info, dict):
                                                for image_type in image_type_reference_dict:
                                                    if image_type_reference_dict[image_type] in tvdb_episode_info:
                                                        return_dict[tvdb_season_num][tvdb_episode_num] = {}
                                                        return_dict[tvdb_season_num][tvdb_episode_num][image_type] = {}
                                                        return_dict[tvdb_season_num][tvdb_episode_num][image_type][
                                                            'image_reference'] = tvdb_episode_info['filename'].strip('/')
                                                        return_dict[tvdb_season_num][tvdb_episode_num][image_type][
                                                            'image_url'] = '%s%s' % (tvdb_base_image_url,
                                                                                     tvdb_episode_info['filename'])
                                            else:
                                                log.warning('tvdb_episode_info %s not dict but %s', tvdb_episode_info,
                                                          type(tvdb_episode_info))
                                    else:
                                        log.debug('tvdb_episode_num %s not in zp_tv_episode_dict[tvdb_season_num] %s',
                                                  tvdb_episode_num, zp_tv_episode_dict[tvdb_season_num])
                                else:
                                    log.debug('tvdb_season_num %s not in zp_tv_episode_dict %s', tvdb_season_num,
                                              zp_tv_episode_dict)
                            else:
                                log.debug('tvdb_episode_num %s not > 0 and or tvdb_season_num %s not > 0 and or'
                                          ' episode_id %s not > 0', tvdb_episode_num, tvdb_season_num, episode_id)
                        else:
                            log.debug('id and or airedEpisodeNumber and or airedEpisodeNumber not in episode %s',
                                      episode)
                    else:
                        log.warning('episode %s not a dict but %s', episode, type(episode))
            else:
                log.warning('tvdb_episodes %s is empty', tvdb_episodes)
        else:
            log.warning('tvdb_episodes %s not a list but %s', tvdb_episodes, type(tvdb_episodes))
                                        #return_dict[tvdb_season_num][tvdb_episode_num] = episode['id']

        log.debug('return_dict %s', return_dict)
        return return_dict

    def get_tv_season_raw_images(self, tvdb_eid, zp_tv_season_list, lang, image_types, highest_rating=True):
        log.debug("---start get_tv_season_raw_images ---")
        log.debug('zp_tv_season_list %s, lang %s', zp_tv_season_list, lang)
        log.debug('zp_tv_season_list %s', zp_tv_season_list)
        log.debug('image_types %s', image_types)
        image_type_reference_dict = {'poster': 'season'}
        if lang is None:
            kwargs = {'language': ''}
        else:
            kwargs = {'language': lang}
        images_summary = self.tvdb_get_section(tvdb_eid, 'Series_Images', 'summary', **kwargs)
        log.debug('images_summary %s', images_summary)
        # for image_type_image in image_type_images_list:

        # log.debug('image_type_image %s', image_type_image)
        # https://www.evanmiller.org/how-not-to-sort-by-average-rating.html

        # raise SystemExit
        image_types = ['poster']
        return_dict = {}
        if isinstance(images_summary, dict):
            for image_type in image_types:
                if image_type in image_type_reference_dict:
                    if image_type_reference_dict[image_type] in images_summary:
                        if images_summary[image_type_reference_dict[image_type]] > 0:
                            image_type_images_list = self.tvdb_get_section(tvdb_eid, 'Series_Images',
                                                                           image_type_reference_dict[image_type],
                                                                           **kwargs)
                            # log.debug('image_type %s', image_type)
                            if isinstance(image_type_images_list, list):
                                if len(image_type_images_list) > 0:
                                    # first_image = image_type_images_list[0]
                                    for image_type_image in image_type_images_list:
                                        if 'subKey' in image_type_image:
                                            season = int(image_type_image['subKey'])
                                            if season in zp_tv_season_list:
                                                if 'fileName' in image_type_image:
                                                    if season in return_dict:
                                                        if image_type_image['ratingsInfo']['average'] > \
                                                            return_dict[season][image_type]['vote_average']:
                                                            return_dict[season][image_type] = {
                                                                'image_reference': image_type_image['fileName'],
                                                                'image_url': '%s%s' % (tvdb_base_image_url,
                                                                                       image_type_image['fileName']),
                                                                'vote_average': image_type_image['ratingsInfo'][
                                                                    'average']
                                                            }
                                                    else:
                                                        return_dict[season] = {}
                                                        return_dict[season][image_type] = {
                                                            'image_reference': image_type_image['fileName'],
                                                            'image_url': '%s%s' % (tvdb_base_image_url,
                                                                                   image_type_image['fileName']),
                                                            'vote_average': image_type_image['ratingsInfo']['average']
                                                            }
                                                else:
                                                    log.debug('season not in zp_tv_season_list %s', zp_tv_season_list)
                                            else:
                                                log.warning('fileName not in image_type_image %s', image_type_image)
                                        else:
                                            log.warning('subKey not in image_type_image %s', image_type_image)
                                else:
                                    log.warning('image_type_images_list %s is empty', image_type_images_list)
                            else:
                                log.warning('image_types_images_list is not list but %s',
                                          type(image_type_images_list))
                        else:
                            log.warning('image summary key %s not > 0',
                                      images_summary[image_type_reference_dict[image_type]])
                    else:
                        log.warning('%s not in images_summary %s', image_type_reference_dict[image_type],
                                  images_summary)
                else:
                    log.warning('image_type %s not in image_type_reference_dict %s', image_type,
                              image_type_reference_dict)
        else:
            log.warning('images_summary %s is not a dict but %s', images_summary, type(images_summary))

        for season in zp_tv_season_list:
            if season in return_dict:
                for image_type in return_dict[season]:
                    if 'vote_average' in return_dict[season][image_type]:
                        del return_dict[season][image_type]['vote_average']
        log.debug('return_dict %s', return_dict)
        #raise SystemExit
        return return_dict

    def get_tv_show_raw_images(self, tvdb_eid, lang, image_types, highest_rating=True):
        log.debug('image_types %s, lang %s', image_types, lang)
        # raise SystemExit
        image_type_reference_dict = {'backdrop': 'fanart',
                                     'banner': 'series',
                                     'poster': 'poster'}
        if lang is None:
            kwargs = {'language': ''}
        else:
            kwargs = {'language': lang}
        images_summary = self.tvdb_get_section(tvdb_eid, 'Series_Images', 'summary', **kwargs)
        log.debug('images_summary %s', images_summary)
        return_dict = {}
        if isinstance(images_summary, dict):
            for image_type in image_types:
                if image_type in image_type_reference_dict:
                    if image_type_reference_dict[image_type] in images_summary:
                        if images_summary[image_type_reference_dict[image_type]] > 0:
                            image_type_images_list = self.tvdb_get_section(tvdb_eid, 'Series_Images',
                                                                           image_type_reference_dict[image_type],
                                                                           **kwargs)
                            # log.debug('image_type %s', image_type)
                            if isinstance(image_type_images_list, list):
                                if len(image_type_images_list) > 0:
                                    first_image = image_type_images_list[0]
                                    if 'fileName' in first_image:
                                        if first_image:
                                            return_dict[image_type] = {'image_reference': first_image['fileName'],
                                                                       'image_url': '%s%s' % (tvdb_base_image_url,
                                                                                              first_image['fileName'])}
                                    else:
                                        log.warning('filename not in first_image %s', first_image)
                                else:
                                    log.debug('image_type_images_list %s is empty', image_type_images_list)
                            else:
                                log.warning('image_types_images_list is not list but %s',
                                          type(image_type_images_list))
                        else:
                            log.warning('image summary key %s not > 0',
                                      images_summary[image_type_reference_dict[image_type]])
                    else:
                        log.debug('%s not in images_summary %s', image_type_reference_dict[image_type],
                                  images_summary)
                else:
                    log.debug('image_type %s not in image_type_reference_dict %s', image_type,
                              image_type_reference_dict)
        else:
            log.warning('images_summary %s is not a dict but %s', images_summary, type(images_summary))

        log.debug("---end get_tv_raw_images ---")
        return return_dict