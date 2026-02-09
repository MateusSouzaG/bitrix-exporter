"""Mapeamento de filtros de data pré-definidos do Bitrix24."""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from calendar import monthrange
from config import DEFAULT_TIMEZONE


def get_last_day_of_month(year: int, month: int) -> int:
    """Retorna o último dia do mês."""
    return monthrange(year, month)[1]


def get_date_range_for_preset(preset: str) -> Optional[Tuple[str, str]]:
    """
    Converte uma opção pré-definida do Bitrix24 em intervalo de datas.
    
    Args:
        preset: Opção pré-definida (ex: "esta_semana", "este_mes", etc.)
        
    Returns:
        Tuple (data_inicial, data_final) em formato ISO8601, ou None se inválido
    """
    now = datetime.now()
    tz = DEFAULT_TIMEZONE
    
    # Mapeamento de opções pré-definidas
    presets = {
        # Sem filtro
        "qualquer_data": None,
        "": None,
        
        # Períodos relativos ao hoje
        "dia_atual": (
            now.replace(hour=0, minute=0, second=0, microsecond=0),
            now.replace(hour=23, minute=59, second=59, microsecond=999999)
        ),
        "amanha": (
            (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
            (now + timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
        ),
        
        # Esta semana (segunda a domingo)
        "esta_semana": (
            (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0),
            (now + timedelta(days=6-now.weekday())).replace(hour=23, minute=59, second=59, microsecond=999999)
        ),
        
        # Este mês
        "este_mes": (
            now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            now.replace(day=get_last_day_of_month(now.year, now.month), hour=23, minute=59, second=59, microsecond=999999)
        ),
        
        # Últimos N dias
        "ultimos_7_dias": (
            (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0),
            now.replace(hour=23, minute=59, second=59, microsecond=999999)
        ),
        "ultimos_30_dias": (
            (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0),
            now.replace(hour=23, minute=59, second=59, microsecond=999999)
        ),
        "ultimos_60_dias": (
            (now - timedelta(days=60)).replace(hour=0, minute=0, second=0, microsecond=0),
            now.replace(hour=23, minute=59, second=59, microsecond=999999)
        ),
        "ultimos_90_dias": (
            (now - timedelta(days=90)).replace(hour=0, minute=0, second=0, microsecond=0),
            now.replace(hour=23, minute=59, second=59, microsecond=999999)
        ),
        
        # Semana passada
        "semana_passada": (
            (now - timedelta(days=now.weekday() + 7)).replace(hour=0, minute=0, second=0, microsecond=0),
            (now - timedelta(days=now.weekday() + 1)).replace(hour=23, minute=59, second=59, microsecond=999999)
        ),
        
        # Mês passado
        "mes_passado": (
            ((now.replace(day=1) - timedelta(days=1)).replace(day=1)).replace(hour=0, minute=0, second=0, microsecond=0),
            (now.replace(day=1) - timedelta(microseconds=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
        ),
        
        # Próxima semana
        "proxima_semana": (
            (now + timedelta(days=7-now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0),
            (now + timedelta(days=13-now.weekday())).replace(hour=23, minute=59, second=59, microsecond=999999)
        ),
        
        # Próximo mês
        "proximo_mes": (
            ((now.replace(day=1) + timedelta(days=32)).replace(day=1)).replace(hour=0, minute=0, second=0, microsecond=0),
            ((now.replace(day=1) + timedelta(days=64)).replace(day=1) - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
        ),
        
        # Trimestre anual (ano atual completo)
        "trimestre_anual": (
            now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
            now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        ),
    }
    
    if preset not in presets:
        return None
    
    date_range = presets[preset]
    if date_range is None:
        return None
    
    start_date, end_date = date_range
    
    # Converter para ISO8601
    start_iso = start_date.strftime(f"%Y-%m-%dT%H:%M:%S{tz}")
    end_iso = end_date.strftime(f"%Y-%m-%dT%H:%M:%S{tz}")
    
    return (start_iso, end_iso)


def format_date_for_input(dt: datetime) -> str:
    """Formata datetime para input datetime-local (YYYY-MM-DDTHH:MM)."""
    return dt.strftime("%Y-%m-%dT%H:%M")


# Opções disponíveis para o select (mapeadas para as opções nativas do Bitrix24)
PRESET_OPTIONS = [
    ("", "Todo o período"),
    ("dia_atual", "Dia atual"),
    ("amanha", "Amanhã"),
    ("esta_semana", "Esta semana"),
    ("este_mes", "Este mês"),
    ("trimestre_anual", "Trimestre anual"),
    ("ultimos_7_dias", "Últimos 7 dias"),
    ("ultimos_30_dias", "Últimos 30 dias"),
    ("ultimos_60_dias", "Últimos 60 dias"),
    ("ultimos_90_dias", "Últimos 90 dias"),
    ("semana_passada", "Semana passada"),
    ("mes_passado", "Mês passado"),
    ("proxima_semana", "Na próxima semana"),
    ("proximo_mes", "No próximo mês"),
    ("intervalo_personalizado", "Intervalo personalizado"),
]
