# IPHS 400 — Mini-Project 1: Web Redesign Report

**Author:** Peyton Hodges
**Date:** 2026-09-07
**Repository:** [`theailab-net`](https://github.com/samuelphodges/theailab-net)
**Live site:** https://samuelphodges.github.io/theailab-net/

This report covers the full history of the site from its original fork to the
final product, in three phases: the instructor-provided starting template, a
prior revision pass, and the redesign work completed in this session.

## Commit Timeline

| Commit | Author | Phase |
|---|---|---|
| `7af54e5` Initial commit | Jon Chun (instructor) | Fork origin |
| `4184aa1` Migrate IPHS 400 course site from ai-swe-best-practices | Jon Chun (instructor) | Fork origin |
| `50ceee1` Strip deploy pipeline, review the site, and implement the revision spec | Peyton Hodges | Phase 1: Revision spec |
| `80e5ce3` Restyle to match kenyon.edu and add a client-side site-search widget | Peyton Hodges | Phase 2: This session |
| `2a34bd2` Revert "Restyle to match kenyon.edu..." | Peyton Hodges | Phase 2: This session |
| `dccaf23` Restyle to match kenyon.edu (colors, type, layout only) | Peyton Hodges | Phase 2: This session |
| `0d6669b` Add MP1 web redesign writeup | Peyton Hodges | Phase 2: This session |

## Fork Origin

The repository began as a copy of the instructor's static course-site template
(`ai-swe-best-practices`), migrated into `theailab-net` with course-specific
content (syllabus, schedule, assignments, policies, weekly pages) and a
WordPress "Twenty Nineteen"-derived stylesheet. This was the bare-bones
starting point for the mini-project: functional, but with no accessibility
remediation, no automated tests, unused legacy CSS carried over from the
WordPress theme, and no meta descriptions or favicon.

## Phase 1: Revision Spec Implementation (prior to this session)

Before this session began, a code review of the forked template was conducted
and turned into a prioritized, 8-task revision spec, which was then fully
implemented (commit `50ceee1`). This phase is not part of this session's work,
but is included here for a complete record:

1. **Content-drift regression tests** — added automated tests (`pytest` +
   BeautifulSoup) that fail if content blocks duplicated across page pairs
   (e.g. the assignments/weights table appearing on both `syllabus.html` and
   `assignments.html`) are edited in only one place and silently diverge.
2. **Dead CSS removal** — deleted ~150 lines of unused WordPress-theme CSS
   (featured-image hero variant, blog post-preview styles, badges, WP block
   styles) confirmed unreferenced by any page.
3. **Meta descriptions and favicon** — added a unique `<meta
   name="description">` to all 22 pages and a shared SVG favicon, neither of
   which existed before.
4. **Accessibility remediation** — added a skip-to-content link, semantic
   table markup (`<thead>`/`scope="row"`/`scope="col"`), an `aria-label` on
   the primary navigation, and `aria-hidden` on the decorative breadcrumb
   separator — none of which existed before.
5. **Internal link convention cleanup** — standardized how `core/` pages
   link to their siblings (bare relative paths vs. redundant round-trip
   paths).
6. **Week-page title alignment** — synced 5 week-page titles/headings with
   the wording already used on the schedule page.
7. **404 page documentation** — documented (in the test suite itself) why
   `404.html` is kept but excluded from navigation/reachability checks.
8. **Housekeeping** — trimmed a generic Python-project `.gitignore` down to
   what the repo actually uses, and added self-documenting comments for
   scope decisions (no dark mode, no print stylesheet, weeks with no
   assignment due).

This phase produced the 39-check `pytest` suite (structure, accessibility,
links, content-sync, e2e reachability) that every later change — including
this session's redesign — was verified against.

## Phase 2: This Session's Redesign

### 1. Deployment
- Pushed the repository's existing commits to the GitHub remote
  (`samuelphodges/theailab-net`), which was three commits behind local work.
- Enabled GitHub Pages, serving directly from the `main` branch at the repo
  root — no build step required, since the site is static HTML/CSS.
- Result: a public, shareable URL that automatically rebuilds on every push
  to `main`.

### 2. Design Research
- Pulled real design tokens directly from kenyon.edu's live, production
  stylesheet rather than approximating them by eye: colors (`#151538` navy,
  `#4b2e84` purple, `#8f80ff` periwinkle, supporting neutrals) and typefaces
  (Gothia — serif display, Matter — sans body/nav) by inspecting Kenyon's
  actual CSS.

### 3. Visual Redesign (CSS only — zero content or wording changes)
Rewrote `css/style.css` in full:
- **Color palette** — replaced the prior default WordPress-blue accent with
  Kenyon's navy/purple/periwinkle system.
- **Typography** — serif headings paired with sans-serif body text, using
  system-font fallback stacks (Georgia/Times New Roman; system sans) rather
  than loading Kenyon's licensed fonts, keeping the site dependency-free.
- **Layout** — replaced the prior asymmetric left-column layout (inherited
  from a WordPress blog theme) with a centered, wider container, giving data
  tables (schedule, grading, assignment weights) real room instead of a
  cramped ~700px column.
- **Hero section** — a solid navy color-block panel with a white serif
  heading, standing in for Kenyon's photographic hero (the course site has
  no photography).
- **Navigation, tables, breadcrumbs, footer** — restyled to match: uppercase
  letter-spaced nav with a periwinkle active-state underline, navy table
  header rows with zebra striping, a navy footer with a periwinkle top
  border.

No HTML file was modified in the final version of this change — confirmed
via `git diff --stat` showing only `css/style.css` touched.

### 4. Design Comparison Before Implementation
Before committing to one direction, three concrete styled mockups were built
and presented side by side, each using the site's real Home-page content
(not placeholder text or abstract color swatches):
1. **Institutional Navy** — a conservative, generic-academic direction.
2. **Terminal Agent** — a direction themed around the course's actual
   subject matter (CLI-native coding agents), using a dark
   terminal-inspired chrome.
3. **Kenyon Match** — visual alignment with the parent institution's own
   site.

The Kenyon Match direction was selected and implemented.

### 5. Iteration
- The Kenyon restyle was initially built together with a client-side search
  widget (a search box matching typed queries to page content and linking
  to the relevant section).
- That combined change was fully reverted at the client's request,
  returning the site to its pre-redesign baseline.
- The Kenyon color/typography/layout styling was then reapplied on its own,
  intentionally scoped to exclude the search widget — a pure
  presentation-layer change with no content impact.

### 6. Continuous Verification
The full `pytest` suite (39 checks covering HTML structure, accessibility,
internal links, content synchronization, and CSS hygiene) was run after
every change in this session. All 39 checks passed throughout, confirming
that no content, wording, or page structure was altered at any point in the
redesign process — only the CSS presentation layer changed.

## Summary

The site moved through three clear phases: an instructor-provided bare-bones
fork, a revision pass that added accessibility, testing, and cleanup
(Phase 1), and a visual redesign matching the parent institution's identity
(Phase 2, this session). Content and information architecture were preserved
across every phase after the initial fork — all changes since Phase 1 were
verified against an automated test suite that would fail immediately on any
content or structural drift. The result is a deployed, publicly accessible
course site that keeps its original, already-tested content intact while
presenting it with a color scheme, typography, and layout matched to Kenyon
College's own visual identity.
