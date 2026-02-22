# src/api/routes/empresas.py
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, Form
from sqlalchemy import insert, select
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from src.store.db import get_db
from src.models import Empresa, CursorDFe, Certificado  # ← Importe Certificado também

router = APIRouter()

# 🔹 Schema Pydantic para validação do JSON de entrada
class EmpresaCreate(BaseModel):
    cnpj: str = Field(..., min_length=14, max_length=14)
    razao_social: str = Field(..., min_length=3, max_length=200)
    nome_fantasia: Optional[str] = ""
    ambiente: str = "HOMOLOG"
    monitorada: bool = True
    ativo: bool = True
    pasta_origem: Optional[str] = ""

    @field_validator('cnpj')
    @classmethod
    def sanitize_cnpj(cls, v: str) -> str:
        """Remove formatação e mantém apenas dígitos"""
        return "".join(filter(str.isdigit, v))

# ✅ NOVO: Schema para atualização (todos os campos opcionais)
class EmpresaUpdate(BaseModel):
    cnpj: Optional[str] = None
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    ambiente: Optional[str] = None
    monitorada: Optional[bool] = None
    ativo: Optional[bool] = None
    pasta_origem: Optional[str] = None

    @field_validator('cnpj')
    @classmethod
    def sanitize_cnpj(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return "".join(filter(str.isdigit, v))
        return v
    
class EmpresaResponse(BaseModel):
    id: int
    cnpj: str
    razao_social: str
    ambiente: str
    ativo: bool
    monitorada: bool
    nome_fantasia: Optional[str] = None
    class Config:
        from_attributes = True  # Permite conversão de ORM → Pydantic

# =============================================================================
# ENDPOINTS
# =============================================================================

# 🔹 GET - Listar empresas
@router.get("/empresas", response_model=list[EmpresaResponse])
async def list_empresas(db: Session = Depends(get_db)):
    """Lista todas as empresas cadastradas"""
    empresas = db.execute(select(Empresa)).scalars().all()
    return empresas


# 🔹 POST - Criar empresa (ACEITA JSON ✅)
@router.post("/empresas", status_code=status.HTTP_201_CREATED)
async def create_empresa(
    empresa_data: EmpresaCreate,  # ✅ Note os dois pontos ":"
    db: Session = Depends(get_db)
):
    # CNPJ já foi sanitizado pelo validator do Pydantic
    cnpj_digits = empresa_data.cnpj
    
    # Verificar duplicidade
    exists = db.execute(select(Empresa).where(Empresa.cnpj == cnpj_digits)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="CNPJ já cadastrado")
    
    # Criar nova empresa
    nova_empresa = Empresa(
        cnpj=cnpj_digits,
        razao_social=empresa_data.razao_social,
        nome_fantasia=empresa_data.nome_fantasia,
        ambiente=empresa_data.ambiente,
        monitorada=empresa_data.monitorada,
        ativo=1 if empresa_data.ativo else 0
    )
    db.add(nova_empresa)
    db.commit()
    db.refresh(nova_empresa)
    
    # Inicializar cursor DFe
    db.execute(insert(CursorDFe).values(
        empresa_id=nova_empresa.id,
        ultimo_nsu="000000000000000",
        max_nsu="000000000000000"
    ))
    db.commit()
    
    return nova_empresa

# 🔹 PUT - Atualizar empresa (✅ NOVO ENDPOINT)
@router.put("/empresas/{empresa_id}", response_model=EmpresaResponse)
async def update_empresa(
    empresa_id: int,
    empresa_data: EmpresaUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza apenas os campos fornecidos de uma empresa existente"""
    
    # 1. Buscar empresa
    empresa = db.get(Empresa, empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    # 2. Atualizar apenas campos fornecidos (não None)
    update_data = empresa_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if value is not None:
            # Sanitizar CNPJ se estiver sendo atualizado
            if field == 'cnpj' and value:
                value = "".join(filter(str.isdigit, value))
                # Verificar se novo CNPJ já existe em outra empresa
                exists = db.execute(select(Empresa).where(Empresa.cnpj == value, Empresa.id != empresa_id)).scalar_one_or_none()
                if exists:
                    raise HTTPException(status_code=409, detail="CNPJ já cadastrado em outra empresa")
            
            setattr(empresa, field, value)
    
    # 3. Normalizar campo 'ativo' (int no DB, bool no schema)
    if hasattr(empresa, 'ativo') and isinstance(empresa.ativo, bool):
        empresa.ativo = 1 if empresa.ativo else 0
    
    db.commit()
    db.refresh(empresa)
    
    return empresa


# 🔹 POST - Upload de certificado (mantém Form, pois é upload de arquivo)
@router.post("/empresas/{empresa_id}/cert")
async def upload_cert(
    empresa_id: int,
    certificado_pfx: UploadFile,
    senha_certificado: str = Form(...),
    db: Session = Depends(get_db)
):
    from pathlib import Path
    from src.settings import settings
    
    # Verificar se empresa existe
    empresa = db.get(Empresa, empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    # Salvar arquivo PFX
    base = Path(settings.CERTS_BASE_PATH)
    base.mkdir(parents=True, exist_ok=True)
    pfx_path = base / f"{empresa_id}_{certificado_pfx.filename}"
    
    contents = await certificado_pfx.read()
    pfx_path.write_bytes(contents)
    
    # Registrar certificado no banco
    # ⚠️ Em produção: criptografar a senha antes de salvar!
    db.execute(insert(Certificado).values(
        empresa_id=empresa_id,
        nome_arquivo=certificado_pfx.filename,
        pfx_path=str(pfx_path),
        senha_cripto=senha_certificado,  # ← Criptografar em produção!
        ativo=True
    ))
    db.commit()
    
    return {"ok": True, "caminho": str(pfx_path)}