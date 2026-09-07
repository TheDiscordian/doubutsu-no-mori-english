"""Install read-only pixel-width mail rendering without altering editing/saves."""

import struct

from aflib import by_vrom, sha256
from mail_viewer import VROM, RAM, evidence
from runtime_module import MODULE_RAM, MODULE_VROM, LINKED_LIMIT

RELOC_VROM = 0x00792610
RELOC_SHA256 = 'cb3f980f865ca0b9fad1c82c88280ce83080a9ff8ae1c38075990cf492589b68'
CALLS = ((0x8088A0A0, 0x80889A9C, 'af_mail_body_hook'),
         (0x8088A0D4, 0x808899E4, 'af_mail_footer_hook'))


def remove_call_relocations(data):
    if len(data) != 240 or sha256(data) != RELOC_SHA256:
        raise ValueError('Unexpected native board relocation file')
    if struct.unpack_from('>5I', data) != (0x1910, 0x430, 0x30, 0xC0, 52):
        raise ValueError('Unexpected native board relocation header')
    records = list(struct.unpack_from('>52I', data, 20))
    for address, _, _ in CALLS:
        expected = 0x44000000 | (address-RAM)
        if records.count(expected) != 1:
            raise ValueError('Missing or duplicated board call relocation')
        records.remove(expected)
    result = bytearray(data)
    struct.pack_into('>I', result, 16, len(records))
    result[20:-4] = struct.pack('>50I', *records)+bytes(len(data)-24-50*4)
    return bytes(result)


def install(rom, replacements, additions, module):
    native = evidence(rom)
    if not module or MODULE_VROM not in additions:
        raise ValueError('Mail read layout requires the resident module')
    # Install before optional configuration words are written. This binds every
    # call target to the already verified, source-matched module artifact.
    if sha256(additions[MODULE_VROM]) != module['module_sha256']:
        raise ValueError('Mail read layout requires unchanged verified module bytes')
    if VROM in replacements or RELOC_VROM in replacements:
        raise ValueError('Overlapping mail-viewer patches')
    files = by_vrom(rom)
    data = bytearray(files[VROM].extract(rom))
    targets = {}
    for address, old, symbol in CALLS:
        target = int(module.get('symbols', {}).get(symbol, '0'), 16)
        if not MODULE_RAM+0x300 <= target < MODULE_RAM+min(module['linked_bytes'], LINKED_LIMIT) or target & 3:
            raise ValueError('Mail read-layout hook is outside the linked module')
        offset = address-RAM
        if struct.unpack_from('>I', data, offset)[0] != 0x0C000000 | ((old & 0x0FFFFFFF) >> 2):
            raise ValueError('Unexpected native board draw call')
        struct.pack_into('>I', data, offset, 0x0C000000 | ((target & 0x0FFFFFFF) >> 2))
        targets[symbol] = f'{target:08X}'
    relocations = remove_call_relocations(files[RELOC_VROM].extract(rom))
    replacements.update({VROM: bytes(data), RELOC_VROM: relocations})
    return {'source_viewer_sha256': native['file_sha256'], 'read_mode': 1,
            'body_pixel_width': 192, 'body_lines': 6,
            'viewer_sha256': sha256(data), 'relocations_sha256': sha256(relocations),
            'hook_targets': targets, 'saved_format_changed': False,
            'status': 'Experimental read-only native fields; full snapshot viewer and wider editing remain'}
