"""merge certificados migration

Revision ID: 5587490d1d7e
Revises: 0002_manifest_columns, add_certificados_001
Create Date: 2025-11-13 10:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5587490d1d7e'
down_revision = ('0002_manifest_columns', 'add_certificados_001')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass