# -*- coding: utf-8 
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import os

from sqlalchemy import orm

from zerrphix.db import commit
from zerrphix.db.tables import TABLES
#from zerrphix.util.eapi import user_library_eapi_order
#from zerrphix.util.filesystem import (os_casesless_check)
from zerrphix.util.text import date_time

log = logging.getLogger(__name__)


def user_film_raw_image(session, zp_film_id, eapi_order, lang_list, zp_user_id, image_type_id):
    proceess_lang_lists = [lang_list, [None]]
    try:
        zp_film_raw_image_id = session.query(TABLES.ZP_FILM_RAW_IMAGE).filter(
            TABLES.ZP_FILM_RAW_IMAGE.ZP_LANG_ID == proceess_lang_lists[0][0],
            TABLES.ZP_FILM_RAW_IMAGE.ZP_USER_ID == zp_user_id,
            TABLES.ZP_FILM_RAW_IMAGE.ZP_ENTITY_ID == zp_film_id,
            TABLES.ZP_FILM_RAW_IMAGE.ZP_ENTITY_TYPE_ID == image_type_id
        ).one()
    except orm.exc.NoResultFound:
        log.debug('No results found in ZP_FILM_RAW_IMAGE for ZP_LANG_ID %s, ZP_USER_ID %s,'
                  ' ZP_ENTITY_ID %s, ZP_ENTITY_TYPE_ID %s', proceess_lang_lists[0][0], zp_user_id, zp_film_id,
                              image_type_id)
    else:
        return zp_film_raw_image_id.ID
    for proceess_lang_list in proceess_lang_lists:
        for zp_lang_id in proceess_lang_list:
            for zp_eapi_id in eapi_order:
                try:
                    zp_film_raw_image_id = session.query(TABLES.ZP_FILM_RAW_IMAGE).filter(
                        TABLES.ZP_FILM_RAW_IMAGE.ZP_LANG_ID == zp_lang_id,
                        TABLES.ZP_FILM_RAW_IMAGE.ZP_EAPI_ID == zp_eapi_id,
                        TABLES.ZP_FILM_RAW_IMAGE.ZP_ENTITY_ID == zp_film_id,
                        TABLES.ZP_FILM_RAW_IMAGE.ZP_ENTITY_TYPE_ID == image_type_id
                    ).one()
                except orm.exc.NoResultFound:
                    log.debug('No results found in ZP_FILM_RAW_IMAGE for ZP_LANG_ID %s, ZP_EAPI_ID %s,'
                              ' ZP_ENTITY_ID %s, ZP_ENTITY_TYPE_ID %s', zp_lang_id, zp_eapi_id, zp_film_id,
                              image_type_id)
                else:
                    return zp_film_raw_image_id.ID
    # todo add lang default
    # todo add system default
    return None

def user_film_collection_raw_image(session, zp_film_collection_id, eapi_order, lang_list, zp_user_id, image_type_id):
    proceess_lang_lists = [lang_list, [None]]
    try:
        zp_film_raw_image_id = session.query(TABLES.ZP_FILM_COLLECTION_RAW_IMAGE).filter(
            TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_LANG_ID == proceess_lang_lists[0][0],
            TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_USER_ID == zp_user_id,
            TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_ID == zp_film_collection_id,
            TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_TYPE_ID == image_type_id
        ).one()
    except orm.exc.NoResultFound:
        log.debug('No results found in ZP_FILM_RAW_IMAGE for ZP_LANG_ID %s, ZP_USER_ID %s,'
                  ' ZP_ENTITY_ID %s, ZP_ENTITY_TYPE_ID %s', proceess_lang_lists[0][0], zp_user_id, zp_film_collection_id,
                              image_type_id)
    else:
        return zp_film_raw_image_id.ID
    for proceess_lang_list in proceess_lang_lists:
        for zp_lang_id in proceess_lang_list:
            for zp_eapi_id in eapi_order:
                try:
                    zp_film_raw_image_id = session.query(TABLES.ZP_FILM_COLLECTION_RAW_IMAGE).filter(
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_LANG_ID == zp_lang_id,
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_EAPI_ID == zp_eapi_id,
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_ID == zp_film_collection_id,
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_TYPE_ID == image_type_id
                    ).one()
                except orm.exc.NoResultFound:
                    log.debug('No results found in ZP_FILM_RAW_IMAGE for ZP_LANG_ID %s, ZP_EAPI_ID %s,'
                              ' ZP_ENTITY_ID %s, ZP_ENTITY_TYPE_ID %s', zp_lang_id, zp_eapi_id, zp_film_collection_id,
                              image_type_id)
                else:
                    return zp_film_raw_image_id.ID
    # todo add lang default
    # todo add system default
    return None

