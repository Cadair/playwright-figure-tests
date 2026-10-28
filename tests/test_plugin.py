"""
Tests for the ``_plugin`` module: entry point, ``screenshot`` fixture, and capture API.
"""

from importlib.metadata import entry_points
from io import BytesIO
from urllib.parse import quote

from playwright_figure_tests._plugin import Screenshot

_PNG_SIG = b"\x89PNG\r\n\x1a\n"


def _savefig_bytes(figure):
    """Save a figure-like to a bytes buffer and return the bytes."""
    buf = BytesIO()
    figure.savefig(buf)
    return buf.getvalue()


def _data_url(html):
    """Build a data: URL from an HTML string."""
    return "data:text/html;charset=utf-8," + quote(html)


def test_entry_point_registered():
    """
    Assert the pytest11 entry point is registered and points at _plugin.
    """
    eps = entry_points(group="pytest11")
    ours = [ep for ep in eps if ep.name == "playwright_figure_tests"]
    assert len(ours) == 1
    assert ours[0].value == "playwright_figure_tests._plugin"


def test_from_locator_returns_png(page):
    """
    Assert from_locator produces a FigureLike that saves valid PNG bytes.
    """
    page.set_content('<div id="t">hello</div>')
    shot = Screenshot(page)
    fig = shot.from_locator(page.locator("#t"))
    assert _savefig_bytes(fig)[:8] == _PNG_SIG


def test_from_locator_is_deterministic(page):
    """
    Assert two from_locator captures of static content save identical bytes.
    """
    page.set_content('<div id="t" style="width:100px;height:100px;background:#3498db"></div>')
    shot = Screenshot(page)
    a = _savefig_bytes(shot.from_locator(page.locator("#t")))
    b = _savefig_bytes(shot.from_locator(page.locator("#t")))
    assert a == b


def test_from_url_captures_page(page):
    """
    Assert from_url navigates and captures the whole page as PNG.
    """
    shot = Screenshot(page)
    url = _data_url('<div id="t" style="width:100px;height:100px;background:#3498db"></div>')
    fig = shot.from_url(url)
    assert _savefig_bytes(fig)[:8] == _PNG_SIG


def test_from_url_with_selector_captures_element(page):
    """
    Assert from_url with a selector captures only the matched element.
    """
    shot = Screenshot(page)
    html = (
        '<div id="a" style="width:100px;height:100px;background:red"></div>'
        '<div id="b" style="width:100px;height:100px;background:blue"></div>'
    )
    url = _data_url(html)
    whole = _savefig_bytes(shot.from_url(url))
    element = _savefig_bytes(shot.from_url(url, selector="#a"))
    assert whole[:8] == _PNG_SIG
    assert element[:8] == _PNG_SIG
    assert whole != element


def test_from_url_is_deterministic(page):
    """
    Assert two from_url captures of the same page save identical bytes.
    """
    shot = Screenshot(page)
    url = _data_url('<div id="t" style="width:100px;height:100px;background:#3498db"></div>')
    a = _savefig_bytes(shot.from_url(url))
    b = _savefig_bytes(shot.from_url(url))
    assert a == b


def test_screenshot_fixture_captures(screenshot):
    """
    Assert the screenshot fixture yields a Screenshot that can capture a locator.
    """
    screenshot.page.set_content('<div id="t">hello</div>')
    fig = screenshot.from_locator(screenshot.page.locator("#t"))
    assert _savefig_bytes(fig)[:8] == _PNG_SIG
