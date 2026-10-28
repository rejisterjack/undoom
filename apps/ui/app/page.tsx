import Link from "next/link";

import { loadLibrary } from "@/lib/data";

import { Status } from "./status";

export default async function HomePage() {
  const library = await loadLibrary();
  return (
    <main>
      <Notice library={library} />
      <h1>Captured runs</h1>
      <p className="lede">
        A failure is a recorded tool-calling run. Open one, then compare it with the replay that
        changed a single thing.
      </p>
      {library.runs.length === 0 ? (
        <p>No runs yet.</p>
      ) : (
        <div className="list">
          {library.runs.map((run) => (
            <Link className="run" href={`/runs/${run.id}`} key={run.id}>
              <Status value={run.status} />
              <strong>{run.name}</strong>
              <small>{run.agent}</small>
              <span className="reason">{run.failure_reason ?? "no failure recorded"}</span>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}

function Notice({
  library,
}: {
  library: Awaited<ReturnType<typeof loadLibrary>>;
}) {
  if (library.demo) {
    return (
      <p className="banner">
        <strong>Synthetic demo.</strong> These traces were generated for the order-lookup story.
        Nothing here was captured from a production agent.
      </p>
    );
  }
  if (library.offline) {
    return (
      <p className="offline">
        <strong>API unreachable.</strong> Start <code>undoom serve</code> or build with{" "}
        <code>NEXT_PUBLIC_DEMO=1</code>.
      </p>
    );
  }
  return null;
}
