import os
import subprocess
import sys
from pathlib import Path

from examples.order_lookup.prompts import BUGGY

REPO = Path(__file__).resolve().parents[1]


def test_demo_then_suite_goes_red_when_the_bug_returns(tmp_path) -> None:
    env = os.environ.copy()
    env["UNDOOM_DEMO_ROOT"] = str(tmp_path)
    env["UNDOOM_MODEL_PROVIDER"] = "examples.order_lookup.fake:provider"
    env["PYTHONPATH"] = str(REPO)
    env.pop("UNDOOM_STORE", None)
    completed = subprocess.run(
        [sys.executable, str(REPO / "examples" / "order_lookup" / "demo.py")],
        cwd=REPO,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    passed = subprocess.run(
        [sys.executable, "-m", "undoom", "test", "--format", "json"],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert passed.returncode == 0, passed.stdout + passed.stderr
    assert '"failed": 0' in passed.stdout
    prompt = tmp_path / "prompts" / "fixed.txt"
    prompt.write_text(BUGGY.strip() + "\n", encoding="utf-8")
    failed = subprocess.run(
        [sys.executable, "-m", "undoom", "test"],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert failed.returncode != 0
    assert "refund_order" in failed.stdout
