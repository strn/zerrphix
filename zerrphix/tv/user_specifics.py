# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging

from sqlalchemy import func, orm, tuple_

from zerrphix.db import commit
from zerrphix.db.tables import TABLES
#from zerrphix.tv.util import update_tv_last_mod
from zerrphix.tv.util import (user_tv_title, user_tv_overview, user_tv_raw_image, user_tv_season_raw_image,
                              user_tv_episode_raw_image, user_tv_episode_title, user_tv_episode_overview)
from zerrphix.util.text import date_time

from zerrphix.tv.base import TVBase
log = logging.getLogger(__name__)


class User_Specifics(TVBase):
    """
    """

    def __init__(self, **kwargs):
        super(User_Specifics, self).__init__(**kwargs)

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
                                                                     16,
                                                                     'User %s/%s' % (
                                                                         zp_user_id, max_user_id
                                                                     ))
                        self.process_user(zp_user_id)
                else:
                    user_processing_complete = True
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

    def process_user(self, zp_user_id):
        session = self.Session()
        eapi_order, title_type_order, lang_list = self.user_prefs(self.library_config_dict['id'], zp_user_id)
        self.process_user_tv(zp_user_id, eapi_order, title_type_order, lang_list)
        self.process_user_tv_season(zp_user_id, eapi_order, title_type_order, lang_list)
        self.process_user_tv_episode(zp_user_id, eapi_order, title_type_order, lang_list)
        #self.process_user_tv_collection(zp_user_id, eapi_order, title_type_order, lang_list)
        session.close()

    def process_user_tv(self, zp_user_id, eapi_order, title_type_order, lang_list):
        session = self.Session()
        max_tv_id = session.query(func.max(TABLES.ZP_TV.ID)).one()[0]
        session.close()
        zp_tv_entity_type_list = [1,2,3,4,5]
        if isinstance(max_tv_id, int):
            for zp_tv_entity_type_id in zp_tv_entity_type_list:
                zp_tv_id = max_tv_id + 1
                self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                             16,
                                                             'User %s, TV %s/%s' % (
                                                                 zp_user_id, zp_tv_id, max_tv_id
                                                             ))
                user_tv_processing_complete = False
                while user_tv_processing_complete is False:
                    tv_processing_list = self.get_tv_processing_list(zp_user_id, zp_tv_id,
                                                                         zp_tv_entity_type_id)
                    if tv_processing_list:
                        for tv_processing_id in tv_processing_list:
                            zp_tv_id = tv_processing_id
                            self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                             16,
                                                             'User %s, TV %s/%s' % (
                                                                 zp_user_id, zp_tv_id, max_tv_id
                                                             ))
                            if zp_tv_entity_type_id == 1:
                                self.process_user_tv_title(zp_user_id, zp_tv_id, eapi_order, title_type_order,
                                                             lang_list, zp_tv_entity_type_id)
                            elif zp_tv_entity_type_id == 2:
                                self.process_user_tv_overview(zp_user_id, zp_tv_id, eapi_order, title_type_order,
                                                             lang_list, zp_tv_entity_type_id)
                            elif zp_tv_entity_type_id == 3:
                                self.process_user_tv_raw_image(zp_user_id, zp_tv_id, eapi_order, lang_list,
                                                                 1, zp_tv_entity_type_id)
                            elif zp_tv_entity_type_id == 4:
                                self.process_user_tv_raw_image(zp_user_id, zp_tv_id, eapi_order, lang_list,
                                                                 2, zp_tv_entity_type_id)
                            elif zp_tv_entity_type_id == 5:
                                self.process_user_tv_raw_image(zp_user_id, zp_tv_id, eapi_order, lang_list,
                                                                 3, zp_tv_entity_type_id)
                    else:
                        user_tv_processing_complete = True

    def process_user_tv_season(self, zp_user_id, eapi_order, title_type_order, lang_list):
        session = self.Session()
        max_tv_id = session.query(func.max(TABLES.ZP_TV.ID)).one()[0]
        session.close()
        zp_tv_entity_type_list = [1]
        if isinstance(max_tv_id, int):
            for zp_tv_entity_type_id in zp_tv_entity_type_list:
                zp_tv_id = max_tv_id + 1
                user_tv_processing_complete = False
                while user_tv_processing_complete is False:
                    tv_processing_list = self.get_tv_season_processing_list(zp_user_id, zp_tv_id,
                                                                         zp_tv_entity_type_id)
                    if tv_processing_list:
                        for tv_processing_id in tv_processing_list:
                            zp_tv_id = tv_processing_id
                            #if zp_tv_entity_type_id == 1:
                            tv_season_processing_list = self.get_tv_season_actual_processing_list(zp_user_id,
                                                                                                  zp_tv_id,
                                                                      zp_tv_entity_type_id)
                            for season in tv_season_processing_list:
                                if zp_tv_entity_type_id == 1:
                                    self.process_user_tv_season_raw_image(zp_user_id, zp_tv_id, season, eapi_order,

                                                               lang_list, 1, zp_tv_entity_type_id)
                            #raise SystemExit
                    else:
                        user_tv_processing_complete = True


    def process_user_tv_episode(self, zp_user_id, eapi_order, title_type_order, lang_list):
        session = self.Session()
        max_tv_id = session.query(func.max(TABLES.ZP_TV.ID)).one()[0]
        session.close()
        zp_tv_entity_type_list = [3,2,1]
        if isinstance(max_tv_id, int):
            for zp_tv_entity_type_id in zp_tv_entity_type_list:
                zp_tv_id = max_tv_id + 1
                user_tv_processing_complete = False
                while user_tv_processing_complete is False:
                    tv_processing_list = self.get_tv_episode_processing_list(zp_user_id, zp_tv_id,
                                                                         zp_tv_entity_type_id)
                    if tv_processing_list:
                        for tv_processing_id in tv_processing_list:
                            zp_tv_id = tv_processing_id
                            #if zp_tv_entity_type_id == 1:
                            tv_season_processing_list = self.get_tv_episode_actual_processing_list(zp_user_id,
                                                                                                  zp_tv_id,
                                                                      zp_tv_entity_type_id)
                            for episode in tv_season_processing_list:
                                if zp_tv_entity_type_id == 1:
                                    self.process_user_tv_episode_title(zp_user_id, zp_tv_id, episode[0], episode[1],
                                                                       eapi_order,
                                                                       title_type_order,
                                                             lang_list, zp_tv_entity_type_id)
                                if zp_tv_entity_type_id == 2:
                                    self.process_user_tv_episode_overview(zp_user_id, zp_tv_id, episode[0], episode[1],
                                                                          eapi_order,
                                                                          title_type_order,
                                                             lang_list, zp_tv_entity_type_id)
                                if zp_tv_entity_type_id == 3:
                                    self.process_user_tv_episode_raw_image(zp_user_id, zp_tv_id, episode[0], episode[1],
                                                                           eapi_order,
                                                               lang_list, 4, zp_tv_entity_type_id)
                            #raise SystemExit
                    else:
                        user_tv_processing_complete = True

    def get_tv_episode_processing_list(self, zp_user_id, zp_tv_id, zp_tv_entity_type_id):
        session = self.Session()
        return_list = []
        qry_tv_missing_raw_eapi_image = session.query(
            TABLES.ZP_TV.ID.distinct().label('ID')
        ).filter(
            TABLES.ZP_TV_EPISODE.ZP_TV_ID == TABLES.ZP_TV.ID,
            TABLES.ZP_TV.ID < zp_tv_id,
            ~TABLES.ZP_TV.ID.in_(
                session.query(TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID).filter(
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == zp_tv_entity_type_id,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON == TABLES.ZP_TV_EPISODE.SEASON,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE == TABLES.ZP_TV_EPISODE.EPISODE,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.LAST_UPDATE_DATETIME >= TABLES.ZP_TV.LAST_EDIT_DATETIME,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV.ID,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_USER_ID == zp_user_id
                ).group_by(
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID
                ).having(
                    func.count() < session.query(func.count(TABLES.ZP_TV_EPISODE.EPISODE).label('E_COUNT')
                                                 ).filter(
                        TABLES.ZP_TV_EPISODE.ZP_TV_ID == TABLES.ZP_TV.ID
                    ).correlate(TABLES.ZP_TV).as_scalar()
                )
            ),
            ~TABLES.ZP_TV.ID.in_(
                session.query(TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID).filter(
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == zp_tv_entity_type_id,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON == TABLES.ZP_TV_EPISODE.SEASON,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE == TABLES.ZP_TV_EPISODE.EPISODE,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV.ID,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.FORCED == 1,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_USER_ID == zp_user_id
                ).group_by(
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID
                ).having(
                    func.count() < session.query(func.count(TABLES.ZP_TV_EPISODE.EPISODE).label('E_COUNT')
                                                 ).filter(
                        TABLES.ZP_TV_EPISODE.ZP_TV_ID == TABLES.ZP_TV.ID
                    ).correlate(TABLES.ZP_TV).as_scalar()
                )
            )
        )

        qry_tv_missing_raw_eapi_image_count = qry_tv_missing_raw_eapi_image.count()
        log.debug('qry_tv_missing_raw_eapi_image_count no retry: %s', qry_tv_missing_raw_eapi_image_count)
        if qry_tv_missing_raw_eapi_image_count > 0:
            tv_missing_raw_eapi_image = qry_tv_missing_raw_eapi_image.order_by(
                TABLES.ZP_TV.ID.desc()).limit(50)
            for tv in tv_missing_raw_eapi_image:
                return_list.append(tv.ID)
        session.close()
        log.debug(return_list)
        #raise SystemExit
        return return_list

    def get_tv_episode_actual_processing_list(self, zp_user_id, zp_tv_id, zp_tv_entity_type_id):
        session = self.Session()
        return_list = []
        qry_tv_missing_raw_eapi_image = session.query(
            TABLES.ZP_TV_EPISODE.SEASON, TABLES.ZP_TV_EPISODE.EPISODE
        ).filter(
            TABLES.ZP_TV_EPISODE.ZP_TV_ID == TABLES.ZP_TV.ID,
            TABLES.ZP_TV.ID == zp_tv_id,
            ~tuple_(TABLES.ZP_TV_EPISODE.SEASON,TABLES.ZP_TV_EPISODE.EPISODE).in_(
                session.query(TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON,
                              TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE).filter(
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == zp_tv_entity_type_id,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON == TABLES.ZP_TV_EPISODE.SEASON,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE == TABLES.ZP_TV_EPISODE.EPISODE,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.LAST_UPDATE_DATETIME >= TABLES.ZP_TV.LAST_EDIT_DATETIME,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV.ID
                )
            ),
            ~tuple_(TABLES.ZP_TV_EPISODE.SEASON,TABLES.ZP_TV_EPISODE.EPISODE).in_(
                session.query(TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON,
                              TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE).filter(
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == zp_tv_entity_type_id,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON == TABLES.ZP_TV_EPISODE.SEASON,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE == TABLES.ZP_TV_EPISODE.EPISODE,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.FORCED == 1,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV.ID
                )
            )
        )

        qry_tv_missing_raw_eapi_image_count = qry_tv_missing_raw_eapi_image.count()
        log.debug('qry_tv_missing_raw_eapi_image_count no retry: %s', qry_tv_missing_raw_eapi_image_count)
        if qry_tv_missing_raw_eapi_image_count > 0:
            tv_missing_raw_eapi_image = qry_tv_missing_raw_eapi_image.order_by(
                TABLES.ZP_TV_EPISODE.SEASON.asc()).all()
            for tv in tv_missing_raw_eapi_image:
                return_list.append((tv.SEASON, tv.EPISODE))
        session.close()
        log.debug(return_list)
        #raise SystemExit
        return return_list

    def get_tv_season_processing_list(self, zp_user_id, zp_tv_id, zp_tv_entity_type_id):
        session = self.Session()
        return_list = []
        qry_tv_missing_raw_eapi_image = session.query(
            TABLES.ZP_TV.ID.distinct().label('ID')
        ).filter(
            TABLES.ZP_TV_EPISODE.ZP_TV_ID == TABLES.ZP_TV.ID,
            TABLES.ZP_TV.ID < zp_tv_id,
            ~TABLES.ZP_TV.ID.in_(
                session.query(TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_TV_ID).filter(
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == zp_tv_entity_type_id,
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.SEASON == TABLES.ZP_TV_EPISODE.SEASON,
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.LAST_UPDATE_DATETIME >= TABLES.ZP_TV.LAST_EDIT_DATETIME,
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV.ID,
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_USER_ID == zp_user_id
                ).group_by(
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID
                ).having(
                    func.count() < session.query(func.count(TABLES.ZP_TV_EPISODE.SEASON.distinct()).label('E_COUNT')
                                                 ).filter(
                        TABLES.ZP_TV_EPISODE.ZP_TV_ID == TABLES.ZP_TV.ID
                    ).correlate(TABLES.ZP_TV).as_scalar()
                )
            ),
            ~TABLES.ZP_TV.ID.in_(
                session.query(TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_TV_ID).filter(
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == zp_tv_entity_type_id,
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.SEASON == TABLES.ZP_TV_EPISODE.SEASON,
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.FORCED == 1,
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV.ID,
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_USER_ID == zp_user_id
                ).group_by(
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID
                ).having(
                    func.count() < session.query(func.count(TABLES.ZP_TV_EPISODE.SEASON.distinct()).label('E_COUNT')
                                                 ).filter(
                        TABLES.ZP_TV_EPISODE.ZP_TV_ID == TABLES.ZP_TV.ID
                    ).correlate(TABLES.ZP_TV).as_scalar()
                )
            )
        )

        qry_tv_missing_raw_eapi_image_count = qry_tv_missing_raw_eapi_image.count()
        log.debug('qry_tv_missing_raw_eapi_image_count no retry: %s', qry_tv_missing_raw_eapi_image_count)
        if qry_tv_missing_raw_eapi_image_count > 0:
            tv_missing_raw_eapi_image = qry_tv_missing_raw_eapi_image.order_by(
                TABLES.ZP_TV.ID.desc()).limit(50)
            for tv in tv_missing_raw_eapi_image:
                return_list.append(tv.ID)
        session.close()
        log.debug(return_list)
        # raise SystemExit
        return return_list

    def get_tv_season_actual_processing_list(self, zp_user_id, zp_tv_id, zp_tv_entity_type_id):
        session = self.Session()
        return_list = []
        qry_tv_missing_raw_eapi_image = session.query(
            TABLES.ZP_TV_EPISODE.SEASON.distinct().label('SEASON')
        ).filter(
            TABLES.ZP_TV_EPISODE.ZP_TV_ID == TABLES.ZP_TV.ID,
            TABLES.ZP_TV.ID == zp_tv_id,
            ~TABLES.ZP_TV_EPISODE.SEASON.in_(
                session.query(TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.SEASON).filter(
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == zp_tv_entity_type_id,
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.SEASON == TABLES.ZP_TV_EPISODE.SEASON,
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.LAST_UPDATE_DATETIME >= TABLES.ZP_TV.LAST_EDIT_DATETIME,
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV.ID)
            ),
            ~TABLES.ZP_TV_EPISODE.SEASON.in_(
                session.query(TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.SEASON).filter(
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == zp_tv_entity_type_id,
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.SEASON == TABLES.ZP_TV_EPISODE.SEASON,
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.FORCED == 1,
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV.ID)
            )
        )

        qry_tv_missing_raw_eapi_image_count = qry_tv_missing_raw_eapi_image.count()
        log.debug('qry_tv_missing_raw_eapi_image_count no retry: %s', qry_tv_missing_raw_eapi_image_count)
        if qry_tv_missing_raw_eapi_image_count > 0:
            tv_missing_raw_eapi_image = qry_tv_missing_raw_eapi_image.order_by(
                TABLES.ZP_TV_EPISODE.SEASON.asc()).all()
            for tv in tv_missing_raw_eapi_image:
                return_list.append(tv.SEASON)
        session.close()
        log.debug(return_list)
        #raise SystemExit
        return return_list

    def get_tv_processing_list(self, zp_user_id, zp_tv_id, zp_tv_entity_type):
        return_list = []
        session = self.Session()
        qry_tv = session.query(TABLES.ZP_TV).filter(
            TABLES.ZP_TV.ID < zp_tv_id,
            ~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID
                ).filter(
                    TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                    TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == zp_tv_entity_type,
                    TABLES.ZP_USER_TV_ENTITY_XREF.LAST_UPDATE_DATETIME >= TABLES.ZP_TV.LAST_EDIT_DATETIME,
                    TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV.ID
                )),
            ~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID
                ).filter(
                    TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                    TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == zp_tv_entity_type,
                    TABLES.ZP_USER_TV_ENTITY_XREF.FORCED == 1,
                    TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV.ID
                ))
        )
        if qry_tv.count() > 0:
            tvs = qry_tv.order_by(TABLES.ZP_TV.ID.desc()).limit(100)
            for tv in tvs:
                return_list.append(tv.ID)
        session.close()
        return return_list


    def process_user_tv_title(self, zp_user_id, zp_tv_id, eapi_order, title_type_order, lang_list,
                                zp_tv_entity_type_id):
        session = self.Session()
        zp_tv_title_id = user_tv_title(session, zp_tv_id, eapi_order,
                                           title_type_order, lang_list, zp_user_id)
        session.close()
        self.set_zp_tv_entity_type(zp_user_id, zp_tv_id, zp_tv_title_id, zp_tv_entity_type_id)

    def process_user_tv_episode_title(self, zp_user_id, zp_tv_id, season, episode, eapi_order, title_type_order,
                                      lang_list,
                                zp_tv_entity_type_id):
        session = self.Session()
        zp_tv_title_id = user_tv_episode_title(session, zp_tv_id, season, episode, eapi_order,
                                           title_type_order, lang_list, zp_user_id)
        session.close()
        self.set_zp_tv_episode_entity_type(zp_user_id, zp_tv_id, season, episode, zp_tv_title_id, zp_tv_entity_type_id)
        
    def process_user_tv_overview(self, zp_user_id, zp_tv_id, eapi_order, title_type_order, lang_list,
                                zp_tv_entity_type_id):
        session = self.Session()
        zp_tv_title_id = user_tv_overview(session, zp_tv_id, eapi_order,
                                           title_type_order, lang_list, zp_user_id)
        session.close()
        self.set_zp_tv_entity_type(zp_user_id, zp_tv_id, zp_tv_title_id, zp_tv_entity_type_id)

    def process_user_tv_episode_overview(self, zp_user_id, zp_tv_id, season, episode,
                                         eapi_order, title_type_order, lang_list,
                                zp_tv_entity_type_id):
        session = self.Session()
        zp_tv_title_id = user_tv_episode_overview(session, zp_tv_id, season, episode, eapi_order,
                                           title_type_order, lang_list, zp_user_id)
        session.close()
        self.set_zp_tv_episode_entity_type(zp_user_id, zp_tv_id, season, episode, zp_tv_title_id, zp_tv_entity_type_id)

    def process_user_tv_raw_image(self, zp_user_id, zp_tv_id, eapi_order, lang_list, image_type_id,
                                    zp_tv_entity_type_id):
        session = self.Session()
        zp_raw_image_id = user_tv_raw_image(session, zp_tv_id, eapi_order,
                                           lang_list, zp_user_id, image_type_id)
        session.close()
        self.set_zp_tv_entity_type(zp_user_id, zp_tv_id, zp_raw_image_id, zp_tv_entity_type_id)

    def process_user_tv_season_raw_image(self, zp_user_id, zp_tv_id, season, eapi_order, lang_list, image_type_id,
                                    zp_tv_entity_type_id):
        session = self.Session()
        zp_raw_image_id = user_tv_season_raw_image(session, zp_tv_id, season, eapi_order,
                                           lang_list, zp_user_id, image_type_id)
        session.close()
        self.set_zp_tv_season_entity_type(zp_user_id, zp_tv_id, season, zp_raw_image_id, zp_tv_entity_type_id)

    def process_user_tv_episode_raw_image(self, zp_user_id, zp_tv_id, season, episode, eapi_order, lang_list,
                                          image_type_id, zp_tv_entity_type_id):
        session = self.Session()
        zp_raw_image_id = user_tv_episode_raw_image(session, zp_tv_id, season, episode, eapi_order,
                                           lang_list, zp_user_id, image_type_id)
        session.close()
        self.set_zp_tv_episode_entity_type(zp_user_id, zp_tv_id, season, episode,
                                           zp_raw_image_id, zp_tv_entity_type_id)

    def set_zp_tv_entity_type(self, zp_user_id, zp_tv_id, zp_tv_entity_id, zp_tv_entity_type_id):
        session = self.Session()
        if not isinstance(zp_tv_entity_id, int) or zp_tv_entity_id < 1:
            log.warning('zp_tv_entity_id %s is not int and greater than 0', zp_tv_entity_id)
            zp_tv_entity_id = None
        try:
            zp_user_tv_title_xref = session.query(TABLES.ZP_USER_TV_ENTITY_XREF).filter(
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == zp_tv_entity_type_id
            ).one()
        except orm.exc.NoResultFound:
            add_zp_user_tv_title_xref = TABLES.ZP_USER_TV_ENTITY_XREF(
                ZP_TV_ID=zp_tv_id,
                ZP_USER_ID=zp_user_id,
                ZP_TV_ENTITY_ID=zp_tv_entity_id,
                ZP_TV_ENTITY_TYPE_ID = zp_tv_entity_type_id,
                LAST_UPDATE_DATETIME=date_time())
            session.add(add_zp_user_tv_title_xref)
            commit(session)
        else:
            if zp_user_tv_title_xref.ZP_TV_ENTITY_ID != zp_tv_entity_id:
                zp_user_tv_title_xref.ZP_TV_ENTITY_ID = zp_tv_entity_id
            zp_user_tv_title_xref.LAST_UPDATE_DATETIME = date_time()
            commit(session)
        session.close()

    def set_zp_tv_season_entity_type(self, zp_user_id, zp_tv_id, season, zp_tv_entity_id, zp_tv_entity_type_id):
        session = self.Session()
        if not isinstance(zp_tv_entity_id, int) or zp_tv_entity_id < 1:
            log.warning('zp_tv_entity_id %s is not int and greater than 0', zp_tv_entity_id)
            zp_tv_entity_id = None
        try:
            zp_user_tv_title_xref = session.query(TABLES.ZP_USER_TV_SEASON_ENTITY_XREF).filter(
                TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.SEASON == season,
                TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == zp_tv_entity_type_id
            ).one()
        except orm.exc.NoResultFound:
            add_zp_user_tv_title_xref = TABLES.ZP_USER_TV_SEASON_ENTITY_XREF(
                ZP_TV_ID=zp_tv_id,
                SEASON=season,
                ZP_USER_ID=zp_user_id,
                ZP_TV_ENTITY_ID=zp_tv_entity_id,
                ZP_TV_ENTITY_TYPE_ID = zp_tv_entity_type_id,
                LAST_UPDATE_DATETIME=date_time())
            session.add(add_zp_user_tv_title_xref)
            commit(session)
        else:
            if zp_user_tv_title_xref.ZP_TV_ENTITY_ID != zp_tv_entity_id:
                zp_user_tv_title_xref.ZP_TV_ENTITY_ID = zp_tv_entity_id
            zp_user_tv_title_xref.LAST_UPDATE_DATETIME = date_time()
            commit(session)
        session.close()

    def set_zp_tv_episode_entity_type(self, zp_user_id, zp_tv_id, season, episode, zp_tv_entity_id,
                                      zp_tv_entity_type_id):
        session = self.Session()
        if not isinstance(zp_tv_entity_id, int) or zp_tv_entity_id < 1:
            log.warning('zp_tv_entity_id %s is not int and greater than 0', zp_tv_entity_id)
            zp_tv_entity_id = None
        try:
            zp_user_tv_title_xref = session.query(TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF).filter(
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON == season,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE == episode,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == zp_tv_entity_type_id
            ).one()
        except orm.exc.NoResultFound:
            add_zp_user_tv_title_xref = TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF(
                ZP_TV_ID=zp_tv_id,
                SEASON=season,
                EPISODE=episode,
                ZP_USER_ID=zp_user_id,
                ZP_TV_ENTITY_ID=zp_tv_entity_id,
                ZP_TV_ENTITY_TYPE_ID = zp_tv_entity_type_id,
                LAST_UPDATE_DATETIME=date_time())
            session.add(add_zp_user_tv_title_xref)
            log.debug('addeed ZP_TV_ENTITY_TYPE_ID %s for zp_user_id %s, zp_tv_id %s, season %s, episode %s,'
                                      ' zp_tv_entity_type_id %s', zp_tv_entity_id,
                      zp_user_id, zp_tv_id, season, episode,
                                      zp_tv_entity_type_id)
            commit(session)
        else:
            if zp_user_tv_title_xref.ZP_TV_ENTITY_ID != zp_tv_entity_id:
                log.debug('set ZP_TV_ENTITY_TYPE_ID %s for zp_user_id %s, zp_tv_id %s, season %s, episode %s,'
                          ' zp_tv_entity_type_id %s', zp_tv_entity_id,
                          zp_user_id, zp_tv_id, season, episode,
                          zp_tv_entity_type_id)
                zp_user_tv_title_xref.ZP_TV_ENTITY_ID = zp_tv_entity_id
            zp_user_tv_title_xref.LAST_UPDATE_DATETIME = date_time()
            commit(session)
        session.close()