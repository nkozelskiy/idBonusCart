import logging
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import authenticate_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    # Уже авторизован → сразу на поиск
    if request.session.get("user_id"):
        return RedirectResponse(url="/search", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, username, password)
    if not user:
        logger.warning("Неудачная попытка входа: %s", username)
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверный логин или пароль"},
            status_code=401,
        )

    # Сохраняем данные пользователя в сессии
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role
    logger.info("Вход: %s (роль: %s)", user.username, user.role)
    return RedirectResponse(url="/search", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    username = request.session.get("username", "unknown")
    request.session.clear()
    logger.info("Выход: %s", username)
    return RedirectResponse(url="/login", status_code=302)
