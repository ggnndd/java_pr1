import unittest
from decimal import Decimal

from delivery.models import InvalidOperationError, OrderStatus, StandardDelivery
from delivery.services import (
    CourierService,
    NotFoundError,
    OrderService,
    ProductService,
)


class CourierServiceTest(unittest.TestCase):

    def setUp(self):
        self.service = CourierService()

    def test_hire_and_find(self):
        first = self.service.hire_courier("Пётр", "89001112233")
        second = self.service.hire_courier("Ольга", "89004445566")
        self.assertEqual((1, 2), (first.id, second.id))
        self.assertIs(second, self.service.get_courier(2))
        self.assertEqual([first, second], self.service.list_couriers())

    def test_available_couriers(self):
        courier = self.service.hire_courier("Пётр", "89001112233")
        courier.occupy()
        self.assertEqual([], self.service.available_couriers())

    def test_unknown_courier(self):
        with self.assertRaises(NotFoundError):
            self.service.get_courier(42)


class ProductServiceTest(unittest.TestCase):

    def setUp(self):
        self.service = ProductService()
        self.pizza = self.service.add_product("Пицца", "500", 2)
        self.cake = self.service.add_product("Торт", "800", 0)

    def test_available_products_exclude_out_of_stock(self):
        self.assertEqual([self.pizza, self.cake], self.service.list_products())
        self.assertEqual([self.pizza], self.service.available_products())

    def test_restock(self):
        self.service.restock(self.cake.id, 3)
        self.assertEqual(3, self.cake.stock)
        self.assertIn(self.cake, self.service.available_products())

    def test_invalid_product_does_not_take_id(self):
        with self.assertRaises(ValueError):
            self.service.add_product("Сок", "0.001", 5)
        self.assertEqual(3, self.service.add_product("Сок", "100", 5).id)

    def test_unknown_product(self):
        with self.assertRaises(NotFoundError):
            self.service.restock(42, 1)


class OrderServiceTest(unittest.TestCase):

    def setUp(self):
        self.couriers = CourierService()
        self.products = ProductService()
        self.service = OrderService(self.couriers, self.products)
        self.courier = self.couriers.hire_courier("Пётр", "89001112233")
        self.pizza = self.products.add_product("Пицца", "450", 10)
        self.order = self.service.create_order("Иван", "89001234567", "ул. Ленина, 1")

    def test_orders_get_sequential_ids(self):
        second = self.service.create_order("Анна", "89005556677", "ул. Мира, 5")
        self.assertEqual((1, 2), (self.order.id, second.id))
        self.assertEqual([self.order, second], self.service.list_orders())

    def test_invalid_customer_data_does_not_create_order(self):
        with self.assertRaises(ValueError):
            self.service.create_order("", "89001234567", "ул. Ленина, 1")
        self.assertEqual(1, len(self.service.list_orders()))

    def test_add_product_reserves_stock(self):
        self.service.add_product(self.order.id, self.pizza.id, 2)
        self.assertEqual(Decimal("900.00"), self.order.items_total)
        self.assertEqual(8, self.pizza.stock)

    def test_unknown_order_product_and_courier(self):
        with self.assertRaises(NotFoundError):
            self.service.get_order(42)
        with self.assertRaises(NotFoundError):
            self.service.add_product(self.order.id, 42, 1)
        with self.assertRaises(NotFoundError):
            self.service.assign_courier(self.order.id, 42)

    def test_full_scenario(self):
        standard = self.service.delivery_methods[0]
        self.service.add_product(self.order.id, self.pizza.id, 1)
        self.service.set_delivery_method(self.order.id, standard)
        self.service.assign_courier(self.order.id, self.courier.id)
        self.assertEqual([], self.couriers.available_couriers())

        for status in (
            OrderStatus.CONFIRMED,
            OrderStatus.IN_DELIVERY,
            OrderStatus.DELIVERED,
        ):
            self.service.change_status(self.order.id, status)

        self.assertIs(OrderStatus.DELIVERED, self.order.status)
        self.assertEqual([self.courier], self.couriers.available_couriers())
        self.assertEqual(9, self.pizza.stock)

    def test_cancel_returns_stock(self):
        self.service.add_product(self.order.id, self.pizza.id, 4)
        self.service.change_status(self.order.id, OrderStatus.CANCELLED)
        self.assertEqual(10, self.pizza.stock)

    def test_unknown_delivery_method_is_rejected(self):
        with self.assertRaises(NotFoundError):
            self.service.set_delivery_method(self.order.id, StandardDelivery())

    def test_domain_errors_are_propagated(self):
        with self.assertRaises(InvalidOperationError):
            self.service.change_status(self.order.id, OrderStatus.DELIVERED)


if __name__ == "__main__":
    unittest.main()
