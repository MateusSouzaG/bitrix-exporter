"""Teste rápido para verificar tarefas do Mateus."""
from excel_handler import read_collaborators_sheet
from task_processor import determine_scope_ids, collect_task_ids
from bitrix_client import BitrixClient
from config import validate_config

print("=" * 60)
print("TESTE RAPIDO - COLABORADOR MATEUS")
print("=" * 60)

# Ler planilha
collaborators_map = read_collaborators_sheet("Planilha de colaboradores.xlsx")

# Procurar Mateus
mateus_collaborators = {uid: info for uid, info in collaborators_map.items() if "mateus" in info["name"].lower()}

if not mateus_collaborators:
    print("\n[ERRO] Nenhum colaborador encontrado com 'mateus' no nome.")
    exit(1)

print(f"\n[OK] Encontrado(s) {len(mateus_collaborators)} colaborador(es):")
for uid, info in mateus_collaborators.items():
    print(f"  ID: {uid}, Nome: {info['name']}, Departamento: {info['dept']}")

# Determinar escopo
print("\n" + "=" * 60)
print("DETERMINANDO ESCOPO...")
print("=" * 60)

scope_ids = determine_scope_ids(collaborators_map, user_substring="Mateus")
print(f"\nColaboradores no escopo: {len(scope_ids)}")
if scope_ids:
    print(f"IDs: {list(scope_ids)}")
else:
    print("[AVISO] Nenhum colaborador encontrado no escopo")
    exit(1)

# Buscar tarefas (sem processar tudo)
print("\n" + "=" * 60)
print("BUSCANDO TAREFAS...")
print("=" * 60)

try:
    validate_config()
    client = BitrixClient()
    
    print("\nBuscando IDs de tarefas (pode levar alguns segundos)...")
    task_ids = collect_task_ids(client, list(scope_ids), activity_from=None, activity_to=None, status=None)
    
    print(f"\n[RESULTADO]")
    print(f"  Total de tarefas encontradas: {len(task_ids)}")
    if task_ids:
        print(f"  Primeiros 10 IDs de tarefas: {list(task_ids)[:10]}")
        print(f"\n[INFO] Para exportar todas as tarefas, use a interface web ou o script completo.")
    else:
        print(f"  [AVISO] Nenhuma tarefa encontrada para o colaborador Mateus.")
        print(f"  Isso pode significar:")
        print(f"    - Não há tarefas atribuídas a este colaborador")
        print(f"    - As tarefas podem estar em outro período")
        print(f"    - Pode ser necessário usar filtros de data")
        
except Exception as e:
    print(f"\n[ERRO] {e}")
    import traceback
    traceback.print_exc()
