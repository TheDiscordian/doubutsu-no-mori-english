"""Current native catalogue initialization, selection, names, and model DMA."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from catalogue_names import APPROVED, Image
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_catalogue import RAM, RELOC, SIZE, VROM
from v3_npc_draw_smoke import boot_proofs


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_text())
    cat = report.get('catalogue')
    if sha256(rom) != report['output_sha256'] or not cat:
        raise ValueError('Catalogue probe needs the exact current cartridge')
    files, boot = by_vrom(rom), boot_proofs(rom)
    blob = files[BLOB].extract(rom)[:0xC000]
    calls = 0

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'catalogue_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Catalogue native check failed: ' + label)

    def call(address, args=(), proof=None):
        nonlocal calls
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                            verified_code=proof or boot.get(address))
        record(result); calls += 1
        return result['return_value']

    def put(at, *values):
        debug.write_memory(at, struct.pack('>' + 'I' * len(values), *values))

    check('complete current resident prefix', BLOB_RAM, blob)
    size = 0x1C000
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x80400000 - size:
        raise ValueError('Catalogue fixture allocation failed')
    root, submenu, stub, overlay = (allocation + n for n in (16, 0xF000, 0xF100, 0))
    # These entry points only use overlay + 10628..10723. Its earlier fields
    # are not accessed, so those addresses may share the owned code allocation;
    # do not reserve an otherwise unused second 64-KiB window at title boot.
    banks = [allocation + 0x11000, allocation + 0x15C00]
    programs = [allocation + 0x13800, allocation + 0x18400]
    state = root + 0x9910
    page = state + 0xEC8
    debug.write_memory(allocation, bytes(size))
    data, reloc = (files[v].extract(rom) for v in (VROM, RELOC))
    if sha256(data) != cat['output_sha256'] or sha256(reloc) != cat['relocation_sha256']:
        raise ValueError('Changed catalogue proof')
    loaded = relocate_verified_data(Image(RAM, len(data), struct.unpack_from('>5I', reloc)),
                                     data, reloc, root)
    call(0x800262D0, [VROM, VROM + len(data), RAM, RAM + len(data),
                      root, root + len(data), len(reloc)])
    check('complete actual native-relocated catalogue', root, loaded)
    core_proof = (root, loaded[:14048])
    # Only entry-animation movement is substituted. Native list construction,
    # name caching, preview initialization, selection, and DMA run unchanged.
    debug.write_memory(stub, bytes.fromhex('03E0000800000000'))
    call(0x8002FE00, [stub, 8]); call(0x80034CE0, [stub, 8])
    put(submenu + 0x2C, overlay)
    put(overlay + 0x106B0, stub)
    put(overlay + 0x10720, state)
    edge = b'V3CA' * 4
    guards = [allocation, allocation + size - 16, TEST_STACK - 0x800, TEST_STACK + 0x40]
    for bank, program in zip(banks, programs):
        guards += [bank - 16, bank + 0x2400, program - 16, program + 0x2000]
    for at in guards:
        debug.write_memory(at, edge)
    player, active_at, runtime_at = 0x80126EC0, 0x80136FD8, 0x8046C000
    old_player, old_active = debug.read_memory(player, 0xBD0), debug.read_memory(active_at, 4)
    old_runtime = debug.read_memory(runtime_at, 704)
    old_segment = debug.read_memory(0x801458B8, 4)
    old_debug = debug.read_memory(0x8010FD60, 4)
    init = APPROVED['symbols']['af_catalog_init']
    name_at = APPROVED['symbols']['af_catalog_name']

    def initialize():
        debug.write_memory(state, bytes(12576))
        for n, (program, bank) in enumerate(zip(programs, banks)):
            put(state + 8 + n * 0x760 + 0x740, program, bank)
        call(root + init, [submenu], (root + init, loaded[init:init + 40]))

    def preview(n, item):
        at = state + 8 + n * 0x760
        row = next(r for r in report['furniture']['imports'] if int(r['item_id'], 16) == item)
        meta = next(r for r in report['furniture_items']['imports'] if int(r['item_id'], 16) == item)
        profile = int.from_bytes(blob[0x5800 + row['runtime_index'] * 4:0x5804 + row['runtime_index'] * 4], 'big')
        check('actual imported preview profile', at + 0x748, struct.pack('>I', profile))
        check('original catalogue index encoding', at, struct.pack('>H', (item - 0x1000) >> 2))
        check('furniture preview type and native timer', at + 0x750, struct.pack('>HH', 0, 15))
        check('actual catalogue price', at + 0x754, struct.pack('>I', meta['price']))
        check('donor-matched draw scale and native viewing height', at + 0x758,
              struct.pack('>ff', 0.9, 42.0))
        check('donor-matched preview vertical position', at + 12, struct.pack('>f', -3.0))
        start = int(row['object_vrom'], 16) - BLOB
        check('complete actual model bank DMA', banks[n],
              files[BLOB].extract(rom)[start:start + row['object_bytes']])

    try:
        put(active_at, player); put(0x8010FD60, 0)
        debug.write_memory(player + 0xAF0, bytes(0x98))
        debug.write_memory(runtime_at + 16 + 160, bytes(512))
        initialize()
        check('uncollected imports stay out of catalogue', page, bytes(2))
        call(0x800B88EC, [0x3225]); call(0x800B88EC, [0x32BB])
        initialize()
        check('both collected imports appear', page, bytes.fromhex('0002'))
        check('stable real item IDs in catalogue order', page + 8, bytes.fromhex('322432B8'))
        check('partial collection is not marked complete', page + 6, bytes(1))
        for n, name in enumerate(('haz-mat barrel', 'oil drum')):
            address = call(root + name_at, [page + 0x380 + n * 10],
                           (root + name_at, loaded[name_at:name_at + 92]))
            if not root + 0x9910 <= address <= root + len(data) - 16:
                raise ValueError('Catalogue full name escaped owned storage')
            check('complete displayed English catalogue name', address, name.encode().ljust(16, b' '))
        preview(0, 0x3224)
        debug.write_memory(page + 4, bytes.fromhex('0001'))
        call(root + 0x808A6A8C - RAM, [submenu, 0], core_proof)
        check('native selection switches preview buffers', state, bytes([1]))
        preview(1, 0x32B8)
        # Test the true maximum with all native furniture plus both additions.
        # Native category construction and full-name storage retain their sizes.
        debug.write_memory(player + 0xAF0, b'\xFF' * 120)
        initialize()
        check('complete additive furniture list count', page, struct.pack('>H', 438))
        check('complete collection indicator', page + 6, bytes([1]))
        check('last two entries fit the native category', page + 8 + 436 * 2, bytes.fromhex('322432B8'))
        # Original complete program and model loaders still run through fallback.
        call(root + 0x808A627C - RAM, [state + 8, 0x1004], core_proof)
        check('original preview keeps original index', state + 8, bytes.fromhex('0001'))
        check('original preview keeps original furniture type', state + 8 + 0x750, bytes(2))
        check('complete resident prefix retained', BLOB_RAM, blob)
        check('catalogue executable prefix unchanged by menu work', root, loaded[:14048])
        check('catalogue suffix retained', root + SIZE, loaded[SIZE:])
        for at in guards:
            check('fixture guard', at, edge)
        check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
        check('no faulted thread', 0x8003CE34, bytes(4))
    finally:
        debug.write_memory(player, old_player); debug.write_memory(active_at, old_active)
        debug.write_memory(runtime_at, old_runtime); debug.write_memory(0x801458B8, old_segment)
        debug.write_memory(0x8010FD60, old_debug)
    call(0x8009C040, [allocation])
    return {'catalogue_native_calls': calls, 'native_list_and_full_name_cases': 3,
            'imported_complete_previews': 2, 'native_selection_tested': True,
            'original_preview_fallback_tested': True, 'gpu_rendered': False,
            'ordinary_order_delivery_tested': False, 'saved_data_written': False,
            'requires_checkpoint_restore': True}
