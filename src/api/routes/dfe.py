from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from pathlib import Path
from src.store.db import SessionLocal
from src.models import Empresa, Certificado, CursorDFe, DFEDocumento
from src.cert.pfx_utils import pfx_to_pem_tempfiles
from src.core.dfe_sync import run_distribution
from src.ws.manifest_client import enviar_manifestacao
import os, certifi
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def _load_cert_tuple(empresa_id:int):
    logger.info(f"🔍 Carregando certificado para empresa_id={empresa_id}")
    with SessionLocal() as db:
        cert = db.execute(select(Certificado).where(Certificado.empresa_id==empresa_id)).scalar_one_or_none()
        emp  = db.execute(select(Empresa).where(Empresa.id==empresa_id)).scalar_one_or_none()
        if not emp: 
            logger.error(f"❌ Empresa não encontrada: id={empresa_id}")
            raise HTTPException(404,"Empresa não encontrada")
        if not cert: 
            logger.error(f"❌ Certificado não cadastrado para empresa_id={empresa_id}")
            raise HTTPException(400,"Certificado não cadastrado")
        
        # Determinar se é certificado antigo (arquivo) ou novo (BYTEA)
        if cert.pfx_path and os.path.exists(cert.pfx_path):
            # Certificado antigo - arquivo no disco
            logger.info(f"📄 Certificado arquivo encontrado: pfx_path={cert.pfx_path}")
            pfx_size = os.path.getsize(cert.pfx_path)
            logger.info(f"📦 Arquivo PFX: tamanho={pfx_size} bytes")
            pfx = open(cert.pfx_path,"rb").read()
            senha = cert.senha_cripto
        elif cert.pfx_file and cert.pfx_password_encrypted:
            # Certificado novo - BYTEA no banco com senha criptografada
            logger.info(f"📄 Certificado BYTEA encontrado: tamanho={len(cert.pfx_file)} bytes")
            pfx = cert.pfx_file
            
            # Descriptografar senha usando a mesma lógica do CRUD
            from src.crud.certificados import decrypt_password
            senha = decrypt_password(cert.pfx_password_encrypted)
        else:
            logger.error(f"❌ Certificado sem dados válidos: pfx_path={cert.pfx_path}, pfx_file={'presente' if cert.pfx_file else 'ausente'}")
            raise HTTPException(400, "Certificado sem dados válidos")
        
        logger.info(f"🔐 Tentando extrair certificado e chave privada")
        
        try:
            cert_path, key_path = pfx_to_pem_tempfiles(pfx, senha)
            logger.info(f"✅ Certificado extraído: cert={cert_path}, key={key_path}")
            return (emp, cert_path, key_path)
        except Exception as e:
            logger.error(f"❌ Erro ao extrair certificado: {e}")
            raise HTTPException(500, f"Erro ao processar certificado: {str(e)}")

@router.get("/dfe/cursor")
def get_cursor(empresa_id:int=Query(...)):
    with SessionLocal() as db:
        cur = db.execute(select(CursorDFe).where(CursorDFe.empresa_id==empresa_id)).scalar_one_or_none()
        if not cur: raise HTTPException(404,"Cursor não encontrado")
        return {"empresa_id":empresa_id,"ultimo_nsu":cur.ultimo_nsu,"max_nsu":cur.max_nsu,"updated_at":str(cur.updated_at)}

@router.post("/dfe/sync")
def sync_now(empresa_id:int=Query(...)):
    logger.info(f"🚀 Iniciando sincronização para empresa_id={empresa_id}")
    cert_tuple = None
    try:
        emp, cert_path, key_path = _load_cert_tuple(empresa_id)
        cert_tuple = (cert_path, key_path)
        verify = certifi.where()
        logger.info(f"🔒 Usando bundle CA: {verify}")
        logger.info(f"📡 Chamando serviço de distribuição DFe...")
        res = run_distribution(emp.id, emp.cnpj, cert_tuple, verify)
        logger.info(f"✅ Sincronização concluída: {res}")
        return res
    except Exception as e:
        logger.error(f"❌ Erro na sincronização: {e}", exc_info=True)
        raise
    finally:
        if cert_tuple:
            for p in cert_tuple:
                try:
                    if p and os.path.exists(p): 
                        os.remove(p)
                        logger.debug(f"🗑️ Arquivo temporário removido: {p}")
                except: pass

