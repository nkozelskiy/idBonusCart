import logging
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.user import User

logger = logging.getLogger(__name__)

# Контекст хэширования паролей (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """Возвращает пользователя при верных логине/пароле, иначе None."""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_default_users(db: Session) -> None:
    """Создаёт дефолтных пользователей при первом запуске (если их нет)."""
    defaults = [
        {"username": "admin",    "password": "admin123",    "role": "admin"},
        {"username": "employee", "password": "employee123", "role": "employee"},
    ]
    for item in defaults:
        if not get_user_by_username(db, item["username"]):
            db.add(User(
                username=item["username"],
                password_hash=hash_password(item["password"]),
                role=item["role"],
            ))
            logger.info("Создан дефолтный пользователь: %s", item["username"])
    db.commit()
