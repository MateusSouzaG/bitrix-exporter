"""Teste direto da API Bitrix24 para diagnosticar problemas."""
from bitrix_client import BitrixClient
from config import validate_config
from excel_handler import read_collaborators_sheet
from task_processor import determine_scope_ids
import json

def test_api_direct():
    """Testa a API diretamente para ver o que está acontecendo."""
    print("=" * 60)
    print("TESTE DIRETO DA API BITRIX24")
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
    
    # Teste 1: Sem filtros
    print("\n" + "=" * 60)
    print("TESTE 1: Sem filtros de data")
    print("=" * 60)
    filters1 = {"filter[RESPONSIBLE_ID]": user_id}
    try:
        response1 = client.list_tasks(filters1, start=0)
        print(f"Resposta completa: {json.dumps(response1, indent=2, ensure_ascii=False)[:500]}")
        result1 = response1.get("result", {})
        if isinstance(result1, list):
            tasks1 = result1
        else:
            tasks1 = result1.get("tasks", [])
        print(f"\nTotal de tarefas encontradas: {len(tasks1)}")
        if tasks1:
            print(f"Primeira tarefa: {json.dumps(tasks1[0], indent=2, ensure_ascii=False)[:300]}")
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()
    
    # Teste 2: Com filtro de data (formato atual)
    print("\n" + "=" * 60)
    print("TESTE 2: Com filtro ACTIVITY_DATE (formato atual)")
    print("=" * 60)
    from date_filters import get_date_range_for_preset
    date_range = get_date_range_for_preset("este_mes")
    if date_range:
        activity_from, activity_to = date_range
        print(f"Filtros: from={activity_from}, to={activity_to}")
        filters2 = {
            "filter[RESPONSIBLE_ID]": user_id,
            "filter[>=ACTIVITY_DATE]": activity_from,
            "filter[<=ACTIVITY_DATE]": activity_to
        }
        try:
            response2 = client.list_tasks(filters2, start=0)
            print(f"Resposta completa: {json.dumps(response2, indent=2, ensure_ascii=False)[:500]}")
            result2 = response2.get("result", {})
            if isinstance(result2, list):
                tasks2 = result2
            else:
                tasks2 = result2.get("tasks", [])
            print(f"\nTotal de tarefas encontradas: {len(tasks2)}")
            if tasks2:
                print(f"Primeira tarefa: {json.dumps(tasks2[0], indent=2, ensure_ascii=False)[:300]}")
        except Exception as e:
            print(f"ERRO: {e}")
            import traceback
            traceback.print_exc()
    
    # Teste 3: Verificar formato de data alternativo
    print("\n" + "=" * 60)
    print("TESTE 3: Com filtro ACTIVITY_DATE (formato alternativo)")
    print("=" * 60)
    if date_range:
        # Tentar sem timezone
        activity_from_simple = activity_from.split("-03:00")[0] if "-03:00" in activity_from else activity_from
        activity_to_simple = activity_to.split("-03:00")[0] if "-03:00" in activity_to else activity_to
        print(f"Filtros (sem timezone): from={activity_from_simple}, to={activity_to_simple}")
        filters3 = {
            "filter[RESPONSIBLE_ID]": user_id,
            "filter[>=ACTIVITY_DATE]": activity_from_simple,
            "filter[<=ACTIVITY_DATE]": activity_to_simple
        }
        try:
            response3 = client.list_tasks(filters3, start=0)
            result3 = response3.get("result", {})
            if isinstance(result3, list):
                tasks3 = result3
            else:
                tasks3 = result3.get("tasks", [])
            print(f"\nTotal de tarefas encontradas: {len(tasks3)}")
        except Exception as e:
            print(f"ERRO: {e}")

if __name__ == "__main__":
    test_api_direct()
