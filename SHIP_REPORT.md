# Ship Readiness Report — Undoom

Testing finished 22 Nov 2026. 40 features passed. Decision: GO.

## Product Summary

Undoom records a tool-calling agent run and replays a failure with one change.
Tool results come from the recording. A cassette miss stops the replay instead of calling the live tool.
A fixed replay can be promoted into a case that `undoom test` runs again.
The public page at https://undoom.rejisterjack.com is a synthetic demo of the Next.js UI, with no write API.
The package is local-first. It is not a monitor, a permission proxy, or a general benchmark suite.

## Feature Table

| ID | Feature | Priority | Status | Bugs Found | Bugs Fixed | UI Issues Fixed | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CAP-01 | Record a run | P0 | PASSED | 0 | 0 | 0 | undoom.run stores prompts, model calls, tool calls, and tool results. |
| CAP-02 | OpenAI wrapper | P0 | PASSED | 0 | 0 | 0 | wrap_openai records chat.completions.create and can run the supplied tools. |
| CAP-03 | Anthropic wrapper | P1 | PASSED | 0 | 0 | 0 | wrap_anthropic records messages.create. It needs the anthropic extra. |
| CAP-04 | Manual capture | P0 | PASSED | 0 | 0 | 0 | record_model and recorder.tool are the contract when there is no SDK wrapper. |
| CAP-05 | Mark a failure | P0 | PASSED | 0 | 0 | 0 | fail() stores a reason and unexpected_tools. Those names become the regression check. |
| CAP-06 | Redaction | P0 | PASSED | 0 | 0 | 0 | Secret field names, sk- tokens, Bearer tokens, and api_key assignments become [REDACTED] before a write. |
| STORE-01 | SQLite | P0 | PASSED | 0 | 0 | 0 | The default file is .undoom/traces.sqlite. A path or sqlite:// URL also works. |
| STORE-02 | Postgres | P1 | PASSED | 0 | 0 | 0 | UNDOOM_STORE=postgresql://... needs the postgres extra. CI sets UNDOOM_TEST_POSTGRES. |
| STORE-03 | Schema version | P1 | PASSED | 0 | 0 | 0 | Documents are schema_version 1. Anything else is rejected. The DDL helper is a stub. |
| CLI-01 | List and show runs | P0 | PASSED | 0 | 0 | 0 | undoom runs list and undoom runs show. --json prints the documents. A missing run exits 1. |
| CLI-02 | Fail from the CLI | P0 | PASSED | 0 | 0 | 0 | undoom runs fail takes --reason and repeatable --unexpected-tool. |
| CLI-03 | Import a trace | P0 | PASSED | 0 | 0 | 0 | undoom import reads OTLP/JSON. A tool span without arguments and a result or error is refused. |
| CLI-04 | Replay one change | P0 | PASSED | 0 | 0 | 0 | Exactly one of prompt, model, or tool. More than one is rejected. Temperature is 0. |
| CLI-05 | Verdicts | P0 | PASSED | 0 | 0 | 0 | fixed, still_failing, diverged, and error were all produced. Assistant text is shown and is not the check. |
| CLI-06 | Cassette | P0 | PASSED | 0 | 0 | 0 | A hit is tool name plus canonical JSON arguments. A miss stops the replay. |
| CLI-07 | Tool override | P1 | PASSED | 1 | 1 | 0 | A missing module is stored as verdict error. Other tools stay on the cassette. |
| CLI-08 | Promote | P0 | PASSED | 0 | 0 | 0 | undoom promote writes a case under .undoom/cases. --expect-tools also locks the tool sequence. |
| CLI-09 | Regression test | P0 | PASSED | 0 | 0 | 0 | undoom test reruns cases. A failure exits 1. --format junit and --case select the output and the case. |
| CLI-10 | Serve | P1 | PASSED | 0 | 0 | 0 | undoom serve listens on 127.0.0.1:8787. --demo refuses writes. The ui extra is required. |
| API-01 | Read endpoints | P0 | PASSED | 0 | 0 | 0 | GET /api/meta, /api/runs, /api/runs/{id}, /api/replays, /api/replays/{id}, and /api/cases. |
| API-02 | Replay and promote | P0 | PASSED | 0 | 0 | 0 | POST /api/replay and POST /api/promote. A bad change is 400. A missing run is 404. |
| API-03 | Demo writes | P0 | PASSED | 0 | 0 | 0 | With demo set, those posts return 403 and do not write. |
| API-04 | Local CORS | P1 | PASSED | 0 | 0 | 0 | CORS allows only http://localhost and http://127.0.0.1, with an optional port. |
| UI-01 | Run list | P1 | PASSED | 0 | 0 | 0 | / lists runs with status, name, agent, and the failure reason, or "No runs yet." |
| UI-02 | Run timeline | P1 | PASSED | 0 | 0 | 1 | /runs/{id} shows the recorded steps. An unknown id says Page not found inside the library layout. |
| UI-03 | Diff | P1 | PASSED | 0 | 0 | 0 | /diff/{id} compares a run with a replay. Final text is visible and is not the verdict. |
| UI-04 | Suite | P1 | PASSED | 0 | 0 | 0 | /suite lists promoted cases. |
| UI-05 | Replay and promote forms | P1 | PASSED | 0 | 0 | 0 | The local UI can submit one change and promote a fixed replay. The demo build does not. |
| UI-06 | Synthetic demo | P0 | PASSED | 0 | 0 | 0 | NEXT_PUBLIC_DEMO=1 reads apps/ui/fixtures/demo.json and shows the synthetic banner. |
| UI-07 | Offline state | P1 | PASSED | 0 | 0 | 0 | If undoom serve is down, the non-demo UI says it is offline and lists nothing. |
| UI-08 | Responsive layout | P2 | PASSED | 0 | 0 | 0 | Below 720px the run rows and columns stack and the header becomes a grid. |
| UI-09 | Title and focus | P1 | PASSED | 0 | 0 | 1 | Title is Undoom. Keyboard focus uses the browser ring. /favicon.ico is served. |
| UI-10 | Security headers | P1 | PASSED | 1 | 1 | 0 | The demo sends nosniff, a strict referrer policy, DENY, and a CSP. The page still renders. |
| DEMO-01 | Order lookup | P0 | PASSED | 0 | 0 | 0 | examples/order_lookup records a refund that should not happen, then a fixed prompt. |
| DEMO-02 | Docker demo | P1 | PASSED | 0 | 0 | 0 | docker compose -f docker/compose.yml up --build demo writes the case onto a volume. |
| DEMO-03 | Fake provider | P0 | PASSED | 0 | 0 | 0 | examples.order_lookup.fake:provider lets undoom test run with no API key. |
| DEVOPS-01 | CI | P0 | PASSED | 1 | 1 | 0 | ruff format was red on anthropic.py. It is formatted. ruff, mypy, and pytest passed locally. |
| DEVOPS-02 | PyPI | P0 | PASSED | 0 | 0 | 0 | A v* tag publishes with trusted publishing. The package version is 1.0.2. PyPI currently serves 1.0.1 until that tag. |
| DEVOPS-03 | Python versions | P1 | PASSED | 0 | 0 | 0 | Requires Python >= 3.11. CI covers 3.11 and 3.12. |
| DEVOPS-04 | Example workflow | P2 | PASSED | 0 | 0 | 0 | examples/ci/undoom.yml and the README snippet run undoom test on push and pull request. |

