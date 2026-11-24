#Модуль читання вхідних даних та збереження звітів у форматах JSON і CSV.

import csv
import json
from pathlib import Path
from .exceptions import StorageIOError
from .models import LicenseItem, PerpetualLicense, SubscriptionLicense
from .validation import parse_log_line


def load_licenses_from_txt(filepath: str | Path) -> list[LicenseItem]:
    """
    Читає текстовий файл записів, парсить кожен валідний рядок через `re`
    та повертає список доменних об'єктів ліцензій.
    """
    path = Path(filepath)
    try:
        # Менеджер контексту with гарантує закриття файлу після виходу з блоку,
        # навіть якщо під час читання або парсингу виникне виняток.
        with path.open("r", encoding="utf-8") as f:
            records: list[LicenseItem] = []

            # enumerate(..., start=1) дає порядковий номер рядка (1, 2, 3...) — для діагностики
            for idx, line in enumerate(f, start=1):
                # Пропускаємо порожні рядки та коментарі, що починаються з '#'
                if not line.strip() or line.lstrip().startswith("#"):
                    continue

                # Перетворюємо рядок на словник нормалізованих полів
                data = parse_log_line(line)

                # Витягуємо тип ліцензії зі словника, щоб не передати зайвий ключ у __init__
                lic_type = data.pop("license_type", "SUB")
                #Оскільки в системі наразі 2 типи підписки зроблено, то  зроблено через if-else
                if lic_type == "PERP":
                    records.append(PerpetualLicense(**data))
                else:
                    records.append(SubscriptionLicense(**data))

            return records
    except OSError as exc:
        # Перетворюємо низькорівневу помилку ОС (файл не знайдено, немає доступу тощо)
        # на наш власний виняток StorageIOError, щоб верхній рівень знав про помилку I/O.
        raise StorageIOError(f"Не вдалося прочитати файл '{path}': {exc}") from exc


def save_report_json(filepath: str | Path, transfers: list[dict], summary: dict) -> None:
    """Зберігає перелік перерозподілів та зведення аудиту у JSON-файл."""
    path = Path(filepath)
    try:
        # Створюємо директорію призначення, якщо її ще немає.
        # exist_ok=True, щоб помилку не вибивало, якщо папка вже існує.
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            # ensure_ascii=False - щоб кирилиця в JSON зберігалась читабельно
            # indent=2 - форматування з відступами, щоб файл було легко прочитати
            json.dump(
                {"summary": summary, "transfers": transfers},
                f,
                ensure_ascii=False,
                indent=2,
            )
    except OSError as exc:
        raise StorageIOError(f"Не вдалося записати JSON-звіт '{path}': {exc}") from exc


def save_report_csv(filepath: str | Path, items: list[LicenseItem]) -> None:
    """Зберігає підсумковий стан усіх об'єктів ліцензій у CSV-файл."""
    path = Path(filepath)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        # newline="" - обов'язкова рекомендація документації Python для модуля csv,
        # щоб у Windows не з'являлися зайві порожні рядки між записами через \r\n.
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)

            # Заголовок таблиці
            writer.writerow([
                "код_ліцензії",
                "відділ",
                "тип",
                "виділено_місць",
                "використано_місць",
                "вільно_місць",
                "дефіцит_місць",
                "втрати_коштів",
            ])

            # Записуємо кожен об'єкт як окремий рядок CSV
            for item in items:
                writer.writerow([
                    item.code,
                    item.department,
                    item.license_type(),
                    item.total_seats,
                    item.used_seats,
                    item.free_seats,
                    item.deficit_seats,
                    item.wasted_cost,
                ])
    except OSError as exc:
        raise StorageIOError(f"Не вдалося записати CSV-звіт '{path}': {exc}") from exc