#!/usr/bin/env bash
# Script helper para gerenciar o frontend
set -euo pipefail

SCRIPT_REAL="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_REAL")"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WEB_DIR="$BASE_DIR/web"

cd "$WEB_DIR"

show_help() {
    cat <<EOF
🎨 DFe Sync - Frontend Helper

Uso: $0 [comando]

Comandos:
  install     Instala dependências (npm install)
  dev         Inicia servidor de desenvolvimento
  build       Build de produção
  preview     Preview do build
  clean       Limpa node_modules e build
  check       Verifica se tudo está ok

Exemplos:
  $0 install
  $0 dev
  $0 build

EOF
}

check_node() {
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js não encontrado. Instale: https://nodejs.org/" >&2
        exit 1
    fi
    if ! command -v npm &> /dev/null; then
        echo "❌ npm não encontrado. Instale: https://nodejs.org/" >&2
        exit 1
    fi
    echo "✅ Node $(node --version)"
    echo "✅ npm $(npm --version)"
}

check_deps() {
    if [ ! -d "node_modules" ]; then
        echo "⚠️  Dependências não instaladas. Execute: $0 install"
        return 1
    fi
    echo "✅ Dependências instaladas"
    return 0
}

check_favicon() {
    if [ -f "public/favicon.ico" ]; then
        echo "✅ Favicon em public/favicon.ico"
    else
        echo "⚠️  Favicon não encontrado em public/"
    fi
}

cmd_install() {
    echo "📦 Instalando dependências..."
    npm install
    echo "✅ Dependências instaladas com sucesso!"
}

cmd_dev() {
    echo "🚀 Iniciando servidor de desenvolvimento..."
    echo ""
    echo "Frontend: http://localhost:5173"
    echo "Backend API deve estar em: http://localhost:8001"
    echo ""
    echo "Pressione Ctrl+C para parar"
    echo ""
    npm run dev
}

cmd_build() {
    echo "🏗️  Construindo para produção..."
    npm run build
    echo ""
    echo "✅ Build concluído!"
    echo "📁 Arquivos em: $WEB_DIR/dist"
    echo ""
    echo "Para testar o build:"
    echo "  $0 preview"
}

cmd_preview() {
    echo "👀 Preview do build de produção..."
    echo ""
    echo "Preview: http://localhost:4173"
    echo ""
    npm run preview
}

cmd_clean() {
    echo "🧹 Limpando..."
    rm -rf node_modules dist
    echo "✅ Limpeza concluída!"
}

cmd_check() {
    echo "🔍 Verificando frontend..."
    echo ""
    check_node
    check_deps || true
    check_favicon
    echo ""
    
    if [ -d "node_modules" ]; then
        echo "✅ Frontend pronto para uso!"
        echo ""
        echo "Comandos disponíveis:"
        echo "  $0 dev      - Iniciar desenvolvimento"
        echo "  $0 build    - Build de produção"
    else
        echo "⚠️  Execute primeiro: $0 install"
    fi
}

# Main
case "${1:-help}" in
    install)
        cmd_install
        ;;
    dev)
        check_node
        check_deps || cmd_install
        cmd_dev
        ;;
    build)
        check_node
        check_deps || cmd_install
        cmd_build
        ;;
    preview)
        check_node
        if [ ! -d "dist" ]; then
            echo "❌ Build não encontrado. Execute primeiro: $0 build" >&2
            exit 1
        fi
        cmd_preview
        ;;
    clean)
        cmd_clean
        ;;
    check)
        cmd_check
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Comando desconhecido: $1" >&2
        echo ""
        show_help
        exit 1
        ;;
esac
