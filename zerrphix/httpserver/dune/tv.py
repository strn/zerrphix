# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import re

import urllib
from sqlalchemy import func, orm, asc, desc, distinct, case, and_, or_

from zerrphix.db import commit
from zerrphix.db.tables import TABLES
from zerrphix.util.numbers import is_even
from zerrphix.util.text import date_time
from zerrphix.util.text import construct_dune_ui_entity_return_list
from zerrphix.util.text import string_to_list
import math
import pprint

log = logging.getLogger(__name__)


def tv_episode_play(self, **kwargs):
    """
    SELECT zpff.SCAN_PATH_SUB_DIR, zpff.LAST_PATH, zpdpp.PLAY_ROOT_PATH FROM
    ZP_FILM_FILEFOLDER_XREF zpffx
    JOIN ZP_FILM_FILEFOLDER zpff ON
    zpffx.ZP_FILM_FILEFOLDER_ID = zpff.ID
    JOIN ZP_DUNE_PLAY_PATH zpdpp ON
    zpff.ZP_SCAN_PATH_ID = zpdpp.ZP_SCAN_PATH_ID
    WHERE zpffx.ZP_FILM_ID = ZP_FILM_ID
    """
    ZP_DUNE_ID = kwargs['ZP_DUNE_ID']
    ZP_TV_EPISODE_FILEFOLDER_ID = kwargs['ZP_TV_EPISODE_FILEFOLDER_ID'][0]
    ZP_USER_ID = kwargs['ZP_USER_ID']
    path_components = self.session.query(
        TABLES.ZP_TV_EPISODE_FILEFOLDER.LAST_PATH.label('EPISODE_LAST_PATH'),
        TABLES.ZP_TV_FILEFOLDER.LAST_PATH,
        TABLES.ZP_DUNE_PLAY_PATH.PLAY_ROOT_PATH,
        TABLES.ZP_TV_EPISODE_FILEFOLDER.SEASON,
        TABLES.ZP_TV_EPISODE_FILEFOLDER.FIRST_EPISODE.label('EPISODE'),
        TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID
    ).filter(
        TABLES.ZP_TV_FILEFOLDER.ZP_SCAN_PATH_ID == TABLES.ZP_DUNE_PLAY_PATH.ZP_SCAN_PATH_ID,
        TABLES.ZP_TV_FILEFOLDER.ID == TABLES.ZP_TV_EPISODE_FILEFOLDER.ZP_TV_FILEFOLDER_ID,
        TABLES.ZP_DUNE_PLAY_PATH.ZP_DUNE_ID == ZP_DUNE_ID,
        TABLES.ZP_TV_EPISODE_FILEFOLDER.ID == ZP_TV_EPISODE_FILEFOLDER_ID
    ).first()

    dune_last_path = re.sub(r'/+', '/', '{0}/{1}'.format(path_components.LAST_PATH.strip(' '),
                                                         path_components.EPISODE_LAST_PATH.strip(' ')).strip('/'))

    dune_play_path = '{0}/{1}'.format(path_components.PLAY_ROOT_PATH.rstrip('/'),
                                      dune_last_path)

    self.wfile.write(dune_play_path.encode('utf-8'))
    # TODO change to show season ep as there may be more than one file per episode not and in the future
    try:
        allready_watched = self.session.query(
            TABLES.ZP_USER_TV_EPISODE_WATCHED
        ).filter(
            TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_USER_ID == ZP_USER_ID,
            TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_TV_ID == path_components.ZP_TV_ID,
            TABLES.ZP_USER_TV_EPISODE_WATCHED.SEASON == path_components.SEASON,
            TABLES.ZP_USER_TV_EPISODE_WATCHED.EPISODE == path_components.EPISODE
        ).one()
    except orm.exc.NoResultFound as e:
        add_tv_episode_watched = TABLES.ZP_USER_TV_EPISODE_WATCHED(ZP_USER_ID=ZP_USER_ID,
                                                                   ZP_TV_ID=path_components.ZP_TV_ID,
                                                                   SEASON=path_components.SEASON,
                                                                   EPISODE=path_components.EPISODE,
                                                                   DATETIME=date_time())
        self.session.add(add_tv_episode_watched)
        commit(self.session)
    else:
        allready_watched.DATETIME = date_time()
        commit(self.session)


def tv_list(self, **kwargs):
    # special_replace_dicts = globals()[virtual_item['@special']](self, **request_query_kwargs)
    return globals()[kwargs['special'][0]](self, **kwargs)


def tv_continue(self, **kwargs):
    ZP_TV_ID = kwargs['ZP_TV_ID'][0]
    last_episode_watched = tv_last_episode_watched(self, ZP_TV_ID)
    if last_episode_watched:
        ZP_TV_EPISODE = tv_episode(self, ZP_TV_ID, last_episode_watched.SEASON, last_episode_watched.EPISODE)
    else:
        ZP_TV_EPISODE = tv_first_episode(self, ZP_TV_ID)

    if ZP_TV_EPISODE:
        kwargs['ZP_TV_EPISODE_FILEFOLDER_ID'] = [ZP_TV_EPISODE.ZP_TV_EPISODE_FILEFOLDER_ID]
        tv_episode_play(self, **kwargs)


def tv_watch_next(self, **kwargs):
    ZP_TV_ID = kwargs['ZP_TV_ID'][0]
    last_episode_watched = tv_last_episode_watched(self, ZP_TV_ID, watch_next=True)
    if last_episode_watched:
        ZP_TV_EPISODE = tv_next_episode(self, ZP_TV_ID, last_episode_watched.SEASON, last_episode_watched.EPISODE)
    else:
        ZP_TV_EPISODE = tv_first_episode(self, ZP_TV_ID)

    if ZP_TV_EPISODE:
        kwargs['ZP_TV_EPISODE_FILEFOLDER_ID'] = [ZP_TV_EPISODE.ZP_TV_EPISODE_FILEFOLDER_ID]
        tv_episode_play(self, **kwargs)


