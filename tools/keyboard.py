"""Guarded English-first patches for the retail N64 text-entry overlays."""

import struct

from aflib import by_vrom, sha256
from font import ATLAS_OFFSET, ATLAS_SIZE, FONT_VROM, get_glyph, pixels, pack_pixels
from textcodec import encode

# Offsets in the decompressed keyboard object, not physical ROM addresses.
LABELS = (
    (0x1848, 48, 16, "I4", "Hira"),
    (0x19C8, 48, 16, "I4", "Kana"),
    (0x1B48, 48, 16, "I4", "Sym."),
    (0x1CC8, 48, 16, "I4", "ABC"),
    (0x1E48, 48, 16, "I4", "123"),
    (0x1FC8, 64, 16, "IA8", "Confirm"),
    (0x5448, 64, 16, "IA8", "Cursor"),
    (0x5848, 32, 16, "IA8", "Del"),
    (0x5A48, 64, 16, "IA8", "Done"),
    (0x15048, 64, 16, "IA8", "Case"),
)

EDITOR_VROM = 0x78CB80
LEDIT_VROM = 0x78BFB0
LABELS_VROM = 0xA40000
LEDIT_RAM = 0x80884340
SOURCE_HASHES = {
    EDITOR_VROM: "3def63100dd8c7910784eab8f14277bb99813be632fefd2e0afebcfddc9c3011",
    LEDIT_VROM: "86798d5b77c3f49bae23d90dc553cfaa7eaeab543fd4649979e9652706638987",
    LABELS_VROM: "0445bb9fdb4634ccfe31cce544695a98c471a77266d94455390868324bf87f17",
}
TITLES = ("Your name?", "Destination", "Catchphrase", "Say it!", "Request a song!")


def english_editor(data):
    """Set mode 3 and clear its scroll byte, without adding instructions."""
    data = bytearray(data)
    if data[0x76C:0x774] != bytes.fromhex("A0600004A0600005"):
        raise ValueError("Keyboard initialisation instructions do not match retail")
    # t9 is dead here and overwritten at +0x784. Big-endian halfword: mode=3,
    # scroll=0. The same two state bytes are written as by the original stores.
    data[0x76C:0x774] = bytes.fromhex("24190300A4790004")
    return bytes(data)


def english_titles(data, info, advances):
    data = bytearray(data)
    start, end = 0x9E0, 0xA18
    strings = [encode(title, info) for title in TITLES]
    if sum(map(len, strings)) > end-start:
        raise ValueError("English prompts exceed the existing string allocation")
    data[start:end] = bytes(end-start)
    offset = start
    for i, text in enumerate(strings):
        record = 0xA18+i*0x28
        old_x = struct.unpack_from(">f", data, record+8)[0]
        old_length = struct.unpack_from(">I", data, record+0x14)[0]
        width = sum(advances.get(f"{ch:02X}", 12) for ch in text)
        # Retail draws these prompts with 0.875 horizontal and vertical scale.
        struct.pack_into(">f", data, record+8, old_x+(old_length*12-width)*0.875/2)
        data[offset:offset+len(text)] = text
        # Existing R_MIPS_32 relocation records still apply to these pointers.
        struct.pack_into(">2I", data, record+0x10, LEDIT_RAM+offset, len(text))
        offset += len(text)
    if data[0x68C:0x690] != bytes.fromhex("24060003") or data[0xAF4:0xAF8] != bytes.fromhex("237B1C00"):
        raise ValueError("Town-name suffix does not match retail")
    data[0x68C:0x690] = bytes.fromhex("24060004")
    data[0xAF4:0xAF8] = encode("town", info)
    return bytes(data)


def label_pixels(atlas, text, width, height=16):
    """Centre unscaled retail glyphs, trimming only empty outer columns."""
    glyphs = []
    for ch in text:
        glyph = get_glyph(atlas, ord(ch))
        ink = [x for x in range(12) if any(row[x] for row in glyph)]
        left, right = (min(ink), max(ink)+1) if ink else (0, 4)
        glyphs.append([row[left:right] for row in glyph])
    span = sum(len(g[0]) for g in glyphs)+max(0, len(glyphs)-1)
    if span > width or height != 16:
        raise ValueError(f"Keyboard label does not fit: {text!r} ({span}/{width})")
    result = [0]*(width*height)
    x = (width-span)//2
    for glyph in glyphs:
        for y, row in enumerate(glyph):
            result[y*width+x:y*width+x+len(row)] = row
        x += len(glyph[0])+1
    return result


def make_english_keyboard(rom, info, advances, labels=True):
    files = by_vrom(rom)
    source = {v: files[v].extract(rom) for v in SOURCE_HASHES}
    for vrom, data in source.items():
        if sha256(data) != SOURCE_HASHES[vrom]:
            raise ValueError(f"Unexpected keyboard resource: {vrom:08X}")
    replacements = {
        EDITOR_VROM: english_editor(source[EDITOR_VROM]),
        LEDIT_VROM: english_titles(source[LEDIT_VROM], info, advances),
    }
    report = {"default_mode": "English", "mode_index": 3,
              "titles": list(TITLES), "name_limits": [6, 6, 4, 10, 10],
              "save_format_changed": False, "layout": "native N64 radial keyboard",
              "graphics_labels": []}
    if labels:
        font = files[FONT_VROM].extract(rom)
        atlas = pixels(font[ATLAS_OFFSET:ATLAS_OFFSET+ATLAS_SIZE])
        data = bytearray(source[LABELS_VROM])
        for offset, width, height, fmt, text in LABELS:
            rendered = label_pixels(atlas, text, width, height)
            texture = (pack_pixels(rendered) if fmt == "I4" else
                       bytes(0xF0 | value for value in rendered))
            if offset+len(texture) > len(data):
                raise ValueError("Keyboard texture outside its DMA file")
            data[offset:offset+len(texture)] = texture
            report["graphics_labels"].append({"offset": f"{offset:05X}", "text": text,
                                               "format": fmt, "size": [width, height]})
        replacements[LABELS_VROM] = bytes(data)
    for vrom, data in replacements.items():
        if len(data) != len(source[vrom]):
            raise ValueError("Keyboard patch changed overlay allocation size")
    return replacements, report


def main():
    import argparse
    from pathlib import Path
    from aflib import verified_rom
    from font import png_gray
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    files = by_vrom(rom)
    data = files[LABELS_VROM].extract(rom)
    font = files[FONT_VROM].extract(rom)
    atlas = pixels(font[ATLAS_OFFSET:ATLAS_OFFSET+ATLAS_SIZE])
    args.output.mkdir(parents=True, exist_ok=True)
    for offset, width, height, fmt, text in LABELS:
        size = width*height//2 if fmt == "I4" else width*height
        raw = data[offset:offset+size]
        # IA8: show white intensity multiplied by the alpha nibble on black.
        original = pixels(raw) if fmt == "I4" else [(b >> 4)*(b & 15)//15 for b in raw]
        new = label_pixels(atlas, text, width, height)
        comparison = []
        for y in range(height):
            comparison.extend(original[y*width:(y+1)*width]+[0]*8+new[y*width:(y+1)*width])
        (args.output/f"{offset:04X}-{text}.png").write_bytes(
            png_gray(width*2+8, height, [p*17 for p in comparison]))


if __name__ == "__main__":
    main()
