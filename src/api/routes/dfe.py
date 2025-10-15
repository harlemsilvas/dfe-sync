from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, update
from src.store.db import SessionLocal
from src.models import Empresa, Certificado, CursorDFe, DFEDocumento
from src.cert.pfx_utils import pfx_to_pem_tempfiles, pfx_extract_cnpj_cpf
from src.core.dfe_sync import run_distribution
import os, certifi
from src.ws.dfe_client import nfe_distribuicao_dfe, nfe_consultar_nsu, nfe_consultar_chave
from src.ws.manifest_client import enviar_manifestacao
from src.settings import settings

router = APIRouter()

def _load_cert_tuple(empresa_id:int):
    with SessionLocal() as db:
        cert = db.execute(select(Certificado).where(Certificado.empresa_id==empresa_id)).scalar_one_or_none()
        emp  = db.execute(select(Empresa).where(Empresa.id==empresa_id)).scalar_one_or_none()
        if not emp: raise HTTPException(404,"Empresa nÃ£o encontrada")
        if not cert: raise HTTPException(400,"Certificado nÃ£o cadastrado")
        pfx = open(cert.pfx_path,"rb").read()
        cert_path, key_path = pfx_to_pem_tempfiles(pfx, cert.senha_cripto)
        return (emp, cert_path, key_path)

@router.get("/dfe/cursor")
def get_cursor(empresa_id:int=Query(...)):
    with SessionLocal() as db:
        cur = db.execute(select(CursorDFe).where(CursorDFe.empresa_id==empresa_id)).scalar_one_or_none()
        if not cur: raise HTTPException(404,"Cursor nÃ£o encontrado")
        return {"empresa_id":empresa_id,"ultimo_nsu":cur.ultimo_nsu,"max_nsu":cur.max_nsu,"updated_at":str(cur.updated_at)}

@router.post("/dfe/sync")
def sync_now(empresa_id:int=Query(...)):
    cert_tuple = None
    try:
        emp, cert_path, key_path = _load_cert_tuple(empresa_id)
        cert_tuple = (cert_path, key_path)
        # Validação H04/H05: CNPJ consultado deve bater com CNPJ-base do certificado (usando PFX original)
        with SessionLocal() as db:
            cert = db.execute(select(Certificado).where(Certificado.empresa_id==empresa_id)).scalar_one()
            pfx_bytes = open(cert.pfx_path,'rb').read()
            tipo, doc = pfx_extract_cnpj_cpf(pfx_bytes, cert.senha_cripto)
            if tipo == "CNPJ":
                if (emp.cnpj or '').strip()[:8] != (doc or '')[:8]:
                    raise HTTPException(422, "CNPJ consultado difere do CNPJ-base do certificado (H04)")
            elif tipo == "CPF":
                raise HTTPException(422, "Certificado PF não suportado neste endpoint")
        verify = certifi.where()  # ou bundle ICP-Brasil
        res = run_distribution(emp.id, emp.cnpj, cert_tuple, verify)
        return res
    finally:
        if cert_tuple:
            for p in cert_tuple:
                try:
                    if p and os.path.exists(p): os.remove(p)
                except: pass

@router.get("/dfe/diagnose")
def diagnose(empresa_id:int=Query(...), ult_nsu:str=Query("000000000000000")):
    """Executa UMA chamada ao serviço de distribuição para diagnóstico sem loop.
    Retorna cStat, xMotivo, ultNSU, maxNSU, quantidade de docs e tempo.
    """
    cert_tuple = None
    try:
        emp, cert_path, key_path = _load_cert_tuple(empresa_id)
        cert_tuple = (cert_path, key_path)
        with SessionLocal() as db:
            cert = db.execute(select(Certificado).where(Certificado.empresa_id==empresa_id)).scalar_one()
            pfx_bytes = open(cert.pfx_path,'rb').read()
            tipo, doc = pfx_extract_cnpj_cpf(pfx_bytes, cert.senha_cripto)
            if tipo == "CNPJ" and (emp.cnpj or '')[:8] != (doc or '')[:8]:
                raise HTTPException(422, "CNPJ consultado difere do CNPJ-base do certificado (H04)")
        verify = settings.DFE_CA_BUNDLE if settings.DFE_CA_BUNDLE else certifi.where()
        res = nfe_distribuicao_dfe(emp.cnpj, ult_nsu, cert_tuple, verify)
        if 'error' in res:
            raise HTTPException(502, f"Erro chamada WS: {res.get('detail')}")
        docs = res.get("docs") or []
        by_schema = {}
        for d in docs:
            sch = d.get("schema") or "?"
            by_schema[sch] = by_schema.get(sch, 0) + 1
        return {
            "cStat":res.get("cStat"),
            "xMotivo":res.get("xMotivo"),
            "ultNSU":res.get("ultNSU"),
            "maxNSU":res.get("maxNSU"),
            "docs_count": len(docs),
            "by_schema": by_schema,
            "elapsed": res.get("elapsed")
        }
    finally:
        if cert_tuple:
            for p in cert_tuple:
                try:
                    if p and os.path.exists(p): os.remove(p)
                except: pass

