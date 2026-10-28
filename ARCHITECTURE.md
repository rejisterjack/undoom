# Architecture

Undoom records a tool-calling run, replays it with one change against the recorded tool results, and stores a successful replay as a regression case. The case file is the artifact CI runs. The trace database is operational history.

## Components

- **Capture API** (`undoom.run`, `undoom.wrap_openai`). A run is a versioned JSON document: model steps (messages, tool calls, the tool schema) and tool steps (arguments, result, error). The OpenAI adapter is a thin caller of that API. Other stacks can record with `record_model` and `tool` directly.
- **Trace store.** SQLite by default, Postgres when `UNDOOM_STORE` is a postgres URL. Both persist the same document plus indexed columns for id, agent, status, time, and failure reason. Writes pass through redaction.
- **Replay engine.** Loads the first model step, applies the changeset, and calls a model provider at temperature 0. Tool calls are answered from a cassette keyed by tool name and canonical JSON arguments. The overridden tool, if the change is a tool implementation, is the only function Undoom executes.
- **Case files.** `.undoom/cases/*.json` holds the original messages, the tool schema, the cassette, the changeset (usually a path), and the expectation. `undoom test` does not need the trace database.
- **Local API and UI.** `undoom serve` exposes the trace log to `apps/ui`. The Vercel build of that UI does not talk to a store. It imports `fixtures/demo.json`, which is a synthetic export of the order-lookup story.

## Failure signature

A case passes when the original failure does not recur:

- none of the source run's `unexpected_tools` are called
- none of the source run's tool errors recur
- if those sets are empty, tools that the fixed replay dropped become the forbidden set
- `--expect-tools` additionally requires the successful tool-name sequence

Assistant text is part of the diff and not the assertion. Model nondeterminism is why. Temperature is forced to 0 on replay, which reduces drift and does not remove it. A cassette miss is a failed replay, not a cue to call the live tool.

## Schema

Every run, replay, and case carries `schema_version`. This release accepts version 1 only. A document from a newer major version fails on read instead of being guessed at. There is no online migrator. Dump the JSON payloads and load them into a new database if you need to move history.

## Trust boundary

- Recorded tools are not executed during replay.
- A tool changeset imports `module:function` and calls it with the model’s arguments. That is user code.
- Case files and sqlite databases may contain ticket contents and whatever redaction did not recognize.
- The demo provider and the Vercel site use fabricated order data.

## Non-goals

- Production monitoring, tracing backends, and dashboards of live traffic.
- General evals, datasets, and LLM-as-judge scoring.
- Least-privilege policy or credential brokering (Keywarden).
- Sandboxed execution of generated code (Boxwren).
- A hosted multi-tenant trace product. The public site is a synthetic demo.
- OpenTelemetry import. Native capture keeps the tool results a cassette needs. GenAI spans often do not, so an importer is a later project rather than a launch dependency.

## Process model

Capture runs inside the agent process and appends one document when the `run` block exits. Replay and `undoom test` are separate processes. They read the case or the trace log, call the model provider, and do not attach to the original agent. The local UI is a reader of that log, plus a replay form that calls the same engine. Demo mode refuses those writes.
