"""Teste rápido apenas do enriquecimento de tarefas."""
from bitrix_client import BitrixClient
from config import validate_config
from excel_handler import read_collaborators_sheet
from task_processor import determine_scope_ids, collect_task_ids, enrich_tasks
from date_filters import get_date_range_for_preset

def test_enrichment():
    """Testa apenas o enriquecimento."""
    print("=" * 60)
    print("TESTE DE ENRIQUECIMENTO")
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
    
    # Coletar tarefas com filtro (limitado a 10 para teste rápido)
    date_range = get_date_range_for_preset("este_mes")
    activity_from, activity_to = date_range if date_range else (None, None)
    
    print(f"\nColetando tarefas...")
    all_task_ids = collect_task_ids(client, list(scope_ids), activity_from=activity_from, activity_to=activity_to, status=None)
    print(f"Total de tarefas encontradas: {len(all_task_ids)}")
    
    # Limitar a 10 para teste rápido
    task_ids = set(list(all_task_ids)[:10])
    print(f"Testando com {len(task_ids)} tarefas...")
    
    # Enriquecer tarefas
    print(f"\nEnriquecendo {len(task_ids)} tarefas...")
    enriched_tasks = enrich_tasks(client, task_ids, list(scope_ids), collaborators_map)
    print(f"Tarefas enriquecidas: {len(enriched_tasks)}")
    
    if enriched_tasks:
        print(f"\n[OK] Enriquecimento funcionando!")
        print(f"Primeira tarefa enriquecida:")
        print(f"  ID: {enriched_tasks[0].get('task_id')}")
        print(f"  Título: {enriched_tasks[0].get('title')}")
        print(f"  Status: {enriched_tasks[0].get('status')}")
        print(f"  Responsável: {enriched_tasks[0].get('responsible_name')}")
    else:
        print(f"\n[ERRO] Nenhuma tarefa foi enriquecida!")

if __name__ == "__main__":
    test_enrichment()
