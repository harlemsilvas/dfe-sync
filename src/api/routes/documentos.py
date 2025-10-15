from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from src.store.db import SessionLocal
from src.models import DFEDocumento
from lxml import etree
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

def _parse_doc_fields(xml_bytes: bytes) -> dict:
    ns = {"nfe":"http://www.portalfiscal.inf.br/nfe"}
    try:
        root = etree.fromstring(xml_bytes)
    except Exception:
        return {}
    data = {}
    # Tenta resNFe
    ch = root.find('.//nfe:chNFe', ns)
    if ch is not None:
        data['chave'] = ch.text
    emit_cnpj = root.find('.//nfe:CNPJ', ns)
    emit_nome = root.find('.//nfe:xNome', ns)
    if emit_cnpj is not None:
        data['emitente_cnpj'] = emit_cnpj.text
    if emit_nome is not None:
        data['emitente_nome'] = emit_nome.text
    # Datas: dhEmi (procNFe/NFe) ou dhEmi/dEmi em resumos
    for xp in ['.//nfe:dhEmi', './/nfe:dEmi']:
        d = root.find(xp, ns)
        if d is not None and d.text:
            data['data_emissao'] = d.text[:10]
            break
    # Valor: vNF ou vProd total
    for xp in ['.//nfe:vNF', './/nfe:total//nfe:vNF', './/nfe:ICMSTot//nfe:vNF']:
        v = root.find(xp, ns)
        if v is not None and v.text:
            data['valor'] = v.text
            break
    return data

@router.get("/documentos/importacao")
def list_docs_importacao(empresa_id:int=Query(...), limit:int=Query(50), offset:int=Query(0), filtro:str|None=Query(None)):
    """Lista documentos com campos enriquecidos a partir do XML salvo, para UI de importação.
    filtro=pendentes -> resNFe; filtro=registradas -> procNFe; vazio -> todos.
    Retorna também contadores por categoria.
    """
    with SessionLocal() as db:
        q = select(DFEDocumento).where(DFEDocumento.empresa_id==empresa_id)
        if filtro == 'pendentes':
            q = q.where(DFEDocumento.schema=="resNFe")
        elif filtro == 'registradas':
            q = q.where(DFEDocumento.schema=="procNFe")
        q = q.order_by(DFEDocumento.id.desc()).offset(offset).limit(limit)
        rows = db.execute(q).all()
        items = []
        for (r,) in rows:
            info = {"id":r.id, "nsu":r.nsu, "schema":r.schema, "chave":r.chave, "created_at":str(r.created_at)}
            # Campos de manifestação persistidos
            info.update({
                "manifest_tp": r.manifest_tp,
                "manifest_nseq": r.manifest_nseq,
                "manifest_cstat": r.manifest_cstat,
                "manifest_xmotivo": r.manifest_xmotivo,
                "manifest_xml_path": r.manifest_xml_path,
                "manifest_updated_at": str(r.manifest_updated_at) if getattr(r, 'manifest_updated_at', None) else None
            })
            try:
                p = Path(r.caminho_xml)
                if p.exists():
                    xmlb = p.read_bytes()
                    info.update(_parse_doc_fields(xmlb))
            except Exception:
                pass
            items.append(info)
        total_all = db.execute(select(func.count()).select_from(DFEDocumento).where(DFEDocumento.empresa_id==empresa_id)).scalar() or 0
        total_reg = db.execute(select(func.count()).select_from(DFEDocumento).where(DFEDocumento.empresa_id==empresa_id, DFEDocumento.schema=="procNFe")).scalar() or 0
        total_pen = db.execute(select(func.count()).select_from(DFEDocumento).where(DFEDocumento.empresa_id==empresa_id, DFEDocumento.schema=="resNFe")).scalar() or 0
        return {"items":items, "count":len(items), "counts": {"todas": total_all, "registradas": total_reg, "pendentes": total_pen}}

@router.get("/documentos/{doc_id}/download")
def download_xml(doc_id:int):
    with SessionLocal() as db:
        row = db.execute(select(DFEDocumento).where(DFEDocumento.id==doc_id)).scalar_one_or_none()
        if not row:
            raise HTTPException(404, "Documento não encontrado")
        p = Path(row.caminho_xml)
        if not p.exists():
            raise HTTPException(404, "Arquivo XML não encontrado")
        return FileResponse(str(p), media_type='application/xml', filename=p.name)