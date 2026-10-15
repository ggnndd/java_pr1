import unittest
from datetime import timedelta
from decimal import Decimal

from delivery.models import OrderStatus
from delivery.services import OrderService
from delivery.ui import ConsoleApp, ConsoleIO
from delivery.ui.formatters import format_duration, plural


class ScriptedIO(ConsoleIO):
    """ConsoleIO, который берёт ввод из списка и запоминает вывод."""

    def __init__(self, inputs):
        self.output = []
        lines = iter(inputs)

        def read(prompt):
            try:
                return next(lines)
            except StopIteration:
                raise EOFError from None

        super().__init__(read, self.output.append)

    @property
    def text(self):
        return "\n".join(self.output)


def run_app(inputs, service=None):
    service = service or OrderService()
    io = ScriptedIO(inputs)
    ConsoleApp(service, io).run()
    return service, io


class ConsoleIOTest(unittest.TestCase):

    def test_read_int_repeats_until_valid(self):
        io = ScriptedIO(["abc", "", "-1", "5"])
        self.assertEqual(5, io.read_int("> ", min_value=1))
        self.assertEqual(3, sum("Ошибка" in line for line in io.output))

    def test_read_price_accepts_comma(self):
        io = ScriptedIO(["0", "99,90"])
        self.assertEqual(Decimal("99.90"), io.read_price("> "))

    def test_choose_back(self):
        io = ScriptedIO(["0"])
        self.assertIsNone(io.choose("Выбор:", ["a", "b"]))


class FormattersTest(unittest.TestCase):

    def test_plural(self):
        forms = ("день", "дня", "дней")
        self.assertEqual("день", plural(21, forms))
        self.assertEqual("дня", plural(3, forms))
        self.assertEqual("дней", plural(11, forms))

    def test_format_duration(self):
        self.assertEqual("3 часа", format_duration(timedelta(hours=3)))
        self.assertEqual("2 дня", format_duration(timedelta(days=2)))


class ConsoleAppTest(unittest.TestCase):

    def setUp(self):
        self.service = OrderService()
        self.service.hire_courier("Пётр", "89001112233")

    def test_full_scenario(self):
        run_app(
            [
                "1", "Иван", "89001234567", "ул. Ленина, 1",
                "Пицца", "2", "500", "д",
                "Сок", "1", "120", "н",
                "4", "1", "1",          # стандартная доставка
                "5", "1", "1",          # курьер
                "6", "1", "1",          # подтверждён
                "6", "1", "1",          # в доставке
                "6", "1", "1",          # доставлен
                "0",
            ],
            self.service,
        )
        order = self.service.get_order(1)
        self.assertIs(OrderStatus.DELIVERED, order.status)
        self.assertEqual(Decimal("1420.00"), order.total_cost)
        self.assertTrue(self.service.get_courier(1).is_available)

    def test_errors_do_not_stop_program(self):
        _, io = run_app(
            [
                "42",                                  # нет такого пункта
                "3",                                   # заказов нет
                "1", "Иван", "телефон", "ул. Ленина",  # неверный телефон
                "0",
            ],
            self.service,
        )
        self.assertIn("пункта «42» нет в меню", io.text)
        self.assertIn("Некорректный номер телефона", io.text)
        self.assertEqual([], self.service.list_orders())
        self.assertIn("До свидания", io.output[-1])

    def test_pickup_rejects_courier(self):
        _, io = run_app(
            [
                "1", "Иван", "89001234567", "ул. Ленина, 1",
                "Пицца", "1", "500", "н",
                "4", "1", "3",          # самовывоз
                "5", "1",               # попытка назначить курьера
                "0",
            ],
            self.service,
        )
        self.assertIn("не требует курьера", io.text)

    def test_end_of_input_exits_gracefully(self):
        _, io = run_app(["3"], self.service)
        self.assertIn("До свидания", io.output[-1])


if __name__ == "__main__":
    unittest.main()
