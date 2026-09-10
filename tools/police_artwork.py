"""Port English police artwork and topology inside the native seasonal resources."""
import argparse
from collections import Counter
import copy
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, verified_rom, replace_dma, make_ups, apply_ups, u32
from building_artwork import Texture, donor_texture_pointers, palette_equivalent, model_refs
from map_artwork import compile_commands
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256, model_texture_shape, untile, pack4
from nookington_sign import NEW_OBJECT, OBJECT, TABLE

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '58e02d5ccc8807ce6adffbcfa20502a10df0f7b2639147956ae1a14e3ca3de74'
ROWS = (
    Texture('obj_s_kouban_t1_tex_txt', 0xDAACF8, 0x571C40, 0xD5BF08, 0x501620, 0x572CC0, 0x470, 0x573208, 0x50),
    Texture('obj_s_kouban_t2_tex_txt', 0xDAB578, 0x5724C0, 0xD5BF08, 0x501620, 0x572CC0, 0x470, 0x5731B8, 0x50),
    Texture('obj_w_kouban_t1_tex_txt', 0xDACDC8, 0x573B20, 0xD5BF28, 0x501640, 0x574BA0, 0x470, 0x5750E8, 0x50),
    Texture('obj_w_kouban_t2_tex_txt', 0xDAD648, 0x5743A0, 0xD5BF28, 0x501640, 0x574BA0, 0x470, 0x575098, 0x50),
)
TRIANGLES = ((0,1,2),(0,3,1),(4,5,6),(4,6,7),(8,9,10),(8,11,9),
             (12,13,14),(13,15,14),(16,17,18),(17,12,18),(19,20,21),(19,21,22))
GC_TRIANGLES = bytes.fromhex('0A16629023008200735895A14941CC40AD27264651839ED0000000000005AB30')
LAYOUTS = (
    ('summer', 0x4BF88, 27, 0x4C2D0, 0x572CC0,
     (0,1,2,3,23,26,24,25,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22)),
    ('winter', 0x4E088, 24, 0x4E3A0, 0x574BA0,
     (0,1,2,3,20,23,21,22,8,9,10,11,11,12,9,13,14,15,8,16,17,18,19)),
)


def commands(out):
    return compile_commands(out, ROOT/'overlays/police/artwork.c', (('police', 56),))['police']


def expected_commands():
    out = bytearray()
    for left, right in zip(TRIANGLES[::2], TRIANGLES[1::2]):
        word = lambda t: t[0]<<17 | t[1]<<9 | t[2]<<1
        out.extend(struct.pack('>2I', 0x06000000|word(left), word(right)))
    return bytes(out)+bytes.fromhex('E000000000000000')


def native_triangles(data):
    result = []
    for a,b in struct.iter_unpack('>2I', data):
        if a == 0xE0000000 and b == 0: continue
        if a>>24 != 6: raise ValueError('Unexpected police triangle command')
        result.extend(tuple((word>>shift)&127 for shift in (17,9,1)) for word in (a,b))
    return result


def geometry(vertices, triangles):
    # Ignore UV/flags but retain positions and every native lighting byte.
    result = []
    for indices in triangles:
        keys = tuple(vertices[i][:6]+vertices[i][12:] for i in indices)
        result.append(min(keys, keys[1:]+keys[:1], keys[2:]+keys[:2]))
    return Counter(result)


