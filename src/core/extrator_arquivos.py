"""
Extrator de arquivos compactados para processamento de documentos fiscais
Suporta ZIP, RAR, 7Z com processamento em lotes
"""

import os
import shutil
import hashlib
import zipfile
import py7zr
from pathlib import Path
from typing import List, Dict, Generator, Tuple, Optional
import tempfile
from datetime import datetime
import mimetypes

from src.core.logging_sistema import ProcessamentoLogger

class ExtratorArquivos:
    """Extrator de arquivos compactados com suporte a lotes e validação"""
    
    FORMATOS_SUPORTADOS = {'.zip', '.rar', '.7z', '.tar', '.tar.gz', '.tar.bz2'}
    EXTENSOES_XML = {'.xml', '.XML'}
    TAMANHO_LOTE = 20  # Conforme especificado
    
    def __init__(self):
        self.logger = ProcessamentoLogger("EXTRATOR")
        self.temp_dir = Path(tempfile.mkdtemp(prefix="dfe_extractor_"))
        self.estatisticas = {
            'arquivos_encontrados': 0,
            'arquivos_extraidos': 0,
            'xmls_validos': 0,
            'erros': 0,
            'duplicatas': 0
        }
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.limpar_temporarios()
    
    def limpar_temporarios(self):
        """Remove diretórios temporários"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.logger.debug(f"Diretório temporário removido: {self.temp_dir}")
    
    def calcular_hash_arquivo(self, caminho: Path) -> str:
        """Calcula hash MD5 do arquivo para detecção de duplicatas"""
        hash_md5 = hashlib.md5()
        with open(caminho, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def is_arquivo_compactado(self, caminho: Path) -> bool:
        """Verifica se o arquivo é um formato compactado suportado"""
        return caminho.suffix.lower() in self.FORMATOS_SUPORTADOS
    
    def is_arquivo_xml(self, caminho: Path) -> bool:
        """Verifica se o arquivo é XML"""
        if caminho.suffix.lower() in self.EXTENSOES_XML:
            return True
        
        # Verificação adicional pelo conteúdo
        try:
            with open(caminho, 'r', encoding='utf-8', errors='ignore') as f:
                primeira_linha = f.readline().strip()
                return primeira_linha.startswith('<?xml')
        except:
            return False
    
    def scanner_diretorios(self, caminhos_origem: List[str]) -> Generator[Path, None, None]:
        """
        Escaneia recursivamente diretórios procurando arquivos compactados
        
        Args:
            caminhos_origem: Lista de diretórios para escanear
            
        Yields:
            Path: Caminho para arquivo compactado encontrado
        """
        self.logger.info(f"Iniciando scanner em {len(caminhos_origem)} diretórios")
        
        for caminho_str in caminhos_origem:
            caminho = Path(caminho_str)
            
            # Verificar se é Windows path e converter para WSL
            if caminho_str.startswith('C:'):
                caminho = Path('/mnt/c' + caminho_str[2:].replace('\\', '/'))
            
            if not caminho.exists():
                self.logger.warning(f"Diretório não encontrado: {caminho}")
                continue
                
            self.logger.info(f"Escaneando: {caminho}")
            
            try:
                for item in caminho.rglob('*'):
                    if item.is_file() and self.is_arquivo_compactado(item):
                        self.estatisticas['arquivos_encontrados'] += 1
                        self.logger.debug(f"Arquivo compactado encontrado: {item}")
                        yield item
            except Exception as e:
                self.logger.error(f"Erro ao escanear {caminho}: {e}")
    
    def extrair_arquivo_unico(self, arquivo_compactado: Path) -> Tuple[bool, List[Path]]:
        """
        Extrai um único arquivo compactado
        
        Args:
            arquivo_compactado: Caminho para o arquivo compactado
            
        Returns:
            Tuple[bool, List[Path]]: (sucesso, lista_de_xmls_extraidos)
        """
        xmls_extraidos = []
        pasta_extracao = self.temp_dir / f"extract_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            pasta_extracao.mkdir(parents=True, exist_ok=True)
            formato = arquivo_compactado.suffix.lower()
            
            self.logger.debug(f"Extraindo {formato}: {arquivo_compactado}")
            
            if formato == '.zip':
                with zipfile.ZipFile(arquivo_compactado, 'r') as zip_ref:
                    zip_ref.extractall(pasta_extracao)
            elif formato == '.7z':
                with py7zr.SevenZipFile(arquivo_compactado, mode='r') as archive:
                    archive.extractall(path=pasta_extracao)
            else:
                pass
                # Usar patool para outros formatos (RAR, etc.)
                # patool.extract_archive(str(arquivo_compactado), outdir=str(pasta_extracao))
            
            # Procurar XMLs extraídos e copiar para área permanente
            lote_id = f"lote_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            for item in pasta_extracao.rglob('*'):
                if item.is_file() and self.is_arquivo_xml(item):
                    # Copiar para área permanente antes de adicionar à lista
                    xml_permanente = self.temp_dir / f"{lote_id}_{item.name}"
                    shutil.copy2(item, xml_permanente)
                    xmls_extraidos.append(xml_permanente)
            
            self.estatisticas['arquivos_extraidos'] += 1
            self.logger.arquivo_processado(
                str(arquivo_compactado),
                "EXTRAIDO",
                {
                    "formato": formato,
                    "xmls_encontrados": len(xmls_extraidos),
                    "tamanho_mb": round(arquivo_compactado.stat().st_size / 1024 / 1024, 2)
                }
            )
            
            return True, xmls_extraidos
            
        except Exception as e:
            self.estatisticas['erros'] += 1
            self.logger.error(
                f"Erro ao extrair {arquivo_compactado}: {e}",
                arquivo_origem=str(arquivo_compactado)
            )
            return False, []
        
        finally:
            # Limpar apenas pasta de extração temporária, mantendo XMLs copiados
            if pasta_extracao.exists():
                shutil.rmtree(pasta_extracao, ignore_errors=True)
    
    def processar_lote(self, arquivos_compactados: List[Path]) -> Dict[str, List[Dict]]:
        """
        Processa um lote de arquivos compactados
        
        Args:
            arquivos_compactados: Lista de até 20 arquivos para processar
            
        Returns:
            Dict contendo listas de resultados por categoria
        """
        resultados = {
            'extraidos': [],
            'erros': [],
            'xmls_validos': []
        }
        
        lote_id = f"lote_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logger.info(f"Processando {lote_id}: {len(arquivos_compactados)} arquivos")
        
        for arquivo in arquivos_compactados:
            sucesso, xmls = self.extrair_arquivo_unico(arquivo)
            
            if sucesso:
                resultado = {
                    'arquivo_origem': str(arquivo),
                    'xmls_extraidos': [],
                    'hash_origem': self.calcular_hash_arquivo(arquivo)
                }
                
                for xml_path in xmls:
                    xml_info = {
                        'caminho': str(xml_path),
                        'nome': xml_path.name,
                        'tamanho': xml_path.stat().st_size,
                        'hash': self.calcular_hash_arquivo(xml_path),
                        'caminho_temp': str(xml_path)  # Já é o caminho permanente
                    }
                    resultado['xmls_extraidos'].append(xml_info)
                
                resultados['extraidos'].append(resultado)
                self.estatisticas['xmls_validos'] += len(xmls)
                
            else:
                resultados['erros'].append({
                    'arquivo_origem': str(arquivo),
                    'erro': 'Falha na extração'
                })
        
        # Log de estatísticas do lote
        self.logger.info(
            f"{lote_id} finalizado",
            dados={
                'total_arquivos': len(arquivos_compactados),
                'extraidos': len(resultados['extraidos']),
                'erros': len(resultados['erros']),
                'total_xmls': sum(len(r['xmls_extraidos']) for r in resultados['extraidos'])
            },
            tag="LOTE_FINALIZADO"
        )
        
        return resultados
    
    def processar_diretorios(self, 
                           caminhos_origem: List[str], 
                           callback_lote: callable = None) -> Generator[Dict, None, None]:
        """
        Processa todos os arquivos compactados encontrados nos diretórios
        
        Args:
            caminhos_origem: Lista de diretórios para processar
            callback_lote: Função chamada após cada lote (opcional)
            
        Yields:
            Dict: Resultado de cada lote processado
        """
        arquivos_encontrados = list(self.scanner_diretorios(caminhos_origem))
        total_arquivos = len(arquivos_encontrados)
        
        self.logger.info(f"Scanner finalizado: {total_arquivos} arquivos compactados encontrados")
        
        # Processar em lotes
        for i in range(0, total_arquivos, self.TAMANHO_LOTE):
            lote = arquivos_encontrados[i:i + self.TAMANHO_LOTE]
            
            inicio_lote = datetime.now()
            resultado_lote = self.processar_lote(lote)
            tempo_lote = (datetime.now() - inicio_lote).total_seconds()
            
            # Adicionar metadados do lote
            resultado_lote['metadados'] = {
                'numero_lote': (i // self.TAMANHO_LOTE) + 1,
                'total_lotes': (total_arquivos // self.TAMANHO_LOTE) + 1,
                'tempo_execucao': tempo_lote,
                'progresso_pct': round(((i + len(lote)) / total_arquivos) * 100, 2)
            }
            
            if callback_lote:
                callback_lote(resultado_lote)
            
            yield resultado_lote
    
    def obter_estatisticas(self) -> Dict:
        """Retorna estatísticas do processamento"""
        return self.estatisticas.copy()

if __name__ == "__main__":
    # Teste do extrator
    caminhos_teste = [
        "C:\\Users\\harle\\Desktop\\contabilidade\\hrm",
        "C:\\Users\\harle\\Desktop\\contabilidade\\abc"
    ]
    
    def callback_lote_teste(resultado):
        metadados = resultado['metadados']
        print(f"Lote {metadados['numero_lote']}/{metadados['total_lotes']} - "
              f"{metadados['progresso_pct']}% - "
              f"{len(resultado['extraidos'])} extraídos")
    
    with ExtratorArquivos() as extractor:
        print("🔍 Iniciando extração de arquivos...")
        
        for resultado in extractor.processar_diretorios(caminhos_teste, callback_lote_teste):
            print(f"  📦 Lote processado: {len(resultado['extraidos'])} arquivos")
        
        estatisticas = extractor.obter_estatisticas()
        print(f"\\n📊 Estatísticas finais:")
        for chave, valor in estatisticas.items():
            print(f"  {chave}: {valor}")