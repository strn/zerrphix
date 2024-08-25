from __future__ import unicode_literals, division, absolute_import, print_function

from sqlalchemy import orm

from zerrphix.db import commit
import zerrphix.template
from zerrphix.db.tables import TABLES
from zerrphix.util.text import date_time
import logging
import time
#from zerrphix.util import smbfs_connection_dict_dune
#from zerrphix.util.db import DBCommon
from zerrphix.util.filesystem import make_dir
from zerrphix.util.filesystem import smbfs
from datetime import datetime, timedelta
from zerrphix.util.plugin import create_eapi_dict
import re
import traceback
from sqlalchemy import func, orm
from zerrphix.constants import military_time_regex
import os
from zerrphix.util.extra import AESCipher
from zerrphix.util.extra import z
from zerrphix.util import time_run_between
from six import string_types
from zerrphix.util.text import xml_to_dict
from zerrphix.util.text import all_keys_in_dict
from datetime import datetime

log = logging.getLogger(__name__)

class Base(object):
    def __init__(self, args, Session, global_config_dict, library_config_dict):
        self.args = args
        self.Session = Session
        self.global_config_dict = global_config_dict
        self.library_config_dict = library_config_dict
        self.image_sub_type_dict_by_id = {1: '',
                                          2: '_sel',
                                          3: '_watched',
                                          4: '_watched_sel'}

    def zp_lang_from_text(self, lang_text):
        iso_lang_type_list = [
            'ISO_639_Part1',
            'ISO_639_Part3',
            'Native_Ref_Name',
            'Ref_Name',
            'ISO_639_Part2T',
            'ISO_639_Part2B',
            'ISO_639_Part3_obs1',
        ]
        session = self.Session()
        for iso_lang_type in iso_lang_type_list:
            zp_lang_result = session.query(
                TABLES.ZP_LANG
            ).filter(
                func.lower(getattr(TABLES.ZP_LANG, iso_lang_type)) == lang_text
            ).first()
            if zp_lang_result is not None:
                log.debug('F lang_text %s found against %s which is %s, ref_name %s', lang_text,
                          iso_lang_type, zp_lang_result.ID, zp_lang_result.Ref_Name)
                return zp_lang_result.ID
            else:
                log.debug('NF lang_text %s not found against %s', lang_text, iso_lang_type)
        return None

    def user_film_title_type_order(self, ZP_USER_ID):
        return_list = []
        session = self.Session()
        try:
            user_ZP_FILM_TITLE_TYPE_ID = session.query(
                TABLES.ZP_USER_FILM_TITLE_TYPE_PREF
            ).filter(
                TABLES.ZP_USER_FILM_TITLE_TYPE_PREF.ZP_USER_ID == ZP_USER_ID
            ).one().ZP_FILM_TITLE_TYPE_ID
        except orm.exc.NoResultFound:
            # TODO: get this from DB
            return_list.append(1)
        else:
            return_list.append(user_ZP_FILM_TITLE_TYPE_ID)
        session.close()

        # TODO: get this from DB
        ZP_FILM_TITLE_TYPE_list = [1, 2]

        for ZP_FILM_TITLE_TYPE_ID in ZP_FILM_TITLE_TYPE_list:
            if ZP_FILM_TITLE_TYPE_ID not in return_list:
                return_list.append(ZP_FILM_TITLE_TYPE_ID)
        return return_list

    def get_user_library_langs(self, zp_library_id, zp_user_id):
        return_list = []
        session = self.Session()
        try:
            ZP_LANG_ID = session.query(
                TABLES.ZP_USER_LIBRARY_LANG
            ).filter(
                TABLES.ZP_USER_LIBRARY_LANG.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_LIBRARY_LANG.ZP_LIBRARY_ID == zp_library_id
            ).one().ZP_LANG_ID
        except:
            pass
        else:
            return_list.append(ZP_LANG_ID)
        session.close()
        # TODO: User choice on use eng algn default
        if 1823 not in return_list:
            return_list.append(1823)
        return return_list

    def user_library_eapi_order(self, zp_library_id, zp_user_id):
        session = self.Session()
        return_list = []
        uesr_eapi_order = session.query(
            TABLES.ZP_USER_EAPI_PREF
        ).filter(
            TABLES.ZP_USER_EAPI_PREF.ZP_EAPI_ID.in_(
                session.query(
                    TABLES.ZP_EAPI.ID
                )
            ),
            TABLES.ZP_USER_EAPI_PREF.ZP_LIBRARY_ID == zp_library_id,
            TABLES.ZP_USER_EAPI_PREF.ZP_USER_ID == zp_user_id
        ).order_by(
            TABLES.ZP_USER_EAPI_PREF.ORDER.asc()
        ).all()

        all_eapi = session.query(
            TABLES.ZP_EAPI_LIBRARY_XREF.ZP_EAPI_ID
        ).filter(
            TABLES.ZP_EAPI_LIBRARY_XREF.ZP_LIBRARY_ID == zp_library_id
        ).all()
        session.close()
        for eapi_order in uesr_eapi_order:
            return_list.append(eapi_order.ZP_EAPI_ID)
        for eapi in all_eapi:
            if eapi.ZP_EAPI_ID not in return_list:
                return_list.append(eapi.ZP_EAPI_ID)
        return return_list

    def user_prefs(self, zp_library_id, zp_user_id):
        eapi_order = self.user_library_eapi_order(zp_library_id, zp_user_id)
        title_type_order = self.user_film_title_type_order(zp_user_id)
        lang_list = self.get_user_library_langs(zp_library_id, zp_user_id)
        return eapi_order, title_type_order, lang_list

    def get_extension_list(self, zp_library_id, ignored=0):
        return_list = []
        session = self.Session()
        qry_extensions = session.query(
            TABLES.ZP_FILE_EXTENSION).filter(
            TABLES.ZP_FILE_EXTENSION.ID.in_(
                session.query(
                    TABLES.ZP_LIBRARY_FILE_EXTENSION.ZP_FILE_EXTENSION_ID
                ).filter(
                    TABLES.ZP_LIBRARY_FILE_EXTENSION.ZP_LIBRARY_ID == zp_library_id,
                    TABLES.ZP_LIBRARY_FILE_EXTENSION.IGNORE_EXTENSION == ignored)
            )
        )
        session.close()
        for extension in qry_extensions.all():
            return_list.append(extension.EXTENSION)
        return return_list

    def construct_user_dict(self):
        return_dict = {}
        session = self.Session()
        rslt_all_users = session.query(TABLES.ZP_USER).all()
        for user in rslt_all_users:
            return_dict[user.ID] = user.USERNAME
        session.close()
        return return_dict

    def eapi_eid_from_zp_film_id(self, eapi_id, zp_film_id):
        """Get eapi_id from zp_film_id

            Args:
                | eapi_id (int): 0
                | zp_film_id (int): 0
        """
        session = self.Session()
        ZP_EAPI_EID = None
        try:
            ZP_EAPI_EID = session.query(TABLES.ZP_FILM_EAPI_EID).filter(
                TABLES.ZP_FILM_EAPI_EID.ZP_FILM_ID == zp_film_id,
                TABLES.ZP_FILM_EAPI_EID.ZP_EAPI_ID == eapi_id).one().ZP_EAPI_EID
        except orm.exc.NoResultFound:
            log.warning(
                'ZP_FILM_ID: {0} with eapi_id {1} not in ZP_FILM_EAPI_EID'.format(
                    zp_film_id,
                    eapi_id))
        session.close()
        return ZP_EAPI_EID

    def add_process_running_history(self, zp_library_id, zp_process_id, process, process_state):
        # keep a history of what happened when for debug purposes
        session = self.Session()
        count = session.query(TABLES.ZP_PROCESS_RUNNING_HISTORY).filter(
            TABLES.ZP_PROCESS_RUNNING_HISTORY.ZP_LIBRARY_ID == zp_library_id
        ).count()
        # limit how much history is kept (max last 5000 per library)
        if count > 5000:
            try:
                date_500 = session.query(TABLES.ZP_PROCESS_RUNNING_HISTORY).filter(
                    TABLES.ZP_PROCESS_RUNNING_HISTORY.ZP_LIBRARY_ID == zp_library_id,
                ).order_by(
                    TABLES.ZP_PROCESS_RUNNING_HISTORY.EPOCH.desc()
                ).limit(1).offset(4000).one()
            #log.debug('date_500.ID %s - %s', date_500.ID, zp_library_id)
            except orm.exc.NoResultFound:
                pass
            else:
                session.query(
                    TABLES.ZP_PROCESS_RUNNING_HISTORY
                ).filter(
                    TABLES.ZP_PROCESS_RUNNING_HISTORY.ZP_LIBRARY_ID == zp_library_id,
                    TABLES.ZP_PROCESS_RUNNING_HISTORY.EPOCH < date_500.EPOCH
                ).delete(synchronize_session=False)
                commit(session)
        session.close()
        session = self.Session()
        add_zp_process_running_history = TABLES.ZP_PROCESS_RUNNING_HISTORY(
            EPOCH='{:0.8f}'.format((datetime.now() - datetime.utcfromtimestamp(0)).total_seconds()),
            ZP_LIBRARY_ID=zp_library_id,
            ZP_PROCESS_ID=zp_process_id,
            PROCESS=process,
            PROCESS_STATE=process_state,
            COUNT=0,
            PROCESS_STATE_DATETIME=date_time(),
            PROCESS_STATE_INITIAL_DATETIME=date_time()
        )
        try:
            process_history = session.query(TABLES.ZP_PROCESS_RUNNING_HISTORY).filter(
                TABLES.ZP_PROCESS_RUNNING_HISTORY.ZP_LIBRARY_ID == zp_library_id
            ).order_by(
                TABLES.ZP_PROCESS_RUNNING_HISTORY.PROCESS_STATE_DATETIME.desc()
            ).limit(1).one()
        except orm.exc.NoResultFound:
            session.add(add_zp_process_running_history)
        else:
            if process_history.ZP_PROCESS_ID == zp_process_id and \
                process_history.PROCESS == process and \
                process_history.PROCESS_STATE == process_state:
                process_history.COUNT = process_history.COUNT + 1
                process_history.PROCESS_STATE_DATETIME = date_time()
            else:
                session.add(add_zp_process_running_history)
        commit(session)
        session.close()

    def set_current_library_process_desc(self, zp_library_id, zp_process_id, process, process_state):
        session = self.Session()
        session.query(TABLES.ZP_PROCESS_RUNNING).filter(
            TABLES.ZP_PROCESS_RUNNING.ZP_LIBRARY_ID == zp_library_id).update(
            {"PROCESS_DATE_TIME": date_time(),
             "ZP_PROCESS_ID": zp_process_id,
             'PROCESS': process,
             'PROCESS_STATE_DATE_TIME': date_time(),
             'PROCESS_STATE': process_state})
        commit(session)
        session.close()
        self.add_process_running_history(zp_library_id, zp_process_id, process, process_state)

    def set_current_library_process_desc_detail(self, zp_library_id, zp_process_id, process_state):
        session = self.Session()
        rslt_process_running = session.query(TABLES.ZP_PROCESS_RUNNING).filter(
            TABLES.ZP_PROCESS_RUNNING.ZP_LIBRARY_ID == zp_library_id).one()
        process = rslt_process_running.PROCESS
        rslt_process_running.PROCESS_STATE_DATE_TIME = date_time()
        rslt_process_running.PROCESS_STATE = process_state
        rslt_process_running.ZP_PROCESS_ID = zp_process_id
        commit(session)
        session.close()
        self.add_process_running_history(zp_library_id, zp_process_id, process, process_state)

    def set_last_scan_datetime(self, zp_scan_path_id):
        session = self.Session()
        session.query(TABLES.ZP_SCAN_PATH).filter(TABLES.ZP_SCAN_PATH.ID == zp_scan_path_id).update(
            {"LAST_SCAN_DATETIME": date_time()})
        commit(session)
        session.close()

    def eapi_eid_from_zp_tv_id(self, eapi_id, zp_tv_id):
        """Get eapi_id from zp_tv_id

            Args:
                | eapi_id (int): 0
                | zp_tv_id (int): 0
        """
        session = self.Session()
        ZP_EAPI_EID = session.query(TABLES.ZP_TV_EAPI_EID).filter(
            TABLES.ZP_TV_EAPI_EID.ZP_TV_ID == zp_tv_id,
            TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID == eapi_id).one().ZP_EAPI_EID
        session.close()
        return ZP_EAPI_EID

    def iso_639_part1_from_zp_lang_id(self, zp_lang_id):
        session = self.Session()
        iso_639_part1 = None
        try:
            iso_639_part1 = session.query(TABLES.ZP_LANG).filter(
                TABLES.ZP_LANG.ID == zp_lang_id).one().ISO_639_Part1
        except orm.exc.NoResultFound:
            log.warning('ZP_LANG.ID: %s not in ZP_LANG', zp_lang_id)
        session.close()
        return iso_639_part1

    def eapi_eid_from_zp_film_collection_id(self, eapi_id, zp_film_collection_id):
        """Get eapi_id from zp_film_collection_id

            Args:
                | eapi_id (int): 0
                | zp_film_collection_id (int): 0
        """
        session = self.Session()
        ZP_EAPI_COLLECTION_EID = None
        try:
            ZP_EAPI_COLLECTION_EID = session.query(TABLES.ZP_FILM_COLLECTION_EAPI_EID).filter(
                TABLES.ZP_FILM_COLLECTION_EAPI_EID.ZP_FILM_COLLECTION_ID == zp_film_collection_id,
                TABLES.ZP_FILM_COLLECTION_EAPI_EID.ZP_EAPI_ID == eapi_id).one().ZP_EAPI_COLLECTION_EID
        except orm.exc.NoResultFound:
            log.warning(
                'ZP_FILM_COLLECTION_ID: {0} with eapi_id {1} not in ZP_FILM_COLLECTION_EAPI_EID'.format(
                    zp_film_collection_id,
                    eapi_id))
        session.close()
        return ZP_EAPI_COLLECTION_EID

    def set_retry(self, ZP_RETRY_TYPE_ID, ZP_RETRY_ENTITY_TYPE_ID, ZP_RETRY_ENTITY_ID, zp_eapi_id=0, zp_lang_id=0):
        session = self.Session()
        max_count = session.query(TABLES.ZP_RETRY_TYPE).filter(
            TABLES.ZP_RETRY_TYPE.ID == ZP_RETRY_TYPE_ID).one().MAX_COUNT
        if not isinstance(zp_lang_id, int):
            zp_lang_id = 0
        try:
            ZP_RETRY = session.query(TABLES.ZP_RETRY).filter(
                TABLES.ZP_RETRY.ZP_RETRY_TYPE_ID == ZP_RETRY_TYPE_ID,
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == ZP_RETRY_ENTITY_TYPE_ID,
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID == ZP_RETRY_ENTITY_ID,
                TABLES.ZP_RETRY.ZP_EAPI_ID == zp_eapi_id,
                TABLES.ZP_RETRY.ZP_LANG_ID == zp_lang_id
            ).one()
        except orm.exc.NoResultFound:
            add_ZP_RETRY = TABLES.ZP_RETRY(ZP_RETRY_TYPE_ID=ZP_RETRY_TYPE_ID,
                                           ZP_RETRY_ENTITY_TYPE_ID=ZP_RETRY_ENTITY_TYPE_ID,
                                           ZP_RETRY_ENTITY_ID=ZP_RETRY_ENTITY_ID,
                                           ZP_EAPI_ID=zp_eapi_id,
                                           ZP_LANG_ID=zp_lang_id,
                                           DATETIME=date_time(),
                                           COUNT=1)
            session.add(add_ZP_RETRY)
            commit(session)
        else:
            if ZP_RETRY.COUNT < max_count:
                ZP_RETRY.COUNT = ZP_RETRY.COUNT + 1
            ZP_RETRY.DATETIME = date_time()
            commit(session)
        session.close()

    def check_can_retry(self, zp_rerty_type_id):
        session = self.Session()
        can_retry = False
        try:
            zp_retry_type = session.query(TABLES.ZP_RETRY_TYPE).filter(
                TABLES.ZP_RETRY_TYPE.ID == zp_rerty_type_id
            ).one()
        except orm.exc.NoResultFound:
            log.error('Cannot find TABLES.ZP_RETRY_TYPE.ID %s', zp_rerty_type_id)
        else:
            if zp_retry_type.RUN_BETWEEN == 1:
                if time_run_between(zp_retry_type.RUN_BETWEEN_START, zp_retry_type.RUN_BETWEEN_END) is True:
                    can_retry = True
            else:
                can_retry = True
        session.close()
        return can_retry

    def get_all_user_library_langs(self, zp_library_id):
        # todo move this into generic functions
        # todo allow to use other languages as fallback
        session = self.Session()
        return_dict = {}
        user_langs = session.query(
            TABLES.ZP_USER_LIBRARY_LANG.ZP_LANG_ID.distinct().label('ZP_LANG_ID'),
            TABLES.ZP_LANG.Ref_Name
        ).filter(
            TABLES.ZP_LANG.ID == TABLES.ZP_USER_LIBRARY_LANG.ZP_LANG_ID,
            TABLES.ZP_USER.ID == TABLES.ZP_USER_LIBRARY_LANG.ZP_USER_ID,
            TABLES.ZP_USER.ENABLED == 1,
            TABLES.ZP_USER_LIBRARY_LANG.ZP_LIBRARY_ID == zp_library_id
        ).all()
        session.close()
        for user_lang in user_langs:
            return_dict[user_lang.ZP_LANG_ID] = user_lang.Ref_Name
        return return_dict

    def create_root_download_folder(self):
        if make_dir(self.global_config_dict['downloaded_images_root_path']):
            return True
        return False

    def raise_invalid_filefolder(self, zp_library_id, zp_scan_path_id, json_scan_path_dict,
                                 source_id, path, reason, path_extra=None):
        session = self.Session()
        try:
            zp_invalid_filefolder = session.query(TABLES.ZP_INVALID_FILEFOLDER).filter(
                TABLES.ZP_INVALID_FILEFOLDER.ZP_LIBRARY_ID == zp_library_id,
                TABLES.ZP_INVALID_FILEFOLDER.ZP_SCAN_PATH_ID == zp_scan_path_id,
                TABLES.ZP_INVALID_FILEFOLDER.SOURCE_ID == source_id,
                TABLES.ZP_INVALID_FILEFOLDER.PATH == path
            ).one()
        except orm.exc.NoResultFound:
            add_zp_invalid_filefolder = TABLES.ZP_INVALID_FILEFOLDER(ZP_LIBRARY_ID=zp_library_id,
                                                                     ZP_SCAN_PATH_ID=zp_scan_path_id,
                                                                     SCAN_PATH_JSON = json_scan_path_dict,
                                                                     SOURCE_ID=source_id,
                                                                     PATH=path,
                                                                     PATH_EXTRA=path_extra,
                                                                     LAST_OCCURANCE_DATETIME=date_time(),
                                                                     REASON=reason
                                                                     )
            session.add(add_zp_invalid_filefolder)
            commit(session)
        else:
            zp_invalid_filefolder.LAST_OCCURANCE_DATETIME = date_time()
            zp_invalid_filefolder.SCAN_PATH_JSON = json_scan_path_dict
            zp_invalid_filefolder.PATH_EXTRA = path_extra
            zp_invalid_filefolder.REASON = reason
            commit(session)
        session.close()

    def get_process_run_list(self, process_dict):
        return_list = []
        session = self.Session()
        for process in process_dict:
            add_process = False
            try:
                zp_process = session.query(TABLES.ZP_PROCESS_RUN).filter(
                    TABLES.ZP_PROCESS_RUN.ZP_PROCESS_ID == process_dict[process]
                ).one()
            except orm.exc.NoResultFound:
                log.error('Could not find TABLES.ZP_PROCESS_RUN.TABLES.ZP_PROCESS_ID == 1 adding process %s to'
                          ' process list %s', process, return_list)
                #return_list.append(process)
                add_process = True
            else:
                if zp_process.ENABLED == 1:
                    if zp_process.FORCE_RUN == 1:
                        return_list.append(process)
                    else:
                        run_between = zp_process.RUN_BETWEEN
                        run_between_start = zp_process.RUN_BETWEEN_START
                        run_between_end = zp_process.RUN_BETWEEN_END
                        run_interval = zp_process.RUN_INTERVAL
                        last_run = zp_process.LAST_RUN_END
                        now = datetime.now()
                        log.debug('RUN_BETWEEN %s, RUN_BETWEEN_START %s, RUN_BETWEEN_END %s',
                                  run_between, run_between_start, run_between_end)
                        if run_between == 1:
                            log.debug('run_between 1')
                            if re.match(military_time_regex, run_between_start) \
                            and re.match(military_time_regex, run_between_end):
                            # todo change last_run + timedelta(minutes=run_interval) to
                            # last_run.timedelta(minutes=run_interval)
                                if time_run_between(run_between_start, run_between_end) is True:
                                    if last_run + timedelta(minutes=run_interval) <= now:
                                        add_process = True
                            else:
                                log.debug('run_between %s %s', run_between, type(run_between))
                                log.debug('run_between_start %s and or'
                                      ' run_between_end %s not valid against %s', run_between_start, run_between_end,
                                          military_time_regex)
                        else:
                            log.debug('run_between %s %s', run_between, type(run_between))
                            log.debug('NO run_between %s, run_between_start %s,'
                                      ' run_between_end %s', run_between, run_between_start, run_between_end)
                            if last_run + timedelta(minutes=run_interval) <= now:
                                log.debug('last_run %s, timedelta(minutes=run_interval) %s,'
                                      ' run_between_end %s', '{:%Y-%m-%d %H:%M:%S}'.format(last_run),
                                       run_interval, '{:%Y-%m-%d %H:%M:%S}'.format(now))
                                add_process = True
                            else:
                                log.debug('NO last_run %s, timedelta(minutes=run_interval) %s,'
                                      ' run_between_end %s', '{:%Y-%m-%d %H:%M:%S}'.format(last_run),
                                       run_interval, '{:%Y-%m-%d %H:%M:%S}'.format(now))
                else:
                    log.warning('process %s is not enabled', process)
            if add_process is True:
                log.debug('adding process %s to return list %s', process, return_list)
                return_list.append(process)
            else:
                log.debug('NOT adding process %s to return list %s', process, return_list)
        session.close()
        return return_list

    def get_scan_paths(self, zp_library_id):
        """
        Get the scan paths from the db
        Parameters
        ----------
        Returns
        -------
        Dict
            {1: [u'/some/path/A',
                u'/some/path/B',
                ....
                u'/some/path/Z']
            2: ['/some/other/path']}
        """
        session = self.Session()
        scan_path_list = []
        scan_paths_query = session.query(
            TABLES.ZP_SCAN_PATH).filter(
            TABLES.ZP_SCAN_PATH.ZP_LIBRARY_ID == zp_library_id,
            TABLES.ZP_SCAN_PATH.ENABLED == 1
        )
        scan_path_count = scan_paths_query.count()
        log.debug('scan_path_count {0}'.format(scan_path_count))
        if scan_path_count >= 1:
            log.debug('scan_path_count {0} >= 1'.format(scan_path_count))
            for scan_path_result in scan_paths_query:
                scan_path_dict = {'scan_path': scan_path_result.PATH,
                                  'scan_path_id': scan_path_result.ID,
                                  'scan_path_fs_type_id': scan_path_result.ZP_SCAN_PATH_FS_TYPE_ID,
                                  'last_mod_datetine': scan_path_result.LAST_MOD_DATETIME,
                                  'force_full_scan': scan_path_result.FORCE_FULL_SCAN,
                                  'always_full_scan': scan_path_result.ALWAYS_FULL_SCAN
                                  }
                log.debug('scan_path_dict {0}'.format(scan_path_dict))
                scan_path_list.append(scan_path_dict)
        log.debug('scan_path_list: {0}'.format(scan_path_list))
        session.close()
        return scan_path_list

    def get_scan_path_dict(self, zp_scan_path_id):
        session = self.Session()
        zp_scan_path = session.query(
            TABLES.ZP_SCAN_PATH).filter(
            TABLES.ZP_SCAN_PATH.ID == zp_scan_path_id
        ).one()
        scan_path_dict = {'scan_path': zp_scan_path.PATH,
                          'scan_path_id': zp_scan_path.ID,
                          'scan_path_fs_type_id': zp_scan_path.ZP_SCAN_PATH_FS_TYPE_ID,
                          'last_mod_datetine': zp_scan_path.LAST_MOD_DATETIME,
                          'force_full_scan': zp_scan_path.FORCE_FULL_SCAN,
                          'always_full_scan': zp_scan_path.ALWAYS_FULL_SCAN
                          }
        if zp_scan_path.ZP_SCAN_PATH_FS_TYPE_ID == 2:
            zp_scan_path_share_xref = session.query(
                TABLES.ZP_SCAN_PATH_SHARE_XREF).filter(
                TABLES.ZP_SCAN_PATH_SHARE_XREF.ZP_SCAN_PATH_ID == zp_scan_path_id
            ).one()
            scan_path_dict['zp_share_id'] = zp_scan_path_share_xref.ZP_SHARE_ID
            scan_path_dict['zp_share_server_id'] = zp_scan_path_share_xref.ZP_SHARE_SERVER_ID
            scan_path_dict['zp_share_credential_id'] = zp_scan_path_share_xref.ZP_SHARE_CREDENTIAL_ID
        session.close()
        return scan_path_dict

    def reset_scan_path_force_full_scan(self, zp_scan_path_id):
        session = self.Session()
        session.query(TABLES.ZP_SCAN_PATH).filter(TABLES.ZP_SCAN_PATH.ID == zp_scan_path_id).update(
            {'FORCE_FULL_SCAN': 0})
        commit(session)
        session.close()

    def get_user_template_info(self, zp_user_id):
        session = self.Session()
        try:
            zp_user_template = session.query(
                TABLES.ZP_USER_TEMPLATE_XREF.ZP_TEMPLATE_ID,
                TABLES.ZP_TEMPLATE.REF_NAME
            ).join(
                TABLES.ZP_TEMPLATE, TABLES.ZP_USER_TEMPLATE_XREF.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID
            ).filter(
                TABLES.ZP_USER_TEMPLATE_XREF.ZP_USER_ID == zp_user_id
            ).one()
        except orm.exc.NoResultFound:
            error_text = 'Could not get a temaplte from ZP_USER_TEMPLATE_XREF with zp_user_id %s' % zp_user_id
            log.error(error_text)
            self.add_error_raised_to_db(8, error_text)
            zp_template_id = 1
            zp_template_ref_name = 'default'
        else:
            zp_template_id = zp_user_template.ZP_TEMPLATE_ID
            zp_template_ref_name = zp_user_template.REF_NAME
        session.close()
        return zp_template_id, zp_template_ref_name

    def get_template_path(self, zp_temaplte_id):
        session = self.Session()
        try:
            zp_temaplte = session.query(TABLES.ZP_TEMPLATE).filter(
                TABLES.ZP_TEMPLATE.ID == zp_temaplte_id
            ).one()
        except orm.exc.NoResultFound:
            path = None
        else:
            if zp_temaplte.PATH_TYPE == 1:
                path = os.path.join(zerrphix.template.__path__[0], zp_temaplte.PATH,
                                    'template.xml')
            else:
                path = os.path.join(zp_temaplte.PATH, 'template.xml')
        session.close()
        return path

    def get_templates_dict(self, zp_template_id, template_xml_path):
        templates_dict = None
        if isinstance(template_xml_path, string_types):
            if os.path.isfile(template_xml_path):
                templates_dict = xml_to_dict(template_xml_path)
                if isinstance(templates_dict, dict):
                    return templates_dict
                else:
                    return None
            else:
                log_message = 'template_xml_path %s is not a file (zp_template_id %s)' % (
                    template_xml_path,
                    zp_template_id)
                log.error(log_message)
                self.add_error_raised_to_db(9, log_message)
        else:
            log_message = 'Could not get template_xml_path for zp_template_id %s' % zp_template_id
            log.error(log_message)
            self.add_error_raised_to_db(9, log_message)
        return templates_dict

    def get_evaluate_temapltes_dict(self, templates_dict):
        evaluated_temapltes_dict = {'library': {
            'film': {},
            'film_collection': {},
            'tv': {},
            'user': {}
        }}
        render_template_required_keys = ['@width', '@height', '@library', '@type', '@icon_sub_type_list']
        if isinstance(templates_dict, dict):
            if 'templates' in templates_dict:
                if 'template' in templates_dict['templates']:
                    try:
                        iter(templates_dict['templates'])
                    except TypeError as e:
                        log_message = '''templates_dict['templates']['temaplte'] is not iterable %s''' % (
                            str(e))
                        log.error(log_message)
                        self.add_error_raised_to_db(10, log_message)
                    else:
                        for template in templates_dict['templates']['template']:
                            if '@space' in template:
                                if template['@space'].lower() == 'render':
                                    if all_keys_in_dict(template, render_template_required_keys) is True:
                                        if template['@library'].lower() in evaluated_temapltes_dict['library']:
                                            evaluated_temapltes_dict['library'][template['@library']][template['@type']] = \
                                                template
                                        else:
                                            log_message = '''template['@library'] %s is an invalid library''' % (
                                                template['@library']
                                            )
                                            log.warning(log_message)
                                            self.add_warning_raised_to_db(10, log_message)
                                    else:
                                        log_message = '''not all keys %s in template.keys() %s''' % (
                                            str(render_template_required_keys),
                                            template.keys()
                                        )
                                        log.warning(log_message)
                                        self.add_warning_raised_to_db(10, log_message)
                            else:
                                log_message = '''key @space not in template %s''' % str(template)
                                log.error(log_message)
                                self.add_error_raised_to_db(10, log_message)
                else:
                    log_message = '''templates_dict['templates'] does not have key template'''
                    log.error(log_message)
                    self.add_error_raised_to_db(10, log_message)
            else:
                log_message = 'templates_dict does not have key templates'
                log.error(log_message)
                self.add_error_raised_to_db(10, log_message)
        else:
            log_message = 'templates_dict is not dict but %s' % type(templates_dict)
            log.error(log_message)
            self.add_error_raised_to_db(10, log_message)
        return evaluated_temapltes_dict

    def get_space_template(self, temapltes_dict, space):
        for template in temapltes_dict['templates']['template']:
            if template['@space'] == space:
                return template
        return None

    def add_db_log(self, source_id, level, text, traceback_string=None):
        session = self.Session()
        date_time_yesterday = date_time(timedelta(days=1))
        try:
            zp_db_log = session.query(TABLES.ZP_DB_LOG).filter(
                TABLES.ZP_DB_LOG.TEXT==text,
                TABLES.ZP_DB_LOG.TRACEBACK==traceback_string,
                TABLES.ZP_DB_LOG.SOURCE_ID==source_id,
                TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME > date_time_yesterday,
                TABLES.ZP_DB_LOG.LEVEL == level
            ).order_by(TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME.desc()).limit(1).one()
        except orm.exc.NoResultFound:
            add_zp_db_log = TABLES.ZP_DB_LOG(
                EPOCH='{:0.8f}'.format((datetime.now() - datetime.utcfromtimestamp(0)).total_seconds()),
                TEXT=text,
                LEVEL=level,
                TRACEBACK=traceback_string,
                COUNT_24=1,
                SOURCE_ID=source_id,
                FIRST_OCCURRENCE_DATE_TIME = date_time(),
                LAST_OCCURRENCE_DATE_TIME = date_time()
            )
            session.add(add_zp_db_log)
            commit(session)
        else:
            zp_db_log.COUNT_24 += 1
            zp_db_log.LAST_OCCURRENCE_DATE_TIME = date_time()
            commit(session)
        session.close()

    def get_image_type_dict_by_name(self):
        return_dict = {}
        session = self.Session()
        rslt_zp_image_type = session.query(
            TABLES.ZP_IMAGE_TYPE
        ).all()
        session.close()
        for zp_image_type in rslt_zp_image_type:
            return_dict[zp_image_type.NAME] = zp_image_type.ID
        return return_dict

    def add_excpetion_raised_to_db(self, source_id, e):
        self.add_db_log(source_id, 45, str(e), traceback.format_exc())

    def add_error_raised_to_db(self, source_id, text):
        self.add_db_log(source_id, 40, text)

    def add_warning_raised_to_db(self, source_id, text):
        self.add_db_log(source_id, 30, text)

    def get_dune_name_by_id_dict(self):
        return_dict = {}
        session = self.Session()
        rslt_zp_dune = session.query(
            TABLES.ZP_DUNE
        ).all()
        session.close()
        for zp_dune in rslt_zp_dune:
            return_dict[zp_dune.ID] = zp_dune.NAME
        return return_dict

    def create_dune_render_store_dict(self, ZP_DUNE_ID, ZP_DUNE_UI_IMAGE_STORE_TYPE_ID, ZP_DUNE_UI_IMAGE_STORE_ROOT,
                                      ZP_DUNE_SHARE_XREF_ID):
        # raise SystemExit
        dune_render_store_dict = {}
        dune_render_store_dict['render_root_library_dir'] = None
        if ZP_DUNE_UI_IMAGE_STORE_TYPE_ID == 1:
            dune_render_store_dict['type'] = 'local'
            dune_render_store_dict['root_template_store'] = self.global_config_dict['template_store_path']
            # dune_render_root_dir = self.global_config_dict['rendered_image_root_path']
            if make_dir(self.global_config_dict['rendered_image_root_path']) is True:
                dune_render_store_dict['rendered_user_image_root_path'] = os.path.join(
                    self.global_config_dict['rendered_image_root_path'], 'user')
                if make_dir(dune_render_store_dict['rendered_user_image_root_path']) is True:
                    log.debug('make dir %s or was allready existing.',
                                  dune_render_store_dict['render_root_library_dir'])
                else:
                    raise IOError('Unable to make dir %s.' % (
                        dune_render_store_dict['rendered_user_image_root_path']))
                dune_render_store_dict['render_root_library_dir'] = os.path.join(
                    self.global_config_dict['rendered_image_root_path'],
                    self.library_config_dict['name']
                )
                if make_dir(dune_render_store_dict['render_root_library_dir']) is True:
                    log.debug('make dir %s or was allready existing.',
                                  dune_render_store_dict['render_root_library_dir'])
                else:
                    raise IOError('Unable to make dir %s.' % (
                        dune_render_store_dict['render_root_library_dir']))
                #if self.library_config_dict['name'] == 'film_collection':
                #    dune_render_store_dict['render_root_library_collection_dir'] = os.path.join(
                #        self.global_config_dict[ 'rendered_image_root_path'],
                #        '%s_%s' % (self.library_config_dict['name'], 'collection')
                #    )
                #    if make_dir(dune_render_store_dict['render_root_library_collection_dir']) is True:
                #        log.debug('make dir %s or was allready existing.',
                #                  dune_render_store_dict['render_root_library_collection_dir'])
                #    else:
                #        raise IOError('Unable to make dir %s',
                #                      dune_render_store_dict['render_root_library_collection_dir'])
            else:
                raise IOError('Unable to make dir %s', self.global_config_dict['rendered_image_root_path'])
        elif ZP_DUNE_UI_IMAGE_STORE_TYPE_ID == 2:
            dune_render_store_dict['type'] = 'smb'
            dune_render_store_dict['root_template_store'] = smbfs.join(
                        ZP_DUNE_UI_IMAGE_STORE_ROOT, 'template_store')
            dune_render_store_dict['rendered_user_image_root_path'] = smbfs.join(
                        ZP_DUNE_UI_IMAGE_STORE_ROOT, 'rendered', 'user')
            if ZP_DUNE_SHARE_XREF_ID:
                # storage_name://zerrphix_ui/zerrphix_ui
                dune_render_store_dict['connection_dict'] = self.smbfs_connection_dict_dune(ZP_DUNE_SHARE_XREF_ID)
                smbcon = smbfs(dune_render_store_dict['connection_dict'])
                dune_rendered_image_root_path = smbfs.join(ZP_DUNE_UI_IMAGE_STORE_ROOT, 'rendered')
                if smbcon.mkdir(dune_rendered_image_root_path) is True:
                    dune_render_store_dict['render_root_library_dir'] = smbfs.join(
                        ZP_DUNE_UI_IMAGE_STORE_ROOT, 'rendered',
                        self.library_config_dict['name'])
                    if smbcon.mkdir(dune_render_store_dict['render_root_library_dir']) is True:
                        log.debug('make dir %s or was allready existing.',
                                  dune_render_store_dict['render_root_library_dir'])
                    else:
                        raise IOError('Unable to make dir %s on ZP_DUNE_ID %s.' % (
                            dune_render_store_dict['render_root_library_dir'],
                            ZP_DUNE_ID))
                    if self.library_config_dict['name'] == 'film':
                        dune_render_store_dict['render_root_library_collection_dir'] = smbfs.join(
                            ZP_DUNE_UI_IMAGE_STORE_ROOT,
                            'rendered',
                            '%s_%s' % (self.library_config_dict['name'], 'collection'))
                        if smbcon.mkdir(dune_render_store_dict['render_root_library_collection_dir']) is True:
                            log.debug('make dir %s or was allready existing.',
                                      dune_render_store_dict['render_root_library_dir'])
                        else:
                            raise IOError('Unable to make dir %s on ZP_DUNE_ID %s.' % (
                                dune_render_store_dict['render_root_library_collection_dir'],
                                ZP_DUNE_ID))
                else:
                    raise IOError('Unable to make dir %s on ZP_DUNE_ID %s.' % (dune_rendered_image_root_path,
                                                                               ZP_DUNE_ID))
            else:
                log.error('TABLES.ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF cannot be empty.')
                raise AttributeError('TABLES.ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF cannot be empty for ZP_DUNE_ID %s.' %
                                     ZP_DUNE_ID)
                #raise Exception('TABLES.ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF cannot be empty.')

        else:
            log.critical(
                'dune.ZP_DUNE_UI_IMAGE_STORE_TYPE_ID: {0} is not recognised'.format(
                    ZP_DUNE_UI_IMAGE_STORE_TYPE_ID))
            return AttributeError('dune.ZP_DUNE_UI_IMAGE_STORE_TYPE_ID: %s is not recognised.' %
                                  ZP_DUNE_UI_IMAGE_STORE_TYPE_ID)
            #raise Exception(
                #'dune.ZP_DUNE_UI_IMAGE_STORE_TYPE_ID: {0} is not recognised'.format(
                #    ZP_DUNE_UI_IMAGE_STORE_TYPE_ID))
        return dune_render_store_dict

    def max_ZP_DUNE_ID(self):
        session = self.Session()
        max_ZP_DUNE_ID = session.query(func.max(TABLES.ZP_DUNE.ID)).one()[0]
        session.close()
        return max_ZP_DUNE_ID

    def get_dunes(self, ZP_DUNE_ID):
        dunes_dict = {}
        session = self.Session()
        qry_dunes = session.query(TABLES.ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF).filter(
            TABLES.ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF.ZP_DUNE_ID > ZP_DUNE_ID,
            TABLES.ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF.ZP_DUNE_ID.in_(
                session.query(
                    TABLES.ZP_USER_GROUP.ZP_DUNE_ID)),
            TABLES.ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF.ZP_DUNE_UI_IMAGE_STORE_TYPE_ID > 1
        )
        if qry_dunes.count() > 0:
            dunes = qry_dunes.order_by(TABLES.ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF.ZP_DUNE_ID.asc()).limit(5)
            # session.expunge(dunes)
            for dune in dunes:
                dunes_dict[dune.ZP_DUNE_ID] = {}
                dunes_dict[dune.ZP_DUNE_ID]['ZP_DUNE_UI_IMAGE_STORE_TYPE_ID'] = dune.ZP_DUNE_UI_IMAGE_STORE_TYPE_ID
                dunes_dict[dune.ZP_DUNE_ID]['ZP_DUNE_UI_IMAGE_STORE_ROOT'] = dune.ZP_DUNE_UI_IMAGE_STORE_ROOT
                dunes_dict[dune.ZP_DUNE_ID]['ZP_DUNE_SHARE_XREF_ID'] = dune.ZP_DUNE_SHARE_XREF_ID
        session.close()
        return dunes_dict

    def get_users(self, ZP_USER_ID, ZP_DUNE_ID):
        user_list = []
        session = self.Session()
        if ZP_DUNE_ID == 1:
            qry_users = session.query(
                TABLES.ZP_USER_GROUP.ZP_USER_ID.distinct().label('ZP_USER_ID')
            ).filter(
                TABLES.ZP_USER_GROUP.ZP_USER_ID > ZP_USER_ID,
                TABLES.ZP_USER.ID == TABLES.ZP_USER_GROUP.ZP_USER_ID,
                TABLES.ZP_USER.ENABLED == 1
            )
        else:
            qry_users = session.query(
                TABLES.ZP_USER_GROUP
            ).filter(
                TABLES.ZP_USER_GROUP.ZP_USER_ID > ZP_USER_ID,
                TABLES.ZP_USER.ID == TABLES.ZP_USER_GROUP.ZP_USER_ID,
                TABLES.ZP_USER.ENABLED == 1,
                TABLES.ZP_USER_GROUP.ZP_DUNE_ID == ZP_DUNE_ID,
                TABLES.ZP_USER_GROUP.ZP_DUNE_ID.in_(
                    session.query(
                        TABLES.ZP_USER_GROUP.ZP_DUNE_ID)
                )
            )
        if qry_users.count() > 0:
            users = qry_users.order_by(TABLES.ZP_USER_GROUP.ZP_USER_ID.asc()).limit(5)
            for user in users:
                user_list.append(user.ZP_USER_ID)
                # session.expunge(users)
        session.close()
        return user_list

    def smbfs_connection_dict_scan_path(self, ZP_SCAN_PATH_ID):
        # https://gist.github.com/mimoo/11383475
        # extra .enc/dec
        session = self.Session()
        connection_dict = False
        try:
            ZP_SCAN_PATH_SHARE_XREF = session.query(
                TABLES.ZP_SCAN_PATH_SHARE_XREF
            ).filter(
                TABLES.ZP_SCAN_PATH_SHARE_XREF.ZP_SCAN_PATH_ID == ZP_SCAN_PATH_ID
            ).one()
        except orm.exc.NoResultFound:
            log.warning(('Cannot find entry in ZP_SCAN_PATH_SHARE_CREDENTIAL_XREF where'
                         ' ZP_SCAN_PATH_ID = {0}').format(ZP_SCAN_PATH_ID))
        else:
            zp_share_id = ZP_SCAN_PATH_SHARE_XREF.ZP_SHARE_ID
            zp_share_server_id = ZP_SCAN_PATH_SHARE_XREF.ZP_SHARE_SERVER_ID
            zp_share_credentail_id = ZP_SCAN_PATH_SHARE_XREF.ZP_SHARE_CREDENTIAL_ID
            connection_dict = self.smbfs_share_connection_dict(zp_share_id, zp_share_server_id, zp_share_credentail_id)
        session.close()
        return connection_dict

    def smbfs_connection_dict_dune(self, ZP_DUNE_SHARE_XREF_ID):
        session = self.Session()
        connection_dict = False
        try:
            ZP_DUNE_SHARE_XREF = session.query(
                TABLES.ZP_DUNE_SHARE_XREF).filter(
                TABLES.ZP_DUNE_SHARE_XREF.ID == ZP_DUNE_SHARE_XREF_ID
            ).one()
        except orm.exc.NoResultFound:
            log.warning(('Cannot find entry in ZP_DUNE_SHARE_XREF where'
                         ' ZP_DUNE_SHARE_XREF.ID = {0}').format(ZP_DUNE_SHARE_XREF_ID))
        else:
            zp_share_id = ZP_DUNE_SHARE_XREF.ZP_SHARE_ID
            zp_share_server_id = ZP_DUNE_SHARE_XREF.ZP_SHARE_SERVER_ID
            zp_share_credentail_id = ZP_DUNE_SHARE_XREF.ZP_SHARE_CREDENTIAL_ID
            connection_dict = self.smbfs_share_connection_dict(zp_share_id, zp_share_server_id, zp_share_credentail_id)
        session.close()
        return connection_dict

    def get_share_reference_name(self, zp_share_id):
        session = self.Session()
        try:
            ref_name = session.query(TABLES.ZP_SHARE).filter(
                TABLES.ZP_SHARE.ID == zp_share_id
            ).one().REF_NAME
        except orm.exc.NoResultFound:
            ref_name = 'zp_share_id %s not found' % zp_share_id
        session.close()
        return ref_name

    def get_share_credential_reference_name(self, zp_share_credential_id):
        session = self.Session()
        try:
            ref_name = session.query(TABLES.ZP_SHARE_CREDENTIAL).filter(
                TABLES.ZP_SHARE_CREDENTIAL.ID == zp_share_credential_id
            ).one().REF_NAME
        except orm.exc.NoResultFound:
            ref_name = 'zp_share_credential_id %s not found' % zp_share_credential_id
        session.close()
        return ref_name

    def get_share_server_reference_name(self, zp_share_server_id):
        session = self.Session()
        try:
            ref_name = session.query(TABLES.ZP_SHARE_SERVER).filter(
                TABLES.ZP_SHARE_SERVER.ID == zp_share_server_id
            ).one().REF_NAME
        except orm.exc.NoResultFound:
            ref_name = 'zp_share_server_id %s not found' % zp_share_server_id
        session.close()
        return ref_name

    def smbfs_share_connection_dict(self, zp_share_id, zp_share_server_id, zp_share_credentail_id):
        session = self.Session()
        connection_dict = False
        try:
            ZP_SHARE = session.query(
                TABLES.ZP_SHARE).filter(
                TABLES.ZP_SHARE.ID == zp_share_id
            ).one()
        except orm.exc.NoResultFound:
            log.warning(('Cannot find entry in ZP_SHARE where'
                         ' ZP_SHARE_ID = {0}').format(zp_share_id))
        else:
            ZP_SHARE_SHARE_NAME = ZP_SHARE.SHARE_NAME
            ZP_SHARE_DOMAIN = ZP_SHARE.DOMAIN
            try:
                ZP_SHARE_CREDENTIAL = session.query(
                    TABLES.ZP_SHARE_CREDENTIAL).filter(
                    TABLES.ZP_SHARE_CREDENTIAL.ID == zp_share_credentail_id
                ).one()
            except orm.exc.NoResultFound:
                log.warning(('Cannot find entry in ZP_SHARE_CREDENTIAL where'
                             ' ZP_SHARE_CREDENTIAL_ID = {0}').format(zp_share_credentail_id))
            except orm.exc.MultipleResultsFound:
                log.error(('More than entry in ZP_SHARE_CREDENTIAL where'
                             ' ZP_SHARE_CREDENTIAL_ID = {0}. This should not be possible').format(
                    zp_share_credentail_id))
            else:
                ZP_SHARE_CREDENTIAL_USERNAME = ZP_SHARE_CREDENTIAL.USERNAME
                ZP_SHARE_CREDENTIAL_PASSWORD = ZP_SHARE_CREDENTIAL.PASSWORD
                try:
                    ZP_SHARE_SERVER = session.query(
                        TABLES.ZP_SHARE_SERVER).filter(
                        TABLES.ZP_SHARE_SERVER.ID == zp_share_server_id
                    ).one()
                except orm.exc.NoResultFound:
                    log.warning(('Cannot find entry in ZP_SHARE_SERVER where'
                                 ' ZP_SHARE_SERVER_ID = {0}').format(zp_share_server_id))
                else:
                    ZP_SHARE_REMOTE_NAME = ZP_SHARE_SERVER.REMOTE_NAME
                    ZP_SHARE_SERVER_HOSTNAME = ZP_SHARE_SERVER.HOSTNAME
                    ZP_SHARE_SERVER_PORT = ZP_SHARE_SERVER.PORT
                    # scan_path_dict['share'] = ZP_SHARE_INFO.SHARE_NAME
                    connection_dict = {}
                    connection_dict['username'] = ZP_SHARE_CREDENTIAL_USERNAME
                    if len(ZP_SHARE_CREDENTIAL_PASSWORD) > 1:
                        connection_dict['password'] = AESCipher(z(
                            self.global_config_dict['holder']
                        )).q(ZP_SHARE_CREDENTIAL_PASSWORD)
                        #print(connection_dict['password'], zp_share_id)
                        #time.sleep(3000)
                    else:
                        connection_dict['password'] = ''
                    connection_dict['my_name'] = 'zerrphix'
                    connection_dict['remote_name'] = ZP_SHARE_REMOTE_NAME
                    connection_dict['domain'] = ZP_SHARE_DOMAIN
                    connection_dict['host'] = ZP_SHARE_SERVER_HOSTNAME
                    connection_dict['port'] = ZP_SHARE_SERVER_PORT
                    connection_dict['share'] = ZP_SHARE_SHARE_NAME
        return connection_dict

    def set_process_last_run_start(self, zp_process_id):
        session = self.Session()
        session.query(TABLES.ZP_PROCESS_RUN).filter(TABLES.ZP_PROCESS_RUN.ZP_PROCESS_ID == zp_process_id).update(
            {'LAST_RUN_START': date_time()})
        commit(session)
        session.close()

    def set_process_last_run_end(self, zp_process_id):
        session = self.Session()
        process_run = session.query(TABLES.ZP_PROCESS_RUN).filter(
            TABLES.ZP_PROCESS_RUN.ZP_PROCESS_ID == zp_process_id
        ).one()
        process_run.LAST_RUN_END = date_time()
        if process_run.FORCE_RUN == 1:
            if process_run.FORCE_RUN_REQUEST_DATE_TIME <= process_run.LAST_RUN_START:
                process_run.FORCE_RUN = 0
        commit(session)
        session.close()

    def set_process_force_run(self, zp_process_id):
        session = self.Session()
        session.query(TABLES.ZP_PROCESS_RUN).filter(TABLES.ZP_PROCESS_RUN.ZP_PROCESS_ID == zp_process_id).update(
            {'FORCE_RUN': 1, 'FORCE_RUN_REQUEST_DATE_TIME': date_time()})
        commit(session)
        session.close()

    def set_library_last_run(self, zp_library_id):
        session = self.Session()
        session.query(TABLES.ZP_LIBRARY_RUN).filter(TABLES.ZP_LIBRARY_RUN.ZP_LIBRARY_ID == zp_library_id).update(
            {"LAST_RUN": date_time()})
        commit(session)
        session.close()

    def library_run_sleep(self, zp_library_id):
        session = self.Session()
        zp_library_run = session.query(TABLES.ZP_LIBRARY_RUN).filter(
            TABLES.ZP_LIBRARY_RUN.ZP_LIBRARY_ID == zp_library_id
        ).one()
        zp_process_force_run_count = session.query(func.count(TABLES.ZP_PROCESS_RUN.ZP_PROCESS_ID).label('frcount')).filter(
            TABLES.ZP_PROCESS_RUN.ZP_LIBRARY_ID == zp_library_id,
            TABLES.ZP_PROCESS_RUN.FORCE_RUN == 1,
            TABLES.ZP_PROCESS_RUN.ENABLED == 1
        ).one().frcount
        session.close()
        library_last_run = zp_library_run.LAST_RUN
        library_run_interval = zp_library_run.RUN_INTERVAL
        now = datetime.now()
        log.debug('library_last_run %s, library_run_interval, now %s', '{:%Y-%m-%d %H:%M:%S}'.format(library_last_run),
                  '{:%Y-%m-%d %H:%M:%S}'.format(now))
        log.debug('library_last_run + timedelta(minutes=library_run_interval) %s, now %s', '{:%Y-%m-%d %H:%M:%S}'.format(
            library_last_run + timedelta(minutes=library_run_interval)), '{:%Y-%m-%d %H:%M:%S}'.format(now))
        log.debug('zp_process_force_run_count %s', zp_process_force_run_count)
        if library_last_run + timedelta(minutes=library_run_interval) <= now or zp_process_force_run_count >= 1:
            return False
        return True