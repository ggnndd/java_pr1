import unittest
from datetime import timedelta
from decimal import Decimal

from delivery.models import (
    Customer,
    ExpressDelivery,
    Order,
    OrderItem,
    OrderStatus,
    PickupDelivery,
    StandardDelivery,
)


def make_order(price, quantity=1):
    order = Order(1, Customer("Иван", "89001234567"), "ул. Ленина, 1")
    order.add_item(OrderItem("Товар", quantity, price))
    return order


class StandardDeliveryTest(unittest.TestCase):

    def setUp(self):
        self.method = StandardDelivery()

    def test_cost_is_fixed_below_threshold(self):
        self.assertEqual(Decimal("300.00"), self.method.calculate_cost(make_order(1000)))

    def test_free_from_threshold(self):
        self.assertEqual(Decimal("0.00"), self.method.calculate_cost(make_order(3000)))

    def test_large_order_takes_longer(self):
        self.assertEqual(timedelta(days=2), self.method.estimate_time(make_order(10, 10)))
        self.assertEqual(timedelta(days=3), self.method.estimate_time(make_order(10, 11)))

    def test_requires_courier(self):
        self.assertTrue(self.method.requires_courier)
        self.assertIs(OrderStatus.IN_DELIVERY, self.method.transit_status)


class ExpressDeliveryTest(unittest.TestCase):

    def test_cost_depends_on_order_total(self):
        method = ExpressDelivery()
        self.assertEqual(Decimal("600.00"), method.calculate_cost(make_order(1000)))
        self.assertEqual(timedelta(hours=3), method.estimate_time(make_order(1000)))

    def test_more_expensive_than_standard(self):
        order = make_order(5000)
        self.assertGreater(
            ExpressDelivery().calculate_cost(order),
            StandardDelivery().calculate_cost(order),
        )


class PickupDeliveryTest(unittest.TestCase):

    def test_free_and_without_courier(self):
        method = PickupDelivery("ТЦ «Центр»")
        self.assertEqual(Decimal("0.00"), method.calculate_cost(make_order(1000)))
        self.assertFalse(method.requires_courier)
        self.assertIs(OrderStatus.READY_FOR_PICKUP, method.transit_status)

    def test_blank_pickup_point_is_rejected(self):
        with self.assertRaises(ValueError):
            PickupDelivery("  ")


if __name__ == "__main__":
    unittest.main()
