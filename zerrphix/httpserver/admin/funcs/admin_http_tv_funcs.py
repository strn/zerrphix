import logging
import re

from sqlalchemy import case
from sqlalchemy import func
# from PIL import Image
from sqlalchemy import orm
from sqlalchemy import or_
from sqlalchemy import and_

from zerrphix.db import commit, flush
from zerrphix.db.tables import TABLES
from zerrphix.tv.util import update_tv_last_mod, update_tv_episode_last_mod
from zerrphix.util.plugin import create_eapi_dict
from zerrphix.util.text import date_time
import os

log = logging.getLogger(__name__)


class AdminHTTPTVFuncs(object):
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

    def check_zp_tv_id_exists(self, zp_tv_id):
        session = self.Session()
        try:
            session.query(TABLES.ZP_TV).filter(TABLES.ZP_TV.ID == zp_tv_id).one()
        except orm.exc.NoResultFound:
            tv_exists = False
        else:
            tv_exists = True
        session.close()
        return tv_exists

    def get_total_num_shows(self):
        session = self.Session()
        num_shows = session.query(TABLES.ZP_TV).count()
        session.close()
        return num_shows

    def reset_tv_filefolder(self, eapi_id, eapi_eid, old_zp_tv_id):
        session = self.Session()
        try:
            zp_tv = session.query(TABLES.ZP_TV).filter(
                TABLES.ZP_TV.ID == old_zp_tv_id
            ).one()
        except orm.exc.NoResultFound:
            log.error('ZP_TV does not exsist with ID %s cannot reset tv', old_zp_tv_id)
        else:
            zp_tv_filefolder_id = zp_tv.ZP_TV_FILEFOLDER_ID
            zp_tv.ZP_TV_FILEFOLDER_ID = None
            try:
                session.query(TABLES.ZP_TV_EAPI_EID).filter(
                    TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID == eapi_id,
                    TABLES.ZP_TV_EAPI_EID.ZP_EAPI_EID == eapi_eid
                ).one()
            except orm.exc.NoResultFound:
                # todo verify tmdbid
                ADDED_DATE_TIME = date_time()
                add_tv = TABLES.ZP_TV(ADDED_DATE_TIME=ADDED_DATE_TIME,
                                          ZP_TV_FILEFOLDER_ID=zp_tv_filefolder_id,
                                          LAST_EDIT_DATETIME=ADDED_DATE_TIME)
                session.add(add_tv)
                log.debug(('Inserted ADDED_DATE_TIME: {0},'
                           ' ZP_TV_FILEFOLDER_ID:{1}, LAST_EDIT_DATETIME: {0} into ZP_TV').format(
                    ADDED_DATE_TIME,
                    zp_tv_filefolder_id))
                flush(session)
                zp_tv_id = add_tv.ID
                tv_filfolder = session.query(TABLES.ZP_TV_FILEFOLDER).filter(
                    TABLES.ZP_TV_FILEFOLDER.ID == zp_tv_filefolder_id).one()
                tv_filfolder.ZP_TV_ID = zp_tv_id
                add_tv_eapi_eid = TABLES.ZP_TV_EAPI_EID(ZP_TV_ID=zp_tv_id,
                                                            ZP_EAPI_EID=eapi_eid,
                                                            ZP_EAPI_ID=eapi_id)
                session.add(add_tv_eapi_eid)
                flush(session)
                session.query(
                    TABLES.ZP_TV_EPISODE
                ).filter(
                    TABLES.ZP_TV_EPISODE.ZP_TV_ID == old_zp_tv_id
                ).update(
                    {"ZP_TV_ID": zp_tv_id}
                )
                commit(session)
            else:
                #session.query(TABLES.ZP_TV_FILEFOLDER).filter(
                #    TABLES.ZP_TV_FILEFOLDER.ID == zp_tv_filefolder_id).update(
                #    {'ZP_TV_ID': zp_tv_eapi_eid.ZP_TV_ID})
                #commit(session)
                log.error('there should not be a tv allready existing with given eapi_id %s, eapi_eid %s',
                          eapi_id, eapi_eid)
        session.close()
        return True

    def tv_list(self, limit=50, offset=0, sort_type='alpha_asc', search=None):
        tv_list = []
        session = self.Session()
        if search:
            tvs = session.query(TABLES.ZP_TV.ID,
                                TABLES.ZP_TV_TITLE.TITLE).join(
                TABLES.ZP_TV_TITLE, TABLES.ZP_TV_TITLE.ID == session.query(TABLES.ZP_TV_TITLE.ID).filter(
                    TABLES.ZP_TV_TITLE.ZP_TV_ID == TABLES.ZP_TV.ID).limit(1).correlate(TABLES.ZP_TV)
            ).filter(
                TABLES.ZP_TV.ID.in_(
                    session.query(
                        TABLES.ZP_TV_FILEFOLDER_XREF.ZP_TV_ID
                    )
                ),
                TABLES.ZP_TV_TITLE.TITLE.like('%%%s%%' % search)
            ).order_by(TABLES.ZP_TV_TITLE.TITLE.asc()).limit(limit).offset(offset)
        elif sort_type == 'added_desc':
            tvs = session.query(
                TABLES.ZP_TV.ID,
                TABLES.ZP_TV_TITLE.TITLE
            ).join(
                TABLES.ZP_TV_TITLE, TABLES.ZP_TV_TITLE.ID == session.query(TABLES.ZP_TV_TITLE.ID).filter(
                    TABLES.ZP_TV_TITLE.ZP_TV_ID == TABLES.ZP_TV.ID).limit(1).correlate(TABLES.ZP_TV)
            ).filter(
                TABLES.ZP_TV.ID.in_(
                    session.query(
                        TABLES.ZP_TV_FILEFOLDER_XREF.ZP_TV_ID
                    )
                )
            ).order_by(TABLES.ZP_TV.ADDED_DATE_TIME.desc()).limit(limit).offset(offset)
        elif sort_type == 'added_asc':
            tvs = session.query(
                TABLES.ZP_TV.ID,
                TABLES.ZP_TV_TITLE.TITLE
            ).join(
                TABLES.ZP_TV_TITLE, TABLES.ZP_TV_TITLE.ID == session.query(TABLES.ZP_TV_TITLE.ID).filter(
                    TABLES.ZP_TV_TITLE.ZP_TV_ID == TABLES.ZP_TV.ID).limit(1).correlate(TABLES.ZP_TV)
            ).filter(
                TABLES.ZP_TV.ID.in_(
                    session.query(
                        TABLES.ZP_TV_FILEFOLDER_XREF.ZP_TV_ID
                    )
                )
            ).order_by(TABLES.ZP_TV.ADDED_DATE_TIME.asc()).limit(limit).offset(offset)
        elif sort_type == 'alpha_desc':
            tvs = session.query(
                TABLES.ZP_TV.ID,
                TABLES.ZP_TV_TITLE.TITLE
            ).join(
                TABLES.ZP_TV_TITLE, TABLES.ZP_TV_TITLE.ID == session.query(TABLES.ZP_TV_TITLE.ID).filter(
                    TABLES.ZP_TV_TITLE.ZP_TV_ID == TABLES.ZP_TV.ID).limit(1).correlate(TABLES.ZP_TV)
            ).filter(
                TABLES.ZP_TV.ID.in_(
                    session.query(
                        TABLES.ZP_TV_FILEFOLDER_XREF.ZP_TV_ID
                    )
                )
            ).order_by(TABLES.ZP_TV_TITLE.TITLE.desc()).limit(limit).offset(offset)
        else:
            tvs = session.query(
                TABLES.ZP_TV.ID,
                TABLES.ZP_TV_TITLE.TITLE
            ).join(
                TABLES.ZP_TV_TITLE, TABLES.ZP_TV_TITLE.ID == session.query(TABLES.ZP_TV_TITLE.ID).filter(
                    TABLES.ZP_TV_TITLE.ZP_TV_ID == TABLES.ZP_TV.ID).limit(1).correlate(TABLES.ZP_TV)
            ).filter(
                TABLES.ZP_TV.ID.in_(
                    session.query(
                        TABLES.ZP_TV_FILEFOLDER_XREF.ZP_TV_ID
                    )
                )
            ).order_by(TABLES.ZP_TV_TITLE.TITLE.asc()).limit(limit).offset(offset)
        for tv in tvs:
            tv_list.append({'title': tv.TITLE,
                            'id': tv.ID})
        session.close()
        return tv_list

    def get_tv_filefolder_id_list(self, zp_tv_id):
        return_list = []
        session = self.Session()
        zp_filefolder_xref_rslt = session.query(
            TABLES.ZP_TV_FILEFOLDER_XREF
        ).filter(
            TABLES.ZP_TV_FILEFOLDER_XREF.ZP_TV_ID == zp_tv_id
        ).all()
        session.close()
        for zp_filefolder_xref in zp_filefolder_xref_rslt:
            return_list.append(zp_filefolder_xref.ZP_TV_FILEFOLDER_ID)
        return return_list

    def tv_path_list(self, zp_tv_filefolder_id_list):
        tv_path_list = []
        session = self.Session()
        zp_film_filefolder_rslt = session.query(
            TABLES.ZP_TV_FILEFOLDER
        ).filter(
            TABLES.ZP_TV_FILEFOLDER.ID.in_(zp_tv_filefolder_id_list)
        ).all()
        session.close()
        for zp_film_filefolder in zp_film_filefolder_rslt:
            zp_scan_path_id = zp_film_filefolder.ZP_SCAN_PATH_ID
            scan_path = self.zp_scan_path_string(zp_scan_path_id)
            path = '%s/%s' % (scan_path, zp_film_filefolder.LAST_PATH)
            tv_path_list.append(path)
        return tv_path_list

    def zp_scan_path_string(self, zp_scan_path_id):
        session = self.Session()
        try:
            rslt_scan_path = session.query(
                TABLES.ZP_SCAN_PATH.PATH,
                TABLES.ZP_SCAN_PATH.ZP_SCAN_PATH_FS_TYPE_ID,
                TABLES.ZP_SHARE.SHARE_NAME,
                TABLES.ZP_SHARE_SERVER.REMOTE_NAME,
                TABLES.ZP_SHARE_SERVER.HOSTNAME,
                TABLES.ZP_SHARE_SERVER.PORT,
                TABLES.ZP_SHARE_CREDENTIAL.USERNAME
            ).outerjoin(
                TABLES.ZP_SCAN_PATH_SHARE_XREF, TABLES.ZP_SCAN_PATH.ID == TABLES.ZP_SCAN_PATH_SHARE_XREF.ZP_SCAN_PATH_ID
            ).outerjoin(
                TABLES.ZP_SHARE, TABLES.ZP_SHARE.ID == TABLES.ZP_SCAN_PATH_SHARE_XREF.ZP_SHARE_ID
            ).outerjoin(
                TABLES.ZP_SHARE_SERVER,
                TABLES.ZP_SHARE_SERVER.ID == TABLES.ZP_SCAN_PATH_SHARE_XREF.ZP_SHARE_SERVER_ID
            ).outerjoin(
                TABLES.ZP_SHARE_CREDENTIAL,
                TABLES.ZP_SHARE_CREDENTIAL.ID == TABLES.ZP_SCAN_PATH_SHARE_XREF.ZP_SHARE_CREDENTIAL_ID
            ).filter(
                TABLES.ZP_SCAN_PATH.ID == zp_scan_path_id
            ).one()
        except orm.exc.NoResultFound:
            path = ''
        else:
            if rslt_scan_path.ZP_SCAN_PATH_FS_TYPE_ID == 1:
                path = rslt_scan_path.PATH
            else:
                path = 'smb://%s@%s[%s]:%s/%s/%s' % (rslt_scan_path.USERNAME,
                                   rslt_scan_path.HOSTNAME,
                                   rslt_scan_path.REMOTE_NAME,
                                   rslt_scan_path.PORT,
                                   rslt_scan_path.SHARE_NAME,
                                   rslt_scan_path.PATH)
        return path

    def tv_genres(self, zp_tv_id):
        session = self.Session()
        tv_genre_list = []
        tv_genres = session.query(TABLES.ZP_TV_GENRE_XREF.ZP_GENRE_ID).filter(
            TABLES.ZP_TV_GENRE_XREF.ZP_TV_ID == zp_tv_id).all()
        session.close()
        for tv in tv_genres:
            tv_genre_list.append(tv.ZP_GENRE_ID)
        return tv_genre_list

    def tv_monitored(self):
        session = self.Session()
        tv_running_list = []
        tvs = session.query(
            TABLES.ZP_TV_RUNNING.ZP_TV_ID,
            TABLES.ZP_TV_TITLE.TITLE
        ).join(
            TABLES.ZP_TV_TITLE, TABLES.ZP_TV_TITLE.ID == session.query(
                TABLES.ZP_TV_TITLE.ID
            ).filter(
                TABLES.ZP_TV_TITLE.ZP_TV_ID == TABLES.ZP_TV_RUNNING.ZP_TV_ID
            ).limit(1).correlate(TABLES.ZP_TV_RUNNING)
        ).join(
            TABLES.ZP_TV, TABLES.ZP_TV.ID == TABLES.ZP_TV_RUNNING.ZP_TV_ID
        ).filter(
            TABLES.ZP_TV.ID.in_(
                session.query(
                    TABLES.ZP_TV_FILEFOLDER_XREF.ZP_TV_ID
                )
            )
        ).order_by(
            TABLES.ZP_TV_TITLE.TITLE.asc()
        )
        session.close()
        for tv in tvs:
            tv_running_list.append({'zp_tv_id': tv.ZP_TV_ID,
                                    'title': tv.TITLE})
        return tv_running_list

    def clear_tv_monitored(self):
        session = self.Session()
        session.query(TABLES.ZP_TV_RUNNING).delete()
        commit(session)
        session.close()

    def add_tv_monitored(self, zp_tv_id):
        session = self.Session()
        add_zp_tv_running = TABLES.ZP_TV_RUNNING(ZP_TV_ID=zp_tv_id)
        session.add(add_zp_tv_running)
        commit(session)
        session.close()

    def get_unidentified_shows(self):
        return_list = []
        session = self.Session()
        unidentified = session.query(
            TABLES.ZP_TV_FILEFOLDER
        ).filter(
            TABLES.ZP_TV_FILEFOLDER.ZP_TV_ID == None,
            TABLES.ZP_TV_FILEFOLDER.ID.in_(session.query(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_ID).filter(
                TABLES.ZP_RETRY.ZP_RETRY_ENTITY_TYPE_ID == 5
            ))
        ).all()
        for filefolder in unidentified:
            #path = os.path.join(filefolder.SCAN_PATH_SUB_DIR, filefolder.LAST_PATH)
            temp_dict = {'path': filefolder.LAST_PATH, 'id': filefolder.ID}
            return_list.append(temp_dict)
        session.close()
        return return_list


    def check_zp_filefolder_id_exists(self, zp_filefolder_id):
        session = self.Session()
        try:
            session.query(TABLES.ZP_TV_FILEFOLDER).filter(
                TABLES.ZP_TV_FILEFOLDER.ID == zp_filefolder_id).one()
        except orm.exc.NoResultFound:
            exists = False
        else:
            exists = True
        session.close()
        return exists

    def check_unidentified(self, zp_filefolder_id):
        return_dict = {'unidentified': False, 'title': ''}
        session = self.Session()
        zp_tv_filefolder = session.query(TABLES.ZP_TV_FILEFOLDER).filter(
            TABLES.ZP_TV_FILEFOLDER.ID == zp_filefolder_id).one()
        #path = os.path.join(ZP_TV_FILEFOLDER.SCAN_PATH_SUB_DIR, ZP_TV_FILEFOLDER.LAST_PATH)
        return_dict['title'] = zp_tv_filefolder.LAST_PATH
        if zp_tv_filefolder.ZP_TV_ID is None:
            return_dict['unidentified'] = True
        session.close()
        return return_dict

    def set_filefolder_eapieid(self, eapi_id, eapi_eid, zp_filefolder_id):
        session = self.Session()
        ADDED_DATE_TIME = date_time()
        try:
            zp_tv_eapi_eid = session.query(
                TABLES.ZP_TV_EAPI_EID
            ).filter(
                TABLES.ZP_TV_EAPI_EID.ZP_EAPI_ID == eapi_id,
                TABLES.ZP_TV_EAPI_EID.ZP_EAPI_EID == eapi_eid
            ).one()
        except orm.exc.NoResultFound:
            # todo verify tmdbid
            add_tv = TABLES.ZP_TV(
                ADDED_DATE_TIME=ADDED_DATE_TIME,
                LAST_EDIT_DATETIME=ADDED_DATE_TIME
            )
            session.add(add_tv)
            log.debug(('Inserted ADDED_DATE_TIME: {0},'
                       ' ZP_TV_FILEFOLDER_ID:{1}, LAST_EDIT_DATETIME: {0} into ZP_TV').format(
                ADDED_DATE_TIME,
                zp_filefolder_id))
            flush(session)
            zp_tv_id = add_tv.ID
            tv_filfolder = session.query(
                TABLES.ZP_TV_FILEFOLDER
            ).filter(
                TABLES.ZP_TV_FILEFOLDER.ID == zp_filefolder_id
            ).one()
            tv_filfolder.ZP_TV_ID = zp_tv_id
            add_tv_eapi_eid = TABLES.ZP_TV_EAPI_EID(
                ZP_TV_ID=zp_tv_id,
                ZP_EAPI_EID=eapi_eid,
                ZP_EAPI_ID=eapi_id
            )
            session.add(add_tv_eapi_eid)
            flush(session)
        else:
            session.query(
                TABLES.ZP_TV_FILEFOLDER
            ).filter(
                TABLES.ZP_TV_FILEFOLDER.ID == zp_filefolder_id
            ).update(
                {'ZP_TV_ID': zp_tv_eapi_eid.ZP_TV_ID}
            )
            zp_tv_id = zp_tv_eapi_eid.ZP_TV_ID
        add_tv_xref = TABLES.ZP_TV_FILEFOLDER_XREF(
            ZP_TV_ID=zp_tv_id,
            ADDED_DATE_TIME=ADDED_DATE_TIME,
            ZP_TV_FILEFOLDER_ID=zp_filefolder_id
        )
        session.add(add_tv_xref)
        commit(session)
        session.close()
        return True

    def tv_overview(self, zp_tv_id, zp_user_id):
        session = self.Session()
        try:
            tv_overview = session.query(TABLES.ZP_TV_OVERVIEW).filter(
                TABLES.ZP_TV_OVERVIEW.ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_ID,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 2).one().OVERVIEW
        except orm.exc.NoResultFound:
            tv_overview = 'No Overview Found or User Specifics is yet to run'
        session.close()
        return tv_overview

    def tv_episode_overview(self, zp_tv_id, season, episode, zp_user_id):
        session = self.Session()
        try:
            tv_overview = session.query(TABLES.ZP_TV_EPISODE_OVERVIEW).filter(
                TABLES.ZP_TV_EPISODE_OVERVIEW.ID == TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_ID,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON == season,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE == episode,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 2).one().OVERVIEW
        except orm.exc.NoResultFound:
            tv_overview = 'No Overview Found or User Specifics is yet to run'
        session.close()
        return tv_overview

    def tv_title(self, zp_tv_id, zp_user_id, strict=False):
        session = self.Session()
        try:
            tv_title = session.query(TABLES.ZP_TV_TITLE).filter(
                TABLES.ZP_TV_TITLE.ID == TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_ID,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1).one().TITLE
        except orm.exc.NoResultFound:
            # if there is not a title for a user but one exists we should try and use one
            # to show on the admin web interface to show which tv is being edited
            if strict is True:
                tv_title = 'No Title Found or User Specifics is yet to run'
            else:
                try:
                    tv_title = session.query(TABLES.ZP_TV_TITLE).filter(
                        TABLES.ZP_TV_TITLE.ZP_TV_ID == zp_tv_id).limit(1).one().TITLE
                except orm.exc.NoResultFound:
                    tv_title = 'No Title Found or User Specifics is yet to run'
        session.close()
        return tv_title

    def tv_episode_title(self, zp_tv_id, season, episode, zp_user_id, strict=False):
        session = self.Session()
        try:
            tv_title = session.query(TABLES.ZP_TV_EPISODE_TITLE).filter(
                TABLES.ZP_TV_EPISODE_TITLE.ID == TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_ID,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON == season,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE == episode,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1).one().TITLE
        except orm.exc.NoResultFound:
            # if there is not a title for a user but one exists we should try and use one
            # to show on the admin web interface to show which tv is being edited
            if strict is True:
                tv_title = 'No Title Found or User Specifics is yet to run'
            else:
                try:
                    tv_title = session.query(TABLES.ZP_TV_EPISODE_TITLE).filter(
                        TABLES.ZP_TV_TITLE.ZP_TV_ID == zp_tv_id,
                        TABLES.ZP_TV_EPISODE_TITLE.SEASON == season,
                        TABLES.ZP_TV_EPISODE_TITLE.EPISODE == episode
                    ).limit(1).one().TITLE
                except orm.exc.NoResultFound:
                    tv_title = 'No Title Found or User Specifics is yet to run'
        session.close()
        return tv_title

    def tv_rating(self, zp_tv_id):
        session = self.Session()
        try:
            tv_rating = session.query(TABLES.ZP_TV_RATING).filter(
                TABLES.ZP_TV_RATING.ZP_TV_ID == zp_tv_id).one().RATING
        except orm.exc.NoResultFound:
            tv_rating = 5
        session.close()
        return tv_rating

    def update_rating(self, zp_tv_id, rating):
        session = self.Session()
        result = True
        try:
            tv_rating = session.query(TABLES.ZP_TV_RATING).filter(
                TABLES.ZP_TV_RATING.ZP_TV_ID == zp_tv_id).one()
        except orm.exc.NoResultFound:
            result = False
        else:
            tv_rating.RATING = rating
            commit(session)
            update_tv_last_mod(self.Session, zp_tv_id)
        session.close()
        return result

    def tv_cast(self, zp_tv_id):
        session = self.Session()
        tv_cast_list = []

        subq = session.query(TABLES.ZP_TV_ROLE_XREF.ZP_PEOPLE_ID,
                             func.count(TABLES.ZP_TV_ROLE_XREF.ZP_PEOPLE_ID).label('pcount')).group_by(
            TABLES.ZP_TV_ROLE_XREF.ZP_PEOPLE_ID).subquery()
        tv_cast = session.query(TABLES.ZP_PEOPLE.NAME, TABLES.ZP_PEOPLE.ID, subq.c.pcount).join(
            TABLES.ZP_TV_ROLE_XREF, TABLES.ZP_TV_ROLE_XREF.ZP_PEOPLE_ID == TABLES.ZP_PEOPLE.ID).join(
            subq, subq.c.ZP_PEOPLE_ID == TABLES.ZP_PEOPLE.ID).filter(
            TABLES.ZP_TV_ROLE_XREF.ZP_TV_ID == zp_tv_id,
            TABLES.ZP_TV_ROLE_XREF.ZP_ROLE_ID == 1,
        ).order_by(case([(TABLES.ZP_TV_ROLE_XREF.ROLE_ORDER == None, 1)], else_=0),
                   TABLES.ZP_TV_ROLE_XREF.ROLE_ORDER.asc(), subq.c.pcount.desc()).all()
        session.close()
        for cast in tv_cast:
            tv_cast_list.append({'id': cast.ID,
                                 'name': cast.NAME})
        return tv_cast_list

    def get_user_tv_raw_image_id(self, zp_tv_id, zp_tv_entity_type_id, zp_user_id):
        session = self.Session()
        zp_tv_raw_image_id = None
        try:
            zp_tv_raw_image_id = session.query(TABLES.ZP_USER_TV_ENTITY_XREF).filter(
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == zp_tv_entity_type_id).one(
            ).ZP_TV_ENTITY_ID
        except orm.exc.NoResultFound:
            log.debug('no result found for zp_tv_id %s, zp_user_id %s, zp_tv_entity_type_id %s',
                      zp_tv_id, zp_user_id, zp_tv_entity_type_id)
        session.close()
        return zp_tv_raw_image_id

    def get_user_tv_season_raw_image_id(self, zp_tv_id, season, zp_tv_entity_type_id, zp_user_id):
        session = self.Session()
        zp_tv_raw_image_id = None
        try:
            zp_tv_raw_image_id = session.query(TABLES.ZP_USER_TV_SEASON_ENTITY_XREF).filter(
                TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.SEASON == season,
                TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == zp_tv_entity_type_id).one(
            ).ZP_TV_ENTITY_ID
        except orm.exc.NoResultFound:
            log.error('no result found for zp_tv_id %s, season %s, zp_user_id %s, zp_tv_entity_type_id %s',
                      zp_tv_id, season, zp_user_id, zp_tv_entity_type_id)
        session.close()
        return zp_tv_raw_image_id

    def get_user_tv_episode_raw_image_id(self, zp_tv_id, season, episode, zp_tv_entity_type_id, zp_user_id):
        session = self.Session()
        zp_tv_raw_image_id = None
        try:
            zp_tv_raw_image_id = session.query(TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF).filter(
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON == season,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE == episode,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == zp_tv_entity_type_id).one(
            ).ZP_TV_ENTITY_ID
        except orm.exc.NoResultFound:
            log.debug('no result found for zp_tv_id %s, zp_user_id %s, zp_tv_entity_type_id %s',
                      zp_tv_id, zp_user_id, zp_tv_entity_type_id)
        session.close()
        return zp_tv_raw_image_id

    def tv_rendered_image(self, zp_tv_id, image_type_id, zp_icon_sub_type_id, zp_user_id):
        session = self.Session()
        rendered_image_id = None
        try:
            rendered_image_id = session.query(
                TABLES.ZP_TV_IMAGE_RENDER_HASH
            ).join(
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF,
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_ID ==
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_ID
            ).filter(
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID ==
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID,
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID == image_type_id,
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID ==
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ID,
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE == zp_icon_sub_type_id,
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE ==
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_IMAGE_SUB_TYPE,
                TABLES.ZP_USER_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_ID ==
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_ID
            ).one().ID
        except orm.exc.NoResultFound:
            log.error('could not find entry in ZP_TV_IMAGE_RENDER_HASH for zp_user_id %s, zp_tv_id %s,'
                      ' image_type_id %s', zp_user_id, zp_tv_id, image_type_id)
        session.close()
        return rendered_image_id

    def tv_episode_rendered_image_list(self, zp_tv_id, season,  episode,image_type_id, zp_user_id):
        return_list = []
        image_sub_type_desc_by_id_dict = {1: 'Unwatched Unselected',
                                     2: 'Unwatched Selected',
                                     3: 'Watched Unselected',
                                     4: 'Watched Selected'}
        session = self.Session()
        rslt_zp_tv_episode_image_render_hash = session.query(
            TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH
        ).join(
            TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF,
            and_(TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TV_ID,
                 TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.FIRST_EPISODE == TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.FIRST_EPISODE,
                 TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.SEASON == TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.SEASON)
        ).filter(
            TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == zp_user_id,
            TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID == TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID,
            TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID == image_type_id,
            TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == zp_tv_id,
            TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.FIRST_EPISODE == episode,
            TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.SEASON == season,
            TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID == TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ID
        ).order_by(
            TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE.asc()
        ).all()
        session.close()
        if rslt_zp_tv_episode_image_render_hash is not None:
            for zp_tv_episode_image_render_hash in rslt_zp_tv_episode_image_render_hash:
                return_list.append(
                    {'id': zp_tv_episode_image_render_hash.ID,
                     'desc': image_sub_type_desc_by_id_dict[zp_tv_episode_image_render_hash.ZP_IMAGE_SUB_TYPE]}
                )
        return return_list

    def tv_episode_rendered_image(self, zp_tv_id, season,  episode, image_type_id, icon_sub_type_id, zp_user_id):
        session = self.Session()
        rendered_image_id = None
        try:
            rendered_image_id = session.query(
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH
            ).join(
                TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF,
                and_(
                    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_ID ==
                    TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TV_ID,
                    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.FIRST_EPISODE ==
                    TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.FIRST_EPISODE,
                    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.SEASON ==
                    TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.SEASON,
                    TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE ==
                    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_IMAGE_SUB_TYPE,
                    TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID ==
                    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID,
                    TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ID ==
                    TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID
                )
            ).filter(
                TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_TYPE_ID == image_type_id,
                TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.FIRST_EPISODE == episode,
                TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.SEASON == season,
                TABLES.ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_IMAGE_SUB_TYPE == icon_sub_type_id
            ).order_by(
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE.asc()
            ).one().ID
        except orm.exc.NoResultFound:
            log.warning('could not find entry in ZP_TV_EPISODE_IMAGE_RENDER_HASH for zp_user_id %s, zp_tv_id %s,'
                        ' episode %s, season %s'
                      ' image_type_id %s, zp_icon_sub_type_id %s', zp_user_id, zp_tv_id, episode, season,
                        image_type_id,
                        icon_sub_type_id)

        session.close()
        return rendered_image_id

    def get_tv_raw_image_filename(self, zp_tv_raw_image_id):
        session = self.Session()
        raw_image_filename = None
        zp_tv_id = None
        try:
            zp_tv_raw_image = session.query(TABLES.ZP_TV_RAW_IMAGE).filter(
                TABLES.ZP_TV_RAW_IMAGE.ID == zp_tv_raw_image_id).one()
        except orm.exc.NoResultFound:
            log.error('no entry for zp_tv_raw_image_id %s, ZP_TV_RAW_IMAGE',
                      zp_tv_raw_image_id)
        else:
            raw_image_filename = zp_tv_raw_image.FILENAME
            zp_tv_id = zp_tv_raw_image.ZP_ENTITY_ID
        session.close()
        return raw_image_filename, zp_tv_id

    def get_tv_season_raw_image_filename(self, zp_tv_raw_image_id):
        session = self.Session()
        raw_image_filename = None
        zp_tv_id = None
        season = None
        try:
            zp_tv_raw_image = session.query(TABLES.ZP_TV_SEASON_RAW_IMAGE).filter(
                TABLES.ZP_TV_SEASON_RAW_IMAGE.ID == zp_tv_raw_image_id).one()
        except orm.exc.NoResultFound:
            log.error('no entry for zp_tv_raw_image_id %s, ZP_TV_RAW_IMAGE',
                      zp_tv_raw_image_id)
        else:
            raw_image_filename = zp_tv_raw_image.FILENAME
            zp_tv_id = zp_tv_raw_image.ZP_ENTITY_ID
            season = zp_tv_raw_image.SEASON
        session.close()
        return raw_image_filename, zp_tv_id, season

    def get_tv_episode_raw_image_filename(self, zp_tv_raw_image_id):
        session = self.Session()
        raw_image_filename = None
        zp_tv_id = None
        season = None
        try:
            zp_tv_raw_image = session.query(TABLES.ZP_TV_EPISODE_RAW_IMAGE).filter(
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ID == zp_tv_raw_image_id).one()
        except orm.exc.NoResultFound:
            log.error('no entry for zp_tv_raw_image_id %s, ZP_TV_RAW_IMAGE',
                      zp_tv_raw_image_id)
        else:
            raw_image_filename = zp_tv_raw_image.FILENAME
            zp_tv_id = zp_tv_raw_image.ZP_ENTITY_ID
            season = zp_tv_raw_image.SEASON
        session.close()
        return raw_image_filename, zp_tv_id, season

    def get_tv_rendered_image_filename(self, zp_tv_rendered_image_id):
        session = self.Session()
        rendered_image_filename = None
        zp_tv_id = None
        template_name = None
        image_type_by_id_dict = {1: 'icon', 2: 'synopsis', 3: 'poster', 4:'backdrop'}
        image_sub_type_by_id_dict = {1: '',
                                     2: '_sel',
                                     3: '_watched',
                                     4: '_watched_sel'}
        try:
            zp_tv_rendered_image = session.query(
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TV_ID,
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
                TABLES.ZP_TV_IMAGE_RENDER_HASH.HASH,
                TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.EXT,
                TABLES.ZP_TEMPLATE.REF_NAME
            ).join(
                TABLES.ZP_TEMPLATE, TABLES.ZP_TEMPLATE.ID == TABLES.ZP_TV_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID
            ).join(
                TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF,
                and_(
                    TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_TV_IMAGE_RENDER_HASH_ID ==
                    TABLES.ZP_TV_IMAGE_RENDER_HASH.ID,
                    TABLES.ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == 1
                )
            ).filter(
                TABLES.ZP_TV_IMAGE_RENDER_HASH.ID == zp_tv_rendered_image_id
            ).one()
        except orm.exc.NoResultFound:
            log.error('no entry for zp_tv_rendered_image_id %s, ZP_TV_IMAGE_RENDER_HASH',
                      zp_tv_rendered_image_id)
        else:
            rendered_image_filename = '.%s%s.%s.%s' % (
                image_type_by_id_dict[zp_tv_rendered_image.ZP_TV_IMAGE_TYPE_ID],
                image_sub_type_by_id_dict[zp_tv_rendered_image.ZP_IMAGE_SUB_TYPE],
                zp_tv_rendered_image.HASH,
                zp_tv_rendered_image.EXT
            )
            zp_tv_id = zp_tv_rendered_image.ZP_TV_ID
            template_name = zp_tv_rendered_image.REF_NAME
        session.close()
        return rendered_image_filename, template_name, zp_tv_id

    def get_tv_episode_rendered_image_filename(self, zp_tv_rendered_image_id):
        session = self.Session()
        rendered_image_filename = None
        zp_tv_id = None
        template_name = None
        image_type_by_id_dict = {5: 'episode_icon', 6: 'episode_synopsis', 7: 'episode_screenshot'}
        image_sub_type_by_id_dict = {1: '',
                                     2: '_sel',
                                     3: '_watched',
                                     4: '_watched_sel'}
        try:
            zp_tv_rendered_image = session.query(
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TV_IMAGE_TYPE_ID,
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.SEASON,
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.FIRST_EPISODE,
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_IMAGE_SUB_TYPE,
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TV_ID,
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.HASH,
                TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.EXT,
                TABLES.ZP_TEMPLATE.REF_NAME
            ).join(
                TABLES.ZP_TEMPLATE, TABLES.ZP_TEMPLATE.ID == TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ZP_TEMPLATE_ID
            ).join(
                TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF,
                and_(
                    TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID ==
                    TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ID,
                    TABLES.ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF.ZP_DUNE_ID == 1
                )
            ).filter(
                TABLES.ZP_TV_EPISODE_IMAGE_RENDER_HASH.ID == zp_tv_rendered_image_id
            ).one()
        except orm.exc.NoResultFound:
            log.error('no entry for zp_tv_rendered_image_id %s, ZP_TV_EPISODE_IMAGE_RENDER_HASH',
                      zp_tv_rendered_image_id)
        else:
            rendered_image_filename = '.%s%s.%s_%s.%s.%s' % (
                image_type_by_id_dict[zp_tv_rendered_image.ZP_TV_IMAGE_TYPE_ID],
                image_sub_type_by_id_dict[zp_tv_rendered_image.ZP_IMAGE_SUB_TYPE],
                str(zp_tv_rendered_image.SEASON).zfill(4),
                str(zp_tv_rendered_image.FIRST_EPISODE).zfill(4),
                zp_tv_rendered_image.HASH,
                zp_tv_rendered_image.EXT
            )
            zp_tv_id = zp_tv_rendered_image.ZP_TV_ID
            template_name = zp_tv_rendered_image.REF_NAME
        session.close()
        return rendered_image_filename, template_name, zp_tv_id

    def get_user_tv_title_id(self, zp_tv_id, zp_user_id):
        session = self.Session()
        zp_tv_title_id = None
        try:
            zp_tv_title_id = session.query(TABLES.ZP_USER_TV_ENTITY_XREF).filter(
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1
            ).one().ZP_TV_ENTITY_ID
        except orm.exc.NoResultFound:
            zp_tv_title_id = None
        session.close()
        return zp_tv_title_id

    def get_user_tv_episode_title_id(self, zp_tv_id, season, episode, zp_user_id):
        session = self.Session()
        zp_tv_title_id = None
        try:
            zp_tv_title_id = session.query(TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF).filter(
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON == season,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE == episode,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 1
            ).one().ZP_TV_ENTITY_ID
        except orm.exc.NoResultFound:
            zp_tv_title_id = None
        session.close()
        return zp_tv_title_id

    def get_user_tv_overview_id(self, zp_tv_id, zp_user_id):
        session = self.Session()
        zp_tv_title_id = None
        try:
            zp_tv_title_id = session.query(TABLES.ZP_USER_TV_ENTITY_XREF).filter(
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 2
            ).one().ZP_TV_ENTITY_ID
        except orm.exc.NoResultFound:
            zp_tv_title_id = None
        session.close()
        return zp_tv_title_id

    def get_user_tv_episode_overview_id(self, zp_tv_id, season, episode, zp_user_id):
        session = self.Session()
        zp_tv_title_id = None
        try:
            zp_tv_title_id = session.query(TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF).filter(
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON == season,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE == episode,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == 2
            ).one().ZP_TV_ENTITY_ID
        except orm.exc.NoResultFound:
            zp_tv_title_id = None
        session.close()
        return zp_tv_title_id

    def tv_title_list(self, zp_tv_id, zp_user_id):
        session = self.Session()
        tv_title_dict = {}
        main_default_present = False
        lang_default_present = False
        user_override = False
        id_inc = 1
        try:
            zp_tv_title = session.query(TABLES.ZP_TV_TITLE).filter(
                TABLES.ZP_TV_TITLE.ZP_TV_ID == zp_tv_id).order_by(
                TABLES.ZP_TV_TITLE.ZP_EAPI_ID.asc(), TABLES.ZP_TV_TITLE.ZP_TV_TITLE_TYPE_ID.asc(),
                TABLES.ZP_TV_TITLE.ZP_LANG_ID.desc()
            ).all()
        except orm.exc.NoResultFound:
            tv_title_dict = None
        else:
            for tv_title in zp_tv_title:
                zp_eapi_id = tv_title.ZP_EAPI_ID
                zp_lang_id = tv_title.ZP_LANG_ID
                zp_tv_title_type_id = tv_title.ZP_TV_TITLE_TYPE_ID
                zp_tv_title_id = tv_title.ID
                title = tv_title.TITLE
                main_default = tv_title.MAIN_DEFAULT
                lang_default = tv_title.LANG_DEFAULT
                zp_tv_title_user_id = tv_title.ZP_USER_ID
                if main_default == 1:
                    main_default_present = True
                if lang_default == 1:
                    lang_default_present = True
                if zp_tv_title_user_id == zp_user_id:
                    user_override = True
                if zp_eapi_id not in tv_title_dict:
                    tv_title_dict[zp_eapi_id] = {'titles': []}
                log.debug('zp_tv_title_user_id %s type %s and zp_user_id %s type %s, user_override %s',
                          zp_tv_title_user_id, type(zp_tv_title_user_id), zp_user_id,
                          type(zp_user_id), user_override)
                tv_title_dict[zp_eapi_id]['titles'].append({'zp_tv_title_id': zp_tv_title_id,
                                                            'zp_lang_id': zp_lang_id,
                                                            'zp_tv_title_type_id': zp_tv_title_type_id,
                                                            'title': title,
                                                            'main_default': main_default,
                                                            'lang_default': lang_default,
                                                            'zp_user_id': zp_tv_title_user_id,
                                                            'id_inc': id_inc})
                id_inc += 1
        if main_default_present is False:
            if 0 not in tv_title_dict:
                tv_title_dict[0] = {'titles': []}
            tv_title_dict[0]['titles'].append({'zp_tv_title_id': None,
                                               'zp_lang_id': None,
                                               'zp_tv_title_type_id': None,
                                               'title': '',
                                               'main_default': 1,
                                               'lang_default': None,
                                               'zp_user_id': None,
                                               'id_inc': id_inc})
            id_inc += 1
        if lang_default_present is False:
            if 0 not in tv_title_dict:
                tv_title_dict[0] = {'titles': []}
            tv_title_dict[0]['titles'].append({'zp_tv_title_id': None,
                                               'zp_lang_id': None,
                                               'zp_tv_title_type_id': None,
                                               'title': '',
                                               'main_default': None,
                                               'lang_default': 1,
                                               'zp_user_id': None,
                                               'id_inc': id_inc})
            id_inc += 1
        if user_override is False:
            if 0 not in tv_title_dict:
                tv_title_dict[0] = {'titles': []}
            tv_title_dict[0]['titles'].append({'zp_tv_title_id': None,
                                               'zp_lang_id': None,
                                               'zp_tv_title_type_id': None,
                                               'title': '',
                                               'main_default': None,
                                               'lang_default': None,
                                               'zp_user_id': zp_user_id,
                                               'id_inc': id_inc})
            id_inc += 1
        session.close()
        return tv_title_dict

    def tv_episode_title_list(self, zp_tv_id, season, episode, zp_user_id):
        session = self.Session()
        tv_title_dict = {}
        main_default_present = False
        lang_default_present = False
        user_override = False
        id_inc = 1
        try:
            zp_tv_title = session.query(TABLES.ZP_TV_EPISODE_TITLE).filter(
                TABLES.ZP_TV_EPISODE_TITLE.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_TV_EPISODE_TITLE.SEASON == season,
                TABLES.ZP_TV_EPISODE_TITLE.EPISODE == episode,
            ).order_by(
                TABLES.ZP_TV_EPISODE_TITLE.ZP_EAPI_ID.asc(),
                TABLES.ZP_TV_EPISODE_TITLE.ZP_LANG_ID.desc()
            ).all()
        except orm.exc.NoResultFound:
            tv_title_dict = None
        else:
            for tv_title in zp_tv_title:
                zp_eapi_id = tv_title.ZP_EAPI_ID
                zp_lang_id = tv_title.ZP_LANG_ID
                zp_tv_title_id = tv_title.ID
                title = tv_title.TITLE
                main_default = tv_title.MAIN_DEFAULT
                lang_default = tv_title.LANG_DEFAULT
                zp_tv_title_user_id = tv_title.ZP_USER_ID
                if main_default == 1:
                    main_default_present = True
                if lang_default == 1:
                    lang_default_present = True
                if zp_tv_title_user_id == zp_user_id:
                    user_override = True
                if zp_eapi_id not in tv_title_dict:
                    tv_title_dict[zp_eapi_id] = {'titles': []}
                log.debug('zp_tv_title_user_id %s type %s and zp_user_id %s type %s, user_override %s',
                          zp_tv_title_user_id, type(zp_tv_title_user_id), zp_user_id,
                          type(zp_user_id), user_override)
                tv_title_dict[zp_eapi_id]['titles'].append({'zp_tv_title_id': zp_tv_title_id,
                                                            'zp_lang_id': zp_lang_id,
                                                            'title': title,
                                                            'main_default': main_default,
                                                            'lang_default': lang_default,
                                                            'zp_user_id': zp_tv_title_user_id,
                                                            'id_inc': id_inc})
                id_inc += 1
        if main_default_present is False:
            if 0 not in tv_title_dict:
                tv_title_dict[0] = {'titles': []}
            tv_title_dict[0]['titles'].append({'zp_tv_title_id': None,
                                               'zp_lang_id': None,
                                               'title': '',
                                               'main_default': 1,
                                               'lang_default': None,
                                               'zp_user_id': None,
                                               'id_inc': id_inc})
            id_inc += 1
        if lang_default_present is False:
            if 0 not in tv_title_dict:
                tv_title_dict[0] = {'titles': []}
            tv_title_dict[0]['titles'].append({'zp_tv_title_id': None,
                                               'zp_lang_id': None,
                                               'title': '',
                                               'main_default': None,
                                               'lang_default': 1,
                                               'zp_user_id': None,
                                               'id_inc': id_inc})
            id_inc += 1
        if user_override is False:
            if 0 not in tv_title_dict:
                tv_title_dict[0] = {'titles': []}
            tv_title_dict[0]['titles'].append({'zp_tv_title_id': None,
                                               'zp_lang_id': None,
                                               'title': '',
                                               'main_default': None,
                                               'lang_default': None,
                                               'zp_user_id': zp_user_id,
                                               'id_inc': id_inc})
            id_inc += 1
        session.close()
        return tv_title_dict

    def tv_overview_list(self, zp_tv_id, zp_user_id):
        session = self.Session()
        tv_overview_text = None
        tv_overview_dict = {}
        main_default_present = False
        lang_default_present = False
        user_override = False
        id_inc = 1
        try:
            zp_tv_overview = session.query(TABLES.ZP_TV_OVERVIEW).filter(
                TABLES.ZP_TV_OVERVIEW.ZP_TV_ID == zp_tv_id).order_by(
                TABLES.ZP_TV_OVERVIEW.ZP_EAPI_ID.asc(),
                TABLES.ZP_TV_OVERVIEW.ZP_LANG_ID.desc()
            ).all()
        except orm.exc.NoResultFound:
            tv_overview_dict = None
        else:
            for tv_overview in zp_tv_overview:
                zp_eapi_id = tv_overview.ZP_EAPI_ID
                zp_lang_id = tv_overview.ZP_LANG_ID
                zp_tv_overview_id = tv_overview.ID
                overview = tv_overview.OVERVIEW
                main_default = tv_overview.MAIN_DEFAULT
                lang_default = tv_overview.LANG_DEFAULT
                zp_tv_overview_user_id = tv_overview.ZP_USER_ID
                if main_default == 1:
                    main_default_present = True
                if lang_default == 1:
                    lang_default_present = True
                if zp_tv_overview_user_id == zp_user_id:
                    user_override = True
                if zp_eapi_id not in tv_overview_dict:
                    tv_overview_dict[zp_eapi_id] = {'overviews': []}
                log.debug('zp_tv_overview_user_id %s type %s and zp_user_id %s type %s, user_override %s',
                          zp_tv_overview_user_id, type(zp_tv_overview_user_id), zp_user_id,
                          type(zp_user_id), user_override)
                tv_overview_dict[zp_eapi_id]['overviews'].append({'zp_tv_overview_id': zp_tv_overview_id,
                                                                  'zp_lang_id': zp_lang_id,
                                                                  'overview': overview,
                                                                  'main_default': main_default,
                                                                  'lang_default': lang_default,
                                                                  'zp_user_id': zp_tv_overview_user_id,
                                                                  'id_inc': id_inc})
                id_inc += 1
                if tv_overview_text is None:
                    tv_overview_text = overview
        if main_default_present is False:
            if 0 not in tv_overview_dict:
                tv_overview_dict[0] = {'overviews': []}
            tv_overview_dict[0]['overviews'].append({'zp_tv_overview_id': None,
                                                     'zp_lang_id': None,
                                                     'overview': '',
                                                     'main_default': 1,
                                                     'lang_default': None,
                                                     'zp_user_id': None,
                                                     'id_inc': id_inc})
            id_inc += 1
        if lang_default_present is False:
            if 0 not in tv_overview_dict:
                tv_overview_dict[0] = {'overviews': []}
            tv_overview_dict[0]['overviews'].append({'zp_tv_overview_id': None,
                                                     'zp_lang_id': None,
                                                     'overview': '',
                                                     'main_default': None,
                                                     'lang_default': 1,
                                                     'zp_user_id': None,
                                                     'id_inc': id_inc})
            id_inc += 1
        if user_override is False:
            if 0 not in tv_overview_dict:
                tv_overview_dict[0] = {'overviews': []}
            tv_overview_dict[0]['overviews'].append({'zp_tv_overview_id': None,
                                                     'zp_lang_id': None,
                                                     'overview': '',
                                                     'main_default': None,
                                                     'lang_default': None,
                                                     'zp_user_id': zp_user_id,
                                                     'id_inc': id_inc})
            id_inc += 1
        session.close()
        return tv_overview_dict

    def tv_episode_overview_list(self, zp_tv_id, season, episode, zp_user_id):
        session = self.Session()
        tv_overview_text = None
        tv_overview_dict = {}
        main_default_present = False
        lang_default_present = False
        user_override = False
        id_inc = 1
        try:
            zp_tv_overview = session.query(TABLES.ZP_TV_EPISODE_OVERVIEW).filter(
                TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_TV_EPISODE_OVERVIEW.SEASON == season,
                TABLES.ZP_TV_EPISODE_OVERVIEW.EPISODE == episode).order_by(
                TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_EAPI_ID.asc(),
                TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_LANG_ID.desc()
            ).all()
        except orm.exc.NoResultFound:
            tv_overview_dict = None
        else:
            for tv_overview in zp_tv_overview:
                zp_eapi_id = tv_overview.ZP_EAPI_ID
                zp_lang_id = tv_overview.ZP_LANG_ID
                zp_tv_overview_id = tv_overview.ID
                overview = tv_overview.OVERVIEW
                main_default = tv_overview.MAIN_DEFAULT
                lang_default = tv_overview.LANG_DEFAULT
                zp_tv_overview_user_id = tv_overview.ZP_USER_ID
                if main_default == 1:
                    main_default_present = True
                if lang_default == 1:
                    lang_default_present = True
                if zp_tv_overview_user_id == zp_user_id:
                    user_override = True
                if zp_eapi_id not in tv_overview_dict:
                    tv_overview_dict[zp_eapi_id] = {'overviews': []}
                log.debug('zp_tv_overview_user_id %s type %s and zp_user_id %s type %s, user_override %s',
                          zp_tv_overview_user_id, type(zp_tv_overview_user_id), zp_user_id,
                          type(zp_user_id), user_override)
                tv_overview_dict[zp_eapi_id]['overviews'].append({'zp_tv_overview_id': zp_tv_overview_id,
                                                                  'zp_lang_id': zp_lang_id,
                                                                  'overview': overview,
                                                                  'main_default': main_default,
                                                                  'lang_default': lang_default,
                                                                  'zp_user_id': zp_tv_overview_user_id,
                                                                  'id_inc': id_inc})
                id_inc += 1
                if tv_overview_text is None:
                    tv_overview_text = overview
        if main_default_present is False:
            if 0 not in tv_overview_dict:
                tv_overview_dict[0] = {'overviews': []}
            tv_overview_dict[0]['overviews'].append({'zp_tv_overview_id': None,
                                                     'zp_lang_id': None,
                                                     'overview': '',
                                                     'main_default': 1,
                                                     'lang_default': None,
                                                     'zp_user_id': None,
                                                     'id_inc': id_inc})
            id_inc += 1
        if lang_default_present is False:
            if 0 not in tv_overview_dict:
                tv_overview_dict[0] = {'overviews': []}
            tv_overview_dict[0]['overviews'].append({'zp_tv_overview_id': None,
                                                     'zp_lang_id': None,
                                                     'overview': '',
                                                     'main_default': None,
                                                     'lang_default': 1,
                                                     'zp_user_id': None,
                                                     'id_inc': id_inc})
            id_inc += 1
        if user_override is False:
            if 0 not in tv_overview_dict:
                tv_overview_dict[0] = {'overviews': []}
            tv_overview_dict[0]['overviews'].append({'zp_tv_overview_id': None,
                                                     'zp_lang_id': None,
                                                     'overview': '',
                                                     'main_default': None,
                                                     'lang_default': None,
                                                     'zp_user_id': zp_user_id,
                                                     'id_inc': id_inc})
            id_inc += 1
        session.close()
        return tv_overview_dict

    def update_tv_overview(self, zp_tv_id, zp_user_id, zp_overview_ident,
                           overview):
        session = self.Session()
        if overview:
            zp_user_lang = self.get_user_lang(zp_user_id)
            overview_ident_regex = r'^(?P<zp_tv_overview_id>\d+|None)_(?P<zp_lang_id>\d+|None)_' \
                                   r'(?P<main_default>\d+|None)_' \
                                   r'(?P<lang_default>\d+|None)_(?P<zp_user_id>\d+|None)$'
            match = re.match(overview_ident_regex, zp_overview_ident)
            if match:
                match_groupdict = match.groupdict()
                zp_tv_overview_id = match_groupdict['zp_tv_overview_id']
                zp_lang_id = match_groupdict['zp_lang_id']
                main_default = match_groupdict['main_default']
                lang_default = match_groupdict['lang_default']
                zp_overview_user_id = match_groupdict['zp_user_id']
                log.debug('zp_overview_ident %s', zp_overview_ident)
                log.debug('zp_tv_overview_id %s, zp_lang_id %s, lang_default %s,'
                          ' main_default %s, zp_user_id %s', zp_tv_overview_id, zp_lang_id,
                          lang_default, main_default, zp_overview_user_id)
                if zp_tv_overview_id.isdigit():
                    zp_tv_overview_id = int(zp_tv_overview_id)
                    if zp_tv_overview_id > 0:
                        try:
                            zp_tv_overview = session.query(TABLES.ZP_TV_OVERVIEW).filter(
                                TABLES.ZP_TV_OVERVIEW.ID == zp_tv_overview_id,
                                TABLES.ZP_TV_OVERVIEW.ZP_TV_ID == zp_tv_id
                            ).one()
                        except orm.exc.NoResultFound:
                            log.error('could not find entry in ZP_TV_OVERVIEW with ID %s and ZP_TV_ID %s',
                                      zp_tv_overview_id, zp_tv_id)
                        else:
                            # todo add more logic here for authorised edits
                            if not (zp_tv_overview.ZP_USER_ID > 0 and
                                        (zp_tv_overview.ZP_USER_ID != int(zp_overview_user_id))):
                                zp_tv_overview.OVERVIEW = overview
                                if commit(session):
                                    update_tv_last_mod(self.Session, zp_tv_id)
                                    self.set_user_zp_tv_entity_xref(zp_user_id, zp_tv_id, 2, zp_tv_overview_id)
                elif zp_tv_overview_id == 'None':
                    zp_tv_overview_id = None
                    if main_default == '1':
                        zp_tv_overview_id = self.add_tv_overview(zp_tv_id, zp_user_lang, 0, 0,
                                                                 0, 1, overview)
                    elif lang_default == '1':
                        zp_tv_overview_id = self.add_tv_overview(zp_tv_id, zp_user_lang, 0, 0,
                                                                 1, 0, overview)
                    elif zp_overview_user_id.isdigit():
                        zp_tv_overview_id = self.add_tv_overview(zp_tv_id, zp_user_lang, 0, zp_user_id,
                                                                 0, 0, overview)
                    if zp_tv_overview_id > 0:
                        log.debug('zp_overview_user_id %s > 0', zp_overview_user_id)
                        self.set_user_zp_tv_entity_xref(zp_user_id, zp_tv_id, 2, zp_tv_overview_id)
                        update_tv_last_mod(self.Session, zp_tv_id)
            else:
                log.error('zp_overview_ident %s failed to match overview_ident_regex %s', zp_overview_ident,
                          overview_ident_regex)
        # todo remove overview by sending empty overview
        session.close()

    def update_tv_episode_overview(self, zp_tv_id, season, episode, zp_user_id, zp_overview_ident,
                                   overview):
        session = self.Session()
        if overview:
            zp_user_lang = self.get_user_lang(zp_user_id)
            overview_ident_regex = r'^(?P<zp_tv_overview_id>\d+|None)_(?P<zp_lang_id>\d+|None)_' \
                                   r'(?P<main_default>\d+|None)_' \
                                   r'(?P<lang_default>\d+|None)_(?P<zp_user_id>\d+|None)$'
            match = re.match(overview_ident_regex, zp_overview_ident)
            if match:
                log.error('zp_overview_ident matches')
                match_groupdict = match.groupdict()
                zp_tv_overview_id = match_groupdict['zp_tv_overview_id']
                zp_lang_id = match_groupdict['zp_lang_id']
                main_default = match_groupdict['main_default']
                lang_default = match_groupdict['lang_default']
                zp_overview_user_id = match_groupdict['zp_user_id']
                log.debug('zp_overview_ident %s', zp_overview_ident)
                log.debug('zp_tv_overview_id %s, zp_lang_id %s, lang_default %s,'
                          ' main_default %s, zp_user_id %s', zp_tv_overview_id, zp_lang_id,
                          lang_default, main_default, zp_overview_user_id)
                if zp_tv_overview_id.isdigit():
                    zp_tv_overview_id = int(zp_tv_overview_id)
                    if zp_tv_overview_id > 0:
                        try:
                            zp_tv_overview = session.query(TABLES.ZP_TV_EPISODE_OVERVIEW).filter(
                                TABLES.ZP_TV_EPISODE_OVERVIEW.ID == zp_tv_overview_id,
                                TABLES.ZP_TV_EPISODE_OVERVIEW.ZP_TV_ID == zp_tv_id,
                                TABLES.ZP_TV_EPISODE_OVERVIEW.SEASON == season,
                                TABLES.ZP_TV_EPISODE_OVERVIEW.EPISODE == episode
                            ).one()
                        except orm.exc.NoResultFound:
                            log.error('could not find entry in ZP_TV_EPISODE_OVERVIEW with ID %s and '
                                      'ZP_TV_ID %s, season %s, episode %s',
                                      zp_tv_overview_id, zp_tv_id, season, episode)
                        else:
                            # todo add more logic here for authorised edits
                            if not (zp_tv_overview.ZP_USER_ID > 0 and
                                        (zp_tv_overview.ZP_USER_ID != int(zp_overview_user_id))):
                                zp_tv_overview.OVERVIEW = overview
                                if commit(session):
                                    update_tv_episode_last_mod(self.Session, zp_tv_id, season, episode)
                                    self.set_user_zp_tv_episode_entity_xref(zp_user_id, zp_tv_id, season,
                                                                            episode, 2, zp_tv_overview_id)
                elif zp_tv_overview_id == 'None':
                    zp_tv_overview_id = None
                    if main_default == '1':
                        zp_tv_overview_id = self.add_tv_episode_overview(zp_tv_id, season, episode,
                                                                         zp_user_lang, 0, 0,
                                                                         0, 1, overview)
                    elif lang_default == '1':
                        zp_tv_overview_id = self.add_tv_episode_overview(zp_tv_id, season, episode,
                                                                         zp_user_lang, 0, 0,
                                                                         1, 0, overview)
                    elif zp_overview_user_id.isdigit():
                        zp_tv_overview_id = self.add_tv_episode_overview(zp_tv_id, season, episode,
                                                                         zp_user_lang, 0, zp_user_id,
                                                                         0, 0, overview)
                    if zp_tv_overview_id > 0:
                        log.debug('zp_overview_user_id %s > 0', zp_overview_user_id)
                        update_tv_episode_last_mod(self.Session, zp_tv_id, season, episode)
                        self.set_user_zp_tv_episode_entity_xref(zp_user_id, zp_tv_id, season,
                                                                episode, 2, zp_tv_overview_id)
            else:
                log.error('zp_overview_ident %s failed to match overview_ident_regex %s', zp_overview_ident,
                          overview_ident_regex)
        # todo remove overview by sending empty overview
        session.close()

    def update_tv_title(self, zp_tv_id, zp_user_id, zp_title_ident,
                        title):
        session = self.Session()
        if title:
            zp_user_lang = self.get_user_lang(zp_user_id)
            title_ident_regex = r'^(?P<zp_tv_title_id>\d+|None)_(?P<zp_lang_id>\d+|None)_' \
                                r'(?P<zp_tv_title_type_id>\d+|None)_(?P<main_default>\d+|None)_' \
                                r'(?P<lang_default>\d+|None)_(?P<zp_user_id>\d+|None)$'
            match = re.match(title_ident_regex, zp_title_ident)
            if match:
                match_groupdict = match.groupdict()
                zp_tv_title_id = match_groupdict['zp_tv_title_id']
                zp_lang_id = match_groupdict['zp_lang_id']
                zp_tv_title_type_id = match_groupdict['zp_tv_title_type_id']
                main_default = match_groupdict['main_default']
                lang_default = match_groupdict['lang_default']
                zp_title_user_id = match_groupdict['zp_user_id']
                log.debug('zp_title_ident %s', zp_title_ident)
                log.debug('zp_tv_title_id %s, zp_lang_id %s, zp_tv_title_type_id %s, lang_default %s,'
                          ' main_default %s, zp_user_id %s', zp_tv_title_id, zp_lang_id,
                          zp_tv_title_type_id, lang_default, main_default, zp_title_user_id)
                if zp_tv_title_id.isdigit():
                    zp_tv_title_id = int(zp_tv_title_id)
                    if zp_tv_title_id > 0:
                        try:
                            zp_tv_title = session.query(TABLES.ZP_TV_TITLE).filter(
                                TABLES.ZP_TV_TITLE.ID == zp_tv_title_id,
                                TABLES.ZP_TV_TITLE.ZP_TV_ID == zp_tv_id
                            ).one()
                        except orm.exc.NoResultFound:
                            log.error('could not find entry in ZP_TV_TITLE with ID %s and ZP_TV_ID %s',
                                      zp_tv_title_id, zp_tv_id)
                        else:
                            # todo add more logic here for authorised edits
                            if not (zp_tv_title.ZP_USER_ID > 0 and
                                        (zp_tv_title.ZP_USER_ID != int(zp_title_user_id))):
                                zp_tv_title.TITLE = title
                                if commit(session):
                                    update_tv_last_mod(self.Session, zp_tv_id)
                                    self.set_user_zp_tv_entity_xref(zp_user_id, zp_tv_id, 1, zp_tv_title_id)
                elif zp_tv_title_id == 'None':
                    zp_tv_title_id = None
                    if main_default == '1':
                        zp_tv_title_id = self.add_tv_title(zp_tv_id, 1, zp_user_lang, 0, 0,
                                                           0, 1, title)
                    elif lang_default == '1':
                        zp_tv_title_id = self.add_tv_title(zp_tv_id, 1, zp_user_lang, 0, 0,
                                                           1, 0, title)
                    elif zp_title_user_id.isdigit():
                        zp_tv_title_id = self.add_tv_title(zp_tv_id, 1, zp_user_lang, 0, zp_user_id,
                                                           0, 0, title)
                    if zp_tv_title_id > 0:
                        log.debug('zp_title_user_id %s is digit', zp_title_user_id)
                        self.set_user_zp_tv_entity_xref(zp_user_id, zp_tv_id, 1, zp_tv_title_id)
                        update_tv_last_mod(self.Session, zp_tv_id)
            else:
                log.error('zp_title_ident %s failed to match title_ident_regex %s', zp_title_ident,
                          title_ident_regex)
        # todo remove title by sending empty title
        session.close()

    def update_tv_episode_title(self, zp_tv_id, season, episode, zp_user_id, zp_title_ident,
                                title):
        session = self.Session()
        log.error(locals())
        if title:
            zp_user_lang = self.get_user_lang(zp_user_id)
            title_ident_regex = r'^(?P<zp_tv_title_id>\d+|None)_(?P<zp_lang_id>\d+|None)_' \
                                r'(?P<main_default>\d+|None)_' \
                                r'(?P<lang_default>\d+|None)_(?P<zp_user_id>\d+|None)$'
            match = re.match(title_ident_regex, zp_title_ident)
            if match:
                log.error('zp_title_ident matches')
                match_groupdict = match.groupdict()
                zp_tv_title_id = match_groupdict['zp_tv_title_id']
                zp_lang_id = match_groupdict['zp_lang_id']
                main_default = match_groupdict['main_default']
                lang_default = match_groupdict['lang_default']
                zp_title_user_id = match_groupdict['zp_user_id']
                log.debug('zp_title_ident %s', zp_title_ident)
                log.debug('zp_tv_title_id %s, zp_lang_id %s, lang_default %s,'
                          ' main_default %s, zp_user_id %s', zp_tv_title_id, zp_lang_id,
                          lang_default, main_default, zp_title_user_id)
                if zp_tv_title_id.isdigit():
                    zp_tv_title_id = int(zp_tv_title_id)
                    if zp_tv_title_id > 0:
                        try:
                            zp_tv_title = session.query(TABLES.ZP_TV_EPISODE_TITLE).filter(
                                TABLES.ZP_TV_EPISODE_TITLE.ID == zp_tv_title_id,
                                TABLES.ZP_TV_EPISODE_TITLE.ZP_TV_ID == zp_tv_id,
                                TABLES.ZP_TV_EPISODE_TITLE.SEASON == season,
                                TABLES.ZP_TV_EPISODE_TITLE.EPISODE == episode
                            ).one()
                        except orm.exc.NoResultFound:
                            log.error('could not find entry in ZP_TV_EPISODE_TITLE with ID %s and'
                                      ' ZP_TV_ID %s, season %s, episode %s',
                                      zp_tv_title_id, zp_tv_id, season, episode)
                        else:
                            # todo add more logic here for authorised edits
                            if not (zp_tv_title.ZP_USER_ID > 0 and
                                        (zp_tv_title.ZP_USER_ID != int(zp_title_user_id))):
                                zp_tv_title.TITLE = title
                                if commit(session):
                                    update_tv_episode_last_mod(self.Session, zp_tv_id, season, episode)
                                    self.set_user_zp_tv_episode_entity_xref(zp_user_id, zp_tv_id, season,
                                                                            episode, 1, zp_tv_title_id)
                elif zp_tv_title_id == 'None':
                    zp_tv_title_id = None
                    if main_default == '1':
                        zp_tv_title_id = self.add_tv_episode_title(zp_tv_id, season, episode,
                                                                   zp_user_lang, 0, 0,
                                                                   0, 1, title)
                    elif lang_default == '1':
                        zp_tv_title_id = self.add_tv_episode_title(zp_tv_id, season, episode,
                                                                   zp_user_lang, 0, 0,
                                                                   1, 0, title)
                    elif zp_title_user_id.isdigit():
                        zp_tv_title_id = self.add_tv_episode_title(zp_tv_id, season, episode,
                                                                   zp_user_lang, 0, zp_user_id,
                                                                   0, 0, title)
                    if zp_tv_title_id > 0:
                        self.set_user_zp_tv_episode_entity_xref(zp_user_id, zp_tv_id, season,
                                                                episode, 1, zp_tv_title_id)
                        update_tv_episode_last_mod(self.Session, zp_tv_id, season, episode)
                        log.debug('zp_title_user_id %s is digit', zp_title_user_id)
            else:
                log.error('zp_title_ident %s failed to match title_ident_regex %s', zp_title_ident,
                          title_ident_regex)
        # todo remove title by sending empty title
        session.close()

    def add_tv_title(self, zp_tv_id, zp_tv_title_type_id, zp_lang_id, zp_eapi_id, zp_user_id,
                     lang_default, main_default, title):
        session = self.Session()
        zp_tv_title_id = None
        add_zp_tv_title = TABLES.ZP_TV_TITLE(ZP_TV_ID=zp_tv_id,
                                             ZP_TV_TITLE_TYPE_ID=zp_tv_title_type_id,
                                             ZP_LANG_ID=zp_lang_id,
                                             ZP_EAPI_ID=zp_eapi_id,
                                             ZP_USER_ID=zp_user_id,
                                             LANG_DEFAULT=lang_default,
                                             MAIN_DEFAULT=main_default,
                                             TITLE=title)
        session.add(add_zp_tv_title)
        if commit(session):
            zp_tv_title_id = add_zp_tv_title.ID
        session.close()
        return zp_tv_title_id

    def add_tv_episode_title(self, zp_tv_id, season, episode, zp_lang_id, zp_eapi_id, zp_user_id,
                             lang_default, main_default, title):
        session = self.Session()
        zp_tv_title_id = None
        add_zp_tv_title = TABLES.ZP_TV_EPISODE_TITLE(ZP_TV_ID=zp_tv_id,
                                                     SEASON=season,
                                                     EPISODE=episode,
                                                     ZP_LANG_ID=zp_lang_id,
                                                     ZP_EAPI_ID=zp_eapi_id,
                                                     ZP_USER_ID=zp_user_id,
                                                     LANG_DEFAULT=lang_default,
                                                     MAIN_DEFAULT=main_default,
                                                     TITLE=title)
        session.add(add_zp_tv_title)
        if commit(session):
            zp_tv_title_id = add_zp_tv_title.ID
        session.close()
        return zp_tv_title_id

    def add_tv_overview(self, zp_tv_id, zp_lang_id, zp_eapi_id, zp_user_id,
                        lang_default, main_default, overview):
        session = self.Session()
        zp_tv_overview_id = None
        add_zp_tv_overview = TABLES.ZP_TV_OVERVIEW(ZP_TV_ID=zp_tv_id,
                                                   ZP_LANG_ID=zp_lang_id,
                                                   ZP_EAPI_ID=zp_eapi_id,
                                                   ZP_USER_ID=zp_user_id,
                                                   LANG_DEFAULT=lang_default,
                                                   MAIN_DEFAULT=main_default,
                                                   OVERVIEW=overview)
        session.add(add_zp_tv_overview)
        if commit(session):
            zp_tv_overview_id = add_zp_tv_overview.ID
        session.close()
        return zp_tv_overview_id

    def add_tv_episode_overview(self, zp_tv_id, season, episode, zp_lang_id, zp_eapi_id, zp_user_id,
                                lang_default, main_default, overview):
        session = self.Session()
        zp_tv_overview_id = None
        add_zp_tv_overview = TABLES.ZP_TV_EPISODE_OVERVIEW(ZP_TV_ID=zp_tv_id,
                                                           SEASON=season,
                                                           EPISODE=episode,
                                                           ZP_LANG_ID=zp_lang_id,
                                                           ZP_EAPI_ID=zp_eapi_id,
                                                           ZP_USER_ID=zp_user_id,
                                                           LANG_DEFAULT=lang_default,
                                                           MAIN_DEFAULT=main_default,
                                                           OVERVIEW=overview)
        session.add(add_zp_tv_overview)
        if commit(session):
            zp_tv_overview_id = add_zp_tv_overview.ID
        session.close()
        return zp_tv_overview_id

    def set_user_tv_raw_image(self, zp_tv_id, image_type, zp_tv_raw_image_id, zp_user_id):
        success = False
        session = self.Session()
        try:
            session.query(TABLES.ZP_TV_RAW_IMAGE).filter(
                TABLES.ZP_TV_RAW_IMAGE.ZP_ENTITY_ID == zp_tv_id,
                TABLES.ZP_TV_RAW_IMAGE.ZP_ENTITY_TYPE_ID == self.image_type_id_dict[image_type],
                TABLES.ZP_TV_RAW_IMAGE.ID == zp_tv_raw_image_id
            ).one()
        except orm.exc.NoResultFound:
            log.error('could not find entry in ZP_TV_RAW_IMAGE for ZP_ENTITY_ID %s,'
                      'ZP_ENTITY_TYPE_ID %s, ID %s', zp_tv_id, self.image_type_id_dict[image_type],
                      zp_tv_raw_image_id)
        else:
            try:
                zp_user_tv_entity_xref = session.query(TABLES.ZP_USER_TV_ENTITY_XREF).filter(
                    TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                    TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == zp_tv_id,
                    TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == self.image_tv_entity_type_id_dict[
                        image_type]
                ).one()
            except orm.exc.NoResultFound:
                add_zp_user_tv_entity_xref = TABLES.ZP_USER_TV_ENTITY_XREF(
                    ZP_USER_ID=zp_user_id,
                    ZP_TV_ID=zp_tv_id,
                    ZP_TV_ENTITY_TYPE_ID=self.image_tv_entity_type_id_dict[image_type],
                    ZP_TV_ENTITY_ID=zp_tv_raw_image_id,
                    FORCED=1,
                    LAST_UPDATE_DATETIME=date_time()
                )
                session.add(add_zp_user_tv_entity_xref)
                if commit(session):
                    update_tv_last_mod(self.Session, zp_tv_id)
                    success = True
            else:
                zp_user_tv_entity_xref.FORCED = 1
                zp_user_tv_entity_xref.ZP_TV_ENTITY_ID = zp_tv_raw_image_id
                zp_user_tv_entity_xref.LAST_UPDATE_DATETIME = date_time()
                if commit(session):
                    update_tv_last_mod(self.Session, zp_tv_id)
                    success = True
        session.close()
        return success

    def set_user_tv_season_raw_image(self, zp_tv_id, season, image_type, zp_tv_raw_image_id, zp_user_id):
        success = False
        session = self.Session()
        try:
            session.query(TABLES.ZP_TV_SEASON_RAW_IMAGE).filter(
                TABLES.ZP_TV_SEASON_RAW_IMAGE.ZP_ENTITY_ID == zp_tv_id,
                TABLES.ZP_TV_SEASON_RAW_IMAGE.SEASON == season,
                TABLES.ZP_TV_SEASON_RAW_IMAGE.ZP_ENTITY_TYPE_ID == self.image_tv_season_entity_type_id_dict[image_type],
                TABLES.ZP_TV_SEASON_RAW_IMAGE.ID == zp_tv_raw_image_id
            ).one()
        except orm.exc.NoResultFound:
            log.error('could not find entry in ZP_TV_RAW_IMAGE for ZP_ENTITY_ID %s, season %s,'
                      ' ZP_ENTITY_TYPE_ID %s, ID %s', zp_tv_id, season,
                      self.image_tv_season_entity_type_id_dict[image_type],
                      zp_tv_raw_image_id)
        else:
            try:
                zp_user_tv_entity_xref = session.query(TABLES.ZP_USER_TV_SEASON_ENTITY_XREF).filter(
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_TV_ID == zp_tv_id,
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.SEASON == season,
                    TABLES.ZP_USER_TV_SEASON_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID ==
                    self.image_tv_season_entity_type_id_dict[
                        image_type]
                ).one()
            except orm.exc.NoResultFound:
                add_zp_user_tv_entity_xref = TABLES.ZP_USER_TV_SEASON_ENTITY_XREF(
                    ZP_USER_ID=zp_user_id,
                    ZP_TV_ID=zp_tv_id,
                    SEASON=season,
                    ZP_TV_ENTITY_TYPE_ID=self.image_tv_season_entity_type_id_dict[image_type],
                    ZP_TV_ENTITY_ID=zp_tv_raw_image_id,
                    FORCED=1,
                    LAST_UPDATE_DATETIME=date_time()
                )
                session.add(add_zp_user_tv_entity_xref)
                if commit(session):
                    update_tv_last_mod(self.Session, zp_tv_id)
                    success = True
            else:
                zp_user_tv_entity_xref.FORCED = 1
                zp_user_tv_entity_xref.ZP_TV_ENTITY_ID = zp_tv_raw_image_id
                zp_user_tv_entity_xref.LAST_UPDATE_DATETIME = date_time()
                if commit(session):
                    update_tv_last_mod(self.Session, zp_tv_id)
                    success = True
        session.close()
        return success

    def set_user_tv_episode_raw_image(self, zp_tv_id, season, episode, image_type, zp_tv_raw_image_id, zp_user_id):
        success = False
        session = self.Session()
        try:
            session.query(TABLES.ZP_TV_EPISODE_RAW_IMAGE).filter(
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID == zp_tv_id,
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.SEASON == season,
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.EPISODE == episode,
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID == self.image_tv_episode_entity_type_id_dict[
                    image_type],
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ID == zp_tv_raw_image_id
            ).one()
        except orm.exc.NoResultFound:
            log.error('could not find entry in ZP_TV_EPISODE_RAW_IMAGE for ZP_ENTITY_ID %s, season %s, episode %s,'
                      ' ZP_ENTITY_TYPE_ID %s, ID %s', zp_tv_id, season, episode,
                      self.image_tv_episode_entity_type_id_dict[image_type],
                      zp_tv_raw_image_id)
        else:
            try:
                zp_user_tv_entity_xref = session.query(TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF).filter(
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID == zp_tv_id,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON == season,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE == episode,
                    TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID ==
                    self.image_tv_episode_user_entity_type_id_dict[image_type]
                ).one()
            except orm.exc.NoResultFound:
                add_zp_user_tv_entity_xref = TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF(
                    ZP_USER_ID=zp_user_id,
                    ZP_TV_ID=zp_tv_id,
                    SEASON=season,
                    EPISODE=episode,
                    ZP_TV_ENTITY_TYPE_ID=self.image_tv_episode_user_entity_type_id_dict[image_type],
                    ZP_TV_ENTITY_ID=zp_tv_raw_image_id,
                    FORCED=1,
                    LAST_UPDATE_DATETIME=date_time()
                )
                session.add(add_zp_user_tv_entity_xref)
                if commit(session):
                    update_tv_last_mod(self.Session, zp_tv_id)
                    success = True
            else:
                zp_user_tv_entity_xref.FORCED = 1
                zp_user_tv_entity_xref.ZP_TV_ENTITY_ID = zp_tv_raw_image_id
                zp_user_tv_entity_xref.LAST_UPDATE_DATETIME = date_time()
                if commit(session):
                    update_tv_last_mod(self.Session, zp_tv_id)
                    success = True
        session.close()
        return success

    def set_user_zp_tv_entity_xref(self, zp_user_id, zp_tv_id, zp_tv_entity_type_id, zp_tv_entity_id):
        session = self.Session()
        try:
            zp_user_tv_entity_xref = session.query(TABLES.ZP_USER_TV_ENTITY_XREF).filter(
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_USER_TV_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == zp_tv_entity_type_id
            ).one()
        except orm.exc.NoResultFound:
            log.error('there should allready be a entry here unless a tv and been added'
                      ' but not yet gone through data and user specifics')
            add_zp_user_tv_entity_xref = TABLES.ZP_USER_TV_ENTITY_XREF(ZP_USER_ID=zp_user_id,
                                                                       ZP_TV_ID=zp_tv_id,
                                                                       ZP_TV_ENTITY_TYPE_ID=zp_tv_entity_type_id,
                                                                       ZP_TV_ENTITY_ID=zp_tv_entity_id,
                                                                       FORCED=1,
                                                                       LAST_UPDATE_DATETIME=date_time())
            session.add(add_zp_user_tv_entity_xref)
            commit(session)
        else:
            zp_user_tv_entity_xref.ZP_TV_ENTITY_ID = zp_tv_entity_id
            zp_user_tv_entity_xref.FORCED = 1
            zp_user_tv_entity_xref.LAST_UPDATE_DATETIME = date_time()
            commit(session)
        session.close()

    def set_user_zp_tv_episode_entity_xref(self, zp_user_id, zp_tv_id, season, episode,
                                           zp_tv_entity_type_id, zp_tv_entity_id):
        log.error(locals())
        session = self.Session()
        try:
            zp_user_tv_entity_xref = session.query(TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF).filter(
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_USER_ID == zp_user_id,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ID == zp_tv_id,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.SEASON == season,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.EPISODE == episode,
                TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF.ZP_TV_ENTITY_TYPE_ID == zp_tv_entity_type_id
            ).one()
        except orm.exc.NoResultFound:
            log.error('there should allready be a entry here unless a tv and been added'
                      ' but not yet gone through data and user specifics')
            add_zp_user_tv_entity_xref = TABLES.ZP_USER_TV_EPISODE_ENTITY_XREF(ZP_USER_ID=zp_user_id,
                                                                               ZP_TV_ID=zp_tv_id,
                                                                               SEASON=season,
                                                                               EPISODE=episode,
                                                                               ZP_TV_ENTITY_TYPE_ID=zp_tv_entity_type_id,
                                                                               ZP_TV_ENTITY_ID=zp_tv_entity_id,
                                                                               FORCED=1,
                                                                               LAST_UPDATE_DATETIME=date_time())
            session.add(add_zp_user_tv_entity_xref)
            commit(session)
        else:
            zp_user_tv_entity_xref.ZP_TV_ENTITY_ID = zp_tv_entity_id
            zp_user_tv_entity_xref.FORCED = 1
            zp_user_tv_entity_xref.LAST_UPDATE_DATETIME = date_time()
            commit(session)
        session.close()

    def genre_by_name(self):
        session = self.Session
        genre_dict = {}
        genres = session.query(TABLES.ZP_GENRE).all()
        session.close()
        for genre in genres:
            genre_dict[genre.GENRE] = genre.ID
        return genre_dict

    def genre_by_id(self):
        session = self.Session
        genre_dict = {}
        genres = session.query(TABLES.ZP_GENRE).all()
        session.close()
        for genre in genres:
            genre_dict[genre.ID] = genre.GENRE
        return genre_dict

    def get_user_lang(self, zp_user_id):
        session = self.Session()
        zp_lang_id = session.query(TABLES.ZP_USER_LIBRARY_LANG).filter(
            TABLES.ZP_USER_LIBRARY_LANG.ZP_USER_ID == zp_user_id,
            TABLES.ZP_USER_LIBRARY_LANG.ZP_LIBRARY_ID == 1
        ).one().ZP_LANG_ID
        session.close()
        return zp_lang_id

    def clear_genres(self, zp_tv_id):
        session = self.Session()
        session.query(TABLES.ZP_TV_GENRE_XREF).filter(
            TABLES.ZP_TV_GENRE_XREF.ZP_TV_ID == zp_tv_id).delete()
        commit(session)
        session.close()
        return True

    def add_genre(self, zp_tv_id, genre):
        session = self.Session()
        add_ZP_TV_GENRE_XREF = TABLES.ZP_TV_GENRE_XREF(ZP_TV_ID=zp_tv_id,
                                                       ZP_GENRE_ID=genre)
        session.add(add_ZP_TV_GENRE_XREF)
        commit(session)
        update_tv_last_mod(self.Session, zp_tv_id)
        session.close()
        return True

    def get_actors(self, name):
        session = self.Session()
        actor_list = []
        subq = session.query(TABLES.ZP_TV_ROLE_XREF.ZP_PEOPLE_ID,
                             case([(func.count(TABLES.ZP_TV_ROLE_XREF.ZP_PEOPLE_ID) == None, 0)],
                                  else_=func.count(TABLES.ZP_TV_ROLE_XREF.ZP_PEOPLE_ID)).label('pcount')).group_by(
            TABLES.ZP_TV_ROLE_XREF.ZP_PEOPLE_ID).subquery()
        actors = session.query(TABLES.ZP_PEOPLE.NAME, TABLES.ZP_PEOPLE.ID, subq.c.pcount).outerjoin(
            subq, subq.c.ZP_PEOPLE_ID == TABLES.ZP_PEOPLE.ID).filter(
            TABLES.ZP_PEOPLE.NAME.like('%%%s%%' % name)
        ).order_by(subq.c.pcount.desc()).limit(50)
        session.close()
        for actor in actors:
            actor_list.append({'id': actor.ID,
                               'name': actor.NAME})
        return actor_list

    def clear_cast(self, zp_tv_id):
        session = self.Session()
        session.query(TABLES.ZP_TV_ROLE_XREF).filter(
            TABLES.ZP_TV_ROLE_XREF.ZP_TV_ID == zp_tv_id,
            TABLES.ZP_TV_ROLE_XREF.ZP_ROLE_ID == 1).delete()
        commit(session)
        session.close()
        return True

    def add_cast(self, zp_tv_id, people_id):
        # todo check is not allready assigned to tv
        session = self.Session()
        add_ZP_TV_ROLE_XREF = TABLES.ZP_TV_ROLE_XREF(ZP_TV_ID=zp_tv_id,
                                                     ZP_ROLE_ID=1,
                                                     ZP_PEOPLE_ID=people_id)
        session.add(add_ZP_TV_ROLE_XREF)
        commit(session)
        update_tv_last_mod(self.Session, zp_tv_id)
        session.close()
        return True

    def add_new_tv_raw_image(self, zp_tv_id, zp_user_id, zp_entity_type_id, new_tv_image_filename,
                             image_reference):
        session = self.Session()
        add_zp_tv_raw_image = TABLES.ZP_TV_RAW_IMAGE(ZP_EAPI_ID=0,
                                                       ZP_EAPI_IMAGE_REF=image_reference,
                                                       ZP_ENTITY_TYPE_ID=zp_entity_type_id,
                                                       ZP_ENTITY_ID=zp_tv_id,
                                                       ZP_USER_ID=zp_user_id,
                                                       FILENAME=new_tv_image_filename)
        session.add(add_zp_tv_raw_image)
        commit(session)
        session.close()
        return True

    def add_new_tv_season_raw_image(self, zp_tv_id, season, zp_user_id, zp_entity_type_id, new_tv_image_filename,
                                    image_reference):
        session = self.Session()
        add_zp_tv_raw_image = TABLES.ZP_TV_SEASON_RAW_IMAGE(ZP_EAPI_ID=0,
                                                              ZP_EAPI_IMAGE_REF=image_reference,
                                                              ZP_ENTITY_TYPE_ID=zp_entity_type_id,
                                                              ZP_ENTITY_ID=zp_tv_id,
                                                              SEASON=season,
                                                              ZP_USER_ID=zp_user_id,
                                                              FILENAME=new_tv_image_filename)
        session.add(add_zp_tv_raw_image)
        commit(session)
        session.close()
        return True

    def add_new_tv_episode_raw_image(self, zp_tv_id, season, episode,
                                     zp_user_id, zp_entity_type_id, new_tv_image_filename,
                                     image_reference):
        session = self.Session()
        add_zp_tv_raw_image = TABLES.ZP_TV_EPISODE_RAW_IMAGE(ZP_EAPI_ID=0,
                                                               ZP_EAPI_IMAGE_REF=image_reference,
                                                               ZP_ENTITY_TYPE_ID=zp_entity_type_id,
                                                               ZP_ENTITY_ID=zp_tv_id,
                                                               SEASON=season,
                                                               EPISODE=episode,
                                                               ZP_USER_ID=zp_user_id,
                                                               FILENAME=new_tv_image_filename)
        session.add(add_zp_tv_raw_image)
        commit(session)
        session.close()
        return True

    def tv_raw_image_list(self, zp_tv_id, image_type_id):
        session = self.Session()
        raw_image_list = []
        try:
            raw_images = session.query(TABLES.ZP_TV_RAW_IMAGE).filter(
                TABLES.ZP_TV_RAW_IMAGE.ZP_ENTITY_ID == zp_tv_id,
                TABLES.ZP_TV_RAW_IMAGE.ZP_ENTITY_TYPE_ID == image_type_id
            ).order_by(TABLES.ZP_TV_RAW_IMAGE.ZP_EAPI_ID.asc(),
                       TABLES.ZP_TV_RAW_IMAGE.ZP_USER_ID.asc()).all()
        except orm.exc.NoResultFound:
            log.debug('no images for zp_tv_id %s, image_type_id %s found in ZP_TV_RAW_IMAGE',
                      zp_tv_id, image_type_id)
        else:
            for raw_image in raw_images:
                raw_image_list.append({'image_url': '/i/raw/tv/%s' % (raw_image.ID),
                                       'source_type': 'eapi' if raw_image.ZP_EAPI_ID > 0 else 'user',
                                       'zp_eapi_id': raw_image.ZP_EAPI_ID,
                                       'zp_tv_raw_image_id': raw_image.ID})
        log.debug(raw_image_list)
        session.close()
        return raw_image_list

    def tv_season_raw_image_list(self, zp_tv_id, season, image_type_id):
        session = self.Session()
        raw_image_list = []
        try:
            raw_images = session.query(TABLES.ZP_TV_SEASON_RAW_IMAGE).filter(
                TABLES.ZP_TV_SEASON_RAW_IMAGE.ZP_ENTITY_ID == zp_tv_id,
                TABLES.ZP_TV_SEASON_RAW_IMAGE.ZP_ENTITY_TYPE_ID == image_type_id,
                TABLES.ZP_TV_SEASON_RAW_IMAGE.SEASON == season
            ).order_by(TABLES.ZP_TV_SEASON_RAW_IMAGE.ZP_EAPI_ID.asc(),
                       TABLES.ZP_TV_SEASON_RAW_IMAGE.ZP_USER_ID.asc()).all()
        except orm.exc.NoResultFound:
            log.debug('no images for zp_tv_id %s, seaspn %s, image_type_id %s found in ZP_TV_RAW_IMAGE',
                      zp_tv_id, season, image_type_id)
        else:
            for raw_image in raw_images:
                raw_image_list.append({'image_url': '/i/raw/tv/season/%s' % (raw_image.ID),
                                       'source_type': 'eapi' if raw_image.ZP_EAPI_ID > 0 else 'user',
                                       'zp_eapi_id': raw_image.ZP_EAPI_ID,
                                       'zp_tv_raw_image_id': raw_image.ID})
        log.debug(raw_image_list)
        session.close()
        return raw_image_list

    def tv_episode_raw_image_list(self, zp_tv_id, season, episode, image_type_id):
        session = self.Session()
        raw_image_list = []
        try:
            raw_images = session.query(TABLES.ZP_TV_EPISODE_RAW_IMAGE).filter(
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_ID == zp_tv_id,
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_ENTITY_TYPE_ID == image_type_id,
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.SEASON == season,
                TABLES.ZP_TV_EPISODE_RAW_IMAGE.EPISODE == episode
            ).order_by(TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_EAPI_ID.asc(),
                       TABLES.ZP_TV_EPISODE_RAW_IMAGE.ZP_USER_ID.asc()).all()
        except orm.exc.NoResultFound:
            log.error('no images for zp_tv_id %s, seaspn %s, episode %s, image_type_id %s found in ZP_TV_RAW_IMAGE',
                      zp_tv_id, season, episode, image_type_id)
        else:
            for raw_image in raw_images:
                raw_image_list.append({'image_url': '/i/raw/tv/episode/%s' % (raw_image.ID),
                                       'source_type': 'eapi' if raw_image.ZP_EAPI_ID > 0 else 'user',
                                       'zp_eapi_id': raw_image.ZP_EAPI_ID,
                                       'zp_tv_raw_image_id': raw_image.ID})
        log.debug(raw_image_list)
        session.close()
        # raise SystemExit
        return raw_image_list

    def tv_season_list(self, zp_tv_id, selected_season=None):
        session = self.Session()
        season_list = []
        # sidebar_season_list = []
        zp_tv_episode = session.query(TABLES.ZP_TV_EPISODE.SEASON.distinct().label('SEASON')).filter(
            TABLES.ZP_TV_EPISODE.ZP_TV_ID == zp_tv_id
        ).order_by(TABLES.ZP_TV_EPISODE.SEASON.asc()).all()
        for season in zp_tv_episode:
            season_list.append(season.SEASON)
        if isinstance(selected_season, int):
            sidebar_season_list = []
            if selected_season in season_list:
                selected_season_index = season_list.index(selected_season)
                if selected_season_index == 0:
                    for season in season_list:
                        if season not in sidebar_season_list:
                            sidebar_season_list.append(season)
                else:
                    list_len = len(season_list)
                    current_list_posiiton = selected_season_index
                    log.debug('season_list %s', season_list)
                    log.debug('list_len %s', list_len)
                    for i in range(current_list_posiiton, list_len):
                        log.debug('A selected_season_index %s, i %s, season_list[i] %s', selected_season_index, i,
                                  season_list[i])
                        sidebar_season_list.append(season_list[i])
                        log.debug('sidebar_season_list %s', sidebar_season_list)
                    for i in range(0, selected_season_index):
                        log.debug('B selected_season_index %s, i %s, season_list[i] %s', selected_season_index, i,
                                  season_list[i])
                        sidebar_season_list.append(season_list[i])
                        log.debug('sidebar_season_list %s', sidebar_season_list)
            else:
                for season in season_list:
                    sidebar_season_list.append(season)
        else:
            sidebar_season_list = season_list
        log.debug('season_list %s', season_list)
        session.close()
        return sidebar_season_list

    def tv_episode_list(self, zp_tv_id, season, selected_episode=None):
        session = self.Session()
        episode_list = []
        zp_tv_episode = session.query(TABLES.ZP_TV_EPISODE).filter(
            TABLES.ZP_TV_EPISODE.ZP_TV_ID == zp_tv_id,
            TABLES.ZP_TV_EPISODE.SEASON == season
        ).order_by(TABLES.ZP_TV_EPISODE.EPISODE.asc()).all()
        for episode in zp_tv_episode:
            episode_list.append(episode.EPISODE)
        if isinstance(selected_episode, int):
            sidebar_episode_list = []
            if selected_episode in episode_list:
                selected_episode_index = episode_list.index(selected_episode)
                log.debug('selected_episode_index %s', selected_episode_index)
                if selected_episode_index == 0:
                    for episode in episode_list:
                        if episode not in sidebar_episode_list:
                            sidebar_episode_list.append(episode)
                else:
                    list_len = len(episode_list)
                    current_list_posiiton = selected_episode_index
                    log.debug('episode_list %s', episode_list)
                    log.debug('list_len %s', list_len)
                    for i in range(current_list_posiiton, list_len):
                        log.debug('A selected_episode_index %s, i %s, episode_list[i] %s', selected_episode_index, i,
                                  episode_list[i])
                        sidebar_episode_list.append(episode_list[i])
                        log.debug('sidebar_episode_list %s', sidebar_episode_list)
                    for i in range(0, selected_episode_index):
                        log.debug('B selected_episode_index %s, i %s, episode_list[i] %s', selected_episode_index, i,
                                  episode_list[i])
                        sidebar_episode_list.append(episode_list[i])
                        log.debug('sidebar_episode_list %s', sidebar_episode_list)
            else:
                sidebar_episode_list = episode_list
        else:
            sidebar_episode_list = episode_list
        log.debug('episode_list %s', episode_list)
        session.close()
        return sidebar_episode_list
