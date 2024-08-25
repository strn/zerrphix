# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import re
import urllib

from sqlalchemy import func, orm, asc, desc, and_, or_

from zerrphix.httpserver.dune.film_collection import *
from zerrphix.util.text import string_to_list
from zerrphix.util.text import date_time
from zerrphix.util.text import construct_dune_ui_entity_return_list
from zerrphix.db import commit
from zerrphix.db.tables import TABLES
import logging
import math

log = logging.getLogger(__name__)


def film_fav(self, **kwargs):
    pass


def film_user_last_watched(self, **kwargs):
    ZP_USER_ID = kwargs['ZP_USER_ID']
    log.debug('image_type %s', kwargs['image_type'])
    subq = self.session.query(
        TABLES.ZP_USER_FILM_WATCHED.ZP_FILM_ID
    ).filter(
        TABLES.ZP_USER_FILM_WATCHED.ZP_USER_ID == ZP_USER_ID
    ).order_by(
        TABLES.ZP_USER_FILM_WATCHED.DATETIME.desc()
    ).limit(1).subquery()
    entity_search_results = self.session.query(
        TABLES.ZP_FILM_TITLE.TITLE,
        TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
        TABLES.ZP_TEMPLATE.REF_NAME,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.HASH,
        TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.EXT,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_USER_FILM_WATCHED.DATETIME,
        TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
        TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID'),
        TABLES.ZP_FILM.ZP_FILM_COLLECTION_ID
    ).join(
        TABLES.ZP_USER_FILM_ENTITY_XREF,
        and_(
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID == TABLES.ZP_FILM_TITLE.ID,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
        )
    ).join(
        TABLES.ZP_FILM_IMAGE_RENDER_HASH,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID
    ).join(
        TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID ==
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID,
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
        )
    ).join(
        TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID ==
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID == \
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID
        )
    ).join(
        TABLES.ZP_FILM_FILEFOLDER,
        and_(
            TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_FILM_FILEFOLDER.ENABLED == 1
        )
    ).join(
        TABLES.ZP_TEMPLATE, TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
    ).join(
        TABLES.ZP_IMAGE_TYPE,
        and_(
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
            TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
        )
    ).join(
        TABLES.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    ).join(
        TABLES.ZP_FILM,
        and_(
            TABLES.ZP_FILM.ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER.ID
        )
    ##
    ).join(
        subq, subq.c.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID
    ##
    ).order_by(
        TABLES.ZP_USER_FILM_WATCHED.DATETIME.desc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
    ).all()

    return_list = construct_dune_ui_entity_return_list(
        entity_search_results, 'ZP_FILM_ID', **kwargs)
    return return_list


def film_search_results(self, **kwargs):
    search_string = urllib.unquote(kwargs['search_string'][0])
    ZP_USER_ID = kwargs['ZP_USER_ID']
    if kwargs['search_type'][0] == 'a':
        search_string = r"""%{0}%""".format(search_string)
    elif kwargs['search_type'][0] == 'b':
        search_string = r"""{0}%""".format(search_string)
    else:
        search_string = r"""%{0}""".format(search_string)
    entity_search_results = self.session.query(
        TABLES.ZP_FILM_TITLE.TITLE,
        TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
        TABLES.ZP_TEMPLATE.REF_NAME,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.HASH,
        TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.EXT,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_USER_FILM_WATCHED.DATETIME,
        TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
        TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID'),
        TABLES.ZP_FILM.ZP_FILM_COLLECTION_ID
    ).join(
        TABLES.ZP_USER_FILM_ENTITY_XREF,
        and_(
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID == TABLES.ZP_FILM_TITLE.ID,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
        )
    ).join(
        TABLES.ZP_FILM_IMAGE_RENDER_HASH,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID
    ).join(
        TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID ==
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID,
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
        )
    ).join(
        TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID ==
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID == \
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID
        )
    ).join(
        TABLES.ZP_FILM_FILEFOLDER,
        and_(
            TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_FILM_FILEFOLDER.ENABLED == 1
        )
    ).join(
        TABLES.ZP_TEMPLATE, TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
    ).join(
        TABLES.ZP_IMAGE_TYPE,
        and_(
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
            TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
        )
    ).join(
        TABLES.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    ).join(
        TABLES.ZP_FILM,
        and_(
            TABLES.ZP_FILM.ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER.ID
        )
    ).outerjoin(
        TABLES.ZP_USER_FILM_WATCHED,
        and_(
            TABLES.ZP_USER_FILM_WATCHED.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_WATCHED.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID
        )
    ##
    ).filter(
        TABLES.ZP_FILM_TITLE.TITLE.like(search_string)
    ##
    ).order_by(
        TABLES.ZP_FILM_TITLE.TITLE.asc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
    ).all()

    return_list = construct_dune_ui_entity_return_list(
        entity_search_results, 'ZP_FILM_ID', **kwargs)
    return return_list


