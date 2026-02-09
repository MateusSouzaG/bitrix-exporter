"""Teste métodos alternativos para buscar lançamentos de tempo."""
from bitrix_client import BitrixClient
from config import validate_config
import json

def test_alternative_methods():
    """Testa métodos alternativos."""
    validate_config()
    client = BitrixClient()
    
    task_id = 25857
    
    print("=" * 60)
    print(f"TESTE: Métodos alternativos para lançamentos de tempo")
    print(f"Tarefa: {task_id}")
    print("=" * 60)
    
    # Método 1: tasks.task.get com seleção de campos
    print("\n1. Testando tasks.task.get com seleção de campos de tempo:")
    try:
        params = {
            "taskId": task_id,
            "select": ["timeSpentInLogs", "elapsedItems", "timeEntries", "elapsedTime"]
        }
        response1 = client._request("tasks.task.get", params)
        result1 = response1.get("result", {}).get("task", {})
        print(f"   Campos de tempo encontrados:")
        for field in ["timeSpentInLogs", "elapsedItems", "timeEntries", "elapsedTime"]:
            if field in result1:
                print(f"     {field}: {result1[field]}")
    except Exception as e:
        print(f"   ERRO: {e}")
    
    # Método 2: tasks.elapseditem.get (sem task.)
    print("\n2. Testando tasks.elapseditem.get (sem 'task.'):")
    try:
        response2 = client._request("tasks.elapseditem.get", {"taskId": task_id})
        print(f"   SUCESSO: {json.dumps(response2, indent=2, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"   ERRO: {e}")
    
    # Método 3: tasks.elapseditem.list
    print("\n3. Testando tasks.elapseditem.list:")
    try:
        response3 = client._request("tasks.elapseditem.list", {"taskId": task_id})
        print(f"   SUCESSO: {json.dumps(response3, indent=2, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"   ERRO: {e}")
    
    # Método 4: Verificar se precisa passar filtros
    print("\n4. Testando tasks.task.elapseditem.get com filtros:")
    try:
        params4 = {
            "taskId": task_id,
            "filter": {"TASK_ID": task_id}
        }
        response4 = client._request("tasks.task.elapseditem.get", params4)
        print(f"   SUCESSO: {json.dumps(response4, indent=2, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"   ERRO: {e}")
    
    # Método 5: Verificar permissões do webhook
    print("\n5. Verificando informações do webhook:")
    try:
        # Tentar buscar informações do usuário atual
        user_info = client._request("user.current", {})
        print(f"   Usuário do webhook: {json.dumps(user_info, indent=2, ensure_ascii=False)[:300]}")
    except Exception as e:
        print(f"   ERRO: {e}")

if __name__ == "__main__":
    test_alternative_methods()
