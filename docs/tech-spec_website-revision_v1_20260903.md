# Tech Spec: Website Revision v1

**Source:** [`docs/report_web-revision_v1_20260903.md`](report_web-revision_v1_20260903.md) · **Repo:** `theailab-net` · **Drafted:** 2026-09-03

This spec turns the 2026-09-03 code review into discrete, independently implementable tasks. Each task lists the files it touches, why it matters, and the exact steps to do it. Tasks are ordered by priority (`high` → `medium` → `low`); within a priority tier, order is arbitrary — none of the tasks depend on another.

**Ground rules carried over from the site's own constraints:**
- The site is plain static HTML/CSS with no build step, no JS, and no deploy pipeline (local `python3 -m http.server` only). Nothing in this spec should introduce a build step for *serving* the site — a one-off editing script that you run once and commit the result is fine; a step that must run every time the site is served is not.
- `tests/` uses `pytest` + `BeautifulSoup`/`lxml`, with shared fixtures in `tests/conftest.py` (`all_html_files`, `parsed_pages`, `nav_pages`). New checks should reuse these fixtures rather than re-implementing file discovery.
- Don't reintroduce anything already stripped in the prior "remove Netlify/CI" pass (`netlify.toml`, `.github/workflows/`) — several items below (metadata, canonical URLs) are deliberately scoped down because the site currently has no public hosting URL.

| # | Task | Priority | Finding | Status |
|---|---|---|---|---|
| 1 | Guard against cross-page content drift | High | 1 | Not started |
| 2 | Remove dead CSS | Medium | 2 | Not started |
| 3 | Add per-page `<meta name="description">` and a favicon | Medium | 5 | Not started |
| 4 | Accessibility remediation (skip link, table semantics, nav label, breadcrumb separator) | Medium | 6 | Not started |
| 5 | Standardize internal nav-link convention in `core/` | Low | 3 | Not started |
| 6 | Align 5 week-page titles with `schedule.html` wording | Low | 4 | Not started |
| 7 | Decide and document `404.html`'s fate | Low | 7 | ✅ Done — Option B |
| 8 | Minor housekeeping (`.gitignore`, CSS scope note, due-date self-documentation) | Low | 8 | Not started |

---

## High priority

### Task 1 — Guard against cross-page content drift

**Description.** Three content blocks are duplicated verbatim across page pairs with no mechanism keeping them in sync: the assignments/weights table (`core/syllabus.html` ↔ `core/assignments.html`), the Secrets Hygiene list (`core/syllabus.html` ↔ `core/policies.html`), and the Course Description + Goals block (`core/syllabus.html` ↔ `core/about.html`). Add an automated regression test that fails the moment any pair diverges, without introducing a templating layer or build step.

**Justification.** This is a static site with no include mechanism, so eliminating the duplication outright would mean adding build tooling — out of scope given the site's "no build step" constraint. A test that asserts the pairs stay byte-identical (or item-identical, for the list) gets 90% of the safety at a fraction of the cost: it can't stop someone from editing only one copy, but it will fail loudly the next time `pytest` runs, which is the same enforcement mechanism already protecting every other invariant in this repo.

**Affected files:** new `tests/test_content_sync.py`; no HTML changes.

**Steps:**

