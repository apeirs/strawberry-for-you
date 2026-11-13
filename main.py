"""make.fun ai-happy-01 entry: copy the artwork beside this file, unchanged, to <output>/entry.png.

The artwork is art.png (or art.jpg if there is no art.png), found relative to this file. Before
copying, it is checked against the contest's file rules: PNG or JPEG signature, at most 1 MiB,
at most 1024x1024 pixels. If a check fails, the program exits non-zero and writes nothing.

The output directory is $MAKEFUN_OUTPUT_DIR, or /output when that is unset. To run locally:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3.13 main.py
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDIDATES = ("art.png", "art.jpg")
MAX_BYTES = 1024 * 1024
MAX_SIDE = 1024

PNG_SIG = b"\x89PNG\r\n\x1a\n"
JPEG_SIG = b"\xff\xd8\xff"
# SOF0..SOF15, minus DHT (C4), JPG (C8) and DAC (CC), which share the range.
JPEG_SOF = set(range(0xC0, 0xD0)) - {0xC4, 0xC8, 0xCC}


def png_size(data: bytes) -> tuple[int, int]:
    if len(data) < 24 or data[12:16] != b"IHDR":
        raise ValueError("PNG has no IHDR chunk where it should be")
    return int.from_bytes(data[16:20]), int.from_bytes(data[20:24])


def jpeg_size(data: bytes) -> tuple[int, int]:
    i = 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            raise ValueError(f"JPEG marker expected at byte {i}")
        marker = data[i + 1]
        if marker == 0xFF:  # fill byte
            i += 1
            continue
        if marker == 0x01 or 0xD0 <= marker <= 0xD7:  # markers without a length
            i += 2
            continue
        if marker in (0xD9, 0xDA):  # end of image / start of scan before any SOF
            break
        length = int.from_bytes(data[i + 2:i + 4])
        if marker in JPEG_SOF:
            if i + 9 > len(data):
                break
            return int.from_bytes(data[i + 7:i + 9]), int.from_bytes(data[i + 5:i + 7])
        i += 2 + length
    raise ValueError("JPEG has no SOF segment before its image data")


def validate(data: bytes) -> None:
    if data.startswith(PNG_SIG):
        width, height = png_size(data)
    elif data.startswith(JPEG_SIG):
        width, height = jpeg_size(data)
    else:
        raise ValueError("not a PNG or JPEG (unrecognised signature)")
    if len(data) > MAX_BYTES:
        raise ValueError(f"{len(data)} bytes is over the {MAX_BYTES}-byte limit")
    if not (0 < width <= MAX_SIDE and 0 < height <= MAX_SIDE):
        raise ValueError(f"{width}x{height} pixels is outside 1..{MAX_SIDE} per side")


def find_art() -> Path:
    for name in CANDIDATES:
        path = HERE / name
        if path.is_file():
            return path
    sys.exit(f"error: no artwork found next to {__file__} (looked for {', '.join(CANDIDATES)})")


def main() -> None:
    art = find_art()
    data = art.read_bytes()
    try:
        validate(data)
    except ValueError as err:
        sys.exit(f"error: {art} fails the contest's file rules: {err}")
    (output_dir() / "entry.png").write_bytes(data)


def output_dir() -> Path:
    return Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")


if __name__ == "__main__":
    main()
