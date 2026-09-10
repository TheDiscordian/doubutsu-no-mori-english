"""Install matching English GC police posters and postal mailbag artwork."""
import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, u32, verified_rom
from artwork_chain import rebuild
from building_artwork import palette_equivalent
from police_artwork import native_triangles
from stall_model_source import packed
from texture_preview import decode, native_range, png_rgba
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256, model_texture_shape, pack4, untile
from toolchain import profile_sha256

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '8f26fe26c1f1bc57fc462bb427d0a122f2aba072b5e6cbbbddb58c38573ea5a2'
BASE_REPORT_SHA = 'f2dec6683a78f94046d4eb540eff05dc0374ab84ae9b5b13db1eeef2790a4dd1'
OWNERS = {
    0x12AC000: 'ea811a32c19d45ef336ae80cbc898d6e5d5f73576a9beb4fa72eed66cc97ade8',
    0x12BB000: '30796b00c4fe4807863e136ddf75ad7a8b5322518ae11e7846a3c00346ad917d',
}
DONOR_POINTERS = {
    0x93E84C: 0x939AE0, 0x93E854: 0x93ACE0, 0x93E864: 0x93DEA0, 0x93E874: 0x93A9E0,
    0x615A9C: 0x610760, 0x615AA4: 0x612CE0, 0x615AB4: 0x6155B0,
}


@dataclass(frozen=True)
class Material:
    name: str
    owner: int
    texture: int
    palette: int
    command: int
    vertices: int
    vertex_count: int
    gc: int
    gc_palette: int
    gc_command: int
    gc_vertex_command: int
    gc_vertex_start: int
    gc_triangles: int
    width: int
    height: int
    symbol: str
    japanese: str
    english: str

    @property
    def size(self):
        return self.width*self.height//2


MATERIALS = (
    Material('wanted', 0x12AC000, 0x3968, 0x2A68, 0x1C10, 0x1180, 4,
             0x93A9E0, 0x939AE0, 0x93E870, 0x93E860, 4, 0x93E880,
             48, 32, 'rom_koban_us_pos1', 'このかおみたら110!', 'WANTED!'),
    Material('recruitment', 0x12AC000, 0x3C68, 0x2A68, 0x1B90, 0x1140, 4,
             0x93ACE0, 0x939AE0, 0x93E850, 0x93E860, 0, 0x93E868,
             32, 48, 'rom_koban_us_pos2', 'ケーカン求ム!', 'I want U!'),
    Material('mailbag', 0x12BB000, 0x5BD8, 0x2B18, 0x1C78, 0x1520, 10,
             0x612CE0, 0x610760, 0x615AA0, 0x615AB0, 0, 0x615AB8,
             48, 48, 'yubin_us_bag_tex', '〒', 'MAIL'),
)


def donor_bindings(rel, symbols):
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Changed supplied English civic-interior source')
    for row in MATERIALS:
        binding = f'{row.symbol} = .data:0x{row.gc:08X}; // type:object size:0x{row.size:X} '
        if symbols.decode().count(binding) != 1:
            raise ValueError('Missing exact civic-interior donor symbol')
    found = {}
    table, size = u32(rel, 0x28), u32(rel, 0x2C)
    for module, first in struct.iter_unpack('>II', rel[table:table+size]):
        section, address = None, 0
        for at in range(first, len(rel)-7, 8):
            delta, kind, target_section, target = struct.unpack_from('>HBBI', rel, at)
            if kind == 203:
                break
            if kind == 202:
                section, address = target_section, 0
                continue
            address += delta
            if section != 5 or address not in DONOR_POINTERS or kind in (0, 201, 204):
                continue
            if ((module, kind, target_section) != (u32(rel, 0), 1, 5)
                    or address in found or u32(rel, DATA_BASE+address)
                    or target != DONOR_POINTERS[address]):
                raise ValueError('Changed actual civic-interior donor fixup')
            found[address] = target
        else:
            raise ValueError('Unterminated civic-interior donor relocation stream')
    if found != DONOR_POINTERS:
        raise ValueError('Missing civic-interior donor pointer')
    return found


