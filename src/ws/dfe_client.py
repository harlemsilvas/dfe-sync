import time, random, zlib, gzip, base64, certifi, logging
from typing import Tuple, List, Dict, Optional, Generator
import requests
from lxml import etree
from zeep import Client, Settings
from zeep.transports import Transport
import os
from src.settings import settings

NS_WS  = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe"
NS_NFE = "http://www.portalfiscal.inf.br/nfe"
ACTION = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe/nfeDistDFeInteresse"

def _wsdl():
    return settings.AN_WSDL_PRODUCAO if settings.NFE_AMBIENTE.upper().startswith("PROD") else settings.AN_WSDL_HOMOLOG

def _dist_url_candidates() -> list[str]:
    # 1) Override explícito via settings (se fornecido)
    env_prod = settings.NFE_AMBIENTE.upper().startswith("PROD")
    override = settings.AN_DIST_URL_PRODUCAO if env_prod else settings.AN_DIST_URL_HOMOLOG
    candidates = []
    if override:
        candidates.append(override)
    # 2) A partir do WSDL configurado (se permitido)
    if settings.DFE_USE_WSDL:
        wsdl = _wsdl() or ""
        base = (wsdl.split("?")[0]) if wsdl else ""
        if base:
            candidates.append(base)
            if "/ws/" in base:
                candidates.append(base.replace("/ws/", "/"))
    # 3) AN endpoints padrão conhecidos (com e sem /ws/)
    if env_prod:
        candidates += [
            "https://www.nfe.fazenda.gov.br/ws/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
            "https://www.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
            "https://www1.nfe.fazenda.gov.br/ws/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
            "https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
        ]
    else:
        candidates += [
            "https://hom.nfe.fazenda.gov.br/ws/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
            "https://hom.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
            "https://www1-hom.nfe.fazenda.gov.br/ws/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
            "https://www1-hom.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
        ]
    # Remover duplicatas preservando ordem
    uniq = []
    for u in candidates:
        if u and u not in uniq:
            uniq.append(u)
    return uniq

def _create_client_with_fallback(session: requests.Session):
    if not settings.DFE_USE_WSDL:
        return None
    transport = Transport(session=session, timeout=45)
    remote_wsdl = _wsdl()
    local_wsdl = settings.AN_WSDL_LOCAL_PATH or os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "wsdl", "NFeDistribuicaoDFe.wsdl")
    local_wsdl = os.path.abspath(local_wsdl)
    # Tenta remoto primeiro
    try:
        return Client(wsdl=remote_wsdl, transport=transport, settings=Settings(strict=False, xml_huge_tree=True))
    except Exception as e:
        if settings.DFE_DEBUG:
            logger.warning(f"Falha ao carregar WSDL remoto ({remote_wsdl}): {e}. Tentando fallback local: {local_wsdl}")
        if os.path.exists(local_wsdl):
            return Client(wsdl=local_wsdl, transport=transport, settings=Settings(strict=False, xml_huge_tree=True))
        # Sem WSDL: retornar None e forçar modo SOAP direto
        return None

def _endpoint_url_from_wsdl(wsdl_url: str) -> str:
        # Remove sufixo ?WSDL
        return (wsdl_url or '').split('?')[0]

def _post_soap_dist(session: requests.Session, cnpj: str, ult_nsu: str) -> Optional[dict]:
        # Tentar SOAP 1.1 e 1.2 em múltiplos endpoints
        tpAmb = "1" if settings.NFE_AMBIENTE.upper().startswith("PROD") else "2"
        # Envelope SOAP 1.1 com wrapper nfeDadosMsg
        envelope11 = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ws="{NS_WS}" xmlns:nfe="{NS_NFE}">
    <soap:Body>
        <ws:nfeDistDFeInteresse>
            <ws:nfeDadosMsg>
                <distDFeInt xmlns="{NS_NFE}" versao="1.01">
                    <tpAmb>{tpAmb}</tpAmb>
                    <CNPJ>{_digits(cnpj)}</CNPJ>
                    <distNSU>
                        <ultNSU>{_ensure_nsu15(ult_nsu)}</ultNSU>
                    </distNSU>
                </distDFeInt>
            </ws:nfeDadosMsg>
        </ws:nfeDistDFeInteresse>
    </soap:Body>
