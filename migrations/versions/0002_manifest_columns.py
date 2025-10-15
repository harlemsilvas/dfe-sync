"""manifest columns on dfe_documentos"""
from alembic import op
import sqlalchemy as sa

revision = "0002_manifest_columns"; down_revision = "0001_init"; branch_labels=None; depends_on=None

def upgrade():
    op.add_column("dfe_documentos", sa.Column("manifest_tp", sa.String(6)))
    op.add_column("dfe_documentos", sa.Column("manifest_nseq", sa.Integer))
    op.add_column("dfe_documentos", sa.Column("manifest_cstat", sa.String(6)))
    op.add_column("dfe_documentos", sa.Column("manifest_xmotivo", sa.Text))
    op.add_column("dfe_documentos", sa.Column("manifest_xml_path", sa.Text))
    op.add_column("dfe_documentos", sa.Column("manifest_updated_at", sa.DateTime))

def downgrade():
    op.drop_column("dfe_documentos", "manifest_updated_at")
    op.drop_column("dfe_documentos", "manifest_xml_path")
    op.drop_column("dfe_documentos", "manifest_xmotivo")
    op.drop_column("dfe_documentos", "manifest_cstat")
    op.drop_column("dfe_documentos", "manifest_nseq")
    op.drop_column("dfe_documentos", "manifest_tp")
