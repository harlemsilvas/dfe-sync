from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from datetime import datetime
from src.store.db import Base

class RemetenteCadastrado(Base):
    __tablename__ = "remetentes_cadastrados"

    id = Column(Integer, primary_key=True, index=True)
    cnpj_cpf = Column(String(14), unique=True, nullable=False, index=True)  # CNPJ ou CPF
    razao_social = Column(String(200), nullable=False)
    nome_fantasia = Column(String(200), nullable=True)
    tipo = Column(String(20), nullable=False, index=True)  # Cliente, Fornecedor, Transportador, Marketplace
    
    # Endereço completo
    logradouro = Column(String(100), nullable=True)
    numero = Column(String(10), nullable=True)
    complemento = Column(String(50), nullable=True)
    bairro = Column(String(50), nullable=True)
    cidade = Column(String(50), nullable=True)
    uf = Column(String(2), nullable=True)
    cep = Column(String(8), nullable=True)
    
    # Contatos
    telefone = Column(String(15), nullable=True)
    email = Column(String(100), nullable=True)
    
    # Dados fiscais
    ie = Column(String(20), nullable=True)  # Inscrição Estadual
    im = Column(String(20), nullable=True)  # Inscrição Municipal
    
    # Controle
    ativo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<RemetenteCadastrado(cnpj_cpf='{self.cnpj_cpf}', razao_social='{self.razao_social}', tipo='{self.tipo}')>"