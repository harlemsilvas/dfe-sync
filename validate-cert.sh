#!/bin/bash
set -euo pipefail
CERT_PFX=${1:-storage/certs/1.pfx}
PASS=${2:-513094}
TMP_DIR=$(mktemp -d)
PFX_PEM="$TMP_DIR/cert.pem"
KEY_PEM="$TMP_DIR/key.pem"
CHAIN_PEM="$TMP_DIR/chain.pem"

if [ ! -f "$CERT_PFX" ]; then
  echo "Arquivo PFX não encontrado: $CERT_PFX" >&2
  exit 1
fi

echo "[1] Extraindo certificados do PFX..."
if ! openssl pkcs12 -in "$CERT_PFX" -nokeys -passin pass:$PASS -legacy -out "$PFX_PEM" 2>"$TMP_DIR/cert_err.log"; then
  echo "Falha ao extrair cert. Log:" >&2
  sed -n '1,15p' "$TMP_DIR/cert_err.log" >&2
  echo "Sugestão: verifique a senha ou tente openssl pkcs12 -in $CERT_PFX -info -legacy" >&2
  exit 1
fi
if ! openssl pkcs12 -in "$CERT_PFX" -nocerts -passin pass:$PASS -legacy -passout pass:temp123 -out "$KEY_PEM" 2>"$TMP_DIR/key_err.log"; then
  echo "Falha ao extrair chave. Log:" >&2
  sed -n '1,15p' "$TMP_DIR/key_err.log" >&2
  exit 1
fi
openssl rsa -in "$KEY_PEM" -passin pass:temp123 -out "$TMP_DIR/key_nopass.pem" 2>/dev/null || true

echo "[2] Informações do certificado:"
openssl x509 -in "$PFX_PEM" -noout -subject -issuer -dates -serial -fingerprint -sha1

echo "[3] Testando conexão HTTPS com Ambiente Nacional..."
TARGET_HOST="www.nfe.fazenda.gov.br"
CURL_OUT=$(curl -s -o /dev/null -w '%{http_code}' --cert "$PFX_PEM" --key "$TMP_DIR/key_nopass.pem" https://$TARGET_HOST/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx || true)
echo "Código HTTP obtido: $CURL_OUT"

echo "[4] Limpeza temporários"
rm -rf "$TMP_DIR"
