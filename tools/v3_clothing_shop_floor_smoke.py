"""Native garment placement/selection and complete sale-to-bare-mannequin flow."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import by_vrom, sha256
from flash_mail import SAVE_RAM, SAVE_BYTES
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_npc_draw_smoke import boot_proofs
import v3_shop_floor as floor_spec
import v3_shop_mannequin as mannequin_spec


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['shop_floor'].get('clothing'):
        raise ValueError('Clothing floor check requires its exact installed cartridge')
    files, boot = by_vrom(rom), boot_proofs(rom)
    blob = files[BLOB].extract(rom)
    calls = 0

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'clothing_floor_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected: raise ValueError('Clothing shop floor mismatch: '+label)

    def call(address, args, expected=None, proof=None):
        nonlocal calls
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM+0x6480,
                            verified_code=proof or boot.get(address))
        record(result); calls += 1
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Unexpected clothing floor result at {address:08X}')
        return result['return_value']

    def put(address, value): debug.write_memory(address, struct.pack('>I', value))

    check('complete current prefix', BLOB_RAM, blob[:0xC000])
    allocation = call(0x8009BFC0, [0x5000])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x803FB000:
        raise ValueError('Clothing floor fixture allocation failed')
    floor, mannequin, field, block, grid, design, actor, clip, goods, slot = (
        allocation+n for n in (16, 0x1100, 0x2400, 0x2800, 0x3000, 0x3400, 0x3600, 0x3800, 0x3880, 0x3900))
    debug.write_memory(allocation, bytes(0x5000))
    proofs = {}
    for spec, owner, contract in ((floor_spec, floor, report['shop_floor']),
                                  (mannequin_spec, mannequin, report['clothing']['mannequin'])):
        data, reloc = (files[v].extract(rom) for v in (spec.VROM, spec.RELOC))
        if sha256(data) != contract['output_sha256'] or sha256(reloc) != contract['relocation_sha256']:
            raise ValueError('Changed complete shop owner')
        loaded = relocate_verified_data(SimpleNamespace(ram=spec.RAM, resident_bytes=spec.SIZE, sections=spec.SECTIONS), data, reloc, owner)
        call(0x800262D0, [spec.VROM, spec.VROM+spec.SIZE, spec.RAM, spec.RAM+spec.SIZE, owner, owner+spec.SIZE, len(reloc)])
        check('complete native-relocated shop owner', owner, loaded)
        proofs[owner] = (owner, loaded)
    saved = {at: debug.read_memory(at, size) for at, size in
        ((floor_spec.POINTER, 4), (mannequin_spec.POINTER, 4), (0x8013A248, 4),
         (0x80136F00, 4), (0x80136F0C, 4), (0x80137944, 4), (BLOB_RAM+0xD7, 1), (SAVE_RAM, SAVE_BYTES))}
    edge = b'V3CF'*4
    guards = (allocation, mannequin-16, field-16, field+0x200, block-16, block+0x700,
              grid-16, grid+512, design-16, actor-16, clip-16, goods-16, goods+16,
              slot-16, slot+0x60, allocation+0x4FF0, TEST_STACK-0x800, TEST_STACK+0x40)
    for at in guards: debug.write_memory(at, edge)
    try:
        put(floor_spec.POINTER, floor); put(mannequin_spec.POINTER, mannequin)
        put(0x80137944, 0); put(0x8013A248, field); put(field+0x148, block)
        debug.write_memory(field+0x166, bytes((1, 1))); put(block+0x584, grid)
        call(0x8008A33C, [0, 0], grid)
        for item, reserve, selected_item in ((0x34BF, 0x1F29, 0x34BF), (0x2400, 0x1F29, 0x2400),
                (0x1F35, 0x1F29, 0xFFFF), (0x34BC, 0, 0xFFFF), (0x3224, 0x1F2A, 0x3224)):
            call(floor, [item], reserve, proofs[floor])
            debug.write_memory(grid+84*2, struct.pack('>H', item))
            call(floor+0x809547E4-floor_spec.RAM, [4, 5], selected_item, proofs[floor])
        debug.write_memory(BLOB_RAM+0xD7, bytes([saved[BLOB_RAM+0xD7][0] & 0x7F]))
        call(floor, [0x34BF], 0, proofs[floor])
        debug.write_memory(grid+84*2, bytes.fromhex('34BF'))
        call(floor+0x809547E4-floor_spec.RAM, [4, 5], 0xFFFF, proofs[floor])
        debug.write_memory(BLOB_RAM+0xD7, saved[BLOB_RAM+0xD7])
        # Actual native sale report, goods-list update, mannequin callback, and
        # field write. Post-constructor actors are explicit fixture state.
        put(clip, design); put(0x80136F00, clip)
        put(clip+0x20, actor); put(clip+0x28, mannequin+0x8095A024-mannequin_spec.RAM)
        put(0x80136F0C, clip+0x20)
        put(design+0x174, goods); put(design+0x17C, 2)
        debug.write_memory(goods, bytes.fromhex('34BF24BF'))
        put(actor+0x174, 1); put(actor+0x178, slot)
        put(slot+0xC, 4); put(slot+0x10, 5)
        debug.write_memory(slot+0x14, bytes.fromhex('34BF'))
        expected_slot = bytearray(debug.read_memory(slot, 0x54)); struct.pack_into('>I', expected_slot, 0x50, 1)
        put(0x80135C14, 100)
        expected_save = bytearray(saved[SAVE_RAM]); struct.pack_into('>I', expected_save, 0x80135C14-SAVE_RAM, 480)
        call(0x800C0194, [0x34BF], 380)
        call(floor+0x80954970-floor_spec.RAM, [4, 5], 0, proofs[floor])
        check('only purchased stock becomes sold clothing', goods, bytes.fromhex('1F3524BF'))
        check('native callback selects bare mannequin without changing its identity', slot, bytes(expected_slot))
        check('purchased floor tile is cleared', grid+84*2, bytes.fromhex('FFFF'))
        check('only native sales total changes in saved payload', SAVE_RAM, bytes(expected_save))
        for owner, proof in proofs.items(): check('complete loaded owner retained', owner, proof[1])
        for at in guards: check('fixture guard', at, edge)
        check('save guard', 0x8046C350, bytes.fromhex('AF53C0DE')*4)
        check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
        check('no faulted thread', 0x8003CE34, bytes(4))
    finally:
        for at, data in saved.items(): debug.write_memory(at, data)
    check('complete prefix restored', BLOB_RAM, blob[:0xC000])
    check('saved payload restored', SAVE_RAM, saved[SAVE_RAM])
    call(0x8009C040, [allocation])
    return {'native_calls': calls, 'reserve_and_selection_cases': 12,
            'complete_native_sale_and_bare_mannequin_callback': True,
            'ordinary_purchase_or_player_payment_tested': False, 'device_io_performed': False,
            'requires_checkpoint_restore': True}
