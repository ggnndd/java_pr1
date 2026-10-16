"""Представление сущностей в виде текста для вывода в консоль."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from delivery.models import Courier, DeliveryMethod, Order, Product


def plural(number: int, forms: tuple[str, str, str]) -> str:
    """Выбирает форму слова для числа: (1 день, 2 дня, 5 дней)."""
    number = abs(number)
    if number % 10 == 1 and number % 100 != 11:
        return forms[0]
    if 2 <= number % 10 <= 4 and not 12 <= number % 100 <= 14:
        return forms[1]
    return forms[2]


def format_money(amount: Decimal) -> str:
    return f"{amount:.2f} руб."


def format_duration(duration: timedelta) -> str:
    """Форматирует срок в часах, если он меньше суток, иначе в днях."""
    hours = int(duration.total_seconds() // 3600)
    if hours < 24:
        return f"{hours} {plural(hours, ('час', 'часа', 'часов'))}"
    days = duration.days
    return f"{days} {plural(days, ('день', 'дня', 'дней'))}"


def format_delivery_option(method: DeliveryMethod, order: Order) -> str:
    """Способ доставки с рассчитанными для заказа стоимостью и сроком."""
    return (
        f"{method.name} — {format_money(method.calculate_cost(order))}, "
        f"срок: {format_duration(method.estimate_time(order))}"
    )


def format_courier(courier: Courier) -> str:
    return str(courier)


def format_product(product: Product) -> str:
    return f"{product.name} — {format_money(product.price)}, в наличии: {product.stock} шт."


def format_order_line(order: Order) -> str:
    """Краткая строка для списка заказов."""
    return str(order)


def _courier_info(order: Order) -> str:
    method = order.delivery_method
    if method is None:
        return "—"
    if not method.requires_courier:
        return "не требуется"
    return str(order.courier) if order.courier else "не назначен"


def format_order_details(order: Order) -> str:
    """Подробная информация о заказе."""
    lines = [
        f"Заказ #{order.id} — {order.status.title}",
        f"  Клиент:  {order.customer}",
        f"  Адрес:   {order.address}",
        "  Позиции:",
    ]
    if order.items:
        lines += [f"    {n}. {item}" for n, item in enumerate(order.items, start=1)]
    else:
        lines.append("    (пусто)")
    lines.append(f"  Сумма товаров: {format_money(order.items_total)}")

    method = order.delivery_method
    if method is None:
        lines.append("  Доставка: не выбрана")
    else:
        lines.append(f"  Доставка: {format_delivery_option(method, order)}")
    lines.append(f"  Курьер:  {_courier_info(order)}")
    lines.append(f"  Итого:   {format_money(order.total_cost)}")

    next_statuses = ", ".join(status.title for status in order.available_statuses)
    lines.append(f"  Следующие статусы: {next_statuses or 'нет'}")
    return "\n".join(lines)
