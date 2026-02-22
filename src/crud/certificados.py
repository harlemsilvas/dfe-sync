from sqlalchemy.orm import Session
from src.models.certificado import Certificado as CertificadoModel
from src.schemas.certificado import CertificadoCreate
from cryptography.fernet import Fernet
import os

# Idealmente, a chave de criptografia deve ser carregada de uma variável de ambiente ou um secret manager.
# Por simplicidade, vamos gerá-la ou lê-la de um arquivo.
KEY_FILE = "secret.key"
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "rb") as f:
        key = f.read()
else:
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)

cipher_suite = Fernet(key)

def encrypt_password(password: str) -> str:
    return cipher_suite.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    return cipher_suite.decrypt(encrypted_password.encode()).decode()

def get_certificado_by_cnpj(db: Session, cnpj: str):
    return db.query(CertificadoModel).filter(CertificadoModel.cnpj == cnpj).first()

def get_all_certificados(db: Session):
    """Lista todos os certificados (sem expor senhas)"""
    certificados = db.query(CertificadoModel).all()
    return [{"id": cert.id, "cnpj": cert.cnpj, "created_at": cert.created_at} for cert in certificados]

def create_certificado(db: Session, schema: CertificadoCreate, pfx_file: bytes):
    encrypted_password = encrypt_password(schema.pfx_password)
    db_certificado = CertificadoModel(
        cnpj=schema.cnpj,
        pfx_file=pfx_file,
        pfx_password_encrypted=encrypted_password
    )
    db.add(db_certificado)
    db.commit()
    db.refresh(db_certificado)
    return db_certificado
