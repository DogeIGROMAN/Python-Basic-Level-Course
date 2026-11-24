"""Доменні моделі ліцензій ПЗ: ієрархія класів, валідація стану та dunder-методи."""

from .exceptions import LicenseCapacityError
from .validation import normalize_code, normalize_department


class LicenseItem:
    """Базовий клас запису про ліцензію у конкретному підрозділі."""

    def __init__(
        self,
        code: str,
        department: str,
        total_seats: int,
        used_seats: int,
        unit_cost: float,
    ) -> None:
        # Код та відділ нормалізуємо через функції з validation.py.
        # Поля з одним підкресленням (_code, _department) - це protected/внутрішні
        self._code = normalize_code(code)
        self._department = normalize_department(department)
        self.total_seats = total_seats
        self.used_seats = used_seats
        self.unit_cost = unit_cost

    @property
    def code(self) -> str:
        """Повертає нормалізований код ліцензії (тільки для читання)."""
        return self._code

    @property
    def department(self) -> str:
        """Повертає нормалізований код відділу (тільки для читання)."""
        return self._department

    @property
    def total_seats(self) -> int:
        """Загальна кількість виділених місць за ліцензією."""
        return self._total_seats

    @total_seats.setter
    def total_seats(self, value: int) -> None:
        # Кількість місць має бути строго додатною.
        # При порушенні кидаємо виняток нашої ієрархії LicenseCapacityError.
        if value <= 0:
            raise LicenseCapacityError("Кількість ліцензій має бути більшою за 0.")
        self._total_seats = value

    @property
    def used_seats(self) -> int:
        """Кількість фактично зайнятих/використаних місць."""
        return self._used_seats

    @used_seats.setter
    def used_seats(self, value: int) -> None:
        # Від'ємна кількість використаних місць беззмістовна.
        # Водночас used_seats може тимчасово перевищувати total_seats (дефіцит).
        if value < 0:
            raise LicenseCapacityError(
                "Кількість використаних ліцензій не може бути від'ємною."
            )
        self._used_seats = value

    @property
    def unit_cost(self) -> float:
        """Вартість одного місця/ліцензії."""
        return self._unit_cost

    @unit_cost.setter
    def unit_cost(self, value: float) -> None:
        if value < 0:
            raise LicenseCapacityError(
                "Вартість одиниці ліцензії не може бути від'ємною."
            )
        self._unit_cost = float(value)


    # Обчислювані властивості, які лише для читання
    @property
    def free_seats(self) -> int:
        """Кількість вільних місць (надлишок); якщо дефіцит — повертає 0."""
        return max(0, self._total_seats - self._used_seats)

    @property
    def deficit_seats(self) -> int:
        """Кількість дефіцитних місць; якщо місць вистачає - повертає 0."""
        return max(0, self._used_seats - self._total_seats)


    @property
    def total_cost(self) -> float:
        """Загальна вартість виділеного пакета ліцензій."""
        return round(self._total_seats * self._unit_cost, 2)

    @property
    def wasted_cost(self) -> float:
        """Вартість невикористаних (вільних) місць."""
        return round(self.free_seats * self._unit_cost, 2)


    def license_type(self) -> str:
        """Повертає строковий тип ліцензії; перевизначається в підкласах."""
        return "GENERIC"

    def __str__(self) -> str:
        """Людиноорієнтоване представлення об'єкта (викликається print(), str())."""
        return (
            f"[{self.license_type()}] {self._code} ({self._department}): "
            f"використано {self._used_seats}/{self._total_seats}, "
            f"вільно {self.free_seats}, дефіцит {self.deficit_seats}"
        )

    def __repr__(self) -> str:
        """Технічне представлення для налагодження/логів (викликається repr(), у консолі)."""
        return (
            f"{self.__class__.__name__}(code={self._code!r}, "
            f"department={self._department!r}, total_seats={self._total_seats}, "
            f"used_seats={self._used_seats}, unit_cost={self._unit_cost})"
        )

    def __eq__(self, other: object) -> bool:
        """Перевірка рівності: два записи рівні за парою (code, department)."""
        if not isinstance(other, LicenseItem):
            return NotImplemented
        return (self._code, self._department) == (other._code, other._department)

    def __lt__(self, other: object) -> bool:
        """
        Порядок менше, який використовує функція sorted().
        Сортує спочатку за спаданням невитрачених коштів (wasted_cost),
        а за однакових втрат — за кодом ліцензії (code).
        """
        if not isinstance(other, LicenseItem):
            return NotImplemented
        return (-self.wasted_cost, self._code) < (-other.wasted_cost, other._code)


class SubscriptionLicense(LicenseItem):
    """Ліцензія за моделлю підписки з певним строком дії у місяцях."""

    def __init__(
        self,
        code: str,
        department: str,
        total_seats: int,
        used_seats: int,
        unit_cost: float,
        term_months: int = 12,
    ) -> None:
        # Викликаємо конструктор базового класу, щоб ініціалізувати спільні поля та перевірки
        super().__init__(code, department, total_seats, used_seats, unit_cost)
        if term_months <= 0:
            raise LicenseCapacityError("Строк підписки у місяцях має бути більшим за 0.")
        self.term_months = term_months

    def license_type(self) -> str:
        return f"SUBSCRIPTION_{self.term_months}M"


class PerpetualLicense(LicenseItem):
    """Безстрокова ліцензія (постійна купівля без періодичного подовження підписки)."""

    def license_type(self) -> str:
        return "PERPETUAL"