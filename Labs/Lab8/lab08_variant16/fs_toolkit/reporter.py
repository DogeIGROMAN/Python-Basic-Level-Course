def print_no_ext_report(file_records: list[dict], min_bytes: int, search_root: str) -> None:
    header_sep = "=" * 96
    row_sep = "-" * 96

    print("\n" + header_sep)
    print(f"{'NO_EXT_SCAN — ЗВІТ ПОШУКУ ФАЙЛІВ БЕЗ РОЗШИРЕНЬ':^96}")
    print(header_sep)
    print(f"Базова директорія пошуку : {search_root}")
    print(f"Мінімальний розмір файлу  : {min_bytes} байт")
    print(row_sep)
    print(
        f"| {'№':^3} | {'Файл':<26} | {'Розмір (Б)':>10} | "
        f"{'Права':^7} | {'Exec':^4} | {'Тип файлу':<24} |"
    )
    print(row_sep)

    total_bytes = 0
    for idx, rec in enumerate(file_records, start=1):
        total_bytes += rec["size_bytes"]
        rel_str = str(rec["relative_path"])
        if len(rel_str) > 26:
            rel_str = f"...{rel_str[-23:]}"
        exec_label = "YES" if rec["executable"] else "NO"
        print(
            f"| {idx:^3d} | {rel_str:<26} | {rec['size_bytes']:>10d} | "
            f"{rec['permissions']:^7} | {exec_label:^4} | {rec['kind']:<24} |"
        )

    print(header_sep)
    total_kb = total_bytes / 1024.0
    print(f"  Всього знайдено файлів без розширення: {len(file_records):>6d}")
    print(f"  Сумарний обсяг вибірки:               {total_bytes:>6d} Б ({total_kb:.2f} КБ)")
    print(header_sep + "\n")
