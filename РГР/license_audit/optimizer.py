"""Модуль аудиту використання ліцензій, їх перерозподілу та заміру продуктивності."""

import time
from .models import LicenseItem


def audit_and_optimize(items: list[LicenseItem]) -> tuple[list[dict], dict]:
    """
    Виконує аудит списку ліцензій і жадібний перерозподіл вільних місць
    на покриття дефіциту в межах однакового коду ліцензії (code).

    Повертає кортеж (transfers, summary):
    transfers - список словників із виконаними переміщеннями місць;
    summary - словник підсумкових метрик після оптимізації.
    """
    # Сортуємо згідно з __lt__ у LicenseItem: спочатку за найбільшою
    # вартістю невикористаних місць (wasted_cost), далі за code.
    sorted_items = sorted(items)
    transfers: list[dict] = []

    # Групуємо записи за кодом ліцензії, щоб не змішувати різні продукти
    by_code: dict[str, list[LicenseItem]] = {}
    for item in sorted_items:
        by_code.setdefault(item.code, []).append(item)

    for code, group in by_code.items():
        # Донори -відділи з надлишком (free_seats > 0)
        # ресивери - відділи з нестачею (deficit_seats > 0)
        donors = [x for x in group if x.free_seats > 0]
        receivers = [x for x in group if x.deficit_seats > 0]

        # Метод двох покажчиків по відсортованих списках донорів і ресиверів
        d_idx, r_idx = 0, 0
        while d_idx < len(donors) and r_idx < len(receivers):
            donor = donors[d_idx]
            receiver = receivers[r_idx]

            # Жадібний крок: перекидаємо максимум можливого за поточну пару,
            # не виходячи за межі вільних місць донора та дефіциту ресивера.
            movable = min(donor.free_seats, receiver.deficit_seats)

            if movable > 0:
                # Змінюємо total_seats через властивість @property
                donor.total_seats -= movable
                receiver.total_seats += movable

                transfers.append(
                    {
                        "code": code,
                        "from_department": donor.department,
                        "to_department": receiver.department,
                        "seats": movable,
                        # Оцінка уникнутих витрат на докупівлю аналогічних місць
                        "saved_new_purchase_cost": round(movable * receiver.unit_cost, 2),
                    }
                )

            # Переходимо до наступного донора, якщо поточний вичерпав вільні місця
            if donor.free_seats == 0:
                d_idx += 1
            # Переходимо до наступного ресивера, якщо його дефіцит уже закрито
            if receiver.deficit_seats == 0:
                r_idx += 1

    # Формуємо зведення для консолі та JSON-звіту
    summary = {
        "total_records": len(sorted_items),
        "total_allocated_seats": sum(x.total_seats for x in sorted_items),
        "total_used_seats": sum(x.used_seats for x in sorted_items),
        "remaining_deficit_seats": sum(x.deficit_seats for x in sorted_items),
        "remaining_wasted_cost": round(sum(x.wasted_cost for x in sorted_items), 2),
        "reallocated_seats": sum(t["seats"] for t in transfers),
        "avoided_extra_cost": round(sum(t["saved_new_purchase_cost"] for t in transfers), 2),
    }
    return transfers, summary


def benchmark_audit(items: list[LicenseItem], repeat: int = 100) -> float:
    """
    Вимірює середній час одного виклику audit_and_optimize у мілісекундах.
    Використовує time.perf_counter() як найточніший таймер для вимірювання інтервалів.
    """
    start = time.perf_counter()
    for _ in range(repeat):
        audit_and_optimize(items)
    elapsed_ms = ((time.perf_counter() - start) / repeat) * 1000
    return round(elapsed_ms, 4)