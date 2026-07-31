"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { API } from "@/lib/api";

type Service = {
  name: string;
  slug: string;
  status: string;
  uptime_24h: number | null;
  avg_latency_ms: number | null;
};

type StatusPage = { handle: string; overall: string; services: Service[] };

export default function PublicStatus() {
  const params = useParams<{ handle: string }>();
  const [data, setData] = useState<StatusPage | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      const res = await fetch(`${API}/api/status/${params.handle}`, { cache: "no-store" });
      if (!res.ok) {
        setError("No status page at that address.");
        return;
      }
      setData(await res.json());
    }
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, [params.handle]);

  if (error) return <div className="shell"><div className="alert">{error}</div></div>;
  if (!data) return <div className="shell"><div className="empty">Loading…</div></div>;

  const colour =
    data.overall === "operational" ? "var(--up)" : data.overall === "degraded" ? "var(--degraded)" : "var(--down)";

  return (
    <div className="shell">
      <div className="topbar">
        <div className="brand">
          <span className="flame" />
          {data.handle}
          <small>status</small>
        </div>
        <span className="mono muted" style={{ fontSize: 11 }}>
          updates every 30s
        </span>
      </div>

      <h1 style={{ color: colour }}>
        {data.overall === "operational" ? "All systems operational" : `Service ${data.overall}`}
      </h1>
      <p className="eyebrow">Live from Vigil</p>

      <div className="rows">
        {data.services.map((s) => (
          <div className="row" key={s.slug} style={{ gridTemplateColumns: "1fr 140px 120px" }}>
            <div className="name">{s.name}</div>
            <div>
              <span className={`pill ${s.status}`}>
                <span className="dot" />
                {s.status}
              </span>
            </div>
            <div className="right">
              <div className="pct">{s.uptime_24h?.toFixed(2) ?? "—"}%</div>
              <div className="sub">24h uptime</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
