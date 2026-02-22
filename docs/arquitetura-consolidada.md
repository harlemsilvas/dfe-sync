# 🏗️ Arquitetura Consolidada - PostgreSQL Docker

## 🎯 **Decisão Arquitetural**

✅ **MIGRAÇÃO COMPLETA PARA POSTGRESQL DOCKER**

- ❌ Remover SQLite/DB locais
- ❌ Eliminar redundâncias
- ✅ Centralizar tudo no PostgreSQL container
- ✅ Backup automático via volumes Docker

## 🐳 **Infraestrutura Docker**

### Container PostgreSQL

```yaml
services:
  db:
    image: postgres:16
    container_name: dfe_db
    environment:
      POSTGRES_USER: dfe
      POSTGRES_PASSWORD: dfe
      POSTGRES_DB: dfe
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
```

### Conexão Unificada

```
postgresql://dfe:dfe@localhost:5432/dfe
```

## 📊 **Estrutura de Dados Consolidada**

### Tabelas Core (✅ Criadas)

- `empresas` - Empresas monitoradas (HRM: 19330326000105, ABC: 51309435000153)
- `tipo_documento` - 7 tipos (NFE_ENTRADA, NFE_SAIDA, NFE_TERCEIROS, NFE_TRANSFERENCIA, CTE, NFSE, EVENTO)
- `dfe_documentos` - Documentos processados com metadados completos
- `certificados` - Unificada (arquivo + BYTEA), compatível com sistema existente
- `cursor_dfe` - Controle de NSU por empresa

### Tabelas de Processamento (✅ Criadas)

- `remetentes_cadastrados` - CNPJs/CPFs de terceiros
- `cfops_transferencia` - CFOPs para classificação (5949, 5152, 6152, 5409, 6409)
- `operacoes_pendentes` - Documentos que precisam classificação manual
- `logs_processamento` - Logs estruturados JSON

## 🔄 **Fluxo de Processamento**

```mermaid
graph TD
    A[Diretórios Windows] --> B[Scanner Recursivo]
    B --> C[Extrator ZIP/RAR/7Z]
    C --> D[Classificador XML]
    D --> E[Organizador Pastas]
    E --> F[PostgreSQL Docker]
    F --> G[Dashboard Web]
```

## 📁 **Estrutura de Arquivos**

```
/storage/empresas/{cnpj}/{ano-mes}/{tipo}/
├── 19330326000105/  # HRM
├── 51309435000153/  # ABC
└── temp/            # Processamento temporário
```

## 🚀 **Vantagens da Consolidação**

### ✅ **Benefícios**

- **Backup Automático**: Volumes Docker persistentes
- **Performance**: PostgreSQL otimizado para consultas complexas
- **Escalabilidade**: Container pode ser replicado/clusterizado
- **Manutenção**: Rollback via snapshots Docker
- **Desenvolvimento**: Ambiente isolado e reproduzível
- **Integridade**: Transações ACID, constraints FK

### ❌ **Eliminado**

- SQLite local (limitações de concorrência)
- Arquivos de log individuais (PostgreSQL centraliza)
- Configurações locais espalhadas
- Dependências de paths específicos

## 🔧 **Comandos Essenciais**

### Iniciar Sistema

```bash
cd /mnt/c/Projetos/dfe-sync
docker-compose up -d db
source .venv/bin/activate
```

### Backup/Restore

```bash
# Backup
docker exec dfe_db pg_dump -U dfe dfe > backup.sql

# Restore
docker exec -i dfe_db psql -U dfe dfe < backup.sql
```

### Logs do Sistema

```bash
# Logs do container
docker logs dfe_db

# Logs da aplicação (via PostgreSQL)
psql postgresql://dfe:dfe@localhost:5432/dfe
SELECT * FROM logs_processamento ORDER BY timestamp DESC LIMIT 50;
```

## 📊 **Status Atual**

### ✅ **Implementado**

- PostgreSQL 16 containerizado
- Todas as tabelas criadas e indexadas
- Empresas monitoradas configuradas (HRM + ABC)
- Tipos de documento e CFOPs carregados
- Sistema de logs estruturado funcionando
- Extrator de arquivos validado

### 🚀 **Próximo**

- Classificador XML (usando base consolidada)
- Organizador de pastas
- Dashboard web
- Processamento em produção

## 🔒 **Segurança & Backup**

### Volumes Docker

- `pgdata:/var/lib/postgresql/data` - Dados persistentes
- Backup automático via snapshots do volume

### Conexões

- Apenas localhost (container isolado)
- Credenciais via `.env`
- SSL disponível para produção

---

**🎉 Sistema completamente consolidado no PostgreSQL Docker!**
**🚀 Pronto para processamento de arquivos em grande escala!**
