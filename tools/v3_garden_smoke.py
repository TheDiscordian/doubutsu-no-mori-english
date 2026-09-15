"""Bounded current garden catalogue decisions, actual lottery acquisition, and HRA."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, u32
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_npc_draw_smoke import boot_proofs
import v3_catalogue as catalogue
import v3_hra as hra


def exercise(debug, rom_path, record, *, scoring_only=False, western=False):
    key, theme, abi = ('western', 55, 65) if western else ('garden', 56, 64)
    path = Path(rom_path)
    image = path.read_bytes()
    report = json.loads((path.parent / 'build.json').read_text())
    if sha256(image) != report['output_sha256'] or report['runtime_abi'] != abi:
        raise ValueError('Theme probe requires its current installed cartridge')
    files, boot = by_vrom(image), boot_proofs(image)

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({key + '_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Garden native mismatch: ' + label)

    def call(address, args, expected=None, proof=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                            verified_code=proof or boot.get(address))
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Garden native return {address:08X}: {result["return_value"]} != {expected}')
        return result['return_value']

    def put(address, value): debug.write_memory(address, struct.pack('>I', value))

    allocation = call(0x8009BFC0, [0x11000])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x803EF000:
        raise ValueError('Garden fixture allocation failed')
    owner = allocation + 16
    layers, points, first, second = (allocation + n for n in (0x10000, 0x10020, 0x10100, 0x10400))
    saved = {at: debug.read_memory(at, size) for at, size in (
        (0x80107B50, 4), (0x8046C000, 864), (0x80126EC0, 0xBD0), (0x80136FD8, 4),
        (0x80135B1C, 1), (0x80135C00, 2), (0x8003C590, 4), (0x801458B8, 4))}
    debug.write_memory(allocation, bytes(0x11000))
    edge = b'V3GA' * 4
    guards = (allocation, layers - 16, points - 16, points + 16, first - 16,
              first + 512, second - 16, second + 512, allocation + 0x10FF0)
    for at in guards: debug.write_memory(at, edge)

    def load(tool, key):
        vrom, reloc_vrom = (tool.NEW_VROM, tool.NEW_RELOC) if key == 'hra' else (tool.VROM, tool.RELOC)
        data, reloc = (files[v].extract(image) for v in (vrom, reloc_vrom))
        if (sha256(data) != report[key]['output_sha256'] or sha256(reloc) != report[key]['relocation_sha256']
                or owner + len(data) + len(reloc) >= layers - 16):
            raise ValueError('Changed or oversized current garden owner')
        loaded = relocate_verified_data(Image(tool.RAM, len(data), struct.unpack_from('>5I', reloc)), data, reloc, owner)
        call(0x800262D0, [vrom, vrom + len(data), tool.RAM, tool.RAM + len(data),
                          owner, owner + len(data), len(reloc)])
        check(key + ' complete actual relocated owner', owner, loaded)
        return loaded, (owner, loaded[:hra.SECTIONS[0]] if key == 'hra' else loaded)

    def catalogue_and_stock():
        loaded, proof = load(catalogue, 'catalogue')
        available = owner + report['catalogue']['code']['symbols']['af_v3_catalogue_available'] - catalogue.RAM
        reward, reward_group = (0x3334, 3) if western else (0x32A0, 5)
        candidates = (0x32B0, 0x32BC, 0x3334) if western else (0x3268, 0x3294, 0x32A0)
        for item in candidates:
            for group in (0, 2, 3, 5):
                expected = int((item == 0x32B0 and group < 3 or item in (0x32BC, 0x3334) and group == 3)
                    if western else (item == 0x3268 and group < 3 or item == 0x32A0 and group == 5))
                call(available, [item, 0, group, 0], expected, proof)
        reward_row = next(r for r in report[key]['imports'] if int(r['item_id'], 16) == reward)
        enabled = int(reward_row['profile_ram'], 16) - 4
        try:
            put(enabled, 0)
            call(available, [reward, 0, reward_group, 0], 0, proof)
        finally:
            put(enabled, 1)

        # Actual existing list selector, with a deterministic last-entry draw.
        debug.write_memory(0x80135B1C, bytes([0x18]))
        debug.write_memory(0x80135C00, bytes(2))
        put(0x80136FD8, 0x80126EC0)
        debug.write_memory(0x80126ED4, bytes(0x24))
        debug.write_memory(0x8046C000 + 208, bytes(640))
        for group in (0, 1, 2, 3, 5): call(0x800C0490, [reward, 0, group, 0], int(group == reward_group))
        random = 0xFF800000
        put(0x8003C590, ((random - 0x3C6EF35F) * pow(0x19660D, -1, 1 << 32)) & 0xFFFFFFFF)
        call(0x800BFCF0, [0, points, 1, 0, 0, 0, reward_group])
        check('native reward selector chooses ' + reward_row['name'], points, struct.pack('>H', reward))
        call(0x800B8B8C, [0x80126EC0, reward, 0], 1)
        check('actual acquisition retains the reward pocket ID', 0x80126ED4, struct.pack('>H', reward))
        owned = bytearray(128)
        bit = (reward - 0x3000) // 4
        owned[bit // 8] |= 1 << (bit & 7)
        check('reward enters the saved ownership catalogue', 0x8046C000 + 208, owned)

    try:
        if not scoring_only:
            catalogue_and_stock()
        loaded, proof = load(hra, 'hra')
        hr = report['hra']
        put(0x80107B50, owner)
        put(layers, first); put(layers + 4, second)
        linked = lambda address: owner + address - hra.RAM
        call(linked(0x8092817C), [layers, 16], proof=proof)
        info = linked(hr['series']['info_address'])
        active = [r for r in report[key]['imports'] if r['enabled']]
        member_count = sum(r['series'] == theme for r in active)
        check('theme counts only selected members', info + theme * 3, bytes((2, member_count, 255)))
        if scoring_only:
            check('unselected boxing theme has no members', info + 58 * 3, bytes.fromhex('0200FF'))
        search = linked(hr['series']['search_address'])
        check('empty theme has no completion mask', search + theme * 4, bytes(4))
        put(points, 17)
        call(linked(0x809274F8), [points, layers, 16, 0, 0], proof=proof)
        baseline = u32(debug.read_memory(points, 4), 0)
        grid, counts = bytearray(512), [0] * 23
        for slot, row in enumerate(active):
            struct.pack_into('>H', grid, (17 + slot) * 2, int(row['item_id'], 16))
            counts[row['birth_category']] += 1
        debug.write_memory(first, grid)
        call(linked(0x8092817C), [layers, 16], proof=proof)
        check('selected items complete their real theme', search + theme * 4,
              struct.pack('>I', (1 << member_count) - 1))
        weights = struct.unpack_from('>23I', loaded, hr['birth_extension']['points_address'] - hra.RAM)
        put(points, 17)
        call(linked(0x809274F8), [points, layers, 16, 0, 0], proof=proof)
        check('real imported IDs reach their complete acquisition counters', TEST_STACK - 92, struct.pack('>23I', *counts))
        check('native acquisition weights retain their full values', points,
              struct.pack('>I', baseline + sum(n * w for n, w in zip(counts, weights, strict=True))))
        for at in guards: check('allocation guard', at, edge)
        check('no CPU fault', 0x8003CE34, bytes(4))
    finally:
        for at, value in saved.items(): debug.write_memory(at, value)
    check('complete saved state restored', 0x8046C000, saved[0x8046C000])
    call(0x8009C040, [allocation])
    return {key + '_catalogue_rules': not scoring_only,
            'native_event_acquisition' if western else 'native_lottery_acquisition': not scoring_only,
            'actual_theme_group_and_birth_points': True, 'saved_data_written': False,
            'post_office_delivery_or_ordinary_gameplay_tested': False,
            'requires_checkpoint_restore': True}
