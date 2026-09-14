"""Reuse the native clothing mannequin with a stable additive display identity."""
import struct
from types import SimpleNamespace

from aflib import by_vrom, sha256, u32, verified_rom
from npc_mail_show import relocate_verified_data
from v3_furniture_runtime import RAM as ROOM_RAM, VROM as ROOM_VROM, SOURCE_SHA as ROOM_SHA
from v3_registry import CLOTHING_DISPLAY_REGISTRY_VERSION, CLOTHING_DISPLAYS, clothing_slot

ABI, PROGRAM, CODE, ROW = 41, 0x6000, 0x6200, 0x6600
VROM, RELOC, RAM, SIZE = 0x0093BD70, 0x0093BF40, 0x80A7BAD0, 464
MODEL, MODEL_BYTES = 0x013EB000, 0xE00
SOURCE_SHA = '42f752c86de909ca6654c1c165e53018ad31acfe6213f3c0b7ffe9a8ecab1bed'
RELOC_SHA = 'ca03b05538a25228788904bd8a65fe602c23495780716f9d716abfc8e5f07331'
MODEL_SHA = '342d1b7278455b6ce84a4968ee16ed6d6e54a8e6612b9b8a5010d8cb32410cd5'
SECTIONS = (0x150, 0x60, 0x20, 0, 8)
SOURCES = ('tools/v3_clothing_display.py', 'overlays/v3/clothing_display.c',
           'overlays/v3/clothing_display.h', 'overlays/v3/clothing_display.ld')
WINDOW = bytes.fromhex('288117ac1420000624e5020028811ba8102000032486e854100000020006308300003025')


def profile_dependency():
    index, item = CLOTHING_DISPLAYS[0x24BF]
    if (index, item) != (1024 + ((item & 0xFFF) >> 2), 0x3AFC):
        raise ValueError('Changed stable clothing-display reservation')
    return {'runtime_index': index, 'item_id': f'{item:04X}',
            'registry_version': CLOTHING_DISPLAY_REGISTRY_VERSION,
            'donor_item_id': '24BF', 'pocket_item_id': f'{clothing_slot(0x24BF)[0]:04X}',
            'profile_ram': f'{0x80460000+ROW+8:08X}',
            'independently_selectable': False}


def program(native):
    verified_rom(native)
    files = by_vrom(native)
    data, reloc, model, room = (files[v].extract(native) for v in (VROM, RELOC, MODEL, ROOM_VROM))
    if (sha256(data) != SOURCE_SHA or len(data) != SIZE or sha256(reloc) != RELOC_SHA
            or struct.unpack_from('>5I', reloc) != SECTIONS or u32(reloc, 60) != 64
            or len(model) != MODEL_BYTES or sha256(model) != MODEL_SHA or sha256(room) != ROOM_SHA):
        raise ValueError('Changed native clothing program, model, or room owner')
    for index in range(491, 746):
        if (struct.unpack_from('>4I', room, 0x80947638-ROOM_RAM+index*16) !=
                (VROM, RELOC, RAM, RAM+SIZE)
                or u32(room, 0x8094B168-ROOM_RAM+index*4) != RAM+0x164):
            raise ValueError('Native clothing does not share the verified complete mannequin')
    if data[0xDC:0x100] != WINDOW:
        raise ValueError('Changed native mannequin index window')
    loaded = bytearray(relocate_verified_data(
        SimpleNamespace(ram=RAM, resident_bytes=SIZE, sections=SECTIONS),
        data, reloc, 0x80460000+PROGRAM, memory_end=0x80800000))
    # The callback already owns caller argument slot +24 and saves outer RA at
    # +1C. Preserve its bank across the C call, then retain both native DMAs.
    struct.pack_into('>9I', loaded, 0xDC, 0xAFA70024,
                     0x0C000000 | ((0x80460000+CODE) >> 2 & 0x3FFFFFF), 0,
                     0x8FA70024, 0x00403025, 0x24E50200, 0, 0, 0)
    if struct.unpack_from('>5I', loaded, 0x150) != tuple(
            0x80460000+PROGRAM+n for n in (0, 0xA0, 0x10, 0xB8, 0xC8)):
        raise ValueError('Relocated native mannequin callbacks do not match their profile')
    return bytes(loaded)


def install(native, base, blob, helper, compiled, item_readers, save_runtime):
    row = profile_dependency()
    image = program(native)
    files = by_vrom(base)
    if any(sha256(files[v].extract(base)) != digest for v, digest in
           ((VROM, SOURCE_SHA), (RELOC, RELOC_SHA), (MODEL, MODEL_SHA))):
        raise ValueError('The current translation changes the native clothing mannequin')
    if (len(blob) != 0xC000 or any(blob[PROGRAM:ROW+80])
            or not helper or len(helper) > ROW-CODE or len(helper) != compiled['bytes']
            or sha256(helper) != compiled['sha256']
            or compiled['symbols']['af_v3_display_clothing_index'] != 0x80460000+CODE
            or compiled['symbols']['af_v3_item_type'] != item_readers['symbols']['af_v3_item_type']
            or compiled['symbols']['af_v3_item_type'] != 0x8046744C
            or PROGRAM+len(image) > CODE or ROW+80 > 0x66CC):
        raise ValueError('Clothing display code/profile overlaps or changes its dependencies')
    profile = bytes.fromhex(save_runtime['profile_hex'])
    if (len(profile) != 192 or not profile[119] & 0x80 or not profile[183] & 0x80
            or blob[0x20:0xE0] != profile):
        raise ValueError('The display and pocket identities must both be in the saved profile')
    packed = struct.pack('>HHI', row['runtime_index'], int(row['item_id'], 16), 1)
    packed += image[0x164:0x1A8] + bytes(4)
    if len(packed) != 80 or u32(packed, 72) != 0x80466150:
        raise ValueError('Changed complete native mannequin profile')
    blob[PROGRAM:PROGRAM+len(image)] = image
    blob[CODE:CODE+len(helper)] = helper
    blob[ROW:ROW+len(packed)] = packed
    return {'imports': [row], 'native_program_vrom': f'{VROM:08X}',
        'native_program_sha256': SOURCE_SHA, 'native_relocation_sha256': RELOC_SHA,
        'program_ram': f'{0x80460000+PROGRAM:08X}', 'program_bytes': len(image),
        'program_sha256': sha256(image), 'profile_sha256': sha256(packed[8:76]),
        'code': compiled, 'draw_ram': '80466010', 'dma_ram': '804660C8',
        'model_vrom': f'{MODEL:08X}', 'model_bytes': MODEL_BYTES, 'model_sha256': MODEL_SHA,
        'bank_bytes_used': 0x220+MODEL_BYTES, 'native_buffer_growth': 0,
        'original_clothing_profiles_checked': 255, 'global_placement_enabled': False,
        'ordinary_home_display_tested': False, 'catalogue_preview_tested': False,
        'save_profile_dependency': {'byte': 119, 'mask': 128},
        'compatibility': 'Older same-clothing profiles lack the display dependency and reject new saves; preserve backups.'}