def patch_assets(native, prior, rel, symbols, compiled):
    verified_rom(native)
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Unexpected English police source')
    if compiled != expected_commands():
        raise ValueError('Compiled police topology differs from native specification')
    original = by_vrom(native)[OBJECT].extract(native)
    if len(prior) != len(original) or prior[0x4BC88:0x4FE50] != original[0x4BC88:0x4FE50]:
        raise ValueError('Police source region has unrelated changes')
    pointers = donor_texture_pointers(rel, ROWS)
    result, changes, textures = bytearray(prior), [], []
    def install(at, value):
        if at < 0 or at+len(value) > len(prior):
            raise ValueError('Police replacement exceeds native storage')
        result[at:at+len(value)] = value
        changes.append({'object_offset': f'{at:06X}', 'bytes': len(value),
            'previous_sha256': sha256(prior[at:at+len(value)]), 'sha256': sha256(value)})
    palettes = by_vrom(native)[0xD5B000].extract(native)
    pal_table = by_vrom(native)[0xD5D000].extract(native)
    for at, expected in ((0xF4, 0x06000F08), (0x260, 0x06000F28)):
        if u32(pal_table, at) != expected:
            raise ValueError('Police seasonal palette reader changed')
    for index, row in enumerate(ROWS):
        model = rel[DATA_BASE+row.gc_model:DATA_BASE+row.gc_model+row.model_bytes]
        if model_texture_shape(model) != (128, 32, 2, 0):
            raise ValueError('Police donor texture shape changed')
        samples = untile(rel[DATA_BASE+row.gc:DATA_BASE+row.gc+2048], 128, 32, 4)
        palette_equivalent(palettes[row.native_palette-0xD5B000:row.native_palette-0xD5B000+32],
            rel[DATA_BASE+row.gc_palette:DATA_BASE+row.gc_palette+32], set(samples))
        if index%2 == 0:
            refs, uses = model_refs(prior, row,
                rel[DATA_BASE+row.gc_vertices:DATA_BASE+row.gc_vertices+row.vertex_bytes])
            if uses != 30 or len(refs) != 2:
                raise ValueError('Police wall/neon model bindings changed')
        elif model[40:72] != GC_TRIANGLES:
            raise ValueError('English police donor topology changed')
        converted = pack4(samples)
        install(row.native-OBJECT, converted)
        textures.append({'symbol': row.symbol, 'native_vrom': f'{row.native:08X}',
            'donor_data_offset': f'{row.gc:08X}', 'sha256': sha256(converted)})
    layouts = []
    for name, vertices, count, triangles, gc_vertices, mapping in LAYOUTS:
        old = [prior[vertices+i*16:vertices+(i+1)*16] for i in range(count)]
        donor = [rel[DATA_BASE+gc_vertices+i*16:DATA_BASE+gc_vertices+(i+1)*16] for i in range(48,71)]
        if (len(mapping) != 23 or count < len(mapping)
                or prior[triangles-8:triangles] != struct.pack('>2I',0x01000000|(count<<12)|(count<<1),0x06000000+vertices)
                or prior[triangles+56:triangles+64] != bytes.fromhex('DF00000000000000')):
            raise ValueError('Native police model boundaries changed')
        new = []
        for source, index in zip(donor, mapping):
            vertex = old[index]
            if source[:6] != vertex[:6]:
                raise ValueError('Police donor changes retained vertex position')
            new.append(vertex[:8]+source[8:12]+vertex[12:])
        old_triangles = native_triangles(prior[triangles:triangles+56])
        removed = [t for t in old_triangles if set(t) & {4,5,6,7}]
        retained = [t for t in old_triangles if not set(t) & {4,5,6,7}]
        if (len(removed) != 2 or any(not set(t) <= {4,5,6,7} for t in removed)
                or geometry(old, retained) != geometry(new, TRIANGLES)):
            raise ValueError('Police adaptation changes geometry beyond the removed notice sign')
        install(vertices, b''.join(new))
        install(triangles, compiled)
        layouts.append({'season': name, 'native_loaded_vertices': count, 'used_vertices': 23,
            'retained_triangles': len(retained), 'removed_notice_triangles': len(removed),
            'native_lighting_retained': True})
    return bytes(result), {'version': 1, 'source_rel_sha256': REL_SHA256, 'source_symbols_sha256': SYMBOLS_SHA256,
        'previous_object_sha256': sha256(prior), 'object_sha256': sha256(result),
        'textures': textures, 'changes': changes, 'layouts': layouts,
        'donor_texture_pointers': {f'{k:08X}':f'{v:08X}' for k,v in pointers.items()},
        'allocation_changed': False, 'actor_changed': False, 'collision_changed': False,
        'palettes_changed': False, 'status': 'English police artwork installed; ordinary scene/hardware acceptance pending'}


