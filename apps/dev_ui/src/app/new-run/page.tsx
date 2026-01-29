"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

async function fetchFiles(type: "base" | "scenarios" | "sweeps") {
  const res = await fetch(`/api/configs?type=${type}`);
  const j = await res.json();
  return (j.files ?? []) as string[];
}

export default function Page() {
  const router = useRouter();

  const [baseFiles, setBaseFiles] = React.useState<string[]>([]);
  const [scenFiles, setScenFiles] = React.useState<string[]>([]);
  const [sweepFiles, setSweepFiles] = React.useState<string[]>([]);

  const [base, setBase] = React.useState("configs/base.yaml");
  const [scenario, setScenario] = React.useState("configs/scenarios/seoul_allgu_v1.yaml");
  const [sweep, setSweep] = React.useState("configs/sweeps/phase1_time_mult.yaml");

  const [running, setRunning] = React.useState(false);
  const [logs, setLogs] = React.useState<string[]>([]);

  React.useEffect(() => {
    (async () => {
      setBaseFiles(await fetchFiles("base"));
      setScenFiles(await fetchFiles("scenarios"));
      setSweepFiles(await fetchFiles("sweeps"));
    })();
  }, []);

  const start = async () => {
    setRunning(true);
    setLogs([]);

    const res = await fetch("/api/runs/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ base, scenario, sweep }),
    });

    const j = await res.json();
    if (!res.ok) {
      setLogs((x) => [...x, `[UI] start failed: ${j.error ?? "unknown"}`]);
      setRunning(false);
      return;
    }

    const runId = j.runId as string;
    const es = new EventSource(`/api/runs/stream?runId=${encodeURIComponent(runId)}`);

    es.onmessage = (e) => setLogs((x) => [...x, e.data]);

    es.addEventListener("done", (e: any) => {
      const data = JSON.parse(e.data);
      setLogs((x) => [...x, `[UI] done exitCode=${data.exitCode} expId=${data.expId ?? "-"}`]);
      es.close();
      setRunning(false);
      if (data.exitCode === 0 && data.expId) {
        router.push(`/experiments/${encodeURIComponent(data.expId)}`);
      }
    });

    es.onerror = () => {
      setLogs((x) => [...x, "[UI] SSE error"]);
      es.close();
      setRunning(false);
    };
  };

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <h1 className="text-2xl font-bold">New Run</h1>
        <a className="text-sm text-neutral-300 hover:underline" href="/experiments">← Experiments</a>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Pick title="base" value={base} onChange={setBase} options={baseFiles} />
        <Pick title="scenario" value={scenario} onChange={setScenario} options={scenFiles} />
        <Pick title="sweep" value={sweep} onChange={setSweep} options={sweepFiles} />
      </div>

      <button
        disabled={running}
        onClick={start}
        className="px-4 py-2 rounded-lg border border-neutral-800 hover:border-neutral-600 bg-neutral-950 disabled:opacity-50"
      >
        {running ? "Running..." : "Run"}
      </button>

      <div className="border border-neutral-800 rounded-xl p-4 bg-neutral-950">
        <div className="font-semibold mb-2">Logs</div>
        <pre className="text-xs overflow-auto max-h-[520px] whitespace-pre-wrap">
          {logs.join("\n")}
        </pre>
      </div>
    </div>
  );
}

function Pick({
  title,
  value,
  onChange,
  options,
}: {
  title: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
}) {
  return (
    <div className="border border-neutral-800 rounded-xl p-4 bg-neutral-950">
      <div className="text-xs text-neutral-400">{title}</div>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-2 w-full bg-neutral-950 border border-neutral-800 rounded-lg px-2 py-2 text-sm"
      >
        {options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    </div>
  );
}