## Gaps

- GAP-01 Security headers for the public UI. BUILT as UI-10. The demo response now sets nosniff, a referrer policy, framing denial, and a content security policy.
- GAP-02 Production monitoring. DEFER. Undoom starts after a failure has already been seen.
- GAP-03 Tool permissions and sandboxing. DEFER. Those belong to Keywarden and Boxwren.
- GAP-04 A general benchmark suite. DEFER. A case is one known failure, not a leaderboard.
- GAP-05 Accounts and billing. DEFER. The package is local. The public page is a fixture demo.
- GAP-06 Light theme. DEFER. The UI sets color-scheme dark and does not offer a toggle.
- GAP-07 Hosted capture. DEFER. The public demo has no write API and must not receive production traces.

## Per-Feature Sections

### CAP-01 Record a run

- **Priority:** P0
- **Status:** PASSED
- **Files:** src/undoom/capture/context.py, src/undoom/config.py
- **Expected behavior:** undoom.configure selects the agent and store. undoom.run(name) opens a run and stores it when the block finishes.
- **Acceptance:**
  - [x] A finished run can be loaded by id.
  - [x] The agent name is the configured one.
- **Test cases:** A short run; an empty name; two runs in one process.
- **UI checks:** none
- **Dependencies:** STORE-01
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### CAP-02 OpenAI wrapper

- **Priority:** P0
- **Status:** PASSED
- **Files:** src/undoom/capture/openai.py
- **Expected behavior:** wrap_openai records chat.completions.create, including tool calls. Supplied tool functions run when the model asks for them, and their results are stored.
- **Acceptance:**
  - [x] A recorded step exists for the model call.
  - [x] A tool result is stored under the tool name.
  - [x] The openai extra is what installs the SDK.
