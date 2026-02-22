# ✅ Favicon Configurado - DFe Sync

## 📍 Localização

```
dfe-sync/
├── assets/
│   └── favicon.ico          # ❌ Localização antiga (fonte)
└── web/
    └── public/
        └── favicon.ico      # ✅ Localização correta (Vite)
```

## 🔧 Configuração Aplicada

### 1. Arquivo Movido
```bash
# Copiado de assets/ para web/public/
cp assets/favicon.ico web/public/favicon.ico
```

### 2. HTML Atualizado
Adicionado no `web/index.html`:
```html
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/x-icon" href="/favicon.ico" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  ...
</head>
```

### 3. Como Funciona no Vite
- **Desenvolvimento** (`npm run dev`): Vite serve arquivos de `public/` na raiz
- **Build** (`npm run build`): Vite copia `public/` para `dist/`
- **URL Final**: `http://localhost:5173/favicon.ico`

## 🚀 Como Usar

### Verificar Configuração
```bash
./scripts-dev/frontend.sh check
```

### Iniciar Frontend
```bash
cd web
npm run dev
# ou
./scripts-dev/frontend.sh dev
```

### Build de Produção
```bash
cd web
npm run build
# ou
./scripts-dev/frontend.sh build
```

## 🧪 Testar Favicon

### 1. Iniciar Backend + Frontend
```bash
# Terminal 1: Backend
./start-api.sh

# Terminal 2: Frontend
./scripts-dev/frontend.sh dev
```

### 2. Acessar
Abrir navegador em: http://localhost:5173

### 3. Verificar
- Aba do navegador deve mostrar o ícone
- DevTools > Network > filtrar "favicon.ico" (deve retornar 200)

### 4. Forçar Reload (se necessário)
- Chrome: Ctrl+Shift+Delete > "Cached images and files"
- Ou: F12 > Network > Desabilitar cache > Ctrl+F5

## 📁 Estrutura Completa do Frontend

```
web/
├── public/                 # Arquivos servidos diretamente
│   └── favicon.ico        # ✅ Ícone da aplicação (15KB)
├── src/
│   ├── api/               # Integração com backend
│   ├── components/        # Componentes React
│   ├── pages/             # Páginas
│   ├── App.tsx
│   └── main.tsx
├── dist/                  # Build de produção (após npm run build)
│   ├── index.html
│   ├── favicon.ico       # ✅ Copiado automaticamente
│   └── assets/
├── index.html            # HTML principal
├── package.json
├── tsconfig.json
└── vite.config.ts        # Proxy API configurado

Scripts auxiliares:
└── scripts-dev/
    └── frontend.sh       # Helper para gerenciar frontend
```

## 🔍 Comandos Úteis

### Script Helper
```bash
# Ver ajuda
./scripts-dev/frontend.sh help

# Verificar status
./scripts-dev/frontend.sh check

# Instalar dependências
./scripts-dev/frontend.sh install

# Desenvolvimento
./scripts-dev/frontend.sh dev

# Build produção
./scripts-dev/frontend.sh build

# Preview do build
./scripts-dev/frontend.sh preview

# Limpar tudo
./scripts-dev/frontend.sh clean
```

### Comandos npm Diretos
```bash
cd web

# Desenvolvimento
npm run dev         # http://localhost:5173

# Build
npm run build       # Gera dist/

# Preview
npm run preview     # http://localhost:4173
```

## 🌐 Proxy API

O frontend está configurado para fazer proxy de `/api` para o backend:

```typescript
// web/vite.config.ts
proxy: {
  "/api": {
    target: "http://localhost:8001",
    changeOrigin: true,
  },
}
```

**Uso no código:**
```typescript
// Requisições para /api/empresas são redirecionadas para http://localhost:8001/api/empresas
fetch('/api/empresas')
  .then(res => res.json())
  .then(data => console.log(data));
```

## 📝 Documentação

- **Frontend completo:** `web/README.md`
- **Scripts de dev:** `scripts-dev/README.md`

## ✅ Checklist de Verificação

- [x] Favicon copiado para `web/public/favicon.ico`
- [x] Link adicionado no `web/index.html`
- [x] Script helper `frontend.sh` criado
- [x] Documentação `web/README.md` criada
- [x] Proxy API configurado no Vite
- [x] Comandos testados e funcionando

## 🎯 Resultado

**Favicon está agora corretamente configurado no frontend Vite/React!**

Quando você rodar `npm run dev` ou fazer o build, o favicon será automaticamente servido e aparecerá na aba do navegador.

---

**Última atualização:** 13/11/2025