1. Create `tests/test_content_sync.py` with the following content:

   ```python
   """Regression tests: content blocks that are hand-duplicated across page
   pairs must stay in sync. If one copy is edited without the other, these
   tests fail loudly instead of letting the pages silently diverge."""
   from bs4 import BeautifulSoup

   CORE = None  # set in fixture below


   def _soup(site_root, rel_path):
       text = (site_root / rel_path).read_text(encoding="utf-8")
       return BeautifulSoup(text, "lxml")


   def _heading_block_text(soup, heading_text):
       """Text of the heading's next sibling element (a <table> or <ul>)."""
       heading = soup.find(
           lambda tag: tag.name in ("h2", "h3") and heading_text in tag.get_text()
       )
       assert heading is not None, f"heading containing {heading_text!r} not found"
       sibling = heading.find_next_sibling()
       assert sibling is not None, f"no sibling block after {heading_text!r}"
       return sibling.get_text(strip=True)


   class TestAssignmentsTableInSync:
       def test_syllabus_and_assignments_tables_match(self, site_root):
           a = _soup(site_root, "core/syllabus.html")
           b = _soup(site_root, "core/assignments.html")
           text_a = _heading_block_text(a, "Summary of Assignments and Weights")
           text_b = _heading_block_text(b, "Summary of Assignments and Weights")
           assert text_a == text_b, (
               "core/syllabus.html and core/assignments.html assignments "
               "tables have diverged"
           )


   class TestSecretsHygieneInSync:
       def test_syllabus_and_policies_secrets_sections_match(self, site_root):
           a = _soup(site_root, "core/syllabus.html")
           b = _soup(site_root, "core/policies.html")
           text_a = _heading_block_text(a, "Secrets Hygiene and Agent Safety")
           text_b = _heading_block_text(b, "Secrets Hygiene and Agent Safety")
           assert text_a == text_b, (
               "core/syllabus.html and core/policies.html secrets-hygiene "
               "lists have diverged"
           )


   class TestCourseDescriptionInSync:
       def test_syllabus_and_about_description_match(self, site_root):
           a = _soup(site_root, "core/syllabus.html")
           b = _soup(site_root, "core/about.html")
           # Compare from "Course Description" through the end of the Goals
           # list, i.e. everything up to (not including) the next <h2>.
           for soup, label in ((a, "syllabus"), (b, "about")):
               start = soup.find("h2", string="Course Description")
               assert start is not None, f"{label}: 'Course Description' h2 not found"
           def _block_text(soup):
               start = soup.find("h2", string="Course Description")
               parts = []
               for sib in start.find_next_siblings():
                   if sib.name == "h2" and sib.get_text(strip=True) not in (
                       "Course Description", "Course Goals and Learning Outcomes"
                   ):
                       break
                   parts.append(sib.get_text(strip=True))
               return "".join(parts)
           assert _block_text(a) == _block_text(b), (
               "core/syllabus.html and core/about.html course description / "
               "goals blocks have diverged"
           )
   ```

2. Run `pytest tests/test_content_sync.py -v` and confirm all three tests pass against the current (in-sync) content — this proves the extraction logic is correct before it's trusted to catch future drift.
3. As a cheap second layer, add an HTML comment at the top of each duplicated block pointing at its counterpart, e.g. in `core/assignments.html` immediately before the assignments table:
   ```html
   <!-- kept in sync with core/syllabus.html § Summary of Assignments and Weights — tests/test_content_sync.py enforces this -->
   ```
   Add the mirrored comment in `core/syllabus.html`, `core/policies.html`, and `core/about.html` at their respective blocks.
4. Run the full suite (`pytest tests/ -v`) to confirm nothing else regressed.

**Verification:** `pytest tests/test_content_sync.py -v` passes now, and manually editing one copy of any of the three blocks (e.g. changing one weight percentage in `core/assignments.html` only) causes the corresponding test to fail — confirm this once, then revert the manual edit.

---

## Medium priority

### Task 2 — Remove dead CSS

**Description.** Delete the ~150 lines of `css/style.css` inherited from the original WordPress theme that no page references: the featured-image hero variant, social nav, blog entry-meta/entry-footer/post-nav/share-links, post-preview/other-blog-pages, the badge system, the placeholder notice, `.columns`, the two `.wp-block-*` rules, and `.page-meta`.

**Justification.** Confirmed by grepping every one of these class names against all 22 HTML files: zero matches. This is pure dead weight — it doesn't affect rendering, but it roughly doubles the effort required for a future maintainer to figure out what's actually styling the live site, and invites someone to build a feature (e.g., marking a week page "draft") on top of a class that looks wired up but isn't.

**Affected files:** `css/style.css` only.

**Steps:**

1. Before deleting anything, re-run the confirmation grep to make sure nothing changed since this spec was written:
   ```bash
   for cls in has-featured-image featured-media social-nav entry-meta entry-footer \
              post-nav share-links post-preview other-blog-pages badge \
              placeholder-notice columns wp-block-image wp-block-separator page-meta; do
     echo -n "$cls: "; grep -rl "$cls" --include=*.html . | grep -v tests | wc -l
   done
   ```
   Every line should print `0`. If any print nonzero, stop and inspect that class before touching it.