- **Test cases:** No tools; one tool; a tool that raises; a missing extra.
- **UI checks:** none
- **Dependencies:** CAP-01
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### CAP-03 Anthropic wrapper

- **Priority:** P1
- **Status:** PASSED
- **Files:** src/undoom/capture/anthropic.py
- **Expected behavior:** wrap_anthropic records messages.create the same way. It needs the anthropic extra.
- **Acceptance:**
  - [x] A messages.create call becomes model and tool steps.
  - [x] Importing the helper without the extra fails clearly.
- **Test cases:** One tool; a text-only reply; the package extra missing.
- **UI checks:** none
- **Dependencies:** CAP-01
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### CAP-04 Manual capture

- **Priority:** P0
- **Status:** PASSED
- **Files:** src/undoom/capture/context.py
- **Expected behavior:** record_model stores a model step. recorder.tool(name, arguments) records the call, and handle.record stores the result or an error.
- **Acceptance:**
  - [x] A manual tool step round-trips through the store.
  - [x] An error result is distinguishable from a value.
- **Test cases:** A result dict; an error string; arguments with reordered keys.
- **UI checks:** none
- **Dependencies:** CAP-01
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### CAP-05 Mark a failure

- **Priority:** P0
- **Status:** PASSED
- **Files:** src/undoom/capture/context.py, src/undoom/cli.py
- **Expected behavior:** recorder.fail(reason, unexpected_tools=[...]) stores the reason and the tool names. Without unexpected tools, promote treats tools that disappeared in the fixed replay as the signature.
- **Acceptance:**
  - [x] The stored run status is failed.
  - [x] The reason and tool names survive a reload.
- **Test cases:** One tool; two tools; no unexpected tools; a reason with emoji and punctuation.
- **UI checks:** none
- **Dependencies:** CAP-01
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### CAP-06 Redaction

- **Priority:** P0
- **Status:** PASSED
- **Files:** src/undoom/redact.py
- **Expected behavior:** Before a write, values under authorization, api_key, password, access_token, and the other SECRET_KEYS become [REDACTED]. sk- and sk-proj- tokens, Bearer tokens, and api_key assignments in strings are redacted. configure(redact_patterns=...) adds patterns.
- **Acceptance:**
  - [x] A stored tool result does not contain an sk- token that was in the input.
  - [x] A normal order id is unchanged.
  - [x] Redaction is not described as complete.
- **Test cases:** sk- token; Bearer header; api_key=secret; a nested password field; a sentence that merely says "password".
- **UI checks:** none
- **Dependencies:** STORE-01
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### STORE-01 SQLite

- **Priority:** P0
- **Status:** PASSED
- **Files:** src/undoom/store/sqlite.py, src/undoom/store/resolve.py
- **Expected behavior:** An unset UNDOOM_STORE uses .undoom/traces.sqlite. A filesystem path and a sqlite:/// URL select SQLite. The parent directory is created.
- **Acceptance:**
  - [x] A new directory receives the database.
  - [x] A second process can read the run.
- **Test cases:** Unset; a relative path; sqlite:///absolute; a path that does not exist yet.
- **UI checks:** none
- **Dependencies:** none
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### STORE-02 Postgres

- **Priority:** P1
- **Status:** PASSED
- **Files:** src/undoom/store/postgres.py
- **Expected behavior:** A postgresql:// URL uses Postgres when the extra is installed. The same run and replay operations work. The default pytest run skips this unless UNDOOM_TEST_POSTGRES is set.
- **Acceptance:**
  - [x] A run saved in Postgres can be fetched by id.
  - [x] A missing driver fails before a partial write.
- **Test cases:** Save and list; a bad URL; the extra not installed.
- **UI checks:** none
- **Dependencies:** STORE-03
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### STORE-03 Schema version

- **Priority:** P1
- **Status:** PASSED
- **Files:** src/undoom/models.py, src/undoom/store/migrate.py
- **Expected behavior:** A document with schema_version other than 1 is rejected. ensure_schema_version creates undoom_schema and does not rewrite old rows. Step migrations are empty.
- **Acceptance:**
  - [x] Version 1 loads.
  - [x] Version 2 is rejected.
  - [x] A fresh database gets the meta row.
- **Test cases:** Missing version; version 0; version 1.
- **UI checks:** none
- **Dependencies:** STORE-01
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### CLI-01 List and show runs

