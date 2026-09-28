"""Shared carried event items: all exercise-card states and Harvest cutlery.

Names, categories, price semantics, icons, and world art come from the donor.
Preparation is independent of activation: unfinished event/player consumers do
not become selectable merely because their complete resources are installed.
"""
import copy
import json
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from apply_translation import write_new
from v3_asset_loader import ROOT, MODULE_RAM, compile_part
from v3_furniture_pipeline import Source
from v3_registry import HOLIDAY_ITEMS, HOLIDAY_ITEM_CATEGORIES, HOLIDAY_ITEM_REGISTRY_VERSION

RAM, TABLE, ICON, ART, END = 0x80705600, 0x80705E00, 0x80706000, 0x80706500, 0x80708000
FIRST, COUNT = 0x2523, 14
# Free renderer-category slots, not replacements for existing item identities.
# The general equipment map still uses 27 + donor category. These explicit
# reservations keep existing 71-entry native arrays and tables unchanged.
CATEGORIES = HOLIDAY_ITEM_CATEGORIES
TABLES = {
    'itemName_etc': (784, '41e671ca45dd43ac8a54f8e71ff4b55b947d52b80cd97bae9fb40e5fc7edc07f'),
    'item1_5_tableNo': (49, '682d400251d20485243dcd4f8b77235f5b4d1ce43fe1e6c19ae814ead87fbb39'),
}
SOURCES = ('tools/v3_holiday_items.py', 'tools/v3_registry.py', 'tools/v3_item_categories.py', 'tools/v3_category_runtime.py',
    'tools/v3_furniture_install.py', 'tools/v3_asset_loader.py', 'overlays/v3/holiday_items.c',
    'overlays/v3/holiday_items.ld', 'overlays/v3/creature_icon.S', 'overlays/v3/item_categories.c',
    'translations/provenance.json')
PREPARED = ROOT/'build/v3-diary-category-work-01/event-items-prepared-03'


def records(source):
    receipts = {}
    for name, (size, digest) in TABLES.items():
        raw = source.raw(name)
        if len(raw) != size or sha256(raw) != digest:
            raise ValueError('Changed complete holiday item table: '+name)
        receipts[name] = dict(offset=source.symbol(name)[0], bytes=size, sha256=digest)
    price, price_receipt = source.function(0x784E0)
    p, n = source.symbol('l_price_info')
    price_refs = source.pointers(p, n)
    if (len(price) != 544 or sha256(price) != '3f45cc5bf10f883d41575bc4f66cd1f8cfa1f86e46795ec386baaf412a7edb2b'
            or n != 64 or source.raw('l_price_info') != bytes(n) or p+5*4 in price_refs):
        raise ValueError('Changed miscellaneous zero-price donor path')
    # These are not shells or the signboard, the two priced miscellaneous
    # exceptions in the complete checked function. Their category has no table.
    names = source.raw('itemName_etc'); types = source.raw('item1_5_tableNo'); rows = []
    for item in range(FIRST, FIRST+COUNT):
        index = item & 255; name = names[index*16:(index+1)*16]; category = types[index]
        if category not in CATEGORIES or category != (47 if index < 48 else 52):
            raise ValueError('Changed complete exercise/Harvest category relationship')
        if HOLIDAY_ITEMS.get(item)!=item:raise ValueError('Changed fixed additive event item identity')
        rows.append(dict(id=f'GAFE01-r0/item/{item:04X}', item_id=f'{item:04X}',
            donor_item_id=f'{item:04X}', name=name.decode('ascii').rstrip(), name_sha256=sha256(name),
            name_source_symbol='itemName_etc', name_source_index=index,
            source_category=category, native_category=CATEGORIES[category], price=0,
            ready=False, selected=False))
    return rows, dict(tables=receipts, price_function=price_receipt,
        price_table=dict(offset=p, bytes=n, pointers=price_refs, miscellaneous_pointer=None),
        source_rel_sha256=sha256(source.rel), source_symbols_sha256=sha256(source.symbols.encode()))


def pocket_icons(source, rows):
    from title_assets import pack4, untile
    from v3_villager_art import native_palette
    a, n = source.symbol('item_tex_data_table$779')
    t, size = source.symbol('etc_tex_table$768'); refs = source.pointers(t, size)
    if (n != 64 or source.pointers(a, n).get(a+5*4) != t or size != 49*8 or
            source.data[t:t+size] != bytes(size) or set(refs) != set(range(t, t+size, 4))):
        raise ValueError('Changed complete miscellaneous pocket-icon binding')
    pairs = {}; data = bytearray(); bindings = []
    for row in rows:
        index = int(row['donor_item_id'], 16) & 255
        pair = tuple(refs[t+8*index+4*lane] for lane in range(2))
        if pair not in pairs:
            offset = len(data); data.extend(struct.pack('>2I', ICON+offset+32, ICON+offset+64)+bytes(24))
            resources = []
            for lane, at in enumerate(pair):
                symbol, _, width = source.containing(at, exact=True); raw = source.raw(symbol)
                if width != (32, 512)[lane] or source.pointers(at, width):
                    raise ValueError('Unsupported complete event item icon')
                converted = native_palette(raw) if lane == 0 else pack4(untile(raw, 32, 32, 4))
                resources.append(dict(symbol=symbol, source_offset=at, source_sha256=sha256(raw),
                    offset=len(data), bytes=width, sha256=sha256(converted)))
                data.extend(converted)
            pairs[pair] = dict(offset=offset, address=ICON+offset, resources=resources)
        bindings.append(dict(item_id=row['item_id'], **pairs[pair]))
    if ICON+len(data) > ART:
        raise ValueError('Event item icons exceed shared reservation')
    return bytes(data), dict(table=t, table_bytes=size, pointers=refs, bindings=bindings,
        unique_icons=len(pairs), width=32, height=32, format_native='CI4/RGBA5551')


