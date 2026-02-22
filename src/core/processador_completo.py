"""
Processador principal que integra extração, classificação e organização
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import time

# Adicionar o diretório raiz ao path para imports relativos
if __name__ == "__main__":
    # Quando executado diretamente, adicionar pasta raiz ao PYTHONPATH
    current_dir = Path(__file__).resolve().parent
    root_dir = current_dir.parent.parent  # Volta duas pastas para chegar na raiz
    sys.path.insert(0, str(root_dir))

from src.core.extrator_arquivos import ExtratorArquivos
from src.core.classificador_xml import ClassificadorXML, DocumentoMetadata
from src.core.organizador_documentos import OrganizadorDocumentos
from src.core.logging_sistema import ProcessamentoLogger
from src.store.db import SessionLocal
from sqlalchemy import text

class ProcessadorCompleto:
    """
    Processador principal que executa todo o fluxo:
    1. Extrair arquivos ZIP/RAR/7Z
    2. Classificar XMLs
    3. Organizar em estrutura de pastas
    """
    
    def __init__(self, pasta_origem: str, manter_originais: bool = True):
        self.pasta_origem = Path(pasta_origem)
        self.manter_originais = manter_originais
        
        # Componentes
        self.extrator = ExtratorArquivos()
        self.classificador = ClassificadorXML()
        self.organizador = OrganizadorDocumentos()
        self.logger = ProcessamentoLogger("PROCESSADOR_PRINCIPAL")
    
    def processar_pasta_completa(self) -> Dict:
        """
        Processa toda a pasta de origem com fluxo completo
        
        Returns:
            Dict com estatísticas do processamento
        """
        inicio = time.time()
        stats = {
            "inicio": datetime.now().isoformat(),
            "pasta_origem": str(self.pasta_origem),
            "arquivos_compactados": 0,
            "arquivos_extraidos": 0,
            "xmls_processados": 0,
            "xmls_classificados": 0,
            "xmls_organizados": 0,
            "xmls_com_erro": 0,
            "operacoes_pendentes": 0,
            "tipos_encontrados": {},
            "empresas_envolvidas": set(),
            "tempo_execucao": 0,
            "erros": []
        }
        
        try:
            self.logger.info(f"Iniciando processamento completo de: {self.pasta_origem}")
            
            # Fase 1: Extração
            self.logger.info("=== FASE 1: EXTRAÇÃO ===")
            
            # Verificar se a pasta existe
            if not self.pasta_origem.exists():
                self.logger.error(f"Pasta não encontrada: {self.pasta_origem}")
                stats["erros"].append(f"Pasta não encontrada: {self.pasta_origem}")
                return stats
            
            # Processar diretórios usando o extrator
            pasta_extraidos = self.pasta_origem / "extraidos"
            pasta_extraidos.mkdir(parents=True, exist_ok=True)
            
            # Usar o extrator para processar a pasta
            total_extraidos = 0
            total_processados = 0
            
            for resultado_lote in self.extrator.processar_diretorios([str(self.pasta_origem)]):
                total_processados += len(resultado_lote.get("processados", []))
                total_extraidos += resultado_lote.get("total_extraidos", 0)
            
            stats["arquivos_compactados"] = total_processados
            stats["arquivos_extraidos"] = total_extraidos
            
            if stats["arquivos_extraidos"] == 0:
                self.logger.warning("Nenhum arquivo extraído. Verificando XMLs já existentes...")
                xmls_existentes = list(self.pasta_origem.rglob("*.xml"))
                if xmls_existentes:
                    self.logger.info(f"Encontrados {len(xmls_existentes)} XMLs existentes")
                    return self._processar_xmls_existentes(xmls_existentes, stats)
            
            # Fase 2: Classificação e Organização
            self.logger.info("=== FASE 2: CLASSIFICAÇÃO E ORGANIZAÇÃO ===")
            
            # Buscar XMLs extraídos no diretório temporário do extrator
            xmls_encontrados = []
            
            # Buscar XMLs no diretório temporário do extrator
            if self.extrator.temp_dir and self.extrator.temp_dir.exists():
                xmls_encontrados.extend(self.extrator.temp_dir.rglob("*.xml"))
            
            # Buscar XMLs na pasta de origem também (caso existam XMLs soltos)
            xmls_encontrados.extend(self.pasta_origem.rglob("*.xml"))
            
            # Remover duplicatas
            xmls_encontrados = list(set(xmls_encontrados))
            
            self.logger.info(f"Encontrados {len(xmls_encontrados)} XMLs para classificação")
            
            for xml_path in xmls_encontrados:
                try:
                    # Pular XMLs já organizados
                    if "storage/empresas" in str(xml_path):
                        continue
                    
                    # Classificar XML
                    metadata = self.classificador.processar_xml(xml_path)
                    stats["xmls_processados"] += 1
                    
                    if metadata.erro_parsing:
                        stats["xmls_com_erro"] += 1
                        stats["erros"].append(f"Erro em {xml_path.name}: {metadata.erro_parsing}")
                        continue
                    
                    # Atualizar estatísticas
                    stats["xmls_classificados"] += 1
                    
                    if metadata.tipo_documento:
                        if metadata.tipo_documento not in stats["tipos_encontrados"]:
                            stats["tipos_encontrados"][metadata.tipo_documento] = 0
                        stats["tipos_encontrados"][metadata.tipo_documento] += 1
                    
                    if metadata.cnpj_emissor:
                        stats["empresas_envolvidas"].add(metadata.cnpj_emissor)
                    if metadata.cnpj_destinatario:
                        stats["empresas_envolvidas"].add(metadata.cnpj_destinatario)
                    
                    if metadata.precisa_validacao:
                        stats["operacoes_pendentes"] += 1
                    
                    # Organizar arquivo
                    if metadata.tipo_documento:
                        arquivo_organizado = self.organizador.organizar_arquivo(
                            xml_path, metadata, self.manter_originais
                        )
                        if arquivo_organizado:
                            stats["xmls_organizados"] += 1
                    
                except Exception as e:
                    stats["xmls_com_erro"] += 1
                    stats["erros"].append(f"Erro ao processar {xml_path.name}: {e}")
                    self.logger.error(f"Erro ao processar {xml_path}: {e}")
            
            # Converter set para list para serialização
            stats["empresas_envolvidas"] = list(stats["empresas_envolvidas"])
            stats["tempo_execucao"] = round(time.time() - inicio, 2)
            
            # Log final
            self.logger.processamento_finalizado(
                stats["xmls_processados"],
                stats["xmls_classificados"], 
                stats["xmls_organizados"],
                stats
            )
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Erro no processamento completo: {e}")
            stats["erros"].append(f"Erro geral: {e}")
            stats["tempo_execucao"] = round(time.time() - inicio, 2)
            return stats
    
    def _processar_xmls_existentes(self, xmls: List[Path], stats: Dict) -> Dict:
        """Processa XMLs já existentes na pasta"""
        for xml_path in xmls:
            try:
                # Pular XMLs já organizados
                if "storage/empresas" in str(xml_path):
                    continue
                
                metadata = self.classificador.processar_xml(xml_path)
                stats["xmls_processados"] += 1
                
                if metadata.erro_parsing:
                    stats["xmls_com_erro"] += 1
                    continue
                
                stats["xmls_classificados"] += 1
                
                if metadata.tipo_documento:
                    arquivo_organizado = self.organizador.organizar_arquivo(
                        xml_path, metadata, self.manter_originais
                    )
                    if arquivo_organizado:
                        stats["xmls_organizados"] += 1
                        
            except Exception as e:
                stats["xmls_com_erro"] += 1
                stats["erros"].append(f"Erro em {xml_path.name}: {e}")
        
        return stats
    
    def processar_arquivo_especifico(self, arquivo_path: str) -> Dict:
        """
        Processa um arquivo específico (ZIP/RAR/XML)
        
        Args:
            arquivo_path: Caminho para o arquivo
            
        Returns:
            Dict com resultado do processamento
        """
        arquivo = Path(arquivo_path)
        
        if not arquivo.exists():
            return {"erro": f"Arquivo não encontrado: {arquivo}"}
        
        resultado = {
            "arquivo": str(arquivo),
            "tipo": "DESCONHECIDO",
            "sucesso": False,
            "detalhes": {}
        }
        
        try:
            if arquivo.suffix.lower() in ['.zip', '.rar', '.7z']:
                # Arquivo compactado - extrair primeiro
                resultado["tipo"] = "COMPACTADO"
                sucesso, xmls_extraidos = self.extrator.extrair_arquivo_unico(arquivo)
                
                if sucesso:
                    resultado["detalhes"]["xmls_extraidos"] = len(xmls_extraidos)
                    
                    # Processar XMLs extraídos
                    for xml_path in xmls_extraidos:
                        metadata = self.classificador.processar_xml(xml_path)
                        if not metadata.erro_parsing and metadata.tipo_documento:
                            self.organizador.organizar_arquivo(
                                xml_path, metadata, self.manter_originais
                            )
                    
                    resultado["sucesso"] = True
                else:
                    resultado["detalhes"]["erro"] = "Falha na extração"
            
            elif arquivo.suffix.lower() == '.xml':
                # XML direto
                resultado["tipo"] = "XML"
                metadata = self.classificador.processar_xml(arquivo)
                
                if metadata.erro_parsing:
                    resultado["detalhes"]["erro"] = metadata.erro_parsing
                else:
                    resultado["detalhes"]["chave"] = metadata.chave_acesso
                    resultado["detalhes"]["tipo_documento"] = metadata.tipo_documento
                    
                    if metadata.tipo_documento:
                        arquivo_organizado = self.organizador.organizar_arquivo(
                            arquivo, metadata, self.manter_originais
                        )
                        resultado["detalhes"]["organizado_em"] = str(arquivo_organizado) if arquivo_organizado else None
                    
                    resultado["sucesso"] = True
            
            return resultado
            
        except Exception as e:
            resultado["detalhes"]["erro"] = str(e)
            self.logger.error(f"Erro ao processar arquivo {arquivo}: {e}")
            return resultado
    
    def gerar_relatorio_completo(self) -> Dict:
        """Gera relatório completo do sistema"""
        relatorio = {
            "timestamp": datetime.now().isoformat(),
            "organizacao": self.organizador.gerar_relatorio_organizacao(),
            "configuracao": {},
            "operacoes_pendentes": []
        }
        
        try:
            with SessionLocal() as db:
                # Configuração do sistema
                empresas = db.execute(text(
                    "SELECT COUNT(*) as total, COUNT(CASE WHEN monitorada THEN 1 END) as monitoradas FROM empresas WHERE ativo = true"
                )).fetchone()
                
                tipos_doc = db.execute(text("SELECT COUNT(*) FROM tipo_documento WHERE ativo = true")).fetchone()
                cfops = db.execute(text("SELECT COUNT(*) FROM cfops_transferencia WHERE ativo = true")).fetchone()
                
                relatorio["configuracao"] = {
                    "empresas_total": empresas.total,
                    "empresas_monitoradas": empresas.monitoradas,
                    "tipos_documento": tipos_doc[0],
                    "cfops_transferencia": cfops[0]
                }
                
                # Operações pendentes
                pendentes = db.execute(text("""
                    SELECT chave_nfe, tipo_sugerido, motivo_pendencia, created_at
                    FROM operacoes_pendentes 
                    WHERE resolvido = false
                    ORDER BY created_at DESC
                    LIMIT 50
                """)).fetchall()
                
                relatorio["operacoes_pendentes"] = [
                    {
                        "chave": p.chave_nfe,
                        "tipo_sugerido": p.tipo_sugerido,
                        "motivo": p.motivo_pendencia,
                        "data": p.created_at.isoformat()
                    } for p in pendentes
                ]
        
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório completo: {e}")
            relatorio["erro"] = str(e)
        
        return relatorio

if __name__ == "__main__":
    # Teste do processador completo
    import sys
    
    if len(sys.argv) > 1:
        pasta = sys.argv[1]
    else:
        pasta = "/mnt/c/Projetos/dfe-sync/docs"
    
    print(f"🚀 Testando Processador Completo")
    print(f"📁 Pasta: {pasta}")
    
    processador = ProcessadorCompleto(pasta, manter_originais=True)
    
    # Testar processamento
    stats = processador.processar_pasta_completa()
    
    print(f"\n📊 Resultados:")
    print(f"  ⚡ Tempo: {stats['tempo_execucao']}s")
    print(f"  📦 Compactados: {stats['arquivos_compactados']}")
    print(f"  📄 XMLs processados: {stats['xmls_processados']}")
    print(f"  ✅ Classificados: {stats['xmls_classificados']}")
    print(f"  🗂️ Organizados: {stats['xmls_organizados']}")
    print(f"  ⚠️ Com erro: {stats['xmls_com_erro']}")
    print(f"  ⏳ Pendentes: {stats['operacoes_pendentes']}")
    print(f"  🏢 Empresas envolvidas: {len(stats['empresas_envolvidas'])}")
    
    if stats['tipos_encontrados']:
        print(f"\n📋 Tipos encontrados:")
        for tipo, qtd in stats['tipos_encontrados'].items():
            print(f"    {tipo}: {qtd}")
    
    if stats['erros']:
        print(f"\n❌ Erros ({len(stats['erros'])}):")
        for erro in stats['erros'][:5]:  # Mostrar só os 5 primeiros
            print(f"    {erro}")
    
    # Gerar relatório completo
    print(f"\n📈 Gerando relatório completo...")
    relatorio = processador.gerar_relatorio_completo()
    
    print(f"  Total arquivos organizados: {relatorio['organizacao']['total_arquivos']}")
    print(f"  Empresas monitoradas: {relatorio['configuracao'].get('empresas_monitoradas', 'N/A')}")
    print(f"  Operações pendentes: {len(relatorio['operacoes_pendentes'])}")