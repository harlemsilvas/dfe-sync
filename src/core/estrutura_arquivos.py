"""
Configuração da estrutura de diretórios para organização de documentos fiscais
"""

import os
from pathlib import Path
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# Configurações de caminhos
BASE_STORAGE_PATH = Path(__file__).parent.parent.parent / "storage"
EMPRESAS_PATH = BASE_STORAGE_PATH / "empresas"
TEMP_EXTRACTION_PATH = BASE_STORAGE_PATH / "temp"
PROCESSED_PATH = BASE_STORAGE_PATH / "processed"

# Tipos de documentos suportados
TIPOS_DOCUMENTOS = {
    "NFE_ENTRADA": "nfe-entrada",
    "NFE_SAIDA": "nfe-saida", 
    "NFE_TERCEIROS": "nfe-terceiros",
    "NFE_TRANSFERENCIA": "nfe-transferencia",
    "CTE": "cte",
    "NFSE": "nfse",
    "EVENTO": "eventos"
}

# Configurações de mapeamento Windows -> WSL
WINDOWS_PATHS = {
    "HRM": "C:\\Users\\harle\\Desktop\\contabilidade\\hrm",
    "ABC": "C:\\Users\\harle\\Desktop\\contabilidade\\abc"
}

# Mapear para WSL (se necessário)
WSL_PATHS = {
    "HRM": "/mnt/c/Users/harle/Desktop/contabilidade/hrm",
    "ABC": "/mnt/c/Users/harle/Desktop/contabilidade/abc"
}

def criar_estrutura_empresa(cnpj: str, ano_mes: str) -> Dict[str, Path]:
    """
    Cria a estrutura de diretórios para uma empresa em um mês específico
    
    Args:
        cnpj: CNPJ da empresa (apenas números)
        ano_mes: Formato YYYY-MM (ex: 2024-11)
    
    Returns:
        Dict com os caminhos criados para cada tipo de documento
    """
    empresa_path = EMPRESAS_PATH / cnpj / ano_mes
    
    paths = {}
    for codigo, pasta in TIPOS_DOCUMENTOS.items():
        path = empresa_path / pasta
        path.mkdir(parents=True, exist_ok=True)
        paths[codigo] = path
        
    logger.info(f"Estrutura criada para {cnpj}/{ano_mes}: {len(paths)} tipos")
    return paths

def obter_caminho_documento(cnpj: str, ano_mes: str, tipo: str, nome_arquivo: str) -> Path:
    """
    Retorna o caminho completo onde um documento deve ser armazenado
    
    Args:
        cnpj: CNPJ da empresa
        ano_mes: Formato YYYY-MM
        tipo: Tipo do documento (chave de TIPOS_DOCUMENTOS)
        nome_arquivo: Nome do arquivo XML
    """
    if tipo not in TIPOS_DOCUMENTOS:
        raise ValueError(f"Tipo de documento inválido: {tipo}")
        
    pasta = TIPOS_DOCUMENTOS[tipo]
    return EMPRESAS_PATH / cnpj / ano_mes / pasta / nome_arquivo

def listar_empresas() -> List[str]:
    """Lista todas as empresas (CNPJs) que têm dados armazenados"""
    if not EMPRESAS_PATH.exists():
        return []
        
    return [d.name for d in EMPRESAS_PATH.iterdir() if d.is_dir() and d.name.isdigit()]

def listar_periodos(cnpj: str) -> List[str]:
    """Lista todos os períodos (YYYY-MM) disponíveis para uma empresa"""
    empresa_path = EMPRESAS_PATH / cnpj
    if not empresa_path.exists():
        return []
        
    return sorted([d.name for d in empresa_path.iterdir() 
                  if d.is_dir() and len(d.name) == 7 and '-' in d.name])

def inicializar_diretorios():
    """Cria diretórios base necessários"""
    directories = [
        BASE_STORAGE_PATH,
        EMPRESAS_PATH, 
        TEMP_EXTRACTION_PATH,
        PROCESSED_PATH
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Diretório garantido: {directory}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    inicializar_diretorios()
    
    # Exemplo de uso
    cnpj_teste = "51309435000153"
    periodo_teste = "2024-11"
    
    print(f"Criando estrutura para {cnpj_teste}/{periodo_teste}")
    paths = criar_estrutura_empresa(cnpj_teste, periodo_teste)
    
    for tipo, caminho in paths.items():
        print(f"  {tipo}: {caminho}")