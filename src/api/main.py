from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from .routes import health, empresas, dfe, documentos, certificados, admin, classificador, cfop
import logging

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG para salvar XMLs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# app = FastAPI(title="DF-e Sync (NSU) + NFSe adapters", version="0.1.0")
app = FastAPI(
    title="DFE Sync - API de Administração",
    description="API para gerenciamento de empresas e certificados com PostgreSQL",
    version="2.0.0",
    # redirect_slashes=True  # ✅ Evita redirect de /api/certificados → /api/certificados/
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174"],
    allow_origins=["*"],  # Permitir todas as origens (ajuste conforme necessário)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("🚀 Aplicação iniciada!")

# Favicon endpoint
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = Path(__file__).parent.parent.parent / "assets" / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    return {"detail": "Favicon not found"}

app.include_router(health.router)
app.include_router(empresas.router, prefix="/api", tags=["Empresas"])
# ✅ CERTIFICADOS - registrar com prefixo /api
# Como certificados.py já tem prefix="/certificados", a rota final será /api/certificados/*
# app.include_router(certificados.router, prefix="/api")
app.include_router(certificados.router, prefix="/api", tags=["Certificados"])

app.include_router(dfe.router, prefix="/api", tags=["DF-e"])
app.include_router(documentos.router, prefix="/api", tags=["Documentos"])


# Rotas de CFOP separadas
app.include_router(cfop.router, prefix="/api", tags=["CFOP"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])
# ✅ Registrar classificador (sem prefixo extra, pois já tem no router)
app.include_router(classificador.router, prefix="/api", tags=["Classificador"]) # ← Registrar!

# Atalho: /api/classificar → /api/classificador/classificar
from fastapi import Request, BackgroundTasks
from src.api.routes.classificador import classificar_documentos, ClassificacaoRequest
@app.post("/api/classificar", tags=["Classificador"])
async def classificar_atalho(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    print("[DEBUG] Payload recebido em /api/classificar:", body)
    try:
        req = ClassificacaoRequest(**body)
    except Exception as e:
        print("[ERRO] Falha ao criar ClassificacaoRequest:", e)
        raise
    return await classificar_documentos(req, background_tasks)
