#!/usr/bin/env python3
"""Builds the Review 3 project report PDF.

  python docs/build/build_report.py

Reads the backlog from scripts/stories.sh and code listings from the source
tree, lays the report out as HTML, prints it with headless Chromium, then
finds where each section landed and prints again with real page numbers in
the contents. Output: Vigil_Project_Report.pdf at the repo root and a copy in
docs/report/.

Needs: pip install playwright pymupdf && python -m playwright install chromium
"""
import html
import pathlib
import re
import shutil

import fitz
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
BUILD = ROOT / "docs" / "build"
SHOTS = "../report/screenshots"
DIAG = "../design/diagrams"
OUT = ROOT / "Vigil_Project_Report.pdf"
REPO = "https://github.com/vatsal-agra/vigil"

# Results recorded from the runs shown in the screenshots.
MUTATION = {
    "round1": {"total": 120, "killed": 92, "timeout": 1, "suspicious": 2, "survived": 25},
    "round2": {"total": 120, "killed": 116, "timeout": 1, "suspicious": 1, "survived": 2},
    "final": {"total": 120, "killed": 117, "timeout": 1, "suspicious": 1, "survived": 1},
}
TESTS = {"unit": 50, "integration": 22, "regression": 7, "e2e": 6, "coverage": 92}

e = html.escape


# ---------------------------------------------------------------- data

def stories():
    text = (ROOT / "scripts" / "stories.sh").read_text(encoding="utf-8")
    out = []
    for rec in re.findall(r'^"(US-\d\d\|.*)"$', text, re.M):
        sid, title, labels, points, story, criteria = rec.split("|")
        moscow = next(v for k, v in {"must-have": "Must", "should-have": "Should",
                                     "could-have": "Could", "wont-have": "Won't"}.items() if k in labels)
        epic = next(v for k, v in {"epic:accounts": "Accounts", "epic:monitors": "Monitors",
                                   "epic:engine": "Engine", "epic:status": "Status",
                                   "epic:alerting": "Alerting", "epic:ops": "Operations"}.items() if k in labels)
        out.append(dict(id=sid, title=title, points=points, story=story, moscow=moscow, epic=epic,
                        ac=[a.strip() for a in criteria.split(" ;; ")]))
    assert len(out) == 25, len(out)
    return out


def listing(rel, start=None, end=None):
    lines = (ROOT / rel).read_text(encoding="utf-8").splitlines()
    s, t = (start or 1), (end or len(lines))
    lang = "python" if rel.endswith(".py") else "typescript"
    body = e("\n".join(lines[s - 1:t]))
    return (f'<pre><code class="language-{lang}">{body}</code></pre>'
            f'<div class="src">{rel}, lines {s}–{t}</div>')


def shot(name, caption, width=100, cls=""):
    return (f'<figure class="{cls}"><img src="{SHOTS}/{name}.png" style="width:{width}%">'
            f'<figcaption>{caption}</figcaption></figure>')


def diagram(name, caption, width=100):
    return (f'<figure><img src="{DIAG}/{name}.png" style="width:{width}%">'
            f'<figcaption>{caption} Editable source: docs/design/diagrams/{name}.drawio</figcaption></figure>')


def pct(r):
    caught = r["killed"] + r["timeout"] + r["suspicious"]
    return caught, round(100 * caught / r["total"], 1)


# ---------------------------------------------------------------- sections

SECTIONS = [  # (anchor, number, title) — contents order
    ("a1", "1", "Integration, Regression and Mutation Testing"),
    ("a2", "2", "Version Management and System Building"),
    ("a3", "3", "Developed Functionalities"),
    ("a4", "4", "Tools and Technologies Used"),
    ("a5", "5", "Project Demo"),
    ("b1", "6", "Problem Statement"),
    ("b2", "7", "User Stories"),
    ("b3", "8", "System Architecture and System Design"),
    ("b4", "9", "Design of Tests"),
    ("x1", "A", "Appendix A — Software Requirements Specification"),
    ("x2", "B", "Appendix B — Data Flow Diagrams"),
    ("x3", "C", "Appendix C — Entity-Relationship Diagram"),
    ("x4", "D", "Appendix D — UML Diagrams"),
    ("x5", "E", "Appendix E — Code Listing and GitHub Link"),
]


def h1(anchor):
    _, num, title = next(s for s in SECTIONS if s[0] == anchor)
    label = title if title.startswith("Appendix") else f'<span class="n">{num}</span>{title}'
    return f'<h1 id="{anchor}" class="pb" data-toc="{anchor}">{label}</h1>'


def cover(pages):
    rows = "".join(
        f'<div class="toc-row"><span class="toc-n">{n if not t.startswith("Appendix") else ""}</span>'
        f'<span class="toc-t">{e(t)}</span><span class="toc-dots"></span>'
        f'<span class="toc-p">{pages.get(a, "")}</span></div>'
        + ('<div class="toc-part">Part B — Project Report</div>' if a == "a5" else "")
        for a, n, t in SECTIONS)
    return f"""
<section class="cover">
  <div class="kicker">DIGITAL ASSIGNMENT 3 &nbsp;/&nbsp; REVIEW 3 &nbsp;·&nbsp; SOFTWARE ENGINEERING</div>
  <div class="ctitle">Vigil</div>
  <div class="csub">Uptime and API monitoring that explains its own outages</div>
  <div class="crule"></div>
  <div class="cmeta">
    <div><b>Name</b>Vatsal Agrawal</div>
    <div><b>Registration number</b>24BAI1355</div>
    <div><b>Programme</b>B.Tech CSE (AI &amp; ML), VIT Chennai</div>
    <div><b>Repository</b><a href="{REPO}">github.com/vatsal-agra/vigil</a></div>
    <div><b>Release</b>v0.3.0-rc.1 (Review 3 release candidate)</div>
    <div><b>Date</b>15 October 2026</div>
  </div>
</section>
<section class="toc pb">
  <h1 class="toc-h">Contents</h1>
  <div class="toc-part">Part A — Review 3 Evidence</div>
  {rows}
  <div class="note">Every screenshot in this report was captured from the running system or from the
  GitHub repository. Terminal screenshots show the real output of the command on their first line.
  Diagrams are exported from editable draw.io sources committed in <code>docs/design/diagrams/</code>.</div>
</section>"""


