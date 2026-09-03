"""Accessibility regression tests: skip link, table header semantics, nav
label, and the decorative breadcrumb separator."""


class TestSkipLink:
    def test_all_pages_have_skip_link_and_main_id(self, parsed_pages):
        failures = []
        for path, _, soup in parsed_pages:
            skip = soup.select_one("a.skip-link[href='#main']")
            main = soup.select_one("main#main")
            if not skip or not main:
                failures.append(path.name)
        assert not failures, f"Pages missing skip link or main#main: {failures[:15]}"


class TestTableSemantics:
    def test_all_table_headers_have_scope(self, parsed_pages):
        failures = []
        for path, _, soup in parsed_pages:
            for th in soup.select("table th"):
                if not th.get("scope"):
                    failures.append(f"{path.name}: <th> without scope ({th.get_text(strip=True)!r})")
        assert not failures, f"<th> cells missing scope: {failures[:20]}"


class TestNavAriaLabel:
    def test_all_nav_elements_have_aria_label(self, parsed_pages):
        failures = []
        for path, _, soup in parsed_pages:
            nav = soup.select_one("nav.main-nav")
            if nav is not None and not nav.get("aria-label"):
                failures.append(path.name)
        assert not failures, f"nav.main-nav missing aria-label: {failures[:15]}"


class TestBreadcrumbSeparatorHidden:
    def test_breadcrumb_separator_is_aria_hidden(self, parsed_pages):
        failures = []
        for path, _, soup in parsed_pages:
            crumbs = soup.select_one(".breadcrumbs")
            if crumbs is None:
                continue
            if "»" in crumbs.get_text():
                # the raw character must live inside an aria-hidden element
                hidden_spans = crumbs.select('[aria-hidden="true"]')
                if not any("»" in s.get_text() for s in hidden_spans):
                    failures.append(path.name)
        assert not failures, f"Breadcrumb separator not aria-hidden: {failures[:15]}"
