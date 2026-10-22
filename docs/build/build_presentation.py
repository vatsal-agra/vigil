#!/usr/bin/env python3
"""Renders docs/presentation/presentation-script.md to a printable PDF.

  python docs/build/build_presentation.py

Needs: pip install markdown playwright && python -m playwright install chromium
"""
import pathlib

import markdown
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "docs" / "presentation" / "presentation-script.md"
OUT = ROOT / "docs" / "presentation" / "Vigil_Presentation_Script.pdf"

CSS = """
@page { size: A4; margin: 14mm 15mm 15mm 15mm; }
body { font-family: "Segoe UI", Calibri, Arial, sans-serif; font-size: 10.5pt; line-height: 1.5; color: #1f2630; }
h1 { font-size: 20pt; margin: 0 0 2pt; color: #12161C; }
h1 + p { color: #5A626D; margin-top: 0; }
h2 { font-size: 13pt; color: #2B5CD9; border-bottom: 2px solid #2B5CD9; padding-bottom: 3pt; margin: 16pt 0 6pt; break-after: avoid; }
h2:nth-of-type(n+2) { break-before: auto; }
em { color: #0E5A3E; font-style: normal; background: #EDF7F1; padding: 0 2pt; border-radius: 2pt; }
strong { color: #12161C; }
code { font-family: Consolas, monospace; font-size: 9pt; background: #F1F3F6; padding: 0 3pt; border-radius: 2pt; }
pre { background: #12161C; color: #E6ECF8; padding: 7pt 10pt; border-radius: 4pt; break-inside: avoid; }
pre code { background: none; color: inherit; font-size: 9.5pt; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 8pt; font-size: 9pt; break-inside: avoid; }
th, td { border: 1px solid #D5DAE1; padding: 3pt 6pt; vertical-align: top; text-align: left; }
th { background: #E8EDF7; }
blockquote { border-left: 3px solid #B8860B; background: #FBF4E3; margin: 6pt 0; padding: 4pt 10pt; }
hr { border: none; border-top: 1px dashed #C9CFD7; margin: 12pt 0; }
p { margin: 4pt 0 6pt; } li { margin-bottom: 3pt; }
a { color: #2B5CD9; text-decoration: none; word-break: break-all; }
"""

FOOTER = ('<div style="font-family:Segoe UI,Arial;font-size:8px;color:#79818D;width:100%;padding:0 15mm;'
          'display:flex;justify-content:space-between"><span>Vigil — presentation script</span>'
          '<span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>')


def main():
    body = markdown.markdown(SRC.read_text(encoding="utf-8"), extensions=["tables", "fenced_code"])
    page = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        p = b.new_page()
        p.set_content(page, wait_until="load")
        p.pdf(path=str(OUT), format="A4", print_background=True, display_header_footer=True,
              header_template="<span></span>", footer_template=FOOTER)
        b.close()
    print("written", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
