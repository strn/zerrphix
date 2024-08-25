# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import copy
import logging
import sys

from sqlalchemy import func, orm

from datetime import datetime
from datetime import timedelta
from zerrphix.db import commit
from zerrphix.db.tables import TABLES
from zerrphix.plugin import load_plugins
from zerrphix.tv.util import update_tv_last_mod
from zerrphix.util.eapi import gather_eids
from zerrphix.util.plugin import create_eapi_plugins_list, create_eapi_dict
from zerrphix.util.text import date_time
#from zerrphix.util import set_retry, check_can_retry
#from types import MethodType
from zerrphix.tv.base import TVBase
log = logging.getLogger(__name__)


class EidGather(TVBase):
    """Get Data for tvs (actors, runtime, synop etc...)
    """

    def __init__(self, **kwargs):
        """Data __init__

            Args:
                | args (list): Passed through args from the command line.
                | Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.
        """
        super(EidGather, self).__init__(**kwargs)
        self, self.eapi_plugins_access_list, loaded_plugins = create_eapi_plugins_list(
            'tv', sys.modules, load_plugins(self.args), self)
        if not self.eapi_plugins_access_list:
            raise Exception(('There not any entries in eapi_plugins_access_list'
                             ' therefore scanning is pointless'))
        session = self.Session()
        self.eapi_dict = create_eapi_dict(session)
        self.library = 'tv'
        #self.set_retry = MethodType(set_retry, self)
        #self.check_can_retry = MethodType(check_can_retry, self)
        session.close()

    def gather(self):
        eapi_dict = {}
        eapi_dict['checked'] = {}
        eapi_dict['looked_up'] = {}
        eapi_dict['init'] = {}
        eapi_dict['to_get'] = {}
        eapi_dict['used'] = []
        session = self.Session()

        eapi_sources = session.query(
            TABLES.ZP_EAPI.NAME
        ).filter(
            TABLES.ZP_EAPI_LIBRARY_XREF.ZP_EAPI_ID == TABLES.ZP_EAPI.ID,
            TABLES.ZP_LIBRARY.DESC == self.library.upper(),
            TABLES.ZP_EAPI_LIBRARY_XREF.ZP_LIBRARY_ID == TABLES.ZP_LIBRARY.ID,
            TABLES.ZP_EAPI.SOURCE == 1
        ).all()
        for eapi_source in eapi_sources:
            # print(eapi_source.NAME)
            eapi_source_name = eapi_source.NAME
            if hasattr(self, eapi_source_name):
                eapi_dict['init'][eapi_source_name] = getattr(self, eapi_source_name)
            eapi_dict['looked_up'][eapi_source_name] = []

        eapi_lookups = session.query(TABLES.ZP_EAPI.NAME).filter(
            TABLES.ZP_EAPI_LIBRARY_XREF.ZP_EAPI_ID == TABLES.ZP_EAPI.ID,
            TABLES.ZP_LIBRARY.DESC == self.library.upper(),
            TABLES.ZP_EAPI_LIBRARY_XREF.ZP_LIBRARY_ID == TABLES.ZP_LIBRARY.ID,
            TABLES.ZP_EAPI.LOOKUP == 1).all()

        eapi_lookup_count = 0
        for eapi_lookup in eapi_lookups:
            eapi_lookup_name = eapi_lookup.NAME
            eapi_dict['to_get'][eapi_lookup_name] = None
            eapi_dict['checked'][eapi_lookup_name] = []
            eapi_lookup_count += 1
        self.eapi_lookup_count = eapi_lookup_count

        # TODO change lookup to per library not general
        # TODO Limit the number of retries
        # print(eapi_dict)
        if eapi_lookup_count > 0 and eapi_dict['to_get'] and eapi_dict['checked'] and eapi_dict['init']:
            processing_complete = False
            max_ZP_TV_ID = session.query(func.max(TABLES.ZP_TV.ID)).one()[0]
            session.close()
            if isinstance(max_ZP_TV_ID, int):
                ZP_TV_ID = max_ZP_TV_ID + 1
                while processing_complete == False:
                    session = self.Session()
                    qry_tv_ids = session.query(TABLES.ZP_TV_EAPI_EID.ZP_TV_ID,
                                               func.count(TABLES.ZP_TV_EAPI_EID.ZP_TV_ID).label(
                                                   'ZP_TV_ID_COUNT')).filter(
                        TABLES.ZP_EAPI.ID == TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID,
                        TABLES.ZP_EAPI.LOOKUP == 1,
                        TABLES.ZP_TV_EAPI_EID.ZP_TV_ID < ZP_TV_ID,
                        ~TABLES.ZP_TV_EAPI_EID.ZP_TV_ID.in_(session.query(
                            TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                            TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 6,
                            TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == 1
                        ))
                    ).group_by(
                        TABLES.ZP_TV_EAPI_EID.ZP_TV_ID).having(
                        func.count(TABLES.ZP_TV_EAPI_EID.ZP_TV_ID) < eapi_lookup_count)
                    # for unidenttified_filefolder in _yield_limit(qry_unidentified_filefolder, TABLES.ZP_TV_FILEFOLDER.ID, maxrq=100, order='desc'):
                    qry_tv_ids_count = qry_tv_ids.count()
                    if qry_tv_ids_count > 0:
                        tv_ids = qry_tv_ids.order_by(TABLES.ZP_TV_EAPI_EID.ZP_TV_ID.desc()).limit(30)
                        # if any(char.isdigit() for char in ZP_TV_FILEFOLDER.LAST_PATH):
                        # if ZP_TV_FILEFOLDER.LAST_PATH not in ['W1A', '''That 70's Show''', 'Stargate SG-1']:
                        tv_id_processing_list = []
                        for tv_id in tv_ids:
                            # print(tv_id.ZP_TV_ID, tv_id.ZP_TV_ID_COUNT)
                            tv_id_processing_list.append(tv_id.ZP_TV_ID)
                        session.close()
                        for _id in tv_id_processing_list:
                            ZP_TV_ID = _id
                            self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                 11,
                                                                 'Gathering EID\'S: TV %s/%s' %
                                                                 (ZP_TV_ID, max_ZP_TV_ID))
                            # log.warning()
                            # tv_eapi_dict = {}
                            # for key in eapi_dict:
                            # tv_eapi_dict[key] = eapi_dict[key]
                            tv_eapi_dict = copy.deepcopy(eapi_dict)
                            log.debug('ZP_TV_ID %s tv_eapi_dict %s', ZP_TV_ID, tv_eapi_dict)

                            session = self.Session()
                            have_eids = session.query(TABLES.ZP_TV_EAPI_EID).filter(
                                TABLES.ZP_TV_EAPI_EID.ZP_TV_ID == ZP_TV_ID).all()

                            for have_eid in have_eids:
                                tv_eapi_dict['to_get'][self.eapi_dict['id'][have_eid.ZP_EAPI_ID]] = have_eid.ZP_EAPI_EID

                            log.debug('''from db tv_eapi_dict['to_get'] %s ZP_TV_ID %s''', tv_eapi_dict['to_get'],
                                      ZP_TV_ID)
                            eapi_to_get_missing_list = []
                            for eapi_to_get in tv_eapi_dict['to_get']:
                                if tv_eapi_dict['to_get'][eapi_to_get] is None:
                                    eapi_to_get_missing_list.append(eapi_to_get)
                            # log.warning('')
                            # print(tv_eapi_dict['to_get'])
                            # print(eapi_to_get_missing_list)
                            log.debug('eapi_to_get_missing_list %s ZP_TV_ID %s', eapi_to_get_missing_list, ZP_TV_ID)
                            if eapi_to_get_missing_list:
                                log.debug('pre gather: tv_eapi_dict %s ZP_TV_ID %s', tv_eapi_dict, ZP_TV_ID)
                                tv_eapi_dict = gather_eids(tv_eapi_dict, self.library)
                                log.debug('post gather tv_eapi_dict %s ZP_TV_ID %s', tv_eapi_dict, ZP_TV_ID)
                                for eapi_to_get_missing in eapi_to_get_missing_list:
                                    if tv_eapi_dict['to_get'][eapi_to_get_missing] is not None:
                                        self.add_eapi_eid(ZP_TV_ID, self.eapi_dict['name'][eapi_to_get_missing],
                                                          tv_eapi_dict['to_get'][eapi_to_get_missing])
                                        # print(tv_eapi_dict['to_get'])
                            else:
                                log.error('eapi_to_get_missing_list is empty %s. Should not be trying to get eids'
                                            ' if we allready have them for ZP_TV_ID: %s', eapi_to_get_missing_list,
                                            ZP_TV_ID)
                            if self.check_film_missing_eid(ZP_TV_ID) is True:
                                self.set_retry(1, 6, ZP_TV_ID)
                            # time.sleep(5)
                            # raise SystemExit
                            # for eapi_source in eapi_dict['init']:
                            # print(eapi_source)
                    else:
                        processing_complete = True
                        session.close()
                if self.check_can_retry(1) is True:
                    log.debug('Retrying TV EID Gather')
                    processing_complete = False
                    ZP_TV_ID = max_ZP_TV_ID + 1
                    while processing_complete == False:
                        session = self.Session()
                        qry_tv_ids = session.query(TABLES.ZP_TV_EAPI_EID.ZP_TV_ID,
                                                   func.count(TABLES.ZP_TV_EAPI_EID.ZP_TV_ID).label(
                                                       'ZP_TV_ID_COUNT'),
                                                   TABLES.ZP_RETRY_COUNT.DELAY,
                                                   TABLES.ZP_RETRY.DATETIME, TABLES.ZP_RETRY.COUNT
                                                   ).filter(
                            TABLES.ZP_EAPI.ID == TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID,
                            TABLES.ZP_EAPI.LOOKUP == 1,
                            TABLES.ZP_TV_EAPI_EID.ZP_TV_ID < ZP_TV_ID,
                            TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == TABLES.ZP_RETRY_COUNT.ZP_RETRY_TYPE_ID,
                            TABLES.ZP_TV_EAPI_EID.ZP_TV_ID == TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID,
                            TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 6,
                            TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == 1,
                            TABLES.ZP_RETRY_COUNT.COUNT == session.query(
                                func.max(TABLES.ZP_RETRY_COUNT.COUNT)
                            ).filter(
                                TABLES.ZP_RETRY.COUNT >= TABLES.ZP_RETRY_COUNT.COUNT).order_by(
                                TABLES.ZP_RETRY_COUNT.COUNT.desc()).correlate(TABLES.ZP_RETRY).as_scalar()
                        ).group_by(
                            TABLES.ZP_TV_EAPI_EID.ZP_TV_ID).having(
                            func.count(TABLES.ZP_TV_EAPI_EID.ZP_TV_ID) < eapi_lookup_count)
                        # for unidenttified_filefolder in _yield_limit(qry_unidentified_filefolder, TABLES.ZP_TV_FILEFOLDER.ID, maxrq=100, order='desc'):
                        qry_tv_ids_count = qry_tv_ids.count()
                        if qry_tv_ids_count > 0:
                            tv_ids = qry_tv_ids.order_by(TABLES.ZP_TV_EAPI_EID.ZP_TV_ID.desc()).limit(30)
                            # if any(char.isdigit() for char in ZP_TV_FILEFOLDER.LAST_PATH):
                            # if ZP_TV_FILEFOLDER.LAST_PATH not in ['W1A', '''That 70's Show''', 'Stargate SG-1']:
                            tv_id_processing_list = []
                            for tv_id in tv_ids:
                                # print(tv_id.ZP_TV_ID, tv_id.ZP_TV_ID_COUNT)
                                tv_id_processing_list.append({'ZP_TV_ID':tv_id.ZP_TV_ID,
                                                              'DELAY': tv_id.DELAY,
                                                              'DATETIME': tv_id.DATETIME,
                                                              'COUNT': tv_id.COUNT})
                            session.close()
                            for _id in tv_id_processing_list:
                                ZP_TV_ID = _id['ZP_TV_ID']
                                if _id['DATETIME'] + timedelta(
                                    days=_id['DELAY']) <= datetime.now():
                                    log.debug('dt %s, plus %s is %s which is less than than now %s',
                                              '{:%Y-%m-%d %H:%M:%S}'.format(_id['DATETIME']),
                                    _id['DELAY'],
                                              '{:%Y-%m-%d %H:%M:%S}'.format(_id['DATETIME'] + timedelta(
                                                  days=_id['DELAY'])), '{:%Y-%m-%d %H:%M:%S}'.format(datetime.now()))

                                    # log.warning()
                                    # tv_eapi_dict = {}
                                    # for key in eapi_dict:
                                    # tv_eapi_dict[key] = eapi_dict[key]
                                    tv_eapi_dict = copy.deepcopy(eapi_dict)
                                    log.debug('ZP_TV_ID %s tv_eapi_dict %s', ZP_TV_ID, tv_eapi_dict)

                                    session = self.Session()
                                    have_eids = session.query(TABLES.ZP_TV_EAPI_EID).filter(
                                        TABLES.ZP_TV_EAPI_EID.ZP_TV_ID == ZP_TV_ID).all()

                                    for have_eid in have_eids:
                                        tv_eapi_dict['to_get'][self.eapi_dict['id'][have_eid.ZP_EAPI_ID]] = have_eid.ZP_EAPI_EID

                                    log.debug('''from db tv_eapi_dict['to_get'] %s ZP_TV_ID %s''', tv_eapi_dict['to_get'],
                                              ZP_TV_ID)
                                    eapi_to_get_missing_list = []
                                    for eapi_to_get in tv_eapi_dict['to_get']:
                                        if tv_eapi_dict['to_get'][eapi_to_get] is None:
                                            eapi_to_get_missing_list.append(eapi_to_get)
                                    # log.warning('')
                                    # print(tv_eapi_dict['to_get'])
                                    # print(eapi_to_get_missing_list)
                                    log.debug('eapi_to_get_missing_list %s ZP_TV_ID %s', eapi_to_get_missing_list, ZP_TV_ID)
                                    if eapi_to_get_missing_list:
                                        log.debug('pre gather: tv_eapi_dict %s ZP_TV_ID %s', tv_eapi_dict, ZP_TV_ID)
                                        tv_eapi_dict = gather_eids(tv_eapi_dict, self.library)
                                        log.debug('post gather tv_eapi_dict %s ZP_TV_ID %s', tv_eapi_dict, ZP_TV_ID)
                                        for eapi_to_get_missing in eapi_to_get_missing_list:
                                            if tv_eapi_dict['to_get'][eapi_to_get_missing] is not None:
                                                self.add_eapi_eid(ZP_TV_ID, self.eapi_dict['name'][eapi_to_get_missing],
                                                                  tv_eapi_dict['to_get'][eapi_to_get_missing])
                                                # print(tv_eapi_dict['to_get'])
                                    else:
                                        log.error('eapi_to_get_missing_list is empty %s. Should not be trying to get eids'
                                                    ' if we allready have them for ZP_TV_ID: %s', eapi_to_get_missing_list,
                                                    ZP_TV_ID)
                                        #raise SystemExit
                                    tv_eapi_dict = None
                                    # time.sleep(5)
                                    # raise SystemExit
                                    # for eapi_source in eapi_dict['init']:
                                    # print(eapi_source)
                                else:
                                    log.debug('dt %s, plus %s is %s which is not less than now %s',
                                              '{:%Y-%m-%d %H:%M:%S}'.format(_id['DATETIME']),
                                    _id['DELAY'],
                                              '{:%Y-%m-%d %H:%M:%S}'.format(_id['DATETIME'] + timedelta(
                                                  days=_id['DELAY'])), '{:%Y-%m-%d %H:%M:%S}'.format(datetime.now()))
                        else:
                            processing_complete = True
                            session.close()

    def check_film_missing_eid(self, ZP_TV_ID):
        session = self.Session()
        try:
            session.query(TABLES.ZP_TV_EAPI_EID.ZP_TV_ID,
                                       func.count(TABLES.ZP_TV_EAPI_EID.ZP_TV_ID).label(
                                           'ZP_TV_ID_COUNT')).filter(
                TABLES.ZP_EAPI.ID == TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID,
                TABLES.ZP_EAPI.LOOKUP == 1,
                TABLES.ZP_TV_EAPI_EID.ZP_TV_ID == ZP_TV_ID,
                ~TABLES.ZP_TV.ID.in_(session.query(
                    TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                    TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 6
                ))
            ).group_by(
                TABLES.ZP_TV_EAPI_EID.ZP_TV_ID).having(
                func.count(TABLES.ZP_TV_EAPI_EID.ZP_TV_ID) < self.eapi_lookup_count)
        except orm.exc.NoResultFound:
            session.close()
            return False
        except orm.exc.MultipleResultsFound as e:
            log.error('should not get multiple results - raise to development')
            session.close()
            return True
        else:
            session.close()
            return True

    def add_eapi_eid(self, ZP_TV_ID, ZP_EAPI_ID, ZP_EAPI_EID):
        # print(locals())
        session = self.Session()
        add_ZP_TV_EAPI_EID = TABLES.ZP_TV_EAPI_EID(ZP_TV_ID=ZP_TV_ID,
                                                   ZP_EAPI_ID=ZP_EAPI_ID,
                                                   ZP_EAPI_EID=ZP_EAPI_EID)
        log.debug('adding ZP_TV_ID %s ZP_EAPI_ID %s ZP_EAPI_EID %s to ZP_TV_EAPI_EID',
                  ZP_TV_ID, ZP_EAPI_ID, ZP_EAPI_EID)
        session.add(add_ZP_TV_EAPI_EID)
        commit(session)
        update_tv_last_mod(self.Session, ZP_TV_ID)
        session.close()
        # raise SystemExit
