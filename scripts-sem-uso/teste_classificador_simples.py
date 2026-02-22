"""
Teste simples do classificador XML
"""

import sys
import os
import tempfile
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, '/mnt/c/Projetos/dfe-sync')

# Simular um XML de teste sem usar banco
xml_teste = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
    <NFe>
        <infNFe Id="NFe35251051309435000153550010000041251728126118">
            <ide>
                <mod>55</mod>
                <nNF>4125</nNF>
                <serie>1</serie>
                <dhEmi>2025-01-14T10:30:00-03:00</dhEmi>
                <natOp>Venda de mercadoria</natOp>
            </ide>
            <emit>
                <CNPJ>12345678000100</CNPJ>
                <xNome>EMPRESA TESTE EMISSOR LTDA</xNome>
            </emit>
            <dest>
                <CNPJ>51309435000153</CNPJ>
                <xNome>EMPRESA TESTE DESTINATARIO LTDA</xNome>
            </dest>
            <det nItem="1">
                <prod>
                    <cProd>001</cProd>
                    <cEAN></cEAN>
                    <xProd>Produto teste</xProd>
                    <CFOP>5102</CFOP>
                    <uCom>UN</uCom>
                    <qCom>1</qCom>
                    <vUnCom>1000.00</vUnCom>
                    <vProd>1000.00</vProd>
                </prod>
            </det>
            <total>
                <ICMSTot>
                    <vBC>1000.00</vBC>
                    <vICMS>180.00</vICMS>
                    <vNF>1000.00</vNF>
                </ICMSTot>
            </total>
        </infNFe>
    </NFe>
