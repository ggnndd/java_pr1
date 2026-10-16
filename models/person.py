"""Базовый класс участника доставки."""

from delivery.models.validation import require_not_blank, require_phone


class Person:
    """Человек с именем и телефоном: общая часть клиента и курьера.

    Проверки полей доступны как статические методы, чтобы интерфейс
    мог проверять каждое поле сразу после ввода.
    """

    def __init__(self, name: str, phone: str) -> None:
        self._name = self.validate_name(name)
        self._phone = self.validate_phone(phone)

    @staticmethod
    def validate_name(name: str) -> str:
        """Проверяет имя и возвращает его без крайних пробелов."""
        return require_not_blank(name, "Имя")

    @staticmethod
    def validate_phone(phone: str) -> str:
        """Проверяет телефон и возвращает его в нормализованном виде."""
        return require_phone(phone)

    @property
    def name(self) -> str:
        return self._name

    @property
    def phone(self) -> str:
        return self._phone

    def __str__(self) -> str:
        return f"{self._name} ({self._phone})"
