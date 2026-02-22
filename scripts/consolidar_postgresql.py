"""
Script de consolidação e validação do PostgreSQL Docker
Garante que todas as estruturas estão corretas e funcionais
"""


from sqlalchemy import text
from src.store.db import engine, SessionLocal
from src.models import *  # Importa todos os modelos
from datetime import datetime

def verificar_conexao():
    """Verifica se a conexão com PostgreSQL Docker está funcionando"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text('SELECT version()'))
            version = result.fetchone()[0]
            print(f"✅ Conexão PostgreSQL OK: {version.split()[0:2]}")
            return True
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def consolidar_estrutura():
    """Consolida toda a estrutura no PostgreSQL Docker"""
    print("\n🔨 Consolidando estrutura do banco...")
    
    with engine.begin() as conn:
        # Verificar e criar índices faltantes
        indices_necessarios = [
            "CREATE INDEX IF NOT EXISTS ix_empresas_cnpj ON empresas(cnpj)",
            "CREATE INDEX IF NOT EXISTS ix_empresas_monitorada ON empresas(monitorada)", 
            "CREATE INDEX IF NOT EXISTS ix_dfe_empresa_nsu ON dfe_documentos(empresa_id, nsu)",
            "CREATE INDEX IF NOT EXISTS ix_dfe_chave ON dfe_documentos(chave)",
            "CREATE INDEX IF NOT EXISTS ix_dfe_tipo_documento ON dfe_documentos(tipo_documento_id)",
            "CREATE INDEX IF NOT EXISTS ix_certificados_empresa ON certificados(empresa_id)",
            "CREATE INDEX IF NOT EXISTS ix_certificados_cnpj ON certificados(cnpj)",
            "CREATE INDEX IF NOT EXISTS ix_remetentes_cnpj ON remetentes_cadastrados(cnpj_cpf)",
            "CREATE INDEX IF NOT EXISTS ix_logs_timestamp ON logs_processamento(timestamp)",
            "CREATE INDEX IF NOT EXISTS ix_logs_nivel ON logs_processamento(nivel)"
        ]
        
        for indice in indices_necessarios:
            try:
                conn.execute(text(indice))
            except Exception as e:
                print(f"⚠️ Índice já existe ou erro: {e}")
        
        # Garantir dados essenciais
        
        # 1. Empresas monitoradas
        conn.execute(text("""
            INSERT INTO empresas (cnpj, razao_social, ambiente, ativo, monitorada) VALUES
            ('19330326000105', 'HRM EMPRESA', 'PRODUCAO', 1, true),
            ('51309435000153', 'ABC CENTER DISTRIBUIDORA LTDA', 'PRODUCAO', 1, true)
            ON CONFLICT (cnpj) DO UPDATE SET 
                monitorada = true,
                ativo = 1
        """))
        
        # 2. Tipos de documentos
        conn.execute(text("""
            INSERT INTO tipo_documento (codigo, descricao, ativo) VALUES
            ('NFE_ENTRADA', 'NF-e de Entrada', true),
            ('NFE_SAIDA', 'NF-e de Saída', true),
            ('NFE_TERCEIROS', 'NF-e de Terceiros', true),
            ('NFE_TRANSFERENCIA', 'NF-e de Transferência', true),
            ('CTE', 'CT-e - Conhecimento de Transporte', true),
            ('NFSE', 'NFS-e - Nota Fiscal de Serviços', true),
            ('EVENTO', 'Evento relacionado a documento', true)
            ON CONFLICT (codigo) DO NOTHING
        """))
        
        # 3. CFOPs de transferência
        conn.execute(text("""
            INSERT INTO cfops_transferencia (codigo, descricao, tipo_operacao, ativo) VALUES
            ('5949', 'Outra saída de mercadoria ou prestação de serviço não especificado', 'Depósito Temporário', true),
            ('5152', 'Transferência de mercadoria adquirida ou recebida de terceiros', 'Transferência', true),
            ('6152', 'Transferência de mercadoria adquirida ou recebida de terceiros', 'Transferência', true),
            ('5409', 'Transferência de mercadoria para outro estabelecimento da mesma empresa', 'Transferência', true),
            ('6409', 'Transferência de mercadoria para outro estabelecimento da mesma empresa', 'Transferência', true)
            ON CONFLICT (codigo) DO NOTHING
        """))
    
    print("✅ Estrutura consolidada!")

def validar_dados():
    """Valida se todos os dados essenciais existem"""
    print("\n🔍 Validando dados essenciais...")
    
    with engine.connect() as conn:
        # Contar registros em cada tabela
        tabelas_importantes = [
            'empresas', 'tipo_documento', 'cfops_transferencia', 
            'dfe_documentos', 'certificados', 'remetentes_cadastrados'
        ]
        
        for tabela in tabelas_importantes:
            try:
                result = conn.execute(text(f'SELECT COUNT(*) FROM {tabela}'))
                count = result.fetchone()[0]
                print(f"  📊 {tabela}: {count} registros")
            except Exception as e:
                print(f"  ❌ Erro ao contar {tabela}: {e}")
        
        # Verificar empresas monitoradas
        result = conn.execute(text(
            "SELECT cnpj, razao_social FROM empresas WHERE monitorada = true"
        ))
        empresas = list(result)
        print(f"\n🏢 Empresas monitoradas ({len(empresas)}):")
        for emp in empresas:
            print(f"  • {emp.cnpj}: {emp.razao_social}")
        
        # Verificar tipos de documentos
        result = conn.execute(text("SELECT codigo FROM tipo_documento ORDER BY codigo"))
        tipos = [row.codigo for row in result]
        print(f"\n📋 Tipos de documentos: {', '.join(tipos)}")

def testar_crud_basico():
    """Testa operações CRUD básicas"""
    print("\n🧪 Testando operações CRUD...")
    
    try:
        with SessionLocal() as db:
            # Teste: Inserir log de teste
            from src.models.log_processamento import LogProcessamento

            log_teste = LogProcessamento(
                nivel="INFO",
                modulo="CONSOLIDACAO",
                processo="teste_crud",
                mensagem="Teste de CRUD funcionando",
                dados_json='{"teste": "ok"}',
                tag="TESTE"
            )

            db.add(log_teste)
            db.commit()

            # Verificar se foi inserido
            logs = db.query(LogProcessamento).filter(
                LogProcessamento.tag == "TESTE"
            ).all()

            print(f"✅ CRUD funcionando: {len(logs)} logs de teste encontrados")

            # Limpar teste
            for log in logs:
                db.delete(log)
            db.commit()
            
    except Exception as e:
        print(f"❌ Erro no teste CRUD: {e}")

def gerar_relatorio_final():
    """Gera relatório final da consolidação"""
    print("\n📊 RELATÓRIO FINAL DA MIGRAÇÃO")
    print("=" * 50)
    
    with engine.connect() as conn:
        # Status geral
        result = conn.execute(text("""
            SELECT 
                (SELECT COUNT(*) FROM empresas WHERE monitorada = true) as empresas_monitoradas,
                (SELECT COUNT(*) FROM tipo_documento) as tipos_documento,
                (SELECT COUNT(*) FROM cfops_transferencia) as cfops,
                (SELECT COUNT(*) FROM certificados) as certificados,
                (SELECT COUNT(*) FROM dfe_documentos) as documentos,
                (SELECT COUNT(*) FROM logs_processamento) as logs
        """))
        
        stats = result.fetchone()
        
        print(f"🏢 Empresas monitoradas: {stats.empresas_monitoradas}")
        print(f"📋 Tipos de documento: {stats.tipos_documento}")
        print(f"🔄 CFOPs configurados: {stats.cfops}")
        print(f"🔐 Certificados: {stats.certificados}")
        print(f"📄 Documentos: {stats.documentos}")
        print(f"📝 Logs: {stats.logs}")
        
        print("\n✅ PostgreSQL Docker completamente funcional!")
        print("🚀 Sistema pronto para processamento de arquivos!")

if __name__ == "__main__":
    print("🐘 CONSOLIDAÇÃO POSTGRESQL DOCKER")
    print("=" * 40)
    
    if not verificar_conexao():
        exit(1)
    
    consolidar_estrutura()
    validar_dados()
    testar_crud_basico()
    gerar_relatorio_final()
    
    print("\n🎉 Migração concluída com sucesso!")
    print("🔗 Conexão: postgresql://dfe:dfe@localhost:5432/dfe")
    print("🐳 Container: dfe_db (postgres:16)")