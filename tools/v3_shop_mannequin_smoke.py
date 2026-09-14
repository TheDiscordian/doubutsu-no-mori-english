"""Complete native mannequin counting, placement search, and garment transfers."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import by_vrom, sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_npc_draw_smoke import boot_proofs
from v3_shop_mannequin import VROM, RELOC, RAM, SIZE, POINTER, SECTIONS


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent/'build.json').read_text())
    mannequin = report['clothing'].get('mannequin')
    if sha256(rom) != report['output_sha256'] or not mannequin:
        raise ValueError('Mannequin check requires its exact installed cartridge')
    files, boot = by_vrom(rom), boot_proofs(rom)
    blob = files[BLOB].extract(rom)
    calls = 0

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'mannequin_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected: raise ValueError('Mannequin mismatch: '+label)

    def call(address, args, expected=None, proof=None):
        nonlocal calls
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM+0x6480,
                            verified_code=proof or boot.get(address))
        record(result); calls += 1
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Unexpected mannequin result at {address:08X}')
        return result['return_value']

    def put(at, value): debug.write_memory(at, struct.pack('>I', value))

    check('complete current prefix', BLOB_RAM, blob[:0xC000])
    allocation = call(0x8009BFC0, [0x4000])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x803FC000:
        raise ValueError('Mannequin fixture allocation failed')
    owner, field, block, grid, actor, slots, output, clip, buffers = (
        allocation+n for n in (16, 0x1400, 0x1800, 0x2000, 0x2400, 0x2600, 0x2800, 0x2840, 0x3000))
    debug.write_memory(allocation, bytes(0x4000))
    data, reloc = (files[v].extract(rom) for v in (VROM, RELOC))
    if sha256(data) != mannequin['output_sha256'] or sha256(reloc) != mannequin['relocation_sha256']:
        raise ValueError('Changed installed mannequin owner')
    loaded = relocate_verified_data(SimpleNamespace(ram=RAM, resident_bytes=SIZE, sections=SECTIONS), data, reloc, owner)
    call(0x800262D0, [VROM, VROM+SIZE, RAM, RAM+SIZE, owner, owner+SIZE, len(reloc)])
    check('complete native-relocated owner', owner, loaded)
    proof = (owner, loaded)
    saved = {at: debug.read_memory(at, size) for at, size in
             ((POINTER, 4), (0x8013A248, 4), (0x80136F0C, 4), (BLOB_RAM+0xD7, 1))}
    edge = b'V3MM'*4
    guards = (allocation, field-16, field+0x200, block-16, block+0x700,
              grid-16, grid+512, actor-16, actor+0x200, slots-16, slots+0x100,
              output-16, output+16, buffers-16, buffers+4*544,
              allocation+0x3FF0, TEST_STACK-0x800, TEST_STACK+0x40)
    for at in guards: debug.write_memory(at, edge)
    try:
        put(POINTER, owner); put(0x8013A248, field); put(field+0x148, block)
        debug.write_memory(field+0x166, bytes((1, 1)))
        put(block+0x584, grid)
        call(0x8008A33C, [0, 0], grid)
        placements = {0: 0x2400, 1: 0x34BF, 2: 0x34BF, 3: 0x34BF,
                      4: 0x34BF, 5: 0x1F35, 6: 0x34BC, 17: 0x24BF}
        grid_bytes = bytearray(512)
        for i, item in placements.items(): struct.pack_into('>H', grid_bytes, i*2, item)
        debug.write_memory(grid, grid_bytes)
        call(owner, [0, 0, 0], 7, proof)
        for ordinal, tile in ((1, 1), (4, 4), (5, 5), (6, 17)):
            call(owner+0x80959674-RAM, [output, output+4, output+8, ordinal, 0, 0], proof=proof)
            check('native placement keeps full identity and tile', output,
                  struct.pack('>IIH', tile%16, tile//16, placements[tile]))
        debug.write_memory(BLOB_RAM+0xD7, bytes([saved[BLOB_RAM+0xD7][0] & 0x7F]))
        call(owner, [0, 0, 0], 3, proof)
        call(owner+0x80959674-RAM, [output, output+4, output+8, 1, 0, 0], proof=proof)
        check('disabled garment is excluded without losing sold marker', output, struct.pack('>IIH', 5, 0, 0x1F35))
        debug.write_memory(BLOB_RAM+0xD7, saved[BLOB_RAM+0xD7])
        # Model post-constructor slots; retain native 0x54-byte records and
        # complete foreground/reload loops. Allocation/draw remain ordinary-play work.
        put(actor+0x174, 3); put(actor+0x178, slots)
        put(actor+0x194, buffers+3*544); put(actor+0x198, buffers+3*544+512)
        for i, item in enumerate((0x24BF, 0x34BF, 0x2400)):
            debug.write_memory(slots+i*0x54+0x14, struct.pack('>H', item))
            put(slots+i*0x54+0x18, buffers+i*544)
            put(slots+i*0x54+0x1C, buffers+i*544+512)
        textures, palettes = (files[v].extract(rom) for v in (0xB68000, 0xB88000))
        expected = [textures[i*512:(i+1)*512]+palettes[i*32:(i+1)*32] for i in (0xBF, 0, 0xFF)]
        expected.insert(1, blob[0xF000:0xF220])
        put(clip, actor); put(0x80136F0C, clip)
        for address, args in ((0x80959A80, [actor]), (0x80959F34, [])):
            debug.write_memory(buffers, bytes([0xA5])*(4*544))
            call(owner+address-RAM, args, proof=proof)
            check('complete original/imported/naked texture and palette transfers', buffers, b''.join(expected))
        check('native grid retained', grid, bytes(grid_bytes))
        check('complete owner retained', owner, loaded)
        for at in guards: check('fixture guard', at, edge)
        check('save guard', 0x8046C350, bytes.fromhex('AF53C0DE')*4)
        check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
        check('no faulted thread', 0x8003CE34, bytes(4))
    finally:
        for at, value in saved.items(): debug.write_memory(at, value)
    check('complete prefix restored', BLOB_RAM, blob[:0xC000])
    call(0x8009C040, [allocation])
    return {'native_calls': calls, 'full_native_count_cases': 2, 'full_native_search_cases': 5,
            'complete_texture_loops': 2, 'ordinary_shop_drawing_or_purchase_tested': False,
            'device_io_performed': False, 'requires_checkpoint_restore': True}
