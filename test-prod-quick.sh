#!/bin/bash
echo "=== Teste Rápido - Ambiente PRODUÇÃO ==="
echo ""

echo "1. Verificando API..."
curl -s "http://localhost:8001/health" && echo " ✓ API OK"
echo ""

echo "2. Cursor antes da sincronização:"
curl -s "http://localhost:8001/api/dfe/cursor?empresa_id=1"
echo -e "\n"

echo "3. Testando sincronização com timeout de 60s..."
timeout 60 curl -v -X POST "http://localhost:8001/api/dfe/sync?empresa_id=1" &
SYNC_PID=$!

echo "4. Aguardando 30s e verificando progresso..."
sleep 30

echo "   Cursor após 30s:"
curl -s "http://localhost:8001/api/dfe/cursor?empresa_id=1"
echo -e "\n"

echo "   Documentos encontrados:"
curl -s "http://localhost:8001/api/documentos?empresa_id=1&limit=3"
echo -e "\n"

# Aguarda o processo ou timeout
wait $SYNC_PID 2>/dev/null

echo "5. Status final:"
echo "   Cursor final:"
curl -s "http://localhost:8001/api/dfe/cursor?empresa_id=1"
echo -e "\n"

echo "   Total de documentos:"
curl -s "http://localhost:8001/api/documentos?empresa_id=1&limit=1" | grep -o '"count":[0-9]*'
echo ""

