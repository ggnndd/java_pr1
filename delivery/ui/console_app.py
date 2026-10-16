"""Консольное меню службы доставки."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from delivery.models import (
    Courier,
    Customer,
    InvalidOperationError,
    Order,
    OrderStatus,
    Product,
)
from delivery.services import (
    CourierService,
    NotFoundError,
    OrderService,
    ProductService,
)
from delivery.ui import formatters as fmt
from delivery.ui.console_io import ConsoleIO


@dataclass(frozen=True)
class MenuCommand:
    """Пункт меню: название и действие."""

    title: str
    action: Callable[[], None]


class ConsoleApp:
    """Связывает пользовательский ввод с операциями сервисов.

    Бизнес-правила здесь не реализуются: меню собирает данные,
    вызывает сервисы и показывает результат или сообщение об ошибке.
    """

    def __init__(
        self,
        order_service: OrderService,
        courier_service: CourierService,
        product_service: ProductService,
        io: ConsoleIO,
    ) -> None:
        self._orders = order_service
        self._couriers = courier_service
        self._products = product_service
        self._io = io
        self._running = False
        self._commands = {
            "1": MenuCommand("Создать заказ", self._create_order),
            "2": MenuCommand("Добавить товары в заказ", self._add_products),
            "3": MenuCommand("Список заказов", self._list_orders),
            "4": MenuCommand("Информация о заказе", self._show_order),
            "5": MenuCommand("Выбрать способ доставки", self._choose_delivery),
            "6": MenuCommand("Назначить курьера", self._assign_courier),
            "7": MenuCommand("Изменить статус заказа", self._change_status),
            "8": MenuCommand("Товары на складе", self._list_products),
            "9": MenuCommand("Добавить товар на склад", self._add_stock_product),
            "10": MenuCommand("Пополнить запас товара", self._restock_product),
            "11": MenuCommand("Список курьеров", self._list_couriers),
            "12": MenuCommand("Добавить курьера", self._hire_courier),
            "0": MenuCommand("Выход", self._exit),
        }

    def run(self) -> None:
        """Запускает главный цикл меню до команды выхода."""
        self._running = True
        self._io.show("=== Служба доставки ===")
        while self._running:
            self._show_menu()
            try:
                self._handle(self._io.read_text("Выберите пункт меню: "))
            except (EOFError, KeyboardInterrupt):
                self._io.show()
                self._exit()

    def _show_menu(self) -> None:
        self._io.show()
        for key, command in self._commands.items():
            self._io.show(f"{key:>2}. {command.title}")

    def _handle(self, choice: str) -> None:
        command = self._commands.get(choice)
        if command is None:
            self._io.error(f"пункта «{choice}» нет в меню")
            return
        try:
            command.action()
        except (ValueError, InvalidOperationError, NotFoundError) as error:
            self._io.error(str(error))

    # --- Заказы ---

    def _select_order(self) -> Order | None:
        orders = self._orders.list_orders()
        if not orders:
            self._io.show("Заказов пока нет. Создайте заказ (пункт 1).")
            return None
        return self._io.choose("Выберите заказ:", orders, fmt.format_order_line)

    def _create_order(self) -> None:
        if not self._products.available_products():
            self._io.error("на складе нет товаров — сначала добавьте товар (пункт 9)")
            return
        name = self._io.read_valid("Имя клиента: ", Customer.validate_name)
        phone = self._io.read_valid("Телефон клиента: ", Customer.validate_phone)
        address = self._io.read_valid("Адрес доставки: ", Order.validate_address)
        order = self._orders.create_order(name, phone, address)
        self._io.success(f"Создан заказ #{order.id}")
        self._select_products(order)
        self._io.show(fmt.format_order_details(order))

    def _add_products(self) -> None:
        order = self._select_order()
        if order is None:
            return
        if not order.is_editable:
            self._io.error(f"заказ в статусе «{order.status.title}» нельзя изменить")
            return
        self._select_products(order)
        self._io.show(fmt.format_order_details(order))

    def _select_products(self, order: Order) -> None:
        """Предлагает выбирать товары со склада, пока пользователь не закончит."""
        while True:
            products = self._products.available_products()
            if not products:
                self._io.show("Товары на складе закончились.")
                break
            product = self._io.choose(
                "Товары на складе:",
                products,
                fmt.format_product,
                back_label="Завершить выбор",
            )
            if product is None:
                break
            quantity = self._io.read_int(
                f"Количество (доступно {product.stock}): ",
                min_value=1,
                max_value=product.stock,
            )
            item = self._orders.add_product(order.id, product.id, quantity)
            self._io.success(f"В заказе: {item}")
            if not self._io.confirm("Добавить ещё товар?"):
                break
        if not order.items:
            self._io.show("Заказ пока пуст — добавьте товары через пункт 2.")

    def _list_orders(self) -> None:
        orders = self._orders.list_orders()
        if not orders:
            self._io.show("Заказов пока нет.")
            return
        for order in orders:
            self._io.show(fmt.format_order_line(order))

    def _show_order(self) -> None:
        order = self._select_order()
        if order is not None:
            self._io.show(fmt.format_order_details(order))

    def _choose_delivery(self) -> None:
        order = self._select_order()
        if order is None:
            return
        if not order.is_editable:
            self._io.error(
                f"способ доставки нельзя изменить в статусе «{order.status.title}»"
            )
            return
        method = self._io.choose(
            "Способы доставки:",
            self._orders.delivery_methods,
            lambda m: fmt.format_delivery_option(m, order),
        )
        if method is None:
            return
        self._orders.set_delivery_method(order.id, method)
        self._io.success(f"Выбрано: {fmt.format_delivery_option(method, order)}")
        self._io.show(f"Итого к оплате: {fmt.format_money(order.total_cost)}")

    def _assign_courier(self) -> None:
        order = self._select_order()
        if order is None:
            return
        order.validate_courier_assignment()
        couriers = self._couriers.available_couriers()
        if not couriers:
            self._io.error("нет свободных курьеров")
            return
        courier = self._io.choose("Свободные курьеры:", couriers, fmt.format_courier)
        if courier is None:
            return
        self._orders.assign_courier(order.id, courier.id)
        self._io.success(f"Курьер {courier.name} назначен на заказ #{order.id}")

    def _change_status(self) -> None:
        order = self._select_order()
        if order is None:
            return
        statuses = order.available_statuses
        if not statuses:
            self._io.error(
                f"заказ в статусе «{order.status.title}» больше нельзя изменить"
            )
            return
        status = self._io.choose(
            f"Текущий статус: {order.status.title}. Новый статус:",
            statuses,
            lambda s: s.title,
        )
        if status is None:
            return
        self._orders.change_status(order.id, status)
        self._io.success(f"Статус изменён на «{status.title}»")
        if status is OrderStatus.CANCELLED and order.items:
            self._io.show("Товары из заказа возвращены на склад.")
        self._io.show(fmt.format_order_details(order))

    # --- Склад ---

    def _list_products(self) -> None:
        products = self._products.list_products()
        if not products:
            self._io.show("Склад пуст.")
            return
        for product in products:
            self._io.show(fmt.format_product(product))

    def _add_stock_product(self) -> None:
        name = self._io.read_valid("Название товара: ", Product.validate_name)
        price = self._io.read_valid("Цена за единицу: ", Product.validate_price)
        stock = self._io.read_int("Количество на складе: ", min_value=0)
        product = self._products.add_product(name, price, stock)
        self._io.success(f"Добавлен товар {fmt.format_product(product)}")

    def _restock_product(self) -> None:
        products = self._products.list_products()
        if not products:
            self._io.show("Склад пуст. Добавьте товар (пункт 9).")
            return
        product = self._io.choose("Товары на складе:", products, fmt.format_product)
        if product is None:
            return
        quantity = self._io.read_int("Сколько добавить: ", min_value=1)
        self._products.restock(product.id, quantity)
        self._io.success(f"Запас пополнен: {fmt.format_product(product)}")

    # --- Курьеры ---

    def _list_couriers(self) -> None:
        couriers = self._couriers.list_couriers()
        if not couriers:
            self._io.show("Курьеров пока нет.")
            return
        for courier in couriers:
            self._io.show(fmt.format_courier(courier))

    def _hire_courier(self) -> None:
        name = self._io.read_valid("Имя курьера: ", Courier.validate_name)
        phone = self._io.read_valid("Телефон курьера: ", Courier.validate_phone)
        courier = self._couriers.hire_courier(name, phone)
        self._io.success(f"Добавлен курьер {fmt.format_courier(courier)}")

    def _exit(self) -> None:
        self._running = False
        self._io.show("Работа завершена. До свидания!")
