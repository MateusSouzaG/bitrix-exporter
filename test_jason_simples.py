"""Teste simples para verificar colaborador jason."""
from excel_handler import read_collaborators_sheet
from task_processor import determine_scope_ids
from bitrix_client import BitrixClient
from config import validate_config

print("=" * 60)
print("TESTE SIMPLES - COLABORADOR JASON")
print("=" * 60)

# Ler planilha
collaborators_map = read_collaborators_sheet("Planilha de colaboradores.xlsx")
print(f"\nTotal de colaboradores: {len(collaborators_map)}")

# Procurar jason
jason_collaborators = {uid: info for uid, info in collaborators_map.items() if "jason" in info["name"].lower()}

if not jason_collaborators:
    print("\n[AVISO] Nenhum colaborador encontrado com 'jason' no nome.")
    print("\nColaboradores disponiveis:")
    for uid, info in sorted(collaborators_map.items(), key=lambda x: x[1]['name']):
        print(f"  {uid}: {info['name']} - {info['dept']}")
else:
    print(f"\n[OK] Encontrado(s) {len(jason_collaborators)} colaborador(es):")
    for uid, info in jason_collaborators.items():
        print(f"  ID: {uid}, Nome: {info['name']}, Departamento: {info['dept']}")
    
    # Testar busca de tarefas (limitado)
    print("\n" + "=" * 60)
    print("TESTE DE BUSCA DE TAREFAS")
    print("=" * 60)
    
    try:
        validate_config()
        client = BitrixClient()
        
        scope_ids = determine_scope_ids(collaborators_map, user_substring="jason")
        print(f"\nColaboradores no escopo: {len(scope_ids)}")
        if scope_ids:
            print(f"IDs: {list(scope_ids)}")
            
            # Buscar apenas algumas tarefas para teste rápido
            from task_processor import collect_task_ids
            print("\nBuscando tarefas (pode levar alguns segundos)...")
            task_ids = collect_task_ids(client, list(scope_ids)[:1], activity_from=None, activity_to=None, status=None)
            print(f"Tarefas encontradas: {len(task_ids)}")
            if task_ids:
                print(f"Primeiros 10 IDs de tarefas: {list(task_ids)[:10]}")
        else:
            print("[AVISO] Nenhum colaborador encontrado no escopo")
            
    except Exception as e:
        print(f"[ERRO] {e}")
        import traceback
        traceback.print_exc()
