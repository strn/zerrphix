# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import os.path
import re

from sqlalchemy import orm

from zerrphix.db import commit
from zerrphix.db.tables import TABLES
from zerrphix.util.filesystem import (smbfs)
from zerrphix.util.text import date_time
#from zerrphix.util import smbfs_connection_dict_scan_path
from datetime import datetime
from zerrphix.tv.base import TVBase
from copy import deepcopy
import json
from zerrphix.util.text import json_serial

log = logging.getLogger(__name__)


class Scan(TVBase):
    """Scans for films that are not yet in the db

    """

    def __init__(self, **kwargs):
        """Scan Init

            Args:
                | args (list): Passed through args from the command line.
                | Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.

            Attributes:
                | args (list): Passed through args from the command line.
                | Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.

        """
        super(Scan, self).__init__(**kwargs)

    def scan(self):
        """Start the scan process

            Attributes:
                scan_paths_dict (dict): scan paths to scan through
        """
        # Be compatible with yadis
        # For TV shows you can have either one master folder with the name of the show and all
        # individual episodes inside (whatever the season), or a master folder for the tv show + season
        # subfolder(s) simply named by season number ( "01" , "02" etc ...)
        # TODO: extension
        scan_path_list = self.get_scan_paths(2)
        log.debug('scan_path_list {0}'.format(scan_path_list))
        if scan_path_list:
            for scan_path_dict in scan_path_list:
                root_scan_path = scan_path_dict['scan_path']
                zp_scan_path_id = scan_path_dict['scan_path_id']
                zp_scan_path_fs_type_id = scan_path_dict['scan_path_fs_type_id']
                db_last_mod_datetime = scan_path_dict['last_mod_datetine']
                log.debug('now processing scan_path_id %s, scan_path %s, scan_path_fs_type_id %s', zp_scan_path_id,
                          root_scan_path, zp_scan_path_fs_type_id)
                json_scan_path_dict = json.dumps(scan_path_dict, default=json_serial)
                if zp_scan_path_fs_type_id == 1:
                    self.scan_local(scan_path_dict, root_scan_path, db_last_mod_datetime, json_scan_path_dict)
                elif zp_scan_path_fs_type_id == 2:
                    self.scan_smbfs(scan_path_dict, root_scan_path, db_last_mod_datetime, json_scan_path_dict)
                else:
                    log.warning('zp_scan_path_fs_type_id: {0} not current supported.'.format(zp_scan_path_fs_type_id))
                if scan_path_dict['force_full_scan'] == 1:
                    self.reset_scan_path_force_full_scan(scan_path_dict['scan_path_id'])
        else:
            log.warning('scan_path_list %s is empty. There are not paths to scan.')

    def scan_smbfs(self, scan_path_dict, scan_path, db_last_mod_datetime, json_scan_path_dict):
        """Scan smb share paths using pysmb implmentation

            Args:
                | scan_path_dict (dict): {'scan_path':'/parent/scan_path/folder',
                |							'connection_dict':{username, password etc},
                |							'scan_path_list'':[list of paths in scan_path to scan]
                |						}
                | ZP_SCAN_PATH_ID (int): ZP_SCAN_PATH_ID

            Attributes:
                | args (list): Passed through args from the command line.
                | smbcon (:obj:): smbconnection object

        """
        smbfs_connection_dict = self.smbfs_connection_dict_scan_path(scan_path_dict['scan_path_id'])
        smbcon = smbfs(smbfs_connection_dict)
        log.debug('now processing scan_path "{0}"" with ZP_SCAN_PATH_ID {1}'.format(scan_path, scan_path_dict['scan_path_id']))
        if smbcon.isdir(scan_path):
            log.debug('scan_path %s with zp_scan_path_id %s is a dir', scan_path, scan_path_dict['scan_path_id'])
            current_last_mod_datetime = smbcon.getmtime(scan_path)
            log.debug('smbfs current_last_mod_datetime %s', current_last_mod_datetime)
            # fs mod datetime might have milliseconds but db won't so we need to remove milliseconds from
            # fs mod datetime
            scan = False
            update_db_last_mod_datetime = False
            if scan_path_dict['force_full_scan'] == 1 or scan_path_dict['always_full_scan'] == 1:
                scan = True
            elif isinstance(current_last_mod_datetime, float):
                update_db_last_mod_datetime = True
                current_last_mod_datetime = datetime.fromtimestamp(current_last_mod_datetime).replace(microsecond=0)
                if db_last_mod_datetime is None or (current_last_mod_datetime > db_last_mod_datetime):
                    log.debug('db_last_mod_datetime %s is none or current_last_mod_datetime %s'
                              'grater than db_last_mod_datetime', db_last_mod_datetime,
                              current_last_mod_datetime)
                    scan = True
            else:
                log.warning('it looks as though there is a bug with pysmb current_last_mod_datetime %s is not float'
                            'but %s', current_last_mod_datetime, type(current_last_mod_datetime))
                scan = True
            if scan is True:
                self.set_last_scan_datetime(scan_path_dict['scan_path_id'])
                self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                             9,
                                                             'SMB %s in share %s on %s to be scanned this run' %
                                                             (scan_path, smbfs_connection_dict['share'],
                                                              smbfs_connection_dict['host']))
                filefolders = sorted(smbcon.listdir(scan_path, dir_only=True))
                log.debug(
                    'filefolders "{0}" in scan_path "{1}" with ZP_SCAN_PATH_ID {2}'.format(filefolders, scan_path,
                                                                                           scan_path_dict['scan_path_id']))
                filefolders_scanned = 0
                filefolders_invalid = 0
                filefolders_added = 0
                for filefolder in filefolders:
                    filefolders_scanned += 1
                    log.debug(
                        'filefolder: "{0}" in scan_path "{1}" with ZP_SCAN_PATH_ID {2}'.format(filefolder,
                                                                                               scan_path,
                                                                                               scan_path_dict['scan_path_id']))
                    added_to_db = self.proceess_folder(filefolder, scan_path_dict['scan_path_id'])
                    if added_to_db == 1:
                        filefolders_added += 1
                    elif added_to_db == 0:
                        filefolders_invalid += 1
                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                 9,
                                                                 'SMB Scanned %s folders in share %s path %s on %s.'
                                                                 ' Added %s - Invalid %s' %
                                                             (filefolders_scanned, smbfs_connection_dict['share'],
                                                              scan_path,
                                                              smbfs_connection_dict['host'],
                                                              filefolders_added, filefolders_invalid
                                                              ))
                if update_db_last_mod_datetime is True:
                    self.set_scan_path_last_mod_datetime(scan_path_dict['scan_path_id'], current_last_mod_datetime)
            else:
                log.debug('current_last_mod_datetime %s is not greater than db_last_mod_datetime %s'
                          'not scanning',
                          current_last_mod_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                          db_last_mod_datetime.strftime("%Y-%m-%d %H:%M:%S") if isinstance(db_last_mod_datetime,
                                                                                           datetime) else
                          db_last_mod_datetime
                          )
        else:
            error_text = 'scan_path "{0}" with ZP_SCAN_PATH_ID "{1}" is NOT a dir will not scan'.format(scan_path,
                                                                                           scan_path_dict[
                                                                                               'scan_path_id'])
            log.error(error_text)
            self.add_error_raised_to_db(3, error_text)

    def set_scan_path_last_mod_datetime(self, zp_scan_path_id, current_last_mod_datetime):
        session = self.Session()
        session.query(TABLES.ZP_SCAN_PATH).filter(TABLES.ZP_SCAN_PATH.ID == zp_scan_path_id).update(
            {"LAST_MOD_DATETIME": current_last_mod_datetime.strftime("%Y-%m-%d %H:%M:%S")})
        commit(session)
        session.close()

    def proceess_folder(self, filefolder, zp_scan_path_id):
        """Process folders found by scan_smbfs

            Args:
                | filefolder (str): filefolder
                | ZP_SCAN_PATH_ID (int): ZP_SCAN_PATH_ID
                | SCAN_PATH_SUB_DIR (str): folder under scan_path (can be blank) \
                used with ZP_SCAN_PATH_STRUCT_TYPE_ID = 1 (i.e. tv show stored in a-z folders)

        """
        session = self.Session()
        try:
            session.query(TABLES.ZP_TV_FILEFOLDER).filter(
                TABLES.ZP_TV_FILEFOLDER.LAST_PATH == filefolder,
                TABLES.ZP_TV_FILEFOLDER.ZP_SCAN_PATH_ID == zp_scan_path_id).one()
        except orm.exc.NoResultFound:
            add_ZP_TV_FILEFOLDER = TABLES.ZP_TV_FILEFOLDER(ZP_SCAN_PATH_ID=zp_scan_path_id,
                                                           LAST_PATH=filefolder,
                                                           ENABLED=1,
                                                           ENABLED_UPDATE_DATETIME=date_time())
            session.add(add_ZP_TV_FILEFOLDER)
            commit(session)
            added_to_db = 1
        except orm.exc.MultipleResultsFound as e:
            added_to_db = 0
            error_message = ('More than entry in ZP_TV_SHOW_FILEFOLDER where'
                         ' LAST_PATH = {0} and ZP_SCAN_PATH_ID = {1}. This should not be possible').format(
                filefolder,
                zp_scan_path_id)
            self.add_error_raised_to_db(6 ,error_message)
            log.exception(error_message)
        else:
            added_to_db = 2
        session.close()
        return added_to_db

    def scan_local(self, scan_path_dict, scan_path, db_last_mod_datetime, json_scan_path_dict):
        # TODO: finish local
        log.debug('now processing scan_path "{0}"" with ZP_SCAN_PATH_ID {1}'.format(scan_path, scan_path_dict['scan_path_id']))
        if os.path.isdir(scan_path):
            log.debug('scan_path %s with zp_scan_path_id %s is a dir', scan_path,
                                                                     scan_path_dict['scan_path_id'])
            current_last_mod_datetime = os.path.getmtime(scan_path)
            log.debug('local current_last_mod_datetime %s', current_last_mod_datetime)
            # fs mod datetime might have milliseconds but db won't so we need to remove milliseconds from
            # fs mod datetime
            scan = False
            update_db_last_mod_datetime = False
            if scan_path_dict['force_full_scan'] == 1 or scan_path_dict['always_full_scan'] == 1:
                scan = True
            elif isinstance(current_last_mod_datetime, float):
                update_db_last_mod_datetime = True
                current_last_mod_datetime = datetime.fromtimestamp(current_last_mod_datetime).replace(microsecond=0)
                if db_last_mod_datetime is None or (current_last_mod_datetime > db_last_mod_datetime):
                    log.debug('db_last_mod_datetime %s is none or current_last_mod_datetime %s'
                              'grater than db_last_mod_datetime', db_last_mod_datetime,
                              current_last_mod_datetime)
                    scan = True
            else:
                scan = True
            if scan is True:
                self.set_last_scan_datetime(scan_path_dict['scan_path_id'])
                self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                             9,
                                                             'LOCAL %s to be scanned this run' %
                                                             scan_path)
                filefolders = sorted(os.listdir(scan_path))
                log.debug(
                    'filefolders "{0}" in scan_path "{1}" '
                    'with ZP_SCAN_PATH_ID {2}'.format(filefolders, scan_path, scan_path_dict['scan_path_id']))
                filefolders_scanned = 0
                filefolders_invalid = 0
                filefolders_added = 0
                for filefolder in filefolders:
                    log.debug(
                        'filefolder: "{0}" in scan_path "{1}" with ZP_SCAN_PATH_ID {2}'.format(filefolder,
                                                                                               scan_path,
                                                                                               scan_path_dict['scan_path_id']))
                    filefolder_path = os.path.join(scan_path, filefolder)
                    if os.path.isdir(filefolder_path):
                        filefolders_scanned += 1
                        added_to_db = self.proceess_folder(filefolder, scan_path_dict['scan_path_id'])
                        if added_to_db == 1:
                            filefolders_added += 1
                        elif added_to_db == 0:
                            filefolders_invalid += 1
                        self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                 9,
                                                                 'LOCAL Founds %s folders in %s.'
                                                                 ' Added %s - Invalid %s' %
                                                                 (filefolders_scanned, filefolder_path,
                                                                  filefolders_added, filefolders_invalid
                                                                  ))
                    else:
                        log.debug('scan_path "{0}" with ZP_SCAN_PATH_ID "{1}" is NOT a dir will not '
                                  'scan'.format(scan_path, scan_path_dict['scan_path_id']))
                if update_db_last_mod_datetime is True:
                    self.set_scan_path_last_mod_datetime(scan_path_dict['scan_path_id'], current_last_mod_datetime)
            else:
                self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                             9,
                                                             'LOCAL %s NOT to be scanned this run' %
                                                             scan_path)
                log.debug('current_last_mod_datetime %s is not greater than db_last_mod_datetime %s'
                          'not scanning',
                          current_last_mod_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                          db_last_mod_datetime.strftime("%Y-%m-%d %H:%M:%S") if isinstance(db_last_mod_datetime,
                                                                                           datetime) else
                          db_last_mod_datetime
                          )
        else:
            error_text = 'scan_path "{0}" with ZP_SCAN_PATH_ID "{1}" is NOT a dir will not scan'.format(scan_path,
                                                           scan_path_dict['scan_path_id'])
            log.error(error_text)
            self.add_error_raised_to_db(4, error_text)
