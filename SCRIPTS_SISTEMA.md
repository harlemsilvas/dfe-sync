# 🚀 Scripts de Gerenciamento do Sistema DFE Sync

## 📋 **Scripts Disponíveis**

O sistema agora possui scripts automatizados para facilitar o gerenciamento do backend e frontend:

### 🎯 **Script Principal - Sistema Completo**

```bash
./start-sistema-completo.sh
```

**Inicia tudo junto**: Backend (FastAPI) + Frontend (Vite React) + PostgreSQL

**URLs após inicialização:**

- 🌐 **Frontend React**: http://localhost:5173 (Sistema antigo recuperado!)
- 📊 **Dashboard HTML**: http://localhost:3000/dashboard.html
- 🔗 **API Docs**: http://localhost:8001/docs
- 🔗 **API Redoc**: http://localhost:8001/redoc

---

### ⚙️ **Scripts Individuais**

#### Backend (FastAPI)

```bash
./start-backend.sh
```

- Inicia apenas a API na porta 8001
- Ativa ambiente virtual automaticamente
- Verifica/inicia PostgreSQL Docker

#### Frontend (Vite React)

```bash
./start-frontend.sh
```

- Inicia apenas o frontend na porta 5173
- Instala dependências npm se necessário
- **Recupera o sistema antigo que estava perdido!**

#### Parar Sistema

```bash
./stop-sistema.sh
```

- Para todos os serviços (Backend + Frontend + Dashboard)
- Mata processos em todas as portas (8001, 5173, 3000)
- Limpeza completa do sistema

---

## 🔍 **Sistema Antigo Recuperado - Frontend React**

O sistema antigo que rodava no Vite (porta 5173) foi **encontrado e recuperado**!

### 📁 **Localização**:

```
dfe-sync/web/
├── package.json       # Configurações npm
├── vite.config.ts     # Configuração Vite com proxy para API
├── src/
│   ├── App.js         # Componente principal
│   ├── main.tsx       # Entry point
│   ├── pages/
│   │   └── Home.tsx   # Página principal com consulta NF-e
│   ├── components/    # Componentes React
│   └── api/           # Cliente da API
```

### 🎯 **Funcionalidades do Frontend React**:

- ✅ **Consulta pública de NF-e SP**
- ✅ **Busca por chave de acesso** (44 dígitos)
- ✅ **Consulta DF-e** via API backend
- ✅ **Download de XMLs** processados
- ✅ **Interface moderna** com React + TypeScript
- ✅ **Proxy configurado** para API backend (porta 8001)

---

## 🚀 **Como Usar o Sistema Completo**

### **Opção 1: Sistema Completo (Recomendado)**

```bash
# Navegar para o diretório
cd /mnt/c/Projetos/dfe-sync

# Iniciar tudo junto
./start-sistema-completo.sh

# Aguardar inicialização (30-60 segundos)
# Acessar URLs disponíveis
```

### **Opção 2: Serviços Separados**

```bash
# Terminal 1: Backend
./start-backend.sh

# Terminal 2: Frontend
./start-frontend.sh

# Para parar
./stop-sistema.sh
```

---

## 📊 **Comparação dos Frontends**

| Característica     | Frontend React (5173)     | Dashboard HTML (3000)     |
| ------------------ | ------------------------- | ------------------------- |
| **Tecnologia**     | React + TypeScript + Vite | HTML + CSS + JavaScript   |
| **Funcionalidade** | Consulta NF-e + DF-e      | Dashboard + Classificação |
| **Público**        | Consulta pública SP       | Sistema interno           |
| **Estado**         | Sistema antigo recuperado | Sistema novo criado       |
| **Uso**            | Consultas externas        | Monitoramento interno     |

---

## 🎯 **URLs de Acesso Rápido**

### **Frontend React (Sistema Antigo Recuperado)**

- 🌐 http://localhost:5173
- 🎯 **Funcionalidade**: Consulta pública de NF-e SP
- 📋 **Recursos**: Busca por chave, download XML, consulta DF-e

### **Dashboard HTML (Sistema Novo)**

- 📊 http://localhost:3000/dashboard.html
- 🎯 **Funcionalidade**: Gerenciamento do sistema de classificação
- 📋 **Recursos**: Gráficos, estatísticas, operações pendentes

### **API REST**

- 🔗 http://localhost:8001/docs (Swagger)
- 🔗 http://localhost:8001/redoc (Redoc)
- 🎯 **Funcionalidade**: API completa para integração

---

## 🛠️ **Configuração do Proxy**

O Frontend React está configurado para se comunicar com a API:

```typescript
// web/vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8001",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
```

---

## 🎉 **Sistema Completo Operacional**

Agora você tem **dois frontends funcionais**:

1. 🌐 **Frontend React** (porta 5173) - Sistema antigo recuperado para consultas públicas
2. 📊 **Dashboard HTML** (porta 3000) - Sistema novo para gerenciamento interno

**Ambos se comunicam com a mesma API REST** (porta 8001) e compartilham o banco PostgreSQL.

### **Para iniciar tudo:**

```bash
./start-sistema-completo.sh
```

### **Para parar tudo:**

```bash
./stop-sistema.sh
```

🚀 **O sistema antigo foi encontrado e está 100% operacional novamente!**