def films_in_genre(self, **kwargs):
    """
    SELECT zpfgx.ZP_FILM_ID as ZP_FILM_ID, zpft.TITLE as TITLE
    FROM ZP_FILM_GENRE_XREF zpfgx
    JOIN ZP_FILM_TITLE zpft
    ON zpft.ZP_FILM_ID = zpfgx.ZP_FILM_ID
    WHERE zpfgx.ZP_GENRE_ID = ZP_GENRE_ID
    """
    return_list = []
    ZP_USER_ID = kwargs['ZP_USER_ID']
    ZP_GENRE_ID = kwargs['ZP_GENRE_ID'][0]
    if re.match(r"""^\d+((\,\d+)+)?$""", ZP_GENRE_ID):

        genre_list = string_to_list(ZP_GENRE_ID, ',')
        genre_list = [int(i) for i in genre_list]

        # return sorted(return_list, key=lambda k: k['::TITLE::'])

        entity_search_results = self.session.query(
            TABLES.ZP_FILM_TITLE.TITLE,
            TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_TEMPLATE.REF_NAME,
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.HASH,
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.EXT,
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
            TABLES.ZP_USER_FILM_WATCHED.DATETIME,
            TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
            TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID'),
            TABLES.ZP_FILM.ZP_FILM_COLLECTION_ID
        ).join(
            TABLES.ZP_USER_FILM_ENTITY_XREF,
            and_(
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID == TABLES.ZP_FILM_TITLE.ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
            )
        ).join(
            TABLES.ZP_FILM_IMAGE_RENDER_HASH,
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID
        ).join(
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF,
            and_(
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID ==
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID,
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
            )
        ).join(
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF,
            and_(
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID,
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID ==
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID,
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID == \
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID
            )
        ).join(
            TABLES.ZP_FILM_FILEFOLDER,
            and_(
                TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                TABLES.ZP_FILM_FILEFOLDER.ENABLED == 1
            )
        ).join(
            TABLES.ZP_TEMPLATE, TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
        ).join(
            TABLES.ZP_IMAGE_TYPE,
            and_(
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
                TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
            )
        ).join(
            TABLES.ZP_IMAGE_SUB_TYPE,
            TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
        ).join(
            TABLES.ZP_FILM,
            and_(
                TABLES.ZP_FILM.ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER.ID
            )
        ##
        ).join(
            TABLES.ZP_FILM_GENRE_XREF,
            and_(
                TABLES.ZP_FILM_GENRE_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                TABLES.ZP_FILM_GENRE_XREF.ZP_GENRE_ID.in_(genre_list),
            )
        ##
        ).outerjoin(
            TABLES.ZP_USER_FILM_WATCHED,
            and_(
                TABLES.ZP_USER_FILM_WATCHED.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                TABLES.ZP_USER_FILM_WATCHED.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID
            )
        ).order_by(
            TABLES.ZP_FILM_TITLE.TITLE.asc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
        ).all()

        return_list = construct_dune_ui_entity_return_list(
            entity_search_results, 'ZP_FILM_ID', **kwargs)
    return return_list


def films_watched(self, **kwargs):
    """
    SELECT zpfgx.ZP_FILM_ID as ZP_FILM_ID, zpft.TITLE as TITLE
    FROM ZP_FILM_GENRE_XREF zpfgx
    JOIN ZP_FILM_TITLE zpft
    ON zpft.ZP_FILM_ID = zpfgx.ZP_FILM_ID
    WHERE zpfgx.ZP_GENRE_ID = ZP_GENRE_ID
    """
    ZP_USER_ID = kwargs['ZP_USER_ID']
    entity_search_results = self.session.query(
        TABLES.ZP_FILM_TITLE.TITLE,
        TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
        TABLES.ZP_TEMPLATE.REF_NAME,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.HASH,
        TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.EXT,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_USER_FILM_WATCHED.DATETIME,
        TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
        TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID'),
        TABLES.ZP_FILM.ZP_FILM_COLLECTION_ID
    ).join(
        TABLES.ZP_USER_FILM_ENTITY_XREF,
        and_(
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID == TABLES.ZP_FILM_TITLE.ID,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
        )
    ).join(
        TABLES.ZP_FILM_IMAGE_RENDER_HASH,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID
    ).join(
        TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID ==
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID,
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
        )
    ).join(
        TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID ==
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID == \
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID
        )
    ).join(
        TABLES.ZP_FILM_FILEFOLDER,
        and_(
            TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_FILM_FILEFOLDER.ENABLED == 1
        )
    ).join(
        TABLES.ZP_TEMPLATE, TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
    ).join(
        TABLES.ZP_IMAGE_TYPE,
        and_(
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
            TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
        )
    ).join(
        TABLES.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    ).join(
        TABLES.ZP_FILM,
        and_(
            TABLES.ZP_FILM.ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER.ID
        )
    ##
    ).join(
        TABLES.ZP_USER_FILM_WATCHED,
        and_(
            TABLES.ZP_USER_FILM_WATCHED.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_WATCHED.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID
        )
    ##
    ).order_by(
    ##
        TABLES.ZP_USER_FILM_WATCHED.DATETIME.desc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
    ##
    ).all()

    return_list = construct_dune_ui_entity_return_list(
        entity_search_results, 'ZP_FILM_ID', **kwargs)
    return return_list


