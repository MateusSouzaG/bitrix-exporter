"""Teste específico para a tarefa 25943 que tem lançamentos de tempo."""
from bitrix_client import BitrixClient
from config import validate_config
import json

def test_task_25943():
    """Testa diferentes formas de buscar lançamentos da tarefa 25943."""
    validate_config()
    client = BitrixClient()
    
    task_id = 25943
    
    print("=" * 60)
    print(f"TESTE ESPECÍFICO: Tarefa {task_id} (tem lançamentos de tempo)")
    print("=" * 60)
    
    # 1. Buscar dados completos da tarefa
    print("\n1. Dados completos da tarefa:")
    try:
        task_data = client.get_task(task_id)
        print(f"   Título: {task_data.get('title', 'N/A')}")
        print(f"   Status: {task_data.get('status', 'N/A')}")
        
        # Verificar campos relacionados a tempo
        time_fields = {k: v for k, v in task_data.items() if any(term in k.lower() for term in ['time', 'elapsed', 'spent', 'duration'])}
        if time_fields:
            print(f"\n   Campos relacionados a tempo:")
            for key, value in time_fields.items():
                print(f"     {key}: {value}")
        else:
            print(f"   Nenhum campo de tempo encontrado diretamente")
    except Exception as e:
        print(f"   ERRO: {e}")
    
    # 2. Tentar método atual (usando BitrixClient.get_time_entries)
    print("\n2. Método atual (get_time_entries):")
    try:
        entries = client.get_time_entries(task_id)
        print(f"   Lançamentos retornados: {len(entries)}")
        if entries:
            print(f"   [OK] SUCESSO! Encontrados {len(entries)} lançamentos")
            print(f"   Primeiro lançamento: {json.dumps(entries[0], indent=2, ensure_ascii=False)[:300]}")
        else:
            print(f"   [AVISO] Método retornou lista vazia")
    except Exception as e:
        print(f"   [ERRO] {e}")
    
    # 3. Tentar com método direto _request
    print("\n3. Método direto _request (tasks.task.elapseditem.get):")
    try:
        response = client._request("tasks.task.elapseditem.get", {"taskId": task_id})
        print(f"   Resposta completa: {json.dumps(response, indent=2, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"   ERRO: {e}")
        print(f"   Tipo do erro: {type(e).__name__}")
    
    # 4. Verificar se há algum campo na tarefa que contenha referência aos lançamentos
    print("\n4. Verificando campos que podem referenciar lançamentos:")
    try:
        task_data = client.get_task(task_id)
        # Procurar por IDs ou referências
        for key, value in task_data.items():
            if isinstance(value, (list, dict)) and value:
                if 'elapsed' in key.lower() or 'time' in key.lower() or 'entry' in key.lower():
                    print(f"   {key}: {type(value).__name__} = {value}")
    except Exception as e:
        print(f"   ERRO: {e}")

if __name__ == "__main__":
    test_task_25943()
