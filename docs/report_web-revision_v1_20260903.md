# Code Review: IPHS 400 Course Website

**Repo:** `theailab-net` · **Reviewed:** 2026-09-03 · **Scope:** all 22 HTML pages, `css/style.css`, `tests/`, `README.md`

## Summary

The site is a small, static HTML/CSS course site (index + 404 + 5 core pages + 15 week pages, one shared stylesheet, no build step, no JS). Structurally it is in good shape: every internal link resolves, every page shares an identical header/nav/footer skeleton, there's no leftover template branding or stub content, and the `pytest` suite enforces those invariants automatically. Calendar arithmetic in the syllabus/schedule/week pages was checked by hand against the actual 2026 calendar (day-of-week for every date cited) and is entirely correct, including the trickier cases (single-session Weeks 1 and 7, the Thanksgiving week silently skipped from the week numbering).

The issues below are mostly maintainability and polish gaps rather than functional bugs: no page is broken today, but several patterns will cause real problems the next time someone edits content by hand. The most consequential finding is **duplicated content blocks with no single source of truth** (item 1) — everything else is comparatively minor.

No page content was changed as part of this review; this is analysis only.

---

## Findings

### 1. Duplicated content blocks with no single source of truth (High)

Several substantial blocks of markup are copy-pasted verbatim across two pages instead of living in one place:

| Content | Duplicated in | Verified |
|---|---|---|
| "Summary of Assignments and Weights" table (9 rows) | `core/syllabus.html` ↔ `core/assignments.html` | byte-for-byte identical |
| "Secrets Hygiene and Agent Safety" section (4 list items) | `core/syllabus.html` ↔ `core/policies.html` | identical text, differs only in heading level (`h2` vs `h3`) and list class |
| "Course Description" + "Course Goals and Learning Outcomes" (intro paragraphs + 9-item outcomes list) | `core/syllabus.html` ↔ `core/about.html` | identical |
| Abbreviated "Course Description" paragraph | `index.html` (shortened) vs. the full version above | near-duplicate |

Because this is hand-authored static HTML with no include/templating mechanism (no SSG, no server-side includes, no client-side templating), every future edit to a grading weight, a policy line, or a course-goals bullet has to be made correctly in two files by hand. Nothing currently enforces that they stay in sync — the test suite checks structure, not cross-page textual consistency — so drift is only a matter of time. This is the one item worth addressing structurally rather than cosmetically; see Recommendations.

### 2. ~40% of `css/style.css` is dead code (Medium)

`style.css` is adapted from a prior WordPress theme ("Twenty Nineteen"-style, per the file's own header comment and the README's provenance note). A number of class rules from that theme were carried over but are never referenced by any of the 22 HTML pages:

`.has-featured-image`, `.featured-media` (+ its duotone/grayscale hero image treatment), `.social-nav`, `.entry-meta`, `.entry-footer`, `.post-nav`, `.share-links`, `.post-preview` / `.other-blog-pages`, `.badge` / `.badge-draft` / `.badge-private` / `.badge-placeholder`, `.placeholder-notice`, `.columns`, `.wp-block-image`, `.wp-block-separator`, and `.page-meta` (one of the two classes the file's own comments mark as "repo addition").

That's roughly 150 of the file's 620 lines with zero call sites, confirmed by grepping every class name against all HTML. It doesn't break anything, but it's dead weight a future maintainer has to read past to understand what's actually styling the live site, and it invites confusion (e.g. a maintainer might assume `.badge-draft` is used to mark in-progress week pages, since that would be a natural fit for a course site — it isn't wired up anywhere).

### 3. Inconsistent internal-link conventions (Low)

Pages within `core/` link to their sibling pages two different ways:

- `core/schedule.html` and `core/syllabus.html` use the fully-qualified form: `href="../core/schedule.html"`
- `core/about.html`, `core/assignments.html`, `core/policies.html` use the bare relative form: `href="schedule.html"`

