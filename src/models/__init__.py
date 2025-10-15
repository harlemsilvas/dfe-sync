from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Index, Numeric, LargeBinary
from datetime import datetime

Base = declarative_base()

class Empresa(Base):
    __tablename__ = "empresas"
    id: Mapped[int] = mapped_column(primary_key=True)
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, index=True)
    razao_social: Mapped[str] = mapped_column(String(200))
    ambiente: Mapped[str] = mapped_column(String(10), default="HOMOLOG")
    ativo: Mapped[int] = mapped_column(Integer, default=1)

class Certificado(Base):
    __tablename__ = "certificados"
    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(2), default="A1")  # A1/A3
    pfx_path: Mapped[str] = mapped_column(Text)                 # caminho do .pfx
    senha_cripto: Mapped[str] = mapped_column(Text)             # armazene cifrada (placeholder)

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
    # Manifestação do destinatário (persistência opcional do retorno)
    manifest_tp: Mapped[str | None] = mapped_column(String(6), nullable=True)
    manifest_nseq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    manifest_cstat: Mapped[str | None] = mapped_column(String(6), nullable=True)
    manifest_xmotivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    manifest_xml_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    manifest_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

Index("ix_dfe_empresa_nsu", DFEDocumento.empresa_id, DFEDocumento.nsu)