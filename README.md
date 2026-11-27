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

d = {'timmy': 'red', 'barry': 'green'}
print(cii.inspect(d))
```

Output:

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