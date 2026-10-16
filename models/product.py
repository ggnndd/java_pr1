"""Товар на складе."""

from decimal import Decimal

from delivery.models.errors import InvalidOperationError
from delivery.models.validation import (
    require_non_negative_int,
    require_not_blank,
    require_positive_int,
    require_positive_money,
)


class Product:
    """Товар с ценой и доступным на складе количеством.

    Количество меняется только через методы: резервирование под заказ,
    возврат резерва при отмене заказа и пополнение склада.
    """

    def __init__(self, product_id: int, name: str, price, stock: int = 0) -> None:
        self._id = require_positive_int(product_id, "Идентификатор товара")
        self._name = self.validate_name(name)
        self._price = self.validate_price(price)
        self._stock = require_non_negative_int(stock, "Количество на складе")

    @staticmethod
    def validate_name(name: str) -> str:
        """Проверяет название товара."""
        return require_not_blank(name, "Название товара")

    @staticmethod
    def validate_price(price) -> Decimal:
        """Проверяет цену: больше нуля, не более двух знаков после запятой."""
        return require_positive_money(price, "Цена")

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def price(self) -> Decimal:
        return self._price

    @property
    def stock(self) -> int:
        """Количество, доступное для заказа."""
        return self._stock

    @property
    def in_stock(self) -> bool:
        return self._stock > 0

    def reserve(self, quantity: int) -> None:
        """Резервирует товар под заказ, уменьшая доступное количество.

        Raises:
            ValueError: если количество не является положительным числом.
            InvalidOperationError: если товара на складе недостаточно.
        """
        require_positive_int(quantity, "Количество")
        if quantity > self._stock:
            raise InvalidOperationError(
                f"Недостаточно товара «{self._name}»: "
                f"запрошено {quantity}, доступно {self._stock}"
            )
        self._stock -= quantity

    def release(self, quantity: int) -> None:
        """Возвращает зарезервированный товар на склад (при отмене заказа)."""
        self._stock += require_positive_int(quantity, "Количество")

    def restock(self, quantity: int) -> None:
        """Пополняет склад новой поставкой."""
        self._stock += require_positive_int(quantity, "Количество")

    def __str__(self) -> str:
        return f"#{self._id} {self._name} — {self._price} руб., в наличии: {self._stock} шт."
