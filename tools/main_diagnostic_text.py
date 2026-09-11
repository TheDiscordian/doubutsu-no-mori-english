"""Translate remaining main-program diagnostic literals in their existing slots."""
import argparse
import json
from pathlib import Path
import struct
import subprocess

from aflib import CODE_RAM, CODE_VROM, by_vrom, verified_rom, sha256, make_ups, apply_ups
from apply_translation import write_new
from rebuild_v1 import checked_output, source_state
from title_start_fix import reconstruct

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '2a04f6e5c54dc2d5ed03009395af815b464bebdef51d67d899554deb54b3bcb4'
# RAM address, complete aligned native slot, original literal, original translation.
TEXT = (
    (0x801175B0, 16, 'BGFGｼｮｷｶ', 'Init BG/FG'),
    (0x801175C0, 20, 'ｶﾜｶﾞｹｾｲｾｲ', 'Make rivers/cliffs'),
    (0x801175D4, 16, 'ｳﾐｾｲｾｲ', 'Make sea'),
    (0x801175E4, 20, 'ﾊｼｻｶｾｲｾｲ', 'Make bridges/slopes'),
    (0x801175F8, 28, 'ｺｳﾊﾞﾝﾋﾛﾊﾞｾｲｾｲ', 'Make police box/plaza'),
    (0x80117614, 32, 'ﾐｾﾕｳﾋﾞﾝｷｮｸｾｲｾｲ', 'Make shop/post office'),
    (0x80117634, 12, 'ｲｹｾｲｾ', 'Make ponds'),
    (0x80117640, 20, 'ﾍﾞｰｽｾｯﾃｲ', 'Set base'),
    (0x80117654, 20, 'ｳﾐﾆｶﾜｾｲｾｲ', 'Make river mouths'),
    (0x80117668, 20, 'ﾌﾞﾛｯｸｾﾝﾀｸ', 'Select blocks'),
    (0x8011767C, 24, 'ﾗﾝﾀﾞﾑｶﾝﾘｮｳ', 'Generation complete'),
    (0x801176C0, 16, 'ﾌｧﾐｺﾝ %d', 'Famicom %d'),
    (0x80117CD4, 8, '(予約)', 'Reserve'),
)
FUNCTIONS = (
    (0x800BCC40, 0x800BCCFC, 'f3512e2dd28473be1c621e1be0463b17a6aa167d139d3a08bd1447fd8d7a60b4'),
    (0x800BF27C, 0x800BF338, 'aad98075848702d24197267e81b3055b499484231120440e2c77c0dd9ca0bdb7'),
)
SOURCE_FILES = {
    'upstream/af/src/code/m_random_field.c': '3499780126072523ca7ae623809e8f3298690c1943457f5e93fee5454440a49f',
    'upstream/af/src/code/m_room_type.c': 'e67b5f21f082141558f15cd58d203de95bfd6be1569ea645b78761bf8bc1f30f',
    'upstream/af/src/code/cfbinfo.c': '1d39cb220b798c22851211aafa8d66b6673b9a4d363bca5bc81318ed8405a5c2',
    'upstream/af/src/boot/libu64/gfxprint.c': '0d52b07cb67b13ce28b0e1f1a1bfa0b01d42a2fede2b894f66ae797ca82a3b89',
}
POINTER_TABLE = 0x8010C6CC


def encoded_slot(original, english, capacity):
    raw = english.encode('ascii')
    if (not raw or any(value < 32 or value > 126 for value in raw)
            or len(raw)+1 > capacity or english.count('%') != original.count('%d')
            or english.count('%d') != original.count('%d')):
        raise ValueError('Diagnostic text must fit completely and retain its exact format arguments')
    return raw+b'\0'*(capacity-len(raw))


