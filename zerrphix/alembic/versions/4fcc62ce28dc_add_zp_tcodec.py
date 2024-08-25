"""Add ZP_TCODEC

Revision ID: 4fcc62ce28dc
Revises: 49823d4740a2
Create Date: 2017-12-30 15:38:55.571796

"""
from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base, DeferredReflection
from sqlalchemy.orm import sessionmaker, scoped_session


# revision identifiers, used by Alembic.
revision = '4fcc62ce28dc'
down_revision = '49823d4740a2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ZP_TCODEC',
        sa.Column('ID', sa.Integer(), primary_key=True),
        sa.Column('CODEC', sa.String(32), nullable=False),
        sa.Column('TEMPLATE_IDENTIFIER', sa.String(32), nullable=False)
    )
    op.drop_column('ZP_FILM_FILEFOLDER_TEXT_METADATA', 'FORMAT')
    url = context.config.get_main_option("sqlalchemy.url")
    #DBSession.configure(bind=engine)
    Base = declarative_base(cls=DeferredReflection)
    class ZP_TCODEC(Base):
        __tablename__ = 'ZP_TCODEC'
    engine = sa.create_engine(url)
    Base.prepare(engine)
    Base.metadata.create_all(engine)
    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()
    session.flush()
    zp_vcodec_data_list = [
        {'CODEC': 'ASS', 'TEMPLATE_IDENTIFIER': 'ass'}, # 1
        {'CODEC': 'DVB Subtitle', 'TEMPLATE_IDENTIFIER': 'dvb'}, # 2
        {'CODEC': 'PGS', 'TEMPLATE_IDENTIFIER': 'pgs'}, # 3
        {'CODEC': 'SSA', 'TEMPLATE_IDENTIFIER': 'ssa'}, # 4
        {'CODEC': 'Timed Text', 'TEMPLATE_IDENTIFIER': 'tt'}, # 5
        {'CODEC': 'UTF-8', 'TEMPLATE_IDENTIFIER': 'utf8'}, # 6
        {'CODEC': 'VobSub', 'TEMPLATE_IDENTIFIER': 'vobsub'}, # 7
        {'CODEC': 'KATE', 'TEMPLATE_IDENTIFIER': 'kate'}, # 8
        {'CODEC': 'Bitmap', 'TEMPLATE_IDENTIFIER': 'bitmap'}, # 9
        {'CODEC': 'USF', 'TEMPLATE_IDENTIFIER': 'usf'}, # 10
        {'CODEC': 'TEXTST', 'TEMPLATE_IDENTIFIER': 'textst'}, # 11
        {'CODEC': 'Apple text', 'TEMPLATE_IDENTIFIER': 'appletext'}, # 12
        {'CODEC': 'TTML', 'TEMPLATE_IDENTIFIER': 'ttml'}, # 13
        {'CODEC': 'Encrypted', 'TEMPLATE_IDENTIFIER': 'encrypted'}, # 14
        {'CODEC': 'DivX Subtitle', 'TEMPLATE_IDENTIFIER': 'divxsubtitle'}, # 15
        {'CODEC': 'Run-Length Encoded', 'TEMPLATE_IDENTIFIER': 'rlesubs'}, # 16
        {'CODEC': 'EIA-708', 'TEMPLATE_IDENTIFIER': 'eia708'}, # 17
        {'CODEC': 'EIA-608', 'TEMPLATE_IDENTIFIER': 'eia608'} # 18
    ]
    for zp_vcodec_data in zp_vcodec_data_list:
        add_zp_acodec = ZP_TCODEC(**zp_vcodec_data)
        session.add(add_zp_acodec)
        session.flush()
    session.commit()
    session.close()


def downgrade():
    op.drop_table('ZP_TCODEC')
    op.add_column('ZP_FILM_FILEFOLDER_TEXT_METADATA', sa.Column('FORMAT', sa.String(32), nullable=False))
