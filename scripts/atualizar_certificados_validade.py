import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../'))
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from src.models.certificado import Certificado
from src.store.db import Base
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv
from datetime import datetime


# Carregar .env
load_dotenv()
DB_URL = os.getenv("DB_URL")

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)


def extrair_validade_pfx(pfx_path, senha):
    try:
        with open(pfx_path, "rb") as f:
            pfx_bytes = f.read()
        private_key, certificate, _ = pkcs12.load_key_and_certificates(
            pfx_bytes, senha.encode("utf-8"), backend=default_backend()
        )
        cn = None
        for attr in certificate.subject:
            if attr.oid._name == 'commonName':
                cn = attr.value
                break
        valido_de = certificate.not_valid_before.strftime("%Y-%m-%d %H:%M:%S")
        valido_ate = certificate.not_valid_after.strftime("%Y-%m-%d %H:%M:%S")
        return cn, valido_de, valido_ate
    except Exception as e:
        return None, None, None


def atualizar_certificados():
    with SessionLocal() as db:
        certificados = db.execute(select(Certificado)).scalars().all()
        atualizados = 0
        for cert in certificados:
            if not cert.valido_ate:
                pfx_path = cert.pfx_path
                senha = cert.senha_cripto
                if pfx_path and senha:
                    cn, valido_de, valido_ate = extrair_validade_pfx(pfx_path, senha)
                    if valido_ate:
                        cert.nome_empresa = cn
                        cert.valido_de = valido_de
                        cert.valido_ate = valido_ate
                        cert.status_validacao = "valido"
                        db.commit()
                        atualizados += 1
                        print(f"Atualizado: {cert.id} | {cert.nome_empresa} | {cert.valido_ate}")
                    else:
                        cert.status_validacao = "invalido"
                        db.commit()
                        print(f"Certificado inválido, pulando: {cert.id} | {pfx_path}")
        print(f"Total certificados atualizados: {atualizados}")

if __name__ == "__main__":
    atualizar_certificados()
