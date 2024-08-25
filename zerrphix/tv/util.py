# -*- coding: utf-8 
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import os

from sqlalchemy import orm

from zerrphix.db import commit
from zerrphix.db.tables import TABLES
#from zerrphix.util import smbfs_connection_dict_scan_path
#from zerrphix.util.eapi import user_library_eapi_order
#from zerrphix.util.filesystem import (os_casesless_check)
from zerrphix.util.text import date_time

log = logging.getLogger(__name__)


#def user_prefs(session, ZP_USER_ID):
#    eapi_order = user_library_eapi_order(session, 2, ZP_USER_ID)
#    title_type_order = user_tv_title_type_order(session, ZP_USER_ID)
#    lang_list = user_tv_langs(session, ZP_USER_ID)
#    return eapi_order, title_type_order, lang_list


def user_tv_langs(session, ZP_USER_ID):
    return_list = []
    try:
        ZP_LANG_ID = session.query(TABLES.ZP_USER_LIBRARY_LANG).filter(
            TABLES.ZP_USER_LIBRARY_LANG.ZP_USER_ID == ZP_USER_ID,
            TABLES.ZP_USER_LIBRARY_LANG.ZP_LIBRARY_ID == 2
        ).one().ZP_LANG_ID
    except:
        # TODO: Don't jsut pass here
        pass
    else:
        return_list.append(ZP_LANG_ID)
    # TODO: User choice on use eng algn default
    if 1823 not in return_list:
        return_list.append(1823)
    return return_list


def user_tv_title(session, ZP_TV_ID, eapi_order, title_type_order, lang_list, ZP_USER_ID):
    # print(locals())
    # raise SystemExit
    for ZP_LANG_ID in lang_list:
        for ZP_TV_TITLE_TYPE_ID in title_type_order:
            for ZP_EAPI_ID in eapi_order:
                try:
                    ZP_TV_TITLE_ID = session.query(TABLES.ZP_TV_TITLE).filter(
                        TABLES.ZP_TV_TITLE.ZP_TV_ID == ZP_TV_ID,
                        TABLES.ZP_TV_TITLE.ZP_TV_TITLE_TYPE_ID == ZP_TV_TITLE_TYPE_ID,
                        TABLES.ZP_TV_TITLE.ZP_LANG_ID == ZP_LANG_ID,
                        TABLES.ZP_TV_TITLE.ZP_EAPI_ID == ZP_EAPI_ID).one().ID
                except orm.exc.NoResultFound as e:
                    # TODO: What to do when no title found
                    log.warning(('Cannot find a ZP_TV_TITLE_ID for ZP_TV_ID: {0},'
                                 ' ZP_TV_TITLE_TYPE_ID: {1}, ZP_LANG_ID: {2}, ZP_EAPI_ID: {3}, ZP_USER_ID: {4}.'
                                 ' Requested: eapi_order: {5}, title_type_order: {6}, lang_list: {7}').format(
                        ZP_TV_ID,
                        ZP_TV_TITLE_TYPE_ID,
                        ZP_LANG_ID,
                        ZP_EAPI_ID,
                        ZP_USER_ID,
                        eapi_order,
                        title_type_order,
                        lang_list))
                else:
                    return ZP_TV_TITLE_ID
    return None


def user_tv_episode_title(session, ZP_TV_ID, season, episode,
                          eapi_order, title_type_order, lang_list, ZP_USER_ID):
    # print(locals())
    # raise SystemExit
    for ZP_LANG_ID in lang_list:
        for ZP_EAPI_ID in eapi_order:
            try:
                ZP_TV_TITLE_ID = session.query(TABLES.ZP_TV_EPISODE_TITLE).filter(
                    TABLES.ZP_TV_EPISODE_TITLE.ZP_TV_ID == ZP_TV_ID,
                    TABLES.ZP_TV_EPISODE_TITLE.SEASON == season,
                    TABLES.ZP_TV_EPISODE_TITLE.EPISODE == episode,
                    TABLES.ZP_TV_EPISODE_TITLE.ZP_LANG_ID == ZP_LANG_ID,
                    TABLES.ZP_TV_EPISODE_TITLE.ZP_EAPI_ID == ZP_EAPI_ID).one().ID
            except orm.exc.NoResultFound as e:
                # TODO: What to do when no title found
                log.warning(('Cannot find a ZP_TV_TITLE_ID for ZP_TV_ID: {0}, episode'
                             ' ZP_LANG_ID: {1}, ZP_EAPI_ID: {2}, ZP_USER_ID: {3}.'
                             ' Requested: eapi_order: {4}, title_type_order: {5}, lang_list: {6}'
                             'episode {8}, season {7}').format(
                    ZP_TV_ID,
                    ZP_LANG_ID,
                    ZP_EAPI_ID,
                    ZP_USER_ID,
                    eapi_order,
                    title_type_order,
                    lang_list,
                    season,
                    episode))
            else:
                return ZP_TV_TITLE_ID
    return None


