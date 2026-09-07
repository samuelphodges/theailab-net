#!/usr/bin/env python3
"""One-off maintenance script: adds id attributes to every <h2>/<h3> in
.page-content (if missing) and (re)generates js/search-index.js, the data
file the client-side site-search widget (js/site-search.js) reads.

This is NOT part of serving the site — run it by hand whenever page
content/headings change, then commit both the updated HTML and the
regenerated js/search-index.js. See tests/test_unit_html_structure.py's
TestSiteSearchAssets for the guard that keeps every page wired to it.

Usage:
    python3 scripts/build_search_index.py
"""
import html
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
EXCERPT_LEN = 200


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-")
    return slug or "section"


def unique_slug(text, used):
    base = slugify(text)
    slug = base
    n = 2
    while slug in used:
        slug = f"{base}-{n}"
        n += 1
    used.add(slug)
    return slug


def excerpt_after(heading):
    parts = []
    for sib in heading.find_next_siblings():
        if sib.name in ("h2", "h3"):
            break
        if sib.find(["h2", "h3"]):
            # Sibling wraps its own subheading (e.g. index.html's
            # <div class="section"><h2>Quick Links</h2>...) — that block
            # gets its own index entry, so stop before absorbing its text.
            break
        parts.append(sib.get_text(" ", strip=True))
    text = " ".join(p for p in parts if p)
    text = re.sub(r"\s+", " ", text).strip()
    return (text[:EXCERPT_LEN] + "…") if len(text) > EXCERPT_LEN else text


def page_url(path):
    rel = path.relative_to(ROOT)
    return str(rel).replace("\\", "/")


def display_title(soup):
    title = soup.title.get_text(strip=True) if soup.title else ""
    return title.split(" – ")[0].strip() if " – " in title else title


def add_ids_to_source(text, headings_needing_ids):
    """headings_needing_ids: list of (tag_name, heading_text, slug) in
    document order, for headings that don't already have an id. Uses a
    positional regex walk so only bare <h2>text</h2>/<h3>text</h3>
    occurrences (no existing attributes) are touched."""
    pos = 0
    for tag, heading_text, slug in headings_needing_ids:
        # get_text() decodes entities (e.g. "&amp;" -> "&"), but the source
        # still has the escaped form — re-escape before matching against it.
        source_text = html.escape(heading_text, quote=False)
        pattern = re.compile(rf"<{tag}>({re.escape(source_text)})</{tag}>")
        m = pattern.search(text, pos)
        if not m:
            continue
        replacement = f'<{tag} id="{slug}">{source_text}</{tag}>'
        text = text[: m.start()] + replacement + text[m.end() :]
        pos = m.start() + len(replacement)
    return text


def process_file(path, meta_description):
    raw = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(raw, "lxml")
    content = soup.select_one(".page-content")
    title = display_title(soup)
    url = page_url(path)

    entries = []
    used_slugs = set()
    needing_ids = []

    if content:
        for h in content.find_all(["h2", "h3"]):
            heading_text = h.get_text(strip=True)
            existing_id = h.get("id")
            if existing_id:
                slug = existing_id
                used_slugs.add(slug)
            else:
                slug = unique_slug(heading_text, used_slugs)
                needing_ids.append((h.name, heading_text, slug))
            entries.append(
                {
                    "url": f"{url}#{slug}",
                    "page": title,
                    "heading": heading_text,
                    "excerpt": excerpt_after(h),
                }
            )

    if needing_ids:
        raw = add_ids_to_source(raw, needing_ids)
        path.write_text(raw, encoding="utf-8")

    if not entries:
        # No sub-headings (most weeks/*.html): index the page itself.
        body_text = content.get_text(" ", strip=True) if content else ""
        body_text = re.sub(r"\s+", " ", body_text).strip()
        excerpt = (body_text[:EXCERPT_LEN] + "…") if len(body_text) > EXCERPT_LEN else body_text
        entries.append(
            {
                "url": url,
                "page": title,
                "heading": title,
                "excerpt": excerpt or meta_description,
            }
        )

    return entries


def main():
    files = []
    for pattern in ("*.html", "core/*.html", "weeks/*.html"):
        files.extend(sorted(ROOT.glob(pattern)))
    files = [f for f in files if f.name != "404.html"]

    index = []
    for f in files:
        raw = f.read_text(encoding="utf-8")
        soup = BeautifulSoup(raw, "lxml")
        meta = soup.find("meta", attrs={"name": "description"})
        meta_description = meta.get("content", "") if meta else ""
        index.extend(process_file(f, meta_description))

    out_path = ROOT / "js" / "search-index.js"
    js = "// Generated by scripts/build_search_index.py — do not hand-edit.\n"
    js += "window.SITE_SEARCH_INDEX = " + json.dumps(index, indent=2) + ";\n"
    out_path.write_text(js, encoding="utf-8")
    print(f"Wrote {len(index)} entries to {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