- **Priority:** P0
- **Status:** PASSED
- **Files:** src/undoom/cli.py, src/undoom/present.py
- **Expected behavior:** undoom runs list prints lines, or "no runs", or JSON with --json. Limit defaults to 50. undoom runs show prints one run. An unknown id exits 1.
- **Acceptance:**
  - [x] An empty store prints no runs and exits 0.
  - [x] A known id prints the name.
  - [x] An unknown id exits 1.
- **Test cases:** Empty; one run; --limit 1; --json; a wrong id.
- **UI checks:** none
- **Dependencies:** STORE-01
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### CLI-02 Fail from the CLI

- **Priority:** P0
- **Status:** PASSED
- **Files:** src/undoom/cli.py
- **Expected behavior:** undoom runs fail ID --reason TEXT --unexpected-tool NAME stores the failure. The tool flag can be repeated. An unknown id exits 1.
- **Acceptance:**
  - [x] Show after fail prints the reason.
  - [x] A missing reason is a usage error.
- **Test cases:** One tool; two tools; unknown id; a very long reason.
- **UI checks:** none
- **Dependencies:** CAP-05
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### CLI-03 Import a trace

- **Priority:** P0
- **Status:** PASSED
- **Files:** src/undoom/otel/import_trace.py, src/undoom/cli.py
- **Expected behavior:** undoom import FILE writes one run and prints its id. A file with more than one trace requires --trace-id. A tool span missing arguments or a result or error is refused. Nothing is invented.
- **Acceptance:**
  - [x] tests/fixtures/otel/complete_trace.json imports.
  - [x] missing_tool_result.json is refused.
  - [x] two_traces.json without --trace-id is refused.
- **Test cases:** One trace; two traces; a missing file; a non-JSON file; a trace id that is not present.
- **UI checks:** none
- **Dependencies:** STORE-01
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### CLI-04 Replay one change

- **Priority:** P0
- **Status:** PASSED
- **Files:** src/undoom/replay/changeset.py, src/undoom/replay/engine.py, src/undoom/cli.py
- **Expected behavior:** Replay accepts one of --prompt-file, --prompt, --model, or --tool. Two of them are rejected. The model is called again at temperature 0. The replay id and verdict are printed.
- **Acceptance:**
  - [x] A prompt-only replay is stored.
  - [x] Prompt plus model exits 1.
  - [x] An unknown run exits 1.
- **Test cases:** Prompt file; inline prompt; model only; tool only; two flags; a missing prompt file.
- **UI checks:** none
- **Dependencies:** CLI-06, DEMO-03
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### CLI-05 Verdicts

- **Priority:** P0
- **Status:** PASSED
- **Files:** src/undoom/replay/engine.py
- **Expected behavior:** fixed means the failure signature did not recur. still_failing means the unexpected tool or tool error returned. diverged means the model called a tool the recording cannot answer. error means the provider or override could not be loaded. Final assistant text is displayed and is not the pass/fail check.
- **Acceptance:**
  - [x] Each verdict can be produced by a fixture or the fake provider.
  - [x] The text difference does not by itself fail a case.
- **Test cases:** Signature gone; signature present; a new tool name; a provider import error.
- **UI checks:** The diff page shows the verdict separately from the text.
- **Dependencies:** CLI-04
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### CLI-06 Cassette

- **Priority:** P0
- **Status:** PASSED
- **Files:** src/undoom/replay/cassette.py, src/undoom/canonical.py
- **Expected behavior:** A cassette hit is the pair of tool name and canonical JSON arguments. Key order does not matter. A miss stops the replay and does not call a live tool.
- **Acceptance:**
  - [x] Reordered keys hit the same entry.
  - [x] A new argument value is a miss and the verdict is diverged.
  - [x] No live function runs on a miss.
- **Test cases:** Same keys; swapped keys; an extra key; a nested object.
- **UI checks:** none
- **Dependencies:** CAP-04
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### CLI-07 Tool override

- **Priority:** P1
- **Status:** PASSED
- **Files:** src/undoom/replay/engine.py, src/undoom/cli.py
- **Expected behavior:** --tool name=module:function replaces that one tool with the function. Other tools stay on the cassette. The function runs with the test process privileges. A bad entrypoint is verdict error.
- **Acceptance:**
  - [x] Only the named tool uses the function.
  - [x] A missing function does not call the network.
- **Test cases:** A local function that returns a new result; a missing module; a tool name that was not in the recording.
- **UI checks:** none
- **Dependencies:** CLI-04
- **Suspected bugs:** none
- **Bugs Found:** A missing module raised ReplayError and the CLI exited 1. The README says that case is verdict error.
- **Bugs Fixed:** load failures inside a replay are stored as verdict error. A regression test covers a missing module and a provider that raises.
- **UI Issues Fixed:**
- **Files Changed:** src/undoom/replay/engine.py, src/undoom/replay/providers.py, tests/test_replay.py
- **Notes:** Passed after the fix. The live CLI printed verdict error and did not call the missing module.

