"""Install the retained classic-letter adapter without changing live scheduling."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom, replace_dma, make_ups, apply_ups
from textbanks import Bank, banks
from mail_reference import BANK_HASHES, DECODER_SHA256, transcode
from gc_text import decoder_tables
from audit_mail_templates import template_fields
from mail_catalog import parse, verify_registered
from classic_letter_profiles import wrap, validate
from build_classic_letters import ROOT, BASE, BASE_SHA
from runtime_layout import MODULE_VROM

IDS = (0, 1, 0x4D, *range(0x53, 0x57), *range(0x58, 0x5C), 0xBF, 0x182, 0x183, *range(0x186, 0x18A))
FONT_VROM, CREATOR_VROM = 0x03400000, 0x03200000
CHANGED = (MODULE_VROM, CREATOR_VROM, FONT_VROM)
GUARDS = {
    (0x80093F04, 0x80093F54): '869d5aa49ea82edb0ac367bb334a87f325049f29487b401bb55f04f7b4dce222',
    (0x80093F54, 0x80093F94): '30abfb8560a0a0fd1a455ea0c7a68c5281823a53e60ad2bff96d1d6759cbe14f',
    (0x80092D10, 0x80092E14): '25e0eb7687fcca1a9d82ce2c8788651b7b7b7c715fa943274854bd4cd8c5e906',
}


def fields(number):
    if number not in IDS:
        raise ValueError('Unapproved retained classic template')
    if number == 1: return set(range(10, 20))
    if number in (0x4D, 0xBF): return {0}
    if 0x53 <= number <= 0x56: return set(range(1, 6))
    if 0x58 <= number <= 0x5B: return {4, 5}
    return set()


def baseline():
    built = (BASE/'animal-forest-halfwidth.z64').read_bytes()
    previous = json.loads((BASE/'build.json').read_text())
    if sha256(built) != BASE_SHA or previous['output_sha256'] != BASE_SHA:
        raise ValueError('Classic letters require the complete reserve-letter predecessor')
    return built, previous


def reviewed_templates(native, catalog):
    verified_rom(native)
    if verify_registered(catalog)['catalog'] != 4:
        raise ValueError('Retained classics require immutable catalogue four')
    contents = parse(catalog)[1]
    source = {bank.name: bank.entries() for bank in banks(native)}
    directory = ROOT/'build/gamecube/files/forest_1st.arc.unpacked/data'
    decoder = ROOT/'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes()) != DECODER_SHA256:
        raise ValueError('Changed retained-classic reference decoder')
    tables = decoder_tables(decoder)
    result, masks = [], {number: set() for number in IDS}
    for name in ('super', 'mail', 'ps'):
        data = (directory/(name+'_data.bin')).read_bytes()
        table = (directory/(name+'_data_table.bin')).read_bytes()
        if (sha256(data), sha256(table)) != BANK_HASHES[name]:
            raise ValueError('Changed retained-classic reference bank')
        reference = Bank(name, 0, 0, data, table).entries()
        for number in IDS:
            value = transcode(reference[number], tables, extended_glyphs=True)
            needed = template_fields(value, extended_glyphs=True)
            if value != contents[name][number] or needed != template_fields(source[name][number]):
                raise ValueError('Changed retained-classic wording, field identity, or catalogue content')
            masks[number] |= needed
            result.append({'id': f'{name}:{number:04X}', 'source_sha256': sha256(source[name][number]),
                           'reference_sha256': sha256(reference[number]), 'encoded_sha256': sha256(value),
                           'bytes': len(value), 'fields': sorted(needed)})
    if any(mask != fields(number) for number, mask in masks.items()):
        raise ValueError('Classic adapter mask differs from the complete native and reference parts')
    return result


def plan(native, base, previous, font, creator):
    files = by_vrom(base)
    native_code = by_vrom(native)[CODE_VROM].extract(native)
    code = files[CODE_VROM].extract(base)
    for (start, end), digest in GUARDS.items():
        if sha256(native_code[start-CODE_RAM:end-CODE_RAM]) != digest or code[start-CODE_RAM:end-CODE_RAM] != native_code[start-CODE_RAM:end-CODE_RAM]:
            raise ValueError('Changed classic-letter loader, argument order, or free-string source')
    rows = reviewed_templates(native, files[0x030A0000].extract(base))
    font_data, font_reloc, font_report = font
    creator_data, creator_reloc, creator_report = creator
    validate('font', *font)
    validate('creator', *creator)
    report = deepcopy(previous)
    module = report['runtime_module']
    if (module['module_sha256'] != '493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6'
            or int(module['symbols']['af_npc_mail_load'], 16) != 0x80197BB4):
        raise ValueError('Changed resident classic-loader import')
    from extended_font_cartridge import configuration as font_configuration
    from npc_mail_loader import configuration as creator_configuration, WORK_BYTES
    font_config = font_configuration(*font)
    creator_config = creator_configuration(*creator, module)
    font_blob, creator_blob = font_data+font_reloc, creator_data+creator_reloc
    binary = bytearray(files[MODULE_VROM].extract(base))
    struct.pack_into('>8I', binary, 0x48, *creator_config)
    struct.pack_into('>8I', binary, 0x68, *font_config)
    module['npc_mail_loader'].update(configuration=creator_config, blob_sha256=sha256(creator_blob),
                                     overlay=creator_report, glyph_font_sha256=sha256(font_blob))
    module['extended_font'].update(configuration=font_config, blob_sha256=sha256(font_blob), font=font_report)
    report['extended_font'].update(module['extended_font'])
    report['extended_font']['system_allocation_bytes'] = len(font_blob)+15
    report['npc_mail_loader'].update(module['npc_mail_loader'])
    report['npc_mail_loader'].update(temporary_allocation_bytes=len(creator_blob)+WORK_BYTES+15,
                                     configured_module_sha256=sha256(binary))
    report['mail_catalog']['glyph_font_sha256'] = sha256(font_blob)
    report['extended_items']['configured_module_sha256'] = sha256(binary)
    for key in ('treasure_owner', 'seasonal_owner'):
        if report['noticeboard'][key]['creator_sha256'] != previous['npc_mail_loader']['blob_sha256']:
            raise ValueError('Changed existing complete notice creator binding')
        report['noticeboard'][key]['creator_sha256'] = sha256(creator_blob)
    updates = {MODULE_VROM: bytes(binary), CREATOR_VROM: creator_blob, FONT_VROM: font_blob}
    report['classic_letters'] = {'version': 1, 'baseline_rom_sha256': BASE_SHA,
        'complete_templates': list(IDS), 'parts': rows, 'catalog': 4,
        'native_guards': {f'{start:08X}': digest for (start, _), digest in GUARDS.items()},
        'files': {f'{v:08X}': sha256(data) for v, data in updates.items()},
        'classic_entry': '80093F04', 'font_hook_offset': font_report['symbols']['af_classic_load'],
        'creator_entry_offset': creator_config[4], 'saved_layout_changes': 0,
        'field_source': 'Native ten-byte literal rows; live complete-field owner routes remain unchanged',
        'status': 'Installed retained-classic adapter; normal gameplay and save/restart remain combined v0 checks'}
    report.pop('patch_sha256', None)
    return updates, report


def assemble(native, base, previous, updates):
    if set(updates) != set(CHANGED):
        raise ValueError('Classic adapter must change only the font, creator, and module configuration')
    files = by_vrom(base)
    moved = {int(k, 16): int(v, 16) for k, v in previous['vrom_relocations'].items()}
    replacements = {int(v, 16): files[moved.get(int(v, 16), int(v, 16))].extract(base)
                    for v in previous['replacement_files']}
    additions = {int(v, 16): files[int(v, 16)].extract(base) for v in previous['added_files']}
    if any(v not in additions for v in CHANGED):
        raise ValueError('Classic adapter lacks its existing cartridge resources')
    additions.update(updates)
    built = replace_dma(native, replacements, moved, additions)
    installed = by_vrom(built)
    if set(installed) != set(files):
        raise ValueError('Classic adapter adds or removes an unrelated DMA resource')
    for vrom, entry in installed.items():
        if entry.index != files[vrom].index:
            raise ValueError('Classic adapter changes an existing DMA index')
        if vrom == 0x19D40:
            if entry.extract(built)[:16] != files[vrom].extract(base)[:16]:
                raise ValueError('Classic adapter changes the DMA-table prefix')
            continue
        expected = updates.get(vrom)
        if expected is None:
            expected = files[vrom].extract(base)
        if entry.extract(built) != expected:
            raise ValueError(f'Classic adapter loses an existing resource at {vrom:08X}')
    return built


def expected_report(native, base, previous, font, creator):
    updates, report = plan(native, base, previous, font, creator)
    built = assemble(native, base, previous, updates)
    report.update(output_sha256=sha256(built), size=len(built))
    return built, report


def verify_installation(built, native, report):
    verified_rom(native)
    base, previous = baseline()
    files = by_vrom(built)
    parts = []
    for vrom, profile in ((FONT_VROM, report['runtime_module']['extended_font']['font']),
                          (CREATOR_VROM, report['runtime_module']['npc_mail_loader']['overlay'])):
        data = files[vrom].extract(built)
        parts.append((data[:profile['bytes']], data[profile['bytes']:], profile))
    expected, expected_metadata = expected_report(native, base, previous, *parts)
    if built != expected:
        raise ValueError('Classic-letter cartridge differs from its complete three-resource update')
    actual = deepcopy(report)
    actual.pop('patch_sha256', None)
    if actual != expected_metadata:
        raise ValueError('Changed classic-letter installation report')
    return base, previous


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, default=ROOT/'build/classic-letters-candidate')
    parser.add_argument('--output', type=Path, default=ROOT/'build/classic-letters-pilot')
    args = parser.parse_args()
    native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    base, previous = baseline()
    from reserve_letters import verify_installation as verify_previous
    verify_previous(base, native, previous)
    parts = []
    for kind in ('font', 'creator'):
        path = args.candidate/kind
        parts.append(((path/'image.bin').read_bytes(), (path/'relocation.bin').read_bytes(),
                      wrap(json.loads((path/'profile.json').read_text()))))
    built, report = expected_report(native, base, previous, *parts)
    verify_installation(built, native, report)
    from runtime_module import verify_test_module
    verify_test_module(built, report['runtime_module'])
    patch = make_ups(native, built)
    if apply_ups(native, patch) != built:
        raise ValueError('Classic-letter UPS reconstruction failed')
    report['patch_sha256'] = sha256(patch)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'animal-forest-halfwidth.z64').write_bytes(built)
    (args.output/'animal-forest-halfwidth.ups').write_bytes(patch)
    (args.output/'runtime-module.json').write_text(json.dumps(report['runtime_module'], indent=2)+'\n')
    (args.output/'build.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'output_sha256': sha256(built), 'patch_sha256': sha256(patch),
                      'complete_templates': len(IDS), 'saved_layout_changes': 0}))


if __name__ == '__main__':
    main()
