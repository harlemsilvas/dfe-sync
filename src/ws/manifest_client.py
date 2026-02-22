import time
import logging
from typing import Tuple, Optional, Dict
from lxml import etree
import requests
import base64
from src.settings import settings
import certifi

logger = logging.getLogger(__name__)

NS_NFE = "http://www.portalfiscal.inf.br/nfe"
NS_SOAP12 = "http://www.w3.org/2003/05/soap-envelope"  # SOAP 1.2
NS_SOAP11 = "http://schemas.xmlsoap.org/soap/envelope/"  # SOAP 1.1
NS_WS_EV = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"

def _resolve_event_urls(chave:str) -> list[str]:
    """Lista candidatos de endpoint do serviço de eventos por UF + Ambiente.
    URLs oficiais de acordo com a documentação da Receita Federal (Nov/2025).
    """
    uf = (chave or '')[:2]
    prod = settings.NFE_AMBIENTE.upper().startswith("PROD")
    urls: list[str] = []
    
    # Mapeamento por UF - Produção e Homologação
    # URLs oficiais conforme documentação da SEFAZ
    if uf == '13':  # AM - Amazonas
        urls.append("https://nfe.sefaz.am.gov.br/services2/services/RecepcaoEvento4")
    elif uf == '29':  # BA - Bahia
        urls.append("https://nfe.sefaz.ba.gov.br/webservices/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx")
    elif uf == '52':  # GO - Goiás
        urls.append("https://nfe.sefaz.go.gov.br/nfe/services/NFeRecepcaoEvento4?wsdl")
    elif uf == '31':  # MG - Minas Gerais
        urls.append("https://nfe.fazenda.mg.gov.br/nfe2/services/NFeRecepcaoEvento4")
    elif uf == '50':  # MS - Mato Grosso do Sul
        urls.append("https://nfe.sefaz.ms.gov.br/ws/NFeRecepcaoEvento4")
    elif uf == '51':  # MT - Mato Grosso
        urls.append("https://nfe.sefaz.mt.gov.br/nfews/v2/services/RecepcaoEvento4?wsdl")
    elif uf == '26':  # PE - Pernambuco
        urls.append("https://nfe.sefaz.pe.gov.br/nfe-service/services/NFeRecepcaoEvento4")
    elif uf == '41':  # PR - Paraná
        urls.append("https://nfe.sefa.pr.gov.br/nfe/NFeRecepcaoEvento4?wsdl")
    elif uf == '43':  # RS - Rio Grande do Sul
        urls.append("https://nfe.sefazrs.rs.gov.br/ws/recepcaoevento/recepcaoevento4.asmx")
    elif uf == '35':  # SP - São Paulo
        urls.append("https://nfe.fazenda.sp.gov.br/ws/nferecepcaoevento4.asmx")
    elif uf == '21':  # MA - Maranhão (usa SVAN)
        urls.append("https://www.sefazvirtual.fazenda.gov.br/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx")
    elif uf in ['12', '27', '16', '25', '24', '42']:  # AC, AL, AP, PB, RN, SC (usam SVRS)
        urls.append("https://nfe.svrs.rs.gov.br/ws/recepcaoevento/recepcaoevento4.asmx")
    elif uf in ['23', '53', '32', '15', '25', '33', '22', '11', '14', '17']:  # CE, DF, ES, PA, PB, RJ, PI, RO, RR, TO (usam SVRS)
        urls.append("https://nfe.svrs.rs.gov.br/ws/recepcaoevento/recepcaoevento4.asmx")
    
    # Fallback: Ambiente Nacional (sempre funciona)
    if prod:
        urls += [
            "https://www.nfe.fazenda.gov.br/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx",
            settings.EV_URL_PRODUCAO,
        ]
    else:
        urls += [
            "https://hom1.nfe.fazenda.gov.br/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx",
            settings.EV_URL_HOMOLOG,
        ]
    
    # Dedup preservando ordem
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
    etree.SubElement(inf, "verEvento").text = "1.00"
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
    """Assina o elemento <evento> dentro de <envEvento> usando implementação customizada."""
    from .xml_signer import sign_evento
    return sign_evento(env_evento, cert_pem_path, key_pem_path)

