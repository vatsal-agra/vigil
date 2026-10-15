#!/usr/bin/env python3
"""Writes the Review 3 report diagrams (DFD and UML) as editable draw.io files.

  python scripts/make_report_diagrams.py

Outputs to docs/design/diagrams/ beside the Review 2 diagrams:
  05-dfd-level-0.drawio        context diagram
  06-dfd-level-1.drawio        processes, data stores and flows
  07-use-case.drawio           UML use case diagram
  08-class.drawio              UML class diagram (domain + modules)
  09-sequence-outage.drawio    UML sequence: worker detects an outage
  10-sequence-dashboard.drawio UML sequence: dashboard read through the cache

PNG exports: python scripts/export_diagrams.py
"""
import html
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from make_design_diagrams import (  # noqa: E402
    BE, BE_BG, BODY, CACHE, CACHE_BG, DATA, DATA_BG, FE, FE_BG, INK, MUTED, OUT, SVC, SVC_BG,
    WK, WK_BG, Diagram,
)

TXT = f"fontColor={INK};fontSize=12;"
FLOW = (f"html=1;endArrow=block;endFill=1;strokeColor={BODY};strokeWidth=1.4;fontSize=10.5;"
        f"fontColor={BODY};labelBackgroundColor=#FFFFFF;rounded=0;")
FLOW_O = FLOW.replace("endArrow=block;endFill=1", "endArrow=open;endFill=0")


class D(Diagram):
    def raw(self, xml):
        self.cells.append(xml)

    def arrow(self, cid, x1, y1, x2, y2, label="", dashed=False, style=None, label_pos=0):
        st = style or (FLOW_O if dashed else FLOW)
        if dashed:
            st += "dashed=1;"
        self.raw(f'<mxCell id="{cid}" value="{html.escape(label, quote=True)}" style="{st}" edge="1" '
                 f'parent="1"><mxGeometry x="{label_pos}" relative="1" as="geometry">'
                 f'<mxPoint x="{x1}" y="{y1}" as="sourcePoint"/><mxPoint x="{x2}" y="{y2}" '
                 f'as="targetPoint"/></mxGeometry></mxCell>')

    def edge_label(self, edge_id, text, pos):
        self.raw(f'<mxCell id="{edge_id}-l{pos}" value="{html.escape(text)}" style="edgeLabel;html=1;'
                 f'align=center;verticalAlign=middle;resizable=0;points=[];fontSize=11;fontStyle=1;'
                 f'fontColor={INK};labelBackgroundColor=#FFFFFF;" vertex="1" connectable="0" '
                 f'parent="{edge_id}"><mxGeometry x="{pos}" relative="1" as="geometry">'
                 f'<mxPoint as="offset"/></mxGeometry></mxCell>')


def process(d, cid, num, name, x, y, size=150, colour=BE, bg=BE_BG):
    d.v(cid, f"<span style='font-size:10px;color:{MUTED}'>{num}</span><br><b>{name}</b>", x, y, size, size,
        f"ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor={bg};strokeColor={colour};strokeWidth=2;{TXT}")


def entity(d, cid, name, x, y, w=170, h=70):
    d.v(cid, f"<b>{name}</b>", x, y, w, h,
        f"rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={INK};strokeWidth=2;{TXT}")


def store(d, cid, ref, name, x, y, w=210, h=44, colour=DATA, bg=DATA_BG):
    d.v(cid, f"<b>{ref}</b>&nbsp;&nbsp;|&nbsp;&nbsp;{name}", x, y, w, h,
        f"shape=partialRectangle;whiteSpace=wrap;html=1;left=1;right=0;top=1;bottom=1;"
        f"fillColor={bg};strokeColor={colour};strokeWidth=2;align=left;spacingLeft=10;{TXT}")


def legend(d, x, y, rows):
    d.v("legend", "<br>".join(rows), x, y, 330, 22 + 18 * len(rows),
        f"rounded=1;whiteSpace=wrap;html=1;fillColor=#F4F6F8;strokeColor=#D5DAE1;align=left;"
        f"verticalAlign=top;spacingLeft=10;spacingTop=6;fontSize=11;fontColor={BODY};")


