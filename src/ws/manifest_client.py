import time
from typing import Tuple, Optional, Dict
from lxml import etree
import requests
import base64
from src.settings import settings
import certifi

NS_NFE = "http://www.portalfiscal.inf.br/nfe"
NS_SOAP12 = "http://www.w3.org/2003/05/soap-envelope"  # SOAP 1.2
NS_SOAP11 = "http://schemas.xmlsoap.org/soap/envelope/"  # SOAP 1.1
NS_WS_EV = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"

def _resolve_event_urls(chave:str) -> list[str]:
    """Lista candidatos de endpoint do serviço de eventos por UF + Ambiente.
    Inclui variações com e sem /ws/ e fallback para Ambiente Nacional.
    """
    uf = (chave or '')[:2]
    prod = settings.NFE_AMBIENTE.upper().startswith("PROD")
    urls: list[str] = []
    if uf == '35':
        if prod:
            urls += [
                # SP Produção
                "https://nfe.fazenda.sp.gov.br/ws/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx",
                "https://nfe.fazenda.sp.gov.br/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx",
            ]
        else:
            urls += [
                # SP Homologação
                "https://homologacao.nfe.fazenda.sp.gov.br/ws/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx",
                "https://homologacao.nfe.fazenda.sp.gov.br/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx",
            ]
    # Fallback Ambiente Nacional
    if prod:
        urls += [
            settings.EV_URL_PRODUCAO,
            # AN Recepção de Evento v4 (caminho oficial costuma ser minúsculo)
            "https://www.nfe.fazenda.gov.br/ws/recepcaoevento/recepcaoevento4.asmx",
            # Possíveis variações de caminho/capitalização
            "https://www.nfe.fazenda.gov.br/ws/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx",
            "https://www.nfe.fazenda.gov.br/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx",
            "https://www.nfe.fazenda.gov.br/ws/RecepcaoEvento/RecepcaoEvento.asmx",
            "https://www.nfe.fazenda.gov.br/RecepcaoEvento/RecepcaoEvento.asmx",
        ]
    else:
        urls += [
            settings.EV_URL_HOMOLOG,
            # AN Homolog
            "https://hom.nfe.fazenda.gov.br/ws/recepcaoevento/recepcaoevento4.asmx",
            # Variações
            "https://hom.nfe.fazenda.gov.br/ws/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx",
            "https://hom.nfe.fazenda.gov.br/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx",
            "https://hom.nfe.fazenda.gov.br/ws/RecepcaoEvento/RecepcaoEvento.asmx",
            "https://hom.nfe.fazenda.gov.br/RecepcaoEvento/RecepcaoEvento.asmx",
        ]
    # dedup preservando ordem
    seen=set(); uniq=[]
    for u in urls:
        if u and u not in seen:
            seen.add(u); uniq.append(u)
    return uniq

def _resolve_verify(override: Optional[str|bool]):
    if override is not None:
        return override
    return settings.DFE_CA_BUNDLE or certifi.where()

def _build_manifest_xml(cnpj:str, chNFe:str, tpEvento:str, nSeqEvento:int, cOrgao:str, justificativa:Optional[str]=None) -> etree._Element:
    # Evento manifestação do destinatário v1.00 (envelopado dentro do envio v4.00)
    env = etree.Element("envEvento", nsmap={None: NS_NFE}, versao="1.00")
    etree.SubElement(env, "idLote").text = str(int(time.time()))
    evento = etree.SubElement(env, "evento", versao="1.00")
    inf = etree.SubElement(evento, "infEvento", Id=f"ID{tpEvento}{chNFe}{nSeqEvento:02d}")
    etree.SubElement(inf, "cOrgao").text = cOrgao
    etree.SubElement(inf, "tpAmb").text = "1" if settings.NFE_AMBIENTE.upper().startswith("PROD") else "2"
    etree.SubElement(inf, "CNPJ").text = cnpj
    etree.SubElement(inf, "chNFe").text = chNFe
    # horário local com offset -03:00 (simplificado); para maior precisão, usar datetime com tzinfo
    etree.SubElement(inf, "dhEvento").text = time.strftime("%Y-%m-%dT%H:%M:%S-03:00", time.localtime())
    etree.SubElement(inf, "tpEvento").text = tpEvento
    etree.SubElement(inf, "nSeqEvento").text = f"{nSeqEvento}"
    det = etree.SubElement(inf, "detEvento", versao="1.00")
    # Desc padrão conforme manual (com acentuação)
    etree.SubElement(det, "descEvento").text = {
        "210200":"Confirmação da Operação",
        "210210":"Ciência da Operação",
        "210220":"Desconhecimento da Operação",
        "210240":"Operação não Realizada",
    }.get(tpEvento, "Ciência da Operação")
    if justificativa:
        etree.SubElement(det, "xJust").text = justificativa
    return env

def _sign_with_pem(env_evento:etree._Element, cert_pem_path:str, key_pem_path:str) -> bytes:
    # Assinatura: inserir <Signature> em <evento>, referenciando #Id do <infEvento>
    # Usa signxml para assinatura enveloped com algoritmo compatível.
    from signxml import XMLSigner, methods
    cert_pem = open(cert_pem_path,'rb').read()
    key_pem = open(key_pem_path,'rb').read()
    signer = XMLSigner(method=methods.enveloped)
    evento = env_evento.find('.//{http://www.portalfiscal.inf.br/nfe}evento')
    inf = env_evento.find('.//{http://www.portalfiscal.inf.br/nfe}infEvento')
    if evento is None or inf is None:
        # fallback: assina raiz
        signed = signer.sign(env_evento, key=key_pem, cert=cert_pem)
        return etree.tostring(signed, encoding='utf-8')
    ref = inf.get('Id')
    if ref and not ref.startswith('#'):
        ref = '#' + ref
    # Assina o elemento "evento", referenciando explicitamente o infEvento
    signed_evento = signer.sign(evento, key=key_pem, cert=cert_pem, reference_uri=ref, signature_algorithm="rsa-sha256", digest_algorithm="sha256")
    # Substituir o nó evento pelo assinado dentro do env_evento
    parent = evento.getparent()
    parent.replace(evento, signed_evento)
    return etree.tostring(env_evento, encoding='utf-8')

