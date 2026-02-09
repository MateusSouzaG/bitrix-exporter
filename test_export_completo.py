"""Teste completo de exportação."""
from excel_handler import read_collaborators_sheet
from web_services import export_tasks_to_excel_bytes
from users_config import get_user

def test_export():
    """Testa exportação completa."""
    print("=" * 60)
    print("TESTE COMPLETO DE EXPORTACAO")
    print("=" * 60)
    
    # Ler planilha
    collaborators_map = read_collaborators_sheet("Planilha de colaboradores.xlsx")
    print(f"\nTotal de colaboradores: {len(collaborators_map)}")
    
    # Listar alguns colaboradores
    print("\nAlguns colaboradores disponiveis:")
    for i, (uid, info) in enumerate(list(collaborators_map.items())[:5]):
        print(f"  {uid}: {info['name']} - {info['dept']}")
    
    # Testar com um colaborador específico (Mateus)
    print("\n" + "=" * 60)
    print("TESTE 1: Exportar tarefas do colaborador 'Mateus'")
    print("=" * 60)
    
    try:
        admin_user = get_user("mateus.souza")
        excel_bytes, num_rows = export_tasks_to_excel_bytes(
            user=admin_user,
            dept=None,
            user_substring="Mateus",
            activity_from=None,
            activity_to=None,
            status=None
        )
        
        output_path = "teste_mateus_export.xlsx"
        with open(output_path, "wb") as f:
            f.write(excel_bytes.getvalue())
        
        print(f"[OK] Exportacao concluida!")
        print(f"   Linhas exportadas: {num_rows}")
        print(f"   Arquivo: {output_path}")
        
    except Exception as e:
        print(f"[ERRO] {e}")
        import traceback
        traceback.print_exc()
    
    # Testar com departamento
    print("\n" + "=" * 60)
    print("TESTE 2: Exportar tarefas do departamento 'GI'")
    print("=" * 60)
    
    try:
        excel_bytes, num_rows = export_tasks_to_excel_bytes(
            user=admin_user,
            dept="GI",
            user_substring=None,
            activity_from=None,
            activity_to=None,
            status=None
        )
        
        output_path = "teste_gi_export.xlsx"
        with open(output_path, "wb") as f:
            f.write(excel_bytes.getvalue())
        
        print(f"[OK] Exportacao concluida!")
        print(f"   Linhas exportadas: {num_rows}")
        print(f"   Arquivo: {output_path}")
        
    except Exception as e:
        print(f"[ERRO] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_export()
