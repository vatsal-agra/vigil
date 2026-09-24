#!/usr/bin/env python3
"""Writes the Review 2 design diagrams as editable draw.io files.

  python scripts/make_design_diagrams.py

Outputs to docs/design/diagrams/:
  01-architecture.drawio        copied from infra/architecture.drawio
  02-module-layers.drawio       layered module / component view of the code
  03-data-model.drawio          entity-relationship model
  04-monitor-state-machine.drawio   monitor status + incident lifecycle

Open any of them at https://app.diagrams.net (File -> Open from -> Device).
PNG exports are produced by scripts/export_diagrams.py.
"""
import html
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "design" / "diagrams"

INK, BODY, MUTED = "#12161C", "#3F4650", "#79818D"
FE, FE_BG = "#2B5CD9", "#EEF3FE"
BE, BE_BG = "#0E7C5A", "#E9F6F1"
SVC, SVC_BG = "#B8860B", "#FBF4E3"
DATA, DATA_BG = "#6A4BC4", "#F0ECFB"
CACHE, CACHE_BG = "#C0392B", "#FBEDEB"
WK, WK_BG = "#8E44AD", "#F6EEFA"


class Diagram:
    def __init__(self, did, name, width, height):
        self.did, self.name, self.w, self.h = did, name, width, height
        self.cells = []

    def v(self, cid, value, x, y, w, h, style, parent="1"):
        self.cells.append(
            f'<mxCell id="{cid}" value="{html.escape(value, quote=True)}" style="{style}" '
            f'vertex="1" parent="{parent}"><mxGeometry x="{x}" y="{y}" width="{w}" '
            f'height="{h}" as="geometry"/></mxCell>')

    def e(self, cid, src, tgt, value="", style="", points=(), label_pos=0):
        pts = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in points)
        pts = f'<Array as="points">{pts}</Array>' if pts else ""
        self.cells.append(
            f'<mxCell id="{cid}" value="{html.escape(value, quote=True)}" style="{style}" '
            f'edge="1" parent="1" source="{src}" target="{tgt}"><mxGeometry x="{label_pos}" '
            f'relative="1" as="geometry">{pts}</mxGeometry></mxCell>')

    def title(self, text, sub):
        self.v(f"{self.did}-title", text, 30, 18, self.w - 60, 34,
               f"text;html=1;fontSize=24;fontStyle=1;fontColor={INK};align=left;verticalAlign=middle;")
        self.v(f"{self.did}-sub", sub, 30, 52, self.w - 60, 22,
               f"text;html=1;fontSize=13;fontColor={MUTED};align=left;verticalAlign=middle;")

    def write(self, path):
        body = "\n".join(self.cells)
        path.write_text(
            f'<mxfile host="app.diagrams.net" type="device">\n'
            f'<diagram id="{self.did}" name="{html.escape(self.name, quote=True)}">\n'
            f'<mxGraphModel dx="{self.w}" dy="{self.h}" grid="0" gridSize="10" guides="1" '
            f'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
            f'pageWidth="{self.w}" pageHeight="{self.h}" background="#FFFFFF" math="0" shadow="0">\n'
            f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>\n{body}\n</root>'
            f'</mxGraphModel></diagram></mxfile>\n', encoding="utf-8")
        print("  wrote", path.relative_to(ROOT))


def layer(colour, bg):
    return (f"rounded=1;arcSize=3;whiteSpace=wrap;html=1;fillColor={bg};strokeColor={colour};"
            f"strokeWidth=2;dashed=1;dashPattern=6 4;verticalAlign=top;align=left;spacingLeft=12;"
            f"spacingTop=6;fontSize=13;fontStyle=1;fontColor={colour};")


def module(colour):
    return (f"rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={colour};"
            f"strokeWidth=1.5;align=left;verticalAlign=top;spacingLeft=8;spacingTop=4;"
            f"fontSize=11;fontColor={BODY};")


def mod_label(name, *lines):
    return f"<b style='color:{INK};font-size:12px'>{name}</b><br>" + "<br>".join(lines)


EDGE = (f"edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;"
        f"strokeColor={BODY};strokeWidth=1.5;fontSize=11;fontColor={BODY};labelBackgroundColor=#FFFFFF;")


# ------------------------------------------------------------------ 02 layers

