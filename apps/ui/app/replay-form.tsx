"use client";

import { useState } from "react";

type Kind = "prompt" | "model" | "tool";
type PromptSource = "text" | "file";

export function ReplayForm({ runId }: { runId: string }) {
  const [kind, setKind] = useState<Kind>("prompt");
  const [promptSource, setPromptSource] = useState<PromptSource>("text");
  const [prompt, setPrompt] = useState("");
  const [promptFile, setPromptFile] = useState("");
  const [model, setModel] = useState("");
  const [toolName, setToolName] = useState("");
  const [entrypoint, setEntrypoint] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");
    const body: Record<string, string> = { run_id: runId };
    if (kind === "prompt") {
      if (promptSource === "file") body.prompt_file = promptFile;
      else body.prompt_text = prompt;
    }
    if (kind === "model") body.model = model;
    if (kind === "tool") {
      body.tool_name = toolName;
      body.tool_entrypoint = entrypoint;
    }
    const base = process.env.NEXT_PUBLIC_UNDOOM_API ?? "http://127.0.0.1:8787";
    try {
      const response = await fetch(`${base}/api/replay`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });
      const payload = (await response.json()) as { id?: string; detail?: string };
      if (!response.ok || !payload.id) {
        setError(typeof payload.detail === "string" ? payload.detail : "Replay failed");
        setPending(false);
        return;
      }
      window.location.assign(`/diff/${payload.id}`);
    } catch {
      setError("Could not reach undoom serve");
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit}>
      <strong>Replay with one change</strong>
      <div className="choices">
        {(["prompt", "model", "tool"] as const).map((option) => (
          <label key={option}>
            <input
              checked={kind === option}
              name="kind"
              onChange={() => setKind(option)}
              type="radio"
            />
            {option}
          </label>
        ))}
      </div>
      {kind === "prompt" ? (
        <>
          <div className="choices">
            <label>
              <input
                checked={promptSource === "text"}
                name="promptSource"
                onChange={() => setPromptSource("text")}
                type="radio"
              />
              inline text
            </label>
            <label>
              <input
                checked={promptSource === "file"}
                name="promptSource"
                onChange={() => setPromptSource("file")}
                type="radio"
              />
              file path
            </label>
          </div>
          {promptSource === "text" ? (
            <label>
              Prompt
              <textarea
                onChange={(event) => setPrompt(event.target.value)}
                required
                rows={4}
                value={prompt}
              />
            </label>
          ) : (
            <label>
              Prompt file on the machine running undoom serve
              <input
                onChange={(event) => setPromptFile(event.target.value)}
                placeholder="prompts/support.txt"
                required
                value={promptFile}
              />
            </label>
          )}
        </>
      ) : null}
      {kind === "model" ? (
        <label>
          Model id
          <input onChange={(event) => setModel(event.target.value)} required value={model} />
        </label>
      ) : null}
      {kind === "tool" ? (
        <>
          <label>
            Tool name
            <input onChange={(event) => setToolName(event.target.value)} required value={toolName} />
          </label>
          <label>
            Entrypoint
            <input
              onChange={(event) => setEntrypoint(event.target.value)}
              placeholder="module:function"
              required
              value={entrypoint}
            />
          </label>
        </>
      ) : null}
      {error ? <p className="error">{error}</p> : null}
      <button disabled={pending} type="submit">
        {pending ? "Replaying" : "Replay"}
      </button>
    </form>
  );
}
