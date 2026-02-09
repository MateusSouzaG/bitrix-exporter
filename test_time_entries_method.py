"""Teste para verificar o método correto de buscar lançamentos de tempo."""
from bitrix_client import BitrixClient
from config import validate_config
import json

def test_time_entries_methods():
    """Testa diferentes métodos para buscar lançamentos de tempo."""
    validate_config()
    client = BitrixClient()
    
    # Usar uma tarefa que você sabe que tem lançamentos
    task_id = 25857  # Ajuste para uma tarefa que você sabe que tem lançamentos
    
    print("=" * 60)
    print(f"TESTE DE MÉTODOS PARA LANÇAMENTOS DE TEMPO")
    print(f"Tarefa de teste: {task_id}")
    print("=" * 60)
    
    # Método 1: tasks.task.elapseditem.get (atual)
    print("\n1. Testando tasks.task.elapseditem.get (método atual):")
    try:
        response1 = client._request("tasks.task.elapseditem.get", {"taskId": task_id})
        print(f"   Status: SUCESSO")
        print(f"   Resposta: {json.dumps(response1, indent=2, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"   Status: ERRO - {e}")
    
    # Método 2: tasks.task.elapseditem.list
    print("\n2. Testando tasks.task.elapseditem.list:")
    try:
        response2 = client._request("tasks.task.elapseditem.list", {"taskId": task_id})
        print(f"   Status: SUCESSO")
        print(f"   Resposta: {json.dumps(response2, indent=2, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"   Status: ERRO - {e}")
    
    # Método 3: Verificar se os lançamentos vêm dentro de tasks.task.get
    print("\n3. Verificando se lançamentos vêm em tasks.task.get:")
    try:
        task_data = client.get_task(task_id)
        if "elapsedItems" in task_data or "elapsed" in task_data or "timeEntries" in task_data:
            print(f"   Status: SUCESSO - Encontrados campos relacionados a tempo")
            print(f"   Campos encontrados: {[k for k in task_data.keys() if 'elapsed' in k.lower() or 'time' in k.lower() or 'entry' in k.lower()]}")
            # Mostrar campos relacionados
            for key in task_data.keys():
                if 'elapsed' in key.lower() or 'time' in key.lower() or 'entry' in key.lower():
                    print(f"   {key}: {task_data[key]}")
        else:
            print(f"   Status: Não encontrados campos de tempo na resposta")
            print(f"   Campos disponíveis: {list(task_data.keys())[:20]}")
    except Exception as e:
        print(f"   Status: ERRO - {e}")
    
    # Método 4: tasks.task.elapseditem.getlist (se existir)
    print("\n4. Testando tasks.task.elapseditem.getlist:")
    try:
        response4 = client._request("tasks.task.elapseditem.getlist", {"taskId": task_id})
        print(f"   Status: SUCESSO")
        print(f"   Resposta: {json.dumps(response4, indent=2, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"   Status: ERRO - {e}")

if __name__ == "__main__":
    test_time_entries_methods()