def tv_episode(self, ZP_TV_ID, SEASON, EPISODE):
    return self.session.query(
        TABLES.ZP_TV_EPISODE
    ).filter(
        TABLES.ZP_TV_EPISODE.SEASON == SEASON,
        TABLES.ZP_TV_EPISODE.EPISODE == EPISODE,
        TABLES.ZP_TV_EPISODE.ZP_TV_ID == ZP_TV_ID
    ).first()


def tv_next_episode(self, ZP_TV_ID, SEASON, EPISODE):
    ZP_TV_EPISODE = self.session.query(
        TABLES.ZP_TV_EPISODE
    ).filter(
        TABLES.ZP_TV_EPISODE.SEASON == SEASON,
        TABLES.ZP_TV_EPISODE.EPISODE > EPISODE,
        TABLES.ZP_TV_EPISODE.ZP_TV_ID == ZP_TV_ID
    ).group_by(
        TABLES.ZP_TV_EPISODE.SEASON, TABLES.ZP_TV_EPISODE.EPISODE
    ).order_by(
        TABLES.ZP_TV_EPISODE.SEASON.asc(),
        TABLES.ZP_TV_EPISODE.EPISODE.asc()
    ).first()
    if ZP_TV_EPISODE:
        return ZP_TV_EPISODE
    else:
        ZP_TV_EPISODE = self.session.query(
            TABLES.ZP_TV_EPISODE
        ).filter(
            TABLES.ZP_TV_EPISODE.SEASON > SEASON,
            TABLES.ZP_TV_EPISODE.ZP_TV_ID == ZP_TV_ID
        ).group_by(
            TABLES.ZP_TV_EPISODE.SEASON,
            TABLES.ZP_TV_EPISODE.EPISODE
        ).order_by(
            TABLES.ZP_TV_EPISODE.SEASON.asc(),
            TABLES.ZP_TV_EPISODE.EPISODE.asc()
        ).first()
        if ZP_TV_EPISODE:
            return ZP_TV_EPISODE
        else:
            return tv_first_episode(self, ZP_TV_ID)


def tv_last_episode_watched(self, ZP_TV_ID, watch_next=False):
    if watch_next:
        return self.session.query(
            TABLES.ZP_USER_TV_EPISODE_WATCHED
        ).filter(
            TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_TV_ID == ZP_TV_ID,
            TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME <= date_time(offset=7)
        ).order_by(
            TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME.desc()
        ).first()
    else:
        return self.session.query(
            TABLES.ZP_USER_TV_EPISODE_WATCHED
        ).filter(
            TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_TV_ID == ZP_TV_ID
        ).order_by(
            TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME.desc()
        ).first()


def tv_first_episode(self, ZP_TV_ID):
    return self.session.query(
        TABLES.ZP_TV_EPISODE
    ).filter(
        TABLES.ZP_TV_EPISODE.ZP_TV_ID == ZP_TV_ID
    ).group_by(
        TABLES.ZP_TV_EPISODE.SEASON,
        TABLES.ZP_TV_EPISODE.EPISODE
    ).order_by(
        TABLES.ZP_TV_EPISODE.SEASON.asc(),
        TABLES.ZP_TV_EPISODE.EPISODE.asc()
    ).first()


def tv_genres(self, **kwargs):
    return_list = []
    genres = self.session.query(
        TABLES.ZP_GENRE
    ).all()
    for result in genres:
        return_list.append({r'::ZP_GENRE_NAME::': result.GENRE,
                            r'::ZP_GENRE_ID::': str(result.ID)})
    return return_list


def tv_az_names(self, **kwargs):
    return_list = [{'::AZ::': '123'}]
    for i in range(65, 91):  # Upper Case Letters A-Z
        return_list.append({r'::AZ::': chr(i)})
    return return_list


def tv_user_last_watched(self, **kwargs):
    ZP_USER_ID = kwargs['ZP_USER_ID']
    log.debug('image_type %s', kwargs['image_type'])
    subq = self.session.query(
        TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_TV_ID
    ).filter(
        TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_USER_ID == ZP_USER_ID
    ).order_by(
        TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME.desc()
    ).limit(1).subquery()
    entity_search_results = self.session.query(
        TABLES.ZP_TV_TITLE.TITLE,
        TABLES.ZP_TV_TITLE.ZP_TV_ID,
        TABLES.ZP_TEMPLATE.REF_NAME,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.HASH,
        TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.EXT,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME,
        TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
        TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID')
    ).join(
        TABLES.ZP_USER_TV_ENTITY_XREF,
        and_(
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_ID == TABLES.ZP_TV_TITLE.ID,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
        )
    ).join(
        TABLES.ZP_TV_IMAGE_RENDER_HASH,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID
    ).join(
        TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID ==
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ID,
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
        )
    ).join(
        TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID ==
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID == \
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ID
        )
    ).join(
        TABLES.ZP_TV_FILEFOLDER,
        and_(
            TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_TV_FILEFOLDER.ENABLED == 1
        )
    ).join(
        TABLES.ZP_TEMPLATE, TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
    ).join(
        TABLES.ZP_IMAGE_TYPE,
        and_(
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
            TABLES.ZP_IMAGE_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
            TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
        )
    ).join(
        TABLES.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    ##
    ).join(
        subq, subq.c.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID
    ##
    ).group_by(
        TABLES.ZP_TV_TITLE.ZP_TV_ID, TABLES.ZP_IMAGE_SUB_TYPE.ID
    ).order_by(
        TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME.desc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
    ).all()

    return_list = construct_dune_ui_entity_return_list(
        entity_search_results, 'ZP_TV_ID', **kwargs)
    return return_list


