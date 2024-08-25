# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging
from types import MethodType

from zerrphix.film.artwork import Artwork
from zerrphix.film.artwork_collection import ArtworkCollection
from zerrphix.film.artwork_user import ArtworkUser
from zerrphix.film.data import Data
from zerrphix.film.raw_images import RawImages
from zerrphix.film.raw_collection_images import RawCollectionImages
from zerrphix.film.identify import Identify
from zerrphix.film.metadata import Metadata
from zerrphix.film.scan import Scan
from zerrphix.film.inverse_scan import InverseScan
from zerrphix.film.score import Score
from zerrphix.film.tidyup import Tidyup
from zerrphix.film.user_specifics import User_Specifics
from zerrphix.film.base import FilmBase
from copy import deepcopy
#from zerrphix.util.image_store import create_eapi_library_keep_images_folders
#from zerrphix.util.image_store import make_library_render_root_dir
from zerrphix.db.tables import TABLES
from zerrphix.db import commit
from zerrphix.util.text import date_time
from sqlalchemy import func
from sqlalchemy import orm
import copy
import time
import re
from datetime import datetime
from datetime import timedelta
import os

log = logging.getLogger(__name__)

logging.getLogger("requests").setLevel(logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.DEBUG)
logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)


class FILM(FilmBase):
    """The FILM Class which initiates the indvidual actions e.g. scan.
	"""

    def __init__(self, **kwargs):
        library_config_dict = {'name': 'film', 'id': 1}
        library_config_dict['downloaded_images_library_root_path'] = os.path.join(
           kwargs['global_config_dict']['downloaded_images_root_path'],
            library_config_dict['name']
        )
        kwargs['library_config_dict']=library_config_dict
        super(FilmBase, self).__init__(**kwargs)
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
        self.process_dict = {'scan': 1,
                            'metadata': 2,
                            'score': 3,
                            'identify': 4,
                            'data': 5,
                            'specifics': 6,
                            'artwork': 7,
                            'tidy_up': 8,
                             'raw_images': 19,
                             'inverse_scan': 22}

    def run(self):
        """Run the FILM individual actions.

			The actions are:
				| Scan - Scan the paths defined for films.
				| Metadata - Grab the metadata from each film file found.
				| Score - Calculate a score for each film (for when there are \
				multiple copies of the same films).
				| Identify - Use external sources (eapi) to indetify each film.
				| Data - Grab data from the eapi(s).
				| User_Specifics - Generate user Specifics for each film.
				| Artwork - Generate all the images for each film.

		"""
        #raise AttributeError('test AttributeError from film run func')
        while True:
            kwargs = self.kwargs
            process_run_list = self.get_process_run_list(self.process_dict)
            if process_run_list:
                self.set_library_last_run(1)
                log.debug('process_run_list %s' % process_run_list)
                if not isinstance(process_run_list, list):
                    process_run_list = ['scan',
                                        'metadata',
                                        'score',
                                        'identify',
                                        'data',
                                        'specifics',
                                        'artwork',
                                        'tidy_up',
                                        'inverse_scan']
                if 'scan' in process_run_list:
                    log.debug('Initialising Scan')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['scan'],
                                                          'Scan',
                                                          'Initialising Scan')
                    scan = Scan(**kwargs)
                    log.debug('Scanning scan paths for films started')
                    self.set_process_last_run_start(self.process_dict['scan'])
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['scan'],
                                                          'Scan',
                                                          'Scanning for new films started')
                    scan.scan()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['scan'],
                                                          'Scan',
                                                          'Scanning for new films finished')
                    log.debug('Scanning scan paths for films completed')
                    #raise SystemExit
                    self.set_process_last_run_end(self.process_dict['scan'])
                    self.set_process_force_run(self.process_dict['score'])
                    self.set_process_force_run(self.process_dict['metadata'])
                    self.set_process_force_run(self.process_dict['identify'])

                if 'metadata' in process_run_list:
                    log.debug('Initialising Metadata')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['metadata'],
                                                          'Metadata',
                                                          'Initialising Metadata')
                    metadata = Metadata(**kwargs)
                    log.debug('Metadata aquasition started')
                    self.set_process_last_run_start(self.process_dict['metadata'])
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['metadata'],
                                                          'Metadata',
                                                          'Metadata started')
                    metadata.acquire()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['metadata'],
                                                          'Metadata',
                                                          'Metadata started')
                    log.debug('Metadata aquasition finished')
                    self.set_process_last_run_end(self.process_dict['metadata'])
                    self.set_process_force_run(self.process_dict['score'])

                if 'score' in process_run_list or 'identify' in process_run_list:
                    log.debug('Initialising Score')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['score'],
                                                          'Score',
                                                          'Initialising Score')
                    score = Score(**kwargs)
                    log.debug('Score aquasition started')
                    self.set_process_last_run_start(self.process_dict['score'])
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['score'],
                                                          'Score',
                                                          'Calculate Score started')
                    score.calculate()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['score'],
                                                          'Score',
                                                          'Calculate Score started')
                    log.debug('Score calacualation finished')
                    self.set_process_last_run_end(self.process_dict['score'])
                    self.set_process_force_run(self.process_dict['data'])

                if 'identify' in process_run_list:
                    #raise SystemExit
                    log.debug('Initialising idenfity')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['identify'],
                                                          'Identify',
                                                          'Initialising Identify')
                    idenfity = Identify(**kwargs)
                    log.debug('identfying films started')
                    self.set_process_last_run_start(self.process_dict['identify'])
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['identify'],
                                                          'Identify',
                                                          'Identification of films started')
                    idenfity.idenfity()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['identify'],
                                                          'Identify',
                                                          'Identification of films finished')
                    log.debug('identfying films completed')
                    self.set_process_last_run_end(self.process_dict['identify'])
                    self.set_process_force_run(self.process_dict['data'])
                    self.set_process_force_run(self.process_dict['raw_images'])

                if 'data' in process_run_list:
                    log.debug('Initialising Data')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['data'],
                                                          'Data',
                                                          'Initialising Data')
                    data = Data(**kwargs)
                    log.debug('Data aquasition started')
                    self.set_process_last_run_start(self.process_dict['data'])
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['data'],
                                                          'Data',
                                                          'Filma data auqasition started')
                    data.acquire()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['data'],
                                                          'Data',
                                                          'Filma data auqasition finished')
                    log.debug('Data aquasition finished')
                    self.set_process_last_run_end(self.process_dict['data'])
                    self.set_process_force_run(self.process_dict['raw_images'])
                    self.set_process_force_run(self.process_dict['specifics'])

                if 'raw_images' in process_run_list:
                    log.debug('Initialising raw_images')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['raw_images'],
                                                          'Raw Images',
                                                          'Initialising RawImages')
                    raw_images = RawImages(**kwargs)
                    self.set_process_last_run_start(self.process_dict['raw_images'])
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['raw_images'],
                                                          'Raw Images',
                                                          'RawImages auqasition started')
                    log.debug('raw aq start')
                    raw_images.acquire()
                    log.debug('raw aq end')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['raw_images'],
                                                          'Raw Images',
                                                          'RawImages auqasition finished')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['raw_images'],
                                                          'Raw Collection Images',
                                                          'Initialising RawCollectionImages')
                    raw_collection_images = RawCollectionImages(**kwargs)
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['raw_images'],
                                                          'Raw Collection Images',
                                                          'RawCollectionImages auqasition started')
                    raw_collection_images.acquire()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['raw_images'],
                                                          'Raw Collection Images',
                                                          'RawCollectionImages auqasition finished')
                    log.debug('raw_images aquasition finished')
                    self.set_process_last_run_end(self.process_dict['raw_images'])
                    self.set_process_force_run(self.process_dict['specifics'])

                if 'specifics' in process_run_list:
                    log.debug('Initialising User Specifics')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['specifics'],
                                                          'User Specifics',
                                                          'Initialising User_Specifics')
                    user_specifics = User_Specifics(**kwargs)
                    log.debug('User Specifics started')
                    self.set_process_last_run_start(self.process_dict['specifics'])
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['specifics'],
                                                          'User Specifics',
                                                          'User_Specifics processing started')
                    user_specifics.process()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['specifics'],
                                                          'User Specifics',
                                                          'User_Specifics processing finished')
                    log.debug('User Specifics finished')
                    self.set_process_last_run_end(self.process_dict['specifics'])
                    self.set_process_force_run(self.process_dict['artwork'])

                if 'artwork' in process_run_list:

                    #log.error(self.library_config_dict['name'])
                    _old_library_config_dict_name = deepcopy(self.library_config_dict['name'])
                    self.library_config_dict['name'] = 'user'
                    log.debug('Initialising Artwork User')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['artwork'],
                                                          'Artwork',
                                                          'Initialising Artwork User')
                    artwork_user = ArtworkUser(**kwargs)
                    log.debug('Artwork User Generation started')
                    log.debug('Rendering User Artowrk')
                    self.set_process_last_run_start(self.process_dict['artwork'])
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['artwork'],
                                                          'Artwork User',
                                                          'Artwork User rendering started')
                    artwork_user.render()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['artwork'],
                                                          'Artwork User',
                                                          'Artwork User rendering finished')
                    log.debug('Finished Rendering User Artowrk')

                    #log.error(self.library_config_dict['name'])



                    self.library_config_dict['name'] = _old_library_config_dict_name
                    #log.error(self.library_config_dict['name'])
                    log.debug('Initialising Artwork')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['artwork'],
                                                          'Artwork',
                                                          'Initialising Artwork')
                    artwork = Artwork(**kwargs)
                    log.debug('Artwork Generation started')
                    log.debug('Rendering Film Artowrk')
                    self.set_process_last_run_start(self.process_dict['artwork'])
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['artwork'],
                                                          'Artwork',
                                                          'Artwork rendering started')
                    artwork.render()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['artwork'],
                                                          'Artwork',
                                                          'Artwork rendering finished')
                    log.debug('Finished Rendering Film Artowrk')





                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['artwork'],
                                                          'Artwork Collection',
                                                          'Initialising ArtworkCollection')

                    _old_library_config_dict_name = deepcopy(self.library_config_dict['name'])
                    self.library_config_dict['name'] = 'film_collection'
                    artwork_collection = ArtworkCollection(**kwargs)
                    log.debug('Rendering Film Collection Artowrk')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['artwork'],
                                                          'Artwork Collection',
                                                          'ArtworkCollection rendering started')
                    artwork_collection.render()
                    #log.error('sleeping for a bit')
                    #time.sleep(84600)
                    self.library_config_dict['name'] = _old_library_config_dict_name
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['artwork'],
                                                          'Artwork Collection',
                                                          'ArtworkCollection rendering finished')
                    log.debug('Finished Rendering Film Collection Artowrk')
                    log.debug('Artwork Generation finished')
                    self.set_process_last_run_end(self.process_dict['artwork'])

                if 'inverse_scan' in process_run_list:
                    log.debug('Initialising Metadata')
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['inverse_scan'],
                                                          'Inverse Scan',
                                                          'Initialising InverseScan')
                    inverse_scan = InverseScan(**kwargs)
                    log.debug('InverseScan started')
                    self.set_process_last_run_start(self.process_dict['inverse_scan'])
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['inverse_scan'],
                                                          'Inverse Scan',
                                                          'Verify film files still exist started')
                    inverse_scan.scan()
                    self.set_current_library_process_desc(self.library_config_dict['id'],
                                                          self.process_dict['inverse_scan'],
                                                          'Inverse Scan',
                                                          'Verify film files still exist finished')
                    log.debug('InverseScan finished')
                    self.set_process_last_run_end(self.process_dict['inverse_scan'])

                # TODO: Tidyup (films orpahned, artwork hashes orpahed)

                if 'tidy_up' in process_run_list:
                    #log.debug('Initialising Tidyup')
                    #self.set_current_library_process_desc(self.library_config_dict['id'],
                    #                                      self.process_dict['tidy_up'],
                    #                                      'Tidyup',
                    #                                      'Initialising Tidyup')
                    #tidyup = Tidyup(**kwargs)
                    #log.debug('Tidyup aquasition started')
                    #self.set_process_last_run_start(self.process_dict['tidy_up'])
                    #self.set_current_library_process_desc(self.library_config_dict['id'],
                    #                                      self.process_dict['tidy_up'],
                    #                                      'Tidyup',
                    #                                      'Tidyup check_highest_quality_set started')
                    #tidyup.check_highest_quality_set()
                    #self.set_current_library_process_desc(self.library_config_dict['id'],
                    #                                      self.process_dict['tidy_up'],
                    #                                      'Tidyup',
                    #                                      'Tidyup check_highest_quality_set finished')
                    #log.debug('Tidyup calacualation finished')
                    self.set_process_last_run_end(self.process_dict['tidy_up'])
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