def enviar_manifestacao(cnpj:str, chNFe:str, tpEvento:str, nSeq:int, cert_tuple:Tuple[str,str], verify_ca:Optional[str|bool]=None) -> Dict:
    # SOAP envelope builder
    def _build_envelope(op_name:str, soap_version:str) -> tuple[bytes, dict]:
        if soap_version == "1.2":
            env = etree.Element("Envelope", nsmap={None:NS_SOAP12})
            body_el = etree.SubElement(env, "Body")
            op = etree.SubElement(body_el, f"{{{NS_WS_EV}}}{op_name}")
            dados = etree.SubElement(op, f"{{{NS_WS_EV}}}nfeDadosMsg")
            dados.append(etree.fromstring(signed_xml_bytes))
            soap_xml = etree.tostring(env, encoding='utf-8', xml_declaration=True)
            action = f"{NS_WS_EV}/{op_name}"
            headers = {"Content-Type": f"application/soap+xml; charset=utf-8; action=\"{action}\""}
            return soap_xml, headers
        else:
            env = etree.Element("Envelope", nsmap={None:NS_SOAP11})
            body_el = etree.SubElement(env, "Body")
            op = etree.SubElement(body_el, f"{{{NS_WS_EV}}}{op_name}")
            dados = etree.SubElement(op, f"{{{NS_WS_EV}}}nfeDadosMsg")
            dados.append(etree.fromstring(signed_xml_bytes))
            soap_xml = etree.tostring(env, encoding='utf-8', xml_declaration=True)
            action = f"{NS_WS_EV}/{op_name}"
            headers = {
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": f"\"{action}\"",
            }
            return soap_xml, headers

    urls = _resolve_event_urls(chNFe)
    # Em v4, a operação padrão costuma ser "nfeRecepcaoEvento" no WSDL NFeRecepcaoEvento4; incluir variações
    base_attempts = [
        ("nfeRecepcaoEvento","1.2"),
        ("nfeRecepcaoEvento4","1.2"),
        ("nfeRecepcaoEvento","1.1"),
        ("nfeRecepcaoEvento4","1.1"),
        ("NFeRecepcaoEvento","1.2"),
        ("NFeRecepcaoEvento4","1.2"),
        ("NFeRecepcaoEvento","1.1"),
        ("NFeRecepcaoEvento4","1.1"),
    ]
    last_resp = None
    last_meta = None
    last_error = None
    cUF = (chNFe or '')[:2] or "91"

    def _is_an(url: str) -> bool:
        h = url.lower()
        return "nfe.fazenda.gov.br" in h

    for url in urls:
        # Priorizar SOAP 1.1 em alguns endpoints estaduais (ex.: SP)
        is_sp = "fazenda.sp.gov.br" in url.lower()
        attempts = base_attempts
        if is_sp:
            attempts = [
                (op, ver) for (op, ver) in base_attempts
                if ver == "1.1"
            ] + [
                (op, ver) for (op, ver) in base_attempts
                if ver == "1.2"
            ]
        for op_name, ver in attempts:
            try:
                # Construir XML do evento com cOrgao adequado ao endpoint
                c_orgao = "91" if _is_an(url) else cUF
                try:
                    body = _build_manifest_xml(cnpj, chNFe, tpEvento, nSeq, c_orgao)
                    signed = _sign_with_pem(body, cert_tuple[0], cert_tuple[1])
                except Exception as e:
                    return {"error":"sign","detail":str(e)}
                signed_xml_bytes = signed
                soap_xml, headers = _build_envelope(op_name, ver)
                headers.setdefault("Accept", "application/soap+xml, text/xml;q=0.9, */*;q=0.8")
                resp = requests.post(url, data=soap_xml, headers=headers, cert=cert_tuple, verify=_resolve_verify(verify_ca), timeout=45)
                last_resp = resp
                last_meta = {"url": url, "op": op_name, "soap": ver}
                if resp.status_code == 200:
                    break
            except requests.RequestException as e:
                # Não abortar: tentar próximos endpoints/candidatos
                last_resp = None
                last_error = str(e)
                last_meta = {"url": url, "op": op_name, "soap": ver}
                continue
        if last_resp is not None and last_resp.status_code == 200:
            break
    if last_resp is None:
        out = {"error":"http","detail": last_error or "sem resposta"}
        if last_meta:
            out.update(last_meta)
        return out
    out = {"status_code": last_resp.status_code}
    if last_resp.status_code != 200:
        out["error"] = "http"
        out["body"] = last_resp.text[:500]
        if last_meta:
            out.update(last_meta)
        return out
    try:
        doc = etree.fromstring(last_resp.content)
        ns = {"soap":"http://www.w3.org/2003/05/soap-envelope", "nfe":NS_NFE}
        # Procurar retEnvEvento/retEvento
        cStat = doc.find('.//nfe:cStat', ns)
        xMotivo = doc.find('.//nfe:xMotivo', ns)
        out.update({
            "cStat": cStat.text if cStat is not None else None,
            "xMotivo": xMotivo.text if xMotivo is not None else None,
            "resp_xml": last_resp.content.decode('utf-8','ignore')
        })
    except Exception as e:
        out["error"] = "parse"
        out["detail"] = str(e)
    return out
