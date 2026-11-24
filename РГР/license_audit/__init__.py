"""
Налаштування імпорту мого пакету для інших програм.
Також для імпорту через import * створив список до яких класів-функцій надавати доступ.
"""
from .exceptions import (
    LicenseAuditError,
    LicenseCapacityError,
    StorageIOError,
    ValidationError,
)
from .models import (
    LicenseItem,
    PerpetualLicense,
    SubscriptionLicense,
)
from .optimizer import (
    audit_and_optimize,
    benchmark_audit,
)
from .storage import (
    load_licenses_from_txt,
    save_report_csv,
    save_report_json,
)
#Обробка варіанту імпорту: from license_audit import *
__all__ = [
    "LicenseAuditError",
    "LicenseCapacityError",
    "StorageIOError",
    "ValidationError",
    "LicenseItem",
    "SubscriptionLicense",
    "PerpetualLicense",
    "audit_and_optimize",
    "benchmark_audit",
    "load_licenses_from_txt",
    "save_report_json",
    "save_report_csv",
]