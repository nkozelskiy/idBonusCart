import re
import logging
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.search_service import search_cards


def _clean_phone(raw: str) -> str:
    """Возвращает пустую строку, если пользователь ввёл только маску без цифр."""
    digits = re.sub(r'\D', '', raw).lstrip('78')
    return raw.strip() if digits else ""

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


def _base_ctx(request: Request) -> dict:
    """Общий контекст для шаблона search.html."""
    return {
        "request":  request,
        "username": request.session.get("username"),
        "role":     request.session.get("role"),
    }


@router.get("/search", response_class=HTMLResponse)
async def search_page(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("search.html", _base_ctx(request))


@router.post("/search", response_class=HTMLResponse)
async def search_result(
    request: Request,
    phone:     str = Form(default=""),
    last_name: str = Form(default=""),
    db: Session = Depends(get_db),
):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=302)

    phone     = _clean_phone(phone)
    last_name = last_name.strip()
    ctx       = _base_ctx(request)
    ctx.update({"phone": phone, "last_name": last_name, "searched": True})

    # Валидация: хотя бы одно поле должно быть заполнено
    if not phone and not last_name:
        ctx["error"] = "Введите номер телефона или фамилию для поиска."
        return templates.TemplateResponse("search.html", ctx)

    results = search_cards(db, phone=phone or None, last_name=last_name or None)
    ctx["results"] = results
    return templates.TemplateResponse("search.html", ctx)
