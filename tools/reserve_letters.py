"""Apply the five retained reserve letters without changing saved formats."""
import argparse
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom, make_ups, apply_ups
from textbanks import Bank, banks
from mail_reference import BANK_HASHES, DECODER_SHA256, transcode
from gc_text import decoder_tables
from unused_names import assemble as assemble_previous

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'build/residual-general-pilot'
BASE_SHA = '8fece2aad3ee8c050ff1ed93c7403dd89e2f2428fdc7b0e9aae659df2731f7c6'
TEMPLATES = tuple(range(0xC0, 0xC5))
LINES = {'super': 1, 'mail': 6, 'ps': 0}
CAPACITIES = {'super': 10, 'mail': 96, 'ps': 16}
LOADER_START, LOADER_END = 0x80093B28, 0x80093F94


def baseline():
    base = (BASE/'animal-forest-halfwidth.z64').read_bytes()
    previous = json.loads((BASE/'build.json').read_text())
    if sha256(base) != BASE_SHA or previous['output_sha256'] != BASE_SHA:
        raise ValueError('Reserve letters require the complete general-string predecessor')
    return base, previous


def values(native):
    verified_rom(native)
    source = {bank.name: bank for bank in banks(native)}
    directory = ROOT/'build/gamecube/files/forest_1st.arc.unpacked/data'
    decoder = ROOT/'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes()) != DECODER_SHA256:
        raise ValueError('Changed reserve-letter reference decoder')
    tables = decoder_tables(decoder)
    result = {}
    for name, lines in LINES.items():
        data = (directory/(name+'_data.bin')).read_bytes()
        table = (directory/(name+'_data_table.bin')).read_bytes()
        if (sha256(data), sha256(table)) != BANK_HASHES[name]:
            raise ValueError('Changed reserve-letter reference bank')
        reference = Bank(name, 0, 0, data, table).entries()
        old = source[name].entries()
        expected = b'\x60\xF7'+b'\xCD'*lines
        replacement = b'Extra'+b'\xCD'*lines
        for number in TEMPLATES:
            if old[number] != expected:
                raise ValueError('Changed native reserve letter or intentional blank lines')
            if name == 'mail':
                # The donor body still contains the native Japanese bytes.
                # Its Latin decoder would misidentify these as accented glyphs.
                if reference[number] != expected:
                    raise ValueError('Changed untranslated reserve-letter donor body')
            elif transcode(reference[number], tables) != replacement:
                raise ValueError('Reserve-letter wording differs from complete English reference')
        if len(replacement) > CAPACITIES[name]:
            raise ValueError('Reserve-letter text exceeds the unchanged native destination')
        result[name] = replacement
    return result


def plan(native, base, previous):
    replacements = values(native)
    native_files, files = by_vrom(native), by_vrom(base)
    source_code = native_files[CODE_VROM].extract(native)
    installed_code = files[CODE_VROM].extract(base)
    start, end = LOADER_START-CODE_RAM, LOADER_END-CODE_RAM
    if installed_code[start:end] != source_code[start:end]:
        raise ValueError('Changed native reserve-letter assembly or destination bounds')
    from mail_controls import native_handlers
    native_handlers(native)
    from audit_mail import capacity_evidence
    capacity_evidence(native)
    source = {bank.name: bank for bank in banks(native)}
    moved = {int(k, 16): int(v, 16) for k, v in previous['vrom_relocations'].items()}
    updates, evidence_rows = {}, []
    for name, value in replacements.items():
        bank = source[name]
        dv, tv = moved.get(bank.data_vrom, bank.data_vrom), moved.get(bank.table_vrom, bank.table_vrom)
        current = replace(bank, data=files[dv].extract(base), table=files[tv].extract(base))
        before = current.entries()
        after = list(before)
        for number in TEMPLATES:
            if before[number] != bank.entries()[number]:
                raise ValueError('Reserve-letter predecessor must retain the exact native source')
            after[number] = value
            evidence_rows.append({'id': f'{name}:{number:04X}',
                                  'source_sha256': sha256(before[number]),
                                  'encoded_sha256': sha256(value), 'bytes': len(value),
                                  'newlines': LINES[name], 'capacity': CAPACITIES[name]})
        data, table = current.rebuild(after, allow_expand=True)
        data += bytes(-len(data) % 16)
        if replace(current, data=data, table=table).entries() != after:
            raise ValueError('Reserve-letter bank round trip failed')
        end_offset = 0
        for entry in after:
            end_offset += len(entry)
            if (end_offset+7) & ~7 > len(data):
                raise ValueError('Native rounded letter read exceeds the padded bank')
        next_vrom = min(v for v in files if v > dv)
        if dv+len(data) > next_vrom:
            raise ValueError('Reserve-letter bank exceeds its existing virtual address gap')
        updates.update({dv: data, tv: table})
    evidence = {'version': 1, 'baseline_rom_sha256': BASE_SHA,
                'complete_templates': list(TEMPLATES), 'parts': evidence_rows,
                'loader_sha256': sha256(source_code[start:end]),
                'changed_records': len(evidence_rows), 'runtime_changes': 0,
                'saved_layout_changes': 0,
                'files': {f'{v:08X}': sha256(data) for v, data in updates.items()}}
    return updates, evidence


def expected_report(previous, output, evidence):
    report = deepcopy(previous)
    report.update(reserve_letters=evidence, output_sha256=sha256(output), size=len(output),
                  translation_edits=previous['translation_edits']+evidence['changed_records'])
    # Explicit same-base DMA resize: preserve the native loader's address while
    # extending the checked aligned file end inside its existing free gap.
    report['vrom_relocations']['00D07000'] = '00D07000'
    report.pop('patch_sha256', None)
    return report


def assemble(native, base, previous, updates):
    if len(updates.get(0xD07000, b'')) != by_vrom(native)[0xD07000].size+16:
        raise ValueError('Reserve body requires its exact aligned DMA extension')
    packing = deepcopy(previous)
    packing['vrom_relocations']['00D07000'] = '00D07000'
    return assemble_previous(native, base, packing, updates)


def verify_installation(built, native, report):
    verified_rom(native)
    base, previous = baseline()
    updates, evidence = plan(native, base, previous)
    if built != assemble(native, base, previous, updates):
        raise ValueError('Reserve-letter cartridge differs from its exact six-file update')
    actual = deepcopy(report)
    actual.pop('patch_sha256', None)
    if actual != expected_report(previous, built, evidence):
        raise ValueError('Changed reserve-letter installation report')
    return base, previous


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/reserve-letters-pilot')
    args = parser.parse_args()
    native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    base, previous = baseline()
    from residual_general import verify_installation as verify_previous
    verify_previous(base, native, previous)
    updates, evidence = plan(native, base, previous)
    output = assemble(native, base, previous, updates)
    report = expected_report(previous, output, evidence)
    verify_installation(output, native, report)
    patch = make_ups(native, output)
    if apply_ups(native, patch) != output:
        raise ValueError('Reserve-letter patch reconstruction failed')
    report['patch_sha256'] = sha256(patch)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'animal-forest-halfwidth.z64').write_bytes(output)
    (args.output/'animal-forest-halfwidth.ups').write_bytes(patch)
    (args.output/'runtime-module.json').write_text(json.dumps(report['runtime_module'], indent=2)+'\n')
    (args.output/'build.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'output_sha256': sha256(output), 'patch_sha256': sha256(patch),
                      'changed_records': evidence['changed_records'], 'runtime_changes': 0}))


if __name__ == '__main__':
    main()
