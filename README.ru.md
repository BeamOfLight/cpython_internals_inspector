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
cpython_internals_inspector(dict): {'timmy': 'red', 'barry': 'green'}
ma_keys -> dk_kind = UNICODE
ma_keys -> dk_usable = 3
ma_keys -> dk_nentries = 2
ma_keys -> dk_indices:
   0: EMPTY    1: 1        2: EMPTY    3: EMPTY    4: EMPTY    5: EMPTY    6: EMPTY    7: 0

ma_keys -> entries:
   0: PyDictUnicodeEntry(key_from_ptr=timmy, value_from_ptr=red) 	# hash_from_key='0xf2210736e2219fff'
   1: PyDictUnicodeEntry(key_from_ptr=barry, value_from_ptr=green) 	# hash_from_key='0x9780a006073911a9'

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

## Локальная сборка

Для локальной сборки wheel-пакета под конкретную версию Python используйте `cibuildwheel`. Это тот же инструмент, что применяется в CI, поэтому результат будет соответствовать тому, что в итоге публикуется.

### Предварительные требования

- Должен быть запущен **Docker** (или Podman). В Linux `cibuildwheel`
по умолчанию выполняет сборку внутри контейнера `manylinux`.
- `cibuildwheel` можно запустить без глобальной установки — с помощью `uvx`.

### Сборка для CPython 3.14 (Linux/macOS)

```bash
CIBW_BUILD="cp314-*" uvx cibuildwheel --output-dir wheelhouse
```

Полученный wheel-файл появляется в директории `wheelhouse/`, например:

```
wheelhouse/cpython_internals_inspector-0.1.0-cp314-cp314-manylinux...whl
```

### Сборка для другой версии

Подставьте нужную версию Python:

```bash
# CPython 3.13
CIBW_BUILD="cp313-*" uvx cibuildwheel --output-dir wheelhouse
```

### Примечания

- Селектор `CIBW_BUILD` переопределяет любые настройки `build` в файле `pyproject.toml`, поэтому собирается только запрошенная версия.
- Поскольку проект использует внутренние заголовочные файлы CPython (`Include/internal/pycore_dict.h`), собранный пакет (wheel) оказывается привязанным к конкретной версии CPython, для которой он был создан. Пакет, собранный для `cp313`, не будет работать в `cp314`, и наоборот.

## Лицензия

MIT. См. [LICENSE](LICENSE).