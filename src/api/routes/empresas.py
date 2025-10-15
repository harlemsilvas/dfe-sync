from fastapi import APIRouter, UploadFile, Form, HTTPException
from sqlalchemy import insert, select, update
from src.store.db import SessionLocal
from src.models import Empresa, Certificado, CursorDFe
from pathlib import Path
from src.settings import settings

router = APIRouter()

@router.post("/empresas")
async def create_empresa(cnpj:str=Form(...), razao_social:str=Form(""), ambiente:str=Form("HOMOLOG")):
    cnpj_digits = "".join(filter(str.isdigit, cnpj))
    with SessionLocal() as db:
        exists = db.execute(select(Empresa).where(Empresa.cnpj==cnpj_digits)).scalar_one_or_none()
        if exists: raise HTTPException(409,"CNPJ jÃ¡ cadastrado")
        db.execute(insert(Empresa).values(cnpj=cnpj_digits, razao_social=razao_social, ambiente=ambiente))
        db.commit()
        emp = db.execute(select(Empresa).where(Empresa.cnpj==cnpj_digits)).scalar_one()
        db.execute(insert(CursorDFe).values(empresa_id=emp.id, ultimo_nsu="000000000000000", max_nsu="000000000000000"))
        db.commit()
        return {"id":emp.id,"cnpj":cnpj_digits}

@router.post("/empresas/{empresa_id}/cert")
async def upload_cert(empresa_id:int, certificado_pfx:UploadFile, senha_certificado:str=Form(...)):
    # OBS: cifre a senha em produÃ§Ã£o (Vault/KMS). Aqui guardamos caminho do PFX e senha cifrada placeholder.
    base = Path(settings.CERTS_BASE_PATH); base.mkdir(parents=True, exist_ok=True)
    pfx_path = base / f"{empresa_id}.pfx"
    pfx_bytes = await certificado_pfx.read()
    pfx_path.write_bytes(pfx_bytes)
    with SessionLocal() as db:
        db.execute(insert(Certificado).values(empresa_id=empresa_id, pfx_path=str(pfx_path), senha_cripto=senha_certificado))
        db.commit()
    return {"ok":True}