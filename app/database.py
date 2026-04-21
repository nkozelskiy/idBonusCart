from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# SQLite файл создаётся в корне проекта
SQLALCHEMY_DATABASE_URL = "sqlite:///./bonus_cards.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # нужно для SQLite + FastAPI
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
