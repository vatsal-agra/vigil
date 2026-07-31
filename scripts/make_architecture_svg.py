"""Renders the Vigil architecture diagram as a landscape SVG for the report.

The editable source of truth is infra/architecture.drawio; this produces the
image embedded in the submission document. Content is kept identical.
"""
import pathlib

W, H = 1620, 960

INK = "#12161C"
BODY = "#3F4650"
MUTED = "#79818D"
LINE = "#C9CFD7"
PAPER = "#FFFFFF"
CANVAS = "#F6F7F9"

FE = "#2B5CD9"      # frontend / presentation
FE_BG = "#EEF3FE"
BE = "#0E7C5A"      # backend / application
BE_BG = "#E9F6F1"
DATA = "#6A4BC4"    # persistence
DATA_BG = "#F0ECFB"
CACHE = "#C0392B"   # cache
CACHE_BG = "#FBEDEB"
EXT = "#8E44AD"     # external
EXT_BG = "#F6EEFA"
EDGE = "#B8860B"    # edge / proxy
EDGE_BG = "#FBF4E3"

FONT = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
MONO = "'Consolas', 'SF Mono', monospace"

p = []


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def box(x, y, w, h, title, lines, stroke, fill, r=6, dash=None, mono_from=99):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" '
           f'stroke="{stroke}" stroke-width="2"{d}/>']
    out.append(f'<text x="{x + 14}" y="{y + 26}" font-family="{FONT}" font-size="15" '
               f'font-weight="700" fill="{stroke}">{esc(title)}</text>')
    for i, ln in enumerate(lines):
        fam = MONO if i >= mono_from else FONT
        out.append(f'<text x="{x + 14}" y="{y + 48 + i * 17}" font-family="{fam}" '
                   f'font-size="11.5" fill="{BODY}">{esc(ln)}</text>')
    return "".join(out)


def label(x, y, s, size=12, fill=BODY, weight=400, font=FONT, anchor="start", spacing=0):
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{ls}>{esc(s)}</text>')


def arrow(pts, stroke=BODY, sw=2, dash=None, both=False):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    path = " ".join(f"{'M' if i == 0 else 'L'}{x},{y}" for i, (x, y) in enumerate(pts))
    start = f' marker-start="url(#head-{stroke.lstrip("#")}-r)"' if both else ""
    return (f'<path d="{path}" fill="none" stroke="{stroke}" stroke-width="{sw}"{d} '
            f'marker-end="url(#head-{stroke.lstrip("#")})"{start}/>')


def tag(x, y, s, colour=MUTED, anchor="middle"):
    w = len(s) * 6.0 + 14
    ax = x - w / 2 if anchor == "middle" else x
    return (f'<rect x="{ax}" y="{y - 12}" width="{w}" height="18" rx="4" fill="{PAPER}" '
            f'opacity="0.95"/>' + label(x, y + 1, s, 10.5, colour, 600, MONO, anchor))


# ---------------------------------------------------------------- defs

markers = []
for c in [BODY, FE, BE, DATA, CACHE, EXT, EDGE, MUTED]:
    cid = c.lstrip("#")
    markers.append(
        f'<marker id="head-{cid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
        f'markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0,1 L9,5 L0,9 z" fill="{c}"/></marker>')
    markers.append(
        f'<marker id="head-{cid}-r" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
        f'markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0,1 L9,5 L0,9 z" fill="{c}"/></marker>')

p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
p.append(f'<defs>{"".join(markers)}</defs>')
p.append(f'<rect width="{W}" height="{H}" fill="{CANVAS}"/>')

# ---------------------------------------------------------------- header

p.append(label(48, 54, "Vigil — System Architecture", 26, INK, 700))
p.append(label(48, 82, "Request flow: client → edge → frontend → backend → cache / database, "
                       "with an independent probe worker reaching monitored endpoints", 13, MUTED))
p.append(f'<line x1="48" y1="100" x2="{W-48}" y2="100" stroke="{LINE}" stroke-width="1"/>')

