"""Teste do fluxo completo de exportação."""
from bitrix_client import BitrixClient
from config import validate_config
from excel_handler import read_collaborators_sheet
from task_processor import determine_scope_ids, collect_task_ids, enrich_tasks
from time_entries_handler import fetch_all_time_entries
from web_services import combine_tasks_with_time_entries
from date_filters import get_date_range_for_preset

def test_full_flow():
    """Testa o fluxo completo de exportação."""
    print("=" * 60)
    print("TESTE DO FLUXO COMPLETO")
    print("=" * 60)
    
    validate_config()
    client = BitrixClient()
    
    # Ler colaboradores
    collaborators_map = read_collaborators_sheet("Planilha de colaboradores.xlsx")
    scope_ids = determine_scope_ids(collaborators_map, user_substring="Mateus")
    
    if not scope_ids:
        print("Nenhum colaborador encontrado")
        return
    
    print(f"Colaboradores no escopo: {list(scope_ids)}")
    
    # Coletar tarefas com filtro
    date_range = get_date_range_for_preset("este_mes")
    activity_from, activity_to = date_range if date_range else (None, None)
    
    print(f"\nColetando tarefas...")
    task_ids = collect_task_ids(client, list(scope_ids), activity_from=activity_from, activity_to=activity_to, status=None)
    print(f"Tarefas encontradas: {len(task_ids)}")
    
    if not task_ids:
        print("[ERRO] Nenhuma tarefa encontrada!")
        return
    
    # Enriquecer tarefas
    print(f"\nEnriquecendo {len(task_ids)} tarefas...")
    enriched_tasks = enrich_tasks(client, task_ids, list(scope_ids), collaborators_map)
    print(f"Tarefas enriquecidas: {len(enriched_tasks)}")
    
    if not enriched_tasks:
        print("[ERRO] Nenhuma tarefa foi enriquecida!")
        return
    
    # Buscar lançamentos de tempo
    print(f"\nBuscando lançamentos de tempo...")
    time_entries_map = fetch_all_time_entries(client, task_ids)
    print(f"Lançamentos encontrados para {len(time_entries_map)} tarefas")
    
    # Combinar
    print(f"\nCombinando tarefas com lançamentos...")
    excel_rows = combine_tasks_with_time_entries(enriched_tasks, time_entries_map, collaborators_map)
    print(f"Linhas geradas para Excel: {len(excel_rows)}")
    
    if len(excel_rows) == 0:
        print("\n[PROBLEMA] Nenhuma linha foi gerada para o Excel!")
        print("Isso pode significar:")
        print("  1. As tarefas enriquecidas estão vazias")
        print("  2. Há um problema na função combine_tasks_with_time_entries")
    else:
        print(f"\n[OK] {len(excel_rows)} linhas prontas para exportação")
        print(f"Primeira linha: {excel_rows[0] if excel_rows else 'N/A'}")

if __name__ == "__main__":
    test_full_flow()
