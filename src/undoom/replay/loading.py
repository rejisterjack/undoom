"""Import a user function named as module:function."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any

from undoom.errors import ReplayError


def load_callable(spec: str) -> Callable[..., Any]:
    if ":" not in spec:
        raise ReplayError(f"entrypoint must be module:function, got {spec!r}")
    module_name, func_name = spec.split(":", 1)
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        raise ReplayError(f"cannot import {module_name}: {exc}") from exc
    try:
        function = getattr(module, func_name)
    except AttributeError as exc:
        raise ReplayError(f"{spec} was not found") from exc
    if not callable(function):
        raise ReplayError(f"{spec} is not callable")
    return function
