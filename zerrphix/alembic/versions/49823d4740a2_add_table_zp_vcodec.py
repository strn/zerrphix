"""Add Table ZP_VCODEC

Revision ID: 49823d4740a2
Revises: 71047edd5449
Create Date: 2017-12-26 19:21:12.684065

"""
from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base, DeferredReflection
from sqlalchemy.orm import sessionmaker, scoped_session



# revision identifiers, used by Alembic.
revision = '49823d4740a2'
down_revision = '71047edd5449'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('ZP_FILM_FILEFOLDER_VIDEO_METADATA', sa.Column('BIT_DEPTH', sa.String(2), nullable=False))
    op.create_table(
        'ZP_VCODEC',
        sa.Column('ID', sa.Integer(), primary_key=True),
        sa.Column('CODEC', sa.String(32), nullable=False),
        sa.Column('TEMPLATE_IDENTIFIER', sa.String(32), nullable=False)
    )
    op.drop_table('ZP_ACODEC_XREF')
    op.drop_table('ZP_VCODEC_XREF')
    op.drop_table('ZP_TCODEC_XREF')
    url = context.config.get_main_option("sqlalchemy.url")
    #DBSession.configure(bind=engine)
    Base = declarative_base(cls=DeferredReflection)
    class ZP_VCODEC(Base):
        __tablename__ = 'ZP_VCODEC'
    engine = sa.create_engine(url)
    Base.prepare(engine)
    Base.metadata.create_all(engine)
    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()
    session.flush()
    zp_vcodec_data_list = [
        {'CODEC': 'MPEG-1', 'TEMPLATE_IDENTIFIER': 'mpeg_1'}, # 1
        {'CODEC': 'MPEG-2', 'TEMPLATE_IDENTIFIER': 'mpeg_2'}, # 2
        {'CODEC': 'MPEG-4', 'TEMPLATE_IDENTIFIER': 'mpeg_4'}, # 3
        {'CODEC': 'h263', 'TEMPLATE_IDENTIFIER': 'h263'}, # 4
        {'CODEC': 'RealVideo', 'TEMPLATE_IDENTIFIER': 'realvideo'}, # 5
        {'CODEC': 'VC1', 'TEMPLATE_IDENTIFIER': 'vc_1'}, # 6
        {'CODEC': 'WMVHD', 'TEMPLATE_IDENTIFIER': 'wmv_hd'}, # 7
        {'CODEC': 'XVID', 'TEMPLATE_IDENTIFIER': 'xvid'}, # 8
        {'CODEC': 'DIVX', 'TEMPLATE_IDENTIFIER': 'divx'}, # 9
        {'CODEC': '3VIX', 'TEMPLATE_IDENTIFIER': '3vix'}, # 10
        {'CODEC': 'AVC', 'TEMPLATE_IDENTIFIER': 'avc'}, # 11
        {'CODEC': 'h264', 'TEMPLATE_IDENTIFIER': 'h264'}, # 12
        {'CODEC': 'HEVC', 'TEMPLATE_IDENTIFIER': 'hevc'}, # 13
        {'CODEC': 'h265', 'TEMPLATE_IDENTIFIER': 'h265'} # 14
    ]
    for zp_vcodec_data in zp_vcodec_data_list:
        add_zp_acodec = ZP_VCODEC(**zp_vcodec_data)
        session.add(add_zp_acodec)
        session.flush()
    session.commit()
    session.close()


def downgrade():
    pass
