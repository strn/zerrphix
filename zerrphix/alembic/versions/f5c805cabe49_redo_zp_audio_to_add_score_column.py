"""Redo ZP_AUDIO to add score column

Revision ID: f5c805cabe49
Revises: 1c079b6b4eff
Create Date: 2017-12-31 20:08:09.750734

"""
from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base, DeferredReflection
from sqlalchemy.orm import sessionmaker, scoped_session


# revision identifiers, used by Alembic.
revision = 'f5c805cabe49'
down_revision = '1c079b6b4eff'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('ZP_ACODEC')
    op.create_table(
        'ZP_ACODEC',
        sa.Column('ID', sa.Integer(), primary_key=True),
        sa.Column('CODEC', sa.String(32), nullable=False),
        sa.Column('SCORE', sa.Integer(), nullable=False),
        sa.Column('TEMPLATE_IDENTIFIER', sa.String(32), nullable=False)
    )
    url = context.config.get_main_option("sqlalchemy.url")
    Base = declarative_base(cls=DeferredReflection)
    class ZP_ACODEC(Base):
        __tablename__ = 'ZP_ACODEC'
    engine = sa.create_engine(url)
    Base.prepare(engine)
    Base.metadata.create_all(engine)
    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()
    zp_acodec_data_list = [
        {'SCORE': 1200, 'CODEC': 'DTS', 'TEMPLATE_IDENTIFIER': 'dts'},
        {'SCORE': 400, 'CODEC': 'MPEG 1/2 Layer 2', 'TEMPLATE_IDENTIFIER': 'mpeg_l2'},
        {'SCORE': 900, 'CODEC': 'AC3', 'TEMPLATE_IDENTIFIER': 'ac3'},
        {'SCORE': 500, 'CODEC': 'MP3', 'TEMPLATE_IDENTIFIER': 'mp3'},
        {'SCORE': 1100, 'CODEC': 'AAC', 'TEMPLATE_IDENTIFIER': 'aac'},
        {'SCORE': 1500, 'CODEC': 'PCM', 'TEMPLATE_IDENTIFIER': 'pcm'},
        {'SCORE': 700, 'CODEC': 'Vorbis', 'TEMPLATE_IDENTIFIER': 'vorbis'},
        {'SCORE': 800, 'CODEC': 'Flac', 'TEMPLATE_IDENTIFIER': 'flac'},
        {'SCORE': 1300, 'CODEC': 'TrueHD', 'TEMPLATE_IDENTIFIER': 'truehd'},
        {'SCORE': 200, 'CODEC': 'Microsoft GSM Audio', 'TEMPLATE_IDENTIFIER': 'gsm'},
        {'SCORE': 1400, 'CODEC': 'DTS_HD', 'TEMPLATE_IDENTIFIER': 'dtshd'},
        {'SCORE': 1000, 'CODEC': 'AC3+', 'TEMPLATE_IDENTIFIER': 'ac3+'},
        {'SCORE': 600, 'CODEC': 'WMA', 'TEMPLATE_IDENTIFIER': 'wma'},
        {'SCORE': 300, 'CODEC': 'MPEG 1/2 Layer 1', 'TEMPLATE_IDENTIFIER': 'mpeg_l1'},
        {'SCORE': 100, 'CODEC': 'GSM610', 'TEMPLATE_IDENTIFIER': 'gsm610'},  # 15
    ]
    for zp_acodec_data in zp_acodec_data_list:
        add_zp_acodec = ZP_ACODEC(**zp_acodec_data)
        session.add(add_zp_acodec)
        session.flush()
    session.commit()
    session.close()


def downgrade():
    pass
