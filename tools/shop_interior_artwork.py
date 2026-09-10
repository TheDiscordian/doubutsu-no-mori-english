"""Install the exact English GC shop-interior signs in existing native storage."""
import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, u32, verified_rom
from artwork_chain import rebuild
from building_artwork import palette_equivalent
from texture_preview import decode, native_range, png_rgba, rgba5551
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256, model_texture_shape, pack4, rgb5a3, untile

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '84852fae59184d6eb97d2ee94cbb44ea913680b22a31156287d5a604c048d3d3'
OWNERS = {
    0x13CD000: '9dc1f8217c19ea6c5062a6fb1091312ecb31d23262c431ccb40efe8785171d86',
    0x13D4000: 'ae146ca3c00d20f6463133e71dbd4bfbae47ef7723c56c75aa63469c8e681a5c',
    0x13DC000: 'fe949b9922ea12fe7ad4774f7ca0723c7418337fa752d120caf24fdf99596afd',
}


@dataclass(frozen=True)
class Sign:
    name: str
    owner: int
    texture: int
    palette: int
    command: int
    gc: int
    gc_palette: int
    gc_command: int
    width: int
    height: int
    symbol: str
    japanese: str
    english: str

    @property
    def size(self):
        return self.width*self.height//2


SIGNS = (
    Sign('second-floor', 0x13CD000, 0x4158, 0x2638, 0x1718, 0x9546A0, 0x952B80, 0x958A58,
         32, 64, 'rom_shop4_1_us_sign01_tex', '', '2nd Fl.'),
    Sign('information', 0x13CD000, 0x4558, 0x2678, 0x23B8, 0x954AA0, 0x952BA0, 0x958EC8,
         32, 16, 'rom_shop4_1_us_sign02_tex', '', 'Information'),
    Sign('welcome', 0x13CD000, 0x4658, 0x2698, 0x18A0, 0x954BA0, 0x952BC0, 0x958AD8,
         48, 64, 'rom_shop4_1_us_sign03_tex', 'いらっしゃいませ クリアランスセール',
         'WELCOME 9:00 AM 10:00 PM Clearance Sale'),
    Sign('raffle-thanks', 0x13D4000, 0x4130, 0x2690, 0x1780, 0x95AAA0, 0x958FE0, 0x95F448,
         32, 64, 'rom_shop4_2_us_sign01_tex', 'ありがとうございます。', 'THANK YOU!'),
    Sign('raffle-information', 0x13D4000, 0x4530, 0x26B0, 0x24B0, 0x95AEA0, 0x959000, 0x95F8F0,
         32, 16, 'rom_shop4_1_us_sign02_tex', '', 'Information'),
    Sign('raffle', 0x13D4000, 0x4630, 0x26D0, 0x1828, 0x95AFA0, 0x959020, 0x95F478,
         48, 64, 'rom_shop4_1_us_sign0_tex', 'ふくびき祭 ビッグチャンス!!',
         'RAFFLE-TICKET DAY BIG CHANCE!'),
    Sign('upstairs-thanks', 0x13DC000, 0x3330, 0x1F70, 0x1618, 0x960D80, 0x95F9C0, 0x964518,
         32, 64, 'rom_shop4_2_us_sign01_tex', 'ありがとうございます。', 'THANK YOU!'),
)


def donor_bindings(rel, symbols):
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Changed supplied English shop-interior source')
    required = {}
    for row in SIGNS:
        binding = f'{row.symbol} = .data:0x{row.gc:08X}; // type:object size:0x{row.size:X} '
        if symbols.decode().count(binding) != 1:
            raise ValueError('Missing exact shop-interior texture symbol')
        at = DATA_BASE+row.gc_command
        if (u32(rel, at-8) != 0xF08F4010
                or model_texture_shape(rel[at:at+8]) != (row.width, row.height, 2, 0)):
            raise ValueError('Changed donor sign palette or texture dimensions')
        required[row.gc_command-4] = row.gc_palette
        required[row.gc_command+4] = row.gc
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
            selected = address in required or any(row.gc_command < address < row.gc_command+40
                and u32(rel, DATA_BASE+address-4) >> 24 == 1 for row in SIGNS)
            if section != 5 or not selected or kind in (0, 201, 204):
                continue
            if ((module, kind, target_section) != (u32(rel, 0), 1, 5)
                    or address in found or u32(rel, DATA_BASE+address)
                    or (address in required and required[address] != target)):
                raise ValueError('Changed actual sign texture/palette/vertex fixup')
            found[address] = target
        else:
            raise ValueError('Unterminated shop-interior donor relocation stream')
    if not required.items() <= found.items() or len(found) != len(SIGNS)*3:
        raise ValueError('Missing or extra selected sign source fixup')
    return found


