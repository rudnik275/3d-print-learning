"""Build bambu-studio-guide.pdf from guide.html.

    uv run --with playwright --with pypdf python docs/guide/build.py

Uses the installed Google Chrome (no browser download). Two passes: the first
renders the PDF and finds on which page every chapter heading landed, the second
writes those page numbers into the table of contents.
"""
import re
from pathlib import Path

from playwright.sync_api import sync_playwright
from pypdf import PdfReader

HERE = Path(__file__).parent
SRC = HERE / "guide.html"
OUT = HERE / "bambu-studio-guide.pdf"
TMP = HERE / ".build.html"

FOOTER = (
    '<div style="width:100%;font-size:7.5pt;color:#8a939d;font-family:Helvetica;'
    'padding:0 14mm;display:flex;justify-content:space-between">'
    '<span>Bambu Studio — руководство</span><span class="pageNumber"></span></div>'
)


def entries(html):
    """Parts (h1 with a part label) and chapters (h2) in document order."""
    out = []
    for m in re.finditer(r'<h1><span class="part">([^<]+)</span>([^<]+)</h1>|<h2[^>]*>([^<]+)</h2>', html):
        if m.group(1):
            out.append(("p", f"{m.group(1)} · {m.group(2)}", m.group(2)))
        else:
            out.append(("c", m.group(3), m.group(3)))
    return out


def toc_html(items, pages):
    rows = []
    for kind, label, _ in items:
        pg = pages.get(label, "")
        cls = ' class="p"' if kind == "p" else ""
        rows.append(f'<div{cls}><span>{label}</span><span class="dots"></span><span class="pg">{pg}</span></div>')
    return "\n".join(rows)


def render(html, browser):
    TMP.write_text(html, encoding="utf-8")
    page = browser.new_page()
    page.goto(TMP.resolve().as_uri(), wait_until="networkidle")
    page.pdf(path=str(OUT), format="A4", print_background=True, display_header_footer=True,
             header_template="<span></span>", footer_template=FOOTER,
             margin={"top": "15mm", "bottom": "16mm", "left": "14mm", "right": "14mm"})
    page.close()


def norm(s):
    return re.sub(r"[\s ]+", "", s)


def find_pages(items):
    reader = PdfReader(str(OUT))
    texts = [norm(p.extract_text() or "") for p in reader.pages]
    pages, start = {}, 2
    for kind, label, needle in items:
        key = norm(needle)[:24]
        for i in range(start, len(texts)):
            if key in texts[i]:
                pages[label] = i + 1
                start = i
                break
    return pages, len(texts)


def main():
    html = SRC.read_text(encoding="utf-8")
    items = entries(html)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        render(html.replace("<!--TOC-->", toc_html(items, {})), browser)
        pages, n = find_pages(items)
        render(html.replace("<!--TOC-->", toc_html(items, pages)), browser)
        browser.close()
    TMP.unlink()
    missing = [l for _, l, _ in items if l not in pages]
    print(f"{OUT.name}: {n} pages; toc entries {len(items)}, not found: {missing}")


if __name__ == "__main__":
    main()