# ------------------------------------------------------------------ 05 DFD level 0

def dfd0():
    d = D("dfd0", "Vigil - DFD Level 0 (Context)", 1300, 720)
    d.title("Vigil - Data Flow Diagram, Level 0 (Context)",
            "The whole system as one process, the three external entities it exchanges data with, "
            "and every flow across the boundary. Yourdon-DeMarco notation.")
    process(d, "sys", "0", "Vigil<br>Monitoring<br>System", 545, 250, size=210)
    entity(d, "user", "Registered user<br><span style='font-weight:normal;font-size:10px'>(developer, operator)</span>", 60, 130)
    entity(d, "visitor", "Public visitor", 60, 500)
    entity(d, "target", "Monitored endpoint<br><span style='font-weight:normal;font-size:10px'>(any HTTP/HTTPS URL)</span>", 1060, 320)

    d.e("f1", "user", "sys", "credentials, monitor definitions,<br>pause / delete / publish, acknowledgements",
        FLOW + "exitX=1;exitY=0.3;entryX=0.3;entryY=0.05;", points=[(500, 151)])
    d.e("f2", "sys", "user", "session token, dashboard (status, uptime, latency),<br>response-time history, incident feed + summaries",
        FLOW + "exitX=0;exitY=0.5;entryX=0.6;entryY=1;", points=[(195, 355)])
    d.e("f3", "visitor", "sys", "status page request (handle)", FLOW + "exitX=1;exitY=0.25;entryX=0.1;entryY=0.8;")
    d.e("f4", "sys", "visitor", "public service status, overall banner", FLOW + "exitX=0.25;exitY=0.95;entryX=1;entryY=0.8;")
    d.e("f5", "sys", "target", "HTTP probe request (method, URL)", FLOW + "exitX=0.95;exitY=0.3;entryX=0;entryY=0.2;")
    d.e("f6", "target", "sys", "status code, latency, or error", FLOW + "exitX=0;exitY=0.85;entryX=0.95;entryY=0.7;")
    legend(d, 60, 630, ["Circle = process  ·  Rectangle = external entity  ·  Arrow = data flow"])
    d.write(OUT / "05-dfd-level-0.drawio")


# ------------------------------------------------------------------ 06 DFD level 1

