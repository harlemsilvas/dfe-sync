import os
from pathlib import Path
from typing import Tuple
from lxml import etree
from sqlalchemy import select, insert, update
from src.store.db import SessionLocal
from src.models import Empresa, CursorDFe, DFEDocumento
from src.settings import settings
from src.ws.dfe_client import pull_until_idle

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
    for pack in pull_until_idle(cnpj, last_nsu, cert_tuple, verify_ca):
        if "error" in pack:
            return {"ok":False, "error":pack}
        docs = pack["batch"]
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
            # atualizar cursor
            db.execute(update(CursorDFe).where(CursorDFe.empresa_id==empresa_id).values(
                ultimo_nsu=pack["ultNSU"], max_nsu=pack["maxNSU"]
            ))
            db.commit()
        processed += len(docs)
        last_ult = pack["ultNSU"]; last_max = pack["maxNSU"]
    return {"ok":True,"processed":processed,"ultNSU":last_ult,"maxNSU":last_max}
