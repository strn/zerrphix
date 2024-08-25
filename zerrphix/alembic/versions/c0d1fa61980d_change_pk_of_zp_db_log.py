"""Change PK of ZP_DB_LOG

Revision ID: c0d1fa61980d
Revises: f5c805cabe49
Create Date: 2018-01-05 08:54:15.165039

"""
from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base, DeferredReflection
from sqlalchemy.orm import sessionmaker, scoped_session
import datetime

# revision identifiers, used by Alembic.
revision = 'c0d1fa61980d'
down_revision = 'f5c805cabe49'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ZP_DB_LOG_TEMP',
        sa.Column('EPOCH', sa.Numeric(precision=18, scale=8), primary_key=True),
        sa.Column('LEVEL', sa.Integer(), nullable=False),
        sa.Column('TEXT', sa.Text(), nullable=False),
        sa.Column('TRACEBACK', sa.Text(), nullable=True),
        sa.Column('COUNT_24', sa.Integer(), nullable=False),
        sa.Column('SOURCE_ID', sa.Integer(), primary_key=True),
        sa.Column('FIRST_OCCURRENCE_DATE_TIME', sa.DateTime(), nullable=False),
        sa.Column('LAST_OCCURRENCE_DATE_TIME', sa.DateTime(), nullable=False)
    )
    op.create_table(
        'ZP_PROCESS_RUNNING_HISTORY_TEMP',
        sa.Column('EPOCH', sa.Numeric(precision=18, scale=8), primary_key=True),
        sa.Column('ZP_LIBRARY_ID', sa.Integer(), primary_key=True),
        sa.Column('ZP_PROCESS_ID', sa.Integer(), primary_key=True),
        sa.Column('PROCESS', sa.Text(), nullable=False),
        sa.Column('PROCESS_STATE', sa.Text(), nullable=False),
        sa.Column('PROCESS_STATE_DATETIME', sa.DateTime(), nullable=False),
        sa.Column('PROCESS_STATE_INITIAL_DATETIME', sa.DateTime(), nullable=False),
        sa.Column('COUNT', sa.Integer(), nullable=False)
    )
    url = context.config.get_main_option("sqlalchemy.url")
    Base = declarative_base(cls=DeferredReflection)
    class ZP_DB_LOG(Base):
        __tablename__ = 'ZP_DB_LOG'
    class ZP_DB_LOG_TEMP(Base):
        __tablename__ = 'ZP_DB_LOG_TEMP'
    class ZP_PROCESS_RUNNING_HISTORY(Base):
        __tablename__ = 'ZP_PROCESS_RUNNING_HISTORY'
    class ZP_PROCESS_RUNNING_HISTORY_TEMP(Base):
        __tablename__ = 'ZP_PROCESS_RUNNING_HISTORY_TEMP'
    engine = sa.create_engine(url)
    Base.prepare(engine)
    Base.metadata.create_all(engine)
    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()
    max_zp_db_log_id = session.query(sa.func.max(ZP_DB_LOG.ID)).one()[0]
    fake_miliseconds = 0.00000001
    if isinstance(max_zp_db_log_id, int):
        if max_zp_db_log_id > 0:
            zp_db_log_id = max_zp_db_log_id + 1
            processing_zp_db_log = False
            while processing_zp_db_log is False:
                db_log_entries = get_db_log_entries(session, zp_db_log_id, ZP_DB_LOG)
                if db_log_entries:
                    for db_log_entry in db_log_entries:
                        zp_db_log_id = db_log_entry['ID']
                        db_log_entry_epoch = (
                            db_log_entry['FIRST_OCCURRENCE_DATE_TIME'] - datetime.datetime.utcfromtimestamp(0)
                        ).total_seconds()
                        db_log_entry_epoch_str = '{}.{}'.format(
                            int(db_log_entry_epoch), ('{:0.8f}'.format(fake_miliseconds)).split('.')[1])
                        fake_miliseconds += 0.00000001
                        if fake_miliseconds >= 1.0:
                            fake_miliseconds = 0.00000001
                        add_db_log_temp_entry = ZP_DB_LOG_TEMP(
                            EPOCH = db_log_entry_epoch_str,
                            LEVEL = db_log_entry['LEVEL'],
                            TEXT = db_log_entry['TEXT'],
                            TRACEBACK = db_log_entry['TRACEBACK'],
                            COUNT_24 = db_log_entry['COUNT_24'],
                            SOURCE_ID = db_log_entry['SOURCE_ID'],
                            FIRST_OCCURRENCE_DATE_TIME =
                            db_log_entry['FIRST_OCCURRENCE_DATE_TIME'].strftime("%Y-%m-%d %H:%M:%S"),
                            LAST_OCCURRENCE_DATE_TIME =
                            db_log_entry['LAST_OCCURRENCE_DATE_TIME'].strftime("%Y-%m-%d %H:%M:%S")
                        )
                        session.add(add_db_log_temp_entry)
                        session.flush()
                else:
                    processing_zp_db_log = True
                session.commit()
    max_zp_process_running_history_id = session.query(sa.func.max(ZP_PROCESS_RUNNING_HISTORY.ID)).one()[0]
    fake_miliseconds = 0.00000001
    if isinstance(max_zp_process_running_history_id, int):
        if max_zp_process_running_history_id > 0:
            zp_process_running_history_id = max_zp_process_running_history_id + 1
            processing_zp_process_running_history = False
            while processing_zp_process_running_history is False:
                db_log_entries = get_process_running_history_entries(session, zp_process_running_history_id,
                                                                     ZP_PROCESS_RUNNING_HISTORY)
                if db_log_entries:
                    for db_log_entry in db_log_entries:
                        zp_process_running_history_id = db_log_entry['ID']
                        db_log_entry_epoch = (
                            db_log_entry['PROCESS_STATE_DATETIME'] - datetime.datetime.utcfromtimestamp(0)
                        ).total_seconds()
                        db_log_entry_epoch_str = '{}.{}'.format(
                            int(db_log_entry_epoch), ('{:0.8f}'.format(fake_miliseconds)).split('.')[1])
                        fake_miliseconds += 0.00000001
                        if fake_miliseconds >= 1.0:
                            fake_miliseconds = 0.00000001
                        add_db_log_temp_entry = ZP_PROCESS_RUNNING_HISTORY_TEMP(
                            EPOCH = db_log_entry_epoch_str,
                            ZP_LIBRARY_ID = db_log_entry['ZP_LIBRARY_ID'],
                            ZP_PROCESS_ID = db_log_entry['ZP_PROCESS_ID'],
                            PROCESS = db_log_entry['PROCESS'],
                            PROCESS_STATE = db_log_entry['PROCESS_STATE'],
                            PROCESS_STATE_DATETIME =
                            db_log_entry['PROCESS_STATE_DATETIME'].strftime("%Y-%m-%d %H:%M:%S"),
                            PROCESS_STATE_INITIAL_DATETIME =
                            db_log_entry['PROCESS_STATE_INITIAL_DATETIME'].strftime("%Y-%m-%d %H:%M:%S"),
                            COUNT = db_log_entry['COUNT']
                        )
                        session.add(add_db_log_temp_entry)
                        session.flush()
                else:
                    processing_zp_process_running_history = True
                session.commit()
    session.commit()
    session.close()
    op.drop_table('ZP_DB_LOG')
    op.drop_table('ZP_PROCESS_RUNNING_HISTORY')
    op.rename_table('ZP_DB_LOG_TEMP', 'ZP_DB_LOG')
    op.rename_table('ZP_PROCESS_RUNNING_HISTORY_TEMP', 'ZP_PROCESS_RUNNING_HISTORY')

