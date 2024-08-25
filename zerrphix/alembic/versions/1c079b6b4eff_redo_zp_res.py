"""Redo ZP_RES

Revision ID: 1c079b6b4eff
Revises: c640c1ca3402
Create Date: 2017-12-30 18:44:34.368164

"""
from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base, DeferredReflection
from sqlalchemy.orm import sessionmaker, scoped_session


# revision identifiers, used by Alembic.
revision = '1c079b6b4eff'
down_revision = 'c640c1ca3402'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('ZP_RES')
    op.create_table(
        'ZP_RES',
        sa.Column('ID', sa.Integer(), primary_key=True),
        sa.Column('RES', sa.Integer(), nullable=False),
        sa.Column('SCORE', sa.Integer(), nullable=False),
        sa.Column('MIN_WIDTH', sa.Integer(), nullable=False),
        sa.Column('MAX_WIDTH', sa.Integer(), nullable=False),
        sa.Column('MIN_HEIGHT', sa.Integer(), nullable=False),
        sa.Column('MAX_HEIGHT', sa.Integer(), nullable=False),
        sa.Column('TEMPLATE_IDENTIFIER', sa.String(8), nullable=False)
    )
    url = context.config.get_main_option("sqlalchemy.url")
    #DBSession.configure(bind=engine)
    Base = declarative_base(cls=DeferredReflection)
    class ZP_RES(Base):
        __tablename__ = 'ZP_RES'
    class ZP_FILM_FILEFOLDER_SCORE(Base):
        __tablename__ = 'ZP_FILM_FILEFOLDER_SCORE'
    engine = sa.create_engine(url)
    Base.prepare(engine)
    Base.metadata.create_all(engine)
    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()
    session.flush()
    # http://www.equasys.de/standardresolution.html
    zp_res_data_list = [
        {'RES': 288, 'TEMPLATE_IDENTIFIER': '288', 'SCORE': 2, 'MIN_WIDTH': 0, 'MAX_WIDTH': 780, 'MIN_HEIGHT': 0, 'MAX_HEIGHT': 340},  # 288
        {'RES': 352, 'TEMPLATE_IDENTIFIER': '352', 'SCORE': 3, 'MIN_WIDTH': 440, 'MAX_WIDTH': 955, 'MIN_HEIGHT': 320, 'MAX_HEIGHT': 360},  # 352
        {'RES': 368, 'TEMPLATE_IDENTIFIER': '368', 'SCORE': 4, 'MIN_WIDTH': 492, 'MAX_WIDTH': 1000, 'MIN_HEIGHT': 360, 'MAX_HEIGHT': 376},  # 368
        {'RES': 384, 'TEMPLATE_IDENTIFIER': '384', 'SCORE': 5, 'MIN_WIDTH': 500, 'MAX_WIDTH': 1050, 'MIN_HEIGHT': 376, 'MAX_HEIGHT': 392},  # 384
        {'RES': 400, 'TEMPLATE_IDENTIFIER': '400', 'SCORE': 6, 'MIN_WIDTH': 550, 'MAX_WIDTH': 1090, 'MIN_HEIGHT': 370, 'MAX_HEIGHT': 440},  # 400
        {'RES': 480, 'TEMPLATE_IDENTIFIER': '480', 'SCORE': 7, 'MIN_WIDTH': 480, 'MAX_WIDTH': 1310, 'MIN_HEIGHT': 440, 'MAX_HEIGHT': 528},  # 480
        {'RES': 576, 'TEMPLATE_IDENTIFIER': '576', 'SCORE': 8, 'MIN_WIDTH': 544, 'MAX_WIDTH': 1600, 'MIN_HEIGHT': 528, 'MAX_HEIGHT': 648},  # 576
        {'RES': 720, 'TEMPLATE_IDENTIFIER': '720', 'SCORE': 16, 'MIN_WIDTH': 850, 'MAX_WIDTH': 2000, 'MIN_HEIGHT': 450, 'MAX_HEIGHT': 1100},  # 720
        {'RES': 1080,'TEMPLATE_IDENTIFIER': '1080','SCORE': 24, 'MIN_WIDTH': 1400, 'MAX_WIDTH': 3000, 'MIN_HEIGHT': 750, 'MAX_HEIGHT': 1620},  # 1080
        {'RES': 2160,'TEMPLATE_IDENTIFIER': '2160','SCORE': 32, 'MIN_WIDTH': 3200, 'MAX_WIDTH': 4400, 'MIN_HEIGHT': 1620, 'MAX_HEIGHT': 3240},  # UHD
        {'RES': 4320,'TEMPLATE_IDENTIFIER': '4320','SCORE': 40, 'MIN_WIDTH': 4000, 'MAX_WIDTH': 8800, 'MIN_HEIGHT': 3000, 'MAX_HEIGHT': 5000}  # 8k
    ]
    for zp_res_data in zp_res_data_list:
        add_zp_acodec = ZP_RES(**zp_res_data)
        session.add(add_zp_acodec)
        session.flush()
    session.query(ZP_FILM_FILEFOLDER_SCORE).delete()
    session.commit()
    session.close()

def downgrade():
    pass
