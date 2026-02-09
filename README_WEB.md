# Sistema de Exportação Bitrix24 - Aplicação Web

Sistema web para exportar tarefas do Bitrix24 via REST API (webhook) para Excel, com interface web, autenticação e controle de acesso por departamento.

## 🚀 Características

- **Interface Web**: Acesso via navegador, sem necessidade de linha de comando
- **Autenticação**: Sistema de login com diferentes níveis de acesso
- **Controle de Acesso**: Administradores e supervisores com permissões por departamento
- **Filtros Avançados**: Por departamento, colaborador, período e status
- **Exportação Excel**: Geração automática de relatórios em Excel

## 👥 Usuários do Sistema

### Administradores (Acesso Total)
- **Juliana Paes** - `juliana.paes`
- **Mateus Souza** - `mateus.souza`

### Supervisores (Acesso por Departamento)
- **Tayla Ferreira** - `tayla.ferreira` (Departamento: RNA)
- **Rafael Reimão** - `rafael.reimao` (Departamento: DTC)
- **Deborah Szajin** - `deborah.szajin` (Departamento: COMERCIAL)

**Senha padrão para todos:** `bitrix2024` (⚠️ **ALTERE EM PRODUÇÃO!**)

## 📋 Requisitos

- Python 3.8 ou superior
- Webhook do Bitrix24 com permissões de leitura (read-only)
- Planilha Excel "Planilha de colaboradores.xlsx" com as colunas:
  - `IDs` (ID do usuário no Bitrix, numérico)
  - `Colaboradores` (nome do colaborador)
  - `Departamentos` (nome do departamento)

## 🔧 Instalação Local

1. **Clone o repositório:**
   ```bash
   git clone <seu-repositorio>
   cd bitrix-exporter
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure o webhook do Bitrix24:**
   - Copie o arquivo `.env.example` para `.env`:
     ```bash
     copy .env.example .env
     ```
   - Edite o arquivo `.env` e adicione sua URL do webhook:
     ```
     BITRIX_WEBHOOK_BASE=https://seu-portal.bitrix24.com.br/rest/1/webhook_token/
     SESSION_SECRET=sua-chave-secreta-aleatoria-aqui
     ```

4. **Coloque a planilha "Planilha de colaboradores.xlsx" no diretório do projeto**

5. **Execute a aplicação:**
   ```bash
   python app.py
   ```
   Ou usando uvicorn diretamente:
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Acesse no navegador:**
   ```
   http://localhost:8000
   ```

## 🌐 Deploy em Servidor Gratuito

### Opção 1: Render.com (Recomendado)

1. **Crie uma conta em [Render.com](https://render.com)**

2. **Conecte seu repositório GitHub:**
   - Vá em "New" → "Web Service"
   - Conecte seu repositório
   - Render detectará automaticamente o `render.yaml`

3. **Configure as variáveis de ambiente:**
   - `BITRIX_WEBHOOK_BASE`: URL do seu webhook Bitrix24
   - `SESSION_SECRET`: Chave secreta para sessões (Render pode gerar automaticamente)

4. **Faça upload da planilha:**
   - Após o deploy, você precisará fazer upload da planilha "Planilha de colaboradores.xlsx"
   - Ou configure para usar um serviço de armazenamento (S3, etc.)

5. **Deploy automático:**
   - Render fará deploy automaticamente a cada push no GitHub

### Opção 2: Railway.app

1. **Crie uma conta em [Railway.app](https://railway.app)**

2. **Conecte seu repositório**

3. **Configure variáveis de ambiente** (mesmas do Render)

4. **Railway detectará automaticamente o Dockerfile ou Procfile**

### Opção 3: Heroku

1. **Instale o Heroku CLI**

2. **Crie um app:**
   ```bash
   heroku create seu-app-name
   ```

3. **Configure variáveis de ambiente:**
   ```bash
   heroku config:set BITRIX_WEBHOOK_BASE=https://seu-webhook
   heroku config:set SESSION_SECRET=sua-chave-secreta
   ```

4. **Faça deploy:**
   ```bash
   git push heroku main
   ```

## 🔐 Segurança

⚠️ **IMPORTANTE ANTES DO DEPLOY:**

1. **Altere as senhas padrão** em `users_config.py`:
   ```python
   # Gere novos hashes de senha
   from users_config import hash_password
   print(hash_password("sua-nova-senha-forte"))
   ```

2. **Configure SESSION_SECRET** forte no `.env` ou variáveis de ambiente

3. **Use HTTPS** em produção (Render e Railway fornecem automaticamente)

4. **O sistema é read-only** - não modifica dados no Bitrix24

## 📊 Como Usar

1. **Acesse a aplicação** no navegador
2. **Faça login** com seu usuário e senha
3. **Configure os filtros:**
   - Departamento (supervisores só veem seus departamentos)
   - Colaborador (opcional)
   - Período de atividade (opcional)
   - Status (opcional)
4. **Clique em "Exportar para Excel"**
5. **Aguarde o processamento** (pode levar alguns minutos)
6. **Baixe o arquivo Excel** gerado

## 🏗️ Estrutura do Projeto

```
bitrix-exporter/
├── app.py                      # Aplicação FastAPI principal
├── auth.py                     # Sistema de autenticação
├── users_config.py             # Configuração de usuários
├── web_services.py             # Serviços web (lógica de exportação)
├── bitrix_client.py            # Cliente HTTP para API Bitrix24
├── config.py                   # Configurações
├── excel_handler.py            # Manipulação de arquivos Excel
├── task_processor.py           # Processamento de tarefas
├── time_entries_handler.py     # Processamento de lançamentos de tempo
├── main.py                     # CLI (mantido para compatibilidade)
├── templates/                  # Templates HTML
│   ├── login.html
│   └── dashboard.html
├── static/                     # Arquivos estáticos
│   └── css/
│       └── style.css
├── requirements.txt            # Dependências Python
├── .env                        # Variáveis de ambiente (não versionado)
├── Procfile                    # Para deploy Heroku/Railway
├── runtime.txt                 # Versão Python
├── render.yaml                 # Configuração Render.com
└── Dockerfile                  # Para deploy Docker
```

## 🐛 Troubleshooting

**Erro: "BITRIX_WEBHOOK_BASE não encontrado"**
- Verifique se o arquivo `.env` existe e contém a variável

**Erro: "Arquivo não encontrado: Planilha de colaboradores.xlsx"**
- Certifique-se de que a planilha está no diretório raiz do projeto

**Erro de autenticação**
- Verifique se está usando o username correto (ex: `juliana.paes`)
- Senha padrão: `bitrix2024`

**Erro 403 ao exportar**
- Supervisores só podem exportar tarefas de seus departamentos
- Verifique se o departamento selecionado está na lista de permissões

## 📝 Notas

- O sistema mantém a funcionalidade CLI original em `main.py`
- A planilha de colaboradores deve estar sempre atualizada
- Exportações grandes podem levar vários minutos
- O sistema trata erros automaticamente e continua processando

## 📄 Licença

Este projeto é fornecido "como está", sem garantias.
