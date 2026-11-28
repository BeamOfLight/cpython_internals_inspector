"""Тесты для модуля cpython_internals_inspector.

Запуск:
    pytest tests/test_cpython_internals_inspector.py -v
"""

import pytest

import cpython_internals_inspector as cii


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

KIND_MAP = {0: "GENERAL", 1: "UNICODE", 2: "SPLIT"}


def get_kind(structure: dict) -> str:
    """Вернуть строковое представление dk_kind из структуры."""
    kind = structure["ma_keys"]["dk_kind"]
    if isinstance(kind, str):
        return kind
    return KIND_MAP.get(kind, "UNKNOWN")


def get_entries(structure: dict) -> list:
    return structure["ma_keys"]["entries"]


def get_indices(structure: dict) -> list:
    return structure["ma_keys"]["dk_indices"]


def get_values(structure: dict):
    return structure.get("ma_values")


def has_dummy(structure: dict) -> bool:
    return -2 in get_indices(structure)


def count_dummy(structure: dict) -> int:
    return get_indices(structure).count(-2)


# ---------------------------------------------------------------------------
# 1. dict(one=1) — unicode-ключи, combined
# ---------------------------------------------------------------------------


def test_dict_from_kwargs_single_unicode_key():
    d = dict(one=1)
    s = cii.get_structure(d)

    assert get_kind(s) == "UNICODE"
    assert s["ma_keys"]["dk_nentries"] == 1
    assert not has_dummy(s)
    assert get_values(s) is None  # combined — ma_values отсутствует

    entries = get_entries(s)
    assert len(entries) == 1
    assert entries[0]["key_from_ptr"] == "one"
    assert entries[0]["value_from_ptr"] == 1


# ---------------------------------------------------------------------------
# 2. {1: 1} — нестроковый ключ, general
# ---------------------------------------------------------------------------


def test_dict_with_int_key_general():
    d = {1: 1}
    s = cii.get_structure(d)

    assert get_kind(s) == "GENERAL"
    assert s["ma_keys"]["dk_nentries"] == 1
    assert not has_dummy(s)

    entries = get_entries(s)
    assert len(entries) == 1
    assert entries[0]["key_from_ptr"] == 1
    assert entries[0]["value_from_ptr"] == 1
    # hash для int 1 равен 1
    assert entries[0]["hash"] == 1


# ---------------------------------------------------------------------------
# 3. {'a': 1, 'b': 2} — unicode, combined, без удалений
# ---------------------------------------------------------------------------


def test_dict_two_unicode_keys_no_deletions():
    d = {"a": 1, "b": 2}
    s = cii.get_structure(d)

    assert get_kind(s) == "UNICODE"
    assert s["ma_keys"]["dk_nentries"] == 2
    assert not has_dummy(s)

    entries = get_entries(s)
    keys = [e["key_from_ptr"] for e in entries]
    values = [e["value_from_ptr"] for e in entries]
    assert keys == ["a", "b"]
    assert values == [1, 2]


# ---------------------------------------------------------------------------
# 4–6. Удаления в словарях с unicode-ключами: DUMMY должен присутствовать
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "keys",
    [
        ["k_a", "k_b", "k_c", "k_d", "k_e"],
        ["k_a", "k_b", "k_c", "k_d"],
        ["k_a", "k_b", "k_c", "k_d", "k_e", "k_f"],
    ],
)
def test_dict_after_deletion_has_dummy(keys):
    d = {k: i for i, k in enumerate(keys)}
    del d["k_b"]
    s = cii.get_structure(d)

    assert get_kind(s) == "UNICODE"
    assert has_dummy(s), "после удаления в dk_indices должен быть DUMMY"

    entries = get_entries(s)
    entry_keys = [e["key_from_ptr"] for e in entries if e is not None]
    assert "k_b" not in entry_keys, "удалённый ключ не должен быть в entries"


# ---------------------------------------------------------------------------
# 7. Пустой словарь
# ---------------------------------------------------------------------------


def test_empty_dict():
    d = {}
    s = cii.get_structure(d)

    assert get_kind(s) == "UNICODE"
    assert s["ma_keys"]["dk_nentries"] == 0
    assert get_entries(s) == []
    assert not has_dummy(s)


# ---------------------------------------------------------------------------
# 8. __dict__ экземпляра — split-режим
# ---------------------------------------------------------------------------


class MyClass:
    def __init__(self, a, b, c, d, e):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e


def test_instance_dict_split_mode():
    obj = MyClass(1, 2, 3, 4, 5)
    d = vars(obj)
    s = cii.get_structure(d)

    assert get_kind(s) == "SPLIT"
    assert s["ma_keys"]["dk_nentries"] >= 5
    assert get_values(s) is not None, "для SPLIT ma_values должен быть списком"

    entries = get_entries(s)
    entry_keys = [e["key_from_ptr"] for e in entries if e is not None]
    for name in ("a", "b", "c", "d", "e"):
        assert name in entry_keys

    values = get_values(s)
    for value in (1, 2, 3, 4, 5):
        assert value in values


