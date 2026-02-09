"""Teste detalhado de diferentes métodos e formatos para buscar lançamentos de tempo."""
from bitrix_client import BitrixClient
from config import validate_config
import json
import requests

def test_detailed_methods():
    """Testa diferentes formatos e métodos para buscar lançamentos."""
    validate_config()
    client = BitrixClient()
    
    task_id = 25943
    base_url = client.webhook_base
    
    print("=" * 60)
    print(f"TESTE DETALHADO: Métodos para lançamentos de tempo")
    print(f"Tarefa: {task_id}")
    print(f"Webhook base: {base_url}")
    print("=" * 60)
    
    # Método 1: tasks.task.elapseditem.get (atual)
    print("\n1. tasks.task.elapseditem.get (método atual):")
    try:
        url = f"{base_url}tasks.task.elapseditem.get"
        params = {"taskId": task_id}
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] SUCESSO: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
        else:
            print(f"   [ERRO] {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"   [EXCECAO] {e}")
    
    # Método 2: tasks.task.elapseditem.get com TASK_ID em maiúsculas
    print("\n2. tasks.task.elapseditem.get com TASK_ID (maiúsculas):")
    try:
        url = f"{base_url}tasks.task.elapseditem.get"
        params = {"TASK_ID": task_id}
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] SUCESSO: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
        else:
            print(f"   [ERRO] {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"   [EXCECAO] {e}")
    
    # Método 3: tasks.task.elapseditem.get com ID
    print("\n3. tasks.task.elapseditem.get com ID:")
    try:
        url = f"{base_url}tasks.task.elapseditem.get"
        params = {"ID": task_id}
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] SUCESSO: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
        else:
            print(f"   [ERRO] {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"   [EXCECAO] {e}")
    
    # Método 4: tasks.task.elapseditem.list
    print("\n4. tasks.task.elapseditem.list:")
    try:
        url = f"{base_url}tasks.task.elapseditem.list"
        params = {"taskId": task_id}
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] SUCESSO: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
        else:
            print(f"   [ERRO] {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"   [EXCECAO] {e}")
    
    # Método 5: Verificar se precisa usar filter
    print("\n5. tasks.task.elapseditem.get com filter[TASK_ID]:")
    try:
        url = f"{base_url}tasks.task.elapseditem.get"
        params = {"filter[TASK_ID]": task_id}
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] SUCESSO: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
        else:
            print(f"   [ERRO] {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"   [EXCECAO] {e}")
    
    # Método 6: Verificar se o método correto é tasks.elapseditem.get (sem task.)
    print("\n6. tasks.elapseditem.get (sem 'task.'):")
    try:
        url = f"{base_url}tasks.elapseditem.get"
        params = {"taskId": task_id}
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] SUCESSO: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
        else:
            print(f"   [ERRO] {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"   [EXCECAO] {e}")
    
    # Método 7: Verificar se precisa passar como parte de tasks.task.get
    print("\n7. Verificando se elapsedItems vem em tasks.task.get com parâmetros especiais:")
    try:
        url = f"{base_url}tasks.task.get"
        params = {"taskId": task_id, "select": ["elapsedItems", "timeSpentInLogs"]}
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            task = data.get("result", {}).get("task", {})
            if "elapsedItems" in task or "elapsed" in str(task).lower():
                print(f"   [OK] Campos relacionados encontrados na tarefa")
                for key in task.keys():
                    if "elapsed" in key.lower() or "time" in key.lower():
                        print(f"      {key}: {task[key]}")
            else:
                print(f"   [AVISO] Nenhum campo de lançamentos encontrado")
        else:
            print(f"   [ERRO] {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"   [EXCECAO] {e}")

if __name__ == "__main__":
    test_detailed_methods()
