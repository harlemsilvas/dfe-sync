"""
API REST para gerenciamento do classificador de documentos
Inclui função imprimir_dashboard para exibir estatísticas de processamento.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import tempfile
import sys
import os
from pathlib import Path
import asyncio
import zipfile
import shutil
from datetime import datetime
import uuid  # ✅ MOVER PARA O TOPO (melhor prática)


# IMPORTS PARA DASHBOARD
try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    Console = None
    Table = None

# Adicionar o diretório raiz ao path para imports relativos
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent.parent
sys.path.insert(0, str(root_dir))

from src.core.processador_completo import ProcessadorCompleto
from src.core.classificador_xml import ClassificadorXML
from src.core.organizador_documentos import OrganizadorDocumentos
from src.core.logging_sistema import ProcessamentoLogger
from src.store.db import SessionLocal
from sqlalchemy import text

# ✅ CRIAR APIRouter, NÃO FastAPI
router = APIRouter(
    prefix="/classificador",
    tags=["Classificador"]
)

# =============================================================================
# MODELS
# =============================================================================

class ProcessamentoStatus(BaseModel):
    task_id: str
    status: str
    progress: int
    message: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    stats: Optional[Dict] = None

class ClassificacaoRequest(BaseModel):
    pasta_origem: str
    manter_originais: bool = True
    processar_subdiretorios: bool = True

class OperacaoPendenteResponse(BaseModel):
    id: int
    chave_nfe: str
    cnpj_emissor: str
    cnpj_destinatario: str
    cfop: str
    natureza_operacao: str
    tipo_sugerido: str
    motivo_pendencia: str
    resolvido: bool

class ResolverPendenciaRequest(BaseModel):
    tipo_final: str
    resolvido_por: str

# =============================================================================
# VARIÁVEIS GLOBAIS
# =============================================================================

task_storage: Dict[str, ProcessamentoStatus] = {}
logger = ProcessamentoLogger("API")

# =============================================================================
# FUNÇÕES AUXILIARES (antes dos endpoints)
# =============================================================================

def adaptar_stats_para_dashboard(stats_originais: Dict) -> Dict:
    """
    Converte stats do ProcessadorCompleto para formato compatível com imprimir_dashboard
    """
    if not stats_originais:
        return {}
    
    return {
        'xmls_processados': stats_originais.get('total_xmls', stats_originais.get('xmls_processados', 0)),
        'xmls_classificados': stats_originais.get('classificados', stats_originais.get('xmls_classificados', 0)),
        'xmls_organizados': stats_originais.get('organizados', stats_originais.get('xmls_organizados', 0)),
        'xmls_com_erro': stats_originais.get('erros', stats_originais.get('xmls_com_erro', 0)),
        'tipos_encontrados': stats_originais.get('por_tipo', stats_originais.get('tipos_encontrados', {})),
        'empresas_envolvidas': list(stats_originais.get('cnpjs', stats_originais.get('empresas_envolvidas', set()))),
        'valores_totais': float(stats_originais.get('valor_total', stats_originais.get('valores_totais', 0))),
        'tempo_execucao': stats_originais.get('tempo_segundos', stats_originais.get('tempo_execucao', 0)),
        'erros': stats_originais.get('lista_erros', stats_originais.get('erros', []))
    }

# Função para exibir dashboard de processamento
def imprimir_dashboard(stats: Dict):
    """
    Exibe um dashboard resumido das estatísticas de processamento.
    Usa rich se disponível, senão fallback para print.
    """
    if Console and Table:
        console = Console()
        console.print("\n[bold green]📊 DASHBOARD DE PROCESSAMENTO[/bold green]\n")
        table = Table(show_header=False, box=None)
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="white")
        table.add_row("📁 XMLs Processados", str(stats.get('xmls_processados', 0)))
        table.add_row("✅ Classificados", str(stats.get('xmls_classificados', 0)))
        table.add_row("🗂️  Organizados", str(stats.get('xmls_organizados', 0)))
        table.add_row("❌ Com Erro", str(stats.get('xmls_com_erro', 0)))
        table.add_row("⏱️  Tempo", f"{stats.get('tempo_execucao', 0)}s")
        table.add_row("💰 Valor Total", f"R$ {stats.get('valores_totais', 0):,.2f}")
        console.print(table)
    else:
        print("\n" + "="*60)
        print("📊 RESUMO DO PROCESSAMENTO")
        print("="*60)
        print(f"📁 XMLs Processados: {stats.get('xmls_processados', 0)}")
        print(f"✅ Classificados: {stats.get('xmls_classificados', 0)}")
        print(f"🗂️  Organizados: {stats.get('xmls_organizados', 0)}")
        print(f"❌ Com Erro: {stats.get('xmls_com_erro', 0)}")
        print(f"⏱️  Tempo: {stats.get('tempo_execucao', 0)}s")
        print(f"💰 Valor Total: R$ {stats.get('valores_totais', 0):,.2f}")
        print("="*60)


async def _processar_pasta_background(task_id: str, pasta_origem: str, manter_originais: bool):
    """Processa pasta em background"""
    try:
        task_storage[task_id].message = "Inicializando processador..."
        task_storage[task_id].progress = 10
        
        processador = ProcessadorCompleto(pasta_origem, manter_originais)
        
        task_storage[task_id].message = "Processando arquivos..."
        task_storage[task_id].progress = 30
        
        stats = processador.processar_pasta_completa()
        
        # ✅✅✅ DASHBOARD: Exibe estatísticas formatadas nos logs ✅✅✅
        try:
            # Tenta usar stats direto, se não funcionar, adapta o formato
            if isinstance(stats, dict) and 'xmls_processados' in stats:
                imprimir_dashboard(stats)
            else:
                stats_adaptados = adaptar_stats_para_dashboard(stats)
                if stats_adaptados:
                    imprimir_dashboard(stats_adaptados)
        except Exception as e:
            logger.warning(f"Não foi possível exibir dashboard: {e}")
        
        task_storage[task_id].status = "COMPLETED"
        task_storage[task_id].progress = 100
        task_storage[task_id].message = "Processamento concluído com sucesso"
        task_storage[task_id].finished_at = datetime.now()
        task_storage[task_id].stats = stats
        
        logger.info(f"Processamento concluído: {task_id} | stats={stats}")
        
    except Exception as e:
        task_storage[task_id].status = "ERROR"
        task_storage[task_id].message = f"Erro: {str(e)}"
        task_storage[task_id].finished_at = datetime.now()
        logger.error(f"Erro no processamento {task_id}: {e}")

# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/", response_model=Dict)
async def root():
    """Endpoint raiz do classificador"""
    return {
        "nome": "DFE Classificador",
        "versao": "1.0.0",
        "status": "ativo"
    }

@router.post("/classificar", response_model=ProcessamentoStatus)
async def classificar_documentos(
    request: ClassificacaoRequest,
    background_tasks: BackgroundTasks
):
    """Inicia processo de classificação de documentos em uma pasta"""
    task_id = str(uuid.uuid4())
    
    pasta = Path(request.pasta_origem)
    if not pasta.exists():
        raise HTTPException(status_code=400, detail=f"Pasta não encontrada: {request.pasta_origem}")
    
    status = ProcessamentoStatus(
        task_id=task_id,
        status="RUNNING",
        progress=0,
        message="Iniciando processamento...",
        started_at=datetime.now()
    )
    task_storage[task_id] = status
    
    background_tasks.add_task(
        _processar_pasta_background, 
        task_id, 
        request.pasta_origem,
        request.manter_originais
    )
    
    logger.info(f"Processamento iniciado: {task_id} | pasta={request.pasta_origem}")
    return status

@router.get("/status/{task_id}", response_model=ProcessamentoStatus)
async def get_status(task_id: str):
    """Consulta status de processamento"""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task não encontrada")
    return task_storage[task_id]

@router.get("/tasks")
async def list_tasks():
    """Lista todas as tasks"""
    return {
        "total": len(task_storage),
        "tasks": list(task_storage.values())
    }

@router.post("/upload")
async def upload_arquivo(
    files: List[UploadFile] = File(...),
    processar: Optional[bool] = Query(None, description="Processar imediatamente após upload?")
):
    """Upload de arquivos. Pode processar imediatamente, apenas salvar, ou perguntar ao usuário."""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            arquivos_salvos = []
            for file in files:
                arquivo_path = temp_path / file.filename
                with open(arquivo_path, "wb") as f:
                    shutil.copyfileobj(file.file, f)
                arquivos_salvos.append(arquivo_path)

            if processar is None:
                return {
                    "success": True,
                    "uploaded_files": [str(p.name) for p in arquivos_salvos],
                    "count": len(arquivos_salvos),
                    "message": "Arquivos salvos. Deseja processar agora?",
                    "can_process": True
                }
            elif processar:
                processador = ProcessadorCompleto(str(temp_path), manter_originais=True)
                resultado = processador.processar_pasta_completa()
                
                # ✅ Dashboard para upload com processamento
                try:
                    if isinstance(resultado, dict) and 'xmls_processados' in resultado:
                        imprimir_dashboard(resultado)
                    else:
                        stats_adaptados = adaptar_stats_para_dashboard(resultado)
                        if stats_adaptados:
                            imprimir_dashboard(stats_adaptados)
                except:
                    pass  # Ignora falha no dashboard, não quebra o processo
                
                return {
                    "success": True,
                    "processed": True,
                    "resultado": resultado,
                    "count": len(arquivos_salvos)
                }
            else:
                return {
                    "success": True,
                    "uploaded_files": [str(p.name) for p in arquivos_salvos],
                    "count": len(arquivos_salvos),
                    "processed": False
                }
    except Exception as e:
        logger.error(f"Erro no upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pendencias", response_model=List[OperacaoPendenteResponse])
async def get_pendencias(limite: int = Query(50)):
    """Lista operações pendentes de validação"""
    try:
        with SessionLocal() as db:
            result = db.execute(text("""
                SELECT id, chave_nfe, cnpj_emissor, cnpj_destinatario, 
                       cfop, natureza_operacao, tipo_sugerido, motivo_pendencia, resolvido
                FROM operacoes_pendentes 
                WHERE resolvido = false
                ORDER BY created_at DESC
                LIMIT :limite
            """), {"limite": limite})
            
            pendencias = []
            for row in result:
                pendencias.append(OperacaoPendenteResponse(
                    id=row.id, chave_nfe=row.chave_nfe, cnpj_emissor=row.cnpj_emissor,
                    cnpj_destinatario=row.cnpj_destinatario, cfop=row.cfop,
                    natureza_operacao=row.natureza_operacao, tipo_sugerido=row.tipo_sugerido,
                    motivo_pendencia=row.motivo_pendencia, resolvido=row.resolvido
                ))
            return pendencias
    
    except Exception as e:
        logger.error(f"Erro ao buscar pendências: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.put("/pendencias/{pendencia_id}")
async def resolver_pendencia(pendencia_id: int, request: ResolverPendenciaRequest):
    """Resolve uma pendência manualmente"""
    try:
        with SessionLocal() as db:
            result = db.execute(text(
                "SELECT id FROM operacoes_pendentes WHERE id = :id AND resolvido = false"
            ), {"id": pendencia_id})
            
            if not result.fetchone():
                raise HTTPException(status_code=404, detail="Pendência não encontrada")
            
            db.execute(text("""
                UPDATE operacoes_pendentes 
                SET tipo_final = :tipo, resolvido = true, resolvido_por = :usuario, resolvido_em = now()
                WHERE id = :id
            """), {
                "tipo": request.tipo_final,
                "usuario": request.resolvido_por,
                "id": pendencia_id
            })
            db.commit()
            
            logger.info(f"Pendência {pendencia_id} resolvida por {request.resolvido_por}")
            return {"success": True, "message": "Pendência resolvida com sucesso"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao resolver pendência: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.get("/relatorio")
async def get_relatorio():
    """Gera relatório completo do sistema"""
    try:
        organizador = OrganizadorDocumentos()
        relatorio = organizador.gerar_relatorio_organizacao()
        
        with SessionLocal() as db:
            empresas = db.execute(text(
                "SELECT COUNT(*) as total, COUNT(CASE WHEN monitorada THEN 1 END) as monitoradas FROM empresas WHERE ativo = 1"
            )).fetchone()
            logs_recentes = db.execute(text(
                "SELECT COUNT(*) FROM logs_processamento WHERE created_at > now() - interval '24 hours'"
            )).fetchone()
            pendencias = db.execute(text(
                "SELECT COUNT(*) FROM operacoes_pendentes WHERE resolvido = false"
            )).fetchone()
            
            relatorio["sistema"] = {
                "empresas_cadastradas": empresas.total,
                "empresas_monitoradas": empresas.monitoradas,
                "logs_24h": logs_recentes[0],
                "pendencias_abertas": pendencias[0],
                "timestamp": datetime.now().isoformat()
            }
        
        return relatorio
    
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.get("/configuracao")
async def get_configuracao():
    """Retorna configurações do sistema"""
    try:
        with SessionLocal() as db:
            empresas = db.execute(text(
                "SELECT cnpj, razao_social FROM empresas WHERE monitorada = true AND ativo = 1"
            )).fetchall()
            tipos = db.execute(text(
                "SELECT codigo, descricao FROM tipo_documento WHERE ativo = true"
            )).fetchall()
            cfops = db.execute(text(
                "SELECT codigo, descricao FROM cfops_transferencia WHERE ativo = true"
            )).fetchall()
            
            return {
                "empresas_monitoradas": [{"cnpj": e.cnpj, "razao_social": e.razao_social} for e in empresas],
                "tipos_documento": [{"codigo": t.codigo, "descricao": t.descricao} for t in tipos],
                "cfops_transferencia": [{"codigo": c.codigo, "descricao": c.descricao} for c in cfops]
            }
    
    except Exception as e:
        logger.error(f"Erro ao buscar configuração: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Remove uma task do storage"""
    if task_id in task_storage:
        del task_storage[task_id]
        return {"success": True, "message": "Task removida"}
    else:
        raise HTTPException(status_code=404, detail="Task não encontrada")