Both resolve correctly (confirmed by the link tests and the local server), so this isn't a bug, but it's a tell that the 5 `core/` pages weren't generated from one shared template — each was authored/edited independently. A single stray copy-paste from the wrong "family" of page (e.g. pasting a `weeks/` nav block, which correctly uses `../core/...`, into a new `core/` page) would produce a broken link that isn't obviously wrong on read-through.

### 4. Five week pages have a shorter `<title>`/`<h1>` than the topic name used elsewhere (Low)

The `<title>` and hero `<h1>` on a page always match each other, but for 5 of the 15 week pages they're a shortened version of the fuller topic name used in `core/schedule.html`'s link text:

| Page | `<title>` / `<h1>` | `schedule.html` link text |
|---|---|---|
| week-06 | "Week 6: Hooks Architecture" | "Week 6: Hooks Architecture **and Guardrails**" |
| week-10 | "Week 10: MP3 Demos and the Spec-Driven Landscape" | "...the Spec-Driven **Development** Landscape" |
| week-13 | "Week 13: Full-Cycle Capstone Work Session" | "...Work Session **and MP4 Presentations**" |
| week-14 | "Week 14: Final Project Work Session" | "...Work Session **and Poster Development**" |
| week-15 | "Week 15: Final Project Presentations" | "Week 15: Final Project **Poster** Presentations" |

Not a functional defect — both are recognizably "the same week" — but it reads as a naming slip rather than a deliberate abbreviation, since the other 10 week pages match `schedule.html` exactly.

### 5. No page-level metadata: SEO/social tags, favicon, canonical, `robots.txt`/`sitemap.xml` (Medium)

Checked across all 22 pages — none has any of:

- `<meta name="description">`
- Open Graph / Twitter Card tags (`og:title`, `og:description`, etc.) — relevant since the syllabus explicitly encourages students to build a public GitHub/portfolio presence, and this site itself models that
- `<link rel="icon">` (favicon) — browsers will show a generic blank-page icon in every tab
- `<link rel="canonical">`
- a `robots.txt` or `sitemap.xml` at the site root

None of this is required for a course site with a captive audience, but a course specifically about professional software practice is a natural place to model these basics.

### 6. Accessibility gaps (Medium)

- **No skip-to-content link.** Every page repeats the same ~6-item header/nav before the main content; keyboard and screen-reader users have no way to bypass it.
- **Data tables lack semantic markup.** Every `<table>` (Course Details, Summary of Assignments, Grading Scale, Required Accounts, the MP3/MP4 rubric — at least 8 tables across the site) uses bare `<tr>/<th>/<td>` with no `<thead>`/`<tbody>` split and no `scope="col"`/`scope="row"` on header cells. Screen readers rely on `scope` to announce which row/column a cell belongs to; without it, tables like the grading rubric (5 rows × 3 columns of prose) are harder to navigate non-visually.
- **No `aria-label` on `<nav>`.** Low priority since there's only one nav region per page, but worth adding if a secondary nav (e.g., a "weeks" sub-nav) is ever introduced.
- **Breadcrumb separator (`»`) is a bare character**, not marked `aria-hidden="true"`, so screen readers will read it aloud as "double chevron" or similar between every breadcrumb segment.

### 7. `404.html` is no longer reachable through any server configuration (Informational)