def user_tv_overview(session, ZP_TV_ID, eapi_order, title_type_order, lang_list, ZP_USER_ID):
    for ZP_LANG_ID in lang_list:
        for ZP_EAPI_ID in eapi_order:
            try:
                ZP_TV_OVERVIEW_ID = session.query(TABLES.ZP_TV_OVERVIEW).filter(
                    TABLES.ZP_TV_OVERVIEW.ZP_TV_ID == ZP_TV_ID,
                    TABLES.ZP_TV_OVERVIEW.ZP_LANG_ID == ZP_LANG_ID,
                    TABLES.ZP_TV_OVERVIEW.ZP_EAPI_ID == ZP_EAPI_ID).one().ID
            except orm.exc.NoResultFound as e:
                # TODO: What to do when no title found
                log.warning(('Cannot find a ZP_TV_TITLE_ID for ZP_TV_ID: {0},'
                             ' ZP_TV_TITLE_TYPE_ID: {1}, ZP_LANG_ID: {2}, ZP_EAPI_ID: {3}, ZP_USER_ID: {4}.'
                             ' Requested: eapi_order: {5}, lang_list: {6}').format(
                    ZP_TV_ID,
                    ZP_LANG_ID,
                    ZP_EAPI_ID,
                    ZP_USER_ID,
                    eapi_order,
                    title_type_order,
                    lang_list))
            else:
                return ZP_TV_OVERVIEW_ID
    return None


def user_tv_episode_overview(session, ZP_TV_ID, season, episode, eapi_order, title_type_order, lang_list, ZP_USER_ID):
    for ZP_LANG_ID in lang_list:
        for ZP_EAPI_ID in eapi_order:
            try:
                ZP_TV_OVERVIEW_ID = session.query(TABLES.ZP_TV_EPISODE_OVERVIEW).filter(
                    TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_TV_ID == ZP_TV_ID,
                    TABLES.ZP_TV_EPISODE_OVERVIEW.SEASON == season,
                    TABLES.ZP_TV_EPISODE_OVERVIEW.EPISODE == episode,
                    TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_LANG_ID == ZP_LANG_ID,
                    TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_EAPI_ID == ZP_EAPI_ID).one().ID
            except orm.exc.NoResultFound as e:
                # TODO: What to do when no title found
                log.warning(('Cannot find a ZP_TV_TITLE_ID for ZP_TV_ID: {0},'
                             ' ZP_TV_TITLE_TYPE_ID: {1}, ZP_LANG_ID: {2}, ZP_EAPI_ID: {3}, ZP_USER_ID: {4}.'
                             ' Requested: eapi_order: {5}, lang_list: {6}'
                             'episode {8}, season {7}').format(
                    ZP_TV_ID,
                    ZP_LANG_ID,
                    ZP_EAPI_ID,
                    ZP_USER_ID,
                    eapi_order,
                    title_type_order,
                    lang_list,
                    season,
                    episode))
            else:
                return ZP_TV_OVERVIEW_ID
    return None

def user_tv_raw_image(session, zp_tv_id, eapi_order, lang_list, zp_user_id, image_type_id):
    proceess_lang_lists = [lang_list, [None]]
    try:
        zp_tv_raw_image_id = session.query(TABLES.ZP_TV_RAW_IMAGE).filter(
            TABLES.ZP_TV_RAW_IMAGE.ZP_LANG_ID == proceess_lang_lists[0][0],
            TABLES.ZP_TV_RAW_IMAGE.ZP_USER_ID == zp_user_id,
            TABLES.ZP_TV_RAW_IMAGE.ZP_ENTITY_ID == zp_tv_id,
            TABLES.ZP_TV_RAW_IMAGE.ZP_ENTITY_TYPE_ID == image_type_id
        ).one()
    except orm.exc.NoResultFound:
        log.debug('No results found in ZP_TV_RAW_IMAGE for ZP_LANG_ID %s, ZP_USER_ID %s,'
                  ' ZP_ENTITY_ID %s, ZP_ENTITY_TYPE_ID %s', proceess_lang_lists[0][0], zp_user_id, zp_tv_id,
                              image_type_id)
    else:
        return zp_tv_raw_image_id.ID
    for proceess_lang_list in proceess_lang_lists:
        for zp_lang_id in proceess_lang_list:
            for zp_eapi_id in eapi_order:
                try:
                    zp_tv_raw_image_id = session.query(TABLES.ZP_TV_RAW_IMAGE).filter(
                        TABLES.ZP_TV_RAW_IMAGE.ZP_LANG_ID == zp_lang_id,
                        TABLES.ZP_TV_RAW_IMAGE.ZP_EAPI_ID == zp_eapi_id,
                        TABLES.ZP_TV_RAW_IMAGE.ZP_ENTITY_ID == zp_tv_id,
                        TABLES.ZP_TV_RAW_IMAGE.ZP_ENTITY_TYPE_ID == image_type_id
                    ).one()
                except orm.exc.NoResultFound:
                    log.debug('No results found in ZP_TV_RAW_IMAGE for ZP_LANG_ID %s, ZP_EAPI_ID %s,'
                              ' ZP_ENTITY_ID %s, ZP_ENTITY_TYPE_ID %s', zp_lang_id, zp_eapi_id, zp_tv_id,
                              image_type_id)
                else:
                    return zp_tv_raw_image_id.ID
    # todo add lang default
    # todo add system default
    return None