def user_film_title(session, ZP_FILM_ID, eapi_order, title_type_order, lang_list, ZP_USER_ID):
    for ZP_LANG_ID in lang_list:
        for ZP_FILM_TITLE_TYPE_ID in title_type_order:
            for ZP_EAPI_ID in eapi_order:
                try:
                    ZP_FILM_TITLE_ID = session.query(TABLES.ZP_FILM_TITLE).filter(
                        TABLES.ZP_FILM_TITLE.ZP_FILM_ID == ZP_FILM_ID,
                        TABLES.ZP_FILM_TITLE.ZP_FILM_TITLE_TYPE_ID == ZP_FILM_TITLE_TYPE_ID,
                        TABLES.ZP_FILM_TITLE.ZP_LANG_ID == ZP_LANG_ID,
                        TABLES.ZP_FILM_TITLE.ZP_EAPI_ID == ZP_EAPI_ID).one().ID
                except orm.exc.NoResultFound as e:
                    # TODO: What to do when no title found
                    log.warning(('Cannot find a ZP_FILM_TITLE_ID for ZP_FILM_ID: {0},'
                                 ' ZP_FILM_TITLE_TYPE_ID: {1}, ZP_LANG_ID: {2}, ZP_EAPI_ID: {3}, ZP_USER_ID: {4}.'
                                 ' Requested: eapi_order: {5}, title_type_order: {6}, lang_list: {7}').format(
                        ZP_FILM_ID,
                        ZP_FILM_TITLE_TYPE_ID,
                        ZP_LANG_ID,
                        ZP_EAPI_ID,
                        ZP_USER_ID,
                        eapi_order,
                        title_type_order,
                        lang_list))
                else:
                    return ZP_FILM_TITLE_ID
    return None

def user_film_overview(session, ZP_FILM_ID, eapi_order, title_type_order, lang_list, ZP_USER_ID):
    for ZP_LANG_ID in lang_list:
        for ZP_EAPI_ID in eapi_order:
            try:
                ZP_FILM_OVERVIEW_ID = session.query(TABLES.ZP_FILM_OVERVIEW).filter(
                    TABLES.ZP_FILM_OVERVIEW.ZP_FILM_ID == ZP_FILM_ID,
                    TABLES.ZP_FILM_OVERVIEW.ZP_LANG_ID == ZP_LANG_ID,
                    TABLES.ZP_FILM_OVERVIEW.ZP_EAPI_ID == ZP_EAPI_ID).one().ID
            except orm.exc.NoResultFound as e:
                # TODO: What to do when no title found
                log.warning(('Cannot find a ZP_FILM_TITLE_ID for ZP_FILM_ID: {0},'
                             ' ZP_FILM_TITLE_TYPE_ID: {1}, ZP_LANG_ID: {2}, ZP_EAPI_ID: {3}, ZP_USER_ID: {4}.'
                             ' Requested: eapi_order: {5}, lang_list: {6}').format(
                    ZP_FILM_ID,
                    ZP_LANG_ID,
                    ZP_EAPI_ID,
                    ZP_USER_ID,
                    eapi_order,
                    title_type_order,
                    lang_list))
            else:
                return ZP_FILM_OVERVIEW_ID
    return None

def user_film_collection_title(session, ZP_FILM_COLLECTION_ID, eapi_order, title_type_order, lang_list, ZP_USER_ID):
    for ZP_LANG_ID in lang_list:
        for ZP_FILM_COLLECTION_TITLE_TYPE_ID in title_type_order:
            for ZP_EAPI_ID in eapi_order:
                try:
                    ZP_FILM_COLLECTION_TITLE_ID = session.query(TABLES.ZP_FILM_COLLECTION_TITLE).filter(
                        TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_ID == ZP_FILM_COLLECTION_ID,
                        TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_TITLE_TYPE_ID ==
                        ZP_FILM_COLLECTION_TITLE_TYPE_ID,
                        TABLES.ZP_FILM_COLLECTION_TITLE.ZP_LANG_ID == ZP_LANG_ID,
                        TABLES.ZP_FILM_COLLECTION_TITLE.ZP_EAPI_ID == ZP_EAPI_ID).one().ID
                except orm.exc.NoResultFound as e:
                    # TODO: What to do when no title found
                    log.warning(('Cannot find a ZP_FILM_TITLE_ID for ZP_FILM_COLLECTION_ID: {0},'
                                 ' ZP_FILM_TITLE_TYPE_ID: {1}, ZP_LANG_ID: {2}, ZP_EAPI_ID: {3}, ZP_USER_ID: {4}.'
                                 ' Requested: eapi_order: {5}, title_type_order: {6}, lang_list: {7}').format(
                        ZP_FILM_COLLECTION_ID,
                        ZP_FILM_COLLECTION_TITLE_TYPE_ID,
                        ZP_LANG_ID,
                        ZP_EAPI_ID,
                        ZP_USER_ID,
                        eapi_order,
                        title_type_order,
                        lang_list))
                else:
                    return ZP_FILM_COLLECTION_TITLE_ID
    return None

