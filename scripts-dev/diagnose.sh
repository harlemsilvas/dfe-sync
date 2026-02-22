#!/bin/bash
echo "=== Diagnóstico Rápido ==="

echo "1. Ambiente atual:"
grep NFE_AMBIENTE .env

echo -e "\n2. Empresa no banco:"
docker exec dfe_db psql -U dfe -d dfe -c "SELECT id, cnpj, ambiente FROM empresas WHERE id = 1;"

echo -e "\n3. Certificado:"
docker exec dfe_db psql -U dfe -d dfe -c "SELECT empresa_id, tipo, substring(pfx_path, 1, 50) as pfx_path FROM certificados WHERE empresa_id = 1;"

echo -e "\n4. Teste simples de sincronização (5s timeout):"
timeout 5 curl -X POST "http://localhost:8001/api/dfe/sync?empresa_id=1" || echo "Timeout ou erro"

