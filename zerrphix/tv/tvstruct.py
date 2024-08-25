# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import re
import os
from sqlalchemy import func, orm, and_, or_

from zerrphix.db import commit
from zerrphix.db.tables import TABLES
#from zerrphix.util import smbfs_connection_dict_scan_path
from zerrphix.util.filesystem import (smbfs)
from zerrphix.util.text import date_time
from zerrphix.util.filesystem import get_file_extension
from zerrphix.tv.base import TVBase

log = logging.getLogger(__name__)


class TVStruct(TVBase):
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
        super(TVStruct, self).__init__(**kwargs)
        self.single_episode_regex = [
            r"""(^|[^\w])s(?:eason|eries)?(?P<season>[0-9]+).*?e(?:p|pisode)?(?P<episode>[0-9]+)([^\w]|$)""",
            r"""(^|[^\w])(?P<season>[0-9]+)x(?P<episode>[0-9]+)([^\w]|$)"""
        ]
        self.multi_episode_regex_list = [
            r"""(^|[^\w])s(?:eason|eries)?(?P<season>[0-9]+).*?e(?:p|pisode)?(?P<fepisode>[0-9]+)(?:(?:-?(?:e(?:p|pisode)?))|-)(?P<lepisode>[0-9]+)([^\w]|$)""",
            r"""(^|[^\w])(?P<season>[0-9]+)x(?P<fepisode>[0-9]+)-(?P<lepisode>[0-9]+)([^\w]|$)"""
        ]
        self._setup_allowed_extentions()

    def _setup_allowed_extentions(self):
        """Get the allowed extensions from the db and make a list

            Attributes:
                self.allowed_extensions_list (list): list of permitted extensions
                for filenames that will be considered video files
        """
        self.allowed_extensions_list = self.get_extension_list(2)
        self.ignore_extensions_list = self.get_extension_list(2, 1)

    def pre_identify(self):
        processing_complete = False
        session = self.Session()
        max_ZP_TV_FILEFOLDER_ID = session.query(func.max(TABLES.ZP_TV_FILEFOLDER.ID)).one()[0]
        session.close()
        if isinstance(max_ZP_TV_FILEFOLDER_ID, int):
            session.close()
            ZP_TV_FILEFOLDER_ID = max_ZP_TV_FILEFOLDER_ID + 1
            while processing_complete == False:
                session = self.Session()
                qry_unidentified_filefolder = session.query(
                    TABLES.ZP_TV_FILEFOLDER.ID,
                    TABLES.ZP_TV_FILEFOLDER.ZP_SCAN_PATH_ID,
                    TABLES.ZP_TV_FILEFOLDER.LAST_PATH,
                    TABLES.ZP_SCAN_PATH.PATH
                ).filter(
                    TABLES.ZP_TV_FILEFOLDER.ID < ZP_TV_FILEFOLDER_ID,
                    TABLES.ZP_TV_FILEFOLDER.ZP_SCAN_PATH_ID == TABLES.ZP_SCAN_PATH.ID,
                    (~TABLES.ZP_TV_FILEFOLDER.ID.in_(session.query(
                        TABLES.ZP_TV_EPISODE_FILEFOLDER.ZP_TV_FILEFOLDER_ID)) |
                     TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID.in_(session.query(
                         TABLES.ZP_TV_RUNNING.ZP_TV_ID)))
                )
                # for unidenttified_filefolder in _yield_limit(qry_unidentified_filefolder, TABLES.ZP_TV_SHOW_FILEFOLDER.ID, maxrq=100, order='desc'):
                ZP_TV_FILEFOLDER = qry_unidentified_filefolder.order_by(TABLES.ZP_TV_FILEFOLDER.ID.desc()).first()
                if ZP_TV_FILEFOLDER is not None:
                    log.debug('ZP_TV_FILEFOLDER %s', ZP_TV_FILEFOLDER)
                    ZP_TV_FILEFOLDER_ID = ZP_TV_FILEFOLDER.ID
                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                 10,
                                                                 'Pre Identify: TV Folder %s/%s' %
                                                                 (ZP_TV_FILEFOLDER_ID,
                                                                  max_ZP_TV_FILEFOLDER_ID)
                                                                 )
                    session.close()
                    self.process_show(ZP_TV_FILEFOLDER.ZP_SCAN_PATH_ID,
                                      ZP_TV_FILEFOLDER.LAST_PATH,
                                      ZP_TV_FILEFOLDER_ID,
                                      ZP_TV_FILEFOLDER.PATH)
                else:
                    processing_complete = True
                    session.close()

    def post_identify(self):
        session = self.Session()
        max_ZP_TV_EPISODE_FILEFOLDER_ID = session.query(func.max(TABLES.ZP_TV_EPISODE_FILEFOLDER.ID)).one()[0]
        session.close()
        processing_complete = False
        if isinstance(max_ZP_TV_EPISODE_FILEFOLDER_ID, int):
            session.close()
            ZP_TV_EPISODE_FILEFOLDER_ID = max_ZP_TV_EPISODE_FILEFOLDER_ID + 1
            while processing_complete == False:
                session = self.Session()
                qry_missing_episodes = session.query(
                    TABLES.ZP_TV_EPISODE_FILEFOLDER.ID,
                    TABLES.ZP_TV_EPISODE_FILEFOLDER.FIRST_EPISODE,
                    TABLES.ZP_TV_EPISODE_FILEFOLDER.LAST_EPISODE,
                    TABLES.ZP_TV_EPISODE_FILEFOLDER.SEASON,
                    TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID,
                ).filter(
                    TABLES.ZP_TV_EPISODE_FILEFOLDER.ID < ZP_TV_EPISODE_FILEFOLDER_ID,
                    TABLES.ZP_TV_FILEFOLDER.ID == TABLES.ZP_TV_EPISODE_FILEFOLDER.ZP_TV_FILEFOLDER_ID,
                    TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID != None,
                    ~TABLES.ZP_TV_EPISODE_FILEFOLDER.ID.in_(
                        session.query(
                            TABLES.ZP_TV_EPISODE_FILEFOLDER.ID
                        ).filter(
                            TABLES.ZP_TV_FILEFOLDER.ID == TABLES.ZP_TV_EPISODE_FILEFOLDER.ZP_TV_FILEFOLDER_ID,
                            TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == TABLES.ZP_TV_EPISODE.ZP_TV_ID,
                            TABLES.ZP_TV_EPISODE.SEASON == TABLES.ZP_TV_EPISODE_FILEFOLDER.SEASON,
                            TABLES.ZP_TV_EPISODE.EPISODE == TABLES.ZP_TV_EPISODE_FILEFOLDER.FIRST_EPISODE
                        )
                    )
                )
                qry_missing_episodes_count = qry_missing_episodes.count()
                log.debug('qry_missing_episodes_count %s', qry_missing_episodes_count)
                #raise SystemExit
                if qry_missing_episodes_count > 0:
                    episodes = qry_missing_episodes.order_by(TABLES.ZP_TV_EPISODE_FILEFOLDER.ID.desc()).limit(250)
                    session.close()
                    episode_processing_dict = {}
                    for ep in episodes:
                        episode_processing_dict[ep.ID] = {'ZP_TV_EPISODE_FILEFOLDER_ID': ep.ID,
                                                          'FIRST_EPISODE': ep.FIRST_EPISODE,
                                                          'LAST_EPISODE': ep.LAST_EPISODE,
                                                          'SEASON': ep.SEASON,
                                                          'ZP_TV_ID': ep.ZP_TV_ID}
                    for ID in episode_processing_dict:
                        ZP_TV_EPISODE_FILEFOLDER_ID = ID
                        self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                 10,
                                                                 'Post Identify A: TV Episode %s/%s' %
                                                                 (ZP_TV_EPISODE_FILEFOLDER_ID,
                                                                  max_ZP_TV_EPISODE_FILEFOLDER_ID)
                                                                 )
                        self.add_episde_to_db(episode_processing_dict[ID]['ZP_TV_ID'],
                                              episode_processing_dict[ID]['SEASON'],
                                              episode_processing_dict[ID]['FIRST_EPISODE'],
                                              episode_processing_dict[ID]['LAST_EPISODE']
                                              )
                        # why can't we just use episode_processing_dict[ID] as
                        # TABLES.ZP_TV_EPISODE.ZP_TV_FILEFOLDER_ID ??? and not
                        # use the below. I need to comment better.
                else:
                    processing_complete = True
                    session.close()
        ZP_TV_ID = 0
        session = self.Session()
        max_ZP_TV_ID = session.query(func.max(TABLES.ZP_TV.ID)).one()[0]
        session.close()
        if isinstance(max_ZP_TV_ID, int):
            processing_complete = False
            while processing_complete is False:
                session = self.Session()
                qry_missing_episodes = session.query(TABLES.ZP_TV_EPISODE).filter(
                    TABLES.ZP_TV_EPISODE.ZP_TV_EPISODE_FILEFOLDER_ID == None,
                    TABLES.ZP_TV_EPISODE.ZP_TV_ID > ZP_TV_ID
                )
                qry_missing_episodes_count = qry_missing_episodes.count()
                if qry_missing_episodes_count > 0:
                    ZP_TV_ID = qry_missing_episodes.order_by(TABLES.ZP_TV_EPISODE.ZP_TV_ID.asc()).first().ZP_TV_ID

                    self.set_current_library_process_desc_detail(self.library_config_dict['id'],
                                                                 10,
                                                                 'Post Identify B: TV %s/%s' %
                                                                 (ZP_TV_ID,
                                                                  max_ZP_TV_ID)
                                                                 )
                    session.close()
                    #if ZP_TV_ID > 1:
                        #raise Exception
                    processing_ZP_TV_ID_complete = False
                    SEASON = 0
                    while processing_ZP_TV_ID_complete is False:
                        session = self.Session()
                        qry_missing_ZP_TV_ID_episodes = session.query(TABLES.ZP_TV_EPISODE).filter(
                            TABLES.ZP_TV_EPISODE.ZP_TV_EPISODE_FILEFOLDER_ID == None,
                            TABLES.ZP_TV_EPISODE.ZP_TV_ID == ZP_TV_ID,
                            TABLES.ZP_TV_EPISODE.SEASON > SEASON
                        )
                        SEASON_first = qry_missing_ZP_TV_ID_episodes.order_by(
                            TABLES.ZP_TV_EPISODE.SEASON.asc()).first()
                        if SEASON_first is not None:
                            SEASON = SEASON_first.SEASON
                        else:
                            SEASON = None
                        session.close()
                        if SEASON is not None:
                            processing_SEASON_complete = False
                            EPISODE = 0
                            session = self.Session()
                            while processing_SEASON_complete is False:
                                #log.warning('EPISODE %s', EPISODE)
                                qry_missing_SEASON_episodes = session.query(TABLES.ZP_TV_EPISODE).filter(
                                    TABLES.ZP_TV_EPISODE.ZP_TV_EPISODE_FILEFOLDER_ID == None,
                                    TABLES.ZP_TV_EPISODE.ZP_TV_ID == ZP_TV_ID,
                                    TABLES.ZP_TV_EPISODE.SEASON == SEASON,
                                    TABLES.ZP_TV_EPISODE.EPISODE > EPISODE
                                )
                                if qry_missing_SEASON_episodes.count() > 0:
                                    episodes = qry_missing_SEASON_episodes.order_by(
                                        TABLES.ZP_TV_EPISODE.SEASON.asc()).limit(50)
                                    session.close()
                                    episode_list = []
                                    for episode in episodes:
                                        episode_list.append(episode.EPISODE)
                                    for _EPISODE in episode_list:
                                        EPISODE = _EPISODE
                                        # log.warning('EPISODE %s', EPISODE)
                                        session = self.Session()
                                        qry_ZP_TV_EPISODE_FILEFOLDER_ID = session.query(
                                            TABLES.ZP_TV_EPISODE_FILEFOLDER
                                        ).filter(
                                            TABLES.ZP_TV_EPISODE_FILEFOLDER.ZP_TV_FILEFOLDER_ID ==
                                            TABLES.ZP_TV_FILEFOLDER.ID,
                                            TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == ZP_TV_ID,
                                            TABLES.ZP_TV_EPISODE_FILEFOLDER.SEASON == SEASON,
                                            or_(TABLES.ZP_TV_EPISODE_FILEFOLDER.FIRST_EPISODE == EPISODE,
                                                and_(EPISODE <= TABLES.ZP_TV_EPISODE_FILEFOLDER.LAST_EPISODE,
                                              EPISODE >= TABLES.ZP_TV_EPISODE_FILEFOLDER.FIRST_EPISODE))
                                        )
                                        ZP_TV_EPISODE_FILEFOLDER_ID_first = qry_ZP_TV_EPISODE_FILEFOLDER_ID.first()
                                        log.debug('ZP_TV_EPISODE_FILEFOLDER_ID_first %s', ZP_TV_EPISODE_FILEFOLDER_ID_first.ID)
                                        #raise SystemExit
                                        if ZP_TV_EPISODE_FILEFOLDER_ID_first is not None:
                                            ZP_TV_EPISODE_FILEFOLDER_ID = ZP_TV_EPISODE_FILEFOLDER_ID_first.ID
                                            session.close()
                                            self.set_associated_ff(ZP_TV_ID, SEASON, EPISODE, ZP_TV_EPISODE_FILEFOLDER_ID)
                                            #raise Exception
                                        else:
                                            log.error('There are no filefolders for ZP_TV_ID %s, SEASON %s, EPISODE %s',
                                                      ZP_TV_ID, SEASON, EPISODE)
                                            session.close()
                                            #raise SystemExit
                                else:
                                    processing_SEASON_complete = True
                        else:
                            processing_ZP_TV_ID_complete = True
                else:
                    processing_complete = True
                    session.close()

    def set_associated_ff(self, ZP_TV_ID, SEASON, EPISODE, ZP_TV_EPISODE_FILEFOLDER_ID):
        session = self.Session()
        session.query(TABLES.ZP_TV_EPISODE).filter(TABLES.ZP_TV_EPISODE.ZP_TV_ID == ZP_TV_ID,
                                                   TABLES.ZP_TV_EPISODE.SEASON == SEASON,
                                                   TABLES.ZP_TV_EPISODE.EPISODE == EPISODE).update(
            {"ZP_TV_EPISODE_FILEFOLDER_ID": ZP_TV_EPISODE_FILEFOLDER_ID})
        log.debug('episode ZP_TV_ID %s, SEASON %s, EPISODE %s now has ZP_TV_EPISODE_FILEFOLDER_ID %s', ZP_TV_ID,
                    SEASON, EPISODE, ZP_TV_EPISODE_FILEFOLDER_ID)
        commit(session)
        session.close()

    def process_show(self, ZP_SCAN_PATH_ID, LAST_PATH, ZP_TV_FILEFOLDER_ID, zp_scan_path):
        session = self.Session()
        try:
            ZP_SCAN_PATH_FS_TYPE_ID = session.query(TABLES.ZP_SCAN_PATH).filter(
                TABLES.ZP_SCAN_PATH.ID == ZP_SCAN_PATH_ID).one(
            ).ZP_SCAN_PATH_FS_TYPE_ID
        except orm.exc.NoResultFound:
            log.warning(('No entry found in ZP_SCAN_PATH where'
                         ' ZP_SCAN_PATH_ID = {0}. This should not be possible').format(ZP_SCAN_PATH_ID))
            raise Exception(('No entry found in ZP_SCAN_PATH where'
                             ' ZP_SCAN_PATH_ID = {0}. This should not be possible').format(ZP_SCAN_PATH_ID))
        except orm.exc.MultipleResultsFound:
            log.warning(('More than entry in ZP_SCAN_PATH where'
                         ' ZP_SCAN_PATH_ID = {0}. This should not be possible').format(ZP_SCAN_PATH_ID))
            raise Exception(('More than entry in ZP_SCAN_PATH where'
                             ' ZP_SCAN_PATH_ID = {0}. This should not be possible').format(ZP_SCAN_PATH_ID))
        else:
            if ZP_SCAN_PATH_FS_TYPE_ID == 1:
                tv_show_path = os.path.join(zp_scan_path, LAST_PATH)
                log.debug(('tv_show_path: {0} for ZP_SCAN_PATH_ID: {1},'
                           ' LAST_PATH: {2}').format(
                    tv_show_path,
                    ZP_SCAN_PATH_ID,
                    LAST_PATH))
                self.local_find_episdoes(tv_show_path, ZP_SCAN_PATH_ID, ZP_TV_FILEFOLDER_ID)
            elif ZP_SCAN_PATH_FS_TYPE_ID == 2:
                tv_show_path = smbfs.join(zp_scan_path, LAST_PATH)
                log.debug(('tv_show_path: {0} for ZP_SCAN_PATH_ID: {1},'
                           ' LAST_PATH: {2}').format(
                    tv_show_path,
                    ZP_SCAN_PATH_ID,
                    LAST_PATH))
                self.smbfs_find_episdoes(tv_show_path, ZP_SCAN_PATH_ID, ZP_TV_FILEFOLDER_ID)
        session.close()

    def smbfs_find_episdoes(self, path, ZP_SCAN_PATH_ID, ZP_TV_FILEFOLDER_ID):
        connection_dict = self.smbfs_connection_dict_scan_path(ZP_SCAN_PATH_ID)
        log.debug('connection_dict: {0} for ZP_SCAN_PATH_ID: {1}'.format(
            connection_dict,
            ZP_SCAN_PATH_ID))
        if connection_dict:
            smbcon = smbfs(connection_dict)
            if smbcon.isdir(path):
                log.debug('path: {0} is dir'.format(path))
                for filefolider in sorted(smbcon.listdir(path)):
                    filefolider_path = smbfs.join(path, filefolider)
                    if smbcon.isdir(filefolider_path):
                        self.smbfs_process_season(smbcon, filefolider_path, filefolider, ZP_TV_FILEFOLDER_ID)
                        ## TODO prcocess files in
            else:
                log.warning('path: {0} is not dir'.format(path))

    def local_find_episdoes(self, path, ZP_SCAN_PATH_ID, ZP_TV_FILEFOLDER_ID):
        if os.path.isdir(path):
            log.debug('path: {0} is dir'.format(path))
            for filefolider in sorted(os.listdir(path)):
                filefolider_path = os.path.join(path, filefolider)
                if os.path.isdir(filefolider_path):
                    log.debug('path: {0} is dir'.format(filefolider_path))
                    self.local_process_season(filefolider_path, filefolider, ZP_TV_FILEFOLDER_ID)
                    ## TODO prcocess files in
                else:
                    log.debug('path: {0} is not a dir'.format(filefolider_path))
        else:
            log.debug('path: {0} is not a dir'.format(path))

    def smbfs_process_season(self, smbcon, filefolider_path, season_folder, ZP_TV_FILEFOLDER_ID):
        for _file in smbcon.listdir(filefolider_path, file_only=True):
            full_path = smbfs.join(filefolider_path, _file)
            log.debug('_file %s', _file)
            _file_path = smbfs.join(filefolider_path, _file)
            file_extention = get_file_extension(_file_path)
            if file_extention in self.allowed_extensions_list:
                log.debug('file_extention %s for file %s in self.allowed_extensions_list %s', file_extention,
                      _file, self.allowed_extensions_list)
                self.process_season(_file, season_folder, full_path, ZP_TV_FILEFOLDER_ID)
            elif file_extention not in self.ignore_extensions_list:
                reason = 'file_extention %s for file %s not in self.allowed_extensions_list %s' % (file_extention,
                      _file, self.allowed_extensions_list)
                log.debug(reason)
                self.raise_invalid_filefolder(2, 0, '', 3, full_path, reason)

    def local_process_season(self, filefolider_path, season_folder, ZP_TV_FILEFOLDER_ID):
        for _file in os.listdir(filefolider_path):
            full_path = os.path.join(filefolider_path, _file)
            log.debug('_file %s', _file)
            _file_path = os.path.join(filefolider_path, _file)
            file_extention = get_file_extension(_file_path)
            if file_extention in self.allowed_extensions_list:
                log.debug('file_extention %s for file %s in self.allowed_extensions_list %s', file_extention,
                      _file, self.allowed_extensions_list)
                if os.path.isfile(_file_path):
                    self.process_season(_file, season_folder, full_path, ZP_TV_FILEFOLDER_ID)
                else:
                    log.debug('_file_path %s is not a file', _file_path)
            elif file_extention not in self.ignore_extensions_list:
                reason = 'file_extention %s for file %s not in self.allowed_extensions_list %s' % (file_extention,
                      _file, self.allowed_extensions_list)
                log.debug(reason)
                self.raise_invalid_filefolder(2, 0, '', 4, full_path, reason)

    def process_season(self, _file, season_folder, full_path, ZP_TV_FILEFOLDER_ID):
        valid_episode_file = False
        for regex_pattern in self.multi_episode_regex_list:
            if valid_episode_file is False:
                regex_search = re.search(regex_pattern, _file, re.I | re.U)
                if regex_search:
                    groupdict = regex_search.groupdict()
                    log.debug('match for %s against regex_pattern %s, groups %s', _file,
                              regex_pattern, groupdict)
                    season = int(groupdict['season'])
                    f_episode = int(groupdict['fepisode'])
                    l_episdoe = int(groupdict['lepisode'])
                    # ignore season 0 and episode 0 for now
                    # TODO: deal with season 0 and episode 0
                    # deal with only ep in filename and get season num from folder name
                    if season > 0 and f_episode > 0 and l_episdoe > 0:
                        self.add_episde_filefolder_to_db(ZP_TV_FILEFOLDER_ID,
                                                         season,
                                                         f_episode,
                                                         l_episdoe,
                                                         os.path.join(season_folder, _file))
                        valid_episode_file = True
        # log.critical(smbfs.join(season_folder, _file))
        if valid_episode_file is False:
            for regex_pattern in self.single_episode_regex:
                if valid_episode_file is False:
                    regex_search = re.search(regex_pattern, _file, re.I | re.U)
                    if regex_search:
                        groupdict = regex_search.groupdict()
                        log.debug('match for %s against self.single_episode_regex %s, groups %s', _file,
                                  regex_pattern, groupdict)
                        season = int(groupdict['season'])
                        episode = int(groupdict['episode'])
                        # ignore season 0 and episode 0 for now
                        # TODO: deal with season 0 and episode 0
                        # deal with only ep in filename and get season num from folder name
                        if season > 0 and episode > 0:
                            self.add_episde_filefolder_to_db(ZP_TV_FILEFOLDER_ID,
                                                             season,
                                                             episode,
                                                             episode,
                                                             os.path.join(season_folder, _file))
                            valid_episode_file = True
        if valid_episode_file is False:
            reason = '%s not a valid_episode_file against %s and %s' % (full_path,
                self.multi_episode_regex_list,
                self.single_episode_regex)
            log.debug(reason)
            self.raise_invalid_filefolder(2, 0, '', 5, full_path, reason)

    def add_episde_filefolder_to_db(self, ZP_TV_FILEFOLDER_ID, season, f_episode, l_episdoe, LAST_PATH):
        session = self.Session()
        try:
            session.query(TABLES.ZP_TV_EPISODE_FILEFOLDER).filter(
                TABLES.ZP_TV_EPISODE_FILEFOLDER.ZP_TV_FILEFOLDER_ID == ZP_TV_FILEFOLDER_ID,
                TABLES.ZP_TV_EPISODE_FILEFOLDER.SEASON == season,
                TABLES.ZP_TV_EPISODE_FILEFOLDER.FIRST_EPISODE == f_episode,
                TABLES.ZP_TV_EPISODE_FILEFOLDER.LAST_EPISODE == l_episdoe,
                TABLES.ZP_TV_EPISODE_FILEFOLDER.LAST_PATH == LAST_PATH).one()
        except orm.exc.NoResultFound:
            add_ZP_TV_EPISODE_FILEFOLDER = TABLES.ZP_TV_EPISODE_FILEFOLDER(ZP_TV_FILEFOLDER_ID=ZP_TV_FILEFOLDER_ID,
                                                                           SEASON=season,
                                                                           FIRST_EPISODE=f_episode,
                                                                           LAST_EPISODE=l_episdoe,
                                                                           LAST_PATH=LAST_PATH)
            session.add(add_ZP_TV_EPISODE_FILEFOLDER)
            commit(session)
        except orm.exc.MultipleResultsFound:
            log.warning(('More than entry in ZP_TV_EPISODE_FILEFOLDER where'
                         ' ZP_TV_FILEFOLDER_ID = {0}. This should not be possible').format(ZP_TV_FILEFOLDER_ID))
            raise Exception(('More than entry in ZP_TV_EPISODE_FILEFOLDER where'
                             ' ZP_TV_FILEFOLDER_ID = {0}. This should not be possible').format(ZP_TV_FILEFOLDER_ID))
        session.close()

    def add_episde_to_db(self, ZP_TV_ID, season, f_episode, l_episode):
        session = self.Session()
        if f_episode > 0 and l_episode >= f_episode:
            for episode in range(f_episode, l_episode+1):
                try:
                    session.query(TABLES.ZP_TV_EPISODE).filter(
                        TABLES.ZP_TV_EPISODE.ZP_TV_ID == ZP_TV_ID,
                        TABLES.ZP_TV_EPISODE.SEASON == season,
                        TABLES.ZP_TV_EPISODE.EPISODE == episode,
                    ).one()
                except orm.exc.NoResultFound:
                    add_ZP_TV_EPISODE = TABLES.ZP_TV_EPISODE(ZP_TV_ID=ZP_TV_ID,
                                                             SEASON=season,
                                                             EPISODE=episode,
                                                             LAST_EDIT_DATETIME=date_time())
                    session.add(add_ZP_TV_EPISODE)
                    commit(session)
                session.close()
        else:
            log.error('! f_episode %s > 0 and l_episode %s >= f_episode %s', f_episode, l_episode, f_episode)
