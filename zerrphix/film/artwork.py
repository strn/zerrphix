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
from zerrphix.specials import film_specials
from zerrphix.util.filesystem import make_dir
from zerrphix.util.image import save_image
from zerrphix.util.plugin import create_eapi_dict
from zerrphix.util.text import date_time
from PIL import Image, ImageDraw, ImageFont
from zerrphix.util.image import resize_and_crop

log = logging.getLogger(__name__)

_types_dict = {'graphic': 1, 'text': 2}

class Artwork(ArtworkBase):
    """The Film Artwork Class which renders iamges for use on the Dune UI
    """

    def __init__(self, **kwargs):
        super(Artwork, self).__init__(**kwargs)
        """Artwork __init__

            Args:
                | args (list): Passed through args from the command line.
                | Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.
                | config (:obj:): The config loaded (ConfigParser). See zerrphix.config.
                | config_root_dir (str): The directory from which the config file was loaded.

        """
        self.smbcon = None
        self.specials = film_specials.Specials(self.Session, self.library_config_dict['name'])
        self.specials.eapi_dict = self.eapi_dict = create_eapi_dict(self.Session)
        self.specials.eapi_plugins_access_list = self.eapi_plugins_access_list
        self.special_type_dict_by_special, self.special_type_dict_by_id = self.specials.make_special_type_dict()
        self.image_type_dict = {'synopsis': 1, 'icon': 2}
        self.user_dict = self.construct_user_dict()

        """
        # TODO: convert below to make cast order by count in db
        SELECT ZP_PEOPLE.*, (SELECT COUNT(*) FROM ZP_FILM_ROLE_XREF WHERE ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID = ZP_PEOPLE.ID) AS TOT
        FROM ZP_PEOPLE
        where ID in (SELECT ZP_PEOPLE_ID FROM ZP_FILM_ROLE_XREF WHERE ZP_FILM_ID = 1)
        ORDER BY TOT DESC
        """

    # TODO: psutil.disk_usage('/')
    # usage(total=21378641920, used=4809781248, free=15482871808, percent=22.5)
    # http://pythonhosted.org/psutil/

    # count_poeple_occourance = session.query(func.count(TABLES.ZP_FILM_ROLE_XREF)).filter(TABLES.ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID == TABLES.ZP_PEOPLE.ID).subquery()
    # count_poeple_occourance = session.query(func.count('*')).filter(
    #							TABLES.ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID == TABLES.ZP_PEOPLE.ID).subquery()
    # directors = session.query(
    #					TABLES.ZP_PEOPLE.NAME, count_poeple_occourance).filter(
    #						TABLES.ZP_PEOPLE.ID.in_(
    #							session.query(
    #								TABLES.ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID).filter(
    #									TABLES.ZP_FILM_ROLE_XREF.ZP_ROLE_ID == 1,
    #									TABLES.ZP_FILM_ROLE_XREF.ZP_FILM_ID == 1))).all()
    # print(directors.__dict__)
    # raise SystemExit



    def render(self):
        """Kick of the process of rendering Images

            Note:
                For each film->dune->user

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
        # print(ZP_FILM_ID)
        # raise SystemExit
        # ZP_FILM_ID = 0
        session = self.Session()
        max_film_id = session.query(func.max(TABLES.ZP_FILM.ID)).one()[0]
        session.close()
        # print(max_film_id)
        if isinstance(max_film_id, int):
            self.process_dunes()
        # session.close()
        # raise SystemExit
        # raise SystemExit
        else:
            log.warning('There do not seem to be any films in TABLES.ZP_FILM')

    def get_entity_processing_dict(self, **kwargs):
        session = self.Session()
        # session.refresh(TABLES.ZP_FILM)
        # session.expire_on_commit = False
        # http://techspot.zzzeek.org/category/sqlalchemy/5/
        return_list = []
        qry_films_with_eid = session.query(
            TABLES.ZP_FILM).filter(
            # Need to fudge this a bit now we are iterating over images above
            TABLES.ZP_FILM.ID < kwargs['ZP_FILM_ID'],
            # make this optional ???
            TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_FILM_EAPI_EID.ZP_FILM_ID)),
            TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID)),
            ~TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID).filter(
                    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == kwargs['ZP_USER_ID'],
                    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID ==
                    TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID,
                    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID == kwargs[
                        'zp_image_type_id'],
                    TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID ==
                    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID,
                    ##

                    # TABLES.ZP_FILM_IMAGE_RENDER_HASH.TEMPLATE_NAME == kwargs['template_name'],
                    # TABLES.ZP_FILM_IMAGE_RENDER_HASH.TEMPLATE_VERSION == kwargs['template_version'],
                    TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == kwargs['zp_template_id'],
                    TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID,
                    TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.RENDER_DATETIME >=
                    TABLES.ZP_TEMPLATE.LAST_MOD_DATETIME,

                    ##
                    TABLES.ZP_FILM.ID == TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID,
                    TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.RENDER_DATETIME >=
                    TABLES.ZP_FILM.LAST_EDIT_DATETIME,
                    TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID ==
                    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID,
                    TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID ==
                    TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID,
                    TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID'],
                    TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE == kwargs['ZP_IMAGE_SUB_TYPE']))
        )
        qry_films_with_eid_count = qry_films_with_eid.count()
        # print('qry_films_with_eid_count', qry_films_with_eid_count)
        log.debug('qry_films_with_eid_count: {0}. ZP_DUNE_ID: {1}, ZP_USER_ID:{2}'.format(
            qry_films_with_eid_count,
            kwargs['ZP_DUNE_ID'],
            kwargs['ZP_USER_ID']))
        if qry_films_with_eid_count > 0:
            films = qry_films_with_eid.order_by(TABLES.ZP_FILM.ID.desc()).limit(100)
            # session.expunge(films)
            # session.flush()
            session.close()
            for film in films:
                return_list.append(film.ID)
        # print(episode_processing_dict)
        return return_list

    def porcess_entity(self, **kwargs):
        """Process films

            Note:
                For the current ZP_DUNE_ID, ZP_USER_ID, film films
                that need processing

            Args:
                | ZP_DUNE_ID (int): the dune id
                | ZP_USER_ID (int): The user id
                | ZP_FILM_ID (int): The film id
                | ZP_LANG_ID (int): The language id
                | ZP_EAPI_ID_REQ (int): The requested EAPI id
                | ZP_LANG_ID_REQ (int): The requested LANG id
                | image_type (string): icon/synopsis
                | image_extension (string): 
                | template_dict (string): 
                | template_name (string): 
                | template_version (string):
                | dune_render_store_dict (dict): {'render_root_film_dir': '/path/to/render_root_film_dir',
                |									'type': 'local'}

            Attributes:
                | films_processed (bool): Used to end while loop when \
                all films have been processed

        """
        #kwargs['ZP_FILM_IMAGE_TYPE_ID'] = self.image_type_dict[kwargs['image_type']]
        session = self.Session()
        max_film_id = session.query(func.max(TABLES.ZP_FILM.ID)).one()[0]
        session.close()
        if isinstance(max_film_id, int):
            for ZP_IMAGE_SUB_TYPE in kwargs['icon_sub_type_require_list']:
                kwargs['ZP_IMAGE_SUB_TYPE'] = ZP_IMAGE_SUB_TYPE
                log.debug('ZP_IMAGE_SUB_TYPE %s ZP_USER_ID %s image_type %s', kwargs['ZP_IMAGE_SUB_TYPE'],
                          kwargs['ZP_USER_ID'], kwargs['image_type'])
                ZP_FILM_ID = max_film_id + 1
                kwargs['ZP_FILM_ID'] = ZP_FILM_ID
                entities_processed = False
                while entities_processed is False:
                    log.debug('ZP_FILM_ID %s, ZP_USER_ID %s, ZP_FILM_IMAGE_TYPE_ID %s, template_name %s,'
                              'template_version %s, ZP_DUNE_ID %s, ZP_IMAGE_SUB_TYPE %s',
                              kwargs['ZP_FILM_ID'], kwargs['ZP_USER_ID'], kwargs['zp_image_type_id'],
                              kwargs['template_name'],
                              kwargs['template_version'], kwargs['ZP_DUNE_ID'], kwargs['ZP_IMAGE_SUB_TYPE'])
                    entity_processing_list = self.get_entity_processing_dict(**kwargs)
                    log.debug('entity_processing_list %s', entity_processing_list)
                    if entity_processing_list:
                        for ID in entity_processing_list:
                            log.debug('dune_id %s, filmid %s, userid %s image_type %s, ZP_IMAGE_SUB_TYPE %s',
                                      kwargs['ZP_DUNE_ID'],
                                      kwargs['ZP_FILM_ID'],
                                      kwargs['ZP_USER_ID'],
                                      kwargs['image_type'],
                                      ZP_IMAGE_SUB_TYPE)
                            kwargs['ZP_FILM_ID'] = ID
                            kwargs['ZP_ENTITY_ID'] = ID
                            self.set_current_library_process_desc_detail(
                                self.library_config_dict['id'],
                                7,
                                'User %s, Film %s/%s, Image_type %s, sub_type %s, Dune %s' % (
                                    self.user_dict[kwargs['ZP_USER_ID']],
                                    kwargs['ZP_ENTITY_ID'],
                                    max_film_id,
                                    kwargs['image_type'],
                                    ZP_IMAGE_SUB_TYPE,
                                    self.dune_name_by_id_dict[kwargs['ZP_DUNE_ID']]
                                )
                            )
                            render_image = True
                            image_ident = self.specials.construct_image_ident(**kwargs)
                            #log.error('pre_image_ident_pre_render %s filmid %s userid %s', image_ident,
                            #          kwargs['ZP_FILM_ID'],
                            #          kwargs['ZP_USER_ID'])
                            if image_ident is not None:
                                # raise SystemExit
                                # TODO: In docs make sure to have the dune root dir a folder within a dune share
                                # to avoid the images being renedred locally if the becomes unmounted

                                image_ident = '{0}T{1}'.format(kwargs['zp_image_type_id'], image_ident)
                                log.debug('image_ident_pre_render %s filmid %s userid %s'
                                          ' image_type %s', image_ident,
                                          kwargs['ZP_FILM_ID'],
                                          kwargs['ZP_USER_ID'],
                                          kwargs['image_type'])
                                kwargs['image_ident_md5'] = md5(image_ident).hexdigest()
                                log.debug('image_ident_pre_render md5 %s', md5(image_ident).hexdigest())
                                kwargs['ZP_FILM_IMAGE_RENDER_HASH_ID'] = self.get_image_hash(**kwargs)
                                if kwargs['ZP_FILM_IMAGE_RENDER_HASH_ID'] is not None:
                                    # log.warning('found ZP_FILM_EPISODE_IMAGE_RENDER_HASH_ID %s for ZP_DUNE_ID %s, ZP_FILM_ID %s, SEASON %s, FIRST_EPISODE %s, ZP_FILM_IMAGE_TYPE_ID %s, ZP_IMAGE_SUB_TYPE %s,'
                                    #			'image_ident_md5 %s, template_name %s, template_version %s',
                                    #			ZP_FILM_EPISODE_IMAGE_RENDER_HASH_ID, ZP_DUNE_ID, ZP_FILM_ID, SEASON, FIRST_EPISODE, ZP_FILM_IMAGE_TYPE_ID, ZP_IMAGE_SUB_TYPE,
                                    #			image_ident_md5, template_name, template_version)
                                    self.set_user_image_hash(**kwargs)
                                    # log.warning('set user xref ZP_FILM_EPISODE_IMAGE_RENDER_HASH_ID %s for ZP_FILM_ID %s, SEASON %s, FIRST_EPISODE %s, ZP_FILM_IMAGE_TYPE_ID %s, ZP_IMAGE_SUB_TYPE %s,'
                                    #		'image_ident_md5 %s, template_name %s, template_version %s',
                                    #		ZP_FILM_EPISODE_IMAGE_RENDER_HASH_ID, ZP_FILM_ID, SEASON, FIRST_EPISODE, ZP_FILM_IMAGE_TYPE_ID, ZP_IMAGE_SUB_TYPE,
                                    #		image_ident_md5, template_name, template_version)
                                    render_image = False
                                    # raise SystemExit
                            else:
                                log.error('image_ident is none for filmid %s userid %s',
                                          kwargs['ZP_FILM_ID'],
                                          kwargs['ZP_USER_ID']
                                          )
                            if render_image:
                                if 'ZP_FILM_IMAGE_RENDER_HASH_ID' in kwargs:
                                    del kwargs['ZP_FILM_IMAGE_RENDER_HASH_ID']
                                self.render_image(**kwargs)
                    else:
                        session.close()
                        entities_processed = True
                        # raise SystemExit

    def render_image(self, **kwargs):
        log.debug('rendering ZP_DUNE_ID %s, ZP_USER_ID %s, ZP_FILM_ID %s, image_type %s, ZP_IMAGE_SUB_TYPE %s',
                  kwargs['ZP_DUNE_ID'], kwargs['ZP_USER_ID'], kwargs['ZP_FILM_ID'], kwargs['image_type'],
                  kwargs['ZP_IMAGE_SUB_TYPE'])
        image_save_folder_exists = False
        image_template_folder = os.path.join(kwargs['dune_render_store_dict']['render_root_library_dir'],
                                         kwargs['template_name'])
        image_save_folder = os.path.join(image_template_folder, str(kwargs['ZP_FILM_ID']))
        log.debug('Tying to make folder %s', image_save_folder)
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
                                                     '.{0}{1}.'.format(kwargs['image_type'],
                                                                       self.image_sub_type_dict_by_id[
                                                                           kwargs['ZP_IMAGE_SUB_TYPE']]))
            log.debug('image_save_path: {0}'.format(kwargs['image_save_path']))
            # raise SystemExit
            image_ident = '{0}T'.format(kwargs['zp_image_type_id'])

            #kwargs['template_folder'] = zerrphix.template.__path__[0]

            specials_dict, img = self.process_template(**kwargs)
            log.debug('specials_dict %s', specials_dict)
            for ZP_FILM_SPECIAL_TYPE_ID in sorted(specials_dict):
                # if ZP_FILM_SPECIAL_TYPE_ID in [2]:
                # TODO: Not using lang here as should be same title accross all langs? change to use lang
                # image_ident += '{0}'.format(specials_dict[ZP_FILM_SPECIAL_TYPE_ID]['ZP_FILM_TITLE_ID'])
                # print(specials_dict)
                log.debug(specials_dict)
                if ZP_FILM_SPECIAL_TYPE_ID in [4]:
                    # TODO: Not using lang here as user defined title by user prefs class
                    image_ident += '{0}'.format(specials_dict[ZP_FILM_SPECIAL_TYPE_ID]['title'])
                    log.debug('special %s, %s', ZP_FILM_SPECIAL_TYPE_ID,
                              specials_dict[ZP_FILM_SPECIAL_TYPE_ID]['title'])
                elif ZP_FILM_SPECIAL_TYPE_ID in [10]:
                    # TODO: Not using lang here as user defined title by user prefs class
                    image_ident += '{0}'.format(specials_dict[ZP_FILM_SPECIAL_TYPE_ID]['overview'])
                    log.debug('special %s, %s', ZP_FILM_SPECIAL_TYPE_ID,
                              specials_dict[ZP_FILM_SPECIAL_TYPE_ID]['overview'])
                elif ZP_FILM_SPECIAL_TYPE_ID in [1,2]:
                    image_ident += '{0}'.format(specials_dict[ZP_FILM_SPECIAL_TYPE_ID]['ZP_RAW_IMAGE_ID'])
                    log.debug('special %s, %s', ZP_FILM_SPECIAL_TYPE_ID,
                              specials_dict[ZP_FILM_SPECIAL_TYPE_ID]['ZP_RAW_IMAGE_ID'])
                elif self.special_type_dict_by_id[ZP_FILM_SPECIAL_TYPE_ID]['USES_LANG'] == 1:
                    # print(ZP_FILM_SPECIAL_TYPE_ID, specials_dict[ZP_FILM_SPECIAL_TYPE_ID])
                    image_ident += '{0}{1}{2}'.format(ZP_FILM_SPECIAL_TYPE_ID,
                                                      specials_dict[ZP_FILM_SPECIAL_TYPE_ID][
                                                          'ZP_EAPI_ID_ACT'],
                                                      specials_dict[ZP_FILM_SPECIAL_TYPE_ID][
                                                          'ZP_LANG_ID_ACT'])
                    log.debug('special %s, %s', ZP_FILM_SPECIAL_TYPE_ID,
                              '{0}{1}{2}'.format(ZP_FILM_SPECIAL_TYPE_ID,
                                                 specials_dict[ZP_FILM_SPECIAL_TYPE_ID][
                                                     'ZP_EAPI_ID_ACT'],
                                                 specials_dict[ZP_FILM_SPECIAL_TYPE_ID][
                                                     'ZP_LANG_ID_ACT']))
                    self.specials.eapi_special_update_db(kwargs['ZP_FILM_ID'],
                                                         ZP_FILM_SPECIAL_TYPE_ID,
                                                         specials_dict[ZP_FILM_SPECIAL_TYPE_ID][
                                                             'ZP_LANG_ID_REQ'],
                                                         specials_dict[ZP_FILM_SPECIAL_TYPE_ID][
                                                             'ZP_LANG_ID_ACT'],
                                                         specials_dict[ZP_FILM_SPECIAL_TYPE_ID][
                                                             'ZP_EAPI_ID_REQ'],
                                                         specials_dict[ZP_FILM_SPECIAL_TYPE_ID][
                                                             'ZP_EAPI_ID_ACT'],
                                                         kwargs['zp_image_type_id'])
                else:
                    image_ident += '{0}{1}'.format(ZP_FILM_SPECIAL_TYPE_ID,
                                                   specials_dict[ZP_FILM_SPECIAL_TYPE_ID][
                                                       'ZP_EAPI_ID_ACT'])
                    log.debug('special %s, %s', ZP_FILM_SPECIAL_TYPE_ID,
                              '{0}{1}'.format(ZP_FILM_SPECIAL_TYPE_ID,
                                              specials_dict[ZP_FILM_SPECIAL_TYPE_ID][
                                                  'ZP_EAPI_ID_ACT']))
                    self.specials.eapi_special_update_db(kwargs['ZP_FILM_ID'],
                                                         ZP_FILM_SPECIAL_TYPE_ID,
                                                         0,
                                                         0,
                                                         specials_dict[ZP_FILM_SPECIAL_TYPE_ID][
                                                             'ZP_EAPI_ID_REQ'],
                                                         specials_dict[ZP_FILM_SPECIAL_TYPE_ID][
                                                             'ZP_EAPI_ID_ACT'],
                                                         kwargs['zp_image_type_id'])

            log.debug('image_ident_render %s filmid %s userid %s'
                      ' image_type %s', image_ident,
                      kwargs['ZP_FILM_ID'],
                      kwargs['ZP_USER_ID'],
                      kwargs['image_type'])
            image_ident_md5 = md5(image_ident).hexdigest()
            log.debug('image_ident_render md5 %s', image_ident_md5)
            kwargs['image_ident_md5'] = image_ident_md5
            kwargs['image_save_path'] += '{0}.{1}'.format(image_ident_md5, kwargs['image_extension'])
            log.debug(
                'rendering image for ZP_FILM_ID: {0}, ZP_DUNE_ID: {1}, ZP_USER_ID: {2}, ZP_IMAGE_SUB_TYPE: {3},'
                ' self.image_type_dict[image_type]: {4}, image_ident_md5: {5},'
                ' template_name: {6}, template_version: {7}'.format(kwargs['ZP_FILM_ID'],
                                                                    kwargs['ZP_DUNE_ID'], kwargs['ZP_USER_ID'],
                                                                    kwargs['ZP_IMAGE_SUB_TYPE'],
                                                                    kwargs['zp_image_type_id'],
                                                                    kwargs['image_ident_md5'],
                                                                    kwargs['template_name'],
                                                                    kwargs['template_version']))
            if save_image(img, kwargs['image_extension'], smbcon=self.smbcon, **kwargs):
                #raise Exception
                # print(image_save_path)
                self.set_image_hash(**kwargs)

                # log.warning('set or updated image hash for ZP_FILM_ID %s, SEASON %s, FIRST_EPISODE %s, ZP_FILM_IMAGE_TYPE_ID %s, ZP_IMAGE_SUB_TYPE %s,'
                #		'image_ident_md5 %s, template_name %s, template_version %s',
                #		ZP_FILM_ID, SEASON, FIRST_EPISODE, ZP_FILM_IMAGE_TYPE_ID, ZP_IMAGE_SUB_TYPE,
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
            ZP_FILM_IMAGE_RENDER_HASH = session.query(TABLES.ZP_FILM_IMAGE_RENDER_HASH).filter(
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID == kwargs['ZP_FILM_ID'],
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE == kwargs['ZP_IMAGE_SUB_TYPE'],
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID == kwargs['zp_image_type_id'],
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.HASH == kwargs['image_ident_md5'],
                ##

                # TABLES.ZP_FILM_IMAGE_RENDER_HASH.TEMPLATE_NAME == kwargs['template_name'],
                # TABLES.ZP_FILM_IMAGE_RENDER_HASH.TEMPLATE_VERSION == kwargs['template_version'],
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == kwargs['zp_template_id'],
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID,
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.RENDER_DATETIME >=
                TABLES.ZP_TEMPLATE.LAST_MOD_DATETIME,

                ##
                TABLES.ZP_FILM.ID == TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID,
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID'],
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID == \
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID,
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.RENDER_DATETIME >= \
                TABLES.ZP_FILM.LAST_EDIT_DATETIME
            ).one()
        except orm.exc.NoResultFound:
            ZP_FILM_IMAGE_RENDER_HASH_ID = None
        else:
            ZP_FILM_IMAGE_RENDER_HASH_ID = ZP_FILM_IMAGE_RENDER_HASH.ID
        session.close()
        return ZP_FILM_IMAGE_RENDER_HASH_ID

    def set_dune_image_hash(self, **kwargs):
        session = self.Session()
        try:
            ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF = session.query(
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF
            ).filter(
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == kwargs['ZP_DUNE_ID'],
                TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID ==
                kwargs['ZP_FILM_IMAGE_RENDER_HASH_ID']
            ).one()
        except orm.exc.NoResultFound:
            log.debug(('Adding ZP_DUNE_ID = {0},'
                       ' ZP_FILM_IMAGE_RENDER_HASH_ID = {1} to'
                       ' ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF').format(kwargs['ZP_DUNE_ID'],
                                                                      kwargs['ZP_FILM_IMAGE_RENDER_HASH_ID']))
            add_ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF = TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF(
                ZP_DUNE_ID=kwargs['ZP_DUNE_ID'],
                ZP_FILM_IMAGE_RENDER_HASH_ID=kwargs['ZP_FILM_IMAGE_RENDER_HASH_ID'],
                RENDER_DATETIME=date_time(),
                EXT=kwargs['image_extension']
            )
            session.add(add_ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF)
            commit(session)
        else:
            ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.RENDER_DATETIME = date_time()
            ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.EXT = kwargs['image_extension']
            commit(session)
        session.close()

    def set_user_image_hash(self, **kwargs):
        """Set the hash used for the user in the filename in the db

            Args:
                | ZP_USER_ID (int): the user id
                | ZP_FILM_ID (int): the tv id
                | ZP_FILM_IMAGE_TYPE_ID (int): tv image type (icon/synopsis) id
                | image_ident_md5 (string): md5 hash used in the filename of the image
                | template_name (string): template name
                | template_version (string): template version

            Raises:
                Exception: if cannot find the hash in ZP_FILM_IMAGE_RENDER_HASH as it should be in there

        """
        session = self.Session()
        try:
            ZP_USER_FILM_IMAGE_RENDER_HASH_XREF = session.query(
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF).filter(
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID == kwargs['ZP_FILM_ID'],
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == kwargs['ZP_USER_ID'],
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID == kwargs['zp_image_type_id'],
                TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_IMAGE_SUB_TYPE == kwargs['ZP_IMAGE_SUB_TYPE']
            ).one()
        except orm.exc.NoResultFound as e:
            log.debug(('Adding ZP_FILM_ID = {0}').format(kwargs['ZP_FILM_ID']))
            add_ZP_USER_FILM_IMAGE_RENDER_HASH_XREF = TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF(
                ZP_FILM_ID=kwargs['ZP_FILM_ID'],
                ZP_USER_ID=kwargs['ZP_USER_ID'],
                ZP_FILM_IMAGE_TYPE_ID=kwargs['zp_image_type_id'],
                ZP_IMAGE_SUB_TYPE=kwargs['ZP_IMAGE_SUB_TYPE'],
                ZP_FILM_IMAGE_RENDER_HASH_ID=kwargs['ZP_FILM_IMAGE_RENDER_HASH_ID'])
            session.add(add_ZP_USER_FILM_IMAGE_RENDER_HASH_XREF)
            commit(session)
        else:
            if ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID != kwargs[
                'ZP_FILM_IMAGE_RENDER_HASH_ID']:
                ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID = kwargs[
                    'ZP_FILM_IMAGE_RENDER_HASH_ID']
                commit(session)
        session.close()

    def set_image_hash(self, **kwargs):
        """Set the hash used in the filename in the db

            Note:
                Set the hash used in the filename in the db to be used by the web
                interface to generate a link to	the image so that the dune can find it

            Args:
                | ZP_FILM_ID (int): the tv id
                | ZP_FILM_IMAGE_TYPE_ID (int): tv image type (icon/synopsis) id
                | image_ident_md5 (string): md5 hash used in the filename of the image
                | template_name (string): template name
                | template_version (string): template version

        """
        session = self.Session()
        try:
            ZP_FILM_IMAGE_RENDER_HASH = session.query(TABLES.ZP_FILM_IMAGE_RENDER_HASH).filter(
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID == kwargs['ZP_FILM_ID'],
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE == kwargs['ZP_IMAGE_SUB_TYPE'],
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID == kwargs['zp_image_type_id'],
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.HASH == kwargs['image_ident_md5'],
                # TABLES.ZP_FILM_IMAGE_RENDER_HASH.TEMPLATE_NAME == kwargs['template_name'],
                # TABLES.ZP_FILM_IMAGE_RENDER_HASH.TEMPLATE_VERSION == kwargs['template_version']
                TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == kwargs['zp_template_id']
            ).one()
        except orm.exc.NoResultFound as e:
            log.debug(('Adding ZP_FILM_ID = {0},'
                       ' image_ident_md5 = {1}').format(kwargs['ZP_FILM_ID'],
                                                        kwargs['image_ident_md5']))
            add_ZP_FILM_IMAGE_RENDER_HASH = TABLES.ZP_FILM_IMAGE_RENDER_HASH(
                ZP_FILM_ID=kwargs['ZP_FILM_ID'],
                ZP_IMAGE_SUB_TYPE=kwargs['ZP_IMAGE_SUB_TYPE'],
                ZP_FILM_IMAGE_TYPE_ID=kwargs['zp_image_type_id'],
                HASH=kwargs['image_ident_md5'],
                #TEMPLATE_NAME=kwargs['template_name'],
                #TEMPLATE_VERSION=kwargs['template_version'],
                ZP_TEMPLATE_ID=kwargs['zp_template_id'],
                #EXT=kwargs['image_extension']
            )
            session.add(add_ZP_FILM_IMAGE_RENDER_HASH)
            commit(session)
            kwargs['ZP_FILM_IMAGE_RENDER_HASH_ID'] = add_ZP_FILM_IMAGE_RENDER_HASH.ID
        else:
            kwargs['ZP_FILM_IMAGE_RENDER_HASH_ID'] = ZP_FILM_IMAGE_RENDER_HASH.ID
            #ZP_FILM_IMAGE_RENDER_HASH.EXT = kwargs['image_extension']
            commit(session)
            log.debug(('ZP_FILM_ID: {0},'
                       ' image_ident_md5: {1} allready in ZP_FILM_IMAGE_RENDER_HASH'.format(kwargs['ZP_FILM_ID'],
                                                                                            kwargs['image_ident_md5'])))
        session.close()

        self.set_user_image_hash(**kwargs)
        self.set_dune_image_hash(**kwargs)

    def get_eapi_eid_dict(self, **kwargs):
        """Get resized image from eapi as a pillow image object

            Note:
                | Downloads the image from the eapi (if ones exists), keeps the image if \
                self.keep_downloads = 1.
                | If an image can be downloaded or found locally resize it and return it.

            Args:
                | image_type (string): the film id
                | ZP_USER_ID (int): the user id
                | ZP_EAPI_ID (int): the eapi id

            Returns:
                | obj: <class 'PIL.Image.Image'> or None if image cannot be made
                | int: ZP_EAPI_ID_ACT or None if image cannot be made

        """
        eapi_eid_dict = {}
        session = self.Session()
        for eapi in self.eapi_plugins_access_list:
            eapi_eid_dict[self.eapi_dict[eapi]] = None
            try:
                zp_eapi_eid = session.query(
                    TABLES.ZP_FILM_EAPI_EID).filter(
                    TABLES.ZP_FILM_EAPI_EID.ZP_FILM_ID == kwargs['ZP_FILM_ID'],
                    TABLES.ZP_FILM_EAPI_EID.ZP_EAPI_ID == self.eapi_dict[eapi]).one().ZP_EAPI_EID
            except orm.exc.NoResultFound as e:
                log.warning('No resluts for ZP_FILM_ID: {0} in ZP_FILM_EAPI_EID'.format(
                    kwargs['ZP_FILM_ID']))
            else:
                eapi_eid_dict[self.eapi_dict[eapi]] = zp_eapi_eid
        return eapi_eid_dict

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
        speical_image_type_entity_type_dict = {'poster': 3, 'backdrop': 4}
        try:
            zp_film_raw_image_xref = session.query(TABLES.ZP_FILM_RAW_IMAGE).filter(
                TABLES.ZP_FILM_RAW_IMAGE.ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == kwargs['ZP_USER_ID'],
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == kwargs['ZP_ENTITY_ID'],
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == speical_image_type_entity_type_dict[
                    speical_image_type]
            ).one()
        except orm.exc.NoResultFound:
            log.warning('could not find a entry in ZP_FILM_RAW_IMAGE where ZP_USER_ID %s,'
                        ' ZP_FILM_ID %s, ZP_FILM_ENTITY_TYPE_ID %s (speical_image_type %s)',
                        kwargs['ZP_USER_ID'], kwargs['ZP_ENTITY_ID'], speical_image_type_entity_type_dict[
                    speical_image_type], speical_image_type)
        else:
            log.debug('Found a entry in ZP_USER_FILM_ENTITY_XREF where ZP_USER_ID %s,'
                        ' ZP_FILM_ID %s, ZP_FILM_ENTITY_TYPE_ID %s (speical_image_type %s) with id %s',
                        kwargs['ZP_USER_ID'], kwargs['ZP_ENTITY_ID'], speical_image_type_entity_type_dict[
                    speical_image_type], speical_image_type, zp_film_raw_image_xref.ID)
            image_path = os.path.join(self.library_config_dict['downloaded_images_library_root_path'],
                                      str(kwargs['ZP_ENTITY_ID']), zp_film_raw_image_xref.FILENAME)
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
            else:
                log.error('image_path %s does not exist', image_path)
        return return_image, zp_film_raw_image_id