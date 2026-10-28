"""
playwright_figure_tests
=======================

A pytest helper library for visual regression testing of rendered web pages
using Playwright, built on top of pytest-mpl.
"""

from importlib.metadata import PackageNotFoundError, version

from ._figure import FigureLike
from ._plugin import Screenshot
from ._screenshot import screenshot_when_stable

try:
    __version__ = version("playwright_figure_tests")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = ["FigureLike", "Screenshot", "__version__", "screenshot_when_stable"]
