"""Load and save regression cases as JSON files in the user's repository."""

from __future__ import annotations

import re
from pathlib import Path

from undoom.models import Case

_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_name(name: str) -> None:
    from undoom.errors import PromoteError

    if not _SLUG.match(name):
        raise PromoteError("case name must be a lowercase slug such as no-unsolicited-refund")


def load_cases(directory: Path) -> list[Case]:
    if not directory.exists():
        return []
    return [
        Case.model_validate_json(path.read_text(encoding="utf-8"))
        for path in sorted(directory.glob("*.json"))
    ]


def write_case(case: Case, directory: Path) -> Path:
    validate_name(case.name)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{case.name}.json"
    path.write_text(case.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return path