def module_layers():
    d = Diagram("module-layers", "Vigil - Module and Layer View", 1400, 1000)
    d.title("Vigil - Module and Layer View",
            "Each box is one file with one job. Dependencies point downward only; "
            "no module imports from a layer above it.")

    # presentation
    d.v("L1", "PRESENTATION - frontend/ (Next.js, TypeScript)", 30, 90, 1340, 200, layer(FE, FE_BG))
    pages = [
        ("p-login", "app/login/page.tsx", "Sign in / register form", "US-01, US-02"),
        ("p-dash", "app/page.tsx", "Dashboard, add-monitor form,", "incident feed - US-05..09, 15"),
        ("p-detail", "app/monitors/[id]/page.tsx", "Latency chart, check log,", "pause/delete - US-10..12"),
        ("p-status", "app/status/[handle]/page.tsx", "Public status page", "no auth - US-16, 17"),
    ]
    for i, (cid, n, a, b) in enumerate(pages):
        d.v(cid, mod_label(n, a, b), 55 + i * 330, 128, 300, 70, module(FE))
    d.v("api-ts", mod_label("lib/api.ts - the only module that talks HTTP",
                            "Typed fetch client, Bearer token, 401 -> /login, shared Monitor / Check / Incident types"),
        55, 214, 1290, 58, module(FE))
    for i, (cid, *_rest) in enumerate(pages):
        d.e(f"e-{cid}", cid, "api-ts", "", EDGE)

    # api layer
    d.v("L2", "API LAYER - backend/app/routers/ (FastAPI)  thin: validate, authorise, delegate",
        30, 340, 960, 150, layer(BE, BE_BG))
    routers = [
        ("r-auth", "auth.py", "register, login", "issues JWT"),
        ("r-mon", "monitors.py", "CRUD + series,", "_owned() check"),
        ("r-inc", "incidents.py", "feed, ack,", "open-only filter"),
        ("r-status", "status.py", "public page,", "20 s cache"),
    ]
    for i, (cid, n, a, b) in enumerate(routers):
        d.v(cid, mod_label(n, a, b), 55 + i * 232, 380, 210, 70, module(BE))
    d.e("e-http", "api-ts", "L2", "JSON over HTTP + Bearer JWT",
        EDGE + "exitX=0.55;exitY=1;exitDx=0;exitDy=0;entryX=0.8;entryY=0;entryDx=0;entryDy=0;")

    # worker
    d.v("L2w", "WORKER PROCESS - separate container", 1030, 340, 340, 150, layer(WK, WK_BG))
    d.v("w-main", mod_label("worker.py", "wait_for_db(), then", "run_cycle() every 30 s"),
        1060, 380, 280, 70, module(WK))

    # services
    d.v("L3", "DOMAIN SERVICES - backend/app/  (shared by API and worker)", 30, 540, 1340, 150,
        layer(SVC, SVC_BG))
    svcs = [
        ("s-sec", "security.py", "PBKDF2 hashing, JWT,", "current_user() dependency"),
        ("s-svc", "services.py", "rollup(), open_incident(),", "unique_slug() - pure queries"),
        ("s-cache", "cache.py", "get_json / set_json /", "invalidate - fails soft"),
        ("s-probe", "probe.py", "due_monitors, probe_once,", "apply_result - state machine"),
    ]
    for i, (cid, n, a, b) in enumerate(svcs):
        d.v(cid, mod_label(n, a, b), 55 + i * 330, 580, 300, 70, module(SVC))
    d.e("e-r-sec", "r-auth", "s-sec", "", EDGE)
    d.e("e-r-svc", "r-inc", "s-svc", "", EDGE)
    d.e("e-r-cache", "r-status", "s-cache", "", EDGE)
    d.e("e-w-probe", "w-main", "s-probe", "", EDGE)

    # data access
    d.v("L4", "DATA ACCESS - backend/app/", 30, 740, 1340, 120, layer(DATA, DATA_BG))
    d.v("d-conf", mod_label("config.py", "Settings - every tunable from env vars"),
        55, 780, 300, 56, module(DATA))
    d.v("d-models", mod_label("models.py", "User, Monitor, Check, Incident (SQLAlchemy 2.0)"),
        380, 780, 410, 56, module(DATA))
    d.v("d-db", mod_label("db.py", "engine, SessionLocal, get_db() dependency"),
        935, 780, 410, 56, module(DATA))
    d.e("e-svc-models", "s-svc", "d-models", "", EDGE)
    d.e("e-probe-models", "s-probe", "d-db", "", EDGE)

    # stores
    cyl = "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;size=10;fontSize=12;fontStyle=1;"
    d.v("pg", "PostgreSQL 16<br><span style='font-weight:normal;font-size:10px'>users, monitors, checks, incidents</span>",
        1025, 900, 230, 76, cyl + f"fillColor={DATA_BG};strokeColor={DATA};fontColor={DATA};")
    d.v("rd", "Redis 7<br><span style='font-weight:normal;font-size:10px'>TTL cache, derivable data only</span>",
        750, 900, 230, 76, cyl + f"fillColor={CACHE_BG};strokeColor={CACHE};fontColor={CACHE};")
    d.e("e-db-pg", "d-db", "pg", "SQL", EDGE)
    d.e("e-cache-rd", "s-cache", "rd", "GET / SETEX / SCAN+DEL", EDGE, label_pos=0.55)
    d.write(OUT / "02-module-layers.drawio")


