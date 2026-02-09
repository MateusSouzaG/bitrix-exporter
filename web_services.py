"""Serviços web para integração da lógica de exportação."""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from io import BytesIO

from config import validate_config
from bitrix_client import BitrixClient
from excel_handler import read_collaborators_sheet, write_tasks_excel
from task_processor import determine_scope_ids, collect_task_ids, enrich_tasks
from time_entries_handler import fetch_all_time_entries, process_time_entries, calculate_total_time
from users_config import User

logger = logging.getLogger(__name__)


def format_time_entry_date(date_str: str) -> str:
    """Formata data do lançamento para exibição (ex: 28/04/2025 13:56)."""
    if not date_str or not str(date_str).strip():
        return ""
    date_str = str(date_str).strip()
    try:
        # Bitrix pode retornar ISO (2025-04-28T13:56:00) ou "YYYY-MM-DD HH:MM:SS"
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%d/%m/%Y %H:%M", "%d/%m/%Y"):
            try:
                dt = datetime.strptime(date_str.replace("Z", "").split(".")[0], fmt)
                return dt.strftime("%d/%m/%Y %H:%M")
            except ValueError:
                continue
    except Exception:
        pass
    return date_str


def format_time(seconds: float) -> str:
    """Formata tempo em segundos para string legível (ex: "2h 30min")."""
    # Garantir que seconds seja um número (pode vir como string)
    try:
        seconds = float(seconds) if seconds else 0.0
    except (ValueError, TypeError):
        seconds = 0.0
    
    if seconds == 0:
        return ""
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}min")
    if secs > 0 and hours == 0:
        parts.append(f"{secs}s")
    
    return " ".join(parts) if parts else "0s"


def combine_tasks_with_time_entries(
    enriched_tasks: List[Dict[str, Any]],
    time_entries_map: Dict[int, List[Dict[str, Any]]],
    collaborators_map: Dict[int, Dict[str, str]]
) -> List[Dict[str, Any]]:
    """Combina tarefas enriquecidas com lançamentos de tempo."""
    excel_rows = []
    
    for task in enriched_tasks:
        task_id = task["task_id"]
        time_entries = time_entries_map.get(task_id, [])
        
        processed_entries = process_time_entries(time_entries, collaborators_map)
        total_time = calculate_total_time(processed_entries)
        
        # Se não há lançamentos individuais mas há timeSpentInLogs, usar como fallback
        if not processed_entries and task.get("time_spent_in_logs"):
            time_spent_seconds = task.get("time_spent_in_logs", 0)
            total_time = {"total_seconds": time_spent_seconds}
            logger.info(f"Tarefa {task_id}: Usando timeSpentInLogs ({time_spent_seconds}s) como fallback (webhook sem permissão para lançamentos individuais)")
        
        # Garantir que todos os campos existam e sejam strings válidas
        accomplices_names = task.get("accomplices_names") or []
        participants_str = ", ".join(str(n) for n in accomplices_names) if accomplices_names else ""
        base_row = {
            "Task_ID": task.get("task_id", 0),
            "Título": str(task.get("title", "")),
            "Status": str(task.get("status", "")),
            "Deadline": str(task.get("deadline", "")) if task.get("deadline") else "",
            "Criada_Em": format_time_entry_date(task.get("created_date", "") or ""),
            "Responsável": str(task.get("responsible_name", "")),
            "Participantes": participants_str,
            "Tempo_Total_Gasto": format_time(total_time.get("total_seconds", 0)),
            "Departamentos_Selecionados": str(task.get("departments", "")),
            "Atividade_em": str(task.get("activity_date", "")) if task.get("activity_date") else ""
        }
        
        if processed_entries:
            # Quem_Lançou vem estritamente do USER_ID do item de tempo (API); só exibir quem tem tempo > 0
            entries_with_time = [e for e in processed_entries if (e.get("seconds") or 0) > 0]
            if entries_with_time:
                for entry in entries_with_time:
                    row = base_row.copy()
                    row["Tempo_Lançamento"] = format_time(entry["seconds"])
                    row["Quem_Lançou"] = entry["user_name"]
                    row["Data do lançamento"] = format_time_entry_date(entry.get("created_date", "") or "")
                    row["Comentário_Lançamento"] = entry["comment"]
                    excel_rows.append(row)
            else:
                # Todos os lançamentos tinham 0 segundos - não atribuir a ninguém
                row = base_row.copy()
                row["Tempo_Lançamento"] = ""
                row["Quem_Lançou"] = ""
                row["Data do lançamento"] = ""
                row["Comentário_Lançamento"] = ""
                excel_rows.append(row)
        elif task.get("time_spent_in_logs"):
            # Não temos lançamentos individuais, mas temos tempo total - criar uma linha com o total
            row = base_row.copy()
            row["Tempo_Lançamento"] = format_time(task.get("time_spent_in_logs", 0))
            row["Quem_Lançou"] = "Tempo total (detalhes não disponíveis)"
            row["Data do lançamento"] = ""
            row["Comentário_Lançamento"] = "Webhook sem permissão para lançamentos individuais. Mostrando tempo total da tarefa."
            excel_rows.append(row)
        else:
            # Sem lançamentos e sem tempo total
            row = base_row.copy()
            row["Tempo_Lançamento"] = ""
            row["Quem_Lançou"] = ""
            row["Data do lançamento"] = ""
            row["Comentário_Lançamento"] = ""
            excel_rows.append(row)
    
    return excel_rows


