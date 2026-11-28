[English](README.md) | [Русский](README.ru.md)

# cpython_internals_inspector

A tool for inspecting the internal layout of CPython objects:
dictionaries, their hash tables, entry arrays, and storage modes
(split / unicode / general).

## ⚠️ Limitations

- Works **only with CPython 3.11 - 3.14**.
- Uses **internal headers** (`Include/internal/pycore_dict.h`), which are
  not a stable API. The build is tied to a specific CPython version and may
  break when moving to another minor version.
- Does not support free-threaded builds (`Py_GIL_DISABLED`).

## Installation

```bash
pip install cpython_internals_inspector
```

Building from source requires a local copy of the CPython sources for the
matching version (for `Include/internal`).

## Usage

```python
import cpython_internals_inspector as cii

d = {'timmy': 'red', 'test': 'orange', 'barry': 'green', 'guido': 'blue'}
del d['test']
print(cii.inspect(d))
```

Output:

```
cpython_internals_inspector(dict): {'timmy': 'red', 'barry': 'green', 'guido': 'blue'}
dk_kind_str = UNICODE
ma_keys -> dk_kind = 1
ma_keys -> dk_usable = 1
ma_keys -> dk_nentries = 4
ma_keys -> dk_refcnt = 1

ma_keys -> dk_indices:
+---+-------+
| i |  slot |
+---+-------+
| 0 | EMPTY |
| 1 | 0     |
| 2 | EMPTY |
| 3 | EMPTY |
| 4 | DUMMY |
| 5 | 3     |
| 6 | EMPTY |
| 7 | 2     |
+---+-------+

ma_keys -> entries:
+-----+--------------+----------------+------------------------------------+
| idx | key_from_ptr | value_from_ptr |              comment               |
+-----+--------------+----------------+------------------------------------+
|  0  |    timmy     |      red       | hash_from_key='0x6020858191cff581' |
|  1  |              |                |                                    |
|  2  |    barry     |     green      | hash_from_key='0xdb0bc72ea097ea7f' |
|  3  |    guido     |      blue      | hash_from_key='0xe4e82bb2c0a15025' |
+-----+--------------+----------------+------------------------------------+

ma_values: NULL

indices_elem_size = 1
indices_count = 8
indices_size = 8
entry_type = PyDictUnicodeEntry
entry_size = 16
entries_count = 4
entries_size = 64
total_size = 72
```

## API

- `inspect(obj)` — human-readable report.
- `get_dict_structure(obj)` — dictionary with structure data
  (`ma_keys`, `ma_values`, `extra`, `dk_indices`, `entries`).

## Development

```bash
uv sync --group dev
pre-commit install
pytest
```

## Building wheels locally

To build a wheel for a specific Python version locally, use `cibuildwheel`.
This is the same tool used in CI, so the result matches what gets published.

### Prerequisites

- **Docker** (or Podman) must be running. On Linux, `cibuildwheel`
  builds inside a `manylinux` container by default.
- `cibuildwheel` can be run without installing it globally via `uvx`.

### Build for CPython 3.14 (Linux/macOS)

```bash
CIBW_BUILD="cp314-*" uvx cibuildwheel --output-dir wheelhouse
```

The resulting wheel appears in `wheelhouse/`, e.g.:

```
wheelhouse/cpython_internals_inspector-0.1.0-cp314-cp314-manylinux...whl
```

### Build for another version

Replace the selector to target a different Python version:

```bash
# CPython 3.13
CIBW_BUILD="cp313-*" uvx cibuildwheel --output-dir wheelhouse
```

### Notes

- The `CIBW_BUILD` selector overrides any `build` setting in
  `pyproject.toml`, so only the requested version is built.
- Because the project uses internal CPython headers
  (`Include/internal/pycore_dict.h`), the wheel is tied to the exact
  CPython version it was built against. A wheel built for `cp313`
  will not load in `cp314` and vice versa.

## License

MIT. See [LICENSE](LICENSE).