def native_reader(obj, row, rel, pointers):
    at = row.command
    expected = ((at-0x30, 0xFD100000, 0x06000000+row.palette),
                (at, 0xFD500000, 0x06000000+row.texture),
                (at+0x30, 0xF2000000, (row.width-1)*4 << 12 | (row.height-1)*4))
    for offset, a, b in expected:
        if obj[offset:offset+8] != struct.pack('>II', a, b):
            raise ValueError('Changed native sign material or dimensions')
    native_loads = [(i, a, b) for i in range(at+0x38, at+0x60, 8)
                    for a, b in [struct.unpack_from('>II', obj, i)] if a >> 24 == 1]
    donor_loads = [(i, a) for i in range(row.gc_command+8, row.gc_command+40, 8)
                   for a in [u32(rel, DATA_BASE+i)] if a >> 24 == 1]
    if len(native_loads) != 1 or len(donor_loads) != 1:
        raise ValueError('Ambiguous sign vertex load')
    _, a, b = native_loads[0]
    gc_at, gc_a = donor_loads[0]
    gc_vertex = pointers.get(gc_at+4, -1)
    nv = b & 0xFFFFFF
    if (a != 0x01004008 or gc_a != a or b >> 24 != 6 or nv+64 > row.command
            or not 0x957320 <= gc_vertex <= 0x9644A0-64):
        raise ValueError('Sign quad escapes its native or donor vertices')
    for index in range(4):
        n = obj[nv+index*16:nv+(index+1)*16]
        g = rel[DATA_BASE+gc_vertex+index*16:DATA_BASE+gc_vertex+(index+1)*16]
        if n[6:8] != b'\0\0' or g[6:8] != b'\0\1' or n[8:] != g[8:]:
            raise ValueError('Shop sign changes donor UV coordinates or lighting')
        if any(abs(5*y-4*x) > 80 for x, y in zip(struct.unpack('>3h', n[:6]), struct.unpack('>3h', g[:6]))):
            raise ValueError('Donor sign is not the corresponding native placement')
    return {'texture_command': f'{row.owner+at:08X}', 'vertices': f'{row.owner+nv:08X}',
            'vertex_count': 4, 'donor_vertices': f'{gc_vertex:08X}',
            'native_vertex_sha256': sha256(obj[nv:nv+64])}


def assets(native, rel, symbols):
    verified_rom(native)
    pointers = donor_bindings(rel, symbols)
    originals = {v: by_vrom(native)[v].extract(native) for v in OWNERS}
    if any(sha256(originals[v]) != digest for v, digest in OWNERS.items()):
        raise ValueError('Changed original shop-interior resource')
    changed = {v: bytearray(value) for v, value in originals.items()}
    rows = []
    for row in SIGNS:
        old = originals[row.owner]
        reader = native_reader(old, row, rel, pointers)
        donor = rel[DATA_BASE+row.gc:DATA_BASE+row.gc+row.size]
        samples = untile(donor, row.width, row.height, 4)
        palette = old[row.palette:row.palette+32]
        if row.name == 'welcome':
            donor_colour = rgb5a3(struct.unpack_from('>H', rel, DATA_BASE+row.gc_palette+18)[0])
            if donor_colour != bytes((156, 115, 165, 255)) or rgba5551(0x9BA9) != donor_colour:
                raise ValueError('Unexpected welcome-board colour conversion')
            # The second user of this palette is the unchanged board edge.
            uses = [i for i in range(0, len(old)-7, 8)
                    if old[i:i+8] == struct.pack('>II', 0xFD100000, 0x06000000+row.palette)]
            edge = old[0x4C58:0x4D58]
            if uses != [0x1870, 0x18F0] or 9 in {v for b in edge for v in (b >> 4, b & 15)}:
                raise ValueError('Welcome colour is shared by another visible material')
            palette = palette[:18]+struct.pack('>H', 0x9BA9)+palette[20:]
            if decode(edge, 16, 32, 'ci4', palette) != decode(edge, 16, 32, 'ci4', old[0x2698:0x26B8]):
                raise ValueError('Welcome palette changes the retained board edge')
            changed[row.owner][row.palette:row.palette+32] = palette
        palette_equivalent(palette, rel[DATA_BASE+row.gc_palette:DATA_BASE+row.gc_palette+32], set(samples))
        converted = pack4(samples)
        prior = old[row.texture:row.texture+row.size]
        if converted == prior:
            raise ValueError('English sign does not replace the selected native texture')
        changed[row.owner][row.texture:row.texture+row.size] = converted
        rows.append({'name': row.name, 'native_texture': f'{row.owner+row.texture:08X}',
                     'source_image_sha256': sha256(prior), 'output_image_sha256': sha256(converted),
                     'gc_texture': f'{row.gc:08X}', 'donor_image_sha256': sha256(donor),
                     'width': row.width, 'height': row.height, 'bytes': row.size, **reader})
    changed = {v: bytes(data) for v, data in changed.items()}
    return changed, {'version': 1, 'source_rel_sha256': REL_SHA256, 'source_symbols_sha256': SYMBOLS_SHA256,
        'source_owners': {f'{v:08X}': digest for v, digest in OWNERS.items()},
        'installed_owners': {f'{v:08X}': sha256(data) for v, data in changed.items()}, 'textures': rows,
        'donor_pointers': {f'{at:08X}': f'{target:08X}' for at, target in sorted(pointers.items())},
        'palette_change': {'vrom': '013CF6AA', 'bytes': 2, 'rgba': [156, 115, 165, 255],
                           'other_material_pixels_unchanged': True},
        'geometry_changed': False, 'commands_changed': False, 'code_changed': False,
        'allocations_changed': False, 'save_layout_changed': False,
        'status': 'Seven exact English GC sign textures installed; ordinary room appearance pending'}


