"""Клиент службы доставки."""

from delivery.models.person import Person


class Customer(Person):
    """Клиент, оформляющий заказ."""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Customer):
            return NotImplemented
        return self.name == other.name and self.phone == other.phone

    def __hash__(self) -> int:
        return hash((self.name, self.phone))
