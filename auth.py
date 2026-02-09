"""Sistema de autenticação e controle de acesso."""
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
import secrets

from users_config import get_user, verify_user_password, User

# Configuração JWT
SECRET_KEY = secrets.token_urlsafe(32)  # Gera uma chave secreta aleatória
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Cria um token JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verifica e decodifica um token JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Autentica um usuário e retorna o objeto User se válido."""
    if not verify_user_password(username, password):
        return None
    return get_user(username)


def get_current_user_from_session(request: Request) -> Optional[User]:
    """Obtém o usuário atual da sessão (para uso com cookies/sessões)."""
    username = request.session.get("username")
    if not username:
        return None
    return get_user(username)


def require_auth(request: Request) -> User:
    """Exige autenticação e retorna o usuário atual."""
    user = get_current_user_from_session(request)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado. Faça login para continuar.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin(user: User) -> User:
    """Exige que o usuário seja administrador."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores podem acessar este recurso."
        )
    return user


def check_department_access(user: User, department: str) -> bool:
    """Verifica se o usuário tem acesso a um departamento."""
    return user.has_access_to_department(department)
