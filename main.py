"""Точка входа: консольный симулятор службы доставки."""

from delivery.services import CourierService, OrderService, ProductService
from delivery.ui import ConsoleApp, ConsoleIO


def create_courier_service() -> CourierService:
    """Создаёт базу курьеров с начальным штатом."""
    service = CourierService()
    service.hire_courier("Алексей Смирнов", "+79001112233")
    service.hire_courier("Мария Иванова", "+79004445566")
    service.hire_courier("Дмитрий Козлов", "+79007778899")
    return service


def create_product_service() -> ProductService:
    """Создаёт склад с начальным набором товаров."""
    service = ProductService()
    service.add_product("Пицца «Маргарита»", "550.00", 10)
    service.add_product("Бургер классический", "320.00", 15)
    service.add_product("Картофель фри", "150.00", 30)
    service.add_product("Салат «Цезарь»", "390.00", 8)
    service.add_product("Чизкейк", "280.00", 5)
    service.add_product("Морс клюквенный 0,5 л", "120.00", 40)
    return service


def main() -> None:
    couriers = create_courier_service()
    products = create_product_service()
    orders = OrderService(couriers, products)
    ConsoleApp(orders, couriers, products, ConsoleIO()).run()


if __name__ == "__main__":
    main()
