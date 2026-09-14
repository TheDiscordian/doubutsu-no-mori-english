"""Connect complete imported names to display and generated-mail consumers."""
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256

ABI, CODE, LIMIT = 24, 0x5400, 0x5800
TEXT, CREATOR, MODULE = 0x3A00000, 0x3200000, 0x2800000
SOURCES = ('tools/v3_villager_readers.py', 'overlays/v3/villager_readers.c',
           'overlays/v3/villager_readers.ld', 'overlays/mail_generation/npc_capture.h',
           'runtime/mail/record.h')
OWNERS = {
    0x3950000: (0x8086F310, 0x3960000,
        '0462b689b147edced562fec29d8910b89fa47a0d27034db89c01f296d69d9613',
        ((0xA9C0, 0x2CC200D8, 'inventory letter sender/recipient'),
         (0xAAB0, 0x2C4200D8, 'inventory quest names'))),
    0x3B00000: (0x8088DBD0, 0x3B10000,
        'dfd43c2ac9801717f7c4977842de34abb82649d247c763cb2b1cfb9ab0626599',
        ((0x6568, 0x2C4200D8, 'map house names'),)),
    0x3B60000: (0x80888E90, 0x3B70000,
        '3eb4eb3515a215546bba2266be869ab15ac0d39077e51b93a2602957d6bde2c9',
        ((0x1FF8, 0x2CC200D8, 'letter read/editor header'),)),
    0x3E60000: (0x8088ADB0, 0x3E68000,
        'f4d20c4a8830e513b950a42c8b18d24be96d5f157b9fd0eb096cefb285dbd1be',
        ((0x1D94, 0x2CC200D8, 'address selection'),)),
    TEXT: (0x80D00000, 3808,
        '988be57c76de3d72435818fe27cd384a6f42366fa52fb6d28031ac0ed7851c96',
        ((0x4B8, 0x2C4200D8, 'conversation identity field'),)),
    CREATOR: (0x80B00000, 0xEF10,
        'e57f003e15fccd7d39c3bf306a9833b0e4a088a67806c3d64fe0bf7acc9bcefd',
        ((0x1C00, 0x2C4200D8, 'departed-villager letter'),
         (0x20FC, 0x2C4200D8, 'birthday/event/goodbye letter'),
         (0x360C, 0x2C4200D8, 'quest-reply letter'),
         (0x448C, 0x2C4200D8, 'treasure notice'))),
}
MAIL_ENTRIES = ((0x898, 0x27BDFFE8, 0x00804025, 'af_v3_mail_source_name'),
                (0x928, 0x27BDFFE8, 0x00805825, 'af_v3_mail_source_alias'))


def relocation_offsets(data):
    sections = struct.unpack_from('>5I', data)
    if 20 + sections[4]*4 > len(data):
        raise ValueError('Incomplete name-reader relocation table')
    return {sum(sections[:(row >> 30)-1]) + (row & 0xFFFFFF)
            for (row,) in struct.iter_unpack('>I', data[20:20+sections[4]*4])}


def install(base, changes, blob, helper, symbols):
    files = by_vrom(base)
    if len(blob) != 0xC000 or not 0 < len(helper) <= LIMIT-CODE or any(blob[CODE:LIMIT]):
        raise ValueError('Villager reader code collides with its resident neighbours')
    if symbols['af_v3_mail_source_name'] != 0x80460000+CODE:
        raise ValueError('Changed shared mail-name entry')
    code, module = (bytearray(changes[v]) for v in (CODE_VROM, MODULE))
    result, reports = {}, []
    for vrom, (ram, relocation, expected_sha, windows) in OWNERS.items():
        original = files[vrom].extract(base)
        if sha256(original) != expected_sha:
            raise ValueError(f'Changed V2 name-reader owner {vrom:08X}')
        data = bytearray(changes.get(vrom, original))
        if len(data) != len(original):
            raise ValueError('Name-reader owner unexpectedly resized')
        reloc = files[relocation].extract(base) if relocation > len(data) else original[relocation:]
        offsets = relocation_offsets(reloc)
        touched = []
        for at, expected, label in windows:
            if struct.unpack_from('>I', data, at)[0] != expected or at in offsets:
                raise ValueError('Changed name-reader bound or relocated immediate')
            struct.pack_into('>I', data, at, (expected & 0xFFFF0000) | 238)
            touched.append({'offset': at, 'address': f'{ram+at:08X}', 'reader': label,
                            'before': f'{expected:08X}', 'after': f'{expected & 0xFFFF0000 | 238:08X}'})
        if vrom == CREATOR:
            for at, first, second, name in MAIL_ENTRIES:
                if struct.unpack_from('>II', data, at) != (first, second) or {at, at+4} & offsets:
                    raise ValueError('Changed mail-name entry or relocated prologue')
                target = symbols[name]
                if not 0x80460000+CODE <= target < 0x80460000+CODE+len(helper):
                    raise ValueError('Mail-name target escapes resident reader code')
                struct.pack_into('>II', data, at, 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
                touched.append({'offset': at, 'address': f'{ram+at:08X}', 'reader': name,
                                'before': struct.pack('>II', first, second).hex(),
                                'after': data[at:at+8].hex()})
        result[vrom] = bytes(data)
        reports.append({'vrom': f'{vrom:08X}', 'ram': f'{ram:08X}', 'bytes': len(data),
                        'input_sha256': sha256(changes.get(vrom, original)),
                        'output_sha256': sha256(data), 'relocation_sha256': sha256(reloc),
                        'relocation': relocation, 'patches': touched})
    # Keep the existing validated startup loader; change only its full-blob CRC.
    start, end = 0x8009D6D0-CODE_RAM, 0x8009D7A8-CODE_RAM
    if sha256(code[start:end]) != '4cd298af8b749b2e5773280c1f5b8a5163f5c45a9412e6b21919ea80b195e769':
        raise ValueError('Changed complete text-extension loader')
    crc = zlib.crc32(result[TEXT])
    struct.pack_into('>II', code, 0x8009D758-CODE_RAM,
                     0x3C030000 | ((crc+0x8000) >> 16 & 0xFFFF), 0x24630000 | (crc & 0xFFFF))
    expected = (CREATOR, 0xF2D0, 0xEF10, 0x3C0, 0xEBF0, 0xEF10, 0x168E238E, 0x41464E01)
    if struct.unpack_from('>8I', module, 0x48) != expected:
        raise ValueError('Changed native generated-letter loading configuration')
    struct.pack_into('>I', module, 0x60, zlib.crc32(result[CREATOR]))
    blob[CODE:CODE+len(helper)] = helper
    result.update({CODE_VROM: bytes(code), MODULE: bytes(module)})
    return result, {'owners': reports, 'resident_code_bytes': len(helper),
                    'resident_code_sha256': sha256(helper), 'text_crc32': f'{crc:08X}',
                    'creator_crc32': f'{zlib.crc32(result[CREATOR]):08X}',
                    'saved_layout_changed': False, 'move_in_enabled': False,
                    'native_execution': 'pending'}
