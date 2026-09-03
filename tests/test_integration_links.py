"""Integration tests: internal links resolve, nav is consistent, schedule links all weeks."""
import re
import pytest
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import unquote

SITE_ROOT = Path(__file__).parent.parent

EXPECTED_NAV_LABELS = {"Home", "Syllabus", "Schedule", "Assignments", "Policies", "About"}


def _rel(path):
    return str(path.relative_to(SITE_ROOT))


def _resolve_href(href, page_path):
    """Resolve a relative href to an absolute Path, or None for external/anchor/mailto links."""
    if not href or href.startswith(("http://", "https://", "mailto:", "#", "javascript:")):
        return None
    href = href.split("#")[0]
    if not href:
        return None
    href = unquote(href)
    return (page_path.parent / href).resolve()


def _collect_broken_links(page_path, soup, selector="a"):
    broken = []
    for tag in soup.select(selector):
        href = tag.get("href", "")
        target = _resolve_href(href, page_path)
        if target is not None and not target.exists():
            broken.append(href)
    return broken


class TestAllInternalLinks:
    def test_all_internal_links_resolve(self, site_root, parsed_pages):
        """Every internal <a href> across all pages must resolve to an existing file."""
        broken = []
        for path, _, soup in parsed_pages:
            for bad in _collect_broken_links(path, soup):
                broken.append(f"{_rel(path)} -> {bad}")
        assert not broken, f"{len(broken)} broken internal links. First 15: {broken[:15]}"


class TestNavConsistency:
    def test_all_nav_pages_have_identical_nav_labels(self, site_root, nav_pages):
        """Every page (except 404.html) must have the exact same set of nav link labels."""
        failures = []
        for f in nav_pages:
            soup = BeautifulSoup(f.read_text(encoding="utf-8"), "lxml")
            nav = soup.select_one("nav.main-nav")
            if not nav:
                failures.append(f"{_rel(f)}: missing nav.main-nav")
                continue
            labels = {a.get_text(strip=True) for a in nav.find_all("a")}
            if labels != EXPECTED_NAV_LABELS:
                failures.append(f"{_rel(f)}: {sorted(labels)}")
        assert not failures, f"Pages with inconsistent nav labels: {failures[:15]}"

    def test_nav_links_resolve(self, site_root, nav_pages):
        """Nav links on every non-404 page must resolve to existing files."""
        broken = []
        for f in nav_pages:
            soup = BeautifulSoup(f.read_text(encoding="utf-8"), "lxml")
            nav = soup.select_one("nav.main-nav")
            if not nav:
                continue
            for link in _collect_broken_links(f, nav, "a"):
                broken.append(f"{_rel(f)} -> {link}")
        assert not broken, f"Broken nav links: {broken[:15]}"


class TestScheduleLinksAllWeeks:
    def test_schedule_links_to_all_15_weeks(self, site_root):
        """core/schedule.html must link to weeks/week-01.html through weeks/week-15.html."""
        schedule = site_root / "core" / "schedule.html"
        soup = BeautifulSoup(schedule.read_text(encoding="utf-8"), "lxml")
        hrefs = {a.get("href", "") for a in soup.find_all("a")}
        missing = []
        for n in range(1, 16):
            expected = f"../weeks/week-{n:02d}.html"
            alt = f"weeks/week-{n:02d}.html"
            if expected not in hrefs and alt not in hrefs and not any(
                h.endswith(f"week-{n:02d}.html") for h in hrefs
            ):
                missing.append(f"week-{n:02d}.html")
        assert not missing, f"core/schedule.html missing links to: {missing}"


class TestWeekTopicNamesMatchSchedule:
    def test_week_title_h1_and_breadcrumb_match_schedule_link_text(self, site_root):
        """Each week page's <title>/<h1>/breadcrumb topic text must exactly
        match the link text used for that week in core/schedule.html —
        schedule.html is the source of truth for the full topic name."""
        schedule = site_root / "core" / "schedule.html"
        schedule_soup = BeautifulSoup(schedule.read_text(encoding="utf-8"), "lxml")
        schedule_topics = {}
        for a in schedule_soup.find_all("a", href=True):
            m = re.match(r"week-(\d{2})\.html$", Path(a["href"]).name)
            if m:
                schedule_topics[int(m.group(1))] = a.get_text(strip=True)

        failures = []
        for n, topic in schedule_topics.items():
            page = site_root / "weeks" / f"week-{n:02d}.html"
            soup = BeautifulSoup(page.read_text(encoding="utf-8"), "lxml")
            title = soup.title.get_text(strip=True).split("–")[0].strip()
            h1 = soup.select_one("section.hero h1").get_text(strip=True)
            crumb = soup.select_one(".breadcrumbs span:last-child").get_text(strip=True)
            for label, value in (("title", title), ("h1", h1), ("breadcrumb", crumb)):
                if value != topic:
                    failures.append(f"week-{n:02d}.html {label}={value!r} != schedule {topic!r}")
        assert not failures, f"Week topic mismatches vs schedule.html: {failures}"


class TestCoreInternalLinkConvention:
    def test_core_pages_link_to_siblings_with_bare_relative_paths(self, site_root):
        """core/*.html pages must link to sibling core/ pages with a bare
        filename (e.g. href="schedule.html"), not the redundant round-trip
        form (href="../core/schedule.html")."""
        failures = []
        for f in (site_root / "core").glob("*.html"):
            soup = BeautifulSoup(f.read_text(encoding="utf-8"), "lxml")
            for a in soup.find_all("a", href=True):
                if a["href"].startswith("../core/"):
                    failures.append(f"{_rel(f)} -> {a['href']}")
        assert not failures, f"core/ pages using the '../core/...' convention: {failures}"
