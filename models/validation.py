"""Общие проверки входных данных для сущностей предметной области."""

import re
from decimal import Decimal, InvalidOperation

_PHONE_PATTERN = re.compile(r"\+?\d{5,15}")
_CENT = Decimal("0.01")


def require_not_blank(value: str, field_name: str) -> str:
    """Проверяет, что строка не пустая, и возвращает её без крайних пробелов."""
    if value is None or not str(value).strip():
        raise ValueError(f"{field_name}: значение не может быть пустым")
    return str(value).strip()


def require_phone(phone: str) -> str:
    """Проверяет номер телефона и возвращает его в нормализованном виде."""
    normalized = re.sub(r"[\s()-]", "", require_not_blank(phone, "Телефон"))
    if not _PHONE_PATTERN.fullmatch(normalized):
        raise ValueError(
            f"Некорректный номер телефона: {phone} "
            "(ожидается от 5 до 15 цифр, например +79001234567)"
        )
    return normalized


def require_positive_int(value: int, field_name: str) -> int:
    """Проверяет, что значение является целым числом больше нуля."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name}: ожидается целое число больше нуля")
    return value


def require_non_negative_int(value: int, field_name: str) -> int:
    """Проверяет, что значение является целым неотрицательным числом."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name}: ожидается целое число не меньше нуля")
    return value


def require_positive_money(value, field_name: str) -> Decimal:
    """Преобразует значение в денежную сумму и проверяет её.

    Сумма должна быть больше нуля и содержать не более двух знаков
    после запятой: значение 0.001 отклоняется, а не округляется до нуля.
    Допускается запятая в качестве разделителя.
    """
    try:
        amount = Decimal(str(value).strip().replace(",", "."))
    except InvalidOperation:
        raise ValueError(f"{field_name}: «{value}» не является числом") from None
    if not amount.is_finite():
        raise ValueError(f"{field_name}: «{value}» не является числом")
    if amount <= 0:
        raise ValueError(f"{field_name}: значение должно быть больше нуля")
    try:
        rounded = amount.quantize(_CENT)
    except InvalidOperation:
        raise ValueError(f"{field_name}: слишком большое значение") from None
    if rounded != amount:
        raise ValueError(f"{field_name}: допускается не более двух знаков после запятой")
    return rounded
