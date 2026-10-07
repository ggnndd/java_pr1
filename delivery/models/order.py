"""Заказ службы доставки."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from delivery.models.courier import Courier
from delivery.models.customer import Customer
from delivery.models.delivery_methods import DeliveryMethod
from delivery.models.errors import InvalidOperationError
from delivery.models.order_item import OrderItem
from delivery.models.order_status import OrderStatus
from delivery.models.validation import require_not_blank, require_positive_int


class Order:
    """Заказ: клиент, адрес доставки, позиции, способ доставки, курьер и статус.

    Состояние изменяется только через методы, которые проверяют
    допустимость операции.
    """

    def __init__(self, order_id: int, customer: Customer, address: str) -> None:
        if not isinstance(customer, Customer):
            raise TypeError("Заказ должен содержать клиента")
        self._id = require_positive_int(order_id, "Номер заказа")
        self._customer = customer
        self._address = require_not_blank(address, "Адрес доставки")
        self._items: list[OrderItem] = []
        self._status = OrderStatus.CREATED
        self._delivery_method: DeliveryMethod | None = None
        self._courier: Courier | None = None

    @property
    def id(self) -> int:
        return self._id

    @property
    def customer(self) -> Customer:
        return self._customer

    @property
    def address(self) -> str:
        return self._address

    @property
    def items(self) -> tuple[OrderItem, ...]:
        """Позиции заказа (только для чтения)."""
        return tuple(self._items)

    @property
    def status(self) -> OrderStatus:
        return self._status

    @property
    def delivery_method(self) -> DeliveryMethod | None:
        return self._delivery_method

    @property
    def courier(self) -> Courier | None:
        return self._courier

    @property
    def items_total(self) -> Decimal:
        """Стоимость всех позиций без учёта доставки."""
        return sum((item.total for item in self._items), Decimal("0.00"))

    @property
    def total_quantity(self) -> int:
        """Общее количество единиц товара в заказе."""
        return sum(item.quantity for item in self._items)

    @property
    def delivery_cost(self) -> Decimal | None:
        """Стоимость доставки или None, если способ доставки не выбран."""
        if self._delivery_method is None:
            return None
        return self._delivery_method.calculate_cost(self)

    @property
    def total_cost(self) -> Decimal:
        """Итоговая стоимость заказа с учётом доставки."""
        return self.items_total + (self.delivery_cost or Decimal("0.00"))

    @property
    def estimated_time(self) -> timedelta | None:
        """Ориентировочный срок доставки или None, если способ не выбран."""
        if self._delivery_method is None:
            return None
        return self._delivery_method.estimate_time(self)

    @property
    def available_statuses(self) -> tuple[OrderStatus, ...]:
        """Статусы, в которые можно перевести заказ из текущего."""
        if self._delivery_method is None:
            if self._status is OrderStatus.CREATED:
                return (OrderStatus.CANCELLED,)
            return ()
        return self._delivery_method.next_statuses(self._status)

    def add_item(self, item: OrderItem) -> None:
        """Добавляет позицию в заказ.

        Raises:
            InvalidOperationError: если заказ уже подтверждён.
        """
        if not isinstance(item, OrderItem):
            raise TypeError("Ожидается позиция заказа")
        self._ensure_editable("добавить позицию")
        self._items.append(item)

    def set_delivery_method(self, method: DeliveryMethod) -> None:
        """Выбирает способ доставки.

        Если новый способ не требует курьера, ранее назначенный курьер
        освобождается.

        Raises:
            InvalidOperationError: если заказ уже подтверждён.
        """
        if not isinstance(method, DeliveryMethod):
            raise TypeError("Ожидается способ доставки")
        self._ensure_editable("изменить способ доставки")
        if not method.requires_courier:
            self._unassign_courier()
        self._delivery_method = method

    def assign_courier(self, courier: Courier) -> None:
        """Назначает курьера на заказ, заменяя ранее назначенного.

        Raises:
            InvalidOperationError: если способ доставки не выбран или
                не требует курьера, заказ уже передан в доставку
                или курьер занят.
        """
        if not isinstance(courier, Courier):
            raise TypeError("Ожидается курьер")
        if self._delivery_method is None:
            raise InvalidOperationError("Сначала выберите способ доставки")
        if not self._delivery_method.requires_courier:
            raise InvalidOperationError(
                f"Способ «{self._delivery_method.name}» не требует курьера"
            )
        if self._status not in (OrderStatus.CREATED, OrderStatus.CONFIRMED):
            raise InvalidOperationError(
                f"Нельзя назначить курьера: заказ в статусе «{self._status.title}»"
            )
        if courier is self._courier:
            return
        courier.occupy()
        self._unassign_courier()
        self._courier = courier

    def change_status(self, new_status: OrderStatus) -> None:
        """Переводит заказ в новый статус, если переход допустим.

        Raises:
            InvalidOperationError: если переход недопустим или для него
                не выполнены условия.
        """
        if new_status not in self.available_statuses:
            raise InvalidOperationError(
                f"Нельзя перевести заказ из «{self._status.title}» "
                f"в «{new_status.title}»"
            )
        if new_status is OrderStatus.CONFIRMED and not self._items:
            raise InvalidOperationError("Нельзя подтвердить заказ без позиций")
        if self._needs_courier_for(new_status):
            raise InvalidOperationError("Сначала назначьте курьера")
        self._status = new_status
        if new_status.is_final and self._courier is not None:
            self._courier.release()

    def _needs_courier_for(self, new_status: OrderStatus) -> bool:
        method = self._delivery_method
        return (
            method is not None
            and method.requires_courier
            and new_status is method.transit_status
            and self._courier is None
        )

    def _ensure_editable(self, action: str) -> None:
        if self._status is not OrderStatus.CREATED:
            raise InvalidOperationError(
                f"Нельзя {action}: заказ в статусе «{self._status.title}»"
            )

    def _unassign_courier(self) -> None:
        if self._courier is not None:
            self._courier.release()
            self._courier = None

    def __str__(self) -> str:
        delivery = self._delivery_method.name if self._delivery_method else "не выбрана"
        return (
            f"Заказ #{self._id} [{self._status.title}] — {self._customer}, "
            f"доставка: {delivery}, итого: {self.total_cost} руб."
        )
