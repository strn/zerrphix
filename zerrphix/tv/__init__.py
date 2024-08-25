# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
from types import MethodType

from zerrphix.tv.artwork import Artwork
from zerrphix.tv.artwork_episode import ArtworkEpisode
from zerrphix.tv.eid_gather import EidGather
from zerrphix.tv.episodedata import EpisodeData
from zerrphix.tv.raw_images import RawImages
from zerrphix.tv.raw_season_images import RawSeasonImages
from zerrphix.tv.raw_episode_images import RawEpisodeImages
# from zerrphix.tv.metadata import Metadata
# from zerrphix.tv.score import Score
from zerrphix.tv.identify import Identify
from zerrphix.tv.scan import Scan
from zerrphix.tv.inverse_scan import InverseScan
from zerrphix.tv.showdata import ShowData
from zerrphix.tv.tvstruct import TVStruct
from zerrphix.tv.user_specifics import User_Specifics
from zerrphix.tv.base import TVBase
#from zerrphix.util.image_store import create_eapi_library_keep_images_folders
#from zerrphix.util.image_store import make_library_render_root_dir
from zerrphix.db.tables import TABLES
from zerrphix.db import commit
from zerrphix.util.text import date_time
from zerrphix.util import time_run_between
from sqlalchemy import func
from sqlalchemy import orm
import copy
import time
import re
from datetime import datetime
from datetime import timedelta
import os

# from zerrphix.tv.tidyup import Tidyup

log = logging.getLogger(__name__)

#logging.getLogger("requests").setLevel(logging.DEBUG)
#logging.getLogger("urllib3").setLevel(logging.DEBUG)
#logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)