def tv_watched(self, **kwargs):
    """
    SELECT zpfgx.ZP_FILM_ID as ZP_FILM_ID, zpft.TITLE as TITLE
    FROM ZP_FILM_GENRE_XREF zpfgx
    JOIN ZP_FILM_TITLE zpft
    ON zpft.ZP_FILM_ID = zpfgx.ZP_FILM_ID
    WHERE zpfgx.ZP_GENRE_ID = ZP_GENRE_ID
    """
    ZP_USER_ID = kwargs['ZP_USER_ID']
    entity_search_results = self.session.query(
        TABLES.ZP_TV_TITLE.TITLE,
        TABLES.ZP_TV_TITLE.ZP_TV_ID,
        TABLES.ZP_TEMPLATE.REF_NAME,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.HASH,
        TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.EXT,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME,
        TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
        TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID')
    ).join(
        TABLES.ZP_USER_TV_ENTITY_XREF,
        and_(
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_ID == TABLES.ZP_TV_TITLE.ID,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
        )
    ).join(
        TABLES.ZP_TV_IMAGE_RENDER_HASH,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID
    ).join(
        TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID ==
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ID,
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
        )
    ).join(
        TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID ==
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID == \
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ID
        )
    ).join(
        TABLES.ZP_TV_FILEFOLDER,
        and_(
            TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_TV_FILEFOLDER.ENABLED == 1
        )
    ).join(
        TABLES.ZP_TEMPLATE, TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
    ).join(
        TABLES.ZP_IMAGE_TYPE,
        and_(
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
            TABLES.ZP_IMAGE_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
            TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
        )
    ).join(
        TABLES.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    ).join(
        TABLES.ZP_USER_TV_EPISODE_WATCHED,
        and_(
            TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID
        )
    ).group_by(
        TABLES.ZP_TV_TITLE.ZP_TV_ID, TABLES.ZP_IMAGE_SUB_TYPE.ID
    ).order_by(
       TABLES.ZP_TV_TITLE.TITLE.asc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
    ).all()
    return_list = construct_dune_ui_entity_return_list(
        entity_search_results, 'ZP_TV_ID', **kwargs)
    return return_list


def tv_to_watch(self, **kwargs):
    """
    SELECT zpfgx.ZP_FILM_ID as ZP_FILM_ID, zpft.TITLE as TITLE
    FROM ZP_FILM_GENRE_XREF zpfgx
    JOIN ZP_FILM_TITLE zpft
    ON zpft.ZP_FILM_ID = zpfgx.ZP_FILM_ID
    WHERE zpfgx.ZP_GENRE_ID = ZP_GENRE_ID
    """
    ZP_USER_ID = kwargs['ZP_USER_ID']
    entity_search_results = self.session.query(
        TABLES.ZP_TV_TITLE.TITLE,
        TABLES.ZP_TV_TITLE.ZP_TV_ID,
        TABLES.ZP_TEMPLATE.REF_NAME,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.HASH,
        TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.EXT,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME,
        TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
        TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID')
    ).join(
        TABLES.ZP_USER_TV_ENTITY_XREF,
        and_(
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_ID == TABLES.ZP_TV_TITLE.ID,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
        )
    ).join(
        TABLES.ZP_TV_IMAGE_RENDER_HASH,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID
    ).join(
        TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID ==
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ID,
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
        )
    ).join(
        TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID ==
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID == \
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ID
        )
    ).join(
        TABLES.ZP_TV_FILEFOLDER,
        and_(
            TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_TV_FILEFOLDER.ENABLED == 1
        )
    ).join(
        TABLES.ZP_TEMPLATE, TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
    ).join(
        TABLES.ZP_IMAGE_TYPE,
        and_(
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
            TABLES.ZP_IMAGE_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
            TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
        )
    ).join(
        TABLES.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    ).join(
        TABLES.ZP_USER_TV_TOWATCH,
        and_(
            TABLES.ZP_USER_TV_TOWATCH.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_TOWATCH.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID
        )
    ).group_by(
        TABLES.ZP_TV_TITLE.ZP_TV_ID, TABLES.ZP_IMAGE_SUB_TYPE.ID
    ).order_by(
       TABLES.ZP_TV_TITLE.TITLE.asc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
    ).all()
    return_list = construct_dune_ui_entity_return_list(
        entity_search_results, 'ZP_TV_ID', **kwargs)
    return return_list


def tv_fav(self, **kwargs):
    """
    SELECT zpfgx.ZP_FILM_ID as ZP_FILM_ID, zpft.TITLE as TITLE
    FROM ZP_FILM_GENRE_XREF zpfgx
    JOIN ZP_FILM_TITLE zpft
    ON zpft.ZP_FILM_ID = zpfgx.ZP_FILM_ID
    WHERE zpfgx.ZP_GENRE_ID = ZP_GENRE_ID
    """
    return_list = []
    ZP_USER_ID = kwargs['ZP_USER_ID']
    entity_search_results = self.session.query(
        TABLES.ZP_TV_TITLE.TITLE,
        TABLES.ZP_TV_TITLE.ZP_TV_ID,
        TABLES.ZP_TEMPLATE.REF_NAME,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.HASH,
        TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.EXT,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME,
        TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
        TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID')
    ).join(
        TABLES.ZP_USER_TV_ENTITY_XREF,
        and_(
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_ID == TABLES.ZP_TV_TITLE.ID,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
        )
    ).join(
        TABLES.ZP_TV_IMAGE_RENDER_HASH,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID
    ).join(
        TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID ==
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ID,
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
        )
    ).join(
        TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID ==
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID == \
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ID
        )
    ).join(
        TABLES.ZP_TV_FILEFOLDER,
        and_(
            TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_TV_FILEFOLDER.ENABLED == 1
        )
    ).join(
        TABLES.ZP_TEMPLATE, TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
    ).join(
        TABLES.ZP_IMAGE_TYPE,
        and_(
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
            TABLES.ZP_IMAGE_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
            TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
        )
    ).join(
        TABLES.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    ).join(
        TABLES.ZP_USER_TV_FAVOURITE,
        and_(
            TABLES.ZP_USER_TV_FAVOURITE.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_FAVOURITE.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID
        )
    ).group_by(
        TABLES.ZP_TV_TITLE.ZP_TV_ID, TABLES.ZP_IMAGE_SUB_TYPE.ID
    ).order_by(
       TABLES.ZP_TV_TITLE.TITLE.asc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
    ).all()
    return_list = construct_dune_ui_entity_return_list(
        entity_search_results, 'ZP_TV_ID', **kwargs)
    return return_list


