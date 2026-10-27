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

__all__ = ["screenshot_when_stable"]


def screenshot_when_stable(page, locator, *, interval=200, max_iterations=25):
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
    page : playwright.sync_api.Page
        The Playwright page owning ``locator``. Used to wait for load state
        and to schedule the inter-capture pause.
    locator : playwright.sync_api.Locator
        The element to screenshot. Must support ``locator.screenshot()``
    interval : int, default 200
        Milliseconds to wait between consecutive captures.
    max_iterations : int, default 25
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
