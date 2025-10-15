from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .routes import health, empresas, dfe, documentos, nfe_publica_sp
app = FastAPI(title="DF-e Sync (NSU) + NFSe adapters", version="0.1.0")

# CORS: permitir UI local (ajuste se necessário)
app.add_middleware(
	CORSMiddleware,
	allow_origins=[
		"http://localhost:8010",
		"http://127.0.0.1:8010",
		"http://localhost:8001",
		"http://127.0.0.1:8001",
	],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(empresas.router, prefix="/api", tags=["Empresas"])
app.include_router(dfe.router, prefix="/api", tags=["DF-e"])
app.include_router(documentos.router, prefix="/api", tags=["Documentos"])
app.include_router(nfe_publica_sp.router, prefix="/api", tags=["NF-e Pública SP"])

# Servir UI estática (opcional) em /ui
app.mount("/ui", StaticFiles(directory="web", html=True), name="ui")