def part_a1():
    r1, r2, rf = MUTATION["round1"], MUTATION["round2"], MUTATION["final"]
    c1, p1 = pct(r1)
    c2, p2 = pct(r2)
    cf, pf = pct(rf)
    t = TESTS
    return f"""
{h1("a1")}
<p>Vigil is tested at four levels. Each one answers a different question, and each runs in a different place.
The backend suites run inside the <code>api</code> container against a <b>real PostgreSQL database and Redis</b>
(an isolated <code>vigil_test</code> database and Redis db 15), so nothing is faked below the HTTP layer. Only the
monitored targets are simulated, through <code>httpx.MockTransport</code>.</p>
<table>
<tr><th style="width:17%">Level</th><th style="width:9%">Tests</th><th>What it proves</th><th style="width:25%">Where it runs</th></tr>
<tr><td>Unit</td><td>{t['unit']}</td><td>Each module in isolation: probe engine, shared queries, hashing and tokens. Exact values, boundaries, error text.</td><td><code>pytest -m unit</code>, every PR</td></tr>
<tr><td>Integration</td><td>{t['integration']}</td><td>Every API route through FastAPI's full stack with the real database, cache and auth, plus a full outage lifecycle across API, worker, database and cache.</td><td><code>pytest -m integration</code>, every PR</td></tr>
<tr><td>Regression</td><td>{t['regression']}</td><td>One test per defect fixed or contract that must never break again; re-run on every change.</td><td><code>pytest -m regression</code>, every PR</td></tr>
<tr><td>Mutation</td><td>{r1['total']} mutants</td><td>Whether the tests would actually notice a bug: mutmut changes the code and checks a test fails.</td><td>On demand / weekly workflow</td></tr>
<tr><td>End-to-end</td><td>{t['e2e']}</td><td>The core user journeys in a real Chromium browser against the running stack.</td><td><code>pytest e2e</code>, against <code>docker compose up</code></td></tr>
</table>

<h2>1.1 Integration testing</h2>
<p>The integration suite exercises the system the way a client does: HTTP requests in, JSON out, with real SQL and real
cache keys in between. The most important test follows one outage from start to finish. It creates a monitor through the API,
runs the worker's probe cycle against a target that fails twice and then recovers, and asserts on what the dashboard API
and the public status page report at each step, including that the worker invalidated the API's cached responses.</p>
{shot("t02-integration-tests", "Figure 1.1 — Integration suite: 22 tests through the HTTP API with PostgreSQL and Redis, all passing.")}
{listing("backend/tests/test_integration_engine.py", 22, 54)}

<h2>1.2 Regression testing</h2>
<p>Each regression test names the defect or contract it guards, so a red test says exactly what came back. R1 reproduces the
Review 2 defect: the dashboard showed "Open incidents: 0" while a monitor was down, because the open incident was
older than the newest 100 rows of the capped feed. The suite runs as its own CI step on every pull request.</p>
{shot("t03-regression-tests", "Figure 1.2 — Regression suite (pytest -m regression): R1–R7, all passing.")}

<h2>1.3 Mutation testing</h2>
<p>Coverage shows which lines ran, but not whether a test would notice if those lines were wrong. Mutation testing checks
that directly. <b>mutmut</b> makes {r1['total']} small changes ("mutants") to <code>probe.py</code> and
<code>services.py</code>, the two modules holding the business logic. It flips <code>&gt;=</code> to <code>&gt;</code>,
swaps <code>*</code> for <code>/</code>, replaces <code>continue</code> with <code>break</code>, and so on, then
re-runs the tests for each one. A mutant that every test still passes is a bug the suite would have missed. It runs in a
throwaway container built from the image, so the source files on disk are never modified.</p>
<table>
<tr><th>Run</th><th>Mutants</th><th>Killed</th><th>Timed out</th><th>Suspicious</th><th>Survived</th><th>Mutation score</th></tr>
<tr><td>Round 1: initial suite</td><td>{r1['total']}</td><td>{r1['killed']}</td><td>{r1['timeout']}</td><td>{r1['suspicious']}</td><td>{r1['survived']}</td><td><b>{p1}%</b></td></tr>
<tr><td>Round 2: after mutation-driven tests</td><td>{r2['total']}</td><td>{r2['killed']}</td><td>{r2['timeout']}</td><td>{r2['suspicious']}</td><td>{r2['survived']}</td><td><b>{p2}%</b></td></tr>
<tr><td>Final: mutant #48 re-run after one more test fix</td><td>{rf['total']}</td><td>{rf['killed']}</td><td>{rf['timeout']}</td><td>{rf['suspicious']}</td><td>{rf['survived']} (equivalent)</td><td><b>{pf}%</b></td></tr>
</table>
<p>The {r1['survived']} survivors from round 1 were read one by one, and they pointed at real gaps rather than noise:</p>
<ul>
<li><b>Values never pinned exactly.</b> Latency was asserted to exist but not to equal anything, so <code>* 1000</code> → <code>/ 1000</code>
survived, as did rounding to 2 decimals instead of 1. A fake <code>perf_counter</code> now fixes the clock, and the tests assert
<code>123.5</code> ms exactly.</li>
<li><b>Boundaries.</b> <code>&gt;=</code> → <code>&gt;</code> on "is this monitor due?" and on the 24-hour window survived, because no test
sat exactly on the boundary. Frozen-clock tests now do.</li>
<li><b>Untested behaviour.</b> <code>continue</code> → <code>break</code> in the scheduler survived because no test had two
never-checked monitors. The worker closing its own HTTP client, and following redirects, were never checked.</li>
<li><b>Runner scope.</b> Two mutants were already caught by regression tests R4 and R7, but the mutmut runner only ran
<code>-m unit</code>, so it was widened to <code>unit or regression</code>.</li>
<li><b>Equivalent mutants.</b> <code>.strip("-")</code> → <code>.strip("XX-XX")</code> can never change behaviour, because
the input is lower-cased first. Mutants like this cannot be killed and are recorded as such.</li>
</ul>
{shot("t06-mutation-testing", "Figure 1.3 — Mutation testing round 2: 120 mutants over probe.py and services.py; 116 killed, 2 survived (spinner frames collapsed to the final line, as a terminal shows them).", 86)}
<p>Round 2 left two survivors. <b>#79</b> is the equivalent <code>strip</code> mutant above. <b>#48</b> changes the outage length
from <code>/ 60</code> to <code>/ 61</code> minutes. It survived because the new test used a 30-minute outage, and 30 × 60 / 61 still
prints as "30 min". The test now uses a 10-hour outage (600 vs 590 minutes). Re-running just that mutant against the saved round-2
state kills it, leaving only the equivalent mutant: <b>{cf} of {rf['total']} caught ({pf}%), with every killable mutant killed.</b></p>
{shot("t07-mutation-48-killed", "Figure 1.4 — The mutant that survived round 2, re-run after the test fix: killed. mutmut results now lists only the equivalent #79.", 80)}

<h2>1.4 Unit tests, coverage and end-to-end tests</h2>
{shot("t01-unit-tests", "Figure 1.5 — Unit suite (last 40 lines of output): 50 tests, all passing.")}
{shot("t04-coverage", f"Figure 1.6 — Whole backend suite with coverage: 79 passed, {t['coverage']}% line coverage; probe.py and services.py at 100%.")}
<p>The uncovered lines are the start-up wait loop and the seed script, which run once when the container boots, plus the
<code>except RedisError</code> branches in <code>cache.py</code>. Those branches are exercised by stopping Redis by hand
(documented under the demo), not by the automated suite.</p>
{shot("t05-e2e-tests", "Figure 1.7 — End-to-end tests: Playwright drives Chromium through the six core journeys against the running stack.")}
<p>Writing the end-to-end tests directly from the acceptance criteria exposed two gaps in US-12. The API supported pausing,
but nothing in the interface could pause a monitor (AC1). "Stop watching" deleted immediately without the confirmation
AC3 requires. Both were fixed in commit <code>904790c</code>, and the E2E test now drives both paths.</p>
"""