def films_towatch(self, **kwargs):
    """
    SELECT zpfgx.ZP_FILM_ID as ZP_FILM_ID, zpft.TITLE as TITLE
    FROM ZP_FILM_GENRE_XREF zpfgx
    JOIN ZP_FILM_TITLE zpft
    ON zpft.ZP_FILM_ID = zpfgx.ZP_FILM_ID
    WHERE zpfgx.ZP_GENRE_ID = ZP_GENRE_ID
    """
    ZP_USER_ID = kwargs['ZP_USER_ID']

    entity_search_results = self.session.query(
        TABLES.ZP_FILM_TITLE.TITLE,
        TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
        TABLES.ZP_TEMPLATE.REF_NAME,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.HASH,
        TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.EXT,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_USER_FILM_WATCHED.DATETIME,
        TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
        TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID'),
        TABLES.ZP_FILM.ZP_FILM_COLLECTION_ID
    ).join(
        TABLES.ZP_USER_FILM_ENTITY_XREF,
        and_(
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID == TABLES.ZP_FILM_TITLE.ID,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
        )
    ).join(
        TABLES.ZP_FILM_IMAGE_RENDER_HASH,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID
    ).join(
        TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID ==
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID,
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
        )
    ).join(
        TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID ==
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID == \
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID
        )
    ).join(
        TABLES.ZP_FILM_FILEFOLDER,
        and_(
            TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_FILM_FILEFOLDER.ENABLED == 1
        )
    ).join(
        TABLES.ZP_TEMPLATE, TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
    ).join(
        TABLES.ZP_IMAGE_TYPE,
        and_(
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
            TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
        )
    ).join(
        TABLES.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    ).join(
        TABLES.ZP_FILM,
        and_(
            TABLES.ZP_FILM.ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER.ID
        )
    ##
    ).join(
        TABLES.ZP_USER_FILM_TOWATCH,
        and_(
            TABLES.ZP_USER_FILM_TOWATCH.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_TOWATCH.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID
        )
    ##
    ).outerjoin(
        TABLES.ZP_USER_FILM_WATCHED,
        and_(
            TABLES.ZP_USER_FILM_WATCHED.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_WATCHED.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID
        )
    ).order_by(
        TABLES.ZP_FILM_TITLE.TITLE.asc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
    ).all()

    return_list = construct_dune_ui_entity_return_list(
        entity_search_results, 'ZP_FILM_ID', **kwargs)
    return return_list


def films_fav(self, **kwargs):
    """
    SELECT zpfgx.ZP_FILM_ID as ZP_FILM_ID, zpft.TITLE as TITLE
    FROM ZP_FILM_GENRE_XREF zpfgx
    JOIN ZP_FILM_TITLE zpft
    ON zpft.ZP_FILM_ID = zpfgx.ZP_FILM_ID
    WHERE zpfgx.ZP_GENRE_ID = ZP_GENRE_ID
    """
    ZP_USER_ID = kwargs['ZP_USER_ID']
    entity_search_results = self.session.query(
        TABLES.ZP_FILM_TITLE.TITLE,
        TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
        TABLES.ZP_TEMPLATE.REF_NAME,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.HASH,
        TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.EXT,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_USER_FILM_WATCHED.DATETIME,
        TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
        TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID'),
        TABLES.ZP_FILM.ZP_FILM_COLLECTION_ID
    ).join(
        TABLES.ZP_USER_FILM_ENTITY_XREF,
        and_(
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID == TABLES.ZP_FILM_TITLE.ID,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
        )
    ).join(
        TABLES.ZP_FILM_IMAGE_RENDER_HASH,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID
    ).join(
        TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID ==
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID,
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
        )
    ).join(
        TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID ==
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID == \
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID
        )
    ).join(
        TABLES.ZP_FILM_FILEFOLDER,
        and_(
            TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_FILM_FILEFOLDER.ENABLED == 1
        )
    ).join(
        TABLES.ZP_TEMPLATE, TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
    ).join(
        TABLES.ZP_IMAGE_TYPE,
        and_(
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
            TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
        )
    ).join(
        TABLES.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    ).join(
        TABLES.ZP_FILM,
        and_(
            TABLES.ZP_FILM.ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER.ID
        )
    ##
    ).join(
        TABLES.ZP_USER_FILM_FAVOURITE,
        and_(
            TABLES.ZP_USER_FILM_FAVOURITE.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_FAVOURITE.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID
        )
    ##
    ).outerjoin(
        TABLES.ZP_USER_FILM_WATCHED,
        and_(
            TABLES.ZP_USER_FILM_WATCHED.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_WATCHED.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID
        )
    ).order_by(
        TABLES.ZP_FILM_TITLE.TITLE.asc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
    ).all()

    return_list = construct_dune_ui_entity_return_list(
        entity_search_results, 'ZP_FILM_ID', **kwargs)
    return return_list


def films_of_rating(self, **kwargs):
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
        TABLES.ZP_FILM_TITLE.TITLE,
        TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
        TABLES.ZP_TEMPLATE.REF_NAME,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.HASH,
        TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.EXT,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_USER_FILM_WATCHED.DATETIME,
        TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
        TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID'),
        TABLES.ZP_FILM.ZP_FILM_COLLECTION_ID
    ).join(
        TABLES.ZP_USER_FILM_ENTITY_XREF,
        and_(
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID == TABLES.ZP_FILM_TITLE.ID,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
        )
    ).join(
        TABLES.ZP_FILM_IMAGE_RENDER_HASH,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID
    ).join(
        TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID ==
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID,
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
        )
    ).join(
        TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID ==
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID == \
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID
        )
    ).join(
        TABLES.ZP_FILM_FILEFOLDER,
        and_(
            TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_FILM_FILEFOLDER.ENABLED == 1
        )
    ).join(
        TABLES.ZP_TEMPLATE, TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
    ).join(
        TABLES.ZP_IMAGE_TYPE,
        and_(
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
            TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
        )
    ).join(
        TABLES.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    ).join(
        TABLES.ZP_FILM,
        and_(
            TABLES.ZP_FILM.ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER.ID
        )
    ##
    ).join(
        TABLES.ZP_FILM_RATING,
        and_(
            TABLES.ZP_FILM_RATING.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            and_(
                TABLES.ZP_FILM_RATING.RATING >= db_rating_min,
                TABLES.ZP_FILM_RATING.RATING <= db_rating_max
            )
        )
    ##
    ).outerjoin(
        TABLES.ZP_USER_FILM_WATCHED,
        and_(
            TABLES.ZP_USER_FILM_WATCHED.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_WATCHED.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID
        )
    ).order_by(
        TABLES.ZP_FILM_TITLE.TITLE.asc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
    ).all()

    return_list = construct_dune_ui_entity_return_list(
        entity_search_results, 'ZP_FILM_ID', **kwargs)
    return return_list


