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
           'af_v3_catalogue_furniture_continue': 0x808A6284,
           'af_v3_catalogue_type_continue': 0x808A6B1C,
           'af_v3_room_query': 0x804680B8,
           'af_v3_native_catalogue_available': 0x800C0490,
           'af_v3_catalogue_owned': 0x80469AD4,
           'af_v3_furniture_import_profile': 0x80465000,
           'af_v3_save_halt': 0x80469270}
PREVIEW_TABLE, PREVIEW_FIRST, PREVIEW_END = 0x80474A40, 0x80474A30, 0x80474BA0
PREVIEW_COUNT = 41
PREVIEW_SHA = 'fa6592f8af1ebb2ddb984e59b39649c36afeb85bdd4f9127dbcae26ba62a2a98'
PREVIEW_GUARD = bytes.fromhex('AFF9C0DE')*4


def install_preview_records(blob, prior, source, records):
    """Bind every imported preview to the donor's common framing table."""
    from v3_import_storage import PACKAGE, PACKAGE_RAM, ITEMS, slot
    from v3_furniture_placement import END as PLACEMENT_END
    draw=source.raw('furniture_draw_data$436')
    begin,end=(PACKAGE+a-PACKAGE_RAM for a in (PREVIEW_FIRST,PREVIEW_END))
    at=PACKAGE+PREVIEW_TABLE-PACKAGE_RAM
    if (len(draw)!=PREVIEW_COUNT*8 or sha256(draw)!=PREVIEW_SHA or
            not PLACEMENT_END<=PREVIEW_FIRST<PREVIEW_TABLE<PREVIEW_END<=0x80475000 or
            at+len(draw)>end-16):
        raise ValueError('Preview table overlaps placement data or accessory artwork')
    previous=prior.get('catalogue_preview_records')
    if previous:
        if (previous['table_ram']!=PREVIEW_TABLE or previous['count']!=PREVIEW_COUNT or
                sha256(blob[begin:end])!=previous['reservation_sha256']):
            raise ValueError('Changed installed catalogue preview table')
    elif any(blob[begin:end]):
        raise ValueError('Catalogue preview reservation is occupied')
    ordering=list(struct.iter_unpack('>HH',source.raw('mCL_furniture_list')))
    previous_modes={r['item_id']:r['mode']+1 for r in previous['imports']} if previous else {}
    rows=[]; seen=set()
    for record in records:
        item=int(record['item_id'],16); index=1024+slot(item)
        found=[(p,m) for p,(i,m) in enumerate(ordering) if i==index]
        if len(found)!=1 or found[0][0]!=record['donor_position'] or item in seen:
            raise ValueError('Ambiguous catalogue preview identity')
        seen.add(item);mode=found[0][1]
        if not 0<=mode<PREVIEW_COUNT: raise ValueError('Catalogue preview mode exceeds donor table')
        scalar=draw[mode*8:mode*8+8]
        if (mode!=record.get('donor_preview_mode',0) or
                record.get('donor_preview_scalar_hex',scalar.hex())!=scalar.hex()):
            raise ValueError('Catalogue preview record differs from actual donor')
        pos=ITEMS+slot(item)*32
        if blob[pos+26]!=previous_modes.get(record['item_id'],0) or any(blob[pos+27:pos+32]):
            raise ValueError('Preview selector overwrites reserved item metadata')
        blob[pos+26]=mode+1
        record.update(donor_preview_mode=mode,donor_preview_scalar_hex=scalar.hex(),
            preview_override=mode!=0,preview_define='AF_V3_CATALOGUE_PREVIEW_RECORDS',
            preview_mapping='native construction; source-indexed final scale/Y')
        rows.append(dict(item_id=record['item_id'],runtime_index=index,mode=mode,scalar_hex=scalar.hex()))
    blob[begin:end]=bytes(end-begin)
    blob[begin:begin+16]=PREVIEW_GUARD;blob[end-16:end]=PREVIEW_GUARD
    blob[at:at+len(draw)]=draw
    rows.sort(key=lambda r:r['runtime_index'])
    return dict(table_ram=PREVIEW_TABLE,count=PREVIEW_COUNT,table_sha256=sha256(draw),
        reservation_start=PREVIEW_FIRST,reservation_end=PREVIEW_END,
        reservation_sha256=sha256(blob[begin:end]),selector_byte=26,imports=rows)


