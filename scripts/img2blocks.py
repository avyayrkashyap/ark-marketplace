#!/usr/bin/env python3
"""Convert a logo image to monochrome terminal art using quadrant block
characters (each character cell covers 2x2 sub-pixels).

Usage: scripts/img2blocks.py IMAGE [WIDTH_IN_CHARS]
"""
import sys
from PIL import Image

# Quadrant bit order: top-left=1, top-right=2, bottom-left=4, bottom-right=8
QUADS = " ▘▝▀▖▌▞▛▗▚▐▜▄▙▟█"


def is_ink(px):
    r, g, b, a = px
    return a > 128 and (r + g + b) / 3 < 200


def convert(path, width=60):
    img = Image.open(path).convert("RGBA")
    cols = width * 2
    # Terminal cells are ~2x taller than wide, so a quadrant sub-pixel is 1:2.
    rows = round(img.height * cols / img.width / 2)
    rows += rows % 2
    small = img.resize((cols, rows), Image.LANCZOS)
    ink = [[is_ink(small.getpixel((x, y))) for x in range(cols)] for y in range(rows)]
    lines = []
    for y in range(0, rows, 2):
        line = ""
        for x in range(0, cols, 2):
            bits = ink[y][x] | ink[y][x + 1] << 1 | ink[y + 1][x] << 2 | ink[y + 1][x + 1] << 3
            line += QUADS[bits]
        lines.append(line.rstrip())
    while lines and not lines[-1]:
        lines.pop()
    while lines and not lines[0]:
        lines.pop(0)
    return "\n".join(lines)


if __name__ == "__main__":
    print(convert(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 60))
