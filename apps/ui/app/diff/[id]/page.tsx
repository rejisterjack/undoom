import Link from "next/link";
import { notFound } from "next/navigation";

import { loadLibrary, recordedReplays } from "@/lib/data";

import { Status } from "../../status";

export function generateStaticParams() {
  return recordedReplays().map((replay) => ({ id: replay.id }));
}

export default async function DiffPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const library = await loadLibrary();
  const replay = library.replays.find((item) => item.id === id);
  if (!replay) notFound();
  const source = library.runs.find((item) => item.id === replay.source_run_id);
  return (
    <main>
      <p>
        <Link href={source ? `/runs/${source.id}` : "/"}>Back</Link>
      </p>
      <h1>Trajectory</h1>
      <p>
        <Status value={replay.verdict} />
      </p>
      <p className="meta">
        change: {replay.changeset.kind}
        {replay.changeset.prompt_file ? ` ${replay.changeset.prompt_file}` : ""}
        {replay.changeset.model ? ` ${replay.changeset.model}` : ""}
        {replay.changeset.tool_name ? ` ${replay.changeset.tool_name}` : ""}
      </p>
      <section className="diff">
        {replay.diff.tool_diffs.map((item, index) => (
          <article className={item.op} key={`${item.op}-${index}`}>
            <div>{item.op}</div>
            <div>{item.detail}</div>
          </article>
        ))}
      </section>
      <div className="columns">
        <section>
          <h2>Failed run</h2>
          <p>{replay.diff.final_text_source ?? "—"}</p>
        </section>
        <section>
          <h2>Replay</h2>
          <p>{replay.diff.final_text_replay ?? "—"}</p>
        </section>
      </div>
      {replay.notes.length > 0 ? <p className="meta">{replay.notes.join(" ")}</p> : null}
    </main>
  );
}
