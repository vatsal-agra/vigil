"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, clearSession, Incident, Monitor, relativeTime, token } from "@/lib/api";

function Pill({ status }: { status: string }) {
  return (
    <span className={`pill ${status}`}>
      <span className="dot" />
      {status}
    </span>
  );
}

function Strip({ status }: { status: string }) {
  const ticks = Array.from({ length: 48 }, (_, i) => {
    if (status === "down" && i > 40) return "down";
    if (status === "degraded" && i % 7 === 0) return "degraded";
    if (status === "pending") return "empty";
    return "ok";
  });
  return (
    <div className="strip" aria-hidden="true">
      {ticks.map((t, i) => (
        <span
          key={i}
          className={`tick ${t === "ok" ? "" : t}`}
          style={{ height: t === "empty" ? 6 : 12 + ((i * 7) % 18) }}
        />
      ))}
    </div>
  );
}

export default function Dashboard() {
  const router = useRouter();
  const [monitors, setMonitors] = useState<Monitor[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({ name: "", url: "https://" });

  const load = useCallback(async () => {
    try {
      // Open incidents are fetched on their own: the feed is capped at the
      // newest 100, so an old incident that is still open can fall off it.
      const [m, i, open] = await Promise.all([
        api<Monitor[]>("/api/monitors"),
        api<Incident[]>("/api/incidents"),
        api<Incident[]>("/api/incidents?open_only=true"),
      ]);
      setMonitors(m);
      setIncidents([...open, ...i.filter((x) => x.resolved_at)]);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not reach the API.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!token()) {
      router.push("/login");
      return;
    }
    load();
    const id = setInterval(load, 15000);
    return () => clearInterval(id);
  }, [load, router]);

  async function addMonitor() {
    if (!form.name.trim()) return;
    try {
      await api<Monitor>("/api/monitors", { method: "POST", body: JSON.stringify(form) });
      setForm({ name: "", url: "https://" });
      setAdding(false);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not add that monitor.");
    }
  }

  const up = monitors.filter((m) => m.current_status === "up").length;
  const openIncidents = incidents.filter((i) => !i.resolved_at).length;
  const avgUptime =
    monitors.length && monitors.some((m) => m.uptime_24h !== null)
      ? (
          monitors.reduce((a, m) => a + (m.uptime_24h ?? 0), 0) / monitors.length
        ).toFixed(2)
      : "—";

  return (
    <div className="shell">
      <div className="topbar">
        <div className="brand">
          <span className="flame" />
          Vigil
          <small>watch</small>
        </div>
        <button
          className="btn"
          onClick={() => {
            clearSession();
            router.push("/login");
          }}
        >
          Sign out
        </button>
      </div>

      <h1>Everything you asked us to watch</h1>
      <p className="eyebrow">Refreshed every 15 seconds</p>

      {error && <div className="alert">{error}</div>}

      <div className="rail">
        <div>
          <div className="k">Monitors</div>
          <div className="v">{monitors.length}</div>
        </div>
        <div>
          <div className="k">Healthy</div>
          <div className="v" style={{ color: "var(--up)" }}>{up}</div>
        </div>
        <div>
          <div className="k">Open incidents</div>
          <div className="v" style={{ color: openIncidents ? "var(--down)" : undefined }}>
            {openIncidents}
          </div>
        </div>
        <div>
          <div className="k">Avg uptime 24h</div>
          <div className="v">{avgUptime}%</div>
        </div>
      </div>

      <div className="split">
        <h2>Monitors</h2>
        <button className="btn primary" onClick={() => setAdding(!adding)}>
          {adding ? "Cancel" : "Add monitor"}
        </button>
      </div>

      {adding && (
        <div className="card" style={{ marginBottom: 18 }}>
          <div className="field">
            <label htmlFor="mname">Name</label>
            <input
              id="mname"
              value={form.name}
              placeholder="Checkout API"
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </div>
          <div className="field">
            <label htmlFor="murl">URL to check</label>
            <input
              id="murl"
              value={form.url}
              onChange={(e) => setForm({ ...form, url: e.target.value })}
            />
          </div>
          <button className="btn primary" onClick={addMonitor}>
            Start watching
          </button>
        </div>
      )}

      {loading ? (
        <div className="empty">Loading monitors…</div>
      ) : monitors.length === 0 ? (
        <div className="empty">
          Nothing is being watched yet. Add a URL and Vigil checks it every minute.
        </div>
      ) : (
        <div className="rows">
          {monitors.map((m) => (
            <Link className="row" key={m.id} href={`/monitors/${m.id}`}>
              <div>
                <div className="name">{m.name}</div>
                <div className="url">{m.url}</div>
                <div style={{ marginTop: 8 }}>
                  <Pill status={m.current_status} />
                </div>
              </div>
              <Strip status={m.current_status} />
              <div className="right">
                <div className="pct">
                  {m.uptime_24h === null ? "—" : `${m.uptime_24h.toFixed(2)}%`}
                </div>
                <div className="sub">
                  {m.avg_latency_ms ? `${Math.round(m.avg_latency_ms)} ms` : "no data"} ·{" "}
                  {relativeTime(m.last_checked_at)}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      <div className="stack-32">
        <h2>Recent incidents</h2>
        <div className="card">
          {incidents.length === 0 ? (
            <div className="muted">No incidents recorded. Quiet is good.</div>
          ) : (
            incidents.slice(0, 6).map((i) => (
              <div className="incident" key={i.id}>
                <span className="when">{relativeTime(i.started_at)}</span>
                <span>
                  <strong>{i.monitor_name}</strong> — {i.cause}
                  <div className="muted" style={{ marginTop: 4 }}>
                    {i.resolved_at ? i.summary ?? "Resolved." : "Still open."}
                  </div>
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
