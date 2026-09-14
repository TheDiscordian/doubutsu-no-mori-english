"""Current native furniture loading/lifetime checks; no placement or save writes."""
import json
import math
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
    blob = files[BLOB].extract(rom)[:report['resident_blob_bytes']]
    furniture = report['furniture']
    animated = [report['speed_bag']] if report.get('speed_bag') else []
    displays = furniture.get('display_imports', [])
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
        for row in furniture['imports'] + displays + animated:
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

    for row in animated:
        index, item = row['runtime_index'], int(row['item_id'], 16)
        row_ram = int(row['row_ram'], 16)
        if row['selectable'] or row['enabled'] and not row['saved_profile_included']:
            raise ValueError('Animated fixture requires a private, profile-bound development item')
        initial_enabled = int(row['enabled'])
        check('animated item has its recorded initial eligibility', row_ram+4, struct.pack('>I',initial_enabled))
        write_word(row_ram+4,0)
        native(0x8093678C, [index], 0)
        call(0x800A5630, [item], 0)
        start = int(row['object_vrom'], 16)
        asset = object_bytes(start, start+row['object_bytes'])
        if sha256(asset) != row['object_sha256']:
            raise ValueError('Changed installed animated model')
        expected = asset+b'\xA5'*(BANK_BYTES-len(asset))
        saved_state = debug.read_memory(0x8046C000, 864)
        write_word(row_ram+4, 1)
        native(0x8093678C, [index], 1)
        debug.write_memory(bank0, b'\xA5'*BANK_BYTES)
        native(0x809389AC, [index, 0, item], 1)
        check('complete animated model, rig, and untouched bank padding', bank0, expected)
        for rotation in range(4):
            native(0x80942688, [index, rotation], item | rotation)
            call(0x800A5630, [item | rotation], 10)
            call(0x800C0194, [item | rotation], row['price'])
        text_at, actor, bridge = allocation+0x1DF00, allocation+0x1D000, allocation+0x1D800
        call(0x801969C8, [text_at, 16, item], 1)
        check('complete installed animated English name', text_at, b'speed bag       ')
        table_at = int(row['vtable_ram'], 16)
        expected_table = struct.pack('>5I', *row['callback_entries'], 0, 0)
        check('complete production callback table', table_at, expected_table)
        for kind, target in zip(('ct', 'mv'), row['callback_entries'][:2]):
            wrapper = struct.pack('>2I', 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
            debug.write_memory(bridge, wrapper)
            call(0x8002FE00, [bridge, len(wrapper)])
            call(0x80034CE0, [bridge, len(wrapper)])
            if kind == 'ct':
                saved_segment = debug.read_memory(0x801458B8, 4)
                saved_audio_scene = debug.read_memory(0x80113844, 1)[0]
                # Positional sounds are intentionally disabled in scene zero
                # (the title checkpoint). Enter the native outdoor audio mode,
                # and use its real listener position rather than assuming zero.
                call(0x800FB3E8, [1])
                check('native positional audio scene enabled', 0x80113844, b'\x01')
                listener = call(0x80060D6C, [word(0x8010EF90)])
                if listener & 3 or not 0x80000400 <= listener <= 0x80400000-12:
                    raise ValueError('Native microphone pointer escapes checked RAM')
                position = list(struct.unpack('>3f', debug.read_memory(listener, 12)))
                if not all(math.isfinite(value) for value in position):
                    raise ValueError('Native microphone is not initialised for this fixture')
                position[0] += 12
                write_word(0x801458B8, bank0-0x80000000)
                debug.write_memory(actor, bytes(0x740))
                debug.write_memory(actor+8, struct.pack('>3f', *position))
            else:
                debug.write_memory(actor+0x12D, b'\x01')
            call(bridge, [actor, 0, 0, bank0], proof=(bridge, wrapper))
            if kind == 'ct':
                check('installed constructor resolves both loaded rig headers', actor+0x14C,
                      struct.pack('>2I', bank0+0xE84, bank0+0xE58))
                check('installed constructor evaluates the initial pose', actor+0x1A4,
                      struct.pack('>9h', 800, 6508, 800, 0, 0, -16384, 0, 0, 0))
                check('installed constructor keeps idle speed', actor+0x140, bytes(4))
            else:
                check('installed hit starts the donor animation', actor+0x140,
                      struct.pack('>2f', .5, 1))
                slots = debug.read_memory(0x80113C34, 6*32)
                hits = [i for i in range(6) if struct.unpack_from('>H', slots, i*32)[0] == 0x169]
                if len(hits) != 1 or slots[hits[0]*32+28] != 70:
                    raise ValueError('Installed positional callback did not dispatch the actual donor sound')
                record({'installed_animated_positional_sound': '0169', 'track': hits[0], 'priority': 70,
                        'pcm_or_listening_verified': False})
        debug.write_memory(0x801458B8, saved_segment)
        call(0x800FB3E8, [saved_audio_scene])
        check('native audio scene restored', 0x80113844, bytes((saved_audio_scene,)))
        check('animated callbacks retain complete loaded model', bank0, expected)
        native(0x80937C84, [index])
        native(0x809374C4, [index], 0xFFFFFFFF)
        write_word(row_ram+4, 0)
        call(0x800A5630, [item], 0)
        write_word(row_ram+4,initial_enabled)
        check('animated component retains the complete save runtime', 0x8046C000, saved_state)

    if displays:
        from v3_clothing_display import MODEL, MODEL_BYTES, PROGRAM, SIZE as DISPLAY_BYTES
        if len(displays) != 1 or not report.get('clothing', {}).get('display'):
            raise ValueError('Unbound clothing display fixture')
        display = displays[0]
        info = report['clothing']['display']
        garment = report['clothing']['imports'][0]
        index, item = display['runtime_index'], int(display['item_id'], 16)
        start = int(garment['vrom'], 16)
        shirt = object_bytes(start, start+544)
        model = object_bytes(MODEL, MODEL+MODEL_BYTES)
        if sha256(model) != info['model_sha256'] or info['bank_bytes_used'] != len(shirt+model):
            raise ValueError('Changed native clothing model layout')
        expected = shirt+model+b'\xA5'*(BANK_BYTES-len(shirt+model))
        native(0x8093678C, [index], 1)
        for rotation in range(4):
            debug.write_memory(bank0, b'\xA5'*BANK_BYTES)
            if rotation == 0:
                native(0x809389AC, [index, 0, item], 1)
            else:
                native(0x8093885C, [index, item | rotation, bank0, 0xFFFFFFFF], 1)
            check('clothing mannequin full texture/palette/model and padding', bank0, expected)
            native(0x80942688, [index, rotation], item | rotation)
        native(0x809374C4, [index], 0)
        program = blob[PROGRAM:PROGRAM+DISPLAY_BYTES]
        if sha256(program) != info['program_sha256']:
            raise ValueError('Changed complete clothing callback program')
        # Call the retained native draw callback into private CPU-side lists;
        # this checks its exact commands, not an ordinary GPU-rendered scene.
        game, graph, commands = (allocation+n for n in (0x1D000, 0x1D100, 0x1D500))
        debug.write_memory(game, bytes(0x800))
        write_word(game, graph)
        write_word(graph+0x298, commands)
        check('complete resident mannequin before draw callback', 0x80460000+PROGRAM, program)
        # The existing call helper only accepts entry addresses below 4 MiB.
        # Use a checked jump in this private allocation, after native cache
        # maintenance; the executed callback remains in its installed location.
        bridge = allocation+0x1D700
        wrapper = struct.pack('>2I', 0x08000000 | (int(info['draw_ram'], 16) >> 2 & 0x3FFFFFF), 0)
        debug.write_memory(bridge, wrapper)
        call(0x8002FE00, [bridge, len(wrapper)])
        call(0x80034CE0, [bridge, len(wrapper)])
        call(bridge, [0, 0, game, bank0], proof=(bridge, wrapper))
        check('native mannequin complete draw commands', commands,
              struct.pack('>8I', 0xDB060018, bank0+0x220, 0xDB060020, bank0,
                          0xDB060024, bank0+0x200, 0xDE000000, 0x06000390))
        check('native mannequin command pointer', graph+0x298, struct.pack('>I', commands+32))
        check('native mannequin draw does not overrun its commands', commands+32, bytes(32))
        native(0x80937C84, [index])
        native(0x809374C4, [index], 0xFFFFFFFF)
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
    for row in rows + displays + animated:
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
            'installed_animated_model_constructor_hit_sound': len(animated),
            'clothing_display_native_model_and_commands': len(displays),
            'native_bank_selection_release_and_cleanup': True,
            'ordinary_placement_tested': False, 'rendering_tested': False,
            'save_reload_tested': False, 'requires_checkpoint_restore': True}
