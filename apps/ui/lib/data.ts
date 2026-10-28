import fixture from "../fixtures/demo.json";

import type { CaseFile, Library, Replay, Run } from "./types";

const recorded = fixture as {
  runs: Run[];
  replays: Replay[];
  cases: CaseFile[];
};

const demoMode = process.env.NEXT_PUBLIC_DEMO === "1";

export function recordedRuns(): Run[] {
  return recorded.runs;
}

export function recordedReplays(): Replay[] {
  return recorded.replays;
}

export async function loadLibrary(): Promise<Library> {
  if (demoMode) {
    return {
      runs: recorded.runs,
      replays: recorded.replays,
      cases: recorded.cases,
      demo: true,
      offline: false,
    };
  }
  const base = process.env.NEXT_PUBLIC_UNDOOM_API ?? "http://127.0.0.1:8787";
  try {
    const [runsResponse, replaysResponse, casesResponse, metaResponse] = await Promise.all([
      fetch(`${base}/api/runs`, { cache: "no-store" }),
      fetch(`${base}/api/replays`, { cache: "no-store" }),
      fetch(`${base}/api/cases`, { cache: "no-store" }),
      fetch(`${base}/api/meta`, { cache: "no-store" }),
    ]);
    if (!runsResponse.ok || !replaysResponse.ok || !casesResponse.ok || !metaResponse.ok) {
      throw new Error("undoom serve returned an error");
    }
    const runsBody = (await runsResponse.json()) as { runs: Run[] };
    const replaysBody = (await replaysResponse.json()) as { replays: Replay[] };
    const casesBody = (await casesResponse.json()) as { cases: CaseFile[] };
    const meta = (await metaResponse.json()) as { demo: boolean };
    return {
      runs: runsBody.runs,
      replays: replaysBody.replays,
      cases: casesBody.cases,
      demo: meta.demo,
      offline: false,
    };
  } catch {
    return { runs: [], replays: [], cases: [], demo: false, offline: true };
  }
}
