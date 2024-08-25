# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import os.path
import time

from sqlalchemy import func

from zerrphix.db.tables import TABLES
# from zerrphix.util import smbfs_connection_dict_scan_path
from zerrphix.film.base import FilmBase
from zerrphix.util.filesystem import SMBConnectionAssertionError, smbfs
import socket
from smb import base as smb_base

log = logging.getLogger(__name__)


class InverseScan(FilmBase):
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
        # self.args = args
        # self.Session = Session
        super(InverseScan, self).__init__(**kwargs)

    def scan(self):
        session = self.Session()
        zp_scan_path_id_list = []
        zp_film_filefolder = session.query(TABLES.ZP_FILM_FILEFOLDER.ZP_SCAN_PATH_ID.distinct().label('ZP_SCAN_PATH_ID')
                                           ).order_by(TABLES.ZP_FILM_FILEFOLDER.ZP_SCAN_PATH_ID.asc(),
                                                      TABLES.ZP_FILM_FILEFOLDER.ID.asc()).all()
        session.close()
        for film_filefolder in zp_film_filefolder:
            zp_scan_path_id_list.append(film_filefolder.ZP_SCAN_PATH_ID)

        for zp_scan_path_id in zp_scan_path_id_list:
            scan_path_dict = self.get_scan_path_dict(zp_scan_path_id)
            log.debug('zp_scan_path_id %s, scan_path_dict %s', zp_scan_path_id, scan_path_dict)
            if scan_path_dict['scan_path_fs_type_id'] == 1:
                if os.path.isdir(scan_path_dict['scan_path']):
                    self.process_scan_path(scan_path_dict)
                else:
                    log.warning('%s is not a dir (scan path id %s). Will not try and verify filefolders'
                              ' as they would all fail.', scan_path_dict['scan_path'],
                              scan_path_dict['scan_path_id'])
                #time.sleep(30000)
            elif scan_path_dict['scan_path_fs_type_id'] == 2:
                smbfs_share_connection_dict = self.smbfs_share_connection_dict(
                    scan_path_dict['zp_share_id'], scan_path_dict['zp_share_server_id'],
                    scan_path_dict['zp_share_credential_id']
                )
                conn = smbfs(smbfs_share_connection_dict)
                try:
                    conn.connect()
                # todo make this more specific exceptions
                except socket.error as e:
                    log.warning('socket error %s', e)
                except smb_base.NotConnectedError as e:
                    log.warning('NotConnectedError %s', e)
                except smb_base.NotReadyError as e:
                    log.warning('NotReadyError %s', e)
                except smb_base.SMBTimeout as e:
                    log.warning('SMBTimeout %s', e)
                except SMBConnectionAssertionError as e:
                    log.warning('SMBConnectionAssertionError %s', e)
                else:
                    if conn.isdir(scan_path_dict['scan_path']):
                        self.process_scan_path(scan_path_dict, conn)
                    else:
                        log.warning('%s is not a dir (scan path id %s). Will not try and verify filefolders'
                                  ' as they would all fail.', scan_path_dict['scan_path'],
                                  scan_path_dict['scan_path_id'])
                conn.close()

    def process_scan_path(self, scan_path_dict, conn=None):
        processing_compelte = False
        session = self.Session()
        max_zp_film_filefolder_id = session.query(func.max(TABLES.ZP_FILM_FILEFOLDER.ID)).one()[0]
        session.close()
        if isinstance(max_zp_film_filefolder_id, int):
            zp_film_filefolder_id = max_zp_film_filefolder_id + 1
            while processing_compelte is False:
                zp_film_filefolder_processing_dict = self.get_filefolder_processing_dict(scan_path_dict['scan_path_id'],
                                                                                         zp_film_filefolder_id)
                if zp_film_filefolder_processing_dict:
                    for zp_film_filefolder_processing_id in reversed(sorted(zp_film_filefolder_processing_dict)):
                        zp_film_filefolder_id = zp_film_filefolder_processing_id
                        self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                     22,
                                                                     'Checking: FileFolder %s/%s' %
                                                                     (zp_film_filefolder_processing_id,
                                                                      max_zp_film_filefolder_id)
                                                                     )
                        if scan_path_dict['scan_path_fs_type_id'] == 1:
                            self.process_local_filefolder(
                                scan_path_dict['scan_path'],
                                zp_film_filefolder_processing_dict[zp_film_filefolder_id]['scan_path_sub_dir'],
                                zp_film_filefolder_processing_dict[zp_film_filefolder_id]['last_path'],
                                zp_film_filefolder_processing_dict[zp_film_filefolder_id]['is_file'],
                                zp_film_filefolder_processing_dict[zp_film_filefolder_id]['enabled'],
                                zp_film_filefolder_id
                            )
                        elif scan_path_dict['scan_path_fs_type_id'] == 2:
                            self.process_smbfs_filefolder(
                                scan_path_dict['scan_path'],
                                zp_film_filefolder_processing_dict[zp_film_filefolder_id]['scan_path_sub_dir'],
                                zp_film_filefolder_processing_dict[zp_film_filefolder_id]['last_path'],
                                zp_film_filefolder_processing_dict[zp_film_filefolder_id]['is_file'],
                                zp_film_filefolder_processing_dict[zp_film_filefolder_id]['enabled'],
                                zp_film_filefolder_id,
                                conn)
                else:
                    processing_compelte = True
        else:
            log.debug('There are not any entries in TABLES.ZP_FILM_FILEFOLDER')


    def process_local_filefolder(self, scan_path, scan_path_sub_dir, last_path, is_file, enabled, zp_film_filefolder_id):
        local_path = os.path.join(
            scan_path,
            scan_path_sub_dir,
            last_path
        )
        filefolder_exists = self.verify_local_filefolder_exists(
            local_path,
            is_file
        )
        if (filefolder_exists is True and enabled == 0):
            self.set_filefolder_enabled_state(zp_film_filefolder_id, 1)
            log.warning('set local_path %s to enabled 1', local_path)
        elif (filefolder_exists is False and enabled == 1):
            self.set_filefolder_enabled_state(zp_film_filefolder_id, 0)
            log.warning('set local_path %s to enabled 0', local_path)

    def process_smbfs_filefolder(self, scan_path, scan_path_sub_dir, last_path, is_file, enabled,
                                 zp_film_filefolder_id, conn):
        remote_path = conn.join(
            scan_path,
            scan_path_sub_dir,
            last_path
        )
        filefolder_exists = self.verify_smbfs_filefolder_exists(
            remote_path,
            is_file,
            conn
        )
        if (filefolder_exists is True and enabled == 0):
            self.set_filefolder_enabled_state(zp_film_filefolder_id, 1)
            log.warning('set remote_path %s to enabled 1', remote_path)
        elif (filefolder_exists is False and enabled == 1):
            self.set_filefolder_enabled_state(zp_film_filefolder_id, 0)
            log.warning('set remote_path %s to enabled 0', remote_path)

    def verify_local_filefolder_exists(self, local_path, is_file):
        filefolder_exists = False
        if is_file is True:
            if os.path.isfile(local_path):
                log.debug('local_path %s is a file. GOOD', local_path)
                filefolder_exists = True
            elif os.path.exists(local_path):
                log.warning('local_path %s is not a file. BAD', local_path)
            else:
                log.warning('local_path %s does not exist. BAD', local_path)
        else:
            if os.path.isdir(local_path):
                log.debug('local_path %s is a folder. GOOD', local_path)
                filefolder_exists = True
            elif os.path.exists(local_path):
                log.warning('local_path %s is not a folder. BAD', local_path)
            else:
                log.warning('local_path %s does not exist. BAD', local_path)
        return filefolder_exists

    def verify_smbfs_filefolder_exists(self, remote_path, is_file, conn):
        filefolder_exists = False
        if is_file is True:
            if conn.isfile(remote_path):
                log.debug('local_path %s is a file. GOOD', remote_path)
                filefolder_exists = True
            elif conn.isdir(remote_path):
                log.warning('local_path %s is not a file. BAD', remote_path)
            else:
                log.warning('local_path %s does not exist. BAD', remote_path)
        else:
            if conn.isdir(remote_path):
                log.debug('local_path %s is a folder. GOOD', remote_path)
                filefolder_exists = True
            elif conn.isfile(remote_path):
                log.warning('local_path %s is not a folder. BAD', remote_path)
            else:
                log.warning('local_path %s does not exist. BAD', remote_path)
        return filefolder_exists

    def get_filefolder_processing_dict(self, zp_scan_path_id, zp_film_filefolder_id):
        session = self.Session()
        return_dict = {}
        qry_zp_film_filefolder = session.query(TABLES.ZP_FILM_FILEFOLDER).filter(
            TABLES.ZP_FILM_FILEFOLDER.ID < zp_film_filefolder_id,
            TABLES.ZP_FILM_FILEFOLDER.ZP_SCAN_PATH_ID == zp_scan_path_id
        )
        rslt_zp_film_filefolder = qry_zp_film_filefolder.order_by(TABLES.ZP_FILM_FILEFOLDER.ID.desc()).limit(100)
        session.close()
        try:
            for zp_film_filefolder in rslt_zp_film_filefolder:
                return_dict[zp_film_filefolder.ID] = {}
                return_dict[zp_film_filefolder.ID]['scan_path_sub_dir'] = zp_film_filefolder.SCAN_PATH_SUB_DIR
                return_dict[zp_film_filefolder.ID]['last_path'] = zp_film_filefolder.LAST_PATH
                return_dict[zp_film_filefolder.ID]['enabled'] = zp_film_filefolder.ENABLED
                if zp_film_filefolder.ZP_FILM_FOLDER_TYPE_ID is None or zp_film_filefolder.ZP_FILM_FOLDER_TYPE_ID == 1:
                    return_dict[zp_film_filefolder.ID]['is_file'] = True
                else:
                    return_dict[zp_film_filefolder.ID]['is_file'] = False
        except TypeError:
            log.debug('No results with zp_film_filefolder_id %s, zp_scan_path_id %s',
                      zp_film_filefolder_id,
                      zp_scan_path_id)
        return return_dict
