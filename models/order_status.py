"""Статусы заказа."""

from enum import Enum


class OrderStatus(Enum):
    """Возможные статусы заказа."""

    CREATED = "Создан"
    CONFIRMED = "Подтверждён"
    IN_DELIVERY = "В доставке"
    READY_FOR_PICKUP = "Готов к выдаче"
    DELIVERED = "Доставлен"
    CANCELLED = "Отменён"

    @property
    def title(self) -> str:
        """Название статуса для отображения пользователю."""
        return self.value

    @property
    def is_final(self) -> bool:
        """Завершён ли жизненный цикл заказа."""
        return self in (OrderStatus.DELIVERED, OrderStatus.CANCELLED)
