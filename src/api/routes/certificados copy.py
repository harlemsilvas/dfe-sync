from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field  # ← Adicionado
import base64  # ← Adicionado
from datetime import datetime  # ← Adicionado
from cryptography.hazmat.primitives.serialization import pkcs12  # ← Adicionado
from cryptography.hazmat.backends import default_backend  # ← Adicionado

from src.store.db import get_db
from src.schemas.certificado import CertificadoCreate, Certificado as CertificadoSchema
from src.crud import certificados as crud_certificados

router = APIRouter(
    prefix="/certificados",
    tags=["certificados"],
)

# =============================================================================
# SCHEMAS ADICIONAIS
# =============================================================================

class CertificadoValidateRequest(BaseModel):
    """Schema para requisição de validação de certificado"""
    arquivo_base64: str = Field(..., description="Conteúdo do certificado PFX em base64")
    senha: str = Field(..., description="Senha do certificado")

class CertificadoValidateResponse(BaseModel):
    """Schema para resposta de validação"""
    sucesso: bool
    dados: dict | None = None
    erro: str | None = None
    
# =============================================================================
# FUNÇÕES AUXILIARES
# =
def _validate_pfx_certificate(pfx_bytes: bytes, senha: str) -> dict:
    """Valida certificado PFX e extrai informações"""
    try:
        # Carregar certificado com senha
        private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
            pfx_bytes, 
            senha.encode('utf-8'),
            backend=default_backend()
        )
        
        # Extrair informações do certificado
        subject = certificate.subject
        issuer = certificate.issuer
        
        # Extrair CN (Common Name)
        cn = None
        for attr in subject:
            if attr.oid._name == 'commonName':
                cn = attr.value
                break
        
        # Datas de validade (compatível com diferentes versões da cryptography)
        valid_from = getattr(certificate, 'not_valid_before_utc', certificate.not_valid_before)
        valid_until = getattr(certificate, 'not_valid_after_utc', certificate.not_valid_after)
        
        # Verificar validade atual
        now = datetime.now(valid_until.tzinfo) if valid_until.tzinfo else datetime.utcnow()
        is_expired = now > valid_until
        is_not_yet_valid = now < valid_from
        
        return {
            "valido": True,
            "cn": cn,
            "emissor": str(issuer),
            "valido_de": valid_from.strftime("%Y-%m-%d %H:%M:%S"),
            "valido_ate": valid_until.strftime("%Y-%m-%d %H:%M:%S"),
            "expirado": is_expired,
            "ainda_nao_valido": is_not_yet_valid,
            "ativo": not is_expired and not is_not_yet_valid
        }
        
    except Exception as e:
        error_msg = str(e).lower()
        if "password" in error_msg or "mac" in error_msg or "invalid" in error_msg:
            return {"valido": False, "erro": "Senha do certificado inválida"}
        return {"valido": False, "erro": f"Erro ao processar certificado: {str(e)}"}    

# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/")
async def list_certificados(db: Session = Depends(get_db)):
    """Lista todos os certificados cadastrados"""
    try:
        certificados = crud_certificados.get_all_certificados(db)
        return certificados
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    
@router.post("/validar", response_model=CertificadoValidateResponse)
async def validar_certificado(request: CertificadoValidateRequest):
    """
    Valida um certificado PFX sem salvá-lo no banco.
    Aceita JSON com arquivo em base64 e senha.
    """
    try:
        # Decodificar base64 (remover prefixo data: se existir)
        base64_content = request.arquivo_base64
        if ',' in base64_content:
            base64_content = base64_content.split(',')[1]
        
        pfx_bytes = base64.b64decode(base64_content)
        
        # Validar certificado
        resultado = _validate_pfx_certificate(pfx_bytes, request.senha)
        
        return CertificadoValidateResponse(
            sucesso=resultado["valido"],
            dados=resultado if resultado["valido"] else None,
            erro=resultado.get("erro") if not resultado["valido"] else None
        )
        
    except Exception as e:
        return CertificadoValidateResponse(
            sucesso=False,
            erro=f"Erro inesperado: {str(e)}"
        )

@router.post("/", response_model=CertificadoSchema)
async def upload_certificado(
    cnpj: str = Form(...),
    pfx_password: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # Validar se tem um arquivo
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Validar extensão do arquivo
        if not file.filename.lower().endswith('.pfx'):
            raise HTTPException(status_code=400, detail=f"Invalid file extension. Got: {file.filename}. Expected: .pfx")

        pfx_file_content = await file.read()
        
        if len(pfx_file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file provided")

        # Verificar se o CNPJ já está cadastrado
        db_certificado = crud_certificados.get_certificado_by_cnpj(db, cnpj=cnpj)
        if db_certificado:
            raise HTTPException(status_code=400, detail="CNPJ already registered")

        # Criar o certificado
        certificado_create = CertificadoCreate(cnpj=cnpj, pfx_password=pfx_password)
        
        return crud_certificados.create_certificado(db=db, schema=certificado_create, pfx_file=pfx_file_content)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
