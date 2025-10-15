#!/usr/bin/env bash
# Script para iniciar a API FastAPI (Linux/WSL)
set -euo pipefail

# Diretório base = pasta onde o script está localizado
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$SCRIPT_DIR"
cd "$BASE_DIR"

# Ativa virtualenv local
VENV_ACTIVATE="$BASE_DIR/.venv/bin/activate"
if [[ -f "$VENV_ACTIVATE" ]]; then
	# shellcheck disable=SC1090
	source "$VENV_ACTIVATE"
else
	echo "[start-api] Virtualenv não encontrado em $VENV_ACTIVATE" >&2
	echo "[start-api] Crie o ambiente: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" >&2
	exit 1
fi

export PYTHONPATH="$BASE_DIR:${PYTHONPATH:-}"
exec uvicorn src.api.main:app --reload --port 8001 --host 0.0.0.0