def user_film_collection_overview(session, ZP_FILM_COLLECTION_ID, eapi_order, lang_list, ZP_USER_ID):
    for ZP_LANG_ID in lang_list:
        for ZP_EAPI_ID in eapi_order:
            try:
                ZP_FILM_COLLECTION_TITLE_ID = session.query(TABLES.ZP_FILM_COLLECTION_OVERVIEW).filter(
                    TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_FILM_COLLECTION_ID == ZP_FILM_COLLECTION_ID,
                    TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_LANG_ID == ZP_LANG_ID,
                    TABLES.ZP_FILM_COLLECTION_OVERVIEW.ZP_EAPI_ID == ZP_EAPI_ID).one().ID
            except orm.exc.NoResultFound as e:
                # TODO: What to do when no title found
                log.warning(('Cannot find a ZP_FILM_TITLE_ID for ZP_FILM_COLLECTION_ID: {0},'
                             ' ZP_LANG_ID: {1}, ZP_EAPI_ID: {2}, ZP_USER_ID: {3}.'
                             ' Requested: eapi_order: {4}, lang_list: {5}').format(
                    ZP_FILM_COLLECTION_ID,
                    ZP_LANG_ID,
                    ZP_EAPI_ID,
                    ZP_USER_ID,
                    eapi_order,
                    lang_list))
            else:
                return ZP_FILM_COLLECTION_TITLE_ID
    return None

def update_film_last_mod(Session, ZP_FILM_ID):
    session = Session()
    session.query(TABLES.ZP_FILM).filter(TABLES.ZP_FILM.ID == ZP_FILM_ID).update({"LAST_EDIT_DATETIME": date_time()})
    commit(session)
    session.close()



def update_film_collection_last_mod(Session, ZP_FILM_COLLECTION_ID):
    session = Session()
    session.query(TABLES.ZP_FILM_COLLECTION).filter(TABLES.ZP_FILM_COLLECTION.ID == ZP_FILM_COLLECTION_ID).update(
        {"LAST_EDIT_DATETIME": date_time()})
    commit(session)
    session.close()

def _construct_source_dict(Session):
    """Construct source dict (Bluray, DVD etc...).

        Returns:
            | dict: {TABLES.ZP_SOURCE.ID:{
            | 'ID':TABLES.ZP_SOURCE.ID,
            | 'SOURCE':TABLES.ZP_SOURCE.SOURCE,
            | 'SCORE':TABLES.ZP_SOURCE.SCORE,
            | 'DISC_SCORE':TABLES.ZP_SOURCE.DISC_SCORE'}}

    """
    session = Session()
    return_dict = {}
    get_source_query = session.query(TABLES.ZP_SOURCE).all()
    for source in get_source_query:
        return_dict[source.ID] = {}
        for field in TABLES.ZP_SOURCE.__table__.columns._data.keys():
            return_dict[source.ID][field] = getattr(source, field)
    session.close()
    return return_dict


def _construct_res_dict(Session):
    """Construct resolution dict (1080p, 720p etc...).

        Returns:
            | dict: {TABLES.ZP_SOURCE.ID:{
            | 	'ID':TABLES.ZP_RES.ID
            | 	'RES':TABLES.ZP_RES.RES
            | 	'SCORE':TABLES.ZP_RES.SCORE
            | 	'HD':TABLES.ZP_RES.HD
            | 	'MIN_WIDTH':TABLES.ZP_RES.MIN_WIDTH
            | 	'MAX_WIDTH':TABLES.ZP_RES.MAX_WIDTH
            | 	'MIN_HEIGHT':TABLES.ZP_RES.MIN_HEIGHT
            | 	'MAX_HEIGHT':TABLES.ZP_RES.MAX_HEIGHT}}

    """
    session = Session()
    return_dict = {}
    get_source_query = session.query(TABLES.ZP_RES).all()
    for res in get_source_query:
        return_dict[res.ID] = {}
        for field in TABLES.ZP_RES.__table__.columns._data.keys():
            return_dict[res.ID][field] = getattr(res, field)
    session.close()
    return return_dict


