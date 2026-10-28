export type RunStatus = "running" | "success" | "failure" | "error";

export type ToolCall = {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
};

export type ModelStep = {
  kind: "model";
  model: string;
  messages: Array<Record<string, unknown>>;
  response_text: string | null;
  tool_calls: ToolCall[];
};

export type ToolStep = {
  kind: "tool";
  call_id: string;
  name: string;
  arguments: Record<string, unknown>;
  result: unknown;
  error: string | null;
};

export type Step = ModelStep | ToolStep;

export type Run = {
  id: string;
  agent: string;
  name: string;
  status: RunStatus;
  failure_reason: string | null;
  unexpected_tools: string[];
  created_at: string;
  steps: Step[];
};

export type StepDiff = {
  op: "same" | "added" | "removed" | "changed";
  detail: string;
  source_tool: string | null;
  replay_tool: string | null;
};

export type Replay = {
  id: string;
  source_run_id: string;
  created_at: string;
  verdict: "fixed" | "still_failing" | "diverged" | "error";
  notes: string[];
  changeset: {
    kind: "prompt" | "model" | "tool";
    prompt_text: string | null;
    prompt_file: string | null;
    model: string | null;
    tool_name: string | null;
    tool_entrypoint: string | null;
  };
  diff: {
    tool_diffs: StepDiff[];
    source_tools: string[];
    replay_tools: string[];
    final_text_source: string | null;
    final_text_replay: string | null;
  };
  run: Run;
};

export type CaseFile = {
  name: string;
  source_failure_id: string;
  replay_id: string;
  model: string;
  changeset: Replay["changeset"];
  expectation: {
    failure_reason: string | null;
    absent_tools: string[];
    absent_tool_errors: string[];
    required_tool_sequence: string[] | null;
  };
};

export type Library = {
  runs: Run[];
  replays: Replay[];
  cases: CaseFile[];
  demo: boolean;
  offline: boolean;
};