def verify_installed(native, built, report, rel, symbols):
    changed, profile = assets(native, rel, symbols)
    if report.get('shop_interior_artwork') != profile:
        raise ValueError('Changed installed shop-interior profile')
    files = by_vrom(built)
    for v, data in changed.items():
        if v not in files or files[v].extract(built) != data:
            raise ValueError('English shop-interior texture, palette, or reader is not installed')
    return profile


def build(native, base, report, rel, symbols):
    if sha256(base) != BASE_SHA or report.get('output_sha256') != BASE_SHA:
        raise ValueError('Shop interiors require the complete shared-stall predecessor')
    changed, profile = assets(native, rel, symbols)
    files = by_vrom(base)
    if any(sha256(files[v].extract(base)) != digest for v, digest in OWNERS.items()):
        raise ValueError('Shop-interior source has unrelated edits')
    image, patch, result = rebuild(native, base, report, changed)
    result['shop_interior_artwork'] = profile
    result['release_status'] = 'English shop interiors and all prior artwork/text; ordinary acceptance pending'
    verify_installed(native, image, result, rel, symbols)
    return image, patch, result


def measure_text(ledger, native, built, report):
    installed = report.get('shop_interior_artwork')
    if installed:
        verify_installed(native, built, report,
            (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    for row in SIGNS:
        if not row.japanese:
            continue
        identity = 'art_shop_interior:'+row.name
        ledger.add_transcribed_artwork(identity, row.japanese, native_range(native, row.owner+row.texture, row.size))
        if installed:
            ledger.credit(identity, row.english.encode('ascii'), 'shop_interior_artwork')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', type=Path, default=ROOT/'build/stall-artwork-01')
    p.add_argument('--output', type=Path, default=ROOT/'build/shop-interior-artwork-01')
    a = p.parse_args()
    native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
    image, patch, report = build(native, (a.base/'animal-forest-halfwidth.z64').read_bytes(),
        json.loads((a.base/'build.json').read_text()), (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    a.output.mkdir(parents=True, exist_ok=False)
    outputs = {'animal-forest-halfwidth.z64': image, 'animal-forest-halfwidth.ups': patch,
               'build.json': (json.dumps(report, indent=2)+'\n').encode()}
    for row in SIGNS:
        outputs[row.name+'.png'] = png_rgba(row.width, row.height,
            decode(native_range(image, row.owner+row.texture, row.size), row.width, row.height, 'ci4',
                   native_range(image, row.owner+row.palette, 32)), 6)
    for name, value in outputs.items():
        with (a.output/name).open('xb') as target:
            target.write(value)
    print(json.dumps({'output': str(a.output), 'sha256': sha256(image), 'patch_sha256': sha256(patch)}))


if __name__ == '__main__':
    main()