def dfd1():
    d = D("dfd1", "Vigil - DFD Level 1", 1560, 1060)
    d.title("Vigil - Data Flow Diagram, Level 1",
            "Process 0 decomposed into six processes and five data stores. D1-D4 are PostgreSQL tables; "
            "D5 is the Redis response cache.")
    entity(d, "user", "Registered user", 40, 380, w=150, h=80)
    entity(d, "visitor", "Public visitor", 40, 900, w=150, h=70)
    entity(d, "target", "Monitored endpoint", 1380, 250, w=150, h=80)

    process(d, "p1", "1.0", "Authenticate<br>user", 300, 110, size=130)
    process(d, "p2", "2.0", "Manage<br>monitors", 300, 330, size=130)
    process(d, "p5", "5.0", "Report status<br>and incidents", 300, 560, size=130)
    process(d, "p6", "6.0", "Publish<br>status page", 300, 850, size=130)
    process(d, "p3", "3.0", "Probe due<br>monitors", 1060, 220, size=130, colour=WK, bg=WK_BG)
    process(d, "p4", "4.0", "Detect and<br>resolve incidents", 1060, 560, size=130, colour=WK, bg=WK_BG)

    store(d, "d1", "D1", "Users", 650, 130)
    store(d, "d2", "D2", "Monitors", 650, 350)
    store(d, "d3", "D3", "Checks", 650, 520)
    store(d, "d4", "D4", "Incidents", 650, 690)
    store(d, "d5", "D5", "Response cache", 650, 880, colour=CACHE, bg=CACHE_BG)

    f = FLOW
    d.e("a1", "user", "p1", "credentials", f + "exitX=0.5;exitY=0;entryX=0;entryY=0.5;")
    d.e("a2", "p1", "user", "JWT token", f + "exitX=0.15;exitY=0.85;entryX=0.75;entryY=0;")
    d.e("a3", "p1", "d1", "new user / lookup", f + "dashed=0;")
    d.e("a4", "user", "p2", "monitor<br>commands", f + "exitX=1;exitY=0.3;entryX=0;entryY=0.5;")
    d.e("a5", "p2", "d2", "monitor rows", f)
    d.e("a6", "p2", "d5", "invalidate", f + "dashed=1;exitX=0.85;exitY=0.85;entryX=0.1;entryY=0;")
    d.e("a7", "d2", "p3", "active, due monitors", f)
    d.e("a8", "p3", "target", "HTTP request", f + "exitX=1;exitY=0.3;entryX=0;entryY=0.3;")
    d.e("a9", "target", "p3", "status, latency, error", f + "exitX=0;exitY=0.8;entryX=1;entryY=0.7;")
    d.e("a10", "p3", "d3", "check result", f + "exitX=0.2;exitY=0.9;entryX=1;entryY=0.3;")
    d.e("a11", "p3", "p4", "check result", f)
    d.e("a12", "p4", "d4", "open / resolve incident<br>+ summary", f + "exitX=0.1;exitY=0.8;entryX=1;entryY=0.5;")
    d.e("a13", "p4", "d2", "current_status,<br>failure count", f + "exitX=0;exitY=0.3;entryX=1;entryY=0.7;")
    d.e("a14", "p4", "d5", "invalidate", f + "dashed=1;exitX=0.5;exitY=1;entryX=1;entryY=0.5;")
    d.e("a15", "d2", "p5", "monitors", f + "exitX=0;exitY=0.8;entryX=1;entryY=0.2;")
    d.e("a16", "d3", "p5", "24 h rollup", f + "exitX=0;exitY=0.5;entryX=1;entryY=0.45;")
    d.e("a17", "d4", "p5", "incident feed", f + "exitX=0;exitY=0.5;entryX=1;entryY=0.7;")
    d.e("a18", "p5", "user", "dashboard, history,<br>incidents", f + "exitX=0;exitY=0.5;entryX=0.6;entryY=1;")
    d.e("a19", "p5", "d5", "cached reads", f + "dashed=1;exitX=0.8;exitY=0.95;entryX=0;entryY=0.2;")
    d.e("a20", "visitor", "p6", "handle", f + "exitX=1;exitY=0.4;entryX=0;entryY=0.5;")
    d.e("a21", "p6", "visitor", "public status", f + "exitX=0.3;exitY=0.97;entryX=1;entryY=0.85;")
    d.e("a22", "d5", "p6", "cached page (20 s)", f + "exitX=0;exitY=0.6;entryX=1;entryY=0.6;")
    d.e("a23", "d1", "p6", "handle -> owner", f + "edgeStyle=orthogonalEdgeStyle;exitX=0;exitY=0.5;entryX=0.95;entryY=0.3;", points=[(612, 152), (612, 889)])
    legend(d, 1060, 900, ["Green = request-driven (API container)",
                          "Purple = time-driven (worker container)",
                          "Dashed = cache write / invalidation"])
    d.write(OUT / "06-dfd-level-1.drawio")


# ------------------------------------------------------------------ 07 use case

