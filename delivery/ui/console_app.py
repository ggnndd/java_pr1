"""Консольное меню службы доставки."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from delivery.models import InvalidOperationError, Order
from delivery.services import NotFoundError, OrderService
from delivery.ui import formatters as fmt
from delivery.ui.console_io import ConsoleIO


@dataclass(frozen=True)
class MenuCommand:
    """Пункт меню: название и действие."""

    title: str
    action: Callable[[], None]


class ConsoleApp:
    """Связывает пользовательский ввод с операциями сервиса заказов.

    Бизнес-правила здесь не реализуются: меню собирает данные,
    вызывает сервис и показывает результат или сообщение об ошибке.
    """

    def __init__(self, service: OrderService, io: ConsoleIO) -> None:
        self._service = service
        self._io = io
        self._running = False
        self._commands = {
            "1": MenuCommand("Создать заказ", self._create_order),
            "2": MenuCommand("Добавить позиции в заказ", self._add_items),
            "3": MenuCommand("Список заказов", self._list_orders),
            "4": MenuCommand("Выбрать способ доставки", self._choose_delivery),
            "5": MenuCommand("Назначить курьера", self._assign_courier),
            "6": MenuCommand("Изменить статус заказа", self._change_status),
            "7": MenuCommand("Информация о заказе", self._show_order),
            "8": MenuCommand("Список курьеров", self._list_couriers),
            "9": MenuCommand("Добавить курьера", self._hire_courier),
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
            self._io.show(f"{key}. {command.title}")

    def _handle(self, choice: str) -> None:
        command = self._commands.get(choice)
        if command is None:
            self._io.error(f"пункта «{choice}» нет в меню")
            return
        try:
            command.action()
        except (ValueError, InvalidOperationError, NotFoundError) as error:
            self._io.error(str(error))

    def _select_order(self) -> Order | None:
        orders = self._service.list_orders()
        if not orders:
            self._io.show("Заказов пока нет. Создайте заказ (пункт 1).")
            return None
        return self._io.choose("Выберите заказ:", orders, fmt.format_order_line)

    def _create_order(self) -> None:
        name = self._io.read_text("Имя клиента: ")
        phone = self._io.read_text("Телефон клиента: ")
        address = self._io.read_text("Адрес доставки: ")
        order = self._service.create_order(name, phone, address)
        self._io.success(f"Создан заказ #{order.id}")
        self._read_items(order)
        self._io.show(fmt.format_order_details(order))

    def _add_items(self) -> None:
        order = self._select_order()
        if order is None:
            return
        if not order.is_editable:
            self._io.error(f"заказ в статусе «{order.status.title}» нельзя изменить")
            return
        self._read_items(order)
        self._io.show(fmt.format_order_details(order))

    def _read_items(self, order: Order) -> None:
        """Добавляет в заказ одну или несколько позиций."""
        while True:
            name = self._io.read_text("Название товара: ")
            quantity = self._io.read_int("Количество: ", min_value=1)
            price = self._io.read_price("Цена за единицу: ")
            item = self._service.add_item(order.id, name, quantity, price)
            self._io.success(f"Добавлено: {item}")
            if not self._io.confirm("Добавить ещё позицию?"):
                return

    def _list_orders(self) -> None:
        orders = self._service.list_orders()
        if not orders:
            self._io.show("Заказов пока нет.")
            return
        for order in orders:
            self._io.show(fmt.format_order_line(order))

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
            self._service.delivery_methods,
            lambda m: fmt.format_delivery_option(m, order),
        )
        if method is None:
            return
        self._service.set_delivery_method(order.id, method)
        self._io.success(f"Выбрано: {fmt.format_delivery_option(method, order)}")
        self._io.show(f"Итого к оплате: {fmt.format_money(order.total_cost)}")

    def _assign_courier(self) -> None:
        order = self._select_order()
        if order is None:
            return
        order.validate_courier_assignment()
        couriers = self._service.available_couriers()
        if not couriers:
            self._io.error("нет свободных курьеров")
            return
        courier = self._io.choose("Свободные курьеры:", couriers, fmt.format_courier)
        if courier is None:
            return
        self._service.assign_courier(order.id, courier.id)
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
        self._service.change_status(order.id, status)
        self._io.success(f"Статус изменён на «{status.title}»")
        self._io.show(fmt.format_order_details(order))

    def _show_order(self) -> None:
        order = self._select_order()
        if order is not None:
            self._io.show(fmt.format_order_details(order))

    def _list_couriers(self) -> None:
        couriers = self._service.list_couriers()
        if not couriers:
            self._io.show("Курьеров пока нет.")
            return
        for courier in couriers:
            self._io.show(fmt.format_courier(courier))

    def _hire_courier(self) -> None:
        name = self._io.read_text("Имя курьера: ")
        phone = self._io.read_text("Телефон курьера: ")
        courier = self._service.hire_courier(name, phone)
        self._io.success(f"Добавлен курьер {fmt.format_courier(courier)}")

    def _exit(self) -> None:
        self._running = False
        self._io.show("Работа завершена. До свидания!")
