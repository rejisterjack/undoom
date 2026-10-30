import Link from "next/link";
import { notFound } from "next/navigation";

import { loadLibrary, recordedRuns } from "@/lib/data";

import { ReplayForm } from "../../replay-form";
import { Status } from "../../status";
import { Timeline } from "../../timeline";

export function generateStaticParams() {
  return recordedRuns().map((run) => ({ id: run.id }));
}

export default async function RunPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const library = await loadLibrary();
  const run = library.runs.find((item) => item.id === id);
  if (!run) notFound();
  const replays = library.replays.filter((item) => item.source_run_id === run.id);
  return (
    <main>
      <p>
        <Link href="/">Runs</Link>
      </p>
      <h1>{run.name}</h1>
      <p>
        <Status value={run.status} /> <span className="meta">{run.agent}</span>
      </p>
      {run.failure_reason ? <p className="callout">{run.failure_reason}</p> : null}
      {run.unexpected_tools.length > 0 ? (
        <p className="meta">unexpected tools: {run.unexpected_tools.join(", ")}</p>
      ) : null}
      <Timeline steps={run.steps} />
      {replays.length === 0 ? (
        <p>No replay has been saved for this run.</p>
      ) : (
        <div className="list">
          {replays.map((replay) => (
            <p key={replay.id}>
              <Link href={`/diff/${replay.id}`}>Compare with the {replay.verdict} replay</Link>
            </p>
          ))}
        </div>
      )}
      {library.demo ? (
        <p className="meta">The demo does not accept a new replay. The comparison above is the recorded fix.</p>
      ) : (
        <ReplayForm runId={run.id} />
      )}
    </main>
  );
}