def use_case():
    d = D("usecase", "Vigil - Use Case Diagram", 1400, 960)
    d.title("Vigil - UML Use Case Diagram",
            "Actors on the outside, the system boundary in the middle. Story IDs refer to docs/user-stories.md.")
    d.v("boundary", "Vigil", 300, 90, 800, 840,
        f"rounded=0;whiteSpace=wrap;html=1;fillColor=#FAFBFC;strokeColor={INK};strokeWidth=2;"
        f"verticalAlign=top;align=center;fontSize=15;fontStyle=1;fontColor={INK};")
    actor = "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;strokeWidth=2;fontSize=12;fontStyle=1;"
    d.v("dev", "Developer", 120, 330, 40, 80, actor + f"strokeColor={FE};fontColor={FE};")
    d.v("vis", "Public visitor", 1230, 800, 40, 80, actor + f"strokeColor={INK};fontColor={INK};")
    d.v("clock", "Scheduler<br>(every 30 s)", 1230, 330, 40, 80, actor + f"strokeColor={WK};fontColor={WK};")
    d.v("svc", "Monitored<br>service", 1230, 110, 40, 80, actor + f"strokeColor={BODY};fontColor={BODY};")

    uc = "ellipse;whiteSpace=wrap;html=1;fontSize=11.5;strokeWidth=1.5;"
    dev_ucs = [("u1", "Register / sign in<br><i>US-01..03</i>", 340, 130), ("u2", "Add monitor<br><i>US-06, US-07</i>", 340, 215),
               ("u3", "View dashboard<br><i>US-05, US-08, US-09</i>", 340, 300), ("u4", "View response-time<br>history <i>US-10, 11</i>", 340, 385),
               ("u5", "Pause / resume<br>monitor <i>US-12</i>", 340, 470), ("u6", "Delete monitor<br><i>US-12</i>", 340, 555),
               ("u7", "View incident feed<br><i>US-15</i>", 340, 640), ("u8", "Acknowledge<br>incident <i>US-18</i>", 340, 725),
               ("u9", "Publish monitor to<br>status page <i>US-17</i>", 340, 810)]
    for cid, label, x, y in dev_ucs:
        d.v(cid, label, x, y, 200, 66, uc + f"fillColor={FE_BG};strokeColor={FE};fontColor={INK};")
        d.e(f"e-{cid}", "dev", cid, "", f"html=1;endArrow=none;strokeColor={FE};strokeWidth=1.2;")
    d.v("u6c", "Confirm deletion", 620, 555, 170, 56, uc + "fillColor=#FFFFFF;strokeColor=#79818D;fontColor=#3F4650;")
    d.e("inc1", "u6", "u6c", "«include»", "html=1;endArrow=open;endFill=0;dashed=1;strokeColor=#79818D;fontSize=10;fontColor=#5A626D;")

    d.v("u10", "View public status<br>page <i>US-16</i>", 860, 830, 210, 66, uc + "fillColor=#F4F6F8;strokeColor=#12161C;fontColor=#12161C;")
    d.e("e-vis", "vis", "u10", "", "html=1;endArrow=none;strokeColor=#12161C;strokeWidth=1.2;")

    sys_ucs = [("s1", "Probe due monitors<br><i>US-13</i>", 860, 230), ("s2", "Record check", 860, 350),
               ("s3", "Open incident<br><i>after 2 failures</i>", 860, 470), ("s4", "Resolve incident<br><i>US-14</i>", 860, 590),
               ("s5", "Write plain-English<br>summary <i>US-21</i>", 860, 710)]
    for cid, label, x, y in sys_ucs:
        d.v(cid, label, x, y, 210, 66, uc + f"fillColor={WK_BG};strokeColor={WK};fontColor={INK};")
    d.e("e-clock", "clock", "s1", "", f"html=1;endArrow=none;strokeColor={WK};strokeWidth=1.2;")
    d.e("e-svc", "svc", "s1", "", f"html=1;endArrow=none;strokeColor={BODY};strokeWidth=1.2;")
    dep = "html=1;endArrow=open;endFill=0;dashed=1;strokeColor=#79818D;fontSize=10;fontColor=#5A626D;"
    d.e("i-s2", "s1", "s2", "«include»", dep)
    d.e("x-s3", "s3", "s1", "«extend»", dep + "edgeStyle=orthogonalEdgeStyle;exitX=0;exitY=0.5;entryX=0;entryY=0.6;", points=[(830, 503), (830, 270)])
    d.e("x-s4", "s4", "s1", "«extend»", dep + "edgeStyle=orthogonalEdgeStyle;exitX=0;exitY=0.5;entryX=0;entryY=0.35;", points=[(800, 623), (800, 253)])
    d.e("i-s5", "s4", "s5", "«include»", dep)
    d.write(OUT / "07-use-case.drawio")


