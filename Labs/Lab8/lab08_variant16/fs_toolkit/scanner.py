from pathlib import Path
import os
import time


def scan_extensionless_files(base_path: Path, min_bytes: int = 0) -> list[dict]:
    if not base_path.exists() or not base_path.is_dir():
        raise ValueError(f"Шлях '{base_path}' не існує або не є директорією.")
    if min_bytes < 0:
        raise ValueError("Мінімальний розмір (--min-bytes) не може бути від'ємним.")

    resolved_root = base_path.resolve()
    matched_files: list[dict] = []

    for item in resolved_root.rglob("*"):
        if not item.is_file():
            continue
        if item.suffix != "":
            continue

        try:
            stat_res = item.stat()
            file_size = stat_res.st_size
            if file_size < min_bytes:
                continue

            octal_permissions = oct(stat_res.st_mode & 0o777)
            is_executable = bool(stat_res.st_mode & 0o111)
            modified_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat_res.st_mtime))

            with item.open("rb") as fh:
                header = fh.read(16)

            if header.startswith(b"#!"):
                file_kind = "script (shebang)"
            elif header.startswith(b"\x7fELF"):
                file_kind = "binary (ELF)"
            elif header.startswith(b"MZ"):
                file_kind = "binary (PE/MZ)"
            else:
                file_kind = "extensionless file"

            matched_files.append({
                "path": item,
                "relative_path": item.relative_to(resolved_root),
                "size_bytes": file_size,
                "size_kb": file_size / 1024.0,
                "modified_at": modified_at,
                "permissions": octal_permissions,
                "executable": is_executable,
                "kind": file_kind,
            })
        except (PermissionError, OSError) as err:
            print(f"Попередження системи: Немає доступу до файлу '{item}': {err}")
            continue

    matched_files.sort(key=lambda rec: (-rec["size_bytes"], str(rec["relative_path"])))
    return matched_files
