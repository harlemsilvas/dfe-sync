# Determinar URL do banco
# db_url = os.environ.get("DB_URL") or args.db_url or getattr(settings, "DB_URL", None)
#!/usr/bin/env python3
"""
Script para popular a tabela cfops_transferencia com CFOPs comuns.
Campos da tabela: id, codigo, descricao, tipo_operacao, ativo

Uso:
    python scripts/popular_cfops.py [--dry-run] [--db-url URL]
"""

import sys
import os
from pathlib import Path

# Adicionar raiz do projeto ao path para imports
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from src.settings import settings
from src.models import CfopTransferencia  # Ajuste conforme seu modelo real
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# =============================================================================
# MAPEAMENTO: CFOP → TIPO DE OPERAÇÃO
# =============================================================================

def get_tipo_operacao(codigo: str) -> str:
    """
    Determina o tipo de operação baseado no primeiro dígito do CFOP:
    1, 2 = Entrada (E)
    3    = Serviços (S)
    5, 6 = Saída (S)
    7    = Transferência (T)
    Outros = Transferência (T) por padrão
    """
    primeiro_digito = codigo[0] if codigo else "0"
    
    if primeiro_digito in ["1", "2"]:
        return "E"  # Entrada
    elif primeiro_digito == "3":
        return "S"  # Serviços
    elif primeiro_digito in ["5", "6"]:
        return "S"  # Saída
    else:
        return "T"  # Transferência (default)


# =============================================================================
# LISTA DE CFOPs COMUNS COM TIPO DE OPERAÇÃO
# =============================================================================

