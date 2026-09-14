"""Convert verified GC villager artwork to matching native N64 texture objects."""

import argparse
import json
from pathlib import Path
import re
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32, verified_rom
from gc_names import rel_sections, symbol_data
from title_assets import pack4, rgb5a3, untile
from v3_import_catalog import DONOR, REL_SHA, ROOT, SYMBOLS_SHA, read_donor

DRAW_BASE = 0x31FE28
DRAW_SIZE = 0xA128
DRAW_STRIDE = 108
NATIVE_DRAW_VROM = 0xE05000
NATIVE_DRAW_STRIDE = 100
NATIVE_BODY_OFFSET = 0xE20
NATIVE_TEXTURE_SIZE = 0x1620
# GX body offset, N64 TMEM byte offset, width, height. Native eye/mouth/cloth
# offsets below are independently checked against the native draw records.
LAYOUTS = {
    'cat': {
        'template_index': 0, 'skeleton': 'cKF_bs_r_cat_1',
        'eye': 0, 'mouth': 0x100, 'cloth': 0x400,
        'parts': ((0, 0x200, 32, 32), (0x200, 0x600, 16, 16),
                  (0x280, 0x680, 16, 16), (0x300, 0x700, 16, 32)),
    },
    'cbr': {
        'template_index': 47, 'skeleton': 'cKF_bs_r_cbr_1',
        'mouth_first': True,
        'eye': 0x400, 'mouth': 0x40, 'cloth': 0x580,
        'parts': ((0, 0, 16, 8), (0x40, 0x140, 16, 8), (0x80, 0x180, 16, 8),
                  (0xC0, 0x1C0, 32, 32), (0x2C0, 0x3C0, 16, 8),
                  (0x300, 0x500, 16, 16), (0x380, 0x780, 16, 8), (0x3C0, 0x7C0, 16, 8)),
    },
    'pig': {
        'template_index': 151, 'skeleton': 'cKF_bs_r_pig_1',
        'eye': 0x200, 'mouth': 0x380, 'cloth': 0x500,
        'body_bytes': 896, 'zero_padding': ((0x780, 128),),
        'position_import_vertices': 67,
        'parts': ((0, 0, 32, 32), (0x200, 0x300, 16, 16),
                  (0x280, 0x480, 16, 16), (0x300, 0x700, 32, 8)),
    },
    'wol': {
        'template_index': 185, 'skeleton': 'cKF_bs_r_wol_1',
        'eye': 0x280, 'mouth': 0, 'cloth': 0x500, 'mouth_frames': 0,
        'zero_padding': ((0x700, 256),),
        'parts': ((0, 0, 16, 16), (0x80, 0x80, 32, 32),
                  (0x280, 0x380, 16, 16), (0x300, 0x400, 16, 16),
                  (0x380, 0x480, 16, 16)),
    },
    'duk': {
        'template_index': 70, 'skeleton': 'cKF_bs_r_duk_1', 'mouth_first': True,
        'eye': 0x380, 'mouth': 0x240, 'cloth': 0x500,
        'parts': ((0, 0, 16, 8), (0x40, 0x40, 32, 32), (0x240, 0x340, 16, 8),
                  (0x280, 0x480, 16, 16), (0x300, 0x700, 32, 8), (0x380, 0x780, 16, 16)),
    },
    'rbt': {
        'template_index': 161, 'skeleton': 'cKF_bs_r_rbt_1',
        'eye': 0x280, 'mouth': 0x380, 'cloth': 0x580,
        'parts': ((0, 0, 16, 16), (0x80, 0x80, 32, 32), (0x280, 0x480, 16, 16),
                  (0x300, 0x500, 16, 16), (0x380, 0x780, 16, 16)),
    },
    'squ': {
        'template_index': 174, 'skeleton': 'cKF_bs_r_squ_1',
        'eye': 0x240, 'mouth': 0x340, 'cloth': 0x500,
        'parts': ((0, 0, 16, 8), (0x40, 0x40, 32, 32), (0x240, 0x440, 16, 8),
                  (0x280, 0x480, 16, 16), (0x300, 0x700, 16, 32)),
    },
    'flg': {
        'template_index': 79, 'skeleton': 'cKF_bs_r_flg_1',
        'eye': 0, 'mouth': 0x100, 'cloth': 0x580,
        'parts': ((0, 0x200, 32, 8), (0x80, 0x280, 32, 40),
                  (0x300, 0x500, 16, 16), (0x380, 0x780, 16, 16)),
    },
    'lon': {
        'template_index': 122, 'skeleton': 'cKF_bs_r_lon_1', 'mouth_first': True,
        'eye': 0x400, 'mouth': 0x300, 'cloth': 0x5C0, 'body_bytes': 1216,
        'edge_rows': {0x300: (4, 'mirror'), 0x380: (4, 'mirror'), 0x440: (4, 'clamp')},
        'parts': ((0, 0, 16, 8), (0x40, 0x40, 16, 8), (0x80, 0x80, 32, 40),
                  (0x300, 0x500, 32, 8), (0x380, 0x540, 32, 8),
                  (0x400, 0x580, 16, 8), (0x440, 0x7C0, 32, 8)),
    },
    'pgn': {
        'template_index': 144, 'skeleton': 'cKF_bs_r_pgn_1', 'mouth_frames': 0,
        'eye': 0x180, 'mouth': 0, 'cloth': 0x480, 'body_bytes': 1408,
        'edge_rows': {0x180: (4, 'mirror'), 0x200: (4, 'clamp')},
        'parts': ((0, 0, 32, 8), (0x80, 0x80, 32, 16), (0x180, 0x280, 32, 8),
                  (0x200, 0x2C0, 32, 8), (0x280, 0x300, 32, 16), (0x380, 0x400, 16, 16),
                  (0x400, 0x680, 32, 8), (0x480, 0x700, 16, 16), (0x500, 0x780, 32, 8)),
    },
    'elp': {
        'template_index': 76, 'skeleton': 'cKF_bs_r_elp_1',
        'eye': 0x180, 'mouth': 0x580, 'cloth': 0x280,
        'parts': ((0, 0, 16, 32), (0x100, 0x100, 16, 16), (0x180, 0x480, 16, 32),
                  (0x280, 0x680, 16, 16), (0x300, 0x700, 16, 16), (0x380, 0x780, 16, 16)),
    },
    'brd': {
        'template_index': 27, 'skeleton': 'cKF_bs_r_brd_1', 'mouth_frames': 0,
        'eye': 0x40, 'mouth': 0, 'cloth': 0x480, 'body_bytes': 1280,
        'parts': ((0, 0, 16, 8), (0x40, 0x140, 32, 32), (0x240, 0x340, 32, 16),
                  (0x340, 0x440, 16, 8), (0x380, 0x680, 16, 24),
                  (0x440, 0x740, 16, 8), (0x480, 0x780, 32, 8)),
    },
    'mus': {
        'template_index': 125, 'skeleton': 'cKF_bs_r_mus_1',
        'eye': 0x300, 'mouth': 0x400, 'cloth': 0x5C0,
        'parts': ((0, 0, 16, 8), (0x40, 0x40, 16, 8), (0x80, 0x80, 16, 16),
                  (0x100, 0x100, 32, 32), (0x300, 0x500, 16, 16),
                  (0x380, 0x580, 16, 8), (0x3C0, 0x7C0, 16, 8)),
    },
    'hrs': {
        'template_index': 104, 'skeleton': 'cKF_bs_r_hrs_1', 'mouth_frames': 0,
        'eye': 0x140, 'mouth': 0, 'cloth': 0x5C0, 'body_bytes': 1408,
        'edge_rows': {0x1C0: (4, 'mirror'), 0x240: (28, 'clamp')},
        'parts': ((0, 0, 16, 16), (0x80, 0x80, 16, 24), (0x140, 0x240, 32, 8),
                  (0x1C0, 0x2C0, 32, 8), (0x240, 0x300, 32, 32),
                  (0x440, 0x4C0, 16, 8), (0x480, 0x500, 16, 16),
                  (0x500, 0x580, 16, 8), (0x540, 0x7C0, 16, 8)),
    },
    'chn': {
        'template_index': 39, 'skeleton': 'cKF_bs_r_chn_1', 'mouth_frames': 0,
        'eye': 0x80, 'mouth': 0, 'cloth': 0x4C0, 'body_bytes': 1216,
        'zero_padding': ((0x7C0, 64),),
        'parts': ((0, 0, 16, 8), (0x40, 0x40, 16, 8), (0x80, 0x180, 32, 32),
                  (0x280, 0x380, 32, 16), (0x380, 0x480, 16, 8),
                  (0x3C0, 0x6C0, 16, 24), (0x480, 0x780, 16, 8)),
    },
    'kal': {
        'template_index': 117, 'skeleton': 'cKF_bs_r_kal_1',
        'eye': 0, 'mouth': 0x100, 'cloth': 0x600, 'body_bytes': 1152,
        'edge_rows': {0: (4, 'mirror'), 0x80: (36, 'clamp')},
        'parts': ((0, 0x200, 32, 8), (0x80, 0x240, 32, 40),
                  (0x300, 0x480, 32, 16), (0x400, 0x580, 16, 16)),
    },
    'tig': {
        'template_index': 182, 'skeleton': 'cKF_bs_r_tig_1', 'mouth_frames': 0,
        'eye': 0x40, 'mouth': 0, 'cloth': 0x580, 'body_bytes': 1408,
        'edge_rows': {0x140: (4, 'mirror'), 0x1C0: (36, 'clamp')},
        'parts': ((0, 0, 16, 8), (0x40, 0x140, 32, 16), (0x140, 0x240, 32, 8),
                  (0x1C0, 0x280, 32, 40), (0x440, 0x4C0, 16, 8),
                  (0x480, 0x500, 16, 16), (0x500, 0x780, 16, 16)),
    },
    'gor': {
        'template_index': 97, 'skeleton': 'cKF_bs_r_gor_1',
        'eye': 0x280, 'mouth': 0x380, 'cloth': 0x4C0,
        'parts': ((0, 0, 16, 8), (0x40, 0x40, 16, 8), (0x80, 0x80, 32, 32),
                  (0x280, 0x480, 16, 8), (0x2C0, 0x6C0, 16, 16),
                  (0x340, 0x740, 16, 16), (0x3C0, 0x7C0, 16, 8)),
    },
}
PILOTS = {'punchy': (235, 'cat', 'cat_15'), 'cheri': (232, 'cbr', 'cbr_11')}
ARTWORK_VILLAGERS = {**PILOTS, 'pigleg': (233, 'pig', 'pig_11'),
                    'dobie': (224, 'wol', 'wol_6'),
    'maelle': (216, 'duk', 'duk_11'), 'ohare': (217, 'rbt', 'rbt_11'),
    'bliss': (218, 'squ', 'squ_11'), 'drift': (219, 'flg', 'flg_13'),
    'bud': (220, 'lon', 'lon_4'), 'boomer': (221, 'pgn', 'pgn_8'),
    'elina': (222, 'elp', 'elp_7'), 'flash': (223, 'brd', 'brd_11'),
    'flossie': (225, 'mus', 'mus_10'), 'annalise': (226, 'hrs', 'hrs_8'),
    'plucky': (227, 'chn', 'chn_9'), 'faith': (228, 'kal', 'kal_6'),
    'rowan': (230, 'tig', 'tig_4'), 'june': (231, 'cbr', 'cbr_10'),
    'ankha': (234, 'cat', 'cat_14'), 'yodel': (229, 'gor', 'gor_5')}


