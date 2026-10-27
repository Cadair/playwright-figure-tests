"""
Tests for ``FigureLike`` and ``_normalize_png``.
"""

import io
import struct
import zlib

import pytest

from playwright_figure_tests._figure import FigureLike, _normalize_png

# ---------------------------------------------------------------------------
# stdlib-only PNG build/parse helpers
# ---------------------------------------------------------------------------
# These build minimal PNGs (IHDR + IDAT + IEND, truecolor RGB, filter type 0)
# and parse them back, without depending on Pillow. They exist solely to make
# the figure tests hermetic and fast.

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _chunk(chunk_type, data):
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def _ihdr(width, height, bit_depth=8, color_type=2):
    # color_type 2 = truecolor RGB
    body = struct.pack(">IIBBBBB", width, height, bit_depth, color_type, 0, 0, 0)
    return _chunk(b"IHDR", body)


def _idat(rgb, width, height):
    stride = width * 3
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type: None
        raw += rgb[y * stride:(y + 1) * stride]
    return _chunk(b"IDAT", zlib.compress(bytes(raw)))


def _text(keyword, text):
    return _chunk(b"tEXt", keyword.encode("latin-1") + b"\x00" + text.encode("latin-1"))


def _png(*chunks):
    return PNG_SIGNATURE + b"".join(chunks)


def _parse_chunks(png):
    assert png[:8] == PNG_SIGNATURE
    chunks = []
    pos = 8
    while pos < len(png):
        length = int.from_bytes(png[pos:pos + 4], "big")
        chunks.append((png[pos + 4:pos + 8], png[pos + 8:pos + 8 + length]))
        pos = pos + 12 + length
    return chunks


def _decode_rgb(png, width, height):
    idat = b"".join(body for ctype, body in _parse_chunks(png) if ctype == b"IDAT")
    raw = zlib.decompress(idat)
    stride = width * 3
    rgb = bytearray()
    pos = 0
    for _ in range(height):
        assert raw[pos] == 0, "test helper only handles filter type 0"
        rgb += raw[pos + 1:pos + 1 + stride]
        pos += 1 + stride
    return bytes(rgb)


# ---------------------------------------------------------------------------
# shared image data
# ---------------------------------------------------------------------------

W, H = 2, 3
PIXELS = bytes(range(W * H * 3))  # 18 bytes: 0..17


@pytest.fixture
def png_minimal():
    return _png(_ihdr(W, H), _idat(PIXELS, W, H), _chunk(b"IEND", b""))


@pytest.fixture
def png_with_text():
    return _png(
        _ihdr(W, H),
        _text("Software", "playwright 1.64.1"),
        _idat(PIXELS, W, H),
        _text("Comment", "2026-10-27T15:00:00Z"),
        _chunk(b"IEND", b""),
    )


# ---------------------------------------------------------------------------
# _normalize_png
# ---------------------------------------------------------------------------

def test_normalize_strips_ancillary_keeps_critical(png_with_text):
    types = [ctype for ctype, _ in _parse_chunks(_normalize_png(png_with_text))]
    assert types == [b"IHDR", b"IDAT", b"IEND"]


def test_normalize_preserves_pixel_data(png_with_text):
    assert _decode_rgb(_normalize_png(png_with_text), W, H) == PIXELS


def test_normalize_noop_on_already_minimal(png_minimal):
    assert _normalize_png(png_minimal) == png_minimal


def test_normalize_preserves_multiple_idat():
    # Split the compressed image data across two IDAT chunks.
    stride = W * 3
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += PIXELS[y * stride:(y + 1) * stride]
    compressed = zlib.compress(bytes(raw))
    half = len(compressed) // 2
    png = _png(
        _ihdr(W, H),
        _chunk(b"IDAT", compressed[:half]),
        _chunk(b"IDAT", compressed[half:]),
        _chunk(b"IEND", b""),
    )
    normalized = _normalize_png(png)
    types = [ctype for ctype, _ in _parse_chunks(normalized)]
    assert types == [b"IHDR", b"IDAT", b"IDAT", b"IEND"]
    assert _decode_rgb(normalized, W, H) == PIXELS


def test_normalize_idempotent(png_with_text):
    once = _normalize_png(png_with_text)
    assert _normalize_png(once) == once


def test_normalize_rejects_non_png():
    with pytest.raises(ValueError):
        _normalize_png(b"\xff\xd8\xff\xe0JPEG bytes")
    with pytest.raises(ValueError):
        _normalize_png(b"")


def test_normalize_rejects_truncated_chunk():
    # Signature + a length field claiming 1000 bytes, but no body/CRC.
    truncated = PNG_SIGNATURE + struct.pack(">I", 1000) + b"tEXt"
    with pytest.raises(ValueError):
        _normalize_png(truncated)


# ---------------------------------------------------------------------------
# FigureLike.savefig
# ---------------------------------------------------------------------------

def test_savefig_writes_raw_bytes_to_path(tmp_path, png_minimal):
    fig = FigureLike(png_minimal, deterministic=False)
    target = tmp_path / "out.png"
    fig.savefig(target)
    assert target.read_bytes() == png_minimal


def test_savefig_writes_raw_bytes_to_str_path(tmp_path, png_minimal):
    fig = FigureLike(png_minimal, deterministic=False)
    target = tmp_path / "out.png"
    fig.savefig(str(target))
    assert target.read_bytes() == png_minimal


def test_savefig_writes_raw_bytes_to_fileobj(png_minimal):
    fig = FigureLike(png_minimal, deterministic=False)
    buf = io.BytesIO()
    fig.savefig(buf)
    assert buf.getvalue() == png_minimal


def test_savefig_ignores_matplotlib_kwargs(tmp_path, png_minimal):
    fig = FigureLike(png_minimal, deterministic=False)
    target = tmp_path / "out.png"
    # pytest-mpl passes these for matplotlib figures; FigureLike ignores them.
    fig.savefig(target, format="png", dpi=80, metadata={"Software": None})
    assert target.read_bytes() == png_minimal


def test_savefig_deterministic_strips_ancillary(tmp_path, png_with_text):
    fig = FigureLike(png_with_text, deterministic=True)
    target = tmp_path / "out.png"
    fig.savefig(target)
    written = target.read_bytes()
    assert written != png_with_text
    types = [ctype for ctype, _ in _parse_chunks(written)]
    assert types == [b"IHDR", b"IDAT", b"IEND"]
    assert _decode_rgb(written, W, H) == PIXELS


def test_figurelike_deterministic_default_is_true(png_with_text):
    assert FigureLike(png_with_text).deterministic is True


def test_savefig_deterministic_false_writes_raw(tmp_path, png_with_text):
    fig = FigureLike(png_with_text, deterministic=False)
    target = tmp_path / "out.png"
    fig.savefig(target)
    assert target.read_bytes() == png_with_text