def part_a2():
    return f"""
{h1("a2")}
<h2>2.1 Version management</h2>
<p>The repository follows <b>GitHub Flow</b>. <code>main</code> is always deployable, every unit of work happens on a short-lived
branch named after its story (<code>feat/us-25-test-suite</code>), and changes reach <code>main</code> only through a pull
request whose CI checks are green. Commits follow <b>Conventional Commits</b> (<code>feat</code>, <code>fix</code>,
<code>test</code>, <code>ci</code>, <code>docs</code>, <code>refactor</code>) and reference the issue they serve. Each review milestone
is a <b>semantic-version tag</b> with a GitHub Release: <code>v0.1.0</code> (Review 1), <code>v0.2.0</code> (Review 2),
and <code>v0.3.0-rc.1</code>, a pre-release, because Review 3's pull request is still open.</p>
{shot("v01-git-log-graph", "Figure 2.1 — Commit graph: feature branches merged through pull requests, tags at each review.")}
{shot("v02-branches-and-tags", "Figure 2.2 — Local and remote branches, and the annotated release tags.", 92)}
{shot("v03-pull-requests", "Figure 2.3 — Every change reached main through a pull request.", 92)}
{shot("v04-releases", "Figure 2.4 — Releases from the command line.", 80)}
{shot("v06-github-releases", "Figure 2.5 — The same releases on GitHub, with release notes and the tagged commit.", 88)}
{shot("v07-github-pull-request", "Figure 2.6 — Pull request #28 (this review's work) on GitHub.", 88)}

<h2>2.2 System building</h2>
<p>The system is built entirely from source by Docker. Both Dockerfiles are multi-stage, with named targets
(<code>dev</code>, <code>prod</code>, <code>worker</code>), so one file produces the development image, the production image
and, for the backend, the worker image. <code>docker compose build</code> builds all three application images, and
<code>docker compose up</code> starts them with PostgreSQL and Redis in dependency order, gated on health checks.</p>
<p>Continuous integration builds the system again on every pull request. GitHub Actions runs the backend test suites against
PostgreSQL and Redis <i>service containers</i>, type-checks and builds the Next.js frontend, and builds both production Docker
images. A pull request cannot merge with a red check. Mutation testing has its own workflow, run on demand and weekly,
because it is too slow to run on every change.</p>
{shot("b01-docker-compose-build", "Figure 2.7 — docker compose build: all three images built from source (last lines of output).")}
{shot("b02-compose-ps", "Figure 2.8 — The built system running: five containers, with db, cache and api reporting healthy.")}
{shot("b03-docker-images", "Figure 2.9 — The images the build produced.", 80)}
{shot("v05-ci-runs", "Figure 2.10 — CI runs for every pull request and every push to main.")}
{shot("b04-ci-run-steps", "Figure 2.11 — One CI run step by step: unit, integration and regression suites, coverage, frontend build, both image builds.", 72)}
{shot("v08-github-actions", "Figure 2.12 — GitHub Actions: every run of the CI workflow, all green.", 88)}
"""


FEATURES = [
    ("f01-sign-in", "Sign in", "US-02", "The entry point. A wrong password shows a message that does not reveal whether the email exists."),
    ("f02-register", "Create an account", "US-01", "The same card switches to registration; an 8+ character password creates the account and signs the user in."),
    ("f03-dashboard", "Dashboard", "US-05, 08, 09", "Every monitor on one screen with status, 24-hour uptime and latency; summary tiles; refreshes every 15 seconds."),
    ("f04-add-monitor-form", "Add a monitor", "US-06, 07", "Only a name and URL are required; method, expected status and interval default sensibly."),
    ("f05-new-monitor-pending", "New monitor appears immediately", "US-06", "The new monitor is listed at once as PENDING; the worker picks it up on its next cycle without a restart."),
    ("f06-monitor-detail-chart", "Monitor detail and history", "US-10, 11", "24-hour response-time chart with failed checks as red markers, and the raw check log in plain English."),
    ("f07-paused-monitor", "Pause and resume", "US-12", "Pausing takes the monitor out of the probe schedule; the subtitle shows PAUSED and the button offers Resume."),
    ("f08-delete-confirmation", "Delete with confirmation", "US-12", "Stop watching asks before deleting, because history and incidents are deleted with the monitor."),
    ("f09-incident-feed", "Incident feed", "US-13, 14, 15, 21", "Open incidents pinned first; resolved ones carry the plain-English summary written at recovery."),
    ("f10-public-status-page", "Public status page", "US-16, 17", "No login. Overall banner from the worst status; only monitors marked public; no URLs or raw errors."),
    ("f11-api-docs-swagger", "API documentation", "US-23", "FastAPI generates interactive OpenAPI documentation for every endpoint at /docs."),
    ("f12-health-endpoint", "Health endpoint", "US-24", "GET /health reports the API, database and cache individually; Docker's health check uses it."),
]


def part_a3():
    cells = "".join(
        f'<div class="feat"><img src="{SHOTS}/{n}.png"><div class="fc"><b>{i + 1}. {t}</b> '
        f'<span class="tag">{s}</span><br>{d}</div></div>'
        for i, (n, t, s, d) in enumerate(FEATURES))
    return f"""
{h1("a3")}
<p>Each screenshot is a browser window on the running stack, with the <code>localhost</code> address bar visible. The tag on each
caption names the user stories the feature satisfies.</p>
<div class="feats">{cells}</div>"""


TOOLS = [
    ("Frontend", "Next.js 15, React, TypeScript 5", "App Router pages, typed API client; next build fails on a type error."),
    ("Backend", "Python 3.12, FastAPI, Pydantic 2", "HTTP API, request validation, dependency injection, OpenAPI docs."),
    ("Persistence", "PostgreSQL 16, SQLAlchemy 2.0", "Relational store for users, monitors, checks and incidents; ORM models."),
    ("Cache", "Redis 7", "Cache-aside for the dashboard and public status page, invalidated on write."),
    ("Probing", "httpx", "HTTP client for probes; MockTransport for deterministic tests."),
    ("Security", "PBKDF2-SHA256, PyJWT", "Salted password hashing; signed 24-hour bearer tokens."),
    ("Containers", "Docker, Docker Compose v2", "Multi-stage images; five-service stack with health-gated start-up."),
    ("Unit / integration testing", "pytest, FastAPI TestClient", "Test runner with unit / integration / regression markers."),
    ("Coverage", "pytest-cov (coverage.py)", "Line coverage per module, reported in CI."),
    ("Mutation testing", "mutmut 2.5", "Mutates probe.py and services.py to measure how strong the tests are."),
    ("End-to-end testing", "Playwright (Chromium)", "Browser tests of the core journeys against the running stack."),
    ("Version control", "Git, GitHub, GitHub CLI", "GitHub Flow, pull requests, semantic-version tags and releases."),
    ("CI", "GitHub Actions", "Tests on Postgres/Redis service containers, frontend build, Docker image builds."),
    ("Project management", "GitHub Issues and Projects", "25 user stories as issues; board with MoSCoW, Epic and Points fields."),
    ("Diagrams", "draw.io (diagrams.net)", "Architecture, DFD, ERD and UML diagrams as editable .drawio sources."),
    ("UI design", "Figma (free plan)", "Six wireframes, committed as Figma-importable SVG."),
    ("Editor", "VS Code", "Python, Pylance, ESLint, Docker and GitLens extensions."),
]