### CLI-08 Promote

- **Priority:** P0
- **Status:** PASSED
- **Files:** src/undoom/suite/promote.py, src/undoom/suite/files.py
- **Expected behavior:** undoom promote REPLAY --name NAME writes a JSON case. The default check is that the original failure does not recur. --expect-tools also locks the successful tool sequence. Prompt and tool changes point at repo paths. The cassette is embedded.
- **Acceptance:**
  - [x] The printed path is under .undoom/cases.
  - [x] A second promote of a new name does not delete the first file.
  - [x] An unknown replay exits 1.
- **Test cases:** Default; --expect-tools; a name with spaces; a replay that is still_failing.
- **UI checks:** none
- **Dependencies:** CLI-05
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### CLI-09 Regression test

- **Priority:** P0
- **Status:** PASSED
- **Files:** src/undoom/suite/runner.py, src/undoom/suite/report.py
- **Expected behavior:** undoom test loads cases and replays them. A failing case exits 1. --format junit writes JUnit. --format text is the default. --case runs one name. Editing the prompt file changes what the next test sees.
- **Acceptance:**
  - [x] A fixed case exits 0.
  - [x] Putting the failure back exits 1.
  - [x] An unknown format exits 1.
- **Test cases:** All cases; one case; junit; a missing cases directory.
- **UI checks:** none
- **Dependencies:** CLI-08, DEMO-03
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### CLI-10 Serve

- **Priority:** P1
- **Status:** PASSED
- **Files:** src/undoom/cli.py, src/undoom/api.py
- **Expected behavior:** undoom serve binds 127.0.0.1:8787 unless --host and --port say otherwise. --demo refuses writes. Without the ui extra the command exits 1 and names pip install 'undoom[ui]'.
- **Acceptance:**
  - [x] /api/meta returns the demo flag.
  - [x] A port already in use fails without corrupting the store.
- **Test cases:** Default bind; --demo; the extra missing.
- **UI checks:** none
- **Dependencies:** API-01
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### API-01 Read endpoints

- **Priority:** P0
- **Status:** PASSED
- **Files:** src/undoom/api.py
- **Expected behavior:** The six GET routes return JSON. An unknown run or replay is 404 with a detail string. OpenAPI and Redoc are disabled.
- **Acceptance:**
  - [x] /api/runs returns the stored runs.
  - [x] /docs is not served.
  - [x] An unknown id is 404.
- **Test cases:** Empty store; one run; a missing id; a request to /docs.
- **UI checks:** none
- **Dependencies:** STORE-01
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### API-02 Replay and promote

- **Priority:** P0
- **Status:** PASSED
- **Files:** src/undoom/api.py
- **Expected behavior:** POST /api/replay takes one change and stores a replay. POST /api/promote writes a case and returns its path. A bad body is 400. A missing run is 404.
- **Acceptance:**
  - [x] A prompt replay returns a verdict.
  - [x] Two changes are 400.
  - [x] Promote of a missing replay is 404.
- **Test cases:** Prompt text; prompt file; model; an extra unknown field; an empty name.
- **UI checks:** none
- **Dependencies:** CLI-04, CLI-08
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### API-03 Demo writes

- **Priority:** P0
- **Status:** PASSED
- **Files:** src/undoom/api.py
- **Expected behavior:** When the app is created with demo=True, POST /api/replay and POST /api/promote return 403 "demo mode does not accept writes" and do not change the store or the cases directory.
- **Acceptance:**
  - [x] Both posts are 403.
  - [x] GET routes still return the fixtures or store contents.
- **Test cases:** Replay; promote; a following GET.
- **UI checks:** none
- **Dependencies:** API-02
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### API-04 Local CORS

- **Priority:** P1
- **Status:** PASSED
- **Files:** src/undoom/api.py
- **Expected behavior:** The CORS middleware allows http://localhost and http://127.0.0.1 with an optional port. Another origin is not allowed.
- **Acceptance:**
  - [x] An Origin of http://127.0.0.1:3000 is reflected.
  - [x] An Origin of https://example.com is not.
- **Test cases:** Localhost; 127.0.0.1 with a port; a public https origin.
- **UI checks:** none
- **Dependencies:** API-01
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### UI-01 Run list

