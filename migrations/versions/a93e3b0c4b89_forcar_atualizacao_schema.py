

from alembic import op
import sqlalchemy as sa


revision = 'a93e3b0c4b89'
down_revision = '4f2094fe7647'
branch_labels = None
depends_on = None

def upgrade():
    # Exemplo: adicionar coluna monitorada
    op.add_column('empresas', sa.Column('monitorada', sa.Boolean(), nullable=False, server_default='false'))
    
    # Exemplo: criar tabela operacoes_pendentes
    op.create_table('operacoes_pendentes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), sa.ForeignKey('empresas.id'), nullable=False),
        sa.Column('tipo_operacao', sa.String(50), nullable=False),
        sa.Column('dados_payload', sa.JSON(), nullable=True),
        sa.Column('tentativas', sa.Integer(), default=0),
        sa.Column('ultima_tentativa', sa.DateTime(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_operacoes_empresa', 'operacoes_pendentes', ['empresa_id'])

def downgrade():
    op.drop_index('ix_operacoes_empresa', table_name='operacoes_pendentes')
    op.drop_table('operacoes_pendentes')
    op.drop_column('empresas', 'monitorada')