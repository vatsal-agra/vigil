const fs = require("fs");
const path = require("path");

const DIR = __dirname;
const ROOT = path.resolve(__dirname, "..", "..");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  ImageRun, PageBreak, PageOrientation, convertInchesToTwip, ExternalHyperlink,
} = require("docx");

const asset = (n) => path.join(DIR, "assets", n);
const stories = JSON.parse(fs.readFileSync(path.join(DIR, "assets", "stories.json"), "utf8"));
const A = "2B5CD9";      // accent
const INK = "12161C";
const MUTED = "5A626D";
const RULE = "D5DAE1";
const PANEL = "F4F6F8";

const PORTRAIT_W = 9746;
const LANDSCAPE_W = 14678;

// ---------------------------------------------------------------- helpers

const h1 = (t, n) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  keepNext: true,
  spacing: { before: 360, after: 160 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: A, space: 6 } },
  children: [
    ...(n ? [new TextRun({ text: n + "  ", bold: true, size: 30, color: A, font: "Calibri" })] : []),
    new TextRun({ text: t, bold: true, size: 30, color: INK, font: "Calibri" }),
  ],
});

const h2 = (t) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  keepNext: true,
  spacing: { before: 280, after: 120 },
  children: [new TextRun({ text: t, bold: true, size: 24, color: INK, font: "Calibri" })],
});

const h3 = (t) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  keepNext: true,
  spacing: { before: 200, after: 80 },
  children: [new TextRun({ text: t, bold: true, size: 21, color: A, font: "Calibri" })],
});

const p = (t, opts = {}) => new Paragraph({
  spacing: { after: opts.after ?? 120, line: 276 },
  alignment: opts.align,
  children: (Array.isArray(t) ? t : [t]).map((x) =>
    typeof x === "string"
      ? new TextRun({ text: x, size: 21, color: opts.color ?? INK, font: "Calibri", italics: opts.italics })
      : x),
});

const b = (t) => new TextRun({ text: t, bold: true, size: 21, color: INK, font: "Calibri" });
const mono = (t) => new TextRun({ text: t, size: 19, color: "24303F", font: "Consolas" });

const bullet = (t, level = 0) => new Paragraph({
  bullet: { level },
  spacing: { after: 70, line: 264 },
  children: (Array.isArray(t) ? t : [t]).map((x) =>
    typeof x === "string" ? new TextRun({ text: x, size: 21, color: INK, font: "Calibri" }) : x),
});

const code = (lines) => lines.map((ln, i) => new Paragraph({
  spacing: { before: i === 0 ? 100 : 0, after: i === lines.length - 1 ? 160 : 0 },
  shading: { type: ShadingType.CLEAR, fill: PANEL },
  indent: { left: 120, right: 120 },
  children: [new TextRun({ text: ln || " ", size: 18, font: "Consolas", color: "23303F" })],
}));

const cell = (children, w, opts = {}) => new TableCell({
  width: { size: w, type: WidthType.DXA },
  shading: opts.fill ? { type: ShadingType.CLEAR, fill: opts.fill } : undefined,
  margins: { top: 70, bottom: 70, left: 110, right: 110 },
  verticalAlign: "top",
  children,
});

const tcell = (text, w, opts = {}) => cell(
  (Array.isArray(text) ? text : [text]).map((t) => new Paragraph({
    spacing: { after: 30, line: 250 },
    children: [new TextRun({
      text: t, size: opts.size ?? 18, bold: opts.bold, color: opts.color ?? INK,
      font: opts.font ?? "Calibri",
    })],
  })), w, opts);

const table = (widths, headers, rows) => new Table({
  columnWidths: widths,
  width: { size: widths.reduce((a, c) => a + c, 0), type: WidthType.DXA },
  borders: {
    top: { style: BorderStyle.SINGLE, size: 4, color: RULE },
    bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE },
    left: { style: BorderStyle.SINGLE, size: 4, color: RULE },
    right: { style: BorderStyle.SINGLE, size: 4, color: RULE },
    insideHorizontal: { style: BorderStyle.SINGLE, size: 4, color: RULE },
    insideVertical: { style: BorderStyle.SINGLE, size: 4, color: RULE },
  },
  rows: [
    new TableRow({
      tableHeader: true,
      children: headers.map((hd, i) => tcell(hd, widths[i], { bold: true, fill: "E8EDF7", size: 18 })),
    }),
    ...rows.map((r) => new TableRow({
      children: r.map((c, i) => Array.isArray(c) && c[0] && c[0].type === "cell"
        ? c[1] : tcell(c, widths[i])),
    })),
  ],
});

const img = (path, w, h) => new Paragraph({
  spacing: { before: 120, after: 60 },
  alignment: AlignmentType.CENTER,
  keepNext: true,
  keepLines: true,
  children: [new ImageRun({ type: "png", data: fs.readFileSync(path), transformation: { width: w, height: h } })],
});

const caption = (t) => new Paragraph({
  spacing: { after: 260 },
  alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: t, size: 17, italics: true, color: MUTED, font: "Calibri" })],
});

const brk = () => new Paragraph({ children: [new PageBreak()] });

const note = (t) => new Paragraph({
  spacing: { before: 120, after: 200 },
  shading: { type: ShadingType.CLEAR, fill: "EEF3FE" },
  indent: { left: 120, right: 120 },
  border: { left: { style: BorderStyle.SINGLE, size: 18, color: A, space: 8 } },
  children: [new TextRun({ text: t, size: 19, color: "1E3A6E", font: "Calibri" })],
});

// ================================================================ TITLE