def build(native, base, report, rel, symbols, compiled):
    if sha256(base) != BASE_SHA or report.get('output_sha256') != BASE_SHA:
        raise ValueError('Police artwork requires the complete shop-sign/grid-label baseline')
    files = by_vrom(base)
    prior = files[OBJECT].extract(base)
    changed, profile = patch_assets(native, prior, rel, symbols, compiled)
    expanded = files[NEW_OBJECT].extract(base)
    if expanded[:len(prior)] != prior or sha256(expanded) != report['nookington_sign']['object_sha256']:
        raise ValueError('Current streamed building source differs from its Nookington profile')
    new_expanded = changed+expanded[len(prior):]
    table = files[TABLE].extract(base)
    count = 0
    for starts, ends in ((8,0xC0),(0x178,0x230)):
        for kind in range(46):
            start, end = u32(table,starts+kind*4), u32(table,ends+kind*4)
            offset, size = start-0x06000000+8, (end-start-8+15)&~15
            if not 0 <= offset <= len(expanded)-size or not 0 < size <= 0x2E00:
                raise ValueError('Police artwork changes native streamed bounds')
            if kind != 0x12 and new_expanded[offset:offset+size] != expanded[offset:offset+size]:
                raise ValueError('Police artwork changes another streamed building')
            count += 1
    profile.update(streamed_object_vrom=f'{NEW_OBJECT:08X}', streamed_object_sha256=sha256(new_expanded),
        building_ranges_checked=count, command_source_sha256=sha256((ROOT/'overlays/police/artwork.c').read_bytes()))
    moved = {int(k,16):int(v,16) for k,v in report['vrom_relocations'].items()}
    replacements = {int(v,16):files[moved.get(int(v,16),int(v,16))].extract(base) for v in report['replacement_files']}
    additions = {int(v,16):files[int(v,16)].extract(base) for v in report['added_files']}
    replacements[OBJECT] = changed
    additions[NEW_OBJECT] = new_expanded
    image = replace_dma(native,replacements,moved,additions)
    installed = by_vrom(image)
    if set(installed) != set(files) or len(image) != len(base):
        raise ValueError('Police artwork changes cartridge/resource sizes')
    for vrom,entry in files.items():
        expected = {OBJECT:changed,NEW_OBJECT:new_expanded}.get(vrom,entry.extract(base))
        actual = installed[vrom].extract(image)
        if vrom == 0x19D40: actual,expected = actual[:16],expected[:16]
        if actual != expected or installed[vrom].index != entry.index or installed[vrom].size != entry.size:
            raise ValueError(f'Police artwork loses earlier resource {vrom:08X}')
    patch = make_ups(native,image)
    if apply_ups(native,patch) != image: raise ValueError('Police artwork UPS reconstruction failed')
    result = copy.deepcopy(report)
    result.update(output_sha256=sha256(image),patch_sha256=sha256(patch),police_artwork=profile,
        release_status='English police/shop artwork and grid; ordinary scene/hardware acceptance pending')
    return image,patch,result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build/police-artwork-01')
    args = parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    baseline = ROOT/'build/shop-signs-01'
    image,patch,report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (baseline/'animal-forest-halfwidth.z64').read_bytes(),json.loads((baseline/'build.json').read_text()),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(),commands(args.output/'gbi'))
    for name,value in {'animal-forest-halfwidth.z64':image,'animal-forest-halfwidth.ups':patch,
        'build.json':(json.dumps(report,indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target: target.write(value)
    print(json.dumps({'output':str(args.output),'sha256':report['output_sha256'],
        'patch_sha256':report['patch_sha256'],'layouts':report['police_artwork']['layouts']}))


if __name__ == '__main__': main()