2. In `css/style.css`, delete the following rule blocks (identified by their own section comments, so exact line numbers aren't load-bearing — search for the comment text):
   - Under `/* Site Header */`: the entire `/* --- Featured-image variant... --- */` comment and the three rules under it (`.site-header.has-featured-image`, `.featured-media`, `.featured-media img`, `.featured-media::after`).
   - `.social-nav` and `.social-nav a` / `.social-nav a:hover`.
   - `.page-meta` (the block explicitly commented `/* Page meta (repo addition — quiet) */`).
   - `.entry-meta` and `.entry-meta a`.
   - `.entry-footer`.
   - `.post-nav`.
   - `.share-links` and its `> span`, `> span::before`, `a`, `a:hover` sub-rules.
   - `.post-preview` and its `h2`, `h2 a`, `h2 a:hover`, `.entry-meta`, `p` sub-rules, plus `.other-blog-pages`.
   - The entire `/* Badges */` section (`.badge`, `.badge-draft`, `.badge-private`, `.badge-placeholder`) and the `/* Placeholder notice */` section (`.placeholder-notice`, `.placeholder-notice h3`).
   - `.columns`.
   - The entire `/* WP Block styles */` section (`.wp-block-image`, `.wp-block-separator`).
3. In the `@media (max-width: 768px)` block near the end of the file, delete the now-orphaned overrides that reference the classes removed above: the `.site-header.has-featured-image` block, the `.featured-media { display: none; }` rule, and `.columns { column-count: 1; }`.
4. Leave `.breadcrumbs` and `.section`/`.item-list` alone — both are actively used (breadcrumbs on every non-index page; `.section`/`.item-list` on `index.html` and `core/schedule.html`).
5. Re-run the class-usage grep from step 1 as a sanity check that you didn't delete anything still-referenced, then start the local server and spot-check `index.html`, one `core/` page, and one `weeks/` page to confirm no visual regression.
6. Run `pytest tests/ -v` — the CSS-link-resolves test should still pass unchanged.

**Verification:** File shrinks from 620 lines to roughly 470; `pytest tests/ -v` still green; the three spot-checked pages render identically to before (visually diff against a `git stash` of the pre-edit file if in doubt).

---

### Task 3 — Add per-page `<meta name="description">` and a favicon

**Description.** Add a unique, accurate meta description to every page's `<head>`, plus a single shared favicon referenced from all 22 pages.

**Justification.** Confirmed via grep that none of the 22 pages has a meta description or a favicon link — browser tabs show a blank generic icon, and any link preview (Slack, iMessage, a README badge) has nothing to show. Scoped down from the full "SEO/social metadata" finding: since the site has no public URL (it's local-server-only by design), `<link rel="canonical">`, Open Graph tags, `robots.txt`, and `sitemap.xml` would all need a real domain to point at and are **not** part of this task — revisit them only if/when the site gets a public deploy target.

**Affected files:** all 22 HTML `<head>` blocks; one new `favicon.svg` at the repo root.

**Steps:**

1. Create `favicon.svg` at the repo root using the site's existing `--primary` accent color (`#0073a8`, already defined in `css/style.css`) so it matches the live palette rather than introducing a new one:
   ```svg
   <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
     <rect width="32" height="32" rx="6" fill="#0073a8"/>
     <text x="16" y="23" font-family="ui-monospace, Menlo, monospace" font-size="16"
           font-weight="700" fill="#ffffff" text-anchor="middle">&gt;_</text>
   </svg>
   ```
   (A terminal-prompt glyph — deliberately on-theme for a course about CLI-native coding agents.)
2. In every page's `<head>`, add a favicon link. Path depends on directory depth:
   - `index.html`, `404.html`: `<link href="favicon.svg" rel="icon" type="image/svg+xml"/>`
   - `core/*.html`, `weeks/*.html`: `<link href="../favicon.svg" rel="icon" type="image/svg+xml"/>`
3. Add one `<meta name="description" content="...">` per page, placed after the viewport meta tag and before `<title>`. Use these exact descriptions for the 7 non-week pages:

   | Page | Description |
   |---|---|
   | `index.html` | `IPHS 400, Frontiers in AI — Kenyon College course site for a hands-on study of AI software engineering: configuring, extending, and orchestrating AI coding agents.` |
   | `404.html` | `Page not found — IPHS 400, Frontiers in AI, Kenyon College.` |
   | `core/syllabus.html` | `Full syllabus for IPHS 400, Frontiers in AI: course details, learning outcomes, required tools, secrets hygiene policy, and grading.` |
   | `core/schedule.html` | `Week-by-week schedule for IPHS 400, Frontiers in AI, Fall 2026, Kenyon College.` |
   | `core/assignments.html` | `Mini-project and Final Project descriptions, deadlines, and grading rubric for IPHS 400, Frontiers in AI.` |
   | `core/policies.html` | `Generative AI use policy, late-work policy, attendance policy, and Kenyon College statements for IPHS 400, Frontiers in AI.` |
   | `core/about.html` | `About IPHS 400, Frontiers in AI: instructor, course goals, and course site information.` |

   For the 15 week pages, derive the description mechanically from the existing `<title>` text to keep the work low-effort and consistent — for `weeks/week-NN.html` with title `"Week N: <Topic> – IPHS 400: Frontiers in AI"`, use:
   ```
   Week N: <Topic> — IPHS 400, Frontiers in AI, Kenyon College course schedule.
   ```
   e.g. for `weeks/week-01.html`: `Week 1: Course Introduction — IPHS 400, Frontiers in AI, Kenyon College course schedule.`
4. Add a test to `tests/test_unit_html_structure.py` guarding both additions so they can't silently regress:
   ```python
   class TestMetaDescriptionAndFavicon:
       def test_all_pages_have_meta_description(self, parsed_pages):
           failures = [
               _rel(p) for p, _, s in parsed_pages
               if not s.find("meta", attrs={"name": "description"})
           ]
           assert not failures, f"Pages missing meta description: {failures[:15]}"

       def test_all_pages_link_favicon(self, parsed_pages):
           failures = [
               _rel(p) for p, _, s in parsed_pages
               if not s.find("link", rel="icon")
           ]
           assert not failures, f"Pages missing favicon link: {failures[:15]}"
   ```
5. Run `pytest tests/ -v`.

**Verification:** `pytest tests/test_unit_html_structure.py -v` passes; opening any page in a browser shows the `>_` favicon in the tab; viewing page source shows a description distinct from every other page's.

---

### Task 4 — Accessibility remediation

**Description.** Four independent fixes: a skip-to-content link, semantic markup on data tables (`<thead>`/`<tbody>` + `scope`), an `aria-label` on the primary nav, and `aria-hidden` on the decorative breadcrumb separator.

**Justification.** None of these currently exist anywhere in the site (confirmed by grep for `aria-`, `skip`, `<thead>`, `scope=`). They're each small, mechanical, and meaningfully improve the experience for keyboard and screen-reader users without changing how the page looks or reads visually.

**Affected files:** `css/style.css`; all 22 HTML `<body>` openings; the 8 data tables (listed below); all 22 `<nav class="main-nav">` tags; the 20 pages with a `.breadcrumbs` div (everything except `index.html` and `404.html`).

#### 4a. Skip-to-content link

1. Add to `css/style.css` (anywhere; suggested: right after the `/* Reset */` block):
   ```css
   .skip-link {
     position: absolute;
     left: -999px;
     top: 0;
     background: var(--accent);
     color: #fff;
     padding: 0.75rem 1.25rem;
     z-index: 100;
     text-decoration: none;
     border-radius: 0 0 4px 0;
   }
   .skip-link:focus {
     left: 0;
   }
   ```
2. On every page, add `<a class="skip-link" href="#main">Skip to content</a>` as the very first child of `<body>`, before `<header>`.
3. On every page, add `id="main"` to the `<main class="content-wrapper">` tag.
4. Add a test to `tests/test_unit_html_structure.py`:
   ```python
   class TestSkipLink:
       def test_all_pages_have_skip_link_and_main_id(self, parsed_pages):
           failures = []
           for path, _, soup in parsed_pages:
               skip = soup.select_one("a.skip-link[href='#main']")
               main = soup.select_one("main#main")
               if not skip or not main:
                   failures.append(_rel(path))
           assert not failures, f"Pages missing skip link or main#id: {failures[:15]}"
   ```

#### 4b. Table semantics

Two distinct table shapes exist in the site; handle each accordingly.

**Row-header tables** (every row is `<tr><th>Label</th><td>Value</td></tr>` — no separate header row): `index.html` Course Details, `core/syllabus.html` Course Details, `core/about.html` Instructor. For these, add `scope="row"` to each `<th>`:
```html
<tr><th scope="row">Instructor</th><td>Jon Chun</td></tr>
```

**Column-header tables** (first row is the header, rest are data): `core/syllabus.html` Required Accounts and Subscriptions, `core/syllabus.html` Summary of Assignments and Weights, `core/syllabus.html` Grading Scale, `core/assignments.html` Summary of Assignments and Weights, `core/assignments.html` Mini-Project 3 & 4 Grading Rubric. For these, wrap the first row in `<thead>` with `scope="col"` on each `<th>`, and wrap the remaining rows in `<tbody>`:
```html
<table>
<thead>
<tr><th scope="col">Assignment</th><th scope="col">Weight</th><th scope="col">Due</th></tr>
</thead>
<tbody>
<tr><td>Class Participation…</td><td>20%</td><td>Ongoing</td></tr>
…
</tbody>
</table>
```
(Note: the "Total" row in that table uses `<th>` for the row label inside `<tbody>` — give it `scope="row"` too.)

Add a test:
```python
class TestTableSemantics:
    def test_all_tables_have_scope_on_headers(self, parsed_pages):
        failures = []
        for path, _, soup in parsed_pages:
            for th in soup.select("table th"):
                if not th.get("scope"):
                    failures.append(_rel(path))
                    break
        assert not failures, f"Pages with <th> missing scope: {failures[:15]}"
```

#### 4c. `aria-label` on primary nav

Change every `<nav class="main-nav">` to `<nav aria-label="Primary" class="main-nav">` (22 occurrences, one per page — a single find/replace across the repo is safe since the string is unique to this element):
```bash
find . -name '*.html' -not -path './.venv/*' -exec \
  sed -i 's/<nav class="main-nav">/<nav aria-label="Primary" class="main-nav">/' {} +
```

#### 4d. `aria-hidden` on breadcrumb separator

The literal `»` character appears only in `.breadcrumbs` divs (confirmed by grep — the *pagination* prev/next links use the `&raquo;` HTML entity instead, so this substitution is unambiguous). Wrap it so screen readers skip it:
```bash
find core weeks -name '*.html' -exec \
  sed -i 's/ » /  <span aria-hidden="true">»<\/span> /g' {} +
```
Then manually collapse the double space introduced before the new span on each of the 20 affected files, or simply re-run with a single space in the replacement (` <span aria-hidden="true">»</span> `) — verify with a diff on 2–3 files before running across all 20.

**Steps (all of 4a–4d), in order:**

1. Implement 4a, run `pytest tests/ -v`.
2. Implement 4b (5 pages, 8 tables — do these by hand; the shapes differ enough that a sed script would be riskier than the manual edit), run `pytest tests/ -v`.
3. Implement 4c via the sed command above, then `git diff` to confirm exactly 22 lines changed and nothing else.
4. Implement 4d via the sed command above, then `git diff` to confirm exactly 20 files changed, each only in `.breadcrumbs` divs.
5. Run the full suite: `pytest tests/ -v`.
6. Spot-check in a browser: tab from the address bar into the page and confirm the skip link appears on first `Tab` press; confirm visual appearance is unchanged (breadcrumbs still read "Home » Syllabus" to the eye).

**Verification:** `pytest tests/ -v` all green; `git diff --stat` shows changes to `css/style.css` plus all 22 HTML files; no visual difference when the pages are viewed normally.

---

## Low priority

### Task 5 — Standardize internal nav-link convention in `core/`

**Description.** `core/schedule.html` and `core/syllabus.html` link to their sibling `core/` pages using the redundant round-trip form (`href="../core/schedule.html"`), while `core/about.html`, `core/assignments.html`, and `core/policies.html` use the bare relative form (`href="schedule.html"`). Standardize on the bare form (the majority convention among these five files).

**Justification.** Both forms resolve correctly today — this isn't a live bug — but the inconsistency is a sign the five `core/` pages weren't built from one shared template, which raises the odds that a future copy-paste (e.g. pasting a `weeks/`-style nav block, which correctly uses `../core/...` because it's linking *across* directories) produces a broken link inside `core/` that doesn't look wrong on read-through. This is scoped narrowly: only the `<nav>` block in these two files is affected — `core/syllabus.html`'s body already uses the bare form correctly at line 118 (`href="assignments.html"`, `href="policies.html"`), so leave that as-is.

**Affected files:** `core/schedule.html` (5 nav lines), `core/syllabus.html` (5 nav lines) — 10 lines total.

**Steps:**

1. In `core/schedule.html`, in the `<nav class="main-nav">` block (5 `<li>` entries), change:
   ```
   href="../core/syllabus.html"    →  href="syllabus.html"
   href="../core/schedule.html"    →  href="schedule.html"
   href="../core/assignments.html" →  href="assignments.html"
   href="../core/policies.html"    →  href="policies.html"
   href="../core/about.html"       →  href="about.html"
   ```
   (Leave `href="../index.html"` for "Home" unchanged — that one correctly crosses into the parent directory.)
2. Apply the identical 5 substitutions to `core/syllabus.html`'s nav block.
3. Confirm no other `../core/` occurrences remain in either file:
   ```bash
   grep -n '\.\./core/' core/schedule.html core/syllabus.html
   ```
   should print nothing.
4. Run `pytest tests/test_integration_links.py -v` to confirm all links (including nav-consistency) still resolve.

**Verification:** the grep in step 3 is empty; `pytest tests/test_integration_links.py -v` passes; clicking every nav link on both pages in the local server still lands on the right page.

---

### Task 6 — Align 5 week-page titles with `schedule.html` wording

**Description.** Update the `<title>` and hero `<h1>` on `weeks/week-06.html`, `week-10.html`, `week-13.html`, `week-14.html`, and `week-15.html` to match the fuller topic name already used in `core/schedule.html`'s link text, matching the other 10 week pages' behavior.

**Justification.** Not a functional defect (both names are recognizably the same week), but it's inconsistent with the other 10 weeks, each of which matches `schedule.html` exactly. This is a visible content change (however small), so treat it as a deliberate copy edit rather than a mechanical one — confirm the exact wording against `core/schedule.html` before editing, since that file is the source of truth for topic names per Task 1's framing.

**Affected files:** `weeks/week-06.html`, `weeks/week-10.html`, `weeks/week-13.html`, `weeks/week-14.html`, `weeks/week-15.html` (2 lines each: `<title>` and `<h1>`).

**Steps:**

1. For each file, change both the `<title>` and the `<section class="hero"><h1>` text (they must stay identical to each other, per the existing `TestTitle` pattern other pages follow) as follows:

   | File | Current | New |
   |---|---|---|
   | `weeks/week-06.html` | Week 6: Hooks Architecture | Week 6: Hooks Architecture and Guardrails |
   | `weeks/week-10.html` | Week 10: MP3 Demos and the Spec-Driven Landscape | Week 10: MP3 Demos and the Spec-Driven Development Landscape |
   | `weeks/week-13.html` | Week 13: Full-Cycle Capstone Work Session | Week 13: Full-Cycle Capstone Work Session and MP4 Presentations |
   | `weeks/week-14.html` | Week 14: Final Project Work Session | Week 14: Final Project Work Session and Poster Development |
   | `weeks/week-15.html` | Week 15: Final Project Presentations | Week 15: Final Project Poster Presentations |

   Remember the `<title>` keeps its `– IPHS 400: Frontiers in AI` suffix; only the part before the en dash changes.
2. Also update the `<span>` inside each page's own `.breadcrumbs` div (it repeats the same topic name as a plain-text breadcrumb) to match.
3. Run `pytest tests/ -v` — in particular `TestTitle` and `TestScheduleLinksAllWeeks`, which will still pass since they don't check exact wording, only suffix/existence, but running the full suite is cheap insurance.
4. Diff `core/schedule.html`'s link text against each updated page one more time by eye to confirm an exact match (including punctuation).

**Verification:** `grep -A1 "Week 6:" core/schedule.html weeks/week-06.html` (and similarly for 10/13/14/15) shows identical topic text on both sides; `pytest tests/ -v` passes.

---

### Task 7 — Decide and document `404.html`'s fate ✅ Done (Option B)

**Description.** `404.html` currently has no server configuration serving it: the Netlify redirect that used to route unmatched paths to it was removed along with `netlify.toml` in an earlier pass, and `python3 -m http.server` doesn't support custom error pages.

**Decision:** keep the file, and document the gap directly in the test suite (rather than only in the README) — the test suite is what already draws the line between "existence is required" (`test_e2e_site.py`) and "excluded from nav/reachability checks" (`conftest.py`'s `nav_pages` fixture), so that's the natural place to also explain *why* the exclusion exists and what would need to change to close the gap.

**Justification.** The file itself is fine — well-formed, on-brand, already excluded correctly from the reachability/nav tests — but its only reason to exist (being served on a 404) was unfulfilled and undocumented, so the next contributor would have had to rediscover this history themselves.

**Affected files:** `tests/conftest.py`, `tests/test_e2e_site.py`.

**What was implemented:**

1. `tests/conftest.py` — expanded the `nav_pages` fixture's docstring to state explicitly that `404.html` is not reachable via `python3 -m http.server` (the repo's only supported way to run the site), and that it's kept in case of a future static-host deploy that supports custom-error routing:
   ```python
   @pytest.fixture(scope="session")
   def nav_pages(all_html_files):
       """All HTML files except 404.html.

       404.html is a custom error page, intentionally not linked from navigation
       or content, so it's excluded from nav-consistency and
       reachability-from-index checks.

       It is NOT currently reachable when running the site locally:
       `python3 -m http.server` (this repo's only supported way of running the
       site, per the README) has no concept of a custom 404 page and always
       serves its own built-in error response for unmatched paths. The file is
       kept in the repo anyway, in case the site is ever deployed to a static
       host that supports routing unmatched requests to a custom error page
       (e.g. a redirect/rewrite rule, an `ErrorDocument` directive) — at that
       point this file would need to be wired up again on the host side.
       """
       return [f for f in all_html_files if f.name != "404.html"]
   ```
2. `tests/test_e2e_site.py` — added a short comment above the `test_required_root_files_exist` parametrize list pointing at the fuller explanation, so a reader hitting this test first isn't confused about why `404.html` is required to exist but excluded elsewhere:
   ```python
   class TestRequiredFiles:
       # 404.html is required to exist even though it's currently unreachable via
       # `python3 -m http.server` — see the `nav_pages` fixture docstring in
       # conftest.py for why it's kept.
       @pytest.mark.parametrize("filename", ["index.html", "404.html", "css/style.css"])
       def test_required_root_files_exist(self, site_root, filename):
   ```
3. No changes to `404.html` itself, `README.md`, or `EXPECTED_TOTAL_PAGES` — the file stays required and counted, just better explained.

**Verification:** `pytest tests/ -v` — all 25 tests pass (confirmed 2026-09-03).

---

### Task 8 — Minor housekeeping

**Description.** Three small, unrelated cleanups bundled together because each is too small to warrant its own task overhead.

**Justification.** None of these affect correctness; each is a small maintainability nicety noticed during review.

**8a. Trim `.gitignore`.**
Current `.gitignore` is a full generic Python-project template (`__pycache__/`, `build/`, `develop-eggs/`, packaging artifacts, etc.) for a repo that's a static site plus a `pytest` suite.
1. Open `.gitignore` and keep only what's actually relevant: `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.venv/` (or whatever virtualenv directory name is actually used), and any editor/OS cruft (`.DS_Store`) already present.
2. Delete the rest (packaging/distribution sections, framework-specific sections for Django/Flask/Scrapy/etc. that don't apply here).
3. Run `git status` before and after to confirm nothing currently tracked or untracked-but-wanted gets newly ignored or unignored.

**8b. Note the light-mode-only scope in `style.css`'s header comment.**
1. In `css/style.css`, the file's opening comment currently documents only the light-mode WordPress-theme provenance. Add one line noting there's no print stylesheet or `prefers-color-scheme` (dark mode) support, and that this is a deliberate v1 scope decision rather than an oversight — e.g.:
   ```
   No print stylesheet or dark-mode (prefers-color-scheme) support in v1 —
   deliberate scope cut, not an oversight.
   ```

**8c. Self-document weeks with no due-date callout.**
`weeks/week-04.html`, `week-06.html`, `week-10.html`, and `week-11.html` have no `<strong>...due...</strong>`-style line that most other week pages have, which is correct (no deadline falls in those weeks) but not self-evident on a quick read.
1. In each of the 4 files, add a one-line HTML comment inside `.page-content`, near the other summary paragraphs, e.g.:
   ```html
   <!-- no assignment due this week -->
   ```
   This is a comment (invisible on the rendered page), not new visible copy, so it doesn't touch page content in any user-facing way.

**Verification:** `git diff` for 8a shows only irrelevant `.gitignore` sections removed and `git status` output is unchanged from before the edit; 8b and 8c are single-line comment additions, confirmed by `git diff --stat` showing 1 changed line in `css/style.css` and 1 line added in each of the 4 week files.
