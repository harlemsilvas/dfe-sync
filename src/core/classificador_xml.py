"""
Classificador de documentos XML fiscais
Aplica regras de negócio para determinar tipo de documento e extrair metadados
"""

import xml.etree.ElementTree as ET
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal

# Adicionar o diretório raiz ao path para imports relativos
if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    root_dir = current_dir.parent.parent
    sys.path.insert(0, str(root_dir))

# Imports do projeto (ajuste conforme sua estrutura)
try:
    from src.core.logging_sistema import ProcessamentoLogger
    from src.store.db import SessionLocal
    from src.models import OperacaoPendente
    from sqlalchemy import text
except ImportError:
    # Fallback para testes sem banco
    ProcessamentoLogger = None
    SessionLocal = None
    OperacaoPendente = None
    text = None


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
        self.logger = ProcessamentoLogger("CLASSIFICADOR") if ProcessamentoLogger else None
        self.empresas_monitoradas = set()
        self.cfops_transferencia = set()
        self.cache_tipos = {}
        
        # Carregar dados do banco se disponível
        if SessionLocal:
            self._carregar_empresas_monitoradas()
            self._carregar_cfops_transferencia()
            self._carregar_tipos_documento()
    
    def _carregar_empresas_monitoradas(self):
        """Carrega lista de CNPJs monitorados do banco"""
        if not SessionLocal:
            return
        try:
            with SessionLocal() as db:
                result = db.execute(text(
                    "SELECT cnpj FROM empresas WHERE monitorada = true AND ativo = 1"
                ))
                self.empresas_monitoradas = {str(row.cnpj).strip() for row in result}
            if self.logger:
                self.logger.info(
                    f"Empresas monitoradas carregadas: {len(self.empresas_monitoradas)}",
                    dados={"cnpjs": list(self.empresas_monitoradas)}
                )
            print(f"[DEBUG] Lista de CNPJs monitorados: {self.empresas_monitoradas}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao carregar empresas monitoradas: {e}")
            self.empresas_monitoradas = set()
    
    def _carregar_cfops_transferencia(self):
        """Carrega CFOPs de transferência do banco"""
        if not SessionLocal:
            return
        try:
            with SessionLocal() as db:
                result = db.execute(text(
                    "SELECT codigo FROM cfops_transferencia WHERE ativo = true"
                ))
                self.cfops_transferencia = {row.codigo for row in result}
            if self.logger:
                self.logger.info(
                    f"CFOPs de transferência carregados: {len(self.cfops_transferencia)}",
                    dados={"cfops": list(self.cfops_transferencia)}
                )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao carregar CFOPs de transferência: {e}")
            self.cfops_transferencia = set()
    
    def _carregar_tipos_documento(self):
        """Carrega tipos de documento do banco"""
        if not SessionLocal:
            return
        try:
            with SessionLocal() as db:
                result = db.execute(text(
                    "SELECT id, codigo FROM tipo_documento WHERE ativo = true"
                ))
                self.cache_tipos = {row.codigo: row.id for row in result}
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao carregar tipos de documento: {e}")
            self.cache_tipos = {}
    
    def _get_text_element(self, parent: ET.Element, tag: str, ns: Dict[str, str]) -> Optional[str]:
        """Busca texto de elemento, tentando com namespace registrado e fallback"""
        try:
            if ns and 'ns' in ns:
                element = parent.find(f".//{{{ns['ns']}}}{tag}")
                if element is not None and element.text:
                    return element.text.strip()
            element = parent.find(f".//{tag}")
            if element is not None and element.text:
                return element.text.strip()
            return None
        except Exception:
            return None
    
    def _parse_data_emissao(self, data_str: str) -> Optional[datetime]:
        """Converte string de data/datetime para objeto datetime"""
        if not data_str:
            return None
        try:
            data_clean = data_str
            if len(data_clean) > 19 and ('+' in data_clean[-6:] or '-' in data_clean[-6:]):
                data_clean = data_clean[:-6]
            if 'T' in data_clean:
                return datetime.fromisoformat(data_clean)
            else:
                return datetime.strptime(data_clean, '%Y-%m-%d')
        except Exception:
            try:
                return datetime.strptime(data_str[:10], '%Y-%m-%d')
            except Exception:
                return None
    
    def detectar_tipo_xml(self, xml_content: str) -> Tuple[str, Dict[str, str]]:
        """Detecta o tipo de XML e retorna namespace"""
        ns = {}
        try:
            root = ET.fromstring(xml_content)
            if root.tag.startswith('{'):
                namespace = root.tag.split('}')[0][1:]
                ET.register_namespace('', namespace)
                ns['ns'] = namespace
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
        except ET.ParseError:
            return 'ERRO_XML', {}
        except Exception:
            return 'ERRO_XML', {}
    
    def extrair_metadados_nfe(self, root: ET.Element, ns: Dict[str, str]) -> DocumentoMetadata:
        """Extrai metadados específicos de NF-e"""
        metadata = DocumentoMetadata()
        try:
            inf_nfe = root.find('.//ns:infNFe', ns)
            if inf_nfe is None:
                inf_nfe = root.find('.//{http://www.portalfiscal.inf.br/nfe}infNFe')
            if inf_nfe is None:
                inf_nfe = root.find('.//infNFe')
            if inf_nfe is None:
                metadata.erro_parsing = "Elemento infNFe não encontrado"
                return metadata
            
            chave_attr = inf_nfe.get('Id', '')
            if chave_attr:
                metadata.chave_acesso = chave_attr.replace('NFe', '').strip()
            
            ide = inf_nfe.find('ns:ide', ns)
            if ide is None:
                ide = inf_nfe.find('.//{http://www.portalfiscal.inf.br/nfe}ide')
            if ide is None:
                ide = inf_nfe.find('ide')
            if ide is not None:
                metadata.modelo = self._get_text_element(ide, 'mod', ns)
                metadata.numero = self._get_text_element(ide, 'nNF', ns)
                metadata.serie = self._get_text_element(ide, 'serie', ns)
                metadata.natureza_operacao = self._get_text_element(ide, 'natOp', ns)
                dh_emi = self._get_text_element(ide, 'dhEmi', ns) or self._get_text_element(ide, 'dEmi', ns)
                if dh_emi:
                    metadata.data_emissao = self._parse_data_emissao(dh_emi)
            
            emit = inf_nfe.find('ns:emit', ns)
            if emit is None:
                emit = inf_nfe.find('.//{http://www.portalfiscal.inf.br/nfe}emit')
            if emit is None:
                emit = inf_nfe.find('emit')
            if emit is not None:
                metadata.cnpj_emissor = self._get_text_element(emit, 'CNPJ', ns)
            
            dest = inf_nfe.find('ns:dest', ns)
            if dest is None:
                dest = inf_nfe.find('.//{http://www.portalfiscal.inf.br/nfe}dest')
            if dest is None:
                dest = inf_nfe.find('dest')
            if dest is not None:
                metadata.cnpj_destinatario = self._get_text_element(dest, 'CNPJ', ns)

            print(f"[DEBUG] CNPJ emitente: '{metadata.cnpj_emissor}' | destinatário: '{metadata.cnpj_destinatario}'")

            total = inf_nfe.find('.//ns:total/ns:ICMSTot', ns)
            if total is None:
                total = inf_nfe.find('.//{http://www.portalfiscal.inf.br/nfe}total/{http://www.portalfiscal.inf.br/nfe}ICMSTot')
            if total is None:
                total = inf_nfe.find('.//total/ICMSTot')
            if total is not None:
                vnf = self._get_text_element(total, 'vNF', ns)
                if vnf:
                    vnf_clean = vnf.replace(',', '.') if ',' in vnf else vnf
                    try:
                        metadata.valor_total = Decimal(vnf_clean)
                    except Exception:
                        metadata.valor_total = None
            
            cfops = []
            dets = inf_nfe.findall('ns:det', ns) if inf_nfe is not None else []
            if not dets:
                dets = inf_nfe.findall('.//{http://www.portalfiscal.inf.br/nfe}det')
            if not dets:
                dets = inf_nfe.findall('det')
            for det in dets:
                prod = det.find('ns:prod', ns) or det.find('.//{http://www.portalfiscal.inf.br/nfe}prod') or det.find('prod')
                if prod is not None:
                    cfop = self._get_text_element(prod, 'CFOP', ns)
                    if cfop:
                        cfops.append(cfop)
                        break
            metadata.cfop = cfops[0] if cfops else None
        
        except Exception as e:
            metadata.erro_parsing = f"Erro ao extrair metadados NF-e: {str(e)}"
            if self.logger:
                self.logger.error(metadata.erro_parsing, chave_nfe=metadata.chave_acesso)
        return metadata
    
    def extrair_metadados_cte(self, root: ET.Element, ns: Dict[str, str]) -> DocumentoMetadata:
        """Extrai metadados específicos de CT-e"""
        metadata = DocumentoMetadata()
        try:
            inf_cte = root.find('.//ns:infCte', ns)
            if inf_cte is None:
                inf_cte = root.find('.//{http://www.portalfiscal.inf.br/cte}infCte')
            if inf_cte is None:
                inf_cte = root.find('.//infCte')
            if inf_cte is None:
                metadata.erro_parsing = "Elemento infCte não encontrado"
                return metadata
            
            chave_attr = inf_cte.get('Id', '')
            if chave_attr.startswith('CTe'):
                metadata.chave_acesso = chave_attr[3:]
            
            ide = inf_cte.find('.//ns:ide', ns)
            if ide is None:
                ide = inf_cte.find('.//{http://www.portalfiscal.inf.br/cte}ide')
            if ide is None:
                ide = inf_cte.find('.//ide')
            if ide is not None:
                metadata.modelo = self._get_text_element(ide, 'mod', ns)
                metadata.numero = self._get_text_element(ide, 'nCT', ns)
                metadata.serie = self._get_text_element(ide, 'serie', ns)
                metadata.natureza_operacao = self._get_text_element(ide, 'natOp', ns)
                dh_emi = self._get_text_element(ide, 'dhEmi', ns)
                if dh_emi:
                    metadata.data_emissao = self._parse_data_emissao(dh_emi)
            
            emit = inf_cte.find('.//ns:emit', ns)
            if emit is None:
                emit = inf_cte.find('.//{http://www.portalfiscal.inf.br/cte}emit')
            if emit is None:
                emit = inf_cte.find('.//emit')
            if emit is not None:
                metadata.cnpj_emissor = self._get_text_element(emit, 'CNPJ', ns)
            
            dest = inf_cte.find('.//ns:dest', ns)
            if dest is None:
                dest = inf_cte.find('.//{http://www.portalfiscal.inf.br/cte}dest')
            if dest is None:
                dest = inf_cte.find('.//dest')
            if dest is not None:
                metadata.cnpj_destinatario = self._get_text_element(dest, 'CNPJ', ns)
            
            v_prest = inf_cte.find('.//ns:vPrest', ns)
            if v_prest is None:
                v_prest = inf_cte.find('.//{http://www.portalfiscal.inf.br/cte}vPrest')
            if v_prest is None:
                v_prest = inf_cte.find('.//vPrest')
            if v_prest is not None:
                vtprest = self._get_text_element(v_prest, 'vTPrest', ns)
                if vtprest:
                    vtprest_clean = vtprest.replace(',', '.') if ',' in vtprest else vtprest
                    try:
                        metadata.valor_total = Decimal(vtprest_clean)
                    except Exception:
                        metadata.valor_total = None
        except Exception as e:
            metadata.erro_parsing = f"Erro ao extrair metadados CT-e: {str(e)}"
            if self.logger:
                self.logger.error(metadata.erro_parsing, chave_nfe=metadata.chave_acesso)
        return metadata
    
    def classificar_documento(self, metadata: DocumentoMetadata) -> str:
        """Aplica regras de negócio para classificar o documento"""
        # Lista de CFOPs de devolução (exemplo, pode ser expandida)
        cfops_devolucao = {"1410", "2410", "5410", "6410", "1202", "2202", "3202", "5202", "6202"}

        if metadata.modelo == '57':
            metadata.motivo_classificacao = "Documento modelo 57 (CT-e)"
            return "CTE"

        if not metadata.cnpj_emissor and not metadata.cnpj_destinatario:
            metadata.precisa_validacao = True
            metadata.motivo_classificacao = "CNPJs emissor e destinatário não identificados"
            return "NFE_TERCEIROS"

        if metadata.cfop:
            cfop = metadata.cfop.strip()
            if cfop in cfops_devolucao:
                metadata.motivo_classificacao = f"CFOP {cfop} identificado como devolução"
                return "NFE_DEVOLUCAO"
            if cfop in self.cfops_transferencia:
                metadata.motivo_classificacao = f"CFOP {cfop} identificado como transferência"
                return "NFE_TRANSFERENCIA"
            if cfop.startswith("1") or cfop.startswith("2"):
                metadata.motivo_classificacao = f"CFOP {cfop} identificado como entrada"
                return "NFE_ENTRADA"
            if cfop.startswith("5") or cfop.startswith("6"):
                metadata.motivo_classificacao = f"CFOP {cfop} identificado como saída"
                return "NFE_SAIDA"

        emissor_monitorado = metadata.cnpj_emissor in self.empresas_monitoradas
        destinatario_monitorado = metadata.cnpj_destinatario in self.empresas_monitoradas

        if emissor_monitorado and destinatario_monitorado:
            metadata.precisa_validacao = True
            metadata.motivo_classificacao = "Emissor e destinatário são empresas monitoradas"
            return "NFE_TRANSFERENCIA"
        elif emissor_monitorado:
            metadata.motivo_classificacao = f"Emissor {metadata.cnpj_emissor} é empresa monitorada"
            return "NFE_SAIDA"
        elif destinatario_monitorado:
            metadata.motivo_classificacao = f"Destinatário {metadata.cnpj_destinatario} é empresa monitorada"
            return "NFE_ENTRADA"
        else:
            metadata.motivo_classificacao = "Nenhum CNPJ é de empresa monitorada"
            return "NFE_TERCEIROS"
    
    def processar_xml(self, xml_path: Path, arquivo_origem: str = None) -> DocumentoMetadata:
        """Processa um arquivo XML e retorna metadados classificados"""
        if self.logger:
            self.logger.debug(f"Processando XML: {xml_path}")
        try:
            with open(xml_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            tipo_xml, ns = self.detectar_tipo_xml(xml_content)
            if tipo_xml == 'ERRO_XML':
                metadata = DocumentoMetadata()
                metadata.erro_parsing = "Arquivo XML mal formado"
                return metadata
            
            root = ET.fromstring(xml_content)
            if tipo_xml == 'NFE':
                metadata = self.extrair_metadados_nfe(root, ns)
            elif tipo_xml == 'CTE':
                metadata = self.extrair_metadados_cte(root, ns)
            else:
                metadata = DocumentoMetadata()
                metadata.modelo = tipo_xml
            
            print(f"[DEBUG] XML: {xml_path} | CNPJ emissor: '{metadata.cnpj_emissor}' | destinatário: '{metadata.cnpj_destinatario}'")
            
            if not metadata.erro_parsing:
                metadata.tipo_documento = self.classificar_documento(metadata)
            
            chave_nfe_log = metadata.chave_acesso or ""
            cnpj_empresa_log = metadata.cnpj_emissor if metadata.cnpj_emissor and metadata.cnpj_emissor in self.empresas_monitoradas else (metadata.cnpj_destinatario or "")
            
            if self.logger:
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
                    chave_nfe=chave_nfe_log,
                    cnpj_empresa=cnpj_empresa_log
                )
            
            if metadata.precisa_validacao and metadata.chave_acesso and OperacaoPendente and SessionLocal:
                self._registrar_operacao_pendente(metadata)
            
            return metadata
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao processar XML {xml_path}: {str(e)}")
            metadata = DocumentoMetadata()
            metadata.erro_parsing = str(e)
            return metadata
    
    def _registrar_operacao_pendente(self, metadata: DocumentoMetadata):
        """Registra operação que precisa validação manual"""
        if not SessionLocal or not OperacaoPendente:
            return
        try:
            with SessionLocal() as db:
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
                    if self.logger:
                        self.logger.operacao_pendente(
                            metadata.chave_acesso or "",
                            metadata.motivo_classificacao or "",
                            {
                                "tipo_sugerido": metadata.tipo_documento,
                                "cnpj_emissor": metadata.cnpj_emissor,
                                "cnpj_destinatario": metadata.cnpj_destinatario,
                                "cfop": metadata.cfop
                            }
                        )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao registrar operação pendente: {str(e)}")


