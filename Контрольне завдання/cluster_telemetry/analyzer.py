"""Фільтрація, статистичний аналіз, генератори та формування аналітичного звіту."""

from collections.abc import Iterable, Iterator
from .models import ServerNodeMetric

__all__ = [
    "stream_metrics",
    "filter_metrics",
    "group_metrics_by_host",
    "find_unique_degraded_hosts",
    "compute_resource_stats",
    "build_incident_report",
]


def stream_metrics(lines: Iterable[str], errors_log: list[str] | None = None) -> Iterator[ServerNodeMetric]:
    """Ліниво перетворює рядки журналу на об'єкти метрик без завантаження всього файлу в RAM."""
    from .parser import parse_log_line
    from .exceptions import TelemetryError

    for line_no, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            yield parse_log_line(line)
        except TelemetryError as exc:
            if errors_log is not None:
                errors_log.append(f"Рядок {line_no}: {exc}")


def filter_metrics(
    metrics: Iterable[ServerNodeMetric],
    *hosts: str,
    min_usage: float = 0.0,
    only_degraded: bool = False,
    **extra_filters: object,
) -> Iterator[ServerNodeMetric]:
    """Фільтрує записи телеметрії з використанням *args, іменованих параметрів і **kwargs."""
    host_set = {h.strip() for h in hosts if h.strip()}
    resource_type = extra_filters.get("resource_type")

    # Генераторний вираз усередині функції-генератора для економії пам'яті
    filtered = (
        metric
        for metric in metrics
        if (not host_set or metric.host_id in host_set)
        and metric.resource_usage >= min_usage
        and (not only_degraded or metric.is_degraded)
        and (resource_type is None or metric.resource_type == resource_type)
    )
    yield from filtered


def group_metrics_by_host(metrics: Iterable[ServerNodeMetric]) -> dict[str, list[ServerNodeMetric]]:
    """Групує записи метрик за ідентифікатором хоста зі збереженням порядку появи."""
    grouped: dict[str, list[ServerNodeMetric]] = {}
    for metric in metrics:
        grouped.setdefault(metric.host_id, []).append(metric)
    return grouped


def find_unique_degraded_hosts(metrics: Iterable[ServerNodeMetric]) -> set[str]:
    """Повертає множину унікальних хостів із ознаками деградації або збою."""
    return {metric.host_id for metric in metrics if metric.is_degraded}


def compute_resource_stats(metrics: Iterable[ServerNodeMetric]) -> dict[str, float | int]:
    """Обчислює кількість записів, min, max та середнє значення споживання ресурсів."""
    count = 0
    total = 0.0
    min_val: float | None = None
    max_val: float | None = None

    for metric in metrics:
        val = metric.resource_usage
        count += 1
        total += val
        min_val = val if min_val is None else min(min_val, val)
        max_val = val if max_val is None else max(max_val, val)

    if count == 0:
        return {"count": 0, "min": 0.0, "max": 0.0, "avg": 0.0}

    return {
        "count": count,
        "min": round(min_val if min_val is not None else 0.0, 2),
        "max": round(max_val if max_val is not None else 0.0, 2),
        "avg": round(total / count, 2),
    }


def build_incident_report(
    metrics: Iterable[ServerNodeMetric],
    parse_errors: list[str],
    critical_errors: list[str],
) -> str:
    """Формує аналітичний звіт про інциденти на основі обробленої телеметрії."""
    metric_list = list(metrics)
    grouped = group_metrics_by_host(metric_list)
    degraded_hosts = sorted(find_unique_degraded_hosts(metric_list))
    stats = compute_resource_stats(metric_list)

    lines = [
        "=== АНАЛІТИЧНИЙ ЗВІТ ПРО ІНЦИДЕНТИ КЛАСТЕРА ===",
        f"Всього валідних записів : {stats['count']}",
        f"Унікальних хостів       : {len(grouped)}",
        f"Деградованих хостів     : {len(degraded_hosts)} -> {', '.join(degraded_hosts) if degraded_hosts else 'Немає'}",
        f"Статистика ресурсів     : min={stats['min']}, max={stats['max']}, avg={stats['avg']}",
        f"Помилок парсингу/масок  : {len(parse_errors)}",
        f"Критичних помилок диска : {len(critical_errors)}",
        "",
        "--- СПОВІЩЕННЯ ПО ДЕГРАДОВАНИХ ВУЗЛАХ ---",
    ]

    alerts = [m.format_alert() for m in metric_list if m.is_degraded and hasattr(m, "format_alert")]
    lines.extend(alerts if alerts else ["Активних сповіщень немає."])

    if critical_errors:
        lines.extend(["", "--- КРИТИЧНІ ІНЦИДЕНТИ СХОВИЩА ---", *critical_errors])

    if parse_errors:
        lines.extend(["", "--- ПОМИЛКИ РОЗБОРУ ЖУРНАЛУ ---", *parse_errors])

    return "\n".join(lines) + "\n"