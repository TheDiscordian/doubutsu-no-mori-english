"""Current native map/address/quest/identity and generated-mail name consumers."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import by_vrom, sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_npc_draw_smoke import boot_proofs
from v3_villager_readers import OWNERS, TEXT, CREATOR


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report.get('villager_readers'):
        raise ValueError('Name-reader fixture requires the current assembled cartridge')
    files, proofs = by_vrom(rom), boot_proofs(rom)
    # Generated mail embeds relocation bytes in the same DMA file. It uses
    # explicit DMA/relocation, not ovlmgr's consecutive-directory-entry loader.
    for address, size, digest in (
            (0x80026B44, 0x7C, '2afa01edf9346c8c9f4a0c6b5fbadb03970d0e348c25f045d09af4ee2602f8d1'),
            (0x8002B9C0, 0x240, '41c8a44c62952d0c323eb039049879515466c46aa55d8cee3a0eed1723dda861')):
        at = 0x1060+address-0x80025C60
        expected = rom[at:at+size]
        if sha256(expected) != digest:
            raise ValueError('Changed explicit cartridge DMA/relocation helper')
        proofs[address] = (address, expected)
    prefix = files[BLOB].extract(rom)[:0xC000]

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'villager_reader_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Native name-reader mismatch: '+label)

    def call(at, args, proof=None, expected=None):
        value = debug.call(f'{at:08X}', args, return_address=MODULE_RAM+0x6480,
                           verified_code=proof or proofs.get(at))
        record(value)
        if expected is not None and value['return_value'] != expected:
            raise ValueError('Unexpected native name-reader return')
        return value['return_value']

    check('complete startup prefix', BLOB_RAM, prefix)
    allocation = call(0x8009BFC0, [0x13000])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-0x13000:
        raise ValueError('Name-reader fixture allocation failed')
    base, identity, out, sources, key, length = (allocation+v for v in (16, 0x10000, 0x10400, 0x10500, 0x10600, 0x10700))
    edge = b'V3NR'*4
    guards = (allocation, identity-16, identity+0x200, out-16, out+32,
              sources-16, sources+16, key-16, key+16, length-16, length+16,
              allocation+0x13000-16, TEST_STACK-0x800, TEST_STACK+0x40)
    for address in guards:
        debug.write_memory(address, edge)

    def load(vrom):
        ram, rel, _, _ = OWNERS[vrom]
        raw = files[vrom].extract(rom)
        data, relocation = (raw, files[rel].extract(rom)) if rel > len(raw) else (raw[:rel], raw[rel:])
        sections = struct.unpack_from('>5I', relocation)
        size = len(data)+sections[3]
        if size+len(relocation)+32 >= identity-base:
            raise ValueError('Native name-reader owner exceeds the fixture')
        spec = SimpleNamespace(ram=ram, resident_bytes=size, sections=sections)
        expected = relocate_verified_data(spec, data, relocation, base)
        if rel > len(raw):
            call(0x800262D0, [vrom, vrom+len(data), ram, ram+size, base, base+size, len(relocation)])
        else:
            call(0x80026B44, [base, vrom, len(raw)])
            call(0x8002B9C0, [base, base+len(data), ram])
            call(0x8002FE00, [base, len(data)])
            call(0x80034CE0, [base, len(data)])
        check('complete loaded/relocated owner', base, expected)
        debug.write_memory(base+size+len(relocation), edge)
        return expected, size+len(relocation)

    native_name = files[0x2C00000].extract(rom)[32:40]
    names = ((0xE000, native_name), (0xE0EA, b'Cheri   '), (0xE0ED, b'Punchy  '))
    loaded, owner_size = load(CREATOR)
    original_creator = files[CREATOR].extract(rom)
    debug.write_memory(sources, struct.pack('>3I', base+0x9E00, base+0xCA40, 0x41464353))
    for npc, name in names:
        debug.write_memory(out, b'!'*32)
        call(base+0x898, [out, sources, npc], (base+0x898, loaded[0x898:0x8A0]), 1)
        check('complete generated-letter field', out, b'\x08\0'+name+bytes(8)+b'!'*14)
        if npc >= 0xE0DA:
            alias = name[:6]
        else:
            alias = next(original_creator[i:i+6] for i in range(0xCA80, 0xCA40+6368, 16)
                         if original_creator[i+6:i+8] == bytes(2))
        debug.write_memory(key, alias)
        debug.write_memory(out, b'!'*32)
        call(base+0x928, [out, sources, key], (base+0x928, loaded[0x928:0x930]), 1)
        check('complete reply alias field', out, b'\x08\0'+name+bytes(8)+b'!'*14)
    for npc in (0xE0D8, 0xE0DA, 0xE0EE):
        debug.write_memory(out, b'!'*32)
        call(base+0x898, [out, sources, npc], (base+0x898, loaded[0x898:0x8A0]), 0)
        check('rejected identity leaves output intact', out, b'!'*32)
    # Disabling a record must also disable its six-byte reply alias.
    present = BLOB_RAM+0x2C00+(0xE0EA-0xE0DA)*32+7
    previous = debug.read_memory(present, 1)
    try:
        debug.write_memory(present, b'\0')
        debug.write_memory(key, b'Cheri ')
        call(base+0x898, [out, sources, 0xE0EA], (base+0x898, loaded[0x898:0x8A0]), 0)
        call(base+0x928, [out, sources, key], (base+0x928, loaded[0x928:0x930]), 0)
        check('disabled name/alias is no-write', out, b'!'*32)
    finally:
        debug.write_memory(present, previous)
    check('creator boundary', base+owner_size, edge)

    loaded, owner_size = load(0x3E60000)
    for npc, name in names:
        saved = bytearray(18); saved[:6] = b'Old   '; saved[12] = npc & 255; saved[16] = 1
        debug.write_memory(identity, saved)
        debug.write_memory(out, b'!'*32)
        call(base+0x1CE0, [out, identity], (base+0x1CE0, loaded[0x1CE0:0x1DA8]), 8)
        check('complete address-list name', out, name+b'!'*24)
        check('saved address unchanged', identity, saved)
    check('address owner boundary', base+owner_size, edge)

    loaded, owner_size = load(0x3950000)
    for npc, name in names:
        debug.write_memory(identity, struct.pack('>H', npc)+bytes(14))
        debug.write_memory(out, b'!'*32)
        call(base+0xAA4C, [out, identity], (base+0xAA4C, loaded[0xAA4C:0xAAD4]))
        check('complete inventory quest name', out, name+b'!'*24)
    check('inventory owner boundary', base+owner_size, edge)

    loaded, owner_size = load(0x3B00000)
    for npc, name in names:
        debug.write_memory(identity, struct.pack('>H', npc)+bytes(14))
        debug.write_memory(out, b'!'*32)
        call(base+0x64C8, [out, identity], (base+0x64C8, loaded[0x64C8:0x65FC]))
        short = files[0xE04000].extract(rom)[8:14] if npc == 0xE000 else name[:6]
        check('native six-byte map destination retained', out, short+b'!'*26)
        debug.write_memory(length, struct.pack('>I', 6))
        pointer = call(base+0x65FC, [out, length], (base+0x65FC, loaded[0x65FC:0x6654]))
        check('map full-name cache', pointer, name)
        check('map full-name length', length, struct.pack('>I', 8))
    check('map owner boundary', base+owner_size, edge)

    # The live startup-owned identity adapter proves the changed text CRC boots.
    entry_word = struct.unpack('>I', debug.read_memory(0x800BB708, 4))[0]
    if entry_word >> 26 != 2:
        raise ValueError('Startup identity bridge is not installed')
    entry = 0x80000000 | ((entry_word & 0x3FFFFFF) << 2)
    raw = files[TEXT].extract(rom)
    expected = relocate_verified_data(SimpleNamespace(ram=0x80D00000, resident_bytes=3808,
        sections=struct.unpack_from('>5I', raw, 3808)), raw[:3808], raw[3808:], entry-0x468)
    for npc, name in names:
        debug.write_memory(identity, struct.pack('>H', npc)+bytes(14))
        debug.write_memory(out, b'!'*32)
        call(entry, [out, identity], (entry, expected[0x468:0x4F8]))
        check('complete conversation identity name', out, name+b'!'*24)
    for address in guards:
        check('fixture guard', address, edge)
    check('resident prefix unchanged', BLOB_RAM, prefix)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    call(0x8009C040, [allocation])
    return {'native_generated_name_and_alias_readers': 2, 'native_display_paths': 4,
            'complete_letter_or_notice_generation_tested': False, 'house_visit_tested': False,
            'saved_data_written': False, 'requires_checkpoint_restore': True}