def part_a4():
    rows = "".join(f"<tr><td>{a}</td><td><b>{b}</b></td><td>{c}</td></tr>" for a, b, c in TOOLS)
    return f"""
{h1("a4")}
<table><tr><th style="width:22%">Concern</th><th style="width:28%">Tool / technology</th><th>Used for</th></tr>{rows}</table>"""


def part_a5():
    return f"""
{h1("a5")}
<p>The demo runs from a clean clone in under two minutes, with no host dependencies beyond Docker:</p>
<pre><code class="language-bash">git clone {REPO}.git &amp;&amp; cd vigil
docker compose up --build          # five containers; demo data seeds automatically
# dashboard  http://localhost:3000   demo@vigil.dev / vigil-demo-2026
# status     http://localhost:3000/status/demo
# API docs   http://localhost:8000/docs</code></pre>
<table>
<tr><th style="width:6%">#</th><th style="width:30%">Show</th><th>What to point out</th></tr>
<tr><td>1</td><td><code>docker compose ps</code></td><td>Five containers; db, cache and api healthy. One command, no manual steps (US-23).</td></tr>
<tr><td>2</td><td>Sign in, dashboard</td><td>All monitors on one screen; status shown by word and colour; auto-refresh every 15 s.</td></tr>
<tr><td>3</td><td>Add a monitor for <code>https://httpbin.org/status/503</code></td><td>Appears as PENDING; after two probe cycles (~1 min) it turns DOWN and an incident opens. One failure alone does not (flap guard).</td></tr>
<tr><td>4</td><td>Open the Legacy invoice worker</td><td>Red failure markers on the chart; the check log reads "Expected 200, got 503".</td></tr>
<tr><td>5</td><td>Incident feed</td><td>Open incident pinned first; resolved incidents carry a one-sentence summary.</td></tr>
<tr><td>6</td><td>Public status page in a private window</td><td>No login; only public monitors; overall banner from the worst status.</td></tr>
<tr><td>7</td><td><code>docker compose stop cache</code>, reload the dashboard</td><td>Still answers (HTTP 200): cache errors are swallowed and reads fall through to PostgreSQL; <code>/health</code> reports <code>"cache": "unreachable"</code>. Measured honestly, each request is slow (about 8 s here), because resolving the stopped container's hostname times out before Redis is even tried. The planned fix is a circuit breaker that skips Redis for a few seconds after a failure.</td></tr>
<tr><td>8</td><td><code>docker compose exec api pytest -m regression -v</code></td><td>The regression suite live; then the CI checks on pull request #28.</td></tr>
</table>"""


def part_b1():
    return f"""
{h1("b1")}
<p>A developer ships a side project, a client site or an internal API. It breaks at 3 a.m., and they find out at 11 a.m. from a
message that begins "hey, is your site down?" The existing options each fail this person in a specific way:</p>
<table>
<tr><th style="width:28%">Option</th><th>Why it does not fit</th></tr>
<tr><td>Pingdom, Better Uptime, Datadog</td><td>Priced for companies. Free tiers cap at a handful of monitors and put the status page behind a paid plan.</td></tr>
<tr><td>UptimeRobot free tier</td><td>Five-minute interval and days of retention: you learn about the outage after it has ended.</td></tr>
<tr><td>A cron job running curl</td><td>No history, no trend, no incident record, nothing to show a client.</td></tr>
<tr><td>Uptime Kuma (self-hosted)</td><td>The closest comparison, but a single process on SQLite: no separate worker, no cache tier, no plain-language incident narrative.</td></tr>
</table>
<div class="note"><b>Problem statement.</b> Developers and small teams who run three to twenty web services need to learn about failures
before their users do, and to explain those failures afterwards, without paying per monitor or building monitoring themselves.
<b>Vigil</b> is a self-hosted platform that probes each service on a schedule, opens an incident on its own after repeated
failures, closes it on recovery with a plain-English explanation, and publishes a public status page, all started with one
<code>docker compose up</code>.</div>
<p><b>Users.</b> Rhea, a solo founder (primary): she needs to know before her customers do. Arjun, a backend engineer (secondary):
he needs latency history and alerts he can trust. Meera, a freelancer (tertiary): she needs unlimited monitors and an uptime figure per
client. <b>Success</b> is measured by time to first monitor (under 90 s), detection latency (within twice the interval),
false-incident rate (under one per monitor per week) and dashboard p95 (under 200 ms at 50 monitors).</p>"""


def part_b2():
    st = stories()
    counts = {}
    for s in st:
        counts.setdefault(s["moscow"], [0, 0])
        counts[s["moscow"]][0] += 1
        counts[s["moscow"]][1] += int(s["points"])
    summary = " · ".join(f"<b>{k}</b> {v[0]} stories, {v[1]} pts" for k, v in counts.items())
    rows = "".join(
        f'<tr><td><b>{s["id"]}</b><br><span class="tag">{s["moscow"]}</span><br><span class="muted">{s["points"]} pts</span></td>'
        f'<td><b>{e(s["title"])}</b><br><span class="muted">{e(s["story"])}</span></td>'
        f'<td><ul class="ac">{"".join(f"<li>{e(a)}</li>" for a in s["ac"])}</ul></td></tr>'
        for s in st)
    return f"""
{h1("b2")}
<p>Twenty-five stories across six epics, each in role / capability / benefit form, with three acceptance criteria and a
story-point estimate. They exist as GitHub Issues (<a href="{REPO}/issues">{REPO.split("//")[1]}/issues</a>) on a Project board
with MoSCoW, Epic and Points fields, all generated from one file, <code>scripts/stories.sh</code>. {summary}.</p>
<table class="stories"><tr><th style="width:11%">Story</th><th style="width:40%">User story</th><th>Acceptance criteria</th></tr>{rows}</table>"""


