"""Busca e processamento de lançamentos de tempo (elapsed items) do Bitrix24."""
import json
import logging
from typing import Any, Dict, List, Optional, Set
from bitrix_client import BitrixClient
from config import BATCH_SIZE, USE_SINGLE_REQUEST_TIME_ENTRIES

logger = logging.getLogger(__name__)


def _parse_time_entries_response(response: Any) -> List[Dict[str, Any]]:
    """
    Converte a resposta da API task.elapseditem.getlist na lista de lançamentos.
    Aceita resposta em dict (result/items), lista direta, ou string JSON (batch pode devolver assim).
    """
    if response is None:
        return []
    # Batch às vezes devolve a resposta como string JSON
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except (json.JSONDecodeError, TypeError):
            return []
    # Batch às vezes devolve a lista diretamente por comando
    if isinstance(response, list):
        return response if response else []
    if not isinstance(response, dict):
        return []
    # Bitrix pode retornar erro no próprio item da resposta do batch (só tratar como erro se error for truthy)
    if response.get("error"):
        logger.warning(
            "Bitrix API retornou erro em task.elapseditem.getlist: %s - %s",
            response.get("error", ""),
            response.get("error_description", ""),
        )
        return []
    result = response.get("result")
    if result is None:
        return []
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

    if USE_SINGLE_REQUEST_TIME_ENTRIES:
        logger.info("Modo: requisições individuais para lançamentos de tempo (task.elapseditem.getlist por tarefa).")
        logger.info(f"Buscando lançamentos de tempo para {total} tarefas (requisições individuais)...")
        for task_id in task_ids_list:
            try:
                entries = client.get_time_entries(task_id)
                time_entries_map[task_id] = list(entries) if entries else []
            except Exception as e:
                logger.warning(f"get_time_entries falhou para tarefa {task_id}: {e}")
                time_entries_map[task_id] = []
        total_entries = sum(len(v) for v in time_entries_map.values())
        logger.info(f"Lançamentos de tempo coletados para {len(time_entries_map)} tarefas (total de itens: {total_entries})")
        return time_entries_map

    logger.info(f"Buscando lançamentos de tempo para {total} tarefas (via batch)...")
    
    first_raw_response_logged = False
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
                # Logar uma amostra da resposta bruta quando vazia (só na primeira vez) para diagnóstico
                if not first_raw_response_logged and not time_entries_map[task_id] and raw_response is not None:
                    sample = json.dumps(raw_response, ensure_ascii=False)[:500]
                    logger.warning(
                        "Resposta bruta do Bitrix (task.elapseditem.getlist) para tarefa %s (amostra): %s",
                        task_id,
                        sample,
                    )
                    first_raw_response_logged = True
        except Exception as e:
            logger.warning(f"Erro no batch de lançamentos de tempo: {e}")
            for task_id in batch_task_ids:
                time_entries_map[task_id] = []

    total_entries = sum(len(v) for v in time_entries_map.values())
    logger.info(f"Lançamentos de tempo coletados para {len(time_entries_map)} tarefas (total de itens: {total_entries})")

    # Fallback: se o batch retornou vazio para todas as tarefas, tentar requisições individuais
    # (alguns webhooks/permissões se comportam diferente em batch vs chamada direta)
    if total_entries == 0 and total > 0:
        logger.warning(
            "Batch de task.elapseditem.getlist retornou vazio. Tentando requisições individuais (fallback)..."
        )
        for task_id in task_ids_list:
            try:
                entries = client.get_time_entries(task_id)
                time_entries_map[task_id] = list(entries) if entries else []
            except Exception as e:
                logger.debug(f"Fallback get_time_entries para tarefa {task_id}: {e}")
                time_entries_map[task_id] = []
        total_entries = sum(len(v) for v in time_entries_map.values())
        if total_entries > 0:
            logger.info(f"Fallback: {total_entries} lançamentos obtidos via requisições individuais.")
        else:
            logger.warning(
                "Nenhum lançamento obtido (batch e fallback). "
                "Confirme no Bitrix24 que o webhook tem permissão para 'Lançamentos de tempo' (tasks.elapseditem)."
            )

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
