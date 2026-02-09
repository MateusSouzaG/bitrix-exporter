"""Teste de diferentes formatos de batch para encontrar o correto."""
from bitrix_client import BitrixClient
from config import validate_config
import json
import requests

def test_batch_formats():
    """Testa diferentes formatos de batch."""
    validate_config()
    client = BitrixClient()
    
    task_id = 25857
    print(f"Testando batch com tarefa {task_id}")
    
    batch_url = f"{client.webhook_base}batch"
    
    # Formato 1: String com query params (atual)
    print("\n1. Testando formato atual (string com query):")
    batch_cmd1 = {
        "cmd1": "tasks.task.get?taskId=25857"
    }
    try:
        response1 = requests.post(batch_url, json={"cmd": batch_cmd1}, timeout=30)
        print(f"Status: {response1.status_code}")
        data1 = response1.json()
        print(f"Resposta: {json.dumps(data1, indent=2, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"ERRO: {e}")
    
    # Formato 2: Objeto com method e params
    print("\n2. Testando formato objeto (method + params):")
    batch_cmd2 = {
        "cmd1": {
            "method": "tasks.task.get",
            "params": {"taskId": task_id}
        }
    }
    try:
        response2 = requests.post(batch_url, json={"cmd": batch_cmd2}, timeout=30)
        print(f"Status: {response2.status_code}")
        data2 = response2.json()
        print(f"Resposta: {json.dumps(data2, indent=2, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"ERRO: {e}")
    
    # Formato 3: Array de objetos
    print("\n3. Testando formato array de objetos:")
    batch_cmd3 = [
        {
            "method": "tasks.task.get",
            "params": {"taskId": task_id}
        }
    ]
    try:
        response3 = requests.post(batch_url, json={"cmd": batch_cmd3}, timeout=30)
        print(f"Status: {response3.status_code}")
        data3 = response3.json()
        print(f"Resposta: {json.dumps(data3, indent=2, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"ERRO: {e}")

if __name__ == "__main__":
    test_batch_formats()