CFOPS_COMUNS = [
    # === ENTRADA (tipo_operacao = "E") ===
    {"codigo": "1101", "descricao": "Entrada para industrialização de mercadoria comprada", "tipo_operacao": "E"},
    {"codigo": "1102", "descricao": "Entrada para comercialização de mercadoria comprada", "tipo_operacao": "E"},
    {"codigo": "1111", "descricao": "Entrada para industrialização de mercadoria recebida de terceiros", "tipo_operacao": "E"},
    {"codigo": "1113", "descricao": "Entrada para comercialização de mercadoria recebida de terceiros", "tipo_operacao": "E"},
    {"codigo": "1116", "descricao": "Entrada de mercadoria para exposição ou demonstração", "tipo_operacao": "E"},
    {"codigo": "1117", "descricao": "Entrada de mercadoria para doação", "tipo_operacao": "E"},
    {"codigo": "1118", "descricao": "Entrada de mercadoria para bonificação", "tipo_operacao": "E"},
    {"codigo": "1120", "descricao": "Entrada de mercadoria para industrialização sob encomenda", "tipo_operacao": "E"},
    {"codigo": "1121", "descricao": "Entrada de mercadoria para industrialização por conta e ordem do remetente", "tipo_operacao": "E"},
    {"codigo": "1122", "descricao": "Entrada de mercadoria para industrialização por conta e ordem do destinatário", "tipo_operacao": "E"},
    {"codigo": "1124", "descricao": "Entrada para industrialização em regime de drawback", "tipo_operacao": "E"},
    {"codigo": "1126", "descricao": "Entrada de mercadoria para depósito fechado", "tipo_operacao": "E"},
    {"codigo": "1128", "descricao": "Entrada de mercadoria para consumo", "tipo_operacao": "E"},
    {"codigo": "1151", "descricao": "Transferência de mercadoria adquirida ou recebida de terceiros", "tipo_operacao": "E"},
    {"codigo": "1152", "descricao": "Transferência de produção do estabelecimento", "tipo_operacao": "E"},
    {"codigo": "1201", "descricao": "Devolução de venda de produção do estabelecimento", "tipo_operacao": "E"},
    {"codigo": "1202", "descricao": "Devolução de venda de mercadoria adquirida ou recebida de terceiros", "tipo_operacao": "E"},
    {"codigo": "1251", "descricao": "Compra de energia elétrica para industrialização", "tipo_operacao": "E"},
    {"codigo": "1252", "descricao": "Compra de energia elétrica para comercialização", "tipo_operacao": "E"},
    {"codigo": "1253", "descricao": "Compra de energia elétrica para consumo", "tipo_operacao": "E"},
    {"codigo": "1301", "descricao": "Aquisição de serviço de comunicação para execução de serviço da mesma natureza", "tipo_operacao": "E"},
    {"codigo": "1302", "descricao": "Aquisição de serviço de comunicação por estabelecimento de produção industrial", "tipo_operacao": "E"},
    {"codigo": "1351", "descricao": "Aquisição de serviço de transporte para execução de serviço da mesma natureza", "tipo_operacao": "E"},
    {"codigo": "1352", "descricao": "Aquisição de serviço de transporte por estabelecimento industrial", "tipo_operacao": "E"},
    {"codigo": "1401", "descricao": "Entrada de mercadoria em regime de consignação mercantil", "tipo_operacao": "E"},
    {"codigo": "1403", "descricao": "Entrada de mercadoria recebida em consignação mercantil para industrialização ou comercialização", "tipo_operacao": "E"},
    {"codigo": "1406", "descricao": "Entrada de mercadoria recebida para depósito fechado", "tipo_operacao": "E"},
    {"codigo": "1407", "descricao": "Entrada de mercadoria para exposição ou demonstração", "tipo_operacao": "E"},
    {"codigo": "1408", "descricao": "Entrada de mercadoria para doação", "tipo_operacao": "E"},
    {"codigo": "1409", "descricao": "Entrada de mercadoria para bonificação", "tipo_operacao": "E"},
    {"codigo": "1411", "descricao": "Entrada de mercadoria para industrialização sob encomenda", "tipo_operacao": "E"},
    {"codigo": "1414", "descricao": "Entrada de mercadoria para industrialização por conta e ordem do remetente", "tipo_operacao": "E"},
    {"codigo": "1415", "descricao": "Entrada de mercadoria para industrialização por conta e ordem do destinatário", "tipo_operacao": "E"},
    {"codigo": "1451", "descricao": "Retorno de mercadoria remetida para industrialização sob encomenda", "tipo_operacao": "E"},
    {"codigo": "1452", "descricao": "Retorno de mercadoria remetida para industrialização por conta e ordem do remetente", "tipo_operacao": "E"},
    {"codigo": "1453", "descricao": "Retorno de mercadoria remetida para industrialização por conta e ordem do destinatário", "tipo_operacao": "E"},
    {"codigo": "1551", "descricao": "Entrada de mercadoria recebida para industrialização com suspensão do ICMS", "tipo_operacao": "E"},
    {"codigo": "1552", "descricao": "Entrada de mercadoria recebida para industrialização com isenção do ICMS", "tipo_operacao": "E"},
    {"codigo": "1553", "descricao": "Entrada de mercadoria recebida para industrialização com diferimento do ICMS", "tipo_operacao": "E"},
    {"codigo": "1651", "descricao": "Compra de combustível ou lubrificante para industrialização", "tipo_operacao": "E"},
    {"codigo": "1652", "descricao": "Compra de combustível ou lubrificante para comercialização", "tipo_operacao": "E"},
    {"codigo": "1653", "descricao": "Compra de combustível ou lubrificante por consumidor ou usuário final", "tipo_operacao": "E"},
    
    # === SAÍDA (tipo_operacao = "S") ===
    {"codigo": "5101", "descricao": "Saída de produção do estabelecimento para industrialização", "tipo_operacao": "S"},
    {"codigo": "5102", "descricao": "Saída de produção do estabelecimento para comercialização", "tipo_operacao": "S"},
    {"codigo": "5103", "descricao": "Saída de produção do estabelecimento para consumo", "tipo_operacao": "S"},
    {"codigo": "5104", "descricao": "Saída para industrialização sob encomenda", "tipo_operacao": "S"},
    {"codigo": "5105", "descricao": "Saída para industrialização por conta e ordem do remetente", "tipo_operacao": "S"},
    {"codigo": "5106", "descricao": "Saída para industrialização por conta e ordem do destinatário", "tipo_operacao": "S"},
    {"codigo": "5109", "descricao": "Saída para industrialização em regime de drawback", "tipo_operacao": "S"},
    {"codigo": "5111", "descricao": "Saída de mercadoria adquirida ou recebida de terceiros para industrialização", "tipo_operacao": "S"},
    {"codigo": "5112", "descricao": "Saída de mercadoria adquirida ou recebida de terceiros para comercialização", "tipo_operacao": "S"},
    {"codigo": "5113", "descricao": "Saída de mercadoria adquirida ou recebida de terceiros para consumo", "tipo_operacao": "S"},
    {"codigo": "5114", "descricao": "Saída de mercadoria para industrialização sob encomenda, do estabelecimento", "tipo_operacao": "S"},
    {"codigo": "5115", "descricao": "Saída de mercadoria para industrialização por conta e ordem do remetente, do estabelecimento", "tipo_operacao": "S"},
    {"codigo": "5116", "descricao": "Saída de mercadoria para industrialização por conta e ordem do destinatário, do estabelecimento", "tipo_operacao": "S"},
    {"codigo": "5117", "descricao": "Saída de mercadoria para industrialização em regime de drawback, do estabelecimento", "tipo_operacao": "S"},
    {"codigo": "5118", "descricao": "Saída de mercadoria adquirida ou recebida de terceiros para exposição ou demonstração", "tipo_operacao": "S"},
    {"codigo": "5119", "descricao": "Saída de mercadoria adquirida ou recebida de terceiros para doação", "tipo_operacao": "S"},
    {"codigo": "5120", "descricao": "Saída de mercadoria adquirida ou recebida de terceiros para bonificação", "tipo_operacao": "S"},
    {"codigo": "5122", "descricao": "Saída de mercadoria adquirida ou recebida de terceiros para demonstração", "tipo_operacao": "S"},
    {"codigo": "5123", "descricao": "Saída de mercadoria adquirida ou recebida de terceiros para industrialização sob encomenda", "tipo_operacao": "S"},
    {"codigo": "5124", "descricao": "Saída de mercadoria adquirida ou recebida de terceiros para industrialização por conta e ordem do remetente", "tipo_operacao": "S"},
    {"codigo": "5125", "descricao": "Saída de mercadoria adquirida ou recebida de terceiros para industrialização por conta e ordem do destinatário", "tipo_operacao": "S"},
    {"codigo": "5129", "descricao": "Saída de mercadoria adquirida ou recebida de terceiros para industrialização em regime de drawback", "tipo_operacao": "S"},
    {"codigo": "5151", "descricao": "Transferência de mercadoria adquirida ou recebida de terceiros", "tipo_operacao": "S"},
    {"codigo": "5152", "descricao": "Transferência de produção do estabelecimento", "tipo_operacao": "S"},
    {"codigo": "5153", "descricao": "Transferência de energia elétrica", "tipo_operacao": "S"},
    {"codigo": "5155", "descricao": "Transferência de mercadoria do estabelecimento", "tipo_operacao": "S"},
    {"codigo": "5156", "descricao": "Transferência de mercadoria para outro estabelecimento da mesma empresa", "tipo_operacao": "S"},
    {"codigo": "5201", "descricao": "Devolução de venda de produção do estabelecimento", "tipo_operacao": "S"},
    {"codigo": "5202", "descricao": "Devolução de venda de mercadoria adquirida ou recebida de terceiros", "tipo_operacao": "S"},
    {"codigo": "5205", "descricao": "Anulação de valor relativo à prestação de serviço de comunicação", "tipo_operacao": "S"},
    {"codigo": "5206", "descricao": "Anulação de valor relativo à prestação de serviço de transporte", "tipo_operacao": "S"},
    {"codigo": "5207", "descricao": "Anulação de valor relativo à venda de energia elétrica", "tipo_operacao": "S"},
    {"codigo": "5208", "descricao": "Devolução de mercadoria utilizada na industrialização", "tipo_operacao": "S"},
    {"codigo": "5251", "descricao": "Saída de mercadoria para industrialização sob encomenda", "tipo_operacao": "S"},
    {"codigo": "5252", "descricao": "Saída de mercadoria para industrialização por conta e ordem do remetente", "tipo_operacao": "S"},
    {"codigo": "5253", "descricao": "Saída de mercadoria para industrialização por conta e ordem do destinatário", "tipo_operacao": "S"},
    {"codigo": "5254", "descricao": "Saída de mercadoria para industrialização em regime de drawback", "tipo_operacao": "S"},
    {"codigo": "5401", "descricao": "Industrialização de mercadoria recebida de terceiros para industrialização sob encomenda", "tipo_operacao": "S"},
    {"codigo": "5402", "descricao": "Industrialização de mercadoria recebida de terceiros para industrialização por conta e ordem do remetente", "tipo_operacao": "S"},
    {"codigo": "5403", "descricao": "Industrialização de mercadoria recebida de terceiros para industrialização por conta e ordem do destinatário", "tipo_operacao": "S"},
    {"codigo": "5405", "descricao": "Industrialização de mercadoria recebida de terceiros para industrialização em regime de drawback", "tipo_operacao": "S"},
    {"codigo": "5551", "descricao": "Venda de mercadoria adquirida ou recebida de terceiros", "tipo_operacao": "S"},
    {"codigo": "5552", "descricao": "Venda de mercadoria adquirida ou recebida de terceiros, em operação com mercadoria sujeita ao regime de substituição tributária", "tipo_operacao": "S"},
    {"codigo": "5601", "descricao": "Transferência de produção do estabelecimento", "tipo_operacao": "S"},
    {"codigo": "5602", "descricao": "Transferência de mercadoria adquirida ou recebida de terceiros", "tipo_operacao": "S"},
    {"codigo": "5603", "descricao": "Devolução de mercadoria adquirida ou recebida de terceiros", "tipo_operacao": "S"},
    {"codigo": "5604", "descricao": "Remessa de mercadoria para industrialização sob encomenda", "tipo_operacao": "S"},
    {"codigo": "5605", "descricao": "Remessa de mercadoria para industrialização por conta e ordem do remetente", "tipo_operacao": "S"},
    {"codigo": "5606", "descricao": "Remessa de mercadoria para industrialização por conta e ordem do destinatário", "tipo_operacao": "S"},
    {"codigo": "5607", "descricao": "Remessa de mercadoria para industrialização em regime de drawback", "tipo_operacao": "S"},
    {"codigo": "5651", "descricao": "Venda de energia elétrica", "tipo_operacao": "S"},
    {"codigo": "5901", "descricao": "Remessa para industrialização por conta e ordem do remetente", "tipo_operacao": "S"},
    {"codigo": "5902", "descricao": "Remessa para industrialização por conta e ordem do destinatário", "tipo_operacao": "S"},
    {"codigo": "5903", "descricao": "Remessa para industrialização em regime de drawback", "tipo_operacao": "S"},
    {"codigo": "5904", "descricao": "Remessa para industrialização sob encomenda", "tipo_operacao": "S"},
    {"codigo": "5910", "descricao": "Lançamento efetuado a título de simples faturamento decorrente de compra para recebimento futuro", "tipo_operacao": "S"},
    {"codigo": "5911", "descricao": "Lançamento efetuado a título de simples faturamento decorrente de venda para entrega futura", "tipo_operacao": "S"},
    {"codigo": "5931", "descricao": "Lançamento efetuado em decorrência de emissão de documento fiscal relativo a operação ou prestação também registrada em equipamento Emissor de Cupom Fiscal - ECF", "tipo_operacao": "S"},
    {"codigo": "5932", "descricao": "Prestação de serviço de transporte", "tipo_operacao": "S"},
    {"codigo": "5933", "descricao": "Prestação de serviço de comunicação", "tipo_operacao": "S"},
    {"codigo": "5934", "descricao": "Saída de mercadoria para venda a consumidor final", "tipo_operacao": "S"},
    {"codigo": "5949", "descricao": "Outra saída de mercadoria ou prestação de serviço não especificado", "tipo_operacao": "S"},
    
    # === TRANSFERÊNCIA INTERESTADUAL (tipo_operacao = "T") ===
    {"codigo": "6101", "descricao": "Transferência de produção do estabelecimento para outro estado", "tipo_operacao": "T"},
    {"codigo": "6102", "descricao": "Transferência de mercadoria adquirida ou recebida de terceiros para outro estado", "tipo_operacao": "T"},
    {"codigo": "6106", "descricao": "Transferência para industrialização por conta e ordem do remetente, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6107", "descricao": "Transferência para industrialização por conta e ordem do destinatário, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6108", "descricao": "Transferência para industrialização em regime de drawback, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6109", "descricao": "Transferência para industrialização sob encomenda, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6151", "descricao": "Transferência de mercadoria adquirida ou recebida de terceiros, destinada a comercialização, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6152", "descricao": "Transferência de produção do estabelecimento, destinada a comercialização, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6153", "descricao": "Transferência de energia elétrica para outro estado", "tipo_operacao": "T"},
    {"codigo": "6154", "descricao": "Transferência de mercadoria para industrialização por conta e ordem do remetente, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6155", "descricao": "Transferência de mercadoria para industrialização por conta e ordem do destinatário, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6156", "descricao": "Transferência de mercadoria para industrialização em regime de drawback, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6157", "descricao": "Transferência de mercadoria para industrialização sob encomenda, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6201", "descricao": "Devolução de venda de produção do estabelecimento para outro estado", "tipo_operacao": "T"},
    {"codigo": "6202", "descricao": "Devolução de venda de mercadoria adquirida ou recebida de terceiros, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6251", "descricao": "Devolução de mercadoria adquirida ou recebida de terceiros, destinada à industrialização, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6401", "descricao": "Industrialização de mercadoria recebida de terceiros, para industrialização sob encomenda, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6402", "descricao": "Industrialização de mercadoria recebida de terceiros, para industrialização por conta e ordem do remetente, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6403", "descricao": "Industrialização de mercadoria recebida de terceiros, para industrialização por conta e ordem do destinatário, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6551", "descricao": "Venda de mercadoria adquirida ou recebida de terceiros, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6552", "descricao": "Venda de mercadoria adquirida ou recebida de terceiros, em operação com mercadoria sujeita ao regime de substituição tributária, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6553", "descricao": "Devolução de mercadoria adquirida ou recebida de terceiros, em operação com mercadoria sujeita ao regime de substituição tributária, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6603", "descricao": "Devolução de mercadoria adquirida ou recebida de terceiros, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6651", "descricao": "Venda de energia elétrica para outro estado", "tipo_operacao": "T"},
    {"codigo": "6901", "descricao": "Remessa para industrialização por conta e ordem do remetente, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6902", "descricao": "Remessa para industrialização por conta e ordem do destinatário, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6903", "descricao": "Remessa para industrialização em regime de drawback, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6904", "descricao": "Remessa para industrialização sob encomenda, para outro estado", "tipo_operacao": "T"},
    {"codigo": "6949", "descricao": "Outra saída de mercadoria ou prestação de serviço não especificado, para outro estado", "tipo_operacao": "T"},
    
    # === CFOPs DE SERVIÇOS (tipo_operacao = "S") ===
    {"codigo": "3101", "descricao": "Prestação de serviço de transporte para execução de serviço da mesma natureza", "tipo_operacao": "S"},
    {"codigo": "3102", "descricao": "Prestação de serviço de transporte por estabelecimento industrial", "tipo_operacao": "S"},
    {"codigo": "3103", "descricao": "Prestação de serviço de transporte por estabelecimento comercial", "tipo_operacao": "S"},
    {"codigo": "3104", "descricao": "Prestação de serviço de transporte por estabelecimento de prestador de serviços", "tipo_operacao": "S"},
    {"codigo": "3201", "descricao": "Prestação de serviço de comunicação para execução de serviço da mesma natureza", "tipo_operacao": "S"},
    {"codigo": "3202", "descricao": "Prestação de serviço de comunicação por estabelecimento de produção industrial", "tipo_operacao": "S"},
    {"codigo": "3203", "descricao": "Prestação de serviço de comunicação por estabelecimento comercial", "tipo_operacao": "S"},
    {"codigo": "3204", "descricao": "Prestação de serviço de comunicação por estabelecimento de prestador de serviços", "tipo_operacao": "S"},
]


