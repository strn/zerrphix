# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function
from zerrphix.db.tables import TABLES
from zerrphix.db import flush, commit
from sqlalchemy import orm, and_
import logging

log = logging.getLogger(__name__)

def get_redered_image_url(self, library, image_type, image_sub_type, entity_id, **kwargs):
    #log.error('locals %s', locals())
    entity_image_query = None
    if library == 'film':
        entity_image_query = self.session.query(
            TABLES.ZP_FILM_IMAGE_RENDER_HASH.HASH,
            TABLES.ZP_TEMPLATE.REF_NAME,
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.EXT,
            TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT
        ).join(
            TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF,
            and_(
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID == entity_id,
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == kwargs['ZP_USER_ID'],
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID ==
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID,
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID == \
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID,
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID ==
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID
            )
        ).join(
            TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF,
            and_(
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID ==
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID,
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
            )
        ).join(
            TABLES.ZP_TEMPLATE, TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
        ).join(
            TABLES.ZP_IMAGE_TYPE,
            and_(
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
                TABLES.ZP_IMAGE_TYPE.NAME == image_type
            )
        ).join(
            TABLES.ZP_IMAGE_SUB_TYPE,
            and_(
                TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
                TABLES.ZP_IMAGE_SUB_TYPE.ID == image_sub_type
            )
        )
    elif library == 'tv':
        entity_image_query = self.session.query(
            TABLES.ZP_TV_IMAGE_RENDER_HASH.HASH,
            TABLES.ZP_TEMPLATE.REF_NAME,
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.EXT,
            TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT
        ).join(
            TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF,
            and_(
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == entity_id,
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == kwargs['ZP_USER_ID'],
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID ==
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID == \
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ID,
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_ID ==
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_ID
            )
        ).join(
            TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF,
            and_(
                TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID ==
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ID,
                TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
            )
        ).join(
            TABLES.ZP_TEMPLATE, TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
        ).join(
            TABLES.ZP_IMAGE_TYPE,
            and_(
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
                TABLES.ZP_IMAGE_TYPE.NAME == image_type
            )
        ).join(
            TABLES.ZP_IMAGE_SUB_TYPE,
            and_(
                TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
                TABLES.ZP_IMAGE_SUB_TYPE.ID == image_sub_type
            )
        )
    elif library == 'film_collection':
        entity_image_query = self.session.query(
            TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.HASH,
            TABLES.ZP_TEMPLATE.REF_NAME,
            TABLES.ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.EXT,
            TABLES.ZP_IMAGE_SUB_TYPE.POST_IMAGE_TYPE_TEXT
        ).join(
            TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF,
            and_(
                TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_ID == entity_id,
                TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == kwargs['ZP_USER_ID'],
                TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_IMAGE_TYPE_ID ==
                TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ZP_FILM_COLLECTION_IMAGE_TYPE_ID,
                TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH_ID == \
                TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ID,
                TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ZP_FILM_COLLECTION_ID ==
                TABLES.ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_ID
            )
        ).join(
            TABLES.ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF,
            and_(
                TABLES.ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH_ID ==
                TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ID,
                TABLES.ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID']
            )
        ).join(
            TABLES.ZP_TEMPLATE, TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
        ).join(
            TABLES.ZP_IMAGE_TYPE,
            and_(
                TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ZP_FILM_COLLECTION_IMAGE_TYPE_ID == TABLES.ZP_IMAGE_TYPE.ID,
                TABLES.ZP_IMAGE_TYPE.NAME == image_type
            )
        ).join(
            TABLES.ZP_IMAGE_SUB_TYPE,
            and_(
                TABLES.ZP_IMAGE_SUB_TYPE.ID == TABLES.ZP_FILM_COLLECTION_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
                TABLES.ZP_IMAGE_SUB_TYPE.ID == image_sub_type
            )
        )

    if entity_image_query is not None:
        try:
            entity_image = entity_image_query.one()
        except orm.exc.NoResultFound:
            log.error('No Result')
            return ''
        else:
            return '{0}/{1}/{2}/{3}/.{4}{5}.{6}.{7}'.format(
                kwargs['root_render_image_url_http'],
                library,
                entity_image.REF_NAME,
                entity_id,
                image_type,
                entity_image.POST_IMAGE_TYPE_TEXT,
                entity_image.HASH,
                entity_image.EXT
            )
    return  ''


