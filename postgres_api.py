#postgres_api.py
""" 
API de administração com banco de dados PostgreSQL
Versão simplificada que não depende das configurações existentes
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509 import Certificate
import tempfile
import base64
from sqlalchemy.orm import Session
from sqlalchemy import select, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Index, Numeric, LargeBinary, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column

# Configuração direta do banco
DATABASE_URL = "postgresql+psycopg://dfe:dfe@localhost:5432/dfe"

# Configuração SQLAlchemy
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modelos SQLAlchemy simplificados
class Empresa(Base):
    __tablename__ = "empresas"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, index=True)
    razao_social: Mapped[str] = mapped_column(String(200))
    ambiente: Mapped[str] = mapped_column(String(10), default="HOMOLOG")
    ativo: Mapped[int] = mapped_column(Integer, default=1)
    monitorada: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

class Certificado(Base):
    __tablename__ = "certificados"
    
    id: Mapped[int] = mapped_column(primary_key=True)
        from sqlalchemy import select
        from src.store.db import SessionLocal, Base
        from src.settings import settings

        # Usa settings.DB_URL do .env para garantir unicidade
        print("🔗 Banco de dados:", settings.DB_URL)
# Criar tabelas se não existirem
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas criadas/verificadas no PostgreSQL")
except Exception as e:
    print(f"❌ Erro ao criar tabelas: {e}")

# Modelos Pydantic para API
class EmpresaCreate(BaseModel):
    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str] = ""
    monitorada: bool = True
    pasta_origem: Optional[str] = ""
    ativo: bool = True

class EmpresaUpdate(BaseModel):
    cnpj: Optional[str] = None
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    monitorada: Optional[bool] = None
    pasta_origem: Optional[str] = None
    ativo: Optional[bool] = None

class CertificadoCreate(BaseModel):
    empresa_id: int
    nome_arquivo: str
    senha: str
    arquivo_base64: Optional[str] = ""
    valido_ate: Optional[str] = ""
    ativo: bool = True

class CertificadoUpdate(BaseModel):
    empresa_id: Optional[int] = None
    nome_arquivo: Optional[str] = None
    senha: Optional[str] = None
    valido_ate: Optional[str] = None
    ativo: Optional[bool] = None

# Configuração da API
app = FastAPI(
    title="DFE Sync - API de Administração",
    description="API para gerenciamento de empresas e certificados com PostgreSQL",
    version="2.0.0"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_timestamp():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Funções de validação de certificado
def create_temp_certificate_file(base64_content: str) -> str:
    """Cria arquivo temporário com o conteúdo do certificado em base64"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx')
    
    try:
        # Decodifica o base64
        if ',' in base64_content:
            # Remove o prefixo "data:application/x-pkcs12;base64," se existir
            base64_content = base64_content.split(',')[1]
        
        certificate_data = base64.b64decode(base64_content)
        temp_file.write(certificate_data)
        temp_file.flush()
        return temp_file.name
    finally:
        temp_file.close()

def validate_certificate(senha: str, arquivo_base64: str) -> dict:
    """Valida certificado PFX/P12 com senha e extrai informações"""
    
    temp_file_path = None
    try:
        # Cria arquivo temporário
        temp_file_path = create_temp_certificate_file(arquivo_base64)
        
        # Lê o arquivo do certificado
        with open(temp_file_path, 'rb') as f:
            pfx_data = f.read()
        
        # Tenta carregar o certificado com a senha
        try:
            private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                pfx_data, 
                senha.encode('utf-8')
            )
        except ValueError as e:
            if "invalid" in str(e).lower() or "password" in str(e).lower():
                return {
                    "valido": False,
                    "erro": "Senha do certificado inválida",
                    "detalhes": str(e)
                }
            else:
                return {
                    "valido": False,
                    "erro": "Erro ao processar certificado",
                    "detalhes": str(e)
                }
        
        # Extrai informações do certificado
        subject = certificate.subject
        issuer = certificate.issuer
        
        # Extrai CN (Common Name) do subject
        cn = None
        for attribute in subject:
            if attribute.oid._name == 'commonName':
                cn = attribute.value
                break
        
        # Extrai datas de validade
        valid_from = certificate.not_valid_before
        valid_until = certificate.not_valid_after
        
        # Verifica se o certificado ainda está válido
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
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
        return {
            "valido": False,
            "erro": "Erro inesperado ao validar certificado",
            "detalhes": str(e)
        }
    finally:
        # Remove arquivo temporário
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

