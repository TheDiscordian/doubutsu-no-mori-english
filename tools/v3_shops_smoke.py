"""Actual native goods selection, pocket acquisition, and imported-order letters."""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from flash_mail import SAVE_RAM, SAVE_BYTES
from mail_catalog import templates
from mail_creator_catalog import identity
from mail_record import Field, Record, pack
from mail_runtime_test_scenario import output_bytes
from mail_storage import HOME_MAILBOX
from runtime_layout import MODULE_RAM, MODULE_VROM, RESERVATION, TEST_STACK
from v3_asset_loader import BASE_SHA, BLOB, BLOB_RAM
from v3_shops import DESCRIPTOR, END, ENTRY


def exercise(debug, rom_path, record, *, stock=True):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_text())
    shop = report.get('shops')
    if sha256(rom) != report['output_sha256'] or not shop:
        raise ValueError('Shop check requires its exact current cartridge')
    base = (Path(__file__).resolve().parents[1] / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
    if sha256(base) != BASE_SHA:
        raise ValueError('Changed retained postal baseline')
    files, original = by_vrom(rom), by_vrom(base)
    code, old_code = files[CODE_VROM].extract(rom), original[CODE_VROM].extract(base)
    blob = files[BLOB].extract(rom)[:0xC000]
    module = files[MODULE_VROM].extract(rom)
    catalog = files[0x030A0000].extract(rom)
    catalog_id = identity(catalog)
    calls = 0

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'shop_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Native shop check failed: ' + label)

    def call(address, args=(), expected=None):
        nonlocal calls
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480)
        record(result); calls += 1
        if expected is not None and result['return_value'] != expected & 0xFFFFFFFF:
            raise ValueError(f'Shop call {address:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']

    def put(at, value):
        debug.write_memory(at, struct.pack('>I', value))

    check('complete current resident prefix', BLOB_RAM, blob)
    for row in shop['retained_owners']:
        check('retained complete native stock owner', row['start'], code[row['start'] - CODE_RAM:row['end'] - CODE_RAM])
    check('installed global shop category', ENTRY, code[ENTRY - CODE_RAM:END - CODE_RAM])
    check('actual goods descriptor', DESCRIPTOR, code[DESCRIPTOR - CODE_RAM:DESCRIPTOR - CODE_RAM + 12])
    if code[0x800B6B94 - CODE_RAM:0x800B6D40 - CODE_RAM] != old_code[0x800B6B94 - CODE_RAM:0x800B6D40 - CODE_RAM]:
        raise ValueError('Imported postal check requires retained creator, gate, and pending loop')
    if files[0x03200000].extract(rom) != original[0x03200000].extract(base):
        raise ValueError('Imported postal check requires the retained complete letter creator')
    check('current postal creator and pending loop', 0x800B6B94, code[0x800B6B94 - CODE_RAM:0x800B6D40 - CODE_RAM])
    allocation = call(0x8009BFC0, [0x3000])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x803FD000:
        raise ValueError('Shop fixture allocation failed')
    result_at, clear_at, work, text = (allocation + n for n in (16, 0x100, 0x400, 0x1400))
    edge = b'V3SH' * 4
    guards = (allocation, result_at + 16, clear_at - 16, clear_at + 176,
              work - 16, work + 3552, text - 16, text + 1040,
              allocation + 0x2FF0, TEST_STACK - 0x1000, TEST_STACK + 0x40)
    for at in guards:
        debug.write_memory(at, edge)
    saved = debug.read_memory(SAVE_RAM, SAVE_BYTES)
    runtime = debug.read_memory(0x8046C000, 704)
    capital, session = 0x80199F64, 0x80199F5C
    globals_before = {at: debug.read_memory(at, size) for at, size in
        ((capital, 4), (session, 4), (0x8003C590, 4), (0x800419F0, 4),
         (0x801458B8, 4), (0x80136FD8, 4), (0x80140680, 200))}
    check('detached creator before testing', session, bytes(4))
    player = SAVE_RAM + 0x20
    selected = ((0x32B8, 0, 'oil drum'), (0x3224, 2, 'haz-mat barrel'))
    # Choose a seed analytically for the last row. The actual native RNG and
    # complete stock selector still execute; no return value is substituted.
    next_random = 0xFF800000
    seed = ((next_random - 0x3C6EF35F) * pow(0x19660D, -1, 1 << 32)) & 0xFFFFFFFF
    try:
        for priorities in (((0, 1, 2), (2, 1, 0)) if stock else ()):
            encoded = priorities[0] << 6 | priorities[1] << 4 | priorities[2] << 2
            debug.write_memory(0x80135B1C, bytes([encoded]))
            for item, group, _ in selected:
                for rarity in range(3):
                    call(0x800C0490, [item, 0, rarity, 0], int(rarity == priorities[group]))
                debug.write_memory(0x80135C00, bytes(2))
                put(0x8003C590, seed)
                call(0x800BFCF0, [0, result_at, 1, 0, 0, 0, priorities[group]])
                check('native stock selector chooses the added row', result_at, struct.pack('>H', item))
                check('native RNG advances exactly once', 0x8003C590, struct.pack('>I', next_random))
        for item, category in (((0x3227, 0), (0x32BB, 0), (0x3000, -1),
                               (0x1008, 0), (0x2000, 1), (0x2400, 2), (0x2700, 4), (0x2600, 3)) if stock else ()):
            call(ENTRY, [item], category)
        if stock:
            put(BLOB_RAM + 0x7254, 0)
            call(ENTRY, [0x32B8], -1)
            put(BLOB_RAM + 0x7254, 1)
        put(0x80136FD8, player)
        debug.write_memory(player + 0x14, bytes(0x24))
        debug.write_memory(0x8046C000 + 16 + 160, bytes(512))
        for item, _, _ in (selected if stock else ()):
            call(0x800B8B8C, [player, item, 0], 1)
        if stock:
            check('native pocket acquisition retains both real IDs', player + 0x14, bytes.fromhex('32B83224'))
            expected_catalogue = bytearray(128); expected_catalogue[17] = 2; expected_catalogue[21] = 64
            check('stock items enter native collection path', 0x8046C000 + 176, bytes(expected_catalogue))
        call(0x8009C384, [clear_at])
        cleared = debug.read_memory(clear_at, 164)
        debug.write_memory(HOME_MAILBOX, cleared * 10)
        pid = b'PLAYER' + b'TOWN  ' + bytes.fromhex('12343001')
        debug.write_memory(player, pid)
        debug.write_memory(player + 0xA74, bytes([1]))
        debug.write_memory(player + 0xA94, struct.pack('>HBBHBB', 0x32B8, 0, 0, 0x3224, 3, 0) + bytes(12))
        put(capital, 0)
        before_delivery = bytearray(debug.read_memory(SAVE_RAM, SAVE_BYTES))
        call(0x800B6C88, [0, 0])
        expected_save = before_delivery
        next_capital = False
        for n, (item, _, name) in enumerate(selected):
            number = 0x49 if n == 0 else 0x4C
            snapshot = Record(catalog_id, 0, (number,), ((0, Field(name.encode().ljust(16, b' '))),), next_capital)
            expected_text = output_bytes(snapshot, templates(catalog, snapshot))
            mail = bytearray(164); mail[:16] = pid
            mail[18:30] = b' ' * 12; mail[30:35] = b'\xFF' * 5
            mail[36:38] = struct.pack('>H', item); mail[39:42] = bytes((128, 7, 55)); mail[42:] = pack(snapshot)
            at = HOME_MAILBOX + n * 164
            expected_save[at - SAVE_RAM:at - SAVE_RAM + 164] = mail
            expected_save[0x20 + 0xA94 + n * 4:0x20 + 0xA96 + n * 4] = bytes(2)
            check('complete imported-order letter and attached item', at, bytes(mail))
            # The full reader is unchanged and uses the stored literal name.
            restore = 0x80196C28
            # Startup deliberately replaces this entry with the accent-aware
            # reader. Bind its target to the complete current font's hook row,
            # not the pre-startup words stored in the resident ROM resource.
            font = files[0x03400000].extract(rom)
            if font != original[0x03400000].extract(base):
                raise ValueError('Changed retained complete mail/font image')
            signature = struct.pack('>3I', restore, 0x14800003, 0)
            if font.count(signature) != 1:
                raise ValueError('Missing unique startup mail-reader hook')
            linked_target = struct.unpack_from('>I', font, font.index(signature) + 12)[0]
            font_base = int.from_bytes(debug.read_memory(0x80199F04, 4), 'big')
            image_size = struct.unpack_from('>I', module, 0x70)[0]
            record({'mail_reader_owner': f'{font_base:08X}',
                    'linked_target': f'{linked_target:08X}', 'image_bytes': image_size})
            if (not 0x80C00000 <= linked_target < 0x80C00000 + image_size
                    or not 0 < image_size <= 0x7000 or image_size & 15
                    or font_base != 0x80450010):
                raise ValueError('Invalid installed startup mail-reader owner')
            target = font_base + linked_target - 0x80C00000
            expected_reader = struct.pack('>II', 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
            expected_reader += module[restore - MODULE_RAM + 8:restore - MODULE_RAM + 64]
            check('current startup-installed complete mail reader', restore, expected_reader)
            call(restore, [text, at + 42, 122, work], 1)
            check('complete restored imported-order English text', text, expected_text)
            next_capital = bool(expected_text[14])
        check('pending orders clear only after complete mailbox receipt', SAVE_RAM, bytes(expected_save))
        check('creator detaches after both deliveries', session, bytes(4))
        check('current resident code is retained', BLOB_RAM, blob)
        for at in guards:
            check('fixture guard', at, edge)
        check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
        check('no faulted thread', 0x8003CE34, bytes(4))
    finally:
        put(BLOB_RAM + 0x7254, 1)
        debug.write_memory(SAVE_RAM, saved); debug.write_memory(0x8046C000, runtime)
        for at, data in globals_before.items():
            debug.write_memory(at, data)
    call(0x8009C040, [allocation])
    return {'shop_native_calls': calls, 'native_random_stock_cases': 4 if stock else 0,
            'town_rarity_permutations': 2 if stock else 0, 'native_imported_order_deliveries': 2,
            'complete_delivered_text_reads': 2, 'ordinary_shop_controls_tested': False,
            'payment_confirmation_tested': False, 'saved_data_written': False,
            'requires_checkpoint_restore': True}