@router.get("/dfe/consnsu")
def cons_nsu(empresa_id:int=Query(...), nsu:str=Query(...)):
    """Consulta pontual por NSU faltante (consNSU), conforme NT 2014/002.
    Retorna cStat, xMotivo e, se localizado, o(s) documento(s) em docZip (decodificados) com schema e NSU.
    """
    cert_tuple = None
    try:
        emp, cert_path, key_path = _load_cert_tuple(empresa_id)
        cert_tuple = (cert_path, key_path)
        with SessionLocal() as db:
            cert = db.execute(select(Certificado).where(Certificado.empresa_id==empresa_id)).scalar_one()
            pfx_bytes = open(cert.pfx_path,'rb').read()
            tipo, doc = pfx_extract_cnpj_cpf(pfx_bytes, cert.senha_cripto)
            if tipo == "CNPJ" and (emp.cnpj or '')[:8] != (doc or '')[:8]:
                raise HTTPException(422, "CNPJ consultado difere do CNPJ-base do certificado (H04)")
        verify = settings.DFE_CA_BUNDLE if settings.DFE_CA_BUNDLE else certifi.where()
        res = nfe_consultar_nsu(emp.cnpj, nsu, cert_tuple, verify)
        if 'error' in res:
            raise HTTPException(502, f"Erro chamada WS: {res.get('detail')}")
        # não retornar XML completo no corpo para evitar payload grande; retornar apenas metadados
        meta = [{"nsu": d.get("nsu"), "schema": d.get("schema"), "xml_size": len(d.get("xml") or b"")} for d in (res.get("docs") or [])]
        return {
            "cStat": res.get("cStat"),
            "xMotivo": res.get("xMotivo"),
            "ultNSU": res.get("ultNSU"),
            "maxNSU": res.get("maxNSU"),
            "docs": meta,
            "elapsed": res.get("elapsed"),
        }
    finally:
        if cert_tuple:
            for p in cert_tuple:
                try:
                    if p and os.path.exists(p): os.remove(p)
                except: pass

@router.get("/dfe/conschave")
def cons_chave(empresa_id:int=Query(...), chNFe:str=Query(..., min_length=44, max_length=44)):
    """Consulta por chave específica (consChNFe) e retorna metadados e tamanhos dos XMLs."""
    cert_tuple = None
    try:
        emp, cert_path, key_path = _load_cert_tuple(empresa_id)
        cert_tuple = (cert_path, key_path)
        with SessionLocal() as db:
            cert = db.execute(select(Certificado).where(Certificado.empresa_id==empresa_id)).scalar_one()
            pfx_bytes = open(cert.pfx_path,'rb').read()
            tipo, doc = pfx_extract_cnpj_cpf(pfx_bytes, cert.senha_cripto)
            if tipo == "CNPJ" and (emp.cnpj or '')[:8] != (doc or '')[:8]:
                raise HTTPException(422, "CNPJ consultado difere do CNPJ-base do certificado (H04)")
        verify = settings.DFE_CA_BUNDLE if settings.DFE_CA_BUNDLE else certifi.where()
        res = nfe_consultar_chave(emp.cnpj, chNFe, cert_tuple, verify)
        if 'error' in res:
            raise HTTPException(502, f"Erro chamada WS: {res.get('detail')}")
        meta = [{"nsu": d.get("nsu"), "schema": d.get("schema"), "xml_size": len(d.get("xml") or b"")} for d in (res.get("docs") or [])]
        return {
            "cStat": res.get("cStat"),
            "xMotivo": res.get("xMotivo"),
            "ultNSU": res.get("ultNSU"),
            "maxNSU": res.get("maxNSU"),
            "docs": meta,
            "elapsed": res.get("elapsed"),
        }
    finally:
        if cert_tuple:
            for p in cert_tuple:
                try:
                    if p and os.path.exists(p): os.remove(p)
                except: pass