def sources(base):
    files = by_vrom(base)
    data, reloc, parent = [files[v].extract(base) for v in (VROM, RELOC, PARENT)]
    if (len(data) != SIZE or sha256(data) != SOURCE_SHA or sha256(reloc) != RELOC_SHA
            or sha256(parent) != PARENT_SHA or struct.unpack_from('>5I', reloc) != (SIZE, 0, 0, 0, 152)
            or struct.unpack_from('>8I', parent, OWNER) !=
            (VROM, VROM + SIZE, RAM, RAM + SIZE, 0x808A96AC, 0x808A97C0, 0x808A92EC, 0)):
        raise ValueError('Changed complete V2 catalogue, relocation, or parent')
    return data, reloc, parent


def table_from_records(base, rel, symbols, furniture, records):
    """Consume source-checked import records without another item-family switch."""
    from v3_catalogue_capacity import CAPACITY
    verify_sources(rel, symbols)
    data, _, _ = sources(base)
    donor = list(struct.iter_unpack('>HH', symbol_data(rel, symbols.decode(), 'mCL_furniture_list')))
    draw = symbol_data(rel, symbols.decode(), 'furniture_draw_data$436')
    if draw[:8] != data[0x808AF87C-RAM:0x808AF884-RAM]:
        raise ValueError('Changed default catalogue framing')
    identities = {r['item_id']: r['runtime_index'] for r in furniture}
    if (len(identities) != len(furniture) or len(records) != len(identities)
            or {r['item_id'] for r in records} != set(identities)):
        raise ValueError('Incomplete or duplicate catalogue records')
    result = []
    for record in records:
        row = dict(record)
        item, index = int(row['item_id'], 16), identities[row['item_id']]
        mode = row.get('donor_preview_mode', 0)
        found = [(n,m) for n,(i,m) in enumerate(donor) if i == index]
        group = row.get('donor_acquisition_list') or row['ordinary_shop_list']
        goods = symbol_data(rel, symbols.decode(), group)
        ids = list(struct.unpack('>'+str(len(goods)//2)+'H', goods))
        if (index != 1024+(item-0x3000)//4 or row['runtime_index'] != index
                or row['catalogue_index'] != (item-0x1000)//4 or row['mode'] != 0
                or found != [(row['donor_position'], mode)] or ids[-1] or 0 in ids[:-1]
                or ids.count(item) != 1 or sha256(goods) != row['shop_list_sha256']
                or mode and (not row.get('preview_override') or
                    draw[mode*8:mode*8+8].hex() != row.get('donor_preview_scalar_hex'))):
            raise ValueError('Catalogue record differs from the checked donor')
        result.append(row)
    result.sort(key=lambda r:r['donor_position'])
    if 436+len(result) > CAPACITY: raise ValueError('Catalogue exceeds native storage')
    native = data[TABLE-RAM:TABLE-RAM+436*4]
    return native+b''.join(struct.pack('>HH', r['catalogue_index'], r['mode']) for r in result), result


def table(base, rel, donor_symbols, furniture, *, expanded=False, garden=False, western=False,
          western_large=False, camping=False, tent_model=False, fire=False, school_desks=False,
          reviewed_rows=None):
    if reviewed_rows is not None:
        if not expanded: raise ValueError('Record-driven catalogue requires expanded pages')
        return table_from_records(base, rel, donor_symbols, furniture, reviewed_rows)
    from v3_construction_items import STOCK
    from v3_catalogue_capacity import CAPACITY
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
    garden_rows = {}
    if garden:
        from v3_garden_items import metadata
        if not expanded:
            raise ValueError('Garden catalogue needs expanded native pages')
        garden_rows = {int(r['item_id'], 16): r for r in metadata(rel, donor_symbols)[1]}
    if western:
        from v3_western_items import metadata
        if not expanded:
            raise ValueError('Western furniture requires expanded catalogue pages')
        garden_rows.update({int(r['item_id'], 16): r for r in metadata(rel, donor_symbols)[1]})
    large_rows = {}
    if western_large:
        from v3_western_items import metadata
        if not expanded or not western:
            raise ValueError('Large Western catalogue requires the Western integration')
        large_rows = {int(r['item_id'], 16): r for r in metadata(rel, donor_symbols, large=True)[1]}
        garden_rows.update(large_rows)
    if camping:
        from v3_camping_items import metadata
        if not expanded:
            raise ValueError('Camping catalogue requires expanded native pages')
        reviewed = {int(r['item_id'], 16): r for r in metadata(rel, donor_symbols)[1]}
        garden_rows.update(reviewed)
        large_rows.update(reviewed)
    if tent_model:
        from v3_camping_actor_art import ACTORS, source_metadata
        if not camping:
            raise ValueError('Tent model requires the camping catalogue integration')
        row = source_metadata(rel, donor_symbols, ACTORS[2])
        row.update(runtime_index=row['donor_runtime_index'], ordinary_stock=False)
        garden_rows[0x336C] = large_rows[0x336C] = reviewed[0x336C] = row
    if fire:
        from v3_camping_actor_art import ACTORS, source_metadata
        if not camping:
            raise ValueError('Fire catalogue needs the camping integration')
        for actor in ACTORS[:2]:
            row = source_metadata(rel, donor_symbols, actor)
            row.update(runtime_index=row['donor_runtime_index'], ordinary_stock=False)
            garden_rows[actor.item] = large_rows[actor.item] = reviewed[actor.item] = row
    if school_desks:
        from v3_school_desks import metadata
        from v3_asset_loader import ROOT
        if not expanded:
            raise ValueError('School desks require expanded catalogue pages')
        school_rows = metadata(rel, donor_symbols, ROOT / 'build/item-identity-megasheet.xlsx')[1]
        garden_rows.update({int(r['item_id'], 16): {**r, 'ordinary_stock': True} for r in school_rows})
    for row in furniture:
        item, index = int(row['item_id'], 16), row['runtime_index']
        if (item, index) not in ((0x3224, 1161), (0x32B8, 1198), (0x3350, 1236)) and not (
                expanded and item in STOCK and STOCK[item][0] == index) and not (
                item in garden_rows and garden_rows[item]['runtime_index'] == index):
            raise ValueError('New catalogue import needs reviewed preview and shop rules')
        found = [(n, mode) for n, (i, mode) in enumerate(struct.iter_unpack('>HH', donor)) if i == index]
        expected_mode = large_rows[item]['preview_mode'] if item in large_rows else 0
        if (len(found) != 1 or found[0][1] != expected_mode
                or draw[:8] != data[0x808AF87C - RAM:0x808AF87C - RAM + 8]):
            raise ValueError('Donor catalogue preview mode is not the verified native mode')
        group = (garden_rows[item]['donor_list'] if item in garden_rows else
                 STOCK[item][1] if item in STOCK else ('ftr_listC' if item == 0x3224 else 'ftr_listA'))
        goods = symbol_data(rel, symbol_text, group)
        ids = struct.unpack('>' + str(len(goods) // 2) + 'H', goods)
        if ids[-1] != 0 or ids.count(item) != 1 or 0 in ids[:-1]:
            raise ValueError('Donor item lacks verified acquisition-list membership')
        records.append({'item_id': f'{item:04X}', 'runtime_index': index,
            'catalogue_index': (item - 0x1000) >> 2, 'donor_position': found[0][0], 'mode': 0,
            'ordinary_shop_list': group, 'shop_list_sha256': sha256(goods)})
        if item in garden_rows:
            records[-1].update(donor_acquisition_list=group,
                ordinary_shop_list=group if garden_rows[item]['ordinary_stock'] else None,
                catalogue_orderable=garden_rows[item].get('catalogue_orderable', item != 0x3294))
        if item in large_rows:
            record = large_rows[item]
            scalar = draw[expected_mode * 8:(expected_mode + 1) * 8]
            if scalar.hex() != record['donor_preview_scalar_hex']:
                raise ValueError('Changed large Western catalogue framing')
            records[-1].update(donor_preview_mode=expected_mode,
                donor_preview_scalar_hex=scalar.hex(),
                preview_override=expected_mode != 0,
                preview_define='AF_V3_CAMPING_ITEMS' if camping and item in reviewed else 'AF_V3_WESTERN_LARGE',
                preview_mapping='native mode 0; guarded final scale/Y override' if expected_mode else 'native mode 0')
    records.sort(key=lambda row: row['donor_position'])
    if len({row['item_id'] for row in records}) != len(records) or len(rows) + len(records) > (CAPACITY if expanded else 444):
        raise ValueError('Catalogue duplicates or exceeds the actual native item capacity')
    rows += [(row['catalogue_index'], row['mode']) for row in records]
    return b''.join(struct.pack('>HH', *row) for row in rows), records


def install(base, parent, suffix, compiled, ordering, records, collection, runtime, room, *, clothing=None, expanded=False):
    old, reloc, source_parent = sources(base)
    symbols = compiled['symbols']
    if any(row.get('preview_override') for row in records) and (
            '-DAF_V3_WESTERN_LARGE=1' not in compiled['flags'] or clothing is None
            or '-DAF_V3_CLOTHING_CATALOGUE=1' not in compiled['flags']):
        raise ValueError('Large Western previews require the installed initializer override')
    if any(row.get('preview_override') and '-D' + row.get('preview_define', 'AF_V3_WESTERN_LARGE') + '=1'
           not in compiled['flags'] for row in records):
        raise ValueError('Catalogue preview lacks its reviewed item-family override')
    limit = 0xE50 if '-DAF_V3_WESTERN_LARGE=1' in compiled['flags'] else 0xC50
    if (len(suffix) != compiled['bytes'] or not suffix or len(suffix) > limit or len(suffix) % 16
            or collection['symbols']['af_v3_catalogue_owned'] != IMPORTS['af_v3_catalogue_owned']
            or runtime['symbols']['af_v3_save_halt'] != IMPORTS['af_v3_save_halt']
            or room['symbols']['af_v3_room_query'] != IMPORTS['af_v3_room_query']
            or any(symbols[name] != value for name, value in IMPORTS.items())
            or parent[OWNER:OWNER + 32] != source_parent[OWNER:OWNER + 32]):
        raise ValueError('Changed catalogue helper dependencies or parent descriptor')
    data = bytearray(old + suffix)
    count = 436 + len(records)
    from v3_catalogue_capacity import CAPACITY, POOL_EXTRA, expand, shifted
    if count > (CAPACITY if expanded else 444):
        raise ValueError('Ordering exceeds installed catalogue storage')
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

    clothing_report = None
    if clothing is not None:
        from v3_clothing_catalogue import POINTER, COUNT, TABLE as CLOTH_TABLE, NATIVE_COUNT
        from v3_npc_clothing import guard_incoming
        clothing_table, clothing_report = clothing
        extra_clothes=3 if '-DAF_V3_ALOHA_DISPLAY=1' in compiled['flags'] else 1
        cloth_address = symbols['af_v3_catalogue_clothing_order']
        cloth_at = cloth_address-RAM
        if ('-DAF_V3_CLOTHING_CATALOGUE=1' not in compiled['flags']
                or len(clothing_table) != (NATIVE_COUNT+extra_clothes)*2
                or not SIZE <= cloth_at <= len(data)-len(clothing_table)
                or data[cloth_at:cloth_at+len(clothing_table)] != clothing_table
                or clothing_table[:NATIVE_COUNT*2] != old[CLOTH_TABLE-RAM:CLOTH_TABLE-RAM+NATIVE_COUNT*2]
                or sha256(old[0x17C:0x630]) != '9011f6c34b7eba02f11fa2e2b87b18af33bc2569b7a17c8dded46fd44657c37d'
                or slots.get(POINTER-RAM) != 2 or slots.get(0x342C) != 4
                or any(at in slots for at in (0x17C, 0x180))):
            raise ValueError('Changed clothing catalogue table, complete initializer, or relocations')
        guard_incoming(old, 14048, RAM, [(0x17C, 8)])
        word(POINTER, CLOTH_TABLE, cloth_address)
        word(COUNT, NATIVE_COUNT, NATIVE_COUNT+extra_clothes)
        word(0x808A952C, jump(0x808A931C), jump(symbols['af_v3_catalogue_bit']))
        word(0x808A627C, 0x27BDFFB8, jump(symbols['af_v3_catalogue_furniture_init'], False))
        word(0x808A6280, 0xAFB00020, 0)
        rows.append(0x4400017C)
        clothing_report = {**clothing_report, 'table_address': cloth_address,
            'table_sha256': sha256(clothing_table), 'initializer_entry': 0x808A627C,
            'initializer_target': symbols['af_v3_catalogue_furniture_init'],
            'initializer_bridge': symbols['af_v3_original_catalogue_furniture_init']}

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
    capacity_report = None
    if expanded:
        data, rows, capacity_report = expand(data, rows)
        if clothing_report is not None:
            clothing_report = {**clothing_report, 'table_address': shifted(clothing_report['table_address'])}
            for key in ('initializer_target', 'initializer_bridge'):
                clothing_report[key] = shifted(clothing_report[key])
    size = (24 + len(rows) * 4 + 15) & ~15
    new_rel = (struct.pack('>5I', len(data), 0, 0, 0, len(rows))
        + struct.pack('>' + str(len(rows)) + 'I', *rows)
        + bytes(size - 24 - len(rows) * 4) + struct.pack('>I', size))
    changed_parent = bytearray(parent)
    struct.pack_into('>I', changed_parent, OWNER + 4, VROM + len(data))
    struct.pack_into('>I', changed_parent, OWNER + 12, RAM + len(data))
    align = lambda value: (value + 63) & ~63
    growth, relocation_growth = align(len(data)) - align(SIZE), align(len(new_rel)) - align(len(reloc))
    required, reserved = 253696 + 0x4400 + 64 + growth + relocation_growth, 257152 + 0x4400 + (POOL_EXTRA if expanded else 0)
    code = by_vrom(base)[CODE_VROM].extract(base)
    if (required > reserved or u32(code, 0x800C4AFC - CODE_RAM) != 0x3C0E8089
            or u32(code, 0x800C4B10 - CODE_RAM) != 0x25CE7620):
        raise ValueError('Extended catalogue exceeds the actual shared menu reservation')
    allowed = {i for p in patches for i in range(p['address'] - RAM, p['address'] - RAM + 4)}
    if expanded:
        allowed |= {i for p in capacity_report['patches'] for i in range(p['address'] - RAM, p['address'] - RAM + 4)}
    for address in (0x801A0010, 0x802F8010, 0x803D0010):
        before = relocate_verified_data(Image(RAM, SIZE, (SIZE, 0, 0, 0, 152)), old, reloc, address)
        after = relocate_verified_data(Image(RAM, len(data), (len(data), 0, 0, 0, len(rows))), bytes(data), new_rel, address)
        if expanded:
            after = after[:capacity_report['insert_at']] + after[capacity_report['insert_at'] + capacity_report['insert_bytes']:]
        if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(before, after))):
            raise ValueError('Catalogue change alters an unrelated relocated word')
    changes = {VROM: bytes(data), RELOC: new_rel, PARENT: bytes(changed_parent)}
    if expanded:
        # The native allocator takes this checked endpoint through a signed
        # ADDIU: growing past 8000 also requires the matching LUI carry.
        endpoint = 0x80897620 + POOL_EXTRA
        code = bytearray(code)
        struct.pack_into('>I', code, 0x800C4AFC - CODE_RAM, 0x3C0E0000 | ((endpoint + 32768) >> 16))
        struct.pack_into('>I', code, 0x800C4B10 - CODE_RAM, 0x25CE0000 | (endpoint & 65535))
        changes[CODE_VROM] = bytes(code)
    return changes, {
        'imports': records, 'native_rows': 436, 'total_rows': count, 'row_capacity': CAPACITY if expanded else 444,
        'catalogue_index_encoding': '(item - 0x1000) >> 2; separate from room runtime indices',
        'source_sha256': SOURCE_SHA, 'relocation_source_sha256': RELOC_SHA,
        'output_sha256': sha256(data), 'relocation_sha256': sha256(new_rel),
        'bytes': len(data), 'relocation_bytes': len(new_rel), 'patches': patches,
        'rounded_growth': growth, 'rounded_relocation_growth': relocation_growth,
        'conservative_pool_required': required, 'pool_reserved': reserved,
        'additional_pool_allocation': POOL_EXTRA if expanded else 0, 'save_format_changed': False,
        'native_preview_tested': False, 'ordinary_order_delivery_tested': False,
        **({'clothing': clothing_report} if clothing_report is not None else {}),
        **({'capacity_expansion': capacity_report} if capacity_report is not None else {})}
