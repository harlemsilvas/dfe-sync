# src/api/routes/certificados.py
"""
Router de certificados - COMPATÍVEL COM SCHEMA REAL DO BANCO

Colunas reais da tabela 'certificados':
- id, empresa_id, tipo, pfx_path, senha_cripto, cnpj, pfx_file, pfx_password_encrypted

Mapeamento para frontend:
- pfx_path → nome_arquivo
- senha_cripto → senha (apenas leitura, mascarada)
- Campos inexistentes → valores padrão
"""

"""
         Column         |          Type          | Collation | Nullable |                 Default
------------------------+------------------------+-----------+----------+------------------------------------------
 id                     | integer                |           | not null | nextval('certificados_id_seq'::regclass)
 empresa_id             | integer                |           |          |
 tipo                   | character varying(2)   |           |          | 'A1'::character varying
 pfx_path               | text                   |           |          |
 senha_cripto           | text                   |           |          |
 cnpj                   | character varying      |           |          |
 pfx_file               | bytea                  |           |          |
 pfx_password_encrypted | character varying      |           |          |
 nome_empresa           | character varying(255) |           |          |
 valido_de              | character varying(25)  |           |          |
 valido_ate             | character varying(25)  |           |          |
 status_validacao       | character varying(50)  |           |          |
Indexes:
    "certificados_pkey" PRIMARY KEY, btree (id)
    "ix_certificados_cnpj" UNIQUE, btree (cnpj)
    "ix_certificados_id" btree (id)
Foreign-key constraints:
    "certificados_empresa_id_fkey" FOREIGN KEY (empresa_id) REFERENCES empresas(id)


 id | empresa_id | tipo |   pfx_path   | senha_cripto |      cnpj      | pfx_file | pfx_password_encrypted |                   nome_empresa                   |      valido_de      |     valido_ate      | status_validacao
----+------------+------+--------------+--------------+----------------+----------+------------------------+--------------------------------------------------+---------------------+---------------------+------------------
  3 |          1 | A1   | 25148168.pfx | 513094       | 51309435000153 |          |                        | ABC CENTER DISTRIBUIDORA LTDA:51309435000153     | 2025-07-07 14:20:36 | 2026-07-07 14:20:36 | valido
  4 |          9 | A1   | 19330326.pfx | 10312708     | 19330326000105 |          |                        | HRM MOTOS PECAS E ACESSORIOS LTDA:19330326000105 | 2025-04-28 15:40:56 | 2026-04-28 15:40:56 | valido
(2 rows)

"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import base64
from datetime import datetime, timezone
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend

from src.store.db import get_db
from src.models import Certificado, Empresa

# ✅ Router com prefixo correto
router = APIRouter(
    prefix="/certificados",
    tags=["Certificados"],
)

# =============================================================================
# SCHEMAS PYDANTIC (Frontend-friendly)
# =============================================================================

class CertificadoCreate(BaseModel):
    """Schema para criação - nomes amigáveis para frontend"""
    empresa_id: int = Field(..., gt=0)
    nome_arquivo: str = Field(..., min_length=1)  # → mapeado para pfx_path
    senha: str = Field(..., min_length=1)          # → mapeado para senha_cripto
    arquivo_base64: Optional[str] = None
    valido_ate: Optional[str] = None
    valido_de: Optional[str] = None
    nome_empresa: Optional[str] = None
    status_validacao: Optional[str] = None
    ativo: bool = True

    @field_validator('empresa_id', mode='before')
    @classmethod
    def parse_empresa_id(cls, v):
        return int(v) if isinstance(v, str) else v

class CertificadoUpdate(BaseModel):
    """Schema para atualização - campos opcionais"""
    empresa_id: Optional[int] = None
    nome_arquivo: Optional[str] = None  # → pfx_path
    senha: Optional[str] = None         # → senha_cripto
    valido_ate: Optional[str] = None    # Ignorado
    ativo: Optional[bool] = None        # Ignorado

class CertificadoResponse(BaseModel):
    """Schema de resposta - nomes amigáveis + valores padrão"""
    id: int
    empresa_id: int
    empresa_nome: str
    empresa_cnpj: str
    nome_arquivo: str          # ← vem de pfx_path
    nome_empresa: Optional[str] = None
    valido_de: Optional[str] = None
    valido_ate: Optional[str] = ""
    status_validacao: Optional[str] = None
    ativo: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True

class CertificadoValidateRequest(BaseModel):
    arquivo_base64: str
    senha: str

class CertificadoValidateResponse(BaseModel):
    sucesso: bool
    dados: dict | None = None
    erro: str | None = None

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def _decode_base64(b64: str) -> bytes:
    if ',' in b64:
        b64 = b64.split(',')[1]
    return base64.b64decode(b64)

def _validate_pfx_certificate(pfx_bytes: bytes, senha: str) -> dict:
    try:
        private_key, certificate, _ = pkcs12.load_key_and_certificates(
            pfx_bytes, senha.encode('utf-8'), backend=default_backend()
        )
        
        cn = None
        for attr in certificate.subject:
            if attr.oid._name == 'commonName':
                cn = attr.value
                break
        
        valid_from = certificate.not_valid_before_utc
        valid_until = certificate.not_valid_after_utc
        now = datetime.now(timezone.utc)
        
        return {
            "valido": True,
            "cn": cn,
            "emissor": str(certificate.issuer),
            "valido_de": valid_from.strftime("%Y-%m-%d %H:%M:%S"),
            "valido_ate": valid_until.strftime("%Y-%m-%d %H:%M:%S"),
            "expirado": now > valid_until,
            "ainda_nao_valido": now < valid_from,
            "ativo": not (now > valid_until or now < valid_from)
        }
    except Exception as e:
        err = str(e).lower()
        if "password" in err or "mac" in err or "invalid" in err:
            return {"valido": False, "erro": "Senha do certificado inválida"}
        return {"valido": False, "erro": f"Erro ao processar: {str(e)}"}

# =============================================================================
# ENDPOINTS - TODOS COMPATÍVEIS COM SCHEMA REAL
# =============================================================================

# 🔹 GET - Listar certificados
@router.get("/", response_model=List[CertificadoResponse])
async def list_certificados(db: Session = Depends(get_db)):
    """Lista certificados usando APENAS colunas reais do banco"""
    resultados = db.execute(
        select(Certificado, Empresa)
        .join(Empresa, Certificado.empresa_id == Empresa.id)
        .order_by(Certificado.id.desc())
    ).all()
    
    return [
        {
            "id": c.id,
            "empresa_id": c.empresa_id,
            "empresa_nome": getattr(e, 'razao_social', 'Desconhecida') if e else "Desconhecida",
            "empresa_cnpj": getattr(e, 'cnpj', '') if e else "",
            
            # ✅ Mapear coluna real → nome amigável
            "nome_arquivo": getattr(c, 'pfx_path', None) or "certificado.pfx",
            
            # ✅ Campos inexistentes → valores padrão
            "valido_ate": getattr(c, 'valido_ate', None) or "",
            "ativo": True,           
            "nome_empresa": getattr(c, 'nome_empresa', None),
            "valido_de": getattr(c, 'valido_de', None),
            "status_validacao": getattr(c, 'status_validacao', None),
            "created_at": getattr(c, 'created_at', None),
            "updated_at": getattr(c, 'updated_at', None),
        }
        for c, e in resultados
    ]

# 🔹 POST - Criar certificado
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=CertificadoResponse)
async def create_certificado(
    cert_: CertificadoCreate,
    db: Session = Depends(get_db)
):
    empresa = db.get(Empresa, cert_.empresa_id)
    if not empresa:
        raise HTTPException(404, detail="Empresa não encontrada")
    
    nome_empresa = None
    valido_de = None
    valido_ate = None
    status_validacao = None
    if cert_.arquivo_base64:
        try:
            pfx_bytes = _decode_base64(cert_.arquivo_base64)
            validacao = _validate_pfx_certificate(pfx_bytes, cert_.senha)
            if not validacao["valido"]:
                status_validacao = "invalido"
                raise HTTPException(400, detail=f"Certificado inválido: {validacao['erro']}")
            if validacao["expirado"]:
                status_validacao = "expirado"
                raise HTTPException(400, detail="Certificado expirado")
            nome_empresa = validacao.get("cn")
            valido_de = validacao.get("valido_de")
            valido_ate = validacao.get("valido_ate")
            status_validacao = "valido"
        except Exception as e:
            status_validacao = "erro"
            raise HTTPException(400, detail=f"Erro ao validar: {str(e)}")
    
    # Verificar certificado existente para este CNPJ
    existente = db.execute(
        select(Certificado).where(Certificado.cnpj == empresa.cnpj)
    ).scalar_one_or_none()
    if existente:
        raise HTTPException(409, detail="Já existe certificado para este CNPJ")
    
    # ✅ Criar usando COLUNAS REAIS do banco
    novo = Certificado(
        empresa_id=cert_.empresa_id,
        cnpj=empresa.cnpj,
        tipo="A1",
        pfx_path=cert_.nome_arquivo,
        senha_cripto=cert_.senha,
        nome_empresa=nome_empresa,
        valido_de=valido_de,
        valido_ate=valido_ate,
        status_validacao=status_validacao,
        # pfx_file=pfx_bytes se quiser salvar o arquivo binário
    )
    
    db.add(novo)
    db.commit()
    db.refresh(novo)
    
    # ✅ Resposta com mapeamento amigável
    return {
        "id": novo.id,
        "empresa_id": novo.empresa_id,
        "empresa_nome": empresa.razao_social,
        "empresa_cnpj": empresa.cnpj,
        "nome_arquivo": novo.pfx_path or cert_.nome_arquivo,
        "nome_empresa": novo.nome_empresa,
        "valido_de": novo.valido_de,
        "valido_ate": novo.valido_ate,
        "status_validacao": novo.status_validacao,
        "ativo": True,
        "created_at": None,
        "updated_at": None
    }

# 🔹 PUT - Atualizar certificado
@router.put("/{cert_id}/", response_model=CertificadoResponse)
async def update_certificado(
    cert_id: int,
    cert_: CertificadoUpdate,
    db: Session = Depends(get_db)
):
    cert = db.get(Certificado, cert_id)
    if not cert:
        raise HTTPException(404, detail="Certificado não encontrado")
    
    # ✅ Mapear campos do schema → colunas reais
    update_map = {
        'empresa_id': 'empresa_id',
        'nome_arquivo': 'pfx_path',
        'senha': 'senha_cripto',
        'nome_empresa': 'nome_empresa',
        'valido_de': 'valido_de',
        'valido_ate': 'valido_ate',
        'status_validacao': 'status_validacao',
    }
    update_data = cert_.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None and field in update_map:
            db_col = update_map[field]
            if db_col and hasattr(cert, db_col):
                setattr(cert, db_col, value)
    db.commit()
    db.refresh(cert)
    empresa = db.get(Empresa, cert.empresa_id)
    return {
        "id": cert.id,
        "empresa_id": cert.empresa_id,
        "empresa_nome": getattr(empresa, 'razao_social', '') if empresa else "",
        "empresa_cnpj": getattr(empresa, 'cnpj', '') if empresa else "",
        "nome_arquivo": getattr(cert, 'pfx_path', None) or "certificado.pfx",
        "nome_empresa": cert.nome_empresa,
        "valido_de": cert.valido_de,
        "valido_ate": cert.valido_ate,
        "status_validacao": cert.status_validacao,
        "ativo": True,
        "created_at": None,
        "updated_at": None
    }

# 🔹 DELETE - Excluir certificado
@router.delete("/{cert_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_certificado(cert_id: int, db: Session = Depends(get_db)):
    cert = db.get(Certificado, cert_id)
    if not cert:
        raise HTTPException(404, detail="Certificado não encontrado")
    db.delete(cert)
    db.commit()
    return [
        {
            "id": c.id,
            "empresa_id": c.empresa_id,
            "empresa_nome": getattr(e, 'razao_social', 'Desconhecida') if e else "Desconhecida",
            "empresa_cnpj": getattr(e, 'cnpj', '') if e else "",
            "nome_arquivo": getattr(c, 'pfx_path', None) or "certificado.pfx",
            "nome_empresa": getattr(c, 'nome_empresa', None),
            "valido_de": getattr(c, 'valido_de', None),
            "valido_ate": getattr(c, 'valido_ate', None),
            "status_validacao": getattr(c, 'status_validacao', None),
            "ativo": True,
            "created_at": None,
            "updated_at": None
        }
        for c, e in resultados
    ]
# 🔹 GET - Debug: Ver schema real (apenas para desenvolvimento)
@router.get("/debug/schema")
async def debug_schema(db: Session = Depends(get_db)):
    """Retorna colunas reais da tabela (remover em produção)"""
    from sqlalchemy import inspect
    try:
        inspector = inspect(db.bind)
        columns = inspector.get_columns('certificados')
        return {
            "table": "certificados",
            "columns": [
                {"name": col['name'], "type": str(col['type']), "nullable": col['nullable']}
                for col in columns
            ],
            "mapeamento_frontend": {
                "pfx_path": "nome_arquivo",
                "senha_cripto": "senha (mascarada)",
                "campos_ficticios": ["valido_ate", "ativo", "created_at", "updated_at"]
            }
        }
    except Exception as e:
        return {"error": str(e)}