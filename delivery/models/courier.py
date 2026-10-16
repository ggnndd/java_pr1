"""Курьер службы доставки."""

from delivery.models.errors import InvalidOperationError
from delivery.models.person import Person
from delivery.models.validation import require_positive_int


class Courier(Person):
    """Курьер. Одновременно может выполнять только один заказ."""

    def __init__(self, courier_id: int, name: str, phone: str) -> None:
        super().__init__(name, phone)
        self._id = require_positive_int(courier_id, "Идентификатор курьера")
        self._available = True

    @property
    def id(self) -> int:
        return self._id

    @property
    def is_available(self) -> bool:
        return self._available

    def occupy(self) -> None:
        """Занимает курьера под заказ.

        Raises:
            InvalidOperationError: если курьер уже занят другим заказом.
        """
        if not self._available:
            raise InvalidOperationError(f"Курьер {self.name} уже занят другим заказом")
        self._available = False

    def release(self) -> None:
        """Освобождает курьера после завершения или отмены заказа."""
        self._available = True

    def __str__(self) -> str:
        state = "свободен" if self._available else "занят"
        return f"#{self._id} {super().__str__()} — {state}"