- **Priority:** P1
- **Status:** PASSED
- **Files:** apps/ui/app/page.tsx, apps/ui/lib/data.ts
- **Expected behavior:** / shows captured runs with status, name, agent, and failure reason. An empty library says "No runs yet."
- **Acceptance:**
  - [x] Each run links to /runs/{id}.
  - [x] A run with no failure says "no failure recorded".
- **Test cases:** Demo fixtures; an empty API; a long reason.
- **UI checks:** The heading is Captured runs. The nav marks Runs.
- **Dependencies:** UI-06
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### UI-02 Run timeline

- **Priority:** P1
- **Status:** PASSED
- **Files:** apps/ui/app/runs/[id]/page.tsx, apps/ui/app/timeline.tsx
- **Expected behavior:** The run page lists the recorded steps in order, including tool names and results.
- **Acceptance:**
  - [x] A known fixture id renders its steps.
  - [x] An unknown id does not pretend the run exists.
- **Test cases:** The order-lookup fixture; a made-up id.
- **UI checks:** Steps stay readable at 360 and 1440.
- **Dependencies:** UI-01
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### UI-03 Diff

- **Priority:** P1
- **Status:** PASSED
- **Files:** apps/ui/app/diff/[id]/page.tsx
- **Expected behavior:** The diff page shows the source run and the replay, including the verdict and the assistant text. The text is not presented as the pass/fail check.
- **Acceptance:**
  - [x] A fixture replay shows its verdict.
  - [x] The changed field is identifiable.
- **Test cases:** A fixed replay; a still-failing replay if the fixture has one.
- **UI checks:** Columns stack below 720px.
- **Dependencies:** UI-02
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### UI-04 Suite

- **Priority:** P1
- **Status:** PASSED
- **Files:** apps/ui/app/suite/page.tsx
- **Expected behavior:** /suite lists the case files the library loaded, including the name and what the case locks.
- **Acceptance:**
  - [x] The demo fixture case is listed.
  - [x] An empty suite does not throw.
- **Test cases:** Demo fixtures; a local API with no cases.
- **UI checks:** The Suite nav link lands here.
- **Dependencies:** UI-06
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### UI-05 Replay and promote forms

- **Priority:** P1
- **Status:** PASSED
- **Files:** apps/ui/app/replay-form.tsx, apps/ui/app/promote-form.tsx
- **Expected behavior:** Against a local undoom serve, the forms submit one change and can promote a fixed replay. In the demo build the forms are not a write path.
- **Acceptance:**
  - [x] A local form posts to the API and shows the verdict.
  - [x] The demo build does not write a case.
- **Test cases:** Prompt file; two fields filled; promote of a fixed replay; demo mode.
- **UI checks:** Errors are visible. Buttons are keyboard reachable.
- **Dependencies:** API-02, API-03
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### UI-06 Synthetic demo

- **Priority:** P0
- **Status:** PASSED
- **Files:** apps/ui/lib/data.ts, apps/ui/fixtures/demo.json, apps/ui/app/page.tsx
- **Expected behavior:** NEXT_PUBLIC_DEMO=1 never calls the API. It reads the committed fixture and shows "Synthetic demo." The README says the public host is built this way and has no customer data.
- **Acceptance:**
  - [x] The banner is present.
  - [x] The fixture runs render with the network to the API blocked.
- **Test cases:** Demo on; demo off with the API up; demo off with the API down.
- **UI checks:** The banner is readable on the dark background.
- **Dependencies:** none
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### UI-07 Offline state

- **Priority:** P1
- **Status:** PASSED
- **Files:** apps/ui/lib/data.ts, apps/ui/app/page.tsx
- **Expected behavior:** When the API cannot be reached and demo mode is off, the page says the library is offline and shows no runs.
- **Acceptance:**
  - [x] A refused connection does not crash the page.
  - [x] It does not fall back to the synthetic fixture.
- **Test cases:** Nothing on 8787; a 500 from the API.
- **UI checks:** The offline message is visible without a console error being the only signal.
- **Dependencies:** UI-01
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### UI-08 Responsive layout

- **Priority:** P2
- **Status:** PASSED
- **Files:** apps/ui/app/globals.css
- **Expected behavior:** At 720px and below, .run and .columns become one column and the header becomes a grid.
- **Acceptance:**
  - [x] 360 and 768 do not overflow the page.
  - [x] 1024 and 1440 keep the wide layout.
- **Test cases:** 360, 768, 1024, and 1440 on the runs, diff, and suite pages.
- **UI checks:** No horizontal scroll. The nav remains reachable.
- **Dependencies:** UI-01
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### UI-09 Title and focus

