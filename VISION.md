# Undoom — Agent Failure Replay and Regression

> Turn production agent failures into regression tests that run on every change.

**Home:** [undoom.rejisterjack.com](https://undoom.rejisterjack.com)

## One-line idea

Capture what production agents actually did, replay a failed run with one thing changed, and promote a fixed replay into a permanent regression test—closing the loop after observability.

## The problem

Agents fail in ways traditional uptime monitoring misses: wrong tool choice, bad arguments, hallucinated steps—while the service stays “healthy.” Teams see traces in Langfuse-style tools, fix a prompt, and hope. They rarely prove the same failure cannot return. Observability is crowded; the gap is **failure → fix → automated proof**. Undoom focuses on that loop for tool-calling agents.

## What Undoom does

- Captures traces: prompts, model calls, tool calls, results
- Replays failed runs deterministically with tool responses mocked from the recording
- Lets you change one variable (prompt, model, tool implementation) and compare outcome
- Saves successful replays as regression tests in a suite
- Reports which historical failures stay fixed and which regress

## Who it's for

- Teams running tool-calling agents in production with recurring failure patterns
- Engineers responsible for agent quality who need evidence a fix worked
- Developers who want regression tests without building a full eval platform from scratch

## How you use it

1. Add the capture hook to your agent (Python package)
2. When a run fails, select that trace in the CLI or web UI
3. Replay with one change; tool I/O comes from the recording
4. On success, one command promotes the replay to a regression test
5. Run the suite on CI or locally before shipping prompt or tool changes

## How it runs

- **Local-first:** `pip install` capture + CLI; traces default to local SQLite
- Optional Postgres for larger teams (self-hosted or Neon)
- Optional local web UI for run comparison
- Hosted demo (if provided) uses synthetic traces only

## Tech stack

- Python (core library and CLI)
- OpenTelemetry-style or framework-native trace hooks
- SQLite initially; PostgreSQL when scale requires it
- CLI first; lightweight web UI for diffing runs
- Docker for reproducible demos

## Success criteria

- End-to-end demo: realistic failure → replay → fix → locked regression test
- README explains differentiation from generic observability and eval platforms
- Documented integration for at least one common agent stack
- Open source at [github.com/rejisterjack/undoom](https://github.com/rejisterjack/undoom)

## Limitations & non-goals

- Narrow focus: tool-calling agent failures and replay—not a general LLM benchmark suite
- Well-funded observability vendors may add overlap; depth on **failure-to-test** is the differentiator
- Not a replacement for production monitoring or Keywarden-style governance

## Deployment

| Component | Notes |
|-----------|--------|
| Library + CLI | PyPI (`undoom`), local execution |
| Optional replay UI | Self-host or documented Vercel demo |
| Trace store | SQLite default; Postgres optional |

## Related projects

Undoom is the **reliability** layer alongside sibling open-source agent infrastructure:

| Project | Role |
|---------|------|
| [Keywarden](https://github.com/rejisterjack/keywarden) | Least-privilege proxy and approvals for tool calls |
| **Undoom** | Replay failures and regression-test fixes |
| [Boxwren](https://github.com/rejisterjack/boxwren) | WASM sandbox for untrusted agent-generated code |

Use Keywarden to limit what agents can do, Undoom to ensure known failures do not return, Boxwren to run untrusted code with hard resource limits.
