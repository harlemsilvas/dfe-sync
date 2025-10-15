#!/bin/bash
# Script para testar a API

echo "Criando empresa..."
curl -X POST "http://localhost:8001/api/empresas" \
  -F "cnpj=51.309.435/0001-53" \
  -F "razao_social=ABC CENTER DISTRIBUIDORA LTDA" \
  -F "ambiente=HOMOLOG"
echo ""
echo "Testando health check..."
curl http://localhost:8001/health
echo ""
