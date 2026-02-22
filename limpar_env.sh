# 1. Parar qualquer processo da API
pkill -f uvicorn 2>/dev/null || true

# 2. Desativar venv atual
deactivate 2>/dev/null || true

# 3. REMOVER o .venv corrompido
rm -rf /mnt/c/Projetos/dfe-sync/.venv

# 4. Criar NOVO ambiente virtual
cd /mnt/c/Projetos/dfe-sync
python3 -m venv .venv

# 5. Ativar o NOVO ambiente
source .venv/bin/activate

# 6. Atualizar pip
pip install --upgrade pip

# 7. Instalar patool CORRETAMENTE
pip install patool

# 8. VERIFICAR se o import funciona AGORA
python -c "import patool; print('✅ SUCESSO:', patool.__file__)"
