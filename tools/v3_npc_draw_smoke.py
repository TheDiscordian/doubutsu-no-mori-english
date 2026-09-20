"""Bounded native overlay draw and constructor-tail checks; no move-ins or saves."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import by_vrom, sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_npc_draw import OWNERS, DRAW_OFFSET, STRIDE

BOOT_PROOFS = {
    0x80026B44: (124, '2afa01edf9346c8c9f4a0c6b5fbadb03970d0e348c25f045d09af4ee2602f8d1'),
    0x800262D0: (240, '2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00'),
    0x8002FE00: (116, '5306341d7122fdbbae63d48917c76f7f6c2ee0321e490862302581561bf0474c'),
    0x80034CE0: (116, '713e7b78373df6fbf3d030b5237e9c1e2148c9443cbfdf938f2e8ffdf8e2d326'),
}


def boot_proofs(rom):
    result = {}
    for address, (length, digest) in BOOT_PROOFS.items():
        start = address - 0x80025C60 + 0x1060
        data = rom[start:start + length]
        if sha256(data) != digest:
            raise ValueError('Changed native loader/cache instructions for V3 fixture')
        result[address] = (address, data)
    return result


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['npc_draw']:
        raise ValueError('V3 draw probe needs its exact current cartridge')
    files = by_vrom(rom)
    boot = boot_proofs(rom)
    blob = files[BLOB].extract(rom)
    return_pc = MODULE_RAM + 0x6480
    edge = b'V3ED' * 4

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'v3_draw_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected:
            raise ValueError('V3 draw check failed: ' + label)

    def call(address, args, proof=None, expected=None):
        if proof is None:
            proof = boot.get(address)
        result = debug.call(f'{address:08X}', args, return_address=return_pc, verified_code=proof)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError('V3 draw call returned an unexpected value')
        return result['return_value']

    check('complete startup blob', BLOB_RAM, blob)
    check('startup installed', 0x8019ACD0, struct.pack('>I', 1))
    size = 0x24C00
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x80400000 - size:
        raise ValueError('V3 native draw fixture allocation failed')
    # Deliberately use the native caller's four-byte-only alignment.
    base, actor, output, bridge = allocation + 16, allocation + 0x24000, allocation + 0x24A14, allocation + 0x24B00
    for at in (allocation, allocation + size - 16, actor - 16, output - 16,
               output + 112, TEST_STACK - 0x800, TEST_STACK + 0x40):
        debug.write_memory(at, edge)
    assertions = 0
    for vrom, reloc_vrom, ram, draw, tail, frame, helper in OWNERS:
        source, reloc = files[vrom].extract(rom), files[reloc_vrom].extract(rom)
        owner_report = next(r for r in report['npc_draw']['owners'] if int(r['vrom'], 16) == vrom)
        if sha256(source) != owner_report['patched_sha256'] or sha256(reloc) != owner_report['relocation_sha256']:
            raise ValueError('Changed V3 NPC test owner')
        sections = struct.unpack_from('>5I', reloc)
        spec = SimpleNamespace(ram=ram, resident_bytes=len(source) + sections[3], sections=sections)
        if spec.resident_bytes + len(reloc) >= actor - base - 16:
            raise ValueError('V3 draw fixture overlaps its NPC actor')
        # Biased table bases add Dxxx*2 to reach the real special-NPC data.
        # Preserve those native relocation addends and the BSS/relocation end.
        constants = (0x80969690 if vrom == 0x8681F0 else 0x80989060,
                     ram + spec.resident_bytes)
        expected_overlay = relocate_verified_data(spec, source, reloc, base, address_constants=constants)
        call(0x800262D0, [vrom, vrom + len(source), ram, ram + spec.resident_bytes,
                          base, base + spec.resident_bytes, len(reloc)])
        check('complete relocated NPC and BSS', base, expected_overlay)
        proof = (base, expected_overlay[:sections[0]])
        entries = [(0xE000, files[0xE05000].extract(rom)[8:108]),
                   (0xE0D9, files[0xE05000].extract(rom)[8 + 217 * 100:8 + 218 * 100])]
        for row in report['npc_draw']['imports']:
            actor_id = int(row['actor_id'], 16)
            at = DRAW_OFFSET + (actor_id - 0xE0DA) * STRIDE
            entries.append((actor_id, blob[at + 4:at + STRIDE]))
        for actor_id, draw_data in entries:
            debug.write_memory(output, bytes(112))
            call(base + draw - ram, [output, actor_id], proof, 1)
            check(f'draw row {actor_id:04X}', output, draw_data + bytes(12))
            # Recreate only the constructor frame so the actual patched tail
            # performs its voice assignment. This is not a complete NPC init.
            row_offset = 0x58 if frame == 0xC0 else 0x50
            words = [0x27BD0000 | (-frame & 0xFFFF), 0xAFBF0024, 0xAFB00020,
                     0x00808025, 0x00A04025, 0x27A90000 | row_offset, 0x240A0019,
                     0x8D0B0000, 0xAD2B0000, 0x25080004, 0x25290004,
                     0x254AFFFF, 0x1540FFFA, 0,
                     0x08000000 | ((base + tail - ram) >> 2 & 0x3FFFFFF), 0]
            wrapper = struct.pack('>' + 'I' * len(words), *words)
            debug.write_memory(bridge, wrapper)
            # Explicit cache maintenance before executing the small fixture.
            call(0x8002FE00, [bridge, len(wrapper)])
            call(0x80034CE0, [bridge, len(wrapper)])
            actor_data = bytearray(b'\xA5' * 0x93C)
            debug.write_memory(actor, actor_data)
            call(bridge, [actor, output], (bridge, wrapper))
            voice = draw_data[95]
            if actor_id >= 0xE0DA:
                voice = next(r['voice_id'] for r in report['npc_draw']['imports']
                             if int(r['actor_id'], 16) == actor_id)
            struct.pack_into('>I', actor_data, 0x930, voice)
            check(f'constructor tail actor {actor_id:04X}', actor, bytes(actor_data))
            assertions += 2
        call(base + draw - ram, [output, 0xE0DA], proof, 0)
        check('missing import leaves output intact', output, entries[-1][1] + bytes(12))
    for at in (allocation, allocation + size - 16, actor - 16, output - 16,
               output + 112, TEST_STACK - 0x800, TEST_STACK + 0x40):
        check('fixture guard', at, edge)
    check('complete V3 blob remains intact', BLOB_RAM, blob)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    return {'native_draw_owners': 2, 'draw_and_tail_assertions': assertions,
            'complete_npc_construction': False, 'audio_playback_tested': False,
            'requires_checkpoint_restore': True}
