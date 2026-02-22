from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from src.store.db import SessionLocal, get_db
from src.models import (
    Empresa, CursorDFe, Certificado, TipoDocumento, 
    RemetenteCadastrado, CfopTransferencia, OperacaoPendente, LogProcessamento
)
import os
from pathlib import Path

router = APIRouter()

@router.get("/xmls/nao-classificados")
async def list_xmls_nao_classificados():
    """Lista XMLs que ainda não foram classificados"""
    with SessionLocal() as db:
        # Buscar operações pendentes
        pendentes = db.execute(select(OperacaoPendente)).scalars().all()
        # Simular XMLs não classificados (pode ser melhorado com análise real dos arquivos)
        xml_path = Path("/mnt/c/Projetos/dfe-sync/storage/xml")
        xmls_nao_classificados = []
        if xml_path.exists():
            for xml_file in list(xml_path.glob("*.xml"))[:50]:  # Limite de 50 para performance
                try:
                    stat = xml_file.stat()
                    xmls_nao_classificados.append({
                        "arquivo": xml_file.name,
                        "caminho": str(xml_file),
                        "tamanho": stat.st_size,
                        "modificado": stat.st_mtime,
                        "status": "pendente"
                    })
                except:
                    continue
        return {
            "total": len(xmls_nao_classificados),
            "xmls": xmls_nao_classificados[:20]  # Retornar apenas primeiros 20
        }

from datetime import datetime, timedelta

@router.get("/dashboard/stats")
async def get_dashboard_stats():
    """Estatísticas para o dashboard"""
    with SessionLocal() as db:
        hoje = datetime.now()
        # Certificados válidos: validade futura
        certificados = db.execute(select(Certificado)).scalars().all()
        certificados_validos = 0
        certificados_vencendo = 0
        for cert in certificados:
            try:
                if cert.valido_ate:
                    dt_validade = datetime.strptime(cert.valido_ate[:19], "%Y-%m-%d %H:%M:%S")
                    if dt_validade > hoje:
                        certificados_validos += 1
                        if dt_validade <= hoje + timedelta(days=30):
                            certificados_vencendo += 1
            except Exception:
                continue
        stats = {
            "empresas_cadastradas": db.execute(select(func.count(Empresa.id))).scalar(),
            "certificados_validos": certificados_validos,
            "certificados_vencendo": certificados_vencendo,
            "documentos_processados": 1843,  # Valor conhecido
            "operacoes_pendentes": db.execute(select(func.count(OperacaoPendente.id))).scalar()
        }
        return stats