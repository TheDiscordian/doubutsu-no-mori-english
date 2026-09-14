"""Current native submenu icon selection and complete drawing-command generation."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import by_vrom, sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_furniture_icon import BLOB_SIZE, DRAW, END, LEAF, RAM, RELOC, RESIDENT, SECTIONS, SIZE, START, VROM
from v3_furniture_room_smoke import extend
from v3_npc_draw_smoke import boot_proofs


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_text())
    icon = report.get('furniture_icon')
    if sha256(rom) != report['output_sha256'] or not icon:
        raise ValueError('Icon probe requires its exact current cartridge')
    files, boot = by_vrom(rom), boot_proofs(rom)
    blob = files[BLOB].extract(rom)[:BLOB_SIZE]
    edge = b'V3IC' * 4

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'icon_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Icon native check failed: ' + label)

    def call(address, args, proof=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                            verified_code=proof or boot.get(address))
        record(result)
        return result['return_value']

    def put(at, *values):
        debug.write_memory(at, struct.pack('>' + 'I' * len(values), *values))

    check('complete current startup prefix', BLOB_RAM, blob)
    size = 0x18000
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x80400000 - size:
        raise ValueError('Icon fixture allocation failed')
    root, graph, gfx, stack = (allocation + n for n in (16, 0x14000, 0x14600, 0x16800))
    debug.write_memory(allocation, bytes(size))
    data, reloc = (files[v].extract(rom) for v in (VROM, RELOC))
    if sha256(data) != icon['output_sha256'] or sha256(reloc) != icon['relocation_sha256']:
        raise ValueError('Changed submenu parent proof')
    loaded = relocate_verified_data(SimpleNamespace(ram=RAM, resident_bytes=RESIDENT, sections=SECTIONS),
        data, reloc, root, address_constants=(RAM + RESIDENT,))
    call(0x800262D0, [VROM, VROM + SIZE, RAM, RAM + RESIDENT, root, root + RESIDENT, len(reloc)])
    check('complete native-relocated current parent and BSS', root, loaded)
    proof = (root, loaded[:SECTIONS[0]])
    saved_parent = debug.read_memory(0x8010DCEC, 4)
    put(0x8010DCEC, root)
    guards = (allocation, graph - 16, gfx - 16, gfx + 0x1000, stack - 0x800,
              stack + 0x200, allocation + size - 16, TEST_STACK - 0x800, TEST_STACK + 0x40)
    for at in guards:
        debug.write_memory(at, edge)
    before = debug.command('g')
    original_regs = [int(before[i:i + 16], 16) for i in range(0, len(before), 16)]
    if len(original_regs) != 71 or original_regs[37] & 0xFFFFFFFF != 0x800D334C:
        raise ValueError('Icon windows require the paused game frame')

    def window(regs, target):
        breakpoint = f'0,{target:x},4'
        if debug.command('Z' + breakpoint) != 'OK':
            raise ValueError('Icon breakpoint refused')
        try:
            if debug.command('G' + ''.join(f'{n:016x}' for n in regs)) != 'OK':
                raise ValueError('Icon register write refused')
            stopped = debug.command('c')
            raw = debug.command('g')
            actual = [int(raw[i:i + 16], 16) for i in range(0, len(raw), 16)]
            if stopped[:3] not in ('T05', 'S05') or actual[37] & 0xFFFFFFFF != target:
                raise ValueError(f'Icon window missed its continuation: {stopped}/{actual[37]:016X}')
            return actual
        finally:
            debug.command('z' + breakpoint)
            debug.command('G' + before)

    for item, selected, disabled in ((0x1004, False, False), (0x3225, True, False),
                                     (0x32BB, True, False), (0x32BB, False, True),
                                     (0x3000, False, False)):
        if disabled:
            put(BLOB_RAM + 0x7254, 0)
        try:
            regs = original_regs.copy()
            for i in range(1, 32):
                if i not in (26, 27):
                    regs[i] = (0x13579000 + i) << 32 | (0x2468A000 + i)
            regs[16], regs[25] = item, item & 0xF000
            regs[29], regs[37] = extend(stack), extend(root + START - RAM)
            wanted = regs.copy()
            wanted[1], wanted[9] = 1, 1 if selected else item >> 12
            actual = window(regs, root + END - RAM)
            differences = {str(i): [f'{wanted[i]:016X}', f'{actual[i]:016X}']
                for i in (*range(26), 28, 29, 30, 31, 33, 34, *range(38, 70)) if wanted[i] != actual[i]}
            record({'icon_type_window': f'{item:04X}', 'selected': selected,
                    'disabled_profile': disabled, 'register_differences': differences,
                    'assertion': 'failed' if differences else 'passed'})
            if differences:
                raise ValueError('Icon classification changed unrelated registers')
        finally:
            if disabled:
                put(BLOB_RAM + 0x7254, 1)

    cases = ((0x1004, 0, 0, LEAF), (0x3225, 0, 0, LEAF), (0x32BB, 0, 0, LEAF),
             (0x15B0, 0, 0, 0x8085DD00), (0x1E3C, 0, 0, 0x8085DD08),
             (0x3225, 1, 1, 0x8085DD18))
    for item, wrapped, variant, descriptor in cases:
        put(stack + 0xC0, item, wrapped, 1, variant, 0)
        regs = original_regs.copy()
        regs[6], regs[7], regs[14] = extend(0xFFFFFFFF), 0, wrapped
        regs[29], regs[37] = extend(stack), extend(root + 0x8085C7F4 - RAM)
        actual = window(regs, root + DRAW - RAM)
        passed = actual[5] & 0xFFFFFFFF == root + descriptor - RAM
        record({'native_icon_selection': f'{item:04X}', 'wrapped': wrapped,
                'descriptor': f'{actual[5] & 0xFFFFFFFF:08X}',
                'assertion': 'passed' if passed else 'failed'})
        if not passed:
            raise ValueError('Native icon selected an incorrect descriptor')
        check('icon selection retains complete item/condition arguments', stack + 0xC0,
              struct.pack('>5I', item, wrapped, 1, variant, 0))

    drawings = []
    # Execute the entire actual draw function into private command storage.
    # No display list is submitted to the GPU and no image is presented.
    for item, wrapped, variant, _ in cases:
        debug.write_memory(gfx, bytes(0x1000))
        put(graph + 0x298, gfx, gfx + 0x1000)
        call(root + 0x8085C7B8 - RAM, [graph, 0, 0, 0x3F800000, item, wrapped, 1, variant, 0], proof)
        end = int.from_bytes(debug.read_memory(graph + 0x298, 4), 'big')
        if not gfx < end <= gfx + 0x1000 or (end - gfx) % 8:
            raise ValueError('Native icon draw escaped its command storage')
        commands = debug.read_memory(gfx, end - gfx)
        drawings.append(commands)
        record({'native_icon_draw': f'{item:04X}', 'wrapped': wrapped,
                'commands': len(commands) // 8, 'sha256': sha256(commands)})
    if drawings[1:3] != [drawings[0], drawings[0]] or any(drawings[i] == drawings[0] for i in (3, 4, 5)):
        raise ValueError('Imported leaf commands or retained special icons differ from expectations')
    record({'imported_icons_match_complete_native_leaf_commands': True,
            'gyroid_fossil_and_gift_commands_remain_distinct': True, 'assertion': 'passed'})
    check('complete resident prefix unchanged', BLOB_RAM, blob)
    check('complete parent and BSS unchanged by icon operations', root, loaded)
    for at in guards:
        check('fixture guard', at, edge)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    debug.write_memory(0x8010DCEC, saved_parent)
    call(0x8009C040, [allocation])
    return {'icon_register_windows': 5, 'native_icon_descriptor_cases': 6,
            'complete_native_icon_draw_cases': 6, 'gpu_rendered': False,
            'ordinary_inventory_tested': False, 'save_reload_tested': False,
            'requires_checkpoint_restore': True}
