#!/bin/bash
# Script para setup completo do ambiente DFe-SEFAZ
# Arquivo: setup-dfe-environment.sh

echo "⚙️ SETUP COMPLETO AMBIENTE DFE-SEFAZ"
echo "===================================="

# Navegar para o diretório correto
cd /home/harlem/projetos/zipados/openai-xml/dfe-sync

echo "📁 Diretório atual: $(pwd)"

# 1. Verificar/instalar PostgreSQL
echo ""
echo "🗄️ 1. Configurando PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo "   📦 Instalando PostgreSQL..."
    sudo apt update && sudo apt install -y postgresql postgresql-contrib
fi

# Iniciar PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Criar usuário e banco se não existir
echo "   👤 Configurando usuário e banco..."
sudo -u postgres psql -c "CREATE USER dfe WITH PASSWORD 'dfe';" 2>/dev/null || echo "   ℹ️ Usuário dfe já existe"
sudo -u postgres psql -c "CREATE DATABASE dfe OWNER dfe;" 2>/dev/null || echo "   ℹ️ Banco dfe já existe"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE dfe TO dfe;" 2>/dev/null

# 2. Criar ambiente virtual
echo ""
echo "🐍 2. Configurando ambiente virtual Python..."
if [ ! -d ".venv-linux" ]; then
    python3 -m venv .venv-linux
    echo "   ✅ Ambiente virtual criado"
else
    echo "   ℹ️ Ambiente virtual já existe"
fi

# Ativar e instalar dependências
source .venv-linux/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install python-multipart jq

# 3. Configurar banco de dados
echo ""
echo "🗄️ 3. Configurando banco de dados..."
alembic upgrade head

# 4. Executar validação
echo ""
echo "✅ 4. Executando validação..."
python validate_setup.py

# 5. Criar alias globais
echo ""
echo "🔗 5. Criando aliases globais..."

# Adicionar aliases ao .bashrc se não existirem
if ! grep -q "alias start-dfe" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# Aliases DFe-SEFAZ" >> ~/.bashrc
    echo "alias start-dfe='cd /home/harlem/projetos/zipados/openai-xml/dfe-sync && ./start-dfe-api.sh'" >> ~/.bashrc
    echo "alias test-dfe='cd /home/harlem/projetos/zipados/openai-xml/dfe-sync && ./test-dfe-api.sh'" >> ~/.bashrc
    echo "alias dfe-logs='cd /home/harlem/projetos/zipados/openai-xml/dfe-sync && tail -f logs/*.log'" >> ~/.bashrc
    echo "alias dfe-db='psql -h localhost -U dfe -d dfe'" >> ~/.bashrc
    echo "   ✅ Aliases adicionados ao .bashrc"
else
    echo "   ℹ️ Aliases já existem"
fi

# 6. Tornar scripts executáveis
chmod +x start-dfe-api.sh
chmod +x test-dfe-api.sh
chmod +x setup-dfe-environment.sh

echo ""
echo "🎉 SETUP CONCLUÍDO!"
echo "=================="
echo ""
echo "📋 COMANDOS DISPONÍVEIS:"
echo "   start-dfe    # Iniciar API DFe-SEFAZ"
echo "   test-dfe     # Testar API rapidamente"
echo "   dfe-logs     # Ver logs em tempo real"
echo "   dfe-db       # Conectar no banco PostgreSQL"
echo ""
echo "🔄 Para ativar os aliases agora:"
echo "   source ~/.bashrc"
echo ""
echo "🚀 Para iniciar a API:"
echo "   ./start-dfe-api.sh"
echo "   ou simplesmente: start-dfe (após source ~/.bashrc)"