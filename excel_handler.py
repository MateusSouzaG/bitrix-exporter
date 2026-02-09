"""Manipulação de arquivos Excel: leitura de colaboradores e escrita de tarefas."""
import pandas as pd
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def read_collaborators_sheet(path: str) -> Dict[int, Dict[str, str]]:
    """
    Lê a planilha de colaboradores e retorna mapeamento ID -> {name, dept}.
    
    Args:
        path: Caminho para o arquivo "Planilha de colaboradores.xlsx"
        
    Returns:
        Dicionário no formato {user_id: {"name": str, "dept": str}}
        
    Raises:
        FileNotFoundError: Se o arquivo não existir
        ValueError: Se as colunas obrigatórias não existirem
    """
    try:
        df = pd.read_excel(path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    except Exception as e:
        raise ValueError(f"Erro ao ler planilha: {e}")
    
    # Normalizar nomes de colunas (strip e aceitar variações)
    df.columns = [str(c).strip() for c in df.columns]
    
    # Mapear colunas obrigatórias (aceitar plural ou singular)
    def _find_col(choices: list) -> str:
        for c in choices:
            if c in df.columns:
                return c
        return None
    
    col_id = _find_col(["IDs", "ID"])
    col_name = _find_col(["Colaboradores", "Colaborador", "Nome completo", "Nome"])
    col_dept = _find_col(["Departamentos", "Departamento", "Depto", "Setor"])
    
    if not col_id or not col_name:
        raise ValueError(
            f"Colunas obrigatórias não encontradas. Precisa de: IDs (ou ID) e Colaboradores (ou Colaborador/Nome completo/Nome). "
            f"Colunas encontradas: {list(df.columns)}"
        )
    
    if not col_dept:
        col_dept = None  # departamento opcional, preencher vazio
        logger.warning("Coluna 'Departamentos' ou 'Departamento' não encontrada na planilha. Filtro por departamento não funcionará.")
    
    # Criar mapeamento
    collaborators_map = {}
    
    for _, row in df.iterrows():
        user_id = row[col_id]
        
        # Pular linhas com ID inválido
        if pd.isna(user_id):
            continue
        
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            logger.warning(f"ID inválido na planilha: {user_id}. Pulando linha.")
            continue
        
        name = str(row[col_name]) if not pd.isna(row[col_name]) else f"USER_{user_id}"
        name = name.strip() if name else f"USER_{user_id}"
        dept = str(row[col_dept]).strip() if col_dept and not pd.isna(row[col_dept]) else ""
        
        collaborators_map[user_id] = {
            "name": name,
            "dept": dept
        }
    
    logger.info(f"Carregados {len(collaborators_map)} colaboradores da planilha")
    return collaborators_map


# Ordem e lista fixa de colunas da planilha exportada (garante "Data do lançamento" sempre presente)
EXCEL_EXPORT_COLUMNS = [
    "Task_ID",
    "Título",
    "Status",
    "Deadline",
    "Criada_Em",
    "Responsável",
    "Participantes",
    "Tempo_Total_Gasto",
    "Tempo_Lançamento",
    "Quem_Lançou",
    "Data do lançamento",
    "Comentário_Lançamento",
    "Departamentos_Selecionados",
    "Atividade_em",
]


def write_tasks_excel(tasks_data: List[Dict[str, Any]], output_path: str):
    """
    Gera arquivo Excel com as tarefas exportadas.
    
    Args:
        tasks_data: Lista de dicionários, cada um representando uma linha do Excel.
                    Cada tarefa pode ter múltiplas linhas (uma por lançamento de tempo).
        output_path: Caminho onde salvar o arquivo Excel
    """
    if not tasks_data:
        logger.warning("Nenhuma tarefa para exportar. Criando Excel vazio.")
        df = pd.DataFrame(columns=EXCEL_EXPORT_COLUMNS)
    else:
        # Montar cada linha com exatamente as colunas de EXCEL_EXPORT_COLUMNS (garante "Data do lançamento" sempre)
        normalized = []
        for row in tasks_data:
            normalized.append({col: row.get(col, "") for col in EXCEL_EXPORT_COLUMNS})
        df = pd.DataFrame(normalized, columns=EXCEL_EXPORT_COLUMNS)
    
    # Ordenar por Task_ID descendente
    if "Task_ID" in df.columns:
        df = df.sort_values("Task_ID", ascending=False)
    
    # Largura mínima por coluna (para não truncar textos importantes no Excel)
    MIN_WIDTH_BY_COLUMN = {
        "Comentário_Lançamento": 70,
        "Título": 45,
        "Quem_Lançou": 45,
        "Participantes": 40,
        "Responsável": 20,
    }
    MAX_WIDTH_DEFAULT = 50

    # Salvar Excel
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Tarefas", index=False)
        
        # Ajustar largura das colunas (evitar truncar "Comentário" / "Quem_Lançou" etc.)
        worksheet = writer.sheets["Tarefas"]
        for idx, col in enumerate(df.columns, 1):
            max_length = max(
                df[col].astype(str).map(len).max() if len(df) > 0 else 0,
                len(str(col))
            )
            min_for_col = MIN_WIDTH_BY_COLUMN.get(col, 0)
            width = max(max_length + 2, min_for_col)
            width = min(width, MAX_WIDTH_DEFAULT if col not in MIN_WIDTH_BY_COLUMN else 80)
            worksheet.column_dimensions[worksheet.cell(1, idx).column_letter].width = width
    
    logger.info(f"Excel exportado com sucesso: {output_path} ({len(df)} linhas)")
