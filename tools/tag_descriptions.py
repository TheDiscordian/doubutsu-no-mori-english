"""Guarded complete English inventory mail/quest descriptions."""
import re
import struct
from aflib import sha256, by_vrom, CODE_VROM, CODE_RAM
from gc_names import symbol_data
import inventory_english as inv
import inventory_menu_text as menu

DRAW_START, DRAW_END = 0x87FC, 0x8BB4
QUEST_RAM, QUEST_SIZE = 0x800BB4B0, 300
QUEST_HASH = '5634dbf8d2931f4fc194b7928700356b586fccc5e5c491120897fdbf01d06bcd'
IMPORTS = {'af_load_display_name': 0x80196044, 'af_tag_native_animal': 0x800ACD18,
           'af_tag_native_special': 0x800ACD74, 'af_tag_native_draw': 0x80090E98,
           'af_tag_description_resume': 0x80870164}
QUEST_CALLS = {0x64: ('af_tag_animal', 0x800ACD18), 0x74: ('af_tag_animal', 0x800ACD18),
               0xC0: ('af_tag_animal', 0x800ACD18), 0xF8: ('af_tag_special', 0x800ACD74),
               0x10C: ('af_tag_animal', 0x800ACD18)}
REFERENCE = {'str_omikuji': b'fortune', 'str_happy_room': b'the HRA', 'mother_str': b'home',
             'str_otodokemono': b'Delivery for', 'str_otegami': b'Letter to',
             'str_title1': b'from\xD3', 'str_title2': b"'s   ", 'str_title4': b'the\xD3 ',
             'l_museum_name_str': b'Museum  '}
SOURCES = [('fortune', 0x80878AC0, 4, b'fortune'), ('hra', 0x80878AC4, 7, b'the HRA'),
           ('delivery', 0x80878ACC, 6, b'Delivery for'), ('letter', 0x80878AD4, 4, b'Letter to'),
           ('recipient', 0x80878AD8, 4, b'to'), ('sender', 0x80878ADC, 4, b'from'),
           ('mother', 0x80879144, 2, b'home'), ('museum', 0x8010AE40, 6, b'Museum')]
APPROVED = {
    'bytes': 44384,
    'symbols': {'af_tag_animal': 43596, 'af_tag_description_draw': 44132,
                'af_tag_description_hook': 42976, 'af_tag_description_prepare': 43732,
                'af_tag_quest_names': 43012, 'af_tag_special': 43508},
    'code_sha256': '070a9cca30dbabb0c7925a20b0a25ae7c04f973308b36f84f45d52af1ccf84d6',
    'relocation_sha256': 'd2db49411e8c8ddd4bca5e1633ffcb142c0b97b199a9a6014e1655099e378901',
}


def source_hashes():
    return {p: sha256((inv.ROOT/p).read_bytes()) for p in
            ('overlays/tag/descriptions.c', 'overlays/tag/descriptions.s', 'overlays/tag/descriptions.ld')}


