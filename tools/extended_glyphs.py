#!/usr/bin/env python3
"""Extract exact supplied English glyphs into a separate native I4 resource."""

import argparse
import json
from pathlib import Path
import struct

from aflib import sha256
from font import get_glyph, pack_pixels, pixels, resize_glyph
from gc_names import symbol_data
from gc_text import decoder_tables

REL_SHA256 = '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837'
SYMBOLS_SHA256 = 'e5267b989d235655c51885bd2a660b3e8c2cbd46d60b2b3c46166d337c7bca87'
FONT_SHA256 = '54965b012354699b29d26683fa0c496c21ef7178d35299b67a8fe55c50174fc4'
# IDs retain the supplied English character codes. The prefix distinguishes
# them from every existing one-byte native character. Unlisted tags stay unknown.
GLYPHS = ((';', 0xD0, True), ('/', 0xAE, True), ('☀', 0xA7, False),
          ('☃', 0xAB, False), ('💀', 0xBA, False))
MAIL_GLYPHS = GLYPHS+(('~',0x2A,True),('🌢',0x3B,False),('💢',0x5C,False),
                     ('ç',0x60,True),('é',0x7C,True),('😃',0xBF,False),('÷',0xF7,True),
                     ('Ç',0x08,True),('É',0x0A,True))
CODEPOINTS = {code: text for text, code, _ in GLYPHS}
ENCODINGS = {text: bytes((0x80, code)) for text, code, _ in GLYPHS}
HEADER = struct.pack('>8I', 0x41464758, 1, 192, 16, len(GLYPHS), 64, 1536, 0)
RESOURCE_BYTES = 1600


def untile_i4(data, width, height):
    """Decode GameCube 8-by-8 I4 blocks into row-major four-bit pixels."""
    if (type(width) is not int or type(height) is not int
            or width <= 0 or height <= 0 or width % 8 or height % 8
            or len(data) != width*height//2):
        raise ValueError('Invalid complete GameCube I4 texture dimensions')
    packed = pixels(data)
    result = [0]*(width*height)
    for block_y in range(height//8):
        for block_x in range(width//8):
            start = (block_y*(width//8)+block_x)*64
            for y in range(8):
                at = (block_y*8+y)*width+block_x*8
                result[at:at+8] = packed[start+y*8:start+y*8+8]
    return result


def source_atlas(rel, symbols, decoder, *, mail=False):
    if sha256(rel) != REL_SHA256 or sha256(symbols.encode()) != SYMBOLS_SHA256:
        raise ValueError('Unexpected English executable or symbol reference')
    raw = symbol_data(rel, symbols, 'FONT_nes_tex_font1')
    if len(raw) != 0x6000 or sha256(raw) != FONT_SHA256:
        raise ValueError('Unexpected complete English font resource')
    table = decoder_tables(decoder)['CHAR_MAP']
    if any(table[code] != text for text, code, _ in (MAIL_GLYPHS if mail else GLYPHS)):
        raise ValueError('English character names differ from their exact source glyphs')
    if mail:
        capitals = symbol_data(rel,symbols,'tbl$1185')
        if len(capitals)!=112 or sha256(capitals)!='fe8c41e0392639364d87bbcb9c0eda5a9991304c76cf49319a4a5d293bd2c897':
            raise ValueError('Changed supplied uppercase glyph table')
        pairs = dict(zip(capitals[::2],capitals[1::2]))
        if (pairs.get(0x60),pairs.get(0x7C)) != (0x08,0x0A):
            raise ValueError('Changed supplied accented-letter capitalization')
    return untile_i4(raw, 192, 256)


def resource(atlas, *, mail=False):
    if len(atlas) != 192*256 or any(type(p) is not int or not 0 <= p <= 15 for p in atlas):
        raise ValueError('Invalid complete decoded English I4 font')
    result = [0]*(192*16)
    widths, rows = [], []
    glyphs = MAIL_GLYPHS if mail else GLYPHS
    for slot, (text, code, halfwidth) in enumerate(glyphs):
        original = get_glyph(atlas, code)
        glyph, advance = resize_glyph(original) if halfwidth else (original, 12)
        for y, row in enumerate(glyph):
            result[y*192+slot*12:y*192+slot*12+12] = row
        widths.append(advance)
        rows.append({'character': text, 'source_code': f'{code:02X}', 'encoding': f'80{code:02X}',
                     'slot': slot, 'advance': advance,
                     'source_glyph_sha256': sha256(pack_pixels([p for row in original for p in row])),
                     'native_glyph_sha256': sha256(pack_pixels([p for row in glyph for p in row])),
                     'conversion': 'approved proportional resampling' if halfwidth else 'unchanged source pixels'})
    codes = bytes(code for _, code, _ in glyphs).ljust(16, b'\0')
    header = struct.pack('>8I',0x41464758,1,192,16,len(glyphs),64,1536,0)
    data = header+codes+bytes(widths).ljust(16, b'\0')+pack_pixels(result)
    validate_resource(data,mail=mail)
    return data, rows


def validate_resource(data, *, mail=False):
    glyphs = MAIL_GLYPHS if mail else GLYPHS
    header = struct.pack('>8I',0x41464758,1,192,16,len(glyphs),64,1536,0)
    if len(data) != RESOURCE_BYTES or data[:32] != header:
        raise ValueError('Invalid extended-glyph header or complete size')
    if (data[32:48] != bytes(code for _, code, _ in glyphs).ljust(16, b'\0')
            or any(data[48+len(glyphs):64])):
        raise ValueError('Changed extended-glyph mapping or reserved width slots')
    for index, (_, _, halfwidth) in enumerate(glyphs):
        width = data[48+index]
        if not (1 <= width <= 6 if halfwidth else width == 12):
            raise ValueError('Invalid extended-glyph advance')
    atlas = pixels(data[64:])
    for y in range(16):
        if any(atlas[y*192+12*len(glyphs):(y+1)*192]):
            raise ValueError('Extended glyph pixels exceed the registered slots')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rel', type=Path, default=Path('build/gamecube/files/foresta.rel.szs.decoded'))
    parser.add_argument('--decomp', type=Path, default=Path('local/ac-decomp'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mail',action='store_true',help='Include all missing mail glyphs and their uppercase forms')
    args = parser.parse_args()
    symbols = (args.decomp/'config/GAFE01_00/foresta/symbols.txt').read_text()
    data, glyphs = resource(source_atlas(args.rel.read_bytes(), symbols, args.decomp/'tools/msg_tool.py',mail=args.mail),mail=args.mail)
    report = {'schema': 1, 'bytes': len(data), 'resource_sha256': sha256(data),
              'reference_executable_sha256': REL_SHA256, 'reference_font_sha256': FONT_SHA256,
              'reference_symbols_sha256': SYMBOLS_SHA256, 'glyphs': glyphs,
              'native_atlas_modified': False, 'installed': False,
              'mail_glyphs':args.mail,
              'scope': 'Separate source-verified glyph resource; renderer, parser, caller, and save acceptance required'}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'glyphs.bin').write_bytes(data)
    (args.output/'glyphs.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
