"""Native HRA grouping and full garment point evaluation, with boundary guards."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, u32
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION
from v3_npc_draw_smoke import boot_proofs
import v3_hra as hra


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    image = path.read_bytes()
    report = json.loads((path.parent / 'build.json').read_text())
    if sha256(image) != report['output_sha256'] or not report.get('aloha_scoring'):
        raise ValueError('Aloha scoring check requires the corrected current cartridge')
    files = by_vrom(image)
    boot = boot_proofs(image)
    hr = report['hra']
    data, reloc = (files[v].extract(image) for v in (hra.NEW_VROM, hra.NEW_RELOC))
    if sha256(data) != hr['output_sha256'] or sha256(reloc) != hr['relocation_sha256']:
        raise ValueError('Changed actual scoring owner')

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'aloha_scoring_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected: raise ValueError('Aloha scoring mismatch: ' + label)

    def call(address, args, proof=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480, verified_code=proof or boot.get(address))
        record(result)
        return result['return_value']

    def put(address, value): debug.write_memory(address, struct.pack('>I', value))

    allocation = call(0x8009BFC0, [0x9000])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x803F7000:
        raise ValueError('Aloha scoring fixture allocation failed')
    owner = allocation + 16
    layers, points, first, second = (allocation + n for n in (0x8000, 0x8020, 0x8100, 0x8400))
    if owner + len(data) + len(reloc) >= layers - 16:
        raise ValueError('Aloha scoring fixture overlaps native owner')
    debug.write_memory(allocation, bytes(0x9000))
    loaded = relocate_verified_data(Image(hra.RAM, len(data), struct.unpack_from('>5I', reloc)), data, reloc, owner)
    call(0x800262D0, [hra.NEW_VROM, hra.NEW_VROM + len(data), hra.RAM, hra.RAM + len(data), owner, owner + len(data), len(reloc)])
    check('complete actual native HRA relocation', owner, loaded)
    proof = (owner, loaded[:hra.SECTIONS[0]])
    linked = lambda address: owner + address - hra.RAM
    saved = {at: debug.read_memory(at, size) for at, size in ((0x80107B50, 4), (0x80466544, 4), (0x8046C000, 864))}
    edge = b'V3AS' * 4
    search_at = hr['series']['search_address'] - hra.RAM
    search_end = owner + search_at + 59 * 4
    # The 12-byte final padding and subsequent dead relocation scratch are not
    # live state. A guard here catches a series-63 mask write past 59 entries.
    if search_end != owner + len(data) - 12:
        raise ValueError('Changed HRA completion-mask end/padding contract')
    guards = (allocation, layers - 16, first - 16, first + 512, second - 16,
              second + 512, allocation + 0x8FF0, search_end)
    for at in guards: debug.write_memory(at, edge)
    try:
        put(0x80107B50, owner)
        put(layers, first); put(layers + 4, second)
        metadata_at = hr['metadata_address'] - hra.RAM
        info_at = hr['series']['info_address'] - hra.RAM
        metadata = bytearray(loaded[metadata_at:metadata_at + 2051 * 4])
        info = bytearray(loaded[info_at:info_at + 59 * 3])
        for series in range(59):
            group, count = (5 if info[series * 3] == 1 else 0), 0
            for index in range(2051):
                word = u32(metadata, index * 4)
                if word >> 26 == series:
                    if info[series * 3] != 1 or word >> 16 & 1023 >= 5:
                        struct.pack_into('>I', metadata, index * 4, word & 0xFC00FFFF | group << 16)
                        group += 1
                    count += 1
            info[series * 3 + 1] = count & 255
        call(linked(0x8092817C), [layers, 5], proof)
        check('all 2051 native and imported group assignments', owner + metadata_at, metadata)
        check('all 59 series counts include construction and both aloha displays', owner + info_at, info)
        check('empty-room completion masks', owner + search_at, bytes(59 * 4))
        put(points, 0)
        call(linked(0x809274F8), [points, layers, 5, 0, 0], proof)
        baseline = u32(debug.read_memory(points, 4), 0)
        clothing_points = u32(loaded, 0x80928680 - hra.RAM + 8 * 4)
        for item in (0x3868, 0x386B, 0x386C, 0x386F, 0x3AFC):
            grid = bytearray(512)
            struct.pack_into('>H', grid, 34, item)
            debug.write_memory(first, grid)
            call(linked(0x8092817C), [layers, 5], proof)
            check('garment completion never exceeds the series array', search_end, edge)
            put(points, 0)
            call(linked(0x809274F8), [points, layers, 5, 0, 0], proof)
            check(f'complete garment {item:04X} uses native clothing points', points, struct.pack('>I', baseline + clothing_points))
        grid = bytearray(512); struct.pack_into('>H', grid, 34, 0x3868)
        debug.write_memory(first, grid)
        put(0x80466544, 0); put(points, 0)
        call(linked(0x809274F8), [points, layers, 5, 0, 0], proof)
        check('disabled display contributes no points', points, struct.pack('>I', baseline))
        check('complete native executable stays unchanged', owner, loaded[:hra.SECTIONS[0]])
        for at in guards: check('fixture and mask boundary guard', at, edge)
        check('no fault', 0x8003CE34, bytes(4))
    finally:
        for at, value in saved.items(): debug.write_memory(at, value)
    check('complete import save state retained', 0x8046C000, saved[0x8046C000])
    call(0x8009C040, [allocation])
    return {'native_aloha_hra_grouping': True, 'complete_garment_point_cases': 5,
            'disabled_display_rejected': True, 'saved_data_written': False,
            'ordinary_hra_letter_or_house_gameplay_tested': False, 'requires_checkpoint_restore': True}
