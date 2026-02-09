"""Configurações e carregamento de variáveis de ambiente."""
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Constantes
BATCH_SIZE = 50  # Tamanho máximo de batch para API Bitrix24
PAGINATION_SIZE = 50  # Tamanho da paginação para tasks.task.list
DEFAULT_TIMEZONE = "-03:00"  # Timezone padrão (Brasil)
MAX_RETRIES = 3  # Número máximo de tentativas em caso de erro
RETRY_BACKOFF = 1  # Fator de backoff exponencial (segundos)

# Variável de ambiente obrigatória
BITRIX_WEBHOOK_BASE = os.getenv("BITRIX_WEBHOOK_BASE")

# Planilha de colaboradores (IDs, Colaboradores, Departamentos)
# Use COLABORADORES_PLANILHA no .env para caminho completo; senão usa a planilha na pasta do projeto
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
COLLABORATORS_SHEET_PATH = os.getenv("COLABORADORES_PLANILHA") or os.path.join(_PROJECT_DIR, "Planilha de colaboradores.xlsx")

# Departamentos usados no dropdown quando a planilha não tem coluna Departamentos (pode editar)
FALLBACK_DEPARTMENTS = ["COMERCIAL", "DTC", "GI", "RNA"]


def validate_config():
    """Valida se as configurações obrigatórias estão presentes."""
    if not BITRIX_WEBHOOK_BASE:
        raise ValueError(
            "BITRIX_WEBHOOK_BASE não encontrado no arquivo .env. "
            "Por favor, configure o webhook do Bitrix24."
        )
    
    if not BITRIX_WEBHOOK_BASE.startswith("http"):
        raise ValueError(
            f"BITRIX_WEBHOOK_BASE deve ser uma URL válida. "
            f"Valor atual: {BITRIX_WEBHOOK_BASE}"
        )
    
    return True