# =============================================================================
# FUNÇÃO DASHBOARD (FORA DA CLASSE - função utilitária)
# =============================================================================

def imprimir_dashboard(stats: Dict):
    """
    Exibe um dashboard resumido das estatísticas de processamento.
    Usa rich se disponível, senão fallback para print.
    """
    try:
        from rich.console import Console
        from rich.table import Table
        console = Console()
        console.print("\n[bold green]📊 DASHBOARD DE PROCESSAMENTO[/bold green]\n")
        table = Table(show_header=False, box=None)
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="white")
        table.add_row("📁 XMLs Processados", str(stats.get('xmls_processados', 0)))
        table.add_row("✅ Classificados", str(stats.get('xmls_classificados', 0)))
        table.add_row("🗂️  Organizados", str(stats.get('xmls_organizados', 0)))
        table.add_row("❌ Com Erro", str(stats.get('xmls_com_erro', 0)))
        table.add_row("⏱️  Tempo", f"{stats.get('tempo_execucao', 0)}s")
        table.add_row("💰 Valor Total", f"R$ {stats.get('valores_totais', 0):,.2f}")
        console.print(table)
    except ImportError:
        print("\n" + "="*60)
        print("📊 RESUMO DO PROCESSAMENTO")
        print("="*60)
        print(f"📁 XMLs Processados: {stats.get('xmls_processados', 0)}")
        print(f"✅ Classificados: {stats.get('xmls_classificados', 0)}")
        print(f"🗂️  Organizados: {stats.get('xmls_organizados', 0)}")
        print(f"❌ Com Erro: {stats.get('xmls_com_erro', 0)}")
        print(f"⏱️  Tempo: {stats.get('tempo_execucao', 0)}s")
        print(f"💰 Valor Total: R$ {stats.get('valores_totais', 0):,.2f}")
        print("="*60)


