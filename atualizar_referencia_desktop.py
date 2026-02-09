"""Copia a planilha de colaboradores da Área de Trabalho para o projeto, se tiver a estrutura correta."""
import os
import shutil

# Caminho do arquivo na Área de Trabalho (ajuste o nome do arquivo se necessário)
DESKTOP = os.path.join(os.path.expanduser("~"), "OneDrive", "Área de Trabalho")
ORIGEM = os.path.join(DESKTOP, "Exportacao_Tarefas_20260128_133859.xlsx")
# Se você salvou a planilha de colaboradores com outro nome, use:
# ORIGEM = os.path.join(DESKTOP, "Planilha de colaboradores.xlsx")

DESTINO = os.path.join(os.path.dirname(__file__), "Planilha de colaboradores.xlsx")
COLUNAS_REFERENCIA = ["IDs", "Colaboradores", "Departamentos"]


def main():
    if not os.path.exists(ORIGEM):
        print(f"Arquivo não encontrado: {ORIGEM}")
        print("Coloque a planilha de colaboradores (com colunas IDs, Colaboradores, Departamentos)")
        print("na pasta do projeto com o nome 'Planilha de colaboradores.xlsx' ou ajuste ORIGEM neste script.")
        return
    try:
        import pandas as pd
        df = pd.read_excel(ORIGEM)
        cols = list(df.columns)
        missing = [c for c in COLUNAS_REFERENCIA if c not in cols]
        if missing:
            print(f"O arquivo não tem a estrutura de referência. Faltam colunas: {missing}")
            print(f"Colunas encontradas: {cols}")
            print("A referência deve ter: IDs, Colaboradores, Departamentos.")
            return
        shutil.copy2(ORIGEM, DESTINO)
        print(f"Referência atualizada: {DESTINO}")
    except Exception as e:
        print(f"Erro: {e}")


if __name__ == "__main__":
    main()