def films_hd(self, **kwargs):
    ZP_USER_ID = kwargs['ZP_USER_ID']
    entity_search_results = self.session.query(
        TABLES.ZP_FILM_TITLE.TITLE,
        TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
        TABLES.ZP_TEMPLATE.REF_NAME,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.HASH,
        TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.EXT,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_USER_FILM_WATCHED.DATETIME,
        TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
        TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID'),
        TABLES.ZP_FILM.ZP_FILM_COLLECTION_ID
    ).join(
        TABLES.ZP_USER_FILM_ENTITY_XREF,
        and_(
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID == TABLES.ZP_FILM_TITLE.ID,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
        )
    ).join(
        TABLES.ZP_FILM_IMAGE_RENDER_HASH,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID
    ).join(
        TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID ==
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID,
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
        )
    ).join(
        TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID ==
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID == \
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID
        )
    ).join(
        TABLES.ZP_FILM_FILEFOLDER,
        and_(
            TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_FILM_FILEFOLDER.ENABLED == 1,
        )
    ).join(
        TABLES.ZP_TEMPLATE, TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
    ).join(
        TABLES.ZP_IMAGE_TYPE,
        and_(
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
            TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
        )
    ).join(
        TABLES.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    ).join(
        TABLES.ZP_FILM,
        and_(
            TABLES.ZP_FILM.ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER.ID
        )
    ).outerjoin(
        TABLES.ZP_USER_FILM_WATCHED,
        and_(
            TABLES.ZP_USER_FILM_WATCHED.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_WATCHED.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID
        )
    ##
    ).filter(
        or_(
            TABLES.ZP_FILM_FILEFOLDER.HD == 1,
            TABLES.ZP_FILM_FILEFOLDER.FHD == 1
        )
    ##
    ).order_by(
        TABLES.ZP_FILM_TITLE.TITLE.asc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
    ).all()

    return_list = construct_dune_ui_entity_return_list(
        entity_search_results, 'ZP_FILM_ID', **kwargs)
    return return_list


def films_new(self, **kwargs):
    ZP_USER_ID = kwargs['ZP_USER_ID']
    entity_search_results = self.session.query(
        TABLES.ZP_FILM_TITLE.TITLE,
        TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
        TABLES.ZP_TEMPLATE.REF_NAME,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.HASH,
        TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.EXT,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_USER_FILM_WATCHED.DATETIME,
        TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
        TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID'),
        TABLES.ZP_FILM.ZP_FILM_COLLECTION_ID
    ).join(
        TABLES.ZP_USER_FILM_ENTITY_XREF,
        and_(
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID == TABLES.ZP_FILM_TITLE.ID,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
        )
    ).join(
        TABLES.ZP_FILM_IMAGE_RENDER_HASH,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID
    ).join(
        TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID ==
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID,
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
        )
    ).join(
        TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID ==
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID == \
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID
        )
    ).join(
        TABLES.ZP_FILM_FILEFOLDER,
        and_(
            TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_FILM_FILEFOLDER.ENABLED == 1
        )
    ).join(
        TABLES.ZP_TEMPLATE, TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
    ).join(
        TABLES.ZP_IMAGE_TYPE,
        and_(
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
            TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
        )
    ).join(
        TABLES.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    ).join(
        TABLES.ZP_FILM,
        and_(
            TABLES.ZP_FILM.ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER.ID
        )
    ).outerjoin(
        TABLES.ZP_USER_FILM_WATCHED,
        and_(
            TABLES.ZP_USER_FILM_WATCHED.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_WATCHED.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID
        )
    ##
    ).order_by(
        TABLES.ZP_FILM.ADDED_DATE_TIME.desc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
    ).limit(35)
    ##

    return_list = construct_dune_ui_entity_return_list(
        entity_search_results, 'ZP_FILM_ID', **kwargs)
    return return_list