def get_available_departments(collaborators_map: Dict[int, Dict[str, str]]) -> List[str]:
    """Retorna lista de departamentos disponíveis."""
    departments = set()
    for info in collaborators_map.values():
        dept = info.get("dept", "")
        if dept:
            departments.add(dept.upper())
    return sorted(list(departments))


def filter_departments_by_user_access(
    departments: List[str],
    user: User
) -> List[str]:
    """Filtra departamentos baseado no acesso do usuário."""
    if user.role == "admin":
        return departments
    if user.allowed_departments is None:
        return []
    return [d for d in departments if d.upper() in [ad.upper() for ad in user.allowed_departments]]


def filter_collaborator_names_by_user_access(
    collaborators_map: Dict[int, Dict[str, str]],
    user: User
) -> List[str]:
    """Retorna apenas os nomes de colaboradores que o usuário pode acessar (admin = todos, supervisor = só do seu departamento)."""
    if user.role == "admin":
        return sorted({info["name"] for info in collaborators_map.values() if info.get("name")})
    if user.allowed_departments is None:
        return []
    allowed_upper = [d.upper() for d in user.allowed_departments]
    names = {
        info["name"] for info in collaborators_map.values()
        if info.get("name") and (info.get("dept") or "").strip().upper() in allowed_upper
    }
    return sorted(names)


def export_tasks_to_excel_bytes(
    user: User,
    dept: Optional[str] = None,
    user_substring: Optional[str] = None,
    activity_from: Optional[str] = None,
    activity_to: Optional[str] = None,
    status: Optional[str] = None,
    collaborators_file: str = "Planilha de colaboradores.xlsx"
) -> Tuple[BytesIO, int]:
    """
    Exporta tarefas para Excel e retorna como BytesIO.
    
    Returns:
        Tuple (BytesIO do Excel, número de linhas exportadas)
    """
    try:
        # Validar configuração
        validate_config()
        
        # Inicializar cliente
        client = BitrixClient()
        
        # Ler planilha de colaboradores
        collaborators_map = read_collaborators_sheet(collaborators_file)
        
        # Verificar acesso do usuário ao departamento
        if dept:
            if not user.has_access_to_department(dept):
                raise ValueError(f"Usuário não tem acesso ao departamento {dept}")
        
        # Determinar escopo de IDs
        scope_ids = determine_scope_ids(
            collaborators_map,
            dept=dept,
            user_substring=user_substring
        )
        # Supervisores: restringir ao departamento permitido (evita ver outros mesmo escolhendo por nome)
        if user.role != "admin" and user.allowed_departments and scope_ids:
            allowed_upper = [d.upper() for d in user.allowed_departments]
            scope_ids = [
                uid for uid in scope_ids
                if ((collaborators_map.get(uid) or {}).get("dept") or "").strip().upper() in allowed_upper
            ]
            logger.info(f"Escopo filtrado por acesso do supervisor: {len(scope_ids)} colaborador(es)")
        
        logger.info(f"Escopo determinado: {len(scope_ids)} colaborador(es)")
        if scope_ids:
            logger.info(f"IDs do escopo: {list(scope_ids)[:10]}...")  # Mostrar primeiros 10
        
        if not scope_ids:
            logger.warning("Nenhum colaborador encontrado no escopo. Retornando Excel vazio.")
            excel_rows = []
        else:
            # Coletar IDs de tarefas
            logger.info(f"Coletando tarefas com filtros: from={activity_from}, to={activity_to}, status={status}")
            task_ids = collect_task_ids(
                client,
                scope_ids,
                activity_from=activity_from,
                activity_to=activity_to,
                status=status
            )
            
            logger.info(f"Tarefas encontradas: {len(task_ids)} IDs únicos")
            if task_ids:
                logger.info(f"Exemplos de IDs de tarefas: {list(task_ids)[:10]}...")
            
            if not task_ids:
                logger.warning("Nenhuma tarefa encontrada com os filtros fornecidos.")
                excel_rows = []
            else:
                # Enriquecer tarefas
                logger.info("Enriquecendo tarefas com detalhes...")
                enriched_tasks = enrich_tasks(client, task_ids, scope_ids, collaborators_map)
                logger.info(f"Tarefas enriquecidas: {len(enriched_tasks)}")
                
                if not enriched_tasks:
                    logger.error(f"CRÍTICO: {len(task_ids)} tarefas encontradas mas 0 foram enriquecidas!")
                    logger.error("Isso pode indicar um problema no método _batch ou no parsing das respostas.")
                    excel_rows = []
                else:
                    # Buscar lançamentos de tempo
                    logger.info("Buscando lançamentos de tempo...")
                    time_entries_map = fetch_all_time_entries(client, task_ids)
                    logger.info(f"Lançamentos encontrados para {len(time_entries_map)} tarefas")
                    
                    # Combinar tarefas com lançamentos de tempo
                    logger.info("Combinando tarefas com lançamentos de tempo...")
                    excel_rows = combine_tasks_with_time_entries(
                        enriched_tasks,
                        time_entries_map,
                        collaborators_map
                    )
                    logger.info(f"Total de linhas geradas para Excel: {len(excel_rows)}")
        
        # Gerar Excel em memória
        output = BytesIO()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_filename = f"temp_export_{timestamp}.xlsx"
        
        # Escrever Excel
        write_tasks_excel(excel_rows, temp_filename)
        
        # Ler arquivo temporário e copiar para BytesIO
        with open(temp_filename, "rb") as f:
            output.write(f.read())
        
        # Limpar arquivo temporário
        import os
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        
        output.seek(0)
        return output, len(excel_rows)
        
    except Exception as e:
        logger.error(f"Erro durante exportação: {e}", exc_info=True)
        raise
