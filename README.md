# IPHS 400: Frontiers in AI

**Kenyon College — Integrated Program for Humane Studies (IPHS) — Fall 2026**

Course website for IPHS 400, a hands-on study of AI software engineering (AI-SWE):
configuring, extending, and orchestrating AI coding agents through a professional
software development lifecycle. This repository contains the site's source and
its test suite; course submissions, quizzes, and grades are handled separately
on Moodle.

- **Instructor:** Jon Chun
- **Schedule:** Tu/Th, 2:40–4:00 PM · Timberlake #5 (Evans Conference Room)

## Repository Structure

```
.
├── index.html              # Home page
├── 404.html                 # Not-found page
├── core/                    # Syllabus, schedule, assignments, policies, about
│   ├── syllabus.html
│   ├── schedule.html
│   ├── assignments.html
│   ├── policies.html
│   └── about.html
├── weeks/                   # One page per week, week-01.html … week-15.html
├── css/
│   └── style.css            # Single shared stylesheet, no build step
├── js/
│   ├── site-search.js       # Client-side search widget (no network calls)
│   └── search-index.js      # Generated data the widget searches — see below
├── scripts/
│   └── build_search_index.py  # One-off script that (re)generates js/search-index.js
├── tests/                   # pytest suite validating the site
│   ├── conftest.py
│   ├── test_unit_html_structure.py
│   ├── test_integration_links.py
│   ├── test_e2e_site.py
│   ├── test_accessibility.py
│   ├── test_content_sync.py
│   ├── test_css_hygiene.py
│   └── requirements.txt
```

The site is static HTML/CSS with no build step or JS framework, other than
the small vanilla-JS search widget described below. Every page shares one
stylesheet and a common header/nav/hero/footer skeleton. It is meant to be
viewed with a local test webserver only — there is no deploy pipeline or
external hosting configuration.

## Site Search

Every page except `404.html` includes a "Search this site" button (bottom
right) backed by `js/site-search.js`. It matches what you type against
`js/search-index.js` — page titles, section headings, and short excerpts —
entirely client-side: no network requests, no external API, no cost.

`js/search-index.js` is generated, not hand-written. If you edit page
content, headings, or add a new page, regenerate it:

```bash
source .venv/bin/activate  # needs bs4/lxml, already in tests/requirements.txt
python3 scripts/build_search_index.py
```

The script also adds an `id` to any `<h2>`/`<h3>` inside `.page-content`
that doesn't already have one, so the search widget can deep-link to that
section (`page.html#section-slug`). Commit both the regenerated
`js/search-index.js` and any HTML files it added ids to.
`tests/test_unit_html_structure.py`'s `TestSiteSearchAssets` and
`TestPageContentHeadingIds` guard that every page stays wired up correctly.

## Local Development

Serve the site locally with Python's built-in HTTP server:

```bash
python3 -m http.server 8080
# then open http://localhost:8080/
```

No install step is required to view the site — only the test suite has
dependencies.

## Running the Tests

The test suite (pytest + BeautifulSoup/lxml) validates structural and content
integrity of every page:

- `test_unit_html_structure.py` — every page has a DOCTYPE, title, stylesheet
  link, header, footer, and hero `<h1>`; no leftover template branding; no
  placeholder or stub content
- `test_integration_links.py` — every internal link resolves; navigation is
  identical across all pages; the schedule links to all 15 week pages
- `test_e2e_site.py` — required files/directories exist; exact page count;
  every page is reachable from `index.html` (no orphaned pages)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r tests/requirements.txt
pytest tests/ -v
```

Run a single test file or test:

```bash
pytest tests/test_unit_html_structure.py -v
pytest tests/test_integration_links.py::TestNavConsistency::test_nav_links_resolve -v
```

## Content Source and Provenance

All course content (syllabus text, schedule, assignments, policies) is
sourced from the official Fall 2026 syllabus. The page layout, navigation
pattern, and stylesheet are adapted from a prior Kenyon course site
([`programminghumanity-org`](https://github.com/jon-chun)) for visual
consistency across Jon Chun's Kenyon course sites; no course content from
that site is reused here.

## License

See [LICENSE](LICENSE).
