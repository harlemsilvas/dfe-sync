"""
API REST para gerenciamento do classificador de documentos
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends, Query
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
    prefix="/classificador",  # Opcional: prefixo para todas as rotas deste router
    tags=["Classificador"]
)

# Models (mesmos do seu código original)
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

# Storage para tasks em background (global ao router)
task_storage: Dict[str, ProcessamentoStatus] = {}
logger = ProcessamentoLogger("API")

# =============================================================================
# ENDPOINTS (usar @router. em vez de @app.)
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
    import uuid
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
    
    logger.info(f"Processamento iniciado: {task_id}", pasta=request.pasta_origem)
    return status

async def _processar_pasta_background(task_id: str, pasta_origem: str, manter_originais: bool):
    """Processa pasta em background"""
    try:
        task_storage[task_id].message = "Inicializando processador..."
        task_storage[task_id].progress = 10
        
        processador = ProcessadorCompleto(pasta_origem, manter_originais)
        
        task_storage[task_id].message = "Processando arquivos..."
        task_storage[task_id].progress = 30
        
        stats = processador.processar_pasta_completa()
        
        task_storage[task_id].status = "COMPLETED"
        task_storage[task_id].progress = 100
        task_storage[task_id].message = "Processamento concluído com sucesso"
        task_storage[task_id].finished_at = datetime.now()
        task_storage[task_id].stats = stats
        
        logger.info(f"Processamento concluído: {task_id}", stats=stats)
        
    except Exception as e:
        task_storage[task_id].status = "ERROR"
        task_storage[task_id].message = f"Erro: {str(e)}"
        task_storage[task_id].finished_at = datetime.now()
        logger.error(f"Erro no processamento {task_id}: {e}")

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
async def upload_arquivo(files: List[UploadFile] = File(...)):
    """Upload e processamento de arquivos (compatível com documentos.py)"""
    try:
        resultados = []
        
        for file in files:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                arquivo_path = temp_path / file.filename
                
                with open(arquivo_path, "wb") as f:
                    shutil.copyfileobj(file.file, f)
                
                processador = ProcessadorCompleto(str(temp_path), manter_originais=True)
                
                if arquivo_path.suffix.lower() in ['.zip', '.rar', '.7z', '.xml']:
                    resultado = processador.processar_arquivo_especifico(str(arquivo_path))
                    resultados.append({
                        "filename": file.filename,
                        "status": "ok",
                        "resultado": resultado
                    })
                else:
                    resultados.append({
                        "filename": file.filename,
                        "status": "error",
                        "erro": f"Tipo não suportado: {arquivo_path.suffix}"
                    })
        
        return {
            "success": True,
            "uploaded_files": resultados,
            "count": len(resultados)
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
                "SELECT COUNT(*) as total, COUNT(CASE WHEN monitorada THEN 1 END) as monitoradas FROM empresas WHERE ativo = true"
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
                "SELECT cnpj, razao_social FROM empresas WHERE monitorada = true AND ativo = true"
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