class TV(TVBase):
    """The TV Class which initiates the indvidual actions e.g. scan.
    """

    def __init__(self, **kwargs):
        library_config_dict = {'name': 'tv', 'id': 2}
        library_config_dict['downloaded_images_library_root_path'] = os.path.join(
           kwargs['global_config_dict']['downloaded_images_root_path'],
            library_config_dict['name']
        )
        kwargs['library_config_dict']=library_config_dict
        super(TVBase, self).__init__(**kwargs)
        """FILM __init__

        Args:
            | args (list): Passed through args from the command line.
            | config (:obj:): The config loaded (ConfigParser). See zerrphix.config.
            | config_root_dir (str): The directory from which the config file was loaded.
            | Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.

        Attributes:
            | args (list): Passed through args from the command line.
            | config (:obj:): The config loaded (ConfigParser). See zerrphix.config.
            | config_root_dir (str): The directory from which the config file was loaded.
            | Session (:obj:): sqlalchemy scoped_session. See zerrphix.db init.

        """

        self.kwargs = kwargs
        self.process_dict = {'scan': 9,
                            'indentify': 10,
                            'eidgahter': 11,
                            'metadata': 12,
                            'score': 13,
                            'showdata': 14,
                            'epdata': 15,
                            'user': 16,
                            'artwork': 17,
                            'tidyup': 18,
                             'raw_image': 20,
                             'inverse_scan': 21}
        self.military_time_regex = r'''^([01]\d|2[0-3]):?([0-5]\d)$'''

    def run(self):
        """Run the FILM individual actions.

            The actions are:
                | Scan - Scan the paths defined for tvs.
                | Metadata - Grab the metadata from each tv file found.
                | Score - Calculate a score for each tv (for when there are \
                multiple copies of the same tvs).
                | Identify - Use external sources (eapi) to indetify each tv.
                | Data - Grab data from the eapi(s).
                | User_Specifics - Generate user Specifics for each tv.
                | Artwork - Generate all the images for each tv.

        """
        while True:
            kwargs = self.kwargs
            process_run_list = self.get_process_run_list(self.process_dict)
            if process_run_list:
                self.set_library_last_run(2)
                log.debug('process_run_list %s' % process_run_list)
                if not isinstance(process_run_list, list):
                    process_run_list = ['scan',
                                        'identify',
                                        'eidgather',
                                        'metadata',
                                        'score',
                                        'showdata',
                                        'epdata',
                                        'raw_image',
                                        'user',
                                        'artwork',
                                        'tidy_up']
                if 'scan' in process_run_list:
                    log.debug('Initialising Scan')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['scan'],
                                                          'Scan',
                                                          'Initialising Scan')
                    scan = Scan(**kwargs)
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['scan'],
                                                          'Scan',
                                                          'Initialised Scan')
                    log.debug('Scanning scan paths for shows started')
                    self.set_process_last_run_start(self.process_dict['scan'])
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['scan'],
                                                          'Scan',
                                                          'Scanning for new shows')
                    scan.scan()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['scan'],
                                                          'Scan',
                                                          'Finished Scanning for new shows')
                    log.debug('Scanning scan paths for shows completed')
                    self.set_process_last_run_end(self.process_dict['scan'])
                    self.set_process_force_run(self.process_dict['indentify'])

                if 'indentify' in process_run_list:
                    # todo seperate out tvstruct and identify
                    log.debug('Initialising TVStruct')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['indentify'],
                                                          'TV Struct',
                                                          'Initialising TVStruct')
                    tvstruct = TVStruct(**kwargs)
                    log.debug('TVStruct pre_identify started')
                    self.set_process_last_run_start(self.process_dict['indentify'])
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['indentify'],
                                                          'TV Struct',
                                                          'TVStruct pre_identify started')
                    tvstruct.pre_identify()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['indentify'],
                                                          'TV Struct',
                                                          'TVStruct pre_identify finished')
                    log.debug('TVStruct pre_identify finished')
                    log.debug('identfying tv show started')
                    log.debug('Initialising idenfity')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['indentify'],
                                                          'Identify',
                                                          'Initialising Identify')
                    idenfity = Identify(**kwargs)
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['indentify'],
                                                          'Identify',
                                                          'Identifying tvs started')
                    idenfity.idenfity()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['indentify'],
                                                          'Identify',
                                                          'Identifying tvs finished')
                    log.debug('identfying tv show completed')
                    log.debug('TVStruct post_identify started')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['indentify'],
                                                          'TV Struct',
                                                          'TVStruct post_identify started')
                    tvstruct.post_identify()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['indentify'],
                                                          'TV Struct',
                                                          'TVStruct post_identify finished')
                    log.debug('TVStruct post_identify finished')
                    self.set_process_last_run_end(self.process_dict['indentify'])
                    self.set_process_force_run(self.process_dict['eidgahter'])
                    self.set_process_force_run(self.process_dict['metadata'])
                    self.set_process_force_run(self.process_dict['score'])
                    self.set_process_force_run(self.process_dict['showdata'])
                    self.set_process_force_run(self.process_dict['epdata'])

                if 'eidgahter' in process_run_list:
                    log.debug('Initialising eidgahter')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['eidgahter'],
                                                          'EAPI Eid Gather',
                                                          'Initialising EidGather')
                    eidgahter = EidGather(**kwargs)
                    log.debug('starting tv eidgahter')
                    self.set_process_last_run_start(self.process_dict['eidgahter'])
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['eidgahter'],
                                                          'EAPI Eid Gather',
                                                          'Gathering EIDs started')
                    eidgahter.gather()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['eidgahter'],
                                                          'EAPI Eid Gather',
                                                          'Gathering EIDs finished')
                    log.debug('finished tv eidgahter')
                    self.set_process_last_run_end(self.process_dict['eidgahter'])

                if 'metadata' in process_run_list:
                    # todo mestadata
                    self.set_process_last_run_start(self.process_dict['metadata'])
                    self.set_process_last_run_end(self.process_dict['metadata'])

                if 'score' in process_run_list:
                    # todo score
                    self.set_process_last_run_start(self.process_dict['score'])
                    self.set_process_last_run_end(self.process_dict['score'])

                if 'showdata' in process_run_list:
                    log.debug('Initialising Data')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['showdata'],
                                                          'Show Data',
                                                          'Initialising ShowData')
                    showdata = ShowData(**kwargs)
                    log.debug('Data aquasition started')
                    self.set_process_last_run_start(self.process_dict['showdata'])
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['showdata'],
                                                          'Show Data',
                                                          'ShowData Aquatsition started')
                    showdata.acquire()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['showdata'],
                                                          'Show Data',
                                                          'ShowData Aquatsition finished')
                    log.debug('Data aquasition finished')
                    self.set_process_last_run_end(self.process_dict['showdata'])
                    self.set_process_force_run(self.process_dict['raw_image'])
                    self.set_process_force_run(self.process_dict['user'])
                    self.set_process_force_run(self.process_dict['artwork'])

                if 'epdata' in process_run_list:
                    log.debug('Initialising EpisodeData')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['epdata'],
                                                          'Episode Data',
                                                          'Initialising EpisodeData')
                    episodedata = EpisodeData(**kwargs)
                    log.debug('EpisodeData aquasition started')
                    self.set_process_last_run_start(self.process_dict['epdata'])
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['epdata'],
                                                          'Episode Data',
                                                          'EpisodeData Aquatsition started')
                    episodedata.acquire()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['epdata'],
                                                          'Episode Data',
                                                          'EpisodeData Aquatsition finished')
                    log.debug('EpisodeData aquasition finished')
                    self.set_process_last_run_end(self.process_dict['epdata'])
                    self.set_process_force_run(self.process_dict['raw_image'])
                    self.set_process_force_run(self.process_dict['user'])
                    self.set_process_force_run(self.process_dict['artwork'])

                if 'raw_image' in process_run_list:
                    log.debug('Initialising raw images')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['raw_image'],
                                                          'Raw Images',
                                                          'Initialising RawImages')
                    raw_images = RawImages(**kwargs)
                    log.debug('Show Raw Image Acquasition started')
                    self.set_process_last_run_start(self.process_dict['raw_image'])
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['raw_image'],
                                                          'Raw Images',
                                                          'RawImages Aquatsition started')
                    raw_images.acquire()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['raw_image'],
                                                          'Raw Images',
                                                          'RawImages Aquatsition finished')
                    log.debug('Show Raw Image Acquasition finished')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['raw_image'],
                                                          'Raw Season Images',
                                                          'Initialising RawSeasonImages')
                    raw_images_season = RawSeasonImages(**kwargs)
                    log.debug('Season Raw Image Acquasition started')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['raw_image'],
                                                          'Raw Season Images',
                                                          'RawSeasonImages Aquatsition started')
                    raw_images_season.acquire()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['raw_image'],
                                                          'Raw Season Images',
                                                          'RawSeasonImages Aquatsition finished')
                    log.debug('Season Raw Image Acquasition finished')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['raw_image'],
                                                          'Raw Episode Images',
                                                          'Initialising RawEpisodeImages')
                    raw_images_episode = RawEpisodeImages(**kwargs)
                    log.debug('Episode Raw Image Acquasition started')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['raw_image'],
                                                          'Raw Episode Images',
                                                          'RawEpisodeImages Aquatsition started')
                    raw_images_episode.acquire()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['raw_image'],
                                                          'Raw Episode Images',
                                                          'RawEpisodeImages Aquatsition finished')
                    log.debug('Episode Raw Image Acquasition finished')
                    self.set_process_last_run_end(self.process_dict['raw_image'])
                    self.set_process_force_run(self.process_dict['user'])
                    self.set_process_force_run(self.process_dict['artwork'])

                if 'user' in process_run_list:
                    log.debug('Initialising User Specifics')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['user'],
                                                          'User Specifics',
                                                          'Initialising User_Specifics')
                    user_specifics = User_Specifics(**kwargs)
                    log.debug('User Specifics started')
                    self.set_process_last_run_start(self.process_dict['user'])
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['user'],
                                                          'User Specifics',
                                                          'User_Specifics started')
                    user_specifics.process()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['user'],
                                                          'User Specifics',
                                                          'User_Specifics finished')
                    log.debug('User Specifics finished')
                    self.set_process_last_run_end(self.process_dict['user'])
                    self.set_process_force_run(self.process_dict['artwork'])

                if 'artwork' in process_run_list:
                    log.debug('Initialising Artwork')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['artwork'],
                                                          'Artwork',
                                                          'Initialising Artwork')
                    artwork = Artwork(**kwargs)
                    log.debug('Show Artwork Generation started')
                    self.set_process_last_run_start(self.process_dict['artwork'])
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['artwork'],
                                                          'Artwork',
                                                          'Rendering Artwork started')
                    artwork.render()
                    #log.error('sleeping for a bit now')
                    #time.sleep(84600)

                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['artwork'],
                                                          'Artwork',
                                                          'Rendering Artwork finished')
                    log.debug('Show Artwork Generation finished')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['artwork'],
                                                          'Artwork Episode',
                                                          'Initialising ArtworkEpisode')
                    artwork_episode = ArtworkEpisode(**kwargs)
                    log.debug('Episode Artwork Generation started')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['artwork'],
                                                          'Artwork Episode',
                                                          'Rendering ArtworkEpisode started')
                    artwork_episode.render()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['artwork'],
                                                          'Artwork Episode',
                                                          'Rendering ArtworkEpisode finished')
                    log.debug('Episode Generation finished')
                    self.set_process_last_run_end(self.process_dict['artwork'])

                if 'inverse_scan' in process_run_list:
                    log.debug('Initialising InverseScan')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['inverse_scan'],
                                                          'Inverse Scan',
                                                          'Initialising InverseScan')
                    inverse_scan = InverseScan(**kwargs)
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['inverse_scan'],
                                                          'Inverse Scan',
                                                          'Initialised InverseScan')
                    log.debug('InverseScan started')
                    self.set_process_last_run_start(self.process_dict['inverse_scan'])
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['inverse_scan'],
                                                          'Inverse Scan',
                                                          'Verifying tv files still exist')
                    inverse_scan.scan()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['inverse_scan'],
                                                          'Inverse Scan',
                                                          'Verifying tv files still exist completed')
                    log.debug('InverseScan finished')
                    self.set_process_last_run_end(self.process_dict['inverse_scan'])

                if 'tidyup' in process_run_list:
                    # todo score
                    self.set_process_last_run_start(self.process_dict['tidyup'])
                    self.set_process_last_run_end(self.process_dict['tidyup'])
                self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          0,
                                                      '',
                                                       'Process Run Compelted')
            else:
                self.set_current_library_process_desc(self.library_config_dict['id'],
                                                      0,
                                                      '',
                                                       'No Processes To Be Run. Sleeping 30 secs')
                time.sleep(30)

            # TODO: Tidyup (tvs orpahned, artwork hashes orpahed)
