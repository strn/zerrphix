# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import os

#from zerrphix.util import smbfs_connection_dict_dune
#from zerrphix.util.db import DBCommon
from zerrphix.util.filesystem import make_dir
from zerrphix.util.filesystem import smbfs
from zerrphix.util.plugin import create_eapi_dict

log = logging.getLogger(__name__)


#def create_eapi_library_keep_images_folders(self):
#    if os.path.isdir(self.global_config_dict['downloaded_images_root_path']):
#        self.global_config_dict['downloaded_images_library_root_path'] = \
#            os.path.join(self.global_config_dict['downloaded_images_root_path'],
#                         self.library_config_dict['name'])
#        make_dir(self.global_config_dict['downloaded_images_library_root_path'])


