# -*- coding: utf-8 -*-
"""Relatório semanal unificado: formulário diário + agenda '#'."""
import logging
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from bitrix_client import BitrixClient
from comercial_calendar import get_calendar_client
from comercial_calendar import build_calendar_summary_for_comercial
from comercial_collaborators import comercial_collaborator_list
from comercial_config import get_conventions_rows, get_week_range, week_range_to_api_dates
from comercial_daily_store import aggregate_daily_by_collaborator, list_daily_reports_in_range
from config import COLLABORATORS_SHEET_PATH, validate_config
from excel_handler import read_collaborators_sheet

# Ordem e rótulos em português (chave interna, cabeçalho na planilha)
DAILY_REPORT_COLUMNS_PT: Sequence[Tuple[str, str]] = (
    ("collaborator_name", "Colaborador"),
    ("report_date", "Data"),
    ("start_time", "Horário início"),
    ("end_time", "Horário fim"),
    ("contacts_count", "Contatos efetuados"),
    ("meetings_scheduled", "Reuniões agendadas"),
    ("meetings_institutional", "Reunião institucional (QSP/QSN)"),
    ("meetings_desdobramento", "Reunião de desdobramento"),
    ("meetings_nutricao", "Reunião de nutrição"),
    ("created_at", "Registrado em"),
)

AGENDA_HASH_COLUMNS_PT: Sequence[Tuple[str, str]] = (
    ("collaborator_name", "Colaborador"),
    ("week_start", "Início da semana"),
    ("week_end", "Fim da semana"),
    ("total_reunioes_hash", "Total reuniões com #"),
    ("hash_institucional_qsp_qsn", "Institucional (QSP/QSN)"),
    ("hash_desdobramento", "Desdobramento"),
    ("hash_nutricao", "Nutrição"),
    ("hash_outros", "Outros"),
)


def _dataframe_pt(
    rows: List[Dict[str, Any]],
    column_order: Sequence[Tuple[str, str]],
) -> pd.DataFrame:
    """Monta DataFrame só com colunas desejadas e cabeçalhos em português."""
    if not rows:
        return pd.DataFrame(columns=[label for _, label in column_order])
    source = pd.DataFrame(rows)
    out: Dict[str, Any] = {}
    for key, label in column_order:
        if key in source.columns:
            out[label] = source[key]
    return pd.DataFrame(out)


logger = logging.getLogger(__name__)


def _int(val: Any) -> int:
    try:
        return int(val or 0)
    except (TypeError, ValueError):
        return 0


def build_unified_weekly_rows(
    collaborators_map: Dict[int, Dict[str, str]],
    client: Optional[BitrixClient] = None,
    previous_week: bool = True,
    include_calendar: bool = True,
) -> List[Dict[str, Any]]:
    """
    Junta agregado do formulário diário com contagem de agenda '#'.
    """
    week_start, week_end = get_week_range(previous_week=previous_week)
    date_from, date_to = week_range_to_api_dates(week_start, week_end)

    form_agg = {
        r["collaborator_name"]: r
        for r in aggregate_daily_by_collaborator(date_from, date_to)
    }

    collab_list = comercial_collaborator_list(collaborators_map)
    calendar_by_name: Dict[str, Dict[str, Any]] = {}
    if include_calendar and client:
        try:
            cal_rows = build_calendar_summary_for_comercial(
                client, collab_list, previous_week=previous_week
            )
            calendar_by_name = {r["collaborator_name"]: r for r in cal_rows}
        except Exception as e:
            logger.error(f"Erro ao buscar agenda: {e}", exc_info=True)

    unified: List[Dict[str, Any]] = []
    for _uid, name in collab_list:
        form = form_agg.get(name, {})
        cal = calendar_by_name.get(name, {})
        form_inst = _int(form.get("total_institucional"))
        form_des = _int(form.get("total_desdobramento"))
        form_nut = _int(form.get("total_nutricao"))
        cal_inst = _int(cal.get("hash_institucional_qsp_qsn"))
        cal_des = _int(cal.get("hash_desdobramento"))
        cal_nut = _int(cal.get("hash_nutricao"))

        unified.append({
            "Colaborador": name,
            "Semana": f"{week_start.strftime('%d/%m/%Y')} a {week_end.strftime('%d/%m/%Y')}",
            "Dias com resumo (formulário)": _int(form.get("dias_preenchidos")),
            "Contatos (formulário)": _int(form.get("total_contatos")),
            "Reuniões agendadas (formulário)": _int(form.get("total_reunioes_agendadas")),
            "Institucional QSP/QSN (formulário)": form_inst,
            "Desdobramento (formulário)": form_des,
            "Nutrição (formulário)": form_nut,
            "Total reuniões # (agenda)": _int(cal.get("total_reunioes_hash")),
            "Institucional # (agenda)": cal_inst,
            "Desdobramento # (agenda)": cal_des,
            "Nutrição # (agenda)": cal_nut,
            "Divergência Institucional": form_inst - cal_inst,
            "Divergência Desdobramento": form_des - cal_des,
            "Divergência Nutrição": form_nut - cal_nut,
        })

    return unified


def build_weekly_excel_bytes(
    collaborators_file: str = COLLABORATORS_SHEET_PATH,
    previous_week: bool = True,
) -> Tuple[BytesIO, int, datetime, datetime]:
    """Gera Excel com abas: Consolidado, Formulário (detalhe), Agenda (resumo)."""
    validate_config()
    collaborators_map = read_collaborators_sheet(collaborators_file)
    client = get_calendar_client()

    week_start, week_end = get_week_range(previous_week=previous_week)
    date_from, date_to = week_range_to_api_dates(week_start, week_end)

    unified = build_unified_weekly_rows(
        collaborators_map, client=client, previous_week=previous_week
    )
    detail_form = list_daily_reports_in_range(date_from, date_to)
    collab_list = comercial_collaborator_list(collaborators_map)
    cal_detail = build_calendar_summary_for_comercial(client, collab_list, previous_week)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(unified).to_excel(writer, sheet_name="Consolidado Semanal", index=False)

        _dataframe_pt(detail_form, DAILY_REPORT_COLUMNS_PT).to_excel(
            writer, sheet_name="Resumos Diários", index=False
        )

        _dataframe_pt(cal_detail, AGENDA_HASH_COLUMNS_PT).to_excel(
            writer, sheet_name="Agenda Hash", index=False
        )

        pd.DataFrame(get_conventions_rows(week_start, week_end)).to_excel(
            writer, sheet_name="Convenções", index=False
        )

    output.seek(0)
    return output, len(unified), week_start, week_end
