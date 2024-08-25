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
import time

log = logging.getLogger(__name__)


class AdminHTTPProcessFuncs(object):
    def __init__(self, Session, global_config_dict):
        # logging.config.dictConfig(LOG_SETTINGS)
        self.Session = Session
        self.global_config_dict = global_config_dict
        self.eapi_dict = create_eapi_dict(Session)
        self.image_type_id_dict = {'poster': 1, 'backdrop': 2, 'banner': 3}
        self.image_tv_entity_type_id_dict = {'poster': 3, 'backdrop': 4, 'banner': 5}
        self.image_season_type_id_dict = {'poster': 1}
        self.image_tv_season_entity_type_id_dict = {'poster': 1}
        self.image_tv_season_user_entity_type_id_dict = {'poster': 1}
        self.image_episode_type_id_dict = {'screenshot': 4}
        self.image_tv_episode_entity_type_id_dict = {'screenshot': 4}
        self.image_tv_episode_user_entity_type_id_dict = {'screenshot': 3}

    def process_list(self):
        process_list = []
        session = self.Session()
        zp_process_run = session.query(TABLES.ZP_PROCESS_RUN).order_by(
            TABLES.ZP_PROCESS_RUN.ZP_LIBRARY_ID.asc(),
            TABLES.ZP_PROCESS_RUN.ZP_PROCESS_ID.asc()
        ).all()
        if zp_process_run is not None:
            for process in zp_process_run:
                process_list.append({'zp_process_id':process.ZP_PROCESS_ID,
                                     'name': process.PROCESS_NAME,
                                     'zp_library_id': process.ZP_LIBRARY_ID,
                                     'enabled': process.ENABLED,
                                     'last_run_finish': process.LAST_RUN_END,
                                     'force_run': process.FORCE_RUN,
                                     'run_interval': process.RUN_INTERVAL,
                                     'run_between': process.RUN_BETWEEN,
                                     'run_between_start': process.RUN_BETWEEN_START,
                                     'run_between_end': process.RUN_BETWEEN_END})
        session.close()
        return process_list

    def set_process_section(self, zp_process_id, process_dict):
        session = self.Session()
        sucess = False
        log.debug('zp_process_id %s, process_dict %s', zp_process_id, process_dict)
        sections = ['enabled', 'run_between', 'force_run', 'run_interval', 'run_between_start',
                    'run_between_end', 'run_between']
        try:
            zp_process_run = session.query(TABLES.ZP_PROCESS_RUN).filter(
                TABLES.ZP_PROCESS_RUN.ZP_PROCESS_ID == zp_process_id
            ).one()
        except orm.exc.NoResultFound:
            log.error('zp_process_id %s not found in ZP_PROCESS_RUN', zp_process_id)
        else:
            for section in sections:
                if section in ['enabled', 'run_between', 'force_run']:
                    if process_dict[section] == '1':
                        #setattr(zp_process_run, process_dict[section], section)
                        setattr(zp_process_run, section.upper(), 1)
                    else:
                        setattr(zp_process_run, section.upper(), 0)
                        #setattr(zp_process_run, section) = 1
                elif section == 'run_interval':
                    log.debug('process_dict[section] %s', process_dict[section])
                    if process_dict[section].isdigit():
                        setattr(zp_process_run, section.upper(), process_dict[section])
                    else:
                        log.debug('process_dict[section] %s is not a digit', process_dict[section])
                elif section == 'run_between_start' or section == 'run_between_end':
                    process_section_value_len = len(process_dict[section])
                    if process_section_value_len in [3,4]:
                        if process_section_value_len == 3:
                            process_dict[section] = '0%s' % process_dict[section]
                        try:
                            time.strptime(process_dict[section], '%H%M')
                        except ValueError:
                            log.error('process_section_value %s should be in 24hour fromat HHMM e.g. 0600',
                                      process_dict[section])
                        else:
                            setattr(zp_process_run, section.upper(), process_dict[section])
                    else:
                        log.error('process_section_value %s len %s needs to be 3 or 4', process_dict[section],
                            process_section_value_len)
                else:
                    log.error('section %s not supported', section)
            if commit(session):
                sucess = True
        session.close()
        return sucess