</soap:Envelope>'''
        # Envelope SOAP 1.2 com wrapper nfeDadosMsg
        envelope12 = f'''<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope" xmlns:ws="{NS_WS}" xmlns:nfe="{NS_NFE}">
    <soap12:Body>
        <ws:nfeDistDFeInteresse>
            <ws:nfeDadosMsg>
                <distDFeInt xmlns="{NS_NFE}" versao="1.01">
                    <tpAmb>{tpAmb}</tpAmb>
                    <CNPJ>{_digits(cnpj)}</CNPJ>
                    <distNSU>
                        <ultNSU>{_ensure_nsu15(ult_nsu)}</ultNSU>
                    </distNSU>
                </distDFeInt>
            </ws:nfeDadosMsg>
        </ws:nfeDistDFeInteresse>
    </soap12:Body>
</soap12:Envelope>'''
        headers11 = {'Content-Type': 'text/xml; charset=utf-8','SOAPAction': ACTION}
        headers12 = {'Content-Type': 'application/soap+xml; charset=utf-8; action="'+ACTION+'"'}
        attempts_log = []
        for candidate in _dist_url_candidates():
            # 1) Tenta SOAP 1.1
            try:
                r = session.post(candidate, data=envelope11.encode('utf-8'), headers=headers11, timeout=45)
                if r.status_code == 200:
                    return {"ok": True, "raw": r.content, "url": candidate, "ver": "1.1"}
                if settings.DFE_DEBUG:
                    logger.error(f"SOAP11 HTTP={r.status_code} url={candidate} body={r.text[:300]}")
                attempts_log.append(f"SOAP11 {candidate} -> HTTP {r.status_code}")
            except Exception as e:
                if settings.DFE_DEBUG:
                    logger.error(f"SOAP11 erro url={candidate} err={e}")
                attempts_log.append(f"SOAP11 {candidate} -> EXC {e}")
            # 2) Tenta SOAP 1.2
            try:
                r = session.post(candidate, data=envelope12.encode('utf-8'), headers=headers12, timeout=45)
                if r.status_code == 200:
                    return {"ok": True, "raw": r.content, "url": candidate, "ver": "1.2"}
                if settings.DFE_DEBUG:
                    logger.error(f"SOAP12 HTTP={r.status_code} url={candidate} body={r.text[:300]}")
                attempts_log.append(f"SOAP12 {candidate} -> HTTP {r.status_code}")
            except Exception as e:
                if settings.DFE_DEBUG:
                    logger.error(f"SOAP12 erro url={candidate} err={e}")
                attempts_log.append(f"SOAP12 {candidate} -> EXC {e}")
        return {"ok": False, "log": "; ".join(attempts_log)}

def _post_soap_consnsu(session: requests.Session, cnpj: str, nsu: str) -> Optional[dict]:
        tpAmb = "1" if settings.NFE_AMBIENTE.upper().startswith("PROD") else "2"
        envelope11 = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ws="{NS_WS}" xmlns:nfe="{NS_NFE}">
    <soap:Body>
        <ws:nfeDistDFeInteresse>
            <ws:nfeDadosMsg>
                <distDFeInt xmlns="{NS_NFE}" versao="1.01">
                    <tpAmb>{tpAmb}</tpAmb>
                    <CNPJ>{_digits(cnpj)}</CNPJ>
                    <consNSU>
                        <NSU>{_ensure_nsu15(nsu)}</NSU>
                    </consNSU>
                </distDFeInt>
            </ws:nfeDadosMsg>
        </ws:nfeDistDFeInteresse>
    </soap:Body>
</soap:Envelope>'''
        envelope12 = f'''<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope" xmlns:ws="{NS_WS}" xmlns:nfe="{NS_NFE}">
    <soap12:Body>
        <ws:nfeDistDFeInteresse>
            <ws:nfeDadosMsg>
                <distDFeInt xmlns="{NS_NFE}" versao="1.01">
                    <tpAmb>{tpAmb}</tpAmb>
                    <CNPJ>{_digits(cnpj)}</CNPJ>
                    <consNSU>
                        <NSU>{_ensure_nsu15(nsu)}</NSU>
                    </consNSU>
                </distDFeInt>
            </ws:nfeDadosMsg>
        </ws:nfeDistDFeInteresse>
    </soap12:Body>
</soap12:Envelope>'''
        headers11 = {'Content-Type':'text/xml; charset=utf-8','SOAPAction': ACTION}
        headers12 = {'Content-Type':'application/soap+xml; charset=utf-8; action="'+ACTION+'"'}
        attempts_log = []
        for candidate in _dist_url_candidates():
            try:
                r = session.post(candidate, data=envelope11.encode('utf-8'), headers=headers11, timeout=45)
                if r.status_code == 200:
                    return {"ok": True, "raw": r.content, "url": candidate, "ver": "1.1"}
                if settings.DFE_DEBUG:
                    logger.error(f"SOAP11 consNSU HTTP=={r.status_code} url={candidate} body={r.text[:300]}")
                attempts_log.append(f"SOAP11 {candidate} -> HTTP {r.status_code}")
            except Exception as e:
                if settings.DFE_DEBUG:
                    logger.error(f"SOAP11 consNSU erro url={candidate} err={e}")
                attempts_log.append(f"SOAP11 {candidate} -> EXC {e}")
            try:
                r = session.post(candidate, data=envelope12.encode('utf-8'), headers=headers12, timeout=45)
                if r.status_code == 200:
                    return {"ok": True, "raw": r.content, "url": candidate, "ver": "1.2"}
                if settings.DFE_DEBUG:
                    logger.error(f"SOAP12 consNSU HTTP=={r.status_code} url={candidate} body={r.text[:300]}")
                attempts_log.append(f"SOAP12 {candidate} -> HTTP {r.status_code}")
            except Exception as e:
                if settings.DFE_DEBUG:
                    logger.error(f"SOAP12 consNSU erro url={candidate} err={e}")
                attempts_log.append(f"SOAP12 {candidate} -> EXC {e}")
        return {"ok": False, "log": "; ".join(attempts_log)}

