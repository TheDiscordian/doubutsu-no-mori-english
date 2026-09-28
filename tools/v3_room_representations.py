"""Distinguish saved designs and museum scenery from fixed donor items.

Read the actual profile tables and complete consumers. A name-table entry is
not evidence of a collectible, a fixed appearance, or a native equivalent.
These records describe dependencies; they do not enable imports.
"""
import struct

from aflib import sha256, u32
from v3_registry import furniture_source_index


DESIGN_CALLBACKS = (
    ('mannequin', 'iam_myfmanekin', 0x2C24EC,
     'b747cd3eefd013f81383fd07c5cc80bb1692b39afe449443c7258c95186bbb85',
     0x2C2554, '97cb769d5464a0d7ec74209e50620a2aeba06992a2e1841723d60409825ba42b',
     'obj_shop_manekin_model', 0x100),
    ('umbrella', 'iam_myfumbrella', 0x2C25E8,
     '2f100d5e239f84283a3026a0fa9f4a227db6db2b579c580e364fd5a9e814c5b5',
     0x2C2650, '4d9d133bdd864e05d833a5d416e805771825416f26c5a7b7db4d44bbba4c6283',
     'obj_shop_umbmy_model', 0x200),
)


def checked_function(source, address, size, digest, relocations):
    raw, receipt = source.function(address)
    if len(raw) != size or sha256(raw) != digest or receipt['relocations'] != relocations:
        raise ValueError('Changed complete room-representation consumer: '+receipt['symbol'])
    return raw, receipt


def profile(source, item):
    index = furniture_source_index(item)
    pointers = [table.get(at+index*4) for (at, _), table in zip(source.names['furniture_quality'], source.quality)]
    if pointers[0] is None or pointers[0] != pointers[1]:
        raise ValueError('Room-representation profile tables disagree')
    name, at, size = source.containing(pointers[0], exact=True)
    if size != 52:
        raise ValueError('Changed room-representation profile size')
    raw = source.data[at:at+size]
    return dict(symbol=name, offset=at, bytes=size, sha256=sha256(raw)), raw


def named_row(source, item, category, reason, **details):
    index = furniture_source_index(item)
    symbol, position = ('ftrName_table', index) if index < 1024 else ('ftrName2_table', index-1024)
    name = source.raw(symbol)[position*16:(position+1)*16]
    if len(name) != 16 or any(c < 32 or c > 126 for c in name) or not name.strip():
        raise ValueError('Room representation lacks its complete source name')
    return dict(item_id=f'{item:04X}', name=name.decode('ascii').rstrip(),
        name_sha256=sha256(name), name_symbol=symbol, name_index=position,
        category=category, independently_selectable=False, runtime_installed=False,
        reason=reason, **details)


