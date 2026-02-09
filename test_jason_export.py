"""Script de teste para exportação do colaborador jason."""
import sys
from excel_handler import read_collaborators_sheet
from web_services import export_tasks_to_excel_bytes
from users_config import get_user

def test_jason_export():
    """Testa exportação para colaborador jason."""
    print("=" * 60)
    print("TESTE DE EXPORTAÇÃO - COLABORADOR JASON")
    print("=" * 60)
    
    # Ler planilha de colaboradores
    try:
        collaborators_map = read_collaborators_sheet("Planilha de colaboradores.xlsx")
        print(f"\nTotal de colaboradores na planilha: {len(collaborators_map)}")
    except Exception as e:
        print(f"Erro ao ler planilha: {e}")
        return
    
    # Procurar colaborador com "jason" no nome
    jason_collaborators = {}
    for user_id, info in collaborators_map.items():
        if "jason" in info["name"].lower():
            jason_collaborators[user_id] = info
    
    if not jason_collaborators:
        print("\n[AVISO] Nenhum colaborador encontrado com 'jason' no nome.")
        print("\nFazendo teste com o primeiro colaborador disponível...")
        # Usar o primeiro colaborador para teste
        first_user_id = list(collaborators_map.keys())[0]
        first_user_info = collaborators_map[first_user_id]
        print(f"  Testando com: {first_user_info['name']} (ID: {first_user_id}) - {first_user_info['dept']}")
        user_substring = first_user_info['name'].split()[0].lower()  # Primeiro nome
    else:
        # Usar o primeiro jason encontrado
        first_user_id = list(jason_collaborators.keys())[0]
        first_user_info = jason_collaborators[first_user_id]
        user_substring = "jason"
    
    if jason_collaborators:
        print(f"\n[OK] Encontrado(s) {len(jason_collaborators)} colaborador(es) com 'jason' no nome:")
        for user_id, info in jason_collaborators.items():
            print(f"  ID: {user_id}, Nome: {info['name']}, Departamento: {info['dept']}")
    
    # Fazer exportação de teste
    print("\n" + "=" * 60)
    print("INICIANDO EXPORTAÇÃO DE TESTE...")
    print("=" * 60)
    
    try:
        # Usar usuário admin para teste
        admin_user = get_user("mateus.souza")
        if not admin_user:
            print("[ERRO] Usuário admin não encontrado")
            return
        
        # Exportar tarefas (sem filtros de data para teste)
        excel_bytes, num_rows = export_tasks_to_excel_bytes(
            user=admin_user,
            dept=None,
            user_substring=user_substring,
            activity_from=None,
            activity_to=None,
            status=None
        )
        
        print(f"\n[OK] Exportação concluída!")
        print(f"   Total de linhas exportadas: {num_rows}")
        
        # Salvar arquivo de teste
        output_path = "teste_jason_export.xlsx"
        with open(output_path, "wb") as f:
            f.write(excel_bytes.getvalue())
        
        print(f"   Arquivo salvo em: {output_path}")
        
    except Exception as e:
        print(f"\n[ERRO] Erro durante exportação: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_jason_export()
