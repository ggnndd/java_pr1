"""Позиция заказа."""

from decimal import Decimal

from delivery.models.product import Product
from delivery.models.validation import require_positive_int


class OrderItem:
    """Позиция заказа: товар со склада, количество и цена за единицу.

    Цена фиксируется в момент создания позиции. Объект неизменяемый.
    """

    def __init__(self, product: Product, quantity: int) -> None:
        if not isinstance(product, Product):
            raise TypeError("Позиция заказа должна ссылаться на товар")
        self._product = product
        self._quantity = require_positive_int(quantity, "Количество")
        self._price = product.price

    @property
    def product(self) -> Product:
        return self._product

    @property
    def product_name(self) -> str:
        return self._product.name

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
            f"{self.product_name} × {self._quantity} "
            f"по {self._price} = {self.total} руб."
        )
