"""Explicit catalogue-four template glyphs; saved literal fields stay one byte."""

CATALOG = 4
SEMANTICS = 2
VROM = 0x030A0000
# Actual donor code identities, not all Unicode aliases in its character map.
ADVANCES = {0xD0:3,0xAE:6,0xA7:12,0xAB:12,0xBA:12,0x2A:6,0x3B:12,
            0x5C:12,0x60:6,0x7C:6,0xBF:12,0xF7:6,0x08:6,0x0A:6}
WIDTHS = {bytes((0x80,code)):width for code,width in ADVANCES.items()}
# Bound to tbl$1185 in the supplied English executable by extended_glyphs.
CAPITALS = {0x60:0x08,0x7C:0x0A}


def glyph(data, pos):
    if pos+1 >= len(data) or data[pos] != 0x80 or data[pos+1] not in ADVANCES:
        raise ValueError('Unknown or truncated mail glyph pair')
    return data[pos+1]
