from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "dev"
    APP_DEBUG: bool = True
    DB_URL: str

    STORAGE_BASE_PATH: str = "storage/xml"
    CERTS_BASE_PATH: str = "storage/certs"

    NFE_AMBIENTE: str = "HOMOLOG"  # HOMOLOG|PRODUCAO
    AN_WSDL_HOMOLOG: str
    AN_WSDL_PRODUCAO: str
    # Fallback local de WSDL (opcional). Se definido ou se arquivo padrão existir, será usado em caso de falha do remoto.
    AN_WSDL_LOCAL_PATH: str | None = None

    # (Opcional) Endpoints diretos do serviço de distribuição DF-e (sem ?WSDL).
    # Caso informados, serão priorizados no modo SOAP direto.
    AN_DIST_URL_HOMOLOG: str | None = None
    AN_DIST_URL_PRODUCAO: str | None = None

    # Em 2025 muitos hosts do AN não servem mais o ?WSDL (404). Por padrão, usar SOAP direto.
    DFE_USE_WSDL: bool = False

    # Endpoints de RecepcaoEvento v4.00 (serviço de eventos da NF-e)
    # São URLs do serviço (SOAP endpoint), não necessariamente WSDL.
    EV_URL_HOMOLOG: str = "https://hom.nfe.fazenda.gov.br/ws/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx"
    EV_URL_PRODUCAO: str = "https://www.nfe.fazenda.gov.br/ws/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx"

    JOB_INTERVAL_MINUTES: int = 10

    DFE_SLEEP_BETWEEN_CALLS_MS: int = 350
    DFE_MAX_ATTEMPTS: int = 4
    DFE_BACKOFF_BASE_SEC: int = 8
    DFE_BACKOFF_CAP_SEC: int = 180
    # Opcional: caminho para bundle de certificados raiz ICP-Brasil (para substituir certifi)
    DFE_CA_BUNDLE: str | None = None
    # Ativa logs detalhados de chamadas DF-e
    DFE_DEBUG: bool = False

    class Config:
        env_file = ".env"

settings = Settings()