def enviar_manifestacao(cnpj:str, chNFe:str, tpEvento:str, nSeq:int, cert_tuple:Tuple[str,str], verify_ca:Optional[str|bool]=None) -> Dict:
    # SOAP envelope builder
    def _build_envelope(op_name:str, soap_version:str) -> tuple[bytes, dict]:
        # Extrair UF da chave para determinar cUF
        uf_code = chNFe[0:2] if len(chNFe) >= 2 else "91"  # 91 = Ambiente Nacional
        
        if soap_version == "1.2":
            # SOAP 1.2 com Header e Body conforme padrão SEFAZ
            nsmap = {None: NS_SOAP12, "xsi": "http://www.w3.org/2001/XMLSchema-instance", "xsd": "http://www.w3.org/2001/XMLSchema"}
            env = etree.Element("Envelope", nsmap=nsmap)
            
            # Header com nfeCabecMsg
            header = etree.SubElement(env, "Header")
            cabec = etree.SubElement(header, f"{{{NS_WS_EV}}}nfeCabecMsg")
            etree.SubElement(cabec, "cUF").text = uf_code
            etree.SubElement(cabec, "versaoDados").text = "4.00"
            
            # Body com nfeDadosMsg
            body_el = etree.SubElement(env, "Body")
            op = etree.SubElement(body_el, f"{{{NS_WS_EV}}}{op_name}")
            dados = etree.SubElement(op, f"{{{NS_WS_EV}}}nfeDadosMsg")
            dados.append(etree.fromstring(signed_xml_bytes))
            
            soap_xml = etree.tostring(env, encoding='utf-8', xml_declaration=True)
            action = f"{NS_WS_EV}/{op_name}"
            headers = {"Content-Type": f"application/soap+xml; charset=utf-8; action=\"{action}\""}
            return soap_xml, headers
        else:
            # SOAP 1.1 com Header e Body conforme padrão SEFAZ
            nsmap = {None: NS_SOAP11, "xsi": "http://www.w3.org/2001/XMLSchema-instance", "xsd": "http://www.w3.org/2001/XMLSchema"}
            env = etree.Element("Envelope", nsmap=nsmap)
            
            # Header com nfeCabecMsg
            header = etree.SubElement(env, "Header")
            cabec = etree.SubElement(header, f"{{{NS_WS_EV}}}nfeCabecMsg")
            etree.SubElement(cabec, "cUF").text = uf_code
            etree.SubElement(cabec, "versaoDados").text = "4.00"
            
            # Body com nfeDadosMsg
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
    # Em v4, a operação correta conforme WSDL é "nfeRecepcaoEventoNF"
    # Priorizar SOAP 1.2 (mais moderno)
    base_attempts = [
        ("nfeRecepcaoEventoNF","1.2"),
        ("nfeRecepcaoEventoNF","1.1"),
        ("nfeRecepcaoEvento","1.2"),
        ("nfeRecepcaoEvento","1.1"),
    ]
    logger.info(f"🔧 DEBUG base_attempts: {base_attempts}")
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
            logger.info(f"🎯 Tentando URL={url[:60]}... op={op_name} soap={ver}")
            try:
                # Construir XML do evento com cOrgao adequado ao endpoint
                c_orgao = chNFe[0:2] if chNFe and len(chNFe) >= 2 else "91"  # UF da chave ou Nacional
                try:
                    body = _build_manifest_xml(cnpj, chNFe, tpEvento, nSeq, c_orgao)
                    signed = _sign_with_pem(body, cert_tuple[0], cert_tuple[1])
                except Exception as e:
                    return {"error":"sign","detail":str(e)}
                signed_xml_bytes = signed
                soap_xml, headers = _build_envelope(op_name, ver)
                # DEBUG: Salvar XML completo
                if logger.isEnabledFor(logging.DEBUG):
                    import os
                    debug_file = f"/tmp/soap_manifestacao_{op_name}_{ver}.xml"
                    with open(debug_file, 'wb') as f:
                        f.write(soap_xml)
                    logger.debug(f"🔍 XML salvo em: {debug_file}")
                headers.setdefault("Accept", "application/soap+xml, text/xml;q=0.9, */*;q=0.8")
                resp = requests.post(url, data=soap_xml, headers=headers, cert=cert_tuple, verify=_resolve_verify(verify_ca), timeout=45)
                last_resp = resp
                last_meta = {"url": url, "op": op_name, "soap": ver}
                logger.info(f"📊 Resposta: status={resp.status_code} content_type={resp.headers.get('Content-Type','?')[:50]}")
                if resp.status_code != 200:
                    body_preview = resp.text[:600] if resp.text else ""
                    logger.warning(f"❌ Status {resp.status_code}: {body_preview}")
                if resp.status_code == 200:
                    break
            except requests.RequestException as e:
                # Não abortar: tentar próximos endpoints/candidatos
                logger.warning(f"⚠️  Exceção: {type(e).__name__}: {str(e)[:100]}")
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
