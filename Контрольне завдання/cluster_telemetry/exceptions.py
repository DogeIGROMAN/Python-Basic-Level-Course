"""Ієрархія користувацьких винятків для обробки телеметрії кластера."""

__all__ = [
    "TelemetryError",
    "MalformedLogEntryError",
    "InvalidBitmaskError",
    "CriticalStorageError",
]


class TelemetryError(Exception):
    """Базовий виняток для всіх помилок обробки телеметрії."""


class MalformedLogEntryError(TelemetryError):
    """Виникає, коли рядок журналу пошкоджений або не відповідає очікуваному формату."""


class InvalidBitmaskError(TelemetryError):
    """Виникає, коли бітова маска регістра стану некоректна або виходить за межі."""


class CriticalStorageError(TelemetryError):
    """Виникає при критичній помилці дискової підсистеми або сховища даних."""