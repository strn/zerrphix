# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import os.path
import re
from zerrphix.util.filesystem import smbfs
from pymediainfo import MediaInfo
from zerrphix.pymediainfo import MediaInfo as MediaInfo_pysmb
from zerrphix.util.filesystem import SMB_Buffer_Wrapper
from six import string_types
from zerrphix.constants import pattern_video_source_dict, pattern_video_res_dict
from zerrphix.db import commit
from zerrphix.db.tables import TABLES
from zerrphix.util.filesystem import (get_filename_root)
#from zerrphix.util import smbfs_connection_dict_scan_path
from zerrphix.util import smbfs_mediainfo
from sqlalchemy import func
from zerrphix.film.base import FilmBase
import time

log = logging.getLogger(__name__)


class Score(FilmBase):
    """
    Scans for films that are not yet in the db
    """

    def __init__(self, **kwargs):
        super(Score, self).__init__(**kwargs)
        """
        """
        session = self.Session()
        self.source_dict = self._construct_source_dict()
        log.debug('self.source_dict: {0}'.format(
            self.source_dict))
        self.res_dict = self._construct_res_dict()
        log.debug('self.res_dict: {0}'.format(
            self.res_dict))
        # TODO: this is used in at least Scan and Detect
        self.folder_type_dict = self._construct_folder_types_dict()
        log.debug('self.folder_type_dict: {0}'.format(
            self.folder_type_dict))
        session.close()

    def _construct_source_dict(self):
        session = self.Session()
        return_dict = {}
        query = session.query(TABLES.ZP_SOURCE).all()
        for source in query:
            return_dict[source.SOURCE] = {}
            for field in TABLES.ZP_SOURCE.__table__.columns._data.keys():
                return_dict[source.SOURCE][field] = getattr(source, field)
        session.close()
        return return_dict

    def _construct_res_dict(self):
        session = self.Session()
        return_dict = {}
        query = session.query(TABLES.ZP_RES).all()
        for res in query:
            return_dict[res.RES] = {}
            for field in TABLES.ZP_RES.__table__.columns._data.keys():
                return_dict[res.RES][field] = getattr(res, field)
        session.close()
        return return_dict

    def _construct_folder_types_dict(self):
        # TODO: make this a generic function to populate a table in a dict
        session = self.Session()
        return_dict = {}
        folder_types_query = session.query(TABLES.ZP_FOLDER_TYPE).all()
        for folder_type in folder_types_query:
            return_dict[folder_type.ID] = {}
            for field in TABLES.ZP_FOLDER_TYPE.__table__.columns._data.keys():
                return_dict[folder_type.ID][field] = getattr(folder_type, field)
        session.close()
        return return_dict

    def get_film_score_processing_dict(self, zp_filefolder_id):
        session = self.Session()
        return_dict = {}
        qry_filefolders_no_score = session.query(
            TABLES.ZP_FILM_FILEFOLDER.LAST_PATH,
            TABLES.ZP_FILM_FILEFOLDER.SCAN_PATH_SUB_DIR,
            TABLES.ZP_FILM_FILEFOLDER.ID,
            TABLES.ZP_FILM_FILEFOLDER.ZP_SCAN_PATH_ID,
            TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_FOLDER_TYPE_ID,
            TABLES.ZP_SCAN_PATH.ZP_SCAN_PATH_FS_TYPE_ID,
            TABLES.ZP_SCAN_PATH.PATH
        ).filter(
            TABLES.ZP_FILM_FILEFOLDER.ID < zp_filefolder_id,
            ~TABLES.ZP_FILM_FILEFOLDER.ID.in_(
                session.query(
                    TABLES.ZP_FILM_FILEFOLDER_SCORE.ZP_FILM_FILEFOLDER_ID)),
            TABLES.ZP_SCAN_PATH.ID == TABLES.ZP_FILM_FILEFOLDER.ZP_SCAN_PATH_ID
        )

        qry_filefolders_no_score_count = qry_filefolders_no_score.count()
        log.debug('qry_filefolders_no_score_count: %s', qry_filefolders_no_score_count)
        if qry_filefolders_no_score_count > 0:
            filefolders_no_score = qry_filefolders_no_score.order_by(TABLES.ZP_FILM_FILEFOLDER.ID.desc()).limit(100)
            session.close()
            for result in filefolders_no_score:
                return_dict[result.ID] = {}
                return_dict[result.ID]['LAST_PATH'] = result.LAST_PATH
                return_dict[result.ID]['SCAN_PATH_SUB_DIR'] = result.SCAN_PATH_SUB_DIR
                return_dict[result.ID]['ZP_SCAN_PATH_ID'] = result.ZP_SCAN_PATH_ID
                return_dict[result.ID]['ZP_FILM_FOLDER_TYPE_ID'] = result.ZP_FILM_FOLDER_TYPE_ID
                return_dict[result.ID]['ZP_SCAN_PATH_FS_TYPE_ID'] = result.ZP_SCAN_PATH_FS_TYPE_ID
                return_dict[result.ID]['PATH'] = result.PATH
        log.debug(return_dict)
        return return_dict

    def calculate(self):
        # TODO: pagintation
        session = self.Session()
        max_zp_filefolder_id = session.query(func.max(TABLES.ZP_FILM_FILEFOLDER.ID)).one()[0]
        session.close()
        film_processing_complete = False
        if isinstance(max_zp_filefolder_id, int):
            zp_filefolder_id = max_zp_filefolder_id + 1
            while film_processing_complete is False:
                film_processing_dict = self.get_film_score_processing_dict(zp_filefolder_id)
                if film_processing_dict:
                    for film_processing_dict_id in film_processing_dict:
                        zp_filefolder_id = film_processing_dict_id
                        self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                     3,
                                                                     'Calculating Internal Score: %s/%s'
                                                                     % (zp_filefolder_id,
                                                                        max_zp_filefolder_id))
                        zp_scan_path_id = film_processing_dict[film_processing_dict_id]['ZP_SCAN_PATH_ID']
                        last_path = film_processing_dict[film_processing_dict_id]['LAST_PATH']
                        scan_path_sub_dir = film_processing_dict[film_processing_dict_id]['SCAN_PATH_SUB_DIR']
                        zp_scan_path = film_processing_dict[film_processing_dict_id]['PATH']
                        zp_scan_fs_type_id = film_processing_dict[film_processing_dict_id]['ZP_SCAN_PATH_FS_TYPE_ID']
                        zp_folder_type_id = film_processing_dict[film_processing_dict_id]['ZP_FILM_FOLDER_TYPE_ID']
                        self.calculate_filefolder_score(zp_filefolder_id, zp_folder_type_id, zp_scan_path_id, zp_scan_fs_type_id,
                                                 zp_scan_path,
                                                 scan_path_sub_dir, last_path)
                else:
                    film_processing_complete = True

    def calculate_filefolder_score(self, zp_filefolder_id, zp_folder_type_id, zp_scan_path_id, zp_scan_fs_type_id,
                        zp_scan_path, scan_path_sub_dir, last_path):

        zp_res_id = None
        smbcon = None
        if zp_scan_fs_type_id == 1:
            filefolder_path = os.path.join(zp_scan_path, scan_path_sub_dir, last_path)
        elif zp_scan_fs_type_id == 2:
            smbfs_connection_dict = self.smbfs_connection_dict_scan_path(zp_scan_path_id)
            smbcon = smbfs(smbfs_connection_dict)
            filefolder_path = smbfs.join(zp_scan_path, scan_path_sub_dir, last_path)
        else:
            log.error('zp_scan_fs_type_id %s is not 1 or 2', zp_scan_fs_type_id)
            filefolder_path = None

        if isinstance(filefolder_path, string_types):
            filefolder_score = {'score': 0}
            is_file = False
            if zp_scan_fs_type_id == 1:
                if os.path.isfile(filefolder_path):
                    is_file = True
            elif zp_scan_fs_type_id == 2:
                if smbcon.isfile(filefolder_path):
                    is_file = True
            if is_file is True:
                log.debug('filefolder_path: {0} is a file'.format(filefolder_path))
                filename_list = [last_path,
                                 scan_path_sub_dir]
                filefolder_score = self.calculate_file_score(filefolder_path, filename_list, zp_scan_fs_type_id,
                                                             smbcon=smbcon)
                log.debug('file: {0} score: {0}'.format( filefolder_path, filefolder_score))
            else:
                is_dir = False
                if zp_scan_fs_type_id == 1:
                    if os.path.isdir(filefolder_path):
                        is_dir = True
                elif zp_scan_fs_type_id == 2:
                    if smbcon.isdir(filefolder_path):
                        is_dir = True
                if is_dir is True:
                    log.debug('filefolder_path: {0} is a directory'.format(filefolder_path))
                    filefolder_score['res'] = \
                    self.res_dict[self.folder_type_dict[zp_folder_type_id]['ZP_RES_RES']]['SCORE']
                    filefolder_score['source'] = \
                    self.source_dict[self.folder_type_dict[zp_folder_type_id]['ZP_SOURCE_SOURCE']]['SCORE']
                    filefolder_score['disc'] = \
                    self.source_dict[self.folder_type_dict[zp_folder_type_id]['ZP_SOURCE_SOURCE']][
                        'DISC_SCORE']
                    filefolder_score['score'] = filefolder_score['res'] + filefolder_score['source'] + filefolder_score[
                        'disc']
                    filefolder_score['ZP_RES_ID'] = \
                    self.res_dict[self.folder_type_dict[zp_folder_type_id]['ZP_RES_RES']]['ID']
                    filefolder_score['ZP_SOURCE_ID'] = \
                    self.source_dict[self.folder_type_dict[zp_folder_type_id]['ZP_SOURCE_SOURCE']]['ID']
                    log.debug('dir: {0} score: {0}'.format(
                        filefolder_path, filefolder_score))
                else:
                    log.warning('filefolder_path: {0} is not a file or folder. does it exist?'.format(filefolder_path))

            if (filefolder_score.has_key('ZP_RES_ID') and
                    filefolder_score.has_key('ZP_SOURCE_ID') and
                    filefolder_score.has_key('disc')):
                log.debug('filefolder_path: {0}, filefolder_score: {1}'.format(
                    filefolder_path,
                    filefolder_score))
                zp_res_id = filefolder_score['ZP_RES_ID']
                self.set_film_filefolder_score(zp_filefolder_id, filefolder_score['score'],
                                               filefolder_score['ZP_SOURCE_ID'], zp_res_id,
                                                                            filefolder_score['disc'])
        self.set_filefolder_res(zp_filefolder_id, zp_res_id)
        if hasattr(smbcon, 'close'):
            smbcon.close()

    def set_filefolder_res(self, zp_filefolder_id, zp_res_id):
        res_dict = {8:'HD', 9:'FHD', 10:'UHD'}
        if zp_res_id in res_dict:
            session = self.Session()
            session.query(TABLES.ZP_FILM_FILEFOLDER).filter(TABLES.ZP_FILM_FILEFOLDER.ID == zp_filefolder_id).update(
                {res_dict[zp_res_id]: 1})
            commit(session)
            session.close()

    def set_film_filefolder_score(self, zp_filefolder_id, score, zp_source_id, zp_res_id, disc):
        session = self.Session()
        add_film_filefolder_score = TABLES.ZP_FILM_FILEFOLDER_SCORE(ZP_FILM_FILEFOLDER_ID=zp_filefolder_id,
                                                                    SCORE=score,
                                                                    ZP_SOURCE_ID=zp_source_id,
                                                                    ZP_RES_ID=zp_res_id,
                                                                    DISC=disc)
        session.add(add_film_filefolder_score)
        commit(session)
        session.close()

    def calculate_file_score(self, path, filename_list, zp_scan_fs_type_id, smbcon=None):
        return_dict = {'res': 0, 'source': 0, 'disc': 0, 'score': 0, 'ZP_SOURCE_ID': 0, 'ZP_RES_ID': 0}
        filename_root = get_filename_root(path)
        for filename in filename_list:
            for pattern in pattern_video_source_dict:
                source_search = re.search(pattern_video_source_dict[pattern], filename, flags=re.I | re.U)
                if source_search:
                    if self.source_dict[pattern]['SCORE'] > return_dict['source']:
                        return_dict['source'] = self.source_dict[pattern]['SCORE']
                        return_dict['ZP_SOURCE_ID'] = self.source_dict[pattern]['ID']
        for pattern in pattern_video_res_dict:
            res_search = re.search(pattern_video_res_dict[pattern], filename_root, flags=re.I | re.U)
            if res_search:
                return_dict['res'] = self.res_dict[pattern]['SCORE']
                return_dict['ZP_RES_ID'] = self.res_dict[pattern]['ID']
        if return_dict['res'] == 0:
            mediainfo = None
            if zp_scan_fs_type_id == 1:
                mediainfo = MediaInfo.parse(path)
            elif zp_scan_fs_type_id == 2:
                file_obj = SMB_Buffer_Wrapper(smbcon, path, bytes_to_read=7 * 188 * 200)
                mediainfo = MediaInfo_pysmb.parse(file_obj=file_obj)
                #mediainfo = smbfs_mediainfo(path, smbcon)
            if isinstance(mediainfo, MediaInfo) or isinstance(mediainfo, MediaInfo_pysmb):
                res_dict = self.medinafo_res(mediainfo, path)
                if isinstance(res_dict, dict):
                    log.debug('''res_dict['SCORE'] %s, res_dict['ID'] %s''', res_dict['SCORE'], res_dict['ID'])
                    return_dict['res'] = res_dict['SCORE']
                    return_dict['ZP_RES_ID'] = res_dict['ID']
                else:
                    log.warning('res_dict %s is not dict but %s', res_dict, type(res_dict))
            else:
                log.warning('could not generate a MediaInfo class from path %s', path)
        return_dict['score'] = return_dict['source'] + return_dict['res']
        return return_dict

    def medinafo_res(self, mediainfo, path):
        mediainfo_width = 0
        mediainfo_height = 0
        for track in mediainfo.tracks:
            log.trace('track.track_type %s', track.track_type)
            if track.track_type == 'Video':
                mediainfo_width = track.width
                mediainfo_height = track.height
        if mediainfo_width > 0 and mediainfo_height > 0:
            for key in sorted(self.res_dict, reverse=True):
                if (mediainfo_width >= self.res_dict[key]['MIN_WIDTH']
                    and mediainfo_width <= self.res_dict[key]['MAX_WIDTH']
                    and mediainfo_height >= self.res_dict[key]['MIN_HEIGHT']
                    and mediainfo_height <= self.res_dict[key]['MAX_HEIGHT']):
                    return self.res_dict[key]
        else:
            error_text = 'could not determine a res for path %s mediainfo_width %s and mediainfo_height %s from ' \
                         ' %s' % (path, mediainfo_width, mediainfo_height, self.res_dict)
            log.debug(error_text)
            self.add_error_raised_to_db(5, error_text)
        #time.sleep(500)
        return None
