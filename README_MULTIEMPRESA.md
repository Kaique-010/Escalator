# Sistema Multi-Empresa - Escalator

Este documento descreve o sistema multi-empresa implementado no projeto Escalator, que permite que múltiplas empresas utilizem o sistema com dados completamente isolados em bancos de dados separados.

## Arquitetura do Sistema

### Estrutura de Bancos de Dados

1. **Banco Master (`master`)**
   - Armazena informações das empresas cadastradas
   - Contém dados de licenças de todas as empresas
   - Gerencia autenticação e roteamento
   - Tabelas principais: `core_empresa`, `core_licenca`, `core_licencahistorico`

2. **Bancos Individuais (`empresa_{id}`)**
   - Um banco específico para cada empresa
   - Contém todos os dados operacionais da empresa
   - Isolamento completo entre empresas
   - Cópia local dos dados de licença para verificação

### Componentes Principais

#### 1. Database Router (`core/routers.py`)
- **Classe**: `DatabaseRouter`
- **Função**: Determina qual banco usar para cada operação
- **Métodos principais**:
  - `db_for_read()`: Define banco para leitura
  - `db_for_write()`: Define banco para escrita
  - `allow_relation()`: Controla relações entre bancos
  - `allow_migrate()`: Controla migrações por banco

#### 2. Middleware de Roteamento (`core/middleware.py`)
- **Classes**: 
  - `DatabaseRoutingMiddleware`: Roteamento principal
  - `EmpresaSessionMiddleware`: Gerenciamento de sessão
- **Função**: Intercepta requisições e define contexto da empresa
- **Funcionalidades**:
  - Identifica empresa do usuário logado
  - Cria bancos dinamicamente se necessário
  - Gerencia sessão da empresa

#### 3. Sistema de Autenticação (`core/authentication.py`)
- **Backend**: `MultiEmpresaAuthBackend`
- **Funções auxiliares**:
  - `login_multiempresa()`: Login com contexto de empresa
  - `logout_multiempresa()`: Logout limpo
  - `verificar_permissoes_empresa()`: Validação de licença
  - `criar_usuario_empresa()`: Criação de usuários

#### 4. Modelos (`core/models.py`)
- **Empresa**: Dados cadastrais das empresas
- **Licenca**: Informações de licenciamento
- **LicencaHistorico**: Histórico de alterações

## Comandos de Management

### 1. Setup do Sistema (`setup_multiempresa`)
```bash
# Criar e migrar banco master
python manage.py setup_multiempresa --create-master

# Criar banco para empresa específica
python manage.py setup_multiempresa --empresa-id 1

# Criar dados de exemplo
python manage.py setup_multiempresa --create-sample
```

### 2. Sincronização de Licenças (`sync_licencas`)
```bash
# Sincronizar todas as empresas
python manage.py sync_licencas

# Sincronizar empresa específica
python manage.py sync_licencas --empresa-id 1

# Modo dry-run (apenas visualizar)
python manage.py sync_licencas --dry-run

# Forçar sincronização
python manage.py sync_licencas --force
```

### 3. Migração de Dados (`migrate_empresa`)
```bash
# Migrar dados existentes para nova empresa
python manage.py migrate_empresa --empresa-nome "Empresa Teste" --empresa-cnpj "12.345.678/0001-90"

# Especificar banco origem
python manage.py migrate_empresa --empresa-nome "Empresa Teste" --empresa-cnpj "12.345.678/0001-90" --from-database default

# Modo dry-run
python manage.py migrate_empresa --empresa-nome "Empresa Teste" --empresa-cnpj "12.345.678/0001-90" --dry-run
```

### 4. Verificação de Licenças (`check_licencas`)
```bash
# Verificar todas as empresas
python manage.py check_licencas

# Verificar empresa específica
python manage.py check_licencas --empresa-id 1

# Apenas licenças com problemas
python manage.py check_licencas --expired-only

# Saída em JSON
python manage.py check_licencas --json-output

# Personalizar dias de aviso
python manage.py check_licencas --days-warning 15
```

