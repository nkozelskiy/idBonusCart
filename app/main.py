import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from app.database import engine, SessionLocal
from app.database import Base

# Импорт моделей — обязателен ДО create_all, чтобы таблицы были зарегистрированы
import app.models  # noqa: F401

from app.routes import auth, search, admin
from app.services.auth_service import create_default_users

# ─── Логирование ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─── Lifespan (запуск/остановка) ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # При старте: создаём таблицы и дефолтных пользователей
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        create_default_users(db)
    finally:
        db.close()
    logger.info("Приложение запущено")
    yield
    logger.info("Приложение остановлено")


# ─── Приложение ───────────────────────────────────────────────────────────────
app = FastAPI(title="Bonus Card Search", lifespan=lifespan)

# Сессии через подписанные cookies (itsdangerous под капотом)
# В продакшене SECRET_KEY нужно вынести в .env!
app.add_middleware(
    SessionMiddleware,
    secret_key="CHANGE_ME_IN_PRODUCTION_32chars!!",
    session_cookie="session",
    max_age=8 * 3600,  # сессия живёт 8 часов
    https_only=False,  # поставьте True при HTTPS
)

# Статические файлы (CSS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Роутеры
app.include_router(auth.router)
app.include_router(search.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    """Корень → перенаправляем на страницу входа."""
    return RedirectResponse(url="/login")
