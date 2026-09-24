#!/usr/bin/env python3
"""Prints docs/build/sdd.html to the Review 2 PDF with headless Chromium.

  python docs/build/build_sdd.py

Writes Vigil_Software_Design_Document.pdf to the repo root and a copy to
docs/design/. Run scripts/make_design_diagrams.py and scripts/export_diagrams.py
first so the figures are current. Needs: pip install playwright && python -m
playwright install chromium (and network access for the syntax-highlighting CSS).
"""
import pathlib
import shutil

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "docs" / "build" / "sdd.html"
OUT = ROOT / "Vigil_Software_Design_Document.pdf"

FOOTER = ('<div style="font-family:Segoe UI,Arial;font-size:8px;color:#79818D;width:100%;'
          'padding:0 16mm;display:flex;justify-content:space-between">'
          '<span>Vigil — Software Design Document · github.com/vatsal-agra/vigil</span>'
          '<span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>')


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(SRC.as_uri(), wait_until="networkidle")
        page.wait_for_function("document.querySelectorAll('code.hljs').length > 0")
        page.pdf(path=str(OUT), format="A4", print_background=True,
                 display_header_footer=True, header_template="<span></span>",
                 footer_template=FOOTER, prefer_css_page_size=True)
        browser.close()
    shutil.copy(OUT, ROOT / "docs" / "design" / OUT.name)
    print("written:", OUT.name, OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
