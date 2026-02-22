"""
Sistema de logging estruturado para processamento de arquivos fiscais
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models.log_processamento import LogProcessamento
from src.store.db import SessionLocal

class ProcessamentoLogger:
    """Logger especializado para o sistema de processamento de arquivos"""
    
    def __init__(self, modulo: str, processo: str = None):
        self.modulo = modulo
        self.processo = processo or f"{modulo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logger = logging.getLogger(f"dfe_sync.{modulo}")
        
    def _log_to_db(self, 
                   nivel: str, 
                   mensagem: str, 
                   dados: Dict[str, Any] = None,
                   arquivo_origem: str = None,
                   chave_nfe: str = None,
                   cnpj_empresa: str = None,
                   tag: str = None):
        """Grava log no banco de dados"""
        try:
            with SessionLocal() as db:
                log_entry = LogProcessamento(
                    nivel=nivel,
                    modulo=self.modulo,
                    processo=self.processo,
                    tag=tag,
                    mensagem=mensagem,
                    dados_json=json.dumps(dados) if dados else None,
                    arquivo_origem=arquivo_origem,
                    chave_nfe=chave_nfe,
                    cnpj_empresa=cnpj_empresa
                )
                db.add(log_entry)
                db.commit()
        except Exception as e:
            # Fallback para log padrão se BD falhar
            self.logger.error(f"Erro ao gravar log no BD: {e}")
    
    def debug(self, mensagem: str, **kwargs):
        """Log nivel DEBUG"""
        self.logger.debug(mensagem)
        self._log_to_db("DEBUG", mensagem, **kwargs)
    
    def info(self, mensagem: str, **kwargs):
        """Log nivel INFO"""
        self.logger.info(mensagem)
        self._log_to_db("INFO", mensagem, **kwargs)
    
    def warning(self, mensagem: str, **kwargs):
        """Log nivel WARNING"""
        self.logger.warning(mensagem)
        self._log_to_db("WARNING", mensagem, **kwargs)
    
    def error(self, mensagem: str, **kwargs):
        """Log nivel ERROR"""
        self.logger.error(mensagem)
        self._log_to_db("ERROR", mensagem, **kwargs)
    
    def arquivo_processado(self, 
                          arquivo: str, 
                          status: str, 
                          detalhes: Dict[str, Any] = None,
                          chave_nfe: str = None,
                          cnpj_empresa: str = None):
        """Log específico para processamento de arquivo"""
        mensagem = f"Arquivo {status}: {arquivo}"
        self.info(
            mensagem,
            dados=detalhes or {},
            arquivo_origem=arquivo,
            chave_nfe=chave_nfe,
            cnpj_empresa=cnpj_empresa,
            tag="ARQUIVO_PROCESSADO"
        )
    
    def duplicata_detectada(self, 
                           chave_nfe: str, 
                           arquivo_origem: str,
                           arquivo_existente: str):
        """Log para duplicata detectada"""
        self.warning(
            f"Duplicata detectada: chave {chave_nfe}",
            dados={
                "arquivo_origem": arquivo_origem,
                "arquivo_existente": arquivo_existente
            },
            arquivo_origem=arquivo_origem,
            chave_nfe=chave_nfe,
            tag="DUPLICATA"
        )
    
    def operacao_pendente(self, 
                         chave_nfe: str,
                         motivo: str,
                         dados_nfe: Dict[str, Any]):
        """Log para operação que precisa validação manual"""
        self.warning(
            f"Operação pendente: {motivo}",
            dados=dados_nfe,
            chave_nfe=chave_nfe,
            cnpj_empresa=dados_nfe.get('cnpj_emissor'),
            tag="OPERACAO_PENDENTE"
        )
    
    def estatisticas_lote(self, 
                         total_arquivos: int,
                         processados: int,
                         erros: int,
                         duplicatas: int,
                         pendentes: int,
                         tempo_execucao: float):
        """Log de estatísticas de um lote processado"""
        dados = {
            "total_arquivos": total_arquivos,
            "processados": processados,
            "erros": erros,
            "duplicatas": duplicatas,
            "pendentes": pendentes,
            "tempo_execucao_segundos": tempo_execucao,
            "taxa_sucesso": (processados / total_arquivos * 100) if total_arquivos > 0 else 0
        }
        
        self.info(
            f"Lote finalizado: {processados}/{total_arquivos} processados",
            dados=dados,
            tag="ESTATISTICAS_LOTE"
        )

def configurar_logging():
    """Configura o sistema de logging padrão - apenas console, BD via PostgreSQL Docker"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()  # Apenas console - BD via PostgreSQL Docker
        ]
    )

# Loggers pré-configurados para módulos específicos
extractor_logger = ProcessamentoLogger("EXTRATOR")
classifier_logger = ProcessamentoLogger("CLASSIFICADOR") 
organizer_logger = ProcessamentoLogger("ORGANIZADOR")
persistence_logger = ProcessamentoLogger("PERSISTENCIA")

if __name__ == "__main__":
    # Teste do sistema de logging
    configurar_logging()
    
    test_logger = ProcessamentoLogger("TEST")
    test_logger.info("Sistema de logging inicializado")
    test_logger.arquivo_processado(
        "/test/arquivo.xml", 
        "PROCESSADO",
        {"tipo": "NFE_ENTRADA", "valor": 1000.50},
        chave_nfe="35251051309435000153550010000041251728126118",
        cnpj_empresa="51309435000153"
    )
    print("✅ Teste de logging concluído!")