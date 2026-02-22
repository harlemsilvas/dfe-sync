"""
Monitoramento automático de pastas para processamento contínuo
"""

import time
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Set
import hashlib
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Adicionar o diretório raiz ao path
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
sys.path.insert(0, str(root_dir))

from src.core.processador_completo import ProcessadorCompleto
from src.core.logging_sistema import ProcessamentoLogger

class MonitoradorPastas(FileSystemEventHandler):
    """
    Monitor de arquivos que detecta novos arquivos compactados e XMLs
    e os processa automaticamente
    """
    
    def __init__(self, pastas_monitoras: List[str], intervalo_processamento: int = 300):
        super().__init__()
        self.pastas_monitoras = [Path(p) for p in pastas_monitoras]
        self.intervalo_processamento = intervalo_processamento
        self.logger = ProcessamentoLogger("MONITOR")
        self.arquivos_pendentes = set()
        self.ultimo_processamento = {}
        self.cache_hashes = {}
        
        # Carregar cache de hashes se existir
        self.arquivo_cache = Path("storage/cache_monitor.json")
        self._carregar_cache()
    
    def _carregar_cache(self):
        """Carrega cache de arquivos já processados"""
        if self.arquivo_cache.exists():
            try:
                with open(self.arquivo_cache, 'r') as f:
                    data = json.load(f)
                    self.cache_hashes = data.get('hashes', {})
                    self.ultimo_processamento = data.get('ultimo_processamento', {})
                    
                self.logger.info(f"Cache carregado: {len(self.cache_hashes)} arquivos conhecidos")
            except Exception as e:
                self.logger.error(f"Erro ao carregar cache: {e}")
    
    def _salvar_cache(self):
        """Salva cache de arquivos processados"""
        try:
            self.arquivo_cache.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'hashes': self.cache_hashes,
                'ultimo_processamento': self.ultimo_processamento,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.arquivo_cache, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar cache: {e}")
    
    def _calcular_hash_arquivo(self, caminho: Path) -> str:
        """Calcula hash SHA256 de um arquivo"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(caminho, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"Erro ao calcular hash de {caminho}: {e}")
            return None
    
    def _arquivo_foi_modificado(self, caminho: Path) -> bool:
        """Verifica se arquivo foi modificado desde último processamento"""
        try:
            stat = caminho.stat()
            caminho_str = str(caminho)
            
            # Verificar se arquivo é muito recente (pode estar sendo copiado)
            if (datetime.now().timestamp() - stat.st_mtime) < 10:
                return False
            
            # Calcular hash atual
            hash_atual = self._calcular_hash_arquivo(caminho)
            if not hash_atual:
                return False
            
            # Verificar se hash mudou
            hash_anterior = self.cache_hashes.get(caminho_str)
            
            if hash_anterior != hash_atual:
                self.cache_hashes[caminho_str] = hash_atual
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar modificação de {caminho}: {e}")
            return False
    
    def _deve_processar_arquivo(self, caminho: Path) -> bool:
        """Determina se arquivo deve ser processado"""
        extensoes_suportadas = {'.zip', '.rar', '.7z', '.xml'}
        
        if caminho.suffix.lower() not in extensoes_suportadas:
            return False
        
        # Ignorar arquivos temporários ou ocultos
        if caminho.name.startswith('.') or caminho.name.startswith('~'):
            return False
        
        # Verificar se arquivo foi modificado
        return self._arquivo_foi_modificado(caminho)
    
    def on_created(self, event):
        """Evento: arquivo criado"""
        if not event.is_directory:
            self._processar_evento_arquivo(event.src_path, "CRIADO")
    
    def on_modified(self, event):
        """Evento: arquivo modificado"""
        if not event.is_directory:
            self._processar_evento_arquivo(event.src_path, "MODIFICADO")
    
    def on_moved(self, event):
        """Evento: arquivo movido"""
        if not event.is_directory:
            self._processar_evento_arquivo(event.dest_path, "MOVIDO")
    
    def _processar_evento_arquivo(self, caminho_str: str, tipo_evento: str):
        """Processa evento de arquivo"""
        try:
            caminho = Path(caminho_str)
            
            if self._deve_processar_arquivo(caminho):
                self.arquivos_pendentes.add(caminho)
                self.logger.info(f"Arquivo {tipo_evento}: {caminho.name}")
                
        except Exception as e:
            self.logger.error(f"Erro ao processar evento {tipo_evento} para {caminho_str}: {e}")
    
    def processar_arquivos_pendentes(self):
        """Processa arquivos que estão na fila"""
        if not self.arquivos_pendentes:
            return
        
        self.logger.info(f"Processando {len(self.arquivos_pendentes)} arquivos pendentes")
        
        # Agrupar arquivos por pasta
        arquivos_por_pasta = {}
        
        for arquivo in list(self.arquivos_pendentes):
            if not arquivo.exists():
                self.arquivos_pendentes.discard(arquivo)
                continue
            
            pasta_pai = arquivo.parent
            if pasta_pai not in arquivos_por_pasta:
                arquivos_por_pasta[pasta_pai] = []
            
            arquivos_por_pasta[pasta_pai].append(arquivo)
        
        # Processar cada pasta
        for pasta, arquivos in arquivos_por_pasta.items():
            try:
                self.logger.info(f"Processando {len(arquivos)} arquivos em {pasta}")
                
                # Usar processador completo na pasta
                processador = ProcessadorCompleto(str(pasta), manter_originais=True)
                
                # Se há arquivos compactados, extrair e processar
                tem_compactados = any(
                    arquivo.suffix.lower() in ['.zip', '.rar', '.7z'] 
                    for arquivo in arquivos
                )
                
                if tem_compactados:
                    stats = processador.processar_pasta_completa()
                else:
                    # Processar XMLs individuais
                    stats = {
                        "xmls_processados": 0,
                        "xmls_organizados": 0,
                        "xmls_com_erro": 0
                    }
                    
                    for arquivo in arquivos:
                        if arquivo.suffix.lower() == '.xml':
                            resultado = processador.processar_arquivo_especifico(str(arquivo))
                            if resultado.get("sucesso"):
                                stats["xmls_processados"] += 1
                                stats["xmls_organizados"] += 1
                            else:
                                stats["xmls_com_erro"] += 1
                
                # Registrar último processamento
                self.ultimo_processamento[str(pasta)] = datetime.now().isoformat()
                
                # Remover arquivos da fila
                for arquivo in arquivos:
                    self.arquivos_pendentes.discard(arquivo)
                
                self.logger.info(f"Pasta {pasta} processada: {stats}")
                
            except Exception as e:
                self.logger.error(f"Erro ao processar pasta {pasta}: {e}")
        
        # Salvar cache
        self._salvar_cache()
    
    def scan_inicial(self):
        """Faz scan inicial das pastas monitoradas"""
        self.logger.info("Iniciando scan inicial das pastas monitoradas")
        
        for pasta in self.pastas_monitoras:
            if not pasta.exists():
                self.logger.warning(f"Pasta não encontrada: {pasta}")
                continue
            
            self.logger.info(f"Escaneando: {pasta}")
            
            # Buscar arquivos relevantes
            extensoes = ['*.zip', '*.rar', '*.7z', '*.xml']
            
            for extensao in extensoes:
                for arquivo in pasta.rglob(extensao):
                    if self._deve_processar_arquivo(arquivo):
                        self.arquivos_pendentes.add(arquivo)
        
        self.logger.info(f"Scan inicial concluído: {len(self.arquivos_pendentes)} arquivos para processar")

class ServicoMonitoramento:
    """
    Serviço principal de monitoramento
    """
    
    def __init__(self, config_file: str = "config/monitor.json"):
        self.config_file = Path(config_file)
        self.config = self._carregar_config()
        self.observer = Observer()
        self.monitor = None
        self.logger = ProcessamentoLogger("SERVICO_MONITOR")
        self.rodando = False
    
    def _carregar_config(self) -> Dict:
        """Carrega configuração do arquivo JSON"""
        config_padrao = {
            "pastas_monitoradas": [
                "/mnt/c/Users/harle/Desktop/contabilidade/abc",
                "/mnt/c/Users/harle/Desktop/contabilidade/hrm"
            ],
            "intervalo_processamento": 300,  # 5 minutos
            "monitoramento_ativo": True,
            "scan_inicial": True
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Mesclar com configuração padrão
                    return {**config_padrao, **config}
            except Exception as e:
                self.logger.error(f"Erro ao carregar configuração: {e}")
        
        # Criar arquivo de configuração se não existir
        self._salvar_config(config_padrao)
        return config_padrao
    
    def _salvar_config(self, config: Dict):
        """Salva configuração no arquivo JSON"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Erro ao salvar configuração: {e}")
    
    def iniciar(self):
        """Inicia o serviço de monitoramento"""
        if self.rodando:
            self.logger.warning("Serviço já está rodando")
            return
        
        self.logger.info("Iniciando serviço de monitoramento")
        
        try:
            # Criar monitor
            self.monitor = MonitoradorPastas(
                self.config["pastas_monitoradas"],
                self.config["intervalo_processamento"]
            )
            
            # Scan inicial se configurado
            if self.config.get("scan_inicial", True):
                self.monitor.scan_inicial()
                
                # Processar arquivos encontrados no scan inicial
                if self.monitor.arquivos_pendentes:
                    self.monitor.processar_arquivos_pendentes()
            
            # Configurar observador de arquivos se monitoramento ativo
            if self.config.get("monitoramento_ativo", True):
                for pasta in self.config["pastas_monitoradas"]:
                    pasta_path = Path(pasta)
                    if pasta_path.exists():
                        self.observer.schedule(self.monitor, str(pasta_path), recursive=True)
                        self.logger.info(f"Monitorando: {pasta}")
                
                self.observer.start()
                self.logger.info("Observer de arquivos iniciado")
            
            self.rodando = True
            self.logger.info("Serviço de monitoramento iniciado com sucesso")
            
            # Loop principal
            try:
                while self.rodando:
                    time.sleep(self.config["intervalo_processamento"])
                    
                    if self.monitor and self.monitor.arquivos_pendentes:
                        self.monitor.processar_arquivos_pendentes()
                    
            except KeyboardInterrupt:
                self.logger.info("Parando serviço por solicitação do usuário")
                self.parar()
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar serviço: {e}")
            self.parar()
    
    def parar(self):
        """Para o serviço de monitoramento"""
        if not self.rodando:
            return
        
        self.logger.info("Parando serviço de monitoramento")
        
        self.rodando = False
        
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
        
        # Salvar cache final
        if self.monitor:
            self.monitor._salvar_cache()
        
        self.logger.info("Serviço de monitoramento parado")
    
    def status(self) -> Dict:
        """Retorna status do serviço"""
        return {
            "rodando": self.rodando,
            "pastas_monitoradas": self.config["pastas_monitoradas"],
            "intervalo": self.config["intervalo_processamento"],
            "arquivos_pendentes": len(self.monitor.arquivos_pendentes) if self.monitor else 0,
            "observer_ativo": self.observer.is_alive() if hasattr(self, 'observer') else False
        }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Serviço de monitoramento de documentos fiscais")
    parser.add_argument("--config", "-c", help="Arquivo de configuração", default="config/monitor.json")
    parser.add_argument("--scan-apenas", action="store_true", help="Fazer apenas scan inicial e sair")
    parser.add_argument("--status", action="store_true", help="Mostrar status e sair")
    
    args = parser.parse_args()
    
    servico = ServicoMonitoramento(args.config)
    
    if args.status:
        status = servico.status()
        print("📊 Status do Monitoramento:")
        print(f"  Rodando: {'✅' if status['rodando'] else '❌'}")
        print(f"  Pastas: {len(status['pastas_monitoradas'])}")
        print(f"  Pendentes: {status['arquivos_pendentes']}")
        print(f"  Observer: {'✅' if status['observer_ativo'] else '❌'}")
        
    elif args.scan_apenas:
        print("🔍 Executando scan inicial apenas...")
        servico.config["monitoramento_ativo"] = False
        servico.iniciar()
        print("✅ Scan concluído!")
        
    else:
        print("🚀 Iniciando serviço de monitoramento...")
        print("📁 Pastas monitoradas:")
        for pasta in servico.config["pastas_monitoradas"]:
            print(f"  - {pasta}")
        print("⏱️ Pressione Ctrl+C para parar")
        
        try:
            servico.iniciar()
        except KeyboardInterrupt:
            print("\n🛑 Parando...")
            servico.parar()