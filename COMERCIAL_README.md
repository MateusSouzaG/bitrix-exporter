# Módulo Comercial (isolado do Timesheet)

Este módulo automatiza os controles de **produtividade comercial** e **reuniões com `#` na agenda Bitrix24**.  
**Não altera** o fluxo de exportação de tarefas (`/export`, `web_services.py`, `task_processor.py`).

## Acesso

- URL: `/comercial`
- **Admin** ou **supervisor** com departamento `COMERCIAL` (ex.: `deborah.szajin`)
- Colaboradores com perfil `colaborador` podem preencher **apenas o próprio** resumo diário

## Fase 0 — Convenções

| Item | Regra |
|------|--------|
| Semana do relatório | Segunda a domingo da **semana anterior** (extração toda segunda-feira) |
| Reunião realizada | Evento na agenda com `#` no **título** ou **descrição** |
| Institucional QSP/QSN | Palavras: institucional, qsp, qsn |
| Desdobramento | Palavras: desdobramento, desdobr |
| Nutrição | Palavras: nutrição, nutricao, nutri |
| Colaboradores | Departamento `COMERCIAL` na planilha de colaboradores |

Ajuste palavras-chave em `comercial_config.py` após alinhar com o time.

## Fluxo 1 — Resumo diário

1. Acesse `/comercial/formulario`
2. Preencha os campos (mesmo modelo da mensagem diária)
3. Dados gravados em `data/comercial/daily_reports.db` (SQLite local)

## Fluxo 2 — Agenda "#"

- API: `calendar.event.get` (via `comercial_calendar.py`)
- Webhook precisa ter permissão de **calendário** (`calendar`); se retornar 401, crie um webhook inbound com escopo de calendário ou use variável `BITRIX_WEBHOOK_CALENDAR` no `.env` (opcional, ver `comercial_calendar.py` / config futura)
- Enquanto o webhook não tiver calendário, o relatório ainda gera a aba de formulário; colunas de agenda ficam em zero

## Relatório semanal unificado

- Web: botão em `/comercial` (coordenação)
- CLI: `python scripts/comercial_weekly_report.py -o relatorio.xlsx`

Excel com abas:

1. **Consolidado Semanal** — formulário + agenda + colunas de divergência
2. **Resumos Diários** — detalhe por dia
3. **Agenda Hash** — contagem por colaborador
4. **Convenções** — regras documentadas

## Validação (segunda-feira)

1. Gerar relatório automático da semana anterior
2. Comparar com planilha manual da coordenadora
3. Ajustar palavras-chave ou convenção do `#` se necessário

## Arquivos do módulo

- `comercial_config.py` — convenções e período
- `comercial_collaborators.py` — filtro COMERCIAL
- `comercial_calendar.py` — API agenda
- `comercial_daily_store.py` — SQLite resumos
- `comercial_report.py` — Excel unificado
- `comercial_routes.py` — rotas FastAPI
- `comercial_access.py` — permissões
