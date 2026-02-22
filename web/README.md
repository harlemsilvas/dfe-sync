# Frontend - DFe Sync Web

Interface web para gerenciamento e visualização de documentos fiscais eletrônicos.

## 🛠️ Tecnologias

- **React 18** - Biblioteca UI
- **TypeScript** - Tipagem estática
- **Vite** - Build tool e dev server
- **CSS Vanilla** - Estilos inline no HTML

## 📁 Estrutura

```
web/
├── public/              # Arquivos estáticos (servidos diretamente)
│   └── favicon.ico     # ✅ Ícone da aplicação
├── src/
│   ├── api/            # Chamadas à API backend
│   ├── components/     # Componentes React
│   ├── pages/          # Páginas da aplicação
│   ├── App.tsx         # Componente raiz
│   └── main.tsx        # Entry point
├── index.html          # HTML principal (com favicon configurado)
├── package.json        # Dependências e scripts
├── tsconfig.json       # Configuração TypeScript
└── vite.config.ts      # Configuração Vite + Proxy API
```

## 🚀 Comandos

### Desenvolvimento

```bash
cd web

# Instalar dependências (primeira vez)
npm install

# Iniciar dev server
npm run dev
# Abre em http://localhost:5173
```

### Build de Produção

```bash
cd web

# Build otimizado
npm run build
# Gera arquivos em web/dist/

# Preview do build
npm run preview
```

## 🔗 Proxy API

O Vite está configurado para fazer proxy das requisições `/api` para o backend FastAPI:

```typescript
// vite.config.ts
server: {
  port: 5173,
  proxy: {
    "/api": {
      target: "http://localhost:8001",  // Backend FastAPI
      changeOrigin: true,
      secure: false,
    },
  },
}
```

**Exemplo de uso:**
```typescript
// Frontend faz requisição para /api/empresas
fetch('/api/empresas')
// Vite redireciona para http://localhost:8001/api/empresas
```

## 🎨 Favicon

O favicon está configurado corretamente:

**Localização:** `web/public/favicon.ico`

**Referência no HTML:**
```html
<link rel="icon" type="image/x-icon" href="/favicon.ico" />
```

**Como o Vite funciona:**
- Arquivos em `public/` são copiados para a raiz do build
- Durante dev: servidos diretamente de `/public`
- Após build: copiados para `/dist`

## 📦 Estrutura de Build

Após `npm run build`:

```
web/dist/
├── index.html
├── favicon.ico         # ✅ Copiado automaticamente
├── assets/
│   ├── index-[hash].js
│   └── index-[hash].css
```

## 🔧 Desenvolvimento Local

### 1. Iniciar Backend
```bash
# Terminal 1: Backend FastAPI
cd /path/to/dfe-sync
./start-api.sh
# Rodando em http://localhost:8001
```

### 2. Iniciar Frontend
```bash
# Terminal 2: Frontend Vite
cd web
npm run dev
# Rodando em http://localhost:5173
```

### 3. Acessar
- Frontend: http://localhost:5173
- Backend API: http://localhost:8001/docs (Swagger)
- Health Check: http://localhost:8001/health

## 🌐 Deploy em Produção

### Opção 1: Build Estático + Nginx

```bash
# 1. Build do frontend
cd web
npm run build

# 2. Copiar dist para servidor web
cp -r dist/* /var/www/dfe-sync/

# 3. Configurar Nginx
# Ver exemplo de configuração abaixo
```

**Exemplo nginx.conf:**
```nginx
server {
    listen 80;
    server_name dfe-sync.exemplo.com;

    # Frontend (arquivos estáticos)
    root /var/www/dfe-sync;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy para API backend
    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Opção 2: FastAPI servindo frontend

```python
# src/api/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# API routes
app.include_router(...)

# Servir frontend buildado
app.mount("/", StaticFiles(directory="web/dist", html=True), name="static")
```

## 🧪 Testes

```bash
cd web

# (Adicionar após configurar testes)
npm test
```

## 🔍 Troubleshooting

### Favicon não aparece

1. **Limpar cache do navegador:**
   - Chrome: Ctrl+Shift+Delete
   - Firefox: Ctrl+Shift+Delete

2. **Verificar arquivo existe:**
   ```bash
   ls -lh web/public/favicon.ico
   ```

3. **Forçar reload:**
   - Abrir DevTools (F12)
   - Clicar com botão direito em Reload
   - "Empty Cache and Hard Reload"

### Erro de CORS

Se houver erro de CORS ao chamar API:

```python
# src/api/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Proxy não funciona

Verificar se backend está rodando:
```bash
curl http://localhost:8001/health
```

Se backend não responde, iniciar com:
```bash
cd /path/to/dfe-sync
./start-api.sh
```

## 📚 Recursos

- [Vite Docs](https://vitejs.dev/)
- [React Docs](https://react.dev/)
- [TypeScript Docs](https://www.typescriptlang.org/)
- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)

## 🎯 Próximos Passos

- [ ] Adicionar testes (Jest + React Testing Library)
- [ ] Configurar ESLint + Prettier
- [ ] Adicionar CI/CD para build automático
- [ ] Implementar PWA (Service Worker)
- [ ] Adicionar mais meta tags (SEO)
