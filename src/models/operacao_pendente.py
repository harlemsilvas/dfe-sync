from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from datetime import datetime
from src.store.db import Base

class OperacaoPendente(Base):
    __tablename__ = "operacoes_pendentes"

    id = Column(Integer, primary_key=True, index=True)
    chave_nfe = Column(String(44), nullable=False, index=True)
    cnpj_emissor = Column(String(14), nullable=False)
    cnpj_destinatario = Column(String(14), nullable=False)
    cfop = Column(String(4), nullable=False)
    natureza_operacao = Column(Text, nullable=False)
    
    # Sugestão do sistema
    tipo_sugerido = Column(String(20), nullable=True)  # NFE_ENTRADA, NFE_SAIDA, etc.
    motivo_pendencia = Column(Text, nullable=False)  # Por que não conseguiu classificar
    
    # Resolução manual
    tipo_definido = Column(String(20), nullable=True)  # Definido pelo usuário
    resolvido = Column(Boolean, default=False, nullable=False)
    resolvido_por = Column(String(50), nullable=True)  # Usuário que resolveu
    resolvido_em = Column(DateTime, nullable=True)
    
    # Controle
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<OperacaoPendente(chave='{self.chave_nfe[:10]}...', resolvido={self.resolvido})>"