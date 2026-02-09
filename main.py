"""CLI principal para exportação de tarefas do Bitrix24."""
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from config import validate_config
from bitrix_client import BitrixClient
from excel_handler import read_collaborators_sheet, write_tasks_excel
from task_processor import determine_scope_ids, collect_task_ids, enrich_tasks
from time_entries_handler import fetch_all_time_entries, process_time_entries, calculate_total_time
from web_services import format_time_entry_date

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def format_time(seconds: float) -> str:
    """Formata tempo em segundos para string legível (ex: "2h 30min")."""
    if not seconds or seconds == 0:
        return ""
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}min")
    if secs > 0 and hours == 0:  # Só mostrar segundos se não houver horas
        parts.append(f"{secs}s")
    
    return " ".join(parts) if parts else "0s"


def combine_tasks_with_time_entries(
    enriched_tasks: List[Dict[str, Any]],
    time_entries_map: Dict[int, List[Dict[str, Any]]],
    collaborators_map: Dict[int, Dict[str, str]]
) -> List[Dict[str, Any]]:
    """
    Combina tarefas enriquecidas com lançamentos de tempo para gerar linhas do Excel.
    
    Cada tarefa pode gerar múltiplas linhas (uma por lançamento de tempo).
    Se não houver lançamentos, gera uma linha única.
    
    Args:
        enriched_tasks: Lista de tarefas enriquecidas
        time_entries_map: Mapeamento task_id -> [lançamentos processados]
        collaborators_map: Mapeamento user_id -> {name, dept}
        
    Returns:
        Lista de dicionários, cada um representando uma linha do Excel
    """
    excel_rows = []
    
    for task in enriched_tasks:
        task_id = task["task_id"]
        time_entries = time_entries_map.get(task_id, [])
        
        # Processar lançamentos de tempo
        processed_entries = process_time_entries(time_entries, collaborators_map)
        total_time = calculate_total_time(processed_entries)
        
        # Dados base da tarefa (repetidos em todas as linhas)
        accomplices_names = task.get("accomplices_names") or []
        participants_str = ", ".join(str(n) for n in accomplices_names) if accomplices_names else ""
        created_str = task.get("created_date", "") or ""
        base_row = {
            "Task_ID": task_id,
            "Título": task["title"],
            "Status": task["status"],
            "Deadline": task["deadline"] if task["deadline"] else "",
            "Criada_Em": format_time_entry_date(created_str) if created_str else "",
            "Responsável": task["responsible_name"],
            "Participantes": participants_str,
            "Tempo_Total_Gasto": format_time(total_time["total_seconds"]),
            "Departamentos_Selecionados": task["departments"],
            "Atividade_em": task["activity_date"] if task["activity_date"] else ""
        }
        
        if processed_entries:
            # Uma linha por lançamento de tempo
            for entry in processed_entries:
                row = base_row.copy()
                row["Tempo_Lançamento"] = format_time(entry["seconds"])
                row["Quem_Lançou"] = entry["user_name"]
                row["Data do lançamento"] = ""
                row["Comentário_Lançamento"] = entry["comment"]
                excel_rows.append(row)
        else:
            # Sem lançamentos: uma linha única com campos vazios
            row = base_row.copy()
            row["Tempo_Lançamento"] = ""
            row["Quem_Lançou"] = ""
            row["Data do lançamento"] = ""
            row["Comentário_Lançamento"] = ""
            excel_rows.append(row)
    
    return excel_rows


def main():
    """Função principal do CLI."""
    parser = argparse.ArgumentParser(
        description="Exporta tarefas do Bitrix24 para Excel com filtros por departamento/colaborador"
    )
    
    parser.add_argument(
        "--dept",
        type=str,
        help="Filtrar por departamento (ex: COMERCIAL, DTC, GI, RNA)"
    )
    
    parser.add_argument(
        "--user",
        type=str,
        help='Filtrar por colaborador (substring do nome, case-insensitive, ex: "João")'
    )
    
    parser.add_argument(
        "--active-from",
        type=str,
        help='Filtro de data inicial para "Estava ativo" (ISO8601, ex: "2024-01-01T00:00:00-03:00")'
    )
    
    parser.add_argument(
        "--active-to",
        type=str,
        help='Filtro de data final para "Estava ativo" (ISO8601, ex: "2024-12-31T23:59:59-03:00")'
    )
    
    parser.add_argument(
        "--status",
        type=str,
        help='Filtro de status (ex: "NEW", "IN_PROGRESS", "COMPLETED"). Omitir para trazer todos.'
    )
    
    parser.add_argument(
        "--input",
        type=str,
        default="Planilha de colaboradores.xlsx",
        help='Caminho para a planilha de colaboradores (padrão: "Planilha de colaboradores.xlsx")'
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Caminho do arquivo Excel de saída (padrão: Exportacao_Tarefas_YYYYMMDD_HHMMSS.xlsx)"
    )
    
    args = parser.parse_args()
    
    try:
        # Validar configuração
        validate_config()
        logger.info("Configuração validada com sucesso")
        
        # Inicializar cliente Bitrix24
        client = BitrixClient()
        logger.info("Cliente Bitrix24 inicializado")
        
        # Ler planilha de colaboradores
        collaborators_map = read_collaborators_sheet(args.input)
        
        # Determinar escopo de IDs
        scope_ids = determine_scope_ids(
            collaborators_map,
            dept=args.dept,
            user_substring=args.user
        )
        
        if not scope_ids:
            logger.error("Nenhum colaborador encontrado no escopo. Verifique os filtros.")
            sys.exit(1)
        
        # Coletar IDs de tarefas
        task_ids = collect_task_ids(
            client,
            scope_ids,
            activity_from=args.active_from,
            activity_to=args.active_to,
            status=args.status
        )
        
        if not task_ids:
            logger.warning("Nenhuma tarefa encontrada com os filtros fornecidos.")
            # Criar Excel vazio mesmo assim
            excel_rows = []
        else:
            # Enriquecer tarefas
            enriched_tasks = enrich_tasks(client, task_ids, scope_ids, collaborators_map)
            
            # Buscar lançamentos de tempo
            time_entries_map = fetch_all_time_entries(client, task_ids)
            
            # Combinar tarefas com lançamentos de tempo
            excel_rows = combine_tasks_with_time_entries(
                enriched_tasks,
                time_entries_map,
                collaborators_map
            )
        
        # Gerar caminho de saída
        if args.output:
            output_path = args.output
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"Exportacao_Tarefas_{timestamp}.xlsx"
        
        # Escrever Excel
        write_tasks_excel(excel_rows, output_path)
        
        logger.info(f"Exportação concluída com sucesso!")
        logger.info(f"Arquivo gerado: {output_path}")
        logger.info(f"Total de linhas: {len(excel_rows)}")
        
    except KeyboardInterrupt:
        logger.info("Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro durante a execução: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
