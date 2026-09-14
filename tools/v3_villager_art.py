"""Convert verified GC cat/cub villager artwork to native N64 texture objects."""

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
}
PILOTS = {'punchy': (235, 'cat', 'cat_15'), 'cheri': (232, 'cbr', 'cbr_11')}


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


def convert_texture(palette, eyes, mouths, body, layout):
    """Store all expressions separately and initialise the native body atlas."""
    if len(eyes) != 8 or len(mouths) != 6 or any(len(t) != 256 for t in [*eyes, *mouths]):
        raise ValueError('Villager needs all eight eyes and six mouths at 32 by 16 CI4')
    if len(body) != 1024:
        raise ValueError('Unsupported donor body texture size')
    converted_eyes = [pack4(untile(t, 32, 16, 4)) for t in eyes]
    converted_mouths = [pack4(untile(t, 32, 16, 4)) for t in mouths]
    atlas, used, source_used = bytearray(2048), bytearray(2048), bytearray(1024)
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
        piece = pack4(untile(body[source:source + count], width, height, 4))
        install(target, tmem_rows(piece, width, height))
        source_used[source:source + count] = b'\x01' * count
        parts.append({'source_offset': source, 'tmem_offset': target, 'width': width, 'height': height})
    install(layout['eye'], tmem_rows(converted_eyes[0], 32, 16))
    install(layout['mouth'], tmem_rows(converted_mouths[0], 32, 16))
    # The native NPC constructor/draw path fills this from the villager's current
    # shirt. No unrelated character's shirt is copied into the new texture.
    install(layout['cloth'], bytes(512))
    if not all(used) or not all(source_used):
        raise ValueError('Unaccounted native atlas or donor body bytes')
    expressions = (converted_mouths + converted_eyes if layout.get('mouth_first')
                   else converted_eyes + converted_mouths)
    texture = native_palette(palette) + b''.join(expressions) + bytes(atlas)
    if len(texture) != NATIVE_TEXTURE_SIZE:
        raise ValueError('Wrong complete native villager texture size')
    return texture, parts


def bind_donor(rel, symbols, pointers, index, species, prefix):
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
    expected.update({48 + i * 4: f'{prefix}_mouth{i + 1}_TA_tex_txt' for i in range(6)})
    if {at - row_at for at in pointers if row_at <= at < row_at + DRAW_STRIDE} != set(expected):
        raise ValueError('Unexpected or missing villager draw pointer fields')
    for offset, name in expected.items():
        if pointers.get(row_at + offset) != symbol_span(symbols, name)[0]:
            raise ValueError(f'Donor identity does not bind {name}')
    if struct.unpack_from('>3I', row, 0x48) != (layout['eye'] // 8, layout['mouth'] // 8, layout['cloth'] // 8):
        raise ValueError('Donor TMEM placement differs from the native species layout')
    if struct.unpack_from('>2h', row, 0x68) != (-1, -1):
        raise ValueError('Villager accessory needs a separate geometry import')
    texture, parts = convert_texture(
        symbol_data(rel, symbols, prefix + '_pal'),
        [symbol_data(rel, symbols, f'{prefix}_eye{i}_TA_tex_txt') for i in range(1, 9)],
        [symbol_data(rel, symbols, f'{prefix}_mouth{i}_TA_tex_txt') for i in range(1, 7)],
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
    order = (*range(6, 14), *range(6)) if layout.get('mouth_first') else tuple(range(14))
    expected = (0x06000E20, 0x06000000, *(0x06000020 + i * 256 for i in order))
    if struct.unpack_from('>16I', row, 8) != expected or len(texture) != NATIVE_TEXTURE_SIZE:
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


def verify_shared_rig(rom, rel, symbols, species, native_row, metadata):
    model = by_vrom(rom)[int(metadata['native_model_vrom'], 16)].extract(rom)
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
            'vertex_transport_flags_normalised': flags_changed}


def build_art(rom, rel, symbols):
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
    for name, (index, species, prefix) in PILOTS.items():
        texture, row, parts = bind_donor(rel, symbols, pointers, index, species, prefix)
        native_row, _, metadata = native_species(rom, species)
        # Confirm the shared species' scale, talk type, and collision dimensions.
        # GC's expanded voice ID and accessory fields are deliberately not cast
        # into the smaller native record.
        if row[0x54:0x5C] != native_row[0x54:0x5C] or row[0x64:0x68] != native_row[0x60:0x64]:
            raise ValueError('Imported villager requires changed species geometry or collision')
        metadata['shared_rig'] = verify_shared_rig(rom, rel, symbols, species, native_row, metadata)
        file = f'{name}.n64tex.bin'
        artifacts[file] = texture
        report['villagers'].append({
            'id': f'{DONOR}/villager/{index:04X}', 'name': name.capitalize(),
            'donor_texture_prefix': prefix, 'donor_draw_record_sha256': sha256(row),
            'donor_voice_id': struct.unpack_from('>H', row, 0x62)[0],
            'native_texture_bytes': len(texture), 'texture_file': file,
            'texture_sha256': sha256(texture), 'body_parts': parts,
            'expression_frames': {'eye': 8, 'mouth': 6}, **metadata,
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
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a fresh artwork output directory')
    donor = read_donor(args.disc)
    artifacts, report = build_art(args.n64.read_bytes(), donor['rel'], args.symbols.read_bytes())
    args.output.mkdir(parents=True)
    for file, data in artifacts.items():
        (args.output / file).write_bytes(data)
    (args.output / 'art.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'output': str(args.output), 'converted_artworks': len(artifacts),
                      'bytes': sum(map(len, artifacts.values())),
                      'shared_bob_roundtrip': report['shared_bob_roundtrip'], 'installed': False}, indent=2))


if __name__ == '__main__':
    main()
