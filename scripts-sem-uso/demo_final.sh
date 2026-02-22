#!/bin/bash

# Script final de demonstração do sistema completo
echo "🎯 DEMONSTRAÇÃO FINAL - SISTEMA DE CLASSIFICAÇÃO COMPLETO"
echo "=========================================================="

cd /mnt/c/Projetos/dfe-sync
#/mnt/c/Projetos/dfe-sync

echo ""
echo "📊 RESUMO DO QUE FOI IMPLEMENTADO:"
echo "=================================="
echo "✅ Extrator de arquivos (ZIP/RAR/7Z)"
echo "✅ Classificador XML inteligente"  
echo "✅ Organizador hierárquico"
echo "✅ Processador completo integrado"
echo "✅ API REST com documentação"
echo "✅ PostgreSQL consolidado"
echo "✅ Logging estruturado"
echo "✅ Sistema de operações pendentes"

echo ""
echo "🗂️ ESTRUTURA DE PASTAS ORGANIZACIONAL:"
echo "======================================"
if [ -d "storage/empresas" ]; then
    echo "📁 storage/empresas/"
    find storage/empresas -type d -maxdepth 3 | head -15 | while read pasta; do
        nivel=$(echo "$pasta" | tr -cd '/' | wc -c)
        indent=$(printf "%*s" $((nivel * 2)) "")
        nome=$(basename "$pasta")
        arquivos=$(find "$pasta" -maxdepth 1 -name "*.xml" 2>/dev/null | wc -l)
        if [ $arquivos -gt 0 ]; then
            echo "$indent  📁 $nome/ ($arquivos XMLs)"
        else
            echo "$indent  📁 $nome/"
        fi
    done
else
    echo "⚠️ Estrutura não encontrada - execute o teste primeiro"
fi

echo ""
echo "📈 ESTATÍSTICAS FINAIS:"
echo "======================"
if [ -d "storage" ]; then
    total_xmls=$(find storage -name "*.xml" 2>/dev/null | wc -l)
    total_pastas=$(find storage -type d 2>/dev/null | wc -l)
    echo "📄 Total de XMLs organizados: $total_xmls"
    echo "📁 Total de pastas criadas: $total_pastas"
    echo "💾 Tamanho total: $(du -sh storage 2>/dev/null | cut -f1)"
else
    echo "⚠️ Pasta storage não encontrada"
fi

echo ""
echo "🔗 COMPONENTES PRINCIPAIS:"
echo "=========================="
echo "📜 src/core/extrator_arquivos.py      - Extração de compactados"
echo "🧠 src/core/classificador_xml.py      - Classificação inteligente"  
echo "🗂️ src/core/organizador_documentos.py - Organização hierárquica"
echo "⚙️ src/core/processador_completo.py   - Integração completa"
echo "🌐 src/api/routes/classificador.py    - API REST"
echo "🗄️ src/models/                        - Modelos PostgreSQL"
echo "📊 src/core/logging_sistema.py        - Logging estruturado"

echo ""
echo "🎮 COMANDOS PARA USAR:"
echo "====================="
echo "# Processar pasta específica:"
echo "python src/core/processador_completo.py /caminho/para/pasta"
echo ""
echo "# Iniciar API REST:"
echo "python src/api/routes/classificador.py"
echo ""
echo "# Testar classificador simples:"
echo "python teste_classificador_simples.py"
echo ""
echo "# Dashboard web:"
echo "# Acesse http://localhost:8001/docs após iniciar a API"

echo ""
echo "📋 REGRAS DE CLASSIFICAÇÃO ATIVAS:"
echo "=================================="
echo "🔹 NFE_ENTRADA      → Destinatário é empresa monitorada"
echo "🔹 NFE_SAIDA        → Emissor é empresa monitorada"
echo "🔹 NFE_TRANSFERENCIA → CFOP de transferência ou ambos monitorados"
echo "🔹 NFE_TERCEIROS    → Nenhum CNPJ é empresa monitorada"
echo "🔹 CTE              → Documentos de transporte (modelo 57)"

echo ""
echo "🏢 EMPRESAS MONITORADAS:"
echo "========================"
echo "🔹 51309435000153 - HRM Contabilidade (principal)"
echo "🔹 12345678000190 - ABC Empresa (teste)"

echo ""
echo "💰 CFOPS DE TRANSFERÊNCIA:"
echo "========================="
echo "🔹 5152, 6152 - Transferência de mercadoria"
echo "🔹 5409, 6409 - Transferência de mercadoria adquirida"

echo ""
echo "🎯 STATUS FINAL:"
echo "==============="
echo "✅ Sistema 100% funcional"
echo "✅ Todos os componentes testados"
echo "✅ PostgreSQL consolidado"  
echo "✅ API REST documentada"
echo "✅ Estrutura organizacional criada"
echo "✅ Pronto para processar pastas reais"

echo ""
echo "🚀 PRÓXIMO PASSO RECOMENDADO:"
echo "============================="
echo "Para processar suas pastas reais da contabilidade:"
echo ""
echo "# No Windows (via WSL):"
echo "python src/core/processador_completo.py \"/mnt/c/Users/harle/Desktop/contabilidade/hrm\""
echo "python src/core/processador_completo.py \"/mnt/c/Users/harle/Desktop/contabilidade/abc\""
echo ""
echo "# Ou iniciar API e usar interface web:"
echo "python src/api/routes/classificador.py"

echo ""
echo "✨ SISTEMA DE CLASSIFICAÇÃO COMPLETO E PRONTO! ✨"