const title = [
  new Paragraph({ spacing: { before: 2200, after: 0 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "DIGITAL ASSIGNMENT 1  /  REVIEW 1", size: 20, bold: true, color: A, font: "Calibri", characterSpacing: 60 })] }),
  new Paragraph({ spacing: { before: 260, after: 0 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Vigil", size: 76, bold: true, color: INK, font: "Calibri" })] }),
  new Paragraph({ spacing: { before: 60, after: 400 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Uptime and API monitoring that explains its own outages", size: 26, color: MUTED, font: "Calibri", italics: true })] }),
  new Paragraph({ spacing: { after: 500 }, alignment: AlignmentType.CENTER,
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: RULE, space: 10 } },
    children: [new TextRun({ text: " ", size: 2 })] }),
  ...[["Name", "Vatsal Agrawal"],
      ["Registration Number", "24BAI1355"],
      ["Programme", "B.Tech, Computer Science and Engineering (AI & ML)"],
      ["Campus", "Vellore Institute of Technology, Chennai"],
      ["Repository", "github.com/vatsal-agra/vigil"],
      ["Date", "31 July 2026"]].map(([k, v]) =>
    new Paragraph({ spacing: { after: 110 }, alignment: AlignmentType.CENTER,
      children: [
        new TextRun({ text: k + "   ", size: 19, color: MUTED, font: "Calibri" }),
        new TextRun({ text: v, size: 21, bold: true, color: INK, font: "Calibri" }),
      ] })),
  brk(),
];

// ================================================================ CONTENTS

const contents = [
  h1("Contents"),
  ...[["1", "Vision Document", "3"],
      ["2", "Twenty-Five User Stories (GitHub Issues and Projects)", "7"],
      ["3", "MoSCoW Prioritisation and Wireframes", "12"],
      ["4", "Architecture Diagram", "19"],
      ["5", "Development Setup", "21"],
      ["6", "Proof That Everything Works", "29"]].map(([n, t, pg]) =>
    new Paragraph({ spacing: { after: 130 },
      tabStops: [{ type: "right", position: 9600, leader: "dot" }],
      children: [
        new TextRun({ text: n + ".", size: 21, bold: true, color: A, font: "Calibri" }),
        new TextRun({ text: "   " + t + "\t" + pg, size: 21, color: INK, font: "Calibri" }),
      ] })),
  note("Deliverables 1 to 4 are reproduced in full below. Deliverable 5 includes screenshots "
     + "captured from the live environment: the running Docker stack, the application in the "
     + "browser on localhost, and the GitHub repository, issues and project board."),
  brk(),
];

// ================================================================ 1. VISION

const vision = [
  h1("Vision Document", "1."),
  note("As required, this vision document is committed as Markdown in the repository's README.md. "
     + "Its full content is reproduced here."),

  h2("1.1  Project Name and Overview"),
  p([b("Vigil"), " is a self-hosted uptime and API monitoring platform. You give it a URL; it checks that URL on a schedule from a background worker, records every response, and opens an incident on its own when the service stops answering. When the service recovers, it closes the incident and writes a one-sentence explanation of what happened."]),
  p("It ships as five containers — a Next.js frontend, a FastAPI backend, a probe worker, PostgreSQL, and Redis — that come up together with a single docker compose up."),
  p(["The name is literal. A ", new TextRun({ text: "vigil", size: 21, italics: true, font: "Calibri", color: INK }), " is a watch kept through the night, when nobody else is looking. That is the entire job."]),

  h2("1.2  The Problem It Solves"),
  p("A developer ships a side project, a client site, or an internal API. Then it breaks at 3am, and they find out at 11am from a message that starts with \u201chey, is your site down?\u201d"),
  p("The existing options each fail this person in a specific way:"),
  table([2600, 7146],
    ["Option", "Why it does not fit"],
    [["Pingdom, Better Uptime, Datadog", "Priced for companies. Free tiers cap at 1\u201310 monitors and put the status page behind a paid plan."],
     ["UptimeRobot free tier", "Five-minute check interval and retention measured in days. You learn about the outage after it has ended."],
     ["A cron job running curl", "No history, no trend, no incident record, nothing to show a client. Answers \u201cis it up now\u201d, never \u201chow often does this break\u201d."],
     ["Uptime Kuma (self-hosted)", "Genuinely good and the closest comparison. But a single monolithic process on SQLite: no separate worker, no cache tier, no plain-language incident narrative."]]),
  p([b("The gap Vigil aims at: "), "an operator who owns three to twenty services and needs history, incident records, and a customer-facing status page, without a per-monitor subscription."], { after: 240 }),

  h2("1.3  Target Users (Personas)"),

  h3("Persona 1 — Rhea, the solo founder  (primary)"),
  p("Twenty-one, final-year CS, runs a small paid SaaS with about 400 users out of her hostel room. Deploys to a single VPS. Ships on Friday nights.", { italics: true, color: MUTED }),
  bullet([b("Goal:  "), "find out about an outage before a customer does, and have something to point customers at that is not a personal apology on WhatsApp."]),
  bullet([b("Frustration:  "), "her monitoring is a browser tab she forgets to look at. She has twice discovered downtime from a refund request."]),
  bullet([b("Needs from Vigil:  "), "instant setup, a public status page on her own domain, and email the moment something breaks."]),
  bullet([b("Success looks like:  "), "she never again learns about downtime from a customer."]),

  h3("Persona 2 — Arjun, backend engineer at a twelve-person startup  (secondary)"),
  p("Twenty-seven, owns eight internal services, on call every third week.", { italics: true, color: MUTED }),
  bullet([b("Goal:  "), "distinguish \u201cthe API is down\u201d from \u201cthe API got four times slower after this morning's deploy\u201d."]),
  bullet([b("Frustration:  "), "their alerting fires on single failed checks, so the channel is full of false alarms and everyone has muted it."]),
  bullet([b("Needs from Vigil:  "), "per-endpoint response-time history, a flap guard so one blip is not an incident, and Slack alerts he can trust."]),
  bullet([b("Success looks like:  "), "the alert channel becomes worth reading again."]),

  h3("Persona 3 — Meera, freelance web developer  (tertiary)"),
  p("Twenty-four, maintains fifteen client WordPress and Next.js sites on a retainer.", { italics: true, color: MUTED }),
  bullet([b("Goal:  "), "prove she is providing the uptime her contract promises."]),
  bullet([b("Frustration:  "), "paying per monitor across fifteen client sites costs more than one retainer earns."]),
  bullet([b("Needs from Vigil:  "), "unlimited monitors on hardware she already pays for, and a monthly uptime figure per client."]),
  bullet([b("Success looks like:  "), "renewal conversations that start from a number instead of a feeling."]),

  h2("1.4  Vision Statement"),
  new Paragraph({
    spacing: { before: 140, after: 260 },
    shading: { type: ShadingType.CLEAR, fill: PANEL },
    indent: { left: 200, right: 200 },
    border: { left: { style: BorderStyle.SINGLE, size: 24, color: A, space: 10 } },
    children: [
      new TextRun({ text: "For ", bold: true, size: 22, font: "Calibri", color: INK }),
      new TextRun({ text: "developers and small teams who run services they cannot afford to babysit, ", size: 22, font: "Calibri", color: INK }),
      new TextRun({ text: "who ", bold: true, size: 22, font: "Calibri", color: INK }),
      new TextRun({ text: "need to know about failures immediately and explain them afterwards, ", size: 22, font: "Calibri", color: INK }),
      new TextRun({ text: "Vigil ", bold: true, size: 22, font: "Calibri", color: INK }),
      new TextRun({ text: "is a self-hosted monitoring platform ", size: 22, font: "Calibri", color: INK }),
      new TextRun({ text: "that ", bold: true, size: 22, font: "Calibri", color: INK }),
      new TextRun({ text: "detects outages automatically, records them as incidents in plain language, and publishes a status page your users can read. ", size: 22, font: "Calibri", color: INK }),
      new TextRun({ text: "Unlike ", bold: true, size: 22, font: "Calibri", color: INK }),
      new TextRun({ text: "hosted monitoring priced per endpoint, or a cron job that leaves no history, ", size: 22, font: "Calibri", color: INK }),
      new TextRun({ text: "Vigil ", bold: true, size: 22, font: "Calibri", color: INK }),
      new TextRun({ text: "runs entirely on your own hardware, costs nothing per monitor, and treats the incident narrative \u2014 not the raw check \u2014 as the thing that matters.", size: 22, font: "Calibri", color: INK }),
    ],
  }),

  h2("1.5  Key Features and Goals"),
  h3("Shipping in this release"),
  bullet([b("Automatic detection.  "), "A dedicated worker probes each monitor on its own interval. Two consecutive failures open an incident; the next success closes it. The flap guard is deliberate \u2014 one bad check is noise."]),
  bullet([b("Response-time history.  "), "Every check is stored with its latency, so slow is visible, not just down."]),
  bullet([b("Plain-language incidents.  "), "Each resolved incident carries a sentence a non-engineer can read: what broke, how long, and where it stands now."]),
  bullet([b("Public status page.  "), "An unauthenticated page per account, served from cache, showing only the services you explicitly publish."]),
  bullet([b("One-command setup.  "), "docker compose up gives a working system with seeded demo data."]),
  h3("Explicit non-goals for version 1"),
  bullet("No log aggregation, APM, or tracing. Vigil answers \u201cis it up and how fast\u201d, nothing deeper."),
  bullet("No multi-region probing. A single vantage point is honest about what it can measure."),
  bullet("No mobile app. The dashboard is responsive; that is enough."),
  bullet("No multi-tenant SaaS billing. It is self-hosted software, not a product to resell."),

  h2("1.6  Success Metrics"),
  table([500, 2500, 2900, 3846],
    ["#", "Metric", "Target", "How it is measured"],
    [["1", "Time to first monitor", "Under 90 seconds from docker compose up to a monitor being checked", "Manual stopwatch on a clean machine, recorded per release"],
     ["2", "Detection latency", "Incident opens within twice the configured interval of the first real failure", "Integration test that kills a target container and asserts on incidents.started_at"],
     ["3", "False-incident rate", "Fewer than one spurious incident per monitor per week", "Incidents shorter than 60s with no corresponding target-side failure, counted weekly"],
     ["4", "Dashboard response time", "p95 under 200 ms for the monitor list at 50 monitors", "Locust run against a seeded database; the Redis cache is what makes this pass"],
     ["5", "Cold-start reliability", "Ten consecutive down -v / up cycles reach healthy with no manual steps", "Scripted in CI"],
     ["6", "Backlog completion", "100% of Must-have stories closed by milestone M1", "GitHub Project board"]]),

  h2("1.7  Assumptions and Constraints"),
  h3("Assumptions"),
  bullet("Users are comfortable with a terminal and Docker. This is developer software and it does not apologise for that."),
  bullet("The host has a stable outbound network. A probe failure caused by the host's own connection is indistinguishable from a target failure \u2014 a known limitation, documented rather than hidden."),
  bullet("Users own the endpoints they monitor. There is no consent workflow."),
  bullet("HTTP and HTTPS checks cover the overwhelming majority of need. TCP, ICMP, and DNS checks are deferred."),
  bullet("A minimum thirty-second interval is acceptable. Anything faster is a load test, not monitoring."),
  h3("Constraints"),
  table([1700, 8046],
    ["Kind", "Constraint"],
    [["Time", "One academic semester, one developer. This is the binding constraint, and it is what the MoSCoW prioritisation in Section 3 exists to manage."],
     ["Hardware", "Must run on a Raspberry Pi 5 (8 GB). Every image is slim or alpine; no image exceeds 400 MB. This rules out Elasticsearch-class dependencies."],
     ["Cost", "Zero recurring spend. GitHub Actions free tier, Cloudflare free tier, self-hosted everything."],
     ["Data", "Checks accumulate at roughly 1,440 rows per monitor per day at a sixty-second interval. Retention and downsampling are required before this is production-grade \u2014 currently a documented debt item."],
     ["Security", "Self-hosted means the operator owns their own TLS and secrets. Vigil ships no default credentials in production mode and refuses to start with the default JWT secret when ENV=production."],
     ["Skill", "Solo build across Python, TypeScript, SQL, and Docker. Anything needing a fifth stack was cut, which is why alerting uses plain SMTP rather than a message queue."]]),
  img(asset("s01-repo-readme.png"), 620, 354),
  caption("Screenshot 1 — The vision document rendering as README.md on the repository landing page."),
  brk(),
];

// ================================================================ 2. STORIES

const epicOrder = ["Accounts and access", "Monitors", "Checking engine", "Public status", "Alerting", "Operations"];
const storySections = [];
epicOrder.forEach((ep) => {
  const inEpic = stories.filter((s) => s.epic === ep);
  const pts = inEpic.reduce((a, c) => a + c.points, 0);
  storySections.push(h2(`Epic \u2014 ${ep}   (${inEpic.length} stories, ${pts} points)`));
  storySections.push(table([760, 3500, 3886, 800, 800],
    ["ID", "User story", "Acceptance criteria", "MoSCoW", "Pts"],
    inEpic.map((s) => [
      [s.id],
      [s.title, "", s.story],
      s.ac.map((a) => "\u2022  " + a),
      [s.moscow],
      [String(s.points)],
    ])));
  storySections.push(p(" ", { after: 60 }));
});

const userStories = [
  h1("Twenty-Five User Stories", "2."),
  p("The backlog is twenty-five stories across six epics, each written in role/capability/benefit form with three acceptance criteria and a story-point estimate on a modified Fibonacci scale (1, 2, 3, 5, 8)."),
  p("All twenty-five exist as GitHub Issues and are tracked on a GitHub Project board with MoSCoW, Epic, and Points fields. Creation is scripted rather than hand-clicked, so the backlog is reproducible:"),
  ...code([
    "$ gh auth login",
    "$ gh auth refresh -s project,read:project",
    "$ ./scripts/bootstrap-github.sh",
    "",
    "  Labels     15 created  (6 epic, 4 MoSCoW, 5 discipline)",
    "  Issues     25 created",
    "  Project    Vigil - Product Backlog",
    "  Fields     MoSCoW (select) - Epic (select) - Points (number)",
    "  Items      25 added, all field values set from labels",
  ]),
  note("scripts/stories.sh is the single source of truth for the backlog. The issue seeder, the "
     + "project-board script, and this document are all generated from it, so they cannot drift apart."),
  table([2400, 1600, 1600, 1600, 2546],
    ["Total", "Must have", "Should have", "Could have", "Won't have (this release)"],
    [["25 stories, 91 points", "16 stories, 58 pts", "6 stories, 22 pts", "2 stories, 6 pts", "1 story, 5 pts"]]),
  p(" ", { after: 60 }),
  ...storySections,
  img(asset("s03-issues.png"), 620, 354),
  caption("Screenshot 3 — The twenty-five user stories as GitHub Issues, labelled by epic and MoSCoW priority."),
  img(asset("s04-project-board.png"), 620, 354),
  caption("Screenshot 4 — The GitHub Project board, grouped by the MoSCoW single-select field."),
  brk(),
];

// ================================================================ 3. MOSCOW + WIREFRAMES

const wireframes = [
  [asset("01-sign-in.png"), "Wireframe 1 \u2014 Sign in.", "Entry point, satisfying US-01 and US-02. A single field pair: no social login in version 1, because self-hosted users have no shared identity provider. Errors render above the card in the interface voice."],
  [asset("02-dashboard.png"), "Wireframe 2 \u2014 Dashboard, the monitor list.", "The primary screen, satisfying US-05, US-08 and US-09. The signature element is the check strip: one tick per probe, coloured by outcome, so an outage is visible without opening anything."],
  [asset("03-add-monitor.png"), "Wireframe 3 \u2014 Add monitor.", "Creation flow, satisfying US-06 and US-07. Only name and URL are required; method, expected status and interval have working defaults. The minimum interval is enforced server-side so a user cannot self-inflict rate limits."],
  [asset("04-monitor-detail.png"), "Wireframe 4 \u2014 Monitor detail.", "Drill-down, satisfying US-10, US-11 and US-12. Failed checks are drawn as vertical markers on the chart so gaps are explained rather than merely absent."],
  [asset("05-incidents.png"), "Wireframe 5 \u2014 Incident feed.", "Triage, satisfying US-13, US-14 and US-15. An incident opens automatically after two consecutive failed checks and closes on the first success, so nothing is filed by hand."],
  [asset("06-public-status.png"), "Wireframe 6 \u2014 Public status page.", "Unauthenticated, satisfying US-16 and US-17. Served from a Redis-cached endpoint with a twenty-second TTL, so a traffic spike during an outage cannot take the database down."],
];

const moscow = [
  h1("MoSCoW Prioritisation and Wireframes", "3."),
  h2("3.1  MoSCoW Prioritisation"),
  table([1900, 1100, 1100, 1200, 4446],
    ["Priority", "Stories", "Points", "% of backlog", "Story IDs"],
    [["Must have", "16", "58", "64%", "US-01, 02, 03, 04, 05, 06, 07, 08, 10, 11, 12, 13, 14, 15, 23, 24"],
     ["Should have", "6", "22", "24%", "US-09, 16, 17, 18, 19, 25"],
     ["Could have", "2", "6", "7%", "US-20, 21"],
     ["Won't have (this release)", "1", "5", "5%", "US-22"],
     ["Total", "25", "91", "100%", ""]]),
  p(" ", { after: 60 }),
  h3("Why these are the Must haves"),
  p("The core loop is: sign in \u2192 add a URL \u2192 the system checks it \u2192 the system tells you when it broke. Every Must-have story is load-bearing for that sentence. Remove any one of them and Vigil is not a monitoring tool."),
  h3("Why the status page is only a Should have"),
  p("It is the strongest differentiator against a cron job and a curl, but a developer monitoring their own side projects gets full value without it. It ships in milestone M2."),
  h3("Why quiet hours is a Won't have"),
  p("It needs per-account timezone handling and a scheduler, and it only matters once alerting is heavily used. Deferring it entirely is cheaper than half-building it."),
  h3("A note on the 64% Must-have share"),
  p("Sixty-four percent is high; sixty percent is the usual ceiling for a commercial backlog. It is defensible here because this is a version 1 with no existing users: there is no working product to fall back on if a Must slips, so the walking skeleton genuinely is all-or-nothing. The mitigation is that the M1 stories are small \u2014 the median is three points and only one story is an eight."),
  h3("Release plan"),
  table([2600, 5146, 2000],
    ["Milestone", "Contents", "Size"],
    [["M1 \u2014 Walking skeleton", "All Must-have stories. A user can sign up, add a URL, and see it go down.", "16 stories, 58 pts"],
     ["M2 \u2014 Usable product", "Should have. Status page, alerting, auto-refresh, CI.", "6 stories, 22 pts"],
     ["M3 \u2014 Polish", "Could have. Only if the semester allows.", "2 stories, 6 pts"],
     ["Deferred", "Won't have this release.", "1 story, 5 pts"]]),
  brk(),
  h2("3.2  Wireframes \u2014 Six Screens"),
  p("Six screens were produced covering the complete primary journey: sign in, see everything, add something new, drill into one service, triage an incident, and publish status externally. Each screen carries numbered annotations in the gutter explaining the design decision behind it, and cross-references the user stories it satisfies."),
  note("The wireframes are committed as SVG in docs/wireframes/ and import into Figma as editable "
     + "frames via File \u2192 Import. They are generated by scripts/make_wireframes.py, which is why "
     + "spacing, type scale and component styling are identical across all six."),
];

wireframes.forEach(([path, cap, desc], i) => {
  moscow.push(img(path, 640, 434));
  moscow.push(caption(cap));
  moscow.push(p(desc, { after: 200 }));
  if (i % 2 === 1 && i !== wireframes.length - 1) moscow.push(brk());
});
moscow.push(brk());

// ================================================================ 4. ARCHITECTURE (landscape)

const architecture = [
  h1("Architecture Diagram", "4."),
  p("Single page, landscape orientation. The diagram shows the complete flow from frontend through backend to data and cache tiers, the containerisation boundary, and the deployment path. Arrows carry labels; a legend keys the tier colours and distinguishes synchronous request paths from asynchronous and deployment paths."),
  img(asset("architecture.png"), 770, 456),
  caption("Figure 1 \u2014 Vigil system architecture. Editable source: infra/architecture.drawio (open at diagrams.net)."),
];

// ================================================================ 4b explanation + 5 DEV SETUP

const devsetup = [
  h2("4.1  Why Each Component Is There"),
  table([2200, 7546],
    ["Decision", "Reasoning"],
    [["A separate worker container", "Probing is slow, blocking I/O \u2014 a monitor that times out occupies a thread for eight seconds. Inside the API process that would make the dashboard slow during an outage, which is exactly when people are reloading it. Splitting them means an outage never degrades the tool reporting the outage."],
     ["Redis as a real cache tier", "The public status page is the one endpoint that spikes precisely when the system is already unhealthy. A twenty-second TTL means a thousand worried customers produce three database queries a minute. The worker deletes the affected keys on write, so the cache is never stale by more than one probe cycle."],
     ["PostgreSQL rather than SQLite", "Two processes write to the checks table concurrently. SQLite's writer lock makes that a correctness problem, not merely a performance one."],
     ["A named volume, not a bind mount", "Database files in a bind mount on a Pi's SD card are a data-loss story waiting to happen."],
     ["Cloudflare Tunnel in front of Caddy", "Gives TLS and DDoS protection without forwarding a port on a home router or exposing a public IP."]]),
  h2("4.2  Request Path for the Dashboard"),
  bullet("The browser sends GET /api/monitors with a Bearer token."),
  bullet("The dependency security.current_user verifies the JWT and loads the user."),
  bullet("The router checks Redis for monitors:list:<user_id>. On a hit it returns immediately."),
  bullet("On a miss it queries Postgres, computes the twenty-four-hour rollup per monitor, writes the result to Redis with a fifteen-second TTL, and returns."),
  bullet("Meanwhile the worker writes new checks and deletes those keys, so the next read is fresh."),
  brk(),

  h1("Development Setup", "5."),

  h2("5.1  Repository Structure"),
  ...code([
    "vigil/",
    "\u251c\u2500\u2500 .github/",
    "\u2502   \u251c\u2500\u2500 ISSUE_TEMPLATE/          user-story and bug-report forms",
    "\u2502   \u251c\u2500\u2500 workflows/ci.yml         pytest \u00b7 next build \u00b7 docker build",
    "\u2502   \u2514\u2500\u2500 pull_request_template.md",
    "\u251c\u2500\u2500 backend/",
    "\u2502   \u251c\u2500\u2500 app/",
    "\u2502   \u2502   \u251c\u2500\u2500 main.py              FastAPI app, lifespan, /health",
    "\u2502   \u2502   \u251c\u2500\u2500 config.py            environment-driven settings",
    "\u2502   \u2502   \u251c\u2500\u2500 db.py                engine and session factory",
    "\u2502   \u2502   \u251c\u2500\u2500 models.py            User \u00b7 Monitor \u00b7 Check \u00b7 Incident",
    "\u2502   \u2502   \u251c\u2500\u2500 schemas.py           Pydantic request/response contracts",
    "\u2502   \u2502   \u251c\u2500\u2500 security.py          PBKDF2 hashing, JWT issue and verify",
    "\u2502   \u2502   \u251c\u2500\u2500 cache.py             Redis helpers, degrade gracefully",
    "\u2502   \u2502   \u251c\u2500\u2500 services.py          shared queries, uptime rollups, slugs",
    "\u2502   \u2502   \u251c\u2500\u2500 probe.py             checking engine, incident state machine",
    "\u2502   \u2502   \u251c\u2500\u2500 seed.py              demo account and backfilled history",
    "\u2502   \u2502   \u2514\u2500\u2500 routers/             auth \u00b7 monitors \u00b7 incidents \u00b7 status",
    "\u2502   \u251c\u2500\u2500 tests/",
    "\u2502   \u251c\u2500\u2500 worker.py                probe loop entrypoint",
    "\u2502   \u251c\u2500\u2500 requirements.txt",
    "\u2502   \u2514\u2500\u2500 Dockerfile               targets: base \u00b7 dev \u00b7 prod \u00b7 worker",
    "\u251c\u2500\u2500 frontend/",
    "\u2502   \u251c\u2500\u2500 app/",
    "\u2502   \u2502   \u251c\u2500\u2500 page.tsx             dashboard",
    "\u2502   \u2502   \u251c\u2500\u2500 login/               sign in and register",
    "\u2502   \u2502   \u251c\u2500\u2500 monitors/[id]/       detail and response-time chart",
    "\u2502   \u2502   \u251c\u2500\u2500 status/[handle]/     public status page",
    "\u2502   \u2502   \u2514\u2500\u2500 globals.css          design tokens and component styles",
    "\u2502   \u251c\u2500\u2500 lib/api.ts               typed fetch client, session handling",
    "\u2502   \u2514\u2500\u2500 Dockerfile               targets: deps \u00b7 dev \u00b7 builder \u00b7 prod",
    "\u251c\u2500\u2500 infra/",
    "\u2502   \u251c\u2500\u2500 architecture.drawio      the system diagram",
    "\u2502   \u2514\u2500\u2500 caddy/Caddyfile          production reverse proxy",
    "\u251c\u2500\u2500 docs/",
    "\u2502   \u251c\u2500\u2500 user-stories.md          25 stories, acceptance criteria, MoSCoW",
    "\u2502   \u2514\u2500\u2500 wireframes/              six screens as SVG",
    "\u251c\u2500\u2500 scripts/",
    "\u2502   \u251c\u2500\u2500 bootstrap-github.sh      one-shot repository setup",
    "\u2502   \u251c\u2500\u2500 stories.sh               the backlog as data",
    "\u2502   \u251c\u2500\u2500 seed-issues.sh           labels and issues",
    "\u2502   \u2514\u2500\u2500 setup-project-board.sh   project board and fields",
    "\u251c\u2500\u2500 docker-compose.yml",
    "\u251c\u2500\u2500 .env.example",
    "\u251c\u2500\u2500 .gitignore",
    "\u2514\u2500\u2500 README.md",
  ]),

  h2("5.2  The .gitignore"),
  p("Grouped by concern rather than dumped as one list, so a contributor can see why each entry exists. Secrets first, because that is the entry that matters."),
  ...code([
    "# ---------- secrets ----------",
    ".env",
    ".env.*",
    "!.env.example",
    "*.pem",
    "*.key",
    "",
    "# ---------- python ----------",
    "__pycache__/",
    "*.py[cod]",
    ".venv/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".coverage",
    "*.sqlite3",
    "*.db",
    "",
    "# ---------- node / next ----------",
    "node_modules/",
    ".next/",
    "out/",
    "dist/",
    "*.tsbuildinfo",
    "npm-debug.log*",
    "",
    "# ---------- docker ----------",
    "docker-compose.override.yml",
    "",
    "# ---------- editors / os ----------",
    ".vscode/",
    ".idea/",
    ".DS_Store",
    "Thumbs.db",
  ]),

  h2("5.3  Branching Strategy \u2014 GitHub Flow"),
  p("main is always deployable. There is no develop branch, no release branch, and no long-lived integration branch \u2014 with one developer those exist only to create merge conflicts with yourself."),
  ...code([
    "main  \u2500\u2500\u25cf\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u25cf\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u25cf\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u25cf\u2500\u2500\u25b6   always deployable, protected",
    "         \\      /              \\      /",
    "          \u25cf\u2500\u2500\u2500\u2500\u25cf                \u25cf\u2500\u2500\u2500\u2500\u25cf",
    "      feat/us-13-probe-worker   feat/us-16-status-page",
  ]),
  bullet([b("Branch off main for every unit of work. "), "One branch per issue."]),
  bullet([b("Name the branch after the story: "), "<type>/us-<id>-<slug> \u2014 for example feat/us-13-probe-worker, fix/us-08-uptime-excludes-timeouts, chore/us-25-ci-pipeline."]),
  bullet([b("Commit in Conventional Commits form, referencing the issue "), "\u2014 feat(engine): open an incident after two consecutive failures, followed by a blank line and Refs #13."]),
  bullet([b("Open a pull request early. "), "The description links the issue with Closes #13, so merging closes the story and moves the board card."]),
  bullet([b("CI must be green. "), "pytest, next build, and both docker builds run on every pull request. main is branch-protected against direct pushes and failing checks."]),
  bullet([b("Squash-merge, then delete the branch. "), "One story, one commit on main, readable history."]),
  p("Working a story end to end:"),
  ...code([
    "$ git switch main && git pull",
    "$ git switch -c feat/us-16-public-status-page",
    "",
    "  ... work, committing as you go ...",
    "",
    "$ git commit -m \"feat(status): serve a cached public status page",
    "",
    "  Refs #16\"",
    "$ git push -u origin feat/us-16-public-status-page",
    "$ gh pr create --fill --base main",
    "$ gh pr merge --squash --delete-branch",
  ]),
  img(asset("s02-branches.png"), 620, 354),
  caption("Screenshot 2 \u2014 The repository branch list showing main alongside the feature branch."),
  brk(),

  h2("5.4  Docker Setup for Local Development"),
  p("Both Dockerfiles are multi-stage with named targets, so the same file produces the development image, the production image, and \u2014 for the backend \u2014 the worker image. The target is selected by an environment variable rather than a second file."),
  h3("backend/Dockerfile"),
  ...code([
    "FROM python:3.12-slim AS base",
    "ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1",
    "WORKDIR /app",
    "RUN apt-get update && apt-get install -y --no-install-recommends curl \\",
    "    && rm -rf /var/lib/apt/lists/*",
    "COPY requirements.txt .",
    "RUN pip install --no-cache-dir -r requirements.txt",
    "COPY . .",
    "RUN useradd --create-home --uid 1001 vigil && chown -R vigil:vigil /app",
    "USER vigil",
    "EXPOSE 8000",
    "HEALTHCHECK --interval=20s --timeout=4s --start-period=25s --retries=5 \\",
    "    CMD curl -fsS http://localhost:8000/health || exit 1",
    "",
    "FROM base AS dev      # hot reload on save",
    "CMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\", \"--reload\"]",
    "",
    "FROM base AS prod     # multiple workers, no reloader",
    "CMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\", \"--workers\", \"2\"]",
    "",
    "FROM base AS worker   # probe loop, no HTTP server",
    "HEALTHCHECK NONE",
    "CMD [\"python\", \"worker.py\"]",
  ]),
  h3("frontend/Dockerfile"),
  ...code([
    "FROM node:22-alpine AS deps",
    "WORKDIR /app",
    "COPY package.json package-lock.json* ./",
    "RUN npm ci || npm install",
    "",
    "FROM node:22-alpine AS dev",
    "WORKDIR /app",
    "COPY --from=deps /app/node_modules ./node_modules",
    "COPY . .",
    "EXPOSE 3000",
    "CMD [\"npm\", \"run\", \"dev\"]",
    "",
    "FROM node:22-alpine AS builder",
    "WORKDIR /app",
    "COPY --from=deps /app/node_modules ./node_modules",
    "COPY . .",
    "RUN npm run build",
    "",
    "FROM node:22-alpine AS prod   # standalone output, no node_modules",
    "WORKDIR /app",
    "RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001",
    "COPY --from=builder /app/public ./public",
    "COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./",
    "COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static",
    "USER nextjs",
    "EXPOSE 3000",
    "CMD [\"node\", \"server.js\"]",
  ]),
  h3("docker-compose.yml \u2014 the five services"),
  p("Startup is health-gated: the API will not start until Postgres passes pg_isready, so first boot does not race. Both application services bind-mount their source, so code edits reload live without a rebuild."),
  table([1500, 2100, 6146],
    ["Service", "Image", "Role"],
    [["db", "postgres:16-alpine", "Persistence. Healthcheck on pg_isready. Data in the named volume vigil_pgdata."],
     ["cache", "redis:7-alpine", "Response cache. Persistence disabled \u2014 everything in it is derivable."],
     ["api", "built, target dev", "FastAPI on port 8000. Depends on db and cache being healthy."],
     ["worker", "built, target worker", "Probe loop. No exposed port. Same image as api."],
     ["web", "built, target dev", "Next.js on port 3000."]]),
  brk(),

  h2("5.5  Quick Start \u2014 Local Development"),
  p("This section is reproduced verbatim from README.md, where the assignment requires it to live."),
  h3("Prerequisites"),
  table([3400, 1600, 4746],
    ["Tool", "Version", "Check with"],
    [["Docker Desktop (or Engine + Compose v2)", "24+", "docker --version && docker compose version"],
     ["Git", "2.40+", "git --version"]]),
  p("Nothing else. Python and Node run inside the containers \u2014 neither is needed on the host."),
  h3("Run it"),
  ...code([
    "$ git clone https://github.com/vatsal-agra/vigil.git",
    "$ cd vigil",
    "$ cp .env.example .env        # optional; compose has working defaults",
    "$ docker compose up --build",
  ]),
  p("The first build takes two to four minutes. Subsequent starts take a few seconds. When it is ready:"),
  table([3400, 6346],
    ["What", "Where"],
    [["Dashboard", "http://localhost:3000"],
     ["Public status page", "http://localhost:3000/status/demo"],
     ["API documentation (Swagger)", "http://localhost:8000/docs"],
     ["Health check", "http://localhost:8000/health"]]),
  p("A demo account is seeded automatically on an empty database:"),
  ...code([
    "email:    demo@vigil.dev",
    "password: vigil-demo-2026",
  ]),
  p("It arrives with four monitors and twenty-four hours of backfilled check history, so the dashboard, the chart and the incident feed are all populated the moment you sign in."),
  h3("Everyday commands"),
  ...code([
    "$ docker compose up                    # start, after the first build",
    "$ docker compose up --build            # rebuild after a Dockerfile or dependency change",
    "$ docker compose down                  # stop, keep the database",
    "$ docker compose down -v               # stop and wipe the database (re-seeds next start)",
    "$ docker compose logs -f api worker    # follow specific services",
    "$ docker compose restart worker        # restart one service",
    "",
    "$ docker compose exec api pytest -q                    # backend tests",
    "$ docker compose exec db psql -U vigil -d vigil        # SQL shell",
    "$ docker compose exec cache redis-cli KEYS 'monitors*' # inspect the cache",
  ]),
  h3("Production images"),
  ...code([
    "$ BACKEND_TARGET=prod FRONTEND_TARGET=prod docker compose up --build",
  ]),
  h3("Troubleshooting"),
  table([2900, 2600, 4246],
    ["Symptom", "Cause", "Fix"],
    [["port is already allocated", "Something else holds 3000, 5432, 6379 or 8000", "lsof -i :5432, stop it, or remap the left-hand side in docker-compose.yml"],
     ["Dashboard shows \u201cCould not reach the API\u201d", "NEXT_PUBLIC_API_URL is a container hostname", "It must be browser-reachable: http://localhost:8000, not http://api:8000"],
     ["relation \u201cmonitors\u201d does not exist", "Volume from an older schema", "docker compose down -v && docker compose up"],
     ["Worker restarts in a loop", "Postgres was not ready", "Handled by wait_for_db; if it persists check docker compose logs db"],
     ["No demo data", "The database was not empty", "docker compose down -v, then start again"]]),
  brk(),

  h2("5.6  Local Development Tools"),
  p("Reproduced from README.md. Each entry states why it is in this project rather than simply that it exists."),
  table([2500, 1300, 5946],
    ["Tool", "Version", "Why it is in this project"],
    [["Docker Desktop", "24+", "Runs all five services. The only host dependency."],
     ["Docker Compose v2", "bundled", "Service graph, health-gated startup ordering, named volumes."],
     ["VS Code", "latest", "Editor. Extensions: Python, Pylance, Ruff, ESLint, Prettier, Docker, GitLens."],
     ["Dev Containers", "optional", "Attaches VS Code directly to the api container for a debugger against the real environment."],
     ["Git", "2.40+", "Version control. GitHub Flow, one branch per issue."],
     ["GitHub CLI (gh)", "2.x", "Creates issues, pull requests and the project board from the terminal. The repository scripts depend on it."],
     ["pytest", "8.3", "Backend tests. Runs in CI and inside the container."],
     ["Ruff", "latest", "Python lint and format \u2014 ruff check backend && ruff format backend."],
     ["TypeScript", "5.7", "Compile-time contract between lib/api.ts and every component. next build fails on a type error, so drift cannot ship."],
     ["Swagger UI", "via FastAPI", "Auto-generated from the Pydantic schemas at /docs. Used to exercise endpoints before the UI exists."],
     ["psql / redis-cli", "in-container", "Inspect database and cache state directly during debugging."],
     ["draw.io (diagrams.net)", "web", "The architecture diagram. Source committed as .drawio, so it stays diffable."],
     ["Figma (free tier)", "web", "The six wireframes. SVG sources import as editable frames."],
     ["GitHub Actions", "hosted", "CI on every pull request: pytest, next build, and both docker builds."]]),
  brk(),
];

// ================================================================ 6. PROOF

const proofShots = [
  [asset("s05-docker-build.png"), "Screenshot 5 \u2014 Terminal: docker compose up --build completes successfully, all five containers started."],
  [asset("s06-compose-ps.png"), "Screenshot 6 \u2014 Terminal: docker compose ps showing all five containers up, with db, cache and api healthy."],
  [asset("s07-worker-logs.png"), "Screenshot 7 \u2014 Terminal: the probe worker completing a check cycle."],
  [asset("s08-dashboard.png"), "Screenshot 8 \u2014 Browser: the application running on http://localhost:3000."],
  [asset("s09-detail.png"), "Screenshot 9 \u2014 Browser: monitor detail with the twenty-four-hour response-time chart."],
  [asset("s10-status-page.png"), "Screenshot 10 \u2014 Browser: the public status page, requiring no authentication."],
];

const proof = [
  h1("Proof That Everything Works", "6."),
  p("The assignment requires screenshots of a successful Docker build, the application running in a browser on localhost, and the GitHub repository page showing branches and README. Screenshots 1 and 2 appear in Sections 1 and 5 respectively; screenshots 3 and 4 in Section 2. The remainder follow."),
  note("Each screenshot below was captured from the live environment: the terminal running the "
     + "stack, and the application in the browser on localhost. docs/screenshots/README.md in "
     + "the repository documents how each capture was produced."),
];
proofShots.forEach(([path, cap]) => {
  proof.push(img(path, 620, 354));
  proof.push(caption(cap));
});
proof.push(h2("Verification summary"));
proof.push(table([3200, 6546],
  ["Requirement", "Evidence"],
  [["Proper folder structure", "Section 5.1 and Screenshot 1"],
   ["A good .gitignore", "Section 5.2"],
   ["Branching strategy explained in README", "Section 5.3"],
   ["At least one feature branch, shown in a screenshot", "Screenshot 2 \u2014 feat/us-16-public-status-page"],
   ["Dockerfile(s) in the repository", "Section 5.4 \u2014 backend and frontend, multi-stage"],
   ["Quick Start section in README", "Section 5.5"],
   ["Local development tools documented in README", "Section 5.6"],
   ["Terminal showing successful build and compose up", "Screenshots 5, 6 and 7"],
   ["App running in the browser on localhost", "Screenshots 8, 9 and 10"],
   ["GitHub repo page showing branches and README", "Screenshots 1 and 2"]]));

// ================================================================ DOCUMENT

const portraitProps = {
  page: {
    size: { width: 11906, height: 16838 },
    margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 },
  },
};
const landscapeProps = {
  page: {
    size: { width: 11906, height: 16838, orientation: PageOrientation.LANDSCAPE },
    margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 },
  },
};

const doc = new Document({
  creator: "Vatsal Agrawal",
  title: "Vigil — Digital Assignment 1",
  description: "Software Engineering Digital Assignment 1 / Review 1",
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 21, color: INK } },
    },
  },
  sections: [
    { properties: portraitProps, children: [...title, ...contents, ...vision, ...userStories, ...moscow] },
    { properties: landscapeProps, children: architecture },
    { properties: portraitProps, children: [...devsetup, ...proof] },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(path.join(ROOT, "Vigil_Digital_Assignment_1.docx"), buf);
  console.log("written:", buf.length, "bytes");
});
