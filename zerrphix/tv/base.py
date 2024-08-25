from __future__ import unicode_literals, division, absolute_import, print_function
from zerrphix.base import Base
from zerrphix.db.tables import TABLES
from zerrphix.db import commit
from zerrphix.util.text import date_time
import logging

log = logging.getLogger(__name__)

class TVBase(Base):
    def __init__(self, **kwargs):
        super(TVBase, self).__init__(**kwargs)

    def set_show_filefolder_enabled_state(self, zp_tv_filefolder_id, state):
        session = self.Session()
        session.query(TABLES.ZP_TV_FILEFOLDER).filter(
            TABLES.ZP_TV_FILEFOLDER.ID == zp_tv_filefolder_id).update(
            {"ENABLED": state,
             "ENABLED_UPDATE_DATETIME": date_time()}
        )
        commit(session)
        session.close()