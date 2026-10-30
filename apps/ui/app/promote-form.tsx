"use client";

import { useState } from "react";

export function PromoteForm({ replayId }: { replayId: string }) {
  const [name, setName] = useState("");
  const [expectTools, setExpectTools] = useState(false);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");
    const base = process.env.NEXT_PUBLIC_UNDOOM_API ?? "http://127.0.0.1:8787";
    try {
      const response = await fetch(`${base}/api/promote`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          replay_id: replayId,
          name,
          expect_tools: expectTools,
        }),
      });
      const payload = (await response.json()) as { path?: string; detail?: string };
      if (!response.ok || !payload.path) {
        setError(typeof payload.detail === "string" ? payload.detail : "Promote failed");
        setPending(false);
        return;
      }
      window.location.assign("/suite");
    } catch {
      setError("Could not reach undoom serve");
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit}>
      <strong>Promote to a regression case</strong>
      <label>
        Case name
        <input
          onChange={(event) => setName(event.target.value)}
          pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
          placeholder="no-unsolicited-refund"
          required
          title="lowercase slug such as no-unsolicited-refund"
          value={name}
        />
      </label>
      <label>
        <input
          checked={expectTools}
          onChange={(event) => setExpectTools(event.target.checked)}
          type="checkbox"
        />
        also lock the successful tool sequence
      </label>
      {error ? <p className="error">{error}</p> : null}
      <button disabled={pending} type="submit">
        {pending ? "Promoting" : "Promote"}
      </button>
    </form>
  );
}
