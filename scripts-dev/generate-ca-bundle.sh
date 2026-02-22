#!/bin/bash
set -euo pipefail
PFX=${1:-storage/certs/1.pfx}
PASS=${2:-changeit}
OUT=${3:-storage/ca/icp-brasil-bundle.pem}
TMP=$(mktemp -d)
mkdir -p "$(dirname "$OUT")"

if [ ! -f "$PFX" ]; then
  echo "PFX não encontrado: $PFX" >&2
  exit 1
fi

echo "[1] Extraindo cadeia do PFX (usa -legacy para compatibilidade OpenSSL 3.x)..."
openssl pkcs12 -in "$PFX" -nokeys -passin pass:$PASS -legacy -out "$TMP/cert_chain_full.pem" 2>"$TMP/err.log" || { echo "Falha openssl pkcs12"; sed -n '1,20p' "$TMP/err.log"; exit 1; }

# Filtrar apenas blocos -----BEGIN CERTIFICATE----- para montar bundle limpo
awk '/-----BEGIN CERTIFICATE-----/{flag=1} flag; /-----END CERTIFICATE-----/{flag=0}' "$TMP/cert_chain_full.pem" > "$OUT"

COUNT=$(grep -c "-----BEGIN CERTIFICATE-----" "$OUT" || true)
if [ "$COUNT" -lt 2 ]; then
  echo "Alerta: bundle contém apenas $COUNT certificado(s). Pode faltar raiz/intermediária." >&2
fi

echo "Bundle gerado em: $OUT (certificados: $COUNT)"

echo "Teste rápido curl usando bundle (sem client cert):"
TARGET=https://www.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' --cacert "$OUT" $TARGET || true)
echo "HTTP code: $HTTP_CODE"

echo "Para usar na aplicação: export DFE_CA_BUNDLE=$OUT"