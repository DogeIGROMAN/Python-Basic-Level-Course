import sys
import time
from pathlib import Path

_ROOT_DIR = Path(__file__).resolve().parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

from fs_toolkit import scan_extensionless_files, print_no_ext_report


def print_usage_help() -> None:
    print("ВИКОРИСТАННЯ:")
    print("    python cli_main.py --path <каталог> --min-bytes <байт>")
    print("    python cli_main.py --help")
    print()
    print("ПАРАМЕТРИ:")
    print("    --path <dir>     : Шлях до цільового каталогу (обов'язковий).")
    print("    --min-bytes <n>  : Мінімальний розмір файлу у байтах (обов'язковий, ціле >= 0).")
    print("    --help, -h       : Вивести цю довідку та завершити роботу.")


def parse_cli_arguments(args_list: list[str]) -> dict:
    if "--help" in args_list[1:] or "-h" in args_list[1:]:
        print_usage_help()
        sys.exit(0)

    config = {
        "path": None,
        "min_bytes": None,
    }

    i = 1
    while i < len(args_list):
        arg = args_list[i]
        if arg == "--path":
            if i + 1 >= len(args_list):
                print("Помилка: Після '--path' потрібно вказати шлях до каталогу.", file=sys.stderr)
                sys.exit(2)
            config["path"] = Path(args_list[i + 1]).resolve()
            i += 2
        elif arg == "--min-bytes":
            if i + 1 >= len(args_list):
                print("Помилка: Після '--min-bytes' потрібно вказати ціле число.", file=sys.stderr)
                sys.exit(2)
            try:
                val = int(args_list[i + 1])
            except ValueError:
                print("Помилка: '--min-bytes' має бути цілим числом.", file=sys.stderr)
                sys.exit(2)
            if val < 0:
                print("Помилка: '--min-bytes' не може бути від'ємним.", file=sys.stderr)
                sys.exit(2)
            config["min_bytes"] = val
            i += 2
        else:
            print(f"Помилка: Невідомий параметр '{arg}'.", file=sys.stderr)
            print_usage_help()
            sys.exit(2)

    if config["path"] is None:
        print("Помилка: Обов'язковий параметр '--path' не вказано.", file=sys.stderr)
        print_usage_help()
        sys.exit(2)

    if config["min_bytes"] is None:
        print("Помилка: Обов'язковий параметр '--min-bytes' не вказано.", file=sys.stderr)
        print_usage_help()
        sys.exit(2)

    return config


def main() -> None:
    cli_config = parse_cli_arguments(sys.argv)
    target_dir = cli_config["path"]
    min_bytes = cli_config["min_bytes"]

    t_start = time.perf_counter()
    try:
        results = scan_extensionless_files(base_path=target_dir, min_bytes=min_bytes)
    except ValueError as val_err:
        print(f"Помилка параметрів: {val_err}", file=sys.stderr)
        sys.exit(2)
    except Exception as exc:
        print(f"Помилка виконання: {exc}", file=sys.stderr)
        sys.exit(1)

    print_no_ext_report(results, min_bytes, str(target_dir))
    elapsed_ms = (time.perf_counter() - t_start) * 1000.0
    print(f"Операцію завершено за {elapsed_ms:.3f} мс.")
    sys.exit(0)


if __name__ == "__main__":
    main()
