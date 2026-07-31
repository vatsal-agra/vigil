"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { API, saveSession } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("demo@vigil.dev");
  const [password, setPassword] = useState("vigil-demo-2026");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/auth/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail ?? "Something went wrong.");
      saveSession(body.access_token, body.handle);
      router.push("/");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <div className="brand" style={{ marginBottom: 8 }}>
          <span className="flame" />
          Vigil
        </div>
        <p className="eyebrow">Keep watch on what you shipped</p>

        {error && <div className="alert">{error}</div>}

        <div className="card">
          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
            />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
            />
          </div>
          <button className="btn primary" onClick={submit} disabled={busy} style={{ width: "100%" }}>
            {busy ? "Working…" : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </div>

        <p className="muted" style={{ marginTop: 16, textAlign: "center" }}>
          {mode === "login" ? "No account yet? " : "Already have one? "}
          <button
            className="btn"
            style={{ padding: "2px 8px", fontSize: 12 }}
            onClick={() => setMode(mode === "login" ? "register" : "login")}
          >
            {mode === "login" ? "Create one" : "Sign in"}
          </button>
        </p>
      </div>
    </div>
  );
}
