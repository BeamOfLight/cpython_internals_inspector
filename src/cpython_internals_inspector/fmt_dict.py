"""Форматирование данных, полученных из get_dict_structure()."""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------


def _format_value(value: Any) -> str:
    """Вернуть repr(value), кроме str — для строк выводим содержимое без кавычек."""
    if value is None:
        return "NULL"
    if isinstance(value, str):
        return f"'{value}'"
    return f"'{repr(value)}'"


def _format_hash(hash_value: Any) -> str:
    """Хэш может быть int (из PyLong) или str (если уже hex)."""
    if isinstance(hash_value, int):
        # Приводим к беззнаковому виду, как в C-версии (size_t)
        return f"0x{hash_value & 0xFFFFFFFFFFFFFFFF:x}"
    return str(hash_value)


def _kind_to_str(kind: Any) -> str:
    """dk_kind может быть строкой (GENERAL/UNICODE/SPLIT) или числом."""
    if isinstance(kind, str):
        return kind
    return {0: "GENERAL", 1: "UNICODE", 2: "SPLIT"}.get(kind, "UNKNOWN")


# ---------------------------------------------------------------------------
# Секции вывода
# ---------------------------------------------------------------------------


def _show_dict_keys_headers(keys: dict) -> str:
    kind = _kind_to_str(keys["dk_kind"])
    lines = [
        f"ma_keys -> dk_kind = {kind}",
        f"ma_keys -> dk_usable = {keys['dk_usable']}",
        f"ma_keys -> dk_nentries = {keys['dk_nentries']}",
    ]
    return "\n".join(lines) + "\n"


def _show_dict_key_indices(keys: dict) -> str:
    dk_log2_size = keys["dk_log2_size"]
    dk_size = 1 << dk_log2_size
    indices = keys["dk_indices"]

    # На случай, если C-функция вернула меньше элементов — добиваем EMPTY
    if len(indices) < dk_size:
        indices = list(indices) + [-1] * (dk_size - len(indices))

    parts: list[str] = ["ma_keys -> dk_indices:"]
    for i in range(dk_size):
        if i % 8 == 0:
            parts.append("\n")
        val = indices[i]
        if val == -1:
            parts.append(f"{i:4d}: EMPTY ")
        elif val == -2:
            parts.append(f"{i:4d}: DUMMY ")
        else:
            parts.append(f"{i:4d}: {val:<5d} ")
    parts.append("\n\n")
    return "".join(parts)


def _show_dict_entry(entry_type: str, entry: dict[str, Any]) -> str:
    dict_items_str = ", ".join([f"{key}={value}" for key, value in entry.items()])
    result = f"{entry_type}({dict_items_str})"
    if entry_type == "PyDictUnicodeEntry":
        result += f" \t# hash_from_key='{_format_hash(hash(entry['key_from_ptr']))}'"
    return result


def _show_dict_key_entries(keys: dict, extra: dict) -> str:
    entries = keys["entries"]
    header = "ma_keys -> entries:\n"
    entry_type = extra["entry_type"]

    lines: list[str] = []
    for i, entry in enumerate(entries):
        if entry is None:
            lines.append(f"{i:4d}: NULL")
            continue
        lines.append(f"{i:4d}: {_show_dict_entry(entry_type, entry)}")

    return header + "\n".join(lines) + "\n\n"


def _show_dict_values(ma_values: list | None, nentries: int) -> str:
    if ma_values is None:
        return "ma_values: NULL\n\n"
    parts: list[str] = ["ma_values: "]
    for i in range(nentries):
        parts.append("\n")
        if i >= len(ma_values) or ma_values[i] is None:
            parts.append(f"{i:4d}: NULL")
            continue
        parts.append(f"{i:4d}: '{_format_value(ma_values[i])}'")
    parts.append("\n\n")
    return "".join(parts)


def _show_dict_keys_stat(keys: dict) -> str:
    dk_size = 1 << keys["dk_log2_size"]
    idx_elem_size = _index_elem_size(keys)
    indices_size = 1 << keys["dk_log2_index_bytes"]
    nentries = keys["dk_nentries"]

    if _kind_to_str(keys["dk_kind"]) == "GENERAL":
        size_per_entry = 24  # sizeof(PyDictKeyEntry) на 64-битной платформе
    else:
        size_per_entry = 16  # sizeof(PyDictUnicodeEntry) на 64-битной платформе
    entries_size = nentries * size_per_entry
    total_size = indices_size + entries_size

    return (
        f"indices_size = {dk_size} * {idx_elem_size} = {indices_size}\n"
        f"entries_size = {nentries} * {size_per_entry} = {entries_size}\n"
        f"total_size = {total_size}\n"
    )


def _index_elem_size(keys: dict) -> int:
    dk_size = 1 << keys["dk_log2_size"]
    if dk_size <= 0xFF:
        return 1
    if dk_size <= 0xFFFF:
        return 2
    if dk_size <= 0xFFFFFFFF:
        return 4
    return 8


# ---------------------------------------------------------------------------
# Публичная точка входа
# ---------------------------------------------------------------------------


def inspect_dict(structure: dict) -> str:
    """Сформировать человекочитаемый отчёт из словаря get_dict_structure()."""
    keys = structure["ma_keys"]
    extra = structure["extra"]
    ma_values = structure.get("ma_values")

    parts: list[str] = []
    parts.append(
        f"cpython_internals_inspector(dict): {structure.get('repr', '<dict>')}\n"
    )
    parts.append(_show_dict_keys_headers(keys))
    parts.append(_show_dict_key_indices(keys))
    parts.append(_show_dict_key_entries(keys, extra))
    parts.append(_show_dict_values(ma_values, keys["dk_nentries"]))
    parts.append(_show_dict_keys_stat(keys))
    return "".join(parts)
