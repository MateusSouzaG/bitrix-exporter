"""Configuração de usuários e permissões do sistema."""
from typing import Dict, List, Optional
from passlib.context import CryptContext

# Contexto para hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _truncate_for_bcrypt(s: str, max_bytes: int = 72) -> str:
    """Bcrypt aceita no máximo 72 bytes; trunca para evitar ValueError no deploy."""
    if not s:
        return s
    b = s.encode("utf-8")[:max_bytes]
    return b.decode("utf-8", errors="ignore")


class User:
    """Representa um usuário do sistema."""
    
    def __init__(
        self,
        username: str,
        password_hash: str,
        full_name: str,
        role: str,
        allowed_departments: Optional[List[str]] = None,
        fixed_collaborator_name: Optional[str] = None
    ):
        """
        Args:
            username: Nome de usuário para login
            password_hash: Hash da senha (bcrypt)
            full_name: Nome completo do usuário
            role: "admin", "supervisor" ou "colaborador"
            allowed_departments: Lista de departamentos permitidos (None = todos para admin)
            fixed_collaborator_name: Nome fixo do colaborador na planilha (role='colaborador' só vê a si mesmo)
        """
        self.username = username
        self.password_hash = password_hash
        self.full_name = full_name
        self.role = role
        self.allowed_departments = allowed_departments
        self.fixed_collaborator_name = fixed_collaborator_name
    
    def has_access_to_department(self, department: str) -> bool:
        """Verifica se o usuário tem acesso a um departamento."""
        if self.role == "admin":
            return True
        if self.allowed_departments is None:
            return False
        return department.upper() in [d.upper() for d in self.allowed_departments]
    
    def verify_password(self, password: str) -> bool:
        """Verifica se a senha está correta."""
        password = _truncate_for_bcrypt(password or "")
        return pwd_context.verify(password, self.password_hash)


# Hashes de senha por gestor (bcrypt, senhas fortes 2026). Para trocar: hash_password("nova_senha") e substitua o hash.
HASH_JULIANA = "$2b$12$Ku5dwNipcP9G.E0zTlpOges.ybnQJBOzpKEjwbAk8UPvORo8Hj/cm"
HASH_MATEUS = "$2b$12$h8/KhUM9WkV9Laip8BxZmur/eTIHI0RLlkM.U3O8Fj95v36O0AenK"
HASH_TAYLA = "$2b$12$pVlJ.sd9xRitW4KRaHvt9.ae0kZC.uuTmlAB7gou40iE0pB50gWmm"
HASH_RAFAEL = "$2b$12$/U25ccGC5pjDcAKdP7ehiuUqHAinQFxr9L8l/KLxJWslP6RAWEcma"
HASH_DEBORAH = "$2b$12$6daKfwmyXiE7hvsNv17.LegTTL9f2jfvF6QycYv5CFvPWB/ce0oO."
HASH_CAROLINE = "$2b$12$sKYjUMEZPHzVek1O/6o0hewMv8Yn.dgPIG//4WDVwnkvsZV3XfqnO"
HASH_JESSICA = "$2b$12$YIB511J9uE1pAu4SrjoLKe6pbyBDEx7kaPUaf0EHNbRynqr9EHdum"
HASH_ROBERTA = "$2b$12$DnItISMe4lZlXvMYLN4ysOE7QreSpwsWuTBS2KzYrwlBIKI92RHb2"
HASH_LARISSA_P = "$2b$12$rA1M7FiGHfn3B2aRz62i5efidTC.ourcdenlravmm94xSkX0NX7.K"

# Configuração de usuários (cada um com sua própria senha)
USERS: Dict[str, User] = {
    # Administradores (acesso total)
    "juliana.paes": User(
        username="juliana.paes",
        password_hash=HASH_JULIANA,
        full_name="Juliana Paes",
        role="admin",
        allowed_departments=None
    ),
    "mateus.souza": User(
        username="mateus.souza",
        password_hash=HASH_MATEUS,
        full_name="Mateus Souza",
        role="admin",
        allowed_departments=None
    ),
    # Supervisores por departamento
    "tayla.ferreira": User(
        username="tayla.ferreira",
        password_hash=HASH_TAYLA,
        full_name="Tayla Ferreira",
        role="supervisor",
        allowed_departments=["RNA"]
    ),
    "rafael.reimao": User(
        username="rafael.reimao",
        password_hash=HASH_RAFAEL,
        full_name="Rafael Reimão",
        role="supervisor",
        allowed_departments=["DTC"]
    ),
    "deborah.szajin": User(
        username="deborah.szajin",
        password_hash=HASH_DEBORAH,
        full_name="Deborah Szajin",
        role="supervisor",
        allowed_departments=["COMERCIAL"]
    ),
    # Colaboradores individuais (só podem ver/exportar suas próprias tarefas)
    "caroline.santana": User(
        username="caroline.santana",
        password_hash=HASH_CAROLINE,
        full_name="Caroline Santana",
        role="colaborador",
        allowed_departments=["GI"],
        fixed_collaborator_name="Caroline Santana"
    ),
    "jessica.albino": User(
        username="jessica.albino",
        password_hash=HASH_JESSICA,
        full_name="Jéssica Albino",
        role="colaborador",
        allowed_departments=["GI"],
        fixed_collaborator_name="Jéssica Albino"
    ),
    "roberta.faria": User(
        username="roberta.faria",
        password_hash=HASH_ROBERTA,
        full_name="Roberta Faria",
        role="colaborador",
        allowed_departments=["GI"],
        fixed_collaborator_name="Roberta Faria"
    ),
    "larissa.porto": User(
        username="larissa.porto",
        password_hash=HASH_LARISSA_P,
        full_name="Larissa Porto",
        role="colaborador",
        allowed_departments=["GI"],
        fixed_collaborator_name="Larissa Porto"
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
    return pwd_context.hash(_truncate_for_bcrypt(password or ""))
