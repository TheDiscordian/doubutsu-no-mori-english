"""Current native furniture loading/lifetime checks; no placement or save writes."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import by_vrom, sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_furniture_runtime import (BANK_BYTES, BLOB_SIZE, CAPACITY, INDICES, NATIVE_COUNT,
                                 PROFILES, RAM, RELOC, RESIDENT, SIZE, VROM)
from v3_npc_draw_smoke import boot_proofs


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom = path.read_bytes()
    report = json.loads((path.parent / 'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['furniture']:
        raise ValueError('Furniture probe requires its exact current cartridge')
    files = by_vrom(rom)
    blob = files[BLOB].extract(rom)[:BLOB_SIZE]
    furniture = report['furniture']
    expanded = furniture.get('expanded_tables')
    profile_ram = int(furniture['profile_table_ram'], 16)
    index_ram = int(furniture['bank_index_ram'], 16)
    capacity = furniture['capacity']
    expanded_initial = debug.read_memory(int(expanded['reservation_start'], 16),
                                       expanded['reservation_bytes']) if expanded else None
    boot = boot_proofs(rom)
    edge = b'V3FU' * 4

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'v3_furniture_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected:
            raise ValueError('V3 furniture check failed: ' + label)

    def call(address, args, expected=None, proof=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                            verified_code=proof if proof is not None else boot.get(address))
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Furniture native call {address:08X}: '
                             f'{result["return_value"]:08X} != {expected:08X}')
        return result['return_value']

    def word(at):
        return struct.unpack('>I', debug.read_memory(at, 4))[0]

    def write_word(at, value):
        debug.write_memory(at, struct.pack('>I', value))

    def object_bytes(start, end):
        entry = next(e for e in files.values() if e.vstart <= start < end <= e.vend)
        return entry.extract(rom)[start - entry.vstart:end - entry.vstart]

    check('complete startup resident prefix', BLOB_RAM, blob)
    check('installed', 0x8019ACD0, struct.pack('>I', 1))
    if expanded:
        from v3_furniture_tables import START, END, EDGE
        check('expanded leading guard', START, struct.pack('>I', EDGE)*4)
        check('expanded trailing guard', END-16, struct.pack('>I', EDGE)*4)
        expected_profiles = bytearray(capacity*4)
        for row in furniture['imports']:
            struct.pack_into('>I', expected_profiles, row['runtime_index']*4, int(row['profile_ram'], 16))
        check('complete expanded startup profiles', profile_ram, bytes(expected_profiles))
        check('complete expanded startup banks', index_ram, b'\xFF'*capacity)
    allocation_size = 0x1E000
    allocation = call(0x8009BFC0, [allocation_size])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x80400000 - allocation_size:
        raise ValueError('Furniture probe could not allocate its isolated fixture')
    live = allocation + 16
    data, reloc = (files[v].extract(rom) for v in (VROM, RELOC))
    owner = furniture['owner']
    if (sha256(data) != (expanded['output_sha256'] if expanded else owner['output_sha256']) or
            sha256(reloc) != owner['output_relocation_sha256']):
        raise ValueError('Changed furniture owner or relocations')
    sections = struct.unpack_from('>5I', reloc)
    spec = SimpleNamespace(ram=RAM, resident_bytes=RESIDENT, sections=sections)
    loaded = relocate_verified_data(spec, data, reloc, live)
    bank0 = live + RESIDENT + len(reloc) + 32
    bank1 = bank0 + BANK_BYTES + 32
    guards = (allocation, allocation + allocation_size - 16,
              bank0 - 16, bank0 + BANK_BYTES, bank1 - 16, bank1 + BANK_BYTES,
              TEST_STACK - 0x800, TEST_STACK + 0x40)
    if bank1 + BANK_BYTES + 16 > allocation + allocation_size - 16:
        raise ValueError('Furniture fixture banks exceed allocation')
    for at in guards:
        debug.write_memory(at, edge)
    call(0x800262D0, [VROM, VROM + SIZE, RAM, RAM + RESIDENT,
                     live, live + RESIDENT, len(reloc)])
    check('complete native-relocated owner and BSS', live, loaded)
    proof = (live, loaded[:sections[0]])

    def native(address, args=(), expected=None):
        return call(live + address - RAM, list(args), expected, proof)

    check('owner descriptor', 0x80100DF0, struct.pack('>4I', VROM, VROM + SIZE, RAM, RAM + RESIDENT))
    saved_owner, saved_limit = word(0x80100E00), word(0x80136ECC)
    write_word(0x80100E00, live)
    write_word(0x80136ECC, 2)
    native(0x80936710)
    native(0x80938C24)
    check('complete expanded bank reset', index_ram, b'\xFF' * capacity)
    check('original profile prefix cleared', profile_ram, bytes(NATIVE_COUNT * 4))
    write_word(live + 0x18D68, bank0)
    write_word(live + 0x18D6C, bank1)
    rows = furniture['imports']
    if len(rows) != 2:
        raise ValueError('Furniture fixture requires the two reviewed static pilots')
    payloads = []
    for slot, row in enumerate(rows):
        index, item, bank = row['runtime_index'], int(row['item_id'], 16), (bank0, bank1)[slot]
        start = int(row['object_vrom'], 16)
        asset = object_bytes(start, start + row['object_bytes'])
        if sha256(asset) != row['object_sha256']:
            raise ValueError('Furniture fixture asset hash changed')
        payload = asset + b'\xA5' * (BANK_BYTES - len(asset))
        payloads.append(payload)
        native(0x8093678C, [index], 1)
        debug.write_memory(bank, b'\xA5' * BANK_BYTES)
        # The actual native bank selector calls the imported DMA bridge.
        native(0x809389AC, [index, 0, item], 1)
        check(row['name'] + ' full model DMA and untouched bank padding', bank, payload)
        native(0x80937490, [index], 1)
        native(0x809374C4, [index], slot)
        native(0x809374F4, [slot], bank)
        for rotation in range(4):
            native(0x80942688, [index, rotation], item | rotation)
    native(0x80937578, [], 0)
    native(0x809375E8, [], 0xFFFFFFFF)
    first = rows[0]
    debug.write_memory(bank0, b'\xA5' * BANK_BYTES)
    native(0x8093885C, [first['runtime_index'], int(first['item_id'], 16), bank0, 0xFFFFFFFF], 1)
    check('imported existing-bank reload', bank0, payloads[0])
    for index in (947, 1024, capacity, 65535):
        native(0x8093678C, [index], 0)
        native(0x809374C4, [index], 0xFFFFFFFF)
        native(0x80942688, [index, 0], 0x1ECC if index == 947 else 0x1088)
    native(0x809374F4, [100], 0)
    native(0x809374F4, [0xFFFFFFFF], 0)
    # No actor objects are constructed by this fixture. The native empty actor
    # list lets the normal last-user release path free the first model bank.
    check('empty fixture actor count', live + 0x80947568 - RAM, bytes(4))
    native(0x80937C84, [first['runtime_index']])
    native(0x809374C4, [first['runtime_index']], 0xFFFFFFFF)
    native(0x80937578, [], 1)
    native(0x809375E8, [], 0)

    # Original item zero must still allocate/relocate its own native profile
    # and execute the retained native model-DMA body through both bridges.
    native(0x8093678C, [0], 1)
    original_allocation = word(live + 0x8094D320 - RAM)
    original_profile = word(profile_ram)
    if not original_allocation or original_profile != original_allocation + 0x314:
        raise ValueError('Original furniture profile allocation/symbol mapping changed')
    start, end, segment, limit = struct.unpack('>4I', debug.read_memory(original_profile, 16))
    asset = object_bytes(start, end)
    if segment != 0x06000000 or limit - segment != len(asset) or len(asset) > BANK_BYTES:
        raise ValueError('Original furniture model no longer fits the native bank')
    debug.write_memory(bank0, b'\xA5' * BANK_BYTES)
    native(0x8093885C, [0, 0x1000, bank0, 0], 1)
    check('original native model DMA and padding retained', bank0,
          asset + b'\xA5' * (BANK_BYTES - len(asset)))
    native(0x809374C4, [0], 0)
    native(0x8093690C)
    check('original heap profile allocation released', live + 0x8094D320 - RAM, bytes(4))
    check('original resolved profile cleared', profile_ram, bytes(4))
    for row in rows:
        check('resident imported profile survives native cleanup',
              profile_ram + row['runtime_index'] * 4,
              struct.pack('>I', int(row['profile_ram'], 16)))
    native(0x80938C24)
    check('complete resident prefix restored after bank/profile cleanup', BLOB_RAM, blob)
    if expanded:
        check('complete expanded reservation restored after native cleanup', START, expanded_initial)
    for at in guards:
        check('fixture guard', at, edge)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    write_word(0x80100E00, saved_owner)
    write_word(0x80136ECC, saved_limit)
    call(0x8009C040, [allocation])
    return {'imported_models_native_dma': 2, 'native_profile_and_model_fallback': True,
            'native_bank_selection_release_and_cleanup': True,
            'ordinary_placement_tested': False, 'rendering_tested': False,
            'save_reload_tested': False, 'requires_checkpoint_restore': True}
