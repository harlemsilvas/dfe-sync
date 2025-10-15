"""init"""
from alembic import op
import sqlalchemy as sa
revision = "0001_init"; down_revision = None; branch_labels=None; depends_on=None

def upgrade():
    op.create_table("empresas",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("cnpj", sa.String(14), nullable=False, unique=True),
        sa.Column("razao_social", sa.String(200), nullable=False),
        sa.Column("ambiente", sa.String(10), nullable=False, server_default="HOMOLOG"),
        sa.Column("ativo", sa.Integer, nullable=False, server_default="1"),
    )
    op.create_table("certificados",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("empresa_id", sa.Integer, sa.ForeignKey("empresas.id"), nullable=False),
        sa.Column("tipo", sa.String(2), nullable=False, server_default="A1"),
        sa.Column("pfx_path", sa.Text, nullable=False),
        sa.Column("senha_cripto", sa.Text, nullable=False),
    )
    op.create_table("cursor_dfe",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("empresa_id", sa.Integer, sa.ForeignKey("empresas.id"), nullable=False, unique=True),
        sa.Column("ultimo_nsu", sa.String(20), nullable=False, server_default="000000000000000"),
        sa.Column("max_nsu", sa.String(20), nullable=False, server_default="000000000000000"),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_table("dfe_documentos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("empresa_id", sa.Integer, sa.ForeignKey("empresas.id"), nullable=False),
        sa.Column("nsu", sa.String(20), nullable=False),
        sa.Column("schema", sa.String(30), nullable=False),
        sa.Column("chave", sa.String(44)),
        sa.Column("caminho_xml", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_dfe_empresa_nsu", "dfe_documentos", ["empresa_id","nsu"])

def downgrade():
    op.drop_index("ix_dfe_empresa_nsu", table_name="dfe_documentos")
    op.drop_table("dfe_documentos")
    op.drop_table("cursor_dfe")
    op.drop_table("certificados")
    op.drop_table("empresas")