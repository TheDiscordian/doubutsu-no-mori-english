"""Guarded English date preparation in the ordinary resident-dialogue overlay."""

import struct

from aflib import sha256
from npc_mail_show import OVERLAYS, source, verify, relocated as original_relocated
from runtime_layout import MODULE_RAM, MODULE_VROM, LINKED_LIMIT, RESERVATION

SPEC = OVERLAYS['ordinary']
CALLS = ((0x8091D980, 0x800C4084, 'af_format_year'),
         (0x8091D9E4, 0x800C40F8, 'af_format_month'),
         (0x8091DA48, 0x800C41B8, 'af_format_day'))
LEAP_HIGH, LEAP_LOW, LEAP_LENGTH = 0x8091EC14, 0x8091EC18, 0x8091EC28
REMOVED_RELOCATIONS = (0x45001464, 0x46001468)
REQUIREMENT = 'ordinary_dialogue_dates'


def changes(module):
    used = module.get('linked_bytes', 0)
    if type(used) is not int or not 0x300 < used <= LINKED_LIMIT:
        raise ValueError('Dialogue dates require a bounded resident module')
    result = []
    for address, original, symbol in CALLS:
        target = int(module['symbols'].get(symbol, '0'), 16)
        if target & 3 or not MODULE_RAM+0x300 <= target < MODULE_RAM+used:
            raise ValueError('Dialogue date formatter lies outside resident code')
        result.append((address, 0x0C000000 | ((original & 0x0FFFFFFF) >> 2),
                       0x0C000000 | ((target & 0x0FFFFFFF) >> 2)))
    literal = int(module['symbols'].get('af_leap_month', '0'), 16)
    if not MODULE_RAM+0x300 <= literal <= MODULE_RAM+used-10:
        raise ValueError('Dialogue leap-month literal lies outside resident data')
    result += [(LEAP_HIGH, 0x3C068092, 0x3C060000 | (((literal+0x8000) >> 16) & 0xFFFF)),
               (LEAP_LOW, 0x24C61BD8, 0x24C60000 | (literal & 0xFFFF)),
               (LEAP_LENGTH, 0x24070005, 0x2407000A)]
    return result


def patch(data, reloc, module):
    verify(SPEC, data, reloc)
    output = bytearray(data)
    for address, before, after in changes(module):
        at = address-SPEC.ram
        if struct.unpack_from('>I', data, at)[0] != before:
            raise ValueError('Dialogue date preparation instructions changed')
        struct.pack_into('>I', output, at, after)
    count = SPEC.sections[4]
    rows = list(struct.unpack_from('>'+str(count)+'I', reloc, 20))
    if any(rows.count(entry) != 1 for entry in REMOVED_RELOCATIONS):
        raise ValueError('Dialogue leap-month relocation pair changed')
    if rows.index(REMOVED_RELOCATIONS[1]) != rows.index(REMOVED_RELOCATIONS[0])+1:
        raise ValueError('Dialogue leap-month relocation pair is not adjacent')
    for address, _, _ in CALLS:
        if any(row & 0xFFFFFF == address-SPEC.ram for row in rows):
            raise ValueError('External date formatter unexpectedly has a relocation')
    rows = [entry for entry in rows if entry not in REMOVED_RELOCATIONS]
    # The leap string now lives at a fixed resident address, so only its HI/LO
    # relocation pair is removed. File, section, and BSS sizes remain unchanged.
    new_reloc = reloc[:16]+struct.pack('>I', len(rows))+struct.pack('>'+str(len(rows))+'I', *rows)
    new_reloc = new_reloc.ljust(len(reloc), b'\0')
    return bytes(output), new_reloc


def relocated(data, reloc, module, base):
    """Independent expectation: relocate original input, then replace fixed targets."""
    patch(data, reloc, module)
    result = bytearray(original_relocated(SPEC, data, reloc, base))
    for address, _, after in changes(module):
        struct.pack_into('>I', result, address-SPEC.ram, after)
    return bytes(result)


def install(rom, replacements, additions, module):
    binary = additions.get(MODULE_VROM, b'')
    if (not module or module.get('source_sha256') != sha256(rom)
            or len(binary) != RESERVATION or sha256(binary) != module.get('module_sha256')):
        raise ValueError('Dialogue dates require the complete unconfigured resident module')
    literal = int(module['symbols'].get('af_leap_month', '0'), 16)-MODULE_RAM
    if literal < 0 or binary[literal:literal+10] != b'leap month':
        raise ValueError('Dialogue dates require the complete English leap-month literal')
    data, reloc = source(rom, 'ordinary')
    patched, new_reloc = patch(data, reloc, module)
    if any(vrom in replacements and replacements[vrom] != original
           for vrom, original in ((SPEC.vrom, data), (SPEC.relocation, reloc))):
        raise ValueError('Dialogue date preparation overlaps another overlay patch')
    replacements[SPEC.vrom], replacements[SPEC.relocation] = patched, new_reloc
    return {'vrom': f'{SPEC.vrom:08X}', 'relocation_vrom': f'{SPEC.relocation:08X}',
            'source_sha256': sha256(data), 'output_sha256': sha256(patched),
            'relocation_sha256': sha256(new_reloc), 'relocations': SPEC.sections[4]-2,
            'changes': [{'ram': f'{a:08X}', 'before': f'{b:08X}', 'after': f'{c:08X}'}
                        for a, b, c in changes(module)],
            'scope': 'Ordinary resident date preparation; native lunar conversion and saved dates unchanged'}


def requires_dialogue_dates(edit):
    requirements = edit.get('runtime_requirements', [])
    if requirements not in ([], [REQUIREMENT]):
        raise ValueError('Unknown or malformed translation runtime requirements')
    return bool(requirements)


def validate_reference_requirements(record):
    if 'runtime_requirements' in record:
        if not requires_dialogue_dates(record) or not record['id'].startswith('message:'):
            raise ValueError('Reference runtime requirements must name the reviewed dialogue-date dependency')


def verify_requirements(edits, rom, replacements, additions, module, *, matches=None):
    requested = [requires_dialogue_dates(edit) for edit in edits]
    # The reviewed identity remains authoritative even if candidate metadata is
    # omitted. Supplying a shorter requirements list cannot remove a dependency.
    for edit in edits:
        record = (matches or {}).get(edit.get('id'), {})
        validate_reference_requirements(record)
        requested.append(requires_dialogue_dates(record))
    if any(requested):
        expected = {}
        install(rom, expected, additions or {}, module)
        if any(replacements.get(vrom) != data for vrom, data in expected.items()):
            raise ValueError('Translation requires the complete English dialogue-date patch')
