"""Add GSM610 to ZP_ACODEC

Revision ID: c640c1ca3402
Revises: 4fcc62ce28dc
Create Date: 2017-12-30 16:44:00.956054

"""
from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base, DeferredReflection
from sqlalchemy.orm import sessionmaker, scoped_session


# revision identifiers, used by Alembic.
revision = 'c640c1ca3402'
down_revision = '4fcc62ce28dc'
branch_labels = None
depends_on = None


def upgrade():
    url = context.config.get_main_option("sqlalchemy.url")
    #DBSession.configure(bind=engine)
    Base = declarative_base(cls=DeferredReflection)
    class ZP_ACODEC(Base):
        __tablename__ = 'ZP_ACODEC'
    class ZP_VCODEC(Base):
        __tablename__ = 'ZP_VCODEC'
    engine = sa.create_engine(url)
    Base.prepare(engine)
    Base.metadata.create_all(engine)
    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()
    zp_acodec_data_list = [
        {'CODEC': 'GSM610', 'TEMPLATE_IDENTIFIER': 'gsm610'}, #15
    ]
    for zp_acodec_data in zp_acodec_data_list:
        add_zp_acodec = ZP_ACODEC(**zp_acodec_data)
        session.add(add_zp_acodec)
        session.flush()
    zp_vcodec_data_list = [
        {'CODEC': 'DV', 'TEMPLATE_IDENTIFIER': 'dv'}, #15
        {'CODEC': 'MP43', 'TEMPLATE_IDENTIFIER': 'mp43'} #16
    ]
    for zp_vcodec_data in zp_vcodec_data_list:
        add_zp_vcodec = ZP_VCODEC(**zp_vcodec_data)
        session.add(add_zp_vcodec)
        session.flush()
    session.commit()
    session.close()


def downgrade():
    pass
