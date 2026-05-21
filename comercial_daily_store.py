# -*- coding: utf-8 -*-
"""Armazenamento SQLite dos resumos diários comerciais."""
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from comercial_config import COMERCIAL_DATA_DIR, COMERCIAL_DB_PATH


def _ensure_db() -> None:
    os.makedirs(COMERCIAL_DATA_DIR, exist_ok=True)
    with sqlite3.connect(COMERCIAL_DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collaborator_name TEXT NOT NULL,
                report_date TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                contacts_count INTEGER DEFAULT 0,
                meetings_scheduled INTEGER DEFAULT 0,
                meetings_institutional INTEGER DEFAULT 0,
                meetings_desdobramento INTEGER DEFAULT 0,
                meetings_nutricao INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                UNIQUE(collaborator_name, report_date)
            )
            """
        )
        conn.commit()


def save_daily_report(
    collaborator_name: str,
    report_date: str,
    start_time: str = "",
    end_time: str = "",
    contacts_count: int = 0,
    meetings_scheduled: int = 0,
    meetings_institutional: int = 0,
    meetings_desdobramento: int = 0,
    meetings_nutricao: int = 0,
) -> None:
    _ensure_db()
    now = datetime.now().isoformat()
    with sqlite3.connect(COMERCIAL_DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO daily_reports (
                collaborator_name, report_date, start_time, end_time,
                contacts_count, meetings_scheduled, meetings_institutional,
                meetings_desdobramento, meetings_nutricao, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(collaborator_name, report_date) DO UPDATE SET
                start_time=excluded.start_time,
                end_time=excluded.end_time,
                contacts_count=excluded.contacts_count,
                meetings_scheduled=excluded.meetings_scheduled,
                meetings_institutional=excluded.meetings_institutional,
                meetings_desdobramento=excluded.meetings_desdobramento,
                meetings_nutricao=excluded.meetings_nutricao,
                created_at=excluded.created_at
            """,
            (
                collaborator_name.strip(),
                report_date.strip(),
                start_time,
                end_time,
                contacts_count,
                meetings_scheduled,
                meetings_institutional,
                meetings_desdobramento,
                meetings_nutricao,
                now,
            ),
        )
        conn.commit()


def list_daily_reports_in_range(
    date_from: str,
    date_to: str,
    collaborator_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista relatórios entre datas (YYYY-MM-DD)."""
    _ensure_db()
    query = """
        SELECT collaborator_name, report_date, start_time, end_time,
               contacts_count, meetings_scheduled, meetings_institutional,
               meetings_desdobramento, meetings_nutricao, created_at
        FROM daily_reports
        WHERE report_date >= ? AND report_date <= ?
    """
    params: List[Any] = [date_from, date_to]
    if collaborator_name:
        query += " AND collaborator_name = ?"
        params.append(collaborator_name.strip())
    query += " ORDER BY collaborator_name, report_date"
    with sqlite3.connect(COMERCIAL_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def aggregate_daily_by_collaborator(
    date_from: str,
    date_to: str,
) -> List[Dict[str, Any]]:
    """Agrega resumos diários por colaborador na semana."""
    _ensure_db()
    with sqlite3.connect(COMERCIAL_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT collaborator_name,
                   COUNT(*) AS dias_preenchidos,
                   SUM(contacts_count) AS total_contatos,
                   SUM(meetings_scheduled) AS total_reunioes_agendadas,
                   SUM(meetings_institutional) AS total_institucional,
                   SUM(meetings_desdobramento) AS total_desdobramento,
                   SUM(meetings_nutricao) AS total_nutricao
            FROM daily_reports
            WHERE report_date >= ? AND report_date <= ?
            GROUP BY collaborator_name
            ORDER BY collaborator_name
            """,
            (date_from, date_to),
        ).fetchall()
    return [dict(r) for r in rows]
