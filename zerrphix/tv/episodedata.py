# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import sys

from datetime import datetime
from datetime import timedelta

from sqlalchemy import and_
from sqlalchemy import func, orm

from zerrphix.db import flush, commit
from zerrphix.db.tables import TABLES
from zerrphix.plugin import load_plugins
#from zerrphix.tv.util import eapi_eid_from_zp_tv_id
from zerrphix.util.plugin import create_eapi_plugins_list, create_eapi_dict
from zerrphix.util.text import date_time
#from zerrphix.util import set_retry, get_user_langs, check_can_retry
from zerrphix.tv.util import update_tv_episode_last_mod
#from zerrphix.util import iso_639_part1_from_zp_lang_id
from types import MethodType
from zerrphix.tv.base import TVBase

log = logging.getLogger(__name__)


class EpisodeData(TVBase):
    """Get Data for tvs (actors, runtime, synop etc...)
    """

    def __init__(self, **kwargs):
        """Data __init__

            Args:
                | args (list): Passed through args from the command line.
                | Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.
        """
        super(EpisodeData, self).__init__(**kwargs)
        self, self.eapi_tv_plugins_access_list, loaded_plugins = create_eapi_plugins_list(
            'tv', sys.modules, load_plugins(self.args), self)
        #self.iso_639_part1_from_zp_lang_id = MethodType(iso_639_part1_from_zp_lang_id, self)
        if not self.eapi_tv_plugins_access_list:
            raise Exception(('There not any entries in eapi_tv_plugins_access_list'
                             ' therefore scanning is pointless'))
        session = self.Session()
        self.eapi_dict = create_eapi_dict(session)
        session.close()
        self.library = 'TV'
        #self.get_user_langs = MethodType(get_user_langs, self)
        #self.set_retry = MethodType(set_retry, self)
        #self.check_can_retry = MethodType(check_can_retry, self)


    def get_tv_missing_ep_data_no_retry(self, zp_tv_id, eapi, zp_lang_id):
        """
        SELECT ZP_TV_EPISODE.*, ZP_TV_FILEFOLDER.ZP_TV_ID
        FROM `ZP_TV_EPISODE`, `ZP_TV_FILEFOLDER`
        where ZP_TV_EPISODE.ZP_TV_FILEFOLDER_ID = ZP_TV_FILEFOLDER.ID
        group by ZP_TV_FILEFOLDER.ZP_TV_ID, `SEASON`, `EPISODE`
        order by ZP_TV_FILEFOLDER.ZP_TV_ID asc, SEASON asc, EPISODE asc
        """
        # Get all seaons eps for each show but do not show multiple
        # epidoes for each season
        """
        select ZP_TV_FILEFOLDER.ZP_TV_ID, ZP_TV_EPISODE.SEASON
        from ZP_TV_EPISODE
        join ZP_TV_FILEFOLDER
        on ZP_TV_EPISODE.ZP_TV_FILEFOLDER_ID = ZP_TV_FILEFOLDER.ID
        left outer join ZP_TV_EPISODE_TITLE_XREF
        on (ZP_TV_EPISODE_TITLE_XREF.ZP_TV_ID = ZP_TV_FILEFOLDER.ZP_TV_ID and ZP_TV_EPISODE.SEASON = 
        ZP_TV_EPISODE_TITLE_XREF.SEASON and ZP_TV_EPISODE.EPISODE = ZP_TV_EPISODE_TITLE_XREF.EPISODE)
        left outer join ZP_TV_EPISODE_OVERVIEW_XREF
        on (ZP_TV_EPISODE_OVERVIEW_XREF.ZP_TV_ID = ZP_TV_FILEFOLDER.ZP_TV_ID and ZP_TV_EPISODE.SEASON = 
        ZP_TV_EPISODE_OVERVIEW_XREF.SEASON and ZP_TV_EPISODE.EPISODE = ZP_TV_EPISODE_OVERVIEW_XREF.EPISODE)
        where ZP_TV_EPISODE_TITLE_XREF.ZP_TV_ID is null or ZP_TV_EPISODE_OVERVIEW_XREF.ZP_TV_ID is null
        group by ZP_TV_FILEFOLDER.ZP_TV_ID, ZP_TV_EPISODE.SEASON
        """
        return_list = []
        session = self.Session()
        tv_missing_ep_data_qry = session.query(TABLES.ZP_TV_EPISODE.ZP_TV_ID).outerjoin(
            TABLES.ZP_TV_EPISODE_TITLE,
            and_(TABLES.ZP_TV_EPISODE_TITLE.ZP_TV_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID,
                 TABLES.ZP_TV_EPISODE.SEASON == TABLES.ZP_TV_EPISODE_TITLE.SEASON,
                 TABLES.ZP_TV_EPISODE.EPISODE == TABLES.ZP_TV_EPISODE_TITLE.EPISODE,
                 TABLES.ZP_TV_EPISODE_TITLE.ZP_LANG_ID == zp_lang_id,
                 TABLES.ZP_TV_EPISODE_TITLE.ZP_EAPI_ID == self.eapi_dict[eapi]
                 )).outerjoin(
            TABLES.ZP_TV_EPISODE_OVERVIEW,
            and_(TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_TV_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID,
                 TABLES.ZP_TV_EPISODE.SEASON == TABLES.ZP_TV_EPISODE_OVERVIEW.SEASON,
                 TABLES.ZP_TV_EPISODE.EPISODE == TABLES.ZP_TV_EPISODE_OVERVIEW.EPISODE,
                 TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_LANG_ID == zp_lang_id,
                 TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_EAPI_ID == self.eapi_dict[eapi]
                 )).filter(
            TABLES.ZP_TV_EPISODE.ZP_TV_ID < zp_tv_id,
            ((TABLES.ZP_TV_EPISODE_TITLE.ZP_TV_ID == None) | (
                TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_TV_ID == None)),
            ~TABLES.ZP_TV_EPISODE.ID.in_(session.query(TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == 1,
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 3,
                TABLES.ZP_RETRY.ZP_LANG_ID == zp_lang_id,
                TABLES.ZP_RETRY.ZP_EAPI_ID == self.eapi_dict[eapi]
            ))
        ).group_by(TABLES.ZP_TV_EPISODE.ZP_TV_ID).order_by(
            TABLES.ZP_TV_EPISODE.ZP_TV_ID.desc())
        if tv_missing_ep_data_qry.count() > 0:
            tv_seasons_missing_ep_data = tv_missing_ep_data_qry.limit(100)
            for tv_id in tv_seasons_missing_ep_data:
                return_list.append(tv_id.ZP_TV_ID)
        session.close()
        return return_list

    def get_tv_seasons_missing_ep_data(self, zp_tv_id, eapi, zp_lang_id):
        return_list = []
        session = self.Session()
        tv_seasons_missing_ep_data_qry = session.query(
            TABLES.ZP_TV_EPISODE.SEASON).outerjoin(
            TABLES.ZP_TV_EPISODE_TITLE,
            and_(TABLES.ZP_TV_EPISODE_TITLE.ZP_TV_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID,
                 TABLES.ZP_TV_EPISODE.SEASON == TABLES.ZP_TV_EPISODE_TITLE.SEASON,
                 TABLES.ZP_TV_EPISODE.EPISODE == TABLES.ZP_TV_EPISODE_TITLE.EPISODE,
                 TABLES.ZP_TV_EPISODE_TITLE.ZP_LANG_ID == zp_lang_id,
                 TABLES.ZP_TV_EPISODE_TITLE.ZP_EAPI_ID == self.eapi_dict[eapi]
                 )).outerjoin(
            TABLES.ZP_TV_EPISODE_OVERVIEW,
            and_(
                TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_TV_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID,
                TABLES.ZP_TV_EPISODE.SEASON == TABLES.ZP_TV_EPISODE_OVERVIEW.SEASON,
                TABLES.ZP_TV_EPISODE.EPISODE == TABLES.ZP_TV_EPISODE_OVERVIEW.EPISODE,
                 TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_LANG_ID == zp_lang_id,
                 TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_EAPI_ID == self.eapi_dict[eapi]
            )).filter(
            TABLES.ZP_TV_EPISODE.ZP_TV_ID == zp_tv_id,
            ((TABLES.ZP_TV_EPISODE_TITLE.ZP_TV_ID == None) | (
                TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_TV_ID == None)),
            ~TABLES.ZP_TV_EPISODE.ID.in_(
                session.query(TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                    TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == 1,
                    TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 3,
                    TABLES.ZP_RETRY.ZP_LANG_ID == zp_lang_id,
                    TABLES.ZP_RETRY.ZP_EAPI_ID == self.eapi_dict[eapi],
                ))
        ).group_by(TABLES.ZP_TV_EPISODE.SEASON).order_by(
            TABLES.ZP_TV_EPISODE.SEASON.desc()).all()
        for missing_season in tv_seasons_missing_ep_data_qry:
            return_list.append(missing_season.SEASON)
        session.close()
        return return_list

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
        #log.error('user_langs %s', user_langs)
        #raise SystemExit
        # max_tv_episode_id = session.query(func.max(TABLES.ZP_TV_EPISODE.ID)).one()[0]
        max_tv_id = session.query(func.max(TABLES.ZP_TV.ID)).one()[0]
        session.close()
        if isinstance(max_tv_id, int):
            #data_keys = ['genres', 'name', 'original_name',
            #             'overview', 'first_air_date',
            #             'rating', 'credits']
            # ZP_TV_EPISODE_ID = max_tv_episode_id + 1
            for zp_lang_id in self.user_langs:
                self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                             15,
                                                             'LANG: %s' % self.user_langs[zp_lang_id])
                for eapi in self.eapi_tv_plugins_access_list:
                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                15,
                                                                 'LANG: %s, EAPI: %s' % (
                                                                     self.user_langs[zp_lang_id],
                                                                     eapi
                                                                 ))
                    if hasattr(getattr(self, eapi), 'get_tv_season_data'):
                        zp_tv_id = max_tv_id + 1
                        lang_processing_complete = False
                        while lang_processing_complete is False:
                            tv_id_list = self.get_tv_missing_ep_data_no_retry(zp_tv_id, eapi, zp_lang_id)
                            log.debug('not retry zp_lang_id %s, tv_id_list %s, eapi %s', zp_lang_id, tv_id_list, eapi)
                            if tv_id_list:
                                for tv in reversed(sorted(tv_id_list)):
                                    zp_tv_id = tv
                                    missing_season_list = self.get_tv_seasons_missing_ep_data(zp_tv_id, eapi,
                                                                                              zp_lang_id)
                                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                                 5,
                                                                                 'LANG: %s EAPI: %s TV: %s/%s' % (
                                                                                     self.user_langs[zp_lang_id],
                                                                                     eapi,
                                                                                     zp_tv_id,
                                                                                     max_tv_id
                                                                                 ))
                                    for season in missing_season_list:
                                        self.get_season_episode_data(tv, eapi, zp_lang_id, season)
                                        self.set_retry_for_missing_epiosde_data(tv, eapi, zp_lang_id, season)
                            else:
                                lang_processing_complete = True
                    else:
                        log.info('eapi %s does not have get_tv_show_data', eapi)
            # print(max_tv_episode_id)
            if self.check_can_retry(1) is True:
                log.debug('Retrying TV Episode Data')
                for zp_lang_id in self.user_langs:
                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                             15,
                                                             'LANG: %s' % self.user_langs[zp_lang_id])
                    for eapi in self.eapi_tv_plugins_access_list:
                        self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                15,
                                                                 'LANG: %s, EAPI: %s' % (
                                                                     self.user_langs[zp_lang_id],
                                                                     eapi
                                                                 ))
                        if hasattr(getattr(self, eapi), 'get_tv_season_data'):
                            zp_tv_id = max_tv_id + 1
                            lang_processing_complete = False
                            while lang_processing_complete is False:
                                tv_id_list = self.get_tv_retry(zp_tv_id, eapi, zp_lang_id)
                                log.debug('retry zp_lang_id %s, tv_id_list %s, eapi %s', zp_lang_id, tv_id_list, eapi)
                                if tv_id_list:
                                    # todo this needs to have retry code
                                    for tv_id in tv_id_list:
                                        zp_tv_id = tv_id
                                        self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                                 5,
                                                                                 'LANG: %s EAPI: %s TV: %s/%s' % (
                                                                                     self.user_langs[zp_lang_id],
                                                                                     eapi,
                                                                                     zp_tv_id,
                                                                                     max_tv_id
                                                                                 ))
                                        tv_seasons = self.get_tv_seaons_retry(tv_id, eapi, zp_lang_id)
                                        for season in tv_seasons:
                                            self.get_season_episode_data(tv_id, eapi, zp_lang_id, season)
                                            self.set_retry_for_missing_epiosde_data(tv_id, eapi, zp_lang_id, season)
                                    #raise SystemExit
                                else:
                                    lang_processing_complete = True
                        else:
                            log.info('eapi %s does not have get_tv_show_data', eapi)

    def get_tv_seaons_retry(self, zp_tv_id, eapi, zp_lang_id):
        session = self.Session()
        tv_episode_missing_ep_data_qry = session.query(TABLES.ZP_TV_EPISODE.SEASON,
                                                       TABLES.ZP_TV_EPISODE.ID.label('ZP_TV_EPISODE_ID'),
                                                       TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID,
                                                       TABLES.ZP_RETRY.DATETIME,
                                                       TABLES.ZP_RETRY.COUNT,
                                                       TABLES.ZP_RETRY_COUNT.DELAY).join(
            TABLES.ZP_RETRY, and_(TABLES.ZP_TV_EPISODE.ID == TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID,
                                  TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == 1,
                                  TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 3,
                                  TABLES.ZP_RETRY.ZP_LANG_ID == zp_lang_id,
                                  TABLES.ZP_RETRY.ZP_EAPI_ID == self.eapi_dict[eapi])
            ).join(TABLES.ZP_RETRY_COUNT, TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == TABLES.ZP_RETRY_COUNT.ZP_RETRY_TYPE_ID
        ).outerjoin(
            TABLES.ZP_TV_EPISODE_TITLE,
            and_(TABLES.ZP_TV_EPISODE_TITLE.ZP_TV_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID,
                 TABLES.ZP_TV_EPISODE.SEASON == TABLES.ZP_TV_EPISODE_TITLE.SEASON,
                 TABLES.ZP_TV_EPISODE.EPISODE == TABLES.ZP_TV_EPISODE_TITLE.EPISODE,
                 TABLES.ZP_TV_EPISODE_TITLE.ZP_LANG_ID == zp_lang_id,
                 TABLES.ZP_TV_EPISODE_TITLE.ZP_EAPI_ID == self.eapi_dict[eapi]
                 )).outerjoin(
            TABLES.ZP_TV_EPISODE_OVERVIEW,
            and_(TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_TV_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID,
                 TABLES.ZP_TV_EPISODE.SEASON == TABLES.ZP_TV_EPISODE_OVERVIEW.SEASON,
                 TABLES.ZP_TV_EPISODE.EPISODE == TABLES.ZP_TV_EPISODE_OVERVIEW.EPISODE,
                 TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_LANG_ID == zp_lang_id,
                 TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_EAPI_ID == self.eapi_dict[eapi]
                 )).filter(
            TABLES.ZP_TV_EPISODE.ZP_TV_ID == zp_tv_id,
            ((TABLES.ZP_TV_EPISODE_TITLE.ZP_TV_ID == None) | (
                TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_TV_ID == None)),
                TABLES.ZP_RETRY_COUNT.COUNT == session.query(
                    func.max(TABLES.ZP_RETRY_COUNT.COUNT)
                ).filter(
                    TABLES.ZP_RETRY.COUNT >= TABLES.ZP_RETRY_COUNT.COUNT).order_by(
                    TABLES.ZP_RETRY_COUNT.COUNT.desc()).correlate(TABLES.ZP_RETRY).as_scalar()
        ).order_by(TABLES.ZP_TV_EPISODE.SEASON.desc()).all()
        season_list = []
        for tv_episode in tv_episode_missing_ep_data_qry:
            if tv_episode.DATETIME + timedelta(days=tv_episode.DELAY) <= datetime.now():
                log.debug('dt %s, plus %s is %s which is less than than now %s',
                          tv_episode.DATETIME,
                          tv_episode.DELAY,
                          tv_episode.DATETIME + timedelta(days=tv_episode.DELAY),
                          datetime.now())
                if tv_episode.SEASON not in season_list:
                    season_list.append(tv_episode.SEASON)
            else:
                log.debug('dt %s, plus %s is %s which is less than than now %s',
                          tv_episode.DATETIME,
                          tv_episode.DELAY,
                          tv_episode.DATETIME + timedelta(days=tv_episode.DELAY),
                          datetime.now())
        #raise SystemExit
        session.close()
        return season_list

    def get_tv_retry(self, zp_tv_id, eapi, zp_lang_id):
        session = self.Session()
        tv_missing_ep_data_qry = session.query(TABLES.ZP_TV_EPISODE.ZP_TV_ID).outerjoin(
            TABLES.ZP_TV_EPISODE_TITLE,
            and_(TABLES.ZP_TV_EPISODE_TITLE.ZP_TV_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID,
                 TABLES.ZP_TV_EPISODE.SEASON == TABLES.ZP_TV_EPISODE_TITLE.SEASON,
                 TABLES.ZP_TV_EPISODE.EPISODE == TABLES.ZP_TV_EPISODE_TITLE.EPISODE,
                 TABLES.ZP_TV_EPISODE_TITLE.ZP_LANG_ID == zp_lang_id,
                 TABLES.ZP_TV_EPISODE_TITLE.ZP_EAPI_ID == self.eapi_dict[eapi]
                 )).outerjoin(
            TABLES.ZP_TV_EPISODE_OVERVIEW,
            and_(TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_TV_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID,
                 TABLES.ZP_TV_EPISODE.SEASON == TABLES.ZP_TV_EPISODE_OVERVIEW.SEASON,
                 TABLES.ZP_TV_EPISODE.EPISODE == TABLES.ZP_TV_EPISODE_OVERVIEW.EPISODE,
                 TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_LANG_ID == zp_lang_id,
                 TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_EAPI_ID == self.eapi_dict[eapi]
                 )).filter(
            TABLES.ZP_TV_EPISODE.ZP_TV_ID < zp_tv_id,
            ((TABLES.ZP_TV_EPISODE_TITLE.ZP_TV_ID == None) | (
                TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_TV_ID == None)),
            TABLES.ZP_TV_EPISODE.ID.in_(session.query(TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == 1,
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 3
            ))
        ).group_by(TABLES.ZP_TV_EPISODE.ZP_TV_ID).order_by(
            TABLES.ZP_TV_EPISODE.ZP_TV_ID.desc())
        tv_id_list = []
        for tv_id in tv_missing_ep_data_qry:
            tv_id_list.append(tv_id.ZP_TV_ID)
        session.close()
        return tv_id_list

    def get_season_episode_data(self, zp_tv_id, eapi, zp_lang_id, SEASON):
        if zp_lang_id is None:
            iso_639_part1 = None
        else:
            iso_639_part1 = self.iso_639_part1_from_zp_lang_id(zp_lang_id)
        try:
            tv_eapi_eid = self.eapi_eid_from_zp_tv_id(self.eapi_dict[eapi], zp_tv_id)
        except orm.exc.NoResultFound as e:
            log.warning(('zp_tv_id: {0} with self.eapi_dict[eapi]: {1} not in ZP_TV_EAPI_EID').format(
                zp_tv_id,
                self.eapi_dict[eapi]))
        else:
            tv_season_data = getattr(self, eapi).get_tv_season_data(tv_eapi_eid, SEASON, language=iso_639_part1)
            if isinstance(tv_season_data, dict):
                if 'episodes' in tv_season_data.keys():
                    if tv_season_data['episodes']:
                        for episode in tv_season_data['episodes']:
                            if 'episode_number' in episode.keys():
                                if 'overview' in episode.keys():
                                    if episode['overview']:
                                        self.process_tv_ep_overview(zp_tv_id, SEASON, episode['episode_number'],
                                                                    episode['overview'], eapi, zp_lang_id)
                                    else:
                                        log.warning(
                                            ('overview empty: {0} for eapi: {1}, self.eapi_dict[eapi]: {2},'
                                             ' eid: {6}, SEASON: {3}, EPISODE: {4}, zp_tv_id: {5}').format(
                                                episode['overview'],
                                                eapi,
                                                self.eapi_dict[eapi],
                                                SEASON,
                                                episode['episode_number'],
                                                zp_tv_id,
                                                tv_eapi_eid))
                                else:
                                    log.warning((
                                                'overview not in episode.keys(): {0} for eapi: {1}, '
                                                'self.eapi_dict[eapi]: {2},'
                                                ' eid: {6}, SEASON: {3}, EPISODE: {4}, zp_tv_id: {5}').format(
                                        episode.keys(),
                                        eapi,
                                        self.eapi_dict[eapi],
                                        SEASON,
                                        episode['episode_number'],
                                        zp_tv_id,
                                        tv_eapi_eid))
                                if 'name' in episode.keys():
                                    if episode['name']:
                                        self.process_tv_ep_title(zp_tv_id, SEASON, episode['episode_number'],
                                                                 episode['name'], eapi, zp_lang_id)
                                    else:
                                        log.warning(('name empty: {0} for eapi: {1}, self.eapi_dict[eapi]: {2},'
                                                     ' eid: {6}, SEASON: {3}, EPISODE: {4}, '
                                                     'zp_tv_id: {5}').format(
                                            episode['name'],
                                            eapi,
                                            self.eapi_dict[eapi],
                                            SEASON,
                                            episode['episode_number'],
                                            zp_tv_id,
                                            tv_eapi_eid))
                                else:
                                    log.warning((
                                                'name not in episode.keys(): {0} for eapi: {1}, '
                                                'self.eapi_dict[eapi]: {2},'
                                                ' eid: {6}, SEASON: {3}, EPISODE: {4}, zp_tv_id: {5}').format(
                                        episode.keys(),
                                        eapi,
                                        self.eapi_dict[eapi],
                                        SEASON,
                                        episode['episode_number'],
                                        zp_tv_id,
                                        tv_eapi_eid))
                            else:
                                log.warning('episode_number not in episode.keys(): {0}'.format(episode.keys()))
                    else:
                        log.warning(
                            '''tv_season_data['episodes']: {0} is empty'''.format(tv_season_data['episodes']))
                else:
                    log.warning(('episodes not in tv_season_data.keys(): {0}').format(tv_season_data.keys()))
            else:
                log.warning('tv_season_data is not dict but {0}'.format(type(tv_season_data)))

            if self.check_for_missing_episode_data(zp_tv_id, eapi, zp_lang_id, SEASON) == False:
                log.debug(
                    'All epsidoes for zp_tv_id: {0} and SEASON: {1} and ZP_LANG_ID: {2} '
                    'have overview and title.'.format(
                        zp_tv_id,
                        SEASON,
                        zp_lang_id))
                # raise SystemExit
                return
            else:
                log.debug(
                    'Not all epsidoes for zp_tv_id: {0} and SEASON: {1} and ZP_LANG_ID: {2} '
                    'have overview and title.'.format(
                        zp_tv_id,
                        SEASON,
                        zp_lang_id))
                # raise SystemExit
                # time.sleep(5)

    def set_retry_for_missing_epiosde_data(self, zp_tv_id, eapi, zp_lang_id, SEASON):
        session = self.Session()
        episodes_missing_data = session.query(TABLES.ZP_TV_EPISODE.ID).outerjoin(
            TABLES.ZP_TV_EPISODE_TITLE,
            and_(TABLES.ZP_TV_EPISODE_TITLE.ZP_TV_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID,
                 TABLES.ZP_TV_EPISODE.SEASON == TABLES.ZP_TV_EPISODE_TITLE.SEASON,
                 TABLES.ZP_TV_EPISODE.EPISODE == TABLES.ZP_TV_EPISODE_TITLE.EPISODE,
                 TABLES.ZP_TV_EPISODE_TITLE.ZP_LANG_ID == zp_lang_id,
                 TABLES.ZP_TV_EPISODE_TITLE.ZP_EAPI_ID == self.eapi_dict[eapi]
                 )).outerjoin(
            TABLES.ZP_TV_EPISODE_OVERVIEW,
            and_(TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_TV_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID,
                 TABLES.ZP_TV_EPISODE.SEASON == TABLES.ZP_TV_EPISODE_OVERVIEW.SEASON,
                 TABLES.ZP_TV_EPISODE.EPISODE == TABLES.ZP_TV_EPISODE_OVERVIEW.EPISODE,
                 TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_LANG_ID == zp_lang_id,
                 TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_EAPI_ID == self.eapi_dict[eapi]
                 )).filter(
            TABLES.ZP_TV_EPISODE.ZP_TV_ID == zp_tv_id,
            TABLES.ZP_TV_EPISODE.SEASON == SEASON,
            ((TABLES.ZP_TV_EPISODE_TITLE.ZP_TV_ID == None) | (
                TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_TV_ID == None))
        ).all()
        episodes = []
        for ZP_TV_EPISODE in episodes_missing_data:
            episodes.append(ZP_TV_EPISODE.ID)
        session.close()
        for id in episodes:
            #log.error(id)
            #self.set_retry_for_missing_epiosde_data(id)
            self.set_retry(1, 3, id, self.eapi_dict[eapi], zp_lang_id)

    def check_for_missing_episode_data(self, zp_tv_id, eapi, zp_lang_id, SEASON):
        # season_missing_data = True
        session = self.Session()
        try:
            session.query(TABLES.ZP_TV_EPISODE.SEASON, TABLES.ZP_TV_EPISODE.ZP_TV_ID).outerjoin(
                TABLES.ZP_TV_EPISODE_TITLE,
                and_(TABLES.ZP_TV_EPISODE_TITLE.ZP_TV_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID,
                     TABLES.ZP_TV_EPISODE.SEASON == TABLES.ZP_TV_EPISODE_TITLE.SEASON,
                     TABLES.ZP_TV_EPISODE.EPISODE == TABLES.ZP_TV_EPISODE_TITLE.EPISODE,
                     TABLES.ZP_TV_EPISODE_TITLE.ZP_LANG_ID == zp_lang_id,
                     TABLES.ZP_TV_EPISODE_TITLE.ZP_EAPI_ID == self.eapi_dict[eapi]
                )).outerjoin(
                TABLES.ZP_TV_EPISODE_OVERVIEW,
                and_(TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_TV_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID,
                     TABLES.ZP_TV_EPISODE.SEASON == TABLES.ZP_TV_EPISODE_OVERVIEW.SEASON,
                     TABLES.ZP_TV_EPISODE.EPISODE == TABLES.ZP_TV_EPISODE_OVERVIEW.EPISODE,
                     TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_LANG_ID == zp_lang_id,
                     TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_EAPI_ID == self.eapi_dict[eapi]
                )).filter(
                TABLES.ZP_TV_EPISODE.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_TV_EPISODE.SEASON == SEASON,
                ((TABLES.ZP_TV_EPISODE_TITLE.ZP_TV_ID == None) | (
                TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_TV_ID == None)),
                ~TABLES.ZP_TV_EPISODE.ID.in_(session.query(TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                    TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == 1,
                    TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 3
                ))
            ).group_by(TABLES.ZP_TV_EPISODE.ZP_TV_ID, TABLES.ZP_TV_EPISODE.SEASON).order_by(
                TABLES.ZP_TV_EPISODE.ZP_TV_ID.desc(), TABLES.ZP_TV_EPISODE.SEASON.asc()).one()
        except orm.exc.NoResultFound as e:
            season_missing_data = False
        except orm.exc.MultipleResultsFound as e:
            season_missing_data = True
        else:
            season_missing_data = True
        session.close()
        return season_missing_data

    def process_tv_ep_overview(self, zp_tv_id, SEASON, EPISODE, overview, eapi, ZP_LANG_ID):
        session = self.Session()
        try:
            session.query(
                TABLES.ZP_TV_EPISODE_OVERVIEW).filter(
                TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_TV_EPISODE_OVERVIEW.SEASON == SEASON,
                TABLES.ZP_TV_EPISODE_OVERVIEW.EPISODE == EPISODE,
                TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_EAPI_ID == self.eapi_dict[eapi],
                TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_LANG_ID == ZP_LANG_ID).one()
        except orm.exc.NoResultFound as e:
            add_tv_episode_overview = TABLES.ZP_TV_EPISODE_OVERVIEW(ZP_TV_ID=zp_tv_id,
                                                        OVERVIEW=overview,
                                                        ZP_LANG_ID=ZP_LANG_ID,
                                                        ZP_EAPI_ID=self.eapi_dict[eapi],
                                                        SEASON=SEASON,
                                                        EPISODE=EPISODE)

            session.add(add_tv_episode_overview)
            commit(session)
            update_tv_episode_last_mod(self.Session, zp_tv_id, SEASON, EPISODE)
        session.close()

    def process_tv_ep_title(self, zp_tv_id, SEASON, EPISODE, title, eapi, ZP_LANG_ID):
        session = self.Session()
        try:
            session.query(
                TABLES.ZP_TV_EPISODE_TITLE).filter(
                TABLES.ZP_TV_EPISODE_TITLE.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_TV_EPISODE_TITLE.SEASON == SEASON,
                TABLES.ZP_TV_EPISODE_TITLE.EPISODE == EPISODE,
                TABLES.ZP_TV_EPISODE_TITLE.ZP_EAPI_ID == self.eapi_dict[eapi],
                TABLES.ZP_TV_EPISODE_TITLE.ZP_LANG_ID == ZP_LANG_ID).one()
        except orm.exc.NoResultFound:
            add_tv_episode_title = TABLES.ZP_TV_EPISODE_TITLE(ZP_TV_ID=zp_tv_id,
                                                        TITLE=title,
                                                        ZP_LANG_ID=ZP_LANG_ID,
                                                        ZP_EAPI_ID=self.eapi_dict[eapi],
                                                        SEASON=SEASON,
                                                        EPISODE=EPISODE)

            session.add(add_tv_episode_title)
            commit(session)
            update_tv_episode_last_mod(self.Session, zp_tv_id, SEASON, EPISODE)
        session.close()
