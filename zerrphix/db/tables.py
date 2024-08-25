from zerrphix.db import Base


class TABLES(object):
    class ZP_ACODEC(Base):
        __tablename__ = 'ZP_ACODEC'

    class ZP_DB_LOG(Base):
        __tablename__ = 'ZP_DB_LOG'

    class ZP_DUNE(Base):
        __tablename__ = 'ZP_DUNE'

    class ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF(Base):
        __tablename__ = 'ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF'

    class ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF(Base):
        __tablename__ = 'ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF'

    class ZP_DUNE_PLAY_PATH(Base):
        __tablename__ = 'ZP_DUNE_PLAY_PATH'

    class ZP_DUNE_SHARE_XREF(Base):
        __tablename__ = 'ZP_DUNE_SHARE_XREF'

    class ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF(Base):
        __tablename__ = 'ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF'

    class ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF(Base):
        __tablename__ = 'ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF'

    class ZP_DUNE_UI_IMAGE_STORE_TYPE(Base):
        __tablename__ = 'ZP_DUNE_UI_IMAGE_STORE_TYPE'

    class ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF(Base):
        __tablename__ = 'ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF'

    class ZP_DUNE_USER_IMAGE_RENDER_HASH_XREF(Base):
        __tablename__ = 'ZP_DUNE_USER_IMAGE_RENDER_HASH_XREF'

    class ZP_EAPI(Base):
        __tablename__ = 'ZP_EAPI'

    class ZP_EAPI_LIBRARY_XREF(Base):
        __tablename__ = 'ZP_EAPI_LIBRARY_XREF'

    class ZP_EAPI_LINK(Base):
        __tablename__ = 'ZP_EAPI_LINK'

    class ZP_FILE_EXTENSION(Base):
        __tablename__ = 'ZP_FILE_EXTENSION'

    class ZP_FILM(Base):
        __tablename__ = 'ZP_FILM'

    class ZP_FILM_COLLECTION(Base):
        __tablename__ = 'ZP_FILM_COLLECTION'

    class ZP_FILM_COLLECTION_EAPI_EID(Base):
        __tablename__ = 'ZP_FILM_COLLECTION_EAPI_EID'

    class ZP_FILM_COLLECTION_IMAGE_RENDER_HASH(Base):
        __tablename__ = 'ZP_FILM_COLLECTION_IMAGE_RENDER_HASH'

    class ZP_FILM_COLLECTION_OVERVIEW(Base):
        __tablename__ = 'ZP_FILM_COLLECTION_OVERVIEW'

    class ZP_FILM_COLLECTION_RAW_IMAGE(Base):
        __tablename__ = 'ZP_FILM_COLLECTION_RAW_IMAGE'

    class ZP_FILM_COLLECTION_SPECIAL_TYPE(Base):
        __tablename__ = 'ZP_FILM_COLLECTION_SPECIAL_TYPE'

    class ZP_FILM_COLLECTION_SPEICAL_TYPE_XREF(Base):
        __tablename__ = 'ZP_FILM_COLLECTION_SPEICAL_TYPE_XREF'

    class ZP_FILM_COLLECTION_TITLE(Base):
        __tablename__ = 'ZP_FILM_COLLECTION_TITLE'

    class ZP_FILM_COLLECTION_XREF(Base):
        __tablename__ = 'ZP_FILM_COLLECTION_XREF'

    class ZP_FILM_EAPI_EID(Base):
        __tablename__ = 'ZP_FILM_EAPI_EID'

    class ZP_FILM_FILEFOLDER(Base):
        __tablename__ = 'ZP_FILM_FILEFOLDER'

    class ZP_FILM_FILEFOLDER_AUIDO_METADATA(Base):
        __tablename__ = 'ZP_FILM_FILEFOLDER_AUIDO_METADATA'

    class ZP_FILM_FILEFOLDER_SCORE(Base):
        __tablename__ = 'ZP_FILM_FILEFOLDER_SCORE'

    class ZP_FILM_FILEFOLDER_TEXT_METADATA(Base):
        __tablename__ = 'ZP_FILM_FILEFOLDER_TEXT_METADATA'

    class ZP_FILM_FILEFOLDER_VIDEO_METADATA(Base):
        __tablename__ = 'ZP_FILM_FILEFOLDER_VIDEO_METADATA'

    class ZP_FILM_GENRE_XREF(Base):
        __tablename__ = 'ZP_FILM_GENRE_XREF'

    class ZP_FILM_IMAGE_RENDER_HASH(Base):
        __tablename__ = 'ZP_FILM_IMAGE_RENDER_HASH'

    class ZP_FILM_OVERVIEW(Base):
        __tablename__ = 'ZP_FILM_OVERVIEW'

    class ZP_FILM_RATING(Base):
        __tablename__ = 'ZP_FILM_RATING'

    class ZP_FILM_RAW_IMAGE(Base):
        __tablename__ = 'ZP_FILM_RAW_IMAGE'

    class ZP_FILM_RELEASE(Base):
        __tablename__ = 'ZP_FILM_RELEASE'

    class ZP_FILM_ROLE_XREF(Base):
        __tablename__ = 'ZP_FILM_ROLE_XREF'

    class ZP_FILM_RUNTIME(Base):
        __tablename__ = 'ZP_FILM_RUNTIME'

    class ZP_FILM_SPECIAL_TYPE(Base):
        __tablename__ = 'ZP_FILM_SPECIAL_TYPE'

    class ZP_FILM_SPEICAL_TYPE_XREF(Base):
        __tablename__ = 'ZP_FILM_SPEICAL_TYPE_XREF'

    class ZP_FILM_TITLE(Base):
        __tablename__ = 'ZP_FILM_TITLE'

    class ZP_FOLDER_TYPE(Base):
        __tablename__ = 'ZP_FOLDER_TYPE'

    class ZP_GENRE(Base):
        __tablename__ = 'ZP_GENRE'

    class ZP_IMAGE_SUB_TYPE(Base):
        __tablename__ = 'ZP_IMAGE_SUB_TYPE'

    class ZP_IMAGE_TYPE(Base):
        __tablename__ = 'ZP_IMAGE_TYPE'

    class ZP_INVALID_FILEFOLDER(Base):
        __tablename__ = 'ZP_INVALID_FILEFOLDER'

    class ZP_INVALID_FILEFOLDER_SOURCE(Base):
        __tablename__ = 'ZP_INVALID_FILEFOLDER_SOURCE'

    class ZP_LANG(Base):
        __tablename__ = 'ZP_LANG'

    class ZP_LIBRARY(Base):
        __tablename__ = 'ZP_LIBRARY'

    class ZP_LIBRARY_FILE_EXTENSION(Base):
        __tablename__ = 'ZP_LIBRARY_FILE_EXTENSION'

    class ZP_LIBRARY_RUN(Base):
        __tablename__ = 'ZP_LIBRARY_RUN'

    class ZP_PEOPLE(Base):
        __tablename__ = 'ZP_PEOPLE'

    class ZP_PEOPLE_EAPI_XREF(Base):
        __tablename__ = 'ZP_PEOPLE_EAPI_XREF'

    class ZP_PROCESS_RUN(Base):
        __tablename__ = 'ZP_PROCESS_RUN'

    class ZP_PROCESS_RUNNING(Base):
        __tablename__ = 'ZP_PROCESS_RUNNING'

    class ZP_PROCESS_RUNNING_HISTORY(Base):
        __tablename__ = 'ZP_PROCESS_RUNNING_HISTORY'

    class ZP_RES(Base):
        __tablename__ = 'ZP_RES'

    class ZP_RETRY(Base):
        __tablename__ = 'ZP_RETRY'

    class ZP_RETRY_COUNT(Base):
        __tablename__ = 'ZP_RETRY_COUNT'

    class ZP_RETRY_ENTITY_TYPE(Base):
        __tablename__ = 'ZP_RETRY_ENTITY_TYPE'

    class ZP_RETRY_TYPE(Base):
        __tablename__ = 'ZP_RETRY_TYPE'

    class ZP_ROLE(Base):
        __tablename__ = 'ZP_ROLE'

    class ZP_SCAN_PATH(Base):
        __tablename__ = 'ZP_SCAN_PATH'

    class ZP_SCAN_PATH_FS_TYPE(Base):
        __tablename__ = 'ZP_SCAN_PATH_FS_TYPE'

    class ZP_SCAN_PATH_SHARE_XREF(Base):
        __tablename__ = 'ZP_SCAN_PATH_SHARE_XREF'

    class ZP_SCHEMA_VERSION(Base):
        __tablename__ = 'ZP_SCHEMA_VERSION'

    class ZP_SHARE(Base):
        __tablename__ = 'ZP_SHARE'

    class ZP_SHARE_CREDENTIAL(Base):
        __tablename__ = 'ZP_SHARE_CREDENTIAL'

    class ZP_SHARE_SERVER(Base):
        __tablename__ = 'ZP_SHARE_SERVER'

    class ZP_SOURCE(Base):
        __tablename__ = 'ZP_SOURCE'

    class ZP_TCODEC(Base):
        __tablename__ = 'ZP_TCODEC'

    class ZP_TEMPLATE(Base):
        __tablename__ = 'ZP_TEMPLATE'

    class ZP_TV(Base):
        __tablename__ = 'ZP_TV'

    class ZP_TV_EAPI_EID(Base):
        __tablename__ = 'ZP_TV_EAPI_EID'

    class ZP_TV_EPISODE(Base):
        __tablename__ = 'ZP_TV_EPISODE'

    class ZP_TV_EPISODE_FILEFOLDER(Base):
        __tablename__ = 'ZP_TV_EPISODE_FILEFOLDER'

    class ZP_TV_EPISODE_IMAGE_RENDER_HASH(Base):
        __tablename__ = 'ZP_TV_EPISODE_IMAGE_RENDER_HASH'

    class ZP_TV_EPISODE_OVERVIEW(Base):
        __tablename__ = 'ZP_TV_EPISODE_OVERVIEW'

    class ZP_TV_EPISODE_TITLE(Base):
        __tablename__ = 'ZP_TV_EPISODE_TITLE'

    class ZP_TV_FILEFOLDER(Base):
        __tablename__ = 'ZP_TV_FILEFOLDER'

    class ZP_TV_FILEFOLDER_XREF(Base):
        __tablename__ = 'ZP_TV_FILEFOLDER_XREF'

    class ZP_TV_GENRE_XREF(Base):
        __tablename__ = 'ZP_TV_GENRE_XREF'

    class ZP_TV_IMAGE_RENDER_HASH(Base):
        __tablename__ = 'ZP_TV_IMAGE_RENDER_HASH'

    class ZP_TV_EPISODE_IMAGE_SUB_TYPE_XREF(Base):
        __tablename__ = 'ZP_TV_EPISODE_IMAGE_SUB_TYPE_XREF'

    class ZP_TV_OVERVIEW(Base):
        __tablename__ = 'ZP_TV_OVERVIEW'

    class ZP_TV_EPISODE_RAW_IMAGE(Base):
        __tablename__ = 'ZP_TV_EPISODE_RAW_IMAGE'

    class ZP_TV_EPISODE_SPEICAL_TYPE_XREF(Base):
        __tablename__ = 'ZP_TV_EPISODE_SPEICAL_TYPE_XREF'

    class ZP_TV_RATING(Base):
        __tablename__ = 'ZP_TV_RATING'

    class ZP_TV_RAW_IMAGE(Base):
        __tablename__ = 'ZP_TV_RAW_IMAGE'

    class ZP_TV_RELEASE(Base):
        __tablename__ = 'ZP_TV_RELEASE'

    class ZP_TV_ROLE_XREF(Base):
        __tablename__ = 'ZP_TV_ROLE_XREF'

    class ZP_TV_RUNNING(Base):
        __tablename__ = 'ZP_TV_RUNNING'

    class ZP_TV_RUNTIME(Base):
        __tablename__ = 'ZP_TV_RUNTIME'

    class ZP_TV_SEASON_RAW_IMAGE(Base):
        __tablename__ = 'ZP_TV_SEASON_RAW_IMAGE'

    class ZP_TV_SPECIAL_TYPE(Base):
        __tablename__ = 'ZP_TV_SPECIAL_TYPE'

    class ZP_TV_SPEICAL_TYPE_XREF(Base):
        __tablename__ = 'ZP_TV_SPEICAL_TYPE_XREF'

    class ZP_TV_TITLE(Base):
        __tablename__ = 'ZP_TV_TITLE'

    class ZP_USER(Base):
        __tablename__ = 'ZP_USER'

    class ZP_USER_EAPI_PREF(Base):
        __tablename__ = 'ZP_USER_EAPI_PREF'

    class ZP_USER_FILM_COLLECTION_ENTITY_XREF(Base):
        __tablename__ = 'ZP_USER_FILM_COLLECTION_ENTITY_XREF'

    class ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF(Base):
        __tablename__ = 'ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF'

    class ZP_USER_FILM_ENTITY_XREF(Base):
        __tablename__ = 'ZP_USER_FILM_ENTITY_XREF'

    class ZP_USER_FILM_FAVOURITE(Base):
        __tablename__ = 'ZP_USER_FILM_FAVOURITE'

    class ZP_USER_FILM_IMAGE_RENDER_HASH_XREF(Base):
        __tablename__ = 'ZP_USER_FILM_IMAGE_RENDER_HASH_XREF'

    class ZP_USER_FILM_TITLE_TYPE_PREF(Base):
        __tablename__ = 'ZP_USER_FILM_TITLE_TYPE_PREF'

    class ZP_USER_FILM_TOWATCH(Base):
        __tablename__ = 'ZP_USER_FILM_TOWATCH'

    class ZP_USER_FILM_WATCHED(Base):
        __tablename__ = 'ZP_USER_FILM_WATCHED'

    class ZP_USER_GROUP(Base):
        __tablename__ = 'ZP_USER_GROUP'

    class ZP_USER_IMAGE_RENDER_HASH(Base):
        __tablename__ = 'ZP_USER_IMAGE_RENDER_HASH'

    class ZP_USER_LIBRARY_LANG(Base):
        __tablename__ = 'ZP_USER_LIBRARY_LANG'

    class ZP_USER_PRIV(Base):
        __tablename__ = 'ZP_USER_PRIV'

    class ZP_USER_SPECIAL_TYPE(Base):
        __tablename__ = 'ZP_USER_SPECIAL_TYPE'

    class ZP_USER_TEMPLATE_XREF(Base):
        __tablename__ = 'ZP_USER_TEMPLATE_XREF'

    class ZP_USER_TV_ENTITY_XREF(Base):
        __tablename__ = 'ZP_USER_TV_ENTITY_XREF'

    class ZP_USER_TV_EPISODE_ENTITY_XREF(Base):
        __tablename__ = 'ZP_USER_TV_EPISODE_ENTITY_XREF'

    class ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF(Base):
        __tablename__ = 'ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF'

    class ZP_USER_TV_SEASON_ENTITY_XREF(Base):
        __tablename__ = 'ZP_USER_TV_SEASON_ENTITY_XREF'

    class ZP_USER_TV_EPISODE_WATCHED(Base):
        __tablename__ = 'ZP_USER_TV_EPISODE_WATCHED'

    class ZP_USER_TV_FAVOURITE(Base):
        __tablename__ = 'ZP_USER_TV_FAVOURITE'

    class ZP_USER_TV_IMAGE_RENDER_HASH_XREF(Base):
        __tablename__ = 'ZP_USER_TV_IMAGE_RENDER_HASH_XREF'

    class ZP_USER_TV_TITLE_TYPE_PREF(Base):
        __tablename__ = 'ZP_USER_TV_TITLE_TYPE_PREF'

    class ZP_USER_TV_TOWATCH(Base):
        __tablename__ = 'ZP_USER_TV_TOWATCH'

    class ZP_VCODEC(Base):
        __tablename__ = 'ZP_VCODEC'

    """ VIEWS
    """
