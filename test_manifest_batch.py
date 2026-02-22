#!/usr/bin/env python3
"""
Script para testar a manifestação de NF-es em lote a partir de arquivos XML.
"""
import os
import sys
import requests
from lxml import etree
import json

# Adicionar src ao path para importar módulos locais
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# --- Configurações ---
XML_DIR = "storage/nfe_para_manifestar"
API_URL = "http://localhost:8001/api/dfe/manifestar"
EMPRESA_ID = 1
TP_EVENTO = "210210"  # Ciência da Operação
# --- Fim Configurações ---

def get_chNFe_from_xml(file_path: str) -> str | None:
    """Extrai a tag chNFe de um arquivo XML de NF-e."""
    try:
        # Usar um parser que remove tags em branco para evitar problemas
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(file_path, parser)
        
        # Namespace comum para NF-e
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # Tenta encontrar a chave no formato procNFe/NFe/infNFe/@Id
        # Remove o prefixo 'NFe'
        chave_elem = tree.find('.//nfe:infNFe', namespaces=ns)
        if chave_elem is not None:
            return chave_elem.get('Id')[3:]

        # Tenta encontrar a chave no formato nfeProc/NFe/infNFe/@Id
        chave_elem = tree.find('.//nfe:infNFe', namespaces=ns)
        if chave_elem is not None:
             return chave_elem.get('Id')[3:]

        # Fallback para encontrar a tag chNFe diretamente
        chave_elem = tree.find('.//nfe:chNFe', namespaces=ns)
        if chave_elem is not None:
            return chave_elem.text

        return None
    except Exception as e:
        print(f"    [ERRO] Falha ao processar {os.path.basename(file_path)}: {e}")
        return None

def main():
    """Função principal do script."""
    print("=" * 80)
    print("INICIANDO TESTE DE MANIFESTAÇÃO EM LOTE")
    print(f"Pasta de XMLs: {XML_DIR}")
    print("=" * 80)

    if not os.path.isdir(XML_DIR):
        print(f"❌ ERRO: O diretório '{XML_DIR}' não foi encontrado.")
        print("Por favor, crie a pasta e adicione os arquivos XML de NF-e.")
        return

    xml_files = [f for f in os.listdir(XML_DIR) if f.lower().endswith('.xml')]

    if not xml_files:
        print(f"🟡 AVISO: Nenhum arquivo .xml encontrado em '{XML_DIR}'.")
        return

    print(f"Encontrados {len(xml_files)} arquivos XML para processar.\n")
    
    success_count = 0
    fail_count = 0
    
    # Garante que a API está rodando em homologação
    try:
        with open('.env', 'r') as f:
            env_content = f.read()
        if 'NFE_AMBIENTE=PRODUCAO' in env_content:
            print("🟡 AVISO: A API parece estar em modo PRODUÇÃO. O teste pode falhar se as chaves forem de homologação.")
        else:
            print("✅ API em modo HOMOLOGAÇÃO.")
    except FileNotFoundError:
        print("🟡 AVISO: Arquivo .env não encontrado. Não foi possível verificar o ambiente da API.")


    for i, filename in enumerate(xml_files):
        file_path = os.path.join(XML_DIR, filename)
        print(f"[{i+1}/{len(xml_files)}] Processando: {filename}")

        chNFe = get_chNFe_from_xml(file_path)

        if not chNFe or len(chNFe) != 44:
            print(f"    ❌ Chave NF-e inválida ou não encontrada no arquivo. Pulando.")
            fail_count += 1
            continue
        
        print(f"    🔑 Chave encontrada: {chNFe}")

        # Tenta manifestar com nSeq=1, depois nSeq=2, etc.
        for nSeq in range(1, 4):
            print(f"    ▶️  Tentando manifestar com nSeq={nSeq}...")
            
            params = {
                "empresa_id": EMPRESA_ID,
                "chNFe": chNFe,
                "tpEvento": TP_EVENTO,
                "nSeq": nSeq
            }
            
            try:
                response = requests.post(API_URL, params=params, timeout=45)
                
                if response.status_code == 200:
                    data = response.json()
                    cStat = data.get('cStat')
                    xMotivo = data.get('xMotivo')
                    
                    if cStat == 135: # Evento registrado e vinculado
                        print(f"    ✅ SUCESSO! (cStat={cStat}): {xMotivo}")
                        success_count += 1
                        break # Vai para o próximo arquivo
                    elif cStat == 573: # Duplicidade de Evento
                        print(f"    🟡 AVISO: Evento já registrado (cStat={cStat}): {xMotivo}. Tentando próximo nSeq...")
                        continue # Tenta próximo nSeq
                    else:
                        print(f"    ❌ FALHA (cStat={cStat}): {xMotivo}")
                        fail_count += 1
                        break # Vai para o próximo arquivo

                else:
                    detail = "N/A"
                    try:
                        detail = response.json().get('detail', response.text)
                    except json.JSONDecodeError:
                        detail = response.text
                    print(f"    ❌ FALHA na API (HTTP {response.status_code}): {detail}")
                    fail_count += 1
                    break # Vai para o próximo arquivo

            except requests.exceptions.RequestException as e:
                print(f"    ❌ ERRO de conexão com a API: {e}")
                fail_count += 1
                break # Vai para o próximo arquivo
        print("-" * 40)

    print("\n" + "=" * 80)
    print("TESTE FINALIZADO")
    print(f"  Resultados: {success_count} SUCESSO(S), {fail_count} FALHA(S)")
    print("=" * 80)

if __name__ == "__main__":
    main()
