"""
pytest plugin exposing the ``screenshot`` fixture.
"""

import pytest
from playwright.sync_api import Locator, Page

from playwright_figure_tests import FigureLike

from ._screenshot import screenshot_when_stable


class Screenshot:
    """
    Pytest fixture class for taking screenshots from playwright.
    """

    def __init__(self, page: Page):
        self.page = page

    def from_url(
        self, url: str, selector: str | None = None, *, deterministic: bool = True, **kwargs
    ) -> FigureLike:
        """
        Create a `.FigureLike` from a url.

        Parameters
        ----------
        url
            The url to capture with playwright.
        selector
            The selector on the page to capture (if `None` then capture whole page).
        deterministic
            If `True` strip potentially variable metadata from the
            generated PNG to improve reliability of hash comparison.
        kwargs
            Extra kwargs are passed to `.screenshot_when_stable`.

        Returns
        -------
        figure
            The figure object to be returned from the test.
        """
        self.page.goto(url)
        locator: Page | Locator = self.page.locator(selector) if selector is not None else self.page
        return self.from_locator(locator, deterministic=deterministic, **kwargs)

    def from_locator(self, locator: Locator | Page, *, deterministic: bool = True, **kwargs):
        """
        Create a `.FigureLike` from a screenshotable playwright class.

        Parameters
        ----------
        locator
            A playwright object with a ``.screenshot()`` method.
        deterministic
            If `True` strip potentially variable metadata from the
            generated PNG to improve reliability of hash comparison.
        kwargs
            Extra kwargs are passed to `.screenshot_when_stable`.

        Returns
        -------
        figure
            The figure object to be returned from the test.
        """
        return self.from_bytes(
            screenshot_when_stable(self.page, locator, **kwargs), deterministic=deterministic
        )

    def from_bytes(self, bytes: bytes, *, deterministic: bool = True) -> FigureLike:
        """
        Generate a `.FigureLike` object from PNG bytes.

        Parameters
        ----------
        bytes
            The bytes of the PNG image.
        deterministic
            If `True` strip potentially variable metadata from the
            generated PNG to improve reliability of hash comparison.

        Returns
        -------
        figure
            The figure object to be returned from the test.
        """
        return FigureLike(bytes, deterministic=deterministic)


@pytest.fixture
def screenshot(page):
    """
    A `.Screenshot` instance using the current playwright ``page`` fixture.
    """
    return Screenshot(page)
