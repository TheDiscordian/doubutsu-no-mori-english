"""Translate the native clock picker without changing time, control, or save logic."""
import argparse
import copy
import json
from pathlib import Path
import struct

from aflib import CODE_VROM, by_vrom, sha256, verified_rom, replace_dma, make_ups, apply_ups, u32
from catalogue_names import Image
from font import WIDTH_TABLE
from npc_mail_show import relocate_verified_data
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256
from textcodec import LATIN

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '15c7a2830f5a561a8470ba70bc4aaa907e65ab1ee5ebb921266df17e6b1cac3c'
VROM, RELOC, RAM = 0x78AE30, 0x78BEE0, 0x808831A0
NATIVE_SHA = '3aebd5b023d62567ff78fa5e808ced29740a0e2e569fa19f16896848c1b779cd'
RELOC_SHA = '3d4b0b08f913207dcaf8c20c1e8f5a24aea1cd10886d87def56dbc25e8ca969d'
SECTIONS = (4128, 144, 0, 32, 46)
SOURCES = ((0x808841E0, 9, 'ed05c3c200c10d1217'),
           (0x808841EC, 14, '3230202017c32020e71120201510'),
           (0x808841FC, 5, 'ed20201bc3'), (0x80884204, 3, '04c17c'))
FIELDS = ((0x808841E0, 20, b'Adjust the clock.'), (0x808841F4, 12, b'20  -  -  '),
          (0x80884200, 4, b':'), (0x80884204, 4, b'OK'))
POSITIONS = ((132.5, 115), (148.25, 115), (164, 115), (102, 137), (115.125, 137))
PATCHES = ((0x80883B98, 0x3C014305, 0x3C014303), (0x80883BAC, 0x3C0142A6, 0x3C0142A4),
           (0x80883C14, 0x24060009, 0x24060011), (0x80883C18, 0x3C0142A6, 0x3C0142F4),
           (0x80883C54, 0x24A541EC, 0x24A541F4), (0x80883C5C, 0x2406000E, 0x2406000A),
           (0x80883C7C, 0x3C0142E4, 0x3C0142E1), (0x80883CB8, 0x24A541FC, 0x24A54200),
           (0x80883CC0, 0x24060005, 0x24060001), (0x80883DA4, 0x3C014334, 0x3C01433E),
           (0x80883DFC, 0x24060003, 0x24060002))


def source(native):
    files = by_vrom(verified_rom(native))
    data, reloc = files[VROM].extract(native), files[RELOC].extract(native)
    if sha256(data) != NATIVE_SHA or sha256(reloc) != RELOC_SHA or struct.unpack_from('>5I', reloc) != SECTIONS:
        raise ValueError('Unexpected native time-setting owner/relocation')
    for address, size, hexdata in SOURCES:
        if data[address-RAM:address-RAM+size] != bytes.fromhex(hexdata):
            raise ValueError('Unexpected native clock wording')
    return data, reloc


def reference(rel, symbols):
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Unexpected English clock source')
    for offset, text in ((0x83EA4, FIELDS[0][2]), (0x83EB8, FIELDS[3][2])):
        if rel[DATA_BASE+offset:DATA_BASE+offset+len(text)] != text:
            raise ValueError('Supplied GameCube clock wording changed')


def widths(built):
    code = by_vrom(built)[CODE_VROM].extract(built)
    expected = {ord(c): 6 for c in ' 0123456789-'} | {ord(':'): 3}
    if any(12-code[WIDTH_TABLE+key] != value for key, value in expected.items()):
        raise ValueError('Installed clock glyph advances no longer fit the verified layout')
    return {chr(k): v for k, v in expected.items()}


def patch_owner(native):
    data, reloc = source(native)
    result = bytearray(data)
    for address, old, new in PATCHES:
        if u32(data, address-RAM) != old:
            raise ValueError('Unexpected native clock reader instruction')
        struct.pack_into('>I', result, address-RAM, new)
    for address, capacity, text in FIELDS:
        if len(text) > capacity or any(v not in LATIN for v in text):
            raise ValueError('Clock text exceeds its existing field or Latin encoding')
        result[address-RAM:address-RAM+capacity] = text+bytes(capacity-len(text))
    for i, xy in enumerate(POSITIONS):
        struct.pack_into('>2f', result, 0x80884220-RAM+i*8, *xy)
    result = bytes(result)
    spec = Image(RAM, len(data)+SECTIONS[3], SECTIONS)
    allowed = {i for a, _, _ in PATCHES for i in range(a-RAM, a-RAM+4)}
    allowed.update(range(0x808841E0-RAM, 0x80884208-RAM))
    allowed.update(range(0x80884220-RAM, 0x80884248-RAM))
    for base in (0x801A0010, 0x802F8010):
        before = relocate_verified_data(spec, data, reloc, base)
        after = relocate_verified_data(spec, result, reloc, base)
        if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(before, after))):
            raise ValueError('Clock translation changes an unrelated relocation or instruction')
        for low, target in ((0x80883C54, 0x808841F4), (0x80883CB8, 0x80884200)):
            word = u32(after, low-RAM)
            if word & 0xFFFF != (base+target-RAM) & 0xFFFF:
                raise ValueError('Moved clock string fails native low-address relocation')
    return result, reloc