# ------------------------------------------------------------------ 08 class

def uml_class(d, cid, name, attrs, methods, x, y, w, colour, bg, stereo=""):
    rows = len(attrs) + len(methods)
    h = 30 + 20 * rows + (8 if methods else 0) + (14 if stereo else 0)
    title = (f"<span style='font-weight:normal;font-size:10px'>«{stereo}»</span><br>" if stereo else "") + name
    d.v(cid, title, x, y, w, h,
        f"swimlane;fontStyle=1;align=center;verticalAlign=top;childLayout=stackLayout;horizontal=1;"
        f"startSize={30 + (14 if stereo else 0)};horizontalStack=0;resizeParent=1;resizeParentMax=0;"
        f"resizeLast=0;collapsible=0;marginBottom=0;html=1;fillColor={bg};strokeColor={colour};"
        f"fontColor={INK};fontSize=13;swimlaneFillColor=#FFFFFF;")
    yy = 30 + (14 if stereo else 0)
    row = ("text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=8;"
           "html=1;fontSize=11;fontFamily=Consolas;fontColor=#24303F;")
    for i, a in enumerate(attrs):
        d.v(f"{cid}-a{i}", html.escape(a), 0, yy, w, 20, row, parent=cid)
        yy += 20
    if methods:
        d.v(f"{cid}-sep", "", 0, yy, w, 8, "line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;"
            "spacingTop=-1;spacingLeft=3;spacingRight=3;rotatable=0;labelPosition=right;points=[];"
            f"portConstraint=eastwest;strokeColor={colour};", parent=cid)
        yy += 8
        for i, m in enumerate(methods):
            d.v(f"{cid}-m{i}", html.escape(m), 0, yy, w, 20, row, parent=cid)
            yy += 20


