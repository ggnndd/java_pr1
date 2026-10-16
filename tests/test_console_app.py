import unittest
from datetime import timedelta
from decimal import Decimal

from delivery.models import Customer, OrderStatus
from delivery.services import CourierService, OrderService, ProductService
from delivery.ui import ConsoleApp, ConsoleIO
from delivery.ui.formatters import format_duration, plural


class ScriptedIO(ConsoleIO):
    """ConsoleIO, который берёт ввод из списка и запоминает вывод и вопросы."""

    def __init__(self, inputs):
        self.output = []
        self.prompts = []
        lines = iter(inputs)

        def read(prompt):
            self.prompts.append(prompt)
            try:
                return next(lines)
            except StopIteration:
                raise EOFError from None

        super().__init__(read, self.output.append)

    @property
    def text(self):
        return "\n".join(self.output)


class ConsoleIOTest(unittest.TestCase):

    def test_read_int_repeats_until_valid(self):
        io = ScriptedIO(["abc", "", "-1", "5"])
        self.assertEqual(5, io.read_int("> ", min_value=1))
        self.assertEqual(3, sum("Ошибка" in line for line in io.output))

    def test_read_valid_repeats_only_this_field(self):
        io = ScriptedIO(["abc", "8 900 123-45-67"])
        self.assertEqual("89001234567", io.read_valid("> ", Customer.validate_phone))
        self.assertEqual(2, len(io.prompts))
        self.assertIn("Некорректный номер телефона", io.text)

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
        self.couriers = CourierService()
        self.products = ProductService()
        self.orders = OrderService(self.couriers, self.products)
        self.couriers.hire_courier("Пётр", "89001112233")
        self.pizza = self.products.add_product("Пицца", "500", 10)
        self.juice = self.products.add_product("Сок", "120", 5)

    def run_app(self, inputs):
        io = ScriptedIO(inputs)
        ConsoleApp(self.orders, self.couriers, self.products, io).run()
        return io

    def create_order_inputs(self, quantity="2"):
        return ["1", "Иван", "89001234567", "ул. Ленина, 1", "1", quantity, "н"]

    def test_full_scenario(self):
        io = self.run_app(
            [
                "1", "Иван", "телефон", "89001234567", "ул. Ленина, 1",
                "1", "20", "2", "д",    # пицца: 20 больше остатка, затем 2
                "2", "1", "н",          # сок
                "5", "1", "1",          # стандартная доставка
                "6", "1", "1",          # курьер
                "7", "1", "1",          # подтверждён
                "7", "1", "1",          # в доставке
                "7", "1", "1",          # доставлен
                "0",
            ]
        )
        order = self.orders.get_order(1)
        self.assertIs(OrderStatus.DELIVERED, order.status)
        self.assertEqual(Decimal("1420.00"), order.total_cost)
        self.assertEqual(8, self.pizza.stock)
        self.assertEqual(4, self.juice.stock)
        self.assertTrue(self.couriers.get_courier(1).is_available)
        # при ошибке в телефоне имя повторно не запрашивается
        self.assertEqual(1, io.prompts.count("Имя клиента: "))
        self.assertEqual(2, io.prompts.count("Телефон клиента: "))

    def test_cancel_returns_products_to_stock(self):
        io = self.run_app(self.create_order_inputs("3") + ["7", "1", "1", "0"])
        self.assertIs(OrderStatus.CANCELLED, self.orders.get_order(1).status)
        self.assertEqual(10, self.pizza.stock)
        self.assertIn("возвращены на склад", io.text)

    def test_out_of_stock_products_are_hidden(self):
        self.run_app(self.create_order_inputs("10") + self.create_order_inputs("1"))
        # во втором заказе пицца закончилась, первым в списке стоит сок
        self.assertEqual(0, self.pizza.stock)
        self.assertEqual(4, self.juice.stock)
        self.assertEqual("Сок", self.orders.get_order(2).items[0].product_name)

    def test_cannot_create_order_with_empty_stock(self):
        self.products = ProductService()
        self.orders = OrderService(self.couriers, self.products)
        io = self.run_app(["1", "0"])
        self.assertIn("на складе нет товаров", io.text)
        self.assertEqual([], self.orders.list_orders())

    def test_add_stock_product_with_price_validation(self):
        io = self.run_app(["9", "Морс", "0.001", "99,9", "5", "0"])
        product = self.products.get_product(3)
        self.assertEqual(Decimal("99.90"), product.price)
        self.assertEqual(5, product.stock)
        self.assertIn("не более двух знаков", io.text)

    def test_restock_product(self):
        self.run_app(["10", "2", "7", "0"])
        self.assertEqual(12, self.juice.stock)

    def test_errors_do_not_stop_program(self):
        io = self.run_app(["42", "3", "0"])
        self.assertIn("пункта «42» нет в меню", io.text)
        self.assertIn("Заказов пока нет", io.text)
        self.assertIn("До свидания", io.output[-1])

    def test_pickup_rejects_courier(self):
        io = self.run_app(self.create_order_inputs() + ["5", "1", "3", "6", "1", "0"])
        self.assertIn("не требует курьера", io.text)

    def test_end_of_input_exits_gracefully(self):
        io = self.run_app(["3"])
        self.assertIn("До свидания", io.output[-1])


if __name__ == "__main__":
    unittest.main()
