# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import sys
from datetime import datetime
from datetime import timedelta
from types import MethodType
from sqlalchemy import func, orm, and_
import uuid
from zerrphix.db import flush, commit
from zerrphix.db.tables import TABLES
from zerrphix.tv.util import update_tv_last_mod
from zerrphix.plugin import load_plugins
from zerrphix.util import list1_not_in_list2
from zerrphix.util.plugin import create_eapi_plugins_list, create_eapi_dict
from zerrphix.util.text import date_time
from six import string_types
from six import text_type
from zerrphix.util.filesystem import make_dir
from zerrphix.util.web import download
from zerrphix.util.filesystem import get_file_extension
#from zerrphix.util import set_retry, check_can_retry
#from zerrphix.util import iso_639_part1_from_zp_lang_id, get_user_langs
from zerrphix.tv.base import TVBase
from zerrphix.raw_images import RawImagesBase
import os
import time
import copy

log = logging.getLogger(__name__)


def eapi_eid_from_zp_tv_id(self, eapi_id, zp_tv_id):
    """Get eapi_id from zp_tv_id

        Args:
            | eapi_id (int): 0
            | zp_tv_id (int): 0
    """
    session = self.Session()
    ZP_EAPI_EID = None
    try:
        ZP_EAPI_EID = session.query(TABLES.ZP_TV_EAPI_EID).filter(
            TABLES.ZP_TV_EAPI_EID.ZP_TV_ID == zp_tv_id,
            TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID == eapi_id).one().ZP_EAPI_EID
    except orm.exc.NoResultFound:
        log.warning(
            'ZP_TV_ID: {0} with eapi_id {1} not in ZP_TV_EAPI_EID'.format(
                zp_tv_id,
                eapi_id))
    session.close()
    return ZP_EAPI_EID


