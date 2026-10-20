#!/usr/bin/env python3
"""Standard-library checks for fail-closed candidate PNG metadata filtering."""
from pathlib import Path
import struct
import tempfile
import zlib

from knee_png_metadata import normalize_png


def chunk(kind, payload):
    return (struct.pack('>I', len(payload)) + kind + payload +
            struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff))


signature = b'\x89PNG\r\n\x1a\n'
header = chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0))
image = chunk(b'IDAT', zlib.compress(bytes((0, 1, 2, 3, 255))))
end = chunk(b'IEND', b'')
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / 'candidate.png'
    for label in (b'/tmp/build-A/source.blend', b'/tmp/build-B/source.blend'):
        path.write_bytes(signature + header + chunk(b'tEXt', b'File\0' + label) +
                         chunk(b'tEXt', b'Date\02026/10/20 12:00') +
                         chunk(b'tEXt', b'Artist\0Original AeroBeat') + image + end)
        normalize_png(path)
        content = path.read_bytes()
        assert b'Artist\0Original AeroBeat' in content
        assert b'File\0' not in content and b'Date\0' not in content
        assert image in content
        if label.startswith(b'/tmp/build-A'):
            first = content
        else:
            assert content == first, 'Only volatile metadata should differ'
        normalize_png(path)
        assert path.read_bytes() == first, 'Normalization must be idempotent'
    damaged = bytearray(first)
    damaged[35] ^= 1
    path.write_bytes(damaged)
    try:
        normalize_png(path)
    except ValueError:
        pass
    else:
        raise AssertionError('Corrupt PNG CRC must fail closed')
print('KNEE_DETERMINISM_HELPER_TEST_OK')
