#!/bin/bash

# Script para forçar início limpo do sistema administrativo
echo "🧹 Limpando cache e iniciando sistema limpo..."

# Parar tudo primeiro
pkill -f "vite" 2>/dev/null || true
pkill -f "classificador.py" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true

# Limpar cache do Vite
cd web/
rm -rf node_modules/.vite 2>/dev/null || true
rm -rf dist 2>/dev/null || true

# Forçar reinstalação das dependências
echo "📦 Reinstalando dependências..."
npm install --force

echo "🚀 Iniciando sistema na porta 5174 (nova)..."

# Modificar temporariamente a porta do Vite
sed -i.bak 's/port: 5173/port: 5174/g' vite.config.ts

# Iniciar em background
npm run dev &
VITE_PID=$!

cd ..

echo "✅ Sistema iniciado na porta 5174"
echo "🌐 Acesse: http://localhost:5174"

echo "Para parar: kill $VITE_PID"
echo "PID do Vite: $VITE_PID"