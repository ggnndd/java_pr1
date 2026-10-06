"""Заказ службы доставки."""

from decimal import Decimal

from delivery.models.customer import Customer
from delivery.models.order_item import OrderItem
from delivery.models.order_status import OrderStatus
from delivery.models.validation import require_not_blank, require_positive_int


class Order:
    """Заказ: клиент, адрес доставки, позиции и текущий статус.

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
    def items_total(self) -> Decimal:
        """Стоимость всех позиций без учёта доставки."""
        return sum((item.total for item in self._items), Decimal("0.00"))

    def add_item(self, item: OrderItem) -> None:
        """Добавляет позицию в заказ.

        Raises:
            RuntimeError: если заказ уже подтверждён и не может быть изменён.
        """
        if not isinstance(item, OrderItem):
            raise TypeError("Ожидается позиция заказа")
        if self._status is not OrderStatus.CREATED:
            raise RuntimeError(
                f"Нельзя добавить позицию: заказ в статусе «{self._status.title}»"
            )
        self._items.append(item)

    def __str__(self) -> str:
        return (
            f"Заказ #{self._id} [{self._status.title}] — {self._customer}, "
            f"позиций: {len(self._items)}, сумма: {self.items_total} руб."
        )
