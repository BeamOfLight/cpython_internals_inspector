[English](CONTRIBUTING.md) | [Русский](CONTRIBUTING.ru.md)

# Contributing

Thank you for your interest in the project!

## Reporting bugs

Open an Issue and include:
- the CPython version (`python --version`);
- OS and architecture;
- a minimal reproducible example;
- expected and actual behaviour.

Because the project works with internal CPython structures,
**always specify the exact version** (e.g. `3.14.0`, not `3.14`):
structure layout may change between patch releases.

## Pull Requests

1. Fork the repository and create a branch from `main`.
2. Install dev dependencies:
   ```bash
   uv sync --group dev
   pre-commit install
   ```
3. Make your changes and add tests.
4. Make sure the following pass:
   ```bash
   pre-commit run --all-files
   pytest
   ```
5. Open a PR with a description of the changes.

## Code style

- Python: `ruff` (linter and formatter), `mypy` (types).
- C: follow CPython style (`Objects/dictobject.c`), 4-space indentation,
  braces on a new line for functions.

## Tests

Tests live in `tests/`. For the C extension, tests run against the built
module; make sure `python setup.py build_ext --inplace` has been run
before `pytest`.