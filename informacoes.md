### 📄 alembic.ini

```ini
[alembic]
script_location = migrations
sqlalchemy.url = postgresql+psycopg2://dfe:dfe@localhost:5432/dfe
file_template = %%(rev)s_%%(slug)s
```

### 📄 src/settings.py

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "dev"
    APP_DEBUG: bool = True
    DB_URL: str

    # Novos campos para compatibilidade com .env
    FRONTEND_PORT: int = 5173
    BACKEND_PORT: int = 8001
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8001"
    API_BASE_URL: str = "http://localhost:8001/api"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    STORAGE_BASE_PATH: str = "storage/xml"
    CERTS_BASE_PATH: str = "storage/certs"

    NFE_AMBIENTE: str = "HOMOLOG"  # HOMOLOG|PRODUCAO
    AN_WSDL_HOMOLOG: str
    AN_WSDL_PRODUCAO: str

    # URLs de recepção de evento (manifestação)
    EV_URL_HOMOLOG: str = "https://hom1.nfe.fazenda.gov.br/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx"
    EV_URL_PRODUCAO: str = "https://www1.nfe.fazenda.gov.br/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx"
    DFE_CA_BUNDLE: str = ""

    JOB_INTERVAL_MINUTES: int = 10

    DFE_SLEEP_BETWEEN_CALLS_MS: int = 350
    DFE_MAX_ATTEMPTS: int = 4
    DFE_BACKOFF_BASE_SEC: int = 8
    DFE_BACKOFF_CAP_SEC: int = 180

    class Config:
        env_file = ".env"

settings = Settings()
```

### 📄 src/models/**init**.py

```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Index, Numeric, LargeBinary, Date, Boolean
from decimal import Decimal
from datetime import datetime
from src.store.db import Base
from .certificado import Certificado
from .tipo_documento import TipoDocumento
from .remetente_cadastrado import RemetenteCadastrado
from .cfop_transferencia import CfopTransferencia
from .operacao_pendente import OperacaoPendente
from .log_processamento import LogProcessamento


class Empresa(Base):
    __tablename__ = "empresas"
    id: Mapped[int] = mapped_column(primary_key=True)
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, index=True)
    razao_social: Mapped[str] = mapped_column(String(200))
    ambiente: Mapped[str] = mapped_column(String(10), default="HOMOLOG")
    ativo: Mapped[int] = mapped_column(Integer, default=1)
    # Nova flag para identificar empresas monitoradas
    monitorada: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

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
    valor_total: Mapped[float] = mapped_column(Numeric(15,2), nullable=True)
    numero_documento: Mapped[str] = mapped_column(String(20), nullable=True, index=True)
    serie: Mapped[str] = mapped_column(String(10), nullable=True)
    modelo: Mapped[str] = mapped_column(String(5), nullable=True)  # 55=NF-e, 57=CT-e, etc.
    natureza_operacao: Mapped[str] = mapped_column(String(100), nullable=True)
    arquivo_origem: Mapped[str] = mapped_column(Text, nullable=True)  # Caminho do ZIP original

Index("ix_dfe_empresa_nsu", DFEDocumento.empresa_id, DFEDocumento.nsu)

```
