"""Add width and height columns to ZP_FILM_FILEFOLDER_VIDEO_METADATA

Revision ID: d9d26cdee08b
Revises: c0d1fa61980d
Create Date: 2018-01-06 17:19:32.422851

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd9d26cdee08b'
down_revision = 'c0d1fa61980d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('ZP_FILM_FILEFOLDER_VIDEO_METADATA', sa.Column('WIDTH', sa.Integer(), nullable=False))
    op.add_column('ZP_FILM_FILEFOLDER_VIDEO_METADATA', sa.Column('HEIGHT', sa.Integer(), nullable=False))


def downgrade():
    op.drop_column('ZP_FILM_FILEFOLDER_VIDEO_METADATA', 'WIDTH')
    op.drop_column('ZP_FILM_FILEFOLDER_VIDEO_METADATA', 'HEIGHT')
