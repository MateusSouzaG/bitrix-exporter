"""Aplicação web FastAPI para exportação de tarefas Bitrix24."""
import logging
from typing import Optional
from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware import Middleware
import os

from auth import authenticate_user, require_auth, get_current_user_from_session
from users_config import get_user, get_allowed_departments_for_user, USERS
from web_services import (
    export_tasks_to_excel_bytes,
    get_available_departments,
    filter_departments_by_user_access,
    filter_collaborator_names_by_user_access,
)
from excel_handler import read_collaborators_sheet
from date_filters import get_date_range_for_preset, PRESET_OPTIONS
from config import COLLABORATORS_SHEET_PATH, FALLBACK_DEPARTMENTS
import excel_handler as _excel_handler

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Inicializar FastAPI com middleware de sessão
middleware = [
    Middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "change-this-secret-key-in-production"))
]
app = FastAPI(title="Bitrix24 Exporter", version="1.0.0", middleware=middleware)

# Log de diagnóstico: confirma qual módulo de Excel está carregado (deve mostrar 14 colunas incluindo "Data do lançamento")
logger.info(
    "Excel export: módulo=%s colunas=%d",
    getattr(_excel_handler, "__file__", "?"),
    len(getattr(_excel_handler, "EXCEL_EXPORT_COLUMNS", [])),
)

# Configurar templates e arquivos estáticos
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redireciona para login se não autenticado, senão para dashboard."""
    user = get_current_user_from_session(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página de login."""
    user = get_current_user_from_session(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    error = request.query_params.get("error", "")
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": error
    })


@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Processa login do usuário."""
    user = authenticate_user(username, password)
    if not user:
        return RedirectResponse(
            url="/login?error=Usuário ou senha inválidos",
            status_code=302
        )
    
    # Criar sessão
    request.session["username"] = user.username
    request.session["full_name"] = user.full_name
    request.session["role"] = user.role
    
    logger.info(f"Usuário {user.username} fez login")
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/logout")
async def logout(request: Request):
    """Faz logout do usuário."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@app.get("/api/collaborators")
async def api_collaborators(request: Request):
    """Retorna a lista de nomes dos colaboradores que o usuário pode acessar (admin = todos, supervisor = só do seu departamento)."""
    user = require_auth(request)
    try:
        collaborators_map = read_collaborators_sheet(COLLABORATORS_SHEET_PATH)
        names = filter_collaborator_names_by_user_access(collaborators_map, user)
        return {"names": names}
    except Exception as e:
        logger.error(f"Erro ao carregar colaboradores para API: {e}")
        return {"names": []}