def class_diagram():
    d = D("class", "Vigil - Class Diagram", 1500, 1000)
    d.title("Vigil - UML Class Diagram",
            "Top: persistent domain classes (app/models.py) and their associations. "
            "Bottom: the modules that operate on them, shown as stereotyped classes.")
    uml_class(d, "User", "User", ["+ id: int {PK}", "+ email: str {unique}", "+ handle: str {unique}",
                                  "- password_hash: str", "+ created_at: datetime"], [], 40, 110, 250, FE, FE_BG, "entity")
    uml_class(d, "Monitor", "Monitor", ["+ id: int {PK}", "+ owner_id: int {FK}", "+ name: str", "+ slug: str",
                                        "+ url: str", "+ method: str = 'GET'", "+ expected_status: int = 200",
                                        "+ interval_seconds: int = 60", "+ is_active: bool", "+ is_public: bool",
                                        "+ current_status: Status", "+ consecutive_failures: int",
                                        "+ last_checked_at: datetime?"], [], 440, 110, 300, BE, BE_BG, "entity")
    uml_class(d, "Check", "Check", ["+ id: int {PK}", "+ monitor_id: int {FK}", "+ checked_at: datetime",
                                    "+ status_code: int?", "+ latency_ms: float?", "+ ok: bool", "+ error: str?"],
              [], 900, 90, 260, DATA, DATA_BG, "entity")
    uml_class(d, "Incident", "Incident", ["+ id: int {PK}", "+ monitor_id: int {FK}", "+ started_at: datetime",
                                          "+ resolved_at: datetime?", "+ cause: str", "+ summary: str?",
                                          "+ acknowledged: bool"], [], 900, 330, 260, CACHE, CACHE_BG, "entity")
    uml_class(d, "Status", "Status", ["pending", "up", "degraded", "down"], [], 1230, 110, 200, BODY, "#F4F6F8",
              "enumeration")

    assoc = f"html=1;endArrow=none;strokeColor={INK};strokeWidth=1.5;fontSize=11;"
    comp = f"html=1;endArrow=none;startArrow=diamondThin;startFill=1;startSize=16;strokeColor={INK};strokeWidth=1.5;"
    d.e("r-owns", "User", "Monitor", "owns", assoc + "exitX=1;exitY=0.3;entryX=0;entryY=0.15;")
    d.edge_label("r-owns", "1", -0.8)
    d.edge_label("r-owns", "0..*", 0.75)
    d.e("r-checks", "Monitor", "Check", "records", comp + "exitX=1;exitY=0.15;entryX=0;entryY=0.3;")
    d.edge_label("r-checks", "1", -0.8)
    d.edge_label("r-checks", "0..*", 0.75)
    d.e("r-inc", "Monitor", "Incident", "opens", comp + "exitX=1;exitY=0.6;entryX=0;entryY=0.3;")
    d.edge_label("r-inc", "1", -0.8)
    d.edge_label("r-inc", "0..*", 0.75)
    d.e("r-status", "Monitor", "Status", "", f"html=1;endArrow=open;endFill=0;dashed=1;strokeColor={MUTED};"
        "exitX=0.85;exitY=0;entryX=0.5;entryY=0;", points=[(695, 85), (1330, 85)])

    uml_class(d, "probe", "probe", [], ["+ due_monitors(db): Monitor[]", "+ probe_once(client, m): Check",
                                        "+ apply_result(db, m, check)", "+ run_cycle(db, client?): int"],
              40, 640, 330, WK, WK_BG, "module")
    uml_class(d, "services", "services", [], ["+ rollup(db, id, hours=24): dict", "+ open_incident(db, id): Incident?",
                                              "+ unique_slug(db, owner, name): str", "+ unique_handle(db, email): str"],
              420, 640, 340, SVC, SVC_BG, "module")
    uml_class(d, "cache", "cache", [], ["+ get_json(key): Any?", "+ set_json(key, value, ttl)",
                                        "+ invalidate(pattern)"], 810, 640, 260, CACHE, CACHE_BG, "module")
    uml_class(d, "security", "security", [], ["+ hash_password(pw): str", "+ verify_password(pw, h): bool",
                                              "+ create_token(user_id): str", "+ current_user(creds, db): User"],
              1110, 640, 350, FE, FE_BG, "module")
    uml_class(d, "Settings", "Settings", ["+ failure_threshold: int = 2", "+ probe_timeout_seconds = 8.0",
                                          "+ probe_interval_seconds = 30", "+ jwt_ttl_minutes = 1440"],
              [], 420, 860, 340, BODY, "#F4F6F8", "config")

    use = f"html=1;endArrow=open;endFill=0;dashed=1;strokeColor={MUTED};fontSize=10;fontColor={MUTED};"
    d.e("d1", "probe", "services", "«use»", use)
    d.e("d2", "probe", "cache", "«use»", use + "exitX=0.7;exitY=1;entryX=0.4;entryY=1;", points=[(271, 820), (914, 820)])
    d.e("d3", "probe", "Settings", "«use»", use + "exitX=0.5;exitY=1;entryX=0;entryY=0.5;", points=[(205, 920)])
    d.e("d4", "probe", "Monitor", "«create Check, Incident»", use + "exitX=0.5;exitY=0;entryX=0.2;entryY=1;")
    d.e("d5", "services", "Monitor", "«query»", use + "exitX=0.5;exitY=0;entryX=0.6;entryY=1;")
    d.e("d6", "security", "User", "«query»", use + "exitX=0.3;exitY=0;entryX=0.5;entryY=1;", points=[(1215, 600), (165, 600)])
    d.write(OUT / "08-class.drawio")


# ------------------------------------------------------------------ sequence helpers

def lifeline(d, cid, name, x, height, colour, bg, w=150):
    d.v(cid, name, x, 100, w, height,
        f"shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=0;"
        f"collapsible=0;recursiveResize=0;outlineConnect=0;size=46;fillColor={bg};strokeColor={colour};"
        f"fontColor={INK};fontSize=11.5;fontStyle=1;")
    return x + w / 2


