"""Курьер службы доставки."""

from delivery.models.validation import (
    require_not_blank,
    require_phone,
    require_positive_int,
)


class Courier:
    """Курьер. Одновременно может выполнять только один заказ."""

    def __init__(self, courier_id: int, name: str, phone: str) -> None:
        self._id = require_positive_int(courier_id, "Идентификатор курьера")
        self._name = require_not_blank(name, "Имя курьера")
        self._phone = require_phone(phone)
        self._available = True

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def phone(self) -> str:
        return self._phone

    @property
    def is_available(self) -> bool:
        return self._available

    def occupy(self) -> None:
        """Занимает курьера под заказ.

        Raises:
            RuntimeError: если курьер уже занят другим заказом.
        """
        if not self._available:
            raise RuntimeError(f"Курьер {self._name} уже занят другим заказом")
        self._available = False

    def release(self) -> None:
        """Освобождает курьера после завершения или отмены заказа."""
        self._available = True

    def __str__(self) -> str:
        state = "свободен" if self._available else "занят"
        return f"#{self._id} {self._name} ({self._phone}) — {state}"
