"""Original event selection/publication contracts for the English adapter."""

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from leaflet_dates import ACTORS, source

FUNCTIONS = {
    'register': (0x8095B9CC, 0x8095BA60, 'c0c07eda3b76f7e4d58a26344aef64c4dbbeff2c36b6290068b79586fdb09dc1'),
    'sale_fields': (0x8095BA60, 0x8095BB80, '975d0ff45a94852b0585b5ee29df42ffd6a1d12ddd11736929d08f10c3f195b3'),
    'redd_fields': (0x8095BB80, 0x8095BBFC, '75f9c69878ab440c18029edee6a9dfb17e6e1790d21bcd905f4afd0f3204f173'),
    'redd_selection': (0x8095BBFC, 0x8095BC60, '0b5b3dc7bc5254053c7aab55353e9d24f0090faa0bc908300c470ec93c74127c'),
    'sale_init': (0x8095BDE8, 0x8095C09C, '5781351d3c2d0a114b48f78e351592402186e11145fa5975b843004e5fed3ab7'),
    'redd_init': (0x8095C09C, 0x8095C264, '535e47fa896d5dfba8972b1857cbfb2e96d2cfdfb808c944ac4377ccc878d0f8'),
    'special_init': (0x8095C37C, 0x8095C4A8, '2f745ea68f54f0db6e120e7394746ee77a7701a066ac270efa630732a540e7b4'),
}
HELPERS = (
    (0x8009C384, 0x8009C3D0, '1d2ff0e947ac76c27913e319506be74da4cab34b6cee4db2703662a45ff758e1'),
    (0x800B6A3C, 0x800B6AC8, '032319ed0866342abee88c99f07298dfe958ad6e3fb83fae8e20da2b70b2ae70'),
)


def evidence(rom):
    rom = verified_rom(rom)
    data, reloc = source(rom, 'event')
    ram = ACTORS['event'].ram
    for name, (start, end, expected) in FUNCTIONS.items():
        if sha256(data[start-ram:end-ram]) != expected:
            raise ValueError('Changed native event leaflet function: '+name)
    code = by_vrom(rom)[CODE_VROM].extract(rom)
    for start, end, expected in HELPERS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM]) != expected:
            raise ValueError('Changed event receipt or clear helper')
    return {'functions': FUNCTIONS, 'helpers': HELPERS,
            'event_save': '80135C44', 'event_save_bytes': 156,
            'sale_time_offset': 12, 'redd_time_offset': 0, 'selected_items_offset': 28,
            'saved_letter': '801361E4', 'receipt_flags': '8013628A', 'receipt_flag_bytes': 2,
            'receipt_mode': 2, 'receipt_success': 1,
            'native_parent_discards_child_return_at': '8095C494',
            'native_actor_bytes': len(data), 'native_bss_bytes': ACTORS['event'].sections[3],
            'native_relocation_sha256': sha256(reloc),
            'owner_hook_installed': False, 'pending_lifetime_resolved': False}
