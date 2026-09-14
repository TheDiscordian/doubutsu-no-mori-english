"""Apply selected donor feng shui colours to the original N64 evaluator."""
import struct

from aflib import CODE_RAM, by_vrom, sha256, u32
from catalogue_names import Image, elf_inventory
from gc_names import rel_sections, symbol_data
from npc_mail_show import relocate_verified_data
from v3_furniture_art import verify_sources
from v3_furniture_room import assembly as room_assembly

ABI = 20
VROM, RELOC, RAM = 0x827DE0, 0x828C00, 0x80930960
NEW_VROM, NEW_RELOC = 0x03F50000, 0x03F54000
SIZE, COUNT, TABLE = 3616, 1267, 0x80930FA0
SECTIONS = (1600, 1920, 96, 0, 12)
SOURCE_SHA = '783bfaf1bf8fa58872ae2c3f9f55e686482f5434c2f42c49e3562de9ee284c47'
RELOC_SHA = '326ba552f9fb152e9c0e174c5ed0f03d9b5f4adf40941e340209f05ee90f06dd'
DONOR_SHA = '5700370581b13dd85eb1102656f858c9c4dbb4752c646c3ad563893937a2517a'
SOURCES = ('tools/v3_feng_shui.py', 'overlays/v3/feng_shui.ld')
ROWS = [
    {'kind': 'range', 'start': 0x80930D90, 'end': 0x80930DA0, 'upper': 0x80930D98,
     'source': 4, 'upper_word': 0x28811ECD, 'branch': 0x1020000A, 'delay': 0x02002825,
     'paired': True, 'lower_word': 0x28811000, 'lower_target': 0x80930DC8,
     'taken': 0x80930DC8, 'fall': 0x80930DA0, 'symbol': 'af_v3_feng_range'},
    {'kind': 'transform', 'start': 0x80930990, 'end': 0x80930998, 'source': 4,
     'destination': 11, 'mode': 1, 'after': 0x000B7083, 'symbol': 'af_v3_feng_index'}]


def sources(base):
    files = by_vrom(base)
    data, reloc = (files[v].extract(base) for v in (VROM, RELOC))
    if (sha256(data) != SOURCE_SHA or sha256(reloc) != RELOC_SHA
            or struct.unpack_from('>5I', reloc) != SECTIONS):
        raise ValueError('Changed complete native feng shui source')
    return data, reloc


def table(base, rel, symbols, furniture, display=None):
    data, _ = sources(base)
    verify_sources(rel, symbols)
    source = symbols.decode()
    lines = [line for line in source.splitlines() if line.startswith('mMkRm_ftr_info =')]
    if len(lines) != 2 or not any('.data:0x0004EBF0;' in line and 'size:0x9E4' in line for line in lines):
        raise ValueError('Changed disambiguated donor feng shui symbol')
    start = rel_sections(rel)[5][0] + 0x4EBF0
    donor = rel[start:start + 1266 * 2]
    if sha256(donor) != DONOR_SHA:
        raise ValueError('Changed complete donor feng shui table')
    for address, name in ((0x80931720, 'money_power_tbl'), (0x80931750, 'goods_power_tbl')):
        native_rules = list(struct.iter_unpack('>ii', data[address - RAM:address - RAM + 48]))
        donor_rules = list(struct.iter_unpack('>ii', symbol_data(rel, source, name)))
        scale = 4 if name == 'goods_power_tbl' else 1
        if donor_rules != [(direction, points * scale) for direction, points in native_rules]:
            raise ValueError('Unreviewed donor feng shui type/point relationship')
        # GC multiplies item-luck weights by four. Keep N64 game balance and
        # its final room clamp/rounding rather than importing those point values.
    from v3_furniture_tables import CAPACITY
    count = CAPACITY if display is not None else COUNT
    output = bytearray(data[TABLE - RAM:TABLE - RAM + 947 * 2] + bytes((count - 947) * 2))
    records, seen = [], set()
    for row in furniture:
        item, index = int(row['item_id'], 16), row['runtime_index']
        if (item, index) not in ((0x3224, 1161), (0x32B8, 1198)) or index in seen:
            raise ValueError('Unreviewed or duplicate feng shui import')
        seen.add(index)
        metadata = donor[index * 2:index * 2 + 2]
        if metadata != bytes((2 if item == 0x3224 else 3, 0)):
            raise ValueError('Changed pilot colour or facing penalty')
        output[index * 2:index * 2 + 2] = metadata
        records.append({'item_id': f'{item:04X}', 'runtime_index': index,
                        'metadata': metadata.hex(), 'colour': 'red' if item == 0x3224 else 'orange'})
    if display is not None:
        from v3_display_items import scoring_identity
        donor_index = scoring_identity(rel, symbols, display)
        metadata = donor[donor_index*2:donor_index*2+2]
        if metadata != bytes(2):
            raise ValueError('Changed imported clothing feng shui properties')
        index = display['runtime_index']
        output[index*2:index*2+2] = metadata
        records.append({**display, 'donor_runtime_index': donor_index,
                        'metadata': metadata.hex(), 'colour': 'none'})
    return bytes(output), records


def assembly():
    def resume(address):
        if not RAM <= address < RAM + SECTIONS[0]:
            raise ValueError('Feng shui continuation escapes native text')
        return ['addiu $sp, $sp, -16', 'sd $ra, 8($sp)', 'lui $ra, 0x8010',
                'lw $ra, 0x7010($ra)', f'addiu $ra, $ra, {address - RAM}',
                'addiu $sp, $sp, 16', 'jr $ra', 'ld $ra, -8($sp)']
    return room_assembly(ROWS, return_builder=resume)