def part_b3():
    return f"""
{h1("b3")}
<h2>8.1 Architecture</h2>
<p>Vigil is a <b>client–server system with a layered backend</b>, packaged as five containers: the Next.js frontend, the FastAPI
API, a probe worker, PostgreSQL and Redis. It is deliberately not microservices. The API is one process over one database, and the
only thing split out is the worker, for a concrete reason: probing is slow, blocking I/O, and an outage must never slow down
the dashboard that reports it.</p>
{diagram("01-architecture", "Figure 8.1 — System architecture (deployment view).", 90)}
<h2>8.2 Module design</h2>
<p>Every source file sits in exactly one layer, and dependencies only point downward. The frontend talks to the backend only through
<code>lib/api.ts</code>. Routers stay thin: validate, authorise, delegate. Domain modules (<code>probe</code>,
<code>services</code>, <code>cache</code>, <code>security</code>) are shared by the API and the worker, which never call each
other. They meet only at the database and at a cache-key naming convention.</p>
{diagram("02-module-layers", "Figure 8.2 — Module and layer view (component diagram).", 84)}
<h2>8.3 Design principles and key decisions</h2>
<table>
<tr><th style="width:22%">Principle / decision</th><th>How it shows up, and why</th></tr>
<tr><td>Abstraction</td><td>Pages call <code>api&lt;T&gt;()</code> and never touch fetch, tokens or 401 handling. Routers call <code>cache.get_json()</code> and never touch Redis, which fails soft, so to callers the cache is optional.</td></tr>
<tr><td>High cohesion</td><td><code>probe.py</code> holds only the checking engine, in three single-purpose steps: <code>due_monitors</code> (which), <code>probe_once</code> (measure, no database writes), <code>apply_result</code> (state transition).</td></tr>
<tr><td>Low coupling</td><td>API and worker share only the schema and cache-key names; the frontend and backend share only a JSON contract (Pydantic ↔ TypeScript types); configuration is one <code>Settings</code> object read from the environment.</td></tr>
<tr><td>Separate worker</td><td>A timing-out probe holds a thread for 8 s; outside the API, an outage cannot slow the dashboard.</td></tr>
<tr><td>Cache-aside, invalidate on write</td><td>The status page spikes when something is failing; a 20 s TTL caps the database load, and invalidation keeps data no staler than one probe cycle.</td></tr>
<tr><td>Flap guard</td><td>An incident opens on the second consecutive failure, not the first, so the alert channel stays worth reading.</td></tr>
<tr><td>404, not 403</td><td>Another user's monitor returns 404, so its existence is not leaked; enforced in one helper, <code>_owned()</code>.</td></tr>
</table>
<p>The data model (Appendix C), the monitor state machine and the UML views (Appendix D) complete the design; Review 2's
Software Design Document covers each decision in more depth (<code>docs/design/</code>).</p>"""


TEST_CASES = [
    # id, level, story, technique, input / scenario, expected, test
    ("TC-01", "Integration", "US-01", "Positive", "Register with a valid email and an 8+ char password", "201, token returned, /me returns the user", "test_register_signs_the_user_in"),
    ("TC-02", "Integration", "US-01", "Negative", "Register an email that already exists", "409 'That email already has an account.'", "test_duplicate_email_is_a_409_with_a_readable_message"),
    ("TC-03", "Integration", "US-01", "Boundary", "Password of 5 characters", "422", "test_short_passwords_are_rejected"),
    ("TC-04", "Integration", "US-02", "Error guessing", "Wrong password vs unknown email", "Identical 401 bodies (no enumeration)", "test_login_does_not_reveal_whether_an_email_exists"),
    ("TC-05", "Integration", "US-04", "Equivalence", "No token / forged token", "401 on a protected route", "test_protected_routes_require_a_valid_token"),
    ("TC-06", "Integration", "US-04", "Negative", "User B reads, edits, deletes user A's monitor", "404 for every verb; A unaffected", "test_another_users_monitor_is_a_404_for_every_verb"),
    ("TC-07", "Integration", "US-06", "Positive", "Create a monitor with only name and URL", "GET / 200 / 60 s defaults, status pending", "test_a_new_monitor_needs_only_a_name_and_url"),
    ("TC-08", "Integration", "US-07", "Boundary value", "interval = 29, 30, 3600, 3601", "422, 201, 201, 422", "test_interval_is_clamped_to_30_through_3600_seconds"),
    ("TC-09", "Integration", "US-08", "Positive", "One passed and one failed check", "uptime 50.0, avg latency of successes only", "test_the_list_carries_uptime_and_latency_per_monitor"),
    ("TC-10", "Integration", "US-10", "Positive", "Checks inserted out of order", "Series returned oldest first; hours=0 → 422", "test_the_series_endpoint_returns_checks_oldest_first"),
    ("TC-11", "Integration", "US-12", "State", "Pause a monitor", "Removed from the probe schedule", "test_pausing_a_monitor_takes_it_out_of_the_probe_schedule"),
    ("TC-12", "Integration", "US-12", "Positive", "Delete a monitor with checks and incidents", "204; checks and incidents deleted", "test_deleting_a_monitor_cascades_to_its_checks_and_incidents"),
    ("TC-13", "Integration", "US-15, 18", "Positive", "Filter open incidents; acknowledge", "Only the open one; acknowledged but not resolved; other user 404", "test_the_incident_feed_filters_and_acknowledges"),
    ("TC-14", "Integration", "US-16, 17", "Positive", "One public and one private monitor", "Status page lists only the public one, no auth", "test_the_status_page_shows_only_public_monitors_without_auth"),
    ("TC-15", "Integration", "US-24", "Positive", "GET /health", "api, database, cache all ok", "test_health_reports_each_dependency"),
    ("TC-16", "Integration", "US-13, 14, 16", "State transition", "Target fails twice, then recovers", "pending → down (incident) → up (resolved, summary); banner follows", "test_an_outage_is_detected_recorded_and_explained_end_to_end"),
    ("TC-17", "Unit", "US-13", "State transition", "One failure", "Counter 1, status unchanged, no incident", "test_one_failure_is_noise_not_an_incident"),
    ("TC-18", "Unit", "US-13", "State transition", "Second consecutive failure", "down; one incident with the cause", "test_the_second_consecutive_failure_opens_an_incident"),
    ("TC-19", "Unit", "US-14", "State transition", "Success after an outage", "Incident resolved; summary names cause and minutes", "test_recovery_resolves_the_incident_and_writes_a_summary"),
    ("TC-20", "Unit", "US-08", "Boundary value", "Latency 2000.0 vs 2000.1 ms", "up vs degraded", "test_slow_but_successful_checks_are_degraded_above_two_seconds"),
    ("TC-21", "Unit", "US-11", "Error guessing", "Timeout; refused connection", "Readable error text, never an exception name", "test_probe_once_turns_a_timeout_into_a_readable_failure"),
    ("TC-22", "Unit", "US-13", "Boundary value", "Checked exactly one interval ago (frozen clock)", "Due", "test_a_monitor_is_due_at_exactly_its_interval"),
    ("TC-23", "Unit", "—", "Positive", "Worker result for one owner", "Only that owner's cache keys invalidated", "test_a_result_invalidates_exactly_the_affected_cache_keys"),
    ("TC-24", "Regression", "Review 2 defect", "Defect-based", "Open incident older than 100 newer ones", "Still returned by ?open_only=true", "test_R1_open_incident_beyond_the_feed_cap_is_still_reported"),
    ("TC-25", "Regression", "US-16", "Defect-based", "Public page for a monitor with an internal URL", "No URL or error text in the response", "test_R5_the_public_page_never_leaks_urls_or_raw_errors"),
    ("TC-26", "E2E", "US-03", "Use case", "Visit / while signed out", "Redirected to /login", "test_signed_out_visitors_are_sent_to_sign_in"),
    ("TC-27", "E2E", "US-06, 12", "Use case", "Add, pause, resume, cancel delete, confirm delete", "Each step visible in the UI; monitor gone at the end", "test_monitor_lifecycle_add_pause_resume_and_confirmed_delete"),
    ("TC-28", "E2E", "US-16", "Use case", "Open /status/demo without signing in", "Public monitors shown; private one hidden", "test_the_public_status_page_needs_no_login"),
]


