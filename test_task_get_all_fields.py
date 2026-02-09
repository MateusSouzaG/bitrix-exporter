"""Testa se os lançamentos vêm dentro de tasks.task.get quando solicitamos todos os campos."""
from bitrix_client import BitrixClient
from config import validate_config
import json

def test_task_get_complete():
    """Testa buscar tarefa completa para ver se lançamentos vêm junto."""
    validate_config()
    client = BitrixClient()
    
    task_id = 25943
    
    print("=" * 60)
    print(f"TESTE: Buscar tarefa completa (todos os campos)")
    print(f"Tarefa: {task_id}")
    print("=" * 60)
    
    # Buscar tarefa sem parâmetros especiais (todos os campos)
    print("\n1. tasks.task.get (sem parâmetros - todos os campos):")
    try:
        task_data = client.get_task(task_id)
        
        # Procurar qualquer campo que possa conter lançamentos
        print(f"\n   Total de campos: {len(task_data)}")
        
        # Procurar campos relacionados a tempo/lançamentos
        time_related = {}
        for key, value in task_data.items():
            key_lower = key.lower()
            if any(term in key_lower for term in ['elapsed', 'time', 'entry', 'log', 'spent']):
                time_related[key] = value
        
        if time_related:
            print(f"\n   [OK] Campos relacionados a tempo encontrados:")
            for key, value in time_related.items():
                if isinstance(value, (dict, list)):
                    print(f"      {key}: {type(value).__name__} = {json.dumps(value, ensure_ascii=False)[:300]}")
                else:
                    print(f"      {key}: {value}")
        else:
            print(f"\n   [AVISO] Nenhum campo de tempo encontrado")
        
        # Verificar se há campos que são listas ou dicionários que podem conter lançamentos
        print(f"\n   Campos que são listas ou dicionários (podem conter lançamentos):")
        for key, value in task_data.items():
            if isinstance(value, list) and len(value) > 0:
                print(f"      {key}: lista com {len(value)} itens")
                if len(value) > 0:
                    print(f"         Primeiro item: {json.dumps(value[0], ensure_ascii=False)[:200]}")
            elif isinstance(value, dict) and value:
                print(f"      {key}: dicionário com {len(value)} chaves")
                if len(list(value.keys())[:3]) > 0:
                    print(f"         Primeiras chaves: {list(value.keys())[:3]}")
        
    except Exception as e:
        print(f"   [ERRO] {e}")
    
    # Tentar buscar com select específico (formato correto)
    print("\n2. tasks.task.get com select (formato array JSON):")
    try:
        import requests
        url = f"{client.webhook_base}tasks.task.get"
        # Formato correto: select deve ser um array JSON
        params = {
            "taskId": task_id,
            "select": json.dumps(["elapsedItems", "timeSpentInLogs", "elapsedTime"])
        }
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            task = data.get("result", {}).get("task", {})
            print(f"   [OK] Resposta recebida")
            if "elapsedItems" in task:
                print(f"   [OK] elapsedItems encontrado: {task['elapsedItems']}")
        else:
            print(f"   [ERRO] {response.status_code}: {response.text[:300]}")
    except Exception as e:
        print(f"   [ERRO] {e}")

if __name__ == "__main__":
    test_task_get_complete()