@app.get("/api/departments")
async def api_departments(request: Request):
    """Retorna a lista de departamentos para o dropdown (requer login)."""
    user = require_auth(request)
    try:
        collaborators_map = read_collaborators_sheet(COLLABORATORS_SHEET_PATH)
        all_departments = get_available_departments(collaborators_map)
        if not all_departments:
            depts_from_users = set(d.upper() for d in FALLBACK_DEPARTMENTS)
            for u in USERS.values():
                if u.allowed_departments:
                    depts_from_users.update(d.upper() for d in u.allowed_departments)
            all_departments = sorted(depts_from_users)
        available_departments = filter_departments_by_user_access(all_departments, user)
        return {"departments": available_departments}
    except Exception as e:
        logger.error(f"Erro ao carregar departamentos para API: {e}")
        return {"departments": []}


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard principal."""
    user = require_auth(request)
    
    # Carregar departamentos e lista de colaboradores para o dropdown
    try:
        collaborators_map = read_collaborators_sheet(COLLABORATORS_SHEET_PATH)
        all_departments = get_available_departments(collaborators_map)
        if not all_departments:
            depts_from_users = set(d.upper() for d in FALLBACK_DEPARTMENTS)
            for u in USERS.values():
                if u.allowed_departments:
                    depts_from_users.update(d.upper() for d in u.allowed_departments)
            all_departments = sorted(depts_from_users)
        available_departments = filter_departments_by_user_access(all_departments, user)
        collaborator_names = filter_collaborator_names_by_user_access(collaborators_map, user)
    except Exception as e:
        logger.error(f"Erro ao carregar colaboradores/departamentos: {e}")
        collaborator_names = []
        depts_fallback = set(d.upper() for d in FALLBACK_DEPARTMENTS)
        for u in USERS.values():
            if u.allowed_departments:
                depts_fallback.update(d.upper() for d in u.allowed_departments)
        available_departments = filter_departments_by_user_access(sorted(depts_fallback), user)
    
    all_collaborators_label = "Todos os colaboradores" if user.role == "admin" else "Todos os colaboradores do departamento"
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "departments": available_departments,
        "collaborator_names": collaborator_names,
        "is_admin": user.role == "admin",
        "all_collaborators_label": all_collaborators_label,
        "preset_options": PRESET_OPTIONS
    })


def convert_datetime_local_to_iso8601(dt_str: Optional[str]) -> Optional[str]:
    """Converte formato datetime-local (YYYY-MM-DDTHH:MM) para ISO8601 com timezone."""
    if not dt_str or not dt_str.strip():
        return None
    
    dt_str = dt_str.strip()
    
    # Se já está no formato ISO8601 completo, retornar como está
    if len(dt_str) > 16 and ("+" in dt_str[-6:] or dt_str[-6:].startswith("-")):
        return dt_str
    
    # Formato datetime-local: YYYY-MM-DDTHH:MM
    # Converter para: YYYY-MM-DDTHH:MM:00-03:00
    if "T" in dt_str and len(dt_str) == 16:
        return dt_str + ":00-03:00"
    elif "T" in dt_str:
        # Já tem segundos mas não tem timezone
        if len(dt_str) == 19:
            return dt_str + "-03:00"
    
    return dt_str


@app.post("/export")
async def export_tasks(
    request: Request,
    dept: str = Form(None),
    user_substring: str = Form(None),
    activity_preset: str = Form(None),
    activity_from: str = Form(None),
    activity_to: str = Form(None),
    status_filter: str = Form(None)
):
    """Exporta tarefas para Excel."""
    user = require_auth(request)
    
    # Supervisores: sem filtro = restringir ao primeiro (e único) departamento permitido
    if user.role != "admin" and user.allowed_departments and not dept and not (user_substring or "").strip():
        dept = user.allowed_departments[0]
        logger.info(f"Supervisor {user.username}: sem filtro; usando departamento padrão {dept}")
    
    # Validar acesso ao departamento
    if dept:
        if not user.has_access_to_department(dept):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Você não tem acesso ao departamento {dept}"
            )
    
    # Processar filtro de data: pré-definido ou intervalo personalizado
    activity_from_iso = None
    activity_to_iso = None
    
    if activity_preset and activity_preset != "intervalo_personalizado" and activity_preset != "":
        # Usar opção pré-definida
        date_range = get_date_range_for_preset(activity_preset)
        if date_range:
            activity_from_iso, activity_to_iso = date_range
            logger.info(f"Usando filtro pré-definido: {activity_preset} -> {activity_from_iso} a {activity_to_iso}")
        else:
            logger.info(f"Filtro pré-definido '{activity_preset}' não requer datas (Todo o período)")
    elif activity_from or activity_to:
        # Usar intervalo personalizado
        activity_from_iso = convert_datetime_local_to_iso8601(activity_from) if activity_from else None
        activity_to_iso = convert_datetime_local_to_iso8601(activity_to) if activity_to else None
    
    logger.info("=" * 60)
    logger.info(f"Exportação solicitada por {user.username} ({user.full_name})")
    logger.info(f"  - Departamento: {dept or 'Todos'}")
    logger.info(f"  - Colaborador: {user_substring or 'Todos'}")
    logger.info(f"  - Data Inicial (ACTIVITY_DATE): {activity_from_iso or 'Não especificada'}")
    logger.info(f"  - Data Final (ACTIVITY_DATE): {activity_to_iso or 'Não especificada'}")
    logger.info(f"  - Status: {status_filter or 'Todos'}")
    logger.info("=" * 60)
    
    try:
        # Exportar tarefas
        excel_bytes, num_rows = export_tasks_to_excel_bytes(
            user=user,
            dept=dept if dept else None,
            user_substring=user_substring if user_substring else None,
            activity_from=activity_from_iso,
            activity_to=activity_to_iso,
            status=status_filter if status_filter else None,
            collaborators_file=COLLABORATORS_SHEET_PATH
        )
        
        # Gerar nome do arquivo
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Exportacao_Tarefas_{timestamp}.xlsx"
        
        logger.info(f"Usuário {user.username} exportou {num_rows} linhas")
        
        # Se não houver linhas, ainda retornar o Excel (vazio mas com estrutura)
        if num_rows == 0:
            logger.warning(f"Exportação gerou 0 linhas. Filtros: dept={dept}, user={user_substring}, "
                         f"from={activity_from_iso}, to={activity_to_iso}, status={status_filter}")
        
        return StreamingResponse(
            excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Erro na exportação: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao exportar tarefas: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