def tvs_az(self, **kwargs):
    # TODO: change substr to startswith
    # TODO: deal with non ascii letters (create a seperate index table the using unicode to ascii module?)
    return_list = []
    ZP_USER_ID = kwargs['ZP_USER_ID']

    if not re.match(r'''[a-zA-Z]''', kwargs['az'][0][:1]):
        entity_search_results = self.session.query(
            TABLES.ZP_TV_TITLE.TITLE,
            TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_TEMPLATE.REF_NAME,
            TABLES.ZP_TV_IMAGE_RENDER_HASH.HASH,
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.EXT,
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
            TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME,
            TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
            TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID')
        ).join(
            TABLES.ZP_USER_TV_ENTITY_XREF,
            and_(
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_ID == TABLES.ZP_TV_TITLE.ID,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
            )
        ).join(
            TABLES.ZP_TV_IMAGE_RENDER_HASH,
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID
        ).join(
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF,
            and_(
                TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID ==
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ID,
                TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
            )
        ).join(
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF,
            and_(
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID,
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID ==
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID == \
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ID
            )
        ).join(
            TABLES.ZP_TV_FILEFOLDER,
            and_(
                TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
                TABLES.ZP_TV_FILEFOLDER.ENABLED == 1
            )
        ).join(
            TABLES.ZP_TEMPLATE, TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
        ).join(
            TABLES.ZP_IMAGE_TYPE,
            and_(
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
                TABLES.ZP_IMAGE_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
                TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
            )
        ).join(
            TABLES.ZP_IMAGE_SUB_TYPE,
            TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
        ).outerjoin(
            TABLES.ZP_USER_TV_EPISODE_WATCHED,
            and_(
                TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
                TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID
            )
        ).filter(
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'A'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'a'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'B'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'c'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'C'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'd'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'D'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'e'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'E'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'f'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'F'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'g'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'G'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'h'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'H'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'i'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'I'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'j'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'K'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'k'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'K'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'l'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'L'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'm'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'M'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'n'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'N'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'o'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'O'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'p'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'P'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'q'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'Q'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'r'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'R'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 's'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'S'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 't'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'T'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'u'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'U'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'v'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'V'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'w'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'W'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'x'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'X'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'y'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'Y'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'z'),
            ~(func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == 'Z')
        ).group_by(
            TABLES.ZP_TV_TITLE.ZP_TV_ID, TABLES.ZP_IMAGE_SUB_TYPE.ID
        ).order_by(
           TABLES.ZP_TV_TITLE.TITLE.asc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
        ).all()
    else:
        entity_search_results = self.session.query(
            TABLES.ZP_TV_TITLE.TITLE,
            TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_TEMPLATE.REF_NAME,
            TABLES.ZP_TV_IMAGE_RENDER_HASH.HASH,
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.EXT,
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
            TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME,
            TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
            TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID')
        ).join(
            TABLES.ZP_USER_TV_ENTITY_XREF,
            and_(
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_ID == TABLES.ZP_TV_TITLE.ID,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
            )
        ).join(
            TABLES.ZP_TV_IMAGE_RENDER_HASH,
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID
        ).join(
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF,
            and_(
                TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID ==
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ID,
                TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
            )
        ).join(
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF,
            and_(
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID,
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID ==
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID == \
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ID
            )
        ).join(
            TABLES.ZP_TV_FILEFOLDER,
            and_(
                TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
                TABLES.ZP_TV_FILEFOLDER.ENABLED == 1
            )
        ).join(
            TABLES.ZP_TEMPLATE, TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
        ).join(
            TABLES.ZP_IMAGE_TYPE,
            and_(
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
                TABLES.ZP_IMAGE_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
                TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
            )
        ).join(
            TABLES.ZP_IMAGE_SUB_TYPE,
            TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
        ).outerjoin(
            TABLES.ZP_USER_TV_EPISODE_WATCHED,
            and_(
                TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
                TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID
            )
        ).filter(
            or_(
                func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == kwargs['az'][0][:1].upper(),
                func.substr(TABLES.ZP_TV_TITLE.TITLE, 1, 1) == kwargs['az'][0][:1].lower()
            )
        ).group_by(
            TABLES.ZP_TV_TITLE.ZP_TV_ID, TABLES.ZP_IMAGE_SUB_TYPE.ID
        ).order_by(
           TABLES.ZP_TV_TITLE.TITLE.asc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
        ).all()
    return_list = construct_dune_ui_entity_return_list(
        entity_search_results, 'ZP_TV_ID', **kwargs)
    return return_list


def tv_ratings(self, **kwargs):
    return_list = []
    for i in range(1, 6):
        return_list.append({r'::rating::': str(i)})
    return return_list


