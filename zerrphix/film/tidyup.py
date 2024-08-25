# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging

from zerrphix.db import commit
from zerrphix.db.tables import TABLES
from zerrphix.film.base import FilmBase

log = logging.getLogger(__name__)


class Tidyup(FilmBase):
    """
    Scans for films that are not yet in the db
    """

    def __init__(self, **kwargs):
        super(Tidyup, self).__init__(**kwargs)
        """
        """

    def check_highest_quality_set(self):
        session = self.Session()
        # TODO: Convert query to sqlalchemy
        # Query to find films that do not have the higest scored filefolder associated
        raw_query = """select *
		from ZP_FILM
		where ZP_FILM_FILEFOLDER_ID not in (
		select tt.ZP_FILM_FILEFOLDER_ID
		from (SELECT zpff.ID AS ZP_FILM_FILEFOLDER_ID, zpffs.SCORE AS SCORE , zpff.ZP_FILM_ID AS ZP_FILM_ID, zpff.LAST_PATH AS LAST_PATH
		FROM ZP_FILM_FILEFOLDER zpff
		inner join ZP_FILM_FILEFOLDER_SCORE zpffs
		on zpff.ID = zpffs.ZP_FILM_FILEFOLDER_ID
		where zpff.ZP_FILM_ID is not null) as tt
		inner join
			(select ZP_FILM_ID, MAX(SCORE) as maxSCORE
		        from (SELECT zpff.ID AS ZP_FILM_FILEFOLDER_ID, zpffs.SCORE AS SCORE , zpff.ZP_FILM_ID AS ZP_FILM_ID, zpff.LAST_PATH AS LAST_PATH
		            FROM ZP_FILM_FILEFOLDER zpff
		            inner join ZP_FILM_FILEFOLDER_SCORE zpffs
		            on zpff.ID = zpffs.ZP_FILM_FILEFOLDER_ID
		            where zpff.ZP_FILM_ID is not null) as ter
		        group by ZP_FILM_ID) groupedtt 
		on tt.ZP_FILM_ID = groupedtt.ZP_FILM_ID
		AND tt.SCORE = groupedtt.maxSCORE)
		"""
        films = session.execute(raw_query)
        for film in films:
            ZP_FILM_FILEFOLDER_ID = session.query(TABLES.ZP_FILM_FILEFOLDER).filter(
                TABLES.ZP_FILM_FILEFOLDER.ID == TABLES.ZP_FILM_FILEFOLDER_SCORE.ZP_FILM_FILEFOLDER_ID,
                TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == film.ID).order_by(
                TABLES.ZP_FILM_FILEFOLDER_SCORE.SCORE.desc()).first()
            # todo ZP_FILM_FILEFOLDER_ID deal with no score
            if ZP_FILM_FILEFOLDER_ID is not None:
                session.query(TABLES.ZP_FILM).filter(TABLES.ZP_FILM.ID == film.ID).update(
                    {'ZP_FILM_FILEFOLDER_ID': ZP_FILM_FILEFOLDER_ID})
                commit(session)