`404.html` exists, is well-formed, and is intentionally excluded from nav-consistency/reachability tests (per `tests/conftest.py`, it's "a server-served fallback page"). Previously, `netlify.toml`'s `[[redirects]]` rule routed all unmatched paths to it with a `404` status. Since the Netlify config was removed as part of the earlier "strip CI/CD" pass in this session, nothing now serves that file as an actual error page — `python3 -m http.server` returns its own built-in 404 HTML for unmatched paths, and any future static host would need an equivalent rule re-added explicitly. This isn't a regression in *content* (the page is untouched and still valid), but it's worth flagging since the file's only reason for existing is currently unfulfilled. Options: drop it (nothing links to it or needs it for a `python -m http.server`-only deployment target) or keep it as a template for whatever hosting is chosen later and note that explicitly in the README.

### 8. Minor / low-priority observations

- **`.gitignore` is a full generic Python-project template** (`__pycache__/`, `build/`, `develop-eggs/`, packaging artifacts, etc.) for a repo that is a static site plus a pytest suite. Harmless, but most of it is irrelevant noise; a maintainer skimming it for "what does this project actually produce" gets little signal.
- **No print stylesheet or `prefers-color-scheme` support.** Reasonable to skip for a v1, but worth a line in the CSS file's own header comment (which currently documents only the light-mode WordPress-theme provenance) if it's a deliberate scope decision rather than an oversight.
- **`weeks/week-04.html`, `week-06.html`, `week-10.html`, `week-11.html` have no `<strong>...due</strong>`-style callout line** that most other week pages have (e.g., "MP1 due Friday..."), which is expected (no deadline falls in those weeks) but means the pattern isn't self-documenting — a reader scanning quickly can't immediately tell "no deadline this week" apart from "deadline line accidentally omitted." A one-line HTML comment or a consistent placeholder wouldn't hurt, though this is a stylistic nicety, not a defect.

---

## What's already solid (verified, not just assumed)

- **All internal links resolve** and **every non-404 page is reachable from `index.html`** — verified independently by hand (via the local test server) in addition to the existing `pytest` suite.
- **Nav is byte-identical in structure and link targets across all 22 pages** (bar the two conventions noted in Finding 3, which are still both individually correct).
- **No leftover template branding, `Lorem ipsum`, `TBD`/`TODO` strings, or empty `.page-content`** anywhere.
- **Every date cited in the syllabus, schedule, and week pages is calendrically correct** — checked programmatically against the real 2026 calendar for all ~40 distinct dates referenced (semester start, both single-session weeks, October Break, Thanksgiving recess, all assignment due dates, exam period). Including the non-obvious case: the week of Nov 24/26 correctly falls inside Thanksgiving recess and is (correctly) omitted from the 15-week numbering rather than mislabeled.
- **No inline styles, no `<script>` tags, no `target="_blank"` links, no insecure (`http://`) external links** anywhere in the site.
- **Heading hierarchy is clean:** exactly one `<h1>` per page (in the hero), content proper starts at `<h2>`, no skipped levels observed in the pages sampled.

## Test-suite coverage gaps

The existing `tests/` suite (structure, links, nav consistency, reachability, exact page/file counts) is solid for what it checks, but it does not — and by design probably shouldn't all — cover:

- Cross-page textual consistency (Finding 1) — would need an explicit "these blocks must match" test if the duplication isn't eliminated structurally.
- Any accessibility checks (table semantics, skip links, `aria-*` usage).
- Any metadata/SEO checks (meta description, favicon, canonical).
- CSS coverage (i.e., flagging unused selectors) — no tooling currently checks this; Finding 2 was found by manual cross-referencing.
- `<title>`/`<h1>` vs. `schedule.html` link-text agreement (Finding 4).

## Recommendations, roughly in priority order

1. **Eliminate the content duplication in Finding 1**, or at minimum leave a `<!-- keep in sync with core/X.html -->` comment at each duplicated block so future edits aren't made in only one place. A lightweight static-include approach (even a simple pre-commit script that inlines a shared fragment) would remove the risk entirely without introducing a build step for the *served* site.
2. **Delete the dead CSS in Finding 2**, or if it's being kept intentionally as scaffolding for a future blog-style page, say so in the stylesheet's header comment so it doesn't read as debris.
3. **Pick one internal-link convention** (bare relative is shorter and is already the majority pattern — 3 of 5 `core/` pages, all 15 `weeks/` pages) **and apply it uniformly**, then let the existing link tests continue to guard it.
4. Add basic `<meta name="description">` per page and a favicon; both are cheap and immediately visible in browser tabs/search results/link previews.
5. Add `scope="col"` to header cells in every data table, and consider a skip-to-content link — both are small, high-leverage accessibility wins for a page that's otherwise simple enough to be near-perfectly accessible already.
6. Decide `404.html`'s fate (Finding 7) now that there's no host wiring it up, and document the decision in the README so it isn't a mystery to the next contributor.
