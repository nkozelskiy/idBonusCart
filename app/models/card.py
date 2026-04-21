from sqlalchemy import Column, Integer, String
from app.database import Base


class BonusCard(Base):
    __tablename__ = "bonus_cards"

    id = Column(Integer, primary_key=True, index=True)

    # Уникальный номер карты (ключ для защиты от дублей)
    card_number = Column(String(64), unique=True, index=True, nullable=False)

    last_name = Column(String(128), index=True, nullable=False)

    # Хранится нормализованный номер (только цифры, без +, пробелов и т.д.)
    phone_number = Column(String(32), unique=True, index=True, nullable=False)
