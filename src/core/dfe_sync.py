import os
from pathlib import Path
from typing import Tuple
from lxml import etree
from sqlalchemy import select, insert, update
from src.store.db import SessionLocal
from src.models import Empresa, CursorDFe, DFEDocumento
from src.settings import settings
from src.ws.dfe_client import pull_until_idle, nfe_consultar_nsu

def _cnpj_digits(s:str)->str: return "".join([c for c in s if c.isdigit()])

def ensure_cursor(empresa_id:int) -> str:
    with SessionLocal() as db:
        cur = db.execute(select(CursorDFe).where(CursorDFe.empresa_id==empresa_id)).scalar_one_or_none()
        if not cur:
            db.execute(insert(CursorDFe).values(empresa_id=empresa_id, ultimo_nsu="000000000000000", max_nsu="000000000000000"))
            db.commit()
            return "000000000000000"
        return cur.ultimo_nsu

def _save_xml(empresa_cnpj:str, nsu:str, schema:str, xml_bytes:bytes) -> str:
    base = Path(settings.STORAGE_BASE_PATH)/empresa_cnpj
    base.mkdir(parents=True, exist_ok=True)
    filename = f"{nsu}_{schema}.xml"
    path = base/filename
    path.write_bytes(xml_bytes)
    return str(path)

def run_distribution(empresa_id:int, cnpj:str, cert_tuple:Tuple[str,str], verify_ca:str|bool=None) -> dict:
    cnpj = _cnpj_digits(cnpj)
    last_nsu = ensure_cursor(empresa_id)
    processed = 0; last_ult = last_nsu; last_max = last_nsu
    by_schema: dict[str,int] = {}
    prev_nsu_int = int(last_nsu)
    CONSNSU_CAP = 10  # máximo de NSUs faltantes a consultar por execução
    for pack in pull_until_idle(cnpj, last_nsu, cert_tuple, verify_ca):
        # Tratamento de erros e paradas explícitas
        if "error" in pack:
            return {"ok": False, "error": pack}
        if pack.get("stopped"):
            # Atualiza cursor e retorna status amigável (ex.: consumo indevido / serviço paralisado)
            try:
                with SessionLocal() as db:
                    db.execute(update(CursorDFe).where(CursorDFe.empresa_id==empresa_id).values(
                        ultimo_nsu=pack.get("ultNSU", last_ult), max_nsu=pack.get("maxNSU", last_max)
                    ))
                    db.commit()
            except Exception:
                pass
            return {
                "ok": True,
                "processed": processed,
                "ultNSU": pack.get("ultNSU", last_ult),
                "maxNSU": pack.get("maxNSU", last_max),
                "by_schema": by_schema,
                "stopped": True,
                "reason": pack.get("reason"),
                "wait_sec": pack.get("wait_sec"),
            }

        docs = pack.get("docs") or pack.get("batch") or []
        # Ordenar NSUs recebidos para detectar lacunas
        nsus_sorted: list[int] = []
        for d in docs:
            try:
                nsus_sorted.append(int(d["nsu"]))
            except Exception:
                continue
        nsus_sorted.sort()
        # Persistir
        with SessionLocal() as db:
            for d in docs:
                xml = d["xml"]
                # extrair chave se houver (procNFe/resNFe)
                chave = None
                try:
                    node = etree.fromstring(xml)
                    ns={"nfe":"http://www.portalfiscal.inf.br/nfe"}
                    ch = node.find(".//nfe:chNFe", ns)
                    if ch is not None: chave = ch.text
                except Exception:
                    pass
                path = _save_xml(cnpj, d["nsu"], d["schema"], xml)
                db.execute(insert(DFEDocumento).values(
                    empresa_id=empresa_id, nsu=d["nsu"], schema=d["schema"], chave=chave, caminho_xml=path
                ))
                sch = d["schema"] or "?"
                by_schema[sch] = by_schema.get(sch, 0) + 1
            # atualizar cursor
            db.execute(update(CursorDFe).where(CursorDFe.empresa_id==empresa_id).values(
                ultimo_nsu=pack.get("ultNSU", last_ult), max_nsu=pack.get("maxNSU", last_max)
            ))
            db.commit()
        processed += len(docs)
        last_ult = pack.get("ultNSU", last_ult); last_max = pack.get("maxNSU", last_max)
        # Recuperar lacunas com consNSU (limitado)
        fetched_missing = 0
        for nsu_int in nsus_sorted:
            if fetched_missing >= CONSNSU_CAP:
                break
            if nsu_int - prev_nsu_int > 1:
                gap_start = prev_nsu_int + 1
                gap_end = min(nsu_int - 1, gap_start + (CONSNSU_CAP - fetched_missing) - 1)
                for miss in range(gap_start, gap_end + 1):
                    res = nfe_consultar_nsu(cnpj, str(miss), cert_tuple, verify_ca)
                    if 'error' in res:
                        break
                    for d in (res.get('docs') or []):
                        xml = d["xml"]
                        chave = None
                        try:
                            node = etree.fromstring(xml)
                            ns={"nfe":"http://www.portalfiscal.inf.br/nfe"}
                            ch = node.find(".//nfe:chNFe", ns)
                            if ch is not None: chave = ch.text
                        except Exception:
                            pass
                        path = _save_xml(cnpj, d["nsu"], d["schema"], xml)
                        with SessionLocal() as db:
                            db.execute(insert(DFEDocumento).values(
                                empresa_id=empresa_id, nsu=d["nsu"], schema=d["schema"], chave=chave, caminho_xml=path
                            ))
                            db.commit()
                        processed += 1
                        sch = d["schema"] or "?"
                        by_schema[sch] = by_schema.get(sch, 0) + 1
                    fetched_missing += 1
            prev_nsu_int = nsu_int
    return {"ok":True,"processed":processed,"ultNSU":last_ult,"maxNSU":last_max, "by_schema": by_schema}