def part_b4():
    rows = "".join(f'<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td><td>{d}</td><td>{e(f)}</td><td>{e(g)}</td>'
                   f'<td><code class="sm">{h}</code></td></tr>' for a, b, c, d, f, g, h in TEST_CASES)
    return f"""
{h1("b4")}
<h2>9.1 Strategy</h2>
<p>Tests are designed from the acceptance criteria first and the code second. Every acceptance criterion that describes behaviour
has at least one test, and the test name reads as the criterion. The pyramid is deliberately wide at the bottom: fast unit tests pin
exact behaviour, integration tests prove that the parts work together on the real database and cache, and a handful of end-to-end tests
cover the journeys a user actually takes. Mutation testing then measures whether the tests are strong enough, and the regression
suite stops a fixed defect from returning.</p>
<table>
<tr><th style="width:24%">Aspect</th><th>Decision</th></tr>
<tr><td>Environment</td><td>Real PostgreSQL 16 and Redis 7 (Docker locally, service containers in CI), isolated test database and Redis db 15; each test starts from empty tables and an empty cache.</td></tr>
<tr><td>Test doubles</td><td>Only the monitored targets are simulated (<code>httpx.MockTransport</code>), plus a fake clock where timing is asserted. The database, cache, auth and HTTP layer are real.</td></tr>
<tr><td>Design techniques</td><td><b>Equivalence partitioning</b> (valid / missing / forged tokens), <b>boundary-value analysis</b> (interval 29/30/3600/3601 s, latency 2000.0/2000.1 ms, the exact due moment), <b>state-transition testing</b> (Appendix D, Figure D.5), <b>error guessing</b> (timeouts, refused connections, user enumeration), and <b>defect-based</b> regression tests.</td></tr>
<tr><td>Entry / exit criteria</td><td>A pull request may merge only when the unit, integration and regression suites, the frontend build and both image builds pass in CI. The mutation score is tracked over time.</td></tr>
<tr><td>Traceability</td><td>Test names cite the behaviour; regression tests cite the defect or story; the table below maps test cases to stories.</td></tr>
</table>
<h2>9.2 Test cases</h2>
<table class="tc"><tr><th>ID</th><th>Level</th><th>Story</th><th>Technique</th><th>Input / scenario</th><th>Expected result</th><th>Automated by</th></tr>{rows}</table>
<h2>9.3 Results</h2>
<p>All {TESTS['unit'] + TESTS['integration'] + TESTS['regression']} backend tests and all {TESTS['e2e']} end-to-end tests pass locally
and in CI. Line coverage is {TESTS['coverage']}%, with <code>probe.py</code> and <code>services.py</code> at 100%. The mutation score
over those two modules rose from {pct(MUTATION['round1'])[1]}% to {pct(MUTATION['round2'])[1]}% after the mutation-driven tests, and to
{pct(MUTATION['final'])[1]}% once the last weak test was fixed; the only survivor is an equivalent mutant (Section 1.3). Writing tests from the acceptance criteria found two genuine defects, both now fixed and guarded: the open-incident
count (Review 2, R1) and the missing pause control and delete confirmation (US-12, E2E).</p>"""


