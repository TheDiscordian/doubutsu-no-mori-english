"""Translate the retained, unselected name list without changing live identities."""
import argparse
from copy import deepcopy
from dataclasses import replace
from functools import lru_cache
import json
from pathlib import Path
import struct

from aflib import (CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom,
                   replace_dma, make_ups, apply_ups)
from textbanks import Bank, banks
from fortune_strings import source_entries, STRING_RELOCATION
from reserve_strings import verify_source as verify_loader_source, START, END as LOADER_END, LOADER_SHA
from display_names import special_table
from audit_string_callers import audit

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'build/accent-items-pilot'
BASE_SHA = 'e09680bf156ae1b2662aca16878e056070f4acb07f26b5043a6789d9890ebb0e'
MANIFEST = ROOT/'translations/n64-unused-names.json'
MANIFEST_SHA = '4da47a5cd46bbe406f54481f73a93f0e46b96c2202fdf72b269e4e4d29c6c89f'
FIRST, END = 0x9C, 0x164
IDS = tuple(f'string:{n:04X}' for n in range(FIRST, END))
SOURCE_SHA = 'c89c7daa27119317a730777b4b6beccf286e4bbab2e01ee1272f371142d7d41e'
DATA_VROM, TABLE_VROM = 0x02600000, 0x00D18000


def group_hash(values):
    return sha256(b''.join(struct.pack('>H', len(value))+value for value in values))


@lru_cache(maxsize=1)
def verify_source(native):
    verified_rom(native)
    verify_loader_source(native)
    originals = source_entries(native)
    if group_hash(originals[FIRST:END]) != SOURCE_SHA:
        raise ValueError('Changed retained native name list')
    from catchphrases import native_table
    if (any(FIRST <= row[1] < END for row in native_table(native))
            or any(FIRST <= row[2] < END for row in special_table(native))):
        raise ValueError('Retained names overlap live default or character selectors')
    getters = audit(native, 0x800C3E30)['callers']
    if [(r['vrom'], r['call_ram']) for r in getters] != [('00675720', '800C3F9C')]:
        raise ValueError('Changed general-string getter consumer inventory')


def edits(native, data=None):
    verify_source(native)
    data = MANIFEST.read_bytes() if data is None else data
    if sha256(data) != MANIFEST_SHA:
        raise ValueError('Changed approved retained-name translation manifest')
    rows = json.loads(data)
    originals = source_entries(native)
    if len(rows) != len(IDS) or tuple(row['id'] for row in rows) != IDS:
        raise ValueError('Retained names require the complete ordered group')
    for row in rows:
        number = int(row['id'][7:], 16)
        value = row['translation'].encode('ascii')
        if (row['source_sha256'] != sha256(originals[number])
                or row['control_policy'] != 'exact' or not 1 <= len(value) <= 13
                or any(not (65 <= b <= 90 or 97 <= b <= 122 or b == 32) for b in value)):
            raise ValueError('Retained name requires its exact source and complete plain spelling')
    return rows


def verify_reference(native):
    """The donor retains these native bytes; its Latin decoder is not a translation."""
    verify_source(native)
    directory = ROOT/'build/gamecube/files/forest_1st.arc.unpacked/data'
    bank = Bank('string', 0, 0, (directory/'string_data.bin').read_bytes(),
                (directory/'string_data_table.bin').read_bytes())
    if bank.entries()[FIRST:END] != source_entries(native)[FIRST:END]:
        raise ValueError('Changed retained-name donor reference')
    return SOURCE_SHA


def baseline():
    base = (BASE/'animal-forest-halfwidth.z64').read_bytes()
    previous = json.loads((BASE/'build.json').read_text())
    if sha256(base) != BASE_SHA or previous['output_sha256'] != BASE_SHA:
        raise ValueError('Retained names require the complete preceding accent cartridge')
    return base, previous


