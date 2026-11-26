"""Точка входу для потокового аналізу журналу та безпечного збереження звіту."""

from pathlib import Path
from .analyzer import build_incident_report, stream_metrics
from .exceptions import CriticalStorageError, TelemetryError


def process_telemetry_file(input_path: Path, output_path: Path) -> None:
    """Потоково читає файл журналу рядок за рядком і записує аналітичний звіт."""
    parse_errors: list[str] = []
    critical_errors: list[str] = []
    collected_metrics = []

    log_handle = None
    try:
        # Менеджер контексту читає файл потоково без повного завантаження в оперативну пам'ять
        with input_path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                if not line.strip():
                    continue
                try:
                    metric = next(stream_metrics([line], errors_log=parse_errors))
                except StopIteration:
                    continue
                except CriticalStorageError as exc:
                    critical_errors.append(f"Рядок {line_no}: {exc}")
                except TelemetryError as exc:
                    parse_errors.append(f"Рядок {line_no}: {exc}")
                else:
                    collected_metrics.append(metric)
    except OSError as exc:
        raise RuntimeError(f"Не вдалося прочитати вхідний файл '{input_path}': {exc}") from exc
    else:
        report_text = build_incident_report(collected_metrics, parse_errors, critical_errors)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as out_f:
                out_f.write(report_text)
        except OSError as exc:
            raise RuntimeError(f"Не вдалося записати файл звіту '{output_path}': {exc}") from exc
    finally:
        if log_handle is not None and not log_handle.closed:
            log_handle.close()


def main() -> None:
    """Створює тестовий лог за потреби та запускає конвеєр обробки телеметрії."""
    base_dir = Path(__file__).resolve().parent
    sample_log = base_dir / "sample_cluster.log"
    report_file = base_dir / "reports" / "incident_report.txt"

    if not sample_log.exists():
        sample_log.write_text(
            "\n".join([
                "node-01.eu-central.cloud 0x0000 CPU:42.5% 2026-11-26T10:00:00Z",
                "550e8400-e29b-41d4-a716-446655440000 0x0002 CPU:94.2% 2026-11-26T10:01:00+02:00",
                "storage-02.eu-central.cloud 0x0001 RAM:8192MiB 2026-11-26T10:02:00Z",
                "storage-03.eu-central.cloud 0x0010 RAM:16384MiB 2026-11-26T10:03:00Z",
                "пошкоджений-рядок-без-полів",
            ])
            + "\n",
            encoding="utf-8",
        )

    process_telemetry_file(sample_log, report_file)
    print(f"Звіт сформовано за шляхом: {report_file}")


if __name__ == "__main__":
    main()

#Варто запускати як пакет з терміналу: python -m cluster_telemetry.main