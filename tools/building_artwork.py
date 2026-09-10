"""Install source-bound English shop textures without changing native models."""
import argparse
import copy
from dataclasses import dataclass
import json
from pathlib import Path
import re
import struct

from aflib import by_vrom, sha256, verified_rom, replace_dma, make_ups, apply_ups, u32
from gc_names import rel_sections
from package_v0 import HARDWARE_FIX_SHA256
from texture_preview import native_range, rgba5551, decode, png_rgba
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256, untile, pack4, rgb5a3, model_texture_shape

ROOT = Path(__file__).resolve().parents[1]
OBJECT = 0xD5E000
OBJECT_SHA = '8b0736724abe607a4939686db0d714874d6702072c155f731050049c5795cca2'
PALETTES_SHA = '374551b2ecdfb841eb3269e1ac2b6abdd92abf5033d67684b751393cb050bd6c'


@dataclass(frozen=True)
class Texture:
    symbol: str
    native: int
    gc: int
    native_palette: int
    gc_palette: int
    gc_vertices: int
    vertex_bytes: int
    gc_model: int
    model_bytes: int
    width: int = 128
    height: int = 32


TEXTURES = (
    Texture('obj_s_shop1_front_txt', 0xDB6AD8, 0x57DA60, 0xD5B948, 0x501060, 0x57F2E0, 0x320, 0x57F740, 0x48),
    Texture('obj_s_shop1_roof_txt', 0xDB72D8, 0x57E260, 0xD5B948, 0x501060, 0x57F2E0, 0x320, 0x57F6F8, 0x48),
    Texture('obj_s_shop1_side_txt', 0xDB7AD8, 0x57EA60, 0xD5B948, 0x501060, 0x57F2E0, 0x320, 0x57F6B0, 0x48),
    Texture('obj_w_shop1_front_txt', 0xDB8B18, 0x57F8A0, 0xD5B968, 0x501080, 0x581120, 0x320, 0x581580, 0x48),
    Texture('obj_w_shop1_roof_txt', 0xDB9318, 0x5800A0, 0xD5B968, 0x501080, 0x581120, 0x320, 0x581538, 0x48),
    Texture('obj_w_shop1_side_txt', 0xDB9B18, 0x5808A0, 0xD5B968, 0x501080, 0x581120, 0x320, 0x5814F0, 0x48),
    Texture('obj_s_shop2_t3_tex_txt', 0xDBAF78, 0x5816E0, 0xD5B988, 0x5010A0, 0x582F60, 0x600, 0x5835B0, 0x68, 64, 64),
    Texture('obj_s_shop2_t2_tex_txt', 0xDBC018, 0x582760, 0xD5B988, 0x5010A0, 0x582F60, 0x600, 0x583680, 0x88),
    Texture('obj_w_shop2_t3_tex_txt', 0xDBD458, 0x5838E0, 0xD5B9A8, 0x5010C0, 0x585160, 0x600, 0x5857B0, 0x68, 64, 64),
    Texture('obj_w_shop2_t2_tex_txt', 0xDBE4F8, 0x584960, 0xD5B9A8, 0x5010C0, 0x585160, 0x600, 0x585880, 0x88),
    Texture('obj_s_shop3_t3_tex_txt', 0xDC0A90, 0x586B60, 0xD5B9C8, 0x5010E0, 0x587360, 0x740, 0x587BD0, 0x90),
    Texture('obj_w_shop3_t3_tex_txt', 0xDC3040, 0x588E80, 0xD5B9E8, 0x501100, 0x589680, 0x740, 0x589EF0, 0x90),
)


def palette_equivalent(native, gc, used):
    if len(native) != 32 or len(gc) != 32 or any(not 0 <= i < 16 for i in used):
        raise ValueError('Invalid shop palette')
    n = [rgba5551(v) for v in struct.unpack('>16H', native)]
    g = [rgb5a3(v) for v in struct.unpack('>16H', gc)]
    for index in used:
        if n[index][3] != g[index][3] or (n[index][3] and n[index] != g[index]):
            raise ValueError(f'Shop palette changes visible index {index}')


