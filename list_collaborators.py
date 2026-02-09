"""Lista todos os colaboradores da planilha."""
from excel_handler import read_collaborators_sheet

collab = read_collaborators_sheet("Planilha de colaboradores.xlsx")
print("=" * 60)
print(f"TOTAL DE COLABORADORES: {len(collab)}")
print("=" * 60)
print("\nLista completa (ordenada por nome):")
print("-" * 60)
for uid, info in sorted(collab.items(), key=lambda x: x[1]['name']):
    print(f"ID: {uid:3d} | Nome: {info['name']:30s} | Dept: {info['dept']}")
