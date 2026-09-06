"""Halfwidth Latin atlas transformation, preserving every Japanese glyph."""

import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom
from textcodec import LATIN

FONT_VROM = 0xBCD000
ATLAS_OFFSET = 0x128
ATLAS_SIZE = 0x6000
WIDTH_TABLE = 0x80106AF4 - CODE_RAM
WIDTH_BRANCH = 0x80090294 - CODE_RAM


def pixels(data):
    return [n for b in data for n in (b >> 4, b & 15)]


def pack_pixels(values):
    return bytes((values[i] << 4) | values[i+1] for i in range(0, len(values), 2))


def get_glyph(atlas, char):
    x, y = char % 16 * 12, char // 16 * 16
    return [atlas[(y+row)*192+x:(y+row)*192+x+12] for row in range(16)]


def glyph_metrics(glyph):
    columns = [x for x in range(12) if any(row[x] for row in glyph)]
    left, right = (min(columns), max(columns)+1) if columns else (0, 0)
    ink_width = min(right-left, 5)
    # Keep a normal space; narrow ink receives exactly one spacing column.
    advance = ink_width+1 if columns else 6
    return left, right, ink_width, advance


def resize_glyph(glyph, left_padding=0):
    """Resample inside one cell; padding never changes the advance width."""
    if left_padding not in (0, 1):
        raise ValueError("Unsupported glyph padding")
    left, right, target_width, advance = glyph_metrics(glyph)
    width = right-left
    result = []
    for row in glyph:
        out = [0]*12
        for dx in range(target_width):
            total = 0
            for sx in range(width):
                overlap = max(0, min((dx+1)*width, (sx+1)*target_width)
                              - max(dx*width, sx*target_width))
                total += row[left+sx]*overlap
            out[left_padding+dx] = (total+width//2)//width
        result.append(out)
    return result, advance


def png_gray(width, height, values):
    def chunk(kind, content):
        return (struct.pack(">I", len(content)) + kind + content +
                struct.pack(">I", zlib.crc32(kind + content)))
    scanlines = b"".join(b"\0" + bytes(values[y*width:(y+1)*width]) for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 0, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(scanlines)) + chunk(b"IEND", b""))


def make_halfwidth(rom, left_padding=0):
    files = by_vrom(rom)
    code = bytearray(files[CODE_VROM].extract(rom))
    font = bytearray(files[FONT_VROM].extract(rom))
    if code[WIDTH_TABLE:WIDTH_TABLE+256] != bytes(256):
        raise ValueError("Expected retail zero-filled font width table")
    if code[WIDTH_BRANCH:WIDTH_BRANCH+4] != bytes.fromhex("10A00007"):
        raise ValueError("Font width branch does not match retail ROM")
    if len(font) < ATLAS_OFFSET+ATLAS_SIZE:
        raise ValueError("Font DMA file too short")
    atlas = pixels(font[ATLAS_OFFSET:ATLAS_OFFSET+ATLAS_SIZE])
    original = atlas[:]
    advances = {}
    for char in sorted(LATIN):
        glyph = get_glyph(original, char)
        resized, advance = resize_glyph(glyph, left_padding)
        for y, out in enumerate(resized):
            start = (char//16*16+y)*192+char%16*12
            atlas[start:start+12] = out
        code[WIDTH_TABLE+char] = 12-advance
        advances[f"{char:02X}"] = advance
    code[WIDTH_BRANCH:WIDTH_BRANCH+4] = bytes(4)
    font[ATLAS_OFFSET:ATLAS_OFFSET+ATLAS_SIZE] = pack_pixels(atlas)
    for char in set(range(256))-LATIN:
        if get_glyph(atlas, char) != get_glyph(original, char):
            raise ValueError("Japanese/symbol glyph unexpectedly changed")
    return {CODE_VROM: bytes(code), FONT_VROM: bytes(font)}, {
        "latin_glyphs": len(LATIN), "advance_pixels_max": 6, "ink_columns_max": 5,
        "advance_by_glyph": advances,
        "left_padding_pixels": left_padding,
        "storage_cell": [12, 16], "japanese_glyphs_unchanged": True,
        "width_branch_ram": "0x80090294", "width_table_ram": "0x80106AF4"}
