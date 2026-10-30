# Changelog

## Unreleased

- Local UI can replay with a prompt file path (read by `undoom serve`), list every replay for a run, and promote a fixed replay to a case.
- `undoom import` turns an OTLP/JSON GenAI export into a stored run when tool spans include arguments and a result or error.

## 1.0.0

First production release.

- Capture tool-calling runs with a manual API and an OpenAI chat-completions wrapper.
- Replay a failure with one change (prompt, model, or a single tool implementation) against a tool cassette.
- Promote a fixed replay to a JSON case file and run it with `undoom test`, including JSON and JUnit output.
- SQLite by default, Postgres via `UNDOOM_STORE`.
- Local diff API (`undoom serve`) and a synthetic-only web UI.
