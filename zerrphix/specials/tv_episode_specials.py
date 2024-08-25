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
    def construct_image_ident(self, **kwargs):
        """Construct the image ident

            Note:
                The image ident is a string containing information about the specials
                (e.g. title, cast etc...) to uniquely identify the image as there
                can be differences even within the same temaplte due to user
                preferences

            Args:
                | template_dict (dict): xml template converted to a dict
                | ZP_TV_ID (int): The tv id
                | ZP_USER_ID (int): The user id
                | ZP_LANG_ID (int): The language id
                | ZP_EAPI_ID_REQ (int): The requested EAPI id
                | ZP_TV_IMAGE_TYPE_ID (int): The image type (i.e.icon/synopsis) id

            Attributes:
                | user_special_list (list): A list of TABLE.ZP_TV_SPECIAL_TYPE.ID's \
                in the template (template_dict) via self.special_type_dict_by_special
                | user_special_dict (dict): { TABLES.ZP_TV_SPEICAL_TYPE.ID: {
                | 'ZP_EAPI_ID_ACT': TABLES.ZP_TV_SPEICAL_TYPE_XREF.ZP_EAPI_ID_ACT
                | 'ZP_LANG_ID_ACT': TABLES.ZP_TV_SPEICAL_TYPE_XREF.ZP_LANG_ID_ACT}}

            Returns:
                str: the image ident

        """
        user_special_list = []
        for item in kwargs['template_dict']['template']['item']:
            for _type in _types_dict:
                if _type in item.keys():
                    if '@special' in item[_type].keys():
                        if (kwargs['ZP_IMAGE_SUB_TYPE'] > 0 and '@icon_sub_type_list' in item[_type].keys() and kwargs[
                            'ZP_IMAGE_SUB_TYPE'] in
                            item[_type]['@icon_sub_type_list']) or '@icon_sub_type_list' not in item[_type].keys():
                            # print(_type, _types_dict[_type], item[_type]['@special'])
                            if item[_type]['@special'] in self.special_type_dict_by_special.keys():
                                if self.special_type_dict_by_special[item[_type]['@special']][
                                    'ID'] not in user_special_list:
                                    user_special_list.append(
                                        self.special_type_dict_by_special[item[_type]['@special']]['ID'])
                                    # user_special_list = sorted(user_special_list)
                                    # ident = ''
        user_special_dict = {}
        for ZP_TV_SPECIAL_TYPE_ID in user_special_list:
            # TV title is not in ZP_TV_SPEICAL_TYPE_XREF as it is specifc to user
            # if ZP_TV_SPECIAL_TYPE_ID != 2:
            # TODO: Not using lang here as should be same title accross all langs? change to use lang
            if ZP_TV_SPECIAL_TYPE_ID not in [2, 6, 1, 8, 9, 10]:
                if self.special_type_dict_by_id[ZP_TV_SPECIAL_TYPE_ID]['USES_LANG'] == 1:
                    ZP_LANG_ID_REQ = kwargs['ZP_LANG_ID_REQ']
                else:
                    ZP_LANG_ID_REQ = 0
                try:
                    session = self.Session()
                    db_special = session.query(TABLES.ZP_TV_EPISODE_SPEICAL_TYPE_XREF).filter(
                        TABLES.ZP_TV_EPISODE_SPEICAL_TYPE_XREF.ZP_TV_ID == kwargs['ZP_TV_ID'],
                        TABLES.ZP_TV_EPISODE_SPEICAL_TYPE_XREF.SEASON == kwargs['SEASON'],
                        TABLES.ZP_TV_EPISODE_SPEICAL_TYPE_XREF.FIRST_EPISODE == kwargs['FIRST_EPISODE'],
                        TABLES.ZP_TV_EPISODE_SPEICAL_TYPE_XREF.ZP_TV_SPECIAL_TYPE_ID == ZP_TV_SPECIAL_TYPE_ID,
                        TABLES.ZP_TV_EPISODE_SPEICAL_TYPE_XREF.ZP_EAPI_ID_REQ == kwargs['ZP_EAPI_ID_REQ'],
                        TABLES.ZP_TV_EPISODE_SPEICAL_TYPE_XREF.ZP_LANG_ID_REQ == ZP_LANG_ID_REQ,
                        TABLES.ZP_TV_EPISODE_SPEICAL_TYPE_XREF.ZP_TV_IMAGE_TYPE_ID == kwargs['zp_image_type_id']).one()
                except orm.exc.NoResultFound:
                    log.debug((
                        'row cannot be found in ZP_TV_EPISODE_SPEICAL_TYPE_XREF for ZP_TV_EPISODE_ID: '
                        '{0}, ZP_TV_SPECIAL_TYPE_ID: {1}, ZP_LANG_ID: {2}').format(
                        kwargs['ZP_TV_EPISODE_ID'],
                        ZP_TV_SPECIAL_TYPE_ID,
                        kwargs['ZP_LANG_ID_REQ'] if self.special_type_dict_by_id[ZP_TV_SPECIAL_TYPE_ID][
                                                    'USES_LANG'] == 1 else 0))
                    return False
                except orm.exc.MultipleResultsFound:
                    log.debug((
                        'more than one row was found in ZP_TV_EPISODE_SPEICAL_TYPE_XREF for ZP_TV_EPISODE_ID: {0}, ZP_TV_SPECIAL_TYPE_ID: {1}, ZP_LANG_ID: {2}').format(
                        kwargs['ZP_TV_EPISODE_ID'],
                        ZP_TV_SPECIAL_TYPE_ID,
                        kwargs['ZP_LANG_ID_REQ'] if self.special_type_dict_by_id[ZP_TV_SPECIAL_TYPE_ID][
                                                    'USES_LANG'] == 1 else 0))
                    raise Exception(
                        'more than one row was found in ZP_TV_EPISODE_SPEICAL_TYPE_XREF for ZP_TV_EPISODE_ID: {0}, ZP_TV_SPECIAL_TYPE_ID: {1}, ZP_LANG_ID: {2}'.format(
                            kwargs['ZP_TV_EPISODE_ID'],
                            ZP_TV_SPECIAL_TYPE_ID,
                            kwargs['ZP_LANG_ID_REQ'] if self.special_type_dict_by_id[ZP_TV_SPECIAL_TYPE_ID][
                                                        'USES_LANG'] == 1 else 0))
                else:
                    user_special_dict[ZP_TV_SPECIAL_TYPE_ID] = {}
                    user_special_dict[ZP_TV_SPECIAL_TYPE_ID]['ZP_EAPI_ID_ACT'] = db_special.ZP_EAPI_ID_ACT
                    # if not ZP_TV_SPECIAL_TYPE_ID in [1, 2]:
                    if self.special_type_dict_by_id[ZP_TV_SPECIAL_TYPE_ID]['USES_LANG'] == 1:
                        user_special_dict[ZP_TV_SPECIAL_TYPE_ID]['ZP_LANG_ID_ACT'] = db_special.ZP_LANG_ID_ACT
                        # print(user_special_dict)
        ident = ''
        for ZP_TV_SPECIAL_TYPE_ID in sorted(user_special_list):
            # if ZP_TV_SPECIAL_TYPE_ID in [2]:
            # ident += '{0}'.format(self.user_ZP_TV_EPISODE_TITLE_ID(ZP_TV_ID, ZP_USER_ID))
            if ZP_TV_SPECIAL_TYPE_ID in [2]:
                ZP_TV_TITLE_ID = self.user_ZP_TV_EPISODE_TITLE_ID(**kwargs)
                if ZP_TV_TITLE_ID > 0:
                    ident += '{0}'.format(ZP_TV_TITLE_ID)
                    log.debug('special %s, %s', ZP_TV_SPECIAL_TYPE_ID,
                              ZP_TV_TITLE_ID)
                else:
                    ident += '0'
                    log.debug('special %s, %s', ZP_TV_SPECIAL_TYPE_ID,
                              '0')
            elif ZP_TV_SPECIAL_TYPE_ID in [6]:
                ZP_TV_OVERVIEW_ID = self.user_ZP_TV_EPISODE_OVERVIEW_ID(**kwargs)
                if ZP_TV_OVERVIEW_ID > 0:
                    ident += '{0}'.format(ZP_TV_OVERVIEW_ID)
                    log.debug('special %s, %s', ZP_TV_SPECIAL_TYPE_ID,
                              ZP_TV_OVERVIEW_ID)
                else:
                    ident += '0'
                    log.debug('special %s, %s', ZP_TV_SPECIAL_TYPE_ID,
                              '0')
            elif ZP_TV_SPECIAL_TYPE_ID in [1,8,9,10]:
                ZP_TV_RAW_IMAGE_ID = self.user_ZP_TV_EPISODE_RAW_IMAGE_ID(ZP_TV_SPECIAL_TYPE_ID, **kwargs)
                if ZP_TV_RAW_IMAGE_ID > 0:
                    ident += '{0}'.format(ZP_TV_RAW_IMAGE_ID)
                    log.debug('special %s, %s', ZP_TV_SPECIAL_TYPE_ID,
                              ZP_TV_RAW_IMAGE_ID)
                else:
                    ident += '0'
                    log.debug('special %s, %s', ZP_TV_SPECIAL_TYPE_ID,
                              '0')
            elif self.special_type_dict_by_id[ZP_TV_SPECIAL_TYPE_ID]['USES_LANG'] == 1:
                ident += '{0}{1}{2}'.format(ZP_TV_SPECIAL_TYPE_ID,
                                            user_special_dict[ZP_TV_SPECIAL_TYPE_ID]['ZP_EAPI_ID_ACT'],
                                            user_special_dict[ZP_TV_SPECIAL_TYPE_ID]['ZP_LANG_ID_ACT'])
            else:
                ident += '{0}{1}'.format(ZP_TV_SPECIAL_TYPE_ID,
                                         user_special_dict[ZP_TV_SPECIAL_TYPE_ID]['ZP_EAPI_ID_ACT'])
        return ident

    def user_ZP_TV_EPISODE_RAW_IMAGE_ID(self, ZP_TV_SPECIAL_TYPE_ID, **kwargs):
        """Get the ZP_TV_TITLE_ID for ZP_USER_ID (assocation created by user specifics).

            Returns:
                int: ZP_TV_TITLE_ID if a ZP_TV_TITLE_ID is found otherwise None is returned

        """
        # todo get this from db/global dict
        speical_image_type_entity_type_dict = {10: 3}
        session = self.Session()
        ZP_TV_RAW_IMAGE_ID = None
        try:
            ZP_TV_RAW_IMAGE_ID = session.query(
                TABLES.ZP_TV_EPISODE_RAW_IMAGE
            ).filter(
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ID == TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_ID,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_USER_ID == kwargs['ZP_USER_ID'],
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID == kwargs['ZP_TV_ID'],
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON == kwargs['SEASON'],
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE == kwargs['FIRST_EPISODE'],
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == speical_image_type_entity_type_dict[
                    ZP_TV_SPECIAL_TYPE_ID]
            ).one().ID
        except orm.exc.NoResultFound:
            log.warning('Unable to get ZP_TV_RAW_IMAGE_ID for ZP_TV_ID: {0} and ZP_USER_ID: {1}, '
                        'ZP_TV_ENTITY_TYPE_ID: {2}'.format(
                kwargs['ZP_TV_ID'],
                kwargs['ZP_USER_ID'],
                speical_image_type_entity_type_dict[ZP_TV_SPECIAL_TYPE_ID]
            ))
            # raise SystemExit
        return ZP_TV_RAW_IMAGE_ID

    def user_ZP_TV_EPISODE_TITLE_ID(self, **kwargs):
        """Get the ZP_TV_TITLE_ID for ZP_USER_ID (assocation created by user specifics).

            Returns:
                int: ZP_TV_TITLE_ID if a ZP_TV_TITLE_ID is found otherwise None is returned

        """
        session = self.Session()
        ZP_TV_EPISODE_TITLE_ID = None
        try:
            ZP_TV_EPISODE_TITLE_ID = session.query(TABLES.ZP_TV_EPISODE_TITLE).filter(
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_ID == TABLES.ZP_TV_EPISODE_TITLE.ID,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_USER_ID == kwargs['ZP_USER_ID'],
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID == kwargs['ZP_TV_ID'],
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON == kwargs['SEASON'],
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE == kwargs['FIRST_EPISODE'],
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1
            ).one().ID
        except orm.exc.NoResultFound:
            log.warning('Unable to get ZP_TV_TITLE_ID for ZP_TV_ID: {0} and ZP_USER_ID: {1}'.format(
                kwargs['ZP_TV_ID'],
                kwargs['ZP_USER_ID']))
            # raise SystemExit
        return ZP_TV_EPISODE_TITLE_ID

    def user_ZP_TV_EPISODE_OVERVIEW_ID(self, **kwargs):
        """Get the ZP_TV_TITLE_ID for ZP_USER_ID (assocation created by user specifics).

            Returns:
                int: ZP_TV_TITLE_ID if a ZP_TV_TITLE_ID is found otherwise None is returned

        """
        session = self.Session()
        ZP_TV_OVERVIEW_ID = None
        try:
            ZP_TV_OVERVIEW_ID = session.query(TABLES.ZP_TV_EPISODE_OVERVIEW).filter(
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_ID == TABLES.ZP_TV_EPISODE_OVERVIEW.ID,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_USER_ID == kwargs['ZP_USER_ID'],
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID == kwargs['ZP_TV_ID'],
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON == kwargs['SEASON'],
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE == kwargs['FIRST_EPISODE'],
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 2
            ).one().ID
        except orm.exc.NoResultFound:
            log.warning('Unable to get ZP_TV_OVERVIEW_ID for ZP_TV_ID: {0} and ZP_USER_ID: {1}'.format(
                kwargs['ZP_TV_ID'],
                kwargs['ZP_USER_ID']))
            # raise SystemExit
        return ZP_TV_OVERVIEW_ID

    def make_special_type_dict(self):
        """Constructs two dict contating the data from TABLES.ZP_TV_SPECIAL_TYPE

            Note:
                Two dicts are needed as they need to be accessed by TABLES.ZP_TV_SPECIAL_TYPE.ID \
                and TABLES.ZP_TV_SPECIAL_TYPE.DESCR.

            Returns:
                | dict: {TABLES.ZP_TV_SPECIAL_TYPE.DESCR:{
                | 'ID':ZP_TV_SPECIAL_TYPE.ID
                | 'USES_LANG':ZP_TV_SPECIAL_TYPE.USES_LANG
                | 'DESCR':ZP_TV_SPECIAL_TYPE.DESCR}}
                | dict: {TABLES.ZP_TV_SPECIAL_TYPE.ID:{
                | 'ID':ZP_TV_SPECIAL_TYPE.ID
                | 'USES_LANG':ZP_TV_SPECIAL_TYPE.USES_LANG
                | 'DESCR':ZP_TV_SPECIAL_TYPE.DESCR}}

        """
        session = self.Session()
        try:
            special_types = session.query(TABLES.ZP_TV_SPECIAL_TYPE).all()
        except orm.exc.NoResultFound:
            log.critical('Cannot get data from TABLES.ZP_TV_SPECIAL_TYPE')
            raise Exception('Cannot get data from TABLES.ZP_TV_SPECIAL_TYPE')
        else:
            return_dict_by_special = {}
            return_dict_by_id = {}
            for special_type in special_types:
                return_dict_by_special[special_type.DESCR] = {}
                return_dict_by_special[special_type.DESCR]['ID'] = special_type.ID
                return_dict_by_special[special_type.DESCR]['USES_LANG'] = special_type.USES_LANG
                return_dict_by_special[special_type.DESCR]['DESCR'] = special_type.DESCR
                return_dict_by_id[special_type.ID] = return_dict_by_special[special_type.DESCR]
            return return_dict_by_special, return_dict_by_id
        session.close()

    def eapi_special_update_db(self, ZP_TV_ID, SEASON, FIRST_EPISODE, ZP_TV_SPECIAL_TYPE_ID,
                               ZP_LANG_ID_REQ, ZP_LANG_ID_ACT,
                               ZP_EAPI_ID_REQ, ZP_EAPI_ID_ACT, ZP_TV_IMAGE_TYPE_ID):
        """Update (if nesescary) the ZP_TV_SPEICAL_TYPE values used to created the image

            Args:
                | ZP_TV_EPISODE_ID: The tv episode id
                | ZP_TV_SPECIAL_TYPE_ID (int):  The sepcial id
                | ZP_LANG_ID_REQ (int): Requested language id
                | ZP_LANG_ID_ACT (int): Actual language id
                | ZP_EAPI_ID_REQ (int): Requested eapi id
                | ZP_EAPI_ID_ACT (int): Actual eapi id
                | ZP_TV_IMAGE_TYPE_ID (int): image type id

        """
        session = self.Session()
        try:
            ZP_TV_EPISODE_SPEICAL_TYPE_XREF = session.query(TABLES.ZP_TV_EPISODE_SPEICAL_TYPE_XREF).filter(
                TABLES.ZP_TV_EPISODE_SPEICAL_TYPE_XREF.ZP_TV_ID == ZP_TV_ID,
                TABLES.ZP_TV_EPISODE_SPEICAL_TYPE_XREF.SEASON == SEASON,
                TABLES.ZP_TV_EPISODE_SPEICAL_TYPE_XREF.FIRST_EPISODE == FIRST_EPISODE,
                TABLES.ZP_TV_EPISODE_SPEICAL_TYPE_XREF.ZP_TV_SPECIAL_TYPE_ID == ZP_TV_SPECIAL_TYPE_ID,
                TABLES.ZP_TV_EPISODE_SPEICAL_TYPE_XREF.ZP_EAPI_ID_REQ == ZP_EAPI_ID_REQ,
                TABLES.ZP_TV_EPISODE_SPEICAL_TYPE_XREF.ZP_LANG_ID_REQ == ZP_LANG_ID_REQ,
                TABLES.ZP_TV_EPISODE_SPEICAL_TYPE_XREF.ZP_TV_IMAGE_TYPE_ID == ZP_TV_IMAGE_TYPE_ID).one()
        except orm.exc.NoResultFound as e:
            log.debug(('Adding ZP_TV_ID = {0},'
                       ' SEASON = {1},'
                       ' FIRST_EPISODE = {2},'
                       ' ZP_TV_SPECIAL_TYPE_ID = {3},'
                       ' ZP_EAPI_ID_REQ = {4},'
                       ' ZP_EAPI_ID_ACT = {5},'
                       ' ZP_LANG_ID_ACT = {6},'
                       ' ZP_LANG_ID_REQ = {7},'
                       ' ZP_TV_IMAGE_TYPE_ID = {8}'
                       ' to ZP_TV_SPEICAL_TYPE_XREF').format(ZP_TV_ID,
                                                             SEASON,
                                                             FIRST_EPISODE,
                                                             ZP_TV_SPECIAL_TYPE_ID,
                                                             ZP_EAPI_ID_REQ,
                                                             ZP_EAPI_ID_ACT,
                                                             ZP_LANG_ID_ACT,
                                                             ZP_LANG_ID_REQ,
                                                             ZP_TV_IMAGE_TYPE_ID))
            add_ZP_TV_EPISODE_SPEICAL_TYPE_XREF = TABLES.ZP_TV_EPISODE_SPEICAL_TYPE_XREF(ZP_TV_ID=ZP_TV_ID,
                                                                                         SEASON=SEASON,
                                                                                         FIRST_EPISODE=FIRST_EPISODE,
                                                                                         ZP_TV_SPECIAL_TYPE_ID=ZP_TV_SPECIAL_TYPE_ID,
                                                                                         ZP_EAPI_ID_REQ=ZP_EAPI_ID_REQ,
                                                                                         ZP_EAPI_ID_ACT=ZP_EAPI_ID_ACT,
                                                                                         ZP_LANG_ID_ACT=ZP_LANG_ID_ACT,
                                                                                         ZP_LANG_ID_REQ=ZP_LANG_ID_REQ,
                                                                                         ZP_TV_IMAGE_TYPE_ID=ZP_TV_IMAGE_TYPE_ID)
            session.add(add_ZP_TV_EPISODE_SPEICAL_TYPE_XREF)
            commit(session)
        else:
            log.debug(('ZP_TV_ID: {0}, SEASON: {6}, FIRST_EPISODE: {7}'
                       ' ZP_TV_SPECIAL_TYPE_ID:{1},'
                       ' ZP_LANG_ID_REQ: {2}, ZP_LANG_ID_ACT: {3},'
                       ' ZP_EAPI_ID_REQ: {4}, ZP_EAPI_ID_ACT: {5} allready in ZP_TV_SPEICAL_TYPE_XREF'.format(ZP_TV_ID,
                                                                                                              ZP_TV_SPECIAL_TYPE_ID,
                                                                                                              ZP_LANG_ID_REQ,
                                                                                                              ZP_LANG_ID_ACT,
                                                                                                              ZP_EAPI_ID_REQ,
                                                                                                              ZP_EAPI_ID_ACT,
                                                                                                              SEASON,
                                                                                                              FIRST_EPISODE, )))
            # ZP_TV_EPISODE_SPEICAL_TYPE_XREF
            if ZP_TV_EPISODE_SPEICAL_TYPE_XREF.ZP_LANG_ID_ACT != ZP_LANG_ID_ACT or \
                    ZP_TV_EPISODE_SPEICAL_TYPE_XREF.ZP_EAPI_ID_ACT != ZP_EAPI_ID_ACT:
                log.warning(('db ZP_TV_EPISODE_SPEICAL_TYPE_XREF.ZP_LANG_ID_ACT: {0},'
                             ' db ZP_TV_EPISODE_SPEICAL_TYPE_XREF.ZP_EAPI_ID_ACT: {1},'
                             ' ZP_LANG_ID_ACT: {2},'
                             ' ZP_EAPI_ID_ACT: {3}.').format(ZP_TV_EPISODE_SPEICAL_TYPE_XREF.ZP_LANG_ID_ACT,
                                                             ZP_TV_EPISODE_SPEICAL_TYPE_XREF.ZP_EAPI_ID_ACT,
                                                             ZP_LANG_ID_ACT,
                                                             ZP_EAPI_ID_ACT))
                # raise SystemExit
                ZP_TV_EPISODE_SPEICAL_TYPE_XREF.ZP_LANG_ID_ACT = ZP_LANG_ID_ACT
                ZP_TV_EPISODE_SPEICAL_TYPE_XREF.ZP_EAPI_ID_ACT = ZP_EAPI_ID_ACT
                commit(session)
        session.close()

    def title(self, **kwargs):
        # print(locals())
        """Get the overview from the db
            Args:
                | ZP_TV_ID (int): the tv id
                | ZP_USER_ID (int): the user id
                | ZP_EAPI_ID (int): the eapi id
                | ZP_LANG_ID (int): the language id
            Returns:
                | string: overview or 'No Overview Found' if no result found
                | int: ZP_EAPI_ID_ACT or 0 if no result found
                | int: ZP_LANG_ID_ACT or 0 if no result found
        """
        ZP_TV_ID = kwargs['ZP_TV_ID']
        ZP_LANG_ID = kwargs['ZP_LANG_ID_REQ']
        SEASON = kwargs['SEASON']
        EPISODE = kwargs['FIRST_EPISODE']
        ZP_USER_ID = kwargs['ZP_USER_ID']
        session = self.Session()
        TITLE = 'Episode {0}'.format(EPISODE)
        # print(self.eapi_plugins_access_list)
        session = self.Session()
        ZP_TV_EPISODE_TITLE_ID = None
        try:
            ZP_TV_EPISODE_TITLE = session.query(TABLES.ZP_TV_EPISODE_TITLE).filter(
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_ID == TABLES.ZP_TV_EPISODE_TITLE.ID,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID == ZP_TV_ID,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON == SEASON,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE == EPISODE,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1
            ).one()
        except orm.exc.NoResultFound:
            log.warning('Unable to get ZP_TV_TITLE_ID for ZP_TV_ID: {0} and ZP_USER_ID: {1}'.format(
                ZP_TV_ID,
                ZP_USER_ID))
            # raise SystemExit
        else:
            session.close()
            return ZP_TV_EPISODE_TITLE.TITLE, ZP_TV_EPISODE_TITLE.ID
        session.close()
        return TITLE, 0

    def overview(self, **kwargs):
        """Get the overview from the db
            Args:
                | ZP_TV_ID (int): the tv id
                | ZP_USER_ID (int): the user id
                | ZP_EAPI_ID (int): the eapi id
                | ZP_LANG_ID (int): the language id
            Returns:
                | string: overview or 'No Overview Found' if no result found
                | int: ZP_EAPI_ID_ACT or 0 if no result found
                | int: ZP_LANG_ID_ACT or 0 if no result found
        """
        ZP_TV_ID = kwargs['ZP_TV_ID']
        SEASON = kwargs['SEASON']
        EPISODE = kwargs['FIRST_EPISODE']
        ZP_USER_ID = kwargs['ZP_USER_ID']
        session = self.Session()
        OVERVIEW = 'No Overview Found'
        # print(self.eapi_plugins_access_list)
        try:
            ZP_TV_EPISODE_OVERVIEW = session.query(
                TABLES.ZP_TV_EPISODE_OVERVIEW).filter(
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID == kwargs['ZP_TV_ID'],
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON == SEASON,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE == EPISODE,
                TABLES.ZP_TV_EPISODE_OVERVIEW.ID == TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_ID,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 2
            ).one()
        except orm.exc.NoResultFound as e:
            log.warning(('TV OVERVIEW for ZP_TV_ID: {0} cannot be found in db from table ZP_TV_OVERVIEW').format(
                ZP_TV_ID))
        else:
            session.close()
            return ZP_TV_EPISODE_OVERVIEW.OVERVIEW, ZP_TV_EPISODE_OVERVIEW.ID
        session.close()
        return OVERVIEW, 0