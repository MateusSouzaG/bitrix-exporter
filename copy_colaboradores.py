# -*- coding: utf-8 -*-
"""Copia a planilha de colaboradores (Colaboradores IDs.xlsx, com nomes completos/sobrenomes)
para a referência do projeto (Planilha de colaboradores.xlsx). Execute após atualizar a planilha de IDs."""
import os
import shutil

# Caminho do arquivo enviado pelo usuário
ORIGEM = r"c:\Users\Mateus\OneDrive\Área de Trabalho\Mateus - RH\Colaboradores\Colaboradores IDs.xlsx"

# Destino: planilha de referência do projeto
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(PROJECT_DIR, "Planilha de colaboradores.xlsx")


def main():
    origem = ORIGEM
    if not os.path.exists(origem):
        # Tentar encontrar "Colaboradores IDs.xlsx" na pasta do usuário
        base = os.path.expanduser(r"~\OneDrive")
        if not os.path.isdir(base):
            print("Pasta OneDrive não encontrada.")
            return
        for root, dirs, files in os.walk(base):
            if "Colaboradores IDs.xlsx" in files:
                origem = os.path.join(root, "Colaboradores IDs.xlsx")
                break
        else:
            print("Arquivo não encontrado:", ORIGEM)
            return

    try:
        import pandas as pd
        df = pd.read_excel(origem)
        df.columns = [str(c).strip() for c in df.columns]
        print("Colunas:", list(df.columns))
        print("Linhas:", len(df))
    except Exception as e:
        print("Erro ao ler arquivo:", e)
        return

    shutil.copy2(origem, DESTINO)
    print("Planilha de referência atualizada:", DESTINO)


if __name__ == "__main__":
    main()
