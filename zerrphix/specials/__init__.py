# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function
from zerrphix.constants import diskfilefolder_types_dict, container_type_dict
import logging

log = logging.getLogger(__name__)

class Specials(object):
    """The Film Specials Base Class which renders iamges for use on the Dune UI
    """

    def __init__(self, Session, library):
        """Artwork __init__

            Args:
                | args (list): Passed through args from the command line.
                | Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.
                | config (:obj:): The config loaded (ConfigParser). See zerrphix.config.
                | config_root_dir (str): The directory from which the config file was loaded.

        """
        self.Session = Session
        self.library = library
        if hasattr(self, 'make_special_type_dict'):
            self.special_type_dict_by_special, self.special_type_dict_by_id = self.make_special_type_dict()

    def get_diskfilefolder_name(self, diskfilefolder_type_id):
        for diskfilefolder_type in diskfilefolder_types_dict:
            if diskfilefolder_type_id == diskfilefolder_types_dict[diskfilefolder_type]:
                return diskfilefolder_type
        return 'unkown'

    def get_container_group_name(self, extension):
        for container_type in container_type_dict:
            if extension in container_type_dict[container_type]:
                log.trace('extension %s, container_type %s, container_type_dict[container_type] %s',
                          extension,
                          container_type,
                          container_type_dict[container_type])
                return container_type
        return 'unkown'