def references():
    inv.reference_labels()
    rel = (inv.ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (inv.ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    for name, expected in REFERENCE.items():
        if symbol_data(rel, symbols, name) != expected: raise ValueError('Changed GameCube description text')
    if sha256(symbol_data(rel, symbols, 'str_color')) != 'd1261bfda8519e3e18d11f023bf191345fc738e8c5c773c8f4fa2bbd96897a35':
        raise ValueError('Changed GameCube description colours')
    return {name: sha256(value) for name, value in REFERENCE.items()}


def quest_source(native):
    inv.native_sources(native)
    data = by_vrom(native)[CODE_VROM].extract(native)[QUEST_RAM-CODE_RAM:QUEST_RAM-CODE_RAM+QUEST_SIZE]
    if sha256(data) != QUEST_HASH: raise ValueError('Changed native quest name resolver')
    return data


def prefix_words(symbols):
    jump = lambda name: ((inv.RAM+symbols[name]) >> 2) & 0x3FFFFFF
    return {0x808700A0-inv.RAM: (0x24050006, 0x08000000 | jump('af_tag_description_hook')),
            0x808700A4-inv.RAM: (0x0C027070, 0),
            0x808784EC-inv.RAM: (0x0C21DEC3, 0x0C000000 | jump('af_tag_description_draw'))}


def patch_image(native, data, symbols):
    result = bytearray(data)
    for at, (old, new) in prefix_words(symbols).items():
        if struct.unpack_from('>I', result, at)[0] != old: raise ValueError('Changed description hook')
        struct.pack_into('>I', result, at, new)
    start = symbols['af_tag_quest_names']
    if data[start:start+QUEST_SIZE] != quest_source(native): raise ValueError('Changed quest clone')
    for offset, (name, before) in QUEST_CALLS.items():
        if struct.unpack_from('>I', result, start+offset)[0] != 0x0C000000 | (before >> 2) & 0x3FFFFFF:
            raise ValueError('Changed cloned quest name call')
        struct.pack_into('>I', result, start+offset, 0x0C000000 | ((inv.RAM+symbols[name]) >> 2) & 0x3FFFFFF)
    return bytes(result)


def restore_base(native, data, symbols):
    result = bytearray(data[:menu.SIZE])
    original = inv.native_sources(native)[0]
    result[DRAW_START:DRAW_END] = original[DRAW_START:DRAW_END]
    for at, (old, new) in prefix_words(symbols).items():
        if struct.unpack_from('>I', result, at)[0] != new: raise ValueError('Changed installed description hook')
        struct.pack_into('>I', result, at, old)
    return bytes(result)


def elf_inventory(text):
    result = []
    for line in text.splitlines():
        if 'R_MIPS_' not in line: continue
        match = re.fullmatch(r'\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_MIPS_(32|26|HI16|LO16)\s+([0-9a-fA-F]+)\s+(\S+)\s*', line)
        if not match: raise ValueError('Unsupported description relocation')
        result.append([int(match[1], 16)-inv.RAM, {'32': 2, '26': 4, 'HI16': 5, 'LO16': 6}[match[2]],
                       int(match[3], 16), match[4]])
    return result


def relocation_data(native, inventory, symbols, size):
    old = menu.relocation_data(native); count = struct.unpack_from('>I', old, 16)[0]
    rows = [r for (r,) in struct.iter_unpack('>I', old[20:20+count*4])
            if not DRAW_START <= (r & 0xFFFFFF) < DRAW_END]
    rows += [0x44000000 | (0x808700A0-inv.RAM)]
    # The redirected draw call already has its original R_MIPS_26 row.
    rows += [0x44000000 | (symbols['af_tag_quest_names']+at) for at in QUEST_CALLS]
    for at, kind, target, name in inventory:
        if at & 3 or not (DRAW_START <= at < DRAW_END or menu.SIZE <= at <= size-4):
            raise ValueError('Description relocation outside owned code')
        if inv.RAM <= target < inv.RAM+size:
            rows.append(0x40000000 | kind << 24 | at)
        elif IMPORTS.get(name) != target or kind != 4:
            raise ValueError('Unbound external description target')
    if len({r & 0xFFFFFF for r in rows}) != len(rows): raise ValueError('Duplicate description relocation')
    length = (24+len(rows)*4+15) & ~15
    return (struct.pack('>5I', size, 0, 0, 0, len(rows))+struct.pack('>'+str(len(rows))+'I', *rows)
            +bytes(length-24-len(rows)*4)+struct.pack('>I', length))


def make_report(native, data, reloc, symbols, inventory):
    base = restore_base(native, data, symbols)
    return {**inv.APPROVED, 'bytes': len(data), 'menu_text': True, 'descriptions': True,
            'sources': source_hashes(), 'description_symbols': symbols, 'imports': IMPORTS,
            'overlay_sha256': sha256(data), 'relocation_sha256': sha256(reloc),
            'description_code_sha256': sha256(data[DRAW_START:DRAW_END]+data[menu.SIZE:]),
            'elf_relocations': inventory, 'reference_sha256': references(), 'quest_sha256': QUEST_HASH,
            'menu_base': menu.make_report(native, base, menu.relocation_data(native))}


def validate(native, data, reloc, report, module):
    if not APPROVED: raise ValueError('Description image needs independent approval')
    symbols = APPROVED['symbols']
    if (len(data) != APPROVED['bytes'] or report.get('bytes') != len(data)
            or report.get('menu_text') is not True or report.get('symbols') != inv.APPROVED['symbols']
            or report.get('descriptions') is not True
            or report.get('description_symbols') != symbols or report.get('sources') != source_hashes()
            or report.get('imports') != IMPORTS or report.get('reference_sha256') != references()
            or report.get('quest_sha256') != QUEST_HASH
            or report.get('overlay_sha256') != sha256(data) or report.get('relocation_sha256') != sha256(reloc)
            or sha256(data[DRAW_START:DRAW_END]+data[menu.SIZE:]) != APPROVED['code_sha256']
            or sha256(reloc) != APPROVED['relocation_sha256']
            or (report.get('elf_relocations') is not None and
                reloc != relocation_data(native, report['elf_relocations'], symbols, len(data)))
            or int(module['symbols']['af_load_display_name'], 16) != IMPORTS['af_load_display_name']):
        raise ValueError('Changed complete English description profile')
    base = restore_base(native, data, symbols)
    menu.validate(native, base, menu.relocation_data(native), report['menu_base'], module)
    inv.allocation(len(data))
    return inv.Image(inv.RAM, len(data), struct.unpack_from('>5I', reloc))
