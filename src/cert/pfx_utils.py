from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
import tempfile, os
import logging

logger = logging.getLogger(__name__)

def pfx_to_pem_tempfiles(pfx_bytes: bytes, password: str):
    logger.info(f"🔐 Tentando carregar PFX (tamanho: {len(pfx_bytes)} bytes, senha fornecida: {'Sim' if password else 'Não'})")
    
    try:
        key, cert, chain = pkcs12.load_key_and_certificates(
            pfx_bytes, 
            password.encode("utf-8") if password else None
        )
        
        if not key or not cert: 
            logger.error("❌ PFX carregado mas chave ou certificado está None")
            raise ValueError("PFX inválido/senha incorreta")
        
        logger.info(f"✅ PFX carregado com sucesso! Certificado: {cert.subject}")
        logger.info(f"📅 Válido de {cert.not_valid_before_utc} até {cert.not_valid_after_utc}")
        
        certs = [cert.public_bytes(Encoding.PEM)]
        if chain:
            logger.info(f"📎 Cadeia de certificados: {len(chain)} certificado(s)")
            for c in chain: 
                certs.append(c.public_bytes(Encoding.PEM))
        
        cert_fd, cert_path = tempfile.mkstemp(suffix=".pem")
        os.write(cert_fd, b"".join(certs))
        os.close(cert_fd)
        logger.info(f"💾 Certificado salvo em: {cert_path}")
        
        key_fd, key_path = tempfile.mkstemp(suffix=".pem")
        os.write(key_fd, key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))
        os.close(key_fd)
        logger.info(f"🔑 Chave privada salva em: {key_path}")
        
        return cert_path, key_path
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar PFX: {type(e).__name__}: {e}")
        raise