def reader(obj, row, rel, pointers):
    at = row.command
    expected = ((at-0x30, 0xFD100000, 0x06000000+row.palette),
                (at, 0xFD500000, 0x06000000+row.texture),
                (at+0x30, 0xF2000000, (row.width-1)*4 << 12 | (row.height-1)*4),
                (at+0x38, 0x01000000 | row.vertex_count << 12 | row.vertex_count << 1,
                 0x06000000+row.vertices))
    if any(obj[offset:offset+8] != struct.pack('>II', a, b) for offset, a, b in expected):
        raise ValueError('Changed native civic-interior material, dimensions, or vertices')
    gc_at = DATA_BASE+row.gc_command
    palette_at = 0x93E848 if row.owner == 0x12AC000 else 0x615A98
    gc_count = 8 if row.owner == 0x12AC000 else 10
    if (u32(rel, DATA_BASE+palette_at) != 0xF08F4010
            or pointers[palette_at+4] != row.gc_palette or pointers[row.gc_command+4] != row.gc
            or model_texture_shape(rel[gc_at:gc_at+8]) != (row.width, row.height, 2, 0)
            or rel[gc_at+8:gc_at+16] != struct.pack('>II', 0xD2F0F000, 0)
            or u32(rel, DATA_BASE+row.gc_vertex_command) != 0x01000000 | gc_count << 12 | gc_count << 1):
        raise ValueError('Changed donor civic-interior material or vertex load')
    gc_vertex = pointers[row.gc_vertex_command+4]+row.gc_vertex_start*16
    if row.gc_vertex_start+row.vertex_count > gc_count or row.vertices+row.vertex_count*16 > at:
        raise ValueError('Civic-interior vertices escape their bound arrays')
    for index in range(row.vertex_count):
        n = obj[row.vertices+index*16:row.vertices+(index+1)*16]
        g = rel[DATA_BASE+gc_vertex+index*16:DATA_BASE+gc_vertex+(index+1)*16]
        if n[6:8] != b'\0\0' or g[6:8] != b'\0\1' or n[8:] != g[8:]:
            raise ValueError('Civic-interior donor UV coordinates or lighting do not match')
        if any(abs(5*y-4*x) > 80 for x, y in zip(struct.unpack('>3h', n[:6]), struct.unpack('>3h', g[:6]))):
            raise ValueError('Donor artwork is not the corresponding native placement')
    triangle_count = 2 if row.vertex_count == 4 else 6
    triangles = []
    for offset in range(at+0x40, at+0x40+triangle_count*4, 8):
        triangles.extend(native_triangles(obj[offset:offset+8]))
    gc_size = (1+(max(0, triangle_count-3)+3)//4)*8
    gc_triangles = packed(rel[DATA_BASE+row.gc_triangles:DATA_BASE+row.gc_triangles+gc_size], gc_count)
    if triangles != [tuple(v-row.gc_vertex_start for v in t) for t in gc_triangles]:
        raise ValueError('Civic-interior donor and native triangle mappings differ')
    return {'texture_command': f'{row.owner+at:08X}', 'vertices': f'{row.owner+row.vertices:08X}',
            'vertex_count': row.vertex_count, 'donor_vertices': f'{gc_vertex:08X}',
            'triangle_count': triangle_count, 'native_vertex_sha256': sha256(
                obj[row.vertices:row.vertices+row.vertex_count*16])}


def assets(native, rel, symbols):
    verified_rom(native)
    pointers = donor_bindings(rel, symbols)
    originals = {v: by_vrom(native)[v].extract(native) for v in OWNERS}
    if any(sha256(originals[v]) != digest for v, digest in OWNERS.items()):
        raise ValueError('Changed original civic-interior room')
    changed, rows = {v: bytearray(value) for v, value in originals.items()}, []
    for row in MATERIALS:
        old = originals[row.owner]
        binding = reader(old, row, rel, pointers)
        donor = rel[DATA_BASE+row.gc:DATA_BASE+row.gc+row.size]
        samples = untile(donor, row.width, row.height, 4)
        palette_equivalent(old[row.palette:row.palette+32],
            rel[DATA_BASE+row.gc_palette:DATA_BASE+row.gc_palette+32], set(samples))
        converted = pack4(samples)
        prior = old[row.texture:row.texture+row.size]
        if len(converted) != row.size or converted == prior:
            raise ValueError('English civic image does not replace the selected native slot')
        changed[row.owner][row.texture:row.texture+row.size] = converted
        rows.append({'name': row.name, 'native_texture': f'{row.owner+row.texture:08X}',
                     'source_image_sha256': sha256(prior), 'output_image_sha256': sha256(converted),
                     'gc_texture': f'{row.gc:08X}', 'donor_image_sha256': sha256(donor),
                     'width': row.width, 'height': row.height, 'bytes': row.size, **binding})
    changed = {v: bytes(data) for v, data in changed.items()}
    return changed, {'version': 1, 'source_rel_sha256': REL_SHA256, 'source_symbols_sha256': SYMBOLS_SHA256,
        'source_owners': {f'{v:08X}': digest for v, digest in OWNERS.items()},
        'installed_owners': {f'{v:08X}': sha256(data) for v, data in changed.items()}, 'textures': rows,
        'donor_pointers': {f'{at:08X}': f'{target:08X}' for at, target in sorted(pointers.items())},
        'palettes_changed': False, 'geometry_changed': False, 'commands_changed': False,
        'code_changed': False, 'allocations_changed': False, 'save_layout_changed': False,
        'status': 'Three exact English GC civic-interior textures installed; ordinary room appearance pending'}


def verify_installed(native, built, report, rel, symbols):
    changed, profile = assets(native, rel, symbols)
    if report.get('civic_interior_artwork') != profile:
        raise ValueError('Changed installed civic-interior profile')
    files = by_vrom(built)
    for v, data in changed.items():
        if v not in files or files[v].extract(built) != data:
            raise ValueError('English civic-interior texture, palette, or reader is not installed')
    return profile


def build(native, base, report, rel, symbols):
    if (sha256(base) != BASE_SHA or report.get('output_sha256') != BASE_SHA
            or profile_sha256(report) != BASE_REPORT_SHA):
        raise ValueError('Civic interiors require the complete shop-interior predecessor')
    changed, profile = assets(native, rel, symbols)
    files = by_vrom(base)
    if any(sha256(files[v].extract(base)) != digest for v, digest in OWNERS.items()):
        raise ValueError('Civic-interior source has unrelated edits')
    image, patch, result = rebuild(native, base, report, changed)
    result['civic_interior_artwork'] = profile
    result['release_status'] = 'English civic interiors and all prior artwork/text; ordinary acceptance pending'
    verify_installed(native, image, result, rel, symbols)
    return image, patch, result


def measure_text(ledger, native, built, report):
    installed = report.get('civic_interior_artwork')
    if installed:
        verify_installed(native, built, report,
            (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    for row in MATERIALS:
        identity = 'art_civic_interior:'+row.name
        ledger.add_transcribed_artwork(identity, row.japanese, native_range(native, row.owner+row.texture, row.size))
        if installed:
            ledger.credit(identity, row.english.encode('ascii'), 'civic_interior_artwork')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', type=Path, default=ROOT/'build/shop-interior-artwork-01')
    p.add_argument('--output', type=Path, default=ROOT/'build/civic-interior-artwork-01')
    a = p.parse_args()
    native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
    image, patch, report = build(native, (a.base/'animal-forest-halfwidth.z64').read_bytes(),
        json.loads((a.base/'build.json').read_text()), (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    a.output.mkdir(parents=True, exist_ok=False)
    outputs = {'animal-forest-halfwidth.z64': image, 'animal-forest-halfwidth.ups': patch,
               'build.json': (json.dumps(report, indent=2)+'\n').encode()}
    for row in MATERIALS:
        outputs[row.name+'.png'] = png_rgba(row.width, row.height,
            decode(native_range(image, row.owner+row.texture, row.size), row.width, row.height, 'ci4',
                   native_range(image, row.owner+row.palette, 32)), 6)
    for name, value in outputs.items():
        with (a.output/name).open('xb') as target:
            target.write(value)
    print(json.dumps({'output': str(a.output), 'sha256': sha256(image), 'patch_sha256': sha256(patch)}))


if __name__ == '__main__':
    main()
