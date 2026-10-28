import re

from undoom.models import ModelStep, Run, RunStatus, ToolCall
from undoom.redact import REDACTED, redact


def test_redacts_secret_keys_and_bearer_tokens() -> None:
    payload = {
        "authorization": "Bearer super-secret-token",
        "note": "Authorization: Bearer abc.def",
        "api_key": "sk-abcdefghijklmnopqrstuvwxyz",
        "nested": {"content": "prefix sk-proj-abcdefghijklmnopqrstuvwxyz suffix"},
    }
    cleaned = redact(payload)
    assert cleaned["authorization"] == REDACTED
    assert cleaned["api_key"] == REDACTED
    assert "super-secret-token" not in str(cleaned)
    assert "abc.def" not in cleaned["note"]
    assert "sk-proj-" not in cleaned["nested"]["content"]
    assert REDACTED in cleaned["nested"]["content"]


def test_user_pattern_is_applied() -> None:
    cleaned = redact("ticket 1042", extra=[re.compile(r"1042")])
    assert cleaned == "ticket [REDACTED]"


def test_redact_run_round_trip() -> None:
    from undoom.redact import redact_run

    run = Run(
        agent="support",
        name="ticket",
        status=RunStatus.failure,
        failure_reason="bad",
        steps=[
            ModelStep(
                model="m",
                messages=[{"role": "user", "content": "sk-abcdefghijklmnopqrstuvwxyz"}],
                tool_calls=[ToolCall(id="1", name="lookup_order", arguments={"order_id": "1"})],
            )
        ],
    )
    stored = redact_run(run)
    assert stored.id == run.id
    assert "sk-" not in stored.model_dump_json()