def films_all(self, **kwargs):
    ZP_USER_ID = kwargs['ZP_USER_ID']

    entity_search_results = self.session.query(
        TABLES.ZP_FILM_TITLE.TITLE,
        TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
        TABLES.ZP_TEMPLATE.REF_NAME,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.HASH,
        TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.EXT,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_USER_FILM_WATCHED.DATETIME,
        TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
        TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID'),
        TABLES.ZP_FILM.ZP_FILM_COLLECTION_ID
    ).join(
        TABLES.ZP_USER_FILM_ENTITY_XREF,
        and_(
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID == TABLES.ZP_FILM_TITLE.ID,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1,
            TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
        )
    ).join(
        TABLES.ZP_FILM_IMAGE_RENDER_HASH,
        TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID
    ).join(
        TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID ==
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID,
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
        )
    ).join(
        TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF,
        and_(
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID ==
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID == \
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID
        )
    ).join(
        TABLES.ZP_FILM_FILEFOLDER,
        and_(
            TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_FILM_FILEFOLDER.ENABLED == 1
        )
    ).join(
        TABLES.ZP_TEMPLATE, TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
    ).join(
        TABLES.ZP_IMAGE_TYPE,
        and_(
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
            TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
        )
    ).join(
        TABLES.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    ).join(
        TABLES.ZP_FILM,
        and_(
            TABLES.ZP_FILM.ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER.ID
        )
    ).outerjoin(
        TABLES.ZP_USER_FILM_WATCHED,
        and_(
            TABLES.ZP_USER_FILM_WATCHED.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_USER_FILM_WATCHED.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID
        )
    ).order_by(
        TABLES.ZP_FILM_TITLE.TITLE.asc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
    ).all()

    return_list = construct_dune_ui_entity_return_list(
        entity_search_results, 'ZP_FILM_ID', **kwargs)
    return return_list

    #collections = self.session.query(
    #    TABLES.ZP_FILM.ZP_FILM_COLLECTION_ID.distinct().label('ZP_FILM_COLLECTION_ID'),
    #    TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.HASH,
    #    TABLES.ZP_TEMPLATE.REF_NAME,
    #    TABLES.ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.EXT,
    #    TABLES.ZP_FILM_COLLECTION_TITLE.TITLE
    #).join(
    #    TABLES.ZP_FILM_COLLECTION_TITLE,
    #    TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_ID == TABLES.ZP_FILM.ZP_FILM_COLLECTION_ID
    #).join(
    #    TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF,
    #    and_(
    #        TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ID == \
    #        TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_ID,
    #        TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_ID == \
    #        TABLES.ZP_FILM_COLLECTION_TITLE.ID,
    #        TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_TYPE_ID == 1,
    #        TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
    #    )
    #).join(
    #    TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH,
    #    TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ZP_FILM_COLLECTION_ID == \
    #    TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_ID
    #).join(
    #    TABLES.ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF,
    #    and_(
    #        TABLES.ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH_ID ==
    #        TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ID,
    #        TABLES.ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
    #    )
    #).join(
    #    TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF,
    #    and_(
    #        TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_ID ==\
    #        TABLES.ZP_FILM_COLLECTION_TITLE.ZP_FILM_COLLECTION_ID,
    #        TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == \
    #        TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_USER_ID,
    #        TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_IMAGE_TYPE_ID ==
    #        TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ZP_FILM_COLLECTION_IMAGE_TYPE_ID,
    #        TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH_ID == \
    #        TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ID
    #    )
    #).join(
    #    TABLES.ZP_IMAGE_TYPE,
    #    and_(
    #        TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ZP_FILM_COLLECTION_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
    #        TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
    #    )
    #).join(
    #    TABLES.ZP_IMAGE_SUB_TYPE,
    #    TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
    #).order_by(
    #    TABLES.ZP_FILM_COLLECTION_TITLE.TITLE.asc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
    #)
#
    ##          """SELECT distinct `ZP_FILM`.`ZP_FILM_COLLECTION_ID` AS `ZP_FILM_ZP_FILM_COLLECTION_ID`,
    ##      `ZP_FILM_COLLECTION_TITLE`.`TITLE` AS `ZP_FILM_COLLECTION_TITLE_TITLE`,
    ##      `ZP_FILM_COLLECTION_IMAGE_RENDER_HASH`.`HASH` AS `ZP_FILM_COLLECTION_IMAGE_RENDER_HASH_HASH`,
    ##      `ZP_FILM_COLLECTION_IMAGE_RENDER_HASH`.`TEMPLATE_NAME` AS `ZP_FILM_COLLECTION_IMAGE_RENDER_HASH_TEMPLATE_NAME`
    ##      FROM `ZP_FILM`
    ##      inner join `ZP_FILM_COLLECTION_TITLE`
    ##      on `ZP_FILM_COLLECTION_TITLE`.ZP_FILM_COLLECTION_ID = `ZP_FILM`.ZP_FILM_COLLECTION_ID
    ##      inner join `ZP_USER_FILM_COLLECTION_TITLE_XREF`
    ##      on (`ZP_USER_FILM_COLLECTION_TITLE_XREF`.`ZP_FILM_COLLECTION_TITLE_ID` = `ZP_FILM_COLLECTION_TITLE`.`ID` and
    ##          `ZP_USER_FILM_COLLECTION_TITLE_XREF`.`ZP_FILM_COLLECTION_ID` = `ZP_FILM_COLLECTION_TITLE`.`ZP_FILM_COLLECTION_ID`)
    ##      inner join ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF
    ##      on (ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_ID = ZP_USER_FILM_COLLECTION_TITLE_XREF.ZP_FILM_COLLECTION_ID and
    ##      ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_USER_ID = ZP_USER_FILM_COLLECTION_TITLE_XREF.ZP_USER_ID)
    ##      inner join ZP_FILM_COLLECTION_IMAGE_RENDER_HASH
    ##      on `ZP_FILM_COLLECTION_IMAGE_RENDER_HASH`.`ID` = `ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF`.`ZP_FILM_COLLECTION_IMAGE_RENDER_HASH_ID`
    ##      where `ZP_FILM_COLLECTION_IMAGE_RENDER_HASH`.`ZP_FILM_COLLECTION_IMAGE_TYPE_ID` = 2
    ##       AND `ZP_USER_FILM_COLLECTION_TITLE_XREF`.`ZP_USER_ID` = 3"""
#
#
    #entity_id_order_list = []
    #entity_processing_dict = {}