# =============================================================================
# BLOCO DE TESTE
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("🧮 TESTE DO CLASSIFICADOR XML")
    print("=" * 80)
    
    classificador = ClassificadorXML()
    
    xml_teste = """<?xml version="1.0" encoding="UTF-8"?>
    <nfeProc versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
        <NFe xmlns="http://www.portalfiscal.inf.br/nfe">
            <infNFe Id="NFe35251042580092002977551600000125381568142699" versao="4.00">
                <ide>
                    <cUF>35</cUF>
                    <natOp>VENDA A PRAZO</natOp>
                    <mod>55</mod>
                    <serie>160</serie>
                    <nNF>12538</nNF>
                    <dhEmi>2025-10-13T00:00:00-03:00</dhEmi>
                    <tpNF>1</tpNF>
                </ide>
                <emit>
                    <CNPJ>42580092002977</CNPJ>
                    <xNome>CIA BRASILEIRA DIST AUTO S.A</xNome>
                </emit>
                <dest>
                    <CNPJ>51309435000153</CNPJ>
                    <xNome>ABC CENTER DISTRIBUIDORA LTDA</xNome>
                </dest>
                <det nItem="1">
                    <prod>
                        <cProd>152413</cProd>
                        <xProd>N-1813 PASTILHA FREIO MOTO - COB</xProd>
                        <CFOP>5405</CFOP>
                        <vProd>185.92</vProd>
                    </prod>
                </det>
                <total>
                    <ICMSTot>
                        <vProd>456.81</vProd>
                        <vNF>459.71</vNF>
                    </ICMSTot>
                </total>
            </infNFe>
        </NFe>
    </nfeProc>"""
    
    caminho_teste = Path('/tmp/teste_nfe_corrigido.xml')
    with open(caminho_teste, 'w', encoding='utf-8') as f:
        f.write(xml_teste)
    
    print(f"\n📁 Arquivo de teste criado: {caminho_teste}")
    print("-" * 80)
    
    resultado = classificador.processar_xml(caminho_teste)
    
    print("\n" + "=" * 80)
    print("🎯 RESULTADO DA EXTRAÇÃO:")
    print("=" * 80)
    print(f"  ✅ Chave de Acesso: {resultado.chave_acesso}")
    print(f"  ✅ Modelo: {resultado.modelo}")
    print(f"  ✅ Número: {resultado.numero}")
    print(f"  ✅ Série: {resultado.serie}")
    print(f"  ✅ CNPJ Emitente: {resultado.cnpj_emissor}")
    print(f"  ✅ CNPJ Destinatário: {resultado.cnpj_destinatario}")
    print(f"  ✅ Data Emissão: {resultado.data_emissao}")
    print(f"  ✅ Valor Total: R$ {resultado.valor_total}")
    print(f"  ✅ CFOP: {resultado.cfop}")
    print(f"  ✅ Natureza Operação: {resultado.natureza_operacao}")
    print(f"  ✅ Tipo Classificado: {resultado.tipo_documento}")
    print(f"  ✅ Precisa Validação: {resultado.precisa_validacao}")
    print(f"  ✅ Motivo: {resultado.motivo_classificacao}")
    if resultado.erro_parsing:
        print(f"  ❌ Erro Parsing: {resultado.erro_parsing}")
    print("=" * 80)
    
    try:
        caminho_teste.unlink()
        print(f"\n🗑️  Arquivo de teste removido")
    except:
        pass
    
    print("\n✅ Teste concluído!")