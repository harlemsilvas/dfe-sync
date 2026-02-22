from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from datetime import datetime
from src.store.db import Base

class LogProcessamento(Base):
    __tablename__ = "logs_processamento"

    id = Column(Integer, primary_key=True, index=True)
    nivel = Column(String(10), nullable=False, index=True)  # DEBUG, INFO, WARNING, ERROR
    modulo = Column(String(50), nullable=False, index=True)  # extractor, classifier, organizer, etc.
    processo = Column(String(50), nullable=False, index=True)  # Nome do processo/lote
    tag = Column(String(50), nullable=True, index=True)  # Tag personalizada
    
    # Conteúdo
    mensagem = Column(Text, nullable=False)
    dados_json = Column(Text, nullable=True)  # Dados estruturados em JSON
    
    # Contexto
    arquivo_origem = Column(Text, nullable=True)  # Arquivo sendo processado
    chave_nfe = Column(String(44), nullable=True, index=True)  # Chave do documento
    cnpj_empresa = Column(String(14), nullable=True, index=True)  # CNPJ relacionado
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<LogProcessamento({self.nivel}, {self.modulo}, {self.timestamp})>"