import unittest
from decimal import Decimal

from delivery.models import (
    Courier,
    Customer,
    InvalidOperationError,
    Order,
    OrderItem,
    OrderStatus,
)


class CustomerTest(unittest.TestCase):

    def test_phone_is_normalized(self):
        customer = Customer("Иван", "+7 (900) 123-45-67")
        self.assertEqual("+79001234567", customer.phone)

    def test_blank_name_is_rejected(self):
        with self.assertRaises(ValueError):
            Customer("   ", "89001234567")

    def test_invalid_phone_is_rejected(self):
        with self.assertRaises(ValueError):
            Customer("Иван", "abc")


class CourierTest(unittest.TestCase):

    def test_courier_cannot_be_occupied_twice(self):
        courier = Courier(1, "Пётр", "89001112233")
        courier.occupy()
        with self.assertRaises(InvalidOperationError):
            courier.occupy()
        courier.release()
        self.assertTrue(courier.is_available)


class OrderItemTest(unittest.TestCase):

    def test_total(self):
        item = OrderItem("Пицца", 2, "499.90")
        self.assertEqual(Decimal("999.80"), item.total)

    def test_invalid_quantity_and_price(self):
        with self.assertRaises(ValueError):
            OrderItem("Пицца", 0, 100)
        with self.assertRaises(ValueError):
            OrderItem("Пицца", 1, -5)
        with self.assertRaises(ValueError):
            OrderItem("Пицца", 1, "дорого")


class OrderTest(unittest.TestCase):

    def setUp(self):
        self.order = Order(1, Customer("Иван", "89001234567"), "ул. Ленина, 1")

    def test_new_order_is_created_and_empty(self):
        self.assertIs(OrderStatus.CREATED, self.order.status)
        self.assertEqual(Decimal("0.00"), self.order.items_total)

    def test_add_items(self):
        self.order.add_item(OrderItem("Пицца", 2, 500))
        self.order.add_item(OrderItem("Сок", 1, "120.50"))
        self.assertEqual(2, len(self.order.items))
        self.assertEqual(Decimal("1120.50"), self.order.items_total)

    def test_items_cannot_be_modified_from_outside(self):
        self.assertIsInstance(self.order.items, tuple)


if __name__ == "__main__":
    unittest.main()
