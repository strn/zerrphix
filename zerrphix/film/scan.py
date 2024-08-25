# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import json
import logging
import os.path
import re

from sqlalchemy import orm

import zerrphix.constants
from zerrphix.constants import pattern_ignore_folders
from zerrphix.db import commit
from zerrphix.db.tables import TABLES
from zerrphix.util.filesystem import (get_file_extension, get_filename_root, get_path_basename,
                                      get_folder_contents_type)
#from zerrphix.util import smbfs_connection_dict_scan_path
from zerrphix.util.filesystem import smbfs
from zerrphix.util.text import date_time
from datetime import datetime
from zerrphix.film.base import FilmBase
from copy import deepcopy
from zerrphix.util.text import json_serial


log = logging.getLogger(__name__)


class Scan(FilmBase):
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
                | filenameroot_title_regex_dict (dict): regex patterns used \
                for detecting title/year from file/folder.

        """
        #self.args = args
        #self.Session = Session
        super(Scan, self).__init__(**kwargs)
        self._setup_allowed_extentions()
        release_pattern_name_list = ['pattern_video_source',
                                     'pattern_video_tags',
                                     'pattern_video_s3d',
                                     'pattern_video_repack',
                                     'pattern_subtitle_tags',
                                     'pattern_video_format',
                                     'pattern_unkown']

        release_patterns_combined = '(?:'
        for pattern in release_pattern_name_list:
            release_patterns_combined += '{0}|'.format(getattr(zerrphix.constants, pattern))
        release_patterns_combined = release_patterns_combined.rstrip('|')
        release_patterns_combined += ')'
        self.filenameroot_title_regex_dict = {
            'title_year_a': r"""(?P<title>[\w\d'`\-\s]+)[^\w\d'`\-\s]?\b(?P<year>[1-2][0-9]{3})\b""",
            'title_only_a': r"""(?P<title>[\w\d'`\-\s]+?){0}""".format(release_patterns_combined),
            'title_only_b': r"""(?P<title>[\w\d'`\-\s]+)"""
        }


    def _setup_allowed_extentions(self):
        """Get the allowed extensions from the db and make a list

            Attributes:
                self.allowed_extensions_list (list): list of permitted extensions
                for filenames that will be considered video files
        """
        self.allowed_extensions_list = self.get_extension_list(1)
        self.ignore_extensions_list = self.get_extension_list(1, 1)

    def scan(self):
        """Start the scan process

            Attributes:
                scan_path_dict (dict): scan paths to scan through

        """
        # TODO: extension
        scan_path_list = self.get_scan_paths(1)
        log.debug('scan_path_list {0}'.format(scan_path_list))
        #for scan_path_dict in scan_path_list:
            #log.error('scan_path_dict %s', scan_path_dict)
        #raise SystemExit
        if scan_path_list:
            for scan_path_dict in scan_path_list:
                log.debug('scan_path_dict %s', scan_path_dict)
                root_scan_path = scan_path_dict['scan_path']
                zp_scan_path_id = scan_path_dict['scan_path_id']
                zp_scan_path_fs_type_id = scan_path_dict['scan_path_fs_type_id']
                db_last_mod_datetime = scan_path_dict['last_mod_datetine']
                log.debug('now processing scan_path_id %s, scan_path %s, scan_path_fs_type_id %s'
                          ', db_last_mod_datetime %s', zp_scan_path_id,
                          root_scan_path, zp_scan_path_fs_type_id, db_last_mod_datetime)
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

    def scan_local(self, scan_path_dict, root_scan_path, db_last_mod_datetime, json_scan_path_dict):
        if os.path.isdir(root_scan_path):
            log.debug('scan_path %s with zp_scan_path_id %s is a dir', root_scan_path, scan_path_dict['scan_path_id'])
            current_last_mod_datetime = os.path.getmtime(root_scan_path)
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
                                                             1,
                                                             'LOCAL %s to be scanned this run' %
                                                             root_scan_path)
                filefolders = sorted(os.listdir(root_scan_path))
                #
                log.debug(
                    'filefolders "{0}" in scan_path "{1}" with scan_path_id {2}'.format(filefolders, root_scan_path,
                                                                                        scan_path_dict['scan_path_id']))
                filefolders_scanned = 0
                filefolders_invalid = 0
                filefolders_added = 0
                for filefolder in filefolders:
                    added_to_db = 0
                    log.debug(
                        'filefolder: "{0}" in scan_path "{1}" with scan_path_id {2}'.format(filefolder, root_scan_path,
                                                                                            scan_path_dict[
                                                                                                'scan_path_id']))
                    filefolder_path = os.path.join(root_scan_path, filefolder)
                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                 1,
                                                                 'LOCAL Scanning %s' %
                                                                 filefolder_path)
                    log.debug(
                        'filefolder_path: "{0}" in scan_path "{1}" with scan_path_id {2}'.format(filefolder_path,
                                                                                                 root_scan_path,
                                                                                                 scan_path_dict[
                                                                                                     'scan_path_id']))
                    # print(SCAN_PATH_SUB_DIR, 'SCAN_PATH_SUB_DIR')
                    if os.path.isdir(filefolder_path):
                        filefolders_scanned += 1
                        if not re.match(pattern_ignore_folders, filefolder, flags=re.I):
                            log.debug(
                                'filefolder_path: "{0}"" in scan_path "{1}" with scan_path_id '
                                '{2} is a directory'.format(
                                    filefolder_path,
                                    root_scan_path,
                                    scan_path_dict['scan_path_id']))
                            # filefolder will be put into the scan_sub_path_dir column so we need it to be added to
                            # the scan path
                            # so that the last path is accurate
                            # scan_path = os.path.join(scan_path, filefolder)
                            # TODO: Deal with windows systems
                            added_to_db = self.proceess_folder(scan_path_dict, root_scan_path, filefolder_path, json_scan_path_dict,
                                                 filefolder)
                        else:
                            reason = 're.match(pattern_ignore_folders, filefolder) returned true for ' \
                                       'pattern_ignore_folders: %s and filefolder: %s,' \
                                     '  json_scan_path_dict %s' % \
                                     (pattern_ignore_folders,
                                        filefolder, json_scan_path_dict)
                            log.debug(reason)
                            added_to_db = 3
                            #self.raise_invalid_filefolder(1, scan_path_dict['scan_path_id'], json_scan_path_dict, 7,
                            #                              filefolder_path, reason
                            #                              )
                            # raise SystemExit
                            #filefolders_invalid += 1
                    elif os.path.isfile(filefolder_path):
                        file_extention = get_file_extension(filefolder_path)
                        if file_extention not in self.ignore_extensions_list:
                            filefolders_scanned += 1
                            log.debug(
                                'filefolder_path: "{0}"" in scan_path "{1}" with scan_path_id {2} is a file'.format(
                                    filefolder_path, root_scan_path, scan_path_dict['scan_path_id']))
                            added_to_db = self.process_file(scan_path_dict, root_scan_path, filefolder_path, filefolder,
                                              json_scan_path_dict)
                        else:
                            added_to_db = 3
                    else:
                        log.debug(('filefolder_path: "{0}"" in scan_path "{1}" with scan_path_id {2} is not a '
                                   'file or a directory will not conintue to process').format(filefolder_path,
                                                                                              root_scan_path,
                                                                                              scan_path_dict[
                                                                                            'scan_path_id']))
                    if added_to_db == 1:
                        filefolders_added += 1
                    elif added_to_db == 0:
                        filefolders_invalid += 1
                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                 1,
                                                                 'LOCAL Scanned %s filefolders in %s.'
                                                                 ' Added %s - Invalid %s' %
                                                                 (filefolders_scanned, filefolder_path,
                                                                  filefolders_added, filefolders_invalid
                                                                  ))
                if update_db_last_mod_datetime is True:
                    self.set_scan_path_last_mod_datetime(scan_path_dict['scan_path_id'], current_last_mod_datetime)
                else:
                    log.debug('not updating set_scan_path_last_mod_datetime zp_scan_path_id %s',
                              scan_path_dict['scan_path_id'])
            else:
                self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                             1,
                                                             'LOCAL %s not to be scanned this run' %
                                                             root_scan_path)
                log.debug('current_last_mod_datetime %s is not greater than db_last_mod_datetime %s'
                          'not scanning',
                          current_last_mod_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                          db_last_mod_datetime.strftime("%Y-%m-%d %H:%M:%S") if isinstance(db_last_mod_datetime,
                                                                                           datetime) else
                          db_last_mod_datetime
                          )
        else:
            error_text = 'scan_path "{0}" with scan_path_id "{1}" is NOT a dir will not scan'.format(root_scan_path,
                                                                                                  scan_path_dict[
                                                                                                      'scan_path_id'])
            log.error(error_text)
            self.add_error_raised_to_db(2, error_text)


    def scan_smbfs(self, scan_path_dict, root_scan_path, db_last_mod_datetime, json_scan_path_dict):
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
        safe_smbfs_connection_dict = deepcopy(smbfs_connection_dict)
        safe_smbfs_connection_dict['password'] = '*****'
        json_safe_smbfs_connection_dict = json.dumps(safe_smbfs_connection_dict)
        smbcon = smbfs(smbfs_connection_dict)
        if smbcon.isdir(root_scan_path):
            log.debug('root_scan_path %s', root_scan_path)
            log.debug('scan_path %s with zp_scan_path_id %s is a dir', root_scan_path, scan_path_dict['scan_path_id'])
            current_last_mod_datetime = smbcon.getmtime(root_scan_path)
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
                log.error('it looks as though there is a bug with pysmb current_last_mod_datetime %s is not float'
                            'but %s', current_last_mod_datetime, type(current_last_mod_datetime))
                scan = True
                #raise SystemExit
            if scan is True:
                self.set_last_scan_datetime(scan_path_dict['scan_path_id'])
                self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                             1,
                                                             'SMB %s in share %s on %s to be scanned this run' %
                                                             (root_scan_path, smbfs_connection_dict['share'],
                                                              smbfs_connection_dict['host']))
                filefolders = sorted(smbcon.listdir(root_scan_path))
                log.debug(
                    'filefolders "{0}" in scan_path "{1}" with ZP_SCAN_PATH_ID {2}'.format(filefolders,
                                                                                           root_scan_path,
                                                                                           scan_path_dict[
                                                                                               'scan_path_id']))
                filefolders_scanned = 0
                filefolders_invalid = 0
                filefolders_added = 0
                for filefolder in filefolders:
                    added_to_db = 0
                    log.debug(
                        'filefolder: "{0}" in scan_path "{1}" with ZP_SCAN_PATH_ID {2}'.format(filefolder,
                                                                                               root_scan_path,
                                                                                               scan_path_dict[
                                                                                                   'scan_path_id']))
                    # self.smbfs_proceess_folder(filefolder, zp_scan_path_id, smbcon)
                    # todo deal with invalid chars eg \
                    root_scan_path = root_scan_path.strip('/\\')
                    root_scan_path = "/%s/" % root_scan_path
                    filefolder_path = smbfs.join(root_scan_path, filefolder)
                    if smbcon.isdir(filefolder_path):
                        filefolders_scanned += 1
                        if not re.match(pattern_ignore_folders, filefolder, flags=re.I):
                            log.debug(
                                'filefolder_path: "{0}"" in scan_path "{1}" with scan_path_id '
                                '{2} is a directory'.format(
                                    filefolder_path,
                                    root_scan_path,
                                    scan_path_dict['scan_path_id']))
                            # TODO: Deal with windows systems
                            added_to_db = self.proceess_folder(scan_path_dict, root_scan_path,
                                                 filefolder_path, json_scan_path_dict, filefolder, smbcon=smbcon,
                                                 json_safe_smbfs_connection_dict=json_safe_smbfs_connection_dict)
                            # raise SystemExit
                        else:
                            reason = 're.match(pattern_ignore_folders, filefolder) returned true for ' \
                                       'pattern_ignore_folders: %s and filefolder: %s,' \
                                     '  json_safe_smbfs_connection_dict %s, json_scan_path_dict %s' % \
                                     (pattern_ignore_folders,
                                        filefolder, json_safe_smbfs_connection_dict, json_scan_path_dict)
                            log.debug(reason)
                            self.raise_invalid_filefolder(1, scan_path_dict['scan_path_id'], json_scan_path_dict, 1,
                                                          filefolder_path, reason,
                                                          path_extra=json_safe_smbfs_connection_dict
                                                          )
                            # raise SystemExit
                    elif smbcon.isfile(filefolder_path):
                        filefolders_scanned += 1
                        log.debug(
                            'filefolder_path: "{0}"" in scan_path "{1}" with scan_path_id {2} is a file'.format(
                                filefolder_path, root_scan_path, scan_path_dict['scan_path_id']))
                        added_to_db = self.process_file(scan_path_dict, root_scan_path,
                                          filefolder_path, filefolder, json_scan_path_dict,
                                          path_extra=json_safe_smbfs_connection_dict)
                    else:
                        log.warning(('filefolder_path: "{0}"" in scan_path "{1}" with scan_path_id {2} is not a '
                                     'file or a directory will not conintue to process').format(filefolder_path,
                                                                                                root_scan_path,
                                                                                                scan_path_dict[
                                                                                                'scan_path_id']))
                    if added_to_db == 1:
                        filefolders_added += 1
                    elif added_to_db == 0:
                        filefolders_invalid += 1
                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                 1,
                                                                 'SMB Scanned %s filefolders in share %s path %s on %s.'
                                                                 ' Added %s - Invalid %s' %
                                                             (filefolders_scanned, smbfs_connection_dict['share'],
                                                              root_scan_path,
                                                              smbfs_connection_dict['host'],
                                                              filefolders_added, filefolders_invalid
                                                              ))
                        # raise SystemExit
                if update_db_last_mod_datetime is True:
                    log.debug('setting zp_scan_path_id %s to current_last_mod_datetime %s', scan_path_dict['scan_path_id'],
                              current_last_mod_datetime.strftime("%Y-%m-%d %H:%M:%S"))
                    self.set_scan_path_last_mod_datetime(scan_path_dict['scan_path_id'], current_last_mod_datetime)
                else:
                    log.debug('not updating set_scan_path_last_mod_datetime zp_scan_path_id %s',
                              scan_path_dict['scan_path_id'])
            else:
                log.debug('current_last_mod_datetime %s is not greater than db_last_mod_datetime %s'
                          'not scanning',
                          current_last_mod_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                          db_last_mod_datetime.strftime("%Y-%m-%d %H:%M:%S") if isinstance(db_last_mod_datetime,
                                                                                           datetime) else
                          db_last_mod_datetime
                          )

        else:
            error_text = 'scan_path "%s" with ZP_SCAN_PATH_ID "%s" is NOT a dir will not scan' % (root_scan_path,
                      scan_path_dict['scan_path_id'])
            log.error(error_text)
            self.add_error_raised_to_db(1, error_text)
        smbcon.close()

    def set_scan_path_last_mod_datetime(self, zp_scan_path_id, current_last_mod_datetime):
        session = self.Session()
        session.query(TABLES.ZP_SCAN_PATH).filter(TABLES.ZP_SCAN_PATH.ID == zp_scan_path_id).update(
            {"LAST_MOD_DATETIME": current_last_mod_datetime.strftime("%Y-%m-%d %H:%M:%S")})
        commit(session)
        session.close()

    def proceess_folder(self, scan_path_dict, scan_path, folder_path, json_scan_path_dict,
                        scan_path_sub_dir, smbcon=None,
                        json_safe_smbfs_connection_dict=None):
        """Process folders found by scan_smbfs

            Args:
                | filefolder (str): filefolder
                | ZP_SCAN_PATH_ID (int): ZP_SCAN_PATH_ID
                | SCAN_PATH_SUB_DIR (str): folder under scan_path (can be blank) \
                used with ZP_SCAN_PATH_STRUCT_TYPE_ID = 1 (i.e. tv show stored in a-z folders)

        """
        added_to_db = 0
        try:
            session = self.Session()
            session.query(TABLES.ZP_FILM_FILEFOLDER).filter(
                TABLES.ZP_FILM_FILEFOLDER.ZP_SCAN_PATH_ID == scan_path_dict['scan_path_id'],
                TABLES.ZP_FILM_FILEFOLDER.SCAN_PATH_SUB_DIR == scan_path_sub_dir).one()
            session.close()
        except orm.exc.NoResultFound:
            folder_type = get_folder_contents_type(folder_path, scan_path, smbcon=smbcon,
                                                   valid_extension_list=self.allowed_extensions_list)
            log.debug('folder_type %s', folder_type)
            folder_type_id = folder_type['type_id']
            if folder_type_id >= 1:
                log.debug('folder_type %s', folder_type)
                # todo remove the need to make last path fix (required due to old way of storing filefolders no loger
                # used)
                if folder_type_id == 1:
                    last_path = re.sub(r"""^/?{0}""".format(re.escape(scan_path_sub_dir)), '',
                                   folder_type['current_walk_path'])
                else:
                    last_path = re.sub(r"""^/?{0}""".format(re.escape(scan_path_sub_dir)), '',
                                       folder_type['last_path'])
                log.debug('last_path %s', last_path)
                filename_root_list = []
                if folder_type['type_id'] == 1:
                    for folder in folder_type['folder_list']:
                        filename_root_list.append(folder)
                if scan_path_sub_dir not in filename_root_list:
                    filename_root_list.append(scan_path_sub_dir)
                log.debug('filename_root_list %s', filename_root_list)
                log.debug('last_path.strip(os.sep) %s, zp_scan_path_id %s, scan_path_sub_dir %s, TITLE_LIST %s'
                          'ZP_FILM_FOLDER_TYPE_ID %s',
                          last_path.strip(os.sep),
                          scan_path_dict['scan_path_id'],
                          scan_path_sub_dir,
                          filename_root_list,
                          folder_type['type_id'])
                self.add_filefolder_to_db(last_path.strip(os.sep),
                                          scan_path_dict['scan_path_id'],
                                          scan_path_sub_dir,
                                          TITLE_LIST=filename_root_list,
                                          ZP_FILM_FOLDER_TYPE_ID=folder_type['type_id'])

                added_to_db = 1
                # raise SystemExit
            else:
                reason = '''folder_type['type_id'] {0} not >= 1 for folder_path: {1}. Not adding to db.'''.format(
                    folder_type['type_id'],
                    folder_path)
                log.warning(reason)
                self.raise_invalid_filefolder(1, scan_path_dict['scan_path_id'], json_scan_path_dict, 6,
                                              folder_path, reason,
                                              path_extra=json_safe_smbfs_connection_dict
                                              )
        else:
            added_to_db = 2
            log.debug('SCAN_PATH_SUB_DIR %s allready in ZP_FILM_FILEFOLDER with ZP_SCAN_PATH_ID %s',
                      scan_path_sub_dir, scan_path_dict['scan_path_id'])
        return added_to_db

    def process_file(self, scan_path_dict, root_scan_path, filefolder_path, filefolder, json_scan_path_dict,
                     path_extra=None):
        """Process folders found by scan_smbfs

            Args:
                | filefolder (str): filefolder
                | ZP_SCAN_PATH_ID (int): ZP_SCAN_PATH_ID
                | SCAN_PATH_SUB_DIR (str): folder under scan_path (can be blank) \
                used with ZP_SCAN_PATH_STRUCT_TYPE_ID = 1 (i.e. tv show stored in a-z folders)

        """
        added_to_db = 0
        try:
            session = self.Session()
            session.query(TABLES.ZP_FILM_FILEFOLDER).filter(
                TABLES.ZP_FILM_FILEFOLDER.ZP_SCAN_PATH_ID == scan_path_dict['scan_path_id'],
                TABLES.ZP_FILM_FILEFOLDER.LAST_PATH == filefolder,
                TABLES.ZP_FILM_FILEFOLDER.SCAN_PATH_SUB_DIR == '').one()
            session.close()
        except orm.exc.NoResultFound:
            file_extension = get_file_extension(filefolder)
            log.debug(
                'file_extension %s for filefolder %s in root_scan_path %s of ZP_SCAN_PATH_ID %s',
                file_extension, filefolder, root_scan_path, scan_path_dict['scan_path_id'])

            if file_extension in self.allowed_extensions_list:
                log.debug('file_extension %s for file_path %s in scan_path %s of '
                          'ZP_SCAN_PATH_ID %s in self.allowed_extensions_list %s', file_extension,
                          filefolder, root_scan_path, scan_path_dict['scan_path_id'],
                          self.allowed_extensions_list)
                filename_root = [get_filename_root(filefolder)]
                log.debug('filefolder.strip(os.sep) %s, zp_scan_path_id %s, TITLE_LIST %s',
                          filefolder.strip(os.sep),
                          scan_path_dict['scan_path_id'],
                          filename_root)
                self.add_filefolder_to_db(filefolder.strip(os.sep),
                                          scan_path_dict['scan_path_id'],
                                          '',
                                          TITLE_LIST=filename_root)
                added_to_db = 1
            elif file_extension not in self.ignore_extensions_list:
                reason = 'file_extension %s for file_path %s in scan_path %s of ' \
                          'ZP_SCAN_PATH_ID %s not in self.allowed_extensions_list %s' % (file_extension,
                          filefolder, root_scan_path, scan_path_dict['scan_path_id'],
                          self.allowed_extensions_list)
                log.warning(reason)
                self.raise_invalid_filefolder(1, scan_path_dict['scan_path_id'], json_scan_path_dict, 2,
                                              filefolder_path, reason,
                                              path_extra=path_extra
                                              )
                # raise SystemExit
        else:
            added_to_db = 2
            log.debug('LAST_PATH %s allready in ZP_FILM_FILEFOLDER with ZP_SCAN_PATH_ID %s'.format(
                filefolder, scan_path_dict['scan_path_id']))

        return added_to_db

    def add_filefolder_to_db(self, LAST_PATH, ZP_SCAN_PATH_ID, SCAN_PATH_SUB_DIR, TITLE_LIST=None,
                             ZP_FILM_FOLDER_TYPE_ID=None):
        """Add filefolder to db

            Args:
                | LAST_PATH (str): the the last path
                | ZP_SCAN_PATH_ID (int): scan_path_id
                | TITLE_LIST (list): list of potential titles of the film to be used by identify
                | SCAN_PATH_SUB_DIR (str): (optional) the folder directly under scan_path
                | SCAN_PATH_SUB_SUB_DIR (str): (optional) the folder directly under SCAN_PATH_SUB_DIR
                | ZP_FILM_FOLDER_TYPE_ID (int): the filefolder type

        """
        session = self.Session()
        # todo: if film association allready exists in ZP_FILM_FILEFOLDER_FILM_XREF for film and provider id
        # calculate film score
        if TITLE_LIST is not None:
            title_list_compressed = json.dumps(TITLE_LIST, ensure_ascii=False).encode('utf-8').encode(
                'zlib_codec').encode('base64_codec')
        else:
            title_list_compressed = None
        add_film_filefolder = TABLES.ZP_FILM_FILEFOLDER(ZP_FILM_ID=None,
                                                        ENABLED=1,
                                                        ENABLED_UPDATE_DATETIME=date_time(),
                                                        ZP_SCAN_PATH_ID=ZP_SCAN_PATH_ID,
                                                        LAST_PATH=LAST_PATH,
                                                        SCAN_PATH_SUB_DIR=SCAN_PATH_SUB_DIR,
                                                        ZP_FILM_FOLDER_TYPE_ID=ZP_FILM_FOLDER_TYPE_ID,
                                                        TITLE_LIST=title_list_compressed)
        session.add(add_film_filefolder)
        log.debug(('Inserted ZP_SCAN_PATH_ID: {0}, LAST_PATH: {1}, SCAN_PATH_SUB_DIR: {2}'
                   ' TITLE_LIST: {3} as {4} into ZP_FILM_FILEFOLDER').format(
            ZP_SCAN_PATH_ID,
            LAST_PATH,
            SCAN_PATH_SUB_DIR,
            TITLE_LIST,
            title_list_compressed))
        commit(session)
        session.close()
