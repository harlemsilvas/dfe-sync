import time, random, zlib, base64, certifi
from typing import Tuple, List, Dict
import requests
from lxml import etree
from zeep import Client, Settings
from zeep.transports import Transport
from src.settings import settings
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

NS_WS  = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe"
NS_NFE = "http://www.portalfiscal.inf.br/nfe"
ACTION = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe/nfeDistDFeInteresse"

def _wsdl():
    # URLs oficiais do Ambiente Nacional para NFeDistribuicaoDFe (Nov/2025)
    # Ambiente Nacional é o único que oferece o serviço de Distribuição DFe
    if settings.NFE_AMBIENTE.upper().startswith("PROD"):
        return "https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx?WSDL"
    else:
        return "https://hom1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx?WSDL"

def _sleep_between():
    time.sleep(settings.DFE_SLEEP_BETWEEN_CALLS_MS / 1000.0)

def _backoff(attempt:int):
    base = settings.DFE_BACKOFF_BASE_SEC
    cap  = settings.DFE_BACKOFF_CAP_SEC
    wait = min(base * (2 ** (attempt-1)), cap) * random.uniform(0.5, 1.5)
    time.sleep(wait)

def _inflate_doczip(b64: str) -> bytes:
    raw = base64.b64decode(b64)
    # docZip = DEFLATE (raw). zlib -15 = raw deflate
    try: return zlib.decompress(raw, -15)
    except zlib.error:
        # fallback: tente zlib normal
        return zlib.decompress(raw)

def nfe_distribuicao_dfe(cnpj:str, ult_nsu:str, cert_tuple:Tuple[str,str], verify_ca:str|bool=None) -> Dict:
    logger.info(f"📞 Chamando NFeDistribuicaoDFe - CNPJ: {cnpj}, ultNSU: {ult_nsu}")
    logger.info(f"🔐 Certificado: {cert_tuple[0][:50]}...")
    logger.info(f"🔒 CA Bundle: {verify_ca}")
    logger.info(f"🌐 WSDL: {_wsdl()}")
    logger.info(f"🏢 Ambiente: {settings.NFE_AMBIENTE}")
    
    session = requests.Session()
    session.cert = cert_tuple
    session.verify = verify_ca if verify_ca is not None else certifi.where()
    transport = Transport(session=session, timeout=45)
    
    try:
        logger.info("🔄 Criando cliente SOAP...")
        client = Client(wsdl=_wsdl(), transport=transport, settings=Settings(strict=False, xml_huge_tree=True))
        
        logger.info(f"🎯 Cliente criado com sucesso")

        # Monta distDFeInt (por NSU)
        root = etree.Element("{%s}distDFeInt" % NS_NFE, versao="1.01")
        etree.SubElement(root, "{%s}tpAmb" % NS_NFE).text = "1" if settings.NFE_AMBIENTE.upper().startswith("PROD") else "2"
        etree.SubElement(root, "{%s}cUFAutor" % NS_NFE).text = "91"   # 91 = AN (Ambiente Nacional)
        etree.SubElement(root, "{%s}CNPJ" % NS_NFE).text = cnpj
        cons = etree.SubElement(root, "{%s}distNSU" % NS_NFE)
        etree.SubElement(cons, "{%s}ultNSU" % NS_NFE).text = ult_nsu

        logger.info("📤 Enviando requisição SOAP...")
        # Chama serviço - parâmetro correto é nfeDadosMsg
        resp = client.service.nfeDistDFeInteresse(nfeDadosMsg=root)
        
        logger.info("📥 Resposta recebida, processando...")
        # resp = retDistDFeInt
        xml = etree.tostring(resp, encoding="utf-8")
        doc = etree.fromstring(xml)

        def gx(p): 
            el = doc.find(p, namespaces={"nfe":NS_NFE})
            return el.text if el is not None else None

        cStat  = gx(".//nfe:cStat")
        xMotivo= gx(".//nfe:xMotivo")
        maxNSU = gx(".//nfe:maxNSU")
        ultNSU = gx(".//nfe:ultNSU")

        logger.info(f"📊 Resposta: cStat={cStat}, xMotivo={xMotivo}, ultNSU={ultNSU}, maxNSU={maxNSU}")

        docs = []
        for el in doc.findall(".//nfe:docZip", namespaces={"nfe":NS_NFE}):
            nsu   = el.get("NSU")
            schema= el.get("schema")
            conteudo = _inflate_doczip(el.text)
            docs.append({"nsu":nsu, "schema":schema, "xml":conteudo})

        logger.info(f"📦 Documentos encontrados: {len(docs)}")
        return {"cStat":cStat,"xMotivo":xMotivo,"maxNSU":maxNSU,"ultNSU":ultNSU,"docs":docs}
        
    except Exception as e:
        logger.error(f"❌ Erro na requisição SOAP: {type(e).__name__}: {e}", exc_info=True)
        raise

def pull_until_idle(cnpj:str, start_nsu:str, cert_tuple:Tuple[str,str], verify_ca:str|bool=None) -> Dict:
    """
    Faz pulls em loop até ultNSU == maxNSU (sem pendências) ou até atingir limites de retentativa.
    Trate cStat: 138=Documentos localizados; 137=Nenhum doc; 656=Consumo indevido (aplicar backoff).
    """
    logger.info(f"🔄 Iniciando pull - CNPJ: {cnpj}, NSU inicial: {start_nsu}")
    attempts = 0
    cursor_ult = start_nsu
    total_docs = 0
    last_max = start_nsu
    while True:
        try:
            res = nfe_distribuicao_dfe(cnpj, cursor_ult, cert_tuple, verify_ca)
            cStat = res["cStat"]; ultNSU=res["ultNSU"] or cursor_ult; maxNSU=res["maxNSU"] or last_max
            if cStat == "656":
                logger.warning(f"⚠️ Consumo indevido (656) - Tentativa {attempts+1}/{settings.DFE_MAX_ATTEMPTS}")
                attempts += 1
                if attempts > settings.DFE_MAX_ATTEMPTS:
                    logger.error(f"❌ Máximo de tentativas atingido por consumo indevido")
                    return {"stopped":True,"reason":"consumo_indevido","attempts":attempts,"ultNSU":cursor_ult,"maxNSU":maxNSU,"total_docs":total_docs}
                _backoff(attempts);  # backoff e tenta de novo
                continue
            attempts = 0  # reset se sucesso

            docs = res["docs"] or []
            total_docs += len(docs)

            yield {"batch":docs, "ultNSU":ultNSU, "maxNSU":maxNSU, "cStat":cStat, "xMotivo":res["xMotivo"]}

            cursor_ult = ultNSU; last_max = maxNSU
            _sleep_between()

            if ultNSU == maxNSU:
                logger.info(f"✅ Pull concluído - ultNSU == maxNSU ({ultNSU})")
                break

        except requests.RequestException as e:
            logger.error(f"❌ Erro HTTP (Tentativa {attempts+1}/{settings.DFE_MAX_ATTEMPTS}): {type(e).__name__}: {e}", exc_info=True)
            attempts += 1
            if attempts > settings.DFE_MAX_ATTEMPTS:
                logger.error(f"❌ Máximo de tentativas HTTP atingido")
                yield {"error":"http","attempts":attempts,"ultNSU":cursor_ult,"maxNSU":last_max}
                break
            _backoff(attempts)
            continue
