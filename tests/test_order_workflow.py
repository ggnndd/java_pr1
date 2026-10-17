import unittest
from decimal import Decimal

from delivery.models import (
    Courier,
    Customer,
    ExpressDelivery,
    InvalidOperationError,
    Order,
    OrderStatus,
    PickupDelivery,
    Product,
    StandardDelivery,
)


class OrderWorkflowTest(unittest.TestCase):

    def setUp(self):
        self.order = Order(1, Customer("Иван", "89001234567"), "ул. Ленина, 1")
        self.pizza = Product(1, "Пицца", 500, 10)
        self.order.add_product(self.pizza, 2)
        self.courier = Courier(1, "Пётр", "89001112233")

    def test_cancel_returns_products_to_stock(self):
        self.order.change_status(OrderStatus.CANCELLED)
        self.assertEqual(10, self.pizza.stock)

    def test_delivery_does_not_return_products(self):
        self.order.set_delivery_method(PickupDelivery("ТЦ «Центр»"))
        for status in (
            OrderStatus.CONFIRMED,
            OrderStatus.READY_FOR_PICKUP,
            OrderStatus.DELIVERED,
        ):
            self.order.change_status(status)
        self.assertEqual(8, self.pizza.stock)

    def test_courier_delivery_full_cycle(self):
        self.order.set_delivery_method(StandardDelivery())
        self.order.assign_courier(self.courier)
        self.order.change_status(OrderStatus.CONFIRMED)
        self.order.change_status(OrderStatus.IN_DELIVERY)
        self.assertIs(self.order, self.courier.current_order)

        self.order.change_status(OrderStatus.DELIVERED)
        self.assertIs(OrderStatus.DELIVERED, self.order.status)
        self.assertIsNone(self.courier.current_order)
        self.assertIs(self.courier, self.order.courier)  # история сохраняется
        self.assertEqual((), self.order.available_statuses)

    def test_courier_is_bound_to_order(self):
        self.order.set_delivery_method(StandardDelivery())
        self.order.assign_courier(self.courier)
        self.assertIs(self.order, self.courier.current_order)
        self.assertIn("выполняет заказ #1", str(self.courier))

    def test_cannot_release_courier_of_active_order(self):
        self.order.set_delivery_method(StandardDelivery())
        self.order.assign_courier(self.courier)
        self.order.change_status(OrderStatus.CONFIRMED)
        self.order.change_status(OrderStatus.IN_DELIVERY)
        with self.assertRaises(InvalidOperationError):
            self.courier.release_order(self.order)
        self.assertIs(self.order, self.courier.current_order)

    def test_cannot_take_another_order_directly(self):
        other = Order(2, Customer("Анна", "89005556677"), "ул. Мира, 5")
        self.order.set_delivery_method(StandardDelivery())
        self.order.assign_courier(self.courier)
        with self.assertRaises(InvalidOperationError):
            self.courier.take_order(other)
        self.assertIs(self.order, self.courier.current_order)

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
        self.assertIsNone(self.order.courier)
        self.assertIs(other, self.courier.current_order)

    def test_reassigning_courier_releases_previous(self):
        second = Courier(2, "Ольга", "89004445566")
        self.order.set_delivery_method(StandardDelivery())
        self.order.assign_courier(self.courier)
        self.order.assign_courier(second)
        self.assertIsNone(self.courier.current_order)
        self.assertIs(self.order, second.current_order)
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
            self.order.add_product(self.pizza, 1)
        with self.assertRaises(InvalidOperationError):
            self.order.set_delivery_method(StandardDelivery())


if __name__ == "__main__":
    unittest.main()
