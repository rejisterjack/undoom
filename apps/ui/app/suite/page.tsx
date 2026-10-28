import Link from "next/link";

import { loadLibrary } from "@/lib/data";

export default async function SuitePage() {
  const library = await loadLibrary();
  return (
    <main>
      <h1>Regression suite</h1>
      <p className="lede">
        A case stays green while the original failure stays gone. The check is the failure
        signature, not the exact assistant text.
      </p>
      {library.offline ? <p className="offline">The local API is not running.</p> : null}
      {library.cases.length === 0 ? (
        <p>No cases yet.</p>
      ) : (
        <div className="suite">
          {library.cases.map((item) => (
            <article key={item.name}>
              <h2>
                <Link href={`/diff/${item.replay_id}`}>{item.name}</Link>
              </h2>
              <p>must not call: {item.expectation.absent_tools.join(", ") || "none"}</p>
              <p className="meta">
                {item.changeset.kind}
                {item.changeset.prompt_file ? ` · ${item.changeset.prompt_file}` : ""}
              </p>
              {item.expectation.failure_reason ? <p>{item.expectation.failure_reason}</p> : null}
            </article>
          ))}
        </div>
      )}
    </main>
  );
}
