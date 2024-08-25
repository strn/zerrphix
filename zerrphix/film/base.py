from __future__ import unicode_literals, division, absolute_import, print_function
from zerrphix.base import Base
import logging
from zerrphix.db.tables import TABLES
from zerrphix.db import commit
from zerrphix.util.text import date_time

log = logging.getLogger(__name__)

class FilmBase(Base):
    def __init__(self, **kwargs):
        super(FilmBase, self).__init__(**kwargs)

    def set_filefolder_enabled_state(self, zp_film_filefolder_id, state):
        session = self.Session()
        session.query(TABLES.ZP_FILM_FILEFOLDER).filter(
            TABLES.ZP_FILM_FILEFOLDER.ID == zp_film_filefolder_id).update(
            {"ENABLED": state,
             "ENABLED_UPDATE_DATETIME": date_time()}
        )
        commit(session)
        session.close()