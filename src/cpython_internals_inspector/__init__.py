"""cpython-internals-inspector — диагностика внутреннего устройства объектов CPython."""

from ._core import get_structure  # type: ignore[import-not-found]
from .fmt_dict import inspect_dict


def inspect(obj):
    """Показать расширенную информацию о внутреннем устройстве объекта."""
    if isinstance(obj, dict):
        structure = get_structure(obj)
        structure["repr"] = repr(obj)
        return inspect_dict(structure)
    raise TypeError(f"inspect() does not support type '{type(obj).__name__}' yet")


__all__ = ["inspect", "get_structure"]
