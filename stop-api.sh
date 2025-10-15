#!/usr/bin/env bash
set -euo pipefail

PORT=8001
# Diretório base = pasta onde o script está localizado
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$BASE_DIR/uvicorn.pid"
FORCE=false

usage(){
  cat <<EOF
Uso: $0 [-p PORTA] [-f]
  -p PORTA   Porta (default 8001)
  -f         Força SIGKILL se término gracioso falhar
  -h         Ajuda
EOF
}

while getopts ":p:fh" opt; do
  case $opt in
    p) PORT=$OPTARG ;;
    f) FORCE=true ;;
    h) usage; exit 0 ;;
    :) echo "Opção -$OPTARG requer valor" >&2; exit 1 ;;
    \?) echo "Opção inválida -$OPTARG" >&2; usage; exit 1 ;;
  esac
done

found_pid=""

if [[ -f $PID_FILE ]]; then
  pid_from_file=$(cat "$PID_FILE" || true)
  if [[ -n "$pid_from_file" && -d "/proc/$pid_from_file" ]]; then
    found_pid=$pid_from_file
    echo "[stop-api] PID encontrado via arquivo: $found_pid"
  else
    echo "[stop-api] Arquivo PID obsoleto. Removendo."; rm -f "$PID_FILE"
  fi
fi

if [[ -z "$found_pid" ]]; then
  # fallback: busca por porta
  pid_port=$(lsof -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null || true)
  if [[ -n "$pid_port" ]]; then
    found_pid=$pid_port
    echo "[stop-api] PID encontrado na porta $PORT: $found_pid"
  fi
fi

if [[ -z "$found_pid" ]]; then
  echo "[stop-api] Nenhum processo uvicorn encontrado para parar."; exit 0
fi

kill "$found_pid" || true
for i in {1..20}; do
  if [[ -d "/proc/$found_pid" ]]; then
    sleep 0.2
  else
    break
  fi
done

if [[ -d "/proc/$found_pid" ]]; then
  if $FORCE; then
    echo "[stop-api] Enviando SIGKILL ao PID $found_pid"
    kill -9 "$found_pid" || true
  else
    echo "[stop-api] Processo não encerrou (use -f para forçar)." >&2
    exit 1
  fi
fi

rm -f "$PID_FILE" 2>/dev/null || true
echo "[stop-api] Encerrado."