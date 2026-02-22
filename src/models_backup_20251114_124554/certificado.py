from sqlalchemy import Column, Integer, String, LargeBinary, ForeignKey, Text
from src.store.db import Base

class Certificado(Base):
    __tablename__ = "certificados"

    id = Column(Integer, primary_key=True, index=True)
    
    # Campos do sistema antigo (para compatibilidade)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=True)
    tipo = Column(String(2), nullable=True, default="A1")
    pfx_path = Column(Text, nullable=True)  # Caminho do arquivo PFX
    senha_cripto = Column(Text, nullable=True)  # Senha do certificado
    
    # Campos do sistema novo (interface web)
    cnpj = Column(String, unique=True, index=True, nullable=True)
    pfx_file = Column(LargeBinary, nullable=True)  # Arquivo binário no banco
    pfx_password_encrypted = Column(String, nullable=True)  # Senha criptografada com Fernet