def user_tv_season_raw_image(session, zp_tv_id, season, eapi_order, lang_list, zp_user_id, image_type_id):
    proceess_lang_lists = [lang_list, [None]]
    try:
        zp_tv_raw_image_id = session.query(TABLES.ZP_TV_SEASON_RAW_IMAGE).filter(
            TABLES.ZP_TV_SEASON_RAW_IMAGE.ZP_LANG_ID == proceess_lang_lists[0][0],
            TABLES.ZP_TV_SEASON_RAW_IMAGE.ZP_USER_ID == zp_user_id,
            TABLES.ZP_TV_SEASON_RAW_IMAGE.ZP_ENTITY_ID == zp_tv_id,
            TABLES.ZP_TV_SEASON_RAW_IMAGE.SEASON == season,
            TABLES.ZP_TV_SEASON_RAW_IMAGE.ZP_ENTITY_TYPE_ID == image_type_id
        ).one()
    except orm.exc.NoResultFound:
        log.debug('No results found in ZP_TV_RAW_IMAGE for ZP_LANG_ID %s, ZP_USER_ID %s,'
                  ' ZP_ENTITY_ID %s, ZP_ENTITY_TYPE_ID %s', proceess_lang_lists[0][0], zp_user_id, zp_tv_id,
                              image_type_id)
    else:
        return zp_tv_raw_image_id.ID
    for proceess_lang_list in proceess_lang_lists:
        for zp_lang_id in proceess_lang_list:
            for zp_eapi_id in eapi_order:
                try:
                    zp_tv_raw_image_id = session.query(TABLES.ZP_TV_SEASON_RAW_IMAGE).filter(
                        TABLES.ZP_TV_SEASON_RAW_IMAGE.ZP_LANG_ID == zp_lang_id,
                        TABLES.ZP_TV_SEASON_RAW_IMAGE.ZP_EAPI_ID == zp_eapi_id,
                        TABLES.ZP_TV_SEASON_RAW_IMAGE.ZP_ENTITY_ID == zp_tv_id,
                        TABLES.ZP_TV_SEASON_RAW_IMAGE.SEASON == season,
                        TABLES.ZP_TV_SEASON_RAW_IMAGE.ZP_ENTITY_TYPE_ID == image_type_id
                    ).one()
                except orm.exc.NoResultFound:
                    log.debug('No results found in ZP_TV_RAW_IMAGE for ZP_LANG_ID %s, ZP_EAPI_ID %s,'
                              ' ZP_ENTITY_ID %s, ZP_ENTITY_TYPE_ID %s', zp_lang_id, zp_eapi_id, zp_tv_id,
                              image_type_id)
                else:
                    return zp_tv_raw_image_id.ID
    # todo add lang default
    # todo add system default
    return None