def texture_body_offset(layout):
    return 32 + (8 + layout.get('mouth_frames', 6))*256


def symbol_span(symbols, name):
    pattern = r'^' + re.escape(name) + r' = \.data:0x([0-9A-Fa-f]+);[^\n]* size:0x([0-9A-Fa-f]+) '
    rows = re.findall(pattern, symbols, re.M)
    if len(rows) != 1:
        raise ValueError(f'Missing or ambiguous donor data symbol: {name}')
    return tuple(int(value, 16) for value in rows[0])


def data_pointers(rel, start, size, *, expected_section=5):
    """Bind same-module data pointers, or explicitly requested text callbacks."""
    sections = rel_sections(rel)
    if (expected_section not in (1, 5) or len(sections) <= 5 or start < 0 or
            size <= 0 or start + size > sections[5][1]):
        raise ValueError('Requested donor pointer span exceeds the data section')
    module, table, table_size = u32(rel, 0), u32(rel, 0x28), u32(rel, 0x2C)
    if not table_size or table_size % 8 or table + table_size > len(rel):
        raise ValueError('Invalid donor relocation import table')
    imports = list(struct.iter_unpack('>II', rel[table:table + table_size]))
    starts = {entry[1] for entry in imports}
    if len(starts) != len(imports) or any(at % 4 or not 0 <= at < len(rel) for at in starts):
        raise ValueError('Invalid donor relocation stream bounds')
    result = {}
    for imported_module, first in imports:
        limit = min((at for at in starts if at > first), default=len(rel))
        section, address, ended = None, 0, False
        for at in range(first, limit - 7, 8):
            delta, kind, target_section, target = struct.unpack_from('>HBBI', rel, at)
            if kind == 203:
                ended = True
                break
            if kind == 202:
                if target_section >= len(sections):
                    raise ValueError('Invalid donor relocation source section')
                section, address = target_section, 0
                continue
            if section is None:
                raise ValueError('Donor relocation lacks a source section')
            address += delta
            if address > sections[section][1]:
                raise ValueError('Donor relocation exceeds its source section')
            if kind in (0, 201, 204) or section != 5 or not start <= address < start + size:
                continue
            if (kind != 1 or imported_module != module or target_section != expected_section
                    or address % 4 or address + 4 > start + size or target >= sections[expected_section][1]
                    or address in result or u32(rel, sections[5][0] + address) != 0):
                raise ValueError('Unsupported, external, or duplicate donor data pointer')
            result[address] = target
        if not ended:
            raise ValueError('Unterminated donor relocation stream')
    return result


