"""Сервис управления складом товаров."""

from delivery.models import Product
from delivery.services.errors import NotFoundError


class ProductService:
    """Хранит товары склада в памяти и выдаёт им идентификаторы.

    Резервирование и возврат товаров выполняет заказ через методы
    Product, поэтому остатки здесь всегда актуальны.
    """

    def __init__(self) -> None:
        self._products: dict[int, Product] = {}
        self._next_id = 1

    def add_product(self, name: str, price, stock: int) -> Product:
        """Добавляет на склад новый товар."""
        product = Product(self._next_id, name, price, stock)
        self._products[product.id] = product
        self._next_id += 1
        return product

    def get_product(self, product_id: int) -> Product:
        """Возвращает товар по идентификатору.

        Raises:
            NotFoundError: если товара с таким идентификатором нет.
        """
        try:
            return self._products[product_id]
        except KeyError:
            raise NotFoundError(f"Товар #{product_id} не найден") from None

    def list_products(self) -> list[Product]:
        """Возвращает все товары склада, включая закончившиеся."""
        return list(self._products.values())

    def available_products(self) -> list[Product]:
        """Возвращает товары, которые есть в наличии."""
        return [product for product in self._products.values() if product.in_stock]

    def restock(self, product_id: int, quantity: int) -> Product:
        """Пополняет запас товара."""
        product = self.get_product(product_id)
        product.restock(quantity)
        return product
