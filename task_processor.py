"""Processamento de tarefas: coleta, deduplicação e enriquecimento."""
import logging
import unicodedata
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from bitrix_client import BitrixClient
from config import PAGINATION_SIZE, DEFAULT_TIMEZONE

logger = logging.getLogger(__name__)


def _normalize_for_match(text: str) -> str:
    """Normaliza texto para comparação: minúsculas e sem acentos (ex: Quézia == Quezia)."""
    if not text:
        return ""
    nfd = unicodedata.normalize("NFD", str(text).lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def determine_scope_ids(
    collaborators_map: Dict[int, Dict[str, str]],
    dept: Optional[str] = None,
    user_substring: Optional[str] = None
) -> List[int]:
    """
    Determina os IDs do escopo baseado nos filtros fornecidos.
    
    Prioridade: --user > --dept > todos
    
    Args:
        collaborators_map: Mapeamento user_id -> {name, dept}
        dept: Nome do departamento (opcional)
        user_substring: Substring do nome do colaborador (opcional, case-insensitive)
        
    Returns:
        Lista de IDs de usuários do escopo
    """
    if user_substring:
        # Filtrar por substring do nome (case-insensitive e sem acentos, ex: Quezia encontra Quézia)
        needle = _normalize_for_match(user_substring.strip())
        scope_ids = [
            user_id for user_id, info in collaborators_map.items()
            if needle in _normalize_for_match(info.get("name", ""))
        ]
        logger.info(f"Filtro --user '{user_substring}': {len(scope_ids)} colaborador(es) encontrado(s)")
        return scope_ids
    
    elif dept:
        # Filtrar por departamento (comparação com strip e case-insensitive)
        dept_clean = (dept or "").strip().upper()
        scope_ids = [
            user_id for user_id, info in collaborators_map.items()
            if (info.get("dept") or "").strip().upper() == dept_clean
        ]
        logger.info(f"Filtro --dept '{dept}': {len(scope_ids)} colaborador(es) encontrado(s)")
        if not scope_ids:
            depts_na_planilha = set((info.get("dept") or "").strip() for info in collaborators_map.values())
            logger.warning(
                f"Nenhum colaborador com departamento '{dept}'. "
                f"Departamentos presentes na planilha: {sorted(depts_na_planilha) or '(vazios ou planilha sem coluna Departamentos)'}"
            )
        return scope_ids
    
    else:
        # Usar todos
        scope_ids = list(collaborators_map.keys())
        logger.info(f"Sem filtros: usando todos os {len(scope_ids)} colaboradores")
        return scope_ids


def normalize_iso8601(date_str: str, default_tz: str = DEFAULT_TIMEZONE) -> str:
    """
    Normaliza string ISO8601 para formato aceito pela API Bitrix24.
    
    A API Bitrix24 aceita datas no formato ISO8601: YYYY-MM-DDTHH:MM:SS+TZ
    Algumas versões podem aceitar sem timezone também.
    
    Args:
        date_str: String de data no formato ISO8601
        default_tz: Timezone padrão a adicionar (ex: "-03:00")
        
    Returns:
        String ISO8601 normalizada no formato aceito pela API
    """
    if not date_str:
        return ""
    
    date_str = date_str.strip()
    
    # Se já está no formato correto com timezone completo, retornar como está
    # Formato: YYYY-MM-DDTHH:MM:SS+TZ ou YYYY-MM-DDTHH:MM:SS-TZ
    if len(date_str) >= 25 and ("+" in date_str[-6:] or (date_str[-6:].startswith("-") and ":" in date_str[-5:])):
        return date_str
    
    # Se termina com Z, substituir por timezone padrão
    if date_str.endswith("Z"):
        date_str = date_str[:-1] + default_tz
        return date_str
    
    # Se tem formato YYYY-MM-DDTHH:MM mas sem segundos/timezone
    if "T" in date_str:
        parts = date_str.split("T")
        if len(parts) == 2:
            date_part = parts[0]
            time_part = parts[1]
            
            # Se time_part não tem segundos, adicionar :00
            if ":" in time_part and time_part.count(":") == 1:
                time_part = time_part + ":00"
            
            # Remover qualquer timezone parcial que possa estar presente
            if "+" in time_part:
                time_part = time_part.split("+")[0]
            elif "-" in time_part and len(time_part.split("-")) > 2:
                # Pode ter timezone no meio, pegar só a parte do tempo
                time_parts = time_part.split("-")
                if len(time_parts) > 2:
                    time_part = "-".join(time_parts[:-1])
            
            # Se não tem timezone no final, adicionar
            if not (time_part.endswith("+03:00") or time_part.endswith("-03:00") or 
                    (len(time_part) > 6 and (time_part[-6:].startswith("+") or time_part[-6:].startswith("-")))):
                time_part = time_part + default_tz
            
            return f"{date_part}T{time_part}"
    else:
        # Apenas data (YYYY-MM-DD), adicionar hora e timezone
        return date_str + "T00:00:00" + default_tz
    
    return date_str


def collect_task_ids(
    client: BitrixClient,
    scope_ids: List[int],
    activity_from: Optional[str] = None,
    activity_to: Optional[str] = None,
    status: Optional[str] = None
) -> Set[int]:
    """
    Coleta IDs únicos de tarefas onde pessoas do escopo aparecem como responsável ou participante.
    
    Args:
        client: Instância do BitrixClient
        scope_ids: Lista de IDs do escopo
        activity_from: Data inicial para filtro ACTIVITY_DATE (ISO8601, opcional)
        activity_to: Data final para filtro ACTIVITY_DATE (ISO8601, opcional)
        status: Status da tarefa para filtrar (opcional)
        
    Returns:
        Conjunto de IDs de tarefas únicos (deduplicados)
    """
    task_ids = set()
    
    # Normalizar datas se fornecidas
    # A API Bitrix24 pode aceitar datas em diferentes formatos
    # Vamos tentar o formato ISO8601 completo primeiro
    if activity_from:
        activity_from_normalized = normalize_iso8601(activity_from)
        logger.info(f"Data inicial: '{activity_from}' -> '{activity_from_normalized}'")
        activity_from = activity_from_normalized
    if activity_to:
        activity_to_normalized = normalize_iso8601(activity_to)
        logger.info(f"Data final: '{activity_to}' -> '{activity_to_normalized}'")
        activity_to = activity_to_normalized
    
    logger.info(f"Coletando tarefas para {len(scope_ids)} colaborador(es)...")
    if activity_from or activity_to:
        logger.info(f"Filtros de data ACTIVITY_DATE aplicados:")
        logger.info(f"  >= {activity_from or 'N/A'}")
        logger.info(f"  <= {activity_to or 'N/A'}")
        logger.info(f"  (Formato: ISO8601 com timezone -03:00)")
    
    for user_id in scope_ids:
        # Buscar tarefas onde o usuário é responsável
        filters_responsible = {"filter[RESPONSIBLE_ID]": user_id}
        if activity_from:
            filters_responsible["filter[>=ACTIVITY_DATE]"] = activity_from
            logger.info(f"Filtro aplicado: filter[>=ACTIVITY_DATE] = {activity_from}")
        if activity_to:
            filters_responsible["filter[<=ACTIVITY_DATE]"] = activity_to
            logger.info(f"Filtro aplicado: filter[<=ACTIVITY_DATE] = {activity_to}")
        if status:
            filters_responsible["filter[STATUS]"] = status
        
        # Buscar tarefas onde o usuário é participante
        filters_accomplice = {"filter[ACCOMPLICE]": user_id}
        if activity_from:
            filters_accomplice["filter[>=ACTIVITY_DATE]"] = activity_from
        if activity_to:
            filters_accomplice["filter[<=ACTIVITY_DATE]"] = activity_to
        if status:
            filters_accomplice["filter[STATUS]"] = status
        
        # Coletar tarefas (responsável)
        start = 0
        tasks_found_for_user = 0
        while True:
            try:
                response = client.list_tasks(filters_responsible, start=start)
                # A resposta pode vir em diferentes formatos
                result = response.get("result", {})
                if isinstance(result, list):
                    tasks = result
                else:
                    tasks = result.get("tasks", [])
                
                if not tasks:
                    break
                
                tasks_found_for_user += len(tasks)
                
                for task in tasks:
                    task_id = normalize_task_field(task, "id") or normalize_task_field(task, "ID")
                    if task_id:
                        task_ids.add(int(task_id))
                
                # Verificar se há mais páginas
                # O total pode estar em response["total"] ou response["result"]["total"]
                total = response.get("total", 0)
                if not total and isinstance(result, dict):
                    total = result.get("total", 0)
                
                # Se não encontrou total, verificar se há mais tarefas pela quantidade retornada
                if not total:
                    # Se retornou menos que PAGINATION_SIZE, provavelmente é a última página
                    if len(tasks) < PAGINATION_SIZE:
                        break
                elif start + len(tasks) >= total:
                    break
                
                start += PAGINATION_SIZE
            
            except Exception as e:
                logger.warning(f"Erro ao buscar tarefas (responsável) para usuário {user_id}: {e}")
                break
        
        if tasks_found_for_user > 0:
            logger.info(f"Usuário {user_id} (responsável): {tasks_found_for_user} tarefas encontradas")
        
        # Coletar tarefas (participante)
        start = 0
        tasks_found_for_user = 0
        while True:
            try:
                response = client.list_tasks(filters_accomplice, start=start)
                # A resposta pode vir em diferentes formatos
                result = response.get("result", {})
                if isinstance(result, list):
                    tasks = result
                else:
                    tasks = result.get("tasks", [])
                
                if not tasks:
                    break
                
                for task in tasks:
                    task_id = normalize_task_field(task, "id") or normalize_task_field(task, "ID")
                    if task_id:
                        task_ids.add(int(task_id))
                
                tasks_found_for_user += len(tasks)
                
                # Verificar se há mais páginas
                # O total pode estar em response["total"] ou response["result"]["total"]
                total = response.get("total", 0)
                if not total and isinstance(result, dict):
                    total = result.get("total", 0)
                
                # Se não encontrou total, verificar se há mais tarefas pela quantidade retornada
                if not total:
                    # Se retornou menos que PAGINATION_SIZE, provavelmente é a última página
                    if len(tasks) < PAGINATION_SIZE:
                        break
                elif start + len(tasks) >= total:
                    break
                
                start += PAGINATION_SIZE
            
            except Exception as e:
                logger.warning(f"Erro ao buscar tarefas (participante) para usuário {user_id}: {e}")
                break
        
        if tasks_found_for_user > 0:
            logger.info(f"Usuário {user_id} (participante): {tasks_found_for_user} tarefas encontradas")
    
    logger.info(f"Coletados {len(task_ids)} IDs únicos de tarefas")
    return task_ids


def normalize_task_field(task: Dict[str, Any], field_name: str) -> Any:
    """
    Normaliza campo de tarefa que pode vir em diferentes formatos (case-sensitive/insensitive).
    
    Args:
        task: Dicionário da tarefa
        field_name: Nome do campo (ex: "id", "title")
        
    Returns:
        Valor do campo normalizado ou None
    """
    # Tentar diferentes variações
    variations = [
        field_name,
        field_name.upper(),
        field_name.lower(),
        field_name.capitalize()
    ]
    
    for var in variations:
        if var in task:
            return task[var]
    
    return None


def normalize_accomplices(accomplices: Any) -> List[int]:
    """
    Normaliza lista de participantes que pode vir como int[], dict[], string "1,2,3" ou None.
    
    Args:
        accomplices: Lista de participantes (pode ser int[], dict[], string, ou None)
        
    Returns:
        Lista de IDs (int)
    """
    if not accomplices:
        return []
    
    if isinstance(accomplices, list):
        result = []
        for item in accomplices:
            if isinstance(item, int):
                result.append(item)
            elif isinstance(item, dict):
                user_id = item.get("ID") or item.get("id") or item.get("USER_ID") or item.get("userId")
                if user_id:
                    result.append(int(user_id))
            elif isinstance(item, str):
                try:
                    result.append(int(item.strip()))
                except (ValueError, TypeError):
                    pass
        return result
    
    if isinstance(accomplices, str):
        result = []
        for part in accomplices.replace(" ", "").split(","):
            if part:
                try:
                    result.append(int(part))
                except (ValueError, TypeError):
                    pass
        return result
    
    if isinstance(accomplices, dict):
        # API pode retornar {"123": "1", "456": "1"} (IDs como chaves)
        result = []
        for k in accomplices:
            try:
                result.append(int(k))
            except (ValueError, TypeError):
                pass
        return result
    
    return []


def enrich_tasks(
    client: BitrixClient,
    task_ids: Set[int],
    scope_ids: List[int],
    collaborators_map: Dict[int, Dict[str, str]]
) -> List[Dict[str, Any]]:
    """
    Enriquece tarefas com detalhes completos, normalizando campos e resolvendo IDs para nomes.
    
    Args:
        client: Instância do BitrixClient
        task_ids: Conjunto de IDs de tarefas
        scope_ids: Lista de IDs do escopo (para identificar "Seu_time_envolvido")
        collaborators_map: Mapeamento user_id -> {name, dept}
        
    Returns:
        Lista de tarefas enriquecidas
    """
    task_ids_list = list(task_ids)
    total = len(task_ids_list)
    
    logger.info(f"Enriquecendo {total} tarefas...")
    
    # Buscar detalhes em batch
    commands = [
        {"method": "tasks.task.get", "params": {"taskId": task_id}}
        for task_id in task_ids_list
    ]
    
    responses = client._batch(commands)
    
    enriched_tasks = []
    
    for i, response in enumerate(responses):
        task_id = task_ids_list[i]
        
        if not response:
            logger.warning(f"Resposta vazia para tarefa {task_id}")
            continue
        
        try:
            # A resposta do batch vem como {"task": {...}} diretamente
            # ou pode vir como {"result": {"task": {...}}}
            task = None
            if isinstance(response, dict):
                if "task" in response:
                    task = response["task"]
                elif "result" in response:
                    task = response["result"].get("task", {})
            
            if not task:
                logger.warning(f"Tarefa {task_id} não encontrada na resposta")
                continue
            
            # Normalizar campos
            # Garantir que task_id sempre seja um int válido
            task_id_value = normalize_task_field(task, "id") or normalize_task_field(task, "ID") or task_id
            try:
                task_id_int = int(task_id_value)
            except (ValueError, TypeError):
                logger.warning(f"ID de tarefa inválido: {task_id_value}. Usando {task_id}.")
                task_id_int = int(task_id)
            
            # Extrair tempo total gasto (timeSpentInLogs) se disponível
            time_spent_in_logs = normalize_task_field(task, "timeSpentInLogs") or normalize_task_field(task, "TIME_SPENT_IN_LOGS")
            if time_spent_in_logs:
                try:
                    time_spent_seconds = int(time_spent_in_logs)
                except (ValueError, TypeError):
                    time_spent_seconds = None
            else:
                time_spent_seconds = None
            
            created_date_raw = normalize_task_field(task, "createdDate") or normalize_task_field(task, "CREATED_DATE") or normalize_task_field(task, "DATE_CREATE") or ""
            normalized_task = {
                "task_id": task_id_int,
                "title": str(normalize_task_field(task, "title") or normalize_task_field(task, "TITLE") or ""),
                "status": str(normalize_task_field(task, "status") or normalize_task_field(task, "STATUS") or ""),
                "deadline": str(normalize_task_field(task, "deadline") or normalize_task_field(task, "DEADLINE") or ""),
                "activity_date": str(normalize_task_field(task, "activityDate") or normalize_task_field(task, "ACTIVITY_DATE") or ""),
                "created_date": str(created_date_raw) if created_date_raw else "",
                "time_spent_in_logs": time_spent_seconds,  # Tempo total em segundos (fallback quando não há lançamentos individuais)
            }
            
            # Resolver responsável
            responsible_id = normalize_task_field(task, "responsibleId") or normalize_task_field(task, "RESPONSIBLE_ID")
            if responsible_id:
                responsible_id = int(responsible_id)
                responsible_info = collaborators_map.get(responsible_id, {})
                normalized_task["responsible_id"] = responsible_id
                normalized_task["responsible_name"] = responsible_info.get("name", f"USER_{responsible_id}")
            else:
                normalized_task["responsible_id"] = None
                normalized_task["responsible_name"] = ""
            
            # Resolver participantes (ACCOMPLICES ou MEMBERS da API)
            accomplices_raw = (
                normalize_task_field(task, "accomplices")
                or normalize_task_field(task, "ACCOMPLICES")
                or normalize_task_field(task, "members")
                or normalize_task_field(task, "MEMBERS")
                or []
            )
            accomplices_ids = normalize_accomplices(accomplices_raw)
            normalized_task["accomplices_ids"] = accomplices_ids
            normalized_task["accomplices_names"] = [
                collaborators_map.get(acc_id, {}).get("name", f"USER_{acc_id}")
                for acc_id in accomplices_ids
            ]
            normalized_task["scope_involved"] = ""  # mantido para compatibilidade (coluna removida do Excel)

            # Coletar departamentos de todas as pessoas envolvidas
            departments = set()
            if normalized_task["responsible_id"]:
                dept = collaborators_map.get(normalized_task["responsible_id"], {}).get("dept", "")
                if dept:
                    departments.add(dept)
            for acc_id in accomplices_ids:
                dept = collaborators_map.get(acc_id, {}).get("dept", "")
                if dept:
                    departments.add(dept)
            normalized_task["departments"] = ", ".join(sorted(departments)) if departments else ""
            
            enriched_tasks.append(normalized_task)
        
        except Exception as e:
            logger.error(f"Erro ao processar tarefa {task_id}: {e}")
            continue
    
    logger.info(f"Tarefas enriquecidas: {len(enriched_tasks)}/{total}")
    return enriched_tasks
