# Импортируем модели, чтобы SQLAlchemy их зарегистрировал перед create_all
from app.models.user import User
from app.models.card import BonusCard

__all__ = ["User", "BonusCard"]
