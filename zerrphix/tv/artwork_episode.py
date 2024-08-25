# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import os
from hashlib import md5

from sqlalchemy import func, orm

# from zerrphix.util.eapi import get_eapi_image
import zerrphix.template
from zerrphix.artwork import ArtworkBase
from zerrphix.db import commit
from zerrphix.db.tables import TABLES
from zerrphix.specials import tv_episode_specials
from zerrphix.util.filesystem import make_dir
from zerrphix.util.image import save_image
from zerrphix.util.plugin import create_eapi_dict
from zerrphix.util.text import date_time
from PIL import Image, ImageDraw, ImageFont
from zerrphix.util.image import resize_and_crop

log = logging.getLogger(__name__)

_types_dict = {'graphic': 1, 'text': 2}


class ArtworkEpisode(ArtworkBase):
    """The TV Artwork Class which renders iamges for use on the Dune UI
    """

    def __init__(self, **kwargs):
        super(ArtworkEpisode, self).__init__(**kwargs)
        """Artwork __init__

            Args:
                | args (list): Passed through args from the command line.
                | Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.
                | config (:obj:): The config loaded (ConfigParser). See zerrphix.config.
                | config_root_dir (str): The directory from which the config file was loaded.

        """
        self.smbcon = None
        self.specials = tv_episode_specials.Specials(self.Session, self.library_config_dict['name'])
        self.specials.eapi_dict = self.eapi_dict = create_eapi_dict(self.Session)
        self.specials.eapi_plugins_access_list = self.eapi_plugins_access_list
        self.special_type_dict_by_special, self.special_type_dict_by_id = self.specials.make_special_type_dict()
        self.image_type_dict = {'episode_icon': 3}
        self.user_dict = self.construct_user_dict()
        """
        # TODO: convert below to make cast order by count in db
        SELECT ZP_PEOPLE.*, (SELECT COUNT(*) FROM ZP_TV_ROLE_XREF WHERE ZP_TV_ROLE_XREF.ZP_PEOPLE_ID = ZP_PEOPLE.ID) AS TOT
        FROM ZP_PEOPLE
        where ID in (SELECT ZP_PEOPLE_ID FROM ZP_TV_ROLE_XREF WHERE ZP_TV_ID = 1)
        ORDER BY TOT DESC
        """

    def render(self):
        """Kick of the process of rendering Images

            Note:
                For each tv->dune->user

            Raises:
                Exception: if cannot os.makedirs(image_save_folder)
        """
        # templates = ['synopsis']
        # templates = ['icon']
        # This is to stop sqlalchemy.orm.exc.DetachedInstanceError this should not happen
        # though as sperate sessions should be being made by the functions as it is
        # scoped_session(sessionmaker(bind=engine)). Some people on stack exchnage do see
        # this. It was also suggested not to have concrrent sessions.
        # i am not sure how else to overcome this using _yield_limit.
        # session.expire_on_commit = False
        # print(ZP_TV_ID)
        # raise SystemExit
        # ZP_TV_ID = 0
        session = self.Session()
        max_tv_id = session.query(func.max(TABLES.ZP_TV.ID)).one()[0]
        session.close()
        # print(max_tv_id)
        if isinstance(max_tv_id, int):
            self.process_dunes()
        # session.close()
        # raise SystemExit
        # raise SystemExit
        else:
            log.warning('There do not seem to be any tvs in TABLES.ZP_TV')

    def get_entity_processing_dict(self, **kwargs):
        session = self.Session()
        # session.refresh(TABLES.ZP_TV)
        # session.expire_on_commit = False
        # http://techspot.zzzeek.org/category/sqlalchemy/5/
        return_dict = {}
        qry_tvs_with_eid = session.query(
            TABLES.ZP_TV_EPISODE_FILEFOLDER.ID,
            TABLES.ZP_TV_EPISODE_FILEFOLDER.FIRST_EPISODE,
            TABLES.ZP_TV_EPISODE_FILEFOLDER.LAST_EPISODE,
            TABLES.ZP_TV_EPISODE_FILEFOLDER.SEASON,
            TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID).filter(
            # Need to fudge this a bit now we are iterating over images above
            TABLES.ZP_TV_EPISODE_FILEFOLDER.ID < kwargs['ZP_TV_EPISODE_ID'],
            # TABLES.ZP_TV_EPISODE.ID == 9594,
            TABLES.ZP_TV_FILEFOLDER.ID == TABLES.ZP_TV_EPISODE_FILEFOLDER.ZP_TV_FILEFOLDER_ID,
            TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID.in_(
                session.query(
                    TABLES.ZP_TV_EAPI_EID.ZP_TV_ID)),
            TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID.in_(
                session.query(
                    TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID)),
            ~TABLES.ZP_TV_EPISODE_FILEFOLDER.ID.in_(
                # make this distinct ?? (multuiple files with same show/ep/season)
                session.query(TABLES.ZP_TV_EPISODE_FILEFOLDER.ID).filter(
                    TABLES.ZP_TV_FILEFOLDER.ID == TABLES.ZP_TV_EPISODE_FILEFOLDER.ZP_TV_FILEFOLDER_ID,
                    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.FIRST_EPISODE == \
                    TABLES.ZP_TV_EPISODE_FILEFOLDER.FIRST_EPISODE,
                    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.SEASON == TABLES.ZP_TV_EPISODE_FILEFOLDER.SEASON,
                    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID,
                    TABLES.ZP_TV_EPISODE.ZP_TV_ID == TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TV_ID,
                    TABLES.ZP_TV_EPISODE.SEASON == TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.SEASON,
                    TABLES.ZP_TV_EPISODE.EPISODE == TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.FIRST_EPISODE,
                    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.FIRST_EPISODE == \
                    TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.FIRST_EPISODE,
                    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.SEASON == \
                    TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.SEASON,
                    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == \
                    TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TV_ID,
                    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == kwargs['ZP_USER_ID'],
                    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID == kwargs[
                        'zp_image_type_id'],
                    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID == \
                    TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ID,
                    ##

                    # TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.TEMPLATE_NAME == kwargs['template_name'],
                    # TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.TEMPLATE_VERSION == kwargs['template_version'],
                    TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == kwargs['zp_template_id'],
                    TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID,
                    TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.RENDER_DATETIME >=
                    TABLES.ZP_TEMPLATE.LAST_MOD_DATETIME,

                    ##
                    TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == \
                    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID,
                    TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID'],
                    TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID == \
                    TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ID,
                    TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.RENDER_DATETIME >= \
                    TABLES.ZP_TV_EPISODE.LAST_EDIT_DATETIME,
                    TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE == kwargs['ZP_IMAGE_SUB_TYPE'])
            )
        )
        qry_tvs_with_eid_count = qry_tvs_with_eid.count()
        # print('qry_tvs_with_eid_count', qry_tvs_with_eid_count)
        log.debug(
            'qry_tvs_with_eid_count: {0}. ZP_DUNE_ID: {1}, ZP_USER_ID: {2}, ZP_IMAGE_SUB_TYPE: {3}'.format(
                qry_tvs_with_eid_count,
                kwargs['ZP_DUNE_ID'],
                kwargs['ZP_USER_ID'],
                kwargs['ZP_IMAGE_SUB_TYPE']))
        # raise SystemExit
        if qry_tvs_with_eid_count > 0:
            tv_eps = qry_tvs_with_eid.order_by(TABLES.ZP_TV_EPISODE_FILEFOLDER.ID.desc()).limit(250)
            # session.expunge(tvs)
            # session.flush()
            session.close()
            for tv_ep in tv_eps:
                return_dict[tv_ep.ID] = {'ZP_TV_ID': tv_ep.ZP_TV_ID,
                                         'FIRST_EPISODE': tv_ep.FIRST_EPISODE,
                                         'LAST_EPISODE': tv_ep.LAST_EPISODE,
                                         'SEASON': tv_ep.SEASON}
                # print(episode_processing_dict)
        return return_dict

    def porcess_entity(self, **kwargs):
        """Process tvs

            Note:
                For the current ZP_DUNE_ID, ZP_USER_ID, tv tvs
                that need processing

            Args:
                | ZP_DUNE_ID (int): the dune id
                | ZP_USER_ID (int): The user id
                | ZP_TV_ID (int): The tv id
                | ZP_LANG_ID (int): The language id
                | ZP_EAPI_ID_REQ (int): The requested EAPI id
                | ZP_LANG_ID_REQ (int): The requested LANG id
                | image_type (string): icon/synopsis
                | image_extension (string): 
                | template_dict (string): 
                | template_name (string): 
                | template_version (string):
                | dune_render_store_dict (dict): {'render_root_library_dir': '/path/to/render_root_library_dir',
                |									'type': 'local'}

            Attributes:
                | tv_eps_processed (bool): Used to end while loop when \
                all tvs have been processed

        """
        #kwargs['ZP_TV_IMAGE_TYPE_ID'] = self.image_type_dict[kwargs['image_type']]
        if kwargs['image_type'] in ['episode_icon', 'episode_synopsis', 'episode_screenshot']:
            session = self.Session()
            max_tv_ep_id = session.query(func.max(TABLES.ZP_TV_EPISODE_FILEFOLDER.ID)).one()[0]
            session.close()
            if isinstance(max_tv_ep_id, int):
                for ZP_IMAGE_SUB_TYPE in kwargs['icon_sub_type_require_list']:
                    kwargs['ZP_IMAGE_SUB_TYPE'] = ZP_IMAGE_SUB_TYPE
                    ZP_TV_EPISODE_ID = max_tv_ep_id + 1
                    kwargs['ZP_TV_EPISODE_ID'] = ZP_TV_EPISODE_ID
                    entities_processed = False
                    while entities_processed is False:
                        entity_processing_dict = self.get_entity_processing_dict(**kwargs)
                        if entity_processing_dict:
                            for ID in entity_processing_dict:
                                # print(ID)
                                kwargs['ZP_TV_EPISODE_ID'] = ID
                                kwargs['ZP_TV_ID'] = entity_processing_dict[ID]['ZP_TV_ID']
                                kwargs['SEASON'] = entity_processing_dict[ID]['SEASON']
                                kwargs['FIRST_EPISODE'] = entity_processing_dict[ID]['FIRST_EPISODE']
                                kwargs['LAST_EPISODE'] = entity_processing_dict[ID]['LAST_EPISODE']
                                kwargs['ZP_ENTITY_ID'] = ID
                                # TODO: Use user specifced ZP_EAPI_ID_REQ
                                self.set_current_library_process_desc_detail(
                                    self.library_config_dict['id'],
                                    17,
                                    'User %s, Episode %s/%s, Image_type %s, sub_type %s, Dune %s' % (
                                        self.user_dict[kwargs['ZP_USER_ID']],
                                        kwargs['ZP_ENTITY_ID'],
                                        max_tv_ep_id,
                                        kwargs['image_type'],
                                        ZP_IMAGE_SUB_TYPE,
                                        self.dune_name_by_id_dict[kwargs['ZP_DUNE_ID']]
                                    )
                                )
                                render_image = True
                                image_ident = self.specials.construct_image_ident(**kwargs)
                                if image_ident is not None:

                                    # raise SystemExit
                                    # TODO: In docs make sure to have the dune root dir a folder within a dune share
                                    # to avoid the images being renedred locally if the becomes unmounted

                                    image_ident = '{0}T{1}'.format(kwargs['zp_image_type_id'], image_ident)
                                    kwargs['image_ident_md5'] = md5(image_ident).hexdigest()
                                    kwargs['ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID'] = self.get_image_hash(**kwargs)
                                    if kwargs['ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID'] is not None:
                                        # log.warning('found ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID %s for ZP_DUNE_ID %s, ZP_TV_ID %s, SEASON %s, FIRST_EPISODE %s, ZP_TV_IMAGE_TYPE_ID %s, ZP_IMAGE_SUB_TYPE %s,'
                                        #			'image_ident_md5 %s, template_name %s, template_version %s',
                                        #			ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID, ZP_DUNE_ID, ZP_TV_ID, SEASON, FIRST_EPISODE, ZP_TV_IMAGE_TYPE_ID, ZP_IMAGE_SUB_TYPE,
                                        #			image_ident_md5, template_name, template_version)
                                        self.set_user_image_hash(**kwargs)
                                        # log.warning('set user xref ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID %s for ZP_TV_ID %s, SEASON %s, FIRST_EPISODE %s, ZP_TV_IMAGE_TYPE_ID %s, ZP_IMAGE_SUB_TYPE %s,'
                                        #		'image_ident_md5 %s, template_name %s, template_version %s',
                                        #		ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID, ZP_TV_ID, SEASON, FIRST_EPISODE, ZP_TV_IMAGE_TYPE_ID, ZP_IMAGE_SUB_TYPE,
                                        #		image_ident_md5, template_name, template_version)
                                        render_image = False
                                        # raise SystemExit
                                if render_image:
                                    # raise SystemExit
                                    if 'ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID' in kwargs:
                                        del kwargs['ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID']
                                    self.render_image(**kwargs)
                        else:
                            session.close()
                            entities_processed = True
                            # raise SystemExit

    def render_image(self, **kwargs):
        image_save_folder_exists = False
        image_template_folder = os.path.join(kwargs['dune_render_store_dict']['render_root_library_dir'],
                                         kwargs['template_name'])
        image_save_folder = os.path.join(kwargs['dune_render_store_dict']['render_root_library_dir'],
                                         kwargs['template_name'], str(kwargs['ZP_TV_ID']))
        if kwargs['dune_render_store_dict']['type'] == 'local':
            if make_dir(image_template_folder):
                if make_dir(image_save_folder):
                    image_save_folder_exists = True
        elif kwargs['dune_render_store_dict']['type'] == 'smb':
            # smbcon = smbfs(dune_render_store_dict['connection_dict'])
            if self.smbcon.mkdir(image_template_folder):
                if self.smbcon.mkdir(image_save_folder):
                    image_save_folder_exists = True
                    log.debug('SMB: made folder %s', image_save_folder)
                else:
                    log.debug('SMB: failed to make folder %s', image_save_folder)
        else:
            log.warning('''dune_render_store_dict['type']: {0} not valid'''.format(
                kwargs['dune_render_store_dict']['type']))
        if image_save_folder_exists:
            kwargs['image_save_path'] = os.path.join(image_save_folder,
                                                     '.{0}{1}.{2}_{3}.'.format(kwargs['image_type'],
                                                                               self.image_sub_type_dict_by_id[
                                                                                   kwargs['ZP_IMAGE_SUB_TYPE']],
                                                                               str(kwargs['SEASON']).zfill(4),
                                                                               str(kwargs['FIRST_EPISODE']).zfill(
                                                                                   4)))
            log.debug('image_save_path: {0}'.format(kwargs['image_save_path']))
            # raise SystemExit
            image_ident = '{0}T'.format(kwargs['zp_image_type_id'])
            # print(ZP_TV_ID, ZP_TV_EPISODE_ID, SEASON, EPISODE, ZP_IMAGE_SUB_TYPE)
            # raise SystemExit
            # kwargs = {'ZP_USER_ID': ZP_USER_ID,
            #          'ZP_LANG_ID_REQ': ZP_LANG_ID_REQ,
            #          'ZP_EAPI_ID_REQ': ZP_EAPI_ID_REQ,
            #          'ZP_TV_ID': ZP_TV_ID,
            #          'ZP_IMAGE_SUB_TYPE': ZP_IMAGE_SUB_TYPE,
            #          'FIRST_EPISODE': FIRST_EPISODE,
            #          'LAST_EPISODE': LAST_EPISODE,
            #          'SEASON': SEASON}

            #kwargs['template_folder'] = zerrphix.template.__path__[0]
            specials_dict, img = self.process_template(**kwargs)
            log.debug('specials_dict %s', specials_dict)
            #raise SystemExit
            for ZP_TV_SPECIAL_TYPE_ID in sorted(specials_dict):
                # if ZP_TV_SPECIAL_TYPE_ID in [2]:
                # TODO: Not using lang here as should be same title accross all langs? change to use lang
                # image_ident += '{0}'.format(specials_dict[ZP_TV_SPECIAL_TYPE_ID]['ZP_TV_TITLE_ID'])
                if ZP_TV_SPECIAL_TYPE_ID in [2]:
                    # TODO: Not using lang here as user defined title by user prefs class
                    image_ident += '{0}'.format(specials_dict[ZP_TV_SPECIAL_TYPE_ID]['title'])
                elif ZP_TV_SPECIAL_TYPE_ID in [6]:
                    # TODO: Not using lang here as user defined title by user prefs class
                    image_ident += '{0}'.format(specials_dict[ZP_TV_SPECIAL_TYPE_ID]['overview'])
                    log.debug('special %s, %s', ZP_TV_SPECIAL_TYPE_ID,
                              specials_dict[ZP_TV_SPECIAL_TYPE_ID]['overview'])
                elif ZP_TV_SPECIAL_TYPE_ID in [1,8,9]:
                    image_ident += '{0}'.format(specials_dict[ZP_TV_SPECIAL_TYPE_ID]['ZP_RAW_IMAGE_ID'])
                    log.debug('special %s, %s', ZP_TV_SPECIAL_TYPE_ID,
                              specials_dict[ZP_TV_SPECIAL_TYPE_ID]['ZP_RAW_IMAGE_ID'])
                elif self.special_type_dict_by_id[ZP_TV_SPECIAL_TYPE_ID]['USES_LANG'] == 1:
                    image_ident += '{0}{1}{2}'.format(ZP_TV_SPECIAL_TYPE_ID,
                                                      specials_dict[ZP_TV_SPECIAL_TYPE_ID][
                                                          'ZP_EAPI_ID_ACT'],
                                                      specials_dict[ZP_TV_SPECIAL_TYPE_ID][
                                                          'ZP_LANG_ID_ACT'])
                    self.specials.eapi_special_update_db(kwargs['ZP_TV_ID'],
                                                         kwargs['SEASON'],
                                                         kwargs['FIRST_EPISODE'],
                                                         ZP_TV_SPECIAL_TYPE_ID,
                                                         specials_dict[ZP_TV_SPECIAL_TYPE_ID][
                                                             'ZP_LANG_ID_REQ'],
                                                         specials_dict[ZP_TV_SPECIAL_TYPE_ID][
                                                             'ZP_LANG_ID_ACT'],
                                                         specials_dict[ZP_TV_SPECIAL_TYPE_ID][
                                                             'ZP_EAPI_ID_REQ'],
                                                         specials_dict[ZP_TV_SPECIAL_TYPE_ID][
                                                             'ZP_EAPI_ID_ACT'],
                                                         kwargs['zp_image_type_id'])
                else:
                    image_ident += '{0}{1}'.format(ZP_TV_SPECIAL_TYPE_ID,
                                                   specials_dict[ZP_TV_SPECIAL_TYPE_ID][
                                                       'ZP_EAPI_ID_ACT'])
                    self.specials.eapi_special_update_db(kwargs['ZP_TV_ID'],
                                                         kwargs['SEASON'],
                                                         kwargs['FIRST_EPISODE'],
                                                         ZP_TV_SPECIAL_TYPE_ID,
                                                         0,
                                                         0,
                                                         specials_dict[ZP_TV_SPECIAL_TYPE_ID][
                                                             'ZP_EAPI_ID_REQ'],
                                                         specials_dict[ZP_TV_SPECIAL_TYPE_ID][
                                                             'ZP_EAPI_ID_ACT'],
                                                         kwargs['zp_image_type_id'])
            image_ident_md5 = md5(image_ident).hexdigest()
            kwargs['image_ident_md5'] = image_ident_md5
            kwargs['image_save_path'] += '{0}.{1}'.format(image_ident_md5, kwargs['image_extension'])
            log.debug(
                'rendering image for ZP_TV_EPISODE_ID: {0}, ZP_DUNE_ID: {1}, ZP_USER_ID: {2}, ZP_IMAGE_SUB_TYPE: {3},'
                ' self.image_type_dict[image_type]: {4}, image_ident_md5: {5},'
                ' template_name: {6}, template_version: {7}'.format(kwargs['ZP_TV_EPISODE_ID'],
                                                                    kwargs['ZP_DUNE_ID'], kwargs['ZP_USER_ID'],
                                                                    kwargs['ZP_IMAGE_SUB_TYPE'],
                                                                    kwargs['zp_image_type_id'],
                                                                    kwargs['image_ident_md5'],
                                                                    kwargs['template_name'],
                                                                    kwargs['template_version']))
            if save_image(img, kwargs['image_extension'], smbcon=self.smbcon, **kwargs):
                #if kwargs['ZP_USER_ID'] != 1:
                    #log.error('user id not 1')
                    #raise SystemExit
                # raise SystemExit
                # print(image_save_path)
                self.set_image_hash(**kwargs)

                # log.warning('set or updated image hash for ZP_TV_ID %s, SEASON %s, FIRST_EPISODE %s, ZP_TV_IMAGE_TYPE_ID %s, ZP_IMAGE_SUB_TYPE %s,'
                #		'image_ident_md5 %s, template_name %s, template_version %s',
                #		ZP_TV_ID, SEASON, FIRST_EPISODE, ZP_TV_IMAGE_TYPE_ID, ZP_IMAGE_SUB_TYPE,
                #		image_ident_md5, template_name, template_version)
                # raise SystemExit
                # print('rendered image')
                # raise SystemExit
                # raise SystemExit
        else:
            log.critical(
                'image_save_folder: {0} does not exist cannot render images there.'.format(
                    image_save_folder))

    def get_image_hash(self, **kwargs):
        session = self.Session()
        try:
            ZP_TV_EPISODE_IMAGE_RENDER_HASH = session.query(TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH).filter(
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TV_ID == kwargs['ZP_TV_ID'],
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.SEASON == kwargs['SEASON'],
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.FIRST_EPISODE == kwargs['FIRST_EPISODE'],
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE == kwargs['ZP_IMAGE_SUB_TYPE'],
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == kwargs['zp_image_type_id'],
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.HASH == kwargs['image_ident_md5'],
                ##

                # TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.TEMPLATE_NAME == kwargs['template_name'],
                # TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.TEMPLATE_VERSION == kwargs['template_version'],
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == kwargs['zp_template_id'],
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID,
                TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.RENDER_DATETIME >=
                TABLES.ZP_TEMPLATE.LAST_MOD_DATETIME,

                ##
                TABLES.ZP_TV_EPISODE.ZP_TV_ID == TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TV_ID,
                TABLES.ZP_TV_EPISODE.SEASON == TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.SEASON,
                TABLES.ZP_TV_EPISODE.EPISODE == TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.FIRST_EPISODE,
                TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID'],
                TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID == \
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ID,
                TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.RENDER_DATETIME >= \
                TABLES.ZP_TV_EPISODE.LAST_EDIT_DATETIME
            ).one()
        except orm.exc.NoResultFound:
            ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID = None
        else:
            ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID = ZP_TV_EPISODE_IMAGE_RENDER_HASH.ID
        session.close()
        return ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID

    def set_dune_image_hash(self, **kwargs):
        session = self.Session()
        try:
            ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF = session.query(
                TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF
            ).filter(
                TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID'],
                TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID == kwargs[
                    'ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID']
            ).one()
        except orm.exc.NoResultFound:
            log.debug(('Adding ZP_DUNE_ID = {0},'
                       ' ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID = {1} to'
                       ' ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF').format(kwargs['ZP_DUNE_ID'],
                                                                            kwargs[
                                                                                'ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID']))
            add_ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF = TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF(
                ZP_DUNE_ID=kwargs['ZP_DUNE_ID'],
                ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID=kwargs['ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID'],
                RENDER_DATETIME=date_time(),
                EXT=kwargs['image_extension']
            )
            session.add(add_ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF)
            commit(session)
        else:
            ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.RENDER_DATETIME = date_time()
            ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.EXT = kwargs['image_extension']
            commit(session)
        session.close()

    def set_user_image_hash(self, **kwargs):
        session = self.Session()
        try:
            # need to put ZP_TV_IMAGE_TYPE_ID and ZP_IMAGE_SUB_TYPE in user hash xref
            ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF = session.query(
                TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF
            ).filter(
                TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == kwargs['ZP_USER_ID'],
                TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == kwargs['ZP_TV_ID'],
                TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.SEASON == kwargs['SEASON'],
                TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.FIRST_EPISODE == kwargs['FIRST_EPISODE'],
                TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID == kwargs['zp_image_type_id'],
                TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_IMAGE_SUB_TYPE == kwargs['ZP_IMAGE_SUB_TYPE']
            ).one()
        except orm.exc.NoResultFound:
            log.debug(('Adding ZP_TV_ID = {0}').format(kwargs['ZP_TV_ID']))
            add_ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF = TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF(
                ZP_USER_ID=kwargs['ZP_USER_ID'],
                ZP_TV_ID=kwargs['ZP_TV_ID'],
                SEASON=kwargs['SEASON'],
                FIRST_EPISODE=kwargs['FIRST_EPISODE'],
                ZP_TV_IMAGE_TYPE_ID=kwargs['zp_image_type_id'],
                ZP_IMAGE_SUB_TYPE=kwargs['ZP_IMAGE_SUB_TYPE'],
                ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID=kwargs['ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID'])
            session.add(add_ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF)
            commit(session)
        else:
            if ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID != \
                kwargs['ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID']:
                ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID = \
                    kwargs['ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID']
                commit(session)
        session.close()

    def set_image_hash(self, **kwargs):
        """Set the hash used in the filename in the db

            Note:
                Set the hash used in the filename in the db to be used by the web
                interface to generate a link to	the image so that the dune can find it

            Args:
                | ZP_TV_ID (int): the tv id
                | ZP_TV_IMAGE_TYPE_ID (int): tv image type (icon/synopsis) id
                | image_ident_md5 (string): md5 hash used in the filename of the image
                | template_name (string): template name
                | template_version (string): template version

        """
        session = self.Session()
        try:
            ZP_TV_EPISODE_IMAGE_RENDER_HASH = session.query(TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH).filter(
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TV_ID == kwargs['ZP_TV_ID'],
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.SEASON == kwargs['SEASON'],
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.FIRST_EPISODE == kwargs['FIRST_EPISODE'],
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE == kwargs['ZP_IMAGE_SUB_TYPE'],
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == kwargs['zp_image_type_id'],
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.HASH == kwargs['image_ident_md5'],
                # TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.TEMPLATE_NAME == kwargs['template_name'],
                # TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.TEMPLATE_VERSION == kwargs['template_version']
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == kwargs['zp_template_id']
            ).one()
        except orm.exc.NoResultFound as e:
            log.debug(('Adding ZP_TV_ID = {0},'
                       ' image_ident_md5 = {1}').format(kwargs['ZP_TV_ID'],
                                                        kwargs['image_ident_md5']))
            add_ZP_TV_EPISODE_IMAGE_RENDER_HASH = TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH(
                ZP_TV_ID=kwargs['ZP_TV_ID'],
                SEASON=kwargs['SEASON'],
                FIRST_EPISODE=kwargs['FIRST_EPISODE'],
                ZP_IMAGE_SUB_TYPE=kwargs['ZP_IMAGE_SUB_TYPE'],
                ZP_TV_IMAGE_TYPE_ID=kwargs['zp_image_type_id'],
                HASH=kwargs['image_ident_md5'],
                #TEMPLATE_NAME=kwargs['template_name'],
                #TEMPLATE_VERSION=kwargs['template_version']
                ZP_TEMPLATE_ID=kwargs['zp_template_id'],
                # EXT=kwargs['image_extension']
            )
            session.add(add_ZP_TV_EPISODE_IMAGE_RENDER_HASH)
            commit(session)
            kwargs['ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID'] = add_ZP_TV_EPISODE_IMAGE_RENDER_HASH.ID
        else:
            kwargs['ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID'] = ZP_TV_EPISODE_IMAGE_RENDER_HASH.ID
            # ZP_TV_EPISODE_IMAGE_RENDER_HASH.EXT = kwargs['image_extension']
            commit(session)

            log.debug(('ZP_TV_ID: {0},'
                       ' image_ident_md5: {1} allready in ZP_TV_IMAGE_RENDER_HASH'.format(kwargs['ZP_TV_ID'],
                                                                                          kwargs['image_ident_md5'])))
        session.close()

        self.set_user_image_hash(**kwargs)
        self.set_dune_image_hash(**kwargs)

    def get_resized_raw_image(self, speical_image_type, width, height, **kwargs):
        # print(locals())
        """Get resized image from eapi as a pillow image object

            Note:
                | Downloads the image from the eapi (if ones exists), keeps the image if \
                self.global_config_dict['keep_downloaded_images'] = 1.
                | If an image can be downloaded or found locally resize it and return it.

            Args:
                | image_type (string): the film id
                | ZP_USER_ID (int): the user id
                | ZP_EAPI_ID (int): the eapi id

            Returns:
                | obj: <class 'PIL.Image.Image'> or None if image cannot be made
                | int: ZP_EAPI_ID_ACT or None if image cannot be made

        """
        session = self.Session()
        return_image = None
        zp_film_raw_image_id = 0
        # todo get this from db/global dict
        speical_image_type_entity_type_dict = {'screenshot': 3}
        try:
            zp_film_raw_image_xref = session.query(
                TABLES.ZP_TV_EPISODE_RAW_IMAGE
            ).filter(
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ID == TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_ID,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_USER_ID == kwargs['ZP_USER_ID'],
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID == kwargs['ZP_ENTITY_ID'],
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON == kwargs['SEASON'],
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE == kwargs['FIRST_EPISODE'],
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == speical_image_type_entity_type_dict[
                    speical_image_type]
            ).one()
        except orm.exc.NoResultFound:
            log.warning('could not find a entry in ZP_TV_RAW_IMAGE where ZP_USER_ID %s,'
                        ' ZP_TV_ID %s, ZP_TV_ENTITY_TYPE_ID %s (speical_image_type %s)',
                        kwargs['ZP_USER_ID'], kwargs['ZP_ENTITY_ID'], speical_image_type_entity_type_dict[
                    speical_image_type], speical_image_type)
        else:
            log.debug('Found a entry in ZP_USER_TV_EPISODE_ENTITY_XREF where ZP_USER_ID %s,'
                        ' ZP_TV_ID %s, ZP_TV_ENTITY_TYPE_ID %s (speical_image_type %s) with id %s',
                        kwargs['ZP_USER_ID'], kwargs['ZP_ENTITY_ID'], speical_image_type_entity_type_dict[
                    speical_image_type], speical_image_type, zp_film_raw_image_xref.ID)
            image_path = os.path.join(self.library_config_dict['downloaded_images_library_root_path'],
                                      str(kwargs['ZP_ENTITY_ID']), str(kwargs['SEASON']),
                                      zp_film_raw_image_xref.FILENAME)
            log.debug(image_path)
            if os.path.isfile(image_path):
                return_image = Image.open(image_path)
                try:
                    return_image.load()
                except IOError as e:
                    log.error('image %s seems to be corrrupt cannot use',
                              image_path)
                    return_image = None
                else:
                    return_image.close()
                    # todo allow the image to be resized if aspectratio does not change beyond threshold
                    return_image = resize_and_crop(image_path, (width, height), crop_type='middle',
                                                   asptect_ratio_change_threshold=9)
                    zp_film_raw_image_id = zp_film_raw_image_xref.ID
            elif os.path.exists(image_path):
                log.error('image_path %s exists but not a file', image_path)
                #raise SystemExit
            else:
                log.error('image_path %s does not exist', image_path)
                #raise SystemExit
        return return_image, zp_film_raw_image_id