# ------------------------------------------------------------------ 03 ER

def data_model():
    d = Diagram("data-model", "Vigil - Data Model", 1240, 640)
    d.title("Vigil - Data Model (PostgreSQL)",
            "Four tables. Every monitor belongs to exactly one user; checks and incidents "
            "cascade-delete with their monitor.")

    def table(tid, name, x, y, w, rows, colour, bg):
        h = 30 + 22 * len(rows)
        d.v(tid, name, x, y, w, h,
            f"swimlane;fontStyle=1;childLayout=stackLayout;horizontal=1;startSize=30;"
            f"horizontalStack=0;resizeParent=1;resizeParentMax=0;collapsible=0;marginBottom=0;"
            f"html=1;fillColor={bg};strokeColor={colour};fontColor={colour};fontSize=14;"
            f"swimlaneFillColor=#FFFFFF;rounded=1;arcSize=4;")
        for i, (field, typ, key) in enumerate(rows):
            weight = "font-weight:bold;" if key == "PK" else ""
            tag = f"<span style='color:{colour};font-size:10px'>{key}</span> " if key else ""
            d.v(f"{tid}-{i}",
                f"{tag}<span style='{weight}color:{INK}'>{field}</span>"
                f"<span style='color:{MUTED}'>&nbsp;&nbsp;{typ}</span>",
                0, 30 + 22 * i, w, 22,
                "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;"
                "spacingLeft=10;fontSize=11;", parent=tid)
        return h

    table("users", "users", 40, 110, 250, [
        ("id", "integer", "PK"), ("email", "varchar(255) unique", ""),
        ("handle", "varchar(64) unique", ""), ("password_hash", "varchar(255)", ""),
        ("created_at", "timestamptz", "")], FE, FE_BG)
    table("monitors", "monitors", 400, 110, 300, [
        ("id", "integer", "PK"), ("owner_id", "-> users.id", "FK"),
        ("name / slug", "varchar(120)", ""), ("url", "varchar(2048)", ""),
        ("method / expected_status", "GET / 200", ""), ("interval_seconds", "int, 30-3600", ""),
        ("is_active / is_public", "boolean", ""), ("current_status", "pending|up|degraded|down", ""),
        ("consecutive_failures", "int", ""), ("last_checked_at", "timestamptz", ""),
        ("unique (owner_id, slug)", "", "UQ")], BE, BE_BG)
    table("checks", "checks", 820, 110, 280, [
        ("id", "integer", "PK"), ("monitor_id", "-> monitors.id", "FK"),
        ("checked_at", "timestamptz, indexed", ""), ("status_code", "int, null on error", ""),
        ("latency_ms", "float", ""), ("ok", "boolean", ""), ("error", "text", "")], DATA, DATA_BG)
    table("incidents", "incidents", 820, 330, 280, [
        ("id", "integer", "PK"), ("monitor_id", "-> monitors.id", "FK"),
        ("started_at", "timestamptz", ""), ("resolved_at", "timestamptz, null = open", ""),
        ("cause", "varchar(255)", ""), ("summary", "text, written on resolve", ""),
        ("acknowledged", "boolean", "")], CACHE, CACHE_BG)

    er = (f"edgeStyle=entityRelationEdgeStyle;html=1;endArrow=ERmany;startArrow=ERmandOne;"
          f"endFill=0;startFill=0;strokeColor={BODY};strokeWidth=1.5;fontSize=11;fontColor={BODY};"
          f"labelBackgroundColor=#FFFFFF;")
    d.e("r1", "users-0", "monitors-1", "owns", er)
    d.e("r2", "monitors-0", "checks-1", "records", er)
    d.e("r3", "monitors-0", "incidents-1", "opens", er)

    d.v("note", "<b>Why this shape.</b> checks is the only table that grows without bound "
        "(about 1,440 rows per monitor per day at 60 s), so both monitor_id and checked_at are indexed "
        "and nothing joins across it on the hot path: the dashboard reads a pre-aggregated rollup "
        "from Redis. Incident state is derived from resolved_at IS NULL, so there is no separate "
        "status column to drift out of sync.",
        40, 470, 700, 84,
        f"rounded=1;whiteSpace=wrap;html=1;fillColor=#F4F6F8;strokeColor=#D5DAE1;align=left;"
        f"verticalAlign=top;spacingLeft=12;spacingTop=8;spacingRight=12;fontSize=12;fontColor={BODY};")
    d.write(OUT / "03-data-model.drawio")


