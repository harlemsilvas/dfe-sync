from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Index, Numeric, LargeBinary, Date, Decimal, Boolean
from datetime import datetime
from src.store.db import Base
from .certificado import Certificado
from .tipo_documento import TipoDocumento


class Empresa(Base):
    __tablename__ = "empresas"
    id: Mapped[int] = mapped_column(primary_key=True)
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, index=True)
    razao_social: Mapped[str] = mapped_column(String(200))
    ambiente: Mapped[str] = mapped_column(String(10), default="HOMOLOG")
    ativo: Mapped[int] = mapped_column(Integer, default=1)

class CursorDFe(Base):
    __tablename__ = "cursor_dfe"
    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), unique=True)
    ultimo_nsu: Mapped[str] = mapped_column(String(20), default="000000000000000")
    max_nsu: Mapped[str] = mapped_column(String(20), default="000000000000000")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class DFEDocumento(Base):
    __tablename__ = "dfe_documentos"
    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), index=True)
    nsu: Mapped[str] = mapped_column(String(20), index=True)
    schema: Mapped[str] = mapped_column(String(30))      # resNFe|procNFe|resEvento|procEvento
    chave: Mapped[str] = mapped_column(String(44), index=True, nullable=True)
    caminho_xml: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Novos campos para classificação e organização
    tipo_documento_id: Mapped[int] = mapped_column(ForeignKey("tipo_documento.id"), nullable=True, index=True)
    cnpj_emissor: Mapped[str] = mapped_column(String(14), nullable=True, index=True)
    cnpj_destinatario: Mapped[str] = mapped_column(String(14), nullable=True, index=True)
    data_emissao: Mapped[datetime] = mapped_column(Date, nullable=True, index=True)
    valor_total: Mapped[float] = mapped_column(Decimal(15,2), nullable=True)
    numero_documento: Mapped[str] = mapped_column(String(20), nullable=True, index=True)
    serie: Mapped[str] = mapped_column(String(10), nullable=True)
    modelo: Mapped[str] = mapped_column(String(5), nullable=True)  # 55=NF-e, 57=CT-e, etc.
    natureza_operacao: Mapped[str] = mapped_column(String(100), nullable=True)
    arquivo_origem: Mapped[str] = mapped_column(Text, nullable=True)  # Caminho do ZIP original

Index("ix_dfe_empresa_nsu", DFEDocumento.empresa_id, DFEDocumento.nsu)
