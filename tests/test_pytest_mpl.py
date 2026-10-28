"""
Tests for running pytest-mpl using ``FigureLike``.

The pytest-mpl comparison path exercised here is the default baseline-image
RMS comparison (via ``matplotlib.testing.compare.compare_images``); the
hash-library path is not used.
"""

import struct
import zlib

_PNG_SIG = b"\x89PNG\r\n\x1a\n"


# Minimal PNG builder (truecolor RGB, filter type 0, single IDAT chunk).

def _chunk(chunk_type, data):
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def _ihdr(width, height):
    return _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))


def _idat(rgb, width, height):
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type: None
        raw += rgb[y * width * 3:(y + 1) * width * 3]
    return _chunk(b"IDAT", zlib.compress(bytes(raw)))


def _png(rgb, width, height):
    return _PNG_SIG + _ihdr(width, height) + _idat(rgb, width, height) + _chunk(b"IEND", b"")


# 4x4 solid black and solid white: same dimensions so the RMS comparison
# path is exercised (no shape-mismatch short-circuit).
_SIDE = 4
PNG_BLACK = _png(b"\x00" * (_SIDE * _SIDE * 3), _SIDE, _SIDE)
PNG_WHITE = _png(b"\xff" * (_SIDE * _SIDE * 3), _SIDE, _SIDE)


def _figure_test_source(png_bytes):
    return f'''
import pytest

from playwright_figure_tests._figure import FigureLike

PNG = {png_bytes!r}


@pytest.mark.mpl_image_compare
def test_fig():
    return FigureLike(PNG)
'''


def _generate(pytester, baseline_dir):
    return pytester.runpytest_subprocess("--mpl-generate-path", str(baseline_dir))


def _compare(pytester, baseline_dir):
    return pytester.runpytest_subprocess("--mpl", "--mpl-baseline-path", str(baseline_dir))


def test_generate_creates_baseline(pytester):
    pytester.makepyfile(test_fig=_figure_test_source(PNG_BLACK))
    baseline_dir = pytester.path / "baseline"
    result = _generate(pytester, baseline_dir)
    result.assert_outcomes(skipped=1)
    baseline = baseline_dir / "test_fig.png"
    assert baseline.is_file()
    assert baseline.read_bytes()[:8] == _PNG_SIG


def test_compare_passes_after_generate(pytester):
    pytester.makepyfile(test_fig=_figure_test_source(PNG_BLACK))
    baseline_dir = pytester.path / "baseline"
    _generate(pytester, baseline_dir).assert_outcomes(skipped=1)
    result = _compare(pytester, baseline_dir)
    result.assert_outcomes(passed=1)


def test_compare_fails_on_mismatch(pytester):
    pytester.makepyfile(test_fig=_figure_test_source(PNG_BLACK))
    baseline_dir = pytester.path / "baseline"
    _generate(pytester, baseline_dir).assert_outcomes(skipped=1)
    # Replace the baseline with different pixels (same dimensions).
    (baseline_dir / "test_fig.png").write_bytes(PNG_WHITE)
    result = _compare(pytester, baseline_dir)
    result.assert_outcomes(failed=1)


def test_compare_fails_when_baseline_missing(pytester):
    pytester.makepyfile(test_fig=_figure_test_source(PNG_BLACK))
    baseline_dir = pytester.path / "baseline"  # never populated
    result = _compare(pytester, baseline_dir)
    result.assert_outcomes(failed=1)


def test_generate_is_deterministic(pytester):
    pytester.makepyfile(test_fig=_figure_test_source(PNG_BLACK))
    dir_a = pytester.path / "baseline_a"
    dir_b = pytester.path / "baseline_b"
    _generate(pytester, dir_a).assert_outcomes(skipped=1)
    _generate(pytester, dir_b).assert_outcomes(skipped=1)
    a = (dir_a / "test_fig.png").read_bytes()
    b = (dir_b / "test_fig.png").read_bytes()
    assert a == b
