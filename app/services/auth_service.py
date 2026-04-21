import logging
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.user import User

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_all_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.role.desc(), User.username).all()


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """Возвращает пользователя при верных логине/пароле, иначе None."""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_user(
    db: Session,
    username: str,
    password: str,
    role: str = "employee",
) -> tuple[User | None, str]:
    """
    Создаёт нового пользователя. Возвращает (user, error_message).
    error_message пустой при успехе.
    """
    if not username or not password:
        return None, "Логин и пароль не могут быть пустыми."
    if len(password) < 6:
        return None, "Пароль должен содержать минимум 6 символов."
    if get_user_by_username(db, username):
        return None, f"Пользователь «{username}» уже существует."
    if role not in ("employee", "admin"):
        role = "employee"

    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Создан пользователь: %s (роль: %s)", username, role)
    return user, ""


def delete_user(db: Session, user_id: int, current_user_id: int) -> str:
    """
    Удаляет пользователя. Нельзя удалить самого себя.
    Возвращает сообщение об ошибке или пустую строку при успехе.
    """
    if user_id == current_user_id:
        return "Нельзя удалить собственную учётную запись."
    user = get_user_by_id(db, user_id)
    if not user:
        return "Пользователь не найден."
    username = user.username
    db.delete(user)
    db.commit()
    logger.info("Удалён пользователь: %s (id=%s)", username, user_id)
    return ""


def change_password(
    db: Session,
    user_id: int,
    new_password: str,
) -> str:
    """Меняет пароль пользователю. Возвращает ошибку или ''."""
    if len(new_password) < 6:
        return "Пароль должен содержать минимум 6 символов."
    user = get_user_by_id(db, user_id)
    if not user:
        return "Пользователь не найден."
    user.password_hash = hash_password(new_password)
    db.commit()
    logger.info("Пароль изменён для пользователя id=%s", user_id)
    return ""


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
