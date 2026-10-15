"""Сервис управления заказами и курьерами."""

from __future__ import annotations

from collections.abc import Iterable

from delivery.models import (
    Courier,
    Customer,
    DeliveryMethod,
    ExpressDelivery,
    Order,
    OrderItem,
    OrderStatus,
    PickupDelivery,
    StandardDelivery,
)


class NotFoundError(LookupError):
    """Запрошенный объект не найден."""


def default_delivery_methods() -> list[DeliveryMethod]:
    """Способы доставки, доступные по умолчанию."""
    return [
        StandardDelivery(),
        ExpressDelivery(),
        PickupDelivery("ул. Пушкина, 10"),
    ]


class OrderService:
    """Хранит заказы и курьеров в памяти и выполняет операции над ними.

    Сервис не взаимодействует с консолью: он принимает данные,
    делегирует проверки сущностям и возвращает результат либо
    выбрасывает исключение.
    """

    def __init__(self, delivery_methods: Iterable[DeliveryMethod] | None = None) -> None:
        methods = list(delivery_methods) if delivery_methods is not None else None
        self._delivery_methods = methods or default_delivery_methods()
        self._orders: dict[int, Order] = {}
        self._couriers: dict[int, Courier] = {}
        self._next_order_id = 1
        self._next_courier_id = 1

    @property
    def delivery_methods(self) -> tuple[DeliveryMethod, ...]:
        """Доступные способы доставки."""
        return tuple(self._delivery_methods)

    def create_order(self, customer_name: str, phone: str, address: str) -> Order:
        """Создаёт новый заказ с уникальным номером."""
        order = Order(self._next_order_id, Customer(customer_name, phone), address)
        self._orders[order.id] = order
        self._next_order_id += 1
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

    def add_item(
        self, order_id: int, product_name: str, quantity: int, price
    ) -> OrderItem:
        """Добавляет позицию в заказ и возвращает её."""
        order = self.get_order(order_id)
        item = OrderItem(product_name, quantity, price)
        order.add_item(item)
        return item

    def set_delivery_method(self, order_id: int, method: DeliveryMethod) -> Order:
        """Выбирает для заказа способ доставки из списка доступных."""
        if method not in self._delivery_methods:
            raise NotFoundError(f"Способ доставки «{method}» недоступен")
        order = self.get_order(order_id)
        order.set_delivery_method(method)
        return order

    def hire_courier(self, name: str, phone: str) -> Courier:
        """Добавляет нового курьера в штат."""
        courier = Courier(self._next_courier_id, name, phone)
        self._couriers[courier.id] = courier
        self._next_courier_id += 1
        return courier

    def get_courier(self, courier_id: int) -> Courier:
        """Возвращает курьера по идентификатору.

        Raises:
            NotFoundError: если курьера с таким идентификатором нет.
        """
        try:
            return self._couriers[courier_id]
        except KeyError:
            raise NotFoundError(f"Курьер #{courier_id} не найден") from None

    def list_couriers(self) -> list[Courier]:
        """Возвращает всех курьеров."""
        return list(self._couriers.values())

    def available_couriers(self) -> list[Courier]:
        """Возвращает свободных курьеров."""
        return [courier for courier in self._couriers.values() if courier.is_available]

    def assign_courier(self, order_id: int, courier_id: int) -> Order:
        """Назначает курьера на заказ."""
        order = self.get_order(order_id)
        order.assign_courier(self.get_courier(courier_id))
        return order

    def change_status(self, order_id: int, new_status: OrderStatus) -> Order:
        """Переводит заказ в новый статус."""
        order = self.get_order(order_id)
        order.change_status(new_status)
        return order
