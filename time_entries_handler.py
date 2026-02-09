"""Busca e processamento de lançamentos de tempo (elapsed items) do Bitrix24."""
import logging
from typing import Dict, List, Any, Set, Optional
from bitrix_client import BitrixClient
from config import BATCH_SIZE

logger = logging.getLogger(__name__)


def _parse_time_entries_response(response: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Converte a resposta da API task.elapseditem.getlist na lista de lançamentos.
    Mesma lógica de get_time_entries, para manter idêntica a qualidade dos dados.
    """
    if not response:
        return []
    result = response.get("result", {})
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        if "items" in result and isinstance(result["items"], list):
            return result["items"]
        if "elapsedItems" in result and isinstance(result["elapsedItems"], list):
            return result["elapsedItems"]
        for value in result.values():
            if isinstance(value, list):
                return value
        return []
    return []


def fetch_all_time_entries(client: BitrixClient, task_ids: Set[int]) -> Dict[int, List[Dict[str, Any]]]:
    """
    Busca todos os lançamentos de tempo para um conjunto de tarefas usando o
    endpoint batch da API Bitrix24, agrupando várias tarefas por requisição.
    Reduz o tempo de processamento sem alterar a qualidade dos dados.
    
    Args:
        client: Instância do BitrixClient
        task_ids: Conjunto de IDs de tarefas
        
    Returns:
        Dicionário {task_id: [lista de lançamentos]}
    """
    time_entries_map = {}
    task_ids_list = list(task_ids)
    total = len(task_ids_list)
    
    logger.info(f"Buscando lançamentos de tempo para {total} tarefas (via batch)...")
    
    for i in range(0, total, BATCH_SIZE):
        batch_task_ids = task_ids_list[i:i + BATCH_SIZE]
        commands = [
            {"method": "task.elapseditem.getlist", "params": {"TASKID": tid}}
            for tid in batch_task_ids
        ]
        try:
            responses = client._batch(commands)
            for task_id, raw_response in zip(batch_task_ids, responses):
                time_entries_map[task_id] = _parse_time_entries_response(raw_response)
        except Exception as e:
            logger.warning(f"Erro no batch de lançamentos de tempo: {e}")
            for task_id in batch_task_ids:
                time_entries_map[task_id] = []
    
    logger.info(f"Lançamentos de tempo coletados para {len(time_entries_map)} tarefas")
    return time_entries_map


def process_time_entries(
    entries: List[Dict[str, Any]], 
    collaborators_map: Dict[int, Dict[str, str]]
) -> List[Dict[str, Any]]:
    """
    Processa e normaliza lançamentos de tempo.
    
    Args:
        entries: Lista de lançamentos de tempo retornados pela API
        collaborators_map: Mapeamento user_id -> {name, dept}
        
    Returns:
        Lista de lançamentos processados, cada um com:
        - user_id: ID do usuário
        - user_name: Nome do usuário (ou "USER_<id>" se não encontrado)
        - seconds: Tempo em segundos
        - minutes: Tempo em minutos (calculado)
        - hours: Tempo em horas (calculado)
        - comment: Comentário do lançamento
        - created_date: Data de criação (se disponível)
    """
    processed = []
    total_seconds = 0
    
    for entry in entries:
        # Normalizar campos (a API pode retornar diferentes formatos)
        user_id = entry.get("USER_ID") or entry.get("userId") or entry.get("USERID")
        
        # IMPORTANTE: SECONDS e MINUTES vêm como STRING da API Bitrix24
        # Exemplo: "SECONDS": "20797" (não 20797)
        # Precisamos converter para int antes de fazer comparações
        seconds_raw = entry.get("SECONDS") or entry.get("seconds") or 0
        minutes_raw = entry.get("MINUTES") or entry.get("minutes") or 0
        
        # Converter para int (tratando strings e valores None)
        try:
            seconds = int(seconds_raw) if seconds_raw else 0
        except (ValueError, TypeError):
            seconds = 0
        
        try:
            minutes = int(minutes_raw) if minutes_raw else 0
        except (ValueError, TypeError):
            minutes = 0
        
        comment = entry.get("COMMENT_TEXT") or entry.get("COMMENT") or entry.get("comment") or ""
        created_date = (
            entry.get("CREATED_DATE") or entry.get("createdDate") or entry.get("DATE")
            or entry.get("DATE_CREATE") or entry.get("DATE_CREATE_UTC") or ""
        )
        
        # Normalizar tempo: se vier em minutos, converter para segundos
        if minutes > 0 and seconds == 0:
            seconds = minutes * 60
        elif seconds == 0 and minutes == 0:
            # Tentar extrair de outros campos
            time_spent = entry.get("TIME_SPENT") or entry.get("timeSpent") or 0
            if time_spent:
                try:
                    seconds = int(time_spent) if time_spent else 0
                except (ValueError, TypeError):
                    seconds = 0
        
        total_seconds += seconds
        
        # Resolver nome do usuário
        if user_id:
            try:
                user_id = int(user_id)
                user_info = collaborators_map.get(user_id, {})
                user_name = user_info.get("name", f"USER_{user_id}")
            except (ValueError, TypeError):
                user_name = f"USER_{user_id}"
        else:
            user_id = None
            user_name = "Desconhecido"
        
        processed_entry = {
            "user_id": user_id,
            "user_name": user_name,
            "seconds": seconds,
            "minutes": seconds / 60.0,
            "hours": seconds / 3600.0,
            "comment": str(comment),
            "created_date": str(created_date) if created_date else ""
        }
        
        processed.append(processed_entry)
    
    return processed


def calculate_total_time(entries: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calcula o tempo total gasto a partir de uma lista de lançamentos.
    
    Args:
        entries: Lista de lançamentos processados
        
    Returns:
        Dicionário com total_seconds, total_minutes, total_hours
    """
    # Garantir que todos os valores de seconds sejam números
    total_seconds = 0.0
    for entry in entries:
        seconds = entry.get("seconds", 0)
        try:
            total_seconds += float(seconds) if seconds else 0.0
        except (ValueError, TypeError):
            # Se não conseguir converter, ignorar este lançamento
            continue
    
    return {
        "total_seconds": float(total_seconds),
        "total_minutes": float(total_seconds / 60.0),
        "total_hours": float(total_seconds / 3600.0)
    }
