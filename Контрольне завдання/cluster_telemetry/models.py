"""Моделі вузлів кластера та міксин системних сповіщень."""

from datetime import datetime
from .bitmasks import (
    HealthFlag,
    MAX_HEALTH_REGISTER,
    decode_health_flags,
    has_critical_or_degraded_state,
)
from .exceptions import CriticalStorageError, InvalidBitmaskError

__all__ = [
    "AlertableMixin",
    "ServerNodeMetric",
    "ComputeNodeMetric",
    "StorageNodeMetric",
]


class AlertableMixin:
    """Міксин для формування системних сповіщень про деградовані або аварійні вузли."""

    def active_flags(self) -> tuple[HealthFlag, ...]:
        """Повертає активні прапори з регістра стану вузла."""
        return decode_health_flags(self.health_register)  # type: ignore[attr-defined]

    def format_alert(self) -> str:
        """Формує текстове сповіщення на основі активних прапорів стану."""
        flags = self.active_flags()
        if not flags:
            return f"[OK] {self.host_id}: активних прапорів збою немає."  # type: ignore[attr-defined]
        flag_names = ", ".join(flag.name for flag in flags)
        return (
            f"[СПОВІЩЕННЯ] Хост={self.host_id} | Регістр=0x{self.health_register:04X} "  # type: ignore[attr-defined]
            f"| Ресурс={self.resource_type}:{self.resource_usage:.2f}{self.resource_unit} "  # type: ignore[attr-defined]
            f"| Прапори=[{flag_names}] | Час={self.timestamp.isoformat()}"  # type: ignore[attr-defined]
        )


class ServerNodeMetric:
    """Базовий клас метрики серверного вузла з інкапсуляцією атрибутів через @property."""

    def __init__(
        self,
        host_id: str,
        health_register: int,
        resource_type: str,
        resource_usage: float,
        resource_unit: str,
        timestamp: datetime,
    ) -> None:
        self.host_id = host_id
        self.health_register = health_register
        self.resource_type = resource_type
        self.resource_usage = resource_usage
        self.resource_unit = resource_unit
        self.timestamp = timestamp

    @property
    def host_id(self) -> str:
        return self._host_id

    @host_id.setter
    def host_id(self, value: str) -> None:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Ідентифікатор хоста не може бути порожнім.")
        self._host_id = cleaned

    @property
    def health_register(self) -> int:
        return self._health_register

    @health_register.setter
    def health_register(self, value: int) -> None:
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidBitmaskError("Регістр стану має бути цілим числом.")
        if not (0 <= value <= MAX_HEALTH_REGISTER):
            raise InvalidBitmaskError(f"Регістр поза допустимим діапазоном: {value:#x}")
        self._health_register = value

    @property
    def resource_type(self) -> str:
        return self._resource_type

    @resource_type.setter
    def resource_type(self, value: str) -> None:
        normalized = value.strip().upper()
        if normalized not in {"CPU", "RAM"}:
            raise ValueError(f"Непідтримуваний тип ресурсу: {value}")
        self._resource_type = normalized

    @property
    def resource_usage(self) -> float:
        return self._resource_usage

    @resource_usage.setter
    def resource_usage(self, value: float) -> None:
        if value < 0:
            raise ValueError("Обсяг спожитого ресурсу не може бути від'ємним.")
        self._resource_usage = float(value)

    @property
    def resource_unit(self) -> str:
        return self._resource_unit

    @resource_unit.setter
    def resource_unit(self, value: str) -> None:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Одиниця вимірювання не може бути порожньою.")
        self._resource_unit = cleaned

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: datetime) -> None:
        if not isinstance(value, datetime):
            raise TypeError("Часова мітка має бути об'єктом datetime.")
        self._timestamp = value

    @property
    def is_degraded(self) -> bool:
        """Перевіряє, чи має вузол ознаки деградації або збою."""
        return has_critical_or_degraded_state(self._health_register)

    def __str__(self) -> str:
        return (
            f"{self.host_id} ({self.resource_type}={self.resource_usage}{self.resource_unit}, "
            f"регістр=0x{self.health_register:04X}, час={self.timestamp.isoformat()})"
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"host_id={self.host_id!r}, "
            f"health_register={self.health_register:#06x}, "
            f"resource_type={self.resource_type!r}, "
            f"resource_usage={self.resource_usage!r}, "
            f"resource_unit={self.resource_unit!r}, "
            f"timestamp={self.timestamp!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ServerNodeMetric):
            return NotImplemented
        return (
            self.host_id == other.host_id
            and self.health_register == other.health_register
            and self.resource_type == other.resource_type
            and self.resource_usage == other.resource_usage
            and self.resource_unit == other.resource_unit
            and self.timestamp == other.timestamp
        )

    def __hash__(self) -> int:
        return hash((
            self.host_id,
            self.health_register,
            self.resource_type,
            self.resource_usage,
            self.resource_unit,
            self.timestamp,
        ))


class ComputeNodeMetric(AlertableMixin, ServerNodeMetric):
    """Спеціалізований клас метрик для обчислювальних вузлів."""

    @property
    def is_cpu_throttled(self) -> bool:
        return bool(self.health_register & HealthFlag.CPU_THROTTLING)


class StorageNodeMetric(AlertableMixin, ServerNodeMetric):
    """Спеціалізований клас метрик для вузлів сховища даних."""

    def __init__(
        self,
        host_id: str,
        health_register: int,
        resource_type: str,
        resource_usage: float,
        resource_unit: str,
        timestamp: datetime,
    ) -> None:
        super().__init__(
            host_id=host_id,
            health_register=health_register,
            resource_type=resource_type,
            resource_usage=resource_usage,
            resource_unit=resource_unit,
            timestamp=timestamp,
        )
        if self.health_register & HealthFlag.DISK_CRITICAL:
            raise CriticalStorageError(
                f"Критична помилка диска на вузлі сховища {self.host_id} "
                f"(регістр=0x{self.health_register:04X})."
            )