"""
Browser determinism tests for capture + normalize.

These verify that captures of a static page, normalized via ``FigureLike``
(``deterministic=True``), produce a stable SHA-256 hash.
"""

import hashlib
import io

from playwright_figure_tests._figure import FigureLike
from playwright_figure_tests._screenshot import screenshot_when_stable

_STATIC_HTML = (
    '<div id="t" style="width:120px;height:80px;'
    "background:#3498db;color:#ffffff;font-family:sans-serif;"
    'display:flex;align-items:center;justify-content:center">'
    "deterministic"
    "</div>"
)


def _normalized_hash(page, locator):
    raw = screenshot_when_stable(page, locator)
    buf = io.BytesIO()
    FigureLike(raw, deterministic=True).savefig(buf)
    return hashlib.sha256(buf.getvalue()).hexdigest()


def test_repeated_captures_stable_hash(page):
    """
    Assert repeated captures within one page yield one stable normalized hash.
    """
    page.set_content(_STATIC_HTML)
    locator = page.locator("#t")
    hashes = [_normalized_hash(page, locator) for _ in range(5)]
    assert len(set(hashes)) == 1


def test_independent_contexts_stable_hash(browser):
    """
    Assert two fresh browser contexts yield the same normalized hash.
    """
    hashes = []
    for _ in range(2):
        context = browser.new_context()
        try:
            page = context.new_page()
            page.set_content(_STATIC_HTML)
            hashes.append(_normalized_hash(page, page.locator("#t")))
        finally:
            context.close()
    assert hashes[0] == hashes[1]
