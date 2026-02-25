# scripts/importar_xmls_docs.py
import sys
from pathlib import Path
sys.path.insert(0, "/mnt/c/Projetos/dfe-sync")

from src.store.db import SessionLocal
from src.models import DFEDocumento
from lxml import etree
import base64
import zlib

def importar_xml(caminho_xml: Path, empresa_id: int):
    """Importa XML manual para o banco"""
    db = SessionLocal()
    try:
        # Ler XML
        xml_bytes = caminho_xml.read_bytes()
        
        # Extrair NSU/chave (lógica simplificada)
        root = etree.fromstring(xml_bytes)
        ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}
        chave = root.findtext(".//nfe:chNFe", namespaces=ns) or "N/A"
        nsu = caminho_xml.name.split("_")[0] if "_" in caminho_xml.name else "000000000000000"
        
        # Comprimir e codificar
        xml_comprimido = zlib.compress(xml_bytes)
        xml_base64 = base64.b64encode(xml_comprimido).decode('utf-8')
        
        # Criar registro
        doc = DFEDocumento(
            empresa_id=empresa_id,
            nsu=nsu.zfill(15),
            schema="manual_import",
            chave=chave,
            caminho_xml=str(caminho_xml),
            conteudo_base64=xml_base64,
            created_at=datetime.utcnow()
        )
        db.add(doc)
        db.commit()
        print(f"✅ Importado: {caminho_xml.name} (NSU: {nsu})")
        return True
    except Exception as e:
        print(f"❌ Erro ao importar {caminho_xml.name}: {e}")
        db.rollback()
        return False
    finally:
        db.close()

# Exemplo de uso:
# from pathlib import Path
# for xml in Path("docs").rglob("*.xml"):
#     importar_xml(xml, empresa_id=2)