from fastapi import APIRouter

# Rota placeholder para evitar falha de import. Pode ser implementada conforme necessário.
router = APIRouter()
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from src.public.nfe_sp_public import consulta_publica_sp

router = APIRouter()

@router.get("/nfe/sp/publica/{chave}")
def consulta_publica(chave: str):
    res = consulta_publica_sp(chave)
    if res.get("status") == "error":
        raise HTTPException(502, res.get("detail"))
    return res

# Rota mock base /api/nfe/ para evitar retorno HTML (ex: index) quando o front
# monta URL incorreta ou incompleta. Retorna sempre JSON 400 padronizado.
@router.get("/nfe/", include_in_schema=False)
@router.get("/nfe", include_in_schema=False)
def nfe_base_placeholder():
    return JSONResponse(
        status_code=400,
        content={"status": "error", "detail": "missing_chave", "expected": "usar /api/nfe/sp/publica/{chave}"},
    )