</nfeProc>"""

def teste_classificador_simples():
    """Teste do classificador sem conexão com banco"""
    
    # Criar arquivo temporário
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
        f.write(xml_teste)
        xml_path = f.name
    
    try:
        # Importar só as partes necessárias para parsing XML
        import xml.etree.ElementTree as ET
        from datetime import datetime
        from dataclasses import dataclass
        from decimal import Decimal
        from typing import Optional, Dict
        
        @dataclass
        class MetadataSimples:
            chave_acesso: Optional[str] = None
            modelo: Optional[str] = None
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
            erro_parsing: Optional[str] = None
        
        def extrair_metadados_simples(xml_content: str) -> MetadataSimples:
            """Extração simples de metadados"""
            metadata = MetadataSimples()
            
            try:
                root = ET.fromstring(xml_content)
                
                # Namespace
                ns = {}
                if root.tag.startswith('{'):
                    namespace = root.tag.split('}')[0][1:]
                    ns['ns'] = namespace
                
                # Encontrar infNFe
                inf_nfe = root.find('.//ns:infNFe', ns)
                if inf_nfe is None:
                    inf_nfe = root.find('.//infNFe')
                if inf_nfe is None:
                    metadata.erro_parsing = "Elemento infNFe não encontrado"
                    return metadata
                
                # Chave de acesso
                chave_attr = inf_nfe.get('Id', '')
                if chave_attr.startswith('NFe'):
                    metadata.chave_acesso = chave_attr[3:]
                
                # IDE
                ide = inf_nfe.find('.//ns:ide', ns)
                if ide is None:
                    ide = inf_nfe.find('.//ide')
                if ide is not None:
                    mod_elem = ide.find('.//ns:mod', ns)
                    if mod_elem is None:
                        mod_elem = ide.find('.//mod')
                    if mod_elem is not None:
                        metadata.modelo = mod_elem.text
                    
                    nnf_elem = ide.find('.//ns:nNF', ns)
                    if nnf_elem is None:
                        nnf_elem = ide.find('.//nNF')
                    if nnf_elem is not None:
                        metadata.numero = nnf_elem.text
                    
                    serie_elem = ide.find('.//ns:serie', ns)
                    if serie_elem is None:
                        serie_elem = ide.find('.//serie')
                    if serie_elem is not None:
                        metadata.serie = serie_elem.text
                    
                    natop_elem = ide.find('.//ns:natOp', ns)
                    if natop_elem is None:
                        natop_elem = ide.find('.//natOp')
                    if natop_elem is not None:
                        metadata.natureza_operacao = natop_elem.text
                
                # Emissor
                emit = inf_nfe.find('.//ns:emit', ns)
                if emit is None:
                    emit = inf_nfe.find('.//emit')
                if emit is not None:
                    cnpj_elem = emit.find('.//ns:CNPJ', ns)
                    if cnpj_elem is None:
                        cnpj_elem = emit.find('.//CNPJ')
                    if cnpj_elem is not None:
                        metadata.cnpj_emissor = cnpj_elem.text
                
                # Destinatário
                dest = inf_nfe.find('.//ns:dest', ns)
                if dest is None:
                    dest = inf_nfe.find('.//dest')
                if dest is not None:
                    cnpj_elem = dest.find('.//ns:CNPJ', ns)
                    if cnpj_elem is None:
                        cnpj_elem = dest.find('.//CNPJ')
                    if cnpj_elem is not None:
                        metadata.cnpj_destinatario = cnpj_elem.text
                
                # CFOP
                det = inf_nfe.find('.//ns:det', ns)
                if det is None:
                    det = inf_nfe.find('.//det')
                if det is not None:
                    prod = det.find('.//ns:prod', ns)
                    if prod is None:
                        prod = det.find('.//prod')
                    if prod is not None:
                        cfop_elem = prod.find('.//ns:CFOP', ns)
                        if cfop_elem is None:
                            cfop_elem = prod.find('.//CFOP')
                        if cfop_elem is not None:
                            metadata.cfop = cfop_elem.text
                
                # Total
                total = inf_nfe.find('.//ns:total/ns:ICMSTot', ns)
                if total is None:
                    total = inf_nfe.find('.//total/ICMSTot')
                if total is not None:
                    vnf_elem = total.find('.//ns:vNF', ns)
                    if vnf_elem is None:
                        vnf_elem = total.find('.//vNF')
                    if vnf_elem is not None:
                        metadata.valor_total = Decimal(vnf_elem.text.replace(',', '.'))
                
            except Exception as e:
                metadata.erro_parsing = f"Erro ao extrair metadados: {e}"
            
            return metadata
        
        def classificar_simples(metadata: MetadataSimples) -> str:
            """Classificação simples com regras hardcoded para teste"""
            # CNPJs de teste das empresas monitoradas
            empresas_monitoradas = {'51309435000153', '12345678000190'}
            cfops_transferencia = {'5152', '6152', '5409', '6409'}
            
            if not metadata.cnpj_emissor and not metadata.cnpj_destinatario:
                metadata.motivo_classificacao = "CNPJs não identificados"
                return "NFE_TERCEIROS"
            
            # Verificar transferência
            if metadata.cfop and metadata.cfop in cfops_transferencia:
                metadata.motivo_classificacao = f"CFOP {metadata.cfop} é de transferência"
                return "NFE_TRANSFERENCIA"
            
            # Verificar direção
            emissor_monitorado = metadata.cnpj_emissor in empresas_monitoradas
            destinatario_monitorado = metadata.cnpj_destinatario in empresas_monitoradas
            
            if emissor_monitorado and destinatario_monitorado:
                metadata.motivo_classificacao = "Ambos são empresas monitoradas"
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
        
        # Processar arquivo
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        metadata = extrair_metadados_simples(xml_content)
        
        if not metadata.erro_parsing:
            metadata.tipo_documento = classificar_simples(metadata)
        
        # Exibir resultado
        print("🎯 TESTE DO CLASSIFICADOR XML")
        print("=" * 50)
        print(f"📄 Arquivo: {Path(xml_path).name}")
        print(f"🔑 Chave: {metadata.chave_acesso}")
        print(f"📋 Modelo: {metadata.modelo}")
        print(f"🏢 Emissor: {metadata.cnpj_emissor}")
        print(f"🏪 Destinatário: {metadata.cnpj_destinatario}")
        print(f"💰 CFOP: {metadata.cfop}")
        print(f"📝 Natureza: {metadata.natureza_operacao}")
        print(f"💵 Valor: R$ {metadata.valor_total}")
        print(f"🎯 Tipo: {metadata.tipo_documento}")
        print(f"💭 Motivo: {metadata.motivo_classificacao}")
        
        if metadata.erro_parsing:
            print(f"❌ Erro: {metadata.erro_parsing}")
        else:
            print("✅ Processado com sucesso!")
            
            # Simular estrutura de organização
            print(f"\n🗂️ ESTRUTURA DE ORGANIZAÇÃO:")
            
            if metadata.tipo_documento == "NFE_ENTRADA":
                cnpj_responsavel = metadata.cnpj_destinatario
            elif metadata.tipo_documento in ["NFE_SAIDA", "NFE_TRANSFERENCIA"]:
                cnpj_responsavel = metadata.cnpj_emissor
            else:
                cnpj_responsavel = "TERCEIROS"
            
            ano_mes = "2025-01"  # Simulado
            pasta_organizada = f"/storage/empresas/{cnpj_responsavel}/{ano_mes}/{metadata.tipo_documento}"
            nome_arquivo = f"{metadata.chave_acesso}.xml"
            
            print(f"📁 Pasta: {pasta_organizada}")
            print(f"📄 Nome: {nome_arquivo}")
            print(f"📍 Caminho completo: {pasta_organizada}/{nome_arquivo}")
    
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Limpar arquivo temporário
        if os.path.exists(xml_path):
            os.unlink(xml_path)

if __name__ == "__main__":
    teste_classificador_simples()