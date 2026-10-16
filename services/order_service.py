"""Сервис управления заказами."""

from __future__ import annotations

from collections.abc import Iterable

from delivery.models import (
    Customer,
    DeliveryMethod,
    ExpressDelivery,
    Order,
    OrderItem,
    OrderStatus,
    PickupDelivery,
    StandardDelivery,
)
from delivery.services.courier_service import CourierService
from delivery.services.errors import NotFoundError
from delivery.services.product_service import ProductService


def default_delivery_methods() -> list[DeliveryMethod]:
    """Способы доставки, доступные по умолчанию."""
    return [
        StandardDelivery(),
        ExpressDelivery(),
        PickupDelivery("ул. Пушкина, 10"),
    ]


class OrderService:
    """Хранит заказы в памяти и выполняет операции над ними.

    Курьеров и товары сервис получает из отдельных сервисов, переданных
    в конструктор. С консолью сервис не взаимодействует: проверки
    выполняют сущности, ошибки передаются вызывающему коду.
    """

    def __init__(
        self,
        courier_service: CourierService,
        product_service: ProductService,
        delivery_methods: Iterable[DeliveryMethod] | None = None,
    ) -> None:
        self._courier_service = courier_service
        self._product_service = product_service
        methods = list(delivery_methods) if delivery_methods is not None else None
        self._delivery_methods = methods or default_delivery_methods()
        self._orders: dict[int, Order] = {}
        self._next_id = 1

    @property
    def delivery_methods(self) -> tuple[DeliveryMethod, ...]:
        """Доступные способы доставки."""
        return tuple(self._delivery_methods)

    def create_order(self, customer_name: str, phone: str, address: str) -> Order:
        """Создаёт новый заказ с уникальным номером."""
        order = Order(self._next_id, Customer(customer_name, phone), address)
        self._orders[order.id] = order
        self._next_id += 1
        return order

    def get_order(self, order_id: int) -> Order:
        """Возвращает заказ по номеру.

        Raises:
            NotFoundError: если заказа с таким номером нет.
        """
        try:
            return self._orders[order_id]
        except KeyError:
            raise NotFoundError(f"Заказ #{order_id} не найден") from None

    def list_orders(self) -> list[Order]:
        """Возвращает все заказы в порядке создания."""
        return list(self._orders.values())

    def add_product(self, order_id: int, product_id: int, quantity: int) -> OrderItem:
        """Резервирует товар со склада и добавляет его в заказ."""
        order = self.get_order(order_id)
        product = self._product_service.get_product(product_id)
        return order.add_product(product, quantity)

    def set_delivery_method(self, order_id: int, method: DeliveryMethod) -> Order:
        """Выбирает для заказа способ доставки из списка доступных."""
        if method not in self._delivery_methods:
            raise NotFoundError(f"Способ доставки «{method}» недоступен")
        order = self.get_order(order_id)
        order.set_delivery_method(method)
        return order

    def assign_courier(self, order_id: int, courier_id: int) -> Order:
        """Назначает курьера на заказ."""
        order = self.get_order(order_id)
        order.assign_courier(self._courier_service.get_courier(courier_id))
        return order

    def change_status(self, order_id: int, new_status: OrderStatus) -> Order:
        """Переводит заказ в новый статус."""
        order = self.get_order(order_id)
        order.change_status(new_status)
        return order
