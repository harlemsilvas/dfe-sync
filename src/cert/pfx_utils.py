from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from cryptography import x509
from cryptography.x509.oid import NameOID
import tempfile, os

def pfx_to_pem_tempfiles(pfx_bytes: bytes, password: str):
    key, cert, chain = pkcs12.load_key_and_certificates(pfx_bytes, password.encode("utf-8") if password else None)
    if not key or not cert: raise ValueError("PFX invÃ¡lido/senha incorreta")
    certs = [cert.public_bytes(Encoding.PEM)]
    if chain:
        for c in chain: certs.append(c.public_bytes(Encoding.PEM))
    cert_fd, cert_path = tempfile.mkstemp(suffix=".pem"); os.write(cert_fd, b"".join(certs)); os.close(cert_fd)
    key_fd, key_path = tempfile.mkstemp(suffix=".pem"); os.write(key_fd, key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())); os.close(key_fd)
    return cert_path, key_path

def pfx_extract_cnpj_cpf(pfx_bytes: bytes, password: str):
    """Extrai CNPJ ou CPF do certificado a partir do PFX.
    Retorna tuple (tipo, valor_digits) onde tipo em {"CNPJ","CPF"} ou (None, None).
    """
    key, cert, chain = pkcs12.load_key_and_certificates(pfx_bytes, password.encode("utf-8") if password else None)
    if not cert:
        raise ValueError("Certificado ausente no PFX")
    # Tentar Subject Alternative Name com OtherName OIDs (biblioteca não expõe OtherName value facilmente em todos os casos)
    try:
        san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        for gn in san:
            try:
                # cryptography representa OtherName com .type_id.dotted_string e .value (bytes)
                if isinstance(gn, x509.OtherName):
                    oid = gn.type_id.dotted_string
                    txt = gn.value.decode(errors="ignore") if isinstance(gn.value, (bytes, bytearray)) else str(gn.value)
                    digits = "".join(ch for ch in txt if ch.isdigit())
                    if oid == "2.16.76.1.3.3" and len(digits) >= 14:
                        return ("CNPJ", digits[-14:])
                    if oid == "2.16.76.1.3.1" and len(digits) >= 11:
                        return ("CPF", digits[-11:])
            except Exception:
                continue
    except Exception:
        pass
    # Fallback: serialNumber (2.5.4.5) no Subject
    try:
        for attr in cert.subject:
            if attr.oid == NameOID.SERIAL_NUMBER or attr.oid.dotted_string == "2.5.4.5":
                digits = "".join(ch for ch in attr.value if ch.isdigit())
                if len(digits) >= 14:
                    return ("CNPJ", digits[-14:])
                if len(digits) >= 11:
                    return ("CPF", digits[-11:])
    except Exception:
        pass
    return (None, None)