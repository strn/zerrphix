# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

from zerrphix.db.tables import TABLES
from sqlalchemy import func
#from zerrphix.util import smbfs_connection_dict_dune
from zerrphix.util.filesystem import smbfs
import logging
import os
from zerrphix.base import Base

log = logging.getLogger(__name__)

class DBCommon(Base):
    def __init__(self, **kwargs):
        super(DBCommon, self).__init__(**kwargs)

