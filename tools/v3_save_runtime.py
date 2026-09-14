"""Guarded complete-bank save/load integration and owned V3 profile state."""
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from flash_mail import CODE_GUARDS, evidence
from v3_save_codec import BANK, BLOB_SIZE, PROFILE

ABI, CODE, LIMIT, BRIDGE, PROFILE_OFFSET = 14, 0x9200, 0xA200, 0xBA60, 0x20
STATE_RAM, STATE_BYTES = 0x8046C000, 0x2C0
SOURCES = ('tools/v3_save_runtime.py', 'overlays/v3/save_runtime.c',
           'overlays/v3/save_runtime.h', 'overlays/v3/save_runtime.ld')
TRAVEL_GUARDS = ((0x80095470, 0x80095B50, '285051125647c3ecd2bf35d1a64e1afe635f100c97b02a68dbfdfb21aed4d1fd'),
                 (0x80095FE4, 0x80096524, 'b957160ece45f63c9c8f19bc6d6f9f0a657e2a7aa4496715c84fbde5f45fcdf4'))
READ_CALLS = (0x8008F2D8, 0x8008F384, 0x8008F48C, 0x8008F4A4, 0x8008F56C,
              0x8008F950, 0x8008F9A8, 0x8008FD00, 0x8008FDF0, 0x8008FF7C,
              0x80095A54, 0x80096468)
PREPARE_CALLS = (0x8008FBA0, 0x80095874, 0x80096260)
ALLOCATIONS = (0x8008F98C, 0x8008FAFC, 0x80095498, 0x80096030)


def profile_bytes(villagers, furniture, clothing=None):
    result = bytearray(PROFILE + (32 if clothing is not None else 0))
    seen = set()
    for row in villagers:
        actor = int(row['actor_id'], 16)
        if not 0xE0DA <= actor <= 0xE0ED or actor in seen or row['registry_version'] != 1:
            raise ValueError('Invalid stable villager profile identity')
        seen.add(actor)
        index = actor - 0xE000
        result[index >> 3] |= 1 << (index & 7)
    for row in furniture:
        item = int(row['item_id'], 16)
        if not 0x3000 <= item <= 0x3FFC or item & 3 or item in seen:
            raise ValueError('Invalid stable furniture profile identity')
        if clothing is not None and 0x3400 <= item <= 0x34FF:
            raise ValueError('Furniture identity collides with the clothing class')
        if row['runtime_index'] != 1024 + ((item & 0xFFF) >> 2):
            raise ValueError('Furniture profile differs from its installed identity')
        seen.add(item)
        index = (item & 0xFFF) >> 2
        result[32 + (index >> 3)] |= 1 << (index & 7)
    if clothing is not None:
        from v3_registry import CLOTHING_REGISTRY_VERSION, clothing_slot
        for row in clothing:
            item, index, vrom = clothing_slot(int(row['donor_item_id'], 16))
            if (row['registry_version'] != CLOTHING_REGISTRY_VERSION
                    or row['item_id'] != f'{item:04X}' or row['resource_index'] != index
                    or row['vrom'] != f'{vrom:08X}' or item in seen):
                raise ValueError('Changed clothing profile identity or duplicate')
            seen.add(item)
            bit = item & 255
            result[160+(bit >> 3)] |= 1 << (bit & 7)
    return bytes(result)