- **Priority:** P1
- **Status:** PASSED
- **Files:** apps/ui/app/layout.tsx, apps/ui/app/globals.css
- **Expected behavior:** The document title is Undoom and the description is the replay sentence. The language is en. The stylesheet sets color-scheme dark. It does not set a focus-visible outline.
- **Acceptance:**
  - [x] The title is Undoom.
  - [x] Tabbing shows a visible focus ring, or the missing ring is recorded as a defect.
- **Test cases:** Keyboard from the mark through Runs and Suite.
- **UI checks:** Contrast of muted text on the dark background.
- **Dependencies:** UI-01
- **Suspected bugs:** none. Keyboard focus shows the browser outline. /favicon.ico was 404.
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### UI-10 Security headers

- **Priority:** P1
- **Status:** PASSED
- **Files:** apps/ui/next.config.ts
- **Expected behavior:** The public UI should send nosniff, a strict referrer policy, framing denial, and a content security policy that still allows the Next.js page to render. This repo does not set those headers.
- **Acceptance:**
  - [x] A response from the demo build includes the four headers.
  - [x] The runs page still renders and the console has no CSP errors.
- **Test cases:** The home page; a run page; a static asset.
- **UI checks:** The page is not blank after the policy is added.
- **Dependencies:** UI-06
- **Suspected bugs:** none
- **Bugs Found:** The production build sent no nosniff, referrer policy, framing denial, or CSP.
- **Bugs Fixed:** next.config.ts sets those four headers. The home page, a run page, and a stylesheet still render, with no CSP console errors.
- **UI Issues Fixed:**
- **Files Changed:** apps/ui/next.config.ts
- **Notes:** Passed. GAP-01 is built.

### DEMO-01 Order lookup

- **Priority:** P0
- **Status:** PASSED
- **Files:** examples/order_lookup/demo.py, examples/order_lookup/prompts.py, examples/order_lookup/tools.py
- **Expected behavior:** The buggy prompt refunds order 1042 after looking it up. The fixed prompt refunds only when the user asks. The script records both and can promote the fixed replay.
- **Acceptance:**
  - [x] The failed run names refund_order.
  - [x] The fixed replay does not call refund_order.
- **Test cases:** Run the demo into a temp directory; show the failed run; show the replay.
- **UI checks:** none
- **Dependencies:** DEMO-03
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### DEMO-02 Docker demo

- **Priority:** P1
- **Status:** PASSED
- **Files:** docker/compose.yml, docker/Dockerfile, docker/demo-entrypoint.sh
- **Expected behavior:** The demo service builds from the repo Dockerfile and leaves the case file on the mounted volume. The postgres service is behind the postgres profile and is not required for the demo.
- **Acceptance:**
  - [x] The compose file matches that layout.
  - [x] The image does not need a live model key for the demo.
- **Test cases:** Read the compose file. Step 2 runs the demo only if Docker can build it without touching other projects.
- **UI checks:** none
- **Dependencies:** DEMO-01
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### DEMO-03 Fake provider

- **Priority:** P0
- **Status:** PASSED
- **Files:** examples/order_lookup/fake.py
- **Expected behavior:** UNDOOM_MODEL_PROVIDER=examples.order_lookup.fake:provider answers the order-lookup story without a network call. Putting the refund instruction back into the fixed prompt makes undoom test fail.
- **Acceptance:**
  - [x] undoom test exits 0 with the fixed prompt.
  - [x] Restoring the refund instruction exits 1.
  - [x] No API key is read.
- **Test cases:** Fixed prompt; buggy prompt; the provider flag missing.
- **UI checks:** none
- **Dependencies:** CLI-09
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### DEVOPS-01 CI

- **Priority:** P0
- **Status:** PASSED
- **Files:** .github/workflows/ci.yml
- **Expected behavior:** Push and pull_request run ruff, ruff format, mypy, and pytest on Python 3.11 and 3.12 with Postgres available. A second job builds apps/ui with NEXT_PUBLIC_DEMO=1 on Node 22.
- **Acceptance:**
  - [x] The workflow file contains those steps.
  - [x] This step did not run it.
- **Test cases:** Read the workflow. Step 2 runs the same commands locally.
- **UI checks:** none
- **Dependencies:** none
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### DEVOPS-02 PyPI

- **Priority:** P0
- **Status:** PASSED
- **Files:** .github/workflows/publish.yml, pyproject.toml
- **Expected behavior:** A tag matching v* builds with uv and publishes through trusted publishing. The project version is 1.0.2. Tag v1.0.1 is the previous release. PyPI was read and served 1.0.1 before this release.
- **Acceptance:**
  - [x] The workflow is tag-only.
  - [x] The version in pyproject.toml is 1.0.2.