def prepare(source, directory):
    from v3_item_categories import convert
    directory = directory.resolve()
    if not directory.is_relative_to(ROOT/'build'):
        raise ValueError('Extracted donor assets must stay in ignored build output')
    rows, receipt = records(source)
    directory.mkdir(parents=True, exist_ok=False)
    artwork = convert(source, directory/'categories', parent_records=rows)
    data, icons = pocket_icons(source, rows)
    write_new(directory/'icons.bin', data)
    receipt.update(format='AFV3-HOLIDAY-ITEMS-PREPARED-1', rows=rows, icons=icons,
        icon_sha256=sha256(data), icon_bytes=len(data), categories=artwork,
        selectable=False, pending=['event activation and exercise-card menu',
            'Harvest player pickup/completion and tabletop drawing', 'profile/save admission'])
    write_new(directory/'items.json', (json.dumps(receipt, indent=2)+'\n').encode())
    return receipt


def install(base, prior, blob, core, module, output, directory=PREPARED):
    from v3_category_runtime import prepared, rebase_art, append_categories
    from v3_furniture_icon import VROM as MENU, RAM as MENU_RAM
    from v3_furniture_install import provenance_patch
    from v3_import_storage import jump
    from v3_holiday_state import RAM as STATE_RAM
    import v3_physical_resources as physical
    e=copy.deepcopy(prior['equipment_resources']);events=e['npc_extra']['events']
    if not events.get('decorations',{}).get('controllers') or e.get('holiday_items'):
        raise ValueError('Shared event items require installed decorations and empty item reservation')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    rows,receipt=records(source);directory=directory.resolve()
    source_report=json.loads((directory/'items.json').read_bytes())
    if any(source_report[k]!=json.loads(json.dumps(v)) for k,v in dict(receipt,rows=rows).items()):
        raise ValueError('Prepared event item records differ from complete donor')
    assets,artwork,art_receipt=prepared(source,directory/'categories',parent_records=rows)
    icons,icon_receipt=pocket_icons(source,rows)
    if ((directory/'icons.bin').read_bytes()!=icons or source_report['icon_sha256']!=sha256(icons) or
            source_report['icons']!=json.loads(json.dumps(icon_receipt))):
        raise ValueError('Changed complete prepared event item icons')
    native=0x8010B1BC
    if (u32(core,0x8010B334-CODE_RAM+5*4)!=native or
            core[native-CODE_RAM:native-CODE_RAM+31].hex()!=
            '160d0d0d0d0d0d0d0d0d0d0d0d09151515141716191818181919181a0e0b00'):
        raise ValueError('Changed native miscellaneous items; additions must not replace them')
    packet=e['holiday_state']['packet'];start=packet['physical'];raw=bytearray(base[start:start+packet['bytes']])
    if (packet['ram']!=STATE_RAM or not STATE_RAM<=RAM<END<=STATE_RAM+len(raw) or
            sha256(raw)!=packet['sha256'] or any(raw[RAM-STATE_RAM:END-STATE_RAM])):
        raise ValueError('Shared event item reservation is occupied or outside loaded packet')
    hooks=[dict(kind=h['kind'],address=h['address'],before=h['after'],prior=h['target'],
        symbol='af_holiday_item_'+h['kind']) for h in e['diary_items']['hooks']
        if h['kind'] in ('name','type','price','display','pocket')]
    if len(hooks)!=5:raise ValueError('Incomplete carried item predecessor chain')
    bindings={'af_holiday_prior_'+h['kind']:h['prior'] for h in hooks}
    bindings['af_holiday_prior_icon']=e['diary_items']['code']['symbols']['af_diary_icon_hook']
    code,compiled=compile_part('holiday_items',output/'holiday-items',
        extra_sources=('overlays/v3/creature_icon.S',),defines=('AF_HOLIDAY_ICON=1',),link_symbols=bindings)
    table=bytearray(struct.pack('>4I',0x41464849,2,COUNT,0))
    for row,icon in zip(rows,icon_receipt['bindings']):
        name=row['name'].encode('ascii').ljust(16,b' ')
        if len(name)!=16 or sha256(name)!=row['name_sha256']:raise ValueError('Changed official event item name')
        table.extend(struct.pack('>HHBBHI',int(row['item_id'],16),row['price'],row['native_category'],
            1 if row['source_category']==47 else 2,0,icon['address'])+name)
    for address,data,limit in ((RAM,code,TABLE),(TABLE,table,ICON),(ICON,icons,ART)):
        if address+len(data)>limit:raise ValueError('Event item resources exceed their reserved ranges')
        raw[address-STATE_RAM:address-STATE_RAM+len(data)]=data
    cursor=ART
    for row in artwork:
        category=row['source_category'];data,fixes=rebase_art(assets[category],row,cursor)
        if cursor+len(data)>END:raise ValueError('Event artwork overlaps retained decoration geometry')
        raw[cursor-STATE_RAM:cursor-STATE_RAM+len(data)]=data
        row.update(native_category=CATEGORIES[category],ram=cursor,
            installed_sha256=sha256(data),pointer_relocations=fixes)
        cursor+=len(data)
    for h in hooks:
        if h['address']>=0x80460000:owner,origin=blob,0x80460000
        else:owner,origin=(module,MODULE_RAM) if h['address']>=MODULE_RAM else (core,CODE_RAM)
        at=h['address']-origin
        if owner[at:at+8]!=bytes.fromhex(h['before']):raise ValueError('Changed event item predecessor: '+h['kind'])
        target=compiled['symbols'][h['symbol']];after=struct.pack('>2I',jump(target),0)
        owner[at:at+8]=after;h.update(target=target,after=after.hex())
    files=by_vrom(base);menu=bytearray(files[MENU].extract(base));at=0x8085C968-MENU_RAM
    before=struct.pack('>2I',jump(bindings['af_holiday_prior_icon']),0)
    if menu[at:at+8]!=before:raise ValueError('Changed complete event icon predecessor')
    after=struct.pack('>2I',jump(compiled['symbols']['af_holiday_icon_hook']),0);menu[at:at+8]=after
    changes=append_categories(base,e,blob,core,output,artwork,query_defines=(
        f'AF_V3_HOLIDAY_CATEGORY_QUERY=0x{compiled["symbols"]["af_holiday_item_type"]:X}u',))
    changes[MENU]=bytes(menu);e['pocket_icons']['owner_sha256']=sha256(menu)
    resources=copy.deepcopy(prior['physical_resources']);physical.verify(base,resources)
    record=next(r for r in resources if r['id']==packet['id'])
    if (record['physical'],record['bytes'],record['sha256'])!=(start,len(raw),packet['sha256']):
        raise ValueError('Changed holiday packet physical owner')
    record['sha256']=sha256(raw)
    e['holiday_state']['packet']=dict(packet,sha256=sha256(raw),crc32=zlib.crc32(raw))
    # Replace only the formerly empty owned reservation. All renderer/controller
    # code, actor state, original art, and guards must remain intact.
    for lo,hi in ((STATE_RAM,RAM),(END,STATE_RAM+len(raw))):
        if raw[lo-STATE_RAM:hi-STATE_RAM]!=base[start+lo-STATE_RAM:start+hi-STATE_RAM]:
            raise ValueError('Event items change retained holiday resources')
    sources={s:sha256((ROOT/s).read_bytes()) for s in SOURCES}
    e['holiday_items']=dict(receipt,format='AFV3-HOLIDAY-ITEMS-1',rows=rows,code=compiled,hooks=hooks,
        ram=RAM,bytes=END-RAM,sha256=sha256(raw[RAM-STATE_RAM:END-STATE_RAM]),
        table_ram=TABLE,table_bytes=len(table),table_sha256=sha256(table),ready_mask=0,
        icons=icon_receipt,artwork=artwork,preparation=art_receipt,
        icon_hook=dict(vrom=MENU,ram=MENU_RAM,address=0x8085C968,before=before.hex(),after=after.hex()),
        native_miscellaneous_count=30,native_category_count=e['item_categories']['count'],
        registry_version=HOLIDAY_ITEM_REGISTRY_VERSION,input_packet=packet,
        selected=0,saved_format_changed=False,native_execution_verified=False,sources=sources,
        pending=source_report['pending'])
    e['npc_extra']['sources'].update(sources)
    attribution=provenance_patch(rows,('tools/v3_holiday_items.py',))
    if attribution:write_new(output/'provenance.patch',attribution.encode())
    write_new(output/'holiday-items.json',(json.dumps(e['holiday_items'],indent=2)+'\n').encode())
    write_new(output/'holiday-items-packet.bin',raw)
    return e,changes,dict(physical_resources=resources),[(dict(record,previous_sha256=packet['sha256']),bytes(raw))]


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=__import__('pathlib').Path, required=True)
    args = parser.parse_args()
    donor = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    result = prepare(donor, args.prepare)
    print(json.dumps(dict(records=len(result['rows']), categories=len(result['categories']['objects']),
        icons=result['icons']['unique_icons'], selectable=False)))