@router.post("/xmls/{xml_id}/classificar")
async def classificar_xml_manual(xml_id: str, classificacao: str = Body(...)):
    """Classifica manualmente um arquivo XML pelo nome, usando o classificador."""
    xml_path = Path("/mnt/c/Projetos/dfe-sync/storage/upload") / xml_id
    if not xml_path.exists():
        raise HTTPException(status_code=404, detail=f"Arquivo XML não encontrado: {xml_id}")
    
    classificador = ClassificadorXML()
    metadata = classificador.processar_xml(xml_path)
    
    # Sobrescreve classificação manual
    metadata.tipo_documento = classificacao

    # Decide destino
    if metadata.erro_parsing:
        destino = Path("/mnt/c/Projetos/dfe-sync/storage/fail")
    else:
        destino = Path("/mnt/c/Projetos/dfe-sync/storage/processed")
    
    destino.mkdir(parents=True, exist_ok=True)
    novo_path = destino / xml_id
    
    try:
        shutil.move(str(xml_path), str(novo_path))
    except Exception as e:
        logger.warning(f"Erro ao mover arquivo classificado: {e}")

    return {
        "arquivo": xml_id,
        "classificacao": classificacao,
        "metadados": metadata.__dict__,
        "movido_para": str(novo_path)
    }
    