class RawEpisodeImages(RawImagesBase):
    """Get Data for tvs (actors, runtime, synop etc...)
    """

    def __init__(self, **kwargs):
        """Data __init__

            Args:
                | args (list): Passed through args from the command line.
                | Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.
        """
        super(RawEpisodeImages, self).__init__(**kwargs)
        self, self.eapi_tv_plugins_access_list, loaded_plugins = create_eapi_plugins_list(
            'tv', sys.modules, load_plugins(self.args), self)
        if not self.eapi_tv_plugins_access_list:
            raise Exception(('There not any entries in eapi_tv_plugins_access_list'
                             ' therefore scanning is pointless'))
        session = self.Session()
        self.eapi_dict = create_eapi_dict(session)
        session.close()
        self.data_keys = ['genres', 'title', 'original_title',
                          'overview', 'release_date', 'runtime',
                          'rating', 'credits', 'belongs_to_collection']

        #self.eapi_eid_from_zp_tv_id = MethodType(eapi_eid_from_zp_tv_id, self)
        #self.iso_639_part1_from_zp_lang_id = MethodType(iso_639_part1_from_zp_lang_id, self)
        self.allowed_extension_list = ['png', 'jpg', 'jpeg', 'gif', 'bmp']
        self.image_types_dict = {'screenshot':
                                     {'id': 4}
                                 }
        # self.image_types_keys = ['backdrop', 'poster', 'banner']
        #self.get_user_langs = MethodType(get_user_langs, self)
        #self.set_retry = MethodType(set_retry, self)
        #self.check_can_retry = MethodType(check_can_retry, self)

    def acquire(self):
        # self.acquire_tv_data()
        # self.acquire_tv_collection_data()
        # self.acquire_tv_collection_data()
        # todo add a system default language
        # image_root_path = os.path.join(self.global_config_dict['downloaded_images_root_path'],
        # self.library_config_dict['name'])
        # if make_dir(image_root_path):
        #log.error('blah')
        if make_dir(self.library_config_dict['downloaded_images_library_root_path']):
            user_langs = self.get_all_user_library_langs(2)
            # todo optionise adding english as a fallback when user specifics are done
            if 1823 not in user_langs:
                user_langs[1823] = 'English'
            self.user_langs = user_langs
            log.debug(user_langs)
            # for zp_lang in user_langs:
            self.acquire_images(user_langs)
        else:
            log.error('''self.library_config_dict['downloaded_images_library_root_path'] %s is not a dir''',
                      self.library_config_dict['downloaded_images_library_root_path'])

    def get_tv_season_not_missing_raw_eapi_image(self, zp_tv_id, eapi, zp_lang_id):
        session = self.Session()
        return_dict = {}
        query_tv_season_not_missing_raw_eapi_image = session.query(TABLES.ZP_TV_EPISODE_RAW_IMAGE).filter(
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_LANG_ID == zp_lang_id,
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID == zp_tv_id,
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi]
        )

        query_tv_season_not_missing_raw_eapi_image_count = query_tv_season_not_missing_raw_eapi_image.count()
        log.debug('qry_tv_missing_raw_eapi_image_count no retry: %s', query_tv_season_not_missing_raw_eapi_image_count)
        if query_tv_season_not_missing_raw_eapi_image_count > 0:
            tv_season_not_missing_raw_eapi_image = query_tv_season_not_missing_raw_eapi_image.order_by(
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.SEASON.asc(),
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID.asc()
            ).all()
            session.close()
            for tv_season_image in tv_season_not_missing_raw_eapi_image:
                if tv_season_image.SEASON not in return_dict:
                    return_dict[tv_season_image.SEASON] = {}
                if tv_season_image.EPISODE not in return_dict[tv_season_image.SEASON]:
                    return_dict[tv_season_image.SEASON][tv_season_image.EPISODE] = []
                if tv_season_image.ZP_ENTITY_TYPE_ID not in return_dict[tv_season_image.SEASON][tv_season_image.EPISODE]:
                    return_dict[tv_season_image.SEASON][tv_season_image.EPISODE].append(
                        tv_season_image.ZP_ENTITY_TYPE_ID)
        return return_dict

    def get_tv_missing_raw_eapi_image_no_retry(self, zp_tv_id, eapi, zp_lang_id, zp_entity_id_list):
        session = self.Session()
        return_list = []
        #qry_tv_missing_raw_eapi_image = session.query(
        #    TABLES.ZP_TV.ID.distinct().label('ID')
        #).filter(
        #    TABLES.ZP_TV.ID < zp_tv_id,
        #    TABLES.ZP_TV_EPISODE.ZP_TV_ID == TABLES.ZP_TV.ID,
        #    ~TABLES.ZP_TV.ID.in_(
        #        session.query(TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID).filter(
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID.in_(zp_entity_id_list),
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi],
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_LANG_ID != zp_lang_id,
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.SEASON == TABLES.ZP_TV_EPISODE.SEASON,
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.EPISODE == TABLES.ZP_TV_EPISODE.EPISODE
        #        ).group_by(
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID
        #        ).having(
        #            func.count(TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID) == len(zp_entity_id_list))
        #    ),
        #    ~TABLES.ZP_TV.ID.in_(
        #        session.query(TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID).filter(
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID.in_(zp_entity_id_list),
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi],
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_LANG_ID == zp_lang_id,
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.SEASON == TABLES.ZP_TV_EPISODE.SEASON,
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.EPISODE == TABLES.ZP_TV_EPISODE.EPISODE
        #        ).group_by(
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID
        #        ).having(
        #            func.count(TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID) == len(zp_entity_id_list))
        #    ),
        #    TABLES.ZP_TV.ID.in_(
        #        session.query(
        #            TABLES.ZP_TV_EAPI_EID.ZP_TV_ID).filter(
        #            TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID == self.eapi_dict[eapi]
        #        )),
        #    ~TABLES.ZP_TV.ID.in_(session.query(
        #        TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
        #        TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 11,
        #        TABLES.ZP_RETRY.ZP_EAPI_ID == self.eapi_dict[eapi],
        #        TABLES.ZP_RETRY.ZP_LANG_ID == 0
        #    ))
        #)
        #else:
        #qry_tv_missing_raw_eapi_image = session.query(
        #    TABLES.ZP_TV.ID.distinct().label('ID')
        #).filter(
        #    TABLES.ZP_TV.ID < zp_tv_id,
        #    TABLES.ZP_TV_EPISODE.ZP_TV_ID == TABLES.ZP_TV.ID,
        #    ~TABLES.ZP_TV.ID.in_(
        #        session.query(TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID).filter(
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID.in_(zp_entity_id_list),
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi],
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_LANG_ID == zp_lang_id,
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.SEASON == TABLES.ZP_TV_EPISODE.SEASON,
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.EPISODE == TABLES.ZP_TV_EPISODE.EPISODE
        #        ).group_by(
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID
        #        ).having(
        #            func.count(TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID) == len(zp_entity_id_list))
        #    ),
        #    TABLES.ZP_TV.ID.in_(
        #        session.query(
        #            TABLES.ZP_TV_EAPI_EID.ZP_TV_ID).filter(
        #            TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID == self.eapi_dict[eapi]
        #        )),
        #    ~TABLES.ZP_TV.ID.in_(session.query(
        #        TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
        #        TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 11,
        #        TABLES.ZP_RETRY.ZP_EAPI_ID == self.eapi_dict[eapi],
        #        TABLES.ZP_RETRY.ZP_LANG_ID == zp_lang_id
        #    ))
        #)
        #qry_tv_missing_raw_eapi_image = session.query(
        #    TABLES.ZP_TV_EPISODE.ZP_TV_ID.distinct().label('ZP_TV_ID')
        #).filter(
        #    TABLES.ZP_TV_EPISODE.ZP_TV_ID < zp_tv_id,
        #    ~TABLES.ZP_TV_EPISODE.ZP_TV_ID.in_(
        #        session.query(TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID).filter(
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID.in_(zp_entity_id_list),
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi],
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_LANG_ID == zp_lang_id,
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.SEASON == TABLES.ZP_TV_EPISODE.SEASON,
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.EPISODE == TABLES.ZP_TV_EPISODE.EPISODE
        #        ).group_by(
        #            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID
        #        ).having(
        #            func.count(TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID) == len(zp_entity_id_list))
        #    )
        #)
        if zp_lang_id is None:
            retry_zp_lang_id = 0
        else:
            retry_zp_lang_id = zp_lang_id
        qry_tv_missing_raw_eapi_image = session.query(
            TABLES.ZP_TV_EAPI_EID.ZP_TV_ID
        ).join(TABLES.ZP_TV_EPISODE,
            TABLES.ZP_TV_EAPI_EID.ZP_TV_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID
        ).join(TABLES.ZP_TV_EPISODE_RAW_IMAGE, and_(
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.EPISODE == TABLES.ZP_TV_EPISODE.EPISODE,
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.SEASON == TABLES.ZP_TV_EPISODE.SEASON,
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID,
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_EAPI_ID == TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID
            )
        ).filter(
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID.in_(zp_entity_id_list),
            TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID == self.eapi_dict[eapi],
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_LANG_ID == zp_lang_id,
            TABLES.ZP_TV_EAPI_EID.ZP_TV_ID < zp_tv_id,
            # left join is null/not in/not exists all seem to be simmilar times
            ~TABLES.ZP_TV_EAPI_EID.ZP_TV_ID.in_(session.query(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 11,
                TABLES.ZP_RETRY.ZP_EAPI_ID == self.eapi_dict[eapi],
                TABLES.ZP_RETRY.ZP_LANG_ID == retry_zp_lang_id
            ))
        ).group_by(
            TABLES.ZP_TV_EAPI_EID.ZP_TV_ID
        ).having(
            func.count() < session.query(func.count(TABLES.ZP_TV_EPISODE.EPISODE).label('E_COUNT')).filter(
                TABLES.ZP_TV_EPISODE.ZP_TV_ID == TABLES.ZP_TV_EAPI_EID.ZP_TV_ID
            ).correlate(TABLES.ZP_TV_EAPI_EID).as_scalar() * len(zp_entity_id_list)
        )


        """
        SELECT ZP_TV_EAPI_EID.ZP_TV_ID
        FROM `ZP_TV_EAPI_EID`
        JOIN ZP_TV_EPISODE 
        on ZP_TV_EAPI_EID.ZP_TV_ID = ZP_TV_EPISODE.ZP_TV_ID
        JOIN `ZP_TV_EPISODE_RAW_IMAGE` ON
            (ZP_TV_EPISODE.ZP_TV_ID = ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID AND
            ZP_TV_EPISODE.SEASON = ZP_TV_EPISODE_RAW_IMAGE.SEASON AND
            ZP_TV_EPISODE.EPISODE = ZP_TV_EPISODE_RAW_IMAGE.EPISODE AND
            ZP_TV_EPISODE_RAW_IMAGE.ZP_EAPI_ID = ZP_TV_EAPI_EID.ZP_EAPI_ID)
        LEFT JOIN ZP_RETRY
        ON (ZP_RETRY.ZP_RETRY_ENTITY_ID = ZP_TV_EAPI_EID.ZP_TV_ID and ZP_RETRY.ZP_EAPI_ID = ZP_TV_EAPI_EID.ZP_EAPI_ID
        AND ZP_RETRY.ZP_LANG_ID = 0 AND ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID = 11)
        WHERE `ZP_TV_EPISODE_RAW_IMAGE`.`ZP_ENTITY_TYPE_ID` in (4)
        AND `ZP_TV_EAPI_EID`.`ZP_EAPI_ID` = 4
        AND `ZP_TV_EPISODE_RAW_IMAGE`.`ZP_LANG_ID` IS NULL
        AND ZP_RETRY.ZP_RETRY_ENTITY_ID IS NULL
        group by ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID
        HAVING count(*) < (select count(ZP_TV_EPISODE.EPISODE)
        from ZP_TV_EPISODE where ZP_TV_EPISODE.ZP_TV_ID = ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID) * 1
        order by ZP_TV_EAPI_EID.ZP_TV_ID desc
        
        
        SELECT ZP_TV_EAPI_EID.ZP_TV_ID
        FROM `ZP_TV_EAPI_EID`
        JOIN ZP_TV_EPISODE 
        on ZP_TV_EAPI_EID.ZP_TV_ID = ZP_TV_EPISODE.ZP_TV_ID
        JOIN `ZP_TV_EPISODE_RAW_IMAGE` ON
            (ZP_TV_EPISODE.ZP_TV_ID = ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID AND
            ZP_TV_EPISODE.SEASON = ZP_TV_EPISODE_RAW_IMAGE.SEASON AND
            ZP_TV_EPISODE.EPISODE = ZP_TV_EPISODE_RAW_IMAGE.EPISODE AND
            ZP_TV_EPISODE_RAW_IMAGE.ZP_EAPI_ID = ZP_TV_EAPI_EID.ZP_EAPI_ID)
        WHERE `ZP_TV_EPISODE_RAW_IMAGE`.`ZP_ENTITY_TYPE_ID` in (4)
        AND `ZP_TV_EAPI_EID`.`ZP_EAPI_ID` = 4
        AND `ZP_TV_EPISODE_RAW_IMAGE`.`ZP_LANG_ID` IS NULL
        AND NOT EXISTS (select 1
            from ZP_RETRY 
            where ZP_RETRY.ZP_LANG_ID = 0 
            AND ZP_RETRY.ZP_EAPI_ID = 4 
            AND ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID = 11
            AND ZP_RETRY.ZP_RETRY_ENTITY_ID = ZP_TV_EAPI_EID.ZP_TV_ID
        )
        group by ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID
        HAVING count(*) < (select count(ZP_TV_EPISODE.EPISODE)
        from ZP_TV_EPISODE where ZP_TV_EPISODE.ZP_TV_ID = ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID) * 1
        order by ZP_TV_EAPI_EID.ZP_TV_ID desc
        
        SELECT ZP_TV_EAPI_EID.ZP_TV_ID
        FROM `ZP_TV_EAPI_EID`
        JOIN ZP_TV_EPISODE 
        on ZP_TV_EAPI_EID.ZP_TV_ID = ZP_TV_EPISODE.ZP_TV_ID
        JOIN `ZP_TV_EPISODE_RAW_IMAGE` ON
            (ZP_TV_EPISODE.ZP_TV_ID = ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID AND
            ZP_TV_EPISODE.SEASON = ZP_TV_EPISODE_RAW_IMAGE.SEASON AND
            ZP_TV_EPISODE.EPISODE = ZP_TV_EPISODE_RAW_IMAGE.EPISODE AND
            ZP_TV_EPISODE_RAW_IMAGE.ZP_EAPI_ID = ZP_TV_EAPI_EID.ZP_EAPI_ID)
        WHERE `ZP_TV_EPISODE_RAW_IMAGE`.`ZP_ENTITY_TYPE_ID` in (4)
        AND `ZP_TV_EAPI_EID`.`ZP_EAPI_ID` = 4
        AND `ZP_TV_EPISODE_RAW_IMAGE`.`ZP_LANG_ID` IS NULL
        AND ZP_TV_EAPI_EID.ZP_TV_ID not in (select ZP_RETRY.ZP_RETRY_ENTITY_ID 
            from ZP_RETRY 
            where ZP_RETRY.ZP_LANG_ID = 0 
            AND ZP_RETRY.ZP_EAPI_ID = 4 
            AND ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID = 11
        )
        group by ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID
        HAVING count(*) < (select count(ZP_TV_EPISODE.EPISODE)
        from ZP_TV_EPISODE where ZP_TV_EPISODE.ZP_TV_ID = ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID) * 1
        order by ZP_TV_EAPI_EID.ZP_TV_ID desc
        """
        #qry_tv_missing_raw_eapi_image_count = qry_tv_missing_raw_eapi_image.count()
        #log.debug('qry_tv_missing_raw_eapi_image_count no retry: %s', qry_tv_missing_raw_eapi_image_count)
        #if qry_tv_missing_raw_eapi_image_count > 0:
        tv_missing_raw_eapi_image = qry_tv_missing_raw_eapi_image.order_by(TABLES.ZP_TV_EAPI_EID.ZP_TV_ID.desc()
                                                                           ).limit(50)
        session.close()
        if tv_missing_raw_eapi_image is not None:
            for tv in tv_missing_raw_eapi_image:
                return_list.append(tv.ZP_TV_ID)
        #raise SystemExit
        return return_list

    def get_tv_not_in_raw_eapi_image_no_retry(self, zp_tv_id, eapi, zp_lang_id, zp_entity_id_list):
        session = self.Session()
        return_list = []
        if zp_lang_id is None:
            retry_zp_lang_id = 0
        else:
            retry_zp_lang_id = zp_lang_id
        qry_tv_missing_raw_eapi_image = session.query(
            TABLES.ZP_TV_EAPI_EID.ZP_TV_ID
        ).filter(
            TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID == self.eapi_dict[eapi],
            TABLES.ZP_TV_EAPI_EID.ZP_TV_ID < zp_tv_id,
            ~TABLES.ZP_TV_EAPI_EID.ZP_TV_ID.in_(session.query(
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID.distinct().label('ZP_ENTITY_ID')).filter(
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID.in_(zp_entity_id_list),
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_EAPI_ID == TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID,
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_LANG_ID == zp_lang_id
            ).group_by(
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID
            ).having(
                func.count(TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID.distinct().label('ZP_ENTITY_TYPE_ID')) ==
                len(zp_entity_id_list)
            )),
            ~TABLES.ZP_TV_EAPI_EID.ZP_TV_ID.in_(session.query(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 11,
                TABLES.ZP_RETRY.ZP_EAPI_ID == self.eapi_dict[eapi],
                TABLES.ZP_RETRY.ZP_LANG_ID == retry_zp_lang_id
            ))
        )

        tv_missing_raw_eapi_image = qry_tv_missing_raw_eapi_image.order_by(TABLES.ZP_TV_EAPI_EID.ZP_TV_ID.desc()
                                                                           ).limit(50)
        session.close()
        if tv_missing_raw_eapi_image is not None:
            for tv in tv_missing_raw_eapi_image:
                return_list.append(tv.ZP_TV_ID)
        #raise SystemExit
        return return_list

    def get_tv_missing_raw_eapi_image_retry(self, zp_tv_id, eapi, zp_lang_id, zp_entity_id_list):
        session = self.Session()
        return_dict = {}
        # we only need to get a non language image if we don't allready have an image (all iamges are chooseable
        # from the admin planel)
        if zp_lang_id is None:
            retry_zp_lang_id = 0
        else:
            retry_zp_lang_id = zp_lang_id
        qry_tv_missing_raw_eapi_image = session.query(
            TABLES.ZP_TV_EAPI_EID.ZP_TV_ID, TABLES.ZP_RETRY_COUNT.DELAY,
            TABLES.ZP_RETRY.DATETIME, TABLES.ZP_RETRY.COUNT
        ).join(TABLES.ZP_TV_EPISODE,
            TABLES.ZP_TV_EAPI_EID.ZP_TV_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID
        ).join(TABLES.ZP_TV_EPISODE_RAW_IMAGE, and_(
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.EPISODE == TABLES.ZP_TV_EPISODE.EPISODE,
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.SEASON == TABLES.ZP_TV_EPISODE.SEASON,
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID,
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_EAPI_ID == TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID
            )
        ).join(TABLES.ZP_RETRY, and_(
            TABLES.ZP_RETRY.ZP_LANG_ID == retry_zp_lang_id,
            TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID == TABLES.ZP_TV_EAPI_EID.ZP_TV_ID,
            TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 11,
            TABLES.ZP_RETRY.ZP_EAPI_ID == TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID
            )
        ).join(TABLES.ZP_RETRY_COUNT,
            TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == TABLES.ZP_RETRY_COUNT.ZP_RETRY_TYPE_ID
        ).filter(
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID.in_(zp_entity_id_list),
            TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID == self.eapi_dict[eapi],
            TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_LANG_ID == zp_lang_id,
            TABLES.ZP_TV_EAPI_EID.ZP_TV_ID < zp_tv_id,
            TABLES.ZP_RETRY_COUNT.COUNT == session.query(
                func.max(TABLES.ZP_RETRY_COUNT.COUNT)
            ).filter(
                TABLES.ZP_RETRY.COUNT >= TABLES.ZP_RETRY_COUNT.COUNT).order_by(
                TABLES.ZP_RETRY_COUNT.COUNT.desc()).correlate(TABLES.ZP_RETRY).as_scalar(),
        ).group_by(
            TABLES.ZP_TV_EAPI_EID.ZP_TV_ID
        ).having(
            func.count() < session.query(func.count(TABLES.ZP_TV_EPISODE.EPISODE).label('E_COUNT')).filter(
                TABLES.ZP_TV_EPISODE.ZP_TV_ID == TABLES.ZP_TV_EAPI_EID.ZP_TV_ID
            ).correlate(TABLES.ZP_TV_EAPI_EID).as_scalar() * len(zp_entity_id_list)
        )
        tv_missing_raw_eapi_image = qry_tv_missing_raw_eapi_image.order_by(TABLES.ZP_TV_EAPI_EID.ZP_TV_ID.desc()
                                                                           ).limit(50)
        session.close()
        if tv_missing_raw_eapi_image is not None:
            for result in tv_missing_raw_eapi_image:
                return_dict[result.ZP_TV_ID] = {}
                return_dict[result.ZP_TV_ID]['datetime'] = result.DATETIME
                return_dict[result.ZP_TV_ID]['count'] = result.COUNT
                return_dict[result.ZP_TV_ID]['delay'] = result.DELAY
        return return_dict

    def get_tv_not_in_raw_eapi_image_retry(self, zp_tv_id, eapi, zp_lang_id, zp_entity_id_list):
        session = self.Session()
        return_dict = {}
        if zp_lang_id is None:
            retry_zp_lang_id = 0
        else:
            retry_zp_lang_id = zp_lang_id
        qry_tv_missing_raw_eapi_image = session.query(
            TABLES.ZP_TV_EAPI_EID.ZP_TV_ID, TABLES.ZP_RETRY_COUNT.DELAY,
            TABLES.ZP_RETRY.DATETIME, TABLES.ZP_RETRY.COUNT
        ).join(TABLES.ZP_RETRY, and_(
            TABLES.ZP_RETRY.ZP_LANG_ID == retry_zp_lang_id,
            TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID == TABLES.ZP_TV_EAPI_EID.ZP_TV_ID,
            TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 11,
            TABLES.ZP_RETRY.ZP_EAPI_ID == TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID
            )
        ).join(TABLES.ZP_RETRY_COUNT,
            TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == TABLES.ZP_RETRY_COUNT.ZP_RETRY_TYPE_ID
        ).filter(
            TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID == self.eapi_dict[eapi],
            TABLES.ZP_TV_EAPI_EID.ZP_TV_ID < zp_tv_id,
            ~TABLES.ZP_TV_EAPI_EID.ZP_TV_ID.in_(session.query(
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID.distinct().label('ZP_ENTITY_ID')).filter(
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID.in_(zp_entity_id_list),
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_EAPI_ID == TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID,
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_LANG_ID == zp_lang_id
            ).group_by(
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID,
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID
            ).having(
                func.count(TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID.distinct().label('ZP_ENTITY_TYPE_ID')) ==
                len(zp_entity_id_list)
            )),
            TABLES.ZP_RETRY_COUNT.COUNT == session.query(
                func.max(TABLES.ZP_RETRY_COUNT.COUNT)
            ).filter(
                TABLES.ZP_RETRY.COUNT >= TABLES.ZP_RETRY_COUNT.COUNT).order_by(
                TABLES.ZP_RETRY_COUNT.COUNT.desc()).correlate(TABLES.ZP_RETRY).as_scalar()
        )

        tv_missing_raw_eapi_image = qry_tv_missing_raw_eapi_image.order_by(TABLES.ZP_TV_EAPI_EID.ZP_TV_ID.desc()
                                                                           ).limit(50)
        session.close()
        #if tv_missing_raw_eapi_image is not None:
        #    for tv in tv_missing_raw_eapi_image:
        #        return_list.append(tv.ZP_TV_ID)
        #raise SystemExit
        if tv_missing_raw_eapi_image is not None:
            for result in tv_missing_raw_eapi_image:
                return_dict[result.ZP_TV_ID] = {}
                return_dict[result.ZP_TV_ID]['datetime'] = result.DATETIME
                return_dict[result.ZP_TV_ID]['count'] = result.COUNT
                return_dict[result.ZP_TV_ID]['delay'] = result.DELAY
        return return_dict

    def get_tv_season_missing_raw_eapi_image(self, zp_tv_id, eapi, zp_lang_id, zp_entity_id_list):
        session = self.Session()
        return_dict = {}
        qry_tv_missing_raw_eapi_image = session.query(
            TABLES.ZP_TV_EPISODE.SEASON,
            TABLES.ZP_TV_EPISODE.EPISODE
        ).filter(
            TABLES.ZP_TV.ID == zp_tv_id,
            TABLES.ZP_TV_EPISODE.ZP_TV_ID == TABLES.ZP_TV.ID,
            ~TABLES.ZP_TV.ID.in_(
                session.query(TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID).filter(
                    TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID.in_(zp_entity_id_list),
                    TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi],
                    TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_LANG_ID == zp_lang_id,
                    TABLES.ZP_TV_EPISODE_RAW_IMAGE.SEASON == TABLES.ZP_TV_EPISODE.SEASON,
                    TABLES.ZP_TV_EPISODE_RAW_IMAGE.EPISODE == TABLES.ZP_TV_EPISODE.EPISODE
                ).group_by(
                    TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID, TABLES.ZP_TV_EPISODE_RAW_IMAGE.SEASON,
                    TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID, TABLES.ZP_TV_EPISODE_RAW_IMAGE.EPISODE
                ).having(
                    func.count(TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID) == len(zp_entity_id_list)
                )
            ),
            TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_EAPI_EID.ZP_TV_ID).filter(
                    TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID == self.eapi_dict[eapi]
                )
            )
        )

        qry_tv_missing_raw_eapi_image_count = qry_tv_missing_raw_eapi_image.count()
        log.debug('qry_tv_missing_raw_eapi_image_count no retry: %s', qry_tv_missing_raw_eapi_image_count)
        if qry_tv_missing_raw_eapi_image_count > 0:
            tv_missing_raw_eapi_image = qry_tv_missing_raw_eapi_image.order_by(TABLES.ZP_TV_EPISODE.SEASON.asc()).all()
            session.close()
            for episode in tv_missing_raw_eapi_image:
                if episode.SEASON not in return_dict:
                    return_dict[episode.SEASON] = []
                return_dict[episode.SEASON].append(episode.EPISODE)
        log.debug('return_dict %s', return_dict)
        return return_dict

    def check_missing_eapi_raw_images(self, zp_tv_id, eapi, zp_lang_id, zp_entity_id_list):
        session = self.Session()
        if zp_lang_id is None:
            retry_zp_lang_id = 0
        else:
            retry_zp_lang_id = zp_lang_id
        try:
            session.query(
                TABLES.ZP_TV_EAPI_EID.ZP_TV_ID
            ).join(TABLES.ZP_TV_EPISODE,
                   TABLES.ZP_TV_EAPI_EID.ZP_TV_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID
                   ).join(TABLES.ZP_TV_EPISODE_RAW_IMAGE, and_(
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.EPISODE == TABLES.ZP_TV_EPISODE.EPISODE,
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.SEASON == TABLES.ZP_TV_EPISODE.SEASON,
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID,
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_EAPI_ID == TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID
            )
                          ).filter(
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID.in_(zp_entity_id_list),
                TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID == self.eapi_dict[eapi],
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_LANG_ID == zp_lang_id,
                TABLES.ZP_TV_EAPI_EID.ZP_TV_ID == zp_tv_id,
                # left join is null/not in/not exists all seem to be simmilar times
                ~TABLES.ZP_TV_EAPI_EID.ZP_TV_ID.in_(session.query(
                    TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                    TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 11,
                    TABLES.ZP_RETRY.ZP_EAPI_ID == self.eapi_dict[eapi],
                    TABLES.ZP_RETRY.ZP_LANG_ID == retry_zp_lang_id
                ))
            ).group_by(
                TABLES.ZP_TV_EAPI_EID.ZP_TV_ID
            ).having(
                func.count() < session.query(func.count(TABLES.ZP_TV_EPISODE.EPISODE).label('E_COUNT')).filter(
                    TABLES.ZP_TV_EPISODE.ZP_TV_ID == TABLES.ZP_TV_EAPI_EID.ZP_TV_ID
                ).correlate(TABLES.ZP_TV_EAPI_EID).as_scalar() * len(zp_entity_id_list)
            )
        except orm.exc.NoResultFound:
            session.close()
            return False
        session.close()
        return True

    def check_tv_for_image_type(self, zp_tv_id, eapi, zp_lang_id, image_type_id):
        session = self.Session()
        try:
            session.query(TABLES.ZP_TV_EPISODE_RAW_IMAGE).filter(
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID == zp_tv_id,
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID == image_type_id,
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi],
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_LANG_ID == zp_lang_id
            ).one()
        except orm.exc.NoResultFound:
            raw_image_present = False
        else:
            raw_image_present = True
        session.close()
        return raw_image_present

    def acquire_images(self, user_langs):
        log.debug('acquire_images start')
        session = self.Session()
        max_tv_id = session.query(func.max(TABLES.ZP_TV.ID)).one()[0]
        session.close()
        log.debug('user_langs %s', user_langs)
        if isinstance(max_tv_id, int):
            for eapi in self.eapi_tv_plugins_access_list:
                log.debug('eapi %s', eapi)
                if hasattr(getattr(self, eapi), 'supported_tv_images'):
                    if hasattr(getattr(self, eapi), 'get_tv_episode_raw_images'):
                        eapi_image_type_dict = {}
                        eapi_image_type_id_list = []
                        for image_type in self.image_types_dict:
                            log.debug('image_type %s', image_type)
                            eapi_supported_tv_images = getattr(getattr(self, eapi), 'supported_tv_images')
                            if 'episode' in eapi_supported_tv_images:
                                if isinstance(eapi_supported_tv_images['episode'], list):
                                    if image_type in eapi_supported_tv_images['episode']:
                                        eapi_image_type_dict[image_type] = self.image_types_dict[image_type]
                                        eapi_image_type_id_list.append(self.image_types_dict[image_type]['id'])
                                    else:
                                        log.warning("image_type %s not in eapi_supported_tv_images['episode']s %s",
                                                    image_type, eapi_supported_tv_images['episode'])
                                else:
                                    log.warning("eapi_supported_tv_images['show'] not a list but %s",
                                                type(eapi_supported_tv_images))
                            else:
                                log.warning("show not in eapi_supported_tv_images %s",
                                            eapi_supported_tv_images)
                        log.debug('eapi_image_type_dict %s, eapi_image_type_id_list %s, self.image_types_dict %s',
                                  eapi_image_type_dict, eapi_image_type_id_list, self.image_types_dict)
                        # raise SystemExit
                        if eapi_image_type_dict:
                            # screen shots do not have specific languages
                            #if getattr(getattr(self, eapi), 'supported_tv_image_langs') is True:
                            #    log.debug('eapi %s supports lang images', eapi)
                            #    for zp_lang_id in user_langs:
                            #        log.error('eapi %s supports lang images. Current lang %s', eapi, zp_lang_id)
                            #        self.acquire_lang_images_no_retry(eapi, eapi_image_type_dict,
                            #                                          eapi_image_type_id_list,
                            #                                          max_tv_id, zp_lang_id)
                            #        # raise SystemExit
                            #        self.acquire_lang_images_retry(eapi, eapi_image_type_dict,
                            #                                       eapi_image_type_id_list,
                            #                                       max_tv_id, zp_lang_id)
                            #else:
                            #log.error('eapi %s does not support lang images', eapi)
                            self.acquire_lang_images_no_retry(eapi, eapi_image_type_dict,
                                                              eapi_image_type_id_list,
                                                              max_tv_id, None)
                            #raise SystemExit
                            if self.check_can_retry(1) is True:
                                log.debug('Retrying TV Episode Raw Images')
                                self.acquire_lang_images_retry(eapi, eapi_image_type_dict,
                                                           eapi_image_type_id_list,
                                                           max_tv_id, None)
                        else:
                            log.warning('eapi_image_types %s is empty for eapi %s', eapi_image_type_dict,
                                      eapi)
                            # log.error('exiting 422')
                            # raise SystemExit('exiting 422')
                    else:
                        log.warning('eapi %s does not have get_tv_episode_raw_images', eapi)
                else:
                    log.warning('eapi %s does not have supported_tv_images', eapi)
        else:
            log.warning('max_tv_id %s is not int but %s', max_tv_id, type(max_tv_id))

    def acquire_lang_images_no_retry(self, eapi, eapi_image_type_dict, eapi_image_type_id_list,
                                     max_tv_id, zp_lang_id):
        log.debug('acquire_lang_images_no_retry')
        tv_processing_complete = False
        zp_tv_id = max_tv_id + 1
        while tv_processing_complete is False:
            log.debug('no retry getting get_tv_missing_raw_eapi_image_no_retry eapi %s, zp_lang_id %s',
                      eapi, zp_lang_id)
            zp_tv_list = self.get_tv_not_in_raw_eapi_image_no_retry(zp_tv_id, eapi, zp_lang_id,
                                                                     eapi_image_type_id_list)
            log.debug('no retry eapi %s, zp_lang_id %s, zp_tv_list %s', eapi, zp_lang_id, zp_tv_list)
            if zp_tv_list:
                for zp_tv_list_id in zp_tv_list:
                    zp_tv_id = zp_tv_list_id
                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                 20,
                                                 'LANG: %s, Eapi: %s, TV: %s/%s' % (
                                                                     zp_lang_id, eapi,
                                                                     zp_tv_id, max_tv_id
                                                                 ))
                    # for season in zp_tv_episode_dict:
                    # log.debug('zp_tv_id %s, Season %s, zp_lang_id %s', zp_tv_id, season, zp_lang_id)
                    self.eapi_lang_images(eapi, zp_tv_id, zp_lang_id, eapi_image_type_dict,
                                          eapi_image_type_id_list)
                    #raise SystemExit
            else:
                tv_processing_complete = True
                # raise SystemExit

        tv_processing_complete = False
        zp_tv_id = max_tv_id + 1
        while tv_processing_complete is False:
            log.debug('no retry getting get_tv_missing_raw_eapi_image_no_retry eapi %s, zp_lang_id %s',
                      eapi, zp_lang_id)
            zp_tv_list = self.get_tv_missing_raw_eapi_image_no_retry(zp_tv_id, eapi, zp_lang_id,
                                                                     eapi_image_type_id_list)
            log.debug('no retry eapi %s, zp_lang_id %s, zp_tv_list %s', eapi, zp_lang_id, zp_tv_list)
            #raise SystemExit
            if zp_tv_list:
                for zp_tv_list_id in zp_tv_list:
                    zp_tv_id = zp_tv_list_id
                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                 20,
                                                 'LANG: %s, Eapi: %s, TV: %s/%s' % (
                                                                     zp_lang_id, eapi,
                                                                     zp_tv_id, max_tv_id
                                                                 ))
                    # for season in zp_tv_episode_dict:
                    # log.debug('zp_tv_id %s, Season %s, zp_lang_id %s', zp_tv_id, season, zp_lang_id)
                    self.eapi_lang_images(eapi, zp_tv_id, zp_lang_id, eapi_image_type_dict,
                                          eapi_image_type_id_list)
                    #raise SystemExit
            else:
                tv_processing_complete = True

    def acquire_lang_images_retry(self, eapi, eapi_image_type_dict, eapi_image_type_id_list,
                                  max_tv_id, zp_lang_id):
        tv_processing_complete = False
        zp_tv_id = max_tv_id + 1
        while tv_processing_complete is False:
            zp_tv_dict = self.get_tv_not_in_raw_eapi_image_retry(zp_tv_id, eapi, zp_lang_id,
                                                                  eapi_image_type_id_list)
            #raise SystemExit
            if zp_tv_dict:
                # we need the ids in deceding order but dict keys can be in any order
                for zp_tv_dict_id in reversed(sorted(zp_tv_dict)):
                    log.debug('retry processing zp_tv_id %s for eapi %s', zp_tv_id, eapi)
                    zp_tv_id = zp_tv_dict_id
                    if zp_tv_dict[zp_tv_id]['datetime'] + timedelta(
                        days=zp_tv_dict[zp_tv_id]['delay']) <= datetime.now():
                        log.debug('dt %s, plus %s is %s which is less than than now %s',
                                  zp_tv_dict[zp_tv_id]['datetime'],
                                  zp_tv_dict[zp_tv_id]['delay'],
                                  zp_tv_dict[zp_tv_id]['datetime'] + timedelta(
                                      days=zp_tv_dict[zp_tv_id]['delay']), datetime.now())
                        self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                 20,
                                                 'LANG: %s, Eapi: %s, TV: %s/%s. Retrying' % (
                                                                     zp_lang_id, eapi,
                                                                     zp_tv_id, max_tv_id
                                                                 ))
                        self.eapi_lang_images(eapi, zp_tv_id, zp_lang_id, eapi_image_type_dict,
                                              eapi_image_type_id_list)

                    else:
                        self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                 20,
                                                 'LANG: %s, Eapi: %s, TV: %s/%s. Not Retrying' % (
                                                                     zp_lang_id, eapi,
                                                                     zp_tv_id, max_tv_id
                                                                 ))
                        log.debug('dt %s, plus %s is %s which is not less than now %s',
                                  zp_tv_dict[zp_tv_id]['datetime'],
                                  zp_tv_dict[zp_tv_id]['delay'],
                                  zp_tv_dict[zp_tv_id]['datetime'] + timedelta(
                                      days=zp_tv_dict[zp_tv_id]['delay']), datetime.now())

            else:
                tv_processing_complete = True
        tv_processing_complete = False
        zp_tv_id = max_tv_id + 1
        while tv_processing_complete is False:
            zp_tv_dict = self.get_tv_missing_raw_eapi_image_retry(zp_tv_id, eapi, zp_lang_id,
                                                                  eapi_image_type_id_list)
            #raise SystemExit
            if zp_tv_dict:
                # we need the ids in deceding order but dict keys can be in any order
                for zp_tv_dict_id in reversed(sorted(zp_tv_dict)):
                    log.debug('retry processing zp_tv_id %s for eapi %s', zp_tv_id, eapi)
                    zp_tv_id = zp_tv_dict_id
                    if zp_tv_dict[zp_tv_id]['datetime'] + timedelta(
                        days=zp_tv_dict[zp_tv_id]['delay']) <= datetime.now():
                        log.debug('dt %s, plus %s is %s which is less than than now %s',
                                  zp_tv_dict[zp_tv_id]['datetime'],
                                  zp_tv_dict[zp_tv_id]['delay'],
                                  zp_tv_dict[zp_tv_id]['datetime'] + timedelta(
                                      days=zp_tv_dict[zp_tv_id]['delay']), datetime.now())
                        self.eapi_lang_images(eapi, zp_tv_id, zp_lang_id, eapi_image_type_dict,
                                              eapi_image_type_id_list)

                    else:
                        log.debug('dt %s, plus %s is %s which is not less than now %s',
                                  zp_tv_dict[zp_tv_id]['datetime'],
                                  zp_tv_dict[zp_tv_id]['delay'],
                                  zp_tv_dict[zp_tv_id]['datetime'] + timedelta(
                                      days=zp_tv_dict[zp_tv_id]['delay']), datetime.now())

            else:
                tv_processing_complete = True

    def get_seasons_image_type_dict(self, zp_tv_id, eapi, zp_lang_id, eapi_image_type_dict, zp_tv_episode_dict):
        tv_season_not_missing_raw_eapi_images_dict = self.get_tv_season_not_missing_raw_eapi_image(zp_tv_id, eapi,
                                                                                                   zp_lang_id)
        log.debug('tv_season_not_missing_raw_eapi_images_dict %s', tv_season_not_missing_raw_eapi_images_dict)
        # raise SystemExit
        seasons_image_type_dict = {}
        for season in zp_tv_episode_dict:
            if season in tv_season_not_missing_raw_eapi_images_dict:
                for episode in zp_tv_episode_dict[season]:
                    if episode in tv_season_not_missing_raw_eapi_images_dict[season]:
                        for image_type in eapi_image_type_dict:
                            if eapi_image_type_dict[image_type]['id'] not in tv_season_not_missing_raw_eapi_images_dict[season][episode]:
                                if season not in seasons_image_type_dict:
                                    seasons_image_type_dict[season] = {}
                                seasons_image_type_dict[season][episode] = {}
                                seasons_image_type_dict[season][episode][image_type] = eapi_image_type_dict[image_type]
                    else:
                        if season not in seasons_image_type_dict:
                            seasons_image_type_dict[season] = {}
                        seasons_image_type_dict[season][episode] = {}
                        for image_type in eapi_image_type_dict:
                            seasons_image_type_dict[season][episode][image_type] = eapi_image_type_dict[image_type]
            else:
                seasons_image_type_dict[season] = {}
                for episode in zp_tv_episode_dict[season]:
                    seasons_image_type_dict[season][episode] = {}
                    for image_type in eapi_image_type_dict:
                        seasons_image_type_dict[season][episode][image_type] = eapi_image_type_dict[image_type]
        log.debug('seasons_image_type_dict %s', seasons_image_type_dict)
        return seasons_image_type_dict

    def eapi_lang_images(self, eapi, zp_tv_id, zp_lang_id, eapi_image_type_dict,
                         eapi_image_type_id_list):
        zp_tv_eapi_eid = self.eapi_eid_from_zp_tv_id(self.eapi_dict[eapi], zp_tv_id)
        if zp_tv_eapi_eid is not None:
            zp_tv_episode_dict = self.get_tv_season_missing_raw_eapi_image(zp_tv_id, eapi, zp_lang_id,
                                                                          eapi_image_type_id_list)
            log.debug('zp_tv_episode_dict %s', zp_tv_episode_dict)
            #raise SystemExit
            seasons_image_type_dict = self.get_seasons_image_type_dict(zp_tv_id, eapi, zp_lang_id,
                                                                       eapi_image_type_dict, zp_tv_episode_dict)

            log.debug('seasons_image_type_dict %s', seasons_image_type_dict)
            #raise SystemExit
            if zp_tv_episode_dict and seasons_image_type_dict:
                # raise SystemExit
                tv_raw_image_root_path = os.path.join(
                    self.library_config_dict['downloaded_images_library_root_path'], str(zp_tv_id))
                if make_dir(tv_raw_image_root_path):
                    log.debug('eapi_image_type_dict %s', eapi_image_type_dict)
                    log.debug('seasons_image_type_dict %s', seasons_image_type_dict)
                    log.debug('zp_tv_episode_dict %s', zp_tv_episode_dict)
                    # raise SystemExit
                    log.debug('zp_tv_id %s, zp_tv_eapi_eid %s, eapi %s', zp_tv_id, zp_tv_eapi_eid, eapi)
                    self.acquire_tv_eapi_raw_images(zp_tv_id, zp_tv_episode_dict,
                                                    zp_lang_id,
                                                    eapi, zp_tv_eapi_eid,
                                                    seasons_image_type_dict,
                                                    tv_raw_image_root_path)
                    #raise SystemExit
                    if self.check_missing_eapi_raw_images(zp_tv_id, eapi, zp_lang_id,
                                                          eapi_image_type_id_list) is True:
                        log.debug('missing images for zp_atv_id %s, eapi %s, lang %s, image_types %s',
                                  zp_tv_id, eapi, zp_lang_id, eapi_image_type_id_list)
                        # raise SystemExit
                        # if getattr(getattr(self, eapi), 'supported_tv_image_langs') is True:
                        log.debug('setting retry for eapi %s, zp_lang_id %s,'
                                  'and supported_tv_image_langs %s',
                                  eapi, zp_lang_id,
                                  getattr(getattr(self, eapi),
                                          'supported_tv_image_langs'))
                        self.set_retry(1, 11, zp_tv_id, self.eapi_dict[eapi], zp_lang_id)
                    else:
                        log.debug('not missing images for eapi %s, lang %s, image_types %s',
                                  eapi, zp_lang_id, eapi_image_type_id_list)
                        # raise SystemExit
                else:
                    log.debug('could not make dir %s', tv_raw_image_root_path)

    def acquire_tv_eapi_raw_images(self, zp_tv_id, zp_tv_episode_dict, zp_lang_id, eapi, zp_tv_eapi_eid,
                                   seasons_image_type_dict, tv_raw_image_root_path):
        if hasattr(getattr(self, eapi), 'get_tv_season_raw_images'):
            if zp_lang_id is None:
                iso_639_part1 = None
            else:
                iso_639_part1 = self.iso_639_part1_from_zp_lang_id(zp_lang_id)
            log.debug('iso_639_part1 %s', iso_639_part1)
            if (iso_639_part1 is not None and zp_lang_id is not None) or \
                (iso_639_part1 is None and zp_lang_id is None):
                eapi_raw_iamges_dict = getattr(getattr(self, eapi), 'get_tv_episode_raw_images')(
                    zp_tv_eapi_eid, zp_tv_episode_dict, iso_639_part1, seasons_image_type_dict)
                log.debug('eapi_raw_iamges_dict %s', eapi_raw_iamges_dict)
                #raise SystemExit
                if isinstance(eapi_raw_iamges_dict, dict):
                    if eapi_raw_iamges_dict:
                    # for eapi_raw_iamges_dict in eapi_raw_iamges_list:
                    # log.debug('eapi_raw_iamges_dict %s', eapi_raw_iamges_dict)
                    # if isinstance(eapi_raw_iamges_dict, dict):
                        for season in seasons_image_type_dict:
                            if season in eapi_raw_iamges_dict:
                                tv_season_raw_image_root_path = os.path.join(tv_raw_image_root_path, str(season))
                                if make_dir(tv_season_raw_image_root_path):
                                    for episode in seasons_image_type_dict[season]:
                                        if episode in eapi_raw_iamges_dict[season]:
                                            #log.debug('image_types %s', seasons_image_type_dict[season].keys())
                                            for image_type in seasons_image_type_dict[season][episode]:
                                                if image_type in eapi_raw_iamges_dict[season][episode]:
                                                    if isinstance(eapi_raw_iamges_dict[season][episode][image_type], dict):
                                                        if 'image_reference' in eapi_raw_iamges_dict[season][episode][image_type] and \
                                                                'image_url' in eapi_raw_iamges_dict[season][episode][image_type]:
                                                            log.debug('image_reference and image_url in %s',
                                                                      eapi_raw_iamges_dict[season][episode][image_type])
                                                            image_reference = eapi_raw_iamges_dict[season][episode][image_type][
                                                                'image_reference']
                                                            image_reference_extension = get_file_extension(image_reference)
                                                            if image_reference_extension in self.allowed_extension_list:
                                                                image_download_url = eapi_raw_iamges_dict[season][episode][image_type][
                                                                    'image_url']
                                                                if isinstance(image_reference, string_types) and isinstance(
                                                                    image_download_url, string_types):
                                                                    log.debug('image_reference %s, url %s', image_reference,
                                                                              image_download_url)
                                                                    image_uuid = uuid.uuid4()
                                                                    new_tv_image_filename = '%s.%s' % (
                                                                    image_uuid, image_reference_extension)
                                                                    new_tv_image_path = os.path.join(tv_season_raw_image_root_path,
                                                                                                     new_tv_image_filename)
                                                                    log.debug('new_tv_image_path %s', new_tv_image_path)
                                                                    # raise SystemExit
                                                                    if download(image_download_url, new_tv_image_path) is True:
                                                                        self.set_acquired_eapi_image(
                                                                            seasons_image_type_dict[season][episode][image_type]['id'],
                                                                            eapi, zp_tv_id, season, episode, zp_lang_id,
                                                                            image_reference, new_tv_image_filename)
                                                                    else:
                                                                        log.warning('unable to download %s to %s',
                                                                                    image_download_url,
                                                                                    new_tv_image_path)
                                                                else:
                                                                    log.warning(
                                                                        'image_reference %s type: and or url %s type: not string_types',
                                                                        image_reference, type(image_reference), image_download_url,
                                                                        type(image_download_url))
                                                            else:
                                                                log.warning(
                                                                    'image_reference_extension %s for image_reference %s is not in'
                                                                    ' list: %s',
                                                                    image_reference_extension, image_reference,
                                                                    self.allowed_extension_list)
                                                        else:
                                                            log.warning('image_reference and or image_url not'
                                                                        ' in eapi_raw_iamges_dict[image_type] %s',
                                                                        eapi_raw_iamges_dict[season][image_type])
                                                    else:
                                                        log.warning('image_type %s eapi_raw_iamges_dict[image_type] %s is not dict',
                                                                    image_type, type(eapi_raw_iamges_dict[season][image_type]))
                                                else:
                                                    log.warning('image_type %s not in eapi_raw_iamges_dict %s', image_type,
                                                                eapi_raw_iamges_dict[season])
                                else:
                                    log.warning('could not make tv_season_raw_image_root_path %s for season %s',
                                                tv_season_raw_image_root_path, season)
                            else:
                                log.warning('season %s not in eapi_raw_iamges_dict %s', season,
                                            eapi_raw_iamges_dict)
                                # else:
                                #    log.warning('eapi_raw_iamges_dict %s type %s is not dict',
                                #                eapi_raw_iamges_dict, type(eapi_raw_iamges_dict))
                                # else:
                                #    log.warning('eapi_raw_iamges_list %s type %s is not dict',
                                #                eapi_raw_iamges_list, type(eapi_raw_iamges_list))
                    else:
                        log.debug('eapi_raw_iamges_dict %s is empty', eapi_raw_iamges_dict)
                        #raise SystemExit
                else:
                    log.error('eapi_raw_iamges_dict %s not dict but %s', eapi_raw_iamges_dict,
                              type(eapi_raw_iamges_dict))
                    #raise SystemExit
        else:
            log.warning('eapi %s, does not have function get_tv_season_raw_images', eapi)
        #raise SystemExit

    def set_acquired_eapi_image(self, image_type_id, eapi, zp_tv_id, season, episode, zp_lang_id,
                                image_reference, new_tv_image_filename):
        session = self.Session()
        try:
            zp_tv_raw_image = session.query(TABLES.ZP_TV_EPISODE_RAW_IMAGE).filter(
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID == image_type_id,
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID == zp_tv_id,
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.SEASON == season,
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.EPISODE == episode,
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi],
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_LANG_ID == zp_lang_id
            ).one()
        except orm.exc.NoResultFound:
            add_zp_tv_raw_image = TABLES.ZP_TV_EPISODE_RAW_IMAGE(ZP_ENTITY_TYPE_ID=image_type_id,
                                                                ZP_ENTITY_ID=zp_tv_id,
                                                                SEASON=season,
                                                                EPISODE=episode,
                                                                ZP_EAPI_ID=self.eapi_dict[eapi],
                                                                ZP_LANG_ID=zp_lang_id,
                                                                ZP_EAPI_IMAGE_REF=image_reference,
                                                                FILENAME=new_tv_image_filename)
            session.add(add_zp_tv_raw_image)
            if commit(session):
                update_tv_last_mod(self.Session, zp_tv_id)
        else:
            log.error('there is allready an extry for ZP_TV_EPISODE_RAW_IMAGE with ZP_ENTITY_TYPE_ID %s'
                      ' ZP_ENTITY_ID %s, SEASON %s, ZP_EAPI_ID %s, ZP_LANG_ID %s of ID %s',
                      image_type_id, zp_tv_id,
                      season, self.eapi_dict[eapi], zp_lang_id, zp_tv_raw_image.ID)
            #raise SystemExit
        session.close()
