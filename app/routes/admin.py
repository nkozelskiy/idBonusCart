import logging
from fastapi import APIRouter, Request, File, Form, UploadFile, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.excel_service import process_excel
from app.services.auth_service import (
    get_all_users,
    create_user,
    delete_user,
    change_password,
)

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


def _require_admin(request: Request):
    """Возвращает RedirectResponse если пользователь не администратор."""
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=302)
    if request.session.get("role") != "admin":
        return RedirectResponse(url="/search", status_code=302)
    return None


def _base_ctx(request: Request) -> dict:
    return {
        "request":  request,
        "username": request.session.get("username"),
        "role":     request.session.get("role"),
    }


# ─── Загрузка Excel ───────────────────────────────────────────────────────────

@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("admin_upload.html", _base_ctx(request))


@router.post("/upload", response_class=HTMLResponse)
async def upload_excel(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    redirect = _require_admin(request)
    if redirect:
        return redirect

    ctx = _base_ctx(request)

    if not file.filename.lower().endswith(".xlsx"):
        ctx["error"] = "Допускаются только файлы формата .xlsx"
        return templates.TemplateResponse("admin_upload.html", ctx)

    try:
        contents = await file.read()
        stats = process_excel(db, contents)
        ctx["success"] = (
            f"Загрузка завершена успешно! "
            f"Добавлено: {stats['added']}, "
            f"обновлено: {stats['updated']}, "
            f"пропущено: {stats['skipped']}, "
            f"ошибок: {stats['errors']}."
        )
        logger.info("Файл '%s' загружен: %s", file.filename, stats)

    except ValueError as exc:
        logger.error("Ошибка формата файла '%s': %s", file.filename, exc)
        ctx["error"] = str(exc)

    except Exception:
        logger.exception("Непредвиденная ошибка при загрузке '%s'", file.filename)
        ctx["error"] = "Непредвиденная ошибка при обработке файла. Проверьте лог."

    return templates.TemplateResponse("admin_upload.html", ctx)


# ─── Управление пользователями ────────────────────────────────────────────────

@router.get("/users", response_class=HTMLResponse)
async def users_page(request: Request, db: Session = Depends(get_db)):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    ctx = _base_ctx(request)
    ctx["users"] = get_all_users(db)
    ctx["current_user_id"] = request.session.get("user_id")
    return templates.TemplateResponse("admin_users.html", ctx)


@router.post("/users/create", response_class=HTMLResponse)
async def create_user_route(
    request: Request,
    new_username: str = Form(...),
    new_password: str = Form(...),
    new_role: str = Form(default="employee"),
    db: Session = Depends(get_db),
):
    redirect = _require_admin(request)
    if redirect:
        return redirect

    ctx = _base_ctx(request)
    ctx["current_user_id"] = request.session.get("user_id")

    _, error = create_user(db, new_username.strip(), new_password, new_role)
    if error:
        ctx["error"] = error
    else:
        ctx["success"] = f"Пользователь «{new_username.strip()}» успешно создан."

    ctx["users"] = get_all_users(db)
    return templates.TemplateResponse("admin_users.html", ctx)


@router.post("/users/delete/{user_id}", response_class=HTMLResponse)
async def delete_user_route(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
):
    redirect = _require_admin(request)
    if redirect:
        return redirect

    current_user_id = request.session.get("user_id")
    error = delete_user(db, user_id, current_user_id)

    ctx = _base_ctx(request)
    ctx["current_user_id"] = current_user_id
    ctx["users"] = get_all_users(db)
    if error:
        ctx["error"] = error
    else:
        ctx["success"] = "Пользователь удалён."
    return templates.TemplateResponse("admin_users.html", ctx)


@router.post("/users/password/{user_id}", response_class=HTMLResponse)
async def change_password_route(
    request: Request,
    user_id: int,
    new_password: str = Form(...),
    db: Session = Depends(get_db),
):
    redirect = _require_admin(request)
    if redirect:
        return redirect

    error = change_password(db, user_id, new_password)

    ctx = _base_ctx(request)
    ctx["current_user_id"] = request.session.get("user_id")
    ctx["users"] = get_all_users(db)
    if error:
        ctx["error"] = error
    else:
        ctx["success"] = "Пароль успешно изменён."
    return templates.TemplateResponse("admin_users.html", ctx)
