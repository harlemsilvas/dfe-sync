#!/bin/bash
# Script para testes rápidos da API DFe-SEFAZ
# Arquivo: test-dfe-api.sh

echo "🧪 TESTES RÁPIDOS API DFE-SEFAZ"
echo "==============================="

API_URL="http://localhost:8002"

# Função para testar endpoint
test_endpoint() {
    local endpoint=$1
    local method=${2:-GET}
    local description=$3
    
    echo ""
    echo "🔍 Testando: $description"
    echo "   $method $endpoint"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$API_URL$endpoint")
        http_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | head -n -1)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$API_URL$endpoint")
        http_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | head -n -1)
    fi
    
    if [ "$http_code" = "200" ]; then
        echo "   ✅ Status: $http_code"
        echo "   📄 Response: $(echo "$body" | jq '.' 2>/dev/null || echo "$body" | head -c 100)..."
    else
        echo "   ❌ Status: $http_code"
        echo "   📄 Response: $body"
    fi
}

# Verificar se a API está rodando
echo "🌐 Verificando se API está ativa..."
if ! curl -s "$API_URL/health" >/dev/null; then
    echo "❌ API não está respondendo em $API_URL"
    echo ""
    echo "🚀 Deseja iniciar a API? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        ./start-dfe-api.sh
        echo ""
        echo "⏳ Aguardando API inicializar..."
        sleep 5
        
        if ! curl -s "$API_URL/health" >/dev/null; then
            echo "❌ Falha ao iniciar API"
            exit 1
        fi
    else
        echo "   Execute: ./start-dfe-api.sh primeiro"
        exit 1
    fi
fi

echo "✅ API está ativa!"

# Testes básicos
test_endpoint "/health" "GET" "Health Check"
test_endpoint "/api/empresas" "GET" "Listar Empresas"
test_endpoint "/api/dfe/diagnose?empresa_id=1" "GET" "Diagnóstico DFe (Empresa 1)"

# Teste de consulta se houver empresa cadastrada
echo ""
echo "📋 RESUMO DOS TESTES"
echo "==================="
echo "✅ Testes concluídos"
echo "🌐 API URL: $API_URL"
echo "📖 Documentação: $API_URL/docs"