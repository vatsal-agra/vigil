#!/usr/bin/env python3
"""Prepares every image the submission document needs.

  python docs/build/make_assets.py

- Parses scripts/stories.sh into assets/stories.json
- Renders the six wireframe SVGs and the architecture SVG to PNG
- For each screenshot slot: uses docs/screenshots/<slot>.png if it exists,
  otherwise generates a labelled placeholder telling you what to capture

Run this again after adding screenshots, then rebuild the document.

Requires: pip install cairosvg pillow
"""
import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "build" / "assets"
SHOTS = ROOT / "docs" / "screenshots"

SLOTS = [
    ("s01-repo-readme", "SCREENSHOT 1", "GitHub repository page showing the README",
     ["Open  https://github.com/vatsal-agra/vigil",
      "Capture the landing page: folder structure at the top,",
      "README rendering below it."]),
    ("s02-branches", "SCREENSHOT 2", "GitHub branches - main plus a feature branch",
     ["Open  https://github.com/vatsal-agra/vigil/branches",
      "Must show  main  and  feat/us-16-public-status-page"]),
    ("s03-issues", "SCREENSHOT 3", "GitHub Issues - the 25 user stories",
     ["Open  https://github.com/vatsal-agra/vigil/issues",
      "Should show 25 open issues with epic and MoSCoW labels."]),
    ("s04-project-board", "SCREENSHOT 4", "GitHub Projects board grouped by MoSCoW",
     ["Open the 'Vigil - Product Backlog' project.",
      "Set the view to  Group by -> MoSCoW",
      "Capture all 25 cards in Must / Should / Could / Won't."]),
    ("s05-docker-build", "SCREENSHOT 5", "Terminal - docker compose up --build succeeds",
     ["Run  docker compose up --build",
      "Capture the five 'Container vigil-*-1  Started' lines."]),
    ("s06-compose-ps", "SCREENSHOT 6", "Terminal - all five containers healthy",
     ["Run  docker compose ps",
      "Wait ~30s so healthchecks pass; db, cache, api show (healthy)."]),
    ("s07-worker-logs", "SCREENSHOT 7", "Terminal - the probe worker running",
     ["Run  docker compose logs --tail 20 worker",
      "Wait for 'cycle complete, 4 monitor(s) checked'."]),
    ("s08-dashboard", "SCREENSHOT 8", "Browser - the app running on localhost:3000",
     ["Open  http://localhost:3000",
      "Sign in as  demo@vigil.dev / vigil-demo-2026",
      "Keep the address bar visible."]),
    ("s09-detail", "SCREENSHOT 9", "Browser - monitor detail with response-time chart",
     ["Click any monitor from the dashboard.",
      "Capture the 24-hour chart and the latest-checks list."]),
    ("s10-status-page", "SCREENSHOT 10", "Browser - the public status page",
     ["Open  http://localhost:3000/status/demo  in a private window."]),
]


def parse_stories():
    text = (ROOT / "scripts" / "stories.sh").read_text(encoding="utf-8")
    records = re.findall(r'^"(US-\d\d\|.*)"$', text, re.M)
    epics = {"epic:accounts": "Accounts and access", "epic:monitors": "Monitors",
             "epic:engine": "Checking engine", "epic:status": "Public status",
             "epic:alerting": "Alerting", "epic:ops": "Operations"}
    moscow = {"must-have": "Must", "should-have": "Should",
              "could-have": "Could", "wont-have": "Won't"}
    out = []
    for rec in records:
        sid, title, labels, points, story, criteria = rec.split("|")
        out.append({
            "id": sid, "title": title, "labels": labels, "points": int(points),
            "story": story, "ac": [a.strip() for a in criteria.split(" ;; ")],
            "epic": next(v for k, v in epics.items() if k in labels),
            "moscow": next(v for k, v in moscow.items() if k in labels),
        })
    if len(out) != 25:
        sys.exit(f"Expected 25 stories in scripts/stories.sh, parsed {len(out)}")
    return out


def render_svgs():
    import cairosvg
    for svg in sorted((ROOT / "docs" / "wireframes").glob("*.svg")):
        cairosvg.svg2png(url=str(svg), write_to=str(ASSETS / f"{svg.stem}.png"),
                         output_width=1800)
        print("  wireframe   ", svg.stem)
    arch = ROOT / "infra" / "architecture.svg"
    cairosvg.svg2png(url=str(arch), write_to=str(ASSETS / "architecture.png"),
                     output_width=2600)
    print("  architecture ")


def placeholder(name, tag, cap, hints):
    from PIL import Image, ImageDraw, ImageFont
    try:
        base = "/usr/share/fonts/truetype/dejavu/DejaVu"
        reg = ImageFont.truetype(f"{base}Sans.ttf", 34)
        bold = ImageFont.truetype(f"{base}Sans-Bold.ttf", 40)
        small = ImageFont.truetype(f"{base}Sans.ttf", 26)
    except OSError:
        reg = bold = small = ImageFont.load_default()

    W, H = 1400, 800
    im = Image.new("RGB", (W, H), (244, 246, 248))
    d = ImageDraw.Draw(im)
    for i in range(0, W, 26):
        d.line([(i, 3), (min(i + 14, W), 3)], fill=(150, 160, 172), width=5)
        d.line([(i, H - 3), (min(i + 14, W), H - 3)], fill=(150, 160, 172), width=5)
    for i in range(0, H, 26):
        d.line([(3, i), (3, min(i + 14, H))], fill=(150, 160, 172), width=5)
        d.line([(W - 3, i), (W - 3, min(i + 14, H))], fill=(150, 160, 172), width=5)
    d.rectangle([70, 250, 78, 300], fill=(43, 92, 217))
    d.text((100, 246), tag, font=bold, fill=(43, 92, 217))
    d.text((100, 310), cap, font=reg, fill=(32, 40, 52))
    y = 380
    for h in hints:
        d.text((100, y), h, font=small, fill=(70, 80, 92))
        y += 46
    d.text((100, H - 90), "Replace with your screenshot, then rerun this script.",
           font=small, fill=(110, 120, 132))
    im.save(ASSETS / f"{name}.png")


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)

    stories = parse_stories()
    (ASSETS / "stories.json").write_text(json.dumps(stories, indent=1), encoding="utf-8")
    print(f"  stories.json  {len(stories)} stories, "
          f"{sum(s['points'] for s in stories)} points")

    render_svgs()

    real = 0
    for name, tag, cap, hints in SLOTS:
        supplied = next((SHOTS / f"{name}{e}" for e in (".png", ".jpg", ".jpeg")
                         if (SHOTS / f"{name}{e}").exists()), None)
        if supplied:
            if supplied.suffix == ".png":
                shutil.copy(supplied, ASSETS / f"{name}.png")
            else:
                from PIL import Image
                Image.open(supplied).convert("RGB").save(ASSETS / f"{name}.png")
            print(f"  screenshot    {name}  <- {supplied.name}")
            real += 1
        else:
            placeholder(name, tag, cap, hints)
            print(f"  placeholder   {name}")

    print(f"\n{real}/10 screenshots supplied. Assets written to {ASSETS}")


if __name__ == "__main__":
    main()