# ------------------------------------------------------------------ 04 state machine

def state_machine():
    d = Diagram("state-machine", "Vigil - Monitor State Machine", 1300, 760)
    d.title("Vigil - Monitor Status and Incident Lifecycle",
            "Implemented in app/probe.py apply_result(). failure_threshold = 2 "
            "(config.py), slow = latency above 2000 ms.")

    def state(sid, name, sub, x, y, colour, bg):
        d.v(sid, f"<b style='font-size:15px'>{name}</b><br><span style='font-size:10px;color:{MUTED}'>{sub}</span>",
            x, y, 190, 70,
            f"rounded=1;arcSize=40;whiteSpace=wrap;html=1;fillColor={bg};strokeColor={colour};"
            f"strokeWidth=2.5;fontColor={colour};")

    d.v("start", "", 90, 330, 26, 26, "ellipse;html=1;fillColor=#12161C;strokeColor=#12161C;")
    state("pending", "pending", "created, never checked", 170, 308, MUTED, "#F4F6F8")
    state("up", "up", "last check ok, fast", 560, 130, BE, BE_BG)
    state("degraded", "degraded", "ok but > 2000 ms", 560, 500, "#B8860B", "#FBF4E3")
    state("down", "down", "incident OPEN", 980, 308, CACHE, CACHE_BG)

    t = (f"html=1;endArrow=block;endFill=1;strokeColor={BODY};strokeWidth=1.5;fontSize=11;"
         f"fontColor={BODY};labelBackgroundColor=#FFFFFF;curved=1;")
    red = t.replace(f"strokeColor={BODY}", f"strokeColor={CACHE}")
    grn = t.replace(f"strokeColor={BODY}", f"strokeColor={BE}")

    d.e("t0", "start", "pending", "", t)
    d.e("t1", "pending", "up", "check ok, fast", t, points=[(330, 200)])
    d.e("t2", "pending", "degraded", "check ok, slow", t, points=[(330, 500)])
    d.e("t3", "up", "degraded", "latency > 2 s", t, points=[(620, 360)], label_pos=-0.55)
    d.e("t4", "degraded", "up", "latency < 2 s", t, points=[(690, 360)], label_pos=-0.55)
    d.e("t5", "up", "down", "2nd consecutive failure\n=> open Incident", red, points=[(1000, 190)])
    d.e("t6", "degraded", "down", "2nd consecutive failure\n=> open Incident", red, points=[(1000, 530)])
    d.e("t7", "down", "up", "first success\n=> resolve + write summary", grn, points=[(870, 290)])
    d.e("t8", "pending", "down", "2 failures before any success", red, points=[(620, 330)])

    d.v("self", "1st failure: consecutive_failures = 1, status unchanged. "
        "One bad check is noise, not an incident (flap guard, US-13).",
        40, 620, 560, 60,
        f"rounded=1;whiteSpace=wrap;html=1;fillColor=#F4F6F8;strokeColor=#D5DAE1;align=left;"
        f"verticalAlign=middle;spacingLeft=12;spacingRight=12;fontSize=12;fontColor={BODY};")
    d.v("inv", "Every transition ends with commit, then cache.invalidate() on the owner's list, "
        "the monitor's series and every public status page.",
        650, 620, 600, 60,
        f"rounded=1;whiteSpace=wrap;html=1;fillColor=#F4F6F8;strokeColor=#D5DAE1;align=left;"
        f"verticalAlign=middle;spacingLeft=12;spacingRight=12;fontSize=12;fontColor={BODY};")
    d.write(OUT / "04-monitor-state-machine.drawio")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "infra" / "architecture.drawio", OUT / "01-architecture.drawio")
    print("  wrote", (OUT / "01-architecture.drawio").relative_to(ROOT))
    module_layers()
    data_model()
    state_machine()


if __name__ == "__main__":
    main()
