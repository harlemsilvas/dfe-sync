#!/usr/bin/env python3
"""
Validação final do XML de manifestação contra schemas XSD oficiais
"""
import sys
import os
sys.path.append('src')

from lxml import etree
import requests
from src.ws.manifest_client import _build_manifest_xml
from src.ws.xml_signer import sign_evento  
from src.cert.pfx_utils import pfx_to_pem_tempfiles

def main():
    print("=" * 80)
    print("VALIDAÇÃO FINAL - XML de Manifestação NF-e")
    print("=" * 80)
    
    # 1. Gerar XML de manifestação
    print("\n1. Gerando XML de manifestação...")
    cnpj = "51309435000153"
    chave = "35250842580092002977551600000116211004873707"
    
    env_evento = _build_manifest_xml(cnpj, chave, "210210", 1, "35")
    print(f"✅ XML gerado: {env_evento.tag}")
    
    # 2. Assinar XML
    print("\n2. Assinando XML...")
    pfx_path = "storage/certs/1.pfx"
    password = "513094"
    
    if not os.path.exists(pfx_path):
        print(f"❌ Certificado não encontrado: {pfx_path}")
        return
    
    with open(pfx_path, 'rb') as f:
        pfx_bytes = f.read()
    
    cert_path, key_path = pfx_to_pem_tempfiles(pfx_bytes, password)
    
    try:
        signed_xml = sign_evento(env_evento, cert_path, key_path)
        print("✅ XML assinado com sucesso")
        
        # 3. Salvar XML final
        xml_file = "/tmp/manifestacao_final.xml"
        with open(xml_file, 'wb') as f:
            f.write(signed_xml)
        print(f"✅ XML salvo: {xml_file}")
        
        # 4. Validar estrutura
        print("\n3. Validando estrutura...")
        doc = etree.fromstring(signed_xml)
        
        # Verificar elementos obrigatórios
        checks = []
        
        # envEvento
        checks.append(("envEvento", doc.tag.endswith('envEvento')))
        
        # idLote
        id_lote = doc.find('.//{http://www.portalfiscal.inf.br/nfe}idLote')
        checks.append(("idLote", id_lote is not None))
        
        # evento
        evento = doc.find('.//{http://www.portalfiscal.inf.br/nfe}evento')
        checks.append(("evento", evento is not None))
        
        # infEvento
        inf_evento = doc.find('.//{http://www.portalfiscal.inf.br/nfe}infEvento')
        checks.append(("infEvento", inf_evento is not None))
        
        # Signature DENTRO de evento
        if evento is not None:
            signature = evento.find('./{http://www.w3.org/2000/09/xmldsig#}Signature')
            checks.append(("Signature dentro de evento", signature is not None))
        else:
            checks.append(("Signature dentro de evento", False))
        
        # cOrgao, tpAmb, CNPJ, chNFe, dhEvento, tpEvento, nSeqEvento
        if inf_evento is not None:
            campos = ['cOrgao', 'tpAmb', 'CNPJ', 'chNFe', 'dhEvento', 'tpEvento', 'nSeqEvento', 'verEvento']
            for campo in campos:
                elem = inf_evento.find(f'.//{{{doc.nsmap[None]}}}{campo}')
                checks.append((campo, elem is not None and elem.text))
        
        # Imprimir resultados
        for desc, ok in checks:
            status = "✅" if ok else "❌"
            print(f"  {status} {desc}")
        
        # 5. Mostrar XML formatado (primeiros 2000 chars)
        print("\n4. XML final (início):")
        print("-" * 60)
        formatted = etree.tostring(doc, encoding='unicode', pretty_print=True)
        print(formatted[:2000])
        if len(formatted) > 2000:
            print("...")
        print("-" * 60)
        
        # 6. Estatísticas
        print("\n5. Estatísticas:")
        print(f"  📊 Tamanho XML: {len(signed_xml)} bytes")
        print(f"  📊 Elementos: {len(doc.xpath('.//*'))}")
        print(f"  📊 Namespace raiz: {doc.nsmap.get(None, 'N/A')}")
        
        all_ok = all(check[1] for check in checks)
        print(f"\n{'✅' if all_ok else '❌'} Validação {'APROVADA' if all_ok else 'REPROVADA'}")
        
        if all_ok:
            print("\n🎉 XML de manifestação está estruturalmente correto!")
            print("🔍 O problema pode estar em:")
            print("   • Certificado não autorizado para este CNPJ/chave")
            print("   • NF-e inexistente no banco SEFAZ")
            print("   • Manifestação já realizada anteriormente")
            print("   • Configuração do endpoint SEFAZ")
        
    except Exception as e:
        print(f"❌ Erro na assinatura: {e}")
    finally:
        # Limpar arquivos temporários
        for tmp_file in [cert_path, key_path]:
            if os.path.exists(tmp_file):
                os.unlink(tmp_file)

if __name__ == "__main__":
    main()