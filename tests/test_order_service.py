import unittest
from decimal import Decimal

from delivery.models import InvalidOperationError, OrderStatus, StandardDelivery
from delivery.services import NotFoundError, OrderService


class OrderServiceTest(unittest.TestCase):

    def setUp(self):
        self.service = OrderService()
        self.order = self.service.create_order("Иван", "89001234567", "ул. Ленина, 1")
        self.courier = self.service.hire_courier("Пётр", "89001112233")

    def test_orders_get_sequential_ids(self):
        second = self.service.create_order("Анна", "89005556677", "ул. Мира, 5")
        self.assertEqual(1, self.order.id)
        self.assertEqual(2, second.id)
        self.assertEqual([self.order, second], self.service.list_orders())

    def test_invalid_customer_data_does_not_create_order(self):
        with self.assertRaises(ValueError):
            self.service.create_order("", "89001234567", "ул. Ленина, 1")
        self.assertEqual(1, len(self.service.list_orders()))

    def test_unknown_order_and_courier(self):
        with self.assertRaises(NotFoundError):
            self.service.get_order(42)
        with self.assertRaises(NotFoundError):
            self.service.assign_courier(self.order.id, 42)

    def test_add_item(self):
        self.service.add_item(self.order.id, "Пицца", 2, "450")
        self.assertEqual(Decimal("900.00"), self.order.items_total)

    def test_full_scenario(self):
        standard = self.service.delivery_methods[0]
        self.service.add_item(self.order.id, "Пицца", 1, 500)
        self.service.set_delivery_method(self.order.id, standard)
        self.service.assign_courier(self.order.id, self.courier.id)
        self.assertEqual([], self.service.available_couriers())

        for status in (
            OrderStatus.CONFIRMED,
            OrderStatus.IN_DELIVERY,
            OrderStatus.DELIVERED,
        ):
            self.service.change_status(self.order.id, status)

        self.assertIs(OrderStatus.DELIVERED, self.order.status)
        self.assertEqual([self.courier], self.service.available_couriers())

    def test_unknown_delivery_method_is_rejected(self):
        with self.assertRaises(NotFoundError):
            self.service.set_delivery_method(self.order.id, StandardDelivery())

    def test_domain_errors_are_propagated(self):
        with self.assertRaises(InvalidOperationError):
            self.service.change_status(self.order.id, OrderStatus.DELIVERED)


if __name__ == "__main__":
    unittest.main()
