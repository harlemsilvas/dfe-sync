"""
Classificador de documentos XML fiscais
Aplica regras de negócio para determinar tipo de documento e extrair metadados
"""

import xml.etree.ElementTree as ET
import sys
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
import re
from decimal import Decimal

# Adicionar o diretório raiz ao path para imports relativos
if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    root_dir = current_dir.parent.parent
    sys.path.insert(0, str(root_dir))

from src.core.logging_sistema import ProcessamentoLogger
from src.store.db import SessionLocal
from src.models import TipoDocumento, Empresa, CfopTransferencia, OperacaoPendente
from sqlalchemy import text

@dataclass
class DocumentoMetadata:
    """Classe para armazenar metadados extraídos do XML"""
    chave_acesso: Optional[str] = None
    modelo: Optional[str] = None  # 55=NF-e, 57=CT-e, etc.
    numero: Optional[str] = None
    serie: Optional[str] = None
    cnpj_emissor: Optional[str] = None
    cnpj_destinatario: Optional[str] = None
    data_emissao: Optional[datetime] = None
    valor_total: Optional[Decimal] = None
    cfop: Optional[str] = None
    natureza_operacao: Optional[str] = None
    tipo_documento: Optional[str] = None
    motivo_classificacao: Optional[str] = None
    precisa_validacao: bool = False
    erro_parsing: Optional[str] = None

