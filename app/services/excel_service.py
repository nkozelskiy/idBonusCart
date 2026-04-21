import io
import re
import logging
import pandas as pd
from sqlalchemy.orm import Session

from app.models.card import BonusCard

logger = logging.getLogger(__name__)

# Поддерживаемые названия столбцов (русские и английские варианты)
COLUMN_MAP = {
    "номер карты":    "card_number",
    "card_number":    "card_number",
    "карта":          "card_number",
    "фамилия":        "last_name",
    "last_name":      "last_name",
    "телефон":        "phone_number",
    "номер телефона": "phone_number",
    "phone_number":   "phone_number",
    "phone":          "phone_number",
}

REQUIRED = {"card_number", "last_name", "phone_number"}


def _normalize_phone(phone: str) -> str:
    return re.sub(r"[\s\+\-\(\)]", "", str(phone))


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Приводит названия столбцов к стандартным ключам."""
    renamed = {}
    for col in df.columns:
        key = col.strip().lower()
        if key in COLUMN_MAP:
            renamed[col] = COLUMN_MAP[key]
    return df.rename(columns=renamed)


def process_excel(db: Session, file_bytes: bytes) -> dict:
    """
    Читает Excel-файл, проверяет структуру и загружает данные в БД.

    Логика дублей:
    - Если запись с таким card_number уже есть → обновляем её.
    - Если card_number новый, но phone_number занят → обновляем ту запись.

    Возвращает словарь со статистикой: added / updated / skipped / errors.
    """
    try:
        df = pd.read_excel(io.BytesIO(file_bytes))
    except Exception as exc:
        logger.error("Ошибка чтения Excel: %s", exc)
        raise ValueError(f"Не удалось прочитать файл: {exc}") from exc

    df = _normalize_columns(df)

    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"В файле отсутствуют столбцы: {', '.join(missing)}")

    added = updated = skipped = errors = 0

    for idx, row in df.iterrows():
        try:
            card_number  = str(row["card_number"]).strip()
            last_name    = str(row["last_name"]).strip()
            phone_number = _normalize_phone(row["phone_number"])

            # Пропускаем строки без обязательных данных
            if not card_number or card_number == "nan":
                skipped += 1
                continue
            if not phone_number or phone_number == "nan":
                skipped += 1
                continue

            # Ищем существующую запись по номеру карты или телефону
            existing = (
                db.query(BonusCard)
                .filter(
                    (BonusCard.card_number == card_number)
                    | (BonusCard.phone_number == phone_number)
                )
                .first()
            )

            if existing:
                existing.card_number  = card_number
                existing.last_name    = last_name
                existing.phone_number = phone_number
                updated += 1
            else:
                db.add(BonusCard(
                    card_number=card_number,
                    last_name=last_name,
                    phone_number=phone_number,
                ))
                added += 1

        except Exception as exc:
            logger.error("Ошибка в строке %s: %s", idx, exc)
            errors += 1

    db.commit()
    logger.info("Excel загружен: +%d ~%d skip%d err%d", added, updated, skipped, errors)
    return {"added": added, "updated": updated, "skipped": skipped, "errors": errors}