def _post_soap_conschave(session: requests.Session, cnpj: str, chNFe: str) -> Optional[dict]:
        tpAmb = "1" if settings.NFE_AMBIENTE.upper().startswith("PROD") else "2"
        envelope11 = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ws="{NS_WS}" xmlns:nfe="{NS_NFE}">
    <soap:Body>
        <ws:nfeDistDFeInteresse>
            <ws:nfeDadosMsg>
                <distDFeInt xmlns="{NS_NFE}" versao="1.01">
                    <tpAmb>{tpAmb}</tpAmb>
                    <CNPJ>{_digits(cnpj)}</CNPJ>
                    <consChNFe>
                        <chNFe>{''.join(ch for ch in (chNFe or '') if ch.isdigit())[:44]}</chNFe>
                    </consChNFe>
                </distDFeInt>
            </ws:nfeDadosMsg>
        </ws:nfeDistDFeInteresse>
    </soap:Body>
</soap:Envelope>'''
        envelope12 = f'''<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope" xmlns:ws="{NS_WS}" xmlns:nfe="{NS_NFE}">
    <soap12:Body>
        <ws:nfeDistDFeInteresse>
            <ws:nfeDadosMsg>
                <distDFeInt xmlns="{NS_NFE}" versao="1.01">
                    <tpAmb>{tpAmb}</tpAmb>
                    <CNPJ>{_digits(cnpj)}</CNPJ>
                    <consChNFe>
                        <chNFe>{''.join(ch for ch in (chNFe or '') if ch.isdigit())[:44]}</chNFe>
                    </consChNFe>
                </distDFeInt>
            </ws:nfeDadosMsg>
        </ws:nfeDistDFeInteresse>
    </soap12:Body>
