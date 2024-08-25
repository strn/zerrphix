# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging

from sqlalchemy import orm

import zerrphix.specials
from zerrphix.db import commit
from zerrphix.db.tables import TABLES

log = logging.getLogger(__name__)

_types_dict = {'graphic': 1, 'text': 2}


class Specials(zerrphix.specials.Specials):

    def make_special_type_dict(self):
        """Constructs two dict contating the data from TABLES.ZP_USER_SPECIAL_TYPE

            Note:
                Two dicts are needed as they need to be accessed by TABLES.ZP_USER_SPECIAL_TYPE.ID \
                and TABLES.ZP_USER_SPECIAL_TYPE.DESCR.

            Returns:
                | dict: {TABLES.ZP_USER_SPECIAL_TYPE.DESCR:{
                | 'ID':ZP_USER_SPECIAL_TYPE.ID
                | 'USES_LANG':ZP_USER_SPECIAL_TYPE.USES_LANG
                | 'DESCR':ZP_USER_SPECIAL_TYPE.DESCR}}
                | dict: {TABLES.ZP_USER_SPECIAL_TYPE.ID:{
                | 'ID':ZP_USER_SPECIAL_TYPE.ID
                | 'USES_LANG':ZP_USER_SPECIAL_TYPE.USES_LANG
                | 'DESCR':ZP_USER_SPECIAL_TYPE.DESCR}}

        """
        session = self.Session()
        special_types = session.query(TABLES.ZP_USER_SPECIAL_TYPE).all()
        return_dict_by_special = {}
        return_dict_by_id = {}
        for special_type in special_types:
            return_dict_by_special[special_type.DESCR] = {}
            return_dict_by_special[special_type.DESCR]['ID'] = special_type.ID
            return_dict_by_special[special_type.DESCR]['USES_LANG'] = special_type.USES_LANG
            return_dict_by_special[special_type.DESCR]['DESCR'] = special_type.DESCR
            return_dict_by_id[special_type.ID] = return_dict_by_special[special_type.DESCR]
        session.close()
        return return_dict_by_special, return_dict_by_id

    def username(self, **kwargs):
        """Get the Title from the db
            Args:
                | ZP_TV_ID (int): the tv id
                | ZP_USER_ID (int): the user id
                | ZP_EAPI_ID (int): the eapi id
            Returns:
                | string: Title or 'No Title Found' if no result found
                | int: ZP_EAPI_ID_ACT or 0 if no result found
        """
        zp_user_id = kwargs['ZP_USER_ID']
        session = self.Session()
        try:
            zp_user = session.query(
                TABLES.ZP_USER).filter(
                TABLES.ZP_USER.ID == zp_user_id
            ).one()
        except orm.exc.NoResultFound as e:
            log.warning(('USERNAME for ZP_USER_ID: {0} cannot be found in db from table ZP_USER').format(
                zp_user_id))
        else:
            session.close()
            return zp_user.USERNAME, 0
        session.close()
        return 'No username found', 0