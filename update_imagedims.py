#!/usr/bin/env python3
"""Update data/imagedims.json with pixel dimensions for every Cloudflare
Image Delivery URL referenced in content/.

Why this exists: the render hook (layouts/_default/_markup/render-image.html)
and the gallery shortcode (layouts/_shortcodes/gallery.html) emit width/height
attributes so browsers can reserve layout space (CLS). Many of the images
behind these URLs are legacy JPEGs whose subsampling Go's decoder (and
therefore Hugo's resources.GetRemote + .Width) cannot read. This script uses
a tiny stdlib-only header parser instead, and stores results in a committed
JSON file so builds do no network work.

Runs automatically before `npm run dev` / `npm run dev:drafts` / `npm run
build` via npm pre-hooks, so there is normally nothing to do by hand.

Usage:
    python3 update_imagedims.py            # fetch dims for URLs not yet in the file
    python3 update_imagedims.py --refresh  # re-fetch everything

Safe to re-run; only missing URLs are fetched. Fetch failures are skipped
(they retry on the next run) and never fail the run, so an offline laptop
can't block the npm scripts this is hooked into.
"""

import json
import re
import struct
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT_DIR = ROOT / "content"
DATA_FILE = ROOT / "data" / "imagedims.json"

# Commas are URL chars here (Cloudflare variants are comma-separated).
# Apostrophes are allowed only between other URL chars (e.g.
# ".../St.-Patrick's-Day_...jpg/..."), so a single-quoted Markdown title
# (![a](url 'title')) is never swallowed into the URL.
_B = r"[^\s\)\"'<>\[\]]"
URL_RE = re.compile(r"https://imagedelivery\.net/" + _B + r"+(?:'" + _B + r"+)*")
TRAILING_JUNK = ".,;:!"  # sentence punctuation a bare URL in prose may pick up

UA = {"User-Agent": "tobyblog-imagedims/1.0"}


def jpeg_dims(b):
    if b[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 9 < len(b):
        if b[i] != 0xFF:
            i += 1
            continue
        marker = b[i + 1]
        if marker == 0x01 or 0xD0 <= marker <= 0xD9:  # standalone markers
            i += 2
            continue
        seglen = struct.unpack(">H", b[i + 2 : i + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack(">HH", b[i + 5 : i + 9])
            return (w, h)
        i += 2 + seglen
    return None


def png_dims(b):
    if b[:8] == b"\x89PNG\r\n\x1a\n" and b[12:16] == b"IHDR":
        w, h = struct.unpack(">II", b[16:24])
        return (w, h)
    return None


def gif_dims(b):
    if b[:6] in (b"GIF87a", b"GIF89a"):
        w, h = struct.unpack("<HH", b[6:10])
        return (w, h)
    return None


def webp_dims(b):
    if b[:4] != b"RIFF" or b[8:12] != b"WEBP":
        return None
    chunk = b[12:16]
    if chunk == b"VP8 ":  # lossy
        w = struct.unpack("<H", b[26:28])[0] & 0x3FFF
        h = struct.unpack("<H", b[28:30])[0] & 0x3FFF
        return (w, h)
    if chunk == b"VP8L":  # lossless
        bits = struct.unpack("<I", b[21:25])[0]
        return ((bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1)
    if chunk == b"VP8X":  # extended
        w = (b[24] | (b[25] << 8) | (b[26] << 16)) + 1
        h = (b[27] | (b[28] << 8) | (b[29] << 16)) + 1
        return (w, h)
    return None


def image_dims(b):
    for parser in (jpeg_dims, png_dims, gif_dims, webp_dims):
        dims = parser(b)
        if dims:
            return dims
    return None


def collect_urls():
    urls = set()
    for md in CONTENT_DIR.rglob("*.md"):
        try:
            urls.update(u.rstrip(TRAILING_JUNK) for u in URL_RE.findall(md.read_text(encoding="utf-8", errors="replace")))
        except OSError as e:
            print(f"warn: could not read {md}: {e}", file=sys.stderr)
    return urls


def fetch_dims(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read(8 * 1024 * 1024)
        dims = image_dims(body)
        if not dims:
            print(f"warn: unrecognized image data for {url}", file=sys.stderr)
        return (url, dims)
    except Exception as e:
        print(f"warn: fetch failed for {url}: {e}", file=sys.stderr)
        return (url, None)


def main():
    refresh = "--refresh" in sys.argv

    existing = {}
    if DATA_FILE.exists() and not refresh:
        existing = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    urls = collect_urls()
    missing = sorted(u for u in urls if u not in existing)
    print(f"{len(urls)} unique image URLs in content; {len(missing)} to fetch")

    failed = 0
    done = 0
    with ThreadPoolExecutor(max_workers=12) as pool:
        for url, dims in pool.map(fetch_dims, missing):
            if dims:
                existing[url] = [dims[0], dims[1]]
            else:
                failed += 1
            done += 1
            if done % 200 == 0:
                print(f"  {done}/{len(missing)} fetched")

    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(existing, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if failed:
        print(f"{failed} URLs failed (will retry next run)")
    print(f"{DATA_FILE.relative_to(ROOT)}: {len(existing)} entries")
    # Never fail: this runs as an npm pre-hook and must not block dev/build.
    return 0


if __name__ == "__main__":
    sys.exit(main())
