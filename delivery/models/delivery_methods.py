"""Способы доставки заказа."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from delivery.models.order_status import OrderStatus
from delivery.models.validation import require_not_blank

if TYPE_CHECKING:
    from delivery.models.order import Order


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class DeliveryMethod(ABC):
    """Общий контракт способа доставки.

    Каждая реализация сама рассчитывает стоимость и срок, сообщает,
    нужен ли курьер, и определяет промежуточный статус заказа между
    подтверждением и получением клиентом.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Название способа доставки для отображения пользователю."""

    @property
    @abstractmethod
    def requires_courier(self) -> bool:
        """Нужно ли назначать курьера на заказ."""

    @property
    @abstractmethod
    def transit_status(self) -> OrderStatus:
        """Статус заказа после подтверждения и до получения клиентом."""

    @abstractmethod
    def calculate_cost(self, order: Order) -> Decimal:
        """Рассчитывает стоимость доставки заказа."""

    @abstractmethod
    def estimate_time(self, order: Order) -> timedelta:
        """Рассчитывает ориентировочный срок доставки заказа."""

    def next_statuses(self, current: OrderStatus) -> tuple[OrderStatus, ...]:
        """Возвращает статусы, в которые можно перевести заказ из текущего."""
        transitions = {
            OrderStatus.CREATED: (OrderStatus.CONFIRMED, OrderStatus.CANCELLED),
            OrderStatus.CONFIRMED: (self.transit_status, OrderStatus.CANCELLED),
            self.transit_status: (OrderStatus.DELIVERED,),
        }
        return transitions.get(current, ())

    def __str__(self) -> str:
        return self.name


class CourierDelivery(DeliveryMethod, ABC):
    """Базовый класс для способов доставки, выполняемых курьером."""

    @property
    def requires_courier(self) -> bool:
        return True

    @property
    def transit_status(self) -> OrderStatus:
        return OrderStatus.IN_DELIVERY


class StandardDelivery(CourierDelivery):
    """Стандартная доставка курьером.

    Фиксированная стоимость, бесплатно при сумме заказа от порога.
    Крупные заказы доставляются на день дольше.
    """

    BASE_COST = Decimal("300.00")
    FREE_THRESHOLD = Decimal("3000.00")
    BASE_DAYS = 2
    LARGE_ORDER_QUANTITY = 10

    @property
    def name(self) -> str:
        return "Стандартная доставка"

    def calculate_cost(self, order: Order) -> Decimal:
        if order.items_total >= self.FREE_THRESHOLD:
            return Decimal("0.00")
        return self.BASE_COST

    def estimate_time(self, order: Order) -> timedelta:
        days = self.BASE_DAYS
        if order.total_quantity > self.LARGE_ORDER_QUANTITY:
            days += 1
        return timedelta(days=days)


class ExpressDelivery(CourierDelivery):
    """Экспресс-доставка курьером: быстрее и дороже стандартной."""

    BASE_COST = Decimal("500.00")
    ORDER_PERCENT = Decimal("0.10")
    DELIVERY_HOURS = 3

    @property
    def name(self) -> str:
        return "Экспресс-доставка"

    def calculate_cost(self, order: Order) -> Decimal:
        return _money(self.BASE_COST + order.items_total * self.ORDER_PERCENT)

    def estimate_time(self, order: Order) -> timedelta:
        return timedelta(hours=self.DELIVERY_HOURS)


class PickupDelivery(DeliveryMethod):
    """Самовывоз из пункта выдачи: бесплатно и без курьера."""

    PREPARATION_DAYS = 1

    def __init__(self, pickup_point: str) -> None:
        self._pickup_point = require_not_blank(pickup_point, "Адрес пункта выдачи")

    @property
    def pickup_point(self) -> str:
        return self._pickup_point

    @property
    def name(self) -> str:
        return f"Самовывоз ({self._pickup_point})"

    @property
    def requires_courier(self) -> bool:
        return False

    @property
    def transit_status(self) -> OrderStatus:
        return OrderStatus.READY_FOR_PICKUP

    def calculate_cost(self, order: Order) -> Decimal:
        return Decimal("0.00")

    def estimate_time(self, order: Order) -> timedelta:
        return timedelta(days=self.PREPARATION_DAYS)
