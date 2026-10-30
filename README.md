# Undoom

Turn a production agent failure into a regression test that runs on every change.

Observability shows that a tool-calling agent failed. An eval platform scores a dataset. Undoom does the step after that: replay the failed run with one change, mock the tools from the recording, and promote a fixed replay into a test your CI can run. It is not a monitor, and it is not a general benchmark suite.

Undoom sits next to [Keywarden](https://github.com/rejisterjack/keywarden) (what an agent is allowed to do) and [Boxwren](https://github.com/rejisterjack/boxwren) (where untrusted code runs). Use those when the question is permission or isolation. Use Undoom when the question is whether a known failure can come back.

## The loop

1. Record a run: prompts, model calls, tool calls, and tool results.
2. Mark it failed, and name the tool calls that should not have happened.
3. Replay with exactly one change: a prompt, a model id, or one tool implementation.
4. Every other tool returns the recorded result. Undoom does not call it.
5. Promote a fixed replay. `undoom test` fails if that failure shows up again.

Live model output is not bit-identical. Deterministic here means the tool I/O is frozen. Replay calls the model again at temperature 0. A cassette hit is the pair `(tool name, canonical JSON arguments)`. Different key order does not count as a new call. A miss stops the replay. Undoom will not fall through to the live tool.

A tool override runs your function, with your privileges, the same way your test suite does. Do not point it at a tool you would not run locally.

## Install

Python 3.11 or newer.

```bash
pip install undoom
pip install 'undoom[openai]'    # live replay against the OpenAI API
pip install 'undoom[postgres]'  # shared trace log
pip install 'undoom[ui]'        # local diff UI
```

Traces default to `.undoom/traces.sqlite`. Case files live in `.undoom/cases/` and are meant to be committed. Keep the database out of git. A useful `.gitignore`:

```gitignore
.undoom/*
!.undoom/cases/
!.undoom/cases/**
```

Traces can contain customer text. Undoom redacts common API-key and `Authorization` shapes before writing. It cannot know every secret. Treat the sqlite file, and any case you commit, as sensitive. See [SECURITY.md](SECURITY.md).

## Record a run

```python
import undoom
from openai import OpenAI

undoom.configure(agent="support")  # sqlite at .undoom/traces.sqlite

def lookup_order(order_id: str) -> dict:
    return {"order_id": order_id, "status": "shipped"}

def refund_order(order_id: str) -> dict:
    return {"order_id": order_id, "status": "refunded"}

with undoom.run(name="ticket-1042") as recorder:
    client = undoom.wrap_openai(
        OpenAI(),
        recorder,
        tools={"lookup_order": lookup_order, "refund_order": refund_order},
    )
    client.chat.completions.create(
        model="gpt-4.1",
        temperature=0,
        messages=[
            {"role": "system", "content": open("prompts/support.txt").read()},
            {"role": "user", "content": "Where is order 1042?"},
        ],
        tools=[...],  # the same schema you pass to the API
    )
    if any(step.kind == "tool" and step.name == "refund_order" for step in recorder.run.steps):
        recorder.fail(
            "refunded without an explicit request",
            unexpected_tools=["refund_order"],
        )
```

`unexpected_tools` is the failure signature. Promote turns those names into the check `undoom test` enforces. Without them, Undoom treats tools that disappeared in the fixed replay as the signature.

You can record a model call and a tool yourself when you are not on the OpenAI SDK. `recorder.record_model(...)` and `with recorder.tool(name, arguments) as handle: handle.record(result)` are the contract. Adapters are thin callers of that API.

```bash
undoom runs list
undoom runs show <run-id>
undoom runs fail <run-id> --reason "refunded without an explicit request" --unexpected-tool refund_order
```

## Import an OpenTelemetry trace

When a stack already exports GenAI spans, you can turn one OTLP/JSON document into a stored run:

```bash
undoom import trace.json --agent support --name ticket-1042
undoom import trace.json --trace-id <id>   # required when the file holds more than one trace
```

The importer only accepts tool spans that include both `gen_ai.tool.call.arguments` and a result or error. GenAI conventions mark those fields as opt-in; a span that omits them cannot fill a cassette, so Undoom refuses the import instead of inventing values. Mark the failure afterward with `undoom runs fail` the same way you would for a native capture.

## Replay one change

```bash
undoom replay <run-id> --prompt-file prompts/support.txt
undoom replay <run-id> --model gpt-4.1-mini
undoom replay <run-id> --tool lookup_order=myapp.tools:lookup_order
```

A command that sets more than one of prompt, model, and tool is rejected. The replay id and verdict are printed. Verdicts:

| Verdict | Meaning |
| --- | --- |
| `fixed` | The failure signature did not recur |
| `still_failing` | The same unexpected tool or tool error came back |
| `diverged` | The model called a tool the recording cannot answer |
| `error` | The provider or the override function could not be loaded |

Final assistant text is shown for comparison. It is not the pass/fail check.

## Promote and test

```bash
undoom promote <replay-id> --name no-unsolicited-refund
undoom promote <replay-id> --name no-unsolicited-refund --expect-tools
undoom test
undoom test --format junit
```

`--expect-tools` also locks the successful tool sequence. The default check is only that the original failure does not recur.

Prompt and tool changes point at files in your repo. `undoom test` reads those paths again, so editing the prompt is what CI evaluates. The case file embeds the tool cassette, which means CI does not need the sqlite history.

```yaml
# .github/workflows/undoom.yml
name: undoom
on: [push, pull_request]
jobs:
  regressions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install undoom
      - run: undoom test --format junit
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

Set `UNDOOM_MODEL_PROVIDER=openai` (the default) for live replay. A provider can also be `module:factory`, a zero-argument function that returns an object with `complete(...)`.

## Offline demo

The order-lookup story ships in `examples/order_lookup/`. A buggy prompt refunds order 1042 after looking it up. The fixed prompt refunds only when the user asks. No API key is required.

```bash
mkdir -p /tmp/undoom-demo
UNDOOM_DEMO_ROOT=/tmp/undoom-demo python examples/order_lookup/demo.py
cd /tmp/undoom-demo
PYTHONPATH=/path/to/undoom \
  UNDOOM_MODEL_PROVIDER=examples.order_lookup.fake:provider \
  undoom test
```

Put the refund instruction back into `prompts/fixed.txt` and `undoom test` fails on `refund_order`.

Docker runs that story and leaves the case file on a volume:

```bash
docker compose -f docker/compose.yml up --build demo
```

Postgres, for a shared trace log rather than for CI, is the `postgres` profile in the same file. Point the CLI at it with `UNDOOM_STORE=postgresql://undoom:undoom@localhost:5432/undoom`.

## Local diff UI

```bash
pip install 'undoom[ui]'
undoom serve
```

The API listens on `http://127.0.0.1:8787`. From `apps/ui`:

```bash
npm install
NEXT_PUBLIC_UNDOOM_API=http://127.0.0.1:8787 npm run dev
```

The hosted demo at [undoom.rejisterjack.com](https://undoom.rejisterjack.com) is the same UI built with `NEXT_PUBLIC_DEMO=1`. It reads committed synthetic fixtures only. There is no write API and no customer data on that deployment. On Vercel, set the project root to `apps/ui` and `NEXT_PUBLIC_DEMO` to `1`.

## Store

| `UNDOOM_STORE` | Store |
| --- | --- |
| unset | `.undoom/traces.sqlite` |
| a filesystem path | SQLite at that path |
| `sqlite:///relative.sqlite` | SQLite |
| `postgresql://...` | Postgres (`undoom[postgres]`) |

Documents are JSON with `schema_version`. This release reads version 1 and rejects anything else.

## Development

```bash
uv sync --all-extras --group dev
uv run ruff check src tests examples
uv run ruff format --check src tests examples
uv run mypy src
uv run pytest
```

`UNDOOM_TEST_POSTGRES` opts into the Postgres integration test. The default suite never calls the network.

## What this is not

Undoom does not replace production monitoring. It does not decide which tools an agent may call, and it does not sandbox code. Those are Keywarden and Boxwren. It is not a place to host a general LLM benchmark. The architecture note in [ARCHITECTURE.md](ARCHITECTURE.md) is the longer version of that boundary.
