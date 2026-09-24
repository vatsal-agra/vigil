#!/usr/bin/env python3
"""Exports every docs/design/diagrams/*.drawio to a PNG beside it.

  python scripts/export_diagrams.py

Renders with the official diagrams.net viewer in headless Chromium, so the PNG
is exactly what draw.io shows for the committed source. Needs network access
(the viewer script is loaded from viewer.diagrams.net) and:
  pip install playwright && python -m playwright install chromium
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIAGRAMS = ROOT / "docs" / "design" / "diagrams"
VIEWER = "https://viewer.diagrams.net/js/viewer-static.min.js"

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<style>body{margin:0;background:#fff}</style></head><body>
<div id="g" class="mxgraph" data-mxgraph='%s'></div>
<script src="%s"></script></body></html>"""


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1800, "height": 1200}, device_scale_factor=2)
        for src in sorted(DIAGRAMS.glob("*.drawio")):
            cfg = {"xml": src.read_text(encoding="utf-8"), "toolbar": "", "nav": False,
                   "resize": False, "border": 16, "lightbox": False}
            attr = json.dumps(cfg).replace("&", "&amp;").replace("'", "&#39;")
            page.set_content(PAGE % (attr, VIEWER), wait_until="networkidle")
            page.wait_for_selector("#g svg", timeout=30000)
            page.wait_for_timeout(500)
            out = src.with_suffix(".png")
            page.locator("#g svg").first.screenshot(path=str(out))
            print("  exported", out.relative_to(ROOT))
        browser.close()


if __name__ == "__main__":
    main()
