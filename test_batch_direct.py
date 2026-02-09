"""Teste direto do batch para verificar o formato."""
from bitrix_client import BitrixClient
from config import validate_config
import json

def test_batch():
    """Testa o batch diretamente."""
    validate_config()
    client = BitrixClient()
    
    # Teste com uma única tarefa
    task_id = 25857
    print(f"Testando batch com tarefa {task_id}")
    
    # Teste 1: Método direto
    print("\n1. Testando método direto (tasks.task.get):")
    try:
        response = client.get_task(task_id)
        print(f"Resposta: {json.dumps(response, indent=2, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"ERRO: {e}")
    
    # Teste 2: Batch com formato atual
    print("\n2. Testando batch com formato atual:")
    commands = [{"method": "tasks.task.get", "params": {"taskId": task_id}}]
    try:
        results = client._batch(commands)
        print(f"Resultado do batch: {json.dumps(results[0] if results else None, indent=2, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_batch()