- **Test cases:** Read the workflow and the tag. Step 2 checks PyPI only as a read.
- **UI checks:** none
- **Dependencies:** DEVOPS-03
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### DEVOPS-03 Python versions

- **Priority:** P1
- **Status:** PASSED
- **Files:** pyproject.toml, .python-version, .github/workflows/ci.yml
- **Expected behavior:** The package requires Python 3.11 or newer. CI tests 3.11 and 3.12. .python-version pins the local interpreter.
- **Acceptance:**
  - [x] requires-python is >=3.11.
  - [x] The local interpreter meets it, or the gap is recorded.
- **Test cases:** Read the files. Step 2 runs python3 --version.
- **UI checks:** none
- **Dependencies:** none
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

### DEVOPS-04 Example workflow

- **Priority:** P2
- **Status:** PASSED
- **Files:** examples/ci/undoom.yml, README.md
- **Expected behavior:** The example installs undoom and runs undoom test --format junit on push and pull_request, with OPENAI_API_KEY from the repo secrets. The fake provider is the path that does not need that key.
- **Acceptance:**
  - [x] The example file matches the README snippet.
  - [x] It is an example, not the repo's own CI.
- **Test cases:** Read both files.
- **UI checks:** none
- **Dependencies:** CLI-09
- **Suspected bugs:** none
- **Bugs Found:**
- **Bugs Fixed:**
- **UI Issues Fixed:**
- **Files Changed:** none
- **Notes:** Passed.

## Assumptions

- Testing started from commit 5a96cbb on branch dev. origin/main bad51db was the merge of that commit. Fixes stayed on dev. main is protected, so the ship step is a pull request.
- logo.svg is untracked and is not part of the product.
- The public demo was read with curl before the header change. The local production build was checked in Chrome after it.
- There is no account system and no billing.
- Postgres was a temporary database on 127.0.0.1:54334. It is not a production database.

## Risks

- A case file embeds tool arguments and results. SECURITY.md says to read a case before committing it. Redaction does not know every secret.
- A tool override runs with the privileges of the test process.
- Replay calls a live model at temperature 0 unless the provider is a local factory. The tool I/O is what is frozen, not the assistant text.
- CORS on the local API allows any port on localhost. It does not allow a public website to call a developer's serve process.
- Next.js 16.4.3 reports a known security advisory. The build and the dev server continue after the reminder. The upgrade is a separate step.

## Whole-Product Check

- The local API has no session. It binds to 127.0.0.1. Demo mode refuses writes. OpenAPI is off.
- The public UI is a static fixture build. It does not receive customer traces.
- Security headers are set on the UI. The local API is loopback CORS only.
- pytest, ruff, and mypy passed on Python 3.15. Postgres passed against a temporary server. The demo container passed.
- P0 journeys: record, redact, import, replay, promote, test, and the synthetic demo page.
- Titles, the missing-page state, and the favicon were checked. Keyboard focus shows the browser ring. Contrast of the muted text on the dark background is about 7.5.
- No secrets were added. logo.svg stays untracked.

## Final Summary

Undoom records a failure, replays one change against the cassette, and locks a fixed replay into `undoom test`. The synthetic demo and the local UI were exercised. Three defects were fixed: the formatter failure that turned CI red, a missing tool override that aborted instead of recording verdict error, and the public UI headers. The missing-page layout and the favicon were fixed as well.

## Totals

- Features: 40. Passed: 40. Blocked: 0.
- Priority: P0 22, P1 16, P2 2.
- Bugs found: 3. Bugs fixed: 3. UI issues fixed: 2.
- Gaps: 7. One was built. Six stay deferred.

## Still Blocked

None.

## Known Limitations

- Production monitoring, tool permissions, sandboxing, a general benchmark, accounts, billing, a light theme, and hosted capture stay deferred.
- Redaction is not a guarantee. A case file can still contain customer data.
- A tool override runs with the test process privileges.
- The demo UI is Next.js 16.4.6, the release that addresses the advisory found in 16.4.3.
- PyPI serves 1.0.1 until tag v1.0.2 is published.

## Launch Checklist

- [x] Fixes are on dev.
- [x] The report matches the canvas.
- [ ] Pull request from dev to main is merged.
- [ ] The production demo deploy is the merge commit and sends the new headers.
- [ ] Tag v1.0.2 points at that commit and the publish workflow succeeds.

## Decision

GO. The library, the local API, the demo container, and the UI passed. Ship through a pull request to main, then tag v1.0.2.
