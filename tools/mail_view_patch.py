"""Install read-only pixel-width mail rendering without altering editing/saves."""

import struct

from aflib import by_vrom, sha256
from mail_viewer import VROM, RAM, evidence
from runtime_module import MODULE_RAM, MODULE_VROM, LINKED_LIMIT

RELOC_VROM = 0x00792610
RELOC_SHA256 = 'cb3f980f865ca0b9fad1c82c88280ce83080a9ff8ae1c38075990cf492589b68'
CALLS = ((0x8088A0A0, 0x80889A9C, 'af_mail_body_hook'),
         (0x8088A0D4, 0x808899E4, 'af_mail_footer_hook'))
SNAPSHOT_CALLS = ((0x8088A034, 0x80889CD8, 'af_mail_header_hook'),
                  (0x8088A47C, 0x8009C67C, 'af_mail_copy_hook'),
                  (0x8088914C, 0x80078DF4, 'af_mail_reader_trigger'))


def verify_reader_files(built, native, module, expected):
    """Verify the complete reader, including its owned letter-editor variant."""
    files = by_vrom(built)
    if 0x03B60000 in files:
        from letter_names import verify_shared_parts, preceding, VROM, RELOC
        if expected != dict(zip((VROM, RELOC), preceding(native))):
            raise ValueError('Letter editor lacks its exact preceding full reader')
        verify_shared_parts(built, native, module)
    elif any(v not in files or files[v].extract(built) != data for v, data in expected.items()):
        raise ValueError('Complete letter reader is not installed')


def remove_call_relocations(data, *, snapshots=False):
    if len(data) != 240 or sha256(data) != RELOC_SHA256:
        raise ValueError('Unexpected native board relocation file')
    if struct.unpack_from('>5I', data) != (0x1910, 0x430, 0x30, 0xC0, 52):
        raise ValueError('Unexpected native board relocation header')
    records = list(struct.unpack_from('>52I', data, 20))
    calls = CALLS+(SNAPSHOT_CALLS[:1] if snapshots else ())
    for address, _, _ in calls:
        expected = 0x44000000 | (address-RAM)
        if records.count(expected) != 1:
            raise ValueError('Missing or duplicated board call relocation')
        records.remove(expected)
    result = bytearray(data)
    struct.pack_into('>I', result, 16, len(records))
    result[20:-4] = struct.pack('>'+str(len(records))+'I', *records)+bytes(len(data)-24-len(records)*4)
    return bytes(result)


def install(rom, replacements, additions, module, *, snapshots=False):
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
    if snapshots:
        if struct.unpack_from('>I',data,0x8088A480-RAM)[0] != 0xAFA3005C:
            raise ValueError('Snapshot copy shim requires the native saved menu pointer')
        if struct.unpack_from('>2I',data,0x80889144-RAM) != (0xAFA40018,0xAFA5001C):
            raise ValueError('Snapshot trigger hook requires unchanged submenu/menu arguments')
    for address, old, symbol in CALLS+(SNAPSHOT_CALLS if snapshots else ()):
        target = int(module.get('symbols', {}).get(symbol, '0'), 16)
        if not MODULE_RAM+0x300 <= target < MODULE_RAM+min(module['linked_bytes'], LINKED_LIMIT) or target & 3:
            raise ValueError('Mail read-layout hook is outside the linked module')
        offset = address-RAM
        if struct.unpack_from('>I', data, offset)[0] != 0x0C000000 | ((old & 0x0FFFFFFF) >> 2):
            raise ValueError('Unexpected native board draw call')
        struct.pack_into('>I', data, offset, 0x0C000000 | ((target & 0x0FFFFFFF) >> 2))
        targets[symbol] = f'{target:08X}'
    relocations = remove_call_relocations(files[RELOC_VROM].extract(rom),snapshots=snapshots)
    replacements.update({VROM: bytes(data), RELOC_VROM: relocations})
    return {'source_viewer_sha256': native['file_sha256'], 'read_mode': 1,
            'body_pixel_width': 192, 'body_lines': 6,
            'viewer_sha256': sha256(data), 'relocations_sha256': sha256(relocations),
            'hook_targets': targets, 'saved_format_changed': False,
            'snapshot_reader': snapshots, 'experimental_snapshot_split': 128 if snapshots else None,
            'status': ('Experimental snapshot reader; no native generation or release/save approval'
                       if snapshots else 'Experimental read-only native fields; wider editing remains')}
