#!/bin/bash
echo "Monitorando sincronização DF-e..."
echo "================================"

while true; do
    clear
    echo "=== Status da Sincronização $(date) ==="
    echo ""
    
    echo "1. Cursor atual:"
    curl -s "http://localhost:8001/api/dfe/cursor?empresa_id=1" | jq . 2>/dev/null || curl -s "http://localhost:8001/api/dfe/cursor?empresa_id=1"
    echo ""
    
    echo "2. Documentos encontrados:"
    curl -s "http://localhost:8001/api/documentos?empresa_id=1&limit=5" | jq . 2>/dev/null || curl -s "http://localhost:8001/api/documentos?empresa_id=1&limit=5"
    echo ""
    
    echo "3. Arquivos XML baixados:"
    find storage/xml/ -name "*.xml" 2>/dev/null | head -5
    echo ""
    
    echo "Pressione Ctrl+C para parar o monitoramento"
    sleep 5
done
