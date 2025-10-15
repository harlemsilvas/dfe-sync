from fastapi import FastAPI

app = FastAPI(title="DF-e Sync - Test", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok", "message": "API está funcionando!"}

@app.get("/")
def root():
    return {"message": "API DF-e Sync funcionando!"}
