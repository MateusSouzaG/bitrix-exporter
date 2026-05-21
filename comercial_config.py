# -*- coding: utf-8 -*-
"""Configuração e convenções do módulo Comercial (isolado do exportador de tarefas)."""
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

# Departamento alvo
COMERCIAL_DEPT = "COMERCIAL"

# Convenção: reunião realizada se o título ou descrição contém "#"
HASH_MARKER = "#"

# Classificação por palavras-chave no título/descrição (minúsculas)
MEETING_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "institucional_qsp_qsn": ["institucional", "qsp", "qsn"],
    "desdobramento": ["desdobramento", "desdobr"],
    "nutricao": ["nutrição", "nutricao", "nutri"],
}

MEETING_TYPE_LABELS = {
    "institucional_qsp_qsn": "Reunião Institucional (QSP/QSN)",
    "desdobramento": "Reunião de Desdobramento",
    "nutricao": "Reunião de Nutrição",
    "outros": "Outros (com #)",
}

# Armazenamento local dos resumos diários (não interfere no export de tarefas)
import os

_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
COMERCIAL_DATA_DIR = os.path.join(_PROJECT_DIR, "data", "comercial")
COMERCIAL_DB_PATH = os.path.join(COMERCIAL_DATA_DIR, "daily_reports.db")


def get_week_range(reference: Optional[datetime] = None, previous_week: bool = True) -> Tuple[datetime, datetime]:
    """
    Retorna (início, fim) da semana em horário local: segunda 00:00 até domingo 23:59:59.
    Se previous_week=True, usa a semana anterior (segunda a domingo).
    Alinhado à extração de segunda-feira sobre a semana que acabou no domingo anterior.
    """
    ref = reference or datetime.now()
    # Segunda da semana que contém ref (weekday: seg=0 … dom=6)
    monday_this_week = (ref - timedelta(days=ref.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    if previous_week:
        monday_start = monday_this_week - timedelta(days=7)
    else:
        monday_start = monday_this_week
    sunday_end = monday_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return monday_start, sunday_end


def get_conventions_rows(week_start: datetime, week_end: datetime) -> List[Dict[str, str]]:
    """Linhas da aba Convenções em linguagem clara para quem extrai o relatório."""
    rows = [
        {
            "Regra": "Reunião realizada",
            "Valor": "Compromisso na agenda com '#' no título ou na descrição",
        },
        {
            "Regra": "Semana do relatório",
            "Valor": (
                f"{week_start.strftime('%d/%m/%Y')} (segunda-feira) a "
                f"{week_end.strftime('%d/%m/%Y')} (domingo)"
            ),
        },
    ]
    for type_key, label in MEETING_TYPE_LABELS.items():
        if type_key == "outros":
            valor = "Reuniões com '#' que não se enquadram nos tipos abaixo"
        else:
            palavras = ", ".join(MEETING_TYPE_KEYWORDS.get(type_key, []))
            valor = f"Palavras no título ou descrição: {palavras}"
        rows.append({"Regra": label, "Valor": valor})
    return rows


def week_range_to_api_dates(start: datetime, end: datetime) -> Tuple[str, str]:
    """Formato aceito por calendar.event.get (YYYY-MM-DD)."""
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