class ClassificadorXML:
    """Classificador de documentos XML com regras de negócio"""
    
    def __init__(self):
        self.logger = ProcessamentoLogger("CLASSIFICADOR")
        self.empresas_monitoradas = set()
        self.cfops_transferencia = set()
        self.cache_tipos = {}
        
        # Carregar dados do banco
        self._carregar_empresas_monitoradas()
        self._carregar_cfops_transferencia()
        self._carregar_tipos_documento()
    
    def _carregar_empresas_monitoradas(self):
        """Carrega lista de CNPJs monitorados do banco"""
        with SessionLocal() as db:
            result = db.execute(text(
                "SELECT cnpj FROM empresas WHERE monitorada = true AND ativo = 1"
            ))
            self.empresas_monitoradas = {row.cnpj for row in result}
            
        self.logger.info(
            f"Empresas monitoradas carregadas: {len(self.empresas_monitoradas)}",
            dados={"cnpjs": list(self.empresas_monitoradas)}
        )
    
    def _carregar_cfops_transferencia(self):
        """Carrega CFOPs de transferência do banco"""
        with SessionLocal() as db:
            result = db.execute(text(
                "SELECT codigo FROM cfops_transferencia WHERE ativo = true"
            ))
            self.cfops_transferencia = {row.codigo for row in result}
            
        self.logger.info(
            f"CFOPs de transferência carregados: {len(self.cfops_transferencia)}",
            dados={"cfops": list(self.cfops_transferencia)}
        )
    
    def _carregar_tipos_documento(self):
        """Carrega tipos de documento do banco"""
        with SessionLocal() as db:
            result = db.execute(text(
                "SELECT id, codigo FROM tipo_documento WHERE ativo = true"
            ))
            self.cache_tipos = {row.codigo: row.id for row in result}
    
    def extrair_metadados_nfe(self, root: ET.Element, ns: Dict[str, str]) -> DocumentoMetadata:
        """Extrai metadados específicos de NF-e"""
        metadata = DocumentoMetadata()
        
        try:
            # Encontrar elemento infNFe
            inf_nfe = root.find('.//ns:infNFe', ns) or root.find('.//infNFe')
            if inf_nfe is None:
                metadata.erro_parsing = "Elemento infNFe não encontrado"
                return metadata
            
            # Chave de acesso
            chave_attr = inf_nfe.get('Id', '')
            if chave_attr.startswith('NFe'):
                metadata.chave_acesso = chave_attr[3:]  # Remove 'NFe'
            
            # Dados da IDE
            ide = inf_nfe.find('.//ns:ide', ns) or inf_nfe.find('.//ide')
            if ide is not None:
                metadata.modelo = self._get_text_element(ide, 'mod', ns)
                metadata.numero = self._get_text_element(ide, 'nNF', ns)
                metadata.serie = self._get_text_element(ide, 'serie', ns)
                metadata.natureza_operacao = self._get_text_element(ide, 'natOp', ns)
                
                # Data de emissão
                dh_emi = self._get_text_element(ide, 'dhEmi', ns) or self._get_text_element(ide, 'dEmi', ns)
                if dh_emi:
                    metadata.data_emissao = self._parse_data_emissao(dh_emi)
            
            # Emissor
            emit = inf_nfe.find('.//ns:emit', ns) or inf_nfe.find('.//emit')
            if emit is not None:
                metadata.cnpj_emissor = self._get_text_element(emit, 'CNPJ', ns)
            
            # Destinatário  
            dest = inf_nfe.find('.//ns:dest', ns) or inf_nfe.find('.//dest')
            if dest is not None:
                metadata.cnpj_destinatario = self._get_text_element(dest, 'CNPJ', ns)
            
            # Total
            total = inf_nfe.find('.//ns:total/ns:ICMSTot', ns) or inf_nfe.find('.//total/ICMSTot')
            if total is not None:
                vnf = self._get_text_element(total, 'vNF', ns)
                if vnf:
                    metadata.valor_total = Decimal(vnf.replace(',', '.'))
            
            # CFOP (do primeiro item)
            det = inf_nfe.find('.//ns:det', ns) or inf_nfe.find('.//det')
            if det is not None:
                prod = det.find('.//ns:prod', ns) or det.find('.//prod')
                if prod is not None:
                    metadata.cfop = self._get_text_element(prod, 'CFOP', ns)
        
        except Exception as e:
            metadata.erro_parsing = f"Erro ao extrair metadados NF-e: {e}"
            self.logger.error(metadata.erro_parsing, chave_nfe=metadata.chave_acesso)
        
        return metadata
    
    def extrair_metadados_cte(self, root: ET.Element, ns: Dict[str, str]) -> DocumentoMetadata:
        """Extrai metadados específicos de CT-e"""
        metadata = DocumentoMetadata()
        
        try:
            # Encontrar elemento infCte
            inf_cte = root.find('.//ns:infCte', ns) or root.find('.//infCte')
            if inf_cte is None:
                metadata.erro_parsing = "Elemento infCte não encontrado"
                return metadata
            
            # Chave de acesso
            chave_attr = inf_cte.get('Id', '')
            if chave_attr.startswith('CTe'):
                metadata.chave_acesso = chave_attr[3:]
            
            # Dados da IDE
            ide = inf_cte.find('.//ns:ide', ns) or inf_cte.find('.//ide')
            if ide is not None:
                metadata.modelo = self._get_text_element(ide, 'mod', ns)
                metadata.numero = self._get_text_element(ide, 'nCT', ns)
                metadata.serie = self._get_text_element(ide, 'serie', ns)
                metadata.natureza_operacao = self._get_text_element(ide, 'natOp', ns)
                
                # Data de emissão
                dh_emi = self._get_text_element(ide, 'dhEmi', ns)
                if dh_emi:
                    metadata.data_emissao = self._parse_data_emissao(dh_emi)
            
            # Emissor
            emit = inf_cte.find('.//ns:emit', ns) or inf_cte.find('.//emit')
            if emit is not None:
                metadata.cnpj_emissor = self._get_text_element(emit, 'CNPJ', ns)
            
            # Destinatário/Tomador
            dest = inf_cte.find('.//ns:dest', ns) or inf_cte.find('.//dest')
            if dest is not None:
                metadata.cnpj_destinatario = self._get_text_element(dest, 'CNPJ', ns)
            
            # Valor total
            v_prest = inf_cte.find('.//ns:vPrest', ns) or inf_cte.find('.//vPrest')
            if v_prest is not None:
                vtprest = self._get_text_element(v_prest, 'vTPrest', ns)
                if vtprest:
                    metadata.valor_total = Decimal(vtprest.replace(',', '.'))
        
        except Exception as e:
            metadata.erro_parsing = f"Erro ao extrair metadados CT-e: {e}"
            self.logger.error(metadata.erro_parsing, chave_nfe=metadata.chave_acesso)
        
        return metadata
    
    def _get_text_element(self, parent: ET.Element, tag: str, ns: Dict[str, str]) -> Optional[str]:
        """Busca texto de um elemento, tentando com e sem namespace"""
        element = parent.find(f'.//ns:{tag}', ns) or parent.find(f'.//{tag}')
        return element.text if element is not None else None
    
    def _parse_data_emissao(self, data_str: str) -> Optional[datetime]:
        """Converte string de data/datetime para objeto datetime"""
        try:
            # Formato ISO: 2025-10-28T12:43:24-03:00 ou 2025-10-28
            if 'T' in data_str:
                # Remove timezone se presente
                data_clean = data_str.split('+')[0].split('-')[0:3]  # Pega só a parte da data/hora
                data_clean = '-'.join(data_clean).split('T')[0] + 'T' + data_str.split('T')[1].split('+')[0].split('-')[0]
                return datetime.fromisoformat(data_clean.replace('T', ' ').split('.')[0])
            else:
                return datetime.strptime(data_str, '%Y-%m-%d')
        except Exception:
            return None
    
    def detectar_tipo_xml(self, xml_content: str) -> Tuple[str, Dict[str, str]]:
        """Detecta o tipo de XML e retorna namespace"""
        ns = {}
        
        try:
            root = ET.fromstring(xml_content)
            
            # Detectar namespace
            if root.tag.startswith('{'):
                namespace = root.tag.split('}')[0][1:]
                ns['ns'] = namespace
            
            # Detectar tipo por elemento raiz
            root_tag = root.tag.split('}')[-1] if '}' in root.tag else root.tag
            
            if root_tag in ['nfeProc', 'NFe']:
                return 'NFE', ns
            elif root_tag in ['cteProc', 'CTe']:
                return 'CTE', ns
            elif root_tag in ['nfseProc', 'NFSe']:
                return 'NFSE', ns
            elif 'evento' in root_tag.lower():
                return 'EVENTO', ns
            else:
                return 'DESCONHECIDO', ns
                
        except ET.ParseError as e:
            return 'ERRO_XML', {}
    
    def classificar_documento(self, metadata: DocumentoMetadata) -> str:
        """
        Aplica regras de negócio para classificar o documento
        
        Regras:
        - NF-e Entrada: CNPJ destinatário = empresa monitorada
        - NF-e Saída: CNPJ emissor = empresa monitorada  
        - NF-e Terceiros: Nenhum CNPJ = empresa monitorada
        - NF-e Transferência: CFOP de transferência
        - CT-e: Sempre CT-e independente de direção
        """
        if not metadata.cnpj_emissor and not metadata.cnpj_destinatario:
            metadata.precisa_validacao = True
            metadata.motivo_classificacao = "CNPJs emissor e destinatário não identificados"
            return "NFE_TERCEIROS"
        
        # Verificar se é transferência primeiro
        if metadata.cfop and metadata.cfop in self.cfops_transferencia:
            metadata.motivo_classificacao = f"CFOP {metadata.cfop} identificado como transferência"
            return "NFE_TRANSFERENCIA"
        
        # CT-e sempre é CT-e
        if metadata.modelo == '57':
            metadata.motivo_classificacao = "Documento modelo 57 (CT-e)"
            return "CTE"
        
        # Regras para NF-e
        emissor_monitorado = metadata.cnpj_emissor in self.empresas_monitoradas
        destinatario_monitorado = metadata.cnpj_destinatario in self.empresas_monitoradas
        
        if emissor_monitorado and destinatario_monitorado:
            # Ambos monitorados - provável transferência entre filiais
            metadata.precisa_validacao = True
            metadata.motivo_classificacao = "Emissor e destinatário são empresas monitoradas"
            return "NFE_TRANSFERENCIA"
        
        elif emissor_monitorado:
            # Empresa emite = Saída
            metadata.motivo_classificacao = f"Emissor {metadata.cnpj_emissor} é empresa monitorada"
            return "NFE_SAIDA"
        
        elif destinatario_monitorado:
            # Empresa recebe = Entrada
            metadata.motivo_classificacao = f"Destinatário {metadata.cnpj_destinatario} é empresa monitorada"
            return "NFE_ENTRADA"
        
        else:
            # Nenhum é monitorado = Terceiros
            metadata.motivo_classificacao = "Nenhum CNPJ é de empresa monitorada"
            return "NFE_TERCEIROS"
    
    def processar_xml(self, xml_path: Path, arquivo_origem: str = None) -> DocumentoMetadata:
        """
        Processa um arquivo XML e retorna metadados classificados
        
        Args:
            xml_path: Caminho para o arquivo XML
            arquivo_origem: Arquivo ZIP/RAR de origem (opcional)
            
        Returns:
            DocumentoMetadata: Metadados extraídos e classificados
        """
        self.logger.debug(f"Processando XML: {xml_path}")
        
        try:
            # Ler conteúdo XML
            with open(xml_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            # Detectar tipo
            tipo_xml, ns = self.detectar_tipo_xml(xml_content)
            
            if tipo_xml == 'ERRO_XML':
                metadata = DocumentoMetadata()
                metadata.erro_parsing = "Arquivo XML mal formado"
                return metadata
            
            # Extrair metadados baseado no tipo
            root = ET.fromstring(xml_content)
            
            if tipo_xml == 'NFE':
                metadata = self.extrair_metadados_nfe(root, ns)
            elif tipo_xml == 'CTE':
                metadata = self.extrair_metadados_cte(root, ns)
            else:
                metadata = DocumentoMetadata()
                metadata.modelo = tipo_xml
            
            # Classificar documento se não houve erro
            if not metadata.erro_parsing:
                metadata.tipo_documento = self.classificar_documento(metadata)
            
            # Log do resultado
            self.logger.arquivo_processado(
                str(xml_path),
                "CLASSIFICADO" if not metadata.erro_parsing else "ERRO",
                {
                    "chave": metadata.chave_acesso,
                    "tipo": metadata.tipo_documento,
                    "modelo": metadata.modelo,
                    "cnpj_emissor": metadata.cnpj_emissor,
                    "cnpj_destinatario": metadata.cnpj_destinatario,
                    "cfop": metadata.cfop,
                    "precisa_validacao": metadata.precisa_validacao,
                    "motivo": metadata.motivo_classificacao,
                    "arquivo_origem": arquivo_origem
                },
                chave_nfe=metadata.chave_acesso,
                cnpj_empresa=metadata.cnpj_emissor if metadata.cnpj_emissor in self.empresas_monitoradas else metadata.cnpj_destinatario
            )
            
            # Registrar operação pendente se necessário
            if metadata.precisa_validacao and metadata.chave_acesso:
                self._registrar_operacao_pendente(metadata)
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Erro ao processar XML {xml_path}: {e}")
            metadata = DocumentoMetadata()
            metadata.erro_parsing = str(e)
            return metadata
    
    def _registrar_operacao_pendente(self, metadata: DocumentoMetadata):
        """Registra operação que precisa validação manual"""
        try:
            with SessionLocal() as db:
                # Verificar se já existe
                exists = db.execute(text(
                    "SELECT 1 FROM operacoes_pendentes WHERE chave_nfe = :chave"
                ), {"chave": metadata.chave_acesso}).fetchone()
                
                if not exists:
                    operacao = OperacaoPendente(
                        chave_nfe=metadata.chave_acesso,
                        cnpj_emissor=metadata.cnpj_emissor or '',
                        cnpj_destinatario=metadata.cnpj_destinatario or '',
                        cfop=metadata.cfop or '',
                        natureza_operacao=metadata.natureza_operacao or '',
                        tipo_sugerido=metadata.tipo_documento,
                        motivo_pendencia=metadata.motivo_classificacao
                    )
                    db.add(operacao)
                    db.commit()
                    
                    self.logger.operacao_pendente(
                        metadata.chave_acesso,
                        metadata.motivo_classificacao,
                        {
                            "tipo_sugerido": metadata.tipo_documento,
                            "cnpj_emissor": metadata.cnpj_emissor,
                            "cnpj_destinatario": metadata.cnpj_destinatario,
                            "cfop": metadata.cfop
                        }
                    )
        except Exception as e:
            self.logger.error(f"Erro ao registrar operação pendente: {e}")

if __name__ == "__main__":
    # Teste do classificador
    classificador = ClassificadorXML()
    
    # Criar XML de teste
    xml_teste = """<?xml version="1.0" encoding="UTF-8"?>
    <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
        <NFe>
            <infNFe Id="NFe35251051309435000153550010000041251728126118">
                <ide>
                    <mod>55</mod>
                    <nNF>12345</nNF>
                    <serie>1</serie>
                    <dhEmi>2025-11-14T10:30:00</dhEmi>
                    <natOp>Venda de mercadoria</natOp>
                </ide>
                <emit>
                    <CNPJ>12345678000100</CNPJ>
                </emit>
                <dest>
                    <CNPJ>51309435000153</CNPJ>
                </dest>
                <det>
                    <prod>
                        <CFOP>5102</CFOP>
                    </prod>
                </det>
                <total>
                    <ICMSTot>
                        <vNF>1000.00</vNF>
                    </ICMSTot>
                </total>
            </infNFe>
        </NFe>
    </nfeProc>"""
    
    # Salvar arquivo de teste
    with open('/tmp/teste_nfe.xml', 'w') as f:
        f.write(xml_teste)
    
    # Testar classificação
    resultado = classificador.processar_xml(Path('/tmp/teste_nfe.xml'))
    
    print(f"🎯 Teste do Classificador:")
    print(f"  Chave: {resultado.chave_acesso}")
    print(f"  Tipo: {resultado.tipo_documento}")
    print(f"  Emissor: {resultado.cnpj_emissor}")
    print(f"  Destinatário: {resultado.cnpj_destinatario}")
    print(f"  Motivo: {resultado.motivo_classificacao}")
    print(f"  Precisa validação: {resultado.precisa_validacao}")