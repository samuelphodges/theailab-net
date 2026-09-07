# IPHS 400 — Mini-Project 1: Web Redesign Report

**Author:** Peyton Hodges
**Date:** 2026-09-07
**Repository:** [`theailab-net`](https://github.com/samuelphodges/theailab-net)
**Live site:** https://samuelphodges.github.io/theailab-net/

## Starting Point

The course site (`theailab-net`) already had an accessibility and content-integrity
pass completed before this redesign began: a skip-to-content link, ARIA labels on
navigation, semantic table markup (`<thead>`/`scope`), per-page meta descriptions
and a favicon, dead CSS removal, and a set of automated regression tests
(content-sync checks that fail if duplicated content across pages drifts out of
sync). A 39-check `pytest` suite validated all of this. This was the foundation
the redesign below was built on top of — not part of the redesign itself.

## Changes Made

### 1. Deployment
- Pushed the repository's existing commits to a GitHub remote
  (`samuelphodges/theailab-net`), which was three commits behind local work.
- Enabled GitHub Pages, serving directly from the `main` branch at the repo root
  — no build step required, since the site is static HTML/CSS.
- Result: a public, shareable URL that automatically rebuilds on every push to
  `main`.

### 2. Design Research
- Pulled real design tokens directly from kenyon.edu's live, production
  stylesheet rather than approximating them by eye: colors (`#151538` navy,
  `#4b2e84` purple, `#8f80ff` periwinkle, supporting neutrals) and typefaces
  (Gothia — serif display, Matter — sans body/nav) by inspecting Kenyon's actual
  CSS.

### 3. Visual Redesign (CSS only — zero content or wording changes)
Rewrote `css/style.css` in full:
- **Color palette** — replaced the prior default WordPress-blue accent with
  Kenyon's navy/purple/periwinkle system.
- **Typography** — serif headings paired with sans-serif body text, using
  system-font fallback stacks (Georgia/Times New Roman; system sans) rather than
  loading Kenyon's licensed fonts, keeping the site dependency-free.
- **Layout** — replaced the prior asymmetric left-column layout (inherited from
  a WordPress blog theme) with a centered, wider container, giving data tables
  (schedule, grading, assignment weights) real room instead of a cramped ~700px
  column.
- **Hero section** — a solid navy color-block panel with a white serif heading,
  standing in for Kenyon's photographic hero (the course site has no
  photography).
- **Navigation, tables, breadcrumbs, footer** — restyled to match: uppercase
  letter-spaced nav with a periwinkle active-state underline, navy table header
  rows with zebra striping, a navy footer with a periwinkle top border.

No HTML file was modified in the final version of this change — confirmed via
`git diff --stat` showing only `css/style.css` touched.

### 4. Design Comparison Before Implementation
Before committing to one direction, three concrete styled mockups were built and
presented side by side, each using the site's real Home-page content (not
placeholder text or abstract color swatches):
1. **Institutional Navy** — a conservative, generic-academic direction.
2. **Terminal Agent** — a direction themed around the course's actual subject
   matter (CLI-native coding agents), using a dark terminal-inspired chrome.
3. **Kenyon Match** — visual alignment with the parent institution's own site.

The Kenyon Match direction was selected and implemented.

### 5. Iteration
- The Kenyon restyle was initially built together with a client-side search
  widget (a search box matching typed queries to page content and linking to
  the relevant section).
- That combined change was fully reverted at the client's request, returning
  the site to its pre-redesign baseline.
- The Kenyon color/typography/layout styling was then reapplied on its own,
  intentionally scoped to exclude the search widget — a pure presentation-layer
  change with no content impact.

### 6. Continuous Verification
The full `pytest` suite (39 checks covering HTML structure, accessibility,
internal links, content synchronization, and CSS hygiene) was run after every
change. All 39 checks passed throughout, confirming that no content, wording,
or page structure was altered at any point in the redesign process — only the
CSS presentation layer changed.

## Summary

Content and information architecture were preserved throughout this project.
Every visual change was isolated to `css/style.css`, and each change was
verified against an automated test suite that would fail immediately if any
content or structural drift occurred. The result is a course site that keeps
its original, already-tested content and accessibility work intact while
presenting it with a color scheme, typography, and layout matched to the
parent institution's visual identity.