def appendix_srs():
    fr = [
        ("FR-01", "The system shall let a visitor register with an email and a password of at least 8 characters, and sign them in.", "US-01"),
        ("FR-02", "The system shall authenticate users by email and password and issue a bearer token valid for 24 hours.", "US-02, 03"),
        ("FR-03", "The system shall restrict every monitor, check and incident to its owner and answer 404 for another owner's resource.", "US-04"),
        ("FR-04", "The system shall let a user create a monitor from a name and URL, with optional method, expected status and interval (30–3600 s).", "US-06, 07"),
        ("FR-05", "The system shall list a user's monitors with status, 24-hour uptime, average latency and last-checked time.", "US-05, 08"),
        ("FR-06", "The system shall let a user pause, resume, publish, unpublish and (after confirmation) delete a monitor.", "US-12, 17"),
        ("FR-07", "The system shall probe every active monitor whose interval has elapsed and record status code, latency and error.", "US-13"),
        ("FR-08", "The system shall open an incident after two consecutive failed checks and never after one.", "US-13"),
        ("FR-09", "The system shall resolve an open incident on the first successful check and store a plain-English summary.", "US-14, 21"),
        ("FR-10", "The system shall mark a monitor degraded when a successful check takes longer than 2000 ms.", "US-08"),
        ("FR-11", "The system shall provide an incident feed, filterable to open incidents, with acknowledgement.", "US-15, 18"),
        ("FR-12", "The system shall serve an unauthenticated status page per account showing only public monitors and an overall banner.", "US-16, 17"),
        ("FR-13", "The system shall show a 24-hour response-time history and the latest checks for each monitor.", "US-10, 11"),
        ("FR-14", "The system shall report the health of the API, database and cache individually.", "US-24"),
    ]
    nfr = [
        ("NFR-01", "Performance", "Dashboard list p95 under 200 ms at 50 monitors; public status page served from cache (20 s TTL)."),
        ("NFR-02", "Reliability", "An outage of a monitored target, or of Redis, must not affect the API's availability; the worker survives a failed cycle."),
        ("NFR-03", "Detection", "An incident opens within twice the configured interval of the first real failure."),
        ("NFR-04", "Security", "Salted PBKDF2-SHA256 password hashes; signed JWTs; no resource existence leaked across accounts; secrets from the environment only."),
        ("NFR-05", "Usability", "Status conveyed by word as well as colour; errors in plain English; a monitor needs only two fields."),
        ("NFR-06", "Maintainability", "Layered modules with downward-only dependencies; CI blocks merges on failing tests; mutation score tracked."),
        ("NFR-07", "Portability", "Runs anywhere Docker runs, including a Raspberry Pi 5; no host dependencies besides Docker."),
        ("NFR-08", "Deployability", "One command (docker compose up) starts a working, seeded system."),
    ]
    api = [("POST", "/api/auth/register", "Create account, return token"), ("POST", "/api/auth/login", "Sign in, return token"),
           ("GET", "/api/auth/me", "Current user"), ("GET", "/api/monitors", "List with 24 h rollup (cached 15 s)"),
           ("POST", "/api/monitors", "Create monitor"), ("GET", "/api/monitors/{id}", "One monitor with rollup"),
           ("PATCH", "/api/monitors/{id}", "Update, pause, publish"), ("DELETE", "/api/monitors/{id}", "Delete with history"),
           ("GET", "/api/monitors/{id}/checks", "Response-time series (cached 30 s)"),
           ("GET", "/api/incidents", "Feed; ?open_only=true"), ("POST", "/api/incidents/{id}/acknowledge", "Acknowledge"),
           ("GET", "/api/status/{handle}", "Public status page (no auth, cached 20 s)"), ("GET", "/health", "Dependency health")]
    return f"""
{h1("x1")}
<h2>A.1 Introduction</h2>
<p><b>Purpose.</b> This specification states what Vigil must do and how well, for the developer and the reviewers.
<b>Scope.</b> Vigil is a self-hosted HTTP/HTTPS uptime and API monitor with automatic incident detection, plain-language incident
summaries and a public status page. Out of scope for this release: log aggregation, APM, multi-region probing, mobile apps and
billing. <b>Definitions.</b> <i>Monitor</i>: a URL checked on an interval. <i>Check</i>: one probe result. <i>Incident</i>: an
outage, open from the second consecutive failure until the next success. <i>Handle</i>: the public name of an account's status page.</p>
<h2>A.2 Overall description</h2>
<p><b>Product perspective.</b> A standalone system of five containers (Section 8). <b>User classes.</b> Registered users (developers
and operators) and anonymous public visitors. <b>Operating environment.</b> Docker Engine 24+ with Compose v2 on Linux, macOS,
Windows or a Raspberry Pi 5; any modern browser. <b>Constraints.</b> One developer, one semester; zero recurring cost; every image
slim. <b>Assumptions.</b> The host has stable outbound network access; users own the endpoints they monitor; HTTP checks cover the
need for this release.</p>
<h2>A.3 Functional requirements</h2>
<table><tr><th style="width:9%">ID</th><th>Requirement</th><th style="width:12%">Stories</th></tr>
{"".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>" for a, b, c in fr)}</table>
<h2>A.4 Non-functional requirements</h2>
<table><tr><th style="width:9%">ID</th><th style="width:16%">Quality</th><th>Requirement</th></tr>
{"".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>" for a, b, c in nfr)}</table>
<h2>A.5 External interfaces</h2>
<p><b>User interface:</b> six screens (sign in / register, dashboard, add monitor, monitor detail, incident feed, public status page),
shown in Section 3. <b>Software interface:</b> a JSON REST API (OpenAPI documentation at <code>/docs</code>):</p>
<table><tr><th style="width:10%">Method</th><th style="width:34%">Path</th><th>Purpose</th></tr>
{"".join(f"<tr><td><code>{a}</code></td><td><code>{e(b)}</code></td><td>{c}</td></tr>" for a, b, c in api)}</table>
<p><b>Communications:</b> HTTPS from clients through the reverse proxy in production; HTTP(S) probes from the worker to monitored
endpoints; PostgreSQL and Redis protocols inside the Compose network only.</p>"""


def appendix_dfd():
    return f"""
{h1("x2")}
{diagram("05-dfd-level-0", "Figure B.1 — DFD Level 0 (context diagram).", 96)}
{diagram("06-dfd-level-1", "Figure B.2 — DFD Level 1: six processes and five data stores.", 100)}"""


def appendix_erd():
    return f"""
{h1("x3")}
<p>Crow's-foot notation. A user owns zero or more monitors; a monitor records zero or more checks and opens zero or more incidents.
Checks and incidents are deleted with their monitor (composition). An incident is open exactly when <code>resolved_at</code> is null,
so there is no second status column to drift out of sync.</p>
{diagram("03-data-model", "Figure C.1 — Entity-relationship diagram (PostgreSQL schema).", 100)}"""


def appendix_uml():
    return f"""
{h1("x4")}
{diagram("07-use-case", "Figure D.1 — Use case diagram.", 92)}
{diagram("08-class", "Figure D.2 — Class diagram: domain entities and the modules that operate on them.", 100)}
{diagram("09-sequence-outage", "Figure D.3 — Sequence diagram: the worker detects an outage.", 100)}
{diagram("10-sequence-dashboard", "Figure D.4 — Sequence diagram: dashboard read through the cache.", 100)}
{diagram("04-monitor-state-machine", "Figure D.5 — State machine diagram: monitor status and incident lifecycle.", 92)}
<p>The component view is Figure 8.2 and the deployment view is Figure 8.1.</p>"""


def appendix_code():
    tree = """vigil/
├── backend/            FastAPI API and probe worker (Python 3.12)
│   ├── app/            main, config, db, models, schemas, security, cache, services, probe, seed
│   │   └── routers/    auth, monitors, incidents, status
│   ├── tests/          unit, integration and regression suites + conftest
│   ├── worker.py       probe loop entrypoint
│   └── Dockerfile      targets: dev · prod · worker
├── frontend/           Next.js 15 + TypeScript (app/ pages, lib/api.ts)
├── e2e/                Playwright end-to-end tests
├── docs/               user stories, wireframes, design/, report/
├── infra/              architecture.drawio, Caddyfile
├── scripts/            GitHub bootstrap, backlog, diagram generators
├── .github/workflows/  ci.yml, mutation.yml
└── docker-compose.yml"""
    counts = [("Backend application (app/ + worker.py)", 17, 939), ("Backend tests", 8, 905),
              ("Frontend (pages, API client, styles)", 7, 1014), ("End-to-end tests", 2, 103),
              ("Scripts (bootstrap, generators)", 9, 1797), ("CI workflows", 2, 136)]
    return f"""
{h1("x5")}
<div class="note"><b>GitHub repository:</b> <a href="{REPO}">{REPO}</a><br>
<b>Release:</b> <a href="{REPO}/releases/tag/v0.3.0-rc.1">v0.3.0-rc.1</a> &nbsp;·&nbsp;
<b>Review 3 pull request:</b> <a href="{REPO}/pull/28">#28</a> &nbsp;·&nbsp;
<b>Issues:</b> <a href="{REPO}/issues">25 user stories</a></div>
<pre><code class="language-plaintext">{e(tree)}</code></pre>
<table><tr><th>Area</th><th style="width:12%">Files</th><th style="width:16%">Lines</th></tr>
{"".join(f"<tr><td>{a}</td><td>{b}</td><td>{c:,}</td></tr>" for a, b, c in counts)}</table>
<h2>E.1 backend/app/probe.py — the checking engine</h2>
{listing("backend/app/probe.py")}
<h2>E.2 backend/app/services.py — shared queries</h2>
{listing("backend/app/services.py")}
<h2>E.3 backend/app/routers/status.py — the cached public status page</h2>
{listing("backend/app/routers/status.py")}
<h2>E.4 frontend/lib/api.ts — the single HTTP client</h2>
{listing("frontend/lib/api.ts", 53, 72)}
<h2>E.5 backend/tests/test_regression.py — the regression suite</h2>
{listing("backend/tests/test_regression.py")}"""


