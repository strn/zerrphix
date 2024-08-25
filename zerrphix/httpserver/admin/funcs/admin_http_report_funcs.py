# -*- coding: utf-8 
from __future__ import unicode_literals, division, absolute_import, print_function

try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse, parse_qs
from sqlalchemy import and_, orm, func, or_
import logging
from zerrphix.db.tables import TABLES
from zerrphix.util.plugin import create_eapi_dict
from zerrphix.util.text import date_time
from datetime import timedelta
from six import string_types
import re

# https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-ii-templates
# https://stackoverflow.com/questions/10946795/render-multiple-templates-at-once-in-flask
# https://www.w3schools.com/w3css/tryw3css_templates_analytics.htm
# http://fontawesome.io/cheatsheet/
# https://github.com/jpercent/flask-control
# http://code.nabla.net/doc/jinja2/api/jinja2/jinja2.filters.html
log = logging.getLogger(__name__)


class AdminHTTPReportFuncs(object):
    def __init__(self, Session, global_config_dict):
        # logging.config.dictConfig(LOG_SETTINGS)
        self.Session = Session
        self.global_config_dict = global_config_dict
        self.eapi_dict = create_eapi_dict(Session)

    def get_issue_count_dict(self):
        session = self.Session()
        now_dbfmt_hour = date_time(offset=timedelta(hours=1))
        now_dbfmt_day = date_time(offset=timedelta(hours=24))
        now_dbfmt_week = date_time(offset=timedelta(weeks=1))
        fatal_hour = session.query(
            TABLES.ZP_DB_LOG
        ).filter(
            TABLES.ZP_DB_LOG.LEVEL == 60
        ).filter(
            TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME > now_dbfmt_hour
        ).count()
        fatal_day = session.query(
            TABLES.ZP_DB_LOG
        ).filter(
            TABLES.ZP_DB_LOG.LEVEL == 60
        ).filter(
            TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME > now_dbfmt_day
        ).count()
        fatal_week = session.query(
            TABLES.ZP_DB_LOG
        ).filter(
            TABLES.ZP_DB_LOG.LEVEL == 60
        ).filter(
            TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME > now_dbfmt_week
        ).count()
        exception_hour = session.query(
            TABLES.ZP_DB_LOG
        ).filter(
            TABLES.ZP_DB_LOG.LEVEL == 45
        ).filter(
            TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME > now_dbfmt_hour
        ).count()
        exception_day = session.query(
            TABLES.ZP_DB_LOG
        ).filter(
            TABLES.ZP_DB_LOG.LEVEL == 45
        ).filter(
            TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME > now_dbfmt_day
        ).count()
        exception_week = session.query(
            TABLES.ZP_DB_LOG
        ).filter(
            TABLES.ZP_DB_LOG.LEVEL == 45
        ).filter(
            TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME > now_dbfmt_week
        ).count()
        error_hour = session.query(
            TABLES.ZP_DB_LOG
        ).filter(
            TABLES.ZP_DB_LOG.LEVEL == 40
        ).filter(
            TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME > now_dbfmt_hour
        ).count()
        error_day = session.query(
            TABLES.ZP_DB_LOG
        ).filter(
            TABLES.ZP_DB_LOG.LEVEL == 40
        ).filter(
            TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME > now_dbfmt_day
        ).count()
        error_week = session.query(
            TABLES.ZP_DB_LOG
        ).filter(
            TABLES.ZP_DB_LOG.LEVEL == 40
        ).filter(
            TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME > now_dbfmt_week
        ).count()
        warning_hour = session.query(
            TABLES.ZP_DB_LOG
        ).filter(
            TABLES.ZP_DB_LOG.LEVEL == 30
        ).filter(
            TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME > now_dbfmt_hour
        ).count()
        warning_day = session.query(
            TABLES.ZP_DB_LOG
        ).filter(
            TABLES.ZP_DB_LOG.LEVEL == 30
        ).filter(
            TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME > now_dbfmt_day
        ).count()
        warning_week = session.query(
            TABLES.ZP_DB_LOG
        ).filter(
            TABLES.ZP_DB_LOG.LEVEL == 30
        ).filter(
            TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME > now_dbfmt_week
        ).count()
        session.close()
        #).order_by(TABLES.ZP_INVALID_FILEFOLDER.ZP_SCAN_PATH_ID.asc()).limit(limit).offset(offset)
        return_dict = {'fatal_hour': fatal_hour,
                       'fatal_day': fatal_day,
                       'fatal_week': fatal_week,
                       'exception_hour': exception_hour,
                       'exception_day': exception_day,
                       'exception_week': exception_week,
                       'error_hour': error_hour,
                       'error_day': error_day,
                       'error_week': error_week,
                       'warning_hour': warning_hour,
                       'warning_day': warning_day,
                       'warning_week': warning_week
                       }
        return return_dict

    def get_db_log_entry(self, epoch, source_id):
        session = self.Session()
        rslt_zp_db_log = session.query(
            TABLES.ZP_DB_LOG
        ).filter(
            TABLES.ZP_DB_LOG.EPOCH == epoch,
            TABLES.ZP_DB_LOG.SOURCE_ID == source_id
        ).one()
        session.close()
        return_dict = {'level': rslt_zp_db_log.LEVEL,
                       'text': rslt_zp_db_log.TEXT,
                       'traceback': rslt_zp_db_log.TRACEBACK.split('\n') if
                       isinstance(rslt_zp_db_log.TRACEBACK, string_types) else '',
                       'source_id': rslt_zp_db_log.SOURCE_ID,
                       'first_occurance': rslt_zp_db_log.FIRST_OCCURRENCE_DATE_TIME.strftime("%Y-%m-%d %H:%M:%S"),
                       'last_occurance': rslt_zp_db_log.LAST_OCCURRENCE_DATE_TIME.strftime("%Y-%m-%d %H:%M:%S")}
        return return_dict

    def recent_fatal_exceptions(self, limit=5):
        session = self.Session()
        rslt_zp_fatal_exception_raised = session.query(
            TABLES.ZP_DB_LOG
        ).filter(
            TABLES.ZP_DB_LOG.LEVEL == 60
        ).order_by(
            TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME.desc()
        ).limit(limit)
        session.close()
        return_list = []
        if rslt_zp_fatal_exception_raised is not None:
            for zp_fatal_exception_raised in rslt_zp_fatal_exception_raised:
                return_list.append({'epoch': zp_fatal_exception_raised.EPOCH,
                                    'source_id': zp_fatal_exception_raised.SOURCE_ID,
                                    'description': zp_fatal_exception_raised.TEXT[:150],
                                    'datetime': zp_fatal_exception_raised.LAST_OCCURRENCE_DATE_TIME})
        return return_list

    def recent_exceptions(self, limit=5):
        session = self.Session()
        rslt_zp_fatal_exception_raised = session.query(
            TABLES.ZP_DB_LOG
        ).filter(
            TABLES.ZP_DB_LOG.LEVEL == 45
        ).order_by(
            TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME.desc()
        ).limit(limit)
        session.close()
        return_list = []
        if rslt_zp_fatal_exception_raised is not None:
            for zp_fatal_exception_raised in rslt_zp_fatal_exception_raised:
                return_list.append({'epoch': zp_fatal_exception_raised.EPOCH,
                                    'source_id': zp_fatal_exception_raised.SOURCE_ID,
                                    'description': zp_fatal_exception_raised.TEXT[:150],
                                    'datetime': zp_fatal_exception_raised.LAST_OCCURRENCE_DATE_TIME})
        return return_list

    def recent_errors(self, limit=5):
        session = self.Session()
        rslt_zp_fatal_exception_raised = session.query(
            TABLES.ZP_DB_LOG
        ).filter(
            TABLES.ZP_DB_LOG.LEVEL == 40
        ).order_by(
            TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME.desc()
        ).limit(limit)
        session.close()
        return_list = []
        if rslt_zp_fatal_exception_raised is not None:
            for zp_fatal_exception_raised in rslt_zp_fatal_exception_raised:
                return_list.append({'epoch': zp_fatal_exception_raised.EPOCH,
                                    'source_id': zp_fatal_exception_raised.SOURCE_ID,
                                    'description': zp_fatal_exception_raised.TEXT[:150],
                                    'datetime': zp_fatal_exception_raised.LAST_OCCURRENCE_DATE_TIME})
        return return_list

    def recent_warnings(self, limit=5):
        session = self.Session()
        rslt_zp_fatal_exception_raised = session.query(
            TABLES.ZP_DB_LOG
        ).filter(
            TABLES.ZP_DB_LOG.LEVEL == 30
        ).order_by(
            TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME.desc()
        ).limit(limit)
        session.close()
        return_list = []
        if rslt_zp_fatal_exception_raised is not None:
            for zp_fatal_exception_raised in rslt_zp_fatal_exception_raised:
                return_list.append({'epoch': zp_fatal_exception_raised.EPOCH,
                                    'source_id': zp_fatal_exception_raised.SOURCE_ID,
                                    'description': zp_fatal_exception_raised.TEXT[:150],
                                    'datetime': zp_fatal_exception_raised.LAST_OCCURRENCE_DATE_TIME})
        return return_list
