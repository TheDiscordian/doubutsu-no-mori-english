"""Verified gyroid/demo message destinations, separate from stored letters."""

import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256

SETTER = 0x8009DA94
SETTER_END = 0x8009DBA4
SETTER_SHA256 = '76b06b4d5b721d9f68e5bcf38dd64d3624743d7a0080af6d2a8f06cabdf9e998'
GC_SETTER_SHA256 = '0afbe1fcd52acfe582012d9d1aedbd41dfc6e4a898d4638dd3a86f5d15ab19d5'
GC_SOURCE_SHA256 = '06cccec1dfb711fa72b731063f8eeb11d08b32665292e9439d6cd889bc9d7ab0'
CALLERS = (
    (0x0082B3C0, 0x80933F40, '016bd00c0b0f9cb5196a12275e9b382b2b3d16bb52710bbfe68b369158b2bbec',
     0x809340DC, (0x3C068093, 0x24C64660, 0x00402025, 0x00002825, 0x0C0276A5, 0x24070040),
     'ovl_Sample', 'Static demonstration text at linked RAM 80934660'),
    (0x0085F7D0, 0x8096AB90, 'bdd7e9093fe20ea5daf78953c3bb29f046c59e182d89ccc43871866c04d1c14d',
     0x8096B358, (0x8FA60020, 0x00402025, 0x00002825, 0x24070040, 0x0C0276A5, 0x24C60018),
     'ovl_Haniwa', 'Saved home-gyroid owner message at house_haniwa+18'),
)
GUARDS = {
    0x8009DA94: 0x04A00041, 0x8009DA9C: 0x1CA0003F,
    0x8009DAA4: 0x10C0003D, 0x8009DAB4: 0x24070044,
    0x8009DAC8: 0x24630132, 0x8009DB18: 0x29210005,
    0x8009DB40: 0x29410010, 0x8009DB84: 0x24040020,
}


def evidence(rom):
    files = by_vrom(rom)
    code = files[CODE_VROM].extract(rom)
    if sha256(code[SETTER-CODE_RAM:SETTER_END-CODE_RAM]) != SETTER_SHA256:
        raise ValueError('Unexpected native gyroid message setter')
    for address, expected in GUARDS.items():
        if struct.unpack_from('>I', code, address-CODE_RAM)[0] != expected:
            raise ValueError('Native gyroid message instruction guard failed')
    callers = []
    for vrom, ram, digest, start, words, name, source in CALLERS:
        data = files[vrom].extract(rom)
        if sha256(data) != digest:
            raise ValueError('Unexpected native gyroid/demo caller file')
        if struct.unpack_from('>'+str(len(words))+'I', data, start-ram) != words:
            raise ValueError('Native gyroid/demo caller instruction guard failed')
        callers.append({'segment': name, 'vrom': f'{vrom:08X}', 'source_sha256': digest,
                        'call_ram': f'{start+16:08X}', 'source': source, 'source_bytes': 64})
    return {'setter_ram': f'{SETTER:08X}', 'setter_sha256': SETTER_SHA256,
            'destination_offset': 0x132, 'destination_bytes': 68, 'saved_source_bytes': 64,
            'native_wrap_characters': 16, 'maximum_line_breaks': 5, 'callers': callers,
            'status': 'Gyroid/demo text, not a Mail_c excerpt; saved/editor capacity remains unchanged'}
