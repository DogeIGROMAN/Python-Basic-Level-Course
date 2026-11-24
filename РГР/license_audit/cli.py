#Модуль інтерфейсу командного рядка (CLI) та координації сценарію аудиту.
import argparse
import sys
from .exceptions import LicenseAuditError
from .optimizer import audit_and_optimize, benchmark_audit
from .storage import load_licenses_from_txt, save_report_csv, save_report_json

#Формує конфігурацію аргументів командного рядка.
def build_parser() -> argparse.ArgumentParser:
    # Створення конфігурації
    parser = argparse.ArgumentParser(description="Аудит та оптимізація розподілу ліцензій ПЗ.")
    # Обов'язковий параметр, щоб без вхідного файлу не запускали
    parser.add_argument(
        "--input",
        required=True,
        help="Шлях до вхідного файлу записів (.txt)",
    )
    # Додаткові параметри мають безпечні значення за замовчуванням для виводу Json та Csv
    parser.add_argument(
        "--out-json",
        default="output/report.json",
        help="Шлях до JSON-звіту",
    )
    parser.add_argument(
        "--out-csv",
        default="output/licenses_audit.csv",
        help="Шлях до CSV-звіту",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Точка координації CLI: парсить аргументи, запускає конвеєр обробки
    та повертає код завершення процесу (0 — успіх, 1 — помилка системи).
    """

    """
    Якщо список аргументів не передано явно (наприклад, з тестів),
    беремо аргументи командного рядка без імені самого скрипта (sys.argv[1:])
    """
    raw_args = argv if argv is not None else sys.argv[1:]
    args = build_parser().parse_args(raw_args)

    try:
        # 1. Завантаження та парсинг і валідація вхідних даних із файлу
        items = load_licenses_from_txt(args.input)

        # 2. Виконання аудиту та жадібного перерозподілу вільних ліцензій
        transfers, summary = audit_and_optimize(items)

        # 3. Замір середнього часу виконання для оцінки швидкодії
        avg_ms = benchmark_audit(items, repeat=50)

        # 4. Збереження результатів у два вихідні формати (JSON та CSV)
        save_report_json(args.out_json, transfers, summary)
        save_report_csv(args.out_csv, items)

        # 5. Вивід короткого підсумку в стандартний потік виводу (stdout)
        print("=== ЗВЕДЕННЯ АУДИТУ ===")
        for key, value in summary.items():
            print(f"{key}: {value}")
        print(f"avg_audit_time_ms: {avg_ms}")
        return 0

    except LicenseAuditError as exc:
        # Перехоплюємо лише очікувані доменні помилки нашої ієрархії
        print(f"[ПОМИЛКА СИСТЕМИ] {exc}", file=sys.stderr)
        return 1