def native_palette(data):
    if len(data) != 32:
        raise ValueError('Villager palette must have sixteen entries')
    words = []
    for (word,) in struct.iter_unpack('>H', data):
        red, green, blue, alpha = rgb5a3(word)
        if alpha not in (0, 255):
            raise ValueError('Partial-alpha donor palette requires a different renderer')
        words.append((red >> 3) << 11 | (green >> 3) << 6 | (blue >> 3) << 1 | (alpha == 255))
    return struct.pack('>16H', *words)


def tmem_rows(data, width, height):
    """N64 preloaded CI4 tiles swap their two 32-bit words on each odd row."""
    if width <= 0 or width % 16 or height <= 0 or len(data) != width * height // 2:
        raise ValueError('Invalid native TMEM tile dimensions')
    stride = width // 2
    return bytes(data[y * stride + (x ^ 4 if y % 2 else x)]
                 for y in range(height) for x in range(stride))


def native_body_piece(body, source, width, height, layout):
    """Remove only fully verified donor edge extensions, never unique pixels."""
    piece = pack4(untile(body[source:source+width*height//2], width, height, 4))
    native_height, mode = layout.get('edge_rows', {}).get(source, (height, None))
    if mode is not None:
        if (mode not in ('mirror', 'clamp') or not 0 < native_height < height
                or native_height % 4 or height-native_height > native_height):
            raise ValueError('Unsupported donor edge extension')
        stride = width//2
        extension = b''.join(piece[y*stride:(y+1)*stride] for y in (
            native_height-1-(i if mode == 'mirror' else 0)
            for i in range(height-native_height)))
        if piece[native_height*stride:] != extension:
            raise ValueError('Donor edge extension contains unique pixels')
        piece = piece[:native_height*stride]
    return tmem_rows(piece, width, native_height), native_height


def convert_texture(palette, eyes, mouths, body, layout):
    """Store all expressions separately and initialise the native body atlas."""
    mouth_frames = layout.get('mouth_frames', 6)
    if (mouth_frames not in (0, 6) or len(eyes) != 8 or len(mouths) != mouth_frames
            or any(len(t) != 256 for t in [*eyes, *mouths])):
        raise ValueError('Villager needs all eight eyes and its complete native mouth frames')
    if len(body) != layout.get('body_bytes', 1024):
        raise ValueError('Unsupported donor body texture size')
    converted_eyes = [pack4(untile(t, 32, 16, 4)) for t in eyes]
    converted_mouths = [pack4(untile(t, 32, 16, 4)) for t in mouths]
    atlas, used, source_used = bytearray(2048), bytearray(2048), bytearray(len(body))
    parts = []

    def install(at, data):
        if at < 0 or at + len(data) > len(atlas) or any(used[at:at + len(data)]):
            raise ValueError('Overlapping or out-of-bounds native texture piece')
        atlas[at:at + len(data)] = data
        used[at:at + len(data)] = b'\x01' * len(data)

    for source, target, width, height in layout['parts']:
        count = width * height // 2
        if source < 0 or source + count > len(body) or any(source_used[source:source + count]):
            raise ValueError('Overlapping or out-of-bounds donor texture piece')
        piece, native_height = native_body_piece(body, source, width, height, layout)
        install(target, piece)
        source_used[source:source + count] = b'\x01' * count
        parts.append({'source_offset': source, 'tmem_offset': target, 'width': width, 'height': height})
        if native_height != height:
            parts[-1].update(native_height=native_height,
                verified_edge_mode=layout['edge_rows'][source][1],
                verified_edge_bytes=width*(height-native_height)//2)
    install(layout['eye'], tmem_rows(converted_eyes[0], 32, 16))
    if converted_mouths:
        install(layout['mouth'], tmem_rows(converted_mouths[0], 32, 16))
    # The native NPC constructor/draw path fills this from the villager's current
    # shirt. No unrelated character's shirt is copied into the new texture.
    install(layout['cloth'], bytes(512))
    for at, count in layout.get('zero_padding', ()):
        install(at, bytes(count))
    if not all(used) or not all(source_used):
        raise ValueError('Unaccounted native atlas or donor body bytes')
    expressions = (converted_mouths + converted_eyes if layout.get('mouth_first')
                   else converted_eyes + converted_mouths)
    texture = native_palette(palette) + b''.join(expressions) + bytes(atlas)
    if len(texture) != texture_body_offset(layout) + 2048:
        raise ValueError('Wrong complete native villager texture size')
    return texture, parts


def bind_donor(rel, symbols, pointers, index, species, prefix, *, accessory=None):
    layout = LAYOUTS[species]
    if symbol_span(symbols, 'npc_draw_data_tbl') != (DRAW_BASE, DRAW_SIZE):
        raise ValueError('Changed donor draw table')
    table = symbol_data(rel, symbols, 'npc_draw_data_tbl')
    if not 0 <= index < 236:
        raise ValueError('Donor index is not a named villager')
    row_at = DRAW_BASE + index * DRAW_STRIDE
    row = table[index * DRAW_STRIDE:(index + 1) * DRAW_STRIDE]
    expected = {4: layout['skeleton'], 8: prefix + '_tmem_txt', 12: prefix + '_pal'}
    expected.update({16 + i * 4: f'{prefix}_eye{i + 1}_TA_tex_txt' for i in range(8)})
    mouth_frames = layout.get('mouth_frames', 6)
    expected.update({48 + i * 4: f'{prefix}_mouth{i + 1}_TA_tex_txt' for i in range(mouth_frames)})
    if mouth_frames == 0 and row[48:72] != bytes(24):
        raise ValueError('Mouthless species has unexpected mouth pointers')
    if {at - row_at for at in pointers if row_at <= at < row_at + DRAW_STRIDE} != set(expected):
        raise ValueError('Unexpected or missing villager draw pointer fields')
    for offset, name in expected.items():
        if pointers.get(row_at + offset) != symbol_span(symbols, name)[0]:
            raise ValueError(f'Donor identity does not bind {name}')
    if struct.unpack_from('>3I', row, 0x48) != (layout['eye'] // 8, layout['mouth'] // 8, layout['cloth'] // 8):
        raise ValueError('Donor TMEM placement differs from the native species layout')
    attachment = struct.unpack_from('>2h', row, 0x68)
    if accessory is not None:
        if (attachment != (accessory['tool'], accessory['joint'])
                or accessory['donor_villager_index'] != index):
            raise ValueError('Converted accessory does not bind this villager and joint')
    elif attachment != (-1, -1):
        raise ValueError('Villager accessory needs a separate geometry import')
    texture, parts = convert_texture(
        symbol_data(rel, symbols, prefix + '_pal'),
        [symbol_data(rel, symbols, f'{prefix}_eye{i}_TA_tex_txt') for i in range(1, 9)],
        [symbol_data(rel, symbols, f'{prefix}_mouth{i}_TA_tex_txt') for i in range(1, mouth_frames+1)],
        symbol_data(rel, symbols, prefix + '_tmem_txt'), layout)
    return texture, row, parts


def native_species(rom, species):
    layout, files = LAYOUTS[species], by_vrom(rom)
    table = files[NATIVE_DRAW_VROM].extract(rom)
    at = 8 + layout['template_index'] * NATIVE_DRAW_STRIDE
    row = table[at:at + NATIVE_DRAW_STRIDE]
    if struct.unpack_from('>3I', row, 0x48) != (layout['eye'] // 8, layout['mouth'] // 8, layout['cloth'] // 8):
        raise ValueError('Native species texture placement differs')
    model_bank, texture_bank = struct.unpack_from('>2H', row)
    code = files[CODE_VROM].extract(rom)

    def object_file(bank):
        start, end = struct.unpack_from('>2I', code, 0x8010DDD0 - CODE_RAM + bank * 8)
        if start not in files or end != files[start].vend:
            raise ValueError('Native object-table bounds disagree with DMA')
        return start, files[start].extract(rom)

    model_vrom, model = object_file(model_bank)
    texture_vrom, texture = object_file(texture_bank)
    mouth_frames = layout.get('mouth_frames', 6)
    order = (*range(6, 14), *range(6)) if layout.get('mouth_first') else tuple(range(8+mouth_frames))
    body_offset = texture_body_offset(layout)
    expressions = tuple(0x06000020 + i * 256 for i in order) + (0,)*(6-mouth_frames)
    expected = (0x06000000+body_offset, 0x06000000, *expressions)
    if struct.unpack_from('>16I', row, 8) != expected or len(texture) != body_offset+2048:
        raise ValueError('Native expression pointers or texture dimensions differ')
    skeleton = u32(row, 4)
    if skeleton >> 24 != 6 or (skeleton & 0xFFFFFF) + 8 > len(model):
        raise ValueError('Native skeleton is outside its model object')
    return row, texture, {
        'species': species, 'native_template_index': layout['template_index'],
        'native_model_bank': model_bank, 'native_model_vrom': f'{model_vrom:08X}',
        'native_model_sha256': sha256(model), 'native_skeleton': f'{skeleton:08X}',
        'native_reference_texture_vrom': f'{texture_vrom:08X}',
        'native_reference_texture_sha256': sha256(texture),
    }


def normalise_vertex_flags(vertices):
    if not vertices or len(vertices) % 16:
        raise ValueError('Incomplete donor vertex array')
    result, changed = bytearray(vertices), 0
    for at in range(0, len(vertices), 16):
        flag = struct.unpack_from('>H', vertices, at + 6)[0]
        if flag not in (0, 1):
            raise ValueError('Unknown donor vertex matrix flag')
        # GC emu64 uses MTX_SHARED/MTX_NONSHARED here. The retained N64 model
        # supplies native matrix commands and zero in this vertex field.
        changed += flag
        result[at + 6:at + 8] = b'\0\0'
    return bytes(result), changed


def verify_shared_rig(rom, rel, symbols, species, native_row, metadata, *, model=None):
    native_model = by_vrom(rom)[int(metadata['native_model_vrom'], 16)].extract(rom)
    if model is None:
        model = native_model
    vertices = symbol_data(rel, symbols, f'{species}_1_v')
    normalised, flags_changed = normalise_vertex_flags(vertices)
    if model[:len(vertices)] != normalised:
        raise ValueError('Shared species vertex positions, UVs, or normals differ')
    skeleton_name = LAYOUTS[species]['skeleton']
    at, size = symbol_span(symbols, skeleton_name)
    skeleton = symbol_data(rel, symbols, skeleton_name)
    native_at = u32(native_row, 4) & 0xFFFFFF
    if size != 8 or model[native_at:native_at + 4] != skeleton[:4]:
        raise ValueError('Shared species skeleton dimensions differ')
    joints_name = f'cKF_je_r_{species}_1_tbl'
    joint_at, joint_size = symbol_span(symbols, joints_name)
    if data_pointers(rel, at, size) != {at + 4: joint_at} or joint_size != skeleton[0] * 12:
        raise ValueError('Shared species skeleton does not bind its joint table')
    joints = symbol_data(rel, symbols, joints_name)
    native_pointer = u32(model, native_at + 4)
    native_joint_at = native_pointer & 0xFFFFFF
    if native_pointer >> 24 != 6 or native_joint_at + joint_size > len(model):
        raise ValueError('Native skeleton joints escape the model')
    pointers = data_pointers(rel, joint_at, joint_size)
    if any((address - joint_at) % 12 for address in pointers):
        raise ValueError('Unexpected pointer inside a species joint')
    for offset in range(0, joint_size, 12):
        native = model[native_joint_at + offset:native_joint_at + offset + 12]
        if native[4:] != joints[offset + 4:offset + 12]:
            raise ValueError('Shared joint children, flags, or position differ')
        pointer = u32(native, 0)
        if bool(pointer) != (joint_at + offset in pointers):
            raise ValueError('Shared species visible-joint pattern differs')
        if pointer and (pointer >> 24 != 6 or (pointer & 0xFFFFFF) >= len(model)):
            raise ValueError('Native joint display pointer escapes the model')
    return {'matched_vertices': len(vertices) // 16, 'matched_joints': skeleton[0],
            'shown_joints': skeleton[1], 'vertices_sha256': sha256(vertices),
            'native_vertices_sha256': sha256(normalised),
            **({'comparison_model': 'converted_native_model',
                'original_native_vertices_sha256': sha256(native_model[:len(vertices)])}
               if model != native_model else {}),
            'vertex_transport_flags_normalised': flags_changed}


def import_species_positions(rom, rel, symbols, species, metadata):
    """Retain native draw commands/rig while importing verified donor coordinates."""
    model = by_vrom(rom)[int(metadata['native_model_vrom'], 16)].extract(rom)
    vertices, _ = normalise_vertex_flags(symbol_data(rel, symbols, f'{species}_1_v'))
    count = LAYOUTS[species]['position_import_vertices']
    if len(vertices) > len(model):
        raise ValueError('Donor vertex array exceeds the native model')
    changed = []
    for at in range(0, len(vertices), 16):
        if model[at+6:at+16] != vertices[at+6:at+16]:
            raise ValueError('Position import changes UVs, normals, alpha, or vertex layout')
        if model[at:at+6] != vertices[at:at+6]:
            changed.append(at//16)
    if changed != list(range(count)):
        raise ValueError('Changed donor coordinate-import range')
    result = vertices + model[len(vertices):]
    return result, {'imported_position_vertices': count,
        'unchanged_position_vertices': len(vertices)//16-count,
        'native_commands_skeleton_and_uvs_retained': True,
        'native_model_sha256': sha256(model), 'converted_model_sha256': sha256(result)}


def build_art(rom, rel, symbols, *, villagers=None, accessory_directory=None, model_directory=None):
    rom = verified_rom(rom)
    if sha256(rel) != REL_SHA or sha256(symbols) != SYMBOLS_SHA:
        raise ValueError('Changed verified donor artwork source')
    symbols = symbols.decode('utf-8')
    pointers = data_pointers(rel, DRAW_BASE, 236 * DRAW_STRIDE)
    artifacts, report = {}, {'format': 'AFV3-VILLAGER-ART-1', 'villagers': []}
    # A shared-character round trip proves the tile placement and palette
    # conversion against real N64 art. Only the mutable shirt area is excluded.
    bob, _, _ = bind_donor(rel, symbols, pointers, 0, 'cat', 'cat_1')
    _, native_bob, _ = native_species(rom, 'cat')
    cloth = NATIVE_BODY_OFFSET + LAYOUTS['cat']['cloth']
    if bob[:cloth] + bob[cloth + 512:] != native_bob[:cloth] + native_bob[cloth + 512:]:
        raise ValueError('Shared Bob artwork does not reproduce the native object')
    report['shared_bob_roundtrip'] = {'matched_bytes': NATIVE_TEXTURE_SIZE - 512,
                                      'excluded_mutable_clothing_bytes': 512}
    selected = tuple(PILOTS) if villagers is None else tuple(villagers)
    if (not selected or len(set(selected)) != len(selected)
            or any(name not in ARTWORK_VILLAGERS for name in selected)):
        raise ValueError('Select distinct supported villager artwork identities')
    accessory_artifacts, accessories = {}, {}
    if accessory_directory is not None:
        from v3_accessory_art import load_objects
        accessory_artifacts, accessories = load_objects(Path(accessory_directory), rel, symbols.encode())
    for species, index, prefix in (('pig', 151, 'pig_1'), ('wol', 185, 'wol_1')):
        if not any(ARTWORK_VILLAGERS[name][1] == species for name in selected):
            continue
        layout = LAYOUTS[species]
        reference, _, _ = bind_donor(rel, symbols, pointers, index, species, prefix)
        _, native_reference, _ = native_species(rom, species)
        cloth = texture_body_offset(layout) + layout['cloth']
        if (reference[:cloth] + reference[cloth+512:]
                != native_reference[:cloth] + native_reference[cloth+512:]):
            raise ValueError(f'Shared {species} artwork does not reproduce the native object')
        report[f'shared_{species}_roundtrip'] = {'donor_index': index, 'matched_bytes': len(reference)-512,
            'excluded_mutable_clothing_bytes': 512,
            'verified_zero_padding_bytes': sum(count for _, count in layout.get('zero_padding', ()))}
    for name, (index, species, prefix) in ARTWORK_VILLAGERS.items():
        if name not in selected:
            continue
        accessory = accessories.get(index)
        texture, row, parts = bind_donor(rel, symbols, pointers, index, species, prefix,
                                         accessory=accessory)
        native_row, _, metadata = native_species(rom, species)
        # Confirm the shared species' scale, talk type, and collision dimensions.
        # GC's expanded voice ID and accessory fields are deliberately not cast
        # into the smaller native record.
        if row[0x54:0x5C] != native_row[0x54:0x5C] or row[0x64:0x68] != native_row[0x60:0x64]:
            raise ValueError('Imported villager requires changed species geometry or collision')
        converted_model, mesh_row = None, native_row
        if 'position_import_vertices' in LAYOUTS[species]:
            converted_model, geometry = import_species_positions(rom, rel, symbols, species, metadata)
            model_file = f'{name}.n64model.bin'
            artifacts[model_file] = converted_model
            metadata.update(model_file=model_file, model_sha256=sha256(converted_model),
                            model_bytes=len(converted_model), geometry_conversion=geometry,
                            target_model_bank=None)
        elif species == 'gor':
            if model_directory is None:
                raise ValueError('Yodel requires his complete converted gorilla model')
            from v3_gorilla_art import VERIFIED_ART_SHA, load_object
            converted_model, geometry = load_object(Path(model_directory), rom, rel, symbols.encode())
            model_file = geometry['model_file']
            artifacts[model_file] = converted_model
            mesh_row = bytearray(native_row)
            struct.pack_into('>I', mesh_row, 4, int(geometry['skeleton'], 16))
            metadata.update(model_file=model_file, model_sha256=sha256(converted_model),
                model_bytes=len(converted_model), converted_skeleton=geometry['skeleton'],
                target_model_bank=None, geometry_conversion={
                    'complete_donor_mesh_converted': True, 'source_manifest_sha256': VERIFIED_ART_SHA,
                    'source_vertices': geometry['vertices'], 'source_triangles': geometry['triangles'],
                    'model_buffer_bytes': geometry['model_buffer_bytes'],
                    'spare_model_bytes': geometry['spare_model_bytes']})
        metadata['shared_rig'] = verify_shared_rig(rom, rel, symbols, species, mesh_row, metadata,
                                                   model=converted_model)
        if accessory is not None:
            from v3_villager_mesh import verify_body_mesh
            metadata['shared_mesh'] = verify_body_mesh(rom, rel, symbols, species, mesh_row, metadata,
                                                       model=converted_model)
            metadata['accessory'] = accessory
            artifacts[accessory['object_file']] = accessory_artifacts[accessory['object_file']]
        file = f'{name}.n64tex.bin'
        artifacts[file] = texture
        report['villagers'].append({
            'id': f'{DONOR}/villager/{index:04X}', 'name': "O'Hare" if name == 'ohare' else name.capitalize(),
            'donor_texture_prefix': prefix, 'donor_draw_record_sha256': sha256(row),
            'donor_voice_id': struct.unpack_from('>H', row, 0x62)[0],
            'native_texture_bytes': len(texture), 'texture_file': file,
            'texture_sha256': sha256(texture), 'body_parts': parts,
            'expression_frames': {'eye': 8, 'mouth': LAYOUTS[species].get('mouth_frames', 6)}, **metadata,
            'status': 'artwork_converted_runtime_pending', 'selectable': False,
            'target_texture_bank': None,
        })
    report.update(source_sha256=sha256(rom), donor_rel_sha256=REL_SHA,
                  symbols_sha256=SYMBOLS_SHA, installed=False)
    return artifacts, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--n64', type=Path, default=ROOT / 'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--disc', type=Path, default=ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    parser.add_argument('--symbols', type=Path, default=ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--accessories', type=Path,
                        help='Verified v3_accessory_art output; required for accessory-bearing bodies')
    parser.add_argument('--models', type=Path,
                        help='Verified v3_gorilla_art output; required for Yodel')
    parser.add_argument('--all-supported', action='store_true',
                        help='Convert all twenty body components with their required dependencies')
    parser.add_argument('--villager', action='append', choices=tuple(ARTWORK_VILLAGERS),
                        help='Convert selected artwork components; default: existing two pilots')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a fresh artwork output directory')
    if args.all_supported and args.villager:
        parser.error('Use --all-supported or individual --villager selections')
    donor = read_donor(args.disc)
    artifacts, report = build_art(args.n64.read_bytes(), donor['rel'], args.symbols.read_bytes(),
        villagers=tuple(ARTWORK_VILLAGERS) if args.all_supported else args.villager,
        accessory_directory=args.accessories, model_directory=args.models)
    args.output.mkdir(parents=True)
    for file, data in artifacts.items():
        (args.output / file).write_bytes(data)
    (args.output / 'art.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'output': str(args.output), 'converted_artworks': len(report['villagers']),
                      'asset_files': len(artifacts),
                      'bytes': sum(map(len, artifacts.values())),
                      'shared_bob_roundtrip': report['shared_bob_roundtrip'], 'installed': False}, indent=2))


if __name__ == '__main__':
    main()
