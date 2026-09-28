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
PICKUP_RAM = 0x80707000
PICKUP_SOURCES = SOURCES+('overlays/v3/holiday_pickup.c','overlays/v3/holiday_pickup.S',
    'overlays/v3/holiday_pickup.ld','overlays/v3/decoration_actor.h','tools/v3_holiday_dialogue.py',
    'tools/v3_event_text.py','tools/v3_player_actions.py')
PICKUP_NATIVE = (
    ('af_holiday_pickup_find',0x800B80B4,0x800B8128,'a66e85096d846c37b6131dc4d5bb3b50fdde2ece121e1355c1c9bedb13bc1394'),
    ('af_holiday_pickup_demo',0x8007CDD8,0x8007CF00,'e96b6e94b5d07e8749ca32ba0cb279ca01c1188c4253a273cb6014e6a03dc5c6'),
    ('af_holiday_pickup_title',0x8007D90C,0x8007D91C,'f36a165b7d65a6ce4b7e25d3a9cc40585f08edd0738b8c924d75b3435c70690a'),
    ('af_holiday_pickup_message',0x8007B5C0,0x8007B5F4,'b54b7ba3c3734fe633386c949511c81623090c04bb59d274a870d8f1be1af1ce'),
    ('af_decor_native_player',0x800B1C84,0x800B1C90,'f680a77d022740add2a8ead09c6438223d596b51cd655775b7a7ec0c80725404'),
    ('af_decor_native_ground',0x80071A08,0x80071AB8,'bb4e0020a3b25835f60ec899571268e482790d1741d23e271b52dbd0919ab750'))
PICKUP_PLAYER = (
    (0x808BBFD4,0x808BC2D8,'e8ec3959fdf4bf8186635be089341893be4dcbe0021478a3909d3b1728444c1d'),
    (0x808C8218,0x808C82A8,'8152a6b5b04fc71330c6d3eb1b7a85cc5c0e1ac3f4404586fa7efe24de36886d'),
    (0x808C82A8,0x808C843C,'23819c4260ccdc049b40d8f2081a37b5af75e17474fbe766a42ee67e5db7b451'),
    (0x808B55E8,0x808B5644,'b445dc7600a6a02ca526606e53ce695404bbb140263b75ff6e7b648896d390a7'),
    (0x808C0624,0x808C06AC,'bb9c5ed4b5282cc3895423b6f1b426b7518422320deabb1b2d765d86df218dd8'))
GROUND_CLASSIFY = (
    '91550b4337a04156de81bb91b881bc8d9eeba654d7401513a9fdaabe433d6218',
    '8f3ff49f740614017caeb2a6f2edfd0fc8f16ba2899f7ddcd08027ba92d805c8',
    'eec27835222c71d0524122d5b2a0ac6fcf3b9b42b3672859fb95e191c761b48e',
    '75bf81404396388cb475e64b1dd63caea96e9e8b61e66d52208cea23bc567922')


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


def pickup_text(base, prior, output):
    from v3_camper_text import donor,extend_bank
    from v3_event_text import MESSAGE,TABLE,CHOICE_TABLE
    from v3_holiday_dialogue import credit,check_provenance
    from gc_text import decode_gc
    from runtime_module import module_command_info
    from textcodec import encode,tokenize
    from textvalidate import expanded_bound
    messages,_,decoder=donor();original=messages[0x3B59];info=module_command_info(base)
    if sha256(original)!='79ed472283ad1d4bf0c54e700fad3701a266df73404ae4f8bf39ee1f624a42f5':
        raise ValueError('Changed official Harvest full-pocket message')
    data=encode(decode_gc(original,decoder),info);tokens=list(tokenize(data,info))
    if (expanded_bound(data,info)>1024 or not tokens or tokens[-1].data!=b'\x7f\0' or
            sum(t.kind=='cmd' and t.data[1]==0 for t in tokens)!=1 or
            any(t.kind=='cmd' and t.data[1] not in (0,3,5) for t in tokens)):
        raise ValueError('Unreviewed Harvest refusal control or buffer bound')
    entry=credit('message:3060','message:3B59',original,data,
        ['Native encoding; retain official wording, line breaks, colours, and pause'])
    entry['locales']['en']['locator']=['tools/v3_holiday_items.py:pickup_text','N64/message/3060']
    text=dict(first_id=0x3060,count=1,source_id=0x3B59,provenance_entries=[entry],
        bytes=len(data),sha256=sha256(data),expanded_bound=expanded_bound(data,info),
        choice_vrom=prior['import_storage']['choice_vrom'])
    check_provenance(text)
    files=by_vrom(base);cv=text['choice_vrom']
    payload,table=extend_bank(files[MESSAGE].extract(base),files[TABLE].extract(base),[data],0x3060)
    text['resources']=[]
    for v,d in ((MESSAGE,payload),(TABLE,table),(cv,files[cv].extract(base)),(CHOICE_TABLE,files[CHOICE_TABLE].extract(base))):
        name=f'pickup-text-{v:08X}.bin';write_new(output/name,d)
        text['resources'].append(dict(vrom=v,file=name,bytes=len(d),sha256=sha256(d),
            original_sha256=sha256(files[v].extract(base))))
    return text