#
#
#
#
#
    #temp_dict = {}
    #collection_dict = {}
    #for result in films:
    #    if result.TITLE in temp_dict:
    #        temp_dict[result.TITLE].append({'FILM_ID': result.ZP_FILM_ID, 'HASH': result.HASH,
    #                                        'TEMPLATE_NAME': result.REF_NAME,
    #                                        'ZP_FILM_COLLECTION_ID': result.ZP_FILM_COLLECTION_ID,
    #                                        'EXT': result.EXT})
    #    else:
    #        temp_dict[result.TITLE] = [{'FILM_ID': result.ZP_FILM_ID, 'HASH': result.HASH,
    #                                    'TEMPLATE_NAME': result.REF_NAME,
    #                                    'ZP_FILM_COLLECTION_ID': result.ZP_FILM_COLLECTION_ID,
    #                                        'EXT': result.EXT}]
#
    #for result in collections:
    #    if result.TITLE in temp_dict:
    #        temp_dict[result.TITLE].append({'COLLECTION_ID': result.ZP_FILM_COLLECTION_ID, 'HASH': result.HASH,
    #                                        'TEMPLATE_NAME': result.REF_NAME,
    #                                        'EXT': result.EXT})
    #    else:
    #        temp_dict[result.TITLE] = [{'COLLECTION_ID': result.ZP_FILM_COLLECTION_ID, 'HASH': result.HASH,
    #                                    'TEMPLATE_NAME': result.REF_NAME,
    #                                        'EXT': result.EXT}]
    #    log.debug('COLLECTION_ID %s , hash %s', result.ZP_FILM_COLLECTION_ID, result.HASH)
    #    collection_dict[result.ZP_FILM_COLLECTION_ID] = result.TITLE
#
    #log.debug('len(collection_dict) %s' % len(collection_dict))
    #log.debug('collection_dict keys %s' % ', '.join(str(v) for v in sorted(collection_dict)))
#
    #for title in sorted(temp_dict):
    #    for item in temp_dict[title]:
    #        if 'FILM_ID' in item:
    #            display_film = False
    #            if item['ZP_FILM_COLLECTION_ID'] is None:
    #                display_film = True
    #            elif item['ZP_FILM_COLLECTION_ID'] in collection_dict:
    #                if title[:3].lower() != collection_dict[item['ZP_FILM_COLLECTION_ID']][:3].lower():
    #                    display_film = True
    #            if display_film is True:
    #                return_list.append({r'::TITLE::': title,
    #                                    r'::icon_url::': '{0}/film/{1}/{2}/.{3}.{4}.{5}'.format(
    #                                        kwargs['root_render_image_url_http'],
    #                                        item['TEMPLATE_NAME'],
    #                                        item['FILM_ID'],
    #                                        kwargs['image_type'],
    #                                        item['HASH'],
    #                                        item['EXT']
    #                                    ),
    #                                    r'::menu::': 'film_synop',
    #                                    r'::args::': 'ZP_FILM_ID={0}&ZP_FILM_COLLECTION_ID={1}'.format(
    #                                        item['FILM_ID'],
    #                                        item['ZP_FILM_COLLECTION_ID'] if item['ZP_FILM_COLLECTION_ID'] \
    #                                                                         is not None else 0)
    #                                    })
    #        elif 'COLLECTION_ID' in item:
    #            return_list.append({r'::TITLE::': title,
    #                                r'::icon_url::': '{0}/film_collection/{1}/{2}/.{3}.{4}.{5}'.format(
    #                                    kwargs['root_render_image_url_http'],
    #                                    item['TEMPLATE_NAME'],
    #                                    item['COLLECTION_ID'],
    #                                    kwargs['image_type'],
    #                                    item['HASH'],
    #                                    item['EXT']
    #                                ),
    #                                r'::menu::': 'film_list',
    #                                r'::args::': 'special=film_collection&ZP_FILM_COLLECTION_ID={0}'.format(
    #                                    item['COLLECTION_ID'])})
    #        else:
    #            log.warning('item %s does not have key FILM_ID or COLLECTION_ID', item)
    #return return_list


def film_az_names(self, **kwargs):
    return_list = [{'::AZ::': '123'}]
    for i in range(65, 91):  # Upper Case Letters A-Z
        return_list.append({r'::AZ::': chr(i)})
    return return_list


def film_ratings(self, **kwargs):
    return_list = []
    for i in range(1, 6):
        return_list.append({r'::rating::': str(i)})
    return return_list


