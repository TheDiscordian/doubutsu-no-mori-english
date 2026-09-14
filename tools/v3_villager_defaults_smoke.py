"""Bounded native initialization, clothing DMA, and personality checks."""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from runtime_layout import MODULE_RAM, TEST_STACK
from textbanks import banks
from v3_asset_loader import BLOB, BLOB_RAM


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom = path.read_bytes(); report = json.loads((path.parent / 'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['villager_text']:
        raise ValueError('V3 defaults probe requires its exact current cartridge')
    files = by_vrom(rom); blob = files[BLOB].extract(rom)[:0xC000]
    actor, animal = MODULE_RAM + 0x6500, MODULE_RAM + 0x6690
    output, default_table = MODULE_RAM + 0x6D00, MODULE_RAM + 0x7000
    cloth_tex, cloth_pal = MODULE_RAM + 0x6D30, MODULE_RAM + 0x6F50
    edge = b'V3DF' * 4

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'v3_defaults_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected: raise ValueError('V3 defaults check failed: ' + label)

    def call(address, args, expected=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError('Unexpected native V3 defaults return value')

    def expected_animal(npc, looks, cloth, phrase):
        data = bytearray(b'\xA5' * 0x540)
        struct.pack_into('>HH', data, 0, npc, 0x1234)
        data[4:10] = b'Forest'; data[0xB] = looks
        data[0x4E5:0x4E9] = phrase
        struct.pack_into('>H', data, 0x520, cloth)
        return bytes(data)

    check('startup blob', BLOB_RAM, blob)
    check('installed state', 0x8019ACD0, struct.pack('>I', 1))
    # In-memory fixture only. The mandatory checkpoint restore discards it; no
    # FlashRAM/Pak write is enabled and no existing game save is opened.
    land_before = debug.read_memory(0x80129E00, 10)
    debug.write_memory(0x80129E00, b'Forest!!\x12\x34')
    actor_data = bytearray(0x180); actor_data[2] = 3
    struct.pack_into('>I', actor_data, 0x174, animal)
    debug.write_memory(actor, actor_data)
    guards = (actor - 16, actor + 0x180, animal + 0x540, output - 16, output + 16,
              default_table - 16, default_table + 1312, cloth_tex - 16, cloth_tex + 512,
              cloth_pal - 16, cloth_pal + 32, TEST_STACK - 0x800, TEST_STACK + 0x40)
    for address in guards: debug.write_memory(address, edge)
    defaults = files[0xE03000].extract(rom)
    debug.write_memory(default_table, defaults)
    cheri, punchy = report['villager_text']['imports']
    if not cheri['initial_defaults_applied']:
        raise ValueError('Missing installed pilot defaults')
    active = [cheri, punchy] if punchy['initial_defaults_applied'] else [cheri]
    for row in active:
        npc_id = int(row['actor_id'],16)
        cloth = int(row.get('applied_clothing_id') or row['clothing_identity']['native_item_id'],16)
        expected = expected_animal(npc_id, row['personality'], cloth, bytes.fromhex(row['saved_default_key']))
        for address, args in ((0x800AA29C, [animal, npc_id, default_table]),
                              (0x800AA218, [animal, npc_id, 255, 0]),
                              (0x800AD8C4, [animal, npc_id & 255])):
            debug.write_memory(animal, b'\xA5' * 0x540)
            call(address, args)
            check(row['name']+' complete initializer write set', animal, expected)
        call(0x8019521C, [output, actor])
        check('initialized full phrase reaches dialogue reader', output, row['catchphrase'].encode().ljust(10,b' '))
        call(0x80195D20, [output, actor])
        check('initialized identity reaches full-name reader', output, row['name'].encode().ljust(8,b' '))
    if punchy['initial_defaults_applied']:
        selected = debug.read_memory(0x8046282A,1)
        try:
            debug.write_memory(0x8046282A,bytes(1))
            call(0x800AD8C4,[animal,237])
            check('missing actual imported shirt is no-write',animal,expected)
        finally:
            debug.write_memory(0x8046282A,selected)
    for npc, looks in ((0xE0EA, 1), (0xE0ED, 2), (0xE0DA, 0), (0xEFFF, 0), (0xD008, 0)):
        call(0x800AA1E0, [npc], looks)
    native_code = files[CODE_VROM].extract(rom)
    for npc in (0xE000, 0xE0D9):
        call(0x800AA1E0, [npc], native_code[0x8010AF58 - CODE_RAM + (npc & 0xFFF)])
    for npc in ((0xE0DA,) if punchy['initial_defaults_applied'] else (0xE0DA,0xE0ED)):
        for address, args in ((0x800AA29C, [animal, npc, default_table]),
                              (0x800AA218, [animal, npc, 0, default_table]),
                              (0x800AD8C4, [animal, npc & 0xFFF])):
            call(address, args)
            check('missing or incomplete import is no-write', animal, expected)
    # Each original route must retain the full native default/string DMA path.
    native = (Path(__file__).resolve().parents[1] / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
    strings = next(b for b in banks(native) if b.name == 'string').entries()
    for address, npc in ((0x800AA29C, 0xE0D9), (0x800AA218, 0xE000), (0x800AD8C4, 0xE000)):
        index = npc & 0xFFF
        cloth, phrase_index = struct.unpack_from('>HH', defaults, index * 6)
        looks = native_code[0x8010AF58 - CODE_RAM + index]
        args = {0x800AA29C: [animal, npc, default_table],
                0x800AA218: [animal, npc, looks, default_table + index * 6],
                0x800AD8C4: [animal, index]}[address]
        debug.write_memory(animal, b'\xA5' * 0x540)
        call(address, args)
        expected = expected_animal(npc, looks, cloth, strings[phrase_index].ljust(4, b' '))
        check('original initializer and four-byte phrase retained', animal, expected)
    # Exercise the real shared 32x32 clothing/palette reader, not only its hashes.
    call(0x800B1EDC, [cloth_tex, cloth_pal, 0x98])
    check('native complete yellow-bar texture DMA', cloth_tex, files[0xB68000].extract(rom)[0x13000:0x13200])
    check('native complete yellow-bar palette DMA', cloth_pal, files[0xB88000].extract(rom)[0x1300:0x1320])
    if punchy['initial_defaults_applied']:
        call(0x800B1EDC,[cloth_tex,cloth_pal,0x10BF])
        garment = files[BLOB].extract(rom)[0xF000:0xF220]
        check('complete imported cherry-shirt texture DMA',cloth_tex,garment[:512])
        check('complete imported cherry-shirt palette DMA',cloth_pal,garment[512:])
        saved = {at:debug.read_memory(at,n) for at,n in
                 ((0x80461E60,20),(0x80464700,32),(0x8013670C,32),(0x80130DB8,15*0x528))}
        try:
            debug.write_memory(0x80130DB8,bytes(15*0x528))
            history = bytearray(b'\xFF'*32);history[237//8] &= ~(1 << (237&7))
            debug.write_memory(0x8013670C,history)
            call(0x800AD6D4,[2],0xFFFFFFFF)
            debug.write_memory(0x80461E73,b'\x01')
            call(0x800AD6D4,[2],237)
            debug.write_memory(0x8046282A,bytes(1))
            call(0x800AD6D4,[2],0xFFFFFFFF)
        finally:
            debug.write_memory(0x8046282A,selected)
            for at,data in saved.items():debug.write_memory(at,data)
    for address in guards: check('fixture guard', address, edge)
    check('source defaults table retained', default_table, defaults)
    check('land source retained', 0x80129E00, b'Forest!!\x12\x34')
    check('immutable V3 blob', BLOB_RAM, blob)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    debug.write_memory(0x80129E00, land_before)
    return {'native_initialization_routes': 3*len(active), 'imported_personalities': 2,
            'native_clothing_dma_tested': True, 'original_initialization_retained': True,
            'ordinary_move_in_tested': False, 'save_reload_tested': False,
            'requires_checkpoint_restore': True}
