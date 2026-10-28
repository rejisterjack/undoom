"""Turn production agent failures into regression tests."""

from importlib.metadata import PackageNotFoundError, version

from undoom.capture.context import run
from undoom.capture.openai import wrap_openai
from undoom.config import configure

try:
    __version__ = version("undoom")
except PackageNotFoundError:
    __version__ = "1.0.0"

__all__ = ["__version__", "configure", "run", "wrap_openai"]