def films_az(self, **kwargs):
    """
    SELECT zpfgx.ZP_FILM_ID as ZP_FILM_ID, zpft.TITLE as TITLE
    FROM ZP_FILM_GENRE_XREF zpfgx
    JOIN ZP_FILM_TITLE zpft
    ON zpft.ZP_FILM_ID = zpfgx.ZP_FILM_ID
    WHERE zpfgx.ZP_GENRE_ID = ZP_GENRE_IDTITLE = session.query(
                TABLES.ZP_FILM_TITLE).filter(
                    TABLES.ZP_FILM_TITLE.ZP_FILM_ID == ZP_FILM_ID,
                    TABLES.ZP_USER_FILM_TITLE_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                    TABLES.ZP_FILM_TITLE.ID == TABLES.ZP_USER_FILM_TITLE_XREF.ZP_FILM_TITLE_ID,
                    TABLES.ZP_USER_FILM_TITLE_XREF.ZP_USER_ID == 1).one().TITLE
    """
    # TODO: change substr to startswith
    # TODO: deal with non ascii letters (create a seperate index table the using unicode to ascii module?)
    ZP_USER_ID = kwargs['ZP_USER_ID']
    if not re.match(r'''[a-zA-Z]''', kwargs['az'][0][:1]):
        entity_search_results = self.session.query(
            TABLES.ZP_FILM_TITLE.TITLE,
            TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_TEMPLATE.REF_NAME,
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.HASH,
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.EXT,
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
            TABLES.ZP_USER_FILM_WATCHED.DATETIME,
            TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
            TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID'),
            TABLES.ZP_FILM.ZP_FILM_COLLECTION_ID
        ).join(
            TABLES.ZP_USER_FILM_ENTITY_XREF,
            and_(
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID == TABLES.ZP_FILM_TITLE.ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
            )
        ).join(
            TABLES.ZP_FILM_IMAGE_RENDER_HASH,
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID
        ).join(
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF,
            and_(
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID ==
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID,
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
            )
        ).join(
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF,
            and_(
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID,
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID ==
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID,
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID == \
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID
            )
        ).join(
            TABLES.ZP_FILM_FILEFOLDER,
            and_(
                TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                TABLES.ZP_FILM_FILEFOLDER.ENABLED == 1
            )
        ).join(
            TABLES.ZP_TEMPLATE, TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
        ).join(
            TABLES.ZP_IMAGE_TYPE,
            and_(
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
                TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
            )
        ).join(
            TABLES.ZP_IMAGE_SUB_TYPE,
            TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
        ).join(
            TABLES.ZP_FILM,
            and_(
                TABLES.ZP_FILM.ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER.ID
            )
        ).outerjoin(
            TABLES.ZP_USER_FILM_WATCHED,
            and_(
                TABLES.ZP_USER_FILM_WATCHED.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                TABLES.ZP_USER_FILM_WATCHED.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID
            )
        ).filter(
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'a'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'A'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'B'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'c'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'C'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'd'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'D'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'e'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'E'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'f'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'F'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'g'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'G'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'h'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'H'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'i'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'I'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'j'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'K'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'k'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'K'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'l'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'L'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'm'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'M'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'n'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'N'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'o'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'O'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'p'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'P'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'q'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'Q'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'r'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'R'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 's'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'S'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 't'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'T'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'u'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'U'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'v'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'V'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'w'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'W'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'x'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'X'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'y'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'Y'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'z'),
            ~(func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == 'Z')
        ).order_by(
            TABLES.ZP_FILM_TITLE.TITLE.asc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
        ).all()
    else:
        entity_search_results = self.session.query(
            TABLES.ZP_FILM_TITLE.TITLE,
            TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
            TABLES.ZP_TEMPLATE.REF_NAME,
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.HASH,
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.EXT,
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
            TABLES.ZP_USER_FILM_WATCHED.DATETIME,
            TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT,
            TABLES.ZP_IMAGE_SUB_TYPE.ID.label('ZP_IMAGE_SUB_TYPE_ID'),
            TABLES.ZP_FILM.ZP_FILM_COLLECTION_ID
        ).join(
            TABLES.ZP_USER_FILM_ENTITY_XREF,
            and_(
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID == TABLES.ZP_FILM_TITLE.ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID
            )
        ).join(
            TABLES.ZP_FILM_IMAGE_RENDER_HASH,
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID
        ).join(
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF,
            and_(
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID ==
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID,
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
            )
        ).join(
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF,
            and_(
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID,
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID ==
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID,
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID == \
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID
            )
        ).join(
            TABLES.ZP_FILM_FILEFOLDER,
            and_(
                TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                TABLES.ZP_FILM_FILEFOLDER.ENABLED == 1
            )
        ).join(
            TABLES.ZP_TEMPLATE, TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
        ).join(
            TABLES.ZP_IMAGE_TYPE,
            and_(
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
                TABLES.ZP_IMAGE_TYPE.NAME == kwargs['image_type']
            )
        ).join(
            TABLES.ZP_IMAGE_SUB_TYPE,
            TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE
        ).join(
            TABLES.ZP_FILM,
            and_(
                TABLES.ZP_FILM.ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER.ID
            )
        ).outerjoin(
            TABLES.ZP_USER_FILM_WATCHED,
            and_(
                TABLES.ZP_USER_FILM_WATCHED.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                TABLES.ZP_USER_FILM_WATCHED.ZP_USER_ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID
            )
        ).filter(
            or_(
                func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == kwargs['az'][0][:1].upper(),
                func.substr(TABLES.ZP_FILM_TITLE.TITLE, 1, 1) == kwargs['az'][0][:1].lower()
            )
        ).order_by(
            TABLES.ZP_FILM_TITLE.TITLE.asc(), TABLES.ZP_IMAGE_SUB_TYPE.ID.asc()
        ).all()

    return_list = construct_dune_ui_entity_return_list(
        entity_search_results, 'ZP_FILM_ID', **kwargs)
    return return_list


def film_list(self, **kwargs):
    # special_replace_dicts = globals()[virtual_item['@special']](self, **request_query_kwargs)
    return globals()[kwargs['special'][0]](self, **kwargs)


def film_synop(self, **kwargs):
    return [{'::ZP_FILM_ID::': kwargs['ZP_FILM_ID'][0]}]


def film_synopsis_bg_image_path(self, ZP_FILM_ID, ZP_USER_ID, ZP_DUNE_ID, root_render_image_url_http):
    try:
        result = self.session.query(
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID,
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.HASH,
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.EXT,
            TABLES.ZP_TEMPLATE.REF_NAME
        ).join(
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF,
            and_(
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID ==
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID,
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == ZP_DUNE_ID
            )
        ).join(
            ##
            TABLES.ZP_TEMPLATE, TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
        ).filter(
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID == \
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID,
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID == 2,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID == ZP_FILM_ID,
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == ZP_USER_ID

        ).one()
    except orm.exc.NoResultFound as e:
        log.warning('Cannot find ZP_FILM_IMAGE_RENDER_HASH for')
    else:
        return '{0}/film/{1}/{2}/.synopsis.{3}.{4}'.format(root_render_image_url_http,
                                                           result.REF_NAME,
                                                           result.ZP_FILM_ID,
                                                           result.HASH,
                                                           result.EXT
                                                           )


