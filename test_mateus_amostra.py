"""Teste de exportação com amostra de tarefas do Mateus."""
from excel_handler import read_collaborators_sheet
from web_services import export_tasks_to_excel_bytes
from users_config import get_user
from datetime import datetime
from task_processor import determine_scope_ids, collect_task_ids
from bitrix_client import BitrixClient
from config import validate_config
from task_processor import enrich_tasks
from time_entries_handler import fetch_all_time_entries
from web_services import combine_tasks_with_time_entries
from excel_handler import write_tasks_excel

def test_mateus_amostra():
    """Testa exportação com amostra limitada."""
    print("=" * 60)
    print("TESTE DE EXPORTACAO - MATEUS (AMOSTRA)")
    print("=" * 60)
    
    # Ler planilha
    collaborators_map = read_collaborators_sheet("Planilha de colaboradores.xlsx")
    
    # Encontrar Mateus
    mateus_ids = determine_scope_ids(collaborators_map, user_substring="Mateus")
    print(f"\nColaborador encontrado: {list(mateus_ids)}")
    
    try:
        validate_config()
        client = BitrixClient()
        
        # Buscar apenas algumas tarefas para teste rápido
        print("\nBuscando tarefas (limitado a 50 para teste rápido)...")
        all_task_ids = collect_task_ids(client, list(mateus_ids), activity_from=None, activity_to=None, status=None)
        print(f"Total de tarefas encontradas: {len(all_task_ids)}")
        
        # Limitar a 50 tarefas para teste
        limited_task_ids = list(all_task_ids)[:50]
        print(f"Processando amostra de {len(limited_task_ids)} tarefas...")
        
        # Enriquecer tarefas
        enriched_tasks = enrich_tasks(client, limited_task_ids, mateus_ids, collaborators_map)
        print(f"Tarefas enriquecidas: {len(enriched_tasks)}")
        
        # Buscar lançamentos de tempo (limitado)
        time_entries_map = fetch_all_time_entries(client, limited_task_ids)
        print(f"Lançamentos de tempo encontrados para {len(time_entries_map)} tarefas")
        
        # Combinar
        excel_rows = combine_tasks_with_time_entries(enriched_tasks, time_entries_map, collaborators_map)
        print(f"Linhas para Excel: {len(excel_rows)}")
        
        # Salvar
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"teste_mateus_amostra_{timestamp}.xlsx"
        write_tasks_excel(excel_rows, output_path)
        
        print(f"\n[OK] Exportacao concluida!")
        print(f"   Linhas exportadas: {len(excel_rows)}")
        print(f"   Arquivo: {output_path}")
        print(f"\n[INFO] Total de tarefas disponiveis: {len(all_task_ids)}")
        print(f"       Para exportar todas, use a interface web.")
        
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mateus_amostra()
