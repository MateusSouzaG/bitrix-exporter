# Guia Rápido de Uso - Sistema de Exportação Bitrix24

## 🚀 Como Começar

### 1. Exportação Básica (Todas as Tarefas)
```bash
python main.py
```
**O que faz:** Exporta todas as tarefas de todos os 24 colaboradores da planilha.

### 2. Filtrar por Departamento
```bash
python main.py --dept COMERCIAL
python main.py --dept DTC
python main.py --dept GI
python main.py --dept RNA
```
**O que faz:** Exporta apenas tarefas de colaboradores do departamento especificado.

### 3. Filtrar por Colaborador
```bash
python main.py --user "Erick"
python main.py --user "Carolina"
```
**O que faz:** Exporta tarefas de colaboradores cujo nome contém a string fornecida (case-insensitive).

### 4. Filtrar por Período de Atividade
```bash
# Exportar tarefas ativas em janeiro de 2024
python main.py --active-from "2024-01-01T00:00:00-03:00" --active-to "2024-01-31T23:59:59-03:00"

# Exportar tarefas ativas no último ano
python main.py --active-from "2024-01-01T00:00:00-03:00" --active-to "2024-12-31T23:59:59-03:00"
```
**O que faz:** Exporta apenas tarefas que estavam ativas no período especificado.

### 5. Filtrar por Status
```bash
python main.py --status NEW
python main.py --status IN_PROGRESS
python main.py --status COMPLETED
```
**Status disponíveis:**
- `NEW` - Tarefas novas
- `IN_PROGRESS` - Tarefas em progresso
- `COMPLETED` - Tarefas concluídas

### 6. Combinar Múltiplos Filtros
```bash
# Tarefas do departamento COMERCIAL, ativas em 2024, que estão em progresso
python main.py --dept COMERCIAL --active-from "2024-01-01T00:00:00-03:00" --active-to "2024-12-31T23:59:59-03:00" --status IN_PROGRESS
```

### 7. Especificar Arquivo de Saída
```bash
python main.py --dept COMERCIAL --output "relatorio_comercial.xlsx"
```

## 📊 O que o Excel contém?

O arquivo Excel gerado terá as seguintes colunas:

- **Task_ID**: ID único da tarefa no Bitrix24
- **Título**: Título da tarefa
- **Status**: Status atual (NEW, IN_PROGRESS, COMPLETED, etc.)
- **Deadline**: Data limite (se houver)
- **Responsável**: Nome do responsável pela tarefa
- **Participantes**: Nomes dos participantes (separados por vírgula)
- **Seu_time_envolvido**: Pessoas do seu escopo que aparecem na tarefa
- **Tempo_Total_Gasto**: Tempo total gasto na tarefa (ex: "2h 30min")
- **Tempo_Lançamento**: Tempo do lançamento individual (uma linha por lançamento)
- **Quem_Lançou**: Nome de quem fez o lançamento de tempo
- **Comentário_Lançamento**: Comentário do lançamento de tempo
- **Departamentos_Selecionados**: Departamentos de todas as pessoas envolvidas
- **Atividade_em**: Data da última atividade

## ⚠️ Observações Importantes

1. **Múltiplas linhas por tarefa**: Se uma tarefa tiver múltiplos lançamentos de tempo, cada lançamento gerará uma linha no Excel.

2. **Tempo de execução**: Exportações grandes podem levar alguns minutos. O sistema mostra o progresso no terminal.

3. **Arquivo de saída**: Por padrão, o arquivo é salvo com nome automático: `Exportacao_Tarefas_YYYYMMDD_HHMMSS.xlsx`

4. **Formato de data**: Use o formato ISO8601 para filtros de data:
   - Com timezone: `2024-01-01T00:00:00-03:00`
   - Sem timezone: `2024-01-01T00:00:00` (será adicionado -03:00 automaticamente)

## 🔍 Exemplos Práticos

### Exemplo 1: Relatório Mensal do Departamento COMERCIAL
```bash
python main.py --dept COMERCIAL --active-from "2024-01-01T00:00:00-03:00" --active-to "2024-01-31T23:59:59-03:00" --output "relatorio_comercial_janeiro.xlsx"
```

### Exemplo 2: Tarefas em Progresso de um Colaborador Específico
```bash
python main.py --user "Erick" --status IN_PROGRESS
```

### Exemplo 3: Todas as Tarefas Concluídas em 2024
```bash
python main.py --status COMPLETED --active-from "2024-01-01T00:00:00-03:00" --active-to "2024-12-31T23:59:59-03:00"
```

## 🆘 Precisa de Ajuda?

Execute `python main.py --help` para ver todas as opções disponíveis.
