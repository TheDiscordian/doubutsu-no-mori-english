"""Actual clothing catalogue lists, full names, selection, and mannequin DMA."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from catalogue_names import APPROVED, Image
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_catalogue import RAM, VROM, RELOC, SIZE
from v3_clothing_catalogue import TABLE
from v3_clothing_display import MODEL
from v3_npc_draw_smoke import boot_proofs
from v3_save_clothing import PROFILE


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent/'build.json').read_text())
    cat = report.get('catalogue', {})
    if sha256(rom) != report['output_sha256'] or not cat.get('clothing'):
        raise ValueError('Clothing catalogue needs its exact current cartridge')
    files, boot = by_vrom(rom), boot_proofs(rom)
    blob = files[BLOB].extract(rom)

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'clothing_catalogue_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected: raise ValueError('Clothing catalogue mismatch: '+label)

    def call(address, args=(), proof=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM+0x6480,
                            verified_code=proof or boot.get(address))
        record(result)
        return result['return_value']

    def put(at, *values): debug.write_memory(at, struct.pack('>'+'I'*len(values), *values))

    check('complete current resident prefix', BLOB_RAM, blob[:0xC000])
    size = 0x1C000
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Clothing catalogue fixture allocation failed')
    root, submenu, stub, overlay = (allocation+n for n in (16, 0xF000, 0xF100, 0))
    banks, programs = [allocation+0x11000, allocation+0x15C00], [allocation+0x13800, allocation+0x18400]
    state = root+0x9910
    furniture_page, page = state+0xEC8, state+0xEC8+3*966
    data, reloc = (files[v].extract(rom) for v in (VROM, RELOC))
    if (sha256(data), sha256(reloc)) != (cat['output_sha256'], cat['relocation_sha256']):
        raise ValueError('Changed complete catalogue image or relocation')
    if 16+len(data)+len(reloc) >= 0xF000: raise ValueError('Catalogue fixture overlaps submenu')
    loaded = relocate_verified_data(Image(RAM, len(data), struct.unpack_from('>5I', reloc)), data, reloc, root)
    debug.write_memory(allocation, bytes(size))
    call(0x800262D0, [VROM, VROM+len(data), RAM, RAM+len(data), root, root+len(data), len(reloc)])
    check('complete native-relocated clothing catalogue', root, loaded)
    proof = (root, loaded[:14048])
    # Reuse the established catalogue fixture: only menu entry movement is a
    # return stub; list/name/selection/model/price functions execute natively.
    debug.write_memory(stub, bytes.fromhex('03E0000800000000'))
    call(0x8002FE00, [stub, 8]); call(0x80034CE0, [stub, 8])
    put(submenu+0x2C, overlay); put(overlay+0x106B0, stub); put(overlay+0x10720, state)
    edge = b'V3CC'*4
    guards = [allocation, allocation+size-16, TEST_STACK-0x800, TEST_STACK+0x40]
    for bank, program in zip(banks, programs): guards += [bank-16, bank+0x2400, program-16, program+0x2000]
    for at in guards: debug.write_memory(at, edge)
    player, active_at, runtime_at = 0x80126EC0, 0x80136FD8, 0x8046C000
    saved = {player: debug.read_memory(player, 0xBD0), active_at: debug.read_memory(active_at, 4),
             runtime_at: debug.read_memory(runtime_at, report['save_runtime']['state_bytes']),
             0x801458B8: debug.read_memory(0x801458B8, 4), 0x8010FD60: debug.read_memory(0x8010FD60, 4)}
    init, name_at = (APPROVED['symbols'][key] for key in ('af_catalog_init', 'af_catalog_name'))

    def initialize():
        debug.write_memory(state, bytes(12576))
        for n, (program, bank) in enumerate(zip(programs, banks)):
            put(state+8+n*0x760+0x740, program, bank)
            debug.write_memory(bank, b'\xA5'*0x2400)
        call(root+init, [submenu], (root+init, loaded[init:init+40]))

    try:
        put(active_at, player); put(0x8010FD60, 0)
        debug.write_memory(player+0xAF0, bytes(0x98))
        debug.write_memory(runtime_at+16+PROFILE, bytes(640))
        initialize()
        check('uncollected clothing absent', page, bytes(2))
        call(0x800B88EC, [0x2400]); call(0x800B88EC, [0x34BF]); call(0x800B88EC, [0x3224])
        initialize()
        check('native and imported garments collected', page, bytes.fromhex('0002'))
        check('complete display IDs preserve original order', page+8, bytes.fromhex('17AC3AFC'))
        check('partial clothing collection indicator', page+6, bytes(1))
        check('static furniture remains on its own page', furniture_page+8, bytes.fromhex('3224'))
        check('static preview presentation retained', state+8+0x758, struct.pack('>ff', 0.9, 42.0))
        name = call(root+name_at, [page+0x380+10], (root+name_at, loaded[name_at:name_at+92]))
        if not root+0x9910 <= name <= root+len(data)-16: raise ValueError('Name escaped owned cache')
        check('complete English clothing name', name, b'cherry shirt'.ljust(16, b' '))
        debug.write_memory(page+4, bytes.fromhex('0001'))
        call(root+0x98C, [submenu, 3], proof)
        check('selection switches preview buffers', state, bytes([1]))
        preview = state+8+0x760
        check('selected preview identity', preview, bytes.fromhex('0ABF'))
        check('real resident mannequin profile', preview+0x748, bytes.fromhex('80466608'))
        check('native type and animation timer', preview+0x750, struct.pack('>HH', 0, 15))
        check('native clothing price', preview+0x754, struct.pack('>I', 380))
        check('native clothing scale and viewing height', preview+0x758, struct.pack('>ff', 1.0, 38.0))
        check('native clothing model height', preview+12, struct.pack('>f', -4.0))
        model = blob[0xF000:0xF220]+files[MODEL].extract(rom)
        check('complete actual garment and mannequin model DMA', banks[1], model)
        check('preview buffer tail retained', banks[1]+len(model), b'\xA5'*(0x2400-len(model)))
        if call(0x800BF10C, [0x3AFC]) != 0x34BF: raise ValueError('Catalogue order lost pocket identity')
        debug.write_memory(player+0xAF0, b'\xFF'*120)
        initialize()
        check('all 246 clothing rows fit original capacity', page, struct.pack('>H', 246))
        check('complete clothing collection indicator', page+6, bytes([1]))
        native_indices = struct.unpack_from('>245H', data, TABLE-RAM)
        expected = b''.join(struct.pack('>H', 0x1000+i*4) for i in native_indices)+bytes.fromhex('3AFC')
        check('entire original plus imported clothing list', page+8, expected)
        # Keep current and working profiles consistent while disabling the
        # dependency; never manufacture a save-state mismatch to test a list.
        for offset in (119, 183):
            current, working = BLOB_RAM+0x20+offset, runtime_at+16+offset
            original = debug.read_memory(current, 1)
            try:
                debug.write_memory(current, bytes([original[0] & 0x7F]))
                debug.write_memory(working, bytes([original[0] & 0x7F]))
                initialize()
                check('missing dependency removes only imported clothing', page, struct.pack('>H', 245))
                check('every original catalogue garment retained', page+8, expected[:-2])
            finally:
                debug.write_memory(current, original); debug.write_memory(working, original)
        check('catalogue executable prefix retained', root, loaded[:14048])
        check('complete appended code and tables retained', root+SIZE, loaded[SIZE:])
        check('complete resident prefix restored', BLOB_RAM, blob[:0xC000])
        for at in guards: check('fixture guard', at, edge)
        check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
        check('no faulted thread', 0x8003CE34, bytes(4))
    finally:
        for at, content in saved.items(): debug.write_memory(at, content)
    check('complete runtime restored', runtime_at, saved[runtime_at])
    check('complete private record restored', player, saved[player])
    call(0x8009C040, [allocation])
    return {'native_clothing_catalogue': True, 'complete_rows': 246,
            'real_clothing_preview_and_full_name': True, 'order_identity': '34BF',
            'ordinary_payment_delivery_tested': False, 'gpu_rendered': False,
            'requires_checkpoint_restore': True}
