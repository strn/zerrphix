# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import sys
from datetime import datetime
from datetime import timedelta
from types import MethodType
from sqlalchemy import func, orm
import uuid
from zerrphix.db import flush, commit
from zerrphix.db.tables import TABLES
from zerrphix.film.util import update_film_last_mod, update_film_collection_last_mod
from zerrphix.plugin import load_plugins
from zerrphix.util import list1_not_in_list2
from zerrphix.util.plugin import create_eapi_plugins_list, create_eapi_dict
from zerrphix.util.text import date_time
from six import string_types
from six import text_type
from zerrphix.util.filesystem import make_dir
from zerrphix.util.web import download
from zerrphix.util.filesystem import get_file_extension
#from zerrphix.util import iso_639_part1_from_zp_lang_id, get_user_langs
import os
import copy
#from zerrphix.util import set_retry, check_can_retry
from zerrphix.film.base import FilmBase
from zerrphix.raw_images import RawImagesBase

log = logging.getLogger(__name__)

class RawCollectionImages(RawImagesBase):
    """Get Data for films (actors, runtime, synop etc...)
    """

    def __init__(self, **kwargs):
        super(RawCollectionImages, self).__init__(**kwargs)
        """Data __init__

            Args:
                | args (list): Passed through args from the command line.
                | Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.
        """
        self, self.eapi_film_plugins_access_list, loaded_plugins = create_eapi_plugins_list(
            'film', sys.modules, load_plugins(self.args), self)
        if not self.eapi_film_plugins_access_list:
            raise Exception(('There not any entries in eapi_film_plugins_access_list'
                             ' therefore scanning is pointless'))
        session = self.Session()
        self.eapi_dict = create_eapi_dict(session)
        session.close()
        self.data_keys = ['genres', 'title', 'original_title',
                          'overview', 'release_date', 'runtime',
                          'rating', 'credits', 'belongs_to_collection']

        #self.eapi_eid_from_zp_film_collection_id = MethodType(eapi_eid_from_zp_film_collection_id, self)
        #self.iso_639_part1_from_zp_lang_id = MethodType(iso_639_part1_from_zp_lang_id, self)
        self.allowed_extension_list = ['png', 'jpg', 'jpeg', 'gif', 'bmp']
        self.image_types_dict = {'backdrop':
                                     {'function':'get_backdrop_url',
                                      'id':2},
                                 'poster':
                                     {'function':'get_poster_url',
                                      'id':1}}
        self.image_types_keys = ['backdrop', 'poster']
        #self.get_user_langs = MethodType(get_user_langs, self)
        #self.set_retry = MethodType(set_retry, self)
        #self.check_can_retry = MethodType(check_can_retry, self)

    def acquire(self):
        # self.acquire_film_data()
        # self.acquire_film_collection_data()
        # self.acquire_film_collection_data()
        # todo add a system default language
        #image_root_path = os.path.join(self.global_config_dict['downloaded_images_root_path'],
                                       #self.library_config_dict['name'])
        #if make_dir(image_root_path):
        self.collection_root_path = '%s_collection' % self.library_config_dict['downloaded_images_library_root_path']
        if make_dir(self.collection_root_path):
            user_langs = self.get_all_user_library_langs(1)
            # todo optionise adding english as a fallback when user specifics are done
            if 1823 not in user_langs:
                user_langs[1823] = 'English'
            self.user_langs = user_langs
            log.debug(user_langs)
            for zp_lang in user_langs:
                self.acquire_lang_images(zp_lang)
        else:
            log.error('''cannot make dir self.collection_root_path %s''',
                      self.collection_root_path)

    def get_film_missing_raw_eapi_image_no_retry(self, zp_film_collection_id, eapi, zp_lang_id):
        session = self.Session()
        return_list = []
        if zp_lang_id is None:
            qry_film_missing_raw_eapi_image = session.query(
                TABLES.ZP_FILM_COLLECTION).filter(
                TABLES.ZP_FILM_COLLECTION.ID < zp_film_collection_id,
                (~TABLES.ZP_FILM_COLLECTION.ID.in_(
                    session.query(TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_ID).filter(
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_TYPE_ID == 1,
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi]
                    )) |
                ~TABLES.ZP_FILM_COLLECTION.ID.in_(
                    session.query(TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_ID).filter(
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_TYPE_ID == 2,
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi]
                    ))),
                TABLES.ZP_FILM_COLLECTION.ID.in_(
                    session.query(
                        TABLES.ZP_FILM_COLLECTION_EAPI_EID.ZP_FILM_COLLECTION_ID)),
                ~TABLES.ZP_FILM_COLLECTION.ID.in_(session.query(
                    TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                    TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 12,
                    TABLES.ZP_RETRY.ZP_EAPI_ID == self.eapi_dict[eapi],
                    TABLES.ZP_RETRY.ZP_LANG_ID == zp_lang_id
                ))
            )
        else:
            qry_film_missing_raw_eapi_image = session.query(
                TABLES.ZP_FILM_COLLECTION).filter(
                TABLES.ZP_FILM_COLLECTION.ID < zp_film_collection_id,
                (~TABLES.ZP_FILM_COLLECTION.ID.in_(
                    session.query(TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_ID).filter(
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_TYPE_ID == 1,
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi],
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_LANG_ID == zp_lang_id
                    )) |
                ~TABLES.ZP_FILM_COLLECTION.ID.in_(
                    session.query(TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_ID).filter(
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_TYPE_ID == 2,
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi],
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_LANG_ID == zp_lang_id
                    ))),
                TABLES.ZP_FILM_COLLECTION.ID.in_(
                    session.query(
                        TABLES.ZP_FILM_COLLECTION_EAPI_EID.ZP_FILM_COLLECTION_ID)),
                ~TABLES.ZP_FILM_COLLECTION.ID.in_(session.query(
                    TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                    TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 12,
                    TABLES.ZP_RETRY.ZP_EAPI_ID == self.eapi_dict[eapi],
                    TABLES.ZP_RETRY.ZP_LANG_ID == zp_lang_id
                ))
            )

        qry_film_missing_raw_eapi_image_count = qry_film_missing_raw_eapi_image.count()
        log.debug('qry_film_missing_raw_eapi_image_count no retry: %s', qry_film_missing_raw_eapi_image_count)
        if qry_film_missing_raw_eapi_image_count > 0:
            film_missing_raw_eapi_image = qry_film_missing_raw_eapi_image.order_by(TABLES.ZP_FILM_COLLECTION.ID.desc()).limit(1000)
            session.close()
            for film in film_missing_raw_eapi_image:
                return_list.append(film.ID)
        return return_list

    def get_film_missing_raw_eapi_image_retry(self, zp_film_collection_id, eapi, zp_lang_id):
        session = self.Session()
        return_dict = {}
        # we only need to get a non language image if we don't allready have an image (all iamges are chooseable
        # from the admin planel)
        if zp_lang_id is None:
            qry_film_missing_raw_eapi_image = session.query(
                TABLES.ZP_FILM_COLLECTION.ID, TABLES.ZP_RETRY_COUNT.DELAY,
                TABLES.ZP_RETRY.DATETIME, TABLES.ZP_RETRY.COUNT).filter(
                TABLES.ZP_FILM_COLLECTION.ID < zp_film_collection_id,
                (~TABLES.ZP_FILM_COLLECTION.ID.in_(
                    session.query(TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_ID).filter(
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_TYPE_ID == 1,
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi]
                    )) |
                ~TABLES.ZP_FILM_COLLECTION.ID.in_(
                    session.query(TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_ID).filter(
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_TYPE_ID == 2,
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi]
                    ))),
                TABLES.ZP_FILM_COLLECTION.ID.in_(
                    session.query(
                        TABLES.ZP_FILM_COLLECTION_EAPI_EID.ZP_FILM_COLLECTION_ID)),
            TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == TABLES.ZP_RETRY_COUNT.ZP_RETRY_TYPE_ID,
            TABLES.ZP_FILM_COLLECTION.ID == TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID,
            TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 12,
            TABLES.ZP_RETRY.ZP_EAPI_ID == self.eapi_dict[eapi],
            TABLES.ZP_RETRY.ZP_LANG_ID == zp_lang_id,
            TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == 1,
            TABLES.ZP_RETRY_COUNT.COUNT == session.query(
                func.max(TABLES.ZP_RETRY_COUNT.COUNT)
            ).filter(
                TABLES.ZP_RETRY.COUNT >= TABLES.ZP_RETRY_COUNT.COUNT).order_by(
                TABLES.ZP_RETRY_COUNT.COUNT.desc()).correlate(TABLES.ZP_RETRY).as_scalar()
            )
        else:
            qry_film_missing_raw_eapi_image = session.query(
            TABLES.ZP_FILM_COLLECTION.ID, TABLES.ZP_RETRY_COUNT.DELAY,
            TABLES.ZP_RETRY.DATETIME, TABLES.ZP_RETRY.COUNT).filter(
                TABLES.ZP_FILM_COLLECTION.ID < zp_film_collection_id,
                (~TABLES.ZP_FILM_COLLECTION.ID.in_(
                    session.query(TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_ID).filter(
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_TYPE_ID == 1,
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi],
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_LANG_ID == zp_lang_id
                    )) |
                ~TABLES.ZP_FILM_COLLECTION.ID.in_(
                    session.query(TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_ID).filter(
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_TYPE_ID == 2,
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi],
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_LANG_ID == zp_lang_id
                    ))),
                TABLES.ZP_FILM_COLLECTION.ID.in_(
                    session.query(
                        TABLES.ZP_FILM_COLLECTION_EAPI_EID.ZP_FILM_COLLECTION_ID)),
            TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == TABLES.ZP_RETRY_COUNT.ZP_RETRY_TYPE_ID,
            TABLES.ZP_FILM_COLLECTION.ID == TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID,
            TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 12,
            TABLES.ZP_RETRY.ZP_EAPI_ID == self.eapi_dict[eapi],
            TABLES.ZP_RETRY.ZP_LANG_ID == zp_lang_id,
            TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == 1,
            TABLES.ZP_RETRY_COUNT.COUNT == session.query(
                func.max(TABLES.ZP_RETRY_COUNT.COUNT)
            ).filter(
                TABLES.ZP_RETRY.COUNT >= TABLES.ZP_RETRY_COUNT.COUNT).order_by(
                TABLES.ZP_RETRY_COUNT.COUNT.desc()).correlate(TABLES.ZP_RETRY).as_scalar()
            )

        qry_film_missing_raw_eapi_image_count = qry_film_missing_raw_eapi_image.count()
        log.debug('qry_film_missing_raw_eapi_image_count retry: %s', qry_film_missing_raw_eapi_image_count)
        if qry_film_missing_raw_eapi_image_count > 0:
            film_missing_raw_eapi_image = qry_film_missing_raw_eapi_image.order_by(TABLES.ZP_FILM_COLLECTION.ID.desc()).limit(10000)
            session.close()
            for result in film_missing_raw_eapi_image:
                return_dict[result.ID] = {}
                return_dict[result.ID]['datetime'] = result.DATETIME
                return_dict[result.ID]['count'] = result.COUNT
                return_dict[result.ID]['delay'] = result.DELAY
        return return_dict

    def check_missing_eapi_raw_images(self, zp_film_collection_id, eapi, zp_lang_id):
        session = self.Session()
        try:
            session.query(
                TABLES.ZP_FILM_COLLECTION).filter(
                TABLES.ZP_FILM_COLLECTION.ID == zp_film_collection_id,
                (~TABLES.ZP_FILM_COLLECTION.ID.in_(
                    session.query(TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_ID).filter(
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_TYPE_ID == 1,
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi],
                        TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_LANG_ID == zp_lang_id,
                         TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_ID == zp_film_collection_id
                    )) |
                 ~TABLES.ZP_FILM_COLLECTION.ID.in_(
                     session.query(TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_ID).filter(
                         TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_TYPE_ID == 2,
                         TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi],
                         TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_LANG_ID == zp_lang_id,
                         TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_ID == zp_film_collection_id
                     )))
            ).one()
        except orm.exc.NoResultFound:
            session.close()
            return False
        session.close()
        return True

    def check_film_for_image_type(self, zp_film_collection_id, eapi, zp_lang_id, image_type_id):
        session = self.Session()
        try:
            session.query(TABLES.ZP_FILM_COLLECTION_RAW_IMAGE).filter(
                TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_ID == zp_film_collection_id,
                TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_TYPE_ID == image_type_id,
                TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi],
                TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_LANG_ID == zp_lang_id
            ).one()
        except orm.exc.NoResultFound:
            raw_image_present = False
        else:
            raw_image_present = True
        session.close()
        return raw_image_present

    def acquire_lang_images(self, zp_lang_id):
        session = self.Session()
        max_film_id = session.query(func.max(TABLES.ZP_FILM_COLLECTION.ID)).one()[0]
        session.close()
        if isinstance(max_film_id, int):
            for eapi in self.eapi_film_plugins_access_list:
                if hasattr(getattr(self, eapi), 'get_film_collection_raw_images'):
                    film_processing_complete = False
                    zp_film_collection_id = max_film_id + 1
                    while film_processing_complete is False:
                        zp_film_collection_list = self.get_film_missing_raw_eapi_image_no_retry(zp_film_collection_id, eapi, zp_lang_id)
                        if zp_film_collection_list:
                            for zp_film_collection_list_id in zp_film_collection_list:
                                zp_film_collection_id = zp_film_collection_list_id
                                self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                             19,
                                                             'LANG: %s, Eapi: %s, Film Collation: %s/%s' % (
                                                                                 zp_lang_id, eapi,
                                                                                 zp_film_collection_list_id,
                                                                                 max_film_id
                                                                             ))
                                zp_film_collection_eapi_eid = self.eapi_eid_from_zp_film_collection_id(self.eapi_dict[eapi], zp_film_collection_id)
                                if zp_film_collection_eapi_eid is not None:
                                    image_types = copy.deepcopy(self.image_types_dict)
                                    for image_type_key in self.image_types_keys:
                                        if self.check_film_for_image_type(zp_film_collection_id, eapi, zp_lang_id,
                                                                     image_types[image_type_key]['id']) is True:
                                            del image_types[image_type_key]
                                    film_raw_image_root_path = os.path.join(
                                        self.collection_root_path, str(zp_film_collection_id))
                                    if make_dir(film_raw_image_root_path):
                                        self.acquire_film_eapi_raw_images(zp_film_collection_id, zp_lang_id,
                                                                          eapi, zp_film_collection_eapi_eid,
                                                                          image_types,
                                                                          film_raw_image_root_path)
                                        if self.check_missing_eapi_raw_images(zp_film_collection_id, eapi, zp_lang_id) is True:
                                            self.set_retry(1, 12, zp_film_collection_id, self.eapi_dict[eapi], zp_lang_id)
                                            for image_type_key in self.image_types_keys:
                                                if image_type_key in image_types:
                                                    if self.check_film_for_image_type(zp_film_collection_id, eapi, None,
                                                                                      image_types[image_type_key][
                                                                                          'id']) is True:
                                                        del image_types[image_type_key]
                                            if image_types:
                                                self.acquire_film_eapi_raw_images(zp_film_collection_id, None,
                                                                              eapi, zp_film_collection_eapi_eid,
                                                                              image_types,
                                                                              film_raw_image_root_path)
                                    else:
                                        log.error('could not make dir %s', film_raw_image_root_path)
                        else:
                            film_processing_complete = True
                else:
                    log.warning('eapi %s does not have either get_backdrop_url or get_poster_url')

            if self.check_can_retry(1) is True:
                log.debug('Retrying Film Raw Images')
                for eapi in self.eapi_film_plugins_access_list:
                    if hasattr(getattr(self, eapi), 'get_film_collection_raw_images'):
                        film_processing_complete = False
                        zp_film_collection_id = max_film_id + 1
                        while film_processing_complete is False:
                            zp_film_collection_dict = self.get_film_missing_raw_eapi_image_retry(zp_film_collection_id, eapi, zp_lang_id)
                            if zp_film_collection_dict:
                                # we need the ids in deceding order but dict keys can be in any order
                                for zp_film_collection_dict_id in reversed(sorted(zp_film_collection_dict)):
                                    log.debug('retry processing zp_film_collection_id %s for eapi %s', zp_film_collection_id, eapi)
                                    zp_film_collection_id = zp_film_collection_dict_id
                                    if zp_film_collection_dict[zp_film_collection_id]['datetime'] + timedelta(
                                        days=zp_film_collection_dict[zp_film_collection_id]['delay']) <= datetime.now():
                                        log.debug('dt %s, plus %s is %s which is less than than now %s',
                                                  zp_film_collection_dict[zp_film_collection_id]['datetime'],
                                                  zp_film_collection_dict[zp_film_collection_id]['delay'],
                                                  zp_film_collection_dict[zp_film_collection_id]['datetime'] + timedelta(
                                                      days=zp_film_collection_dict[zp_film_collection_id]['delay']), datetime.now())
                                        zp_film_collection_eapi_eid = self.eapi_eid_from_zp_film_collection_id(self.eapi_dict[eapi], zp_film_collection_id)
                                        if zp_film_collection_eapi_eid is not None:
                                            image_types = copy.deepcopy(self.image_types_dict)
                                            for image_type_key in self.image_types_keys:
                                                if self.check_film_for_image_type(zp_film_collection_id, eapi, zp_lang_id,
                                                                             image_types[image_type_key]['id']) is True:
                                                    del image_types[image_type_key]
                                            film_raw_image_root_path = os.path.join(
                                                self.collection_root_path, str(zp_film_collection_id))
                                            if make_dir(film_raw_image_root_path):
                                                self.acquire_film_eapi_raw_images(zp_film_collection_id, zp_lang_id,
                                                                                  eapi, zp_film_collection_eapi_eid,
                                                                                  image_types,
                                                                                  film_raw_image_root_path)
                                                if self.check_missing_eapi_raw_images(zp_film_collection_id, eapi, zp_lang_id) is True:
                                                    self.set_retry(1, 12, zp_film_collection_id, self.eapi_dict[eapi], zp_lang_id)
                                                    for image_type_key in self.image_types_keys:
                                                        if image_type_key in image_types:
                                                            if self.check_film_for_image_type(zp_film_collection_id, eapi, None,
                                                                                              image_types[image_type_key][
                                                                                                  'id']) is True:
                                                                del image_types[image_type_key]
                                                    if image_types:
                                                        self.acquire_film_eapi_raw_images(zp_film_collection_id, None,
                                                                                      eapi, zp_film_collection_eapi_eid,
                                                                                      image_types,
                                                                                      film_raw_image_root_path)
                                            else:
                                                log.error('could not make dir %s', film_raw_image_root_path)
                                    else:
                                        log.debug('dt %s, plus %s is %s which is not less than now %s',
                                                  zp_film_collection_dict[zp_film_collection_id]['datetime'],
                                                  zp_film_collection_dict[zp_film_collection_id]['delay'],
                                                  zp_film_collection_dict[zp_film_collection_id]['datetime'] + timedelta(
                                                      days=zp_film_collection_dict[zp_film_collection_id]['delay']), datetime.now())

                            else:
                                film_processing_complete = True
                    else:
                        log.warning('eapi %s does not have either get_backdrop_url or get_poster_url')

    def acquire_film_eapi_raw_images(self, zp_film_collection_id, zp_lang_id, eapi, zp_film_collection_eapi_eid, image_types,
                                     film_raw_image_root_path):
        if hasattr(getattr(self, eapi), 'get_film_collection_raw_images'):
            if zp_lang_id is None:
                iso_639_part1 = None
            else:
                iso_639_part1 = self.iso_639_part1_from_zp_lang_id(zp_lang_id)
            log.debug('iso_639_part1 %s', iso_639_part1)
            if (iso_639_part1 is not None and zp_lang_id is not None) or \
                (iso_639_part1 is None and zp_lang_id is None):
                eapi_raw_iamges_dict = getattr(getattr(self, eapi), 'get_film_collection_raw_images')(
                    zp_film_collection_eapi_eid, iso_639_part1)
                if isinstance(eapi_raw_iamges_dict, dict):
                    for image_type in image_types:
                        if image_type in eapi_raw_iamges_dict:
                            if isinstance(eapi_raw_iamges_dict[image_type], dict):
                                if 'image_reference' in eapi_raw_iamges_dict[image_type] and \
                                    'image_url' in eapi_raw_iamges_dict[image_type]:
                                    image_reference = eapi_raw_iamges_dict[image_type]['image_reference']
                                    image_reference_extension = get_file_extension(image_reference)
                                    if image_reference_extension in self.allowed_extension_list:
                                        image_download_url = eapi_raw_iamges_dict[image_type]['image_url']
                                        if isinstance(image_reference, string_types) and isinstance(image_download_url, string_types):
                                            log.debug('image_reference %s, url %s', image_reference, image_download_url)
                                            image_uuid = uuid.uuid4()
                                            new_film_image_filename = '%s.%s' % (image_uuid, image_reference_extension)
                                            new_film_image_path = os.path.join(film_raw_image_root_path,
                                                                               new_film_image_filename)
                                            log.debug('new_film_image_path %s', new_film_image_path)
                                            #raise SystemExit
                                            if download(image_download_url, new_film_image_path) is True:
                                                self.set_acquired_eapi_image(image_types[image_type]['id'],
                                                                             eapi, zp_film_collection_id, zp_lang_id,
                                                                             image_reference, new_film_image_filename)
                                            else:
                                                log.error('uable to download %s to %s', image_download_url,
                                                          new_film_image_path)
                                        else:
                                            log.error('image_reference %s type: and or url %s type: not string_types',
                                                      image_reference, type(image_reference), image_download_url,
                                                        type(image_download_url))
                                    else:
                                        log.error('image_reference_extension %s for image_reference %s is not in'
                                                      ' list: %s',
                                                      image_reference_extension, image_reference,
                                                  self.allowed_extension_list)
                                else:
                                    log.error('image_reference and or image_url not'
                                              ' in eapi_raw_iamges_dict[image_type] %s',
                                              eapi_raw_iamges_dict[image_type])
                            else:
                                log.warning('image_type %s eapi_raw_iamges_dict[image_type] %s is not dict',
                                          image_type, type(eapi_raw_iamges_dict[image_type]))
                        else:
                            log.warning('image_type %s not in eapi_raw_iamges_dict %s', image_type,
                                          eapi_raw_iamges_dict)
        else:
            log.warning('eapi %s, does not have function get_film_collection_raw_images', eapi)

    def set_acquired_eapi_image(self, image_type_id, eapi, zp_film_collection_id, zp_lang_id, image_reference,
                                new_film_image_filename):
        session = self.Session()
        try:
            zp_film_collection_raw_image = session.query(TABLES.ZP_FILM_COLLECTION_RAW_IMAGE).filter(
                TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_TYPE_ID == image_type_id,
                TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_ENTITY_ID == zp_film_collection_id,
                TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_EAPI_ID == self.eapi_dict[eapi],
                TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ZP_LANG_ID == zp_lang_id
            ).one()
        except orm.exc.NoResultFound:
            add_zp_film_collection_raw_image = TABLES.ZP_FILM_COLLECTION_RAW_IMAGE(ZP_ENTITY_TYPE_ID = image_type_id,
                                                            ZP_ENTITY_ID = zp_film_collection_id,
                                                            ZP_EAPI_ID = self.eapi_dict[eapi],
                                                            ZP_LANG_ID = zp_lang_id,
                                                            ZP_EAPI_IMAGE_REF = image_reference,
                                                            FILENAME = new_film_image_filename)
            session.add(add_zp_film_collection_raw_image)
            if commit(session):
                update_film_last_mod(self.Session, zp_film_collection_id)
        else:
            log.error('there is allready an extry for ZP_FILM_COLLECTION_RAW_IMAGE with ZP_ENTITY_TYPE_ID %s'
                      ' ZP_ENTITY_ID %s, ZP_EAPI_ID %s, ZP_LANG_ID %s of ID %s', image_type_id, zp_film_collection_id,
            self.eapi_dict[eapi], zp_lang_id, zp_film_collection_raw_image.ID)
        session.close()



