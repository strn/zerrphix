import logging
import re

from sqlalchemy import case
from sqlalchemy import func
# from PIL import Image
from sqlalchemy import orm

from zerrphix.db import commit
from zerrphix.db import flush
from zerrphix.db.tables import TABLES
from zerrphix.tv.util import update_tv_last_mod, update_tv_episode_last_mod
from zerrphix.util.plugin import create_eapi_dict
from zerrphix.util.text import date_time
from six import string_types
import os
from smb import base as smb_base
from zerrphix.util.extra import AESCipher
from zerrphix.util.extra import z
from zerrphix.base import Base
from zerrphix.util.filesystem import smbfs, SMBConnectionAssertionError
import socket
import datetime
import time

log = logging.getLogger(__name__)


class AdminHTTPScanPathFuncs(Base):
    def __init__(self, Session, global_config_dict):
        # logging.config.dictConfig(LOG_SETTINGS)
        super(AdminHTTPScanPathFuncs, self).__init__(args=[],
            Session=Session,
            global_config_dict=global_config_dict,
            library_config_dict={}
        )
        #self.Session = Session
        #self.global_config_dict = global_config_dict
        self.eapi_dict = create_eapi_dict(Session)
        self.image_type_id_dict = {'poster': 1, 'backdrop': 2, 'banner': 3}
        self.image_tv_entity_type_id_dict = {'poster': 3, 'backdrop': 4, 'banner': 5}
        self.image_season_type_id_dict = {'poster': 1}
        self.image_tv_season_entity_type_id_dict = {'poster': 1}
        self.image_tv_season_user_entity_type_id_dict = {'poster': 1}
        self.image_episode_type_id_dict = {'screenshot': 4}
        self.image_tv_episode_entity_type_id_dict = {'screenshot': 4}
        self.image_tv_episode_user_entity_type_id_dict = {'screenshot': 3}

    def scan_path_list(self):
        scan_path_list = []
        session = self.Session()
        zp_scan_path_run = session.query(
            TABLES.ZP_SCAN_PATH, TABLES.ZP_SCAN_PATH_SHARE_XREF
        ).outerjoin(
            TABLES.ZP_SCAN_PATH_SHARE_XREF,
            TABLES.ZP_SCAN_PATH_SHARE_XREF.ZP_SCAN_PATH_ID == TABLES.ZP_SCAN_PATH.ID
        ).order_by(
            TABLES.ZP_SCAN_PATH.ZP_LIBRARY_ID.asc(),
            TABLES.ZP_SCAN_PATH.PATH.asc()
        ).all()
        if zp_scan_path_run is not None:
            for scan_path in zp_scan_path_run:
                temp_dict = {'zp_scan_path_id':scan_path.ZP_SCAN_PATH.ID,
                                       'path': scan_path.ZP_SCAN_PATH.PATH,
                                       'zp_library_id': scan_path.ZP_SCAN_PATH.ZP_LIBRARY_ID,
                                       'fs_type': scan_path.ZP_SCAN_PATH.ZP_SCAN_PATH_FS_TYPE_ID,
                                       'last_mod': scan_path.ZP_SCAN_PATH.LAST_MOD_DATETIME,
                                       'force_full_scan': scan_path.ZP_SCAN_PATH.FORCE_FULL_SCAN,
                                       'always_full_scan': scan_path.ZP_SCAN_PATH.ALWAYS_FULL_SCAN,
                                       'enabled': scan_path.ZP_SCAN_PATH.ENABLED,
                                       'verify': scan_path.ZP_SCAN_PATH.VERIFY,
                                       'zp_share_id': None,
                                       'zp_share_server_id': None,
                                       'zp_share_credential_id': None
                             }
                if scan_path.ZP_SCAN_PATH_SHARE_XREF is not None and scan_path.ZP_SCAN_PATH.ZP_SCAN_PATH_FS_TYPE_ID > 1:
                    temp_dict['zp_share_id'] = scan_path.ZP_SCAN_PATH_SHARE_XREF.ZP_SHARE_ID
                    temp_dict['zp_share_server_id'] = scan_path.ZP_SCAN_PATH_SHARE_XREF.ZP_SHARE_SERVER_ID
                    temp_dict['zp_share_credential_id'] = scan_path.ZP_SCAN_PATH_SHARE_XREF.ZP_SHARE_CREDENTIAL_ID
                scan_path_list.append(temp_dict)
        session.close()
        return scan_path_list

    def update_scan_path(self, zp_scan_path_id, path, zp_scan_path_fs_type_id,
                         force_full_scan, always_full_scan, enabled, verify, zp_share_id=None, zp_share_server_id=None,
                         zp_share_credential_id=None):
        #print(dir(logging.getLoggerClass()))
        #print(dir(log))
        log.trace(locals())
        session = self.Session()
        session.query(TABLES.ZP_SCAN_PATH).filter(TABLES.ZP_SCAN_PATH.ID == zp_scan_path_id).update(
            {'PATH': path,
             'ZP_SCAN_PATH_FS_TYPE_ID': zp_scan_path_fs_type_id,
             'FORCE_FULL_SCAN': force_full_scan,
             'ALWAYS_FULL_SCAN': always_full_scan,
             'ENABLED': enabled,
             'VERIFY': verify
             }
        )
        flush(session)
        if (isinstance(zp_share_id, int) and isinstance(zp_share_server_id, int)
            and isinstance(zp_share_credential_id, int)):
            try:
                zp_scan_path_xref = session.query(TABLES.ZP_SCAN_PATH_SHARE_XREF).filter(
                    TABLES.ZP_SCAN_PATH_SHARE_XREF.ZP_SCAN_PATH_ID == zp_scan_path_id).one()
            except orm.exc.NoResultFound:
                add_zp_scan_path_xref = TABLES.ZP_SCAN_PATH_SHARE_XREF(ZP_SCAN_PATH_ID=zp_scan_path_id,
                                                                       ENABLED=enabled,
                                                                       VERIFY=verify,
                                                                       ZP_SHARE_ID=zp_share_id,
                                                                       ZP_SHARE_SERVER_ID=zp_share_server_id,
                                                                       ZP_SHARE_CREDENTIAL_ID=zp_share_credential_id
                                                                       )
                session.add(add_zp_scan_path_xref)
            else:
                zp_scan_path_xref.ZP_SHARE_ID=zp_share_id
                zp_scan_path_xref.ZP_SHARE_SERVER_ID=zp_share_server_id
                zp_scan_path_xref.ZP_SHARE_CREDENTIAL_ID=zp_share_credential_id
                zp_scan_path_xref.ENABLED=enabled
                zp_scan_path_xref.VERIFY=verify
        commit(session)
        session.close()

    def test_new_share(self, path, zp_share_id, zp_share_server_id,
                       zp_share_credential_id):
        smbfs_share_connection_dict = self.smbfs_share_connection_dict(
            zp_share_id, zp_share_server_id,
            zp_share_credential_id
        )
        #print(smbfs_share_connection_dict)
        conn = smbfs(smbfs_share_connection_dict)
        can_connect = False
        is_dir = False
        is_file = False
        num_filefolders = False
        error_text = ''
        try:
            conn.connect()
        # todo make this more specific exceptions
        except socket.error as e:
            error_text = str(e)
        except smb_base.NotConnectedError as e:
            error_text = str(e)
        except smb_base.NotReadyError as e:
            error_text = str(e)
        except smb_base.SMBTimeout as e:
            error_text = str(e)
        except SMBConnectionAssertionError as e:
            error_text = str(e)
            #log.error(str(e))
        else:
            can_connect = True
            if path[:1] != '/':
                path = '/%s' % path
            if conn.isdir(path) is True:
                is_dir = True
                num_filefolders = len(conn.listdir(path))
            elif conn.isfile(path) is True:
                is_file = True
                error_text = 'Path %s is a file' % path
        conn.close()
        return can_connect, is_dir, is_file, num_filefolders, error_text

    def add_scan_path(self, path, zp_library_id, zp_scan_path_fs_type_id,
                         force_full_scan, always_full_scan, zp_share_id=None, zp_share_server_id=None,
                         zp_share_credential_id=None):
        session = self.Session()
        try:
            if zp_scan_path_fs_type_id == 2:
                session.query(
                    TABLES.ZP_SCAN_PATH
                ).join(
                    TABLES.ZP_SCAN_PATH_SHARE_XREF, TABLES.ZP_SCAN_PATH_SHARE_XREF.ZP_SCAN_PATH_ID == \
                                                    TABLES.ZP_SCAN_PATH.ID
                ).filter(
                    TABLES.ZP_SCAN_PATH.PATH == path,
                    TABLES.ZP_SCAN_PATH.ZP_SCAN_PATH_FS_TYPE_ID == zp_scan_path_fs_type_id,
                    TABLES.ZP_SCAN_PATH_SHARE_XREF.ZP_SHARE_ID == zp_share_id,
                    TABLES.ZP_SCAN_PATH_SHARE_XREF.ZP_SHARE_SERVER_ID == zp_share_server_id
                ).one()
            else:
                session.query(
                    TABLES.ZP_SCAN_PATH
                ).filter(
                    TABLES.ZP_SCAN_PATH.PATH == path
                ).one()
        except orm.exc.NoResultFound:
            add_zp_scan_path = TABLES.ZP_SCAN_PATH(PATH=path,
                                                   ZP_LIBRARY_ID=zp_library_id,
                                                   ZP_SCAN_PATH_FS_TYPE_ID=zp_scan_path_fs_type_id,
                                                   LAST_MOD_DATETIME=datetime.datetime.fromtimestamp(0).strftime("%Y-%m-%d %H:%M:%S"),
                                                   LAST_SCAN_DATETIME=datetime.datetime.fromtimestamp(0).strftime("%Y-%m-%d %H:%M:%S"),
                                                   FORCE_FULL_SCAN=force_full_scan,
                                                   ALWAYS_FULL_SCAN=always_full_scan,
                                                   )
            session.add(add_zp_scan_path)
            flush(session)
            if (isinstance(zp_share_id, int) and isinstance(zp_share_server_id, int)
                and isinstance(zp_share_credential_id, int)):
                add_zp_scan_path_xref = TABLES.ZP_SCAN_PATH_SHARE_XREF(ZP_SCAN_PATH_ID=add_zp_scan_path.ID,
                                                                       ZP_SHARE_ID=zp_share_id,
                                                                       ZP_SHARE_SERVER_ID=zp_share_server_id,
                                                                       ZP_SHARE_CREDENTIAL_ID=zp_share_credential_id
                                                                       )
                session.add(add_zp_scan_path_xref)
            commit(session)
        session.close()

    def get_share_list(self):
        session = self.Session()
        return_list = []
        zp_share = session.query(TABLES.ZP_SHARE).all()
        for share in zp_share:
            return_list.append({'zp_share_id': share.ID,
                                'ref_name': share.REF_NAME,
                                'share_name': share.SHARE_NAME,
                                'domain': share.DOMAIN})
        session.close()
        return return_list

    def get_server_list(self):
        session = self.Session()
        return_list = []
        zp_share_server = session.query(TABLES.ZP_SHARE_SERVER).all()
        for share_server in zp_share_server:
            return_list.append({'zp_share_server_id': share_server.ID,
                                'ref_name': share_server.REF_NAME,
                                'remote_name': share_server.REMOTE_NAME,
                                'hostname': share_server.HOSTNAME,
                                'port': share_server.PORT})
        session.close()
        return return_list

    def get_credential_list(self):
        session = self.Session()
        return_list = []
        zp_share_server = session.query(TABLES.ZP_SHARE_CREDENTIAL).all()
        for share_server in zp_share_server:
            return_list.append({'zp_share_credential_id': share_server.ID,
                                'ref_name': share_server.REF_NAME,
                                'zp_cred_u': share_server.USERNAME,
                                'zp_cred_p': '*****'})
        session.close()
        return return_list

    def update_share(self, zp_share_id, ref_name, share_name, domain):
        session = self.Session()
        session.query(TABLES.ZP_SHARE).filter(
            TABLES.ZP_SHARE.ID == zp_share_id).update(
            {"REF_NAME": ref_name,
             'SHARE_NAME':share_name,
             'DOMAIN': domain}
        )
        commit(session)
        session.close()

    def add_share(self, ref_name, share_name, domain):
        session = self.Session()
        add_zp_share = TABLES.ZP_SHARE(
            REF_NAME=ref_name,
            SHARE_NAME=share_name,
            DOMAIN=domain
        )
        session.add(add_zp_share)
        commit(session)
        session.close()

    def update_share_server(self, zp_share_server_id, ref_name, remote_name, hostname, port):
        session = self.Session()
        session.query(TABLES.ZP_SHARE_SERVER).filter(
            TABLES.ZP_SHARE_SERVER.ID == zp_share_server_id).update(
            {"REF_NAME": ref_name,
                "REMOTE_NAME": remote_name,
             'HOSTNAME': hostname,
             'PORT': port}
        )
        commit(session)
        session.close()

    def add_share_server(self, ref_name, remote_name, hostname, port):
        session = self.Session()
        add_zp_share = TABLES.ZP_SHARE_SERVER(
            REF_NAME=ref_name,
            REMOTE_NAME=remote_name,
            HOSTNAME=hostname,
            PORT=port
        )
        session.add(add_zp_share)
        commit(session)
        session.close()

    def update_share_credential(self, zp_share_credential_id, ref_name, username, password):
        session = self.Session()
        if password and password != '*****':
            session.query(TABLES.ZP_SHARE_CREDENTIAL).filter(
                TABLES.ZP_SHARE_CREDENTIAL.ID == zp_share_credential_id
            ).update(
                {"REF_NAME": ref_name,
                 'USERNAME': username,
                 'PASSWORD': AESCipher(z(self.global_config_dict['holder'])).v(password)})
        else:
            session.query(TABLES.ZP_SHARE_CREDENTIAL).filter(
                TABLES.ZP_SHARE_CREDENTIAL.ID == zp_share_credential_id
            ).update(
                {"REF_NAME": ref_name,
                 'USERNAME': username})
        commit(session)
        session.close()

    def add_share_credential(self, ref_name, username, password):
        session = self.Session()
        add_zp_share = TABLES.ZP_SHARE_CREDENTIAL(
            REF_NAME=ref_name,
            USERNAME=username,
            PASSWORD=AESCipher(z(self.global_config_dict['holder'])).v(password)
        )
        session.add(add_zp_share)
        commit(session)
        session.close()

    def get_share_dict(self):
        session = self.Session()
        return_dict = {0: {'name': 'Choose'}}
        zp_share = session.query(TABLES.ZP_SHARE).all()
        for share in zp_share:
            return_dict[share.ID] = {}
            return_dict[share.ID]['name'] = share.REF_NAME
        session.close()
        return return_dict

    def get_share_server_dict(self):
        session = self.Session()
        return_dict = {0: {'name': 'Choose'}}
        zp_share_server = session.query(TABLES.ZP_SHARE_SERVER).all()
        for share_server in zp_share_server:
            return_dict[share_server.ID] = {}
            return_dict[share_server.ID]['name'] = share_server.REF_NAME
        session.close()
        return return_dict

    def get_share_credential_dict(self):
        session = self.Session()
        return_dict = {0: {'name': 'Choose'}}
        zp_share_credential = session.query(TABLES.ZP_SHARE_CREDENTIAL).all()
        for share_credential in zp_share_credential:
            return_dict[share_credential.ID] = {}
            return_dict[share_credential.ID]['name'] = share_credential.REF_NAME
        session.close()
        return return_dict

    def set_scan_path_section(self, zp_scan_path_id, section, scan_path_section_value):
        session = self.Session()
        sucess = False
        log.debug('zp_scan_path_id %s, section %s, scan_path_section_value %s', zp_scan_path_id, section,
                  scan_path_section_value)
        try:
            zp_scan_path_run = session.query(TABLES.ZP_PROCESS_RUN).filter(
                TABLES.ZP_PROCESS_RUN.ZP_PROCESS_ID == zp_scan_path_id
            ).one()
        except orm.exc.NoResultFound:
            log.error('zp_scan_path_id %s not found in ZP_PROCESS_RUN', zp_scan_path_id)
        else:
            if section in ['enabled', 'run_between', 'force_run']:
                if scan_path_section_value == '1' or scan_path_section_value == '0':
                    if section == 'enabled':
                        zp_scan_path_run.ENABLED = scan_path_section_value
                    elif section == 'force_run':
                        zp_scan_path_run.FORCE_RUN = scan_path_section_value
                    else:
                        zp_scan_path_run.RUN_BETWEEN = scan_path_section_value
                    if commit(session):
                        sucess = True
            elif section == 'interval':
                if scan_path_section_value.isdigit():
                    zp_scan_path_run.INTERVAL = scan_path_section_value
            elif section == 'run_between_start' or section == 'run_between_end':
                scan_path_section_value_len = len(scan_path_section_value)
                if scan_path_section_value_len in [3,4]:
                    if scan_path_section_value_len == 3:
                        scan_path_section_value = '0%s' % scan_path_section_value
                    try:
                        time.strptime(scan_path_section_value, '%H%M')
                    except ValueError:
                        log.error('scan_path_section_value %s should be in 24hour fromat HHMM e.g. 0600',
                                  scan_path_section_value)
                    else:
                        if section == 'run_between_start':
                            zp_scan_path_run.RUN_BETWEEN_START = scan_path_section_value
                        else:
                            zp_scan_path_run.RUN_BETWEEN_END = scan_path_section_value
                else:
                    log.error('scan_path_section_value %s len %s needs to be 3 or 4', scan_path_section_value,
                        scan_path_section_value_len)
            else:
                log.error('section %s not supported', section)
            if commit(session):
                sucess = True
        session.close()
        return sucess