"""
Screenshot capture helper that waits for rendered content to settle.

WebGL/canvas content is drawn asynchronously after an element is attached to
the DOM, so capturing immediately can grab a partially-rendered frame.
``screenshot_when_stable`` waits for the page network to be idle and then
repeatedly screenshots until two consecutive captures are identical, making
the result robust against these render races.

``screenshot_when_stable`` is adapted from glue-jupyter
(``glue_jupyter/tests/helpers.py``), which is BSD-3-Clause licensed.
"""

from typing import Protocol

from playwright.sync_api import Page

__all__ = ["screenshot_when_stable"]


class _Screenshotable(Protocol):
    def screenshot(self) -> bytes: ...


def screenshot_when_stable(
    page: Page,
    locator: _Screenshotable,
    *,
    interval: int = 200,
    max_iterations: int = 25,
) -> bytes:
    """
    Take a screenshot of ``locator`` once its rendered content has settled.

    WebGL/canvas content (e.g. image contours) is drawn asynchronously after
    the element is attached to the DOM, so capturing immediately can grab a
    partially-rendered frame. We wait for the network to be idle and then
    repeatedly screenshot until two consecutive captures are identical (or we
    hit ``max_iterations``), which makes the comparison robust against these
    render races.

    Parameters
    ----------
    page
        The Playwright page owning ``locator``. Used to wait for load state
        and to schedule the inter-capture pause.
    locator
        The element to screenshot. Must support ``locator.screenshot()``
    interval
        Milliseconds to wait between consecutive captures.
    max_iterations
        Maximum number of comparison captures. If the content never settles,
        the most recent screenshot is returned after this many iterations.

    Returns
    -------
    bytes
        The stable PNG screenshot bytes of ``locator``.
    """
    page.wait_for_load_state("networkidle")
    screenshot = locator.screenshot()
    for _ in range(max_iterations):
        page.wait_for_timeout(interval)
        new_screenshot = locator.screenshot()
        if new_screenshot == screenshot:
            break
        screenshot = new_screenshot
    return screenshot