def user_tv_episode_raw_image(session, zp_tv_id, season, episode, eapi_order, lang_list, zp_user_id, image_type_id):
    proceess_lang_lists = [[None]]
    #log.error(locals())
    #log.error(locals())
    try:
        zp_tv_raw_image_id = session.query(TABLES.ZP_TV_EPISODE_RAW_IMAGE).filter(
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_LANG_ID == None,
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_USER_ID == zp_user_id,
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID == zp_tv_id,
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.SEASON == season,
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.EPISODE == episode,
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID == image_type_id
        ).one()
    except orm.exc.NoResultFound:
        log.debug('No results found in ZP_TV_RAW_IMAGE for ZP_LANG_ID %s, ZP_USER_ID %s,'
                  ' ZP_ENTITY_ID %s, ZP_ENTITY_TYPE_ID %s', proceess_lang_lists[0][0], zp_user_id, zp_tv_id,
                              image_type_id)
    else:
        log.error('ZP_TV_EPISODE_RAW_IMAGE.ID %s for zp_tv_id %s, season %s, episode %s', zp_tv_raw_image_id.ID,
                  zp_tv_id, season, episode)
        #raise SystemExit
        return zp_tv_raw_image_id.ID
    for proceess_lang_list in proceess_lang_lists:
        for zp_lang_id in proceess_lang_list:
            for zp_eapi_id in eapi_order:
                try:
                    zp_tv_raw_image_id = session.query(TABLES.ZP_TV_EPISODE_RAW_IMAGE).filter(
                        TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_LANG_ID == zp_lang_id,
                        TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_EAPI_ID == zp_eapi_id,
                        TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID == zp_tv_id,
                        TABLES.ZP_TV_EPISODE_RAW_IMAGE.SEASON == season,
                        TABLES.ZP_TV_EPISODE_RAW_IMAGE.EPISODE == episode,
                        TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID == image_type_id
                    ).one()
                except orm.exc.NoResultFound:
                    log.debug('No results found in ZP_TV_RAW_IMAGE for ZP_LANG_ID %s, ZP_EAPI_ID %s,'
                              ' ZP_ENTITY_ID %s, ZP_ENTITY_TYPE_ID %s', zp_lang_id, zp_eapi_id, zp_tv_id,
                              image_type_id)
                else:
                    #log.error(zp_tv_raw_image_id.ID)
                    log.debug('ZP_TV_EPISODE_RAW_IMAGE.ID %s for zp_tv_id %s, season %s, episode %s', zp_tv_raw_image_id.ID,
                    zp_tv_id, season, episode)
                    #raise SystemExit
                    return zp_tv_raw_image_id.ID
    # todo add lang default
    # todo add system default
    #log.error('None')
        log.warning('ZP_TV_EPISODE_RAW_IMAGE.ID NONE for zp_tv_id %s, season %s, episode %s',
                  zp_tv_id, season, episode)
    #raise SystemExit
    return None


def user_tv_title_type_order(session, ZP_USER_ID):
    return_list = []
    try:
        user_ZP_TV_TITLE_TYPE_ID = session.query(TABLES.ZP_USER_TV_TITLE_TYPE_PREF).filter(
            TABLES.ZP_USER_TV_TITLE_TYPE_PREF.ZP_USER_ID == ZP_USER_ID).one().ZP_TV_TITLE_TYPE_ID
    except orm.exc.NoResultFound as e:
        # TODO: get this from DB
        return_list.append(1)
    else:
        return_list.append(user_ZP_TV_TITLE_TYPE_ID)

    # TODO: get this from DB
    ZP_TV_TITLE_TYPE_list = [1, 2]

    for ZP_TV_TITLE_TYPE_ID in ZP_TV_TITLE_TYPE_list:
        if ZP_TV_TITLE_TYPE_ID not in return_list:
            return_list.append(ZP_TV_TITLE_TYPE_ID)
    return return_list


def update_tv_last_mod(Session, ZP_TV_ID):
    session = Session()
    session.query(TABLES.ZP_TV).filter(TABLES.ZP_TV.ID == ZP_TV_ID).update({"LAST_EDIT_DATETIME": date_time()})
    commit(session)
    session.close()


def update_tv_episode_last_mod(Session, zp_tv_episode_id=None, ZP_TV_ID=None, SEASON=None, EPISODE=None):
    session = Session()
    if isinstance(zp_tv_episode_id, int):
        session.query(TABLES.ZP_TV_EPISODE).filter(
            TABLES.ZP_TV_EPISODE.ID == zp_tv_episode_id
            #TABLES.ZP_TV_EPISODE.EPISODE == EPISODE).update({"LAST_EDIT_DATETIME": date_time()},
            #                                                synchronize_session='fetch')
            ).update(
            {"LAST_EDIT_DATETIME": date_time()}
        )
        commit(session)
    elif isinstance(ZP_TV_ID, int) and isinstance(SEASON, int) and isinstance(EPISODE, int):
        session.query(TABLES.ZP_TV_EPISODE).filter(
            TABLES.ZP_TV_EPISODE.ZP_TV_ID == ZP_TV_ID,
            TABLES.ZP_TV_EPISODE.SEASON == SEASON,
            #TABLES.ZP_TV_EPISODE.EPISODE == EPISODE).update({"LAST_EDIT_DATETIME": date_time()},
            #                                                synchronize_session='fetch')
            TABLES.ZP_TV_EPISODE.EPISODE == EPISODE).update(
            {"LAST_EDIT_DATETIME": date_time()}
        )
        commit(session)
    session.close()
