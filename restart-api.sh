#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
Uso: $0 [-p PORTA] [-m APP_MODULE] [-H HOST] [-b] [-l LOGFILE]
  -p PORTA       Porta (default: 8001)
  -m APP_MODULE  Módulo ASGI (default: src.api.main:app)
  -H HOST        Host bind (default: 0.0.0.0)
  -b             Executa em background (nohup) liberando terminal
  -l LOGFILE     Caminho do log (default: logs/api.log quando -b)
  -h             Ajuda
EOF
}

# Defaults
PORT=8001
HOST=0.0.0.0
APP_MODULE="src.api.main:app"
BACKGROUND=false
LOGFILE=""

while getopts ":p:m:H:bl:h" opt; do
  case $opt in
    p) PORT=$OPTARG ;;
    m) APP_MODULE=$OPTARG ;;
    H) HOST=$OPTARG ;;
    b) BACKGROUND=true ;;
    l) LOGFILE=$OPTARG ;;
    h) usage; exit 0 ;;
    :) echo "[restart-api] Opção -$OPTARG requer valor" >&2; exit 1 ;;
    \?) echo "[restart-api] Opção inválida: -$OPTARG" >&2; usage; exit 1 ;;
  esac
done

# Diretório base = pasta onde o script está localizado
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$BASE_DIR/.venv/bin/activate"
PID_FILE="$BASE_DIR/uvicorn.pid"

echo "[restart-api] Base: $BASE_DIR Porta: $PORT Background: $BACKGROUND"

cd "$BASE_DIR"

if [[ -f "$VENV" ]]; then
  # shellcheck disable=SC1090
  source "$VENV"
else
  echo "[restart-api] ERRO: Virtualenv não encontrado em $VENV" >&2
  exit 1
fi

export PYTHONPATH="$BASE_DIR:${PYTHONPATH:-}"

# Derruba processo anterior via PID_FILE se existir
if [[ -f "$PID_FILE" ]]; then
  OLD_PID=$(cat "$PID_FILE" || true)
  if [[ -n "$OLD_PID" && -d "/proc/$OLD_PID" ]]; then
    echo "[restart-api] Matando PID anterior (arquivo pid): $OLD_PID"
    kill "$OLD_PID" 2>/dev/null || true
  fi
  rm -f "$PID_FILE"
fi

# Detectar processo ouvindo na porta (fallback)
PID=$(lsof -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null || true)
if [[ -n "$PID" ]]; then
  echo "[restart-api] Encontrado processo na porta $PORT (PID=$PID). Encerrando..."
  kill "$PID" || true
  for i in {1..20}; do
    if lsof -iTCP:"$PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
      sleep 0.3
    else
      break
    fi
  done
  if lsof -iTCP:"$PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "[restart-api] Aviso: processo persistente, enviando SIGKILL"
    kill -9 "$PID" || true
  fi
else
  echo "[restart-api] Nenhum processo na porta $PORT"
fi

if $BACKGROUND; then
  mkdir -p logs
  if [[ -z "$LOGFILE" ]]; then
    LOGFILE="logs/api.log"
  fi
  echo "[restart-api] Subindo (background) uvicorn $APP_MODULE -> $LOGFILE"
  nohup uvicorn "$APP_MODULE" --reload --port "$PORT" --host "$HOST" > "$LOGFILE" 2>&1 &
  NEW_PID=$!
  echo $NEW_PID > "$PID_FILE"
  disown $NEW_PID || true
  echo "[restart-api] PID: $NEW_PID (log: $LOGFILE)"
else
  echo "[restart-api] Subindo (foreground) uvicorn $APP_MODULE"
  exec uvicorn "$APP_MODULE" --reload --port "$PORT" --host "$HOST"
fi
