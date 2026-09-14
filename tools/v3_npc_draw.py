"""Convert pilot draw rows and bind both native NPC overlay routes."""
import struct

from aflib import by_vrom, sha256, u32
from gc_names import symbol_data
from v3_registry import REGISTRY_VERSION, villager_actor
from v3_villager_art import (DRAW_STRIDE, NATIVE_DRAW_VROM, PILOTS, native_species)

BLOB_SIZE, ABI, DRAW_OFFSET, STRIDE = 0x4000, 2, 0x2000, 104
SOURCE_FILES = ('tools/v3_npc_draw.py', 'tools/v3_registry.py',
                'overlays/v3/npc_draw.c', 'overlays/v3/npc_voice.S')
OWNERS = (
    (0x8681F0, 0x878550, 0x809735B0, 0x809809FC, 0x8097F93C, 0xC0, 'af_v3_npc_voice_tail'),
    (0x8798C0, 0x886FA0, 0x80995BF0, 0x809A0AB8, 0x8099FCEC, 0xB8, 'af_v3_npc2_voice_tail'),
)


def draw_records(native, rel, symbols, artwork):
    table = symbol_data(rel, symbols.decode(), 'npc_draw_data_tbl')
    native_table = by_vrom(native)[NATIVE_DRAW_VROM].extract(native)
    if len(native_table) != 32720 or any(native_table[8 + i * 100 + 95] == 255 for i in range(327)):
        raise ValueError('Native draw table no longer leaves the imported voice marker unused')
    result, report = bytearray(20 * STRIDE), []
    for row in artwork['villagers']:
        donor, species, _ = PILOTS[row['name'].lower()]
        actor = villager_actor(donor)
        bank = 410 + donor - 216
        source = table[donor * DRAW_STRIDE:(donor + 1) * DRAW_STRIDE]
        template, _, _ = native_species(native, species)
        if sha256(source) != row['donor_draw_record_sha256']:
            raise ValueError('Draw row is not the artwork-verified donor identity')
        # Native model, skeleton, expression ordering, and TMEM offsets. Identity-
        # specific dimensions/flags come from the verified donor, not its template.
        draw = bytearray(template)
        struct.pack_into('>H', draw, 2, bank)
        draw[0x54:0x5F] = source[0x54:0x5F]
        draw[0x5F] = 255
        draw[0x60:0x64] = source[0x64:0x68]
        voice = struct.unpack_from('>H', source, 0x62)[0]
        if voice != row['donor_voice_id'] or voice >= 299 or source[0x5F:0x62] != bytes(3):
            raise ValueError('Unsupported donor voice or additional draw flags')
        at = (donor - 216) * STRIDE
        result[at:at + STRIDE] = struct.pack('>HH', actor, voice) + draw
        report.append({'id': row['id'], 'name': row['name'], 'actor_id': f'{actor:04X}',
            'object_bank': bank, 'voice_id': voice, 'record_sha256': sha256(draw),
            'registry_version': REGISTRY_VERSION, 'audio_playback_ready': False})
    return bytes(result), report


def relocation_offsets(data, resident_size):
    text, rodata, other, bss, count = struct.unpack_from('>5I', data)
    if text + rodata + other != resident_size or 20 + count * 4 > len(data) - 4:
        raise ValueError('Unexpected native NPC relocation dimensions')
    result = set()
    for (word,) in struct.iter_unpack('>I', data[20:20 + count * 4]):
        section, kind, offset = word >> 30, word >> 24 & 63, word & 0xFFFFFF
        if section not in (1, 2, 3) or kind not in (2, 4, 5, 6):
            raise ValueError('Unsupported NPC relocation')
        size, base = ((text, 0), (rodata, text), (other, text + rodata))[section - 1]
        if offset % 4 or offset + 4 > size or base + offset in result:
            raise ValueError('Out-of-bounds or duplicate NPC relocation')
        result.add(base + offset)
    return result


def patch_owners(native, base, symbols):
    files, original = by_vrom(base), by_vrom(native)
    changes, report = {}, []
    for vrom, reloc, ram, draw, tail, frame, helper in OWNERS:
        before = files[vrom].extract(base)
        data = bytearray(before)
        reloc_data = files[reloc].extract(base)
        if reloc_data != original[reloc].extract(native):
            raise ValueError('Native NPC relocation table has changed')
        slots = relocation_offsets(reloc_data, len(data))
        hooks = ((draw, 'af_v3_npc_draw', (0x27BDFF70, 0xAFA50094)),
                 (tail, helper, (0x8FB00020, 0x27BD0000 | frame)))
        for address, name, expected in hooks:
            at, target = address - ram, symbols[name]
            if (struct.unpack_from('>2I', data, at) != expected or {at, at + 4} & slots
                    or not 0x80460100 <= target < 0x80461000 or target % 4):
                raise ValueError('Changed NPC hook bytes, relocation, or helper address')
            struct.pack_into('>2I', data, at, 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
        # The tail hook consumes the existing caller frame and saved RA/S0.
        if (u32(data, tail - ram - 4) != 0x8FBF0024
                or data[tail - ram + 8:tail - ram + 16] != struct.pack('>2I', 0x03E00008, 0)):
            raise ValueError('Changed NPC constructor epilogue')
        changes[vrom] = bytes(data)
        report.append({'vrom': f'{vrom:08X}', 'link_address': f'{ram:08X}',
            'draw_hook': f'{draw:08X}', 'voice_tail_hook': f'{tail:08X}',
            'source_sha256': sha256(before), 'patched_sha256': sha256(data),
            'relocation_sha256': sha256(reloc_data), 'relocations_unchanged': True})
    return changes, report