def install(native, base, code, blob, helper, symbols, codec, room, villagers, furniture, clothing=None):
    evidence(base)
    profile = profile_bytes(villagers, furniture, clothing)
    if (len(blob) != BLOB_SIZE or not helper or len(helper) > LIMIT - CODE or any(blob[CODE:LIMIT])
            or any(blob[BRIDGE:BRIDGE + 32]) or any(blob[PROFILE_OFFSET:PROFILE_OFFSET + len(profile)])
            or 0x8000 + room['bytes'] > CODE or 0xB400 + codec['bytes'] > BRIDGE
            or codec['symbols']['af_v3_save_check'] != 0x8046B400
            or codec['symbols']['af_v3_save_pack'] != 0x8046B7A0):
        raise ValueError('Save runtime overlaps existing data or uses a changed codec ABI')
    for start, end, digest in CODE_GUARDS + TRAVEL_GUARDS:
        if sha256(code[start - CODE_RAM:end - CODE_RAM]) != digest:
            raise ValueError(f'Changed complete native save owner: {start:08X}')
    # Every direct bank-reader reference in the retail image is in this audited
    # main-code list. Reject new direct callers or address-taken references.
    observed = []
    for vrom, entry in by_vrom(native).items():
        data = entry.extract(native)
        for at in range(0, len(data) - 3, 4):
            word = struct.unpack_from('>I', data, at)[0]
            if word == 0x8008F8A0:
                raise ValueError('Unexpected address-taken bank reader')
            if word == 0x0C023E28:
                observed.append((vrom, at + CODE_RAM))
    if observed != [(CODE_VROM, a) for a in READ_CALLS]:
        raise ValueError('Bank-reader caller set differs from the capacity audit')
    patches = []
    jump = lambda target: 0x08000000 | (target >> 2 & 0x3FFFFFF)
    jal = lambda target: 0x0C000000 | (target >> 2 & 0x3FFFFFF)

    def target(name):
        address = symbols[name]
        if not 0x80460000 + CODE <= address < 0x80460000 + CODE + len(helper) or address & 3:
            raise ValueError('Invalid save-runtime target')
        return address

    def write(address, before, after):
        at = address - CODE_RAM
        if bytes(code[at:at + len(before)]) != before or len(before) != len(after):
            raise ValueError(f'Changed save instruction window {address:08X}')
        code[at:at + len(after)] = after
        patches.append({'address': address, 'before': before.hex(), 'after': after.hex()})

    def word(address, before, after):
        write(address, struct.pack('>I', before), struct.pack('>I', after))

    for i, (address, name, prologue) in enumerate((
            (0x8008F8A0, 'af_v3_save_read', (0x27BDFFC8, 0xAFB2001C)),
            (0x8008EF94, 'af_v3_save_clear', (0x27BDFFE8, 0xAFBF0014)))):
        struct.pack_into('>4I', blob, BRIDGE + i * 16, *prologue, jump(address + 8), 0)
        write(address, struct.pack('>II', *prologue), struct.pack('>II', jump(target(name)), 0))
    write(0x8008EEE8, bytes.fromhex('8c8e00043c014e41'),
          struct.pack('>II', jump(target('af_v3_save_signature')), 0))
    write(0x8008F7C8, bytes.fromhex('27bdffc8afb00018'),
          struct.pack('>II', jump(target('af_v3_save_sync')), 0))
    write(0x8008F938, bytes.fromhex('27bdffe8afbf0014'), struct.pack('>II', jump(0x8008F968), 0))
    word(0x8008F8D4, 0x265301F3, 0x26530200)  # Read 512 complete bank pages.
    for address in ALLOCATIONS:
        word(address, 0x3404F980, 0x3C040001)  # 64-KiB private heap/framebuffer buffers.
    word(0x8008F4B8, 0x3406F980, 0x3C060001)  # Include normalised extension in comparison.
    for address in PREPARE_CALLS:
        word(address, jal(0x8008EFDC), jal(target('af_v3_save_prepare')))
    word(0x8008F9EC, jal(0x800360E0), jal(target('af_v3_save_commit')))
    blob[PROFILE_OFFSET:PROFILE_OFFSET + len(profile)] = profile
    blob[CODE:CODE + len(helper)] = helper
    return {'patches': patches, 'native_save_hooks_enabled': True,
            'native_catalogue_hooks_enabled': False, 'bank_bytes': BANK,
            'native_live_payload_bytes': 0xF980, 'state_ram': STATE_RAM,
            'state_bytes': STATE_BYTES+(160 if clothing is not None else 0),
            'current_profile_ram': 0x80460000 + PROFILE_OFFSET, 'profile_hex': profile.hex(),
            'profile_sha256': sha256(profile), 'native_reader_calls_audited': len(READ_CALLS),
            'legacy_padding_normalised': True, 'incompatible_profile': 'English instruction screen; stop caller without writing',
            'synchronous_writer_banks': 1, 'asynchronous_writer_banks': 2,
            'controller_pak_profile_transport': 'pending; only town FlashRAM preparation/readback is integrated',
            'native_save_reload_tested': False}
