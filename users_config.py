"""Configuração de usuários e permissões do sistema."""
from typing import Dict, List, Optional
from passlib.context import CryptContext

# Contexto para hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User:
    """Representa um usuário do sistema."""
    
    def __init__(
        self,
        username: str,
        password_hash: str,
        full_name: str,
        role: str,
        allowed_departments: Optional[List[str]] = None
    ):
        """
        Args:
            username: Nome de usuário para login
            password_hash: Hash da senha (bcrypt)
            full_name: Nome completo do usuário
            role: "admin" ou "supervisor"
            allowed_departments: Lista de departamentos permitidos (None = todos para admin)
        """
        self.username = username
        self.password_hash = password_hash
        self.full_name = full_name
        self.role = role
        self.allowed_departments = allowed_departments
    
    def has_access_to_department(self, department: str) -> bool:
        """Verifica se o usuário tem acesso a um departamento."""
        if self.role == "admin":
            return True
        if self.allowed_departments is None:
            return False
        return department.upper() in [d.upper() for d in self.allowed_departments]
    
    def verify_password(self, password: str) -> bool:
        """Verifica se a senha está correta."""
        return pwd_context.verify(password, self.password_hash)


# Senha padrão para todos os usuários (deve ser alterada em produção)
# Senha: "bitrix2024" (hash bcrypt)
DEFAULT_PASSWORD_HASH = pwd_context.hash("bitrix2024")

# Configuração de usuários
USERS: Dict[str, User] = {
    # Administradores (acesso total)
    "juliana.paes": User(
        username="juliana.paes",
        password_hash=DEFAULT_PASSWORD_HASH,
        full_name="Juliana Paes",
        role="admin",
        allowed_departments=None  # None = acesso a todos
    ),
    "mateus.souza": User(
        username="mateus.souza",
        password_hash=DEFAULT_PASSWORD_HASH,
        full_name="Mateus Souza",
        role="admin",
        allowed_departments=None  # None = acesso a todos
    ),
    
    # Supervisores por departamento
    "tayla.ferreira": User(
        username="tayla.ferreira",
        password_hash=DEFAULT_PASSWORD_HASH,
        full_name="Tayla Ferreira",
        role="supervisor",
        allowed_departments=["RNA"]
    ),
    "rafael.reimao": User(
        username="rafael.reimao",
        password_hash=DEFAULT_PASSWORD_HASH,
        full_name="Rafael Reimão",
        role="supervisor",
        allowed_departments=["DTC"]
    ),
    "deborah.szajin": User(
        username="deborah.szajin",
        password_hash=DEFAULT_PASSWORD_HASH,
        full_name="Deborah Szajin",
        role="supervisor",
        allowed_departments=["COMERCIAL"]
    ),
}


def get_user(username: str) -> Optional[User]:
    """Retorna um usuário pelo username."""
    return USERS.get(username.lower())


def get_allowed_departments_for_user(username: str) -> Optional[List[str]]:
    """Retorna a lista de departamentos permitidos para um usuário."""
    user = get_user(username)
    if user is None:
        return None
    if user.role == "admin":
        return None  # None = todos os departamentos
    return user.allowed_departments


def verify_user_password(username: str, password: str) -> bool:
    """Verifica se o username e senha estão corretos."""
    user = get_user(username)
    if user is None:
        return False
    return user.verify_password(password)


def hash_password(password: str) -> str:
    """Gera hash de uma senha (útil para atualizar senhas)."""
    return pwd_context.hash(password)
