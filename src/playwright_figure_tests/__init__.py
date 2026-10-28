"""
playwright_figure_tests
=======================

A pytest helper library for visual regression testing of rendered web pages
using Playwright, built on top of pytest-mpl.
"""

from importlib.metadata import PackageNotFoundError, version

from ._figure import FigureLike
from ._screenshot import screenshot_when_stable
from ._plugin import Screenshot

try:
    __version__ = version("playwright_figure_tests")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = ["Screenshot", "FigureLike", "screenshot_when_stable", "__version__"]
