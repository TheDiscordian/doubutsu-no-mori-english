"""Add imported catalogue rows and native previews without reusing native IDs."""
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from catalogue_names import Image, elf_inventory
from gc_names import symbol_data
from npc_mail_show import relocate_verified_data
from v3_furniture_art import verify_sources

VROM, RELOC, RAM, SIZE = 0x03970000, 0x03980000, 0x808A6100, 53680
PARENT, OWNER, TABLE = 0x7749C0, 0x2C90, 0x808AEB84
SOURCE_SHA = '081a4ff212d3fa57cdefc0f34ff710616d09877d95f8c163dc878a097e1ee1d8'
RELOC_SHA = 'a6e62af7ac0c66458f06043995289f3b10a7405dc9e1bcc17729fc6672612a13'
PARENT_SHA = '3812a0538eead12ea59bc1826e8df7c6bd02e8575e0a3a36dfec31f717d262d3'
SOURCES = ('tools/v3_catalogue.py', 'overlays/v3/catalogue.c',
           'overlays/v3/catalogue_bridge.S', 'overlays/v3/catalogue.ld')
POINTERS = ((0x808A943C, 0x808A9450, 16), (0x808A6594, 0x808A65F4, 2))
AVAILABLE = (0x808A667C, 0x808A6698, 0x808A66B0, 0x808A66C8, 0x808A66E0, 0x808A66F8)
IMPORTS = {'af_v3_native_catalogue_bit': 0x808A931C,
           'af_v3_catalogue_program_continue': 0x808A6150,
           'af_v3_catalogue_type_continue': 0x808A6B1C,
           'af_v3_room_query': 0x804680B8,
           'af_v3_native_catalogue_available': 0x800C0490,
           'af_v3_catalogue_owned': 0x80469AD4,
           'af_v3_furniture_import_profile': 0x80465000,
           'af_v3_save_halt': 0x80469270}


def sources(base):
    files = by_vrom(base)
    data, reloc, parent = [files[v].extract(base) for v in (VROM, RELOC, PARENT)]
    if (len(data) != SIZE or sha256(data) != SOURCE_SHA or sha256(reloc) != RELOC_SHA
            or sha256(parent) != PARENT_SHA or struct.unpack_from('>5I', reloc) != (SIZE, 0, 0, 0, 152)
            or struct.unpack_from('>8I', parent, OWNER) !=
            (VROM, VROM + SIZE, RAM, RAM + SIZE, 0x808A96AC, 0x808A97C0, 0x808A92EC, 0)):
        raise ValueError('Changed complete V2 catalogue, relocation, or parent')
    return data, reloc, parent