def discover(source):
    module = u32(source.rel, 0)
    rows, consumers = [], {}
    for kind, symbol, draw_at, draw_sha, dma_at, dma_sha, model, interaction in DESIGN_CALLBACKS:
        at, size = source.symbol(symbol)
        model_at, _ = source.symbol(model)
        draw, draw_receipt = checked_function(source, draw_at, 96, draw_sha,
            {10:(6,module,5,model_at), 38:(4,module,5,model_at)})
        dma, dma_receipt = checked_function(source, dma_at, 144, dma_sha,
            {62:(6,module,6,48192), 78:(4,module,6,48192)})
        # The complete DMA callback subtracts the first display ID, divides by
        # four, masks to eight slots, and reads the owning player's saved design.
        first = (-struct.unpack_from('>h', dma, 0x3A)[0]) & 65535
        items = [0x1000+i*4 if i < 1024 else 0x3000+(i-1024)*4
                 for i in range(1266) if source.quality[0].get(0x39FB4+i*4) == at]
        if items != list(range(first, first+32, 4)) or size != 52:
            raise ValueError('Saved-design profiles disagree with their complete DMA range')
        consumers[kind] = dict(draw=draw_receipt, dma=dma_receipt)
        for slot, item in enumerate(items):
            receipt, raw = profile(source, item)
            vtable = source.relocations.get(at+48)
            if (raw[:32] != bytes(32) or raw[32:48] != struct.pack('>ff6BH',30,.01,4,0,0,0,0,0,interaction)
                    or raw[48:] != bytes(4) or vtable is None or vtable[:3] != (1,True,5)
                    or {p-at for p in source.relocations if at <= p < at+52} != {48}):
                raise ValueError('Changed saved-design profile or callback binding')
            vt = vtable[3]
            if source.containing(vt, exact=True)[2] != 20 or any(source.data[vt:vt+20]):
                raise ValueError('Changed saved-design callback table')
            for offset in range(0,20,4):
                pointer = source.relocations.get(vt+offset)
                if pointer is None or pointer[:3] != (1,True,1):
                    raise ValueError('Incomplete saved-design callback table')
                code, _ = source.function(pointer[3])
                if ((offset in (0,4,12) and (code != bytes.fromhex('4e800020')
                                           or source.function(pointer[3])[1]['relocations']))
                        or offset == 8 and pointer[3] != draw_at
                        or offset == 16 and pointer[3] != dma_at):
                    raise ValueError('Changed saved-design lifecycle')
            rows.append(named_row(source,item,'saved-player-design',
                'Player-created design display, not a fixed donor appearance. Requires saved designs, '
                'editing, owner-aware rendering, and the corresponding clothing/umbrella interaction.',
                form=kind, design_slot=slot, profile=receipt, native_identity='not_established',
                texture_bytes=512, palette_bytes=32, saved_record_bytes=544,
                source_model=model))

    table_at, size = source.symbol('mMmd_museum_fossil_data')
    table = source.raw('mMmd_museum_fossil_data')
    if (size != 200 or sha256(table) != '921dcbd70358ab200ac6b9b4b8877b91853b0b3b8165f29ee02e93c9a7e9ab30'
            or source.pointers(table_at,size)):
        raise ValueError('Changed complete museum fossil placeholder table')
    code, receipt = checked_function(source,0x57968,212,
        'f55200ea479b5504a1708832f54307e5a12ece3cf819636aed6bebda4d78f261',
        {16:(10,0,4,2148118212),192:(10,0,4,2148118288),
         22:(6,module,5,table_at),30:(4,module,5,table_at)})
    first, count = u32(code,0x74)&65535, u32(code,0xB4)&65535
    if count*8 != size or u32(code,0x80)&65535 != first:
        raise ValueError('Museum specimen range disagrees with complete consumer')
    placeholders = {}
    for index, (tile,padding,item,rotation) in enumerate(struct.iter_unpack('>BBHI',table)):
        if padding or item&3 or rotation > 3 or first <= item < first+count*4:
            raise ValueError('Invalid museum placeholder identity or placement')
        placeholders.setdefault(item,[]).append(dict(specimen_item_id=f'{first+index*4:04X}',
            museum_tile=tile, rotation=rotation))
    for item, specimens in sorted(placeholders.items()):
        bound, raw = profile(source,item)
        if struct.unpack_from('>H',raw,46)[0] != 0x400:
            raise ValueError('Museum placeholder lacks its actual fossil interaction')
        rows.append(named_row(source,item,'museum-placeholder',
            'Museum scenery used before the associated fossils are donated; not an additional collectible fossil.',
            profile=bound, specimens=specimens))
    consumers['museum'] = dict(function=receipt, table=dict(symbol='mMmd_museum_fossil_data',
        offset=table_at,bytes=size,sha256=sha256(table)))
    return dict(format='AFV3-ROOM-REPRESENTATIONS-1', consumers=consumers,
        rows=sorted(rows,key=lambda r:r['item_id']))


def annotate_inventory(items, catalogue):
    by_id = {row['donor_item_id']:row for row in items}
    if len(by_id) != len(items):
        raise ValueError('Duplicate donor inventory identity')
    for representation in catalogue['rows']:
        row = by_id.get(representation['item_id'])
        if row is None or row['name_sha256'] != representation['name_sha256'] or row['selectable']:
            raise ValueError('Room representation does not bind the complete donor inventory')
        row.update(status=representation['category'], room_representation=representation,
                   reason=representation['reason'])