def install(base, code, suffix, compiled, metadata, records):
    old, reloc = sources(base)
    symbols = compiled['symbols']
    if (len(metadata) not in (COUNT*2, 2051*2)
            or len(suffix) != compiled['bytes'] or not 0 < len(suffix) <= 0x2000 - SIZE
            or len(suffix) % 16 or symbols['af_v3_room_query'] != 0x804680B8):
        raise ValueError('Changed compiled feng shui image or dependency')
    data = bytearray(old + suffix)
    table_address = symbols['af_v3_feng_table']
    at = table_address - RAM
    if not SIZE <= at <= len(data) - len(metadata) or data[at:at + len(metadata)] != metadata:
        raise ValueError('Changed linked feng shui metadata')
    slots = [(sum(SECTIONS[:(w >> 30) - 1]) + (w & 0xFFFFFF), w >> 24 & 63)
             for (w,) in struct.iter_unpack('>I', reloc[20:20 + SECTIONS[4] * 4])]
    patches = []
    def word(address, before, after):
        if u32(data, address - RAM) != before:
            raise ValueError('Changed native feng shui instruction contract')
        struct.pack_into('>I', data, address - RAM, after)
        patches.append({'address': address, 'before': before, 'after': after})
    if ([RAM + at for at in range(0, SECTIONS[0], 4) if u32(old, at) & 0xFC1FFFFF == 0x28011ECD]
            != [0x80930D98] or struct.unpack_from('>5I', old, 0x430)
            != (0x28811000, 0x1420000C, 0x28811ECD, 0x1020000A, 0x02002825)
            or struct.unpack_from('>2I', old, 0x30) != (0x248BF000, 0x000B7083)):
        raise ValueError('Changed complete feng shui range/index inventory')
    for row in ROWS:
        if any(row['start'] - RAM <= pos < row['end'] - RAM for pos, _ in slots):
            raise ValueError('Feng shui hook displaces a relocation')
        for address in range(row['start'], row['end'], 4):
            target = symbols[row['symbol']]
            if not RAM + SIZE <= target < table_address:
                raise ValueError('Feng shui hook escapes compiled text')
            word(address, u32(old, address - RAM),
                 0x08000000 | (target >> 2 & 0x3FFFFFF) if address == row['start'] else 0)
        slots.append((row['start'] - RAM, 4))
    word(0x80930998, 0x3C188093, 0x3C180000 | (table_address + 0x8000) >> 16)
    word(0x809309A0, 0x27180FA0, 0x27180000 | table_address & 65535)
    for pos, kind, target, name in elf_inventory(compiled['elf_relocations'], ram=RAM):
        if not SIZE <= pos <= len(data) - 4 or pos & 3:
            raise ValueError('Feng shui suffix relocation escapes image')
        if RAM <= target < RAM + len(data):
            slots.append((pos, kind))
        elif (name, target, kind) != ('af_v3_room_query', 0x804680B8, 4):
            raise ValueError('Unbound feng shui suffix target')
    if len({at for at, _ in slots}) != len(slots):
        raise ValueError('Duplicate feng shui relocation')
    size = (24 + len(slots) * 4 + 15) & ~15
    new_rel = (struct.pack('>5I', len(data), 0, 0, 0, len(slots))
        + struct.pack('>' + str(len(slots)) + 'I', *(0x40000000 | kind << 24 | pos for pos, kind in slots))
        + bytes(size - 24 - len(slots) * 4) + struct.pack('>I', size))
    allowed = {i for p in patches for i in range(p['address'] - RAM, p['address'] - RAM + 4)}
    for loaded in (0x801A0010, 0x802F8010, 0x803D0010):
        before = relocate_verified_data(Image(RAM, SIZE, SECTIONS), old, reloc, loaded)
        after = relocate_verified_data(Image(RAM, len(data), (len(data), 0, 0, 0, len(slots))), bytes(data), new_rel, loaded)
        if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(before, after))):
            raise ValueError('Feng shui adapter changes unrelated relocated data/code')
    scheduler = []
    for high, low, reg, before, after in (
            (0x80092C58, 0x80092C60, 15, RAM + SIZE, RAM + len(data)),
            (0x80092C98, 0x80092C9C, 7, RAM + SIZE, RAM + len(data)),
            (0x80092C8C, 0x80092CA8, 4, VROM, NEW_VROM),
            (0x80092C90, 0x80092CA4, 5, VROM + SIZE, NEW_VROM + len(data))):
        for address, first, second in (
                (high, 0x3C000000 | reg << 16 | (before + 0x8000) >> 16,
                 0x3C000000 | reg << 16 | (after + 0x8000) >> 16),
                (low, 0x24000000 | reg << 21 | reg << 16 | before & 65535,
                 0x24000000 | reg << 21 | reg << 16 | after & 65535)):
            if u32(code, address - CODE_RAM) != first:
                raise ValueError('Changed native feng shui scheduler')
            struct.pack_into('>I', code, address - CODE_RAM, second)
            scheduler.append({'address': address, 'before': first, 'after': second})
    return {VROM: bytes(data), RELOC: new_rel}, {'imports': records,
        'source_sha256': SOURCE_SHA, 'source_relocation_sha256': RELOC_SHA,
        'donor_metadata_sha256': DONOR_SHA, 'metadata_sha256': sha256(metadata),
        'metadata_address': table_address, 'metadata_rows': len(metadata)//2,
        'bytes': len(data), 'relocation_bytes': size,
        'on_demand_growth': len(suffix), 'output_sha256': sha256(data),
        'relocation_sha256': sha256(new_rel), 'patches': patches, 'scheduler': scheduler,
        'sites': ROWS, 'donor_goods_weight_multiple': 4, 'native_point_rules_retained': True,
        'save_format_changed': False, 'ordinary_house_evaluation_tested': False}
