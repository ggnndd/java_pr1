"""Курьер службы доставки."""

from __future__ import annotations

from typing import TYPE_CHECKING

from delivery.models.errors import InvalidOperationError
from delivery.models.person import Person
from delivery.models.validation import require_positive_int

if TYPE_CHECKING:
    from delivery.models.order import Order


class Courier(Person):
    """Курьер. Одновременно закреплён не более чем за одним заказом.

    Связь «курьер — заказ» двусторонняя и меняется только согласованно:
    заказ назначает курьера через Order.assign_courier, а курьер
    принимает и отпускает заказ, сверяясь с состоянием самого заказа.
    Поэтому курьера нельзя занять или освободить в обход заказа.
    """

    def __init__(self, courier_id: int, name: str, phone: str) -> None:
        super().__init__(name, phone)
        self._id = require_positive_int(courier_id, "Идентификатор курьера")
        self._current_order: Order | None = None

    @property
    def id(self) -> int:
        return self._id

    @property
    def current_order(self) -> Order | None:
        """Заказ, который курьер выполняет сейчас, или None."""
        return self._current_order

    @property
    def is_available(self) -> bool:
        return self._current_order is None

    def take_order(self, order: Order) -> None:
        """Закрепляет за курьером заказ.

        Вызывается из Order.assign_courier: к этому моменту заказ уже
        должен указывать на этого курьера.

        Raises:
            InvalidOperationError: если заказ не назначил этого курьера
                или курьер уже выполняет другой заказ.
        """
        if order.courier is not self:
            raise InvalidOperationError(
                f"Курьер {self.name} не назначен на заказ #{order.id}: "
                "курьер назначается через заказ"
            )
        if self._current_order is order:
            return
        if self._current_order is not None:
            raise InvalidOperationError(
                f"Курьер {self.name} уже выполняет заказ #{self._current_order.id}"
            )
        self._current_order = order

    def release_order(self, order: Order) -> None:
        """Открепляет заказ от курьера.

        Допустимо, когда заказ завершён (доставлен или отменён) либо
        заказ уже отказался от этого курьера.

        Raises:
            InvalidOperationError: если курьер не выполняет этот заказ
                или заказ ещё активен и рассчитывает на курьера.
        """
        if self._current_order is not order:
            raise InvalidOperationError(
                f"Курьер {self.name} не выполняет заказ #{order.id}"
            )
        if order.courier is self and not order.status.is_final:
            raise InvalidOperationError(
                f"Заказ #{order.id} ещё не завершён — курьера нельзя освободить"
            )
        self._current_order = None

    def __str__(self) -> str:
        if self._current_order is None:
            state = "свободен"
        else:
            state = f"выполняет заказ #{self._current_order.id}"
        return f"#{self._id} {super().__str__()} — {state}"
