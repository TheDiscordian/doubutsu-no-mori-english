"""Correct reported catalogue and repayment labels on the complete RC4 build."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, make_ups, sha256, verified_rom
from apply_translation import write_new
from artwork_matches import converted, data_pointers
from catalogue_names import Image, metadata
from font import WIDTH_TABLE
from npc_mail_show import relocate_verified_data
from rebuild_v1 import checked_output, source_state
from texture_preview import decode, png_rgba
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256, model_texture_shape
from title_start_fix import reconstruct
from toolchain import IMAGE

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '5930435f588947df35313ae9cc2ea301af9fc7e68d59a7d8e13a48741d4f3067'
CAT, CAT_REL, RAM, START = 0x3970000, 0x3980000, 0x808A6100, 53584
PARENT, PARENT_AT, ASSET, REPAY, REPAY_REL, REPAY_RAM = 0x7749C0, 0x2C90, 0xB2A000, 0x79B120, 0x79BF10, 0x808979C0
HASHES = {
    CAT: '7cbd4bbfd5699c28ef7bdded5af5c3125d0a1933192ecf366cab461d7f5ee972',
    CAT_REL: 'e828349a5dd1b46b2df4673af1d9d3f0d1938af332c4ab1783cdcc7179831122',
    PARENT: '8330dab471aa6cc6c294c846908b55367add552e2723642b29b9130a4063e121',
    ASSET: '86ceb1eee7f2fd023e8cbe1a0987483733ce1add3429cacdd77ac145045ecba0',
    REPAY: 'c399ed1dd7f5c8f3552993294f234b2190889448f5ceb76dc3861f8694e28d63',
    REPAY_REL: 'b0c5b4c56ce2844910a0d9a75428ce35912b00233fae22bd23144d04cb62d1ba',
}
SOURCES = ('tools/rc4_menu_labels.py', 'overlays/rc4_menu_labels/catalogue.s',
           'overlays/rc4_menu_labels/catalogue.ld')
TEXT = ((0x7E158, 'not_sell', b'Not for Sale'),
        (0x81028, 'kingaku_str$537', b'Your Loan'), (0x81034, 'kettei_str$538', b'OK'))
REPAY_SECTIONS = (3440, 112, 16, 48, 59)


def source_hashes():
    return {name: sha256((ROOT/name).read_bytes()) for name in SOURCES}


def references(rel, symbols):
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Changed supplied menu-label source')
    for at, name, text in TEXT:
        symbol = f'{name} = .data:0x{at:08X}; // type:object size:0x{len(text):X} '.encode()
        if symbols.count(symbol) != 1 or rel[DATA_BASE+at:DATA_BASE+at+len(text)] != text:
            raise ValueError('Missing complete English menu wording')
    if symbols.count(b'clg_win_beruT_model = .data:0x003EF490; // type:object size:0x40 ') != 1:
        raise ValueError('Changed catalogue currency model')
    pointers = data_pointers(rel)
    if (pointers.get(0x3EF4AC) != 0x3E88A0
            or model_texture_shape(rel[DATA_BASE+0x3EF4A8:DATA_BASE+0x3EF4B0]) != (32, 16, 4, 0)):
        raise ValueError('Changed actual catalogue currency image binding')
    return converted(rel[DATA_BASE+0x3E88A0:DATA_BASE+0x3E89A0], 32, 16, 'i4', 4)


def compile_adapter(out):
    out.mkdir(parents=True, exist_ok=False)
    docker = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{ROOT}:/source:ro', '-v', f'{out.resolve()}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        return subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                              check=True, capture_output=True, text=True, timeout=60).stdout
    run('as', '-EB', '-mabi=32', '-march=vr4300', '-o', 'adapter.o',
        '/source/overlays/rc4_menu_labels/catalogue.s')
    run('ld', '-EB', '--emit-relocs', '-T', '/source/overlays/rc4_menu_labels/catalogue.ld',
        '-o', 'adapter.elf', 'adapter.o')
    if run('nm', '--undefined-only', 'adapter.elf').strip():
        raise ValueError('Unresolved catalogue adapter symbol')
    run('objcopy', '-O', 'binary', '-j', '.text', 'adapter.elf', 'adapter.bin')
    write_new(out/'adapter.asm', run('objdump', '-d', 'adapter.elf').encode())
    write_new(out/'relocations.txt', run('readelf', '-rW', 'adapter.elf').encode())
    return (out/'adapter.bin').read_bytes()


def checked_adapter(blob):
    label = RAM+START+84
    words = (0x8FAE0040, 0x15C00011, 0, 0x3C050000 | ((label+0x8000) >> 16),
             0x24A50000 | (label & 65535), 0x2406000C, 0x44872000, 0x3C0E4110,
             0x448E3000, 0x46062101, 0x44072000, 0xC7A40010, 0x3C0E3F80,
             0x448E3000, 0x46062101, 0xE7A40010, 0x3C0E3F60, 0xAFAE002C,
             0xAFAE0030, 0x080243A6, 0)
    expected = struct.pack('>21I', *words)+TEXT[0][2]
    if blob != expected or len(blob) != 96:
        raise ValueError('Assembled adapter differs from the bounded native calling contract')


def patch_catalogue(old, reloc, parent, blob):
    if any(sha256(value) != HASHES[v] for v, value in ((CAT, old), (CAT_REL, reloc), (PARENT, parent))):
        raise ValueError('Changed complete catalogue source or parent')
    checked_adapter(blob)
    if (struct.unpack_from('>5I', reloc) != (START, 0, 0, 0, 149)
            or parent[PARENT_AT:PARENT_AT+32] != metadata()
            or sha256(old[0x2118:0x225C]) != '02dc4c417f3ffb1f7b02e40374711887139897a90574b7f8b74af5330f2de406'
            or old[0x9864:0x9869] != bytes.fromhex('1af6011ac3')):
        raise ValueError('Changed catalogue price presenter, stack contract, or metadata')
    rows = list(struct.unpack('>149I', reloc[20:20+149*4]))
    additions = [0x44002244, 0x45000000 | (START+12), 0x46000000 | (START+16)]
    if any((r & 0xFFFFFF) == 0x2244 for r in rows):
        raise ValueError('Catalogue font call unexpectedly already relocated')
    rows += additions
    data = bytearray(old+blob)
    struct.pack_into('>I', data, 0x2244, 0x0C000000 | ((RAM+START) >> 2 & 0x3FFFFFF))
    length = (24+len(rows)*4+15) & ~15
    new_rel = (struct.pack('>5I', len(data), 0, 0, 0, len(rows))
               +struct.pack('>'+str(len(rows))+'I', *rows)
               +bytes(length-24-len(rows)*4)+struct.pack('>I', length))
    owner = bytearray(parent)
    struct.pack_into('>I', owner, PARENT_AT+4, CAT+len(data))
    struct.pack_into('>I', owner, PARENT_AT+12, RAM+len(data))
    allowed = set(range(0x2244, 0x2248))
    for address in (0x801A0010, 0x802F8010, 0x803D0010):
        before = relocate_verified_data(Image(RAM, len(old), (START, 0, 0, 0, 149)), old, reloc, address)
        after = relocate_verified_data(Image(RAM, len(data), (len(data), 0, 0, 0, len(rows))), bytes(data), new_rel, address)
        if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(before, after))):
            raise ValueError('Catalogue adapter changes an unrelated relocation')
        hi = struct.unpack_from('>I', after, START+12)[0] & 65535
        lo = struct.unpack_from('>h', after, START+18)[0]
        if ((hi << 16)+lo != address+START+84
                or after[START+84:] != TEXT[0][2]
                or struct.unpack_from('>I', after, START+76)[0] != 0x080243A6
                or (struct.unpack_from('>I', after, 0x2244)[0] & 0x3FFFFFF)*4 | 0x80000000 != address+START):
            raise ValueError('Relocated catalogue adapter loses its text, call, or fixed font target')
    align = lambda n: (n+63) & ~63
    growth = align(len(data))-align(len(old))
    relocation_growth = align(len(new_rel))-align(len(reloc))
    # The current pool adds 0x4400 after the embedded-warning stage. Charge
    # that entire later reservation as used, retaining only the earlier slack.
    required, reserved = 253696+0x4400+growth+relocation_growth, 257152+0x4400
    if growth != 64 or relocation_growth != 0 or required > reserved:
        raise ValueError('Catalogue adapter exceeds the existing menu reservation')
    return bytes(data), new_rel, bytes(owner), {'overlay_growth': 96, 'rounded_pool_growth': growth,
        'rounded_relocation_growth': relocation_growth, 'conservative_required_bytes': required,
        'later_reservation_charged_in_full': 0x4400, 'reserved_bytes': reserved,
        'stack_growth': 0, 'native_price_buffer_bytes_written': 5}


def patch_repayment(old, reloc, widths):
    if (sha256(old) != HASHES[REPAY] or sha256(reloc) != HASHES[REPAY_REL]
            or struct.unpack_from('>5I', reloc) != REPAY_SECTIONS
            or sha256(widths) != '74ecbd2d0f1ca55cd55fc57f977d3a957dc2659068e7ad99360f097ef9834fc1'
            or old[0xDB4:0xDC4] != bytes.fromhex('06c3e707c2017e121700000004c17c00')):
        raise ValueError('Changed repayment text, relocation, or installed font metrics')
    if sum(12-widths[c] for c in TEXT[1][2]) != 54 or sum(12-widths[c] for c in TEXT[2][2]) != 12:
        raise ValueError('Changed complete English repayment label widths')
    changed = bytearray(old)
    changed[0xDB4:0xDBD] = TEXT[1][2]
    changed[0xDC0:0xDC3] = TEXT[2][2]+b'\0'
    edits = ((0x7C8, 0x3C014305, 0x3C01431E),   # Heading X: 133 -> 158.
             (0x988, 0x3C014260, 0x3C014286),   # Button X increment: 56 -> 67.
             (0x9C4, 0x24060003, 0x24060002))   # Actual button draw length.
    for at, before, after in edits:
        if struct.unpack_from('>I', old, at)[0] != before:
            raise ValueError('Changed native repayment label drawing instruction')
        struct.pack_into('>I', changed, at, after)
    allowed = set(range(0xDB4, 0xDBD)) | set(range(0xDC0, 0xDC3))
    for at, _, _ in edits:
        allowed.update(range(at, at+4))
    spec = Image(REPAY_RAM, len(old)+48, REPAY_SECTIONS)
    for address in (0x801A0010, 0x802F8010, 0x803D0010):
        before = relocate_verified_data(spec, old, reloc, address)
        after = relocate_verified_data(spec, bytes(changed), reloc, address)
        if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(before, after))):
            raise ValueError('Repayment label change alters an unrelated relocated instruction')
    return bytes(changed)


def build(native, base, rel, symbols, adapter):
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('Menu corrections require the complete exact RC4 cartridge')
    bells = references(rel, symbols)
    files = by_vrom(base)
    old = {v: files[v].extract(base) for v in HASHES}
    if any(sha256(old[v]) != digest for v, digest in HASHES.items()):
        raise ValueError('Changed selected RC4 menu resource')
    asset = old[ASSET]
    if (asset[0x37E0:0x37E8] != bytes.fromhex('FD9000000C004888')
            or asset[0x3810:0x3820] != bytes.fromhex('F20000000007C03C010040080C002ED0')
            or [i for i in range(len(asset)-3) if asset[i:i+4] == bytes.fromhex('0C004888')] != [0x37E4]):
        raise ValueError('Changed catalogue Bells reader, dimensions, or vertices')
    changed_asset = asset[:0x4888]+bells+asset[0x4988:]
    cat, relocation, parent, allocation = patch_catalogue(old[CAT], old[CAT_REL], old[PARENT], adapter)
    code = files[CODE_VROM].extract(base)
    if (struct.unpack_from('>I', code, 0x800C4B10-CODE_RAM)[0] != 0x25CE7620
            or struct.unpack_from('>I', code, 0x800C4AFC-CODE_RAM)[0] != 0x3C0E8089):
        raise ValueError('Current shared menu reservation is absent')
    repay = patch_repayment(old[REPAY], old[REPAY_REL], code[WIDTH_TABLE:WIDTH_TABLE+256])
    changes = {CAT: cat, CAT_REL: relocation, PARENT: parent, ASSET: changed_asset, REPAY: repay}
    image = reconstruct(native, base, changes, resized=(CAT, CAT_REL))
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Menu-label correction patch reconstruction failed')
    return image, patch, {'version': 1, 'source_sha256': sha256(native), 'baseline_sha256': BASE_SHA,
        'output_sha256': sha256(image), 'patch_sha256': sha256(patch), 'sources': source_hashes(),
        'source_rel_sha256': REL_SHA256, 'source_symbols_sha256': SYMBOLS_SHA256,
        'changed_files': {f'{v:08X}': sha256(data) for v, data in changes.items()},
        'text': [s.decode() for _, _, s in TEXT], 'bells_texture_sha256': sha256(bells),
        'catalogue_allocation': allocation, 'required_ram_bytes': 0x800000,
        'save_format_changed': False, 'save_readers_writers_changed': False,
        'price_and_repayment_arithmetic_changed': False, 'earlier_resources_retained': True,
        'fixed_issues': ['V1-21', 'V1-22', 'V1-23'], 'native_drawing_verified': False,
        'ordinary_save_restart_verified': False, 'hardware_retest': 'pending'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', type=Path, default=ROOT/'build/v1rc4/Animal Forest English V1RC4.z64')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = checked_output(a.output)
    state = source_state()
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    out.mkdir(parents=True, exist_ok=False)
    adapter = compile_adapter(out/'adapter')
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(), a.base.read_bytes(),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(), adapter)
    report.update(source_revision=revision, worktree_modified=state['worktree_modified'],
                  toolchain_image=IMAGE, complete_correction_rebuild=True)
    if report['sources'] != source_hashes() or state['worktree_modified'] != source_state()['worktree_modified']:
        raise ValueError('Menu-label sources changed during construction')
    for name, value in {'animal-forest-menu-labels.z64': image, 'animal-forest-menu-labels.ups': patch,
                        'fixes.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        write_new(out/name, value)
    asset = by_vrom(image)[ASSET].extract(image)
    write_new(out/'catalogue-bells.png', png_rgba(32, 16, decode(asset[0x4888:0x4988], 32, 16, 'i4'), 6))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
