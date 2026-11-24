"""Модуль регулярної перевірки та нормалізації вхідних даних записів аудиту."""

import re
from .exceptions import ValidationError

# Попередньо скомпільовані регулярні вирази (re.compile):
# 1) Код ліцензії: 2-4 великі літери, дефіс, 3-6 цифр (наприклад JET-1042)
LICENSE_CODE_RE = re.compile(r"^[A-Z]{2,4}-\d{3,6}$")
# 2) Код підрозділу: 2-20 символів (латиниця, цифри, підкреслення, дефіс)
DEPT_RE = re.compile(r"^[A-Za-z0-9_-]{2,20}$")
# 3) Допустимий тип ліцензії: SUB (підписка) або PERP (безстрокова)
# (?:...) - незахоплююча група, щоб не створювати зайвих підгруп
LICENSE_TYPE_RE = re.compile(r"^(?:SUB|PERP)$")


def normalize_code(raw_code: str) -> str:
    """Перевіряє сирий код ліцензії та нормалізує його до верхнього регістру."""
    # .strip() прибирає пробіли/переноси рядка по краях, .upper() зводить до великих літер
    cleaned = raw_code.strip().upper()
    if not LICENSE_CODE_RE.match(cleaned):
        raise ValidationError(f"Некоректний код ліцензії: '{raw_code}'")
    return cleaned


def normalize_department(raw_dept: str) -> str:
    """Перевіряє назву/код відділу та нормалізує його до верхнього регістру."""
    cleaned = raw_dept.strip().upper()
    if not DEPT_RE.match(cleaned):
        raise ValidationError(f"Некоректний код відділу: '{raw_dept}'")
    return cleaned


def normalize_license_type(raw_type: str | None) -> str:
    """
    Перевіряє та нормалізує тип ліцензії (SUB або PERP).
    Якщо поле не задане (None), повертає SUB за замовчуванням.
    """
    if raw_type is None:
        return "SUB"
    cleaned = raw_type.strip().upper()
    if not LICENSE_TYPE_RE.match(cleaned):
        raise ValidationError(f"Некоректний тип ліцензії: '{raw_type}' (очікується SUB або PERP)")
    return cleaned


def parse_log_line(line: str) -> dict:
    """
    Розбирає рядок вхідного файлу формату:
    DEPT=DEV | CODE=JET-1042 | TOTAL=20 | USED=14 | COST=150.0 [| TYPE=SUB|PERP]

    Повертає словник із нормалізованими та приведеними до потрібних типів полями.
    """
    # Іменовані групи (?P<назва>...) дозволяють звертатися до частин рядка за ключем,
    # а не за крихкими числовими індексами груп.
    # [^|]+? - "ліниве" захоплення до найближчого розділювача '|'.
    # (?:\s*\|\s*TYPE=...)? - опціональний блок типу ліцензії в кінці рядка.
    pattern = re.compile(
        r"^\s*DEPT=(?P<dept>[^|]+?)\s*\|\s*"
        r"CODE=(?P<code>[^|]+?)\s*\|\s*"
        r"TOTAL=(?P<total>-?\d+)\s*\|\s*"
        r"USED=(?P<used>-?\d+)\s*\|\s*"
        r"COST=(?P<cost>-?\d+(?:\.\d+)?)"
        r"(?:\s*\|\s*TYPE=(?P<type>[^|]+?))?\s*$"
    )
    match = pattern.match(line)
    if not match:
        raise ValidationError(f"Порушено формат запису: '{line.strip()}'")

    return {
        "department": normalize_department(match.group("dept")),
        "code": normalize_code(match.group("code")),
        "total_seats": int(match.group("total")),
        "used_seats": int(match.group("used")),
        "unit_cost": float(match.group("cost")),
        "license_type": normalize_license_type(match.group("type")),
    }