"""
End-to-end tests running the ``screenshot`` fixture through a real pytest-mpl
generate/compare cycle via ``pytester``.
"""

_PNG_SIG = b"\x89PNG\r\n\x1a\n"

_HTML = '<div id="t" style="width:100px;height:100px;background:red"></div>'


def _both_methods_source():
    return f'''
from urllib.parse import quote

import pytest

HTML = {_HTML!r}
URL = "data:text/html;charset=utf-8," + quote(HTML)


@pytest.mark.mpl_image_compare
def test_from_locator(screenshot, page):
    page.set_content(HTML)
    return screenshot.from_locator(page.locator("#t"))


@pytest.mark.mpl_image_compare
def test_from_url(screenshot):
    return screenshot.from_url(URL)
'''


def _locator_source(color):
    return f'''
import pytest

@pytest.mark.mpl_image_compare
def test_from_locator(screenshot, page):
    page.set_content(
        '<div id="t" style="width:100px;height:100px;background:{color}"></div>'
    )
    return screenshot.from_locator(page.locator("#t"))
'''


def _generate(pytester, baseline_dir, browser):
    return pytester.runpytest_subprocess(
        "--mpl-generate-path", str(baseline_dir), "--browser", browser
    )


def _compare(pytester, baseline_dir, browser):
    return pytester.runpytest_subprocess(
        "--mpl", "--mpl-baseline-path", str(baseline_dir), "--browser", browser
    )


def test_generate_creates_baselines(pytester, browser_name):
    pytester.makepyfile(test_shot=_both_methods_source())
    baseline_dir = pytester.path / "baseline"
    result = _generate(pytester, baseline_dir, browser_name)
    result.assert_outcomes(skipped=2)
    # pytest-playwright parametrizes browser tests as ``test_name[<browser>]``,
    # so baseline filenames carry the ``[<browser>]`` suffix; glob rather than
    # hardcode.
    baselines = sorted(baseline_dir.glob("*.png"))
    assert len(baselines) == 2
    assert all(b.read_bytes()[:8] == _PNG_SIG for b in baselines)


def test_compare_passes_after_generate(pytester, browser_name):
    pytester.makepyfile(test_shot=_both_methods_source())
    baseline_dir = pytester.path / "baseline"
    _generate(pytester, baseline_dir, browser_name).assert_outcomes(skipped=2)
    result = _compare(pytester, baseline_dir, browser_name)
    result.assert_outcomes(passed=2)


def test_compare_fails_on_mismatch(pytester, browser_name):
    pytester.makepyfile(test_shot=_locator_source("red"))
    baseline_dir = pytester.path / "baseline"
    _generate(pytester, baseline_dir, browser_name).assert_outcomes(skipped=1)
    # Recapture the same element in a different colour: same dimensions, so the
    # RMS comparison path is exercised (no shape-mismatch short-circuit).
    pytester.makepyfile(test_shot=_locator_source("blue"))
    result = _compare(pytester, baseline_dir, browser_name)
    result.assert_outcomes(failed=1)
