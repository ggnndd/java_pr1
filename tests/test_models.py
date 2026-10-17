import unittest
from decimal import Decimal

from delivery.models import (
    Courier,
    Customer,
    InvalidOperationError,
    Order,
    OrderItem,
    OrderStatus,
    Person,
    Product,
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

    def test_fields_can_be_validated_separately(self):
        self.assertEqual("+79001234567", Customer.validate_phone("+7 900 123 45 67"))
        with self.assertRaises(ValueError):
            Customer.validate_phone("123")
        with self.assertRaises(ValueError):
            Customer.validate_name("")

    def test_customer_and_courier_are_persons(self):
        self.assertIsInstance(Customer("Иван", "89001234567"), Person)
        self.assertIsInstance(Courier(1, "Пётр", "89001112233"), Person)


class CourierTest(unittest.TestCase):

    def setUp(self):
        self.courier = Courier(1, "Пётр", "89001112233")
        self.order = Order(1, Customer("Иван", "89001234567"), "ул. Ленина, 1")

    def test_new_courier_is_free(self):
        self.assertTrue(self.courier.is_available)
        self.assertIsNone(self.courier.current_order)
        self.assertIn("свободен", str(self.courier))

    def test_cannot_take_order_bypassing_order(self):
        with self.assertRaises(InvalidOperationError):
            self.courier.take_order(self.order)
        self.assertTrue(self.courier.is_available)

    def test_cannot_release_order_it_does_not_have(self):
        with self.assertRaises(InvalidOperationError):
            self.courier.release_order(self.order)


class ProductTest(unittest.TestCase):

    def setUp(self):
        self.product = Product(1, "Пицца", "500", 5)

    def test_reserve_and_release(self):
        self.product.reserve(3)
        self.assertEqual(2, self.product.stock)
        self.product.release(3)
        self.assertEqual(5, self.product.stock)

    def test_cannot_reserve_more_than_in_stock(self):
        with self.assertRaises(InvalidOperationError):
            self.product.reserve(6)
        self.assertEqual(5, self.product.stock)

    def test_restock(self):
        self.product.restock(10)
        self.assertEqual(15, self.product.stock)

    def test_invalid_quantities(self):
        with self.assertRaises(ValueError):
            self.product.reserve(0)
        with self.assertRaises(ValueError):
            self.product.restock(-1)
        with self.assertRaises(ValueError):
            Product(2, "Сок", 100, -1)


class PriceValidationTest(unittest.TestCase):

    def test_valid_prices(self):
        self.assertEqual(Decimal("499.90"), Product.validate_price("499,9"))
        self.assertEqual(Decimal("0.01"), Product.validate_price("0.01"))
        self.assertEqual(Decimal("100.00"), Product.validate_price(100))

    def test_fractions_of_cent_are_rejected_not_rounded(self):
        with self.assertRaises(ValueError):
            Product.validate_price("0.001")
        with self.assertRaises(ValueError):
            Product.validate_price("10.555")

    def test_non_positive_and_garbage_are_rejected(self):
        for value in ("0", "-5", "abc", "nan", "inf", "1e100"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    Product.validate_price(value)


class OrderItemTest(unittest.TestCase):

    def test_total_uses_product_price(self):
        item = OrderItem(Product(1, "Пицца", "499.90", 10), 2)
        self.assertEqual(Decimal("999.80"), item.total)
        self.assertEqual("Пицца", item.product_name)

    def test_invalid_quantity(self):
        with self.assertRaises(ValueError):
            OrderItem(Product(1, "Пицца", 100, 10), 0)


class OrderTest(unittest.TestCase):

    def setUp(self):
        self.order = Order(1, Customer("Иван", "89001234567"), "ул. Ленина, 1")
        self.pizza = Product(1, "Пицца", 500, 10)
        self.juice = Product(2, "Сок", "120.50", 10)

    def test_new_order_is_created_and_empty(self):
        self.assertIs(OrderStatus.CREATED, self.order.status)
        self.assertEqual(Decimal("0.00"), self.order.items_total)

    def test_add_products_reserves_stock(self):
        self.order.add_product(self.pizza, 2)
        self.order.add_product(self.juice, 1)
        self.assertEqual(2, len(self.order.items))
        self.assertEqual(Decimal("1120.50"), self.order.items_total)
        self.assertEqual(8, self.pizza.stock)
        self.assertEqual(9, self.juice.stock)

    def test_same_product_is_merged(self):
        self.order.add_product(self.pizza, 2)
        self.order.add_product(self.pizza, 3)
        self.assertEqual(1, len(self.order.items))
        self.assertEqual(5, self.order.items[0].quantity)
        self.assertEqual(5, self.pizza.stock)

    def test_insufficient_stock_does_not_change_order(self):
        with self.assertRaises(InvalidOperationError):
            self.order.add_product(self.pizza, 11)
        self.assertEqual((), self.order.items)
        self.assertEqual(10, self.pizza.stock)

    def test_items_cannot_be_modified_from_outside(self):
        self.assertIsInstance(self.order.items, tuple)

    def test_address_validation(self):
        with self.assertRaises(ValueError):
            Order.validate_address("  ")


if __name__ == "__main__":
    unittest.main()
