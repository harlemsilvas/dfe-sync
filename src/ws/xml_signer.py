"""
Assinatura XML para NF-e usando lxml + cryptography
Baseado nas especificações da Receita Federal
"""
from lxml import etree
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography import x509
import base64
import hashlib
import logging

logger = logging.getLogger(__name__)

NS_DS = "http://www.w3.org/2000/09/xmldsig#"
NS_NFE = "http://www.portalfiscal.inf.br/nfe"

def sign_evento(env_evento: etree._Element, cert_pem_path: str, key_pem_path: str) -> bytes:
    """
    Assina o elemento <evento> dentro de <envEvento> conforme padrão NF-e.
    A assinatura deve estar DENTRO do elemento <evento>, após <infEvento>.
    
    Args:
        env_evento: Elemento <envEvento> contendo <evento> a ser assinado
        cert_pem_path: Caminho para certificado em formato PEM
        key_pem_path: Caminho para chave privada em formato PEM
    
    Returns:
        XML completo com assinatura em bytes
    """
    # DEBUG: Ver estrutura recebida
    logger.info(f"🔧 sign_evento: env_evento.tag = {env_evento.tag}")
    filhos = list(env_evento)
    logger.info(f"🔧 sign_evento: filhos = {[c.tag for c in filhos][:5]}")
    if filhos:
        logger.info(f"🔧 sign_evento: namespace do primeiro filho = {filhos[0].tag if not isinstance(filhos[0].tag, str) else repr(filhos[0].tag)}")
    
    # Carregar certificado e chave
    with open(cert_pem_path, 'rb') as f:
        cert_pem = f.read()
        cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    
    with open(key_pem_path, 'rb') as f:
        key_pem = f.read()
        private_key = serialization.load_pem_private_key(key_pem, password=None, backend=default_backend())
    
    # Encontrar elemento evento e infEvento
    # Usar busca sem namespace para compatibilidade
    evento = None
    for child in env_evento:
        if child.tag.endswith('evento') or child.tag == 'evento':
            evento = child
            break
    
    if evento is None:
        raise ValueError(f"Elemento <evento> não encontrado. Filhos: {[(c.tag, type(c.tag)) for c in env_evento]}")
    
    logger.info(f"✅ Evento encontrado: {evento.tag}")
    
    inf_evento = None
    for child in evento:
        if child.tag.endswith('infEvento') or child.tag == 'infEvento':
            inf_evento = child
            break
    
    if inf_evento is None:
        raise ValueError(f"Elemento <infEvento> não encontrado. Filhos de evento: {[c.tag for c in evento]}")
    
    # Obter URI de referência (Id do infEvento)
    ref_uri = inf_evento.get('Id')
    if not ref_uri:
        raise ValueError("Atributo 'Id' não encontrado em <infEvento>")
    if not ref_uri.startswith('#'):
        ref_uri = f"#{ref_uri}"
    
    # 1. Canonicalizar o elemento evento (C14N)
    evento_c14n = etree.tostring(evento, method='c14n', exclusive=False, with_comments=False)
    
    # 2. Calcular digest (SHA-1) do elemento canonicalizado
    digest = hashlib.sha1(evento_c14n).digest()
    digest_b64 = base64.b64encode(digest).decode('ascii')
    
    # 3. Criar elemento SignedInfo
    signed_info = etree.Element(f"{{{NS_DS}}}SignedInfo")
    
    # CanonicalizationMethod
    canon_method = etree.SubElement(signed_info, f"{{{NS_DS}}}CanonicalizationMethod")
    canon_method.set("Algorithm", "http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
    
    # SignatureMethod
    sig_method = etree.SubElement(signed_info, f"{{{NS_DS}}}SignatureMethod")
    sig_method.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#rsa-sha1")
    
    # Reference
    reference = etree.SubElement(signed_info, f"{{{NS_DS}}}Reference")
    reference.set("URI", ref_uri)
    
    # Transforms
    transforms = etree.SubElement(reference, f"{{{NS_DS}}}Transforms")
    
    transform1 = etree.SubElement(transforms, f"{{{NS_DS}}}Transform")
    transform1.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#enveloped-signature")
    
    transform2 = etree.SubElement(transforms, f"{{{NS_DS}}}Transform")
    transform2.set("Algorithm", "http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
    
    # DigestMethod e DigestValue
    digest_method = etree.SubElement(reference, f"{{{NS_DS}}}DigestMethod")
    digest_method.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#sha1")
    
    digest_value_elem = etree.SubElement(reference, f"{{{NS_DS}}}DigestValue")
    digest_value_elem.text = digest_b64
    
    # 4. Canonicalizar SignedInfo
    signed_info_c14n = etree.tostring(signed_info, method='c14n', exclusive=False, with_comments=False)
    
    # 5. Assinar SignedInfo com RSA-SHA1
    signature_bytes = private_key.sign(
        signed_info_c14n,
        padding.PKCS1v15(),
        hashes.SHA1()
    )
    signature_b64 = base64.b64encode(signature_bytes).decode('ascii')
    
    # 6. Criar elemento Signature completo
    # Registrar namespace DS sem prefix para evitar ns0:
    nsmap_sig = {None: NS_DS}  # None = namespace padrão sem prefix
    signature_elem = etree.Element(f"{{{NS_DS}}}Signature", nsmap=nsmap_sig)
    signature_elem.append(signed_info)
    
    # SignatureValue
    sig_value = etree.SubElement(signature_elem, f"{{{NS_DS}}}SignatureValue")
    sig_value.text = signature_b64
    
    # KeyInfo
    key_info = etree.SubElement(signature_elem, f"{{{NS_DS}}}KeyInfo")
    x509_data = etree.SubElement(key_info, f"{{{NS_DS}}}X509Data")
    x509_cert = etree.SubElement(x509_data, f"{{{NS_DS}}}X509Certificate")
    
    # Extrair certificado em base64 (sem header/footer)
    cert_b64 = base64.b64encode(cert.public_bytes(serialization.Encoding.DER)).decode('ascii')
    x509_cert.text = cert_b64
    
    # 7. Adicionar Signature ao elemento evento (APÓS infEvento)
    evento.append(signature_elem)
    
    # 8. Retornar XML completo
    return etree.tostring(env_evento, encoding='utf-8', xml_declaration=False)
