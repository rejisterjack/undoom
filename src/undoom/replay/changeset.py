"""Apply the single allowed change to the recorded prompt."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from undoom.errors import ReplayError
from undoom.models import Changeset


def ensure_changeset(changeset: Changeset) -> None:
    try:
        changeset.check()
    except ValueError as exc:
        raise ReplayError(str(exc)) from exc


def read_prompt(changeset: Changeset) -> str:
    ensure_changeset(changeset)
    if changeset.prompt_text is not None:
        return changeset.prompt_text
    path = Path(changeset.prompt_file or "")
    if not path.is_file():
        raise ReplayError(f"prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


def build_changeset(
    *,
    prompt_text: str | None = None,
    prompt_file: str | None = None,
    model: str | None = None,
    tool_name: str | None = None,
    tool_entrypoint: str | None = None,
) -> Changeset:
    """Build the one change a replay is allowed to make."""

    prompt_set = prompt_text is not None or prompt_file is not None
    model_set = model is not None
    tool_set = tool_name is not None or tool_entrypoint is not None
    if int(prompt_set) + int(model_set) + int(tool_set) != 1:
        raise ReplayError("specify exactly one of prompt, model, or tool")
    if prompt_text is not None and prompt_file is not None:
        raise ReplayError("pass prompt text or a prompt file, not both")
    if prompt_set:
        return Changeset(kind="prompt", prompt_text=prompt_text, prompt_file=prompt_file)
    if model_set:
        return Changeset(kind="model", model=model)
    if not tool_name or not tool_entrypoint:
        raise ReplayError("a tool change needs a name and an entrypoint")
    return Changeset(kind="tool", tool_name=tool_name, tool_entrypoint=tool_entrypoint)


def apply_prompt(messages: list[dict[str, Any]], prompt: str) -> list[dict[str, Any]]:
    cloned: list[dict[str, Any]] = copy.deepcopy(messages)
    for message in cloned:
        if message.get("role") == "system":
            message["content"] = prompt
            return cloned
    cloned.insert(0, {"role": "system", "content": prompt})
    return cloned
