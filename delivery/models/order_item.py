"""Позиция заказа."""

from decimal import Decimal

from delivery.models.validation import (
    require_not_blank,
    require_positive_int,
    require_positive_money,
)


class OrderItem:
    """Позиция заказа: товар, количество и цена за единицу.

    Объект неизменяемый: после создания позицию нельзя отредактировать.
    """

    def __init__(self, product_name: str, quantity: int, price) -> None:
        self._product_name = require_not_blank(product_name, "Название товара")
        self._quantity = require_positive_int(quantity, "Количество")
        self._price = require_positive_money(price, "Цена")

    @property
    def product_name(self) -> str:
        return self._product_name

    @property
    def quantity(self) -> int:
        return self._quantity

    @property
    def price(self) -> Decimal:
        return self._price

    @property
    def total(self) -> Decimal:
        """Стоимость позиции с учётом количества."""
        return self._price * self._quantity

    def __str__(self) -> str:
        return (
            f"{self._product_name} × {self._quantity} "
            f"по {self._price} = {self.total} руб."
        )