def frame(d, cid, kind, guard, x, y, w, h):
    d.v(cid, kind, x, y, w, h, f"shape=umlFrame;whiteSpace=wrap;html=1;width=64;height=22;"
        f"fillColor=none;strokeColor={MUTED};fontSize=11;fontStyle=1;fontColor={INK};")
    d.v(f"{cid}-g", f"[{guard}]", x + 70, y + 2, 360, 20,
        f"text;html=1;align=left;verticalAlign=middle;fontSize=11;fontColor={BODY};fontStyle=2;")


def divider(d, cid, guard, x, y, w):
    d.raw(f'<mxCell id="{cid}" style="html=1;endArrow=none;dashed=1;strokeColor={MUTED};" edge="1" parent="1">'
          f'<mxGeometry relative="1" as="geometry"><mxPoint x="{x}" y="{y}" as="sourcePoint"/>'
          f'<mxPoint x="{x + w}" y="{y}" as="targetPoint"/></mxGeometry></mxCell>')
    d.v(f"{cid}-g", f"[{guard}]", x + 8, y + 2, 300, 20,
        f"text;html=1;align=left;verticalAlign=middle;fontSize=11;fontColor={BODY};fontStyle=2;")


def activation(d, cid, cx, y1, y2, colour):
    d.v(cid, "", cx - 6, y1, 12, y2 - y1, f"rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={colour};")


def selfcall(d, cid, cx, y, label):
    d.raw(f'<mxCell id="{cid}" value="{html.escape(label)}" style="{FLOW}align=left;spacingLeft=6;" edge="1" parent="1">'
          f'<mxGeometry relative="1" as="geometry"><mxPoint x="{cx + 6}" y="{y}" as="sourcePoint"/>'
          f'<mxPoint x="{cx + 6}" y="{y + 26}" as="targetPoint"/><Array as="points">'
          f'<mxPoint x="{cx + 46}" y="{y}"/><mxPoint x="{cx + 46}" y="{y + 26}"/></Array></mxGeometry></mxCell>')
    d.v(f"{cid}-t", html.escape(label), cx + 52, y - 4, 280, 34,
        f"text;html=1;align=left;verticalAlign=middle;fontSize=10.5;fontColor={BODY};whiteSpace=wrap;")


# ------------------------------------------------------------------ 09 sequence: outage

def seq_outage():
    d = D("seq-outage", "Vigil - Sequence: Outage Detection", 1360, 880)
    d.title("Vigil - UML Sequence Diagram: the worker detects an outage",
            "One probe cycle (app/probe.py run_cycle). The API is never involved: the worker reaches it "
            "only through the database and by invalidating cache keys.")
    H = 740
    w = lifeline(d, "L-worker", "worker.py<br><span style='font-weight:normal'>main loop</span>", 40, H, WK, WK_BG)
    p = lifeline(d, "L-probe", "probe.py", 260, H, WK, WK_BG)
    db = lifeline(d, "L-db", "PostgreSQL", 500, H, DATA, DATA_BG)
    t = lifeline(d, "L-target", "Monitored<br>endpoint", 740, H, BODY, "#F4F6F8")
    r = lifeline(d, "L-redis", "Redis", 980, H, CACHE, CACHE_BG)

    activation(d, "act-w", w, 170, 815, WK)
    activation(d, "act-p", p, 185, 795, WK)
    d.arrow("m1", w + 6, 190, p - 6, 190, "1: run_cycle(db)")
    d.arrow("m2", p + 6, 225, db - 6, 225, "2: SELECT active monitors")
    d.arrow("m3", db - 6, 255, p + 6, 255, "3: due monitors", dashed=True)
    frame(d, "f-loop", "loop", "for each due monitor", 175, 280, 1000, 495)
    d.arrow("m4", p + 6, 320, t - 6, 320, "4: probe_once(): GET url  (timeout 8 s)")
    d.arrow("m5", t - 6, 355, p + 6, 355, "5: 503 Service Unavailable", dashed=True)
    selfcall(d, "m6", p, 385, "6: apply_result(): consecutive_failures += 1")
    frame(d, "f-alt", "alt", "consecutive_failures >= 2 and no open incident", 205, 440, 950, 200)
    d.arrow("m7", p + 6, 485, db - 6, 485, "7: UPDATE monitor SET status = 'down'")
    d.arrow("m8", p + 6, 520, db - 6, 520, "8: INSERT incident (cause)")
    divider(d, "div1", "first failure: status unchanged (flap guard)", 205, 560, 950)
    d.arrow("m9", p + 6, 600, db - 6, 600, "9: UPDATE monitor (counter only)")
    d.arrow("m10", p + 6, 680, db - 6, 680, "10: INSERT check; COMMIT")
    d.arrow("m11", p + 6, 725, r - 6, 725, "11: invalidate monitors:list:{owner}, status:public:*")
    d.arrow("m12", p - 6, 805, w + 6, 805, "12: number checked", dashed=True)
    d.write(OUT / "09-sequence-outage.drawio")


