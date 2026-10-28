import type { Step } from "@/lib/types";

export function Timeline({ steps }: { steps: Step[] }) {
  return (
    <ol className="timeline">
      {steps.map((step, index) => (
        <li key={`${step.kind}-${index}`}>
          {step.kind === "model" ? (
            <>
              <div className="kind">model {step.model}</div>
              <div>
                tools: {step.tool_calls.map((call) => call.name).join(", ") || "none"}
              </div>
              <div>text: {step.response_text ?? "—"}</div>
            </>
          ) : (
            <>
              <div className="kind">tool {step.name}</div>
              <div>args: {JSON.stringify(step.arguments)}</div>
              <div>result: {JSON.stringify(step.result)}</div>
              {step.error ? <div>error: {step.error}</div> : null}
            </>
          )}
        </li>
      ))}
    </ol>
  );
}
