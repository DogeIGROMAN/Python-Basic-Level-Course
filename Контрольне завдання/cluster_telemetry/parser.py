"""Синтаксична перевірка та парсинг рядків журналу за допомогою іменованих груп regex."""

from datetime import datetime
import re
from .exceptions import InvalidBitmaskError, MalformedLogEntryError
from .models import ComputeNodeMetric, ServerNodeMetric, StorageNodeMetric

__all__ = ["LOG_PATTERN", "parse_log_line"]

LOG_PATTERN = re.compile(
    r"""
    ^\s*
    (?P<host>
        (?:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})
        |
        (?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+)
    )
    \s+
    (?P<health_reg>(?:0[xX])?[0-9a-fA-F]{1,4})
    \s+
    (?P<resource_type>CPU|RAM):(?P<resource_value>[0-9]+(?:\.[0-9]+)?)(?P<resource_unit>%|[A-Za-z]+)
    \s+
    (?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))
    \s*$
    """,
    re.VERBOSE,
)


def parse_log_line(line: str) -> ServerNodeMetric:
    """Розбирає один рядок журналу у відповідний об'єкт метрики вузла."""
    match = LOG_PATTERN.match(line)
    if not match:
        raise MalformedLogEntryError(f"Некоректний рядок журналу: {line.strip()!r}")

    groups = match.groupdict()
    host_id = groups["host"]
    raw_reg = groups["health_reg"]
    resource_type = groups["resource_type"]
    resource_value = float(groups["resource_value"])
    resource_unit = groups["resource_unit"]
    raw_ts = groups["timestamp"]

    try:
        health_register = int(raw_reg, 16)
    except ValueError as exc:
        raise InvalidBitmaskError(f"Недійсний шістнадцятковий регістр {raw_reg!r}") from exc

    try:
        iso_ts = raw_ts[:-1] + "+00:00" if raw_ts.endswith("Z") else raw_ts
        timestamp = datetime.fromisoformat(iso_ts)
    except ValueError as exc:
        raise MalformedLogEntryError(f"Некоректна мітка часу ISO 8601 {raw_ts!r}") from exc

    if resource_type == "CPU":
        return ComputeNodeMetric(
            host_id=host_id,
            health_register=health_register,
            resource_type=resource_type,
            resource_usage=resource_value,
            resource_unit=resource_unit,
            timestamp=timestamp,
        )

    return StorageNodeMetric(
        host_id=host_id,
        health_register=health_register,
        resource_type=resource_type,
        resource_usage=resource_value,
        resource_unit=resource_unit,
        timestamp=timestamp,
    )