# -*- coding: utf-8 -*-
"""Leitura de agenda Bitrix24 e contagem de reuniões com '#'."""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import os

from bitrix_client import BitrixClient
from config import BITRIX_WEBHOOK_BASE
from comercial_config import (
    HASH_MARKER,
    MEETING_TYPE_KEYWORDS,
    MEETING_TYPE_LABELS,
    get_week_range,
    week_range_to_api_dates,
)

logger = logging.getLogger(__name__)

# Após 401 no calendário, não repetir chamadas (webhook sem permissão calendar)
_calendar_api_disabled = False


def event_has_hash_marker(event: Dict[str, Any]) -> bool:
    name = str(event.get("NAME") or event.get("name") or "")
    desc = str(event.get("DESCRIPTION") or event.get("description") or "")
    return HASH_MARKER in name or HASH_MARKER in desc


def classify_meeting_type(event: Dict[str, Any]) -> str:
    """Classifica evento por palavras-chave; retorna chave de MEETING_TYPE_LABELS."""
    text = (
        str(event.get("NAME") or event.get("name") or "")
        + " "
        + str(event.get("DESCRIPTION") or event.get("description") or "")
    ).lower()
    for type_key, keywords in MEETING_TYPE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return type_key
    return "outros"


def parse_event_start(event: Dict[str, Any]) -> Optional[datetime]:
    """Tenta extrair data de início do evento."""
    for key in ("DATE_FROM_TS_UTC", "dateFromTsUtc"):
        ts = event.get(key)
        if ts:
            try:
                return datetime.utcfromtimestamp(int(ts))
            except (TypeError, ValueError):
                pass
    raw = event.get("DATE_FROM") or event.get("dateFrom") or ""
    if not raw:
        return None
    raw = str(raw).strip()
    for fmt in ("%m/%d/%Y %I:%M:%S %p", "%d/%m/%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(raw.split("+")[0].strip(), fmt)
        except ValueError:
            continue
    return None


def get_calendar_client() -> BitrixClient:
    """Webhook dedicado ao calendário (opcional); senão usa o mesmo das tarefas."""
    webhook = (os.getenv("BITRIX_WEBHOOK_CALENDAR") or "").strip() or BITRIX_WEBHOOK_BASE
    return BitrixClient(webhook_base=webhook)


def fetch_user_calendar_events(
    client: BitrixClient,
    owner_id: int,
    date_from: str,
    date_to: str,
) -> List[Dict[str, Any]]:
    """Chama calendar.event.get sem alterar bitrix_client.py."""
    params = {
        "type": "user",
        "ownerId": owner_id,
        "from": date_from,
        "to": date_to,
    }
    global _calendar_api_disabled
    if _calendar_api_disabled:
        return []
    try:
        response = client._request("calendar.event.get", params)
        result = response.get("result", [])
        if isinstance(result, list):
            return result
        return []
    except Exception as e:
        err = str(e)
        if "401" in err:
            _calendar_api_disabled = True
            logger.warning(
                "calendar.event.get sem permissão (401). "
                "Configure BITRIX_WEBHOOK_CALENDAR no .env com webhook que inclua calendário. "
                "Relatório seguirá só com dados do formulário diário."
            )
        else:
            logger.warning(f"calendar.event.get falhou para user {owner_id}: {e}")
        return []


def count_hash_meetings_for_user(
    client: BitrixClient,
    owner_id: int,
    week_start: datetime,
    week_end: datetime,
) -> Dict[str, Any]:
    """
    Conta eventos da semana com '#' e agrupa por tipo.
    """
    date_from, date_to = week_range_to_api_dates(week_start, week_end)
    events = fetch_user_calendar_events(client, owner_id, date_from, date_to)
    counts = {k: 0 for k in MEETING_TYPE_LABELS}
    matched_events: List[Dict[str, Any]] = []

    for ev in events:
        if not event_has_hash_marker(ev):
            continue
        ev_start = parse_event_start(ev)
        if ev_start:
            if ev_start.date() < week_start.date() or ev_start.date() > week_end.date():
                continue
        mtype = classify_meeting_type(ev)
        counts[mtype] = counts.get(mtype, 0) + 1
        matched_events.append({
            "id": ev.get("ID") or ev.get("id"),
            "name": ev.get("NAME") or ev.get("name"),
            "date_from": ev.get("DATE_FROM") or ev.get("dateFrom"),
            "type": mtype,
            "type_label": MEETING_TYPE_LABELS.get(mtype, mtype),
        })

    counts["total_hash"] = sum(counts.values())
    return {
        "total_hash": counts["total_hash"],
        "by_type": counts,
        "events": matched_events,
    }


def build_calendar_summary_for_comercial(
    client: BitrixClient,
    collaborators: List[Tuple[int, str]],
    previous_week: bool = True,
) -> List[Dict[str, Any]]:
    """Resumo de agenda '#' para todos os colaboradores COMERCIAL."""
    week_start, week_end = get_week_range(previous_week=previous_week)
    rows = []
    for owner_id, name in collaborators:
        stats = count_hash_meetings_for_user(client, owner_id, week_start, week_end)
        row = {
            "collaborator_name": name,
            "week_start": week_start.strftime("%d/%m/%Y"),
            "week_end": week_end.strftime("%d/%m/%Y"),
            "total_reunioes_hash": stats["total_hash"],
        }
        for type_key, label in MEETING_TYPE_LABELS.items():
            row[f"hash_{type_key}"] = stats["by_type"].get(type_key, 0)
        rows.append(row)
    return rows