def table(base, rel, donor_symbols, furniture):
    data, _, _ = sources(base)
    verify_sources(rel, donor_symbols)
    symbol_text = donor_symbols.decode()
    donor = symbol_data(rel, symbol_text, 'mCL_furniture_list')
    draw = symbol_data(rel, symbol_text, 'furniture_draw_data$436')
    if sha256(donor) != '91bad7d2198f5da32b464547c3a3c15df9cc77e1969ad7eebc7c0fa45f66956f':
        raise ValueError('Changed donor catalogue ordering')
    native = data[TABLE - RAM:TABLE - RAM + 436 * 4]
    rows = list(struct.iter_unpack('>HH', native))
    if len({i for i, _ in rows}) != 436 or any(i >= 947 for i, _ in rows):
        raise ValueError('Invalid original catalogue index set')
    records = []
    for row in furniture:
        item, index = int(row['item_id'], 16), row['runtime_index']
        if (item, index) not in ((0x3224, 1161), (0x32B8, 1198)):
            raise ValueError('New catalogue import needs reviewed preview and shop rules')
        found = [(n, mode) for n, (i, mode) in enumerate(struct.iter_unpack('>HH', donor)) if i == index]
        if len(found) != 1 or found[0][1] != 0 or draw[:8] != data[0x808AF87C - RAM:0x808AF87C - RAM + 8]:
            raise ValueError('Donor catalogue preview mode is not the verified native mode')
        group = 'ftr_listC' if item == 0x3224 else 'ftr_listA'
        goods = symbol_data(rel, symbol_text, group)
        ids = struct.unpack('>' + str(len(goods) // 2) + 'H', goods)
        if ids[-1] != 0 or ids.count(item) != 1 or 0 in ids[:-1]:
            raise ValueError('Donor item lacks verified ordinary-shop list membership')
        records.append({'item_id': f'{item:04X}', 'runtime_index': index,
            'catalogue_index': (item - 0x1000) >> 2, 'donor_position': found[0][0], 'mode': 0,
            'ordinary_shop_list': group, 'shop_list_sha256': sha256(goods)})
    records.sort(key=lambda row: row['donor_position'])
    if len({row['item_id'] for row in records}) != len(records) or len(rows) + len(records) > 444:
        raise ValueError('Catalogue duplicates or exceeds the actual native item capacity')
    rows += [(row['catalogue_index'], row['mode']) for row in records]
    return b''.join(struct.pack('>HH', *row) for row in rows), records


def install(base, parent, suffix, compiled, ordering, records, collection, runtime, room):
    old, reloc, source_parent = sources(base)
    symbols = compiled['symbols']
    if (len(suffix) != compiled['bytes'] or not suffix or len(suffix) > 0xB50 or len(suffix) % 16
            or collection['symbols']['af_v3_catalogue_owned'] != IMPORTS['af_v3_catalogue_owned']
            or runtime['symbols']['af_v3_save_halt'] != IMPORTS['af_v3_save_halt']
            or room['symbols']['af_v3_room_query'] != IMPORTS['af_v3_room_query']
            or any(symbols[name] != value for name, value in IMPORTS.items())
            or parent[OWNER:OWNER + 32] != source_parent[OWNER:OWNER + 32]):
        raise ValueError('Changed catalogue helper dependencies or parent descriptor')
    data = bytearray(old + suffix)
    count = 436 + len(records)
    table_address = symbols['af_v3_catalogue_order']
    table_at = table_address - RAM
    if (not SIZE <= table_at <= len(data) - len(ordering) or data[table_at:table_at + len(ordering)] != ordering
            or len(ordering) != count * 4):
        raise ValueError('Linked complete catalogue table differs from donor conversion')
    rows = list(struct.unpack_from('>152I', reloc, 20))
    slots = {row & 0xFFFFFF: row >> 24 & 63 for row in rows}
    patches = []

    def word(address, before, after):
        at = address - RAM
        if u32(data, at) != before:
            raise ValueError(f'Changed catalogue instruction/data window {address:08X}')
        struct.pack_into('>I', data, at, after)
        patches.append({'address': address, 'before': before, 'after': after})

    def jump(target, call=True):
        return (0x0C000000 if call else 0x08000000) | (target >> 2 & 0x3FFFFFF)

    for address, name, original, kind in ((0x808A9470, 'af_v3_catalogue_bit', 0x808A931C, 4),
            *((address, 'af_v3_catalogue_available', 0x800C0490, None) for address in AVAILABLE)):
        if slots.get(address - RAM) != kind:
            raise ValueError('Changed catalogue call relocation')
        word(address, jump(original), jump(symbols[name]))
        if kind is None:
            rows.append(0x44000000 | (address - RAM))
    if slots.get(0x48) is not None or u32(old, 0x4C) != 0xAFB00020:
        raise ValueError('Changed catalogue program-loader entry')
    word(0x808A6148, 0x27BDFFD0, jump(symbols['af_v3_catalogue_program'], False))
    word(0x808A614C, 0xAFB00020, 0)
    rows.append(0x44000048)
    if slots.get(0xA14) is not None or slots.get(0xA18) is not None:
        raise ValueError('Changed catalogue selection type relocations')
    word(0x808A6B14, 0x3223F000, jump(symbols['af_v3_catalogue_type'], False))
    word(0x808A6B18, 0x00031B03, 0)
    rows.append(0x44000A14)
    for hi, lo, register in POINTERS:
        if slots.get(hi - RAM) != 5 or slots.get(lo - RAM) != 6:
            raise ValueError('Changed catalogue table pointer relocations')
        word(hi, 0x3C000000 | register << 16 | ((TABLE + 0x8000) >> 16),
             0x3C000000 | register << 16 | ((table_address + 0x8000) >> 16))
        word(lo, 0x24000000 | register << 21 | register << 16 | (TABLE & 65535),
             0x24000000 | register << 21 | register << 16 | (table_address & 65535))
    word(0x808A6600, 0x240501B4, 0x24050000 | count)
    word(0x808A9460, 0x241401B4, 0x24140000 | count)
    word(0x808AF7A8, 436, count)
    inventory = elf_inventory(compiled['elf_relocations'], ram=RAM)
    for at, kind, target, name in inventory:
        if not SIZE <= at <= len(data) - 4 or at & 3:
            raise ValueError('Catalogue suffix relocation escapes appended code')
        if RAM <= target < RAM + len(data):
            rows.append(0x40000000 | kind << 24 | at)
        elif IMPORTS.get(name) != target or kind != 4:
            raise ValueError('Unbound catalogue external target')
    if len({row & 0xFFFFFF for row in rows}) != len(rows):
        raise ValueError('Duplicate catalogue relocation')
    size = (24 + len(rows) * 4 + 15) & ~15
    new_rel = (struct.pack('>5I', len(data), 0, 0, 0, len(rows))
        + struct.pack('>' + str(len(rows)) + 'I', *rows)
        + bytes(size - 24 - len(rows) * 4) + struct.pack('>I', size))
    changed_parent = bytearray(parent)
    struct.pack_into('>I', changed_parent, OWNER + 4, VROM + len(data))
    struct.pack_into('>I', changed_parent, OWNER + 12, RAM + len(data))
    align = lambda value: (value + 63) & ~63
    growth, relocation_growth = align(len(data)) - align(SIZE), align(len(new_rel)) - align(len(reloc))
    required, reserved = 253696 + 0x4400 + 64 + growth + relocation_growth, 257152 + 0x4400
    code = by_vrom(base)[CODE_VROM].extract(base)
    if (required > reserved or u32(code, 0x800C4AFC - CODE_RAM) != 0x3C0E8089
            or u32(code, 0x800C4B10 - CODE_RAM) != 0x25CE7620):
        raise ValueError('Extended catalogue exceeds the actual shared menu reservation')
    allowed = {i for p in patches for i in range(p['address'] - RAM, p['address'] - RAM + 4)}
    for address in (0x801A0010, 0x802F8010, 0x803D0010):
        before = relocate_verified_data(Image(RAM, SIZE, (SIZE, 0, 0, 0, 152)), old, reloc, address)
        after = relocate_verified_data(Image(RAM, len(data), (len(data), 0, 0, 0, len(rows))), bytes(data), new_rel, address)
        if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(before, after))):
            raise ValueError('Catalogue change alters an unrelated relocated word')
    return {VROM: bytes(data), RELOC: new_rel, PARENT: bytes(changed_parent)}, {
        'imports': records, 'native_rows': 436, 'total_rows': count, 'row_capacity': 444,
        'catalogue_index_encoding': '(item - 0x1000) >> 2; separate from room runtime indices',
        'source_sha256': SOURCE_SHA, 'relocation_source_sha256': RELOC_SHA,
        'output_sha256': sha256(data), 'relocation_sha256': sha256(new_rel),
        'bytes': len(data), 'relocation_bytes': len(new_rel), 'patches': patches,
        'rounded_growth': growth, 'rounded_relocation_growth': relocation_growth,
        'conservative_pool_required': required, 'pool_reserved': reserved,
        'additional_pool_allocation': 0, 'save_format_changed': False,
        'native_preview_tested': False, 'ordinary_order_delivery_tested': False}
