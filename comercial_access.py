# -*- coding: utf-8 -*-
"""Controle de acesso ao módulo Comercial."""
from fastapi import HTTPException, status

from users_config import User
from comercial_config import COMERCIAL_DEPT


def user_has_timesheet_access(user: User) -> bool:
    """Usuários comercial_only não acessam dashboard/exportação de tarefas."""
    return not getattr(user, "comercial_only", False)


def user_home_path(user: User) -> str:
    if getattr(user, "comercial_only", False):
        return "/comercial"
    return "/dashboard"


def user_can_access_comercial(user: User) -> bool:
    if user.role == "admin":
        return True
    if user.role == "supervisor" and user.allowed_departments:
        allowed = [d.upper() for d in user.allowed_departments]
        return COMERCIAL_DEPT.upper() in allowed
    if getattr(user, "comercial_only", False):
        return True
    if user.role == "colaborador" and user.fixed_collaborator_name:
        return True
    return False


def require_comercial_access(user: User) -> User:
    if not user_can_access_comercial(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado ao módulo Comercial.",
        )
    return user


def user_can_manage_comercial_reports(user: User) -> bool:
    """Supervisor COMERCIAL ou admin: exportar relatório de todos."""
    if user.role == "admin":
        return True
    if user.role == "supervisor" and user.allowed_departments:
        return COMERCIAL_DEPT.upper() in [d.upper() for d in user.allowed_departments]
    return False
