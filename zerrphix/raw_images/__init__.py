# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import os
import re
import sys
from types import MethodType

from PIL import Image, ImageDraw, ImageFont

import zerrphix.template
from zerrphix.plugin import load_plugins
from zerrphix.template import tempalte_icon_sub_type_list_convert
#from zerrphix.util.db import DBCommon
from zerrphix.util.filesystem import make_dir, get_file_extension, check_for_exisiting_default_image
from zerrphix.util.image import text_box, text_line, download_and_resize_image
#from zerrphix.util.image_store import create_dune_render_store_dict
from zerrphix.util.plugin import create_eapi_plugins_list
from zerrphix.util.text import xml_to_dict
from zerrphix.base import Base
from zerrphix.util.filesystem import smbfs
from zerrphix.db.tables import TABLES
from zerrphix.util.image import resize_and_crop
from six import string_types
from sqlalchemy import orm
from zerrphix.util.filesystem import make_dir

log = logging.getLogger(__name__)

class RawImagesBase(Base):
    def __init__(self, **kwargs):
        super(RawImagesBase, self).__init__(**kwargs)
        try:
            self.create_root_raw_images_download_folder()
        except (IOError) as e:
            self.add_excpetion_raised_to_db(1, e)
            raise

    def create_root_raw_images_download_folder(self):
        if make_dir(self.global_config_dict['downloaded_images_root_path']):
            log.debug('make dir %s or was allready existing.',
                      self.global_config_dict['downloaded_images_root_path'])
        else:
            log.error('Cannot make downloaded_images_root_path %s' %
                          self.global_config_dict['downloaded_images_root_path'])
            raise IOError('Cannot make downloaded_images_root_path %s' %
                          self.global_config_dict['downloaded_images_root_path'])