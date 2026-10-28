"""Text, JSON, and JUnit renderers for `undoom test`."""

from __future__ import annotations

import json
from xml.sax.saxutils import escape

from undoom.models import SuiteReport


def render_report(report: SuiteReport, report_format: str) -> str:
    if report_format == "json":
        return render_json(report)
    if report_format == "junit":
        return render_junit(report)
    if report_format == "text":
        return render_text(report)
    raise ValueError("format must be text, json, or junit")


def render_text(report: SuiteReport) -> str:
    lines: list[str] = []
    for case in report.cases:
        label = "PASS" if case.status == "passed" else "FAIL"
        suffix = f": {case.message}" if case.message else ""
        lines.append(f"{label} {case.name}{suffix}")
    lines.append(f"{report.passed} passed, {report.failed} failed")
    return "\n".join(lines)


def render_json(report: SuiteReport) -> str:
    payload = {
        "passed": report.passed,
        "failed": report.failed,
        "cases": [case.model_dump() for case in report.cases],
    }
    return json.dumps(payload, indent=2)


def render_junit(report: SuiteReport) -> str:
    failures = sum(1 for case in report.cases if case.status == "failed")
    errors = sum(1 for case in report.cases if case.status == "error")
    bodies: list[str] = []
    for case in report.cases:
        if case.status == "passed":
            inner = ""
        else:
            tag = "failure" if case.status == "failed" else "error"
            inner = f"<{tag} message={_attr(case.message)}></{tag}>"
        bodies.append(
            f'<testcase name={_attr(case.name)} classname="undoom.case">{inner}</testcase>'
        )
    suite = (
        f'<testsuite name="undoom" tests="{len(report.cases)}" '
        f'failures="{failures}" errors="{errors}">' + "".join(bodies) + "</testsuite>"
    )
    return '<?xml version="1.0" encoding="utf-8"?>' + suite


def _attr(value: str) -> str:
    return '"' + escape(value, {'"': "&quot;"}) + '"'