# ---------------------------------------------------------------- host boundary

p.append(f'<rect x="470" y="146" width="880" height="676" rx="10" fill="{PAPER}" '
         f'stroke="{MUTED}" stroke-width="2" stroke-dasharray="9 6"/>')
p.append(label(488, 172, "DEPLOYMENT HOST — Raspberry Pi 5 (Ubuntu Server)", 11.5, MUTED, 700, MONO, spacing=0.6))
p.append(label(488, 190, "Docker Compose · bridge network: vigil_default · 5 containers", 11, MUTED))

# ---------------------------------------------------------------- clients

p.append(box(60, 212, 175, 78, "Dashboard user", ["Signed-in operator", "Chrome / Firefox"], FE, FE_BG))
p.append(box(60, 344, 175, 78, "Public visitor", ["No account", "Reads status page"], FE, FE_BG))

# ---------------------------------------------------------------- edge

p.append(box(282, 212, 158, 78, "Cloudflare", ["Tunnel · DNS", "TLS · DDoS"], EDGE, EDGE_BG))
p.append(box(282, 344, 158, 78, "Caddy", ["Reverse proxy", "Routes /api/*"], EDGE, EDGE_BG))

# ---------------------------------------------------------------- containers

p.append(box(512, 236, 196, 122, "web", ["Next.js 15 App Router", "React 19 · TypeScript",
                                         "node:22-alpine", "port 3000"], FE, FE_BG, mono_from=2))
p.append(box(772, 220, 204, 138, "api", ["FastAPI · Uvicorn", "SQLAlchemy 2.0 ORM",
                                         "python:3.12-slim", "port 8000"], BE, BE_BG, mono_from=2))

# auth layer
p.append(f'<rect x="772" y="368" width="204" height="40" rx="5" fill="{BE_BG}" stroke="{BE}" '
         f'stroke-width="1.5" stroke-dasharray="5 3"/>')
p.append(label(786, 384, "AUTH LAYER", 9.5, BE, 700, MONO, spacing=0.8))
p.append(label(786, 399, "JWT HS256 · PBKDF2 password hashing", 10, BODY))

p.append(box(1058, 200, 214, 112, "cache", ["Redis 7", "Response cache, TTL 15–30 s",
                                            "port 6379"], CACHE, CACHE_BG, mono_from=1))
p.append(box(1058, 350, 214, 124, "db", ["PostgreSQL 16", "4 tables: users, monitors,",
                                         "checks, incidents", "port 5432"], DATA, DATA_BG, mono_from=1))

# volume
p.append(f'<rect x="1108" y="516" width="164" height="66" rx="8" fill="{DATA_BG}" stroke="{DATA}" '
         f'stroke-width="2" stroke-dasharray="6 4"/>')
p.append(label(1122, 540, "vigil_pgdata", 13, DATA, 700, MONO))
p.append(label(1122, 560, "named volume — durable", 10.5, BODY))

p.append(box(512, 574, 236, 130, "worker", ["Probe loop, 30 s tick", "httpx client",
                                            "Incident state machine",
                                            "Same image, worker target"], BE, BE_BG, mono_from=4))

# ---------------------------------------------------------------- external

p.append(box(1400, 574, 172, 92, "Monitored", ["endpoints", "Customer sites", "and APIs"],
             EXT, EXT_BG, dash="6 4"))
p.append(box(1400, 700, 172, 92, "Alerting", ["SMTP email", "Slack webhook"],
             EXT, EXT_BG, dash="6 4"))
p.append(box(1400, 212, 172, 78, "GitHub Actions", ["pytest · next build", "docker build"],
             MUTED, CANVAS))
p.append(box(1400, 330, 172, 78, "GHCR", ["Image registry", "compose pull"],
             MUTED, CANVAS))

# ---------------------------------------------------------------- arrows

p.append(arrow([(235, 251), (282, 251)], FE))
p.append(tag(258, 244, "HTTPS", FE))