# ---------------------------------------------------------------------------
# 9. Не-dict объект → TypeError (и для inspect, и для get_structure)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("obj", [1, "string", [1, 2], object()])
def test_inspect_non_dict_raises(obj):
    with pytest.raises(TypeError):
        cii.inspect(obj)


@pytest.mark.parametrize("obj", [1, "string", [1, 2], object()])
def test_get_structure_non_dict_raises(obj):
    with pytest.raises(TypeError):
        cii.get_structure(obj)


# ---------------------------------------------------------------------------
# 10. Хэш: для GENERAL — int, для UNICODE — считается в inspect
# ---------------------------------------------------------------------------


def test_inicode_no_hash():
    d = {"timmy": "red"}
    s = cii.get_structure(d)
    entries = get_entries(s)
    assert "hash" not in entries[0]


def test_general_hash_is_int():
    d2 = {42: "answer"}
    s2 = cii.get_structure(d2)
    entries = get_entries(s2)
    assert isinstance(entries[0]["hash"], int)


def test_inspect_hash_is_hex_format():
    d = {"timmy": "red", "barry": "green", "guido": "blue"}
    out = cii.inspect(d)
    assert "hash_from_key='0x" in out, (
        f"хэш должен выводиться в hex-формате, вывод:\n{out}"
    )


# ---------------------------------------------------------------------------
# 11. Размеры: проверка через структуру и через inspect
# ---------------------------------------------------------------------------


def test_structure_sizes():
    d = {"a": 1, "b": 2, "c": 3}
    s = cii.get_structure(d)
    keys = s["ma_keys"]

    dk_size = 1 << keys["dk_log2_size"]
    assert dk_size >= keys["dk_nentries"]
    assert len(get_indices(s)) == dk_size


def test_inspect_headers_contain_sizes():
    d = {"a": 1, "b": 2, "c": 3}
    out = cii.inspect(d)
    for field in (
        "indices_size =",
        "entries_size =",
        "total_size =",
    ):
        assert field in out, f"отсутствует поле {field!r}, вывод:\n{out}"


# ---------------------------------------------------------------------------
# 12. Порядок ключей сохраняется (combined-режим)
# ---------------------------------------------------------------------------


def test_insertion_order_preserved():
    d = {"first": 1, "second": 2, "third": 3}
    s = cii.get_structure(d)
    entry_keys = [e["key_from_ptr"] for e in get_entries(s) if e is not None]
    assert entry_keys == ["first", "second", "third"]


# ---------------------------------------------------------------------------
# 13. Повторные удаления оставляют DUMMY
# ---------------------------------------------------------------------------


def test_multiple_deletions_leave_multiple_dummy():
    d = {k: i for i, k in enumerate("abcdefgh")}
    del d["b"]
    del d["d"]
    del d["f"]
    s = cii.get_structure(d)
    assert count_dummy(s) >= 3


# ---------------------------------------------------------------------------
# 14. Большой словарь — размер элемента индекса
# ---------------------------------------------------------------------------


def test_large_dict_index_element_size():
    d = {f"k{i}": i for i in range(300)}
    s = cii.get_structure(d)
    keys = s["ma_keys"]
    dk_size = 1 << keys["dk_log2_size"]

    # Вычисляем размер элемента по dk_size (как в C)
    if dk_size <= 0xFF:
        elem_size = 1
    elif dk_size <= 0xFFFF:
        elem_size = 2
    elif dk_size <= 0xFFFFFFFF:
        elem_size = 4
    else:
        elem_size = 8

    assert elem_size >= 2, (
        f"для 300 ключей ожидался размер элемента индекса >= 2, "
        f"получено {elem_size} (dk_size={dk_size})"
    )


# ---------------------------------------------------------------------------
# 15. Проверка inspect: общие секции и соответствие структуре
# ---------------------------------------------------------------------------


def assert_common_sections(output: str) -> None:
    assert isinstance(output, str)
    assert output, "inspect() вернул пустую строку"
    assert "dk_kind = " in output, "отсутствует секция dk_kind"
    assert "dk_indices:" in output, "отсутствует содержимое dk_indices"
    assert "entries:" in output, "отсутствует содержимое entries"


@pytest.mark.parametrize(
    "d,expected_kind",
    [
        (dict(one=1), "UNICODE"),
        ({1: 1}, "GENERAL"),
        ({"a": 1, "b": 2}, "UNICODE"),
        ({}, "UNICODE"),
    ],
)
def test_inspect_kind_matches_structure(d, expected_kind):
    s = cii.get_structure(d)
    assert get_kind(s) == expected_kind

    out = cii.inspect(d)
    assert_common_sections(out)
    assert f"dk_kind_str = {expected_kind}" in out


def test_inspect_after_deletion_has_dummy():
    d = dict(a=1, b=2, c=3)
    del d["b"]
    s = cii.get_structure(d)
    assert has_dummy(s)
    out = cii.inspect(d)
    assert "DUMMY" in out


def test_inspect_split_shows_values():
    obj = MyClass(1, 2, 3, 4, 5)
    d = vars(obj)
    s = cii.get_structure(d)
    assert get_kind(s) == "SPLIT"

    out = cii.inspect(d)
    assert "SPLIT" in out
    for value in (1, 2, 3, 4, 5):
        assert str(value) in out
