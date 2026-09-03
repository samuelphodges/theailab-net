"""Regression tests: content blocks that are hand-duplicated across page
pairs must stay in sync. If one copy is edited without the other, these
tests fail loudly instead of letting the pages silently diverge."""
from bs4 import BeautifulSoup


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

        def _block_text(soup):
            start = soup.find("h2", string="Course Description")
            assert start is not None, "'Course Description' h2 not found"
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
