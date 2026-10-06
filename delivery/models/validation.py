"""Общие проверки входных данных для сущностей предметной области."""

import re
from decimal import Decimal, InvalidOperation

_PHONE_PATTERN = re.compile(r"\+?\d{5,15}")


def require_not_blank(value: str, field_name: str) -> str:
    """Проверяет, что строка не пустая, и возвращает её без крайних пробелов."""
    if value is None or not str(value).strip():
        raise ValueError(f"{field_name}: значение не может быть пустым")
    return str(value).strip()


def require_phone(phone: str) -> str:
    """Проверяет номер телефона и возвращает его в нормализованном виде."""
    normalized = re.sub(r"[\s()-]", "", require_not_blank(phone, "Телефон"))
    if not _PHONE_PATTERN.fullmatch(normalized):
        raise ValueError(f"Некорректный номер телефона: {phone}")
    return normalized


def require_positive_int(value: int, field_name: str) -> int:
    """Проверяет, что значение является целым числом больше нуля."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name}: ожидается целое число больше нуля")
    return value


def require_positive_money(value, field_name: str) -> Decimal:
    """Преобразует значение в Decimal и проверяет, что оно больше нуля."""
    try:
        amount = Decimal(str(value))
    except InvalidOperation:
        raise ValueError(f"{field_name}: ожидается число") from None
    if not amount.is_finite() or amount <= 0:
        raise ValueError(f"{field_name}: значение должно быть больше нуля")
    return amount.quantize(Decimal("0.01"))
