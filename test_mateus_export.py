"""Teste de exportação para o colaborador Mateus."""
from excel_handler import read_collaborators_sheet
from web_services import export_tasks_to_excel_bytes
from users_config import get_user
from datetime import datetime

def test_mateus_export():
    """Testa exportação para colaborador Mateus."""
    print("=" * 60)
    print("TESTE DE EXPORTACAO - COLABORADOR MATEUS")
    print("=" * 60)
    
    # Ler planilha de colaboradores
    try:
        collaborators_map = read_collaborators_sheet("Planilha de colaboradores.xlsx")
        print(f"\nTotal de colaboradores na planilha: {len(collaborators_map)}")
    except Exception as e:
        print(f"Erro ao ler planilha: {e}")
        return
    
    # Procurar colaborador Mateus
    mateus_collaborators = {}
    for user_id, info in collaborators_map.items():
        if "mateus" in info["name"].lower():
            mateus_collaborators[user_id] = info
    
    if not mateus_collaborators:
        print("\n[ERRO] Nenhum colaborador encontrado com 'mateus' no nome.")
        return
    
    print(f"\n[OK] Encontrado(s) {len(mateus_collaborators)} colaborador(es) com 'mateus' no nome:")
    for user_id, info in mateus_collaborators.items():
        print(f"  ID: {user_id}, Nome: {info['name']}, Departamento: {info['dept']}")
    
    # Fazer exportação de teste
    print("\n" + "=" * 60)
    print("INICIANDO EXPORTACAO DE TESTE...")
    print("=" * 60)
    
    try:
        # Usar usuário admin para teste
        admin_user = get_user("mateus.souza")
        if not admin_user:
            print("[ERRO] Usuário admin não encontrado")
            return
        
        print("\nTestando exportação sem filtros de data...")
        # Exportar tarefas do Mateus (sem filtros de data para teste)
        excel_bytes, num_rows = export_tasks_to_excel_bytes(
            user=admin_user,
            dept=None,
            user_substring="Mateus",
            activity_from=None,
            activity_to=None,
            status=None
        )
        
        print(f"\n[OK] Exportação concluída!")
        print(f"   Total de linhas exportadas: {num_rows}")
        
        # Salvar arquivo de teste
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"teste_mateus_export_{timestamp}.xlsx"
        with open(output_path, "wb") as f:
            f.write(excel_bytes.getvalue())
        
        print(f"   Arquivo salvo em: {output_path}")
        
        if num_rows == 0:
            print("\n[AVISO] Nenhuma tarefa foi encontrada. Isso pode significar:")
            print("  - Não há tarefas para este colaborador no Bitrix24")
            print("  - As tarefas podem estar em outro período")
            print("  - Pode ser necessário verificar os filtros de data")
        
    except Exception as e:
        print(f"\n[ERRO] Erro durante exportação: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mateus_export()
