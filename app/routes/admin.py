import logging
from fastapi import APIRouter, Request, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.excel_service import process_excel

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
    }


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

    # Проверяем расширение файла
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

    except Exception as exc:
        logger.exception("Непредвиденная ошибка при загрузке '%s'", file.filename)
        ctx["error"] = "Непредвиденная ошибка при обработке файла. Проверьте лог."

    return templates.TemplateResponse("admin_upload.html", ctx)
