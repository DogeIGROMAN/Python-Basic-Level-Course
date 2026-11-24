#Файл з власною ієрархією винятків
#Усі помилки системи наслідуються від LicenseAuditError, щоб на рівні CLI можна було чітко перехоплювати бізнес-помилки
# й показувати зрозуміле повідомлення замість сирого трейсбеку.
class LicenseAuditError(Exception):
    """Базовий виняток системи обліку та аудиту ліцензій."""


class ValidationError(LicenseAuditError):
    """Помилка формату або нормалізації вхідних даних."""


class LicenseCapacityError(LicenseAuditError):
    """Помилка кількості ліцензій або перевищення лімітів."""


class StorageIOError(LicenseAuditError):
    """Помилка читання або запису файлів даних/звітів."""