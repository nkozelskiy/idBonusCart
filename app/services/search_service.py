import re
import logging
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.models.card import BonusCard

logger = logging.getLogger(__name__)


def extract_local_phone(phone: str) -> str:
    """
    Извлекает локальную часть номера для поиска.

    Логика:
      1. Убирает все нецифровые символы.
      2. Убирает ведущий код страны (7 или 8).
      3. Убирает код города (первые 3 цифры), оставляя локальный номер.
      4. Если введено меньше 4 цифр — возвращает их как есть (частичный ввод).

    Примеры:
      '+7 (999) 1234567'  →  '1234567'
      '+7 (999) 123'      →  '123'
      '+7 ('              →  ''         (только префикс маски — пусто)
      '79991234567'       →  '1234567'
      '89991234567'       →  '1234567'
    """
    digits = re.sub(r'\D', '', phone)
    if digits.startswith(('7', '8')):
        digits = digits[1:]        # убираем код страны
    if len(digits) > 3:
        return digits[3:]          # убираем код города → локальный номер
    return digits                  # частичный ввод (< 4 цифр)


def search_cards(
    db: Session,
    phone: str | None = None,
    last_name: str | None = None,
) -> list[BonusCard]:
    """
    Поиск бонусных карт по телефону и/или фамилии.

    Телефон: ищет по локальной части (последние 7 цифр), поддерживает
             частичное совпадение — например, ввод 3-х цифр найдёт все
             номера, содержащие эти цифры в локальной части.

    Фамилия: частичное совпадение без учёта регистра и языка
             — например, «ник» совпадает с «Никита», «НИКИТИН» и т.д.

    Если переданы оба поля — OR-логика (результаты по любому условию).
    """
    if not phone and not last_name:
        return []

    filters = []

    if phone:
        local = extract_local_phone(phone)
        if local:
            filters.append(BonusCard.phone_number.contains(local))

    if last_name:
        clean = last_name.strip()
        if clean:
            # func.lower переопределён в database.py для поддержки кириллицы
            filters.append(
                func.lower(BonusCard.last_name).contains(clean.lower())
            )

    if not filters:
        return []

    results = db.query(BonusCard).filter(or_(*filters)).all()
    logger.info(
        "Поиск: phone=%r last_name=%r → найдено %d",
        phone, last_name, len(results),
    )
    return results
