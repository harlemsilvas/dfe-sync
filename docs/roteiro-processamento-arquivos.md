# 📋 Roteiro - Sistema de Processamento de Arquivos Fiscais

## 🎯 Objetivo
Criar sistema automatizado para processar arquivos compactados contendo documentos fiscais (NF-e, CT-e, NFS-e), organizá-los por empresa/período/tipo e armazenar metadados no banco de dados.

## 📁 Estrutura Implementada

### Diretórios de Origem (Windows)
- `C:\Users\harle\Desktop\contabilidade\hrm\` 
- `C:\Users\harle\Desktop\contabilidade\abc\`

### Estrutura de Destino (WSL)
```
/storage/empresas/{cnpj}/{ano-mes}/{tipo}/
├── 51309435000153/
│   ├── 2024-11/
│   │   ├── nfe-entrada/     ← NF-e onde empresa é destinatária
│   │   ├── nfe-saida/       ← NF-e onde empresa é emissora  
│   │   ├── nfe-terceiros/   ← NF-e onde empresa não participa
│   │   ├── nfe-transferencia/ ← NF-e de transferência entre filiais
│   │   ├── cte/             ← Conhecimentos de transporte
│   │   ├── nfse/            ← Notas fiscais de serviços
│   │   └── eventos/         ← Eventos relacionados aos documentos
│   └── 2024-12/
└── 42580092002977/
```

## 🗄️ Banco de Dados

### Tabela `tipo_documento` ✅ CRIADA
- `id`: Chave primária
- `codigo`: NFE_ENTRADA, NFE_SAIDA, NFE_TERCEIROS, NFE_TRANSFERENCIA, CTE, NFSE, EVENTO
- `descricao`: Descrição legível
- `ativo`: Flag ativo/inativo

### Tabela `dfe_documentos` ✅ EXPANDIDA
**Campos Originais:**
- `id`, `empresa_id`, `nsu`, `schema`, `chave`, `caminho_xml`, `created_at`

**Novos Campos:**
- `tipo_documento_id`: FK para tipo_documento
- `cnpj_emissor`: CNPJ do emitente
- `cnpj_destinatario`: CNPJ do destinatário
- `data_emissao`: Data de emissão do documento
- `valor_total`: Valor total do documento
- `numero_documento`: Número da NF-e/CT-e
- `serie`: Série do documento
- `modelo`: Modelo (55=NF-e, 57=CT-e)
- `natureza_operacao`: Natureza da operação
- `arquivo_origem`: Caminho do ZIP original

## 🔄 Fluxo de Processamento Planejado

### 1. Scanner de Arquivos
- Ler recursivamente diretórios Windows via WSL
- Identificar arquivos ZIP/RAR/7Z
- Manter controle de arquivos já processados

### 2. Extrator 
- Descompactar arquivos em diretório temporário
- Validar conteúdo (XML válido)
- Listar arquivos extraídos

### 3. Analisador XML
- Parser XML para extrair metadados
- Identificar tipo de documento (modelo)
- Extrair CNPJs, datas, valores, chaves

### 4. Classificador
- Aplicar regras de negócio para determinar tipo
- Considerar empresa monitorada vs terceiros
- Detectar transferências por CFOP/natureza

### 5. Organizador
- Criar estrutura de diretórios por CNPJ/período
- Mover XMLs para local correto
- Evitar duplicatas (verificar por chave)

### 6. Persistência
- Registrar metadados no banco
- Vincular com empresas existentes
- Manter histórico de processamento

## 🤔 Perguntas Pendentes para Refinamento

### Critérios de Classificação
1. **NF-e Entrada**: CNPJ destinatário = empresa monitorada?
2. **NF-e Saída**: CNPJ emissor = empresa monitorada?
3. **NF-e Terceiros**: Nenhum CNPJ = empresa monitorada?
4. **NF-e Transferência**: Baseado em CFOP ou natureza operação?

### Tratamento de Duplicatas
1. Como lidar com mesmo XML em múltiplos ZIPs?
2. Verificar por chave de acesso antes de processar?
3. Manter controle de origem (qual ZIP)?

### Performance e Monitoramento
1. Processar em lotes ou arquivo por arquivo?
2. Paralelização para múltiplas empresas?
3. Dashboard web para progresso?
4. Logs detalhados de erros/sucessos?

### Empresas Monitoradas
1. Quais CNPJs considerar como "nossas empresas"?
2. Criar tabela de CNPJs monitorados?
3. Como lidar com filiais/matriz?

## ✅ Status Atual

### Concluído
- ✅ Estrutura de diretórios definida
- ✅ Schema do banco criado  
- ✅ Tabela tipo_documento com tipos padrão
- ✅ Campos expandidos em dfe_documentos
- ✅ Módulo estrutura_arquivos.py

### Próximos Passos
1. Aguardar respostas das perguntas de refinamento
2. Implementar scanner de arquivos Windows
3. Criar extrator de arquivos compactados
4. Desenvolver parser XML e classificador
5. Implementar organizador e persistência
6. Criar interface de monitoramento

## 📊 Estimativa de Benefícios
- **Organização**: Documentos estruturados por empresa/período/tipo
- **Busca**: Localização rápida via banco de dados
- **Automação**: Redução manual de classificação
- **Auditoria**: Rastreabilidade completa de origem
- **Performance**: Índices otimizados para consultas

---
*Aguardando definições de regras de negócio para prosseguir com implementação.*