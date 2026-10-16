"""Низкоуровневое взаимодействие с консолью: ввод с проверкой и вывод."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar

T = TypeVar("T")

_YES = {"д", "да", "y", "yes"}
_NO = {"н", "нет", "n", "no"}


class ConsoleIO:
    """Чтение и вывод данных в консоль.

    Методы чтения повторяют запрос, пока пользователь не введёт
    корректное значение. Функции ввода и вывода можно подменить,
    например, в тестах.
    """

    def __init__(
        self,
        input_func: Callable[[str], str] = input,
        output_func: Callable[[str], None] = print,
    ) -> None:
        self._input = input_func
        self._output = output_func

    def show(self, text: str = "") -> None:
        """Выводит текст."""
        self._output(text)

    def success(self, text: str) -> None:
        """Выводит сообщение об успешной операции."""
        self._output(f"✔ {text}")

    def error(self, text: str) -> None:
        """Выводит сообщение об ошибке."""
        self._output(f"✖ Ошибка: {text}")

    def read_text(self, prompt: str) -> str:
        """Читает непустую строку."""
        while True:
            value = self._input(prompt).strip()
            if value:
                return value
            self.error("значение не может быть пустым")

    def read_int(
        self,
        prompt: str,
        min_value: int | None = None,
        max_value: int | None = None,
    ) -> int:
        """Читает целое число в заданных границах."""
        while True:
            raw = self.read_text(prompt)
            try:
                value = int(raw)
            except ValueError:
                self.error(f"«{raw}» не является целым числом")
                continue
            if min_value is not None and value < min_value:
                self.error(f"число должно быть не меньше {min_value}")
            elif max_value is not None and value > max_value:
                self.error(f"число должно быть не больше {max_value}")
            else:
                return value

    def read_valid(self, prompt: str, validate: Callable[[str], T]) -> T:
        """Читает значение и сразу проверяет его функцией validate.

        Если validate выбрасывает ValueError, показывается сообщение
        и запрашивается только это же поле.

        Returns:
            Результат validate (например, нормализованное значение).
        """
        while True:
            raw = self.read_text(prompt)
            try:
                return validate(raw)
            except ValueError as error:
                self.error(str(error))

    def confirm(self, prompt: str) -> bool:
        """Задаёт вопрос «да/нет»."""
        while True:
            answer = self.read_text(f"{prompt} (д/н): ").lower()
            if answer in _YES:
                return True
            if answer in _NO:
                return False
            self.error("введите «д» или «н»")

    def choose(
        self,
        title: str,
        options: Sequence[T],
        describe: Callable[[T], str] = str,
        back_label: str = "Назад",
    ) -> T | None:
        """Предлагает выбрать вариант из списка.

        Returns:
            Выбранный вариант или None, если пользователь выбрал пункт 0.
        """
        self.show(title)
        for number, option in enumerate(options, start=1):
            self.show(f"  {number}. {describe(option)}")
        self.show(f"  0. {back_label}")
        choice = self.read_int("Ваш выбор: ", min_value=0, max_value=len(options))
        return None if choice == 0 else options[choice - 1]
