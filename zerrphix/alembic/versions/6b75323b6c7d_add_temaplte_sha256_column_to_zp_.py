"""Add temaplte_sha256 column to ZP_TEMPLATE

Revision ID: 6b75323b6c7d
Revises: 
Create Date: 2017-12-23 13:17:58.204125

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6b75323b6c7d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('ZP_TEMPLATE', sa.Column('CURRENT_SHA256', sa.String(64)))


def downgrade():
    op.drop_column('ZP_TEMPLATE', 'CURRENT_SHA256')
