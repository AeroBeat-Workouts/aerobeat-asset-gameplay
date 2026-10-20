"""Remove only volatile Blender PNG ancillary text; retain IDAT and image bytes.

The C1 candidate scenes contain no concept or external images. Blender embeds
absolute source paths and wall-clock render stats in PNG tEXt chunks, which
must not become provisional reproducibility authority. A precise chunk filter
preserves every nonvolatile chunk and all rendered image bytes.
"""
from pathlib import Path
import struct
import zlib

VOLATILE_TEXT_KEYS = {
    b'File', b'Date', b'RenderTime',
    b'cycles.ViewLayer.total_time', b'cycles.ViewLayer.render_time',
}
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'


def normalize_png(path):
    path = Path(path)
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError(f'Invalid PNG: {path}')
    out = bytearray(PNG_SIGNATURE)
    offset = len(PNG_SIGNATURE)
    seen_end = False
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError(f'Truncated PNG chunk: {path}')
        size = struct.unpack_from('>I', data, offset)[0]
        chunk_end = offset + 12 + size
        if chunk_end > len(data):
            raise ValueError(f'Truncated PNG payload: {path}')
        name = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + size]
        crc = struct.unpack_from('>I', data, offset + 8 + size)[0]
        if zlib.crc32(name + payload) & 0xffffffff != crc:
            raise ValueError(f'PNG CRC mismatch: {path}')
        if not (name == b'tEXt' and payload.partition(b'\0')[0] in VOLATILE_TEXT_KEYS):
            out.extend(data[offset:chunk_end])
        offset = chunk_end
        if name == b'IEND':
            seen_end = True
            break
    if not seen_end or offset != len(data):
        raise ValueError(f'Missing or trailing PNG data: {path}')
    path.write_bytes(out)
