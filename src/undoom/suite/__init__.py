"""Regression suite."""

from undoom.suite.files import load_cases, write_case
from undoom.suite.promote import promote_replay
from undoom.suite.runner import run_suite

__all__ = ["load_cases", "promote_replay", "run_suite", "write_case"]
