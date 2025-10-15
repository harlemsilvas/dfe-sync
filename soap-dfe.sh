#!/bin/bash
set -euo pipefail
CNPJ=${1:-51309435000153}
ULT_NSU=${2:-000000000000000}
AMBIENTE=${3:-PRODUCAO} # PRODUCAO ou HOMOLOG
PFX=${4:-storage/certs/1.pfx}
PASS=${5:-513094}
TMP=$(mktemp -d)
CERT_PEM=$TMP/cert.pem
KEY_PEM=$TMP/key.pem
KEY_NOPASS=$TMP/key_nopass.pem
OUT=$TMP/resp.xml
SOAP=$TMP/envelope.xml

TPAMB="1"; [ "${AMBIENTE^^}" = "HOMOLOG" ] && TPAMB="2"

openssl pkcs12 -in "$PFX" -nokeys -passin pass:$PASS -legacy -out "$CERT_PEM" 2>/dev/null
openssl pkcs12 -in "$PFX" -nocerts -passin pass:$PASS -legacy -passout pass:temp123 -out "$KEY_PEM" 2>/dev/null
openssl rsa -in "$KEY_PEM" -passin pass:temp123 -out "$KEY_NOPASS" 2>/dev/null

cat > "$SOAP" <<EOF
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:nfe="http://www.portalfiscal.inf.br/nfe" xmlns:ws="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe">
  <soap:Body>
    <ws:nfeDistDFeInteresse>
      <nfe:distDFeInt versao="1.01">
        <nfe:tpAmb>$TPAMB</nfe:tpAmb>
        <nfe:cUFAutor>91</nfe:cUFAutor>
        <nfe:CNPJ>$CNPJ</nfe:CNPJ>
        <nfe:distNSU>
          <nfe:ultNSU>$ULT_NSU</nfe:ultNSU>
        </nfe:distNSU>
      </nfe:distDFeInt>
    </ws:nfeDistDFeInteresse>
  </soap:Body>
</soap:Envelope>
EOF

URLS_PROD=(
  "https://www.nfe.fazenda.gov.br/ws/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx"
  "https://www.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx"
)
URLS_HOMO=(
  "https://hom.nfe.fazenda.gov.br/ws/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx"
  "https://hom.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx"
)

HTTP=""; URL=""
URL_LIST=()
if [ "${AMBIENTE^^}" = "HOMOLOG" ]; then
  URL_LIST=("${URLS_HOMO[@]}")
else
  URL_LIST=("${URLS_PROD[@]}")
fi
for CAND in "${URL_LIST[@]}"; do
  URL="$CAND"
  echo "[SOAP] Enviando para $URL (ultNSU=$ULT_NSU)" >&2
  HTTP=$(curl -s -o "$OUT" -w '%{http_code}' --cert "$CERT_PEM" --key "$KEY_NOPASS" -H 'Content-Type: text/xml; charset=utf-8' -H 'SOAPAction: http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe/nfeDistDFeInteresse' --data @"$SOAP" "$URL" || true)
  [ "$HTTP" = "200" ] && break
done

echo "HTTP: $HTTP" >&2
if [ "$HTTP" != "200" ]; then
  echo "Resposta não OK. Conteúdo bruto:" >&2
  sed -n '1,60p' "$OUT" >&2
  exit 1
fi

# Extrair cStat, xMotivo, ultNSU, maxNSU
python3 - <<PY "$OUT"
import sys, lxml.etree as ET
path = sys.argv[1]
xml = ET.parse(path)
ns = {'soap':'http://schemas.xmlsoap.org/soap/envelope/','nfe':'http://www.portalfiscal.inf.br/nfe'}
root = xml.getroot()
# retDistDFeInt está dentro do Body; procurar tags
cStat = root.find('.//nfe:cStat', ns)
xMotivo = root.find('.//nfe:xMotivo', ns)
ultNSU = root.find('.//nfe:ultNSU', ns)
maxNSU = root.find('.//nfe:maxNSU', ns)
print({'cStat':cStat.text if cStat is not None else None,
       'xMotivo':xMotivo.text if xMotivo is not None else None,
       'ultNSU':ultNSU.text if ultNSU is not None else None,
       'maxNSU':maxNSU.text if maxNSU is not None else None})
# quantidade de docZip
docs = root.findall('.//nfe:docZip', ns)
print('docs_zip', len(docs))
PY

rm -rf "$TMP"
