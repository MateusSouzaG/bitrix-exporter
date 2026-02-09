"""Teste de paginação para verificar se está coletando todas as tarefas."""
from bitrix_client import BitrixClient
from config import validate_config
from excel_handler import read_collaborators_sheet
from task_processor import determine_scope_ids, collect_task_ids
from date_filters import get_date_range_for_preset

def test_pagination():
    """Testa se a paginação está funcionando corretamente."""
    print("=" * 60)
    print("TESTE DE PAGINACAO")
    print("=" * 60)
    
    validate_config()
    client = BitrixClient()
    
    # Ler colaboradores
    collaborators_map = read_collaborators_sheet("Planilha de colaboradores.xlsx")
    scope_ids = determine_scope_ids(collaborators_map, user_substring="Mateus")
    
    if not scope_ids:
        print("Nenhum colaborador encontrado")
        return
    
    user_id = list(scope_ids)[0]
    print(f"\nTestando com usuário ID: {user_id}")
    
    # Teste sem filtros
    print("\n" + "=" * 60)
    print("TESTE: Sem filtros de data")
    print("=" * 60)
    task_ids_no_filter = collect_task_ids(client, list(scope_ids), activity_from=None, activity_to=None, status=None)
    print(f"Total de IDs únicos coletados: {len(task_ids_no_filter)}")
    print(f"Primeiros 10 IDs: {list(task_ids_no_filter)[:10]}")
    
    # Teste com filtro de data
    print("\n" + "=" * 60)
    print("TESTE: Com filtro de data (este mês)")
    print("=" * 60)
    date_range = get_date_range_for_preset("este_mes")
    if date_range:
        activity_from, activity_to = date_range
        print(f"Filtros: {activity_from} a {activity_to}")
        task_ids_with_filter = collect_task_ids(client, list(scope_ids), activity_from=activity_from, activity_to=activity_to, status=None)
        print(f"Total de IDs únicos coletados: {len(task_ids_with_filter)}")
        print(f"Primeiros 10 IDs: {list(task_ids_with_filter)[:10]}")
        
        if len(task_ids_with_filter) == 0:
            print("\n[PROBLEMA] Nenhuma tarefa encontrada com filtro de data!")
            print("Isso pode indicar:")
            print("  1. O filtro ACTIVITY_DATE não está funcionando corretamente")
            print("  2. As tarefas não têm ACTIVITY_DATE no período especificado")
            print("  3. O formato da data pode estar incorreto")
        else:
            print(f"\n[OK] Encontradas {len(task_ids_with_filter)} tarefas com filtro")

if __name__ == "__main__":
    test_pagination()
