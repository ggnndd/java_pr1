"""Клиент службы доставки."""

from delivery.models.validation import require_not_blank, require_phone


class Customer:
    """Клиент, оформляющий заказ."""

    def __init__(self, name: str, phone: str) -> None:
        self._name = require_not_blank(name, "Имя клиента")
        self._phone = require_phone(phone)

    @property
    def name(self) -> str:
        return self._name

    @property
    def phone(self) -> str:
        return self._phone

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Customer):
            return NotImplemented
        return self._name == other._name and self._phone == other._phone

    def __hash__(self) -> int:
        return hash((self._name, self._phone))

    def __str__(self) -> str:
        return f"{self._name} ({self._phone})"
