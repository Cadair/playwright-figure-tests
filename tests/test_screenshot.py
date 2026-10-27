"""
Tests for ``screenshot_when_stable`` (real browser via pytest-playwright).
"""

from playwright_figure_tests._screenshot import screenshot_when_stable

_PNG_SIG = b"\x89PNG\r\n\x1a\n"


def test_returns_png_bytes(page):
    """
    Assert a screenshot of a simple element is valid PNG bytes.
    """
    page.set_content('<div id="t">hello</div>')
    shot = screenshot_when_stable(page, page.locator("#t"))
    assert shot[:8] == _PNG_SIG


def test_stable_for_static_content(page):
    """
    Assert two captures of static content are byte-identical.
    """
    page.set_content(
        '<div id="t" style="width:100px;height:100px;background:#3498db"></div>'
    )
    a = screenshot_when_stable(page, page.locator("#t"))
    b = screenshot_when_stable(page, page.locator("#t"))
    assert a == b


def test_waits_for_async_content(page):
    """
    Assert content injected after a delay is captured, not a blank frame.
    """
    page.set_content("""
    <div id="t" style="width:100px;height:100px"></div>
    <script>
      setTimeout(() => {
        document.getElementById('t').innerHTML =
          '<div style="width:80px;height:80px;background:red"></div>';
      }, 500);
    </script>
    """)
    immediate = page.locator("#t").screenshot()
    stable = screenshot_when_stable(page, page.locator("#t"))
    assert stable[:8] == _PNG_SIG
    assert stable != immediate


def test_terminates_at_max_iterations(page):
    """
    Assert perpetually-changing content does not hang; last bytes returned.
    """
    page.set_content("""
    <div id="t" style="width:50px;height:50px"></div>
    <script>
      setInterval(() => {
        document.getElementById('t').textContent = String(Date.now());
      }, 16);
    </script>
    """)
    shot = screenshot_when_stable(
        page, page.locator("#t"), interval=50, max_iterations=3
    )
    assert shot[:8] == _PNG_SIG