def profile(data, advances):
    return {'version': 1, 'native_owner_sha256': NATIVE_SHA, 'owner_sha256': sha256(data),
        'relocation_sha256': RELOC_SHA, 'source_rel_sha256': REL_SHA256,
        'assembly_source_sha256': sha256((ROOT/'overlays/time_setting/labels.s').read_bytes()),
        'strings': [{'native_address': f'{a:08X}', 'source_bytes': n,
                     'english_address': f'{b:08X}', 'english': text.decode(), 'read_bytes': len(text)}
                    for (a, n, _), (b, capacity, text) in zip(SOURCES, FIELDS)],
        'positions': [list(xy) for xy in POSITIONS], 'glyph_advances': advances,
        'date_format': '20YY-MM-DD', 'time_format': 'HH:MM', 'selection_order_changed': False,
        'rtc_logic_changed': False, 'save_layout_changed': False, 'allocation_changed': False,
        'status': 'Installed English native clock picker; ordinary adjustment/hardware checks pending'}


def measure_text(ledger, native, built, report):
    original, reloc = source(native)
    installed = report.get('time_setting')
    if installed:
        expected, expected_reloc = patch_owner(native)
        files = by_vrom(built)
        if (files[VROM].extract(built) != expected or files[RELOC].extract(built) != expected_reloc
                or installed != profile(expected, widths(built))):
            raise ValueError('Changed installed clock translation or reader metadata')
    for number, ((address, length, _), (_, _, english)) in enumerate(zip(SOURCES, FIELDS)):
        identity = f'ui_time_setting:{number:04X}'
        ledger.add(identity, original[address-RAM:address-RAM+length])
        if installed:
            ledger.credit(identity, english, 'time_setting')


def build(native, base, report, rel, symbols):
    if sha256(base) != BASE_SHA or report.get('output_sha256') != BASE_SHA:
        raise ValueError('Clock translation requires complete inventory/map/shop/fix baseline')
    reference(rel, symbols)
    advances = widths(base)
    changed, reloc = patch_owner(native)
    files = by_vrom(base)
    if sha256(files[VROM].extract(base)) != NATIVE_SHA or files[RELOC].extract(base) != reloc:
        raise ValueError('Installed clock owner already has unrelated changes')
    moved = {int(k, 16): int(v, 16) for k, v in report['vrom_relocations'].items()}
    replacements = {int(v, 16): files[moved.get(int(v, 16), int(v, 16))].extract(base)
                    for v in report['replacement_files']}
    additions = {int(v, 16): files[int(v, 16)].extract(base) for v in report['added_files']}
    if VROM in moved or VROM in additions:
        raise ValueError('Clock ownership changed')
    replacements[VROM] = changed
    image = replace_dma(native, replacements, moved, additions)
    installed = by_vrom(image)
    if set(installed) != set(files) or len(image) != len(base):
        raise ValueError('Clock translation changes ROM size or DMA identities')
    for vrom, entry in files.items():
        actual, expected = installed[vrom].extract(image), changed if vrom == VROM else entry.extract(base)
        if vrom == 0x19D40:
            actual, expected = actual[:16], expected[:16]
        if actual != expected or installed[vrom].index != entry.index:
            raise ValueError(f'Clock translation loses prior resource {vrom:08X}')
    ups = make_ups(native, image)
    if apply_ups(native, ups) != image:
        raise ValueError('Clock translation patch reconstruction failed')
    result = copy.deepcopy(report)
    result.update(output_sha256=sha256(image), patch_sha256=sha256(ups),
        replacement_files=[f'{v:08X}' for v in sorted(replacements)], time_setting=profile(changed, advances),
        release_status='Clock/inventory/map/shop English candidate; ordinary visual/hardware checks pending')
    return image, ups, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/time-setting-01')
    args = parser.parse_args()
    baseline = ROOT/'build/inventory-artwork-02'
    image, ups, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (baseline/'animal-forest-halfwidth.z64').read_bytes(), json.loads((baseline/'build.json').read_text()),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    args.output.mkdir(parents=True, exist_ok=False)
    for name, value in {'animal-forest-halfwidth.z64': image, 'animal-forest-halfwidth.ups': ups,
        'build.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target:
            target.write(value)
    print(json.dumps({'output': str(args.output), 'sha256': report['output_sha256'],
                      'patch_sha256': report['patch_sha256'], 'strings': report['time_setting']['strings']}))


if __name__ == '__main__':
    main()
