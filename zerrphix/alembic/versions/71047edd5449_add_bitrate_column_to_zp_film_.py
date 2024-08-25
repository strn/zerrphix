"""Add BIT_RATE column to ZP_FILM_FILEFOLDER_AUIDO_METADATA, Add BIT_RATE, FRAME_RATE, ASPECT_RATIO columns to
ZP_FILM_FILEFOLDER_VIDEO_METADATA

Revision ID: 71047edd5449
Revises: 6b75323b6c7d
Create Date: 2017-12-26 09:45:06.838536

"""
from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base, DeferredReflection
from sqlalchemy.orm import sessionmaker, scoped_session

# revision identifiers, used by Alembic.
revision = '71047edd5449'
down_revision = '6b75323b6c7d'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('ZP_ACODEC')
    op.drop_column('ZP_FILM_FILEFOLDER_VIDEO_METADATA', 'ASPECT_RATIO')
    op.add_column('ZP_FILM_FILEFOLDER_AUIDO_METADATA', sa.Column('BIT_RATE', sa.String(16), nullable=False))
    op.add_column('ZP_FILM_FILEFOLDER_VIDEO_METADATA', sa.Column('BIT_RATE', sa.String(16), nullable=False))
    op.add_column('ZP_FILM_FILEFOLDER_VIDEO_METADATA', sa.Column('ASPECT_RATIO', sa.String(32), nullable=False))
    op.add_column('ZP_FILM_FILEFOLDER_VIDEO_METADATA', sa.Column('DISPLAY_ASPECT_RATIO', sa.String(32), nullable=False))
    op.create_table(
        'ZP_ACODEC',
        sa.Column('ID', sa.Integer(), primary_key=True),
        sa.Column('CODEC', sa.String(32), nullable=False),
        sa.Column('TEMPLATE_IDENTIFIER', sa.String(32), nullable=False)
    )
    url = context.config.get_main_option("sqlalchemy.url")
    Base = declarative_base(cls=DeferredReflection)
    class ZP_FILM_FILEFOLDER_AUIDO_METADATA(Base):
        __tablename__ = 'ZP_FILM_FILEFOLDER_AUIDO_METADATA'
    class ZP_FILM_FILEFOLDER_TEXT_METADATA(Base):
        __tablename__ = 'ZP_FILM_FILEFOLDER_TEXT_METADATA'
    class ZP_FILM_FILEFOLDER_VIDEO_METADATA(Base):
        __tablename__ = 'ZP_FILM_FILEFOLDER_VIDEO_METADATA'
    class ZP_ACODEC(Base):
        __tablename__ = 'ZP_ACODEC'
    engine = sa.create_engine(url)
    Base.prepare(engine)
    Base.metadata.create_all(engine)
    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()
    session.query(ZP_FILM_FILEFOLDER_AUIDO_METADATA).delete()
    session.query(ZP_FILM_FILEFOLDER_VIDEO_METADATA).delete()
    session.query(ZP_FILM_FILEFOLDER_TEXT_METADATA).delete()
    session.flush()
    zp_acodec_data_list = [
        {'CODEC': 'DTS', 'TEMPLATE_IDENTIFIER': 'dts'},
        {'CODEC': 'MPEG 1/2 Layer 2', 'TEMPLATE_IDENTIFIER': 'mpeg_l2'},
        {'CODEC': 'AC3', 'TEMPLATE_IDENTIFIER': 'ac3'},
        {'CODEC': 'MP3', 'TEMPLATE_IDENTIFIER': 'mp3'},
        {'CODEC': 'AAC', 'TEMPLATE_IDENTIFIER': 'aac'},
        {'CODEC': 'PCM', 'TEMPLATE_IDENTIFIER': 'pcm'},
        {'CODEC': 'Vorbis', 'TEMPLATE_IDENTIFIER': 'vorbis'},
        {'CODEC': 'Flac', 'TEMPLATE_IDENTIFIER': 'flac'},
        {'CODEC': 'TrueHD', 'TEMPLATE_IDENTIFIER': 'truehd'},
        {'CODEC': 'Microsoft GSM Audio', 'TEMPLATE_IDENTIFIER': 'gsm'},
        {'CODEC': 'DTS_HD', 'TEMPLATE_IDENTIFIER': 'dtshd'},
        {'CODEC': 'AC3+', 'TEMPLATE_IDENTIFIER': 'ac3+'},
        {'CODEC': 'WMA', 'TEMPLATE_IDENTIFIER': 'wma'},
        {'CODEC': 'MPEG 1/2 Layer 1', 'TEMPLATE_IDENTIFIER': 'mpeg_l1'}
    ]
    for zp_acodec_data in zp_acodec_data_list:
        add_zp_acodec = ZP_ACODEC(**zp_acodec_data)
        session.add(add_zp_acodec)
        session.flush()
    session.commit()
    session.close()


def downgrade():
    op.drop_column('ZP_FILM_FILEFOLDER_AUIDO_METADATA', 'BIT_RATE')
    op.drop_column('ZP_FILM_FILEFOLDER_VIDEO_METADATA', 'BIT_RATE')
    op.drop_column('ZP_FILM_FILEFOLDER_VIDEO_METADATA', 'ASPECT_RATIO')
    op.add_column('ZP_FILM_FILEFOLDER_VIDEO_METADATA', sa.Column('ASPECT_RATIO', sa.TEXT()))
    op.drop_column('ZP_FILM_FILEFOLDER_VIDEO_METADATA', 'DISPLAY_ASPECT_RATIO')