def plan(native, base):
    rows = edits(native)
    files = by_vrom(base)
    bank = next(b for b in banks(native) if b.name == 'string')
    current = replace(bank, data=files[DATA_VROM].extract(base),
                      table=files[TABLE_VROM].extract(base))
    before = current.entries()
    if before[FIRST:END] != bank.entries()[FIRST:END]:
        raise ValueError('Retained name group is not the unchanged native source')
    # Only the established data-base relocation differs inside the native loader.
    code = bytearray(files[CODE_VROM].extract(base))
    _, at, old, installed = STRING_RELOCATION
    if code[at-CODE_RAM:at-CODE_RAM+8] != bytes.fromhex(installed):
        raise ValueError('Retained names require the verified relocated string bank')
    code[at-CODE_RAM:at-CODE_RAM+8] = bytes.fromhex(old)
    if sha256(code[START-CODE_RAM:LOADER_END-CODE_RAM]) != LOADER_SHA:
        raise ValueError('Changed installed bounded general-string loader')
    values = [row['translation'].encode('ascii') for row in rows]
    after = list(before)
    after[FIRST:END] = values
    data, table = current.rebuild(after, allow_expand=True)
    if replace(current, data=data, table=table).entries() != after:
        raise ValueError('Retained-name bank round trip failed')
    evidence = {
        'version': 1, 'baseline_rom_sha256': BASE_SHA, 'manifest_sha256': MANIFEST_SHA,
        'source_group_sha256': SOURCE_SHA, 'english_group_sha256': group_hash(values),
        'ids': list(IDS), 'records': len(rows), 'maximum_stored_bytes': max(map(len, values)),
        'source_characters': sum(map(len, before[FIRST:END])),
        'data_vrom': f'{DATA_VROM:08X}', 'table_vrom': f'{TABLE_VROM:08X}',
        'data_sha256': sha256(data), 'table_sha256': sha256(table),
        'loader_sha256': LOADER_SHA, 'runtime_changes': 0, 'saved_layout_changes': 0,
        'scope': 'Retained unselected general-string names; live identities remain unchanged',
    }
    return {DATA_VROM: data, TABLE_VROM: table}, evidence


def assemble(native, base, previous, updates):
    files = by_vrom(base)
    moved = {int(k, 16): int(v, 16) for k, v in previous['vrom_relocations'].items()}
    inverse = {v: k for k, v in moved.items()}
    replacements = {int(v, 16): files[moved.get(int(v, 16), int(v, 16))].extract(base)
                    for v in previous['replacement_files']}
    additions = {int(v, 16): files[int(v, 16)].extract(base) for v in previous['added_files']}
    for vrom, value in updates.items():
        if vrom in additions:
            raise ValueError('Retained-name update unexpectedly targets an added resource')
        replacements[inverse.get(vrom, vrom)] = value
    return replace_dma(native, replacements, moved, additions)


def expected_report(previous, output, evidence):
    report = deepcopy(previous)
    report.update(unused_names=evidence, translation_edits=previous['translation_edits']+len(IDS),
                  output_sha256=sha256(output), size=len(output))
    report.pop('patch_sha256', None)
    return report


def verify_installation(built, native, report):
    verified_rom(native)
    base, previous = baseline()
    updates, evidence = plan(native, base)
    expected = assemble(native, base, previous, updates)
    if built != expected:
        raise ValueError('Retained-name cartridge differs from its exact two-file update')
    actual_report = deepcopy(report)
    actual_report.pop('patch_sha256', None)
    if actual_report != expected_report(previous, expected, evidence):
        raise ValueError('Changed retained-name installation report')
    # Every preceding payload and report field is retained. Callers can verify
    # the predecessor's strict accent profile without relaxing that profile.
    return base, previous


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/unused-names-pilot')
    args = parser.parse_args()
    native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    verify_reference(native)
    base, previous = baseline()
    from accent_items_install import verify_installation as verify_accents
    verify_accents(base, native, previous)
    updates, evidence = plan(native, base)
    output = assemble(native, base, previous, updates)
    report = expected_report(previous, output, evidence)
    verify_installation(output, native, report)
    patch = make_ups(native, output)
    if apply_ups(native, patch) != output:
        raise ValueError('Retained-name patch reconstruction failed')
    report['patch_sha256'] = sha256(patch)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'animal-forest-halfwidth.z64').write_bytes(output)
    (args.output/'animal-forest-halfwidth.ups').write_bytes(patch)
    (args.output/'runtime-module.json').write_text(json.dumps(report['runtime_module'], indent=2)+'\n')
    (args.output/'build.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'output_sha256': sha256(output), 'patch_sha256': sha256(patch),
                      'translated_records': len(IDS), 'runtime_changes': 0}))


if __name__ == '__main__':
    main()
