from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import select
from src.store.db import SessionLocal
from src.models import Empresa
from src.api.routes.dfe import _load_cert_tuple
from src.core.dfe_sync import run_distribution
import os, certifi
from src.settings import settings

sched = BlockingScheduler()

@sched.scheduled_job("interval", minutes=settings.JOB_INTERVAL_MINUTES)
def sync_all():
    with SessionLocal() as db:
        empresas = [e for (e,) in db.execute(select(Empresa).where(Empresa.ativo==1)).all()]
    for emp in empresas:
        cert_tuple = None
        try:
            emp2, cert_path, key_path = _load_cert_tuple(emp.id)
            cert_tuple = (cert_path, key_path)
            verify = certifi.where()
            res = run_distribution(emp.id, emp.cnpj, cert_tuple, verify)
            print(f"[DFE] empresa={emp.cnpj} ok={res.get('ok')} nsu={res.get('ultNSU')}/{res.get('maxNSU')} processed={res.get('processed')}")
        except Exception as e:
            print(f"[DFE] empresa={emp.cnpj} erro: {e}")
        finally:
            if cert_tuple:
                for p in cert_tuple:
                    try:
                        if p and os.path.exists(p): os.remove(p)
                    except: pass

if __name__ == "__main__":
    sched.start()
