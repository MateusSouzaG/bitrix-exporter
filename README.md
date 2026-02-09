# Sistema de Exportação de Tarefas Bitrix24

Sistema Python para exportar tarefas do Bitrix24 via REST API (webhook) para Excel, com suporte a filtros por departamento/colaborador, status, período de atividade, e detalhamento de lançamentos de tempo por pessoa.

## Requisitos

- Python 3.8 ou superior
- Webhook do Bitrix24 com permissões de leitura (read-only)
- Planilha Excel "Planilha de colaboradores.xlsx" com as colunas:
  - `IDs` (ID do usuário no Bitrix, numérico)
  - `Colaboradores` (nome do colaborador)
  - `Departamentos` (nome do departamento)

## Instalação

1. Clone ou baixe este repositório
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Configure o webhook do Bitrix24:

   - Copie o arquivo `.env.example` para `.env`:
   ```bash
   copy .env.example .env
   ```

   - Edite o arquivo `.env` e adicione sua URL do webhook:
   ```
   BITRIX_WEBHOOK_BASE=https://seu-portal.bitrix24.com.br/rest/1/webhook_token/
   ```

4. Coloque a planilha "Planilha de colaboradores.xlsx" no diretório do projeto

## Uso

### Exemplos Básicos

**Exportar todas as tarefas de todos os colaboradores:**
```bash
python main.py
```

**Filtrar por departamento:**
```bash
python main.py --dept COMERCIAL
```

**Filtrar por colaborador (substring do nome):**
```bash
python main.py --user "João"
```

**Filtrar por período de atividade:**
```bash
python main.py --active-from "2024-01-01T00:00:00-03:00" --active-to "2024-12-31T23:59:59-03:00"
```

**Filtrar por status:**
```bash
python main.py --status IN_PROGRESS
```

**Combinar múltiplos filtros:**
```bash
python main.py --dept DTC --active-from "2024-01-01T00:00:00-03:00" --status NEW
```

**Especificar arquivo de entrada e saída:**
```bash
python main.py --input "minha_planilha.xlsx" --output "resultado.xlsx"
```

### Opções da CLI

- `--dept <NOME>`: Filtrar por departamento (ex: COMERCIAL, DTC, GI, RNA)
- `--user "<substring>"`: Filtrar por colaborador (substring do nome, case-insensitive)
- `--active-from "<ISO8601>"`: Filtro de data inicial para "Estava ativo"
- `--active-to "<ISO8601>"`: Filtro de data final para "Estava ativo"
- `--status <STATUS>`: Filtro de status (ex: NEW, IN_PROGRESS, COMPLETED). Omitir para trazer todos
- `--input <path>`: Caminho para a planilha de colaboradores (padrão: "Planilha de colaboradores.xlsx")
- `--output <path>`: Caminho do arquivo Excel de saída (padrão: Exportacao_Tarefas_YYYYMMDD_HHMMSS.xlsx)

### Prioridade de Filtros

1. Se `--user` for fornecido, ignora `--dept`
2. Se apenas `--dept` for fornecido, filtra por departamento
3. Se nenhum for fornecido, usa todos os colaboradores da planilha

### Formato de Data

As datas devem estar no formato ISO8601. Se você não especificar o timezone, o sistema assumirá "-03:00" (Brasil).

Exemplos:
- `2024-01-01T00:00:00-03:00` (com timezone)
- `2024-01-01T00:00:00` (sem timezone, será adicionado -03:00 automaticamente)

## Estrutura do Excel de Saída

O arquivo Excel gerado contém uma aba "Tarefas" com as seguintes colunas:

- **Task_ID**: ID único da tarefa
- **Título**: Título da tarefa
- **Status**: Status da tarefa
- **Deadline**: Data limite (se houver)
- **Responsável**: Nome do responsável pela tarefa
- **Participantes**: Nomes dos participantes (separados por vírgula)
- **Seu_time_envolvido**: Nomes das pessoas do escopo que aparecem na tarefa
- **Tempo_Total_Gasto**: Soma total de tempo gasto na tarefa (formato: "2h 30min")
- **Tempo_Lançamento**: Tempo do lançamento individual (uma linha por lançamento)
- **Quem_Lançou**: Nome de quem fez o lançamento de tempo
- **Comentário_Lançamento**: Comentário do lançamento de tempo
- **Departamentos_Selecionados**: Departamentos de todas as pessoas envolvidas
- **Atividade_em**: Data da última atividade (ACTIVITY_DATE)

### Observações Importantes

- **Múltiplas linhas por tarefa**: Se uma tarefa tiver múltiplos lançamentos de tempo, cada lançamento gerará uma linha no Excel. Os dados básicos da tarefa (Título, Status, etc.) serão repetidos em cada linha.
- **Deduplicação**: As tarefas são deduplicadas por Task_ID antes de buscar detalhes, mas podem aparecer múltiplas vezes no Excel se houver múltiplos lançamentos de tempo.
- **Lançamentos de tempo**: Todos os lançamentos de tempo de todas as pessoas são incluídos (sem filtro adicional por pessoa do escopo).

## Segurança

⚠️ **IMPORTANTE**: Este sistema é **read-only** e não modifica nenhum dado no Bitrix24. Ele apenas lê informações via API REST.

- Nenhuma tarefa é criada, modificada ou deletada
- Nenhum lançamento de tempo é alterado
- Apenas operações de leitura são realizadas

Certifique-se de usar um webhook com permissões mínimas (read-only) para maior segurança.

## Tratamento de Erros

O sistema trata automaticamente:
- Timeouts de rede (com retry automático)
- Erros da API Bitrix24
- Tarefas não encontradas
- Lançamentos de tempo ausentes
- IDs de usuários não encontrados na planilha (mostra como "USER_<id>")

## Estrutura do Projeto

```
bitrix-exporter/
├── .env                          # Configuração do webhook (não versionado)
├── .env.example                  # Exemplo de configuração
├── .gitignore                    # Arquivos ignorados pelo Git
├── requirements.txt              # Dependências Python
├── config.py                     # Carregamento de configurações
├── bitrix_client.py              # Cliente HTTP para API Bitrix24
├── excel_handler.py              # Manipulação de arquivos Excel
├── task_processor.py             # Processamento de tarefas
├── time_entries_handler.py       # Processamento de lançamentos de tempo
├── main.py                       # CLI principal
└── README.md                     # Este arquivo
```

## Troubleshooting

**Erro: "BITRIX_WEBHOOK_BASE não encontrado"**
- Verifique se o arquivo `.env` existe e contém a variável `BITRIX_WEBHOOK_BASE`

**Erro: "Arquivo não encontrado: Planilha de colaboradores.xlsx"**
- Verifique se o arquivo existe no diretório do projeto ou use `--input` para especificar o caminho

**Erro: "Colunas obrigatórias não encontradas"**
- Verifique se a planilha contém as colunas: IDs, Colaboradores, Departamentos

**Nenhuma tarefa encontrada**
- Verifique se os filtros estão corretos
- Verifique se os IDs na planilha correspondem aos IDs reais no Bitrix24
- Verifique se o webhook tem permissões para ler tarefas

## Licença

Este projeto é fornecido "como está", sem garantias.
