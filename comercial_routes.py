# -*- coding: utf-8 -*-
"""
Rotas do módulo Comercial — isoladas do exportador de tarefas (/export, /dashboard).
"""
import logging
from datetime import date

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from auth import get_current_user_from_session, require_auth
from comercial_access import (
    require_comercial_access,
    user_can_manage_comercial_reports,
    user_has_timesheet_access,
)
from comercial_collaborators import comercial_collaborator_list
from comercial_config import COMERCIAL_DEPT, get_week_range
from comercial_daily_store import save_daily_report
from comercial_report import build_weekly_excel_bytes
from config import COLLABORATORS_SHEET_PATH
from excel_handler import read_collaborators_sheet

logger = logging.getLogger(__name__)

comercial_router = APIRouter(prefix="/comercial", tags=["comercial"])
templates = Jinja2Templates(directory="templates")


@comercial_router.get("", response_class=HTMLResponse)
@comercial_router.get("/", response_class=HTMLResponse)
async def comercial_home(request: Request):
    user = require_auth(request)
    require_comercial_access(user)
    week_start, week_end = get_week_range(previous_week=True)
    can_export_all = user_can_manage_comercial_reports(user)
    return templates.TemplateResponse(
        request=request,
        name="comercial_dashboard.html",
        context={
            "user": user,
            "week_start": week_start.strftime("%d/%m/%Y"),
            "week_end": week_end.strftime("%d/%m/%Y"),
            "can_export_all": can_export_all,
            "comercial_dept": COMERCIAL_DEPT,
            "show_timesheet_link": user_has_timesheet_access(user),
        },
    )


@comercial_router.get("/formulario", response_class=HTMLResponse)
async def comercial_form_page(request: Request):
    user = require_auth(request)
    require_comercial_access(user)
    collaborators_map = read_collaborators_sheet(COLLABORATORS_SHEET_PATH)
    collab_list = comercial_collaborator_list(collaborators_map)

    if user.role == "colaborador" and user.fixed_collaborator_name:
        names = [user.fixed_collaborator_name]
        fixed_name = user.fixed_collaborator_name
    else:
        names = [n for _, n in collab_list]
        fixed_name = ""

    today = date.today().isoformat()
    return templates.TemplateResponse(
        request=request,
        name="comercial_form.html",
        context={
            "user": user,
            "collaborator_names": names,
            "fixed_collaborator_name": fixed_name,
            "default_date": today,
            "success": request.query_params.get("success", ""),
            "error": request.query_params.get("error", ""),
            "show_timesheet_link": user_has_timesheet_access(user),
        },
    )


@comercial_router.post("/formulario")
async def comercial_form_submit(
    request: Request,
    collaborator_name: str = Form(...),
    report_date: str = Form(...),
    start_time: str = Form(""),
    end_time: str = Form(""),
    contacts_count: int = Form(0),
    meetings_scheduled: int = Form(0),
    meetings_institutional: int = Form(0),
    meetings_desdobramento: int = Form(0),
    meetings_nutricao: int = Form(0),
):
    user = require_auth(request)
    require_comercial_access(user)

    if user.role == "colaborador" and user.fixed_collaborator_name:
        collaborator_name = user.fixed_collaborator_name

    collaborators_map = read_collaborators_sheet(COLLABORATORS_SHEET_PATH)
    allowed_names = {n for _, n in comercial_collaborator_list(collaborators_map)}
    if collaborator_name.strip() not in allowed_names:
        return RedirectResponse(
            url="/comercial/formulario?error=Colaborador+inválido",
            status_code=302,
        )

    try:
        save_daily_report(
            collaborator_name=collaborator_name,
            report_date=report_date,
            start_time=start_time,
            end_time=end_time,
            contacts_count=contacts_count,
            meetings_scheduled=meetings_scheduled,
            meetings_institutional=meetings_institutional,
            meetings_desdobramento=meetings_desdobramento,
            meetings_nutricao=meetings_nutricao,
        )
    except Exception as e:
        logger.error(f"Erro ao salvar resumo diário: {e}", exc_info=True)
        return RedirectResponse(
            url="/comercial/formulario?error=Erro+ao+salvar",
            status_code=302,
        )

    return RedirectResponse(
        url="/comercial/formulario?success=1",
        status_code=302,
    )


@comercial_router.post("/exportar-semanal")
async def comercial_export_weekly(request: Request):
    user = require_auth(request)
    require_comercial_access(user)
    if not user_can_manage_comercial_reports(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas coordenação COMERCIAL ou administradores podem exportar o relatório completo.",
        )
    try:
        excel_bytes, num_rows, week_start, week_end = build_weekly_excel_bytes(
            previous_week=True
        )
        from datetime import datetime

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Relatorio_Comercial_Semana_{week_start.strftime('%Y%m%d')}_{ts}.xlsx"
        logger.info(
            f"Relatório comercial exportado por {user.username}: {num_rows} colaboradores"
        )
        return StreamingResponse(
            excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"Erro relatório comercial: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar relatório: {str(e)}",
        )
