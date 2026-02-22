#!/bin/bash
echo "=== Teste Completo do Workflow DF-e ==="
echo ""

echo "1. Verificando API..."
curl -s "http://localhost:8001/health" && echo " ✓ API OK"
echo ""

echo "2. Consultando cursor inicial..."
curl -s "http://localhost:8001/api/dfe/cursor?empresa_id=1"
echo ""

echo "3. Iniciando sincronização em background..."
echo "   (Executando: curl -X POST 'http://localhost:8001/api/dfe/sync?empresa_id=1' &)"
curl -X POST "http://localhost:8001/api/dfe/sync?empresa_id=1" > sync_result.log 2>&1 &
SYNC_PID=$!
echo "   Sincronização iniciada com PID: $SYNC_PID"
echo ""

echo "4. Monitorando enquanto sincroniza..."
for i in {1..6}; do
    echo "   --- Verificação $i/6 ---"
    echo "   Cursor:"
    curl -s "http://localhost:8001/api/dfe/cursor?empresa_id=1" | head -c 200
    echo ""
    echo "   Documentos:"
    curl -s "http://localhost:8001/api/documentos?empresa_id=1&limit=3" | head -c 200
    echo ""
    echo "   Arquivos XML:"
    find storage/xml/ -name "*.xml" 2>/dev/null | wc -l | xargs echo "   Total de XMLs:"
    echo ""
    sleep 10
done

echo "5. Resultado final da sincronização:"
wait $SYNC_PID
cat sync_result.log
echo ""