</soap12:Envelope>'''
        headers11 = {'Content-Type':'text/xml; charset=utf-8','SOAPAction': ACTION}
        headers12 = {'Content-Type':'application/soap+xml; charset=utf-8; action="'+ACTION+'"'}
        attempts_log = []
        for candidate in _dist_url_candidates():
            try:
                r = session.post(candidate, data=envelope11.encode('utf-8'), headers=headers11, timeout=45)
                if r.status_code == 200:
                    return {"ok": True, "raw": r.content, "url": candidate, "ver": "1.1"}
                if settings.DFE_DEBUG:
                    logger.error(f"SOAP11 consChave HTTP=={r.status_code} url={candidate} body={r.text[:300]}")
                attempts_log.append(f"SOAP11 {candidate} -> HTTP {r.status_code}")
            except Exception as e:
                if settings.DFE_DEBUG:
                    logger.error(f"SOAP11 consChave erro url={candidate} err={e}")
                attempts_log.append(f"SOAP11 {candidate} -> EXC {e}")
            try:
                r = session.post(candidate, data=envelope12.encode('utf-8'), headers=headers12, timeout=45)
                if r.status_code == 200:
                    return {"ok": True, "raw": r.content, "url": candidate, "ver": "1.2"}
                if settings.DFE_DEBUG:
                    logger.error(f"SOAP12 consChave HTTP=={r.status_code} url={candidate} body={r.text[:300]}")
                attempts_log.append(f"SOAP12 {candidate} -> HTTP {r.status_code}")
            except Exception as e:
                if settings.DFE_DEBUG:
                    logger.error(f"SOAP12 consChave erro url={candidate} err={e}")
                attempts_log.append(f"SOAP12 {candidate} -> EXC {e}")
        return {"ok": False, "log": "; ".join(attempts_log)}

def _sleep_between():
    time.sleep(settings.DFE_SLEEP_BETWEEN_CALLS_MS / 1000.0)

def _backoff(attempt:int):
    base = settings.DFE_BACKOFF_BASE_SEC
    cap  = settings.DFE_BACKOFF_CAP_SEC
    wait = min(base * (2 ** (attempt-1)), cap) * random.uniform(0.5, 1.5)
    time.sleep(wait)

def _inflate_doczip(b64: str) -> bytes:
    raw = base64.b64decode(b64)
    # NT indica GZip; alguns ambientes enviam DEFLATE/zlib. Tentar nessa ordem.
    try:
        # gzip header 0x1f 0x8b
        if len(raw) >= 2 and raw[0] == 0x1F and raw[1] == 0x8B:
            return gzip.decompress(raw)
    except Exception:
        pass
    # tentar zlib com auto header (gzip/zlib) wbits=15+32
    try:
        return zlib.decompress(raw, 15 | 32)
    except zlib.error:
        # fallback: DEFLATE raw (-15)
        return zlib.decompress(raw, -15)

def _ensure_nsu15(nsu: str) -> str:
    digits = ''.join(ch for ch in (nsu or '') if ch.isdigit())
    return digits.zfill(15)[:15]

def _digits(s: str) -> str:
    return ''.join(ch for ch in (s or '') if ch.isdigit())

def _resolve_verify(override: Optional[str|bool]):
    if override is not None:
        return override
    if settings.DFE_CA_BUNDLE:
        return settings.DFE_CA_BUNDLE  # usa bundle customizado (ICP-Brasil)
    return certifi.where()

logger = logging.getLogger("dfe.ws")
if settings.DFE_DEBUG and not logger.handlers:
    h = logging.StreamHandler()
    fmt = logging.Formatter('[DFE] %(asctime)s %(levelname)s %(message)s')
    h.setFormatter(fmt)
    logger.addHandler(h)
    logger.setLevel(logging.DEBUG)

def nfe_distribuicao_dfe(cnpj:str, ult_nsu:str, cert_tuple:Tuple[str,str], verify_ca:Optional[str|bool]=None) -> Dict:
    started = time.time()
    session = requests.Session()
    session.cert = cert_tuple
    session.verify = _resolve_verify(verify_ca)
    client = _create_client_with_fallback(session)

    # Monta distDFeInt (por NSU) usando namespace padrão (sem prefixo) para evitar erro 404 (prefixo de namespace)
    root = etree.Element("distDFeInt", nsmap={None: NS_NFE}, versao="1.01")
    etree.SubElement(root, "tpAmb").text = "1" if settings.NFE_AMBIENTE.upper().startswith("PROD") else "2"
    etree.SubElement(root, "CNPJ").text = cnpj
    cons = etree.SubElement(root, "distNSU")
    etree.SubElement(cons, "ultNSU").text = _ensure_nsu15(ult_nsu)

    # Chama serviço
    if client is not None:
        try:
            resp = client.service.nfeDistDFeInteresse(nfeDistDFeInteresse=root)
        except Exception as e:
            logger.error(f"Falha chamada WS: {e}") if settings.DFE_DEBUG else None
            return {"error":"ws_call","detail":str(e)}
        xml = etree.tostring(resp, encoding="utf-8")
    else:
        raw = _post_soap_dist(session, cnpj, ult_nsu)
        if not raw or not raw.get("ok"):
            det = raw.get("log") if isinstance(raw, dict) else None
            return {"error":"wsdl_404","detail":"Falha WSDL e SOAP direto sem sucesso" + (f" | tentativas: {det}" if det else "")}
        # extrair o retDistDFeInt do envelope SOAP
        env = etree.fromstring(raw["raw"] if isinstance(raw, dict) else raw)
        ret = env.find('.//{http://www.portalfiscal.inf.br/nfe}retDistDFeInt')
        if ret is None:
            # tentar buscar por namespace default
            ret = env.find('.//retDistDFeInt')
        if ret is None:
            return {"error":"parse","detail":"retDistDFeInt não encontrado"}
        xml = etree.tostring(ret, encoding='utf-8')
    doc = etree.fromstring(xml)

    def gx(p): 
        el = doc.find(p, namespaces={"nfe":NS_NFE})
        return el.text if el is not None else None

    cStat  = gx(".//nfe:cStat")
    xMotivo= gx(".//nfe:xMotivo")
    maxNSU = gx(".//nfe:maxNSU")
    ultNSU = gx(".//nfe:ultNSU")

    docs = []
    for el in doc.findall(".//nfe:docZip", namespaces={"nfe":NS_NFE}):
        nsu   = el.get("NSU")
        schema= el.get("schema")
        conteudo = _inflate_doczip(el.text)
        docs.append({"nsu":nsu, "schema":schema, "xml":conteudo})

    elapsed = time.time() - started
    if settings.DFE_DEBUG:
        logger.debug(f"WS distDFe cStat={cStat} xMotivo={xMotivo} ultNSU={ultNSU} maxNSU={maxNSU} docs={len(docs)} t={elapsed:.2f}s")
    return {"cStat":cStat,"xMotivo":xMotivo,"maxNSU":maxNSU,"ultNSU":ultNSU,"docs":docs,"elapsed":elapsed}

def nfe_consultar_nsu(cnpj:str, nsu:str, cert_tuple:Tuple[str,str], verify_ca:Optional[str|bool]=None) -> Dict:
    """
    Consulta pontual por NSU faltante (consNSU), conforme NT 2014/002.
    """
    started = time.time()
    session = requests.Session()
    session.cert = cert_tuple
    session.verify = _resolve_verify(verify_ca)
    client = _create_client_with_fallback(session)

    root = etree.Element("distDFeInt", nsmap={None: NS_NFE}, versao="1.01")
    etree.SubElement(root, "tpAmb").text = "1" if settings.NFE_AMBIENTE.upper().startswith("PROD") else "2"
    etree.SubElement(root, "CNPJ").text = cnpj
    c = etree.SubElement(root, "consNSU")
    etree.SubElement(c, "NSU").text = _ensure_nsu15(nsu)

    if client is not None:
        try:
            resp = client.service.nfeDistDFeInteresse(nfeDistDFeInteresse=root)
        except Exception as e:
            logger.error(f"Falha chamada WS consNSU: {e}") if settings.DFE_DEBUG else None
            return {"error":"ws_call","detail":str(e)}
        xml = etree.tostring(resp, encoding="utf-8")
    else:
        raw = _post_soap_consnsu(session, cnpj, nsu)
        if not raw or not raw.get("ok"):
            det = raw.get("log") if isinstance(raw, dict) else None
            return {"error":"wsdl_404","detail":"Falha WSDL e SOAP direto sem sucesso" + (f" | tentativas: {det}" if det else "")}
        env = etree.fromstring(raw["raw"] if isinstance(raw, dict) else raw)
        ret = env.find('.//{http://www.portalfiscal.inf.br/nfe}retDistDFeInt')
        if ret is None:
            ret = env.find('.//retDistDFeInt')
        if ret is None:
            return {"error":"parse","detail":"retDistDFeInt não encontrado"}
        xml = etree.tostring(ret, encoding='utf-8')
    doc = etree.fromstring(xml)
    def gx(p): 
        el = doc.find(p, namespaces={"nfe":NS_NFE})
        return el.text if el is not None else None
    cStat  = gx(".//nfe:cStat"); xMotivo= gx(".//nfe:xMotivo"); maxNSU = gx(".//nfe:maxNSU"); ultNSU = gx(".//nfe:ultNSU")
    docs = []
    for el in doc.findall(".//nfe:docZip", namespaces={"nfe":NS_NFE}):
        docs.append({"nsu": el.get("NSU"), "schema": el.get("schema"), "xml": _inflate_doczip(el.text)})
    elapsed = time.time() - started
    if settings.DFE_DEBUG:
        logger.debug(f"WS consNSU cStat={cStat} xMotivo={xMotivo} ultNSU={ultNSU} maxNSU={maxNSU} docs={len(docs)} t={elapsed:.2f}s")
    return {"cStat":cStat,"xMotivo":xMotivo,"maxNSU":maxNSU,"ultNSU":ultNSU,"docs":docs,"elapsed":elapsed}

def nfe_consultar_chave(cnpj:str, chNFe:str, cert_tuple:Tuple[str,str], verify_ca:Optional[str|bool]=None) -> Dict:
    """
    Consulta por chave específica (consChNFe) via Distribuição DF-e.
    Retorna metadados e, se autorizado/pertinente, o(s) docZip (procNFe/resNFe/eventos).
    """
    started = time.time()
    session = requests.Session()
    session.cert = cert_tuple
    session.verify = _resolve_verify(verify_ca)
    client = _create_client_with_fallback(session)

    # Payload raiz (para caminho WSDL, se usado)
    root = etree.Element("distDFeInt", nsmap={None: NS_NFE}, versao="1.01")
    etree.SubElement(root, "tpAmb").text = "1" if settings.NFE_AMBIENTE.upper().startswith("PROD") else "2"
    etree.SubElement(root, "CNPJ").text = _digits(cnpj)
    cg = etree.SubElement(root, "consChNFe")
    etree.SubElement(cg, "chNFe").text = ''.join(ch for ch in (chNFe or '') if ch.isdigit())[:44]

    if client is not None:
        try:
            resp = client.service.nfeDistDFeInteresse(nfeDistDFeInteresse=root)
        except Exception as e:
            logger.error(f"Falha chamada WS consChave: {e}") if settings.DFE_DEBUG else None
            return {"error":"ws_call","detail":str(e)}
        xml = etree.tostring(resp, encoding="utf-8")
    else:
        raw = _post_soap_conschave(session, cnpj, chNFe)
        if not raw or not raw.get("ok"):
            det = raw.get("log") if isinstance(raw, dict) else None
            return {"error":"wsdl_404","detail":"Falha WSDL e SOAP direto sem sucesso" + (f" | tentativas: {det}" if det else "")}
        env = etree.fromstring(raw["raw"] if isinstance(raw, dict) else raw)
        ret = env.find('.//{http://www.portalfiscal.inf.br/nfe}retDistDFeInt')
        if ret is None:
            ret = env.find('.//retDistDFeInt')
        if ret is None:
            return {"error":"parse","detail":"retDistDFeInt não encontrado"}
        xml = etree.tostring(ret, encoding='utf-8')

    doc = etree.fromstring(xml)
    def gx(p):
        el = doc.find(p, namespaces={"nfe":NS_NFE})
        return el.text if el is not None else None
    cStat  = gx(".//nfe:cStat"); xMotivo= gx(".//nfe:xMotivo"); maxNSU = gx(".//nfe:maxNSU"); ultNSU = gx(".//nfe:ultNSU")
    docs = []
    for el in doc.findall(".//nfe:docZip", namespaces={"nfe":NS_NFE}):
        docs.append({"nsu": el.get("NSU"), "schema": el.get("schema"), "xml": _inflate_doczip(el.text)})
    elapsed = time.time() - started
    if settings.DFE_DEBUG:
        logger.debug(f"WS consChave cStat={cStat} xMotivo={xMotivo} ultNSU={ultNSU} maxNSU={maxNSU} docs={len(docs)} t={elapsed:.2f}s")
    return {"cStat":cStat,"xMotivo":xMotivo,"maxNSU":maxNSU,"ultNSU":ultNSU,"docs":docs,"elapsed":elapsed}

def pull_until_idle(cnpj:str, start_nsu:str, cert_tuple:Tuple[str,str], verify_ca:str|bool=None) -> Generator[Dict, None, None]:
    """
    Faz pulls em loop atÃ© ultNSU == maxNSU (sem pendÃªncias) ou atÃ© atingir limites de retentativa.
    Trate cStat: 138=Documentos localizados; 137=Nenhum doc; 656=Consumo indevido (aplicar backoff).
    """
    attempts = 0
    cursor_ult = _ensure_nsu15(start_nsu)
    total_docs = 0
    last_max = start_nsu
    while True:
        try:
            res = nfe_distribuicao_dfe(cnpj, cursor_ult, cert_tuple, verify_ca)
            if 'error' in res:
                yield {"error":res.get("error"),"detail":res.get("detail"),"ultNSU":cursor_ult,"maxNSU":last_max}
                break
            cStat = res["cStat"]; ultNSU=res["ultNSU"] or cursor_ult; maxNSU=res["maxNSU"] or last_max
            if cStat in ("108","109"):
                # Serviço paralisado: interrompe ciclo e deixe orquestração agendar nova tentativa.
                yield {"stopped": True, "reason": "service_down", "cStat": cStat, "xMotivo": res.get("xMotivo"), "ultNSU": cursor_ult, "maxNSU": maxNSU, "total_docs": total_docs}
                break

            if cStat == "656":
                # Consumo Indevido: o AN orienta aguardar ~1h e usar sempre o ultNSU da última resposta.
                # Em vez de retentar agressivamente, pausamos o ciclo e deixamos o agendador reagendar.
                yield {"stopped": True, "reason": "consumo_indevido", "wait_sec": 3600,
                       "cStat": cStat, "xMotivo": res.get("xMotivo"),
                       "ultNSU": ultNSU, "maxNSU": maxNSU, "total_docs": total_docs}
                break
            attempts = 0  # reset se sucesso

            docs = res["docs"] or []
            total_docs += len(docs)

            yield {"batch":docs, "ultNSU":ultNSU, "maxNSU":maxNSU, "cStat":cStat, "xMotivo":res["xMotivo"]}

            cursor_ult = ultNSU; last_max = maxNSU
            _sleep_between()

            if ultNSU == maxNSU:
                break

        except requests.RequestException as e:
            attempts += 1
            if attempts > settings.DFE_MAX_ATTEMPTS:
                yield {"error":"http","attempts":attempts,"detail":str(e),"ultNSU":cursor_ult,"maxNSU":last_max}
                break
            _backoff(attempts)
            continue