# src/api/routes/xmls.py
"""
Endpoint para listagem de XMLs não classificados
Estrutura esperada:
  docs/
  ├── {chave_nfe}-nfe.xml          (ex: 35251042580092002977551600000125381568142699-nfe.xml)
  └── {cnpj}/
      ├── {nsu}_{schema}.xml       (ex: 000000000011206_resEvento_v1.01.xsd.xml)
      └── {nsu}_{schema}.xml
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.store.db import get_db
from src.models import DFEDocumento

router = APIRouter(prefix="/xmls", tags=["XMLs"])
logger = logging.getLogger(__name__)

def get_docs_path() -> Path:
    """
    Descobre automaticamente o diretório 'docs/' na raiz do projeto.
    """
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent  # Sobe até /mnt/c/Projetos/dfe-sync
    
    candidates = [
        project_root / "docs",
        Path("docs"),  # Relativo ao cwd
    ]
    
    for path in candidates:
        if path.exists() and path.is_dir():
            logger.info(f"✅ Diretório docs encontrado: {path}")
            return path.resolve()
    
    raise HTTPException(
        status_code=404,
        detail="Diretório 'docs/' não encontrado na raiz do projeto"
    )

def extract_nsu_or_chave(filename: str) -> tuple[Optional[str], Optional[str], str]:
    """
    Extrai NSU/chave e schema do nome do arquivo.
    Retorna: (nsu_ou_chave, schema, tipo_identificador)
    
    Padrões suportados:
      - {nsu}_{schema}.xml          → NSU
      - {chave}-nfe.xml             → Chave NF-e
      - {chave}.xml                 → Chave genérica
    """
    if not filename.endswith(".xml"):
        return None, None, "invalido"
    
    basename = filename[:-4]  # Remover .xml
    
    # Padrão 1: {nsu}_{schema}.xml (ex: 000000000011206_resEvento_v1.01.xsd)
    if "_" in basename:
        parts = basename.split("_", 1)
        nsu_candidate = parts[0].strip()
        
        if nsu_candidate.isdigit() and len(nsu_candidate) <= 15:
            nsu_normalized = nsu_candidate.zfill(15)
            schema = parts[1].replace(".xsd", "").strip() if len(parts) > 1 else "desconhecido"
            return nsu_normalized, schema, "nsu"
    
    # Padrão 2: {chave}-nfe.xml (ex: 35251042580092002977551600000125381568142699-nfe)
    if "-nfe" in basename:
        chave = basename.split("-nfe")[0].strip()
        if len(chave) >= 44:  # Chave NF-e tem 44 dígitos
            return chave[-44:], "procNFe", "chave"
    
    # Padrão 3: {chave}.xml (fallback)
    if len(basename) >= 44 and basename.isdigit():
        return basename[-44:], "desconhecido", "chave"
    
    # Não identificado
    return basename, "desconhecido", "desconhecido"

def is_xml_processed(db: Session, nsu: Optional[str], chave: Optional[str]) -> bool:
    """
    Verifica se XML já foi processado.
    Busca por NSU OU chave no banco.
    """
    if nsu:
        stmt = select(DFEDocumento.id).where(DFEDocumento.nsu == nsu).limit(1)
        if db.execute(stmt).scalar() is not None:
            return True
    
    if chave:
        stmt = select(DFEDocumento.id).where(DFEDocumento.chave == chave).limit(1)
        if db.execute(stmt).scalar() is not None:
            return True
    
    return False

@router.get("/nao-classificados")
async def list_xmls_nao_classificados(
    page: int = Query(1, ge=1, description="Página (inicia em 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
    db: Session = Depends(get_db)
):
    """
    Lista XMLs em docs/ que ainda não foram classificados/processados.
    
    Estratégia:
      1. Varre docs/ recursivamente
      2. Extrai NSU ou chave do nome do arquivo
      3. Verifica se já existe em dfe_documentos (por NSU ou chave)
      4. Retorna apenas não processados
    """
    try:
        docs_path = get_docs_path()
        logger.info(f"📁 Procurando XMLs em: {docs_path}")
        
        # Listar XMLs (ignorar diretórios ocultos/backup)
        xml_files = []
        for ext in ["*.xml", "*.XML"]:
            for path in docs_path.rglob(ext):
                if not any(p.startswith((".", "_", "backup", "tmp")) for p in path.parts):
                    xml_files.append(path)
        
        logger.info(f"📄 Encontrados {len(xml_files)} arquivos XML em docs/")
        
        # Filtrar não processados
        nao_processados = []
        for xml_file in xml_files:
            filename = xml_file.name
            
            # Extrair identificador (NSU ou chave)
            identificador, schema, tipo_id = extract_nsu_or_chave(filename)
            
            if not identificador:
                continue
            
            # Verificar se já foi processado
            is_nsu = tipo_id == "nsu"
            is_chave = tipo_id == "chave"
            
            if is_xml_processed(
                db, 
                nsu=identificador if is_nsu else None,
                chave=identificador if is_chave else None
            ):
                continue
            
            # Coletar metadados
            try:
                stat = xml_file.stat()
                # Identificar CNPJ pelo caminho (se existir diretório com CNPJ)
                cnpj = "N/A"
                for parent in xml_file.parents:
                    dirname = parent.name
                    digits = "".join(c for c in dirname if c.isdigit())
                    if len(digits) >= 14:
                        cnpj = digits[-14:]
                        break
                
                nao_processados.append({
                    "arquivo": filename,
                    "caminho": str(xml_file.relative_to(docs_path)),
                    "identificador": identificador,
                    "tipo_identificador": tipo_id,
                    "schema": schema,
                    "cnpj_empresa": cnpj,
                    "tamanho_kb": round(stat.st_size / 1024, 2),
                    "modificado": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "status": "nao_classificado"
                })
            except Exception as e:
                logger.warning(f"⚠️  Erro ao processar {xml_file}: {e}")
                continue
        
        # Paginação
        total = len(nao_processados)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = nao_processados[start:end]
        
        logger.info(f"✅ XMLs não classificados: {total} (página {page})")
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "xmls": paginated,
            "docs_path": str(docs_path),
            "debug": {
                "xmls_encontrados": len(xml_files),
                "xmls_processados": len(xml_files) - total,
                "exemplos_nomes": [f.name for f in xml_files[:3]] if xml_files else []
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"💥 Erro no endpoint /xmls/nao-classificados: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
    

@router.post("/processar-nao-classificados")
async def processar_xmls_nao_classificados(
    limit: int = Query(50, ge=1, le=200, description="Máximo de XMLs a processar"),
    confirmacao: bool = Query(False, description="Confirmação obrigatória para limit > 50"),
    empresa_id: Optional[int] = Query(None, description="Processar apenas XMLs desta empresa (pelo CNPJ no caminho)"),
    schema_filtro: Optional[str] = Query(None, description="Filtrar por schema (ex: 'resNFe', 'resEvento')"),
    forcar: bool = Query(False, description="Forçar importação mesmo se já existir no banco"),
    db: Session = Depends(get_db)
):
    """
    Processa XMLs não classificados do diretório docs/ e importa para o banco.
    Versão compatível com schema: dfe_documentos (sem conteudo_base64)
    """
    try:
        # ✅ VALIDAÇÃO DE SEGURANÇA (ANTES de qualquer processamento)
        if limit > 50 and not confirmacao:
            raise HTTPException(
                status_code=400,
                detail=f"⚠️ Confirmação necessária para processar {limit} XMLs.\n"
                       f"Use o parâmetro: confirmacao=true"
            )
        
        docs_path = get_docs_path()
        logger.info(f"🔄 Iniciando processamento de XMLs em: {docs_path}")       
        
      
        # Listar XMLs
        xml_files = []
        for ext in ["*.xml", "*.XML"]:
            for path in docs_path.rglob(ext):
                if not any(p.startswith((".", "_", "backup", "tmp")) for p in path.parts):
                    xml_files.append(path)
        
        logger.info(f"📄 Encontrados {len(xml_files)} XMLs para análise")
        
        # Dentro da função processar_xmls_nao_classificados, antes do processamento:
        if limit > 50 and not confirmacao:
            raise HTTPException(
                status_code=400,
                detail=f"Confirmação necessária para processar {limit} XMLs. Use parametro confirmacao=true"
                )
        
        # Filtrar não processados
        a_processar = []
        for xml_file in xml_files:
            filename = xml_file.name
            identificador, schema, tipo_id = extract_nsu_or_chave(filename)
            
            if not identificador:
                continue
            
            # Filtro por schema
            if schema_filtro and schema_filtro.lower() not in schema.lower():
                continue
            
            # Filtro por empresa (CNPJ no caminho)
            if empresa_id:
                cnpj_empresa = "N/A"
                for parent in xml_file.parents:
                    dirname = parent.name
                    digits = "".join(c for c in dirname if c.isdigit())
                    if len(digits) >= 14:
                        cnpj_empresa = digits[-14:]
                        break
                
                # Buscar empresa pelo CNPJ
                from src.models import Empresa
                empresa = db.execute(
                    select(Empresa).where(Empresa.cnpj.contains(cnpj_empresa[-8:]))
                ).scalar_one_or_none()
                
                if not empresa or empresa.id != empresa_id:
                    continue
            
            # Verificar se já existe (a menos que forçado)
            if not forcar and is_xml_processed(
                db,
                nsu=identificador if tipo_id == "nsu" else None,
                chave=identificador if tipo_id == "chave" else None
            ):
                continue
            
            a_processar.append({
                "path": xml_file,
                "identificador": identificador,
                "tipo_id": tipo_id,
                "schema": schema
            })
        
        # Limitar quantidade
        a_processar = a_processar[:limit]
        total = len(a_processar)
        logger.info(f"⚙️  Selecionados {total} XMLs para processamento")
        
        # Processar
        sucesso = 0
        erros = 0
        detalhes = []
        
        for item in a_processar:
            xml_file = item["path"]
            identificador = item["identificador"]
            tipo_id = item["tipo_id"]
            schema = item["schema"]
            
            try:
                # Ler XML
                xml_bytes = xml_file.read_bytes()
                
                # Classificar documento
                classificacao = _classificar_documento_xml(xml_bytes, schema)
                
                # Identificar empresa pelo CNPJ no caminho
                cnpj_empresa = "N/A"
                for parent in xml_file.parents:
                    dirname = parent.name
                    digits = "".join(c for c in dirname if c.isdigit())
                    if len(digits) >= 14:
                        cnpj_empresa = digits[-14:]
                        break
                
                # Buscar empresa no banco
                from src.models import Empresa
                empresa = None
                if cnpj_empresa != "N/A":
                    empresa = db.execute(
                        select(Empresa).where(Empresa.cnpj.like(f"%{cnpj_empresa}%"))
                    ).scalar_one_or_none()
                
                if not empresa:
                    # Fallback para empresa_id fornecido ou empresa 2
                    empresa_id_usar = empresa_id or 2
                    empresa = db.execute(
                        select(Empresa).where(Empresa.id == empresa_id_usar)
                    ).scalar_one_or_none()
                
                if not empresa:
                    raise ValueError(f"Empresa não encontrada para CNPJ {cnpj_empresa}")
                
                # ✅ CORREÇÃO: Usar APENAS campos existentes no seu modelo
                from src.models import DFEDocumento
                from datetime import datetime
                
                # Preparar kwargs com campos EXISTENTES no seu schema
                kwargs = {
                    "empresa_id": empresa.id,
                    "nsu": identificador if tipo_id == "nsu" else "000000000000000",
                    "schema": schema,
                    "chave": classificacao.get("chave") or (identificador if tipo_id == "chave" else None),
                    "caminho_xml": str(xml_file),  # Caminho completo do arquivo
                }
                
                # Campos opcionais (só adicionar se existirem no modelo)
                # Verificar dinamicamente os campos do modelo
                colunas_modelo = {c.name for c in DFEDocumento.__table__.columns}
                
                if "emitente_cnpj" in colunas_modelo and classificacao.get("emitente_cnpj"):
                    kwargs["emitente_cnpj"] = classificacao["emitente_cnpj"]
                
                if "emitente_nome" in colunas_modelo and classificacao.get("emitente_nome"):
                    kwargs["emitente_nome"] = classificacao["emitente_nome"]
                
                if "valor_total" in colunas_modelo and classificacao.get("valor_total"):
                    try:
                        kwargs["valor_total"] = float(classificacao["valor_total"])
                    except:
                        pass
                
                if "data_emissao" in colunas_modelo and classificacao.get("data_emissao"):
                    kwargs["data_emissao"] = classificacao["data_emissao"]
                
                if "tipo_documento" in colunas_modelo:
                    kwargs["tipo_documento"] = classificacao.get("tipo_documento", "desconhecido")
                
                if "subtipo" in colunas_modelo:
                    kwargs["subtipo"] = classificacao.get("subtipo", "nao_classificado")
                
                if "descricao" in colunas_modelo:
                    kwargs["descricao"] = classificacao.get("descricao", f"XML manual {schema}")
                
                # Criar registro
                novo_doc = DFEDocumento(**kwargs)
                db.add(novo_doc)
                db.commit()
                db.refresh(novo_doc)
                
                sucesso += 1
                detalhes.append({
                    "arquivo": xml_file.name,
                    "nsu": novo_doc.nsu,
                    "chave": novo_doc.chave,
                    "status": "sucesso"
                })
                logger.info(f"✅ Importado: {xml_file.name} → NSU {novo_doc.nsu}")
            
            except Exception as e:
                erros += 1
                detalhes.append({
                    "arquivo": xml_file.name,
                    "erro": str(e),
                    "status": "erro"
                })
                logger.warning(f"❌ Erro ao processar {xml_file.name}: {e}")
                db.rollback()
        
        logger.info(f"✅ Processamento concluído: {sucesso} sucesso | {erros} erros")
        
        return {
            "total_analisados": total,
            "processados_com_sucesso": sucesso,
            "erros": erros,
            "detalhes": detalhes[:20],
            "docs_path": str(docs_path),
            "mensagem": f"Processados {sucesso} de {total} XMLs selecionados"
        }
    
    except Exception as e:
        logger.exception(f"💥 Erro no processamento em lote: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

def _classificar_documento_xml(xml_bytes: bytes, schema: str) -> dict:
    """
    Classifica documento XML reutilizando lógica do serviço DFe.
    Versão simplificada para importação manual.
    """
    from lxml import etree
    
    try:
        root = etree.fromstring(xml_bytes)
    except Exception as e:
        logger.warning(f"Erro ao parsear XML: {e}")
        return {"tipo_documento": "desconhecido", "subtipo": "erro_parse"}
    
    # Namespaces
    ns = {
        "nfe": "http://www.portalfiscal.inf.br/nfe",
        "cte": "http://www.portalfiscal.inf.br/cte"
    }
    
    # Tentar extrair campos básicos de NFe
    data = {}
    
    # Chave
    ch = root.find('.//nfe:chNFe', ns)
    if ch is not None and ch.text:
        data['chave'] = ch.text
    
    # Emitente
    emit_cnpj = root.find('.//nfe:emit/nfe:CNPJ', ns)
    emit_nome = root.find('.//nfe:emit/nfe:xNome', ns)
    if emit_cnpj is not None and emit_cnpj.text:
        data['emitente_cnpj'] = emit_cnpj.text
    if emit_nome is not None and emit_nome.text:
        data['emitente_nome'] = emit_nome.text
    
    # Valor total
    vnf = root.find('.//nfe:vNF', ns)
    if vnf is not None and vnf.text:
        data['valor_total'] = vnf.text
    
    # Data de emissão
    dh_emi = root.find('.//nfe:dhEmi', ns)
    if dh_emi is not None and dh_emi.text:
        try:
            from datetime import datetime
            data['data_emissao'] = datetime.fromisoformat(dh_emi.text.replace('Z', '+00:00'))
        except:
            pass
    
    # Determinar tipo pelo schema ou conteúdo
    if 'resNFe' in schema or 'resNFe' in str(root.tag):
        data['tipo_documento'] = 'nfe'
        data['subtipo'] = 'resumo'
        data['descricao'] = 'NFe Resumo'
    elif 'procNFe' in schema or 'procNFe' in str(root.tag) or '-nfe.xml' in schema:
        data['tipo_documento'] = 'nfe'
        data['subtipo'] = 'completa'
        data['descricao'] = 'NFe Completa'
    elif 'resEvento' in schema or 'resEvento' in str(root.tag):
        data['tipo_documento'] = 'evento'
        data['subtipo'] = 'resumo'
        data['descricao'] = 'Evento Resumo'
    elif 'procEvento' in schema or 'procEvento' in str(root.tag):
        data['tipo_documento'] = 'evento'
        data['subtipo'] = 'completo'
        data['descricao'] = 'Evento Processado'
    else:
        data['tipo_documento'] = 'outro'
        data['subtipo'] = 'desconhecido'
        data['descricao'] = f'Documento {schema}'
    
    return data