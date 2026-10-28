# Security

Undoom stores prompts, tool arguments, and tool results. Those payloads often contain customer data and sometimes contain credentials that were passed through a tool call.

## What the library does

Before a run or replay is written, Undoom replaces:

- values of common secret fields (`authorization`, `api_key`, `password`, `access_token`, and similar)
- `sk-` and `sk-proj-` tokens
- `Bearer` tokens
- `api_key=...` and `authorization: ...` assignments

You can add regexes with `undoom.configure(redact_patterns=[...])`. Redaction is not a guarantee. Review a case file before you commit it.

## What you should do

- Keep `.undoom/*.sqlite` out of git. Commit `.undoom/cases/` only after you have read it.
- Do not point `--tool module:function` at a function you would not run in CI. The override executes with the privileges of the test process.
- Do not send production traces to the public demo. The demo build has no write API and only displays fixtures shipped in the repository.
- Prefer a local sqlite file. Use Postgres only on a database you control.

## Reporting

Open a private security advisory on [github.com/rejisterjack/undoom](https://github.com/rejisterjack/undoom) or email rejisterjack@gmail.com. Please include the version and a description of the data that was stored. Do not include a live customer trace in a public issue.
