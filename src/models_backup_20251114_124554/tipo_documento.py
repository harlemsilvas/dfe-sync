from sqlalchemy import Column, Integer, String, Boolean
from src.store.db import Base

class TipoDocumento(Base):
    __tablename__ = "tipo_documento"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    descricao = Column(String(100), nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<TipoDocumento(codigo='{self.codigo}', descricao='{self.descricao}')>"