@router.get("/dfe/conschave/download")
def cons_chave_download(
    empresa_id:int=Query(...),
    chNFe:str=Query(..., min_length=44, max_length=44),
    prefer:str=Query("procNFe", description="Prefixo preferido do schema: procNFe|resNFe|resEvento"),
    save:bool=Query(False, description="Se true, salva XML no storage e retorna saved_path")
):
    """Consulta por chave e retorna o XML (preferência de schema) como texto; opcionalmente salva no storage."""
    cert_tuple = None
    try:
        emp, cert_path, key_path = _load_cert_tuple(empresa_id)
        cert_tuple = (cert_path, key_path)
        with SessionLocal() as db:
            cert = db.execute(select(Certificado).where(Certificado.empresa_id==empresa_id)).scalar_one()
            pfx_bytes = open(cert.pfx_path,'rb').read()
            tipo, doc = pfx_extract_cnpj_cpf(pfx_bytes, cert.senha_cripto)
            if tipo == "CNPJ" and (emp.cnpj or '')[:8] != (doc or '')[:8]:
                raise HTTPException(422, "CNPJ consultado difere do CNPJ-base do certificado (H04)")
        verify = settings.DFE_CA_BUNDLE if settings.DFE_CA_BUNDLE else certifi.where()
        res = nfe_consultar_chave(emp.cnpj, chNFe, cert_tuple, verify)
        if 'error' in res:
            raise HTTPException(502, f"Erro chamada WS: {res.get('detail')}")
        docs = res.get("docs") or []
        if not docs:
            raise HTTPException(404, "Nenhum documento localizado para a chave")
        # seleção por preferência
        preferred = (prefer or '').strip()
        chosen = None
        if preferred:
            for d in docs:
                if (d.get("schema") or '').startswith(preferred):
                    chosen = d; break
        # fallback: procNFe -> resNFe -> primeiro
        if chosen is None:
            for pref in ("procNFe","resNFe","resEvento"):
                for d in docs:
                    if (d.get("schema") or '').startswith(pref):
                        chosen = d; break
                if chosen is not None:
                    break
        if chosen is None:
            chosen = docs[0]
        xml_bytes = chosen.get("xml") or b""
        try:
            txt = xml_bytes.decode('utf-8')
        except UnicodeDecodeError:
            txt = xml_bytes.decode('latin-1', errors='ignore')
        saved_path = None
        if save:
            try:
                from pathlib import Path
                base = Path(settings.STORAGE_BASE_PATH)/emp.cnpj
                base.mkdir(parents=True, exist_ok=True)
                safe_schema = (chosen.get("schema") or "").split(".")[0]
                fname = f"{chNFe}-{safe_schema}-{chosen.get('nsu') or 'nsu'}.xml"
                p = base/fname
                p.write_text(txt, encoding='utf-8')
                saved_path = str(p)
            except Exception as e:
                # não falhar download por erro de I/O; apenas não retornar saved_path
                saved_path = None
        return {
            "status":"ok",
            "schema": chosen.get("schema"),
            "nsu": chosen.get("nsu"),
            "preferred": preferred or None,
            "saved_path": saved_path,
            "xml": txt,
        }
    finally:
        if cert_tuple:
            for p in cert_tuple:
                try:
                    if p and os.path.exists(p): os.remove(p)
                except: pass

@router.post("/dfe/manifestar")
def manifestar_destinatario(
    empresa_id:int=Query(...),
    chNFe:str=Query(..., min_length=44, max_length=44),
    tpEvento:str=Query(..., description="210210=Ciencia, 210200=Confirmacao, 210220=Desconhecimento, 210240=Operacao nao Realizada"),
    nSeq:int=Query(1),
    justificativa:str|None=Query(None)
):
    """Envia manifestação do destinatário (RecepcaoEvento 4.00). Requer certificado A1 da empresa."""
    cert_tuple = None
    try:
        emp, cert_path, key_path = _load_cert_tuple(empresa_id)
        cert_tuple = (cert_path, key_path)
        # Valida CNPJ-base conforme H04
        with SessionLocal() as db:
            cert = db.execute(select(Certificado).where(Certificado.empresa_id==empresa_id)).scalar_one()
            pfx_bytes = open(cert.pfx_path,'rb').read()
            tipo, doc = pfx_extract_cnpj_cpf(pfx_bytes, cert.senha_cripto)
            if tipo == "CNPJ" and (emp.cnpj or '')[:8] != (doc or '')[:8]:
                raise HTTPException(422, "CNPJ consultado difere do CNPJ-base do certificado (H04)")
            if tipo == "CPF":
                raise HTTPException(422, "Certificado PF não suportado para manifestação do destinatário")
        verify = settings.DFE_CA_BUNDLE if settings.DFE_CA_BUNDLE else certifi.where()
        res = enviar_manifestacao(emp.cnpj, chNFe, tpEvento, nSeq, cert_tuple, verify)
        # Persistir resultado no documento mais recente com esta chave (se existir)
        try:
            with SessionLocal() as db:
                doc = db.execute(select(DFEDocumento).where(DFEDocumento.empresa_id==empresa_id, DFEDocumento.chave==chNFe).order_by(DFEDocumento.id.desc())).scalar_one_or_none()
                if doc:
                    xml_path = None
                    try:
                        # salvar XML de resposta se existir
                        resp_xml = res.get("resp_xml")
                        if resp_xml:
                            from pathlib import Path
                            base = Path(settings.STORAGE_BASE_PATH)/emp.cnpj
                            base.mkdir(parents=True, exist_ok=True)
                            fname = f"evento_{chNFe}_{tpEvento}_{nSeq}.xml"
                            p = base/fname
                            p.write_text(resp_xml, encoding='utf-8')
                            xml_path = str(p)
                    except Exception:
                        xml_path = None
                    db.execute(update(DFEDocumento).where(DFEDocumento.id==doc.id).values(
                        manifest_tp=tpEvento,
                        manifest_nseq=nSeq,
                        manifest_cstat=str(res.get("cStat") or ""),
                        manifest_xmotivo=res.get("xMotivo"),
                        manifest_xml_path=xml_path,
                        manifest_updated_at=__import__("datetime").datetime.utcnow(),
                    ))
                    db.commit()
        except Exception:
            pass
        return res
    finally:
        if cert_tuple:
            for p in cert_tuple:
                try:
                    if p and os.path.exists(p): os.remove(p)
                except: pass