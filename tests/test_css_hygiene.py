"""CSS hygiene: every class selector defined in css/style.css must be used
by at least one class="..." attribute somewhere on the site, or created at
runtime by one of the site's own scripts. This guards against dead CSS
accumulating again after the v1 cleanup."""
import re
from pathlib import Path

CSS_PATH = Path(__file__).parent.parent / "css" / "style.css"
JS_DIR = Path(__file__).parent.parent / "js"


def _css_class_selectors():
    text = CSS_PATH.read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)  # strip comments
    selectors = re.findall(r"([^{}]+)\{", text)
    classes = set()
    for sel in selectors:
        classes.update(m.group(1) for m in re.finditer(r"\.([a-zA-Z_][a-zA-Z0-9_-]*)", sel))
    return classes


def _classes_referenced_in_js():
    """Classes the JS widgets (e.g. js/site-search.js) assign at runtime via
    element.className = "..." — these never appear in static HTML, so the
    static-HTML scan below can't see them on its own."""
    classes = set()
    for js_path in JS_DIR.glob("*.js"):
        text = js_path.read_text(encoding="utf-8")
        for m in re.finditer(r'\.className\s*=\s*"([^"]*)"', text):
            classes.update(m.group(1).split())
        for m in re.finditer(r'\.classList\.(?:add|remove|toggle)\(([^)]*)\)', text):
            classes.update(re.findall(r'"([^"]*)"', m.group(1)))
    return classes


class TestNoDeadCSS:
    def test_every_css_class_is_used_somewhere(self, parsed_pages):
        css_classes = _css_class_selectors()
        used_classes = set()
        for _, _, soup in parsed_pages:
            for tag in soup.find_all(class_=True):
                used_classes.update(tag.get("class"))
        used_classes.update(_classes_referenced_in_js())
        dead = sorted(css_classes - used_classes)
        assert not dead, f"CSS classes defined in style.css but unused in any HTML page or JS widget: {dead}"
