# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import os.path
import re

#from zerrphix.pymediainfo import MediaInfo
from pymediainfo import MediaInfo
from zerrphix.pymediainfo import MediaInfo as MediaInfo_pysmb
from zerrphix.util.filesystem import SMB_Buffer_Wrapper
from sqlalchemy import func, orm, and_, or_
from six import string_types
from zerrphix.db import commit
from zerrphix.db.tables import TABLES
from zerrphix.util.text import conform_track_lang
#from zerrphix.util import smbfs_connection_dict_scan_path
from zerrphix.util import smbfs_mediainfo
from zerrphix.util.filesystem import smbfs, get_file_extension
from zerrphix.film.base import FilmBase
from zerrphix.util.text import bitrate_text_to_float, frame_rate_text_to_float, display_aspect_ratio_from_text
from zerrphix.util.filesystem import find_largest_file_in_dir
from zerrphix.util.text import get_higest_number_in_string
from zerrphix.util.text import xml_to_dict
import pprint
import time
import json
import xmltodict

log = logging.getLogger(__name__)

# http://blog.willbeattie.com/2010/11/mediainfo-deprecated-attributes-in.html
#

class Metadata(FilmBase):
    """Get Metadata for films (Codecs, Lang...)
    """

    def __init__(self, **kwargs):
        super(Metadata, self).__init__(**kwargs)
        """Metadata __init__

        Args:
            args (list): Passed through args from the command line.
            | Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.

        Attributes:
            Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.
            | scan_path_dict (dict): see zerrphix.film.util._get_scan_paths
        """
        #self.scan_path_dict = get_scan_paths(self.Session, 1)

    def acquire(self):
        """Get Metadata from files

        {
            "adult":true|false,
            "genres":[
                        {
                            "id": unicode,
                            "Name": unicode
                        }
                    ],
            "title": unicode,
            "original_title": unicode,
            "overview": unicode,
            "release_date": YYYY-MM-DD
            "runtime": int
            "rating": float (0.0 - 10.0)
            "credits": {
                            "cast":
                                    [
                                        {
                                            "id": unicode,
                                            "name": unicode,
                                            "character": unicode,
                                            "order": int
                                        }
                                    ],
                            "crew":
                                    [
                                        {
                                            "id": unicode,
                                            "name": unicode,
                                            "role": unicode,
                                            "order": int
                                        }
                                    ]
                        }
        }
        """
        # TODO: do not process any filefolder that allready has and entry for vcodec and acodec
        # TODO: add languages from http://www.science.co.il/Language/Codes.php
        session = self.Session()
        max_filefolder_id = session.query(func.max(TABLES.ZP_FILM_FILEFOLDER.ID)).one()[0]
        session.close()
        filefolder_processing_complete = False
        #global res_dict
        #res_dict = {}
        if isinstance(max_filefolder_id, int):
            ZP_FILM_FILEFOLDER_ID = max_filefolder_id + 1
            while filefolder_processing_complete == False:
                session = self.Session()
                # todo what to do with files that do not have both audio and video metadata
                # detectabe by mediainfo
                qry_filefolders = session.query(TABLES.ZP_FILM_FILEFOLDER.LAST_PATH,
                                                TABLES.ZP_FILM_FILEFOLDER.SCAN_PATH_SUB_DIR,
                                                TABLES.ZP_FILM_FILEFOLDER.ID,
                                                TABLES.ZP_FILM_FILEFOLDER.ZP_SCAN_PATH_ID,
                                                TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_FOLDER_TYPE_ID,
                                                TABLES.ZP_SCAN_PATH.ZP_SCAN_PATH_FS_TYPE_ID,
                                                TABLES.ZP_SCAN_PATH.PATH).filter(
                    TABLES.ZP_FILM_FILEFOLDER.ID < ZP_FILM_FILEFOLDER_ID,
                    ~TABLES.ZP_FILM_FILEFOLDER.ID.in_(
                        session.query(
                            TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_FILM_FILEFOLDER_ID)),
                    ~TABLES.ZP_FILM_FILEFOLDER.ID.in_(
                        session.query(
                            TABLES.ZP_FILM_FILEFOLDER_VIDEO_METADATA.ZP_FILM_FILEFOLDER_ID)),
                    ~TABLES.ZP_FILM_FILEFOLDER.ID.in_(
                        session.query(
                            TABLES.ZP_FILM_FILEFOLDER_SCORE.ZP_FILM_FILEFOLDER_ID
                        ).filter(
                            TABLES.ZP_FILM_FILEFOLDER_SCORE.DISC == 1)
                    ),
                    # todo use tables instead
                    or_(
                        ~TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_FOLDER_TYPE_ID.in_((10, 15)),
                        TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_FOLDER_TYPE_ID == None
                    ),
                    TABLES.ZP_SCAN_PATH.ID == TABLES.ZP_FILM_FILEFOLDER.ZP_SCAN_PATH_ID
                ).order_by(
                    TABLES.ZP_FILM_FILEFOLDER.ID.desc()
                )
                    #raise SystemExit
                filfolders_missing_metadata = qry_filefolders.order_by(TABLES.ZP_FILM_FILEFOLDER.ID.desc()).limit(300)
                session.close()
                #if hasattr(self, 'text_dict_temp'):
                #    pprint.pprint(self.text_dict_temp)
                #pprint.pprint(res_dict)
                processing_list = []
                for zp_filefolder in filfolders_missing_metadata:
                    processing_list.append({'ZP_SCAN_PATH_FS_TYPE_ID': zp_filefolder.ZP_SCAN_PATH_FS_TYPE_ID,
                                            'ZP_SCAN_PATH_ID': zp_filefolder.ZP_SCAN_PATH_ID,
                                            'ID': zp_filefolder.ID,
                                            'PATH': zp_filefolder.PATH,
                                            'LAST_PATH': zp_filefolder.LAST_PATH,
                                            'SCAN_PATH_SUB_DIR': zp_filefolder.SCAN_PATH_SUB_DIR,
                                            'ZP_FILM_FOLDER_TYPE_ID': zp_filefolder.ZP_FILM_FOLDER_TYPE_ID,
                                            })
                if processing_list:
                    for filefolder in processing_list:
                        zp_scan_path_fs_type_id = filefolder['ZP_SCAN_PATH_FS_TYPE_ID']
                        zp_scan_path_id = filefolder['ZP_SCAN_PATH_ID']
                        ZP_FILM_FILEFOLDER_ID = filefolder['ID']
                        zp_scan_path = filefolder['PATH']
                        self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                     2,
                                                                     'Aquiring Metadata: %s/%s' %
                                                                     (ZP_FILM_FILEFOLDER_ID,
                                                                      max_filefolder_id))

                        filefolder_path = os.path.join(filefolder['PATH'],
                                                       filefolder['SCAN_PATH_SUB_DIR'],
                                                       filefolder['LAST_PATH'])
                        is_file = False
                        is_dir = False
                        smbcon = None
                        if zp_scan_path_fs_type_id == 1:
                            if os.path.isfile(filefolder_path):
                                is_file = True
                            elif os.path.isdir(filefolder_path):
                                is_dir = True
                        elif zp_scan_path_fs_type_id == 2:
                            smbfs_connection_dict = self.smbfs_connection_dict_scan_path(zp_scan_path_id)
                            smbcon = smbfs(smbfs_connection_dict)
                            if smbcon.isfile(filefolder_path):
                                is_file = True
                            elif smbcon.isdir(filefolder_path):
                                is_dir = True
                        if is_file is True or is_dir is True:
                            log.debug('filefolder_path: {0} for ZP_FILM_FILEFOLDER_ID: {1} is file'.format(
                                filefolder_path,
                                ZP_FILM_FILEFOLDER_ID))
                            log.debug(
                                'Starting mediainfo parsing. This can take a little time depending on the file and its size.')
                            mediainfo = None
                            mediainfo_type = None
                            if is_file is True:
                                file_path = filefolder_path
                            else:
                                log.debug('filefolder_path %s', filefolder_path)
                                log.debug("filefolder['PATH'] %s", filefolder['PATH'])
                                file_path_dict = find_largest_file_in_dir(filefolder_path, filefolder['PATH'],
                                                                          smbcon=smbcon, levels=4)
                                #log.error(pprint.pformat(file_path_dict))
                                #time.sleep(300000)
                                file_path = None
                                if isinstance(file_path_dict, dict):
                                    if 'current_walk_path' in file_path_dict:
                                        if zp_scan_path_fs_type_id == 1:
                                            file_path = os.path.join(zp_scan_path,
                                                                     file_path_dict['current_walk_path'].strip(os.sep))
                                        elif zp_scan_path_fs_type_id == 2:
                                            log.trace('zp_scan_path %s', zp_scan_path)
                                            log.trace("file_path_dict['current_walk_path'] %s",
                                                      file_path_dict['current_walk_path'])
                                            file_path = smbfs.join(zp_scan_path,
                                                                   file_path_dict['current_walk_path'].strip('/'))
                            if isinstance(file_path, string_types):
                                log.debug('filepath %s', file_path)
                                if zp_scan_path_fs_type_id == 1:
                                    mediainfo = MediaInfo.parse(file_path)
                                    mediainfo_type = 'local'
                                elif zp_scan_path_fs_type_id == 2:
                                    log.trace('zp_scan_path %s', zp_scan_path)
                                    log.trace('file_path %s', file_path)
                                    file_obj = SMB_Buffer_Wrapper(smbcon, file_path, bytes_to_read=7*188*200)
                                    mediainfo = MediaInfo_pysmb.parse(file_obj=file_obj)
                                    mediainfo_type = 'smbfs'
                                if isinstance(mediainfo, MediaInfo) or isinstance(mediainfo, MediaInfo_pysmb):
                                    #mediainfo_dict = json.loads(json.dumps(xmltodict.parse(mediainfo.raw_xml())))
                                    #pprint.pprint(mediainfo_dict)
                                    #time.sleep(30000)
                                    if hasattr(mediainfo, 'tracks'):
                                        log.debug('len tracks %s', len(mediainfo.tracks))
                                        video_track_found = False
                                        audio_track_found = False
                                        for track in mediainfo.tracks:
                                            log.trace('track.track_id %s', track.track_id)
                                            track.track_id = self.conform_track_id(track.track_id)
                                            if self.validtate_track_id(track.track_id) is True:
                                                log.debug('track.track_id %s valid', track.track_id)
                                                track_id = track.track_id
                                                log.debug('track.track_type %s', track.track_type)
                                                track_type = track.track_type.lower()
                                                log.trace('track.track_id %s, track_type %s', track.track_id, track_type)
                                                log.trace('track_type %s, file_path %s', track_type, file_path)
                                                if track_type == 'audio':
                                                    audio_track_found = True
                                                    log.trace('track type audio')
                                                    self.process_audio_track(track, track_id, ZP_FILM_FILEFOLDER_ID,
                                                                             file_path)
                                                elif track_type == 'video':
                                                    video_track_found = True
                                                    log.trace('track type video')
                                                    self.process_video_track(track, track_id, ZP_FILM_FILEFOLDER_ID,
                                                                             file_path)
                                                elif track_type == 'text':
                                                    log.trace('track type text')
                                                    self.process_text_track(track, track_id, ZP_FILM_FILEFOLDER_ID,
                                                                            file_path)
                                            elif isinstance(track.track_type, string_types):
                                                if track.track_type.lower() not in {'general', 'menu'}:
                                                    log.debug('track.track_id %s is not valid, track_type %s', track.track_id,
                                                          track.track_type)
                                            else:
                                                log.debug('track.track_id %s is not valid, track_type %s',
                                                          track.track_id,
                                                          track.track_type)
                                        if video_track_found is False:
                                            message = 'No video tracks for %s - %s - %s' % (
                                                file_path, mediainfo_type, len(mediainfo.tracks))
                                            log.warning(message)
                                            self.add_warning_raised_to_db(13, message)
                                        if audio_track_found is False:
                                            message = 'No audio tracks for %s - %s - %s' % (
                                                file_path, mediainfo_type, len(mediainfo.tracks))
                                            log.warning(message)
                                            self.add_warning_raised_to_db(13, message)
                                    else:
                                        log.warning('mediainfo does not have attr tracks %s', dir(mediainfo))
                                else:
                                    log.warning('mediainfo not of Class Mediainfo but %s, %s, %s, %s', type(mediainfo),
                                              mediainfo_type, file_path, mediainfo)
                        else:
                            log.warning(
                                ('''filefolder_path: {0} for ZP_FILM_FILEFOLDER.ID: {1} does not exist, skipping.'''
                                 ''' zp_scan_path: {2},'''
                                 ''' filefolder.SCAN_PATH_SUB_DIR: {3}, '''
                                 ''' filefolder.LAST_PATH: {4}''').format(filefolder_path,
                                                                          ZP_FILM_FILEFOLDER_ID,
                                                                          zp_scan_path,
                                                                          filefolder['SCAN_PATH_SUB_DIR'],
                                                                          filefolder['LAST_PATH']))
                else:
                    filefolder_processing_complete = True
                    session.close()
            #if hasattr(self, 'text_dict_temp'):
            #    pprint.pprint(self.text_dict_temp)
            #with open('/tmp/res_test.json', 'w') as rest:
            #    json.dump(res_dict, rest)

    def process_audio_track(self, track, track_id, ZP_FILM_FILEFOLDER_ID, filefolder_path):
        """Process audio track

            Args:
                | track (obj): mediainfo track
                | track_id (int): track id
                | ZP_FILM_FILEFOLDER_ID (int): ZP_FILM_FILEFOLDER_ID

        """
        session = self.Session()
        try:
            # check if track allready in db
            session.query(TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA).filter(
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.TRACK_ID == track_id,
                TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA.ZP_FILM_FILEFOLDER_ID == ZP_FILM_FILEFOLDER_ID).one()
        except orm.exc.NoResultFound:
            zp_codec_id = 0
            track_parsed_dict = {'codec_id': 0, 'language': '', 'channel_s': 0, 'format_profile': '',
                                 'bit_rate': '0.0', 'format': ''}
            for track_key in track_parsed_dict:
                log.debug('track_key %s', track_key)
                #track_key_conformed = track_key.lower().strip().strip('_')
                track_value_list = self.get_track_value_list(track, track_key)
                log.debug('track_value_list %s', track_value_list)
                track_parsed_dict[track_key] = self.process_track_value_list(track_key, track_value_list)
                log.debug('track_parsed_dict[track_key] %s', track_parsed_dict[track_key])

            if track_parsed_dict['language']:
                track_langauge = conform_track_lang(track.language)
                track_langauge_lower = track_langauge.lower()
                if not re.search('undefined', track_langauge, flags=re.I):
                    track_parsed_dict['zp_lang_id'] = self.zp_lang_from_text(track_langauge_lower)
            if 'zp_lang_id' not in track_parsed_dict:
                track_parsed_dict['zp_lang_id'] = 1823
                # There the track does not specify a language so will default to en
                message = ('The audio track does not specify a language or cannot identiy the language '
                           'so will default to en (1823)'
                          ' for ZP_FILM_FILEFOLDER.ID: {0}, filefolder_path {1}, track_parsed_dict {2}'
                           ).format(ZP_FILM_FILEFOLDER_ID, filefolder_path, track_parsed_dict)
                log.warning(message)
                self.add_warning_raised_to_db(12, message)

            #pprint.pprint(track_parsed_dict)
            #time.sleep(3000)
            if 'format' in track_parsed_dict:
                if track_parsed_dict['format']:
                    track_format_alphanum = re.sub(r'''[^a-z+0-9]+''', '', track_parsed_dict['format'].lower())
                    auido_format_dict = {'aac': 5, 'ac3': 3, 'eac3': 12, 'ac3+': 12, 'dts': 1, 'dtshd': 11,
                                        'flac': 8, 'mpegaudio': 0, 'pcm': 6, 'truehd': 9, 'vorbis': 7, 'wma': 13,
                                         'mp3': 4, 'mpeg 1/2 layer 2': 2, 'mpeg 1/2 layer 1': 14, 'gsm610': 15}
                    if track_format_alphanum not in auido_format_dict:
                        log.warning('track_format_alphanum %s for %s not in auido_format_dict %s', track_format_alphanum,
                                  filefolder_path, pprint.pformat(auido_format_dict))
                    else:
                        direct_set = {'aac', 'eac3', 'ac3+', 'dtshd', 'flac', 'pcm', 'truehd', 'vorbis', 'wma', 'gsm610',
                                      'atmostruehd'}
                        if track_format_alphanum in direct_set:
                            log.trace('track_format_alphanum %s in %s', track_format_alphanum, direct_set)
                            zp_codec_id = auido_format_dict[track_format_alphanum]
                        elif track_format_alphanum == 'dts':
                            log.trace('track_format_alphanum %s is dts', track_format_alphanum)
                            if re.search(r'''ma''', track_parsed_dict['format_profile'].lower(), flags=re.I):
                                log.trace('ma in %s', track_parsed_dict['format_profile'])
                                zp_codec_id = auido_format_dict['dtshd']
                            else:
                                log.trace('ma not in %s', track_parsed_dict['format_profile'])
                                zp_codec_id = auido_format_dict[track_format_alphanum]
                        elif track_format_alphanum == 'ac3':
                            log.trace('track_format_alphanum %s is ac3', track_format_alphanum)
                            if re.search(r'''e''', track_parsed_dict['codec_id'].lower(), flags=re.I):
                                log.trace('e in %s', track_parsed_dict['format_profile'])
                                zp_codec_id = auido_format_dict['eac3']
                            else:
                                log.trace('e not in %s', track_parsed_dict['format_profile'])
                                zp_codec_id = auido_format_dict[track_format_alphanum]
                        elif track_format_alphanum == 'mpegaudio':
                            log.trace('track_format_alphanum %s is mpegaudio', track_format_alphanum)
                            match = re.search(r'''(?P<layer>[123])''',
                                              track_parsed_dict['format_profile'].lower(), flags=re.I)
                            if match:
                                log.trace('1,2,3 in %s', track_parsed_dict['format_profile'])
                                match_group_dict = match.groupdict()
                                if match_group_dict['layer'] == '3':
                                    log.trace("match_group_dict['layer'] %s is 3",
                                              match_group_dict['layer'])
                                    zp_codec_id = auido_format_dict['mp3']
                                elif match_group_dict['layer'] == '2':
                                    log.trace("match_group_dict['layer'] %s is 2",
                                              match_group_dict['layer'])
                                    zp_codec_id = auido_format_dict['mpeg 1/2 layer 2']
                                elif match_group_dict['layer'] == '1':
                                    log.trace("match_group_dict['layer'] %s is 1",
                                              match_group_dict['layer'])
                                    zp_codec_id = auido_format_dict['mpeg 1/2 layer 1']
                            else:
                                log.trace('1,2,3 not in %s', track_parsed_dict['format_profile'])
                                zp_codec_id = auido_format_dict['mpeg 1/2 layer 2']
                        if zp_codec_id == 0:
                            message = ("could not get zp_codec_id from %s.  track_format_alphanum %s,"
                                       " track_parsed_dict['format_profile'] %s" % (
                                filefolder_path,
                                track_format_alphanum,
                                track_parsed_dict['format_profile']
                            ))
                            log.error(message)
                            self.add_warning_raised_to_db(11, message)
                    #pprint.pprint(track_parsed_dict)
                    #time.sleep(3000)
                    if zp_codec_id > 0:
                        add_zp_film_filefolder_audio_metadata = TABLES.ZP_FILM_FILEFOLDER_AUIDO_METADATA(
                            ZP_FILM_FILEFOLDER_ID = ZP_FILM_FILEFOLDER_ID,
                            TRACK_ID = track_id,
                            ZP_CODEC_ID = zp_codec_id,
                            ZP_LANG_ID = track_parsed_dict['zp_lang_id'],
                            CHANNELS = track_parsed_dict['channel_s'],
                            BIT_RATE = str(track_parsed_dict['bit_rate'])
                        )
                        session.add(add_zp_film_filefolder_audio_metadata)
                        commit(session)
                    else:
                        log.error('zp_codec_id 0 for audio track_parsed_dict %s', track_parsed_dict)
                else:
                    message = ('Audio track_id %s format has track_format of %s. File %s' % (
                        track_id, track_parsed_dict['format'], filefolder_path
                    ))
                    log.error(message)
                    self.add_warning_raised_to_db(11, message)
            else:
                message = ('Audio track_id %s does not have attribute format. File %s' % (
                    track_id, filefolder_path
                ))
                log.error(message)
                self.add_warning_raised_to_db(11, message)
        else:
            log.debug('audio track id: {0} allready in db with ZP_FILM_FILEFOLDER.ID: {1}'.format(
                track_id,
                ZP_FILM_FILEFOLDER_ID))
        session.close()

    def process_video_track(self, track, track_id, ZP_FILM_FILEFOLDER_ID, filefolder_path):
        """Process video track

            Args:
                | track (obj): mediainfo track
                | track_id (int): track id
                | ZP_FILM_FILEFOLDER_ID (int): ZP_FILM_FILEFOLDER_ID

        """
        #if (isinstance(track.width, string_types) or isinstance(track.width, int)) and \
        #    (isinstance(track.height, string_types) or isinstance(track.height, int)):
        #    res_string = '%sx%s' % (track.width, track.height)
        #    if res_string in res_dict:
        #        res_dict[res_string] += 1
        #    else:
        #        res_dict[res_string] = 1
        #log.error('track.width %s, track.height %s', track.width, track.height)
        #log.error(res_dict)
        session = self.Session()
        try:
            session.query(TABLES.ZP_FILM_FILEFOLDER_VIDEO_METADATA).filter(
                TABLES.ZP_FILM_FILEFOLDER_VIDEO_METADATA.TRACK_ID == track_id,
                TABLES.ZP_FILM_FILEFOLDER_VIDEO_METADATA.ZP_FILM_FILEFOLDER_ID == ZP_FILM_FILEFOLDER_ID).one()
        except orm.exc.NoResultFound:
            zp_codec_id = 0
            track_parsed_dict = {'codec_id': 0, 'format_profile': '', 'format_version': '', 'frame_rate': '0.0',
                                 'aspect_ratio': '0.0',
                                 'display_aspect_ratio': '', 'bit_rate': '0.0', 'format': '', 'bit_depth': '0',
                                 'maximum_bit_rate': '0.0', 'width': '0', 'height': '0'}
            for track_key in track_parsed_dict:
                log.debug('track_key %s', track_key)
                #track_key_conformed = track_key.lower().strip().strip('_')
                track_value_list = self.get_track_value_list(track, track_key)
                log.debug('track_value_list %s', track_value_list)
                track_parsed_dict[track_key] = self.process_track_value_list(track_key, track_value_list)
                log.debug('track_parsed_dict[track_key] %s', track_parsed_dict[track_key])
            log.debug('track_parsed_dict %s', pprint.pformat(track_parsed_dict))
            if track_parsed_dict['format']:
                track_format_alphanum = re.sub(r'''[^a-z+0-9]+''', '', track_parsed_dict['format'].lower())
                video_format_dict = {'mpeg1': 1, 'mpeg2': 2, 'mpeg4': 3, 'h263': 4,
                                     'realvideo': 5, 'vc1': 6, 'wmvhd': 7, 'xvid': 8,
                                     'divx': 9, '3vix': 10, 'avc': 11, 'h264': 12, 'hevc': 13,
                                     'h265': 14, 'dv': 15, 'mp43': 16}
                if track_format_alphanum in {'avc', 'h264', 'hevc', 'h265', 'dv', 'mp43'}:
                    zp_codec_id = video_format_dict[track_format_alphanum]
                elif track_format_alphanum == 'vc1':
                    if re.search(r'''advanced|ap''', track_parsed_dict['format_profile']):
                        level_match = re.search(r'''(?P<level>\d{1})''', track_parsed_dict['format_profile'])
                        if level_match:
                            level = int(level_match.groupdict()['level'])
                            if level >= 2:
                                zp_codec_id = video_format_dict['wmvhd']
                    if zp_codec_id == 0:
                        zp_codec_id = video_format_dict['vc1']
                elif re.search(r'''real''', track_format_alphanum, flags=re.I):
                    zp_codec_id = video_format_dict['realvideo']
                elif track_format_alphanum == 'mpeg4visual':
                    if re.search(r'''dv|dx''', track_parsed_dict['codec_id'], flags=re.I):
                        zp_codec_id = video_format_dict['divx']
                    elif re.search(r'''xvid''', track_parsed_dict['codec_id'], flags=re.I):
                        zp_codec_id = video_format_dict['xvid']
                    elif re.search(r'''3iv''', track_parsed_dict['codec_id'], flags=re.I):
                        zp_codec_id = video_format_dict['3vix']
                    else:
                        zp_codec_id = video_format_dict['mpeg4']
                elif track_format_alphanum == 'mpegvideo':
                    if '2' in track_parsed_dict['codec_id'] or '2' in track_parsed_dict['format_version']:
                        zp_codec_id = video_format_dict['mpeg2']
                    elif '1' in track_parsed_dict['codec_id'] or '1' in track_parsed_dict['format_version']:
                        zp_codec_id = video_format_dict['mpeg1']
                log.debug('track_parsed_dict %s', pprint.pformat(track_parsed_dict))
                #time.sleep(3000)
                if zp_codec_id == 0 and track_parsed_dict['format'] != 'jpeg':
                    log.warning('file %s codec could not be identified. track_format_alphanum %s,'
                              ' track_format_version %s, track_format_profile %s',
                              filefolder_path, track_format_alphanum, track_parsed_dict['format_version'],
                              track_parsed_dict['format_profile'])
                else:
                    add_zp_film_filefolder_video_metadata = TABLES.ZP_FILM_FILEFOLDER_VIDEO_METADATA(
                        ZP_FILM_FILEFOLDER_ID=ZP_FILM_FILEFOLDER_ID,
                        TRACK_ID=track_id,
                        FRAME_RATE=str(track_parsed_dict['frame_rate']),
                        BIT_RATE=str(track_parsed_dict['bit_rate']) if track_parsed_dict['bit_rate'] else str(track_parsed_dict['maximum_bit_rate']),
                        ZP_CODEC_ID=zp_codec_id,
                        ASPECT_RATIO=str(track_parsed_dict['aspect_ratio']),
                        DISPLAY_ASPECT_RATIO=track_parsed_dict['display_aspect_ratio'],
                        BIT_DEPTH=str(track_parsed_dict['bit_depth']),
                        WIDTH=track_parsed_dict['width'],
                        HEIGHT=track_parsed_dict['height']
                    )
                    session.add(add_zp_film_filefolder_video_metadata)
                    commit(session)
            else:
                log.warning('format is empty or None: %s, %s', track_parsed_dict['format_version'],
                          filefolder_path)

        else:
            log.debug('video track id: {0} allready in db with ZP_FILM_FILEFOLDER.ID: {1}'.format(
                track_id,
                ZP_FILM_FILEFOLDER_ID))
        session.close()

    def process_text_track(self, track, track_id, ZP_FILM_FILEFOLDER_ID, filefolder_path):
        """Process text track

            Args:
                | track (obj): mediainfo track
                | track_id (int): track id
                | ZP_FILM_FILEFOLDER_ID (int): ZP_FILM_FILEFOLDER_ID

        """

        session = self.Session()
        try:
            session.query(TABLES.ZP_FILM_FILEFOLDER_TEXT_METADATA).filter(
                TABLES.ZP_FILM_FILEFOLDER_TEXT_METADATA.TRACK_ID == track_id,
                TABLES.ZP_FILM_FILEFOLDER_TEXT_METADATA.ZP_FILM_FILEFOLDER_ID == ZP_FILM_FILEFOLDER_ID).one()
        except orm.exc.NoResultFound:
            zp_codec_id = 0
            track_parsed_dict = {'format': '', 'language': ''}
            for track_key in track_parsed_dict:
                track_value_list = self.get_track_value_list(track, track_key)
                track_parsed_dict[track_key] = self.process_track_value_list(track_key, track_value_list)
            if track_parsed_dict['format']:
                track_format_alphanum = re.sub(r'''[^a-z0-9]+''', '', track_parsed_dict['format'].lower())
                video_format_dict = {
                                        'ass': 1, 'dvbsubtitle': 2, 'pgs': 3, 'ssa': 4, 'timedtext': 5,
                                        'utf8': 6, 'vobsub': 7, 'kate': 8, 'bitmap': 9, 'usf': 10, 'textst': 11,
                'appletext': 12, 'ttml': 13, 'encrypted': 14, 'divxsubtitle': 15, 'rle': 16, 'eia708': 17,
                'eia608': 18
                }
                if track_parsed_dict['language']:
                    track_langauge = conform_track_lang(track.language)
                    track_langauge_lower = track_langauge.lower()
                    if not re.search('undefined', track_langauge, flags=re.I):
                        track_parsed_dict['zp_lang_id'] = self.zp_lang_from_text(track_langauge_lower)
                if 'zp_lang_id' not in track_parsed_dict:
                    track_parsed_dict['zp_lang_id'] = 1823
                if track_format_alphanum in video_format_dict:
                    zp_codec_id = video_format_dict[track_format_alphanum]
                    add_zp_film_filefolder_text_metadata = TABLES.ZP_FILM_FILEFOLDER_TEXT_METADATA(
                        ZP_FILM_FILEFOLDER_ID=ZP_FILM_FILEFOLDER_ID,
                        TRACK_ID=track_id,
                        ZP_CODEC_ID=zp_codec_id,
                        ZP_LANG_ID = track_parsed_dict['zp_lang_id']
                    )
                    session.add(add_zp_film_filefolder_text_metadata)
                    commit(session)
                else:
                    log.error('file %s format could not be identified. track_format_alphanum %s,'
                              ' format %s',
                              filefolder_path, track_format_alphanum, track_parsed_dict['format'])
        else:
            log.debug('video track id: {0} allready in db with ZP_FILM_FILEFOLDER.ID: {1}'.format(
                track_id,
                ZP_FILM_FILEFOLDER_ID))
        session.close()

    def get_track_value_list(self, track, track_key):
        get_track_value_list = []
        if getattr(track, track_key) is not None:
            get_track_value_list = [getattr(track, track_key)]
            if isinstance(getattr(track, 'other_%s' % track_key), list):
                get_track_value_list = get_track_value_list + getattr(track, 'other_%s' % track_key)
        return get_track_value_list

    def process_track_key(self, track_key, track_value):
        track_value_list = None
        if isinstance(track_value, string_types):
            track_value_list = [track_value]
        elif isinstance(track_value, list):
            track_value_list = track_value
        elif isinstance(track_value, int) or isinstance(track_value, float):
            track_value_list = [str(track_value)]
        else:
            log.warning('track_value_list not int/float/string_types/list but %s',
                      type(track_value))
        if isinstance(track_value_list, list):
            return self.process_track_value_list(track_key, track_value_list)
        elif track_key in {'channel_s'}:
            return 0
        else:
            return ''

    def get_max_channels(self, track_value):
        if isinstance(track_value, int):
            return track_value
        elif isinstance(track_value, string_types):
            max_num_channels = 0
            for num_channels in re.findall(r'''\d+''', track_value):
                num_channels_int = int(num_channels)
                if num_channels_int > max_num_channels:
                    max_num_channels = num_channels_int
            return max_num_channels

    def process_track_value_list(self, track_key, track_value_list):
        if track_key in {'channel_s'}:
            current_track_value = 0
        elif track_key in {'bit_rate', 'frame_rate'}:
            current_track_value = 0.0
        else:
            current_track_value = ''
        for track_value in track_value_list:
            track_value_str = str(track_value)
            if track_key == 'language':
                if (len(current_track_value) == 0) or (
                    len(track_value_str) < len(current_track_value)):
                    current_track_value = track_value_str
            elif track_key == 'channel_s':
                max_channels = self.get_max_channels(track_value_str)
                if max_channels > current_track_value:
                    current_track_value = max_channels
            elif track_key in {'bit_rate', 'maximum_bit_rate'}:
                if track_value_str.isdigit():
                    return str(float(track_value_str))
                bit_rate = bitrate_text_to_float(track_value_str)
                if bit_rate > current_track_value:
                    current_track_value = bit_rate
            elif track_key in {'width', 'height'}:
                if not track_value_str.isdigit():
                    return '0'
                else:
                    return track_value_str
            elif track_key in {'frame_rate', 'aspect_ratio'}:
                if track_key == 'aspect_ratio':
                    log.debug('aspect_ratio %s', track_value_list)
                frame_rate = frame_rate_text_to_float(track_value_str)
                if isinstance(frame_rate, float):
                    return frame_rate
            elif track_key == 'display_aspect_ratio':
                display_aspect_ratio = display_aspect_ratio_from_text(track_value_str)
                if isinstance(display_aspect_ratio, string_types):
                    return display_aspect_ratio
            else:
                return track_value
        return current_track_value

    def conform_track_id(self, track_id):
        if isinstance(track_id, int):
            return track_id
        elif isinstance(track_id, string_types):
            if track_id.isdigit():
                return track_id
            elif re.match(r'''\d+-\d+''', track_id):
                return track_id.split('-')[1]
        return None

    def validtate_track_id(self, track_id):
        if isinstance(track_id, int):
            return True
        elif isinstance(track_id, string_types):
            if track_id.isdigit():
                return True
        return None
