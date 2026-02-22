from fastapi import APIRouter, Query, UploadFile, File, HTTPException
from sqlalchemy import select, and_, or_
from src.store.db import SessionLocal
from src.models import DFEDocumento
import os
from pathlib import Path

router = APIRouter()

@router.get("/documentos")
def list_docs(empresa_id:int=Query(...), limit:int=Query(50), offset:int=Query(0)):
    with SessionLocal() as db:
        rows = db.execute(select(DFEDocumento).where(DFEDocumento.empresa_id==empresa_id).order_by(DFEDocumento.id.desc()).offset(offset).limit(limit)).all()
        items = []
        for (r,) in rows:
            items.append({
                "id":r.id,"nsu":r.nsu,"schema":r.schema,"chave":r.chave,
                "caminho_xml": r.caminho_xml, "created_at": str(r.created_at)
            })
        return {"items":items,"count":len(items)}

@router.get("/documentos/importacao")
def list_importacao(
    empresa_id: int = Query(...),
    limit: int = Query(50),
    offset: int = Query(0),
    filtro: str = Query(None)  # pendentes, registradas, todas
):
    """
    Lista documentos para importação.
    Filtros disponíveis:
    - pendentes: documentos não processados
    - registradas: documentos já processados/importados
    - todas ou None: todos os documentos
    """
    with SessionLocal() as db:
        query = select(DFEDocumento).where(DFEDocumento.empresa_id == empresa_id)
        
        # Aplicar filtro se fornecido
        # Nota: Como não temos campo de status, vamos retornar todos por enquanto
        # Você pode adicionar um campo 'status' ou 'importado' na model depois
        
        rows = db.execute(
            query.order_by(DFEDocumento.id.desc())
            .offset(offset)
            .limit(limit)
        ).scalars().all()
        
        items = []
        for r in rows:
            items.append({
                "id": r.id,
                "nsu": r.nsu,
                "schema": r.schema,
                "chave": r.chave,
                "caminho_xml": r.caminho_xml,
                "created_at": str(r.created_at),
                # Adicionar campos úteis para importação
                "status": "pendente",  # placeholder - implementar lógica real
                "tipo": _get_tipo_documento(r.schema)
            })
        
        return {
            "items": items,
            "count": len(items),
            "total": db.execute(
                select(DFEDocumento).where(DFEDocumento.empresa_id == empresa_id)
            ).scalars().all().__len__()
        }

def _get_tipo_documento(schema: str) -> str:
    """Identifica o tipo de documento pelo schema"""
    if "resNFe" in schema:
        return "NFe (Resumo)"
    elif "procNFe" in schema:
        return "NFe (Completa)"
    elif "resEvento" in schema:
        return "Evento (Resumo)"
    elif "procEvento" in schema:
        return "Evento (Completo)"
    else:
        return schema

@router.post("/upload")
async def upload_documents(files: list[UploadFile] = File(...)):
    """Upload de múltiplos arquivos de documentos"""
    upload_dir = Path("/mnt/c/Projetos/dfe-sync/storage/upload")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    uploaded_files = []
    
    for file in files:
        if file.filename:
            # Verificar extensão
            allowed_extensions = ['.xml', '.zip', '.rar', '.7z']
            if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
                raise HTTPException(400, f"Tipo de arquivo não suportado: {file.filename}")
            
            # Salvar arquivo
            file_path = upload_dir / file.filename
            content = await file.read()
            file_path.write_bytes(content)
            
            uploaded_files.append({
                "filename": file.filename,
                "size": len(content),
                "path": str(file_path),
                "status": "uploaded"
            })
    
    return {
        "success": True,
        "uploaded_files": uploaded_files,
        "count": len(uploaded_files)
    }
