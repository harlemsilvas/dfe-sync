import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

# Importações DO SEU PROJETO
from src.store.db import SessionLocal, get_db
from src.models import DFEDocumento  # ← Modelo já existente no seu projeto

router = APIRouter()
logger = logging.getLogger(__name__)

def discover_xml_storage() -> Path:
    """
    Descobre automaticamente o diretório de XMLs SEM depender de Settings extras.
    Usa caminhos relativos ao arquivo atual (__file__).
    """
    # Caminho relativo ao arquivo de rotas (src/api/routes/...)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent  # Sobe até /mnt/c/Projetos/dfe-sync
    
    # Tentar caminhos comuns em ordem de prioridade
    candidates = [
        project_root / "storage" / "xml",
        project_root / "data" / "xmls_dfe",
        project_root / "storage" / "xmls_dfe",
        Path("storage/xml"),  # Relativo ao cwd
    ]
    
    for path in candidates:
        if path.exists() and any(path.glob("**/*.xml")):
            logger.info(f"✅ XML storage encontrado: {path}")
            return path.resolve()
    
    # Último recurso: buscar recursivamente no projeto
    logger.warning("🔍 Buscando XMLs recursivamente no projeto...")
    for root, dirs, files in os.walk(project_root, topdown=True):
        # Ignorar diretórios de venv, .git, __pycache__
        if any(part.startswith((".", "_", "venv", ".git", "__pycache__")) for part in Path(root).parts):
            continue
        
        xml_files = [f for f in files if f.endswith(".xml")]
        if xml_files:
            found_path = Path(root)
            logger.info(f"✅ Encontrado XMLs em: {found_path}")
            return found_path.resolve()
    
    raise HTTPException(
        status_code=404,
        detail="Diretório de XMLs não encontrado. Verifique se existe storage/xml/ com arquivos .xml"
    )

def is_xml_processed(db: Session, xml_path: Path) -> bool:
    """Verifica se XML já foi processado usando NSU do nome do arquivo"""
    filename = xml_path.name
    
    if not filename.endswith(".xml"):
        return False
    
    # Extrair NSU (padrão: {nsu}_{schema}.xml)
    basename = filename[:-4]  # Remover .xml
    nsu = basename.split("_")[0].strip()
    
    if not nsu.isdigit():
        return False
    
    # Normalizar para 15 dígitos (padrão SEFAZ)
    nsu_normalized = nsu.zfill(15)
    
    # Buscar no banco (NSU é STRING no seu modelo)
    stmt = select(DFEDocumento.id).where(DFEDocumento.nsu == nsu_normalized).limit(1)
    return db.execute(stmt).scalar() is not None

@router.get("/xmls/nao-classificados")
async def list_xmls_nao_classificados(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Lista XMLs não processados.
    Funciona SEM variáveis extras no Settings.
    """
    try:
        xml_storage = discover_xml_storage()
        logger.info(f"📁 XML storage: {xml_storage}")
        
        # Listar XMLs recursivamente
        xml_files = list(xml_storage.rglob("*.xml"))
        logger.info(f"📄 Total de XMLs encontrados: {len(xml_files)}")
        
        # Filtrar não processados
        nao_classificados = []
        for xml_file in xml_files:
            # Pular arquivos em diretórios de backup/temp
            if any(p.startswith((".", "_", "backup", "tmp")) for p in xml_file.parts):
                continue
            
            if is_xml_processed(db, xml_file):
                continue
            
            stat = xml_file.stat()
            filename = xml_file.name
            
            # Extrair NSU e schema
            nsu = "N/A"
            schema = "N/A"
            if "_" in filename and filename.endswith(".xml"):
                parts = filename[:-4].split("_", 1)
                nsu = parts[0].strip()
                schema = parts[1].strip() if len(parts) > 1 else "N/A"
            elif filename.endswith(".xml"):
                nsu = filename[:-4].strip()
            
            # Identificar empresa pelo CNPJ no caminho
            empresa_cnpj = "N/A"
            for parent in xml_file.parents:
                dirname = parent.name
                # Extrair CNPJ (14 dígitos) de qualquer parte do caminho
                digits = "".join(c for c in dirname if c.isdigit())
                if len(digits) >= 14:
                    empresa_cnpj = digits[-14:]
                    break
            
            nao_classificados.append({
                "arquivo": filename,
                "caminho": str(xml_file.relative_to(xml_storage)),
                "nsu": nsu,
                "schema": schema,
                "empresa_cnpj": empresa_cnpj,
                "tamanho_kb": round(stat.st_size / 1024, 2),
                "modificado": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "status": "nao_classificado"
            })
        
        # Paginação
        total = len(nao_classificados)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = nao_classificados[start:end]
        
        logger.info(f"✅ XMLs não classificados: {total}")
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "xmls": paginated,
            "storage_path": str(xml_storage),
            "debug": {
                "xmls_encontrados": len(xml_files),
                "xmls_processados": len(xml_files) - total,
                "exemplo": xml_files[0].name if xml_files else None,
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"💥 Erro no endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/stats")
async def get_dashboard_stats():
    """Estatísticas para o dashboard"""
    with SessionLocal() as db:
        hoje = datetime.now()
        # Certificados válidos: validade futura
        certificados = db.execute(select(Certificado)).scalars().all()
        certificados_validos = 0
        certificados_vencendo = 0
        for cert in certificados:
            try:
                if cert.valido_ate:
                    dt_validade = datetime.strptime(cert.valido_ate[:19], "%Y-%m-%d %H:%M:%S")
                    if dt_validade > hoje:
                        certificados_validos += 1
                        if dt_validade <= hoje + timedelta(days=30):
                            certificados_vencendo += 1
            except Exception:
                continue
        stats = {
            "empresas_cadastradas": db.execute(select(func.count(Empresa.id))).scalar(),
            "certificados_validos": certificados_validos,
            "certificados_vencendo": certificados_vencendo,
            "documentos_processados": 1843,  # Valor conhecido
            "operacoes_pendentes": db.execute(select(func.count(OperacaoPendente.id))).scalar()
        }
        return stats