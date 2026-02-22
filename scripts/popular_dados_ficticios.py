import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
DATABASE_URL = os.environ.get("DB_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Dados fictícios
empresas = [
    {
        "id": 4,
        "cnpj": "12345678000198",
        "razao_social": "Empresa Exemplo LTDA",
        "ambiente": "HOMOLOG",
        "ativo": 1,
        "monitorada": True
    },
    {
        "id": 5,
        "cnpj": "98765432000111",
        "razao_social": "Comercial Beta S/A",
        "ambiente": "HOMOLOG",
        "ativo": 1,
        "monitorada": False
    }
]

certificados = [
    {
        "id": 4,
        "empresa_id": 4,
        "tipo": "A1",
        "pfx_path": "/mnt/c/Projetos/dfe-sync/storage/certs/25148168.pfx",
        "senha_cripto": "*****",
        "cnpj": "19330326000105",
        "pfx_file": None,
        "pfx_password_encrypted": None
    },
    {
        "id": 5,
        "empresa_id": 5,
        "tipo": "A1",
        "pfx_path": "/mnt/c/Projetos/dfe-sync/storage/certs/1.pfx",
        "senha_cripto": "*****",
        "cnpj": "98765432000111",
        "pfx_file": None,
        "pfx_password_encrypted": None
    }
]

def main():
    session = SessionLocal()
    try:
        # Inserir empresas
        for emp in empresas:
            session.execute(text("""
                INSERT INTO empresas (id, cnpj, razao_social, ambiente, ativo, monitorada)
                VALUES (:id, :cnpj, :razao_social, :ambiente, :ativo, :monitorada)
                ON CONFLICT (id) DO NOTHING
            """), emp)
        # Inserir certificados
        for cert in certificados:
            session.execute(text("""
                INSERT INTO certificados (id, empresa_id, tipo, pfx_path, senha_cripto, cnpj, pfx_file, pfx_password_encrypted)
                VALUES (:id, :empresa_id, :tipo, :pfx_path, :senha_cripto, :cnpj, :pfx_file, :pfx_password_encrypted)
                ON CONFLICT (id) DO NOTHING
            """), cert)
        session.commit()
        print("✅ Dados fictícios inseridos com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao inserir dados: {e}")
        session.rollback()
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    main()