def downgrade():
    pass


def get_process_running_history_entries(session, zp_process_running_history_id, ZP_PROCESS_RUNNING_HISTORY):
    return_list = []
    zp_process_running_history_id_qry = session.query(
        ZP_PROCESS_RUNNING_HISTORY
    ).filter(
        ZP_PROCESS_RUNNING_HISTORY.ID < zp_process_running_history_id
    ).order_by(
        ZP_PROCESS_RUNNING_HISTORY.ID.desc()
    ).limit(100)

    for zp_process_running_history in zp_process_running_history_id_qry:
        return_list.append(
            {'ID': zp_process_running_history.ID,
            'ZP_LIBRARY_ID': zp_process_running_history.ZP_LIBRARY_ID,
            'ZP_PROCESS_ID': zp_process_running_history.ZP_PROCESS_ID,
            'PROCESS': zp_process_running_history.PROCESS,
            'PROCESS_STATE': zp_process_running_history.PROCESS_STATE,
            'PROCESS_STATE_DATETIME': zp_process_running_history.PROCESS_STATE_DATETIME,
            'PROCESS_STATE_INITIAL_DATETIME': zp_process_running_history.PROCESS_STATE_INITIAL_DATETIME,
            'COUNT': zp_process_running_history.COUNT}
        )
    return return_list


def get_db_log_entries(session, zp_db_log_id, ZP_DB_LOG):
    return_list = []
    zp_db_log_id_qry = session.query(
        ZP_DB_LOG
    ).filter(
        ZP_DB_LOG.ID < zp_db_log_id
    ).order_by(
        ZP_DB_LOG.ID.desc()
    ).limit(100)

    for zp_db_log in zp_db_log_id_qry:
        return_list.append(
            {'ID': zp_db_log.ID,
            'LEVEL': zp_db_log.LEVEL,
            'TEXT': zp_db_log.TEXT,
            'TRACEBACK': zp_db_log.TRACEBACK,
            'COUNT_24': zp_db_log.COUNT_24,
            'SOURCE_ID': zp_db_log.SOURCE_ID,
            'FIRST_OCCURRENCE_DATE_TIME': zp_db_log.FIRST_OCCURRENCE_DATE_TIME,
            'LAST_OCCURRENCE_DATE_TIME': zp_db_log.LAST_OCCURRENCE_DATE_TIME}
        )
    return return_list