# ENDPOINTS DE EMPRESAS
@app.get("/api/empresas")
def list_empresas(db: Session = Depends(get_db)):
    """Listar todas as empresas"""
    try:
        empresas = db.execute(select(Empresa).order_by(Empresa.id)).scalars().all()
        return [
            {
                "id": empresa.id,
                "cnpj": empresa.cnpj,
                "razao_social": empresa.razao_social,
                "nome_fantasia": "",
                "monitorada": empresa.monitorada,
                "ativo": bool(empresa.ativo),
                "pasta_origem": "",
                "created_at": get_current_timestamp(),
                "updated_at": get_current_timestamp()
            } for empresa in empresas
        ]
    except Exception as e:
        print(f"❌ Erro ao listar empresas: {e}")
        raise HTTPException(500, f"Erro interno do servidor: {str(e)}")

@app.post("/api/empresas", status_code=201)
def create_empresa(empresa_data: EmpresaCreate, db: Session = Depends(get_db)):
    """Criar nova empresa"""
    try:
        # Verificar se CNPJ já existe
        existing_empresa = db.execute(select(Empresa).where(Empresa.cnpj == empresa_data.cnpj)).scalar_one_or_none()
        if existing_empresa:
            raise HTTPException(409, f"CNPJ {empresa_data.cnpj} já cadastrado")
        
        # Criar nova empresa
        nova_empresa = Empresa(
            cnpj=empresa_data.cnpj,
            razao_social=empresa_data.razao_social,
            monitorada=empresa_data.monitorada,
            ativo=1 if empresa_data.ativo else 0
        )
        
        db.add(nova_empresa)
        db.commit()
        db.refresh(nova_empresa)
        
        print(f"✅ Empresa criada: ID {nova_empresa.id}, CNPJ: {nova_empresa.cnpj}")
        
        return {
            "id": nova_empresa.id,
            "cnpj": nova_empresa.cnpj,
            "razao_social": nova_empresa.razao_social,
            "nome_fantasia": "",
            "monitorada": nova_empresa.monitorada,
            "ativo": bool(nova_empresa.ativo),
            "pasta_origem": "",
            "created_at": get_current_timestamp(),
            "updated_at": get_current_timestamp()
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro ao criar empresa: {e}")
        db.rollback()
        raise HTTPException(500, f"Erro interno do servidor: {str(e)}")

@app.put("/api/empresas/{empresa_id}")
def update_empresa(empresa_id: int, empresa_data: EmpresaUpdate, db: Session = Depends(get_db)):
    """Atualizar empresa existente"""
    try:
        empresa = db.get(Empresa, empresa_id)
        if not empresa:
            raise HTTPException(404, f"Empresa {empresa_id} não encontrada")
        
        # Atualizar campos fornecidos
        if empresa_data.cnpj is not None:
            # Verificar se novo CNPJ já existe em outra empresa
            existing = db.execute(select(Empresa).where(Empresa.cnpj == empresa_data.cnpj, Empresa.id != empresa_id)).scalar_one_or_none()
            if existing:
                raise HTTPException(409, f"CNPJ {empresa_data.cnpj} já cadastrado em outra empresa")
            empresa.cnpj = empresa_data.cnpj
        
        if empresa_data.razao_social is not None:
            empresa.razao_social = empresa_data.razao_social
        
        if empresa_data.monitorada is not None:
            empresa.monitorada = empresa_data.monitorada
        
        if empresa_data.ativo is not None:
            empresa.ativo = 1 if empresa_data.ativo else 0
        
        db.commit()
        db.refresh(empresa)
        
        print(f"✅ Empresa atualizada: ID {empresa.id}")
        
        return {
            "id": empresa.id,
            "cnpj": empresa.cnpj,
            "razao_social": empresa.razao_social,
            "nome_fantasia": "",
            "monitorada": empresa.monitorada,
            "ativo": bool(empresa.ativo),
            "pasta_origem": "",
            "created_at": get_current_timestamp(),
            "updated_at": get_current_timestamp()
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro ao atualizar empresa: {e}")
        db.rollback()
        raise HTTPException(500, f"Erro interno do servidor: {str(e)}")

@app.delete("/api/empresas/{empresa_id}")
def delete_empresa(empresa_id: int, db: Session = Depends(get_db)):
    """Excluir empresa"""
    try:
        empresa = db.get(Empresa, empresa_id)
        if not empresa:
            raise HTTPException(404, f"Empresa {empresa_id} não encontrada")
        
        # Verificar se empresa tem certificados
        certificados = db.execute(select(Certificado).where(Certificado.empresa_id == empresa_id)).scalars().all()
        if certificados:
            raise HTTPException(400, "Não é possível excluir empresa que possui certificados cadastrados")
        
        db.delete(empresa)
        db.commit()
        
        print(f"✅ Empresa excluída: ID {empresa_id}")
        
        return {"message": "Empresa excluída com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro ao excluir empresa: {e}")
        db.rollback()
        raise HTTPException(500, f"Erro interno do servidor: {str(e)}")

# ENDPOINTS DE CERTIFICADOS
@app.get("/api/certificados")
def list_certificados(db: Session = Depends(get_db)):
    """Listar todos os certificados"""
    try:
        certificados = db.execute(
            select(Certificado, Empresa)
            .join(Empresa, Certificado.empresa_id == Empresa.id)
            .order_by(Certificado.id)
        ).all()
        
        return [
            {
                "id": cert.id,
                "empresa_id": cert.empresa_id,
                "empresa_nome": empresa.razao_social,
                "empresa_cnpj": empresa.cnpj,
                "nome_arquivo": cert.nome_arquivo,
                "senha": "*****",  # Senha mascarada
                "valido_ate": cert.valido_ate,
                "ativo": cert.ativo,
                "created_at": get_current_timestamp(),
                "updated_at": get_current_timestamp()
            } for cert, empresa in certificados
        ]
    except Exception as e:
        print(f"❌ Erro ao listar certificados: {e}")
        raise HTTPException(500, f"Erro interno do servidor: {str(e)}")

@app.post("/api/certificados", status_code=201)
def create_certificado(certificado_data: CertificadoCreate, db: Session = Depends(get_db)):
    """Criar novo certificado com validação"""
    try:
        # Verificar se empresa existe
        empresa = db.get(Empresa, certificado_data.empresa_id)
        if not empresa:
            raise HTTPException(404, f"Empresa {certificado_data.empresa_id} não encontrada")
        
        # Valida o certificado se foi fornecido arquivo em base64
        if certificado_data.arquivo_base64:
            validacao = validate_certificate(certificado_data.senha, certificado_data.arquivo_base64)
            
            if not validacao["valido"]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Erro na validação do certificado: {validacao['erro']}"
                )
            
            # Extrai data de validade automaticamente
            certificado_data.valido_ate = validacao["valido_ate"]
            
            # Verifica se o certificado está expirado
            if validacao["expirado"]:
                raise HTTPException(
                    status_code=400, 
                    detail="O certificado está expirado"
                )
            
            # Verifica se o certificado ainda não é válido
            if validacao["ainda_nao_valido"]:
                raise HTTPException(
                    status_code=400, 
                    detail="O certificado ainda não é válido"
                )
        
        # Verificar se já existe certificado ativo para esta empresa
        if certificado_data.ativo:
            cert_ativo = db.execute(
                select(Certificado).where(
                    Certificado.empresa_id == certificado_data.empresa_id,
                    Certificado.ativo == True
                )
            ).scalar_one_or_none()
            
            if cert_ativo:
                raise HTTPException(409, "Já existe um certificado ativo para esta empresa")
        
        # Criar novo certificado
        novo_certificado = Certificado(
            empresa_id=certificado_data.empresa_id,
            nome_arquivo=certificado_data.nome_arquivo,
            senha=certificado_data.senha,  # Em produção, criptografar a senha
            valido_ate=certificado_data.valido_ate,
            ativo=certificado_data.ativo
        )
        
        db.add(novo_certificado)
        db.commit()
        db.refresh(novo_certificado)
        
        print(f"✅ Certificado criado: ID {novo_certificado.id}, Empresa: {empresa.razao_social}")
        
        return {
            "id": novo_certificado.id,
            "empresa_id": novo_certificado.empresa_id,
            "empresa_nome": empresa.razao_social,
            "empresa_cnpj": empresa.cnpj,
            "nome_arquivo": novo_certificado.nome_arquivo,
            "senha": "*****",
            "valido_ate": novo_certificado.valido_ate,
            "ativo": novo_certificado.ativo,
            "created_at": get_current_timestamp(),
            "updated_at": get_current_timestamp()
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro ao criar certificado: {e}")
        db.rollback()
        raise HTTPException(500, f"Erro interno do servidor: {str(e)}")

@app.put("/api/certificados/{cert_id}")
def update_certificado(cert_id: int, cert_data: CertificadoUpdate, db: Session = Depends(get_db)):
    """Atualizar certificado"""
    try:
        certificado = db.get(Certificado, cert_id)
        if not certificado:
            raise HTTPException(404, f"Certificado {cert_id} não encontrado")
        
        # Verificar se nova empresa existe
        if cert_data.empresa_id is not None:
            empresa = db.get(Empresa, cert_data.empresa_id)
            if not empresa:
                raise HTTPException(404, f"Empresa {cert_data.empresa_id} não encontrada")
            certificado.empresa_id = cert_data.empresa_id
        
        # Verificar conflito de certificado ativo
        if cert_data.ativo is not None and cert_data.ativo:
            cert_ativo = db.execute(
                select(Certificado).where(
                    Certificado.empresa_id == certificado.empresa_id,
                    Certificado.ativo == True,
                    Certificado.id != cert_id
                )
            ).scalar_one_or_none()
            
            if cert_ativo:
                raise HTTPException(409, "Já existe um certificado ativo para esta empresa")
        
        # Atualizar campos fornecidos
        if cert_data.nome_arquivo is not None:
            certificado.nome_arquivo = cert_data.nome_arquivo
        if cert_data.senha is not None:
            certificado.senha = cert_data.senha
        if cert_data.valido_ate is not None:
            certificado.valido_ate = cert_data.valido_ate
        if cert_data.ativo is not None:
            certificado.ativo = cert_data.ativo
        
        db.commit()
        db.refresh(certificado)
        
        # Buscar dados da empresa para resposta
        empresa = db.get(Empresa, certificado.empresa_id)
        
        print(f"✅ Certificado atualizado: ID {certificado.id}")
        
        return {
            "id": certificado.id,
            "empresa_id": certificado.empresa_id,
            "empresa_nome": empresa.razao_social,
            "empresa_cnpj": empresa.cnpj,
            "nome_arquivo": certificado.nome_arquivo,
            "senha": "*****",
            "valido_ate": certificado.valido_ate,
            "ativo": certificado.ativo,
            "created_at": get_current_timestamp(),
            "updated_at": get_current_timestamp()
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro ao atualizar certificado: {e}")
        db.rollback()
        raise HTTPException(500, f"Erro interno do servidor: {str(e)}")

@app.delete("/api/certificados/{cert_id}")
def delete_certificado(cert_id: int, db: Session = Depends(get_db)):
    """Excluir certificado"""
    try:
        certificado = db.get(Certificado, cert_id)
        if not certificado:
            raise HTTPException(404, f"Certificado {cert_id} não encontrado")
        
        db.delete(certificado)
        db.commit()
        
        print(f"✅ Certificado excluído: ID {cert_id}")
        
        return {"message": "Certificado excluído com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro ao excluir certificado: {e}")
        db.rollback()
        raise HTTPException(500, f"Erro interno do servidor: {str(e)}")

# ENDPOINT DE VALIDAÇÃO
@app.post("/api/certificados/validar")
async def validar_certificado(data: dict):
    """Endpoint para validar certificado antes de salvar"""
    try:
        arquivo_base64 = data.get("arquivo_base64", "")
        senha = data.get("senha", "")
        
        if not arquivo_base64 or not senha:
            raise HTTPException(400, "Arquivo e senha são obrigatórios")
        
        validacao = validate_certificate(senha, arquivo_base64)
        
        return {
            "sucesso": validacao["valido"],
            "dados": validacao
        }
        
    except Exception as e:
        return {
            "sucesso": False,
            "erro": str(e)
        }

# ENDPOINT DE DIRETÓRIOS (para compatibilidade)
@app.get("/api/diretorios")
def listar_diretorios(caminho: str = "/"):
    """Listar conteúdo de um diretório"""
    try:
        if caminho == "/" or not caminho:
            base_path = Path.home()
        else:
            base_path = Path(caminho)
        
        if not base_path.exists() or not base_path.is_dir():
            raise HTTPException(404, "Diretório não encontrado")
        
        items = []
        for item in sorted(base_path.iterdir()):
            if item.name.startswith('.'):
                continue
            
            items.append({
                "nome": item.name,
                "caminho": str(item),
                "tipo": "pasta" if item.is_dir() else "arquivo",
                "tamanho": item.stat().st_size if item.is_file() else 0
            })
        
        return {
            "caminho_atual": str(base_path),
            "itens": items
        }
    
    except Exception as e:
        raise HTTPException(500, f"Erro ao listar diretório: {str(e)}")

# ENDPOINT DE DOCUMENTOS/XMLs (versão simplificada)
@app.get("/api/documentos")
def list_documentos():
    """Listar documentos DFE processados"""
    # Por enquanto retorna estrutura vazia para compatibilidade
    return {
        "total": 0,
        "xmls": []
    }

# ENDPOINT DE SAÚDE
@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    """Verificar status da API e banco de dados"""
    try:
        # Testa conexão com o banco
        empresas = db.execute(select(Empresa)).scalars().all()
        certificados = db.execute(select(Certificado)).scalars().all()
        
        return {
            "status": "OK",
            "database": "Connected",
            "empresas_count": len(empresas),
            "certificados_count": len(certificados),
            "timestamp": get_current_timestamp()
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "database": "Disconnected",
            "error": str(e),
            "timestamp": get_current_timestamp()
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando API com PostgreSQL...")
    print("🔗 Banco de dados:", DATABASE_URL)
    uvicorn.run(app, host="0.0.0.0", port=8001)