def tvs_of_rating(self, **kwargs):
    max_db_rating = 10
    ZP_USER_ID = kwargs['ZP_USER_ID']
    rating = int(kwargs['rating'][0])
    rating_max = int(kwargs['rating_max'][0])
    rating_10 = max_db_rating / rating_max
    db_rating_min = int(math.floor((rating - 1) * rating_10) + 1)
    db_rating_max = int(math.floor(rating * rating_10))
    log.debug('rating_max %s, rating %s, db_rating_min %s, db_rating_max %s',
              rating_max, rating, db_rating_min, db_rating_max
              )
    entity_search_results = self.session.query(
        TABLES.ZP_TV_TITLE.TITLE,
        TABLES.ZP_TV_TITLE.ZP_TV_ID,
        TABLES.ZP_TEMPLATE.REF_NAME,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.HASH,
        TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.EXT,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME,
        TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
        TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID')
    ).join(
        TABLES.ZP_USER_TV_ENTITY_XREF,
        and_(
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_ID == TABLES.ZP_TV_TITLE.ID,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
        )
    ).join(
        TABLES.ZP_TV_IMAGE_RENDER_HASH,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID
    ).join(
        TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID ==
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ID,
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
        )
    ).join(
        TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID ==
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID == \
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ID
        )
    ).join(
        TABLES.ZP_TV_FILEFOLDER,
        and_(
            TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_TV_FILEFOLDER.ENABLED == 1
        )
    ).join(
        TABLES.ZP_TEMPLATE, TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
    ).join(
        TABLES.ZP_IMAGE_TYPE,
        and_(
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
            TABLES.ZP_IMAGE_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
            TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
        )
    ).join(
        TABLES.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    ).outerjoin(
        TABLES.ZP_USER_TV_EPISODE_WATCHED,
        and_(
            TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID
        )
    ##
    ).join(
        TABLES.ZP_TV_RATING,
        and_(
            TABLES.ZP_TV_RATING.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            and_(
                TABLES.ZP_TV_RATING.RATING >= db_rating_min,
                TABLES.ZP_TV_RATING.RATING <= db_rating_max
            )
        )
    ##
    ).group_by(
        TABLES.ZP_TV_TITLE.ZP_TV_ID, TABLES.ZP_IMAGE_SUB_TYPE.ID
    ).order_by(
       TABLES.ZP_TV_TITLE.TITLE.asc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
    ).all()
    return_list = construct_dune_ui_entity_return_list(
        entity_search_results, 'ZP_TV_ID', **kwargs)
    return return_list


def tvs_all(self, **kwargs):
    #return_list = []
    ZP_USER_ID = kwargs['ZP_USER_ID']
    entity_search_results = self.session.query(
        TABLES.ZP_TV_TITLE.TITLE,
        TABLES.ZP_TV_TITLE.ZP_TV_ID,
        TABLES.ZP_TEMPLATE.REF_NAME,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.HASH,
        TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.EXT,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME,
        TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
        TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID')
    ).join(
        TABLES.ZP_USER_TV_ENTITY_XREF,
        and_(
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_ID == TABLES.ZP_TV_TITLE.ID,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
        )
    ).join(
        TABLES.ZP_TV_IMAGE_RENDER_HASH,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID
    ).join(
        TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID ==
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ID,
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
        )
    ).join(
        TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID ==
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID == \
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ID
        )
    ).join(
        TABLES.ZP_TV_FILEFOLDER,
        and_(
            TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_TV_FILEFOLDER.ENABLED == 1
        )
    ).join(
        TABLES.ZP_TEMPLATE, TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
    ).join(
        TABLES.ZP_IMAGE_TYPE,
        and_(
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
            TABLES.ZP_IMAGE_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
            TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
        )
    ).join(
        TABLES.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    ).outerjoin(
        TABLES.ZP_USER_TV_EPISODE_WATCHED,
        and_(
            TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID
        )
    ).group_by(
        TABLES.ZP_TV_TITLE.ZP_TV_ID, TABLES.ZP_IMAGE_SUB_TYPE.ID
    ).order_by(
       TABLES.ZP_TV_TITLE.TITLE.asc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
    ).all()
    return_list = construct_dune_ui_entity_return_list(
        entity_search_results, 'ZP_TV_ID', **kwargs)
    return return_list


def tvs_new(self, **kwargs):
    ZP_USER_ID = kwargs['ZP_USER_ID']
    entity_search_results = self.session.query(
        TABLES.ZP_TV_TITLE.TITLE,
        TABLES.ZP_TV_TITLE.ZP_TV_ID,
        TABLES.ZP_TEMPLATE.REF_NAME,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.HASH,
        TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.EXT,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME,
        TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
        TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID')
    ).join(
        TABLES.ZP_USER_TV_ENTITY_XREF,
        and_(
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_ID == TABLES.ZP_TV_TITLE.ID,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
        )
    ).join(
        TABLES.ZP_TV_IMAGE_RENDER_HASH,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID
    ).join(
        TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID ==
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ID,
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
        )
    ).join(
        TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID ==
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID == \
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ID
        )
    ).join(
        TABLES.ZP_TV_FILEFOLDER,
        and_(
            TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_TV_FILEFOLDER.ENABLED == 1
        )
    ).join(
        TABLES.ZP_TEMPLATE, TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
    ).join(
        TABLES.ZP_IMAGE_TYPE,
        and_(
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
            TABLES.ZP_IMAGE_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
            TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
        )
    ).join(
        TABLES.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    ).join(
        TABLES.ZP_TV, TABLES.ZP_TV.ID == TABLES.ZP_TV_TITLE.ZP_TV_ID
    ).outerjoin(
        TABLES.ZP_USER_TV_EPISODE_WATCHED,
        and_(
            TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID
        )
    ).group_by(
        TABLES.ZP_TV_TITLE.ZP_TV_ID, TABLES.ZP_IMAGE_SUB_TYPE.ID
    ).order_by(
        TABLES.ZP_TV.ADDED_DATE_TIME.desc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
    ).limit(35).all()
    return_list = construct_dune_ui_entity_return_list(
        entity_search_results, 'ZP_TV_ID', **kwargs)
    return return_list


