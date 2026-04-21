import sqlite3
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# SQLite файл создаётся в корне проекта
SQLALCHEMY_DATABASE_URL = "sqlite:///./bonus_cards.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)


# SQLite встроенный lower() не поддерживает кириллицу (только ASCII).
# Подменяем его Python-реализацией, которая корректно работает с Unicode.
@event.listens_for(Engine, "connect")
def _register_unicode_functions(dbapi_connection, _connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        dbapi_connection.create_function(
            "lower", 1, lambda s: s.lower() if isinstance(s, str) else s
        )
        dbapi_connection.create_function(
            "upper", 1, lambda s: s.upper() if isinstance(s, str) else s
        )


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency: открывает сессию БД, закрывает после запроса."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