# =============================================================================
# FUNÇÃO PRINCIPAL DE POPULAÇÃO
# =============================================================================

def popular_cfops(db_url: str, dry_run: bool = False) -> dict:
    """
    Popula a tabela cfops_transferencia com CFOPs comuns.
    
    Args:
        db_url: URL de conexão com o banco PostgreSQL
        dry_run: Se True, apenas mostra o que seria inserido (não altera o banco)
    
    Returns:
        dict com estatísticas da operação
    """
    stats = {
        "total_cfops": len(CFOPS_COMUNS),
        "inseridos": 0,
        "atualizados": 0,
        "pulados": 0,
        "erros": 0,
        "dry_run": dry_run
    }
    
    print(f"🔄 Populando CFOPs (dry_run={dry_run})...")
    print(f"📊 Total de CFOPs a processar: {stats['total_cfops']}")
    
    try:
        # Criar engine e sessão
        engine = create_engine(db_url)
        
        with Session(engine) as session:
            for cfop_data in CFOPS_COMUNS:
                try:
                    codigo = cfop_data["codigo"]
                    descricao = cfop_data["descricao"]
                    tipo_operacao = cfop_data.get("tipo_operacao", get_tipo_operacao(codigo))
                    
                    # Verificar se já existe pelo campo 'codigo'
                    existing = session.execute(
                        select(CfopTransferencia).where(CfopTransferencia.codigo == codigo)
                    ).scalar_one_or_none()
                    
                    if existing:
                        # Atualizar se descrição ou tipo_operacao estiverem diferentes
                        needs_update = (
                            existing.descricao != descricao or 
                            getattr(existing, 'tipo_operacao', None) != tipo_operacao
                        )
                        
                        if needs_update:
                            if not dry_run:
                                existing.descricao = descricao
                                existing.tipo_operacao = tipo_operacao
                                existing.ativo = True
                                stats["atualizados"] += 1
                                print(f"✏️  Atualizado: {codigo} - {tipo_operacao}")
                            else:
                                print(f"✏️  [DRY] Atualizaria: {codigo}")
                        else:
                            stats["pulados"] += 1
                    else:
                        # Inserir novo CFOP
                        if not dry_run:
                            novo_cfop = CfopTransferencia(
                                codigo=codigo,              # ✅ Campo correto
                                descricao=descricao,         # ✅ Campo correto
                                tipo_operacao=tipo_operacao, # ✅ Campo novo
                                ativo=True                   # ✅ Campo correto
                            )
                            session.add(novo_cfop)
                            stats["inseridos"] += 1
                            print(f"✅ Inserido: {codigo} - {tipo_operacao} - {descricao[:40]}...")
                        else:
                            stats["inseridos"] += 1
                            print(f"✅ [DRY] Inseriria: {codigo} - {tipo_operacao}")
                    
                except Exception as e:
                    stats["erros"] += 1
                    print(f"❌ Erro ao processar {cfop_data.get('codigo', '?')}: {e}")
            
            # Commit se não for dry run
            if not dry_run:
                session.commit()
                print(f"💾 Alterações confirmadas no banco!")
        
        # Resumo final
        print(f"\n📈 Resumo da operação:")
        print(f"   ✅ Inseridos:   {stats['inseridos']}")
        print(f"   ✏️  Atualizados: {stats['atualizados']}")
        print(f"   ⏭️  Pulados:    {stats['pulados']}")
        print(f"   ❌ Erros:       {stats['erros']}")
        
        return stats
        
    except Exception as e:
        print(f"❌ Erro crítico ao conectar ao banco: {e}")
        import traceback
        traceback.print_exc()
        stats["erros"] += 1
        return stats


# =============================================================================
# EXECUÇÃO VIA LINHA DE COMANDO
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Popular CFOPs comuns no banco de dados")
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Apenas simular, não alterar o banco"
    )
    parser.add_argument(
        "--db-url", 
        type=str, 
        default=None,
        help="URL do banco (padrão: usa settings.DB_URL)"
    )
    
    args = parser.parse_args()
    
    # Determinar URL do banco
    db_url =  os.environ.get("DB_URL") or args.db_url or getattr(settings, "DB_URL", None)
    
    if not db_url:
        print("❌ Erro: DB_URL não configurada!")
        print("Defina a variável de ambiente DB_URL ou use --db-url")
        sys.exit(1)
    
    # Mask password in log
    db_url_log = db_url
    if hasattr(settings, "DB_PASSWORD") and settings.DB_PASSWORD:
        db_url_log = db_url.replace(settings.DB_PASSWORD, "***")
    
    print(f"🔗 Conectando a: {db_url_log}")
    
    # Executar
    resultado = popular_cfops(db_url, dry_run=args.dry_run)
    
    # Código de saída
    sys.exit(0 if resultado["erros"] == 0 else 1)
    