def install_pickup(base,prior,blob,core,output):
    from v3_equipment_runtime import PLAYER_RAM,PLAYER_VROM,PLAYER_RELOC
    from v3_ground_categories import OWNERS
    from v3_event_text import patch_bounds
    from v3_import_storage import jump
    from v3_npc_draw import relocation_offsets
    from v3_npc_clothing import guard_incoming
    from v3_holiday_state import RAM as STATE_RAM
    from v3_decoration_actor import SERVICES,CONTEXT,DATA_END
    import v3_physical_resources as physical
    del blob
    e=copy.deepcopy(prior['equipment_resources']);items=e['holiday_items']
    if items.get('pickup') or items['ready_mask'] or items['selected']:
        raise ValueError('Event pickup requires the complete inactive item batch, once')
    packet=e['holiday_state']['packet'];p=packet['physical'];raw=bytearray(base[p:p+packet['bytes']])
    if (sha256(raw)!=packet['sha256'] or sha256(raw[RAM-STATE_RAM:END-STATE_RAM])!=items['sha256'] or
            any(raw[PICKUP_RAM-STATE_RAM:END-STATE_RAM])):
        raise ValueError('Changed shared pickup reservation or retained item resources')
    files=by_vrom(base);player=files[PLAYER_VROM].extract(base);rel=files[PLAYER_RELOC].extract(base)
    # Player-action metadata predates the installed creature/UI consumers.
    # Guard the complete current owner, not that earlier component's receipt.
    input_player=sha256(player);input_reloc=sha256(rel)
    if (input_player!='97577813f1e3fba1fdb6e28d4876fcbdfe6760b1c86e2f91eea9e1e4c785ba01' or
            input_reloc!='1c750e3767eb8b4d8bb58079555fe32698a7cd7b47d2d1cd85e2b4e5adc89cad'):
        raise ValueError('Changed complete player owner')
    for a,b,digest in PICKUP_PLAYER:
        if sha256(player[a-PLAYER_RAM:b-PLAYER_RAM])!=digest:raise ValueError('Changed complete native pickup consumer')
    bindings={}
    for symbol,a,b,digest in PICKUP_NATIVE:
        if sha256(core[a-CODE_RAM:b-CODE_RAM])!=digest:raise ValueError('Changed native pickup dependency: '+symbol)
        bindings[symbol]=a
    controllers=e['npc_extra']['events']['decorations']['controllers'];previous=controllers['code']['symbols']
    bindings.update(af_holiday_item_type=items['code']['symbols']['af_holiday_item_type'],
        af_holiday_pickup_prior_resolve=previous['af_decor_actor_resolve'],af_decor_actor_context=CONTEXT,
        af_holiday_pickup_active=0x80136FD8,af_holiday_pickup_player_ctor=0x80143900)
    text=pickup_text(base,prior,output);text['hooks']=patch_bounds(core,text['first_id'],1)
    code,compiled=compile_part('holiday_pickup',output/'holiday-pickup',
        extra_sources=('overlays/v3/holiday_pickup.S',),defines=(f'AF_HOLIDAY_FORK_REFUSAL={text["first_id"]}',),
        link_symbols=bindings)
    if PICKUP_RAM+len(code)>END:raise ValueError('Pickup code overlaps retained models')
    raw[PICKUP_RAM-STATE_RAM:PICKUP_RAM-STATE_RAM+len(code)]=code
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    functions=[]
    for at,name,n in ((0x16DBE0,'Player_actor_CheckAndRequest_main_pickup_all',0x45C),
            (0x17D7CC,'Player_actor_request_main_pickup_jump',0xA0),
            (0x17D86C,'Player_actor_setup_main_Pickup_jump',0x198),
            (0x167240,'Player_actor_putin_item_layer2',0x58),
            (0x174F10,'Player_actor_Refuse_pickup_demo_ct',0x9C)):
        body,receipt=source.function(at)
        if len(body)!=n or receipt['symbol']!=name:raise ValueError('Changed complete source pickup controller')
        functions.append(receipt)
    changes={};hooks=[];removed=[]
    def patch_owner(vrom,rv,ram,plans):
        data=bytearray(files[vrom].extract(base));reloc=bytearray(files[rv].extract(base))
        sections=struct.unpack_from('>5I',reloc);words=list(struct.unpack_from('>'+str(sections[4])+'I',reloc,20))
        locations={sum(sections[:(w>>30)-1])+(w&0xFFFFFF):w for w in words}
        slots=relocation_offsets(reloc,len(data));deleted=[]
        guard_incoming(data,sections[0],ram,[(address-ram,4) for address,_,_,_ in plans])
        for address,before,target,internal in plans:
            at=address-ram
            if u32(data,at)!=before or ((at in slots)!=internal):raise ValueError('Changed pickup call/relocation')
            if internal:
                word=locations[at]
                if word>>24!=0x44:raise ValueError('Pickup call is not a text JAL relocation')
                deleted.append(word)
            after=jump(target,link=True);struct.pack_into('>I',data,at,after)
            hooks.append(dict(vrom=vrom,ram=ram,address=address,before=f'{before:08x}',after=f'{after:08x}',
                removed_relocation=locations.get(at)))
        kept=[w for w in words if w not in deleted];struct.pack_into('>I',reloc,16,len(kept))
        reloc[20:20+len(words)*4]=struct.pack('>'+str(len(kept))+'I',*kept)+bytes(4*len(deleted))
        changes[vrom]=bytes(data);changes[rv]=bytes(reloc)
        removed.extend(dict(vrom=rv,word=w) for w in deleted)
        return sha256(data),sha256(reloc),len(deleted)
    symbols=compiled['symbols']
    player_sha,rel_sha,count=patch_owner(PLAYER_VROM,PLAYER_RELOC,PLAYER_RAM,[
        (0x808BC1E0,jump(0x800B1C84,link=True),symbols['af_holiday_pickup_entry'],False),
        (0x808C8398,jump(0x808B55E8,link=True),symbols['af_holiday_pickup_insert'],True)])
    e['player_actions'].update(owner_sha256=player_sha,relocation_sha256=rel_sha,
        removed_relocations=e['player_actions']['removed_relocations']+count)
    e['player_motion'].update(owner_sha256=player_sha,reloc_sha256=rel_sha)
    for spec,digest,row in zip(OWNERS,GROUND_CLASSIFY,e['ground_categories']['owners']):
        data=files[spec['vrom']].extract(base)
        if sha256(data[0x5AE0:0x5E14])!=digest or u32(data,0x5D88)!=0x8FA400E8:
            raise ValueError('Changed complete seasonal foreground loop')
        image_sha,rel_sha,_=patch_owner(spec['vrom'],spec['reloc'],spec['ram'],[
            (spec['ram']+0x5D84,jump(spec['ram']+0x5A6C,link=True),symbols['af_holiday_pickup_ground'],True)])
        row.update(output_sha256=image_sha,output_reloc_sha256=rel_sha)
    at=SERVICES-STATE_RAM
    if struct.unpack_from('>5I',raw,at)!=(7,previous['af_decor_actor_demo'],previous['af_decor_actor_resolve'],
            previous['af_decor_actor_effect'],0):raise ValueError('Changed decoration service directory')
    struct.pack_into('>I',raw,at+8,symbols['af_holiday_pickup_resolve'])
    struct.pack_into('>I',raw,at+16,symbols['af_holiday_pickup_pocket'])
    # Providers are connected, but HARVEST admission remains closed until the
    # event/item profile and saved-item validators are bound.
    controllers['data']['sha256']=sha256(raw[CONTEXT-STATE_RAM:DATA_END-STATE_RAM])
    items['sha256']=sha256(raw[RAM-STATE_RAM:END-STATE_RAM])
    items['pickup']=dict(code=compiled,ram=PICKUP_RAM,bytes=len(code),hooks=hooks,removed_relocations=removed,
        input_player_sha256=input_player,input_player_relocation_sha256=input_reloc,
        native_player_functions=PICKUP_PLAYER,native_functions=PICKUP_NATIVE,source_functions=functions,
        text=text,service_ready=7,source_tick_removal=2,ground_variants=4,installed=True,
        saved_format_changed=False,native_execution_verified=False,
        source_files={str(path.relative_to(ROOT)):sha256(path.read_bytes()) for path in (
            ROOT/'local/ac-decomp/src/game/m_player_main_pickup_jump.c_inc',
            ROOT/'local/ac-decomp/src/game/m_player_main_refuse_pickup.c_inc',
            ROOT/'local/ac-decomp/src/bg_item/bg_item_common.c_inc')})
    items['pending']=['event activation and exercise-card menu','profile/save admission','connected native gameplay']
    controllers['pending']=['fishing record/text consumers and profile-gated Harvest admission',
        'shared event activation, attendance, calendar choice, and native execution']
    resources=copy.deepcopy(prior['physical_resources']);physical.verify(base,resources)
    record=next(r for r in resources if r['id']==packet['id']);record['sha256']=sha256(raw)
    e['holiday_state']['packet']=dict(packet,sha256=sha256(raw),crc32=zlib.crc32(raw))
    e['npc_extra']['sources'].update({s:sha256((ROOT/s).read_bytes()) for s in PICKUP_SOURCES})
    write_new(output/'holiday-pickup.json',(json.dumps(items['pickup'],indent=2)+'\n').encode())
    write_new(output/'holiday-pickup-packet.bin',raw)
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
