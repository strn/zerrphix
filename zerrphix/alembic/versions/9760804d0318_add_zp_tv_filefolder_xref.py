"""Add ZP_TV_FILEFOLDER_XREF

Revision ID: 9760804d0318
Revises: d9d26cdee08b
Create Date: 2018-01-15 19:49:55.074218

"""
from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base, DeferredReflection
from sqlalchemy.orm import sessionmaker, scoped_session


# revision identifiers, used by Alembic.
revision = '9760804d0318'
down_revision = 'd9d26cdee08b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ZP_TV_FILEFOLDER_XREF',
        sa.Column('ZP_TV_FILEFOLDER_ID', sa.Integer(), primary_key=True),
        sa.Column('ZP_TV_ID', sa.Integer(), nullable=False),
        sa.Column('ADDED_DATE_TIME', sa.DateTime(), nullable=False)
    )
    url = context.config.get_main_option("sqlalchemy.url")
    Base = declarative_base(cls=DeferredReflection)
    class ZP_TV(Base):
        __tablename__ = 'ZP_TV'
    class ZP_TV_FILEFOLDER_XREF(Base):
        __tablename__ = 'ZP_TV_FILEFOLDER_XREF'
    engine = sa.create_engine(url)
    Base.prepare(engine)
    Base.metadata.create_all(engine)
    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()
    max_zp_tv_id = session.query(sa.func.max(ZP_TV.ID)).one()[0]
    if isinstance(max_zp_tv_id, int):
        if max_zp_tv_id > 0:
            zp_tv_id = max_zp_tv_id + 1
            processing_zp_db_log = False
            while processing_zp_db_log is False:
                zp_tv_list = get_zp_tv_list(session, zp_tv_id, ZP_TV)
                if zp_tv_list:
                    for zp_tv_dict in zp_tv_list:
                        zp_tv_id = zp_tv_dict['zp_tv_id']
                        add_zp_tv_filefolder_xref = ZP_TV_FILEFOLDER_XREF(
                            ZP_TV_FILEFOLDER_ID=zp_tv_dict['zp_tv_filefolder_id'],
                            ZP_TV_ID=zp_tv_dict['zp_tv_id'],
                            ADDED_DATE_TIME=zp_tv_dict['added_datetime'].strftime("%Y-%m-%d %H:%M:%S")
                        )
                        session.add(add_zp_tv_filefolder_xref)
                        session.commit()
                else:
                    processing_zp_db_log = True
    session.close()
    op.drop_column('ZP_TV', 'ZP_TV_FILEFOLDER_ID')


def downgrade():
    pass


def get_zp_tv_list(session, zp_tv_id, ZP_TV):
    return_list = []
    zp_tv_qry = session.query(
        ZP_TV
    ).filter(
        ZP_TV.ID < zp_tv_id
    ).order_by(
        ZP_TV.ID.desc()
    ).limit(100)

    for zp_tv_rslt in zp_tv_qry:
        return_list.append(
            {'zp_tv_id': zp_tv_rslt.ID,
             'zp_tv_filefolder_id': zp_tv_rslt.ZP_TV_FILEFOLDER_ID,
             'added_datetime': zp_tv_rslt.ADDED_DATE_TIME
             }
        )
    return return_list
