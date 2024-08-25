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
from zerrphix.util.filesystem import path_avail_space
import os

# https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-ii-templates
# https://stackoverflow.com/questions/10946795/render-multiple-templates-at-once-in-flask
# https://www.w3schools.com/w3css/tryw3css_templates_analytics.htm
# http://fontawesome.io/cheatsheet/
# https://github.com/jpercent/flask-control
# http://code.nabla.net/doc/jinja2/api/jinja2/jinja2.filters.html
log = logging.getLogger(__name__)


class AdminHTTPApiFuncs(object):
    def __init__(self, Session, global_config_dict):
        # logging.config.dictConfig(LOG_SETTINGS)
        self.Session = Session
        self.global_config_dict = global_config_dict
        self.eapi_dict = create_eapi_dict(Session)

    def films_awatting_data_aquasition(self, zp_lang_id):
        session = self.Session()
        qry_film_missing_data = session.query(
            TABLES.ZP_FILM).filter(
            and_(~TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_FILM_ROLE_XREF.ZP_FILM_ID)),
                 ~TABLES.ZP_FILM.ID.in_(
                     session.query(
                         TABLES.ZP_FILM_GENRE_XREF.ZP_FILM_ID)),
                 ~TABLES.ZP_FILM.ID.in_(
                     session.query(
                         TABLES.ZP_FILM_RATING.ZP_FILM_ID)),
                 ~TABLES.ZP_FILM.ID.in_(
                     session.query(
                         TABLES.ZP_FILM_OVERVIEW.ZP_FILM_ID).filter(
                         TABLES.ZP_FILM_OVERVIEW.ZP_LANG_ID == zp_lang_id
                     )),
                 ~TABLES.ZP_FILM.ID.in_(
                     session.query(
                         TABLES.ZP_FILM_RUNTIME.ZP_FILM_ID)),
                 ~TABLES.ZP_FILM.ID.in_(
                     session.query(
                         TABLES.ZP_FILM_TITLE.ZP_FILM_ID).filter(
                         TABLES.ZP_FILM_TITLE.ZP_LANG_ID == zp_lang_id
                     )),
                 ~TABLES.ZP_FILM.ID.in_(
                     session.query(
                         TABLES.ZP_FILM_RELEASE.ZP_FILM_ID)),
                 TABLES.ZP_FILM.ID.in_(
                     session.query(
                         TABLES.ZP_FILM_EAPI_EID.ZP_FILM_ID))),
            ~TABLES.ZP_FILM.ID.in_(session.query(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 2
            ))
        )
        count = qry_film_missing_data.count()
        session.close()
        return count

    def films_awating_images_count(self, zp_lang_id):
        session = self.Session()
        qry_film_missing_raw_eapi_image = session.query(
            TABLES.ZP_FILM).filter(
            TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_FILM_EAPI_EID.ZP_FILM_ID)),
            ~TABLES.ZP_FILM.ID.in_(
            session.query(TABLES.ZP_FILM_RAW_IMAGE.ZP_ENTITY_ID).filter(
                    or_(TABLES.ZP_FILM_RAW_IMAGE.ZP_LANG_ID == zp_lang_id,
                        TABLES.ZP_FILM_RAW_IMAGE.ZP_LANG_ID == None)
                )),
            ~TABLES.ZP_FILM.ID.in_(session.query(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 8
            ))
        )
        count = qry_film_missing_raw_eapi_image.count()
        session.close()
        return count

    def films_awating_artwork_count(self, user_id, image_type_id, zp_dune_id, zp_icon_sub_type):
        session = self.Session()
        log.debug('ZP_USER_ID %s, ZP_FILM_IMAGE_TYPE_ID %s,'
                  ' ZP_DUNE_ID %s, ZP_IMAGE_SUB_TYPE %s',
                 user_id, image_type_id, zp_dune_id, zp_icon_sub_type)
        qry_films_artowrk_to_render = session.query(
            TABLES.ZP_FILM).filter(
            TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_FILM_EAPI_EID.ZP_FILM_ID)),
            TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID)),
            ~TABLES.ZP_FILM.ID.in_(
                session.query(
                    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID).filter(
                    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == user_id,
                    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_ID ==
                    TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID,
                    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID == image_type_id,
                    TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID ==
                    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID,
                    ##

                    # TABLES.ZP_FILM_IMAGE_RENDER_HASH.TEMPLATE_NAME == kwargs['template_name'],
                    # TABLES.ZP_FILM_IMAGE_RENDER_HASH.TEMPLATE_VERSION == kwargs['template_version'],
                    #TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == zp_template_id,
                    TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID,
                    TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.RENDER_DATETIME >=
                    TABLES.ZP_TEMPLATE.LAST_MOD_DATETIME,
                    TABLES.ZP_USER_TEMPLATE_XREF.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID,
                    TABLES.ZP_USER_TEMPLATE_XREF.ZP_USER_ID == TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_USER_ID,

                    ##
                    TABLES.ZP_FILM.ID == TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_ID,
                    TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.RENDER_DATETIME >=
                    TABLES.ZP_FILM.LAST_EDIT_DATETIME,
                    TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_FILM_IMAGE_TYPE_ID ==
                    TABLES.ZP_USER_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_TYPE_ID,
                    TABLES.ZP_FILM_IMAGE_RENDER_HASH.ID ==
                    TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_FILM_IMAGE_RENDER_HASH_ID,
                    TABLES.ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == zp_dune_id,
                    TABLES.ZP_FILM_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE == zp_icon_sub_type))
        )
        count = qry_films_artowrk_to_render.count()
        session.close()
        return count

    def shows_awatting_data_aquasition(self, zp_lang_id):
        session = self.Session()
        qry_tv_missing_data = session.query(
            TABLES.ZP_TV).filter(
            and_(~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_ROLE_XREF.ZP_TV_ID)),
            ~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_GENRE_XREF.ZP_TV_ID)),
            ~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_RATING.ZP_TV_ID)),
            ~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_OVERVIEW.ZP_TV_ID).filter(
                    TABLES.ZP_TV_OVERVIEW.ZP_LANG_ID == zp_lang_id
                )),
            ~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_TITLE.ZP_TV_ID).filter(
                    TABLES.ZP_TV_TITLE.ZP_LANG_ID == zp_lang_id
                )),
            ~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_RELEASE.ZP_TV_ID))),
            TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_EAPI_EID.ZP_TV_ID)),
            ~TABLES.ZP_TV.ID.in_(session.query(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 4
            ))
        )
        count = qry_tv_missing_data.count()
        session.close()
        return count

    def shows_awating_images_count(self, zp_lang_id):
        session = self.Session()
        qry_tv_missing_raw_eapi_image = session.query(
            TABLES.ZP_TV).filter(
            ~TABLES.ZP_TV.ID.in_(
                session.query(TABLES.ZP_TV_RAW_IMAGE.ZP_ENTITY_ID).filter(
                    or_(TABLES.ZP_TV_RAW_IMAGE.ZP_LANG_ID == zp_lang_id,
                        TABLES.ZP_TV_RAW_IMAGE.ZP_LANG_ID == None)
                )
            ),
            TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_EAPI_EID.ZP_TV_ID)),
            ~TABLES.ZP_TV.ID.in_(session.query(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 9
            ))
        )
        count = qry_tv_missing_raw_eapi_image.count()
        session.close()
        return count

    def shows_awating_artwork_count(self, user_id, image_type_id, temaplte_name,
                                         template_version, zp_dune_id, zp_icon_sub_type):
        session = self.Session()
        qry_tvs_with_eid = session.query(
            TABLES.ZP_TV).filter(
            TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_EAPI_EID.ZP_TV_ID)),
            TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID)),
            ~TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_ID).filter(
                    TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == user_id,
                    TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_ID,
                    TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == image_type_id,
                    TABLES.ZP_TV_IMAGE_RENDER_HASH.ID == \
                    TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID,
                    ##

                    # TABLES.ZP_TV_IMAGE_RENDER_HASH.TEMPLATE_NAME == temaplte_name,
                    # TABLES.ZP_TV_IMAGE_RENDER_HASH.TEMPLATE_VERSION == template_version,

                    TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID,
                    TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.RENDER_DATETIME >=
                    TABLES.ZP_TEMPLATE.LAST_MOD_DATETIME,
                    TABLES.ZP_USER_TEMPLATE_XREF.ZP_TEMPLATE_ID == TABLES.ZP_TEMPLATE.ID,
                    TABLES.ZP_USER_TEMPLATE_XREF.ZP_USER_ID == TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_USER_ID,

                    ##
                    TABLES.ZP_TV.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_ID,
                    TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.RENDER_DATETIME > TABLES.ZP_TV.LAST_EDIT_DATETIME,
                    TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == \
                    TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID,
                    TABLES.ZP_TV_IMAGE_RENDER_HASH.ID == \
                    TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID,
                    TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == zp_dune_id,
                    TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE == zp_icon_sub_type))
        )
        count = qry_tvs_with_eid.count()
        session.close()
        return count

    def films_unidentified_no_retry(self):
        session = self.Session()
        qry_unidentified_filefolder = session.query(
            TABLES.ZP_FILM_FILEFOLDER).filter(
            TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == None,
            ~TABLES.ZP_FILM_FILEFOLDER.ID.in_(session.query(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 1
            ))
        )
        count = qry_unidentified_filefolder.count()
        session.close()
        return count

    def films_unidentified_retry(self):
        session = self.Session()
        qry_unidentified_filefolder = session.query(
            TABLES.ZP_FILM_FILEFOLDER
        ).filter(
            TABLES.ZP_FILM_FILEFOLDER.ZP_FILM_ID == None,
            TABLES.ZP_FILM_FILEFOLDER.ID.in_(session.query(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 1
            ))
        )
        count = qry_unidentified_filefolder.count()
        session.close()
        return count

    def shows_unidentified_no_retry(self):
        session = self.Session()
        qry_unidentified_filefolder = session.query(
            TABLES.ZP_TV_FILEFOLDER).filter(
            TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == None,
            ~TABLES.ZP_TV_FILEFOLDER.ID.in_(session.query(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 5
            )))
        count = qry_unidentified_filefolder.count()
        session.close()
        return count

    def shows_unidentified_retry(self):
        session = self.Session()
        qry_unidentified_filefolder = session.query(
            TABLES.ZP_TV_FILEFOLDER
        ).filter(
            TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == None,
            TABLES.ZP_TV_FILEFOLDER.ID.in_(session.query(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 5
            ))
        )
        count = qry_unidentified_filefolder.count()
        session.close()
        return count

    def current_library_process_running(self, zp_library_id):
        session = self.Session()
        try:
            qry_unidentified_filefolder = session.query(
                TABLES.ZP_PROCESS_RUN.PROCESS_NAME
            ).filter(
                TABLES.ZP_PROCESS_RUN.LAST_RUN_START == session.query(
                    func.max(TABLES.ZP_PROCESS_RUN.LAST_RUN_START)
                ).filter(
                    TABLES.ZP_PROCESS_RUN.ZP_LIBRARY_ID == zp_library_id
                ),
                TABLES.ZP_PROCESS_RUN.LAST_RUN_START > session.query(
                    func.max(TABLES.ZP_PROCESS_RUN.LAST_RUN_END)
                ).filter(
                    TABLES.ZP_PROCESS_RUN.ZP_LIBRARY_ID == zp_library_id
                ),
                TABLES.ZP_PROCESS_RUN.ZP_LIBRARY_ID == zp_library_id
            ).one()
        except orm.exc.NoResultFound:
            process_name = 'None'
        else:
            process_name = qry_unidentified_filefolder.PROCESS_NAME
        session.close()
        return process_name

    def current_library_process_running_state(self, zp_library_id):
        session = self.Session()
        qry_unidentified_filefolder = session.query(
            TABLES.ZP_PROCESS_RUNNING.PROCESS,
            TABLES.ZP_PROCESS_RUNNING.PROCESS_STATE,
            TABLES.ZP_PROCESS_RUNNING.PROCESS_STATE_DATE_TIME
        ).filter(
            TABLES.ZP_PROCESS_RUNNING.ZP_LIBRARY_ID == zp_library_id,
        ).one()
        if qry_unidentified_filefolder.PROCESS_STATE_DATE_TIME is not None:
            process_date_time = qry_unidentified_filefolder.PROCESS_STATE_DATE_TIME.strftime("%Y-%m-%d %H:%M:%S")
        else:
            process_date_time = '##'

        if zp_library_id == 1:
            process = 'Film %s' % qry_unidentified_filefolder.PROCESS
        else:
            process = 'TV %s' % qry_unidentified_filefolder.PROCESS
        processing_state_dict = {'process': process,
                                 'process_state': qry_unidentified_filefolder.PROCESS_STATE,
                                 'date_time': process_date_time
                                }
        session.close()
        return processing_state_dict

    def films_invalid_count(self, zp_library_id, limit=50, offset=0):
        session = self.Session()
        rslt_invalid_filefolder_count = session.query(
            TABLES.ZP_INVALID_FILEFOLDER
        ).filter(
            TABLES.ZP_INVALID_FILEFOLDER.ZP_SCAN_PATH_ID == TABLES.ZP_SCAN_PATH.ID,
            TABLES.ZP_INVALID_FILEFOLDER.ZP_LIBRARY_ID == zp_library_id,
            TABLES.ZP_INVALID_FILEFOLDER.LAST_OCCURANCE_DATETIME > TABLES.ZP_SCAN_PATH.LAST_SCAN_DATETIME
        ).count()
        #).order_by(TABLES.ZP_INVALID_FILEFOLDER.ZP_SCAN_PATH_ID.asc()).limit(limit).offset(offset)
        return_dict = {'count': rslt_invalid_filefolder_count}
        return return_dict

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

    def free_space(self):
        #log.error(self.global_config_dict)
        #os.fstatvfs()
        return_dict = {
            'downloaded_images_avail_space': path_avail_space(
            self.global_config_dict['downloaded_images_root_path'], hr=True),
            'rendered_image_avail_space': path_avail_space(
            self.global_config_dict['rendered_image_root_path'], hr=True)
        }
        return return_dict


