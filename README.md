# DF-e Sync (NSU) + base NFS-e

## Rodar (Linux/WSL)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d db
alembic upgrade head
uvicorn src.api.main:app --reload --port 8001
```

## Estrutura

- `src/api/` - FastAPI endpoints
- `src/ws/` - Cliente SOAP NFeDistribuicaoDFe
- `src/core/` - Lógica de sincronização
- `src/models/` - Modelos SQLAlchemy
- `src/jobs/` - Scheduler APScheduler
- `storage/` - XMLs baixados

## Endpoints principais

- POST `/api/empresas` - Cadastrar empresa
- POST `/api/empresas/{id}/cert` - Upload certificado A1 (.pfx)
- GET `/api/dfe/cursor?empresa_id=X` - Consultar cursor NSU
- POST `/api/dfe/sync?empresa_id=X` - Forçar sincronização
- GET `/api/documentos?empresa_id=X` - Listar documentos baixados
