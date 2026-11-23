#!/usr/bin/env python3
"""news-image-20261123: sum up the world's news of Monday 23 November 2026
in one 1024x1024 PNG front page.

The front page is pre-rendered and shipped in this repository as entry.png
(the same 134,242 bytes every run produced). This program is a stdlib-only
copier: it copies the bundled PNG to $MAKEFUN_OUTPUT_DIR/entry.png
(default /output/entry.png). No third-party imports, no network, no
randomness: every run writes identical bytes.
"""
import os
import shutil
from pathlib import Path

BUNDLED = Path(__file__).resolve().parent / "entry.png"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _check_png(data: bytes) -> None:
    if not data.startswith(PNG_MAGIC):
        raise ValueError("bundled entry.png is not a PNG file")
    if len(data) == 0:
        raise ValueError("bundled entry.png is empty")


def main() -> None:
    data = BUNDLED.read_bytes()
    _check_png(data)
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "entry.png"
    out_path.write_bytes(data)
    if out_path.stat().st_size != len(data):
        raise ValueError("copied entry.png has the wrong size")
    print(f"wrote {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
