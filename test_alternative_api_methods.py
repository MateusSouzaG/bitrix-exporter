"""Testa métodos alternativos que podem retornar lançamentos de tempo."""
from bitrix_client import BitrixClient
from config import validate_config
import json
import requests

def test_alternative_methods():
    """Testa métodos alternativos da API."""
    validate_config()
    client = BitrixClient()
    
    task_id = 25943
    base_url = client.webhook_base
    
    print("=" * 60)
    print(f"TESTE: Métodos alternativos da API")
    print(f"Tarefa: {task_id}")
    print("=" * 60)
    
    # Método 1: tasks.task.get com campos específicos via select (formato correto)
    print("\n1. tasks.task.get com select (formato correto - array):")
    try:
        url = f"{base_url}tasks.task.get"
        # Tentar passar select como array de forma diferente
        params = {
            "taskId": task_id,
            "select[0]": "elapsedItems",
            "select[1]": "timeSpentInLogs"
        }
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            task = data.get("result", {}).get("task", {})
            if "elapsedItems" in task:
                print(f"   [OK] elapsedItems encontrado!")
                print(f"   {json.dumps(task.get('elapsedItems'), indent=2, ensure_ascii=False)[:500]}")
            else:
                print(f"   [AVISO] elapsedItems não encontrado nos campos retornados")
        else:
            print(f"   [ERRO] {response.status_code}: {response.text[:300]}")
    except Exception as e:
        print(f"   [ERRO] {e}")
    
    # Método 2: Verificar se há um método tasks.task.elapseditem.list
    print("\n2. tasks.task.elapseditem.list (com diferentes parâmetros):")
    methods_to_try = [
        ("tasks.task.elapseditem.list", {"taskId": task_id}),
        ("tasks.task.elapseditem.list", {"TASK_ID": task_id}),
        ("tasks.task.elapseditem.list", {"ID": task_id}),
        ("tasks.task.elapseditem.list", {"filter[taskId]": task_id}),
    ]
    
    for method, params in methods_to_try:
        try:
            url = f"{base_url}{method}"
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"   [OK] {method} com {params} funcionou!")
                print(f"   {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
                break
            elif response.status_code != 404:
                print(f"   Status {response.status_code} para {method}: {response.text[:200]}")
        except Exception as e:
            pass
    
    # Método 3: Verificar se há métodos relacionados a "elapsed" ou "time"
    print("\n3. Testando métodos relacionados a 'elapsed' ou 'time':")
    methods = [
        "tasks.elapseditem.get",
        "tasks.elapseditem.list",
        "tasks.task.elapsed.get",
        "tasks.task.elapsed.list",
        "tasks.task.time.get",
        "tasks.task.time.list",
    ]
    
    for method in methods:
        try:
            url = f"{base_url}{method}"
            params = {"taskId": task_id}
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   [OK] {method} funcionou!")
                print(f"   {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
            elif response.status_code == 400:
                # 400 pode significar que o método existe mas os parâmetros estão errados
                print(f"   [INFO] {method} retornou 400 (método pode existir): {response.text[:200]}")
        except:
            pass

if __name__ == "__main__":
    test_alternative_methods()
