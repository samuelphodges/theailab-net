"""CSS hygiene: every class selector defined in css/style.css must be used
by at least one class="..." attribute somewhere on the site. This guards
against dead CSS accumulating again after the v1 cleanup."""
import re
from pathlib import Path

CSS_PATH = Path(__file__).parent.parent / "css" / "style.css"


def _css_class_selectors():
    text = CSS_PATH.read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)  # strip comments
    selectors = re.findall(r"([^{}]+)\{", text)
    classes = set()
    for sel in selectors:
        classes.update(m.group(1) for m in re.finditer(r"\.([a-zA-Z_][a-zA-Z0-9_-]*)", sel))
    return classes


class TestNoDeadCSS:
    def test_every_css_class_is_used_somewhere(self, parsed_pages):
        css_classes = _css_class_selectors()
        used_classes = set()
        for _, _, soup in parsed_pages:
            for tag in soup.find_all(class_=True):
                used_classes.update(tag.get("class"))
        dead = sorted(css_classes - used_classes)
        assert not dead, f"CSS classes defined in style.css but unused in any HTML page: {dead}"
