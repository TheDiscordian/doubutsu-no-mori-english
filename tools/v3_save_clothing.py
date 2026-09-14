"""Install the separate checked clothing codec without moving public save entries."""
import struct
import zlib

from aflib import sha256

from v3_storage import START as STORAGE
ABI, VROM, RAM, LIMIT, DESCRIPTOR = 31, STORAGE+0xF400, 0x8046D000, 0xC00, 0xE0
PROFILE, STATE, RUNTIME_BYTES = 192, 832, 864
SOURCES = ('tools/v3_save_clothing.py', 'overlays/v3/save_clothing.ld')
DEFINES = ('AF_V3_CLOTHING_PROFILE=1',
           'af_v3_save_check=af_v3_save_check_extended',
           'af_v3_save_pack=af_v3_save_pack_extended',
           'af_v3_save_collect=af_v3_save_collect_extended')


def install(blob, helper, compiled, original, runtime):
    if (len(blob) != 0xC000 or not helper or len(helper) > LIMIT-16 or any(blob[DESCRIPTOR:DESCRIPTOR+16])
            or len(bytes.fromhex(runtime['profile_hex'])) != PROFILE or runtime['state_bytes'] != RUNTIME_BYTES
            or runtime['state_ram']+RUNTIME_BYTES > RAM or len(helper) != compiled['bytes']
            or sha256(helper) != compiled['sha256']
            or sha256(blob[0xB400:0xB400+original['bytes']]) != original['sha256']):
        raise ValueError('Invalid clothing codec resource or state layout')
    payload = helper+bytes((-len(helper)) % 16)
    hooks = []
    for name in ('check', 'pack', 'collect'):
        entry = original['symbols']['af_v3_save_'+name]
        target = compiled['symbols']['af_v3_save_'+name+'_extended']
        at = entry-0x80460000
        if not 0xB400 <= at < 0xBA58 or not RAM <= target < RAM+len(helper) or (entry | target) & 3:
            raise ValueError('Changed public save entry or extended codec address')
        before = bytes(blob[at:at+8])
        struct.pack_into('>2I', blob, at, 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
        hooks.append({'entry': f'{entry:08X}', 'target': f'{target:08X}',
                      'before': before.hex(), 'after': blob[at:at+8].hex()})
    struct.pack_into('>4I', blob, DESCRIPTOR, VROM, len(payload), zlib.crc32(payload), RAM)
    return payload, {'format_version': 2, 'registry_version': 2, 'legacy_formats_read': ['NAFJ', 'AFS3-v1'],
        'profile_bytes': PROFILE, 'working_state_bytes': STATE, 'runtime_bytes': RUNTIME_BYTES,
        'resource_vrom': f'{VROM:08X}', 'resource_ram': f'{RAM:08X}', 'resource_bytes': len(payload),
        'resource_sha256': sha256(payload), 'descriptor_offset': DESCRIPTOR, 'public_entries': hooks,
        'older_v3_reads_new_saves': False, 'ordinary_clothing_persistence_tested': False}
