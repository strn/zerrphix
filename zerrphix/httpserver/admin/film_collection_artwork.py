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
from zerrphix.specials import film_collection_specials
from zerrphix.util.filesystem import make_dir
from zerrphix.util.image import save_image
from zerrphix.util.plugin import create_eapi_dict
from zerrphix.util.text import date_time
from PIL import Image, ImageDraw, ImageFont
from zerrphix.util.image import resize_and_crop

log = logging.getLogger(__name__)

_types_dict = {'graphic': 1, 'text': 2}

class Artwork(ArtworkBase):

    def __init__(self, **kwargs):
        super(Artwork, self).__init__(**kwargs)
        """Artwork __init__

            Args:
                | args (list): Passed through args from the command line.
                | Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.
                | config (:obj:): The config loaded (ConfigParser). See zerrphix.config.
                | config_root_dir (str): The directory from which the config file was loaded.

        """
        self.specials = film_collection_specials.Specials(self.Session, 'film_collection')
        self.specials.eapi_dict = self.eapi_dict = create_eapi_dict(self.Session)
        self.specials.eapi_plugins_access_list = self.eapi_plugins_access_list
        self.special_type_dict_by_special, self.special_type_dict_by_id = self.specials.make_special_type_dict()
        # self.image_type_dict = {'synopsis': 1, 'icon': 2}

    def render(self, ZP_ENTITY_ID, ZP_USER_ID, image_type, zp_icon_sub_type_id):
        #kwargs={'ZP_ENTITY_ID': 95, 'ZP_USER_ID': 3, 'image_type': 'synopsis'}
        kwargs = {'ZP_ENTITY_ID': ZP_ENTITY_ID,
                  'ZP_USER_ID': ZP_USER_ID,
                  'image_type': image_type,
                  'ZP_IMAGE_SUB_TYPE': zp_icon_sub_type_id
                  }
        #kwargs['zp_template_id'] = self.get_user_template(kwargs['ZP_USER_ID'])
        ##kwargs['template_folder'] = zerrphix.template.__path__[0]
        #kwargs['template_name'], kwargs['template_version'], kwargs['template_dict'], \
        #kwargs['icon_sub_type_require_list'], kwargs['template_folder'] = self.template_prep(kwargs['zp_template_id'], image_type)
        #kwargs = {}
        kwargs['zp_image_type_id'] = self.all_image_types_dict[image_type]
        kwargs['zp_template_id'], kwargs['template_name'] = \
            self.get_user_template_info(kwargs['ZP_USER_ID'])
        template_xml_path = self.get_template_path(kwargs['zp_template_id'])
        templates_dict = self.get_templates_dict(kwargs['zp_template_id'], template_xml_path)
        evaluated_templates = self.get_evaluate_temapltes_dict(templates_dict)
        kwargs['template_folder'] = os.path.abspath(os.path.dirname(template_xml_path))
        user_library_langs = self.get_user_library_langs(1,
                                                         kwargs['ZP_USER_ID'])
        user_library_eapi_order = self.user_library_eapi_order(1,
                                                               kwargs['ZP_USER_ID'])
        kwargs['ZP_EAPI_ID_REQ'] = user_library_eapi_order[0]
        kwargs['ZP_LANG_ID_REQ'] = user_library_langs[0]
        kwargs['template_dict'] = {'template':
                                       evaluated_templates['library']['film_collection'][image_type]}

        log.debug('kwargs %s', kwargs)
        specials_dict, img = self.process_template(**kwargs)
        return img

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
            zp_film_raw_image_xref = session.query(TABLES.ZP_FILM_COLLECTION_RAW_IMAGE).filter(
                TABLES.ZP_FILM_COLLECTION_RAW_IMAGE.ID ==
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_ID,
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_USER_ID == kwargs['ZP_USER_ID'],
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ID == kwargs['ZP_ENTITY_ID'],
                TABLES.ZP_USER_FILM_COLLECTION_ENTITY_XREF.ZP_FILM_COLLECTION_ENTITY_TYPE_ID ==
                speical_image_type_entity_type_dict[speical_image_type]
            ).one()
        except orm.exc.NoResultFound:
            log.warning('could not find a entry in ZP_FILM_COLLECTION_RAW_IMAGE where ZP_USER_ID %s,'
                        ' ZP_FILM_COLLECTION_ID %s, ZP_FILM_COLLECTION_ENTITY_TYPE_ID %s (speical_image_type %s)',
                        kwargs['ZP_USER_ID'], kwargs['ZP_ENTITY_ID'], speical_image_type_entity_type_dict[
                    speical_image_type], speical_image_type)
        else:
            log.debug('Found a entry in ZP_USER_FILM_COLLECTION_ENTITY_XREF where ZP_USER_ID %s,'
                        ' ZP_FILM_COLLECTION_ID %s, ZP_FILM_COLLECTION_ENTITY_TYPE_ID %s (speical_image_type %s) with id %s',
                        kwargs['ZP_USER_ID'], kwargs['ZP_ENTITY_ID'], speical_image_type_entity_type_dict[
                    speical_image_type], speical_image_type, zp_film_raw_image_xref.ID)
            log.debug('self.library_config_dict %s', self.library_config_dict)
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