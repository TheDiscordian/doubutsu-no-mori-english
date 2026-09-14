"""Execute actual feng shui calculations with imported and native room furniture."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import by_vrom, sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_npc_draw_smoke import boot_proofs
import v3_feng_shui as feng


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_text())
    result = report.get('feng_shui')
    if sha256(rom) != report['output_sha256'] or not result:
        raise ValueError('Feng shui check requires its current complete cartridge')
    files, boot = by_vrom(rom), boot_proofs(rom)
    blob = files[BLOB].extract(rom)[:0xC000]

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'feng_shui_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Native feng shui check failed: ' + label)

    def call(address, args, proof=None):
        value = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                           verified_code=proof or boot.get(address))
        record(value)
        return value['return_value']

    def put(at, value):
        debug.write_memory(at, struct.pack('>I', value))

    check('complete current resident prefix', BLOB_RAM, blob)
    extra = 0x800 if result.get('metadata_rows', feng.COUNT) > feng.COUNT else 0
    size = 0x2800+extra
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x80400000 - size:
        raise ValueError('Feng shui fixture allocation failed')
    owner = allocation+16
    layers, points, first, second = (allocation + extra + n for n in (0x1C00, 0x1C40, 0x1E00, 0x2100))
    data, reloc = (files[v].extract(rom) for v in (feng.NEW_VROM, feng.NEW_RELOC))
    if (sha256(data), sha256(reloc)) != (result['output_sha256'], result['relocation_sha256']):
        raise ValueError('Changed complete feng shui image')
    if owner + len(data) + len(reloc) >= layers - 16:
        raise ValueError('Feng shui fixture areas overlap')
    expected = relocate_verified_data(SimpleNamespace(ram=feng.RAM, resident_bytes=len(data),
        sections=struct.unpack_from('>5I', reloc)), data, reloc, owner)
    debug.write_memory(allocation, bytes(size))
    call(0x800262D0, [feng.NEW_VROM, feng.NEW_VROM + len(data), feng.RAM,
                     feng.RAM + len(data), owner, owner + len(data), len(reloc)])
    check('complete native relocated feng shui owner', owner, expected)
    proof = (owner, expected)
    globals_before = {at: debug.read_memory(at, 4) for at in (0x80107010, 0x801375F0)}
    put(0x80107010, owner)
    edge = b'V3FS' * 4
    guards = (allocation, layers - 16, first - 16, first + 512, second - 16,
              second + 512, allocation + size - 16, TEST_STACK - 0x800, TEST_STACK + 0x40)
    for at in guards:
        debug.write_memory(at, edge)
    try:
        for item, x, z, money, goods in ((0x1414, 4, 3, 0, 2), (0x3227, 4, 3, 0, 2),
                (0x3224, 1, 3, 0, 0), (0x32B9, 3, 1, 2, 1), (0x32BB, 3, 4, 0, 0)):
            debug.write_memory(points, bytes.fromhex('FFFFFFFFFFFFFFFF'))
            call(owner, [item, x, z, 6, points, points + 4], proof)
            check(f'complete item {item:04X} at ({x},{z})', points, struct.pack('>II', money, goods))
        if extra:
            for rotation in range(4):
                debug.write_memory(points, b'\xFF'*8)
                call(owner, [0x3AFC | rotation, 4, 3, 6, points, points+4], proof)
                check('complete native clothing feng shui retains donor neutral colour', points, bytes(8))
        put(layers, first); put(layers + 4, second)
        grid1, grid2 = bytearray(512), bytearray(512)
        for grid, x, z, item in ((grid1, 4, 3, 0x3227), (grid2, 3, 1, 0x32B9),
                               (grid1, 4, 4, 0x1414), (grid2, 1, 1, 0x3000)):
            struct.pack_into('>H', grid, (z * 16 + x) * 2, item)
        debug.write_memory(first, grid1); debug.write_memory(second, grid2)
        for enabled, money, goods in ((1, 2, 3), (0, 0, 2)):
            put(BLOB_RAM + 0x7254, enabled)
            call(owner + 0x80930D14 - feng.RAM, [points, layers, 6], proof)
            check('complete two-layer room with native/imported and unknown items',
                  0x801375F0, struct.pack('>HH', money, goods))
        put(BLOB_RAM + 0x7254, 1)
        debug.write_memory(first, bytes(512)); debug.write_memory(second, bytes(512))
        call(owner + 0x80930D14 - feng.RAM, [points, layers, 6], proof)
        check('complete empty-room fallback', 0x801375F0, bytes(4))
        check('complete current owner remains unchanged', owner, expected)
        check('complete resident prefix remains unchanged', BLOB_RAM, blob)
        for at in guards:
            check('fixture guard', at, edge)
        check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
        check('no faulted thread', 0x8003CE34, bytes(4))
    finally:
        put(BLOB_RAM + 0x7254, 1)
        for at, value in globals_before.items():
            debug.write_memory(at, value)
    call(0x8009C040, [allocation])
    return {'complete_native_item_evaluations': 5+(4 if extra else 0), 'complete_native_room_evaluations': 3,
            'actual_donor_feng_shui_properties_tested': True,
            'ordinary_house_evaluation_tested': False, 'saved_data_written': False,
            'requires_checkpoint_restore': True}
