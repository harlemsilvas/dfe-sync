"""
Organizador de documentos classificados
Move arquivos para estrutura de pastas organizada
"""

import shutil
import sys
import os
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import calendar

# Adicionar o diretório raiz ao path para imports relativos
if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    root_dir = current_dir.parent.parent
    sys.path.insert(0, str(root_dir))

from src.core.logging_sistema import ProcessamentoLogger
from src.core.classificador_xml import DocumentoMetadata
from src.store.db import SessionLocal
from src.models import Empresa
from sqlalchemy import text

class OrganizadorDocumentos:
    """Organiza documentos em estrutura de pastas baseada nos metadados"""
    
    def __init__(self, pasta_destino: str = "/mnt/c/Projetos/dfe-sync/storage/empresas"):
        self.pasta_destino = Path(pasta_destino)
        self.logger = ProcessamentoLogger("ORGANIZADOR")
        self.cache_empresas = {}
        
        # Garantir que pasta destino existe
        self.pasta_destino.mkdir(parents=True, exist_ok=True)
        
        # Carregar empresas
        self._carregar_empresas()
    
    def _carregar_empresas(self):
        """Carrega empresas do banco para cache"""
        with SessionLocal() as db:
            result = db.execute(text(
                "SELECT cnpj, razao_social FROM empresas WHERE ativo = true"
            ))
            self.cache_empresas = {
                row.cnpj: row.razao_social for row in result
            }
    
    def determinar_cnpj_responsavel(self, metadata: DocumentoMetadata) -> Optional[str]:
        """
        Determina qual CNPJ será usado para organização baseado no tipo
        
        Regras:
        - NFE_ENTRADA: CNPJ do destinatário (empresa que recebeu)
        - NFE_SAIDA: CNPJ do emissor (empresa que emitiu) 
        - NFE_TRANSFERENCIA: CNPJ do emissor (empresa que enviou)
        - NFE_TERCEIROS: Não organiza por empresa específica
        - CTE: CNPJ do emissor (transportadora)
        """
        if metadata.tipo_documento == "NFE_ENTRADA":
            return metadata.cnpj_destinatario
        elif metadata.tipo_documento in ["NFE_SAIDA", "NFE_TRANSFERENCIA", "CTE"]:
            return metadata.cnpj_emissor
        elif metadata.tipo_documento == "NFE_TERCEIROS":
            # Para terceiros, usar pasta especial
            return "TERCEIROS"
        else:
            return None
    
    def gerar_caminho_organizacao(self, metadata: DocumentoMetadata) -> Optional[Path]:
        """
        Gera caminho de destino baseado nos metadados
        
        Estrutura: /storage/empresas/{cnpj}/{ano-mes}/{tipo}/{arquivo}
        Exemplo: /storage/empresas/51309435000153/2025-11/NFE_ENTRADA/35251051309435000153550010000041251.xml
        """
        cnpj_responsavel = self.determinar_cnpj_responsavel(metadata)
        if not cnpj_responsavel:
            return None
        
        # Data para pasta (ano-mes)
        if metadata.data_emissao:
            ano_mes = metadata.data_emissao.strftime("%Y-%m")
        else:
            # Se não tem data, usar mes atual
            hoje = datetime.now()
            ano_mes = hoje.strftime("%Y-%m")
        
        # Construir caminho
        if cnpj_responsavel == "TERCEIROS":
            caminho_base = self.pasta_destino / "TERCEIROS" / ano_mes / metadata.tipo_documento
        else:
            # Verificar se CNPJ é de empresa cadastrada
            razao_social = self.cache_empresas.get(cnpj_responsavel)
            if razao_social:
                # Usar razão social limpa como nome da pasta
                nome_empresa = self._limpar_nome_empresa(razao_social)
                pasta_empresa = f"{cnpj_responsavel}-{nome_empresa}"
            else:
                # CNPJ não cadastrado, usar só o número
                pasta_empresa = cnpj_responsavel
            
            caminho_base = self.pasta_destino / pasta_empresa / ano_mes / metadata.tipo_documento
        
        return caminho_base
    
    def _limpar_nome_empresa(self, razao_social: str) -> str:
        """Remove caracteres especiais do nome da empresa para usar em pasta"""
        import re
        # Remove caracteres especiais, mantém só letras, números e espaços
        limpo = re.sub(r'[^\w\s-]', '', razao_social.upper())
        # Remove espaços extras e substitui por underscore
        limpo = re.sub(r'\s+', '_', limpo.strip())
        # Limita tamanho
        return limpo[:50]
    
    def gerar_nome_arquivo(self, metadata: DocumentoMetadata, arquivo_original: str) -> str:
        """
        Gera nome padronizado para o arquivo
        
        Padrão: {chave_acesso}.xml ou {numero}-{serie}_{emissor[:8]}.xml
        """
        if metadata.chave_acesso:
            # Usar chave de acesso como nome
            return f"{metadata.chave_acesso}.xml"
        
        elif metadata.numero and metadata.serie and metadata.cnpj_emissor:
            # Usar numero-serie_emissor
            emissor_short = metadata.cnpj_emissor[:8]
            return f"{metadata.numero}-{metadata.serie}_{emissor_short}.xml"
        
        else:
            # Manter nome original se não conseguir gerar padrão
            return Path(arquivo_original).name
    
    def organizar_arquivo(self, arquivo_xml: Path, metadata: DocumentoMetadata, 
                         manter_original: bool = True) -> Optional[Path]:
        """
        Move/copia arquivo para pasta organizada
        
        Args:
            arquivo_xml: Caminho do arquivo XML
            metadata: Metadados do documento
            manter_original: Se True, copia; se False, move
            
        Returns:
            Path do arquivo no destino ou None se erro
        """
        try:
            # Verificar se arquivo existe
            if not arquivo_xml.exists():
                self.logger.error(f"Arquivo não encontrado: {arquivo_xml}")
                return None
            
            # Gerar caminho de destino
            pasta_destino = self.gerar_caminho_organizacao(metadata)
            if not pasta_destino:
                self.logger.warning(
                    f"Não foi possível determinar pasta de destino",
                    chave_nfe=metadata.chave_acesso,
                    tipo=metadata.tipo_documento
                )
                return None
            
            # Criar pasta se não existe
            pasta_destino.mkdir(parents=True, exist_ok=True)
            
            # Gerar nome do arquivo
            nome_arquivo = self.gerar_nome_arquivo(metadata, str(arquivo_xml))
            arquivo_destino = pasta_destino / nome_arquivo
            
            # Verificar se já existe (evitar duplicatas)
            if arquivo_destino.exists():
                # Adicionar sufixo numérico
                contador = 1
                nome_base = arquivo_destino.stem
                extensao = arquivo_destino.suffix
                
                while arquivo_destino.exists():
                    novo_nome = f"{nome_base}_{contador:02d}{extensao}"
                    arquivo_destino = pasta_destino / novo_nome
                    contador += 1
            
            # Copiar ou mover arquivo
            if manter_original:
                shutil.copy2(arquivo_xml, arquivo_destino)
                operacao = "COPIADO"
            else:
                shutil.move(str(arquivo_xml), str(arquivo_destino))
                operacao = "MOVIDO"
            
            # Log da operação
            self.logger.arquivo_processado(
                str(arquivo_destino),
                operacao,
                {
                    "origem": str(arquivo_xml),
                    "chave": metadata.chave_acesso,
                    "tipo": metadata.tipo_documento,
                    "cnpj_responsavel": self.determinar_cnpj_responsavel(metadata),
                    "pasta_relativa": str(arquivo_destino.relative_to(self.pasta_destino))
                },
                chave_nfe=metadata.chave_acesso
            )
            
            return arquivo_destino
            
        except Exception as e:
            self.logger.error(
                f"Erro ao organizar arquivo {arquivo_xml}: {e}",
                chave_nfe=metadata.chave_acesso
            )
            return None
    
    def gerar_relatorio_organizacao(self, pasta_origem: str = None) -> Dict:
        """
        Gera relatório da estrutura organizacional atual
        
        Returns:
            Dict com estatísticas da organização
        """
        stats = {
            "total_empresas": 0,
            "total_arquivos": 0,
            "por_empresa": {},
            "por_tipo": {},
            "por_mes": {},
            "sem_organizacao": []
        }
        
        try:
            # Varrer pasta de empresas
            if self.pasta_destino.exists():
                for pasta_empresa in self.pasta_destino.iterdir():
                    if pasta_empresa.is_dir():
                        stats["total_empresas"] += 1
                        stats["por_empresa"][pasta_empresa.name] = {"total": 0, "por_tipo": {}}
                        
                        # Varrer meses
                        for pasta_mes in pasta_empresa.iterdir():
                            if pasta_mes.is_dir() and len(pasta_mes.name) == 7:  # YYYY-MM
                                mes_nome = pasta_mes.name
                                if mes_nome not in stats["por_mes"]:
                                    stats["por_mes"][mes_nome] = 0
                                
                                # Varrer tipos
                                for pasta_tipo in pasta_mes.iterdir():
                                    if pasta_tipo.is_dir():
                                        tipo_nome = pasta_tipo.name
                                        
                                        # Contar arquivos
                                        arquivos = list(pasta_tipo.glob("*.xml"))
                                        qtd_arquivos = len(arquivos)
                                        
                                        stats["total_arquivos"] += qtd_arquivos
                                        stats["por_empresa"][pasta_empresa.name]["total"] += qtd_arquivos
                                        
                                        if tipo_nome not in stats["por_empresa"][pasta_empresa.name]["por_tipo"]:
                                            stats["por_empresa"][pasta_empresa.name]["por_tipo"][tipo_nome] = 0
                                        stats["por_empresa"][pasta_empresa.name]["por_tipo"][tipo_nome] += qtd_arquivos
                                        
                                        if tipo_nome not in stats["por_tipo"]:
                                            stats["por_tipo"][tipo_nome] = 0
                                        stats["por_tipo"][tipo_nome] += qtd_arquivos
                                        
                                        stats["por_mes"][mes_nome] += qtd_arquivos
            
            self.logger.info(
                f"Relatório de organização gerado: {stats['total_arquivos']} arquivos em {stats['total_empresas']} empresas"
            )
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório: {e}")
            return stats

if __name__ == "__main__":
    # Teste do organizador
    organizador = OrganizadorDocumentos()
    
    # Simular metadata de teste
    from src.core.classificador_xml import DocumentoMetadata
    
    metadata_teste = DocumentoMetadata(
        chave_acesso="35251051309435000153550010000041251728126118",
        modelo="55",
        numero="4125",
        serie="1", 
        cnpj_emissor="12345678000100",
        cnpj_destinatario="51309435000153",
        data_emissao=datetime.now(),
        tipo_documento="NFE_ENTRADA",
        motivo_classificacao="Teste"
    )
    
    print(f"🗂️ Teste do Organizador:")
    print(f"  CNPJ responsável: {organizador.determinar_cnpj_responsavel(metadata_teste)}")
    print(f"  Caminho: {organizador.gerar_caminho_organizacao(metadata_teste)}")
    print(f"  Nome arquivo: {organizador.gerar_nome_arquivo(metadata_teste, 'teste.xml')}")
    
    # Gerar relatório
    relatorio = organizador.gerar_relatorio_organizacao()
    print(f"  Total arquivos organizados: {relatorio['total_arquivos']}")
    print(f"  Total empresas: {relatorio['total_empresas']}")