def donor_texture_pointers(rel, rows=None):
    """Resolve the actual REL fixup for each selected model's texture command."""
    if sha256(rel) != REL_SHA256:
        raise ValueError('Unexpected GameCube artwork source')
    sections = rel_sections(rel)
    if sections[5][0] != DATA_BASE:
        raise ValueError('Unexpected GameCube data section')
    wanted = {}
    for row in TEXTURES if rows is None else rows:
        model = rel[DATA_BASE+row.gc_model:DATA_BASE+row.gc_model+row.model_bytes]
        positions = [row.gc_model+i*8+4 for i, (a, b) in enumerate(struct.iter_unpack('>2I', model))
                     if a >> 24 == 0xFD]
        if len(positions) != 1 or positions[0] in wanted:
            raise ValueError('Ambiguous donor texture command')
        wanted[positions[0]] = row.gc
    table, size = u32(rel, 0x28), u32(rel, 0x2C)
    imports = list(struct.iter_unpack('>2I', rel[table:table+size]))
    found = {}
    for module, first in imports:
        limit = min((start for _, start in imports if start > first), default=len(rel))
        section, address = None, 0
        for position in range(first, limit-7, 8):
            delta, kind, target_section, target = struct.unpack_from('>HBBI', rel, position)
            if kind == 203:
                break
            if kind == 202:
                section, address = target_section, 0
                continue
            address += delta
            if section != 5 or address not in wanted or kind in (0, 201, 204):
                continue
            if (kind != 1 or module != u32(rel, 0) or target_section != 5
                    or target != wanted[address] or address in found or u32(rel, DATA_BASE+address) != 0):
                raise ValueError('Donor model texture pointer does not bind its declared asset')
            found[address] = target
        else:
            raise ValueError('Unterminated donor relocation stream')
    if found != wanted:
        raise ValueError('Missing actual donor model texture fixup')
    return found