p.append(arrow([(235, 383), (282, 383)], FE))
p.append(tag(258, 376, "HTTPS", FE))

p.append(arrow([(361, 290), (361, 344)], EDGE))

p.append(arrow([(440, 290), (476, 290), (476, 297), (512, 297)], EDGE))

p.append(arrow([(440, 383), (476, 383), (476, 320), (512, 320)], EDGE))

p.append(arrow([(708, 290), (772, 290)], FE, sw=2.5))
p.append(tag(740, 208, "REST + JWT", FE))

p.append(arrow([(976, 256), (1058, 256)], CACHE, both=True))
p.append(tag(1017, 234, "GET / SETEX", CACHE))

p.append(arrow([(976, 330), (1012, 330), (1012, 412), (1058, 412)], DATA, both=True))
p.append(tag(998, 496, "SQL on cache miss", DATA))

p.append(arrow([(1165, 474), (1165, 516)], DATA, dash="6 4"))
p.append(tag(1215, 498, "persist", DATA))

p.append(arrow([(748, 620), (900, 620), (900, 452), (1058, 452)], DATA))
p.append(tag(880, 600, "INSERT checks · incidents", DATA))

p.append(arrow([(748, 590), (1020, 590), (1020, 312)], CACHE, dash="5 4"))
p.append(tag(1020, 340, "invalidate", CACHE))

p.append(arrow([(748, 650), (1400, 650)], EXT, sw=2.5))
p.append(tag(1080, 638, "outbound HTTP probe every 30 s", EXT))

p.append(arrow([(748, 690), (1340, 690), (1340, 746), (1400, 746)], EXT, dash="5 4"))
p.append(tag(1080, 706, "on incident open / close", EXT))

p.append(arrow([(1486, 290), (1486, 330)], MUTED, dash="5 4"))
p.append(arrow([(1400, 369), (1350, 369)], MUTED, dash="5 4"))
p.append(tag(1372, 348, "deploy", MUTED))

# ---------------------------------------------------------------- legend

p.append(f'<rect x="60" y="574" width="360" height="248" rx="8" fill="{PAPER}" stroke="{LINE}" '
         f'stroke-width="1.5"/>')
p.append(label(80, 602, "LEGEND", 11, MUTED, 700, MONO, spacing=1.2))

rows = [
    (FE, FE_BG, "Presentation tier — browser-facing"),
    (BE, BE_BG, "Application tier — Python services"),
    (DATA, DATA_BG, "Persistence tier — Postgres + volume"),
    (CACHE, CACHE_BG, "Cache tier — Redis, 15–30 s TTL"),
    (EXT, EXT_BG, "External / third-party services"),
    (EDGE, EDGE_BG, "Edge tier — TLS and routing"),
]
for i, (stroke, fill, txt) in enumerate(rows):
    y = 624 + i * 26
    p.append(f'<rect x="80" y="{y - 11}" width="22" height="15" rx="3" fill="{fill}" '
             f'stroke="{stroke}" stroke-width="1.8"/>')
    p.append(label(112, y, txt, 11.5, BODY))

p.append(f'<line x1="80" y1="790" x2="400" y2="790" stroke="{LINE}"/>')
p.append(f'<path d="M80,806 L104,806" stroke="{BODY}" stroke-width="2" marker-end="url(#head-{BODY.lstrip("#")})"/>')
p.append(label(112, 810, "Solid = synchronous request path", 11, BODY))
p.append(f'<path d="M80,806 L104,806" stroke="none"/>')
p.append(f'<path d="M80,822 L104,822" stroke="{BODY}" stroke-width="2" stroke-dasharray="5 4" marker-end="url(#head-{BODY.lstrip("#")})"/>')
p.append(label(112, 826, "Dashed = asynchronous / deploy path", 11, BODY))

p.append("</svg>")

target = pathlib.Path(__file__).resolve().parent.parent / "infra" / "architecture.svg"
target.write_text("\n".join(p), encoding="utf-8")
print("wrote", target)