# ------------------------------------------------------------------ 10 sequence: dashboard read

def seq_dashboard():
    d = D("seq-dash", "Vigil - Sequence: Dashboard Read", 1460, 900)
    d.title("Vigil - UML Sequence Diagram: dashboard read through the cache",
            "GET /api/monitors, polled every 15 s. Cache-aside: Redis first, PostgreSQL only on a miss.")
    H = 760
    b = lifeline(d, "L-b", "Browser<br><span style='font-weight:normal'>app/page.tsx</span>", 40, H, FE, FE_BG)
    a = lifeline(d, "L-a", "lib/api.ts", 260, H, FE, FE_BG)
    rt = lifeline(d, "L-r", "routers/<br>monitors.py", 480, H, BE, BE_BG)
    s = lifeline(d, "L-s", "security.py", 700, H, SVC, SVC_BG)
    rd = lifeline(d, "L-rd", "Redis", 920, H, CACHE, CACHE_BG)
    db = lifeline(d, "L-db", "PostgreSQL", 1140, H, DATA, DATA_BG)

    activation(d, "act-a", a, 180, 820, FE)
    activation(d, "act-r", rt, 210, 790, BE)
    d.arrow("n1", b + 6, 185, a - 6, 185, "1: api('/api/monitors')")
    d.arrow("n2", a + 6, 215, rt - 6, 215, "2: GET /api/monitors  Bearer JWT")
    d.arrow("n3", rt + 6, 250, s - 6, 250, "3: current_user(token)")
    d.arrow("n4", s + 6, 280, db - 6, 280, "4: SELECT user by id")
    d.arrow("n5", s - 6, 310, rt + 6, 310, "5: User", dashed=True)
    d.arrow("n6", rt + 6, 345, rd - 6, 345, "6: GET monitors:list:{user_id}")
    frame(d, "f-alt", "alt", "cache hit", 390, 375, 1010, 380)
    d.arrow("n7", rd - 6, 420, rt + 6, 420, "7: cached JSON", dashed=True)
    divider(d, "div", "cache miss (or Redis down: treated as a miss)", 390, 470, 1010)
    d.arrow("n8", rt + 6, 515, db - 6, 515, "8: SELECT monitors WHERE owner_id")
    selfcall(d, "n9", rt, 545, "9: rollup() per monitor: 24 h uptime, avg latency")
    d.arrow("n10", rt + 6, 615, db - 6, 615, "10: aggregate checks (COUNT, AVG)")
    d.arrow("n11", rt + 6, 680, rd - 6, 680, "11: SETEX monitors:list:{user_id} 15 s")
    d.arrow("n12", rt - 6, 790, a + 6, 790, "12: 200 OK  Monitor[] JSON", dashed=True)
    d.arrow("n13", a - 6, 820, b + 6, 820, "13: typed Monitor[]: render rows", dashed=True)
    d.write(OUT / "10-sequence-dashboard.drawio")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    dfd0()
    dfd1()
    use_case()
    class_diagram()
    seq_outage()
    seq_dashboard()


if __name__ == "__main__":
    main()
