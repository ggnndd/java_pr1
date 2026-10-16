"""Сервис управления курьерами."""

from delivery.models import Courier
from delivery.services.errors import NotFoundError


class CourierService:
    """Хранит курьеров в памяти и выдаёт им идентификаторы."""

    def __init__(self) -> None:
        self._couriers: dict[int, Courier] = {}
        self._next_id = 1

    def hire_courier(self, name: str, phone: str) -> Courier:
        """Добавляет нового курьера в штат."""
        courier = Courier(self._next_id, name, phone)
        self._couriers[courier.id] = courier
        self._next_id += 1
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
