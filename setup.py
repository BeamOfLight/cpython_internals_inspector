# setup.py
import sys
import sysconfig
import tarfile
import urllib.request
from pathlib import Path
from setuptools import setup, Extension


def download_cpython_headers(version_info):
    """Скачивает и распаковывает заголовки CPython для указанной версии."""
    major, minor, micro = version_info[:3]
    version_str = f"{major}.{minor}.{micro}"
    url = f"https://www.python.org/ftp/python/{version_str}/Python-{version_str}.tgz"
    cache_dir = Path("/tmp/cpython-headers")
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Если уже скачано — пропускаем
    include_dir = cache_dir / "Include"
    if include_dir.exists():
        return include_dir

    tgz_path = cache_dir / f"Python-{version_str}.tgz"
    if not tgz_path.exists():
        urllib.request.urlretrieve(url, tgz_path)

    with tarfile.open(tgz_path, "r:gz") as tar:
        tar.extractall(cache_dir)

    return cache_dir / f"Python-{version_str}" / "Include"


# Получаем пути к заголовкам для текущей версии Python
cpython_include = download_cpython_headers(sys.version_info)
internal_include = cpython_include / "internal"

ext = Extension(
    name="cpython_internals_inspector._core",
    sources=[
        "src/cpython_internals_inspector/_core.c",
        "src/cpython_internals_inspector/_dict.c",
        "src/cpython_internals_inspector/_utils.c",
    ],
    include_dirs=[
        sysconfig.get_path("include"),
        str(cpython_include),
        str(internal_include),
    ],
    extra_compile_args=["-DPy_BUILD_CORE_MODULE"],
)

setup(ext_modules=[ext])