CSS = """
:root { --a:#2B5CD9; --ink:#12161C; --body:#2E3440; --muted:#5A626D; --rule:#D5DAE1; --panel:#F4F6F8; }
@page { size: A4; margin: 15mm 15mm 17mm 15mm; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", Calibri, Arial, sans-serif; color: var(--body); font-size: 10pt; line-height: 1.45; margin: 0; }
h1 { font-size: 16pt; color: var(--ink); margin: 0 0 8pt; padding-bottom: 4pt; border-bottom: 2px solid var(--a); }
h1 .n { color: var(--a); margin-right: 8pt; }
h2 { font-size: 11.5pt; color: var(--ink); margin: 12pt 0 4pt; break-after: avoid; }
p { margin: 0 0 6pt; } ul { margin: 0 0 6pt; padding-left: 16pt; } li { margin-bottom: 2pt; }
a { color: var(--a); text-decoration: none; }
code { font-family: Consolas, monospace; font-size: 8.8pt; background: var(--panel); padding: 0 2pt; border-radius: 2pt; color: #24303F; }
code.sm { font-size: 7.2pt; background: none; padding: 0; word-break: break-all; }
pre { margin: 4pt 0 8pt; }
pre code.hljs { display: block; font-size: 7.8pt; line-height: 1.32; padding: 6pt 8pt; background: #F6F8FA; border: 1px solid #E1E5EA; border-left: 3px solid var(--a); border-radius: 3pt; white-space: pre-wrap; }
.src { font-size: 7.6pt; color: var(--muted); margin: -4pt 0 8pt; font-family: Consolas, monospace; }
figure { margin: 6pt 0 10pt; text-align: center; break-inside: avoid; }
figure img { max-width: 100%; border: 1px solid var(--rule); border-radius: 3pt; }
figcaption { font-size: 8.4pt; color: var(--muted); font-style: italic; margin-top: 3pt; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 9pt; font-size: 8.7pt; }
tr { break-inside: avoid; }
th { background: #E8EDF7; color: var(--ink); text-align: left; font-weight: 600; }
th, td { border: 1px solid var(--rule); padding: 3.2pt 5pt; vertical-align: top; }
table.tc { font-size: 7.6pt; } table.stories { font-size: 8pt; }
ul.ac { margin: 0; padding-left: 12pt; } ul.ac li { margin: 0 0 1pt; }
.muted { color: var(--muted); } .tag { display: inline-block; font-size: 7.4pt; color: var(--a); border: 1px solid #C9D6F5; background: #EEF3FE; border-radius: 8pt; padding: 0 5pt; }
.note { background: #EEF3FE; border-left: 3px solid var(--a); padding: 6pt 9pt; margin: 6pt 0 9pt; font-size: 9.2pt; color: #1E3A6E; break-inside: avoid; }
.pb { break-before: page; }
.cover { height: 250mm; display: flex; flex-direction: column; justify-content: center; text-align: center; }
.kicker { color: var(--a); font-size: 9pt; font-weight: 700; letter-spacing: 2pt; }
.ctitle { font-size: 52pt; font-weight: 800; color: var(--ink); margin: 10pt 0 2pt; }
.csub { font-size: 14pt; color: var(--muted); font-style: italic; }
.crule { width: 60%; margin: 22pt auto; border-bottom: 1px solid var(--rule); }
.cmeta div { margin: 5pt 0; font-size: 11pt; color: var(--ink); font-weight: 600; }
.cmeta b { display: inline-block; width: 160pt; text-align: right; margin-right: 12pt; font-weight: 400; color: var(--muted); font-size: 9.5pt; }
.toc-h { margin-bottom: 12pt; }
.toc-part { font-weight: 700; color: var(--a); margin: 12pt 0 4pt; font-size: 10.5pt; }
.toc-row { display: flex; align-items: baseline; margin: 4pt 0; font-size: 10.5pt; }
.toc-n { width: 22pt; color: var(--a); font-weight: 700; } .toc-dots { flex: 1; border-bottom: 1px dotted #9AA3AE; margin: 0 6pt; transform: translateY(-3pt); }
.toc-p { width: 22pt; text-align: right; }
.feats { display: grid; grid-template-columns: 1fr 1fr; gap: 10pt 12pt; }
.feat { break-inside: avoid; } .feat img { width: 100%; border: 1px solid var(--rule); border-radius: 3pt; }
.fc { font-size: 8.4pt; margin-top: 3pt; } .fc b { color: var(--ink); }
"""


def document(pages):
    body = "".join([cover(pages), part_a1(), part_a2(), part_a3(), part_a4(), part_a5(), part_b1(), part_b2(),
                    part_b3(), part_b4(), appendix_srs(), appendix_dfd(), appendix_erd(), appendix_uml(),
                    appendix_code()])
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Vigil — Project Report</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/typescript.min.js"></script>
<style>{CSS}</style></head><body>{body}<script>hljs.highlightAll();</script></body></html>"""


FOOTER = ('<div style="font-family:Segoe UI,Arial;font-size:8px;color:#79818D;width:100%;padding:0 15mm;'
          'display:flex;justify-content:space-between"><span>Vigil — Project Report (Review 3) · '
          'github.com/vatsal-agra/vigil</span><span>Page <span class="pageNumber"></span> of '
          '<span class="totalPages"></span></span></div>')


def render(pages, out):
    src = BUILD / "report.html"
    src.write_text(document(pages), encoding="utf-8")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        p = b.new_page()
        p.goto(src.as_uri(), wait_until="networkidle")
        p.wait_for_function("document.querySelectorAll('code.hljs').length > 0")
        p.pdf(path=str(out), format="A4", print_background=True, display_header_footer=True,
              header_template="<span></span>", footer_template=FOOTER, prefer_css_page_size=True)
        b.close()


def find_pages(pdf):
    doc = fitz.open(pdf)
    found = {}
    tops = []
    for i in range(doc.page_count):                # every section starts a page: read its first lines
        lines = [ln.strip() for ln in doc[i].get_text().splitlines() if ln.strip()]
        tops.append(" ".join(lines[:3]))
    for anchor, num, title in SECTIONS:
        for i in range(2, doc.page_count):         # skip cover and contents
            if title in tops[i]:
                found[anchor] = i + 1
                break
    return found, doc.page_count


def main():
    render({}, OUT)
    pages, total = find_pages(OUT)
    render(pages, OUT)
    pages2, total = find_pages(OUT)
    assert pages == pages2, (pages, pages2)
    shutil.copy(OUT, ROOT / "docs" / "report" / OUT.name)
    print(f"written {OUT.name}: {total} pages")
    for a, n, t in SECTIONS:
        print(f"  {n:>2}  {t:<55} p.{pages.get(a, '??')}")


if __name__ == "__main__":
    main()
