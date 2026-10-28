"""
Figure-like object bridging pre-rendered PNG bytes into pytest-mpl.

pytest-mpl hashes the bytes written by ``fig.savefig(path)``, this
implements a duck-typed Figure like class with a ``savefig`` method.

``FigureLike`` generalises the ``DummyFigure`` class from glue-jupyter
(``glue_jupyter/tests/helpers.py``), which is BSD-3-Clause licensed, adding
optional deterministic PNG chunk stripping (see :func:`_normalize_png`).
"""

import os

__all__ = ["FigureLike"]


_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_CRITICAL_CHUNKS = frozenset({b"IHDR", b"IDAT", b"IEND"})


def _normalize_png(data):
    """
    Strip ancillary PNG chunks from *data*.

    Only the critical chunks (IHDR, IDAT, IEND) are retained, in order,
    with their original CRCs. Stripping metadata chunks (tEXt, gAMA, tIME,
    ...) makes the byte output -- and therefore the SHA-256 hash pytest-mpl
    computes over the saved file -- stable across captures that differ only
    in embedded metadata (software tags, timestamps, ...).

    Parameters
    ----------
    data : bytes
        The PNG bytes to normalize.

    Returns
    -------
    bytes
        The normalized PNG bytes with only critical chunks retained.

    Raises
    ------
    ValueError
        If *data* does not start with the PNG signature or is truncated
        mid-chunk.
    """
    if data[:8] != _PNG_SIGNATURE:
        raise ValueError("FigureLike expected PNG bytes; the PNG signature was not found.")

    out = bytearray(_PNG_SIGNATURE)
    pos = 8
    n = len(data)
    while pos < n:
        if pos + 8 > n:
            raise ValueError("Truncated PNG: incomplete chunk header.")
        length = int.from_bytes(data[pos : pos + 4], "big")
        chunk_type = data[pos + 4 : pos + 8]
        data_start = pos + 8
        data_end = data_start + length
        if data_end + 4 > n:
            raise ValueError("Truncated PNG: incomplete chunk body or CRC.")
        if chunk_type in _CRITICAL_CHUNKS:
            # length + type + data + crc, verbatim (CRC stays valid).
            out += data[pos : data_end + 4]
        pos = data_end + 4
    return bytes(out)


class FigureLike:
    """
    Wrap pre-rendered PNG bytes for use as a pytest-mpl figure.

    Implements the ``savefig`` method pytest-mpl invokes when hashing a
    figure: ``fig.savefig(filename, **savefig_kwargs)``. Unlike a Matplotlib
    Figure the image is already rendered, so ``savefig`` simply writes the
    stored bytes to the target path and ignores Matplotlib-specific keyword
    arguments such as ``format``, ``dpi`` or ``metadata``.

    Parameters
    ----------
    png_bytes : bytes
        The rendered PNG image bytes to compare.
    deterministic : bool, default True
        If True, ``savefig`` writes the bytes with ancillary PNG chunks
        stripped (see :func:`_normalize_png`), so the file content -- and the
        SHA-256 hash pytest-mpl computes over it -- is stable across captures
        that differ only in metadata. Set to False to write the raw bytes
        verbatim.
    """

    def __init__(self, png_bytes, *, deterministic=True):
        self._png_bytes = png_bytes
        self.deterministic = deterministic

    def savefig(self, filename_or_fileobj, *args, **kwargs):
        """
        Write the PNG bytes to the file.

        Parameters
        ----------
        filename_or_fileobj : str, os.PathLike, or file-like object
            A path (`str` or :class:`os.PathLike`) or a file-like object with a
            ``write`` method.
        *args, **kwargs
            Additional positional and keyword arguments are accepted
            for signature compatibility with Matplotlib's ``savefig``,
            and ignored.
        """
        data = self._png_bytes
        if self.deterministic:
            data = _normalize_png(data)

        if hasattr(filename_or_fileobj, "write"):
            filename_or_fileobj.write(data)
        else:
            with open(os.fspath(filename_or_fileobj), "wb") as f:
                f.write(data)
