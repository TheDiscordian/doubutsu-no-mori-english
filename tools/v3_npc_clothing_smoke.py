"""Run both relocated NPC owners' complete clothing loops with real native DMA."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import by_vrom, sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_npc_draw import OWNERS
from v3_npc_draw_smoke import boot_proofs


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['clothing']['npc_streaming_clothes_installed']:
        raise ValueError('NPC clothing probe requires the current assembled cartridge')
    files, boot = by_vrom(rom), boot_proofs(rom)
    blob_file = files[BLOB].extract(rom)
    prefix = blob_file[:0xC000]

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'npc_clothing_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected: raise ValueError('NPC clothing mismatch: '+label)

    def call(address, args, proof=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM+0x6480,
                            verified_code=proof if proof else boot.get(address))
        record(result)
        return result['return_value']

    check('complete startup prefix', BLOB_RAM, prefix)
    # Largest image + BSS + relocation is 22640 bytes; keep only the
    # measured overlay, ten clothing slots, three outputs, and guard gaps.
    size = 0x23800
    allocation = call(0x8009BFC0, [size])
    if allocation % 16 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('NPC clothing fixture allocation failed')
    base, actor, buffers = allocation+16, allocation+0x22700, allocation+0x23000
    edge = b'V3NC'*4
    guards = [allocation, actor-16, buffers-16, allocation+size-16,
              TEST_STACK-0x800, TEST_STACK+0x40]
    for i in range(3):
        at = buffers+i*0x280
        guards += [at, at+0x210, at+0x240, at+0x270]
    for at in guards: debug.write_memory(at, edge)
    native_tex, native_pal = (files[v].extract(rom) for v in (0xB68000, 0xB88000))
    expected = [(0x24BF, native_tex[0x17E00:0x18000], native_pal[0x17E0:0x1800]),
                (0x34BF, blob_file[0xF000:0xF200], blob_file[0xF200:0xF220]),
                (0x2400, native_tex[:512], native_pal[:32])]
    for owner_index, (vrom, reloc_vrom, ram, *_) in enumerate(OWNERS):
        source, reloc = files[vrom].extract(rom), files[reloc_vrom].extract(rom)
        owner = report['clothing']['owners'][owner_index]
        if (sha256(source), sha256(reloc)) != (owner['patched_sha256'], owner['relocation_sha256']):
            raise ValueError('Changed NPC clothing owner or relocation')
        sections = struct.unpack_from('>5I', reloc)
        spec = SimpleNamespace(ram=ram, resident_bytes=len(source)+sections[3], sections=sections)
        if spec.resident_bytes+len(reloc) >= actor-base-16:
            raise ValueError('NPC clothing fixture overlaps its controller')
        constants = (0x80969690 if owner_index == 0 else 0x80989060, ram+spec.resident_bytes)
        relocated = relocate_verified_data(spec, source, reloc, base, address_constants=constants)
        call(0x800262D0, [vrom, vrom+len(source), ram, ram+spec.resident_bytes,
                          base, base+spec.resident_bytes, len(reloc)])
        check('complete relocated NPC owner and BSS', base, relocated)
        proof = (base, relocated[:sections[0]])
        pointer = base+(0x80981970 if owner_index == 0 else 0x809A1350)-ram
        debug.write_memory(pointer, struct.pack('>I', actor))
        for mode in ('foreground', 'queued'):
            control = bytearray(0x174+10*0xB0)
            for i, item in enumerate((0x24BF, 0x34BF, 0x3224)):
                at, out = 0x174+i*0xB0, buffers+i*0x280
                control[at] = 1
                struct.pack_into('>H', control, at+4, item)
                control[at+6:at+8] = b'\x07\x09'
                struct.pack_into('>I', control, at+0xC, out+16)
                struct.pack_into('>I', control, at+0x60, out+0x220)
                debug.write_memory(out+16, b'\xA5'*512)
                debug.write_memory(out+0x220, b'\xA5'*32)
            debug.write_memory(actor, control)
            entry = base+(0x314 if mode == 'foreground' else 0x178)
            call(entry, [actor], proof)
            if mode == 'queued':
                # Debugger reads do not advance emulated time. Retain the native
                # frame between request submission and the completion poll.
                for i in range(3): check('queued slot remains pending', actor+0x174+i*0xB0, b'\x01')
                record(debug.advance_game_frame())
                call(entry, [actor], proof)
            for i, (item, texture, palette) in enumerate(expected):
                slot, out = actor+0x174+i*0xB0, buffers+i*0x280
                check(f'{owner_index}/{mode}/{item:04X} completed slot', slot, bytes(1))
                check(f'{owner_index}/{mode}/{item:04X} full identity and flags', slot+4,
                      struct.pack('>H', item)+b'\x07\x09')
                check(f'{owner_index}/{mode}/{item:04X} complete texture', out+16, texture)
                check(f'{owner_index}/{mode}/{item:04X} complete palette', out+0x220, palette)
            check(f'{owner_index}/{mode} unused seven slots intact', actor+0x174+3*0xB0, bytes(7*0xB0))
    for at in guards: check('fixture guard', at, edge)
    check('resident prefix intact', BLOB_RAM, prefix)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    call(0x8009C040, [allocation])
    return {'complete_native_clothing_loops': 4, 'native_imported_invalid_shirt_rows': 12,
            'saved_data_written': False, 'punchy_defaults_enabled': False,
            'ordinary_wearing_gameplay_tested': False, 'requires_checkpoint_restore': True}
