#!/usr/bin/env python3
"""
Script para testar a assinatura XML isoladamente
"""
import sys
from lxml import etree
from src.ws.manifest_client import _build_manifest_xml
from src.ws.xml_signer import sign_evento

# Dados de teste
cnpj = "51309435000153"
chNFe = "35251042580092002977551600000125381568142699"
tpEvento = "210210"
nSeq = 1
cOrgao = "35"  # SP

# Certificados temporários (usar os últimos gerados)
cert_path = "/tmp/tmp7ardyzi5.pem"
key_path = "/tmp/tmp7bn_wfrt.pem"

print("=" * 80)
print("TESTE DE ASSINATURA XML - NF-e Manifestação")
print("=" * 80)

# 1. Construir XML do evento
print("\n1. Construindo XML do evento...")
try:
    env_evento = _build_manifest_xml(cnpj, chNFe, tpEvento, nSeq, cOrgao)
    print("✅ XML construído com sucesso")
    print(f"   Tag raiz: {env_evento.tag}")
    print(f"   Filhos: {[c.tag for c in env_evento]}")
except Exception as e:
    print(f"❌ Erro ao construir XML: {e}")
    sys.exit(1)

# 2. Salvar XML antes da assinatura
print("\n2. XML ANTES da assinatura:")
xml_antes = etree.tostring(env_evento, pretty_print=True, encoding='unicode')
print(xml_antes[:500])
with open('/tmp/evento_antes_assinatura.xml', 'w') as f:
    f.write(xml_antes)
print("   Salvo em: /tmp/evento_antes_assinatura.xml")

# 3. Assinar o XML
print("\n3. Assinando XML...")
try:
    # Gerar novos certificados temporários
    from src.cert.pfx_utils import pfx_to_pem_tempfiles
    with open('storage/certs/1.pfx', 'rb') as f:
        pfx_bytes = f.read()
    cert_path, key_path = pfx_to_pem_tempfiles(pfx_bytes, '513094')
    print(f"   Certificado: {cert_path}")
    print(f"   Chave: {key_path}")
    
    signed_xml_bytes = sign_evento(env_evento, cert_path, key_path)
    print("✅ XML assinado com sucesso")
except Exception as e:
    print(f"❌ Erro ao assinar XML: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. Salvar XML depois da assinatura
print("\n4. XML DEPOIS da assinatura:")
signed_xml = signed_xml_bytes.decode('utf-8')
print(signed_xml[:800])
with open('/tmp/evento_depois_assinatura.xml', 'w') as f:
    f.write(signed_xml)
print("   Salvo em: /tmp/evento_depois_assinatura.xml")

# 5. Validar estrutura
print("\n5. Validando estrutura do XML assinado...")
try:
    root = etree.fromstring(signed_xml_bytes)
    
    # Verificar se Signature está DENTRO de <evento>
    evento = None
    for child in root:
        if child.tag.endswith('evento') or child.tag == 'evento':
            evento = child
            break
    
    if evento is None:
        print("❌ Elemento <evento> não encontrado!")
        sys.exit(1)
    
    print(f"✅ Elemento <evento> encontrado")
    print(f"   Filhos de evento: {[c.tag.split('}')[-1] if '}' in c.tag else c.tag for c in evento]}")
    
    # Procurar Signature
    signature_found = False
    for child in evento:
        if 'Signature' in child.tag:
            signature_found = True
            print(f"✅✅✅ SUCESSO! <Signature> está DENTRO de <evento>!")
            print(f"   Tag completa: {child.tag}")
            break
    
    if not signature_found:
        print("❌ <Signature> NÃO encontrada dentro de <evento>")
        print("   Procurando em outros lugares...")
        for child in root:
            if 'Signature' in child.tag:
                print(f"   ❌ <Signature> encontrada em {root.tag} (ERRADO!)")
    
    # Verificar elementos obrigatórios
    inf_evento = None
    for child in evento:
        if child.tag.endswith('infEvento') or child.tag == 'infEvento':
            inf_evento = child
            break
    
    if inf_evento:
        print(f"✅ Elemento <infEvento> encontrado")
        id_attr = inf_evento.get('Id')
        print(f"   Id: {id_attr}")
    
except Exception as e:
    print(f"❌ Erro ao validar XML: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("TESTE CONCLUÍDO!")
print("=" * 80)
print("\nArquivos gerados:")
print("  - /tmp/evento_antes_assinatura.xml")
print("  - /tmp/evento_depois_assinatura.xml")
