"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, Check, Monitor, relativeTime, token } from "@/lib/api";

function LatencyChart({ checks }: { checks: Check[] }) {
  const points = checks.filter((c) => c.latency_ms !== null);
  if (points.length < 2) {
    return <div className="empty">Not enough samples yet. Come back in a few minutes.</div>;
  }

  const W = 900;
  const H = 160;
  const max = Math.max(...points.map((p) => p.latency_ms ?? 0)) * 1.15;
  const path = points
    .map((p, i) => {
      const x = (i / (points.length - 1)) * W;
      const y = H - ((p.latency_ms ?? 0) / max) * (H - 12);
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <svg className="chart" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img"
         aria-label="Response time over the last 24 hours">
      {[0.25, 0.5, 0.75].map((f) => (
        <line key={f} x1="0" x2={W} y1={H * f} y2={H * f} stroke="var(--line)" strokeWidth="1" />
      ))}
      <path d={`${path} L${W},${H} L0,${H} Z`} fill="rgba(122,162,255,0.10)" />
      <path d={path} fill="none" stroke="var(--signal)" strokeWidth="2" vectorEffect="non-scaling-stroke" />
      {checks.map((c, i) =>
        c.ok ? null : (
          <line
            key={i}
            x1={(i / Math.max(1, checks.length - 1)) * W}
            x2={(i / Math.max(1, checks.length - 1)) * W}
            y1="0"
            y2={H}
            stroke="var(--down)"
            strokeWidth="1.5"
            opacity="0.5"
          />
        )
      )}
    </svg>
  );
}

export default function MonitorDetail() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [monitor, setMonitor] = useState<Monitor | null>(null);
  const [checks, setChecks] = useState<Check[]>([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [m, c] = await Promise.all([
        api<Monitor>(`/api/monitors/${params.id}`),
        api<Check[]>(`/api/monitors/${params.id}/checks?hours=24`),
      ]);
      setMonitor(m);
      setChecks(c);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load this monitor.");
    }
  }, [params.id]);

  useEffect(() => {
    if (!token()) {
      router.push("/login");
      return;
    }
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, [load, router]);

  async function remove() {
    await api(`/api/monitors/${params.id}`, { method: "DELETE" });
    router.push("/");
  }

  async function togglePublic() {
    if (!monitor) return;
    await api(`/api/monitors/${params.id}`, {
      method: "PATCH",
      body: JSON.stringify({ is_public: !monitor.is_public }),
    });
    load();
  }

  if (error) return <div className="shell"><div className="alert">{error}</div></div>;
  if (!monitor) return <div className="shell"><div className="empty">Loading…</div></div>;

  const failures = checks.filter((c) => !c.ok).length;

  return (
    <div className="shell">
      <div className="topbar">
        <div className="brand">
          <span className="flame" />
          Vigil
        </div>
        <Link className="btn" href="/">
          Back to dashboard
        </Link>
      </div>

      <h1>{monitor.name}</h1>
      <p className="eyebrow">
        {monitor.method} {monitor.url} · every {monitor.interval_seconds}s
      </p>

      <div className="rail">
        <div>
          <div className="k">Status</div>
          <div className="v" style={{ fontSize: 18, textTransform: "uppercase" }}>
            {monitor.current_status}
          </div>
        </div>
        <div>
          <div className="k">Uptime 24h</div>
          <div className="v">{monitor.uptime_24h?.toFixed(2) ?? "—"}%</div>
        </div>
        <div>
          <div className="k">Avg response</div>
          <div className="v">{monitor.avg_latency_ms ? `${Math.round(monitor.avg_latency_ms)}ms` : "—"}</div>
        </div>
        <div>
          <div className="k">Failed checks</div>
          <div className="v">{failures}</div>
        </div>
      </div>

      <h2>Response time, last 24 hours</h2>
      <div className="card" style={{ padding: 14 }}>
        <LatencyChart checks={checks} />
      </div>

      <div className="stack-32">
        <h2>Latest checks</h2>
        <div className="card">
          {[...checks].reverse().slice(0, 10).map((c, i) => (
            <div className="incident" key={i}>
              <span className="when">{relativeTime(c.checked_at)}</span>
              <span className="mono" style={{ fontSize: 12 }}>
                {c.ok ? (
                  <span style={{ color: "var(--up)" }}>{c.status_code} OK</span>
                ) : (
                  <span style={{ color: "var(--down)" }}>{c.error}</span>
                )}
                <span className="muted"> · {c.latency_ms ? `${Math.round(c.latency_ms)} ms` : "no response"}</span>
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="stack-32" style={{ display: "flex", gap: 10 }}>
        <button className="btn" onClick={togglePublic}>
          {monitor.is_public ? "Remove from status page" : "Show on status page"}
        </button>
        <button className="btn" onClick={remove}>
          Stop watching
        </button>
      </div>
    </div>
  );
}
