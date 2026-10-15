"""Точка входа: консольный симулятор службы доставки."""

from delivery.services import OrderService
from delivery.ui import ConsoleApp, ConsoleIO


def create_service() -> OrderService:
    """Создаёт сервис с несколькими курьерами для начала работы."""
    service = OrderService()
    service.hire_courier("Алексей Смирнов", "+79001112233")
    service.hire_courier("Мария Иванова", "+79004445566")
    service.hire_courier("Дмитрий Козлов", "+79007778899")
    return service


def main() -> None:
    ConsoleApp(create_service(), ConsoleIO()).run()


if __name__ == "__main__":
    main()
