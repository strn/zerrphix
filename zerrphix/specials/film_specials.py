# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging

from sqlalchemy import orm

import zerrphix.specials
from zerrphix.db import commit
from zerrphix.db.tables import TABLES
from sqlalchemy import func, case
from zerrphix.util.filesystem import get_file_extension

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
                | ZP_FILM_ID (int): The tv id
                | ZP_USER_ID (int): The user id
                | ZP_LANG_ID (int): The language id
                | ZP_EAPI_ID_REQ (int): The requested EAPI id
                | ZP_FILM_IMAGE_TYPE_ID (int): The image type (i.e.icon/synopsis) id

            Attributes:
                | user_special_list (list): A list of TABLE.ZP_FILM_SPECIAL_TYPE.ID's \
                in the template (template_dict) via self.special_type_dict_by_special
                | user_special_dict (dict): { TABLES.ZP_FILM_SPEICAL_TYPE.ID: {
                | 'ZP_EAPI_ID_ACT': TABLES.ZP_FILM_SPEICAL_TYPE_XREF.ZP_EAPI_ID_ACT
                | 'ZP_LANG_ID_ACT': TABLES.ZP_FILM_SPEICAL_TYPE_XREF.ZP_LANG_ID_ACT}}

            Returns:
                str: the image ident

        """
        user_special_list = []
        for item in kwargs['template_dict']['template']['item']:
            for _type in _types_dict:
                if _type in item.keys():
                    if '@special' in item[_type].keys():
                        # print(_type, _types_dict[_type], item[_type]['@special'])
                        if item[_type]['@special'] in self.special_type_dict_by_special.keys():
                            if self.special_type_dict_by_special[item[_type]['@special']][
                                'ID'] not in user_special_list:
                                user_special_list.append(
                                    self.special_type_dict_by_special[item[_type]['@special']]['ID'])
                                # user_special_list = sorted(user_special_list)
                                # ident = ''
        user_special_dict = {}
        for ZP_FILM_SPECIAL_TYPE_ID in user_special_list:
            # TV title is not in ZP_FILM_SPEICAL_TYPE_XREF as it is specifc to user
            if ZP_FILM_SPECIAL_TYPE_ID not in [4,1,2,10]:
                # TODO: Not using lang here as should be same title accross all langs? change to use lang
                if self.special_type_dict_by_id[ZP_FILM_SPECIAL_TYPE_ID]['USES_LANG'] == 1:
                    ZP_LANG_ID_REQ = kwargs['ZP_LANG_ID_REQ']
                else:
                    ZP_LANG_ID_REQ = 0
                try:
                    session = self.Session()
                    db_special = session.query(TABLES.ZP_FILM_SPEICAL_TYPE_XREF).filter(
                        TABLES.ZP_FILM_SPEICAL_TYPE_XREF.ZP_FILM_ID == kwargs['ZP_ENTITY_ID'],
                        TABLES.ZP_FILM_SPEICAL_TYPE_XREF.ZP_FILM_SPECIAL_TYPE_ID == ZP_FILM_SPECIAL_TYPE_ID,
                        TABLES.ZP_FILM_SPEICAL_TYPE_XREF.ZP_EAPI_ID_REQ == kwargs['ZP_EAPI_ID_REQ'],
                        TABLES.ZP_FILM_SPEICAL_TYPE_XREF.ZP_LANG_ID_REQ == ZP_LANG_ID_REQ,
                        TABLES.ZP_FILM_SPEICAL_TYPE_XREF.ZP_FILM_IMAGE_TYPE_ID == kwargs['zp_image_type_id']).one()
                except orm.exc.NoResultFound:
                    log.debug((
                        'row cannot be found in ZP_FILM_SPEICAL_TYPE_XREF for ZP_FILM_ID: {0}, ZP_FILM_SPECIAL_TYPE_ID: {1}, ZP_LANG_ID: {2}').format(
                        kwargs['ZP_ENTITY_ID'],
                        ZP_FILM_SPECIAL_TYPE_ID,
                        ZP_LANG_ID_REQ if self.special_type_dict_by_id[ZP_FILM_SPECIAL_TYPE_ID][
                                              'USES_LANG'] == 1 else 0))
                    #session.close()
                    return False
                except orm.exc.MultipleResultsFound:
                    log.debug((
                        'more than one row was found in ZP_FILM_SPEICAL_TYPE_XREF for ZP_FILM_ID: {0}, ZP_FILM_SPECIAL_TYPE_ID: {1}, ZP_LANG_ID: {2}').format(
                        kwargs['ZP_ENTITY_ID'],
                        ZP_FILM_SPECIAL_TYPE_ID,
                        ZP_LANG_ID_REQ if self.special_type_dict_by_id[ZP_FILM_SPECIAL_TYPE_ID][
                                              'USES_LANG'] == 1 else 0))
                    raise Exception(
                        'more than one row was found in ZP_FILM_SPEICAL_TYPE_XREF for ZP_FILM_ID: {0}, ZP_FILM_SPECIAL_TYPE_ID: {1}, ZP_LANG_ID: {2}'.format(
                            kwargs['ZP_ENTITY_ID'],
                            ZP_FILM_SPECIAL_TYPE_ID,
                            ZP_LANG_ID_REQ if self.special_type_dict_by_id[ZP_FILM_SPECIAL_TYPE_ID][
                                                  'USES_LANG'] == 1 else 0))
                else:
                    user_special_dict[ZP_FILM_SPECIAL_TYPE_ID] = {}
                    user_special_dict[ZP_FILM_SPECIAL_TYPE_ID]['ZP_EAPI_ID_ACT'] = db_special.ZP_EAPI_ID_ACT
                    # if not ZP_FILM_SPECIAL_TYPE_ID in [1, 2]:
                    if self.special_type_dict_by_id[ZP_FILM_SPECIAL_TYPE_ID]['USES_LANG'] == 1:
                        user_special_dict[ZP_FILM_SPECIAL_TYPE_ID]['ZP_LANG_ID_ACT'] = db_special.ZP_LANG_ID_ACT
                        # print(user_special_dict)
        ident = ''
        #log.error('user_special_list %s', user_special_list)
        #log.error('user_special_dict %s', user_special_dict)
        for ZP_FILM_SPECIAL_TYPE_ID in sorted(user_special_list):
            if ZP_FILM_SPECIAL_TYPE_ID in [4]:
                ZP_FILM_TITLE_ID = self.user_ZP_FILM_TITLE_ID(kwargs['ZP_ENTITY_ID'], kwargs['ZP_USER_ID'])
                if ZP_FILM_TITLE_ID > 0:
                    ident += '{0}'.format(ZP_FILM_TITLE_ID)
                    log.debug('special %s, %s', ZP_FILM_SPECIAL_TYPE_ID,
                              ZP_FILM_TITLE_ID)
                else:
                    ident += '0'
                    log.debug('special %s, %s', ZP_FILM_SPECIAL_TYPE_ID,
                              '0')
            elif ZP_FILM_SPECIAL_TYPE_ID in [10]:
                ZP_FILM_OVERVIEW_ID = self.user_ZP_FILM_OVERVIEW_ID(kwargs['ZP_ENTITY_ID'], kwargs['ZP_USER_ID'])
                if ZP_FILM_OVERVIEW_ID > 0:
                    ident += '{0}'.format(ZP_FILM_OVERVIEW_ID)
                    log.debug('special %s, %s', ZP_FILM_SPECIAL_TYPE_ID,
                              ZP_FILM_OVERVIEW_ID)
                else:
                    ident += '0'
                    log.debug('special %s, %s', ZP_FILM_SPECIAL_TYPE_ID,
                              '0')
            elif ZP_FILM_SPECIAL_TYPE_ID in [1,2]:
                ZP_FILM_RAW_IMAGE_ID = self.user_ZP_FILM_RAW_IMAGE_ID(kwargs['ZP_ENTITY_ID'], kwargs['ZP_USER_ID'],
                                                                      ZP_FILM_SPECIAL_TYPE_ID)
                if ZP_FILM_RAW_IMAGE_ID > 0:
                    ident += '{0}'.format(ZP_FILM_RAW_IMAGE_ID)
                    log.debug('special %s, %s', ZP_FILM_SPECIAL_TYPE_ID,
                              ZP_FILM_RAW_IMAGE_ID)
                else:
                    ident += '0'
                    log.debug('special %s, %s', ZP_FILM_SPECIAL_TYPE_ID,
                              '0')
            elif self.special_type_dict_by_id[ZP_FILM_SPECIAL_TYPE_ID]['USES_LANG'] == 1:
                ident += '{0}{1}{2}'.format(ZP_FILM_SPECIAL_TYPE_ID,
                                            user_special_dict[ZP_FILM_SPECIAL_TYPE_ID]['ZP_EAPI_ID_ACT'],
                                            user_special_dict[ZP_FILM_SPECIAL_TYPE_ID]['ZP_LANG_ID_ACT'])
                log.debug('special %s, %s', ZP_FILM_SPECIAL_TYPE_ID,
                              '{0}{1}{2}'.format(ZP_FILM_SPECIAL_TYPE_ID,
                                                 user_special_dict[ZP_FILM_SPECIAL_TYPE_ID]['ZP_EAPI_ID_ACT'],
                                                 user_special_dict[ZP_FILM_SPECIAL_TYPE_ID]['ZP_LANG_ID_ACT']))
            else:
                ident += '{0}{1}'.format(ZP_FILM_SPECIAL_TYPE_ID,
                                         user_special_dict[ZP_FILM_SPECIAL_TYPE_ID]['ZP_EAPI_ID_ACT'])
                log.debug('special %s, %s', ZP_FILM_SPECIAL_TYPE_ID,
                          '{0}{1}'.format(ZP_FILM_SPECIAL_TYPE_ID,
                                          user_special_dict[ZP_FILM_SPECIAL_TYPE_ID]['ZP_EAPI_ID_ACT']))
        return ident

    def user_ZP_FILM_RAW_IMAGE_ID(self, ZP_FILM_ID, ZP_USER_ID, ZP_FILM_SPECIAL_TYPE_ID):
        """Get the ZP_FILM_TITLE_ID for ZP_USER_ID (assocation created by user specifics).

            Returns:
                int: ZP_FILM_TITLE_ID if a ZP_FILM_TITLE_ID is found otherwise None is returned

        """
        # todo get this from db/global dict
        speical_image_type_entity_type_dict = {2: 3, 1: 4}
        session = self.Session()
        ZP_FILM_RAW_IMAGE_ID = None
        try:
            ZP_FILM_RAW_IMAGE_ID = session.query(TABLES.ZP_FILM_RAW_IMAGE).filter(
                TABLES.ZP_FILM_RAW_IMAGE.ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == ZP_FILM_ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == speical_image_type_entity_type_dict[
                    ZP_FILM_SPECIAL_TYPE_ID]
            ).one().ID
        except orm.exc.NoResultFound:
            log.warning('Unable to get ZP_FILM_RAW_IMAGE_ID for ZP_FILM_ID: {0} and ZP_USER_ID: {1}, '
                        'ZP_FILM_ENTITY_TYPE_ID: {2}'.format(
                ZP_FILM_ID,
                ZP_USER_ID,
                speical_image_type_entity_type_dict[ZP_FILM_SPECIAL_TYPE_ID]
            ))
            # raise SystemExit
        return ZP_FILM_RAW_IMAGE_ID

    def user_ZP_FILM_TITLE_ID(self, ZP_FILM_ID, ZP_USER_ID):
        """Get the ZP_FILM_TITLE_ID for ZP_USER_ID (assocation created by user specifics).

            Returns:
                int: ZP_FILM_TITLE_ID if a ZP_FILM_TITLE_ID is found otherwise None is returned

        """
        session = self.Session()
        ZP_FILM_TITLE_ID = None
        try:
            ZP_FILM_TITLE_ID = session.query(TABLES.ZP_FILM_TITLE).filter(
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID == TABLES.ZP_FILM_TITLE.ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == ZP_FILM_ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1
            ).one().ID
        except orm.exc.NoResultFound:
            log.warning('Unable to get ZP_FILM_TITLE_ID for ZP_FILM_ID: {0} and ZP_USER_ID: {1}'.format(
                ZP_FILM_ID,
                ZP_USER_ID))
            # raise SystemExit
        return ZP_FILM_TITLE_ID

    def user_ZP_FILM_OVERVIEW_ID(self, ZP_FILM_ID, ZP_USER_ID):
        """Get the ZP_FILM_TITLE_ID for ZP_USER_ID (assocation created by user specifics).

            Returns:
                int: ZP_FILM_TITLE_ID if a ZP_FILM_TITLE_ID is found otherwise None is returned

        """
        session = self.Session()
        ZP_FILM_OVERVIEW_ID = None
        try:
            ZP_FILM_OVERVIEW_ID = session.query(TABLES.ZP_FILM_OVERVIEW).filter(
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID == TABLES.ZP_FILM_OVERVIEW.ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == ZP_FILM_ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == ZP_USER_ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 2
            ).one().ID
        except orm.exc.NoResultFound:
            log.warning('Unable to get ZP_FILM_OVERVIEW_ID for ZP_FILM_ID: {0} and ZP_USER_ID: {1}'.format(
                ZP_FILM_ID,
                ZP_USER_ID))
            # raise SystemExit
        return ZP_FILM_OVERVIEW_ID

    def make_special_type_dict(self):
        """Constructs two dict contating the data from TABLES.ZP_FILM_SPECIAL_TYPE

            Note:
                Two dicts are needed as they need to be accessed by TABLES.ZP_FILM_SPECIAL_TYPE.ID \
                and TABLES.ZP_FILM_SPECIAL_TYPE.DESCR.

            Returns:
                | dict: {TABLES.ZP_FILM_SPECIAL_TYPE.DESCR:{
                | 'ID':ZP_FILM_SPECIAL_TYPE.ID
                | 'USES_LANG':ZP_FILM_SPECIAL_TYPE.USES_LANG
                | 'DESCR':ZP_FILM_SPECIAL_TYPE.DESCR}}
                | dict: {TABLES.ZP_FILM_SPECIAL_TYPE.ID:{
                | 'ID':ZP_FILM_SPECIAL_TYPE.ID
                | 'USES_LANG':ZP_FILM_SPECIAL_TYPE.USES_LANG
                | 'DESCR':ZP_FILM_SPECIAL_TYPE.DESCR}}

        """
        session = self.Session()
        special_types = session.query(TABLES.ZP_FILM_SPECIAL_TYPE).all()
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

    def eapi_special_update_db(self, ZP_FILM_ID, ZP_FILM_SPECIAL_TYPE_ID, ZP_LANG_ID_REQ, ZP_LANG_ID_ACT,
                               ZP_EAPI_ID_REQ, ZP_EAPI_ID_ACT, ZP_FILM_IMAGE_TYPE_ID):
        """Update (if nesescary) the ZP_FILM_SPEICAL_TYPE values used to created the image

            Args:
                | ZP_FILM_ID: The film id
                | ZP_FILM_SPECIAL_TYPE_ID (int):  The sepcial id
                | ZP_LANG_ID_REQ (int): Requested language id
                | ZP_LANG_ID_ACT (int): Actual language id
                | ZP_EAPI_ID_REQ (int): Requested eapi id
                | ZP_EAPI_ID_ACT (int): Actual eapi id
                | ZP_FILM_IMAGE_TYPE_ID (int): image type id

        """
        session = self.Session()
        try:
            ZP_FILM_SPEICAL_TYPE_XREF = session.query(TABLES.ZP_FILM_SPEICAL_TYPE_XREF).filter(
                TABLES.ZP_FILM_SPEICAL_TYPE_XREF.ZP_FILM_ID == ZP_FILM_ID,
                TABLES.ZP_FILM_SPEICAL_TYPE_XREF.ZP_FILM_SPECIAL_TYPE_ID == ZP_FILM_SPECIAL_TYPE_ID,
                TABLES.ZP_FILM_SPEICAL_TYPE_XREF.ZP_EAPI_ID_REQ == ZP_EAPI_ID_REQ,
                TABLES.ZP_FILM_SPEICAL_TYPE_XREF.ZP_LANG_ID_REQ == ZP_LANG_ID_REQ,
                TABLES.ZP_FILM_SPEICAL_TYPE_XREF.ZP_FILM_IMAGE_TYPE_ID == ZP_FILM_IMAGE_TYPE_ID).one()
        except orm.exc.NoResultFound as e:
            log.debug(('Adding ZP_FILM_ID = {0},'
                       ' ZP_FILM_SPECIAL_TYPE_ID = {1},'
                       ' ZP_EAPI_ID_REQ = {2},'
                       ' ZP_EAPI_ID_ACT = {3},'
                       ' ZP_LANG_ID_ACT = {4},'
                       ' ZP_LANG_ID_REQ = {5},'
                       ' ZP_FILM_IMAGE_TYPE_ID = {6}'
                       ' to ZP_FILM_SPEICAL_TYPE_XREF').format(ZP_FILM_ID,
                                                               ZP_FILM_SPECIAL_TYPE_ID,
                                                               ZP_EAPI_ID_REQ,
                                                               ZP_EAPI_ID_ACT,
                                                               ZP_LANG_ID_ACT,
                                                               ZP_LANG_ID_REQ,
                                                               ZP_FILM_IMAGE_TYPE_ID))
            add_ZP_FILM_SPEICAL_TYPE_XREF = TABLES.ZP_FILM_SPEICAL_TYPE_XREF(ZP_FILM_ID=ZP_FILM_ID,
                                                                             ZP_FILM_SPECIAL_TYPE_ID=ZP_FILM_SPECIAL_TYPE_ID,
                                                                             ZP_EAPI_ID_REQ=ZP_EAPI_ID_REQ,
                                                                             ZP_EAPI_ID_ACT=ZP_EAPI_ID_ACT,
                                                                             ZP_LANG_ID_ACT=ZP_LANG_ID_ACT,
                                                                             ZP_LANG_ID_REQ=ZP_LANG_ID_REQ,
                                                                             ZP_FILM_IMAGE_TYPE_ID=ZP_FILM_IMAGE_TYPE_ID)
            session.add(add_ZP_FILM_SPEICAL_TYPE_XREF)
            commit(session)
        else:
            log.debug(('ZP_FILM_ID: {0}, ZP_FILM_SPECIAL_TYPE_ID:{1},'
                       ' ZP_LANG_ID_REQ: {2}, ZP_LANG_ID_ACT: {3},'
                       ' ZP_EAPI_ID_REQ: {4}, ZP_EAPI_ID_ACT: {5} allready in ZP_FILM_SPEICAL_TYPE_XREF'.format(
                ZP_FILM_ID,
                ZP_FILM_SPECIAL_TYPE_ID,
                ZP_LANG_ID_REQ,
                ZP_LANG_ID_ACT,
                ZP_EAPI_ID_REQ,
                ZP_EAPI_ID_ACT)))
            if ZP_FILM_SPEICAL_TYPE_XREF.ZP_LANG_ID_ACT != ZP_LANG_ID_ACT or \
                    ZP_FILM_SPEICAL_TYPE_XREF.ZP_EAPI_ID_ACT != ZP_EAPI_ID_ACT:
                log.warning(('db ZP_FILM_SPEICAL_TYPE_XREF.ZP_LANG_ID_ACT: {0},'
                             ' db ZP_FILM_SPEICAL_TYPE_XREF.ZP_EAPI_ID_ACT: {1},'
                             ' ZP_LANG_ID_ACT: {2},'
                             ' ZP_EAPI_ID_ACT: {3}.').format(ZP_FILM_SPEICAL_TYPE_XREF.ZP_LANG_ID_ACT,
                                                             ZP_FILM_SPEICAL_TYPE_XREF.ZP_EAPI_ID_ACT,
                                                             ZP_LANG_ID_ACT,
                                                             ZP_EAPI_ID_ACT))
                # raise SystemExit
                ZP_FILM_SPEICAL_TYPE_XREF.ZP_LANG_ID_ACT = ZP_LANG_ID_ACT
                ZP_FILM_SPEICAL_TYPE_XREF.ZP_EAPI_ID_ACT = ZP_EAPI_ID_ACT
                commit(session)
        session.close()

    def video_codec(self, **kwargs):
        #zp_lang_id = kwargs['ZP_LANG_ID_REQ']
        session = self.Session()
        zp_vcodec_rslt = session.query(
            TABLES.ZP_VCODEC
        ).join(
            TABLES.ZP_FILM_FILEFOLDER_VIDEO_METADATA,
            TABLES.ZP_FILM_FILEFOLDER_VIDEO_METADATA.ZP_CODEC_ID == TABLES.ZP_VCODEC.ID
        ).join(
            TABLES.ZP_FILM,
            TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER_VIDEO_METADATA.ZP_FILM_FILEFOLDER_ID
        ).filter(
            TABLES.ZP_FILM.ID == kwargs['ZP_ENTITY_ID']
        ).first()
        if hasattr(zp_vcodec_rslt, 'TEMPLATE_IDENTIFIER'):
            template_identifier = zp_vcodec_rslt.TEMPLATE_IDENTIFIER
        else:
            try:
                zp_filmfilefolder_rslt = session.query(
                    TABLES.ZP_FILM_FILEFOLDER
                ).join(
                    TABLES.ZP_FILM,
                    TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER.ID
                ).filter(
                        TABLES.ZP_FILM.ID == kwargs['ZP_ENTITY_ID']
                ).one()
            except orm.exc.NoResultFound:
                template_identifier = ''
            else:
                template_identifier = self.get_diskfilefolder_name(zp_filmfilefolder_rslt.ZP_FILM_FOLDER_TYPE_ID)

        session.close()
        return template_identifier

    def audio_codec(self, **kwargs):
        #zp_lang_id = kwargs['ZP_LANG_ID_REQ']
        session = self.Session()
        zp_acodec_rslt = session.query(
            TABLES.ZP_ACODEC
        ).join(
            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA,
            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_CODEC_ID == TABLES.ZP_ACODEC.ID
        ).join(
            TABLES.ZP_FILM,
            TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_FILM_FILEFOLDER_ID
        ).filter(
            TABLES.ZP_FILM.ID == kwargs['ZP_ENTITY_ID'],
            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_LANG_ID == kwargs['ZP_LANG_ID_REQ']
        ).order_by(
            TABLES.ZP_ACODEC.SCORE.desc(),
            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.TRACK_ID.desc()
        ).first()
        if hasattr(zp_acodec_rslt, 'TEMPLATE_IDENTIFIER'):
            template_identifier = zp_acodec_rslt.TEMPLATE_IDENTIFIER
        else:
            zp_acodec_rslt = session.query(
                TABLES.ZP_ACODEC
            ).join(
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA,
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_CODEC_ID == TABLES.ZP_ACODEC.ID
            ).join(
                TABLES.ZP_FILM,
                TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_FILM_FILEFOLDER_ID
            ).filter(
                TABLES.ZP_FILM.ID == kwargs['ZP_ENTITY_ID'],
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_LANG_ID == 1823
            ).order_by(
                TABLES.ZP_ACODEC.SCORE.desc(),
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.TRACK_ID.desc()
            ).first()
            if hasattr(zp_acodec_rslt, 'TEMPLATE_IDENTIFIER'):
                template_identifier = zp_acodec_rslt.TEMPLATE_IDENTIFIER
            else:
                zp_acodec_rslt = session.query(
                    TABLES.ZP_ACODEC
                ).join(
                    TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA,
                    TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_CODEC_ID == TABLES.ZP_ACODEC.ID
                ).join(
                    TABLES.ZP_FILM,
                    TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID ==
                    TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_FILM_FILEFOLDER_ID
                ).filter(
                    TABLES.ZP_FILM.ID == kwargs['ZP_ENTITY_ID']
                ).order_by(
                    TABLES.ZP_ACODEC.SCORE.desc(),
                    TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.TRACK_ID.desc()
                ).first()
                if hasattr(zp_acodec_rslt, 'TEMPLATE_IDENTIFIER'):
                    template_identifier = zp_acodec_rslt.TEMPLATE_IDENTIFIER
                else:
                    template_identifier = ''
        session.close()
        return template_identifier

    def format(self, **kwargs):
        session = self.Session()
        try:
            zp_filmfilefolder_rslt = session.query(
                TABLES.ZP_FILM_FILEFOLDER
            ).join(
                TABLES.ZP_FILM,
                TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER.ID
            ).filter(
                    TABLES.ZP_FILM.ID == kwargs['ZP_ENTITY_ID']
            ).one()
        except orm.exc.NoResultFound:
            format = 'UNK'
        else:
            zp_film_filefolder_type_id = zp_filmfilefolder_rslt.ZP_FILM_FOLDER_TYPE_ID
            if isinstance(zp_film_filefolder_type_id, int):
                if zp_film_filefolder_type_id == 1:
                    extension = get_file_extension(zp_filmfilefolder_rslt.LAST_PATH).lower()
                    log.trace('extension %s', extension)
                    format = self.get_container_group_name(extension)
                    log.trace('format %s', format)
                else:
                    format = self.get_diskfilefolder_name(zp_film_filefolder_type_id).lower()
            else:
                extension = get_file_extension(zp_filmfilefolder_rslt.LAST_PATH).lower()
                log.trace('extension %s', extension)
                format = self.get_container_group_name(extension)
                log.trace('format %s', format)
            if not format:
                format = ''
        session.close()
        return format

    def video_resolution(self, **kwargs):
        session = self.Session()
        zp_vcodec_rslt = session.query(
            TABLES.ZP_RES
        ).join(
            TABLES.ZP_FILM_FILEFOLDER_SCORE,
            TABLES.ZP_FILM_FILEFOLDER_SCORE.ZP_RES_ID == TABLES.ZP_RES.ID
        ).join(
            TABLES.ZP_FILM,
            TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER_SCORE.ZP_FILM_FILEFOLDER_ID
        ).filter(
            TABLES.ZP_FILM.ID == kwargs['ZP_ENTITY_ID']
        ).first()
        session.close()
        if hasattr(zp_vcodec_rslt, 'RES'):
            template_identifier = zp_vcodec_rslt.RES
        else:
            template_identifier = ''
        return template_identifier

    def aspect_ratio(self, **kwargs):
        session = self.Session()
        zp_vcodec_rslt = session.query(
            TABLES.ZP_FILM_FILEFOLDER_VIDEO_METADATA
        ).join(
            TABLES.ZP_FILM,
            TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER_VIDEO_METADATA.ZP_FILM_FILEFOLDER_ID
        ).filter(
            TABLES.ZP_FILM.ID == kwargs['ZP_ENTITY_ID']
        ).order_by(
            TABLES.ZP_FILM_FILEFOLDER_VIDEO_METADATA.TRACK_ID.asc()
        ).first()
        session.close()
        if hasattr(zp_vcodec_rslt, 'DISPLAY_ASPECT_RATIO'):
            template_identifier_split = zp_vcodec_rslt.DISPLAY_ASPECT_RATIO.split(':')
            if len(template_identifier_split) == 2:
                template_identifier = '%s : %s' % (template_identifier_split[0], template_identifier_split[1])
            else:
                template_identifier = ''
        else:
            template_identifier = ''
        return template_identifier

    def video_frame_rate(self, **kwargs):
        session = self.Session()
        zp_vcodec_rslt = session.query(
            TABLES.ZP_FILM_FILEFOLDER_VIDEO_METADATA
        ).join(
            TABLES.ZP_FILM,
            TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER_VIDEO_METADATA.ZP_FILM_FILEFOLDER_ID
        ).filter(
            TABLES.ZP_FILM.ID == kwargs['ZP_ENTITY_ID']
        ).order_by(
            TABLES.ZP_FILM_FILEFOLDER_VIDEO_METADATA.TRACK_ID.asc()
        ).first()
        session.close()
        if hasattr(zp_vcodec_rslt, 'FRAME_RATE'):
            return zp_vcodec_rslt.FRAME_RATE
        return ''

    def audio_channels(self, **kwargs):
        session = self.Session()
        zp_acodec_rslt = session.query(
            TABLES.ZP_ACODEC,
            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA
        ).join(
            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA,
            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_CODEC_ID == TABLES.ZP_ACODEC.ID
        ).join(
            TABLES.ZP_FILM,
            TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_FILM_FILEFOLDER_ID
        ).filter(
            TABLES.ZP_FILM.ID == kwargs['ZP_ENTITY_ID'],
            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_LANG_ID == kwargs['ZP_LANG_ID_REQ']
        ).order_by(
            TABLES.ZP_ACODEC.SCORE.desc(),
            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.TRACK_ID.desc()
        ).first()
        if hasattr(zp_acodec_rslt, 'ZP_FILM_FILEFOLDER_AUIDO_METADATA'):
            channels = zp_acodec_rslt.ZP_FILM_FILEFOLDER_AUIDO_METADATA.CHANNELS
        else:
            zp_acodec_rslt = session.query(
                TABLES.ZP_ACODEC
            ).join(
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA,
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_CODEC_ID == TABLES.ZP_ACODEC.ID
            ).join(
                TABLES.ZP_FILM,
                TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_FILM_FILEFOLDER_ID
            ).filter(
                TABLES.ZP_FILM.ID == kwargs['ZP_ENTITY_ID'],
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_LANG_ID == 1823
            ).order_by(
                TABLES.ZP_ACODEC.SCORE.desc(),
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.TRACK_ID.desc()
            ).first()
            if hasattr(zp_acodec_rslt, 'ZP_FILM_FILEFOLDER_AUIDO_METADATA'):
                channels = zp_acodec_rslt.ZP_FILM_FILEFOLDER_AUIDO_METADATA.CHANNELS
            else:
                zp_acodec_rslt = session.query(
                    TABLES.ZP_ACODEC
                ).join(
                    TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA,
                    TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_CODEC_ID == TABLES.ZP_ACODEC.ID
                ).join(
                    TABLES.ZP_FILM,
                    TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_FILM_FILEFOLDER_ID
                ).filter(
                    TABLES.ZP_FILM.ID == kwargs['ZP_ENTITY_ID']
                ).order_by(
                    TABLES.ZP_ACODEC.SCORE.desc(),
                    TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.TRACK_ID.desc()
                ).first()
                if hasattr(zp_acodec_rslt, 'ZP_FILM_FILEFOLDER_AUIDO_METADATA'):
                    channels = zp_acodec_rslt.ZP_FILM_FILEFOLDER_AUIDO_METADATA.CHANNELS
                else:
                    channels = 2
        if channels < 1:
            channels = 2
        channels_template_identifer_dict = {
            1: '1.0',
            2: '2.0',
            3: '3.0',
            4: '4.0',
            5: '5.0',
            6: '5.1',
            7: '6.1',
            8: '7.1'
        }
        if channels in channels_template_identifer_dict:
            channels_identifier = channels_template_identifer_dict[channels]
        else:
            channels_identifier = channels_template_identifer_dict[8]
        session.close()
        return channels_identifier

    def audio_language(self, **kwargs):
        session = self.Session()
        zp_acodec_rslt = session.query(
            TABLES.ZP_ACODEC,
            TABLES.ZP_LANG,
            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA
        ).join(
            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA,
            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_CODEC_ID == TABLES.ZP_ACODEC.ID
        ).join(
            TABLES.ZP_LANG,
            TABLES.ZP_LANG.ID == TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_LANG_ID
        ).join(
            TABLES.ZP_FILM,
            TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_FILM_FILEFOLDER_ID
        ).filter(
            TABLES.ZP_FILM.ID == kwargs['ZP_ENTITY_ID'],
            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_LANG_ID == kwargs['ZP_LANG_ID_REQ']
        ).order_by(
            TABLES.ZP_ACODEC.SCORE.desc(),
            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.TRACK_ID.desc()
        ).first()
        if hasattr(zp_acodec_rslt, 'ZP_LANG'):
            ISO_639_Part1 = zp_acodec_rslt.ZP_LANG.ISO_639_Part1
        else:
            zp_acodec_rslt = session.query(
                TABLES.ZP_ACODEC,
                TABLES.ZP_LANG,
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA
            ).join(
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA,
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_CODEC_ID == TABLES.ZP_ACODEC.ID
            ).join(
                TABLES.ZP_LANG,
                TABLES.ZP_LANG.ID == TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_LANG_ID
            ).join(
                TABLES.ZP_FILM,
                TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_FILM_FILEFOLDER_ID
            ).filter(
                TABLES.ZP_FILM.ID == kwargs['ZP_ENTITY_ID'],
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_LANG_ID == 1823
            ).order_by(
                TABLES.ZP_ACODEC.SCORE.desc(),
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.TRACK_ID.desc()
            ).first()
            if hasattr(zp_acodec_rslt, 'ZP_LANG'):
                ISO_639_Part1 = zp_acodec_rslt.ZP_LANG.ISO_639_Part1
            else:
                zp_acodec_rslt = session.query(
                    TABLES.ZP_ACODEC,
                    TABLES.ZP_LANG,
                    TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA
                ).join(
                    TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA,
                    TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_CODEC_ID == TABLES.ZP_ACODEC.ID
                ).join(
                    TABLES.ZP_LANG,
                    TABLES.ZP_LANG.ID == TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_LANG_ID
                ).join(
                    TABLES.ZP_FILM,
                    TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_FILM_FILEFOLDER_ID
                ).filter(
                    TABLES.ZP_FILM.ID == kwargs['ZP_ENTITY_ID']
                ).order_by(
                    TABLES.ZP_ACODEC.SCORE.desc(),
                    TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.TRACK_ID.desc()
                ).first()
                if hasattr(zp_acodec_rslt, 'ZP_LANG'):
                    ISO_639_Part1 = zp_acodec_rslt.ZP_LANG.ISO_639_Part1
                else:
                    ISO_639_Part1 = 'en'
        session.close()
        return ISO_639_Part1

    def subtitle_language(self, **kwargs):
        session = self.Session()
        zp_acodec_rslt = session.query(
            TABLES.ZP_TCODEC,
            TABLES.ZP_LANG,
            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA
        ).join(
            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA,
            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_CODEC_ID == TABLES.ZP_TCODEC.ID
        ).join(
            TABLES.ZP_LANG,
            TABLES.ZP_LANG.ID == TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_LANG_ID
        ).join(
            TABLES.ZP_FILM,
            TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_FILM_FILEFOLDER_ID
        ).filter(
            TABLES.ZP_FILM.ID == kwargs['ZP_ENTITY_ID'],
            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_LANG_ID == kwargs['ZP_LANG_ID_REQ']
        ).order_by(
            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.TRACK_ID.desc()
        ).first()
        if hasattr(zp_acodec_rslt, 'ZP_LANG'):
            ISO_639_Part1 = zp_acodec_rslt.ZP_LANG.ISO_639_Part1
        else:
            zp_acodec_rslt = session.query(
                TABLES.ZP_TCODEC,
                TABLES.ZP_LANG,
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA
            ).join(
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA,
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_CODEC_ID == TABLES.ZP_TCODEC.ID
            ).join(
                TABLES.ZP_LANG,
                TABLES.ZP_LANG.ID == TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_LANG_ID
            ).join(
                TABLES.ZP_FILM,
                TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_FILM_FILEFOLDER_ID
            ).filter(
                TABLES.ZP_FILM.ID == kwargs['ZP_ENTITY_ID'],
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_LANG_ID == 1823
            ).order_by(
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.TRACK_ID.desc()
            ).first()
            if hasattr(zp_acodec_rslt, 'ZP_LANG'):
                ISO_639_Part1 = zp_acodec_rslt.ZP_LANG.ISO_639_Part1
            else:
                zp_acodec_rslt = session.query(
                    TABLES.ZP_TCODEC,
                    TABLES.ZP_LANG,
                    TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA
                ).join(
                    TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA,
                    TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_CODEC_ID == TABLES.ZP_TCODEC.ID
                ).join(
                    TABLES.ZP_LANG,
                    TABLES.ZP_LANG.ID == TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_LANG_ID
                ).join(
                    TABLES.ZP_FILM,
                    TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_FILM_FILEFOLDER_ID
                ).filter(
                    TABLES.ZP_FILM.ID == kwargs['ZP_ENTITY_ID']
                ).order_by(
                    TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.TRACK_ID.desc()
                ).first()
                if hasattr(zp_acodec_rslt, 'ZP_LANG'):
                    ISO_639_Part1 = zp_acodec_rslt.ZP_LANG.ISO_639_Part1
                else:
                    ISO_639_Part1 = 'en'
        session.close()
        return ISO_639_Part1

    def score(self, **kwargs):
        """Get the score value from the db

            Args:
                ZP_FILM_ID (int): the film id

            Returns:
                int: if a result is founnd None if not

        """
        session = self.Session()
        try:
            filefolder_score = session.query(
                TABLES.ZP_FILM_FILEFOLDER_SCORE).filter(
                TABLES.ZP_FILM.ID == kwargs['ZP_ENTITY_ID'],
                TABLES.ZP_FILM_FILEFOLDER_SCORE.ZP_FILM_FILEFOLDER_ID == TABLES.ZP_FILM.ZP_FILM_FILEFOLDER_ID).one()
        except orm.exc.NoResultFound as e:
            log.warning(('Cannot find an entry in ZP_FILM_FILEFOLDER_SCORE with ZP_FILM_ID: {0}').format(
                kwargs['ZP_ENTITY_ID']))
        else:
            session.close()
            return filefolder_score.__dict__
        session.close()
        return None

    def genres(self, **kwargs):
        """Get the genres from the db

            Args:
                ZP_FILM_ID (int): the film id
                | ZP_USER_ID (int): the user id
                | ZP_EAPI_ID (int): the eapi id
                | ZP_LANG_ID (int): the language id

            Returns:
                | string: comma seperated list of Generes or 'No Genre Found' if no result found
                | int: ZP_EAPI_ID_ACT or 0 if no result found
                | int: ZP_LANG_ID_ACT or 0 if no result found

        """
        session = self.Session()
        string = 'No Genre Found'
        ZP_LANG_ID = kwargs['ZP_LANG_ID_REQ']
        for eapi in self.eapi_plugins_access_list:
            try:
                # TODO: change to ZP_FILM_GENRE_LANG
                genres = session.query(
                    TABLES.ZP_GENRE).filter(
                    TABLES.ZP_GENRE.ID.in_(
                        session.query(
                            TABLES.ZP_FILM_GENRE_XREF.ZP_GENRE_ID).filter(
                            TABLES.ZP_FILM_GENRE_XREF.ZP_FILM_ID == kwargs['ZP_ENTITY_ID']))).all()
            except orm.exc.NoResultFound as e:
                log.warning(('Film TITLE for ZP_FILM_ID: {0} cannot be found in db from table ZP_FILM_TITLE').format(
                    kwargs['ZP_ENTITY_ID']))
            else:
                string = ''
                for genre in genres:
                    string += "{0}, ".format(genre.GENRE)
                session.close()
                return string.rstrip(', '), self.eapi_dict[eapi], ZP_LANG_ID
        session.close()
        return string, 0, 0

    def cast(self, **kwargs):
        """Get cast from the db

            Note:
                | # TODO: convert below to make cast order by count in db
                | SELECT ZP_PEOPLE.*, (SELECT COUNT(*) FROM ZP_FILM_ROLE_XREF WHERE ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID = ZP_PEOPLE.ID) AS TOT
                | FROM ZP_PEOPLE
                | where ID in (SELECT ZP_PEOPLE_ID FROM ZP_FILM_ROLE_XREF WHERE ZP_FILM_ID = 1)
                | ORDER BY TOT DESC

            Args:
                | ZP_FILM_ID (int): the film id
                | ZP_USER_ID_ACT (int): the user id
                | ZP_EAPI_ID_ACT (int): the eapi id

            Returns:
                | string: comma seperated list of cast or 'No Cast Found' if no result found
                | int: ZP_EAPI_ID or 0 if no result found

        """
        """
        select *
        from ZP_FILM_ROLE_XREF
        inner join ZP_PEOPLE
        on ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID = ZP_PEOPLE.ID
        inner JOIN 
            (
                SELECT ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID, COUNT(ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID) as "count"
                    FROM ZP_FILM_ROLE_XREF
                    GROUP BY ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID
            ) AS pcount
        ON ZP_PEOPLE.ID = pcount.ZP_PEOPLE_ID
        where ZP_FILM_ROLE_XREF.ZP_FILM_ID = 1900
        and ZP_PEOPLE.ID = ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID
        and ZP_FILM_ROLE_XREF.ZP_ROLE_ID = 1
        order by CASE WHEN ZP_FILM_ROLE_XREF.ROLE_ORDER IS NULL THEN 1 ELSE 0 END, ZP_FILM_ROLE_XREF.ROLE_ORDER asc, pcount.count desc
        ;
        """
        session = self.Session()
        string = 'No Cast Found'
        for eapi in self.eapi_plugins_access_list:
            try:
                # TODO: change to ZP_FILM_GENRE_LANG
                # directors = session.query(
                #    TABLES.ZP_PEOPLE).filter(
                #    TABLES.ZP_PEOPLE.ID.in_(
                #        session.query(
                #            TABLES.ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID).filter(
                #            TABLES.ZP_FILM_ROLE_XREF.ZP_ROLE_ID == 1,
                #            TABLES.ZP_FILM_ROLE_XREF.ZP_FILM_ID == kwargs['ZP_ENTITY_ID']))).all()

                # We want the use the order number if specified by the eapi, if no order numbers order by the count
                # of actors appeaing in all films descending.
                """
                select ZP_PEOPLE.NAME
                from ZP_PEOPLE
                inner join ZP_FILM_ROLE_XREF
                on ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID = ZP_PEOPLE.ID
                inner JOIN 
                    (
                        SELECT ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID, COUNT(ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID) as "count"
                            FROM ZP_FILM_ROLE_XREF
                            GROUP BY ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID
                    ) AS pcount
                ON ZP_PEOPLE.ID = pcount.ZP_PEOPLE_ID
                where ZP_FILM_ROLE_XREF.ZP_FILM_ID = 1965
                and ZP_PEOPLE.ID = ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID
                and ZP_FILM_ROLE_XREF.ZP_ROLE_ID = 1
                order by CASE WHEN ZP_FILM_ROLE_XREF.ROLE_ORDER IS NULL THEN 1 ELSE 0 END, ZP_FILM_ROLE_XREF.ROLE_ORDER asc, pcount.count desc
                ;
                """
                subq = session.query(TABLES.ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID,
                                     func.count(TABLES.ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID).label('pcount')).group_by(
                    TABLES.ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID).subquery()
                cast = session.query(TABLES.ZP_PEOPLE.NAME, subq.c.pcount).join(
                    TABLES.ZP_FILM_ROLE_XREF, TABLES.ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID == TABLES.ZP_PEOPLE.ID).join(
                    subq, subq.c.ZP_PEOPLE_ID == TABLES.ZP_PEOPLE.ID).filter(
                    TABLES.ZP_FILM_ROLE_XREF.ZP_FILM_ID == kwargs['ZP_ENTITY_ID'],
                    TABLES.ZP_FILM_ROLE_XREF.ZP_ROLE_ID == 1,
                ).order_by(case([(TABLES.ZP_FILM_ROLE_XREF.ROLE_ORDER == None, 1)], else_=0),
                          TABLES.ZP_FILM_ROLE_XREF.ROLE_ORDER.asc(), subq.c.pcount.desc())

            except orm.exc.NoResultFound:
                log.warning(('Film TITLE for ZP_FILM_ID: {0} cannot be found in db from table ZP_FILM_TITLE').format(
                    kwargs['ZP_ENTITY_ID']))
            else:
                string = ''
                for person in cast:
                    string += "{0}, ".format(person.NAME)
                session.close()
                #raise SystemExit
                return string.rstrip(', '), self.eapi_dict[eapi]
        session.close()
        return string, 0

    def rating(self, **kwargs):
        """Get cast from the db

            Args:
                | ZP_FILM_ID (int): the film id
                | ZP_USER_ID (int): the user id
                | ZP_EAPI_ID (int): the eapi id

            Returns:
                | int: RATING or 0 if no result found
                | int: ZP_EAPI_ID_ACT or 0 if no result found

        """
        session = self.Session()
        # TODO: What to do when there is no rating
        RATING = 0
        for eapi in self.eapi_plugins_access_list:
            try:
                # TODO: change to ZP_FILM_GENRE_LANG
                RATING = session.query(TABLES.ZP_FILM_RATING).filter(
                    TABLES.ZP_FILM_RATING.ZP_FILM_ID == kwargs['ZP_ENTITY_ID']).one().RATING
            except orm.exc.NoResultFound as e:
                log.warning(('Film RATING for ZP_FILM_ID: {0} cannot be found in db from table ZP_FILM_RATING').format(
                    kwargs['ZP_ENTITY_ID']))
            else:
                session.close()
                return RATING, self.eapi_dict[eapi]
        session.close()
        return RATING, 0

    def directors(self, **kwargs):
        """Get directors from the db

            Args:
                | ZP_FILM_ID (int): the film id
                | ZP_USER_ID (int): the user id
                | ZP_EAPI_ID (int): the eapi id

            Returns:
                | string: comma seperated list of directors or 'No Director(s) Found' if no result found
                | int: ZP_EAPI_ID_ACT or 0 if no result found

        """
        session = self.Session()
        string = 'No Director(s) Found'
        for eapi in self.eapi_plugins_access_list:
            try:
                # TODO: change to ZP_FILM_GENRE_LANG
                directors = session.query(
                    TABLES.ZP_PEOPLE).filter(
                    TABLES.ZP_PEOPLE.ID.in_(
                        session.query(
                            TABLES.ZP_FILM_ROLE_XREF.ZP_PEOPLE_ID).filter(
                            TABLES.ZP_FILM_ROLE_XREF.ZP_ROLE_ID == 2,
                            TABLES.ZP_FILM_ROLE_XREF.ZP_FILM_ID == kwargs['ZP_ENTITY_ID']))).all()

            except orm.exc.NoResultFound as e:
                log.warning(('Film TITLE for ZP_FILM_ID: {0} cannot be found in db from table ZP_FILM_TITLE').format(
                    kwargs['ZP_ENTITY_ID']))
            else:
                string = ''
                for person in directors:
                    string += "{0}, ".format(person.NAME)
                session.close()
                return string.rstrip(', '), self.eapi_dict[eapi]
        session.close()
        return string, 0

    def overview(self, **kwargs):
        """Get the overview from the db

            Args:
                | ZP_FILM_ID (int): the film id
                | ZP_USER_ID (int): the user id
                | ZP_EAPI_ID (int): the eapi id
                | ZP_LANG_ID (int): the language id

            Returns:
                | string: overview or 'No Overview Found' if no result found
                | int: ZP_EAPI_ID_ACT or 0 if no result found
                | int: ZP_LANG_ID_ACT or 0 if no result found

        """
        session = self.Session()
        TITLE = 'No Overview Found'
        try:
            ZP_FILM_OVERVIEW = session.query(
                TABLES.ZP_FILM_OVERVIEW).filter(
                TABLES.ZP_FILM_OVERVIEW.ZP_FILM_ID == kwargs['ZP_ENTITY_ID'],
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == TABLES.ZP_FILM_OVERVIEW.ZP_FILM_ID,
                TABLES.ZP_FILM_OVERVIEW.ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == kwargs['ZP_USER_ID'],
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 2
            ).one()
        except orm.exc.NoResultFound as e:
            log.warning(('Film OVERVIEW for ZP_FILM_ID: {0} cannot be found in db from table ZP_FILM_TITLE').format(
                kwargs['ZP_ENTITY_ID']))
        else:
            session.close()
            return ZP_FILM_OVERVIEW.OVERVIEW, ZP_FILM_OVERVIEW.ID
        session.close()
        return TITLE, 0

    def title(self, **kwargs):
        """Get the Title from the db

            Args:
                | ZP_FILM_ID (int): the film id
                | ZP_USER_ID (int): the user id
                | ZP_EAPI_ID (int): the eapi id

            Returns:
                | string: Title or 'No Title Found' if no result found
                | int: ZP_EAPI_ID_ACT or 0 if no result found

        """
        session = self.Session()
        TITLE = 'No Title Found'
        try:
            ZP_FILM_TITLE = session.query(
                TABLES.ZP_FILM_TITLE).filter(
                TABLES.ZP_FILM_TITLE.ZP_FILM_ID == kwargs['ZP_ENTITY_ID'],
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ID == TABLES.ZP_FILM_TITLE.ZP_FILM_ID,
                TABLES.ZP_FILM_TITLE.ID == TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_ID,
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_USER_ID == kwargs['ZP_USER_ID'],
                TABLES.ZP_USER_FILM_ENTITY_XREF.ZP_FILM_ENTITY_TYPE_ID == 1
            ).one()
        except orm.exc.NoResultFound as e:
            log.warning(('Film TITLE for ZP_FILM_ID: {0} cannot be found in db from table ZP_FILM_TITLE').format(
                kwargs['ZP_ENTITY_ID']))
        else:
            session.close()
            return ZP_FILM_TITLE.TITLE, ZP_FILM_TITLE.ID
        session.close()
        return TITLE, 0

    def year(self, **kwargs):
        """Get the year from the db

            Args:
                | ZP_FILM_ID (int): the film id
                | ZP_USER_ID (int): the user id
                | ZP_EAPI_ID (int): the eapi id

            Returns:
                | int: year or 0000 if no result found
                | int: ZP_EAPI_ID_ACT or 0 if no result found

        """
        session = self.Session()
        YEAR = 0000
        for eapi in self.eapi_plugins_access_list:
            try:
                YEAR = session.query(
                    TABLES.ZP_FILM_RELEASE).filter(
                    TABLES.ZP_FILM_RELEASE.ZP_FILM_ID == kwargs['ZP_ENTITY_ID']).one().RELEASE_DATE.year
            except orm.exc.NoResultFound as e:
                log.warning(
                    ('Film RELEASE_DATE for ZP_FILM_ID: {0} cannot be found in db from table ZP_FILM_RELEASE').format(
                        kwargs['ZP_ENTITY_ID']))
            else:
                session.close()
                return YEAR, self.eapi_dict[eapi]
        return YEAR, 0

    def runtime(self, **kwargs):
        """Get the runtime from the db

            Args:
                | ZP_FILM_ID (int): the film id
                | ZP_USER_ID (int): the user id
                | ZP_EAPI_ID (int): the eapi id

            Returns:
                | int: runtime or 000 if no result found
                | int: ZP_EAPI_ID_ACT or 0 if no result found

        """
        session = self.Session()
        RUNTIME = 000
        for eapi in self.eapi_plugins_access_list:
            try:
                RUNTIME = session.query(
                    TABLES.ZP_FILM_RUNTIME).filter(
                    TABLES.ZP_FILM_RUNTIME.ZP_FILM_ID == kwargs['ZP_ENTITY_ID']).one().RUNTIME
            except orm.exc.NoResultFound as e:
                log.warning((
                    'Film RELEASE_DATE for ZP_FILM_RUNTIME: {0} cannot be found in db from table ZP_FILM_RELEASE').format(
                    kwargs['ZP_ENTITY_ID']))
            else:
                session.close()
                return str(RUNTIME), self.eapi_dict[eapi]
        session.close()
        return RUNTIME, 0
