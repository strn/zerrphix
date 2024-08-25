import logging

from sqlalchemy import and_
# from PIL import Image
from sqlalchemy import orm
from sqlalchemy import or_

from zerrphix.base import Base
from zerrphix.db import commit
from zerrphix.db.tables import TABLES
from zerrphix.util.plugin import create_eapi_dict

log = logging.getLogger(__name__)


class AdminHTTPDuneFuncs(Base):
    def __init__(self, Session, global_config_dict):
        # logging.config.dictConfig(LOG_SETTINGS)
        super(AdminHTTPDuneFuncs, self).__init__(args=[],
                                                 Session=Session,
                                                 global_config_dict=global_config_dict,
                                                 library_config_dict={}
                                                 )
        # self.Session = Session
        # self.global_config_dict = global_config_dict
        self.eapi_dict = create_eapi_dict(Session)
        self.image_type_id_dict = {'poster': 1, 'backdrop': 2, 'banner': 3}
        self.image_tv_entity_type_id_dict = {'poster': 3, 'backdrop': 4, 'banner': 5}
        self.image_season_type_id_dict = {'poster': 1}
        self.image_tv_season_entity_type_id_dict = {'poster': 1}
        self.image_tv_season_user_entity_type_id_dict = {'poster': 1}
        self.image_episode_type_id_dict = {'screenshot': 4}
        self.image_tv_episode_entity_type_id_dict = {'screenshot': 4}
        self.image_tv_episode_user_entity_type_id_dict = {'screenshot': 3}

    def get_dune_list(self):
        session = self.Session()
        return_list = []
        zp_dune_result = session.query(TABLES.ZP_DUNE).all()
        if zp_dune_result is not None:
            for dune in zp_dune_result:
                return_list.append({'id': dune.ID,
                                    'name': dune.NAME})
        session.close()
        return return_list

    def get_scan_path_map_list(self, zp_dune_id):
        session = self.Session()
        return_list = []
        zp_scan_path_result = session.query(TABLES.ZP_SCAN_PATH, TABLES.ZP_DUNE_PLAY_PATH, TABLES.ZP_LIBRARY).join(
            TABLES.ZP_LIBRARY, TABLES.ZP_LIBRARY.ID == TABLES.ZP_SCAN_PATH.ZP_LIBRARY_ID
        ).outerjoin(
            TABLES.ZP_DUNE_PLAY_PATH, and_(TABLES.ZP_SCAN_PATH.ID == TABLES.ZP_DUNE_PLAY_PATH.ZP_SCAN_PATH_ID,
                                           TABLES.ZP_DUNE_PLAY_PATH.ZP_DUNE_ID == zp_dune_id)
        ).order_by(
            TABLES.ZP_SCAN_PATH.ID.asc()
        ).all()
        if zp_scan_path_result is not None:
            for zp_scan_path in zp_scan_path_result:
                if zp_scan_path.ZP_DUNE_PLAY_PATH == None:
                    return_list.append({'id': zp_scan_path.ZP_SCAN_PATH.ID,
                                        'library': zp_scan_path.ZP_LIBRARY.DESC,
                                        'scan_path': zp_scan_path.ZP_SCAN_PATH.PATH,
                                        'play_path': ''})
                else:
                    # log.error(dir(zp_scan_path))
                    # log.error(dir(zp_scan_path.ZP_SCAN_PATH))
                    # log.error(dir(zp_scan_path.ZP_DUNE_PLAY_PATH))
                    return_list.append({'id': zp_scan_path.ZP_SCAN_PATH.ID,
                                        'library': zp_scan_path.ZP_LIBRARY.DESC,
                                        'scan_path': zp_scan_path.ZP_SCAN_PATH.PATH,
                                        'play_path': zp_scan_path.ZP_DUNE_PLAY_PATH.PLAY_ROOT_PATH})
        session.close()
        return return_list

    def set_dune_play_path(self, zp_dune_id, zp_scan_path_id, dune_play_path):
        session = self.Session()
        try:
            zp_dune_play_path = session.query(TABLES.ZP_DUNE_PLAY_PATH).filter(
                TABLES.ZP_DUNE_PLAY_PATH.ZP_DUNE_ID == zp_dune_id,
                TABLES.ZP_DUNE_PLAY_PATH.ZP_SCAN_PATH_ID == zp_scan_path_id
            ).one()
        except orm.exc.NoResultFound:
            add_zp_dune_play_path = TABLES.ZP_DUNE_PLAY_PATH(
                ZP_DUNE_ID=zp_dune_id,
                ZP_SCAN_PATH_ID=zp_scan_path_id,
                PLAY_ROOT_PATH=dune_play_path
            )
            session.add(add_zp_dune_play_path)
            commit(session)
        else:
            zp_dune_play_path.PLAY_ROOT_PATH = dune_play_path
            commit(session)
        session.close()

    def get_dune_name(self, zp_dune_id):
        session = self.Session()
        zp_dune = session.query(TABLES.ZP_DUNE).filter(
            TABLES.ZP_DUNE.ID == zp_dune_id
        ).one()
        session.close()
        return zp_dune.NAME

    def get_dune_ui_store_dict(self, zp_dune_id):
        session = self.Session()
        try:
            zp_dune = session.query(TABLES.ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF).filter(
                TABLES.ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF.ZP_DUNE_ID == zp_dune_id
            ).one()
        except orm.exc.NoResultFound:
            return_dict = {'ui_store_type_id': '',
                           'ui_share_xref_id': '',
                           'ui_root': '',
                           'ui_dune_ref': '',
                           }
        else:
            return_dict = {'ui_store_type_id': zp_dune.ZP_DUNE_UI_IMAGE_STORE_TYPE_ID,
                           'ui_share_xref_id': zp_dune.ZP_DUNE_SHARE_XREF_ID if zp_dune.ZP_DUNE_SHARE_XREF_ID != None else '',
                           'ui_root': zp_dune.ZP_DUNE_UI_IMAGE_STORE_ROOT if zp_dune.ZP_DUNE_UI_IMAGE_STORE_ROOT != None else '',
                           'ui_dune_ref': zp_dune.DUNE_LOCAL_REF if zp_dune.DUNE_LOCAL_REF != None else '',
                           }
        session.close()
        return return_dict

    def get_share_xref_dict(self):
        session = self.Session()
        return_dict = {0: {'zp_share_id': 'choose',
                           'zp_share_server_id': '',
                           'zp_share_credential_id': '', }}
        zp_share = session.query(TABLES.ZP_DUNE_SHARE_XREF).all()
        for share_xref in zp_share:
            return_dict[share_xref.ID] = {'zp_share_id': share_xref.ZP_SHARE_ID,
                                          'zp_share_server_id': share_xref.ZP_SHARE_SERVER_ID,
                                          'zp_share_credential_id': share_xref.ZP_SHARE_CREDENTIAL_ID,
                                          }
        session.close()
        return return_dict

    def get_share_xref_list(self):
        session = self.Session()
        return_list = []
        zp_share = session.query(TABLES.ZP_DUNE_SHARE_XREF).all()
        for share_xref in zp_share:
            return_list.append({'zp_share_xref_id': share_xref.ID,
                                'ref_name': share_xref.REF_NAME,
                                'zp_share_id': share_xref.ZP_SHARE_ID,
                                'zp_share_server_id': share_xref.ZP_SHARE_SERVER_ID,
                                'zp_share_credential_id': share_xref.ZP_SHARE_CREDENTIAL_ID,
                                })
        session.close()
        return return_list

    def set_share_xref(self, zp_share_xref_id, ref_name, zp_share_id, zp_share_server_id, zp_share_credential_id):
        session = self.Session()
        session.query(TABLES.ZP_DUNE_SHARE_XREF).filter(
            TABLES.ZP_DUNE_SHARE_XREF.ID == zp_share_xref_id).update(
            {"REF_NAME": ref_name,
             "ZP_SHARE_ID": zp_share_id,
             "ZP_SHARE_SERVER_ID": zp_share_server_id,
             "ZP_SHARE_CREDENTIAL_ID": zp_share_credential_id})
        commit(session)
        session.close()

    def add_share_xref(self, ref_name, zp_share_id, zp_share_server_id, zp_share_credential_id):
        session = self.Session()
        add_zp_dune_share_xref = TABLES.ZP_DUNE_SHARE_XREF(REF_NAME = ref_name,
                                                            ZP_SHARE_ID  = zp_share_id,
                                                            ZP_SHARE_SERVER_ID = zp_share_server_id,
                                                            ZP_SHARE_CREDENTIAL_ID = zp_share_credential_id)
        session.add(add_zp_dune_share_xref)
        commit(session)
        session.close()

    def add_dune(self, dune_name):
        session = self.Session()
        add_zp_dune = TABLES.ZP_DUNE(NAME = dune_name)
        session.add(add_zp_dune)
        commit(session)
        session.close()

    def get_dune_assigment_dict(self):
        session = self.Session()
        assigments = session.query(TABLES.ZP_USER_GROUP).all()
        session.close()
        try:
            iter(assigments)
        except TypeError:
            return {}
        else:
            return_dict = {}
            for assigment in assigments:
                if assigment.ZP_DUNE_ID not in return_dict:
                    return_dict[assigment.ZP_DUNE_ID] = []
                return_dict[assigment.ZP_DUNE_ID].append(assigment.ZP_USER_ID)
            return return_dict

    def clear_dune_assigments(self):
        session = self.Session()
        session.query(TABLES.ZP_USER_GROUP).delete(synchronize_session='fetch')
        commit(session)
        session.close()

    def add_dune_assigments(self, zp_user_id, zp_dune_id):
        session = self.Session()
        add_zp_user_group = TABLES.ZP_USER_GROUP(
            ZP_USER_ID = zp_user_id,
            ZP_DUNE_ID = zp_dune_id
        )
        session.add(add_zp_user_group)
        commit(session)
        session.close()

    def set_ui_store(self, zp_dune_id, ui_store_type_id, ui_share_xref_id, ui_root, ui_dune_ref):
        session = self.Session()
        try:
            zp_dune_ui_image_store_type_xref = session.query(TABLES.ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF).filter(
                TABLES.ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF.ZP_DUNE_ID == zp_dune_id
            ).one()
        except orm.exc.NoResultFound:
            add_zp_dune_ui_image_store_type_xref = TABLES.ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF(
                ZP_DUNE_ID=zp_dune_id,
                ZP_DUNE_UI_IMAGE_STORE_TYPE_ID=ui_store_type_id,
                ZP_DUNE_SHARE_XREF_ID=ui_share_xref_id,
                ZP_DUNE_UI_IMAGE_STORE_ROOT=ui_root,
                DUNE_LOCAL_REF=ui_dune_ref
            )
            session.add(add_zp_dune_ui_image_store_type_xref)
            commit(session)
        else:
            zp_dune_ui_image_store_type_xref.ZP_DUNE_ID = zp_dune_id
            zp_dune_ui_image_store_type_xref.ZP_DUNE_UI_IMAGE_STORE_TYPE_ID = ui_store_type_id
            zp_dune_ui_image_store_type_xref.ZP_DUNE_SHARE_XREF_ID = ui_share_xref_id
            zp_dune_ui_image_store_type_xref.ZP_DUNE_UI_IMAGE_STORE_ROOT = ui_root
            zp_dune_ui_image_store_type_xref.DUNE_LOCAL_REF = ui_dune_ref
            commit(session)
        session.close()

    def check_dune_exists(self, zp_dune_id):
        session = self.Session()
        try:
            session.query(TABLES.ZP_DUNE).filter(TABLES.ZP_DUNE.ID == zp_dune_id).one()
        except orm.exc.NoResultFound:
            dune_exists = False
        else:
            dune_exists = True
        session.close()
        return dune_exists

    def get_play_path_dict(self, zp_dune_id):
        session = self.Session()
        return_dict = {}
        qry_zp_scan_path = session.query(
            TABLES.ZP_SCAN_PATH.ID,
            TABLES.ZP_SCAN_PATH.PATH,
            TABLES.ZP_SCAN_PATH.ZP_SCAN_PATH_FS_TYPE_ID,
            TABLES.ZP_SHARE.SHARE_NAME,
            TABLES.ZP_SHARE_SERVER.REMOTE_NAME,
            TABLES.ZP_SHARE_SERVER.HOSTNAME,
            TABLES.ZP_SHARE_SERVER.PORT,
            TABLES.ZP_SHARE_CREDENTIAL.USERNAME,
            TABLES.ZP_DUNE_PLAY_PATH.PLAY_ROOT_PATH
        ).outerjoin(
            TABLES.ZP_DUNE_PLAY_PATH, TABLES.ZP_DUNE_PLAY_PATH.ZP_SCAN_PATH_ID == TABLES.ZP_SCAN_PATH.ID
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
            or_(TABLES.ZP_DUNE_PLAY_PATH.ZP_DUNE_ID == zp_dune_id,
                TABLES.ZP_DUNE_PLAY_PATH.ZP_DUNE_ID == None)
        ).order_by(TABLES.ZP_SCAN_PATH.ID.asc()).all()
        session.close()
        for rslt_scan_path in qry_zp_scan_path:
            if rslt_scan_path.ZP_SCAN_PATH_FS_TYPE_ID == 1:
                path = rslt_scan_path.PATH
            else:
                path = 'smb://%s@%s{%s}:%s/%s/%s' % (rslt_scan_path.USERNAME,
                                   rslt_scan_path.HOSTNAME,
                                   rslt_scan_path.REMOTE_NAME,
                                   rslt_scan_path.PORT,
                                   rslt_scan_path.SHARE_NAME,
                                   rslt_scan_path.PATH)
            return_dict[rslt_scan_path.ID] = {'scan_path': path,
                                              'play_path': rslt_scan_path.PLAY_ROOT_PATH if \
                                                  rslt_scan_path.PLAY_ROOT_PATH is not None else ''}
        return return_dict

    def set_play_path(self, zp_dune_id, zp_scan_path_id, play_path):
        session = self.Session()
        try:
            zp_dune_play_path = session.query(
                TABLES.ZP_DUNE_PLAY_PATH
            ).filter(
                TABLES.ZP_DUNE_PLAY_PATH.ZP_DUNE_ID == zp_dune_id,
                TABLES.ZP_DUNE_PLAY_PATH.ZP_SCAN_PATH_ID == zp_scan_path_id
            ).one()
        except orm.exc.NoResultFound:
            add_zp_dune_play_path = TABLES.ZP_DUNE_PLAY_PATH(
                ZP_DUNE_ID = zp_dune_id,
                ZP_SCAN_PATH_ID = zp_scan_path_id,
                PLAY_ROOT_PATH = play_path
            )
            session.add(add_zp_dune_play_path)
            commit(session)
        else:
            zp_dune_play_path.PLAY_ROOT_PATH = play_path
            commit(session)
        session.close()
