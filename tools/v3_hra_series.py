"""Grow native HRA theme storage without changing its unrolled scoring loops."""
from aflib import sha256, u32
from gc_names import symbol_data
from v3_furniture_art import verify_sources

COUNT = 59
INFO, NAMES, SEARCH = 0x809283B0, 0x80928458, 0x80929750
SOURCES = ('tools/v3_hra_series.py',)
# Three initial necessity rows precede a four-row loop; theme matching has
# one initial row then a two-row loop. 60 would overrun both termination values.
COUNTERS = {
    0x809259E4: 0x28A10037, 0x80926A3C: 0x24120037,
    0x80926E5C: 0x2A010037, 0x80926FD0: 0x240D0037,
    0x80927378: 0x240A0037, 0x80927800: 0x24040036,
    0x80927F18: 0x24130037,
}
POINTERS = {
    0x809259F8: NAMES,
    0x80926A2C: SEARCH, 0x80926A34: INFO,
    0x80926B64: INFO, 0x80926B9C: SEARCH,
    0x80926E6C: INFO, 0x80926E74: INFO+3,
    0x80926E80: INFO+1, 0x80926E90: INFO+2,
    0x80926ED0: INFO+55*3,
    0x80926FC4: SEARCH, 0x80926FC8: INFO,
    0x80927274: INFO, 0x80927288: SEARCH,
    0x809272CC: INFO+3, 0x809272DC: SEARCH+4,
    0x8092731C: INFO+6, 0x80927328: SEARCH+8,
    0x8092736C: SEARCH, 0x80927370: INFO+9,
    0x809277FC: SEARCH,
    0x80927A0C: INFO+1, 0x80927BA8: INFO+1,
    0x80927D44: INFO+1, 0x80927EE0: INFO+1,
    0x80927F10: INFO, 0x80927F94: SEARCH,
}


def prepare(base, rel, symbols):
    from v3_hra import RAM, sources
    native, _ = sources(base)
    verify_sources(rel, symbols)
    donor_info = symbol_data(rel, symbols.decode(), 'mMkRm_series_info')
    donor_names = symbol_data(rel, symbols.decode(), 'mMkRm_series_name')
    if (sha256(donor_info) != '5e8ff8c0d4041c76981c74ba62075d28249dc8d8e1d4cab9191315829738bd65'
            or sha256(donor_names) != '9d5b0d3d4faa60cc780462ef1ed8320bd14b3f01e22f09303ce513e4e41c6e42'
            or donor_info[58*3:59*3] != bytes.fromhex('020041')
            or donor_names[58*16:59*16] != b'boxing          '):
        raise ValueError('Changed donor HRA boxing definition')
    if COUNT != 59 or (COUNT-55) % 4:
        raise ValueError('Expanded series count breaks native unrolled loop termination')
    # Unimplemented donor series 55..57 cannot acquire an accidental native
    # floor/wall match. Boxing keeps its true theme type; its donor surfaces
    # are not installed, so FF explicitly means no matching native surface.
    info = native[INFO-RAM:INFO-RAM+55*3] + bytes.fromhex('FF00FF')*3 + bytes.fromhex('0200FF')
    names = native[NAMES-RAM:NAMES-RAM+55*10] + b' '*30 + b'boxing    '
    return {'af_v3_hra_series_info': info, 'af_v3_hra_series_names': names,
            'af_v3_hra_series_search': bytes(COUNT*4)}


def assembly(resources):
    result = '.section .rodata.hra_series\n'
    for name, data in resources.items():
        result += f'.balign 4\n.globl {name}\n{name}:\n'
        result += ''.join('.byte '+','.join(str(v) for v in data[i:i+16])+'\n'
                          for i in range(0, len(data), 16))
    return result


def replacement(target, symbols):
    for start, width, symbol in ((INFO, 3, 'af_v3_hra_series_info'),
                                 (NAMES, 10, 'af_v3_hra_series_names'),
                                 (SEARCH, 4, 'af_v3_hra_series_search')):
        if start <= target < start+55*width:
            return symbols[symbol]+target-start
    if target == INFO+55*3:
        return symbols['af_v3_hra_series_info']+COUNT*3
    return None


def install(old, data, symbols, resources, pointers, word):
    from v3_hra import RAM, SECTIONS, START
    if {p['low']: p['before'] for p in pointers} != POINTERS:
        raise ValueError('Changed complete native series-reference inventory')
    found = {RAM+at: u32(old, at) for at in range(0, SECTIONS[0], 4)
             if u32(old, at) >> 26 in (9, 10, 11, 12, 13)
             and u32(old, at) & 65535 in (54, 55)}
    if found != COUNTERS:
        raise ValueError('Changed complete HRA series-count inventory')
    for address, before in COUNTERS.items():
        word(address, before, before & 0xFFFF0000 | (COUNT-1 if address == 0x80927800 else COUNT))
    for name, payload in resources.items():
        at = symbols[name]-RAM
        if at < START or at & 3 or data[at:at+len(payload)] != payload:
            raise ValueError('Linked series resource differs or escapes appended storage')
    return {'count': COUNT, 'info_address': symbols['af_v3_hra_series_info'],
            'names_address': symbols['af_v3_hra_series_names'],
            'search_address': symbols['af_v3_hra_series_search'],
            'resource_bytes': sum(map(len, resources.values())),
            'resource_sha256': {name: sha256(value) for name, value in resources.items()},
            'pointer_changes': pointers, 'counter_sites': list(COUNTERS),
            'boxing': {'series': 58, 'type': 2, 'name': 'boxing',
                       'donor_wall_floor_index': 65, 'native_wall_floor_index': 255,
                       'matching_surfaces_installed': False, 'score_letter_name_installed': False},
            'native_scoring_tested': False}