def tv_synopsis_bg_image_path(self, ZP_TV_ID, ZP_USER_ID, ZP_DUNE_ID, root_render_image_url_http):
    try:
        result = self.session.query(
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_ID,
            TABLES.ZP_TV_IMAGE_RENDER_HASH.HASH,
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.EXT,
            TABLES.ZP_TEMPLATE.REF_NAME
        ).filter(
            ##
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID ==
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ID,
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == ZP_DUNE_ID,
            ##
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID,
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ID == TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID,
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == 2,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == ZP_TV_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == ZP_USER_ID
        ).one()
    except orm.exc.NoResultFound as e:
        log.warning('Cannot find ZP_TV_IMAGE_RENDER_HASH_ID for')
    else:
        return '{0}/tv/{1}/{2}/.synopsis.{3}.{4}'.format(root_render_image_url_http,
                                                         result.REF_NAME,
                                                         result.ZP_TV_ID,
                                                         result.HASH,
                                                         result.EXT
                                                         )


def tv_list_season(self, **kwargs):
    """
    SELECT zpfgx.ZP_TV_ID as ZP_TV_ID, zpft.TITLE as TITLE
    FROM ZP_TV_GENRE_XREF zpfgx
    JOIN ZP_TV_TITLE zpft
    ON zpft.ZP_TV_ID = zpfgx.ZP_TV_ID
    WHERE zpfgx.ZP_TV_GENRE_ID = ZP_GENRE_ID
    """
    return_list = []
    ZP_TV_ID = kwargs['ZP_TV_ID'][0]
    # print(ZP_TV_ID)
    tv_season = self.session.query(distinct(TABLES.ZP_TV_EPISODE.SEASON).label('DISTINCT_SEASON')).filter(
        TABLES.ZP_TV_EPISODE.ZP_TV_ID == TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID,
        TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == ZP_TV_ID
    ).order_by(
        asc(TABLES.ZP_TV_EPISODE.SEASON)).all()
    for result in tv_season:
        return_list.append({r'::SEASON::': str(result.DISTINCT_SEASON)})
    return return_list


