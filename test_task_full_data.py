"""Teste para ver todos os campos de uma tarefa e verificar se há dados de tempo."""
from bitrix_client import BitrixClient
from config import validate_config
import json

def test_task_full_data():
    """Testa buscar uma tarefa completa e ver todos os campos."""
    validate_config()
    client = BitrixClient()
    
    task_id = 25857
    
    print("=" * 60)
    print(f"TESTE: Dados completos da tarefa {task_id}")
    print("=" * 60)
    
    try:
        # Buscar tarefa completa
        task_data = client.get_task(task_id)
        
        print(f"\nTotal de campos: {len(task_data)}")
        print(f"\nTodos os campos disponíveis:")
        for key in sorted(task_data.keys()):
            value = task_data[key]
            # Mostrar apenas primeiros 100 caracteres do valor
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False)[:100]
            else:
                value_str = str(value)[:100]
            print(f"  {key}: {value_str}")
        
        # Procurar campos relacionados a tempo
        print(f"\n\nCampos relacionados a TEMPO:")
        time_related = []
        for key in task_data.keys():
            key_lower = key.lower()
            if any(term in key_lower for term in ['time', 'elapsed', 'duration', 'spent', 'hours', 'minutes', 'seconds', 'entry']):
                time_related.append(key)
                print(f"  {key}: {task_data[key]}")
        
        if not time_related:
            print("  Nenhum campo relacionado a tempo encontrado diretamente na tarefa")
        
        # Verificar se há um campo que contenha os lançamentos
        print(f"\n\nVerificando campos que podem conter lançamentos:")
        for key in task_data.keys():
            value = task_data[key]
            if isinstance(value, (dict, list)) and value:
                print(f"  {key}: {type(value).__name__} com {len(value) if isinstance(value, list) else 'dados'}")
                if isinstance(value, list) and len(value) > 0:
                    print(f"    Primeiro item: {json.dumps(value[0], ensure_ascii=False)[:200]}")
        
    except Exception as e:
        print(f"ERRO: {e}")

if __name__ == "__main__":
    test_task_full_data()
