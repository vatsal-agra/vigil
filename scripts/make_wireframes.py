"""Generates the six Vigil wireframes as SVG files that import into Figma as frames.

Run:  python scripts/make_wireframes.py
Out:  docs/wireframes/0X-name.svg
"""
import pathlib

W, H = 1440, 900
BAND = 76
TOTAL_H = H + BAND

INK = "#1A1D22"
BODY = "#4A5058"
MUTED = "#8B929C"
LINE = "#D7DBE0"
FILL = "#FFFFFF"
CANVAS = "#F1F3F5"
BLOCK = "#E4E7EB"
ACCENT = "#3B62D6"
UP = "#1F9D6B"
DOWN = "#D2405A"
WARN = "#C98A15"

FONT = "'Inter', 'Helvetica Neue', Arial, sans-serif"
MONO = "'JetBrains Mono', 'SF Mono', Consolas, monospace"

out = []


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rect(x, y, w, h, fill=FILL, stroke=LINE, r=4, sw=1, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"{st}{d}/>'


def text(x, y, s, size=13, fill=INK, weight=400, font=FONT, anchor="start", spacing=0):
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    return (
        f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{ls}>{esc(s)}</text>'
    )


def line(x1, y1, x2, y2, stroke=LINE, sw=1, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{d}/>'


def circle(cx, cy, r, fill):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>'


def placeholder(x, y, w, h, r=3):
    """Grey bar standing in for a line of copy."""
    return rect(x, y, w, h, fill=BLOCK, stroke=None, r=r)


def button(x, y, w, h, label, primary=False):
    fill = ACCENT if primary else FILL
    fg = "#FFFFFF" if primary else INK
    stroke = ACCENT if primary else LINE
    return (
        rect(x, y, w, h, fill=fill, stroke=stroke, r=5)
        + text(x + w / 2, y + h / 2 + 4, label, 13, fg, 600, anchor="middle")
    )


def field(x, y, w, label, value="", h=40):
    return (
        text(x, y - 8, label.upper(), 9, MUTED, 500, MONO, spacing=1.4)
        + rect(x, y, w, h, fill="#FAFBFC", stroke=LINE, r=5)
        + text(x + 12, y + h / 2 + 4, value, 12, BODY if value else MUTED, 400, MONO)
    )


def pill(x, y, label, colour):
    w = 20 + len(label) * 6.6
    return (
        rect(x, y, w, 22, fill="none", stroke=colour, r=11)
        + circle(x + 11, y + 11, 3.2, colour)
        + text(x + 20, y + 15, label.upper(), 9, colour, 500, MONO, spacing=1.2)
    )


def uptime_strip(x, y, w, n=46, bad_from=None, warn_every=None):
    """The signature element: one tick per recent check."""
    gap = 2
    tw = (w - gap * (n - 1)) / n
    parts = []
    for i in range(n):
        colour = UP
        if bad_from is not None and i >= bad_from:
            colour = DOWN
        elif warn_every and i % warn_every == 0:
            colour = WARN
        h = 10 + (i * 7) % 16
        parts.append(
            f'<rect x="{x + i * (tw + gap):.1f}" y="{y + 26 - h}" width="{tw:.1f}" '
            f'height="{h}" rx="1" fill="{colour}" opacity="0.9"/>'
        )
    return "".join(parts)


def annotate(x, y, n, note, anchor="start", light=False):
    """Numbered callout in the gutter, so the reader can follow intent."""
    fg = "#C7CEDA" if light else BODY
    return (
        circle(x, y - 4, 9, ACCENT)
        + text(x, y, str(n), 10, "#FFFFFF", 700, MONO, anchor="middle")
        + text(x + 16, y, note, 11, fg, 400, anchor=anchor)
    )


def frame(number, name, purpose, body):
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{TOTAL_H}" '
        f'viewBox="0 0 {W} {TOTAL_H}">',
        rect(0, 0, W, TOTAL_H, fill=CANVAS, stroke=None, r=0),
        # header band
        rect(0, 0, W, BAND, fill="#FFFFFF", stroke=None, r=0),
        line(0, BAND, W, BAND),
        text(48, 32, f"VIGIL / WIREFRAME {number:02d}", 10, MUTED, 500, MONO, spacing=1.6),
        text(48, 55, name, 19, INK, 700),
        text(W - 48, 47, purpose, 12, MUTED, 400, anchor="end"),
        f'<g transform="translate(0,{BAND})">',
        rect(0, 0, W, H, fill=CANVAS, stroke=None, r=0),
        body,
        "</g>",
        "</svg>",
    ]
    return "\n".join(parts)


# ---------------------------------------------------------------- chrome

def app_chrome(active="Monitors", handle="demo"):
    """Shared top navigation used by the signed-in screens."""
    return (
        rect(0, 0, W, 64, fill=FILL, stroke=None, r=0)
        + line(0, 64, W, 64)
        + circle(52, 32, 5, ACCENT)
        + text(66, 37, "Vigil", 17, INK, 700)
        + text(112, 37, "WATCH", 9, MUTED, 500, MONO, spacing=1.4)
        + text(200, 37, "Monitors", 13, INK if active == "Monitors" else MUTED,
               600 if active == "Monitors" else 400)
        + text(280, 37, "Incidents", 13, INK if active == "Incidents" else MUTED,
               600 if active == "Incidents" else 400)
        + text(362, 37, "Status page", 13, INK if active == "Status" else MUTED,
               600 if active == "Status" else 400)
        + (line(200, 63, 258, 63, ACCENT, 2) if active == "Monitors" else "")
        + (line(280, 63, 340, 63, ACCENT, 2) if active == "Incidents" else "")
        + text(W - 130, 37, f"{handle}@vigil", 12, MUTED, 400, MONO)
        + circle(W - 52, 32, 14, BLOCK)
    )


def stat_rail(y, items):
    x, w = 48, (W - 96) / 4
    parts = [rect(48, y, W - 96, 84, fill=FILL, stroke=LINE, r=6)]
    for i, (k, v, colour) in enumerate(items):
        cx = x + i * w
        if i:
            parts.append(line(cx, y + 16, cx, y + 68))
        parts.append(text(cx + 22, y + 32, k.upper(), 9, MUTED, 500, MONO, spacing=1.4))
        parts.append(text(cx + 22, y + 62, v, 25, colour, 700))
    return "".join(parts)


# ---------------------------------------------------------------- 01 sign in

body = "".join([
    rect(470, 190, 500, 480, fill=FILL, stroke=LINE, r=8),
    circle(510, 246, 5, ACCENT),
    text(524, 251, "Vigil", 20, INK, 700),
    text(502, 288, "KEEP WATCH ON WHAT YOU SHIPPED", 9, MUTED, 500, MONO, spacing=1.6),
    field(502, 340, 436, "Email", "you@company.com"),
    field(502, 424, 436, "Password", "••••••••••••"),
    button(502, 496, 436, 44, "Sign in", primary=True),
    line(502, 570, 938, 570),
    text(720, 602, "No account yet?", 12, MUTED, 400, anchor="middle"),
    button(640, 618, 160, 34, "Create one"),
    annotate(210, 300, 1, "Single field pair. No social login in v1 —"),
    text(226, 318, "self-hosted users have no shared identity provider.", 11, BODY),
    annotate(210, 380, 2, "Errors render above the card in the interface"),
    text(226, 398, "voice: \u201cEmail or password is incorrect.\u201d", 11, BODY),
    annotate(210, 460, 3, "Successful sign-in stores a JWT and redirects"),
    text(226, 478, "to the dashboard. Token TTL is 24 hours.", 11, BODY),
])
out.append(("01-sign-in", frame(1, "Sign in", "Entry point — US-01, US-02", body)))

# ---------------------------------------------------------------- 02 dashboard

rows = []
data = [
    ("Marketing site", "https://example.com", "up", "100.00%", "182 ms", None, None),
    ("Checkout API", "https://api.example.com/health", "up", "99.94%", "210 ms", None, None),
    ("Search service", "https://search.example.com", "degraded", "99.12%", "2 409 ms", None, 7),
    ("Invoice worker", "https://jobs.example.com/ping", "down", "84.21%", "no response", 38, None),
]
ry = 402
for i, (name, url, status, pct, lat, bad, warn) in enumerate(data):
    top = ry + i * 92
    colour = {"up": UP, "degraded": WARN, "down": DOWN}[status]
    rows.append(rect(48, top, W - 96, 92, fill=FILL, stroke=None, r=0))
    rows.append(line(48, top + 92, W - 48, top + 92))
    rows.append(text(72, top + 34, name, 14, INK, 600))
    rows.append(text(72, top + 54, url, 11, MUTED, 400, MONO))
    rows.append(pill(72, top + 62, status, colour))
    rows.append(uptime_strip(400, top + 32, 620, bad_from=bad, warn_every=warn))
    rows.append(text(1120, top + 22, "LAST 24 H", 8, MUTED, 500, MONO, spacing=1.4))
    rows.append(text(W - 72, top + 42, pct, 16, INK, 500, MONO, anchor="end"))
    rows.append(text(W - 72, top + 62, lat, 10, MUTED, 400, MONO, anchor="end"))

body = "".join([
    app_chrome("Monitors"),
    text(48, 122, "Everything you asked us to watch", 27, INK, 700),
    text(48, 148, "REFRESHED EVERY 15 SECONDS", 9, MUTED, 500, MONO, spacing=1.6),
    button(W - 220, 108, 172, 40, "Add monitor", primary=True),
    stat_rail(186, [("Monitors", "4", INK), ("Healthy", "2", UP),
                    ("Open incidents", "1", DOWN), ("Avg uptime 24h", "95.82%", INK)]),
    text(48, 318, "Monitors", 15, INK, 700),
    text(W - 48, 318, "Sorted by name", 11, MUTED, 400, anchor="end"),
    rect(48, 340, W - 96, 30, fill="#FAFBFC", stroke=LINE, r=0),
    text(72, 360, "SERVICE", 9, MUTED, 500, MONO, spacing=1.4),
    text(400, 360, "LAST 46 CHECKS", 9, MUTED, 500, MONO, spacing=1.4),
    text(W - 72, 360, "UPTIME / RESPONSE", 9, MUTED, 500, MONO, spacing=1.4, anchor="end"),
    rect(48, 370, W - 96, 92 * 4 + 32, fill="none", stroke=LINE, r=0),
    "".join(rows),
    text(72, 800, "Row click opens the monitor detail screen.", 11, MUTED),
    annotate(1090, 800, 1, "Signature element: the check strip. One tick per"),
    text(1106, 818, "probe, coloured by outcome — outages are visible", 11, BODY),
    text(1106, 834, "at a glance without opening anything.", 11, BODY),
])
out.append(("02-dashboard", frame(2, "Dashboard — monitor list",
                                  "Primary screen — US-05, US-08, US-09", body)))

# ---------------------------------------------------------------- 03 add monitor

body = "".join([
    app_chrome("Monitors"),
    rect(0, 64, W, H - 64, fill="#0C1220", stroke=None, r=0),
    f'<rect x="0" y="64" width="{W}" height="{H-64}" fill="#000000" opacity="0.35"/>',
    rect(420, 150, 600, 620, fill=FILL, stroke=LINE, r=8),
    text(452, 196, "Add a monitor", 20, INK, 700),
    text(452, 220, "Vigil starts checking as soon as you save.", 12, MUTED),
    line(420, 244, 1020, 244),
    field(452, 288, 536, "Name", "Checkout API"),
    field(452, 372, 536, "URL to check", "https://api.example.com/health"),
    field(452, 456, 250, "Method", "GET"),
    field(738, 456, 250, "Expected status", "200"),
    field(452, 540, 250, "Check every", "60 seconds"),
    rect(738, 540, 250, 40, fill="#FAFBFC", stroke=LINE, r=5),
    rect(752, 552, 30, 16, fill=ACCENT, stroke=None, r=8),
    circle(775, 560, 6, "#FFFFFF"),
    text(794, 565, "Show on status page", 11, BODY),
    line(420, 690, 1020, 690),
    button(842, 712, 146, 42, "Start watching", primary=True),
    button(716, 712, 110, 42, "Cancel"),
    annotate(140, 300, 1, "Only name and URL are required.", light=True),
    text(156, 318, "Everything else has a working default.", 11, "#C7CEDA"),
    annotate(140, 380, 2, "Method and expected status let this cover", light=True),
    text(156, 398, "API health endpoints, not just web pages.", 11, "#C7CEDA"),
    annotate(140, 460, 3, "Minimum interval is 30s — enforced by the", light=True),
    text(156, 478, "API so a user cannot self-inflict rate limits.", 11, "#C7CEDA"),
    annotate(140, 560, 4, "Toggle controls whether this service appears", light=True),
    text(156, 578, "on the public status page.", 11, "#C7CEDA"),
])
out.append(("03-add-monitor", frame(3, "Add monitor", "Create flow — US-06, US-07", body)))

# ---------------------------------------------------------------- 04 monitor detail

pts = []
vals = [0.30, 0.28, 0.34, 0.31, 0.29, 0.36, 0.33, 0.30, 0.42, 0.38, 0.31, 0.29,
        0.33, 0.30, 0.35, 0.68, 0.88, 0.94, 0.72, 0.41, 0.33, 0.30, 0.28, 0.31,
        0.30, 0.34, 0.29, 0.32, 0.30, 0.28]
cx0, cy0, cw, ch = 80, 430, W - 160, 170
for i, v in enumerate(vals):
    px = cx0 + i * (cw / (len(vals) - 1))
    py = cy0 + ch - v * ch
    pts.append(f"{px:.1f},{py:.1f}")
poly = " ".join(pts)

body = "".join([
    app_chrome("Monitors"),
    text(48, 118, "\u2190  Back to dashboard", 12, MUTED, 400),
    text(48, 158, "Checkout API", 27, INK, 700),
    text(48, 182, "GET https://api.example.com/health  \u00b7  every 60s", 11, MUTED, 400, MONO),
    pill(48, 200, "up", UP),
    button(W - 220, 148, 172, 40, "Edit monitor"),
    stat_rail(248, [("Status", "UP", UP), ("Uptime 24h", "99.94%", INK),
                    ("Avg response", "210 ms", INK), ("Failed checks", "3", DOWN)]),
    text(48, 382, "Response time, last 24 hours", 15, INK, 700),
    text(W - 48, 382, "24 H   \u00b7   7 D   \u00b7   30 D", 11, MUTED, 400, MONO, anchor="end"),
    rect(48, 398, W - 96, 234, fill=FILL, stroke=LINE, r=6),
    line(cx0, cy0 + ch * 0.25, cx0 + cw, cy0 + ch * 0.25, "#EDEFF2"),
    line(cx0, cy0 + ch * 0.5, cx0 + cw, cy0 + ch * 0.5, "#EDEFF2"),
    line(cx0, cy0 + ch * 0.75, cx0 + cw, cy0 + ch * 0.75, "#EDEFF2"),
    f'<polyline points="{poly}" fill="none" stroke="{ACCENT}" stroke-width="2"/>',
    line(cx0 + 16 * (cw / 29), cy0, cx0 + 16 * (cw / 29), cy0 + ch, DOWN, 1.5, "3 3"),
    text(cx0 + 16 * (cw / 29) + 8, cy0 + 16, "failed check", 9, DOWN, 500, MONO),
    text(52, cy0 + 8, "1.2 s", 9, MUTED, 400, MONO),
    text(52, cy0 + ch, "0 ms", 9, MUTED, 400, MONO),
    text(48, 672, "Latest checks", 15, INK, 700),
    rect(48, 690, W - 96, 134, fill=FILL, stroke=LINE, r=6),
    *[
        text(76, 716 + i * 30, t, 11, c, 400, MONO)
        for i, (t, c) in enumerate([
            ("14s ago      200 OK        198 ms", BODY),
            ("1m ago       200 OK        204 ms", BODY),
            ("2m ago       Expected 200, got 503        no response", DOWN),
            ("3m ago       200 OK        211 ms", BODY),
        ])
    ],
    button(48, 844, 176, 34, "Show on status page"),
    button(236, 844, 136, 34, "Stop watching"),
])
out.append(("04-monitor-detail", frame(4, "Monitor detail",
                                       "Drill-down — US-10, US-11, US-12", body)))

# ---------------------------------------------------------------- 05 incidents

inc = [
    ("Invoice worker", "Expected 200, got 503", "OPEN", "3h 45m", DOWN, False),
    ("Search service", "No response within 8s", "RESOLVED", "12 min", UP, True),
    ("Checkout API", "Connection failed: ConnectError", "RESOLVED", "4 min", UP, True),
    ("Marketing site", "Expected 200, got 502", "RESOLVED", "2 min", UP, True),
]
cards = []
for i, (mon, cause, state, dur, colour, resolved) in enumerate(inc):
    top = 300 + i * 132
    cards.append(rect(48, top, W - 96, 116, fill=FILL, stroke=LINE, r=6))
    cards.append(rect(48, top, 4, 116, fill=colour, stroke=None, r=0))
    cards.append(pill(76, top + 22, state, colour))
    cards.append(text(200, top + 38, mon, 15, INK, 600))
    cards.append(text(76, top + 74, cause, 12, BODY, 400, MONO))
    cards.append(text(76, top + 96, "Started 14:22 IST  \u00b7  duration " + dur, 10, MUTED, 400, MONO))
    if resolved:
        cards.append(text(560, top + 74,
                          "Recovered after " + dur + ". Now answering in 204 ms.", 11, MUTED))
    else:
        cards.append(button(W - 300, top + 40, 106, 34, "Acknowledge"))
        cards.append(button(W - 182, top + 40, 110, 34, "Open monitor"))

body = "".join([
    app_chrome("Incidents"),
    text(48, 122, "Incidents", 27, INK, 700),
    text(48, 148, "NEWEST FIRST  \u00b7  LAST 30 DAYS", 9, MUTED, 500, MONO, spacing=1.6),
    rect(48, 186, 120, 34, fill=ACCENT, stroke=ACCENT, r=17),
    text(108, 208, "All", 12, "#FFFFFF", 600, anchor="middle"),
    rect(180, 186, 120, 34, fill=FILL, stroke=LINE, r=17),
    text(240, 208, "Open only", 12, BODY, 400, anchor="middle"),
    rect(312, 186, 140, 34, fill=FILL, stroke=LINE, r=17),
    text(382, 208, "Unacknowledged", 12, BODY, 400, anchor="middle"),
    text(48, 268, "1 open  \u00b7  3 resolved this week", 13, BODY, 500),
    "".join(cards),
    annotate(48, 862, 1, "An incident opens automatically after 2 consecutive failed checks, "
                         "and closes on the first success. No manual filing."),
])
out.append(("05-incidents", frame(5, "Incident feed", "Triage — US-13, US-14, US-15", body)))

# ---------------------------------------------------------------- 06 public status

svcs = [
    ("Marketing site", "up", "100.00%", None, None),
    ("Checkout API", "up", "99.94%", None, None),
    ("Search service", "degraded", "99.12%", None, 6),
]
rows = []
for i, (name, status, pct, bad, warn) in enumerate(svcs):
    top = 442 + i * 96
    colour = {"up": UP, "degraded": WARN, "down": DOWN}[status]
    rows.append(rect(320, top, 800, 96, fill=FILL, stroke=None, r=0))
    rows.append(line(320, top + 96, 1120, top + 96))
    rows.append(text(348, top + 40, name, 14, INK, 600))
    rows.append(pill(348, top + 54, status, colour))
    rows.append(uptime_strip(600, top + 34, 340, n=30, warn_every=warn))
    rows.append(text(1096, top + 44, pct, 15, INK, 500, MONO, anchor="end"))
    rows.append(text(1096, top + 62, "90-day uptime", 9, MUTED, 400, MONO, anchor="end"))

body = "".join([
    rect(0, 0, W, H, fill="#FAFBFC", stroke=None, r=0),
    rect(0, 0, W, 72, fill=FILL, stroke=None, r=0),
    line(0, 72, W, 72),
    circle(340, 36, 5, ACCENT),
    text(354, 41, "Acme Inc.", 16, INK, 700),
    text(432, 41, "STATUS", 9, MUTED, 500, MONO, spacing=1.4),
    text(1100, 41, "Updated 14s ago", 11, MUTED, 400, MONO, anchor="end"),
    rect(320, 132, 800, 116, fill="#F0FAF5", stroke=UP, r=6),
    circle(360, 190, 8, UP),
    text(382, 184, "All systems operational", 22, INK, 700),
    text(382, 210, "No incidents in the last 7 days.", 12, BODY),
    text(320, 300, "SERVICES", 9, MUTED, 500, MONO, spacing=1.6),
    rect(320, 320, 800, 96 * 3 + 122, fill="none", stroke=LINE, r=6),
    rect(320, 320, 800, 92, fill="#FAFBFC", stroke=None, r=0),
    line(320, 412, 1120, 412),
    text(348, 356, "Grouped by service", 12, BODY, 500),
    text(348, 378, "Each bar is one hour. Hover for exact figures.", 10, MUTED, 400, MONO),
    text(1096, 366, "90 DAYS", 9, MUTED, 500, MONO, spacing=1.4, anchor="end"),
    "".join(rows),
    text(320, 776, "PAST INCIDENTS", 9, MUTED, 500, MONO, spacing=1.6),
    text(320, 806, "16 July \u2014 Search service degraded for 12 minutes.", 12, BODY),
    text(320, 830, "Elevated response times from the upstream index. Resolved.", 11, MUTED),
    text(720, 872, "Powered by Vigil", 11, MUTED, 400, anchor="middle"),
    annotate(1180, 200, 1, "No login. No JWT."),
    text(1196, 218, "Served from a Redis-", 11, BODY),
    text(1196, 234, "cached endpoint with a", 11, BODY),
    text(1196, 250, "20s TTL so a traffic spike", 11, BODY),
    text(1196, 266, "during an outage cannot", 11, BODY),
    text(1196, 282, "take the database down.", 11, BODY),
])
out.append(("06-public-status", frame(6, "Public status page",
                                      "Unauthenticated — US-16, US-17", body)))

# ---------------------------------------------------------------- write

target = pathlib.Path(__file__).resolve().parent.parent / "docs" / "wireframes"
target.mkdir(parents=True, exist_ok=True)
for name, svg in out:
    (target / f"{name}.svg").write_text(svg, encoding="utf-8")
    print("wrote", name + ".svg")
