"""Форматирование данных, полученных из get_dict_structure()."""

from __future__ import annotations

from typing import Any, Final, TypedDict

from prettytable import PrettyTable


MAX_TABLE_VALUE_LEN: Final = 20
MIN_COLUMN_HEIGHT: Final = 8

DKIX_EMPTY: Final = -1
DKIX_DUMMY: Final = -2

KIND_NAMES: Final[dict[int, str]] = {
    0: "GENERAL",
    1: "UNICODE",
    2: "SPLIT",
}

ENTRY_TYPE_KEY: Final = "PyDictKeyEntry"
ENTRY_TYPE_UNICODE: Final = "PyDictUnicodeEntry"


# ---------------------------------------------------------------------------
# Типы структуры, возвращаемой get_dict_structure()
# ---------------------------------------------------------------------------

class Entry(TypedDict, total=False):
    hash: int
    key_from_ptr: Any
    value_from_ptr: Any


class MaKeys(TypedDict):
    dk_refcnt: int
    dk_kind: int
    dk_usable: int
    dk_nentries: int
    dk_log2_size: int
    dk_log2_index_bytes: int
    dk_indices: list[int]
    entries: list[Entry | None]


class Extra(TypedDict):
    entry_type: str
    entry_size: int
    idx_elem_size: int


class DictStructure(TypedDict):
    ma_keys: MaKeys
    extra: Extra
    ma_values: list[Any] | None
    repr: str


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def _cut_long_str(text: str, max_length: int = MAX_TABLE_VALUE_LEN) -> str:
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text


def _format_value(value: Any) -> str:
    """Вернуть repr(value), кроме str — для строк выводим содержимое без кавычек."""
    if value is None:
        return "NULL"
    if isinstance(value, str):
        return value
    return repr(value)


def _format_hash(hash_value: int) -> str:
    """Привести хэш к беззнаковому hex-виду, как в C-версии (size_t)."""
    return f"0x{hash_value & 0xFFFFFFFFFFFFFFFF:x}"


def _kind_to_str(kind: int) -> str:
    return KIND_NAMES.get(kind, "UNKNOWN")


# ---------------------------------------------------------------------------
# Секции вывода
# ---------------------------------------------------------------------------

def _show_dict_keys_headers(keys: MaKeys) -> str:
    kind = _kind_to_str(keys["dk_kind"])
    return (
        f"dk_kind_str = {kind}\n"
        f"ma_keys -> dk_kind = {keys['dk_kind']}\n"
        f"ma_keys -> dk_usable = {keys['dk_usable']}\n"
        f"ma_keys -> dk_nentries = {keys['dk_nentries']}\n"
        f"ma_keys -> dk_refcnt = {keys['dk_refcnt']}\n"
        "\n"
    )


def _format_index_slot(val: int) -> str:
    if val == DKIX_EMPTY:
        return f"EMPTY"
    if val == DKIX_DUMMY:
        return f"DUMMY"
    return f"{val:<5d}"


def _show_dict_key_indices(keys: MaKeys) -> str:
    dk_size = 1 << keys["dk_log2_size"]
    indices = keys["dk_indices"]

    table = PrettyTable()
    column_height = max(MIN_COLUMN_HEIGHT, dk_size >> 2)
    columns_cnt = dk_size // column_height

    for col_idx in range(columns_cnt):
        idx_from = column_height * col_idx
        idx_to = column_height * (col_idx + 1)
        table.add_column("i", range(idx_from, idx_to))
        table.add_column("slot", list(map(_format_index_slot, indices[idx_from:idx_to])))

    return f"ma_keys -> dk_indices:\n{table}\n\n"


def _entries_field_names(entry_type: str) -> list[str]:
    if entry_type == ENTRY_TYPE_KEY:
        return ["idx", "hash", "key_from_ptr", "value_from_ptr"]
    if entry_type == ENTRY_TYPE_UNICODE:
        return ["idx", "key_from_ptr", "value_from_ptr", "comment"]
    raise RuntimeError(f"Unknown entry_type: {entry_type}")


def _entry_row(i: int, entry: Entry, entry_type: str) -> list[Any]:
    key = _cut_long_str(_format_value(entry.get("key_from_ptr")))
    value = _cut_long_str(_format_value(entry.get("value_from_ptr")))

    if entry_type == ENTRY_TYPE_KEY:
        return [i, _format_hash(entry["hash"]), key, value]

    if entry_type == ENTRY_TYPE_UNICODE:
        key_obj = entry.get("key_from_ptr")
        comment = f"hash_from_key='{_format_hash(hash(key_obj))}'"
        return [i, key, value, comment]

    raise RuntimeError(f"Unknown entry_type: {entry_type}")


def _show_dict_key_entries(keys: MaKeys, extra: Extra) -> str:
    entry_type = extra["entry_type"]
    table = PrettyTable(field_names=_entries_field_names(entry_type))

    empty_row_len = len(table.field_names) - 1
    for i, entry in enumerate(keys["entries"]):
        if entry is None:
            table.add_row([i] + [""] * empty_row_len)
        else:
            table.add_row(_entry_row(i, entry, entry_type))

    return f"ma_keys -> entries:\n{table}\n\n"


def _show_dict_values(ma_values: list[Any] | None, nentries: int) -> str:
    if ma_values is None:
        return "ma_values: NULL\n\n"

    table = PrettyTable(field_names=("i", "value_from_ptr"))
    for i in range(nentries):
        table.add_row((i, _format_value(ma_values[i])))
    return f"ma_values:\n{table}\n\n"


def _show_dict_stat(keys: MaKeys, extra: Extra) -> str:
    idx_elem_size = extra["idx_elem_size"]
    entry_type = extra["entry_type"]
    entry_size = extra["entry_size"]

    dk_size = 1 << keys["dk_log2_size"]
    indices_size = 1 << keys["dk_log2_index_bytes"]
    nentries = keys["dk_nentries"]
    entries_size = nentries * entry_size
    total_size = indices_size + entries_size

    return (
        f"indices_elem_size = {idx_elem_size}\n"
        f"indices_count = {dk_size}\n"
        f"indices_size = {indices_size}\n"
        f"entry_type = {entry_type}\n"
        f"entry_size = {entry_size}\n"
        f"entries_count = {nentries}\n"
        f"entries_size = {entries_size}\n"
        f"total_size = {total_size}\n"
    )


# ---------------------------------------------------------------------------
# Публичная точка входа
# ---------------------------------------------------------------------------

def inspect_dict(structure: DictStructure) -> str:
    """Сформировать человекочитаемый отчёт из словаря get_dict_structure()."""
    keys = structure["ma_keys"]
    extra = structure["extra"]
    ma_values = structure.get("ma_values")

    parts = [
        f"cpython_internals_inspector(dict): {structure.get('repr', '<dict>')}\n",
        _show_dict_keys_headers(keys),
        _show_dict_key_indices(keys),
        _show_dict_key_entries(keys, extra),
        _show_dict_values(ma_values, keys["dk_nentries"]),
        _show_dict_stat(keys, extra),
    ]
    return "".join(parts)
