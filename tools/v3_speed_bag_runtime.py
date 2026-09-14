"""Install the animated model/callbacks and explicitly bound gameplay profile."""
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from gc_names import symbol_data
from v3_registry import furniture_slot
from v3_speed_bag import SOURCE_FILES as CALLBACK_SOURCES, build as build_callbacks
from v3_speed_bag_art import build as build_art
from v3_speed_bag_sound_runtime import SOUND_ID

ABI, PROGRAM, SOUND, VTABLE, ROW, END = 49, 0x6F20, 0x7100, 0x7110, 0x7130, 0x7180
SOURCES = CALLBACK_SOURCES + ('tools/v3_speed_bag_runtime.py', 'tools/v3_speed_bag_art.py',
                             'overlays/v3/speed_bag.h')


def install(native, code, blob, rel, symbols, out, *, gameplay=False):
    index, item, vrom = furniture_slot(0x3350)
    if (index, item) != (1236, 0x3350) or len(blob) != 0xC000:
        raise ValueError('Changed speed-bag identity or resident reservation')
    if type(gameplay) is not bool or (gameplay and not blob[0x20+32+26] & 16):
        raise ValueError('Speed-bag gameplay requires its selected save dependency')
    # The expanded profile/index tables no longer use this seed's tail. Two
    # collection bridges at 6F00..6F1F remain live and are not reclaimed.
    before = b'\xFF'*(0x70F3-PROGRAM)+bytes(END-0x70F3)
    if blob[PROGRAM:END] != before or any(blob[0x72E0:0x7300]):
        raise ValueError('Speed-bag code/profile overwrites a live resident resource')
    profile_seed = 0x5800+index*4
    if any(blob[profile_seed:profile_seed+4]):
        raise ValueError('Speed-bag profile replaces an existing furniture identity')
    out.mkdir(parents=True, exist_ok=False)
    art = build_art(rel, symbols, out/'art')
    asset = (out/'art'/art['object_file']).read_bytes()
    if (len(asset) != 0xE90 or sha256(asset) != art['object_sha256']
            or {key: row['native_offset'] for key, row in art['headers'].items()} !=
            {'animation': 0xE58, 'joints': 0xE6C, 'skeleton': 0xE84}):
        raise ValueError('Speed-bag callbacks do not match the complete converted object')
    callbacks, compiled = build_callbacks(native, out/'callbacks', 0x80460000+SOUND)
    if (len(callbacks) > SOUND-PROGRAM or compiled['entry_offsets'] !=
            {'af_v3_speed_bag_ct': 0, 'af_v3_speed_bag_mv': 0x94, 'af_v3_speed_bag_dw': 0x148}):
        raise ValueError('Speed-bag callbacks exceed their checked fixed slots')
    original = by_vrom(native)[CODE_VROM].extract(native)
    sound_native = bytes(code[0x800D1D58-CODE_RAM:0x800D1D94-CODE_RAM])
    if sound_native != original[0x800D1D58-CODE_RAM:0x800D1D94-CODE_RAM]:
        raise ValueError('Changed actual native positional sound entry')
    # Tail call sAdo_OngenTrgStart(u16, xyz*), retaining the original caller RA.
    sound = struct.pack('>4I', 0x00802825, 0x24040000 | SOUND_ID,
                        0x08000000 | (0x800D1D58 >> 2 & 0x3FFFFFF), 0)
    entries = [0x80460000+PROGRAM+compiled['entry_offsets'][name]
               for name in ('af_v3_speed_bag_ct', 'af_v3_speed_bag_mv', 'af_v3_speed_bag_dw')]
    table = struct.pack('>5I', *entries, 0, 0)
    scalar = bytes.fromhex(art['donor_profile_scalar_hex'])
    profile = struct.pack('>12I', vrom, vrom+len(asset), 0x06000000,
                          0x06000000+len(asset), *([0]*8))+scalar+struct.pack('>I', 0x80460000+VTABLE)
    if len(profile) != 68 or u32(profile, 64) != 0x80460000+VTABLE:
        raise ValueError('Invalid complete animated furniture profile')
    # The composer enables gameplay only with the installed shop, catalogue,
    # scoring, score-letter, and save dependencies. Component callers stay off.
    record = struct.pack('>HHI', index, item, int(gameplay))+profile+bytes(4)
    names = symbol_data(rel, symbols.decode(), 'ftrName2_table')
    name = names[(item-0x3000)//4*16:((item-0x3000)//4+1)*16]
    price = symbol_data(rel, symbols.decode(), 'ftr_price_table')[index*2:(index+1)*2]
    if name != b'speed bag       ' or price != bytes.fromhex('0bae'):
        raise ValueError('Changed actual donor speed-bag name or price')
    metadata = struct.pack('>HHHBB', index, item, 2990, 0, 1)+name+bytes(8)
    blob[PROGRAM:END] = bytes(END-PROGRAM)
    blob[PROGRAM:PROGRAM+len(callbacks)] = callbacks
    blob[SOUND:SOUND+len(sound)] = sound
    blob[VTABLE:VTABLE+len(table)] = table
    blob[ROW:ROW+len(record)] = record
    blob[0x72E0:0x7300] = metadata
    struct.pack_into('>I', blob, profile_seed, 0x80460000+ROW+8)
    return asset, {'id': art['id'], 'name': 'speed bag', 'item_id': f'{item:04X}',
        'runtime_index': index, 'object_vrom': f'{vrom:08X}', 'object_bytes': len(asset),
        'object_sha256': sha256(asset), 'profile_ram': f'{0x80460000+ROW+8:08X}',
        'profile_sha256': sha256(profile), 'row_ram': f'{0x80460000+ROW:08X}',
        'vtable_ram': f'{0x80460000+VTABLE:08X}', 'callback_entries': entries,
        'callback_ram': 0x80460000+PROGRAM, 'callback_bytes': len(callbacks),
        'callbacks': compiled, 'artwork': art, 'sound_id': f'{SOUND_ID:04X}',
        'sound_adapter_ram': 0x80460000+SOUND, 'sound_adapter_hex': sound.hex(),
        'native_positional_sound_sha256': sha256(sound_native),
        'metadata_ram': '804672E0', 'metadata_sha256': sha256(metadata), 'price': 2990,
        'runtime_installed': True, 'enabled': gameplay, 'selectable': False,
        'saved_profile_included': gameplay, 'ordinary_gameplay_tested': False,
        'pending': ['ordinary acquisition/interaction and persistence', 'Punchy house integration']}
