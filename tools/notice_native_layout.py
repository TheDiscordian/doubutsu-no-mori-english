"""Independent expected native notice rows, retaining every manual space/break."""

from mail_reader_smoke import glyph_advances


def rows(text, widths):
    result = []
    start = position = width = 0
    while position < len(text):
        if text[position] == 0xCD:
            result.append((start, text[start:position], width))
            position += 1
            start, width = position, 0
            continue
        size = 2 if text[position] == 0x80 else 1
        if position+size > len(text): raise ValueError('Incomplete expected notice glyph')
        advance = glyph_advances(text[position:position+size], widths)[0]
        if width+advance > 192:
            result.append((start, text[start:position], width))
            start, width = position, 0
        width += advance
        position += size
    if start < len(text): result.append((start, text[start:], width))
    return result
