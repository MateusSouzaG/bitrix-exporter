"""Script de diagnóstico para entender por que a exportação está vazia."""
from excel_handler import read_collaborators_sheet
from task_processor import determine_scope_ids, collect_task_ids
from bitrix_client import BitrixClient
from config import validate_config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def diagnostico():
    """Diagnostica problemas na exportação."""
    print("=" * 60)
    print("DIAGNOSTICO DE EXPORTACAO")
    print("=" * 60)
    
    # 1. Verificar planilha de colaboradores
    print("\n1. Verificando planilha de colaboradores...")
    try:
        collaborators_map = read_collaborators_sheet("Planilha de colaboradores.xlsx")
        print(f"   [OK] {len(collaborators_map)} colaboradores carregados")
        
        # Mostrar alguns exemplos
        print("\n   Exemplos de colaboradores:")
        for i, (uid, info) in enumerate(list(collaborators_map.items())[:5]):
            print(f"      ID: {uid}, Nome: {info['name']}, Dept: {info['dept']}")
    except Exception as e:
        print(f"   [ERRO] Falha ao ler planilha: {e}")
        return
    
    # 2. Verificar configuração
    print("\n2. Verificando configuração...")
    try:
        validate_config()
        print("   [OK] Configuração válida")
    except Exception as e:
        print(f"   [ERRO] {e}")
        return
    
    # 3. Testar busca sem filtros
    print("\n3. Testando busca de tarefas SEM filtros de data...")
    try:
        client = BitrixClient()
        
        # Testar com Mateus
        scope_ids = determine_scope_ids(collaborators_map, user_substring="Mateus")
        print(f"   Colaboradores no escopo: {len(scope_ids)}")
        if scope_ids:
            print(f"   IDs: {list(scope_ids)}")
            
            task_ids = collect_task_ids(client, list(scope_ids), activity_from=None, activity_to=None, status=None)
            print(f"   [RESULTADO] {len(task_ids)} tarefas encontradas SEM filtros")
            if task_ids:
                print(f"   Primeiros 10 IDs: {list(task_ids)[:10]}")
        else:
            print("   [AVISO] Nenhum colaborador encontrado no escopo")
    except Exception as e:
        print(f"   [ERRO] {e}")
        import traceback
        traceback.print_exc()
    
    # 4. Testar busca COM filtros (exemplo: este mês)
    print("\n4. Testando busca de tarefas COM filtros de data (este mês)...")
    try:
        from date_filters import get_date_range_for_preset
        date_range = get_date_range_for_preset("este_mes")
        if date_range:
            activity_from, activity_to = date_range
            print(f"   Filtro aplicado: {activity_from} a {activity_to}")
            
            task_ids = collect_task_ids(client, list(scope_ids), activity_from=activity_from, activity_to=activity_to, status=None)
            print(f"   [RESULTADO] {len(task_ids)} tarefas encontradas COM filtros")
            if task_ids:
                print(f"   Primeiros 10 IDs: {list(task_ids)[:10]}")
            else:
                print("   [AVISO] Nenhuma tarefa encontrada com esses filtros")
                print("   Isso pode significar:")
                print("     - Não há tarefas ativas neste período")
                print("     - O filtro ACTIVITY_DATE pode estar muito restritivo")
                print("     - As tarefas podem ter ACTIVITY_DATE diferente do esperado")
    except Exception as e:
        print(f"   [ERRO] {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("DIAGNOSTICO CONCLUIDO")
    print("=" * 60)
    print("\nRECOMENDACOES:")
    print("1. Se encontrou tarefas SEM filtros mas não COM filtros:")
    print("   - O filtro ACTIVITY_DATE pode estar muito restritivo")
    print("   - Tente usar 'Qualquer data' ou um período maior")
    print("2. Se não encontrou tarefas em nenhum caso:")
    print("   - Verifique se o colaborador tem tarefas atribuídas no Bitrix24")
    print("   - Verifique se o ID do colaborador está correto na planilha")
    print("3. Para debug, verifique os logs do servidor para mais detalhes")

if __name__ == "__main__":
    diagnostico()
