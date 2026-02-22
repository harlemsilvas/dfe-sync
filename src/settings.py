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