def tv_season_episode(self, **kwargs):
    """
    SELECT DISTINCT(ZP_TV_EPISODE.EPISODE), ZP_TV_EPISODE.ID
    FROM `ZP_TV_EPISODE`, ZP_TV_FILEFOLDER
    where ZP_TV_EPISODE.ZP_TV_FILEFOLDER_ID = ZP_TV_FILEFOLDER.ID
    and ZP_TV_FILEFOLDER.ZP_TV_ID = 111
    and ZP_TV_EPISODE.SEASON = 1
    order by ZP_TV_EPISODE.EPISODE asc
    """
    return_list = []
    ZP_TV_ID = kwargs['ZP_TV_ID'][0]
    ZP_USER_ID = kwargs['ZP_USER_ID']
    SEASON = kwargs['SEASON'][0]
    # print(ZP_TV_ID, ZP_USER_ID, SEASON)
    tv_season_episode = self.session.query(
        TABLES.ZP_TV_EPISODE.EPISODE,
        TABLES.ZP_TV_EPISODE.ZP_TV_EPISODE_FILEFOLDER_ID,
        TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.HASH,
        TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.EXT,
        TABLES.ZP_TV_EPISODE_IMAGE_SUB_TYPE_XREF.pre_ident,
        TABLES.ZP_TEMPLATE.REF_NAME,
        TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME
    ).join(
        TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.FIRST_EPISODE == TABLES.ZP_TV_EPISODE.EPISODE,
            TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.SEASON == TABLES.ZP_TV_EPISODE.SEASON,
            TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID,
            TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == ZP_USER_ID
        )
    ).join(
        TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH,
        TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID ==
        TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ID
    ).join(
        TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID ==
            TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ID,
            TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
        )
    ).join(
        TABLES.ZP_TV_EPISODE_IMAGE_SUB_TYPE_XREF,
        TABLES.ZP_TV_EPISODE_IMAGE_SUB_TYPE_XREF.ZP_IMAGE_SUB_TYPE == \
        TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    ).join(
        ##
        TABLES.ZP_TEMPLATE, TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
    ).join(
        ##
        TABLES.ZP_IMAGE_TYPE,
        and_(
            TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
            TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
        )
    ).join(
        TABLES.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    ).outerjoin(
        TABLES.ZP_USER_TV_EPISODE_WATCHED,
        and_(
            TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_TV_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID,
            TABLES.ZP_USER_TV_EPISODE_WATCHED.SEASON == TABLES.ZP_TV_EPISODE.SEASON,
            TABLES.ZP_USER_TV_EPISODE_WATCHED.EPISODE == TABLES.ZP_TV_EPISODE.EPISODE,
            TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_USER_ID == TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_USER_ID
        )
    ).filter(
        TABLES.ZP_TV_EPISODE.ZP_TV_ID == ZP_TV_ID,
        TABLES.ZP_TV_EPISODE.SEASON == SEASON
        # TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID == 3,

        #((TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_IMAGE_SUB_TYPE == case(
        #    [(TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME != None, 3)], else_=1)) |
        # (TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_IMAGE_SUB_TYPE == case(
        #     [(TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME != None, 4)], else_=2)))
    #).having(
    #    or_(
    #        and_(
    #            func.count(TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE.distinct()) <= 3,
    #            TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME == None,
    #            TABLES.ZP_IMAGE_SUB_TYPE.ID.in_((1,2))
    #        ),
    #        and_(
    #            func.count(TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE.distinct()) <= 3,
    #            TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME != None,
    #            TABLES.ZP_IMAGE_SUB_TYPE.ID.in_((1,2,3))
    #        ),
    #        and_(
    #            func.count(TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE.distinct()) >= 4,
    #            TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME == None,
    #            TABLES.ZP_IMAGE_SUB_TYPE.ID.in_((1,2))
    #        ),
    #        and_(
    #            func.count(TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE.distinct()) >= 4,
    #            TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME != None,
    #            TABLES.ZP_IMAGE_SUB_TYPE.ID.in_((3,4))
    #        )
    #    )
    ).order_by(
        TABLES.ZP_TV_EPISODE.EPISODE.asc(), TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE.asc()
    ).all()
    tv_season_dict = {}
    log.debug('tv_season_dict %s', pprint.pformat(tv_season_dict))
    for result in tv_season_episode:
        # return_list.append({r'::EPISODE_NUM::':str(result.DISTINCT_EPISODE),
        #					r'::ZP_TV_EPISODE_ID::':str(result.ID),
        #					r'::icon_url::': '{0}/tv/{1}/{2}/.episode_icon.{3}_{4}.{5}.png'.format(kwargs['root_render_image_url_http'],
        #																result.TEMPLATE_NAME,
        #																ZP_TV_ID,
        #																SEASON.zfill(4),
        #																str(result.EPISODE).zfill(4),
        #																result.HASH)})
        # print(result.ID)
        TEMPLATE_NAME = result.REF_NAME
        if result.EPISODE not in tv_season_dict:
            tv_season_dict[result.EPISODE] = {}
            tv_season_dict[result.EPISODE]['ZP_TV_EPISODE_FILEFOLDER_ID'] = result.ZP_TV_EPISODE_FILEFOLDER_ID
        if is_even(result.ZP_IMAGE_SUB_TYPE):
            if (result.ZP_IMAGE_SUB_TYPE == 4 and result.DATETIME is not None) or \
                (result.ZP_IMAGE_SUB_TYPE == 2 and result.DATETIME is None):
                tv_season_dict[result.EPISODE]['icon_sel'] = {}
                tv_season_dict[result.EPISODE]['icon_sel']['hash'] = result.HASH
                tv_season_dict[result.EPISODE]['icon_sel']['pre_ident'] = result.pre_ident
                tv_season_dict[result.EPISODE]['icon_sel']['ext'] = result.EXT
        else:
            if (result.ZP_IMAGE_SUB_TYPE == 3 and result.DATETIME is not None) or \
                (result.ZP_IMAGE_SUB_TYPE == 1 and result.DATETIME is None):
                tv_season_dict[result.EPISODE]['icon'] = {}
                tv_season_dict[result.EPISODE]['icon']['hash'] = result.HASH
                tv_season_dict[result.EPISODE]['icon']['pre_ident'] = result.pre_ident
                tv_season_dict[result.EPISODE]['icon']['ext'] = result.EXT
    # print(tv_season_dict[result.DISTINCT_EPISODE])
    log.debug('tv_season_dict %s', pprint.pformat(tv_season_dict))
    # todo move away from TABLES.ZP_TV_EPISODE_IMAGE_SUB_TYPE_XREF.pre_ident and use
    # ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT
    for episode in sorted(tv_season_dict):
        log.warning(tv_season_dict[episode])
        episode_dict = {}
        episode_dict[r'::EPISODE_NUM::'] = str(episode)
        episode_dict[r'::ZP_TV_EPISODE_FILEFOLDER_ID::'] = str(tv_season_dict[episode]['ZP_TV_EPISODE_FILEFOLDER_ID'])
        if 'icon' in tv_season_dict[episode]:
            episode_dict[r'::icon_url::'] = '{0}/tv/{1}/{2}/.{3}.{4}_{5}.{6}.{7}'.format(
                                        kwargs['root_render_image_url_http'],
                                        TEMPLATE_NAME,
                                        ZP_TV_ID,
                                        tv_season_dict[episode]['icon']['pre_ident'],
                                        SEASON.zfill(4),
                                        str(episode).zfill(4),
                                        tv_season_dict[episode]['icon']['hash'],
                                        tv_season_dict[episode]['icon']['ext']
                                    )
        if 'icon_sel' in tv_season_dict[episode]:
            episode_dict['::icon_sel_url::'] = '{0}/tv/{1}/{2}/.{3}.{4}_{5}.{6}.{7}'.format(
                                    kwargs['root_render_image_url_http'],
                                    TEMPLATE_NAME,
                                    ZP_TV_ID,
                                    tv_season_dict[episode]['icon_sel']['pre_ident'],
                                    SEASON.zfill(4),
                                    str(episode).zfill(4),
                                    tv_season_dict[episode]['icon_sel']['hash'],
                                    tv_season_dict[episode]['icon_sel']['ext']
                                )

        # print(tv_season_dict)
        return_list.append(episode_dict)
    log.debug('return_list %s', pprint.pformat(return_list))
    return return_list


def tv_in_genre(self, **kwargs):
    """
    SELECT zpfgx.ZP_TV_ID as ZP_TV_ID, zpft.TITLE as TITLE
    FROM ZP_TV_GENRE_XREF zpfgx
    JOIN ZP_TV_TITLE zpft
    ON zpft.ZP_TV_ID = zpfgx.ZP_TV_ID
    WHERE zpfgx.ZP_TV_GENRE_ID = ZP_GENRE_ID
    """
    return_list = []
    ZP_USER_ID = kwargs['ZP_USER_ID']
    ZP_GENRE_ID = kwargs['ZP_GENRE_ID'][0]
    if re.match(r"""^\d+((\,\d+)+)?$""", ZP_GENRE_ID):

        genre_list = string_to_list(ZP_GENRE_ID, ',')
        genre_list = [int(i) for i in genre_list]
        entity_search_results = self.session.query(
            TABLES.ZP_TV_TITLE.TITLE,
            TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_TEMPLATE.REF_NAME,
            TABLES.ZP_TV_IMAGE_RENDER_HASH.HASH,
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.EXT,
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
            TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME,
            TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
            TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID')
        ).join(
            TABLES.ZP_USER_TV_ENTITY_XREF,
            and_(
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_ID == TABLES.ZP_TV_TITLE.ID,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
            )
        ).join(
            TABLES.ZP_TV_IMAGE_RENDER_HASH,
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID
        ).join(
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF,
            and_(
                TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID ==
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ID,
                TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
            )
        ).join(
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF,
            and_(
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID,
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID ==
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID == \
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ID
            )
        ).join(
            TABLES.ZP_TV_FILEFOLDER,
            and_(
                TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
                TABLES.ZP_TV_FILEFOLDER.ENABLED == 1
            )
        ).join(
            TABLES.ZP_TEMPLATE, TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
        ).join(
            TABLES.ZP_IMAGE_TYPE,
            and_(
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
                TABLES.ZP_IMAGE_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
                TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
            )
        ).join(
            TABLES.ZP_IMAGE_SUB_TYPE,
            TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
        ##
        ).join(
            TABLES.ZP_TV_GENRE_XREF,
            and_(
                TABLES.ZP_TV_GENRE_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
                TABLES.ZP_TV_GENRE_XREF.ZP_GENRE_ID.in_(genre_list),
            )
        ##
        ).outerjoin(
            TABLES.ZP_USER_TV_EPISODE_WATCHED,
            and_(
                TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
                TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID
            )
        ).group_by(
            TABLES.ZP_TV_TITLE.ZP_TV_ID, TABLES.ZP_IMAGE_SUB_TYPE.ID
        ).order_by(
           TABLES.ZP_TV_TITLE.TITLE.asc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
        ).all()
        return_list = construct_dune_ui_entity_return_list(
            entity_search_results, 'ZP_TV_ID', **kwargs)
    return return_list