## Configuração

### Settings.py
```python
# Configuração de múltiplos bancos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'master': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'master.sqlite3',
    }
}

# Router de banco de dados
DATABASE_ROUTERS = ['core.routers.DatabaseRouter']

# Backend de autenticação customizado
AUTHENTICATION_BACKENDS = [
    'core.authentication.MultiEmpresaAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Middleware
MIDDLEWARE = [
    # ... outros middlewares
    'core.middleware.DatabaseRoutingMiddleware',
    'core.middleware.EmpresaSessionMiddleware',
]

# Apps instalados
INSTALLED_APPS = [
    # ... outros apps
    'core',
]
```

## Fluxo de Funcionamento

### 1. Login do Usuário
1. Usuário faz login com credenciais
2. Sistema identifica empresa do usuário (`usuario.empresa_id`)
3. Middleware define contexto da empresa na thread
4. Todas as operações subsequentes usam o banco da empresa

### 2. Roteamento de Dados
1. Router intercepta operações de banco
2. Verifica se é modelo do core (usa `master`) ou da empresa
3. Direciona para o banco apropriado
4. Cria banco da empresa se não existir

### 3. Sincronização
1. Dados de licença são mantidos no banco master
2. Comando `sync_licencas` copia dados relevantes para bancos das empresas
3. Verificações de limite são feitas localmente em cada banco

## Tipos de Licença

### Básico
- Até 10 funcionários
- Até 3 usuários
- Funcionalidades básicas

### Profissional
- Até 50 funcionários
- Até 10 usuários
- Banco de horas
- Ponto eletrônico
- Relatórios avançados

### Empresarial
- Funcionários ilimitados
- Até 25 usuários
- Todas as funcionalidades
- Integração API

### Corporativo
- Sem limites
- Todas as funcionalidades
- Suporte prioritário

## Segurança e Isolamento

### Isolamento de Dados
- Cada empresa possui banco próprio
- Impossibilidade de acesso cruzado entre empresas
- Validação de empresa em todas as operações

### Controle de Acesso
- Usuários vinculados a uma única empresa
- Verificação de licença em tempo real
- Bloqueio automático para licenças expiradas

### Auditoria
- Histórico de alterações de licença
- Log de criação de bancos
- Rastreamento de sincronizações

## Manutenção

### Backup
```bash
# Backup do banco master
cp master.sqlite3 master_backup_$(date +%Y%m%d).sqlite3

# Backup de empresa específica
cp empresa_1.sqlite3 empresa_1_backup_$(date +%Y%m%d).sqlite3
```

### Monitoramento
```bash
# Verificar status das licenças diariamente
python manage.py check_licencas --expired-only

# Sincronizar licenças semanalmente
python manage.py sync_licencas
```

### Limpeza
```bash
# Remover bancos de empresas inativas (implementar conforme necessário)
# python manage.py cleanup_inactive_empresas
```

## Troubleshooting

### Problemas Comuns

1. **Banco da empresa não encontrado**
   - Executar: `python manage.py setup_multiempresa --empresa-id X`

2. **Licença não sincronizada**
   - Executar: `python manage.py sync_licencas --empresa-id X --force`

3. **Usuário sem empresa**
   - Verificar campo `empresa_id` no modelo Usuario
   - Associar usuário a uma empresa válida

4. **Erro de migração**
   - Verificar se banco master foi criado
   - Executar migrações específicas por banco

### Logs Importantes
- Criação de bancos: `core.routers.create_empresa_database`
- Roteamento: `core.routers.DatabaseRouter`
- Autenticação: `core.authentication.MultiEmpresaAuthBackend`

## Próximos Passos

1. Implementar interface administrativa para gerenciar empresas
2. Criar sistema de cobrança automática
3. Adicionar métricas de uso por empresa
4. Implementar backup automático
5. Criar sistema de notificações para vencimento de licenças