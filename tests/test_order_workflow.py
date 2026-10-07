import unittest
from decimal import Decimal

from delivery.models import (
    Courier,
    Customer,
    ExpressDelivery,
    InvalidOperationError,
    Order,
    OrderItem,
    OrderStatus,
    PickupDelivery,
    StandardDelivery,
)


class OrderWorkflowTest(unittest.TestCase):

    def setUp(self):
        self.order = Order(1, Customer("Иван", "89001234567"), "ул. Ленина, 1")
        self.order.add_item(OrderItem("Пицца", 2, 500))
        self.courier = Courier(1, "Пётр", "89001112233")

    def test_courier_delivery_full_cycle(self):
        self.order.set_delivery_method(StandardDelivery())
        self.order.assign_courier(self.courier)
        self.order.change_status(OrderStatus.CONFIRMED)
        self.order.change_status(OrderStatus.IN_DELIVERY)
        self.assertFalse(self.courier.is_available)

        self.order.change_status(OrderStatus.DELIVERED)
        self.assertIs(OrderStatus.DELIVERED, self.order.status)
        self.assertTrue(self.courier.is_available)
        self.assertEqual((), self.order.available_statuses)

    def test_pickup_full_cycle_without_courier(self):
        self.order.set_delivery_method(PickupDelivery("ТЦ «Центр»"))
        self.order.change_status(OrderStatus.CONFIRMED)
        self.order.change_status(OrderStatus.READY_FOR_PICKUP)
        self.order.change_status(OrderStatus.DELIVERED)
        self.assertIs(OrderStatus.DELIVERED, self.order.status)

    def test_total_cost_includes_delivery(self):
        self.assertIsNone(self.order.delivery_cost)
        self.order.set_delivery_method(ExpressDelivery())
        self.assertEqual(Decimal("600.00"), self.order.delivery_cost)
        self.assertEqual(Decimal("1600.00"), self.order.total_cost)

    def test_cannot_confirm_without_delivery_method(self):
        with self.assertRaises(InvalidOperationError):
            self.order.change_status(OrderStatus.CONFIRMED)

    def test_cannot_skip_statuses(self):
        self.order.set_delivery_method(StandardDelivery())
        with self.assertRaises(InvalidOperationError):
            self.order.change_status(OrderStatus.DELIVERED)

    def test_cannot_confirm_empty_order(self):
        order = Order(2, Customer("Анна", "89005556677"), "ул. Мира, 5")
        order.set_delivery_method(StandardDelivery())
        with self.assertRaises(InvalidOperationError):
            order.change_status(OrderStatus.CONFIRMED)

    def test_cannot_start_delivery_without_courier(self):
        self.order.set_delivery_method(StandardDelivery())
        self.order.change_status(OrderStatus.CONFIRMED)
        with self.assertRaises(InvalidOperationError):
            self.order.change_status(OrderStatus.IN_DELIVERY)

    def test_pickup_does_not_accept_courier(self):
        self.order.set_delivery_method(PickupDelivery("ТЦ «Центр»"))
        with self.assertRaises(InvalidOperationError):
            self.order.assign_courier(self.courier)

    def test_switching_to_pickup_releases_courier(self):
        self.order.set_delivery_method(StandardDelivery())
        self.order.assign_courier(self.courier)
        self.order.set_delivery_method(PickupDelivery("ТЦ «Центр»"))
        self.assertIsNone(self.order.courier)
        self.assertTrue(self.courier.is_available)

    def test_busy_courier_cannot_be_assigned(self):
        other = Order(2, Customer("Анна", "89005556677"), "ул. Мира, 5")
        other.set_delivery_method(StandardDelivery())
        other.assign_courier(self.courier)
        self.order.set_delivery_method(StandardDelivery())
        with self.assertRaises(InvalidOperationError):
            self.order.assign_courier(self.courier)

    def test_reassigning_courier_releases_previous(self):
        second = Courier(2, "Ольга", "89004445566")
        self.order.set_delivery_method(StandardDelivery())
        self.order.assign_courier(self.courier)
        self.order.assign_courier(second)
        self.assertTrue(self.courier.is_available)
        self.assertIs(second, self.order.courier)

    def test_cancel_releases_courier(self):
        self.order.set_delivery_method(StandardDelivery())
        self.order.assign_courier(self.courier)
        self.order.change_status(OrderStatus.CANCELLED)
        self.assertTrue(self.courier.is_available)

    def test_confirmed_order_cannot_be_edited(self):
        self.order.set_delivery_method(PickupDelivery("ТЦ «Центр»"))
        self.order.change_status(OrderStatus.CONFIRMED)
        with self.assertRaises(InvalidOperationError):
            self.order.add_item(OrderItem("Сок", 1, 100))
        with self.assertRaises(InvalidOperationError):
            self.order.set_delivery_method(StandardDelivery())


if __name__ == "__main__":
    unittest.main()