def film_fav_bg_image_path(self, ZP_FILM_ID, ZP_USER_ID):
    favourited = False
    try:
        qry_ZP_USER_FILM_FAVOURITE = self.session.query(
            TABLES.ZP_USER_FILM_FAVOURITE
        ).filter(
            TABLES.ZP_USER_FILM_FAVOURITE.ZP_FILM_ID == ZP_FILM_ID,
            TABLES.ZP_USER_FILM_FAVOURITE.ZP_USER_ID == ZP_USER_ID
        )
        qry_ZP_USER_FILM_FAVOURITE.one()
    except orm.exc.NoResultFound:
        add_ZP_USER_FILM_FAVOURITE = TABLES.ZP_USER_FILM_FAVOURITE(ZP_FILM_ID=ZP_FILM_ID,
                                                                   ZP_USER_ID=ZP_USER_ID)
        self.session.add(add_ZP_USER_FILM_FAVOURITE)
        commit(self.session)
        favourited = True
    else:
        qry_ZP_USER_FILM_FAVOURITE.delete()
        commit(self.session)

    if favourited == True:
        return 'added'
    else:
        return 'removed'


def film_tow_bg_image_path(self, ZP_FILM_ID, ZP_USER_ID):
    favourited = False
    try:
        qry_ZP_USER_FILM_TOWATCH = self.session.query(
            TABLES.ZP_USER_FILM_TOWATCH
        ).filter(
            TABLES.ZP_USER_FILM_TOWATCH.ZP_FILM_ID == ZP_FILM_ID,
            TABLES.ZP_USER_FILM_TOWATCH.ZP_USER_ID == ZP_USER_ID
        )
        qry_ZP_USER_FILM_TOWATCH.one()
    except orm.exc.NoResultFound as e:
        add_ZP_USER_FILM_TOWATCH = TABLES.ZP_USER_FILM_TOWATCH(ZP_FILM_ID=ZP_FILM_ID,
                                                               ZP_USER_ID=ZP_USER_ID)
        self.session.add(add_ZP_USER_FILM_TOWATCH)
        commit(self.session)
        favourited = True
    else:
        qry_ZP_USER_FILM_TOWATCH.delete()
        commit(self.session)

    if favourited == True:
        return 'added'
    else:
        return 'removed'


def film_play(self, ZP_FILM_ID, ZP_USER_ID, ZP_DUNE_ID, **kwargs):
    """
    SELECT zpff.SCAN_PATH_SUB_DIR, zpff.LAST_PATH, zpdpp.PLAY_ROOT_PATH FROM
    ZP_FILM_FILEFOLDER_XREF zpffx
    JOIN ZP_FILM_FILEFOLDER zpff ON
    zpffx.ZP_FILM_FILEFOLDER_ID = zpff.ID
    JOIN ZP_DUNE_PLAY_PATH zpdpp ON
    zpff.ZP_SCAN_PATH_ID = zpdpp.ZP_SCAN_PATH_ID
    WHERE zpffx.ZP_FILM_ID = ZP_FILM_ID
    """
    film_path_components = self.session.query(
        TABLES.ZP_FILM_FILEFOLDER.SCAN_PATH_SUB_DIR,
        TABLES.ZP_FILM_FILEFOLDER.LAST_PATH,
        TABLES.ZP_DUNE_PLAY_PATH.PLAY_ROOT_PATH
    ).filter(
        TABLES.ZP_FILM_FILEFOLDER.ZP_SCAN_PATH_ID == TABLES.ZP_DUNE_PLAY_PATH.ZP_SCAN_PATH_ID,
        TABLES.ZP_FILM_FILEFOLDER.ID == TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID,
        TABLES.ZP_DUNE_PLAY_PATH.ZP_DUNE_ID == ZP_DUNE_ID,
        TABLES.ZP_FILM.ID == ZP_FILM_ID
    ).one()

    dune_last_path = re.sub(r'/+', '/', '{0}/{1}'.format(film_path_components.SCAN_PATH_SUB_DIR.strip(' '),
        film_path_components.LAST_PATH.strip(' ')).strip('/'))

    dune_play_path = '{0}/{1}'.format(film_path_components.PLAY_ROOT_PATH.rstrip('/'),
                                      dune_last_path)

    self.wfile.write(dune_play_path)

    try:
        check_for_allready_watched = self.session.query(
            TABLES.ZP_USER_FILM_WATCHED
        ).filter(
            TABLES.ZP_USER_FILM_WATCHED.ZP_FILM_ID == ZP_FILM_ID,
            TABLES.ZP_USER_FILM_WATCHED.ZP_USER_ID == ZP_USER_ID
        ).one()
    except orm.exc.NoResultFound as e:
        add_film_watched = TABLES.ZP_USER_FILM_WATCHED(ZP_FILM_ID=ZP_FILM_ID,
                                                       ZP_USER_ID=ZP_USER_ID,
                                                       DATETIME=date_time())
        self.session.add(add_film_watched)
        commit(self.session)
    else:
        check_for_allready_watched.DATETIME = date_time()
        commit(self.session)


def film_search(self, **kwargs):
    return []
