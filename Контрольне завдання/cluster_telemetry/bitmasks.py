"""Бітові прапорці та функції для декодування регістра стану (Health Register)."""

from enum import IntFlag
from .exceptions import InvalidBitmaskError

__all__ = [
    "HealthFlag",
    "MAX_HEALTH_REGISTER",
    "decode_health_flags",
    "has_critical_or_degraded_state",
]


class HealthFlag(IntFlag):
    """Апаратні та системні прапори стану в регістрі Health Register."""

    NONE = 0x0000
    MEMORY_DEGRADATION = 0x0001  # Деградація пам'яті
    CPU_THROTTLING = 0x0002      # Тротлінг CPU
    COOLING_FAILURE = 0x0004     # Відмова охолодження
    NIC_ISOLATION = 0x0008       # Ізоляція мережевого інтерфейсу
    DISK_CRITICAL = 0x0010       # Критична помилка дискової підсистеми


MAX_HEALTH_REGISTER = 0xFFFF
KNOWN_FLAGS_MASK = (
    HealthFlag.MEMORY_DEGRADATION
    | HealthFlag.CPU_THROTTLING
    | HealthFlag.COOLING_FAILURE
    | HealthFlag.NIC_ISOLATION
    | HealthFlag.DISK_CRITICAL
)


def decode_health_flags(register_value: int) -> tuple[HealthFlag, ...]:
    """Перевіряє значення регістра та повертає кортеж активних відомих прапорів."""
    if not isinstance(register_value, int) or isinstance(register_value, bool):
        raise InvalidBitmaskError("Регістр стану має бути цілим числом.")
    if register_value < 0 or register_value > MAX_HEALTH_REGISTER:
        raise InvalidBitmaskError(f"Регістр 0x{register_value:X} виходить за межі 0x0..0x{MAX_HEALTH_REGISTER:X}.")

    # Побітове І перевіряє, чи встановлений відповідний біт
    active_flags = [flag for flag in HealthFlag if flag != HealthFlag.NONE and (register_value & flag)]
    return tuple(active_flags)


def has_critical_or_degraded_state(register_value: int) -> bool:
    """Повертає True, якщо встановлено хоча б один прапор деградації або збою."""
    if register_value < 0 or register_value > MAX_HEALTH_REGISTER:
        raise InvalidBitmaskError(
            f"Регістр 0x{register_value:X} виходить за допустимі межі."
        )
    return bool(register_value & KNOWN_FLAGS_MASK)