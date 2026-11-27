[English](README.md) | [Русский](README.ru.md)

# cpython_internals_inspector

Инструмент для просмотра внутреннего устройства объектов CPython:
словарей, их хеш-таблиц, массивов записей и режимов хранения
(split / unicode / general).

## ⚠️ Ограничения

- Работает **только с CPython 3.13 и 3.14**.
- Использует **внутренние заголовки** (`Include/internal/pycore_dict.h`),
  которые не являются стабильным API. Сборка привязана к конкретной
  версии CPython и может сломаться при переходе на другую минорную версию.
- Не поддерживает free-threaded сборки (`Py_GIL_DISABLED`).

## Установка

```bash
pip install cpython_internals_inspector
```

Для сборки из исходников требуется локальная копия исходников CPython
соответствующей версии (для `Include/internal`).

## Использование

```python
import cpython_internals_inspector as cii

d = {'timmy': 'red', 'barry': 'green'}
print(cii.inspect(d))
```

Вывод:

```
Memory_analyzer(dict): {'timmy': 'red', 'barry': 'green'}
ma_keys -> dk_kind = UNICODE
ma_keys -> dk_usable = 5
ma_keys -> dk_nentries = 2
ma_keys -> dk_indices:
   0: EMPTY    1: 1        2: EMPTY    3: EMPTY
   4: EMPTY    5: 0        6: EMPTY    7: EMPTY

ma_keys -> entries:
   0: {key='timmy', value='red'} 	# hash_from_key='0x...'
   1: {key='barry', value='green'} 	# hash_from_key='0x...'

ma_values: NULL

indices_size = 8 * 1 = 8
entries_size = 2 * 16 = 32
total_size = 40
```

## API

- `inspect(obj)` — человекочитаемый отчёт.
- `get_dict_structure(obj)` — словарь с данными о структуре
  (`ma_keys`, `ma_values`, `extra`, `dk_indices`, `entries`).

## Разработка

```bash
uv sync --group dev
pre-commit install
pytest
```

## Лицензия

MIT. См. [LICENSE](LICENSE).