def users(self, **kwargs):
    return_list = []
    users = self.session.query(
        TABLES.ZP_USER.ID,
        TABLES.ZP_USER.USERNAME,
        TABLES.ZP_USER_IMAGE_RENDER_HASH.HASH,
        TABLES.ZP_USER_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
        TABLES.ZP_USER_TEMPLATE_XREF.ZP_TEMPLATE_ID,
        TABLES.ZP_DUNE_USER_IMAGE_RENDER_HASH_XREF.EXT
    ).filter(
        TABLES.ZP_USER_IMAGE_RENDER_HASH.ZP_USER_ID == TABLES.ZP_USER.ID,
        TABLES.ZP_USER_GROUP.ZP_USER_ID == TABLES.ZP_USER.ID,
        TABLES.ZP_USER_GROUP.ZP_DUNE_ID == kwargs['ZP_DUNE_ID'],
        TABLES.ZP_USER_TEMPLATE_XREF.ZP_USER_ID == TABLES.ZP_USER.ID,
        TABLES.ZP_DUNE_USER_IMAGE_RENDER_HASH_XREF.ZP_USER_IMAGE_RENDER_HASH_ID ==
        TABLES.ZP_USER_IMAGE_RENDER_HASH.ID,
        TABLES.ZP_DUNE_USER_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID ==
        TABLES.ZP_USER_GROUP.ZP_DUNE_ID
    ).all()
    user_icon_dict = {}
    for result in users:
        if result.ID not in user_icon_dict:
            user_icon_dict[result.ID] = {}
        if result.ZP_IMAGE_SUB_TYPE == 1:
            user_icon_dict[result.ID]['icon_hash'] = result.HASH
        else:
            user_icon_dict[result.ID]['icon_sel_hash'] = result.HASH
        user_icon_dict[result.ID]['username'] = result.USERNAME
        user_icon_dict[result.ID]['zp_template_id'] = result.ZP_TEMPLATE_ID
        user_icon_dict[result.ID]['ext'] = result.EXT
    for user in user_icon_dict:
        return_list.append({r'::ZP_USER_USERNAME::': user_icon_dict[user]['username'],
                            r'::ZP_USER_ID::': str(user),
                            r'::icon_url::': '{}/user/{}.icon.{}.{}'.format(
                                kwargs['root_render_image_url_http'],
                                user,
                                user_icon_dict[user]['icon_hash'],
                                user_icon_dict[user]['ext']
                            ),
                            r'::icon_sel_url::': '{}/user/{}.icon_sel.{}.{}'.format(
                                kwargs['root_render_image_url_http'],
                                user,
                                user_icon_dict[user]['icon_sel_hash'],
                                user_icon_dict[user]['ext']
                            ),
                            r'::zp_template_id::': str(user_icon_dict[user]['zp_template_id'])})
    return return_list


def search_az09(self, **kwargs):
    return_list = []
    for i in range(65, 91):  # Lower Case Letters A-Z
        return_list.append({'::char::': chr(i)})

    for i in range(0, 10):  # Lower Case Letters A-Z
        return_list.append({'::char::': str(i)})
    return return_list


def search_type_rotate(self, **kwargs):
    if kwargs['search_type'][0] == 'a':
        return [{r'::new_search_type::': 'b'}]
    elif kwargs['search_type'][0] == 'b':
        return [{r'::new_search_type::': 'e'}]
    else:
        return [{r'::new_search_type::': 'a'}]

