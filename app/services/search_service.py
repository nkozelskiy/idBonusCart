import re
import logging
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.models.card import BonusCard

logger = logging.getLogger(__name__)


def normalize_phone(phone: str) -> str:
    """Убирает +, пробелы, скобки, тире — оставляет только цифры."""
    return re.sub(r"[\s\+\-\(\)]", "", phone)


def search_cards(
    db: Session,
    phone: str | None = None,
    last_name: str | None = None,
) -> list[BonusCard]:
    """
    Ищет бонусные карты по телефону и/или фамилии.

    - Телефон: точное совпадение нормализованной строки (хранится нормализованно).
    - Фамилия: частичное совпадение без учёта регистра.
    - Если переданы оба поля — возвращает совпадения по любому из них (OR).
    """
    if not phone and not last_name:
        return []

    filters = []

    if phone:
        normalized = normalize_phone(phone)
        if normalized:
            filters.append(BonusCard.phone_number.contains(normalized))

    if last_name:
        clean = last_name.strip()
        if clean:
            # func.lower для регистронезависимого поиска (поддержка Unicode в SQLite)
            filters.append(
                func.lower(BonusCard.last_name).contains(clean.lower())
            )

    results = db.query(BonusCard).filter(or_(*filters)).all()
    logger.info(
        "Поиск: phone=%s last_name=%s → найдено %d",
        phone, last_name, len(results),
    )
    return results