def patch_main(code):
    for start, end, digest in FUNCTIONS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM]) != digest:
            raise ValueError('Diagnostic reader instructions changed')
    pointer_bytes = struct.pack('>11I', *(row[0] for row in TEXT[:11]))
    if code[POINTER_TABLE-CODE_RAM:POINTER_TABLE-CODE_RAM+44] != pointer_bytes:
        raise ValueError('Generation step table changed')
    for address, raw in ((0x80117694, b'RandomTry %d\0'), (0x801176A4, b'RandomStep %s\0')):
        if code[address-CODE_RAM:address-CODE_RAM+len(raw)] != raw:
            raise ValueError('Unchanged diagnostic prefix or format changed')
    changed, records, spans = bytearray(code), [], []
    for index, (address, size, original, english) in enumerate(TEXT):
        at = address-CODE_RAM
        source = original.encode('euc_jp')+b'\0'
        if (at < 0 or at+size > len(code) or len(source) > size
                or code[at:at+size] != source+b'\0'*(size-len(source))
                or any(at < end and start < at+size for start, end in spans)):
            raise ValueError('Changed or overlapping native diagnostic storage')
        replacement = encoded_slot(original, english, size)
        if index < 11 and 3+len('RandomStep ')+len(english) > 40:
            raise ValueError('Generation label exceeds native screen columns')
        changed[at:at+size] = replacement
        spans.append((at, at+size))
        records.append({'ram': f'{address:08X}', 'bytes': size, 'original': original,
            'translation': english, 'source_sha256': sha256(code[at:at+size]),
            'installed_sha256': sha256(replacement),
            'reader': 'generation stage' if index < 11 else ('Famicom index' if index == 11 else 'unused reserve literal')})
    cursor = 0
    for start, end in sorted(spans):
        if changed[cursor:start] != code[cursor:start]:
            raise ValueError('Diagnostic replacement changes unrelated main-program bytes')
        cursor = end
    if len(changed) != len(code) or changed[cursor:] != code[cursor:]:
        raise ValueError('Diagnostic replacement changes main-program storage')
    return bytes(changed), records


def build(native, base):
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('Main diagnostic text requires the exact current RC8 baseline')
    if any(sha256((ROOT/name).read_bytes()) != digest for name, digest in SOURCE_FILES.items()):
        raise ValueError('Changed diagnostic source definitions or graphics-print encoding')
    code, records = patch_main(by_vrom(base)[CODE_VROM].extract(base))
    image = reconstruct(native, base, {CODE_VROM: code})
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Diagnostic-text UPS does not reconstruct the complete candidate')
    return image, patch, {'version': 1, 'source_sha256': sha256(native), 'baseline_sha256': BASE_SHA,
        'output_sha256': sha256(image), 'patch_sha256': sha256(patch), 'rom_bytes': len(image),
        'source_builder_sha256': sha256(Path(__file__).read_bytes()), 'source_definitions': SOURCE_FILES,
        'changed_files': {f'{CODE_VROM:08X}': sha256(code)}, 'records': records,
        'translated_records': len(records), 'drawn_diagnostic_records': 12, 'unused_literal_records': 1,
        'text_storage_bytes': sum(row[1] for row in TEXT), 'instructions_changed': False,
        'pointers_changed': False, 'allocation_changed': False, 'menu_access_changed': False,
        'generation_behaviour_changed': False, 'saved_format_changed': False,
        'save_readers_writers_changed': False, 'required_ram_bytes': 0x800000,
        'native_execution_verified': False, 'original_hardware_verified': False,
        'prior_rc8_corrections_retained': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=ROOT/'build/v1rc8/Animal Forest English V1RC8.z64')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = checked_output(args.output)
    if source_state()['worktree_modified']:
        raise ValueError('Commit diagnostic-text sources before construction')
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True,
        capture_output=True, text=True).stdout.strip()
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(), args.base.read_bytes())
    if source_state()['worktree_modified']:
        raise ValueError('Source changed during diagnostic-text construction')
    report.update(source_revision=revision, worktree_modified=False)
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in {'animal-forest-diagnostic-text.z64': image, 'animal-forest-diagnostic-text.ups': patch,
                     'fixes.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        write_new(output/name, raw)
    print(json.dumps({key: value for key, value in report.items() if key not in ('records', 'source_definitions')}, indent=2))


if __name__ == '__main__':
    main()