def model_refs(data, row, gc_vertices):
    """Check native load size/stride and all texture-consuming vertex coordinates."""
    target = struct.pack('>2I', 0xFD500000, 0x06000000+row.native-OBJECT)
    key = lambda value: value[:6]+value[8:12]
    vertices = {key(gc_vertices[i:i+16]) for i in range(0, len(gc_vertices), 16)}
    refs, total = [], 0
    for pos in range(0, len(data)-7, 8):
        if data[pos:pos+8] != target:
            continue
        commands = []
        for at in range(pos+8, min(len(data)-7, pos+1024), 8):
            a, b = struct.unpack_from('>2I', data, at)
            if a >> 24 in (0xFD, 0xDF):
                break
            commands.append((a, b))
        else:
            raise ValueError('Unterminated native shop texture commands')
        if (0xF3000000, 0x073FF000 | (0x100 if row.width == 128 else 0x200)) not in commands:
            raise ValueError('Unexpected native shop texture load size/stride')
        if not any(a == (0xF5400000 | (row.width//16 << 9)) for a, b in commands):
            raise ValueError('Unexpected native CI4 render stride')
        if not any(a == 0xF2000000 and b == (((row.width-1)*4 << 12) | ((row.height-1)*4))
                   for a, b in commands):
            raise ValueError('Unexpected native shop texture dimensions')
        count = 0
        for a, b in commands:
            if a >> 24 != 1:
                continue
            start, n = b & 0xFFFFFF, (a >> 12) & 255
            if b >> 24 != 6 or not n or start+n*16 > len(data):
                raise ValueError('Shop vertex load exceeds native object')
            for i in range(n):
                if key(data[start+i*16:start+(i+1)*16]) not in vertices:
                    raise ValueError('Native shop texture coordinates do not match the donor model')
            count += n
        if not count:
            raise ValueError('Shop texture reference has no vertices')
        refs.append(f'{OBJECT+pos:08X}')
        total += count
    if not refs:
        raise ValueError('Native model never loads shop texture')
    return refs, total


def extract(native, rel, symbols):
    verified_rom(native)
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Unexpected GameCube artwork source or symbol map')
    donor_pointers = donor_texture_pointers(rel)
    source = by_vrom(native)[OBJECT].extract(native)
    if sha256(source) != OBJECT_SHA or sha256(by_vrom(native)[0xD5B000].extract(native)) != PALETTES_SHA:
        raise ValueError('Unexpected native building object or palettes')
    rows, textures = [], {}
    for row in TEXTURES:
        binding = rf'^{row.symbol} = \.data:0x{row.gc:08X}; // type:object size:0x800 '
        if len(re.findall(binding, symbols.decode(), re.M)) != 1:
            raise ValueError('Missing scoped shop texture symbol')
        donor = rel[DATA_BASE+row.gc:DATA_BASE+row.gc+2048]
        model = rel[DATA_BASE+row.gc_model:DATA_BASE+row.gc_model+row.model_bytes]
        if model_texture_shape(model) != (row.width, row.height, 2, 0):
            raise ValueError('Donor shop model has different texture dimensions/format')
        samples = untile(donor, row.width, row.height, 4)
        converted = pack4(samples)
        palette_equivalent(native_range(native, row.native_palette, 32),
            rel[DATA_BASE+row.gc_palette:DATA_BASE+row.gc_palette+32], set(samples))
        refs, count = model_refs(source, row,
            rel[DATA_BASE+row.gc_vertices:DATA_BASE+row.gc_vertices+row.vertex_bytes])
        old = source[row.native-OBJECT:row.native-OBJECT+2048]
        if old == converted:
            raise ValueError('Shop replacement does not change its texture')
        textures[row.native] = converted
        rows.append({'symbol': row.symbol, 'native_vrom': f'{row.native:08X}',
            'gc_data_offset': f'{row.gc:08X}', 'bytes': 2048, 'width': row.width, 'height': row.height,
            'source_sha256': sha256(donor), 'native_sha256': sha256(old), 'output_sha256': sha256(converted),
            'changed_pixels': sum(a != b for a, b in zip(samples, (v for x in old for v in (x >> 4, x & 15)))),
            'native_texture_references': refs, 'matched_vertex_uses': count,
            'native_palette_vrom': f'{row.native_palette:08X}', 'gc_palette_offset': f'{row.gc_palette:08X}'})
    result = bytearray(source)
    for address, data in textures.items():
        result[address-OBJECT:address-OBJECT+len(data)] = data
    return bytes(result), textures, {'version': 1, 'source_rel_sha256': REL_SHA256,
        'symbols_sha256': SYMBOLS_SHA256, 'native_object_sha256': OBJECT_SHA,
        'object_vrom': f'{OBJECT:08X}', 'object_sha256': sha256(result), 'textures': rows,
        'donor_model_texture_pointers': {f'{k:08X}': f'{v:08X}' for k, v in donor_pointers.items()},
        'code_changed': False, 'geometry_changed': False, 'palettes_changed': False,
        'memory_requirement_mib': 4, 'status': 'Installed asset bindings; ordinary visual/hardware checks pending'}


def build(native, base, report, rel, symbols):
    if sha256(base) != HARDWARE_FIX_SHA256 or report.get('output_sha256') != HARDWARE_FIX_SHA256:
        raise ValueError('Shop artwork requires the complete hardware-fix baseline')
    changed, textures, profile = extract(native, rel, symbols)
    files = by_vrom(base)
    if sha256(files[OBJECT].extract(base)) != OBJECT_SHA:
        raise ValueError('Installed shop object already has unrelated changes')
    moved = {int(k, 16): int(v, 16) for k, v in report['vrom_relocations'].items()}
    replacements = {int(v, 16): files[moved.get(int(v, 16), int(v, 16))].extract(base)
                    for v in report['replacement_files']}
    additions = {int(v, 16): files[int(v, 16)].extract(base) for v in report['added_files']}
    if OBJECT in moved or OBJECT in additions:
        raise ValueError('Native building object ownership changed')
    replacements[OBJECT] = changed
    image = replace_dma(native, replacements, moved, additions)
    installed = by_vrom(image)
    if set(installed) != set(files) or len(image) != len(base):
        raise ValueError('Shop textures alter cartridge size or DMA identities')
    for vrom, entry in files.items():
        actual, expected = installed[vrom].extract(image), changed if vrom == OBJECT else entry.extract(base)
        if vrom == 0x19D40:
            actual, expected = actual[:16], expected[:16]
        if actual != expected or installed[vrom].index != entry.index:
            raise ValueError(f'Shop artwork loses prior resource {vrom:08X}')
    ups = make_ups(native, image)
    if apply_ups(native, ups) != image:
        raise ValueError('Shop artwork UPS reconstruction failed')
    result = copy.deepcopy(report)
    result.update(output_sha256=sha256(image), patch_sha256=sha256(ups),
        replacement_files=[f'{v:08X}' for v in sorted(replacements)], building_artwork=profile,
        release_status='English shop artwork candidate; ordinary visual/hardware checks pending')
    return image, ups, result, textures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/shop-artwork-01')
    args = parser.parse_args()
    native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
    baseline = ROOT/'build/v0-hardware-fixes-02'
    image, ups, report, textures = build(native, (baseline/'animal-forest-halfwidth.z64').read_bytes(),
        json.loads((baseline/'build.json').read_text()),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    args.output.mkdir(parents=True, exist_ok=False)
    outputs = {'animal-forest-halfwidth.z64': image, 'animal-forest-halfwidth.ups': ups,
        'build.json': (json.dumps(report, indent=2)+'\n').encode()}
    for row in TEXTURES:
        outputs[row.symbol+'.png'] = png_rgba(row.width, row.height,
            decode(textures[row.native], row.width, row.height, 'ci4', native_range(native, row.native_palette, 32)), 4)
    for name, value in outputs.items():
        with (args.output/name).open('xb') as target:
            target.write(value)
    print(json.dumps({'output': str(args.output), 'sha256': report['output_sha256'],
        'textures': len(textures), 'changed_pixels': sum(r['changed_pixels'] for r in report['building_artwork']['textures']),
        'matched_vertex_uses': sum(r['matched_vertex_uses'] for r in report['building_artwork']['textures'])}))


if __name__ == '__main__':
    main()