def tv_fav_bg_image_path(self, ZP_TV_ID, ZP_USER_ID):
    favourited = False
    try:
        qry_ZP_USER_TV_FAVOURITE = self.session.query(TABLES.ZP_USER_TV_FAVOURITE).filter(
            TABLES.ZP_USER_TV_FAVOURITE.ZP_TV_ID == ZP_TV_ID,
            TABLES.ZP_USER_TV_FAVOURITE.ZP_USER_ID == ZP_USER_ID)
        qry_ZP_USER_TV_FAVOURITE.one()
    except orm.exc.NoResultFound:
        add_ZP_USER_TV_FAVOURITE = TABLES.ZP_USER_TV_FAVOURITE(ZP_TV_ID=ZP_TV_ID,
                                                               ZP_USER_ID=ZP_USER_ID)
        self.session.add(add_ZP_USER_TV_FAVOURITE)
        commit(self.session)
        favourited = True
    else:
        qry_ZP_USER_TV_FAVOURITE.delete()
        commit(self.session)

    if favourited == True:
        return 'added'
    else:
        return 'removed'


def tv_tow_bg_image_path(self, ZP_TV_ID, ZP_USER_ID):
    favourited = False
    try:
        qry_ZP_USER_TV_TOWATCH = self.session.query(TABLES.ZP_USER_TV_TOWATCH).filter(
            TABLES.ZP_USER_TV_TOWATCH.ZP_TV_ID == ZP_TV_ID,
            TABLES.ZP_USER_TV_TOWATCH.ZP_USER_ID == ZP_USER_ID)
        qry_ZP_USER_TV_TOWATCH.one()
    except orm.exc.NoResultFound:
        add_ZP_USER_TV_TOWATCH = TABLES.ZP_USER_TV_TOWATCH(ZP_TV_ID=ZP_TV_ID,
                                                           ZP_USER_ID=ZP_USER_ID)
        self.session.add(add_ZP_USER_TV_TOWATCH)
        commit(self.session)
        favourited = True
    else:
        qry_ZP_USER_TV_TOWATCH.delete()
        commit(self.session)

    if favourited == True:
        return 'added'
    else:
        return 'removed'


def tv_search_results(self, **kwargs):
    search_string = urllib.unquote(kwargs['search_string'][0])
    ZP_USER_ID = kwargs['ZP_USER_ID']
    if kwargs['search_type'][0] == 'a':
        search_string = r"""%{0}%""".format(search_string)
    elif kwargs['search_type'][0] == 'b':
        search_string = r"""{0}%""".format(search_string)
    else:
        search_string = r"""%{0}""".format(search_string)
    entity_search_results = self.session.query(
        TABLES.ZP_TV_TITLE.TITLE,
        TABLES.ZP_TV_TITLE.ZP_TV_ID,
        TABLES.ZP_TEMPLATE.REF_NAME,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.HASH,
        TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.EXT,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_USER_TV_EPISODE_WATCHED.DATETIME,
        TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
        TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID')
    ).join(
        TABLES.ZP_USER_TV_ENTITY_XREF,
        and_(
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_ID == TABLES.ZP_TV_TITLE.ID,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1,
            TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
        )
    ).join(
        TABLES.ZP_TV_IMAGE_RENDER_HASH,
        TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID
    ).join(
        TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID ==
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ID,
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
        )
    ).join(
        TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID ==
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID == \
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ID
        )
    ).join(
        TABLES.ZP_TV_FILEFOLDER,
        and_(
            TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_TV_FILEFOLDER.ENABLED == 1
        )
    ).join(
        TABLES.ZP_TEMPLATE, TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
    ).join(
        TABLES.ZP_IMAGE_TYPE,
        and_(
            TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
            TABLES.ZP_IMAGE_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
            TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
        )
    ).join(
        TABLES.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    ).outerjoin(
        TABLES.ZP_USER_TV_EPISODE_WATCHED,
        and_(
            TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_TV_ID == TABLES.ZP_TV_TITLE.ZP_TV_ID,
            TABLES.ZP_USER_TV_EPISODE_WATCHED.ZP_USER_ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID
        )
    ##
    ).filter(
        TABLES.ZP_TV_TITLE.TITLE.like(search_string)
    ##
    ).group_by(
        TABLES.ZP_TV_TITLE.ZP_TV_ID, TABLES.ZP_IMAGE_SUB_TYPE.ID
    ).order_by(
       TABLES.ZP_TV_TITLE.TITLE.asc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
    ).all()
    return_list = construct_dune_ui_entity_return_list(
        entity_search_results, 'ZP_TV_ID', **kwargs)
    return return_list


def tv_search(self, **kwargs):
    return []