@router.get("/dfe/conschave/download")
def download_by_chave(
    empresa_id: int = Query(...),
    chNFe: str = Query(...),
    prefer: str = Query("procNFe")  # procNFe, resNFe, resEvento, procEvento
):
    """
    Baixa XML de um documento específico pela chave de acesso.
    Retorna o arquivo XML encontrado, priorizando o tipo solicitado.
    """
    with SessionLocal() as db:
        # Buscar documentos com essa chave
        docs = db.execute(
            select(DFEDocumento)
            .where(DFEDocumento.empresa_id == empresa_id)
            .where(DFEDocumento.chave == chNFe)
            .order_by(DFEDocumento.id.desc())
        ).scalars().all()
        
        if not docs:
            raise HTTPException(404, f"Nenhum documento encontrado para chave {chNFe}")
        
        # Tentar encontrar o tipo preferido
        preferred_doc = None
        for doc in docs:
            if prefer in doc.schema:
                preferred_doc = doc
                break
        
        # Se não encontrou o preferido, pega o primeiro
        if not preferred_doc:
            preferred_doc = docs[0]
        
        # Verificar se arquivo existe
        xml_path = Path(preferred_doc.caminho_xml)
        if not xml_path.exists():
            raise HTTPException(404, f"Arquivo XML não encontrado: {xml_path}")
        
        # Retornar arquivo
        return FileResponse(
            path=xml_path,
            media_type="application/xml",
            filename=xml_path.name
        )

@router.post("/dfe/manifestar")
def manifestar(
    empresa_id: int = Query(...),
    chNFe: str = Query(..., min_length=44, max_length=44),
    tpEvento: str = Query(...),  # 210200, 210210, 210220, 210240
    nSeq: int = Query(1)
):
    """
    Envia evento de manifestação do destinatário para a SEFAZ.
    
    Tipos de evento:
    - 210200: Confirmação da Operação
    - 210210: Ciência da Operação
    - 210220: Desconhecimento da Operação
    - 210240: Operação não Realizada
    """
    logger.info(f"📝 Manifestação: empresa_id={empresa_id}, chNFe={chNFe}, tpEvento={tpEvento}, nSeq={nSeq}")
    
    cert_tuple = None
    try:
        emp, cert_path, key_path = _load_cert_tuple(empresa_id)
        cert_tuple = (cert_path, key_path)
        
        # Remover formatação do CNPJ
        cnpj = ''.join(c for c in emp.cnpj if c.isdigit())
        
        logger.info(f"📡 Enviando manifestação para SEFAZ...")
        result = enviar_manifestacao(
            cnpj=cnpj,
            chNFe=chNFe,
            tpEvento=tpEvento,
            nSeq=nSeq,
            cert_tuple=cert_tuple,
            verify_ca=certifi.where()
        )
        
        logger.info(f"📨 Resposta SEFAZ: {result}")
        
        # Verificar se houve sucesso
        if 'error' in result:
            logger.error(f"❌ Erro na manifestação: {result}")
            raise HTTPException(500, f"Erro ao enviar manifestação: {result.get('error')} - {result.get('detail', '')}")
        
        # Verificar cStat
        cStat = result.get('cStat')
        if cStat in ['135', '136']:  # 135=Evento registrado, 136=Evento já registrado
            logger.info(f"✅ Manifestação enviada com sucesso: {cStat}")
        else:
            logger.warning(f"⚠️ Manifestação com status diferente: {cStat} - {result.get('xMotivo')}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao processar manifestação: {e}", exc_info=True)
        raise HTTPException(500, f"Erro ao processar manifestação: {str(e)}")
    finally:
        if cert_tuple:
            for p in cert_tuple:
                try:
                    if p and os.path.exists(p):
                        os.remove(p)
                        logger.debug(f"🗑️ Certificado temporário removido: {p}")
                except:
                    pass
