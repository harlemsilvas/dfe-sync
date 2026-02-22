
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from src.store.db import SessionLocal
from src.models import CfopTransferencia

router = APIRouter()

class CfopCreate(BaseModel):
    codigo: str
    descricao: str
    tipo_operacao: str
    ativo: bool = True

class CfopUpdate(BaseModel):
    descricao: str
    tipo_operacao: str
    ativo: bool = True

@router.get("/cfops")
async def list_cfops():
    """Lista todos os CFOPs configurados"""
    with SessionLocal() as db:
        cfops = db.execute(select(CfopTransferencia)).scalars().all()
        return [
            {
                "id": cfop.id,
                "codigo": cfop.codigo,
                "descricao": cfop.descricao,
                "tipo_operacao": cfop.tipo_operacao,
                "ativo": cfop.ativo
            }
            for cfop in cfops
        ]

@router.post("/cfops")
async def create_cfop(cfop: CfopCreate):
    """Cria um novo CFOP"""
    with SessionLocal() as db:
        exists = db.execute(select(CfopTransferencia).where(CfopTransferencia.codigo == cfop.codigo)).scalar_one_or_none()
        if exists:
            raise HTTPException(409, f"CFOP {cfop.codigo} já existe")
        novo_cfop = CfopTransferencia(
            codigo=cfop.codigo,
            descricao=cfop.descricao,
            tipo_operacao=cfop.tipo_operacao,
            ativo=cfop.ativo
        )
        db.add(novo_cfop)
        db.commit()
        db.refresh(novo_cfop)
        return {
            "id": novo_cfop.id,
            "codigo": novo_cfop.codigo,
            "descricao": novo_cfop.descricao,
            "tipo_operacao": novo_cfop.tipo_operacao,
            "ativo": novo_cfop.ativo
        }

@router.put("/cfops/{cfop_id}")
async def update_cfop(cfop_id: int, cfop: CfopUpdate):
    """Atualiza um CFOP existente"""
    with SessionLocal() as db:
        obj = db.execute(select(CfopTransferencia).where(CfopTransferencia.id == cfop_id)).scalar_one_or_none()
        if not obj:
            raise HTTPException(404, f"CFOP id={cfop_id} não encontrado")
        setattr(obj, "descricao", cfop.descricao)
        setattr(obj, "tipo_operacao", cfop.tipo_operacao)
        setattr(obj, "ativo", cfop.ativo)
        db.commit()
        db.refresh(obj)
        return {
            "id": obj.id,
            "codigo": obj.codigo,
            "descricao": obj.descricao,
            "tipo_operacao": obj.tipo_operacao,
            "ativo": obj.ativo
        }


@router.delete("/cfops/{cfop_id}")
async def deactivate_cfop(cfop_id: int):
    """Desativa (soft delete) um CFOP, marcando ativo=False"""
    with SessionLocal() as db:
        obj = db.execute(select(CfopTransferencia).where(CfopTransferencia.id == cfop_id)).scalar_one_or_none()
        if not obj:
            raise HTTPException(404, f"CFOP id={cfop_id} não encontrado")
        if not obj.ativo:
            raise HTTPException(400, f"CFOP id={cfop_id} já está desativado")
        obj.ativo = False
        db.commit()
        db.refresh(obj)
        return {
            "id": obj.id,
            "codigo": obj.codigo,
            "descricao": obj.descricao,
            "tipo_operacao": obj.tipo_operacao,
            "ativo": obj.ativo
        }