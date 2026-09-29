"""Connect the shared carried-item resource batch to bounded native readers.

Readiness remains off until inventory actions, persistence, and optional
selection are connected. Retain all existing event controls and native items.
"""
import copy
import json
import struct
import zlib

from aflib import CODE_RAM,by_vrom,sha256,u32
from apply_translation import write_new
from v3_asset_loader import ROOT,MODULE_RAM,compile_part
from v3_furniture_pipeline import Source
from v3_import_storage import jump
from v3_registry import CARRIED_ITEMS,CARRIED_ITEM_CATEGORIES,CARRIED_ITEM_REGISTRY_VERSION,CARRIED_PAPER_STYLE

RAM,TABLE,ICON,ART,PAPER,END=0x80771000,0x80773800,0x80774000,0x80776000,0x80777000,0x80778000
BITMAP=0x804AA250
GUARD=b'AFV3CARRIEDGUARD'
SOURCES=('tools/v3_carried_runtime.py','tools/v3_carried_items.py','tools/v3_category_runtime.py','tools/v3_asset_loader.py',
    'tools/v3_item_categories.py','tools/v3_registry.py','tools/v3_furniture_install.py',
    'tools/v3_room_goods.py','tools/v3_creature_items.py','tools/v3_holiday_selection.py','tools/v3_submenu_tables.py',
    'tools/v3_furniture_capacity.py','overlays/v3/carried_menu.c','overlays/v3/carried_actions.c',
    'overlays/v3/carried_items.c','overlays/v3/carried_items.h',
    'overlays/v3/carried_items.ld','overlays/v3/creature_icon.S',
    'overlays/v3/item_categories.c','overlays/v3/ground_categories.c','translations/provenance.json')
STORAGE_SOURCES=('overlays/v3/console_storage.c','overlays/v3/console_storage.h',
    'overlays/v3/save_compressed.c','overlays/v3/save_compressed.h',
    'overlays/v3/holiday_cards.c','overlays/v3/holiday_cards.h',
    'overlays/v3/holiday_item_storage.ld','overlays/v3/carried_collection.c',
    'overlays/v3/carried_catalogue.c','overlays/v3/carried_catalogue.ld')


def native_identities(core):
    """Verify actual short native tables, not donor enums or apparent holes."""
    expected={0:bytes([17]*64),5:bytes.fromhex('160d0d0d0d0d0d0d0d0d0d0d0d09151515141716191818181919181a0e0b'),
        8:bytes((1,5,4,3,2,6,17)),9:bytes([17]*10),13:bytes([18]*32)}
    rows=[]
    for group,data in expected.items():
        ram=u32(core,0x8010B334-CODE_RAM+group*4);at=ram-CODE_RAM
        if not 0<=at<=len(core)-len(data) or core[at:at+len(data)]!=data:
            raise ValueError('Changed native carried item table; preserve its identities')
        rows.append(dict(group=group,ram=ram,bytes=len(data),sha256=sha256(data)))
        if any(item>>8==0x20+group and item&255<len(data) for item in CARRIED_ITEMS.values()):
            raise ValueError('Carried import replaces an original native identity')
    if (CARRIED_ITEMS[0x2003]!=0x2040 or CARRIED_ITEMS[0x2901]!=0x290A or CARRIED_PAPER_STYLE!=64):
        raise ValueError('Changed stable additive paper/plant identity contract')
    return rows


def letter_window(base,core,menu,paper,symbols):
    """Extend the existing complete paper tables; retain original drawing code."""
    from v3_submenu_tables import Owner,resize
    files=by_vrom(base);vrom,reloc,ram=0x3B60000,0x3B70000,0x80888E90
    owner=Owner(files[vrom].extract(base),files[reloc].extract(base),ram)
    bg,lines,colours=0x8088A7A0,0x8088A8A0,0x8088AAA4
    if (sha256(owner.original)!='5edd7193c494609f28228dca4bf2ca0582cba831e67aec6b5b2cb08df2a89098' or
            sha256(owner.relocation)!='e13aa96c88da53a1e218a9f9ac6813204412662dda91a860d2a2aaa29ec7a447' or
            any(u32(owner.original,bg-ram+4*i)>>24!=12 for i in range(64)) or
            any(u32(owner.original,lines-ram+4*i)>>24 not in (0,12) for i in range(64))):
        raise ValueError('Changed complete native letter owner or stationery tables')
    binding=paper['bindings'][0]
    for address,label in ((bg,'background'),(lines,'lines')):
        model=binding[label];target=(PAPER&0x1FFFFFFF)+paper['offsets'][model]
        owner.table(address,64,4,struct.pack('>I',target),pointer_offsets=(),expected_references=1)
    owner.table(colours,64,4,bytes(binding['text_rgba']),pointer_offsets=(),expected_references=1)
    owner.patch(0x8088A760,jump(0x8088A604,link=True),
        jump(symbols['af_carried_board_load'],link=True),remove_relocation=True)
    data,rel,receipt=owner.finish()
    metadata=resize(menu,core,vrom=vrom,ram=ram,offset=0x2B90,before=len(owner.original),after=len(data))
    receipt.update(vrom=vrom,reloc=reloc,ram=ram,native_styles=64,additional_style=64,
        loader=symbols['af_carried_board_load'],ordinary_rendering_verified=False)
    changes={vrom:data,reloc:rel}
    resizes=[dict(vrom=v,previous_bytes=files[v].size,previous_sha256=sha256(files[v].extract(base)),
        bytes=len(d),sha256=sha256(d)) for v,d in changes.items() if len(d)!=files[v].size]
    return changes,receipt,[metadata],resizes


def install(base, prior, blob, core, module, output, directory):
    if prior['equipment_resources'].get('carried_items'):
        if prior['equipment_resources']['carried_items'].get('field_creatures'):
            carried=prior['equipment_resources']['carried_items']
            if carried.get('interactions') and not carried.get('spawning'):
                return install_creature_spawns(base,prior,output,directory)
            if carried.get('spawning') and not carried.get('quest'):
                return install_quest_state(base,prior,core,output,directory)
            if carried.get('quest') and not carried['quest'].get('manager'):
                return install_quest_manager(base,prior,core,output,directory)
            return install_interactions(base,prior,core,output,directory)
        if prior['equipment_resources']['carried_items'].get('eating'):
            return install_creature_field(base,prior,blob,output,directory)
        if prior['equipment_resources']['carried_items'].get('storage'):
            return install_field_actions(base,prior,output,directory)
        if prior['equipment_resources']['carried_items'].get('actions'):
            return install_storage(base,prior,blob,core,output,directory)
        return install_actions(base,prior,blob,core,output,directory)
    from v3_carried_items import FORMAT,records,pocket_icons,paper_art
    from v3_item_categories import discover,checked_art
    from v3_category_runtime import rebase_art,append_categories
    from v3_furniture_pipeline import assemble_models
    from v3_console_disk_install import reservations
    from v3_furniture_icon import VROM as MENU,RAM as MENU_RAM
    import v3_physical_resources as physical
    e=copy.deepcopy(prior['equipment_resources']);old_items=e['holiday_items']
    if e.get('carried_items') or not e['npc_extra']['events'].get('selection'):
        raise ValueError('Carried integration requires the connected event base and no existing batch')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    directory=directory.resolve();prepared=json.loads((directory/'items.json').read_bytes())
    rows,receipt=records(source,ROOT/'build/item-identity-megasheet.xlsx',prepared['installed_imports'])
    if (prepared['format']!=FORMAT or prepared['rows']!=rows or
            any(prepared[k]!=json.loads(json.dumps(v)) for k,v in receipt.items()) or
            {int(r['donor_item_id'],16) for r in rows}!=set(CARRIED_ITEMS)):
        raise ValueError('Prepared carried batch differs from complete source states')
    identities=native_identities(core)
    if any(a<END and RAM<b for a,b in reservations(prior)):
        raise ValueError('Carried reservation overlaps retained Expansion Pak data')
    events=e['npc_extra']['events'];festival=events['festivals'];old=festival['packet']
    if not old['ram']<old['ram']+old['bytes']<=RAM<END<=0x807DA800:
        raise ValueError('Carried batch does not extend the last loaded shared packet')
    raw=bytearray(base[old['physical']:old['physical']+old['bytes']])
    if sha256(raw)!=old['sha256']:raise ValueError('Changed retained festival packet')
    raw.extend(bytes(END-old['ram']-len(raw)))
    hooks=[dict(h,prior=h['target'],before=h['after'],symbol='af_carried_'+h['kind'])
           for h in old_items['hooks']]
    if {h['kind'] for h in hooks}!={'name','type','price','display','pocket'}:
        raise ValueError('Incomplete shared carried predecessor chain')
    bindings={'af_carried_prior_'+h['kind']:h['prior'] for h in hooks}
    bindings.update(af_carried_prior_icon=old_items['code']['symbols']['af_holiday_icon_hook'],
        af_carried_event_type=old_items['code']['symbols']['af_holiday_item_type'])
    code,compiled=compile_part('carried_items',output/'carried-items',
        extra_sources=('overlays/v3/creature_icon.S','overlays/v3/ground_categories.c','overlays/v3/carried_menu.c'),
        defines=('AF_CARRIED_ICON=1','AF_V3_GROUND_PREPARE_ONLY=1','AF_V3_CATEGORY_COUNT=71',
            f'AF_V3_GROUND_CATEGORY_FLAGS=0x{BITMAP:X}u'),link_symbols=bindings)
    icons,icon_receipt=pocket_icons(source,rows,ram=ICON)
    old_icons,old_icon_receipt=pocket_icons(source,rows)
    if ((directory/'icons.bin').read_bytes()!=old_icons or
            prepared['icons']!=json.loads(json.dumps(old_icon_receipt))):
        raise ValueError('Changed complete carried pocket resources')
    parents=sorted({r['parent_item_id'] for r in rows});table=bytearray(struct.pack('>8I',0x41464350,1,len(rows),32,0,0,0,0))
    for row,icon in zip(rows,icon_receipt['bindings']):
        item=CARRIED_ITEMS[int(row['donor_item_id'],16)];parent=CARRIED_ITEMS[int(row['parent_item_id'],16)]
        family=parents.index(row['parent_item_id']);category=CARRIED_ITEM_CATEGORIES[row['source_category']]
        name=row['name'].encode('ascii').ljust(16,b' ')
        if len(name)!=16 or sha256(name)!=row['name_sha256']:raise ValueError('Changed complete official carried name')
        row.update(native_item_id=f'{item:04X}',native_parent_id=f'{parent:04X}',family=family,
            native_category=category,icon=icon['address'])
        table.extend(struct.pack('>3H4BHI',item,int(row['donor_item_id'],16),parent,family,row['state_index'],
            category,0,row['price'],icon['address'])+name)
    for address,data,limit in ((RAM,code,TABLE),(TABLE,table,ICON),(ICON,icons,ART)):
        if address+len(data)>limit:raise ValueError('Carried resources exceed their fixed reservations')
        raw[address-old['ram']:address-old['ram']+len(data)]=data
    expected={r['source_category']:r for r in discover(source,prepared['rows'],require_ground=False)['rows']}
    artwork=[];reused=[];cursor=ART
    for row in prepared['categories']['objects']:
        category=row['source_category'];reference=expected.pop(category)
        if any(row[k]!=json.loads(json.dumps(v)) for k,v in reference.items()):
            raise ValueError('Changed complete carried model binding')
        data,_=checked_art(source,directory/'categories',row)
        native=CARRIED_ITEM_CATEGORIES[category]
        prior_art=[r for r in e['item_categories']['objects'] if r['native_category']==native]
        if prior_art:
            if len(prior_art)!=1 or prior_art[0]['source_category']!=category or prior_art[0]['object_sha256']!=row['object_sha256']:
                raise ValueError('Carried reuse differs from installed category resources')
            reused.append(dict(source_category=category,native_category=native,ram=prior_art[0]['ram']))
            continue
        row=copy.deepcopy(row);data,fixes=rebase_art(data,row,cursor)
        if cursor+len(data)>PAPER:raise ValueError('Carried graphics overlap stationery')
        raw[cursor-old['ram']:cursor-old['ram']+len(data)]=data
        row.update(ram=cursor,native_category=native,installed_sha256=sha256(data),pointer_relocations=fixes,
            source_mapping=category not in (17,18),ground_installed=bool(row['ground_descriptors']))
        artwork.append(row);cursor+=len(data)
    if expected:raise ValueError('Missing complete carried category')
    paper,paper_receipt=paper_art(source,prepared['rows']);p=prepared['stationery']
    if any(p[k]!=json.loads(json.dumps(v)) for k,v in paper_receipt.items()):raise ValueError('Changed stationery bindings')
    file=(directory/p['file']).resolve()
    if not file.is_relative_to(directory):raise ValueError('Stationery escapes prepared directory')
    paper_data=file.read_bytes()
    if (sha256(paper_data)!=p['sha256'] or p['resources']!=paper[2] or
            (directory/'stationery/commands.c').read_text()!=paper[5]):raise ValueError('Changed complete stationery resources')
    sections={m['layer']:paper_data[m['native_offset']:m['native_offset']+m['bytes']] for m in p['models']}
    rebuilt,offsets,models,_=assemble_models(paper,sections)
    if rebuilt!=paper_data or models!=p['models'] or offsets!=p['offsets'] or PAPER+len(rebuilt)>END-16:
        raise ValueError('Incomplete stationery assembly or reservation')
    installed_paper,paper_fixes=rebase_art(rebuilt,dict(resources=p['resources'],compiled_models=p['models']),PAPER)
    raw[PAPER-old['ram']:PAPER-old['ram']+len(installed_paper)]=installed_paper;raw[-16:]=GUARD
    changes=append_categories(base,e,blob,core,output,artwork,qualified=True,
        query_defines=(f'AF_V3_CARRIED_CATEGORY_QUERY=0x{compiled["symbols"]["af_carried_category"]:X}u',))
    if e['item_categories']['ground_bitmap']['ram']!=BITMAP:raise ValueError('Changed shared ground bitmap reservation')
    # Keep all existing seasonal entry addresses and trampolines. Redirect only
    # their common constructor-time descriptor preparation to the new mask reader.
    ground=e['ground_categories'];at=e['blob_offset']+ground['code_offset'];before=bytes(blob[at:at+8])
    if sha256(blob[at:at+ground['code']['bytes']])!=ground['code']['sha256']:
        raise ValueError('Changed installed ground descriptor builder')
    after=struct.pack('>2I',jump(compiled['symbols']['af_v3_ground_prepare']),0);blob[at:at+8]=after
    ground['code']['sha256']=sha256(blob[at:at+ground['code']['bytes']])
    ground['carried_prepare']=dict(address=e['ram']+ground['code_offset'],before=before.hex(),after=after.hex(),
        target=compiled['symbols']['af_v3_ground_prepare'])
    e.update(sha256=sha256(blob[e['blob_offset']:e['blob_offset']+e['bytes']]),
        crc32=zlib.crc32(blob[e['blob_offset']:e['blob_offset']+e['bytes']]))
    for h in hooks:
        if h['address']>=0x80460000:owner,origin=blob,0x80460000
        elif h['address']>=MODULE_RAM:owner,origin=module,MODULE_RAM
        else:owner,origin=core,CODE_RAM
        at=h['address']-origin
        if owner[at:at+8]!=bytes.fromhex(h['before']):raise ValueError('Changed shared carried reader: '+h['kind'])
        target=compiled['symbols'][h['symbol']];after=struct.pack('>2I',jump(target),0)
        owner[at:at+8]=after;h.update(target=target,after=after.hex())
    menu=bytearray(by_vrom(base)[MENU].extract(base));at=0x8085C968-MENU_RAM
    before=bytes.fromhex(old_items['icon_hook']['after']);after=struct.pack('>2I',jump(compiled['symbols']['af_carried_icon_hook']),0)
    if menu[at:at+8]!=before:raise ValueError('Changed carried pocket-icon predecessor')
    menu[at:at+8]=after
    letter_changes,letter,menu_allocations,resizes=letter_window(base,core,menu,p,compiled['symbols'])
    changes.update(letter_changes);changes[MENU]=bytes(menu);e['pocket_icons']['owner_sha256']=sha256(menu)
    if len(raw)!=END-old['ram']:
        raise ValueError(f'Carried packet assembly changed its reserved extent: {len(raw):X} != {END-old["ram"]:X}')
    resources=copy.deepcopy(prior['physical_resources'])
    try:replacement=physical.grow_backwards(base,resources,old['id'],bytes(raw))
    except ValueError as error:
        if str(error)!='No checked adjacent space for complete physical resource growth':raise
        replacement=physical.allocate(base,resources,bytes(raw),'carried-festivals-GAFE01-r0',best_fit=True)
    resource={k:replacement[k] for k in ('id','physical','bytes','sha256')}
    if resource['id']==old['id']:
        resources[resources.index(next(r for r in resources if r['id']==old['id']))]=resource
    else:resources.append(resource)
    packet=dict(resource,ram=old['ram'],crc32=zlib.crc32(raw),storage='physical-ROM')
    festival['packet']=packet;festival['carried_packet_extension']=dict(previous_bytes=old['bytes'],end=END,
        bytes=len(raw)-old['bytes'])
    from v3_furniture_install import relocate_resource_plan
    growth=[];files=by_vrom(base)
    for vrom,data in letter_changes.items():
        _,allocation=relocate_resource_plan(base,files,vrom,data,minimum_physical=0x100000,
            reservations=resources+growth,append_only=False,allow_compressed=True)
        growth.append(allocation)
    sources={s:sha256((ROOT/s).read_bytes()) for s in SOURCES}
    e['carried_items']=dict(format='AFV3-CARRIED-ITEMS-1',registry_version=CARRIED_ITEM_REGISTRY_VERSION,
        rows=rows,parent_count=len(parents),state_count=len(rows),native_tables=identities,
        code=compiled,ram=RAM,bytes=END-RAM,sha256=sha256(raw[RAM-old['ram']:]),
        table_ram=TABLE,table_bytes=len(table),table_sha256=sha256(table),icons=icon_receipt,
        artwork=artwork,reused_artwork=reused,paper=dict(p,ram=PAPER,native_style=CARRIED_PAPER_STYLE,
            installed_sha256=sha256(installed_paper),pointer_relocations=paper_fixes,letter_window=letter),
        menu_allocations=menu_allocations,
        hooks=hooks,icon_hook=dict(vrom=MENU,address=0x8085C968,before=before.hex(),after=after.hex()),
        packet=packet,previous_packet=old,ready_mask=0,selected_mask=0,additional_resident_bytes=len(raw)-old['bytes'],
        prepared=str(directory.relative_to(ROOT)),sources=sources,saved_format_changed=False,
        native_execution_verified=False,pending=['inventory/menu behaviours','stationery catalogue and collection',
            'saved identities and ownership','independent optional selection'])
    write_new(output/'carried-items.json',(json.dumps(e['carried_items'],indent=2)+'\n').encode())
    write_new(output/'carried-packet.bin',raw)
    return e,changes,dict(physical_resources=resources,runtime_owner_resizes=resizes,
        resource_growth=growth),[(replacement,bytes(raw))]


ACTION_SOURCES=(
    (0x287138,'mTG_1catch_proc','f4630352fe9abfdaa30c012642a1808ad92d08c7b2b55b1271fb001c37ff4c0d'),
    (0x28A884,'mTG_select_tag_decide_item_normal','279e89153d01784f41aeb7e602f1f5709482240ec4042ab471a39e16f89b529c'),
    (0x26DC70,'mHD_prepare_drop_paper','dda8e1cb9c8d5008205b9a9aa729dee1c330b07df24af16b021ba9cc0fee569a'),
    (0x26DB74,'mHD_prepare_drop_wisp','e55621c1c295fc1c5c6178f344f401ac82de9110e887d61cff0d10266930a715'),
    (0x26DD84,'mHD_drop_item2','a01981cdb2e32bc70b64ad11faf837f5bfa21d388507ab12b214490461fce696'),
    (0x255034,'mBD_move_Obey','676cb429a71ca6b3488c21944927704136cabcf4a59fce103e7647a13ea4a8f7'))


def install_actions(base,prior,blob,core,output,directory):
    """Continue the installed shared batch, without recompiling any artwork."""
    from v3_submenu_tables import Owner,resize
    from v3_furniture_install import relocate_resource_plan
    from v3_npc_draw import relocation_offsets
    from v3_furniture_icon import VROM as MENU
    import v3_physical_resources as physical
    del blob
    e=copy.deepcopy(prior['equipment_resources']);d=e['carried_items'];old=d['packet']
    if d.get('actions') or d['ready_mask'] or d['selected_mask'] or directory.resolve()!=ROOT/d['prepared']:
        raise ValueError('Carried actions require the checked inactive prepared batch')
    raw=bytearray(base[old['physical']:old['physical']+old['bytes']]);start=RAM-old['ram']
    previous=d['code']
    if (sha256(raw)!=old['sha256'] or raw[-16:]!=GUARD or old['ram']+len(raw)!=END or
            sha256(raw[start:])!=d['sha256'] or
            sha256(raw[start:start+previous['bytes']])!=previous['sha256'] or
            any(raw[start+previous['bytes']:TABLE-old['ram']])):
        raise ValueError('Changed complete carried packet or code reservation')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    donors=[]
    for at,name,digest in ACTION_SOURCES:
        _,receipt=source.function(at)
        if receipt['symbol']!=name or receipt['sha256']!=digest:
            raise ValueError('Changed complete donor stack/action function: '+name)
        donors.append(receipt)
    controls=e['holiday_items']['controls'];links=dict(previous['link_symbols'])
    links['af_carried_prior_menu']=controls['code']['symbols']['af_hi_menu_type']
    first=controls['tag']['tables'][0]['count']
    if first!=47:raise ValueError('Changed complete native action-menu count')
    code,compiled=compile_part('carried_items',output/'carried-items',
        extra_sources=('overlays/v3/creature_icon.S','overlays/v3/ground_categories.c',
            'overlays/v3/carried_menu.c','overlays/v3/carried_actions.c'),
        defines=tuple(f[2:] for f in previous['flags'] if f.startswith('-D'))+
            (f'AF_CARRIED_PAPER_MENUS={first}',),link_symbols=links)
    if (len(code)>TABLE-RAM or code[:previous['bytes']]!=raw[start:start+previous['bytes']] or
            any(compiled['symbols'].get(k)!=v for k,v in previous['symbols'].items() if k.startswith('af_'))):
        raise ValueError('Carried action extension moves or changes a retained reader')
    symbols=compiled['symbols'];raw[start:TABLE-old['ram']]=code.ljust(TABLE-RAM,b'\0')
    files=by_vrom(base);tag=Owner(files[0x3950000].extract(base),files[0x3960000].extract(base),0x8086F310)
    if (sha256(tag.original)!=controls['tag']['owner_sha256'] or
            sha256(tag.relocation)!=controls['tag']['relocation_sha256']):
        raise ValueError('Changed current complete native action owner')
    table=controls['tag']['tables'][0]['address'];extra=bytearray();menus=[]
    grab_one=tag.append(tag.original[0x8087999C-tag.ram:0x808799AC-tag.ram]+
        struct.pack('>I',symbols['af_carried_grab_one']))
    if tag.data[grab_one-tag.ram:grab_one-tag.ram+16]!=b'Grab One        ':
        raise ValueError('Changed complete translated native stack action')
    # Reuse every existing word, handler, and cancellation position. The one
    # additional choice uses the new shared splitter, not the native ticket code.
    for index in (3,4,15,17):
        pointer,count=struct.unpack_from('>II',tag.original,table-tag.ram+index*8)
        words=list(struct.unpack_from('>'+str(count)+'I',tag.original,pointer-tag.ram))
        if words[0]!=0x80879834 or words[1]!=0x80879848 or words[-1]!=0x80879898:
            raise ValueError('Changed complete paper-menu word order')
        words.insert(1,grab_one)
        address=tag.append(struct.pack('>'+str(len(words))+'I',*words),
            pointers=tuple(range(0,len(words)*4,4)))
        extra.extend(struct.pack('>II',address,len(words)))
        menus.append(dict(index=first+len(menus),original_index=index,words=words,address=address))
    tag.table(table,first,8,bytes(extra),expected_references=16)
    tag.patch(0x80875834,jump(links['af_carried_prior_menu'],link=True),
        jump(symbols['af_carried_menu_type'],link=True))
    tag_data,tag_reloc,tag_receipt=tag.finish()
    letter=Owner(files[0x3B60000].extract(base),files[0x3B70000].extract(base),0x80888E90)
    binding=d['paper']['letter_window']
    if (sha256(letter.original)!=binding['owner_sha256'] or sha256(letter.relocation)!=binding['relocation_sha256']):
        raise ValueError('Changed complete extended stationery window')
    letter.patch(0x80889434,jump(0x800B8B08,link=True),jump(symbols['af_carried_consume_paper'],link=True))
    letter_data,letter_reloc,letter_receipt=letter.finish()
    # Hand still uses its native text/data/BSS sections, unlike flattened tag and
    # letter owners. Preserve all sizes and remove only the redirected JAL fixup.
    hand=bytearray(files[0x7829E0].extract(base));rel=bytearray(files[0x784DE0].extract(base))
    if (sha256(hand)!='bec1d8b6c099be250fafc9031e8b1b59079eec8c0f13ec06cf1d33b519de8097' or
            sha256(rel)!='9f37119751663b60db3d6b5eae64143f3b862b4fdd2b751d08d701bdb689a972'):
        raise ValueError('Changed complete current hand owner')
    at=0x8087B184-0x8087A330;slots=relocation_offsets(rel,len(hand))
    count=u32(rel,16);words=list(struct.unpack_from('>'+str(count)+'I',rel,20));word=0x44000000|at
    if at not in slots or word not in words or u32(hand,at)!=jump(0x8087AC90,link=True):
        raise ValueError('Changed hand stack/drop call or relocation')
    before=u32(hand,at);after=jump(symbols['af_carried_drop_stack'],link=True)
    struct.pack_into('>I',hand,at,after);words.remove(word);struct.pack_into('>I',rel,16,len(words))
    rel[20:20+count*4]=struct.pack('>'+str(len(words))+'I',*words)+bytes(4)
    parent=bytearray(files[MENU].extract(base))
    allocation=resize(parent,core,vrom=0x3950000,ram=tag.ram,offset=0x2CB0,
        before=len(tag.original),after=len(tag_data))
    d['menu_allocations'].append(allocation);e['pocket_icons']['owner_sha256']=sha256(parent)
    changes={0x3950000:tag_data,0x3960000:tag_reloc,0x3B60000:letter_data,0x3B70000:letter_reloc,
        0x7829E0:bytes(hand),0x784DE0:bytes(rel),MENU:bytes(parent)}
    resizes=[dict(vrom=v,previous_bytes=files[v].size,previous_sha256=sha256(files[v].extract(base)),
        bytes=len(data),sha256=sha256(data)) for v,data in changes.items() if len(data)!=files[v].size]
    resources=copy.deepcopy(prior['physical_resources']);resource=dict(id=old['id'],physical=old['physical'],
        bytes=len(raw),sha256=sha256(raw))
    if resource['id'] not in {r['id'] for r in resources}:raise ValueError('Missing owned carried physical packet')
    resources[resources.index(next(r for r in resources if r['id']==old['id']))]=resource
    packet=dict(resource,ram=old['ram'],crc32=zlib.crc32(raw),storage='physical-ROM')
    growth=[]
    for row in resizes:
        v=row['vrom'];_,record=relocate_resource_plan(base,files,v,changes[v],minimum_physical=0x100000,
            reservations=resources+growth,append_only=False,allow_compressed=True)
        growth.append(record)
    e['npc_extra']['events']['festivals']['packet']=packet
    d.update(code=compiled,sha256=sha256(raw[start:]),packet=packet,
        sources={s:sha256((ROOT/s).read_bytes()) for s in SOURCES})
    d['actions']=dict(donors=donors,menus=menus,tag=tag_receipt,letter=letter_receipt,
        hand=dict(vrom=0x7829E0,reloc=0x784DE0,ram=0x8087A330,address=0x8087B184,
            before=before,after=after,removed_relocation=word,owner_sha256=sha256(hand),relocation_sha256=sha256(rel)),
        code_previous=previous,additional_resident_bytes=0,additional_menu_bytes=allocation['additional_pool_bytes'],
        native_execution_verified=False)
    write_new(output/'carried-items.json',(json.dumps(d,indent=2)+'\n').encode())
    write_new(output/'carried-packet.bin',raw)
    return e,changes,dict(physical_resources=resources,runtime_owner_resizes=resizes,
        resource_growth=growth),[(dict(resource,previous_sha256=old['sha256']),bytes(raw))]


def install_storage(base,prior,blob,core,output,directory):
    """Connect all carried profiles and paper collection in the actual save path."""
    from v3_console_disk_install import reservations
    from v3_holiday_selection import refresh_receipts
    import v3_physical_resources as physical
    e=copy.deepcopy(prior['equipment_resources']);d=e['carried_items'];old=d['packet']
    if (d.get('storage') or not d.get('actions') or d['ready_mask'] or d['selected_mask'] or
            directory.resolve()!=ROOT/d['prepared']):
        raise ValueError('Carried storage requires the checked inactive action integration')
    raw=bytearray(base[old['physical']:old['physical']+old['bytes']])
    if (sha256(raw)!=old['sha256'] or old['ram']+len(raw)!=END or raw[-16:]!=GUARD or
            sha256(raw[RAM-old['ram']:])!=d['sha256']):
        raise ValueError('Changed complete carried predecessor')
    storage=e['holiday_items']['controls']['storage'];previous=copy.deepcopy(storage['code'])
    prefix_packet=e['npc_extra']['events']['sky']['packet']
    prefix_sha=prefix_packet['sha256']
    prefix=bytearray(base[prefix_packet['physical']:prefix_packet['physical']+prefix_packet['bytes']])
    at=storage['ram']-prefix_packet['ram']
    if (sha256(prefix)!=prefix_packet['sha256'] or
            sha256(prefix[at:at+storage['bytes']])!=previous['sha256'] or
            storage['save_format']!=15 or storage['wire_version']!=2):
        raise ValueError('Changed complete predecessor save owner')
    clothing=copy.deepcopy(prior['clothing']);hooks=clothing['display']['readers']['collection_hooks']
    links=dict(previous['link_symbols'],AF_HI_STORAGE_RAM=END)
    for kind,h in zip(('record','owned'),hooks):
        links['af_carried_prior_'+kind]=h['target']
    for name in ('af_carried_category','af_carried_reserved'):
        links[name]=d['code']['symbols'][name]
    code,compiled=compile_part('holiday_item_storage',output/'carried-storage',
        primary_source='overlays/v3/console_storage.c',
        extra_sources=('overlays/v3/save_compressed.c','overlays/v3/holiday_cards.c',
            'overlays/v3/carried_collection.c'),
        defines=tuple(f[2:] for f in previous['flags'] if f.startswith('-D'))+('AF_V3_CARRIED_PROFILE=1',),
        link_symbols=links)
    end=END+len(code)+16
    if end>0x807DA800 or any(a<end and END<b for a,b in reservations(prior)):
        raise ValueError('Carried save owner overlaps retained memory')
    cat_ram=RAM+d['code']['bytes']
    cat_links=dict(AF_CARRIED_CATALOGUE_RAM=cat_ram,af_carried_owned=compiled['symbols']['af_carried_owned'],
        af_carried_prior_catalogue_bit=prior['room_surfaces']['menu']['code']['symbols']['af_v3_surface_catalogue_bit'])
    for name in ('af_carried_category','af_carried_price'):cat_links[name]=d['code']['symbols'][name]
    cat_code,cat_compiled=compile_part('carried_catalogue',output/'carried-catalogue',link_symbols=cat_links)
    cat_start=cat_ram-old['ram']
    if cat_ram+len(cat_code)>TABLE or any(raw[cat_start:cat_start+len(cat_code)]):
        raise ValueError('Catalogue adapter overlaps installed carried code or records')
    raw[cat_start:cat_start+len(cat_code)]=cat_code
    redirects=[];symbols=previous['symbols']
    bounds=sorted({v for v in symbols.values() if storage['ram']<=v<storage['ram']+storage['bytes']})
    for name,address in sorted(symbols.items()):
        if (not name.startswith(('af_v3_','af_holiday_cards_')) or
                not storage['ram']<=address<storage['ram']+storage['bytes']):continue
        target=compiled['symbols'].get(name)
        stop=next((a for a in bounds if a>address),storage['ram']+storage['bytes'])
        if target is None or not END<=target<end-16 or stop-address<8:
            raise ValueError('Missing or short public save entry: '+name)
        offset=address-prefix_packet['ram'];before=bytes(prefix[offset:offset+8])
        after=struct.pack('>2I',jump(target),0);prefix[offset:offset+8]=after
        redirects.append(dict(name=name,address=address,target=target,before=before.hex(),after=after.hex()))
    if len(redirects)!=30:raise ValueError('Changed public save/profile entry inventory')
    collection=[]
    for kind,h in zip(('record','owned'),hooks):
        offset=h['entry']-0x80460000;before=bytes.fromhex(h['after'])
        if not 0<=offset<=len(blob)-8 or blob[offset:offset+8]!=before:
            raise ValueError('Changed collection reader predecessor: '+kind)
        target=compiled['symbols']['af_carried_'+kind];after=struct.pack('>2I',jump(target),0)
        blob[offset:offset+8]=after
        collection.append(dict(kind=kind,address=h['entry'],prior=h['target'],target=target,
            before=before.hex(),after=after.hex()))
        h.update(carried_prior_target=h['target'],target=target,after=after.hex())
    raw.extend(code);raw.extend(GUARD)
    resources=copy.deepcopy(prior['physical_resources'])
    try:replacement=physical.grow_backwards(base,resources,old['id'],bytes(raw))
    except ValueError as error:
        if str(error)!='No checked adjacent space for complete physical resource growth':raise
        replacement=physical.allocate(base,resources,bytes(raw),'carried-save-GAFE01-r0',best_fit=True)
    resource={k:replacement[k] for k in ('id','physical','bytes','sha256')}
    if resource['id']==old['id']:
        resources[resources.index(next(r for r in resources if r['id']==old['id']))]=resource
    else:resources.append(resource)
    festival=e['npc_extra']['events']['festivals']
    festival['packet']=dict(resource,ram=old['ram'],crc32=zlib.crc32(raw),storage='physical-ROM')
    extension=festival['carried_packet_extension']
    extension.update(end=end,bytes=len(raw)-extension['previous_bytes'])
    refresh_receipts(e,resources,{prefix_packet['id']:prefix,resource['id']:raw})
    storage['sha256']=storage['code']['sha256']=sha256(prefix[at:at+storage['bytes']])
    storage.update(carried_profile_redirects=redirects,active_code=copy.deepcopy(compiled),
        save_format=16,wire_version=3)
    e['console_storage'].update(save_format=16,card_runtime=copy.deepcopy(compiled))
    d.update(bytes=end-RAM,sha256=sha256(raw[RAM-old['ram']:]),saved_format_changed=True,
        sources={s:sha256((ROOT/s).read_bytes()) for s in (*SOURCES,*STORAGE_SOURCES)},
        pending=['remaining field/gameplay behaviours','independent optional selection',
            'native gameplay/save verification'])
    d['storage']=dict(code=compiled,ram=END,bytes=len(code),sha256=sha256(code),end=end,
        previous_code=previous,redirects=redirects,collection_hooks=collection,
        save_format=16,wire_version=3,required_family_mask=127,paper_ownership_offset=9,
        retained_card_state=storage['retained_card_state'],retained_scratch=storage['retained_scratch'],
        additional_resident_bytes=end-END,native_save_reload_verified=False)
    changes,cat,resizes,growth=paper_catalogue(base,prior,e,core,cat_compiled,resources)
    updates={k:copy.deepcopy(prior[k]) for k in ('save_codec','room_surfaces')}
    updates['clothing']=clothing
    updates['save_codec'].update(format_version=16,active_storage_code=copy.deepcopy(compiled),
        card_storage_code=copy.deepcopy(compiled))
    clothing['save_extension'].update(format_version=16,active_storage_code=copy.deepcopy(compiled))
    clothing['save_extension']['legacy_formats_read']=list(dict.fromkeys(
        [*clothing['save_extension']['legacy_formats_read'],'AFS3-v15']))
    updates['room_surfaces']['save']['disk_format_version']=16
    updates['save_warning']=('Format-16 experimental saves require this or a newer compatible build. '
        'Compatible older saves migrate forward. Removing required imports, including any carried-item '
        'family, rejects the save. V2 and format-15-or-earlier V3 cannot load new saves. Keep backups. '
        'Native carried-item gameplay and save/reload remain unverified.')
    updates['physical_resources']=resources
    updates.update(catalogue=cat,runtime_owner_resizes=resizes,resource_growth=growth)
    prefix_resource=next(r for r in resources if r['id']==prefix_packet['id'])
    write_new(output/'carried-items.json',(json.dumps(d,indent=2)+'\n').encode())
    write_new(output/'carried-packet.bin',raw)
    return e,changes,updates,[(dict(prefix_resource,previous_sha256=prefix_sha),bytes(prefix)),
        (replacement,bytes(raw))]


def food_tables(source,owner,relocation,art,ram):
    """Extend the complete inventory food category, retaining native animation."""
    from v3_player_actions import native_references
    origin=0x8087D480
    donors=[]
    for at,n,digest in (
            (0x2725C0,696,'bb1a5b2bd58b5bd3c91c52d36c7628b7282fae2ed0c946951af35359d0267b96'),
            (0x26E17C,420,'ceeb4f2f9800be098509529e66734dbc1005001c4dfaed478b662d849b7197fd')):
        raw,receipt=source.function(at)
        if len(raw)!=n or sha256(raw)!=digest:raise ValueError('Changed complete source eating consumer')
        donors.append(receipt)
    if sha256(owner[0x8087E628-origin:0x8087E980-origin])!='339a6921992f11cdbe9ce6556e87a2bb6090e53ad7d291e5a6bfe796cf6b8afb':
        raise ValueError('Changed complete native food animation/drawing')
    sections=struct.unpack_from('>5I',relocation)
    if sections[:3]!=(15664,1008,160):raise ValueError('Changed native inventory sections')
    groups,absolute,rows,locations,_=native_references(owner,relocation,expected_sections=sections[:4])
    patched=bytearray(owner);data=bytearray();tables=[];removed=set();patches=[]
    for role,source_at,targets,native,checksum in (
            ('material',0x80118,(8980576,8992672,8997600,8996896,8994080,8991968,None,8985536,8989856),
             0x808814B0,'31f52e5b6fe5f42ee60e45f135cef0679ff8c758647d6b047100ba670dc2b318'),
            ('geometry',0x8013C,(8980648,8992744,8997672,8996968,8994152,8992040,8984192,8985608,8989928),
             0x808814D0,'6ffda60cc26ca41f2095f9d46131120e1be2d9746a50abe5af8ebdcb5664c608')):
        name,at,n=source.containing(source_at,exact=True)
        pointers={p-at:r for p,r in source.relocations.items() if at<=p<at+n}
        expected={i*4:(1,True,5,p) for i,p in enumerate(targets) if p is not None}
        if n!=36 or any(source.data[at:at+n]) or pointers!=expected:
            raise ValueError('Changed complete donor food drawing table')
        models=[m for m in art['compiled_models'] if m['layer']==role]
        if len(models)!=1 or models[0]['source_parts'][0]['donor_offset']!=targets[7]:
            raise ValueError('Food drawer does not use the complete installed carried model')
        model=models[0];target=(art['ram']+model['native_offset'])&0x1FFFFFFF
        old=owner[native-origin:native-origin+32]
        if sha256(old)!=checksum or any(native-origin+i in locations for i in range(0,32,4)):
            raise ValueError('Changed complete native food drawing table')
        # Donor order: seven original foods, coconut, then the original turnip.
        # Keep every original segmented pointer and the null candy material.
        raw=old[:28]+struct.pack('>I',target)+old[28:];address=ram+len(data)
        pairs=[]
        for hi,lows in groups.items():
            if any(native<=value<native+32 for _,value in lows):
                if any(value!=native for _,value in lows):raise ValueError('Shared or interior food reference')
                pairs.extend((hi,lo) for lo,_ in lows)
        if len(pairs)!=1 or any(native<=p<native+32 for p in absolute.values()):
            raise ValueError('Changed complete food table-reference inventory')
        for hi,lo in pairs:
            for p,half in ((hi,(address+0x8000)>>16),(lo,address&65535)):
                before=u32(patched,p);after=before&0xFFFF0000|half
                if p in removed:raise ValueError('Overlapping food table references')
                struct.pack_into('>I',patched,p,after);removed.add(p)
                patches.append(dict(address=origin+p,before=before,after=after))
        data.extend(raw)
        tables.append(dict(role=role,source_symbol=name,source_offset=at,source_bytes=n,
            source_pointers=pointers,native=native,native_sha256=checksum,ram=address,
            bytes=len(raw),sha256=sha256(raw),count=9,model=target))
    rel=bytearray(relocation);kept=[r for r in rows if r not in {locations[p] for p in removed}]
    if len(rows)-len(kept)!=4:raise ValueError('Incomplete food reference relocation removal')
    struct.pack_into('>I',rel,16,len(kept))
    rel[20:-4]=struct.pack('>'+str(len(kept))+'I',*kept)+bytes(len(rel)-24-len(kept)*4)
    return bytes(patched),bytes(rel),bytes(data),dict(donors=donors,tables=tables,patches=patches,
        removed_relocations=[locations[p] for p in sorted(removed)],native_function_sha256=
        '339a6921992f11cdbe9ce6556e87a2bb6090e53ad7d291e5a6bfe796cf6b8afb')


def install_field_actions(base,prior,output,directory):
    """Connect carried field consumers using existing resident resources."""
    from v3_holiday_selection import refresh_receipts
    from v3_npc_draw import relocation_offsets
    e=copy.deepcopy(prior['equipment_resources']);d=e['carried_items'];packet=d['packet']
    if (d.get('eating') or d['ready_mask'] or d['selected_mask'] or
            directory.resolve()!=ROOT/d['prepared']):
        raise ValueError('Field actions require the checked inactive carried batch')
    files=by_vrom(base);iv=e['inventory_preview'];hand=d['actions']['hand']
    owner,rel=files[0x785700].extract(base),files[0x7898C0].extract(base)
    hand_data=bytearray(files[hand['vrom']].extract(base));hand_rel=files[hand['reloc']].extract(base)
    raw=bytearray(base[packet['physical']:packet['physical']+packet['bytes']])
    if (sha256(owner)!=iv['owner_sha256'] or sha256(rel)!=iv['relocation_sha256'] or
            sha256(hand_data)!=hand['owner_sha256'] or sha256(hand_rel)!=hand['relocation_sha256'] or
            sha256(raw)!=packet['sha256'] or sha256(raw[RAM-packet['ram']:])!=d['sha256']):
        raise ValueError('Changed complete inventory/hand/carried resource')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    art=next(r for r in d['artwork'] if r['source_category']==28)
    offset=art['ram']-packet['ram']
    if sha256(raw[offset:offset+art['object_bytes']])!=art['installed_sha256']:
        raise ValueError('Changed complete installed food artwork')
    cat=d['paper']['catalogue']['code'];ram=(cat['link_symbols']['AF_CARRIED_CATALOGUE_RAM']+cat['bytes']+15)&~15
    owner_new,rel_new,tables,receipt=food_tables(source,owner,rel,art,ram)
    at=ram-packet['ram']
    if ram+len(tables)>TABLE or any(raw[at:at+len(tables)]):
        raise ValueError('Food tables overlap carried code/records')
    raw[at:at+len(tables)]=tables
    # Native fruit indexing already supplies 7 for coconut. Move only the
    # turnip branch to slot 8; preserve drop/consumption, clothes, and equipment.
    at=0x8087B2C0-hand['ram'];before=0x24190007;after=0x24190008
    native_hand=hand_data[0x8087B07C-hand['ram']:0x8087B5D4-hand['ram']]
    if (sha256(native_hand)!='339fb73d846ee3d87e0aa8d6d91c28fa3bb4bcddb353dff017961ffd8da1d630' or
            u32(hand_data,at)!=before or at in relocation_offsets(hand_rel,len(hand_data)) or
            hand_data[at+24:at+28]!=bytes.fromhex('a13903de')):
        raise ValueError('Changed complete native turnip food-index binding')
    struct.pack_into('>I',hand_data,at,after)
    receipt.update(ram=ram,bytes=len(tables),sha256=sha256(tables),coconut_index=7,turnip_index=8,
        inventory_vrom=0x785700,inventory_reloc=0x7898C0,inventory_ram=0x8087D480,
        original_owner_sha256=sha256(owner),owner_sha256=sha256(owner_new),relocation_sha256=sha256(rel_new),
        hand_patch=dict(address=hand['ram']+at,before=before,after=after),
        native_hand_sha256=sha256(native_hand),
        hand_previous_sha256=sha256(files[hand['vrom']].extract(base)),
        hand_sha256=sha256(hand_data),native_gameplay_verified=False,additional_resident_bytes=0)
    iv.update(owner_sha256=sha256(owner_new),relocation_sha256=sha256(rel_new))
    hand['owner_sha256']=sha256(hand_data)
    records=copy.deepcopy(prior['physical_resources']);before_sha=packet['sha256']
    refresh_receipts(e,records,{packet['id']:raw})
    d.update(eating=receipt,sha256=sha256(raw[RAM-packet['ram']:]),
        sources={s:sha256((ROOT/s).read_bytes()) for s in (*SOURCES,*STORAGE_SOURCES)})
    resource=next(r for r in records if r['id']==packet['id'])
    write_new(output/'carried-items.json',(json.dumps(d,indent=2)+'\n').encode())
    return e,{0x785700:owner_new,0x7898C0:rel_new,hand['vrom']:bytes(hand_data)},dict(physical_resources=records),[
        (dict(resource,previous_sha256=before_sha),bytes(raw))]


def install_creature_field(base,prior,blob,output,directory):
    """Extend the installed creature category using its checked carried batch."""
    from v3_creature_field import discover
    from v3_furniture_pipeline import prepare_models
    from v3_npc_draw import relocation_offsets
    e=copy.deepcopy(prior['equipment_resources']);d=e['carried_items']
    directory=directory.resolve();prepared=json.loads((directory/'linked.json').read_bytes());linked=prepared['linked']
    ram,art_ram,table_ram,info_ram,end=0x80784000,0x80786400,0x80786A00,0x80786C00,0x80787000
    tree=e['scenery']['tree_effects'];tree_packet=tree['packet'];tree_previous=copy.deepcopy(tree_packet)
    tree_raw=bytearray(base[tree_packet['physical']:tree_packet['physical']+tree_packet['bytes']])
    code=(directory/linked['file']).read_bytes()
    if (prepared['format']!='AFV3-CARRIED-CREATURES-1' or linked['base_sha256']!=sha256(base) or
            linked['ram']!=ram or linked['limit']!=art_ram or len(code)!=linked['bytes'] or
            sha256(code)!=linked['sha256'] or ram+len(code)>art_ram or
            d.get('field_creatures') or d['ready_mask'] or d['selected_mask'] or
            tree_packet['ram']!=0x80780000 or tree_packet['bytes']!=0x8000 or
            tree['code']['bytes']>0x4000 or sha256(tree_raw)!=tree_packet['sha256'] or
            any(tree_raw[0x4000:0x7000])):
        raise ValueError('Changed complete inactive carried field preparation or reservation')
    for path,digest in prepared['compiled']['runtime_sources'].items():
        if sha256((ROOT/path).read_bytes())!=digest:raise ValueError('Stale carried field runtime: '+path)
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    inventory=discover(source,carried_rows=d['rows'])
    if prepared['field']['inventory']!=json.loads(json.dumps(inventory)):
        raise ValueError('Changed complete carried field identity')
    row,=prepared['field']['objects'];part=prepare_models(source,row['descriptor'])
    art=bytearray((directory/'field'/row['object_file']).read_bytes())
    if (row['item_id']!='2D28' or len(art)!=row['object_bytes'] or sha256(art)!=row['object_sha256'] or
            row['resources']!=part[2] or art[:len(part[1])]!=part[1] or len(art)>0xC00):
        raise ValueError('Changed complete carried creature resources')
    field=e['creature_field'];old_insects=e['creature_insects'];oldp=old_insects['packet']
    before=base[oldp['physical']:oldp['physical']+oldp['bytes']];updated=bytearray(before)
    if sha256(before)!=linked['predecessor']['sha256'] or sha256(before)!=oldp['sha256']:
        raise ValueError('Changed retained insect owner')
    redirects=[]
    for r in linked['required_redirects']:
        at=r['previous']-oldp['ram'];original=before[at:at+8]
        after=struct.pack('>2I',jump(r['target']),0)
        if len(original)!=8:raise ValueError('Invalid complete carried reader redirect')
        updated[at:at+8]=after;redirects.append(dict(r,before=original.hex(),after=after.hex()))
    old_resource=old_insects['physical_resource'];previous_sha=old_resource['sha256']
    records=copy.deepcopy(prior['physical_resources'])
    resource=next(r for r in records if r['id']==old_resource['id'])
    resource['sha256']=sha256(updated);old_insects['physical_resource']=copy.deepcopy(resource)
    oldp.update(sha256=sha256(updated),crc32=zlib.crc32(updated))
    old_insects['compiled']['sha256']=sha256(updated[:old_insects['compiled']['bytes']])
    packet=bytearray(end-ram);packet[:len(code)]=code
    existing=[r for r in field['rows'] if r['category']=='insect']
    start=max(r['end'] for r in existing);offset=(start&0xFFFFFF)+8
    for model in row['models']:
        a=model['native_offset'];n=model['bytes']
        if sha256(art[a:a+n])!=model['output_sha256']:raise ValueError('Changed complete carried model commands')
        for at in range(a,a+n,8):
            first,target=struct.unpack_from('>2I',art,at)
            if first>>24 in (1,0xFD,0xDE):
                if target>>24!=6 or target&0xFFFFFF>=len(art):raise ValueError('Unbounded carried graphics pointer')
                struct.pack_into('>I',art,at+4,target+offset)
    packet[art_ram-ram:art_ram-ram+len(art)]=art
    frames=[0x06000000+offset+o for o in row['frame_offsets']]
    frame_ram=table_ram+3*41*4
    packet[frame_ram-ram:frame_ram-ram+16]=struct.pack('>4I',*frames)
    additions=(start,0x06000000+offset+len(art),frame_ram);tables=[]
    p=field['packet'];original_field=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
    if sha256(original_field)!=p['sha256']:raise ValueError('Changed complete existing field tables')
    for i,(name,value) in enumerate(zip(('insect-starts','insect-ends','insect-models'),additions,strict=True)):
        old=next(t for t in field['tables'] if t['name']==name);at=old['ram']-p['ram']
        data=original_field[at:at+old['bytes']]
        if len(data)!=160 or sha256(data)!=old['sha256']:raise ValueError('Changed complete native/imported insect table')
        target=table_ram+i*41*4;data+=struct.pack('>I',value)
        packet[target-ram:target-ram+len(data)]=data
        tables.append(dict(name=name,ram=target,bytes=len(data),sha256=sha256(data),previous=old['ram']))
    vrom=0x113D000+offset
    struct.pack_into('>8I',packet,info_ram-ram,0x41464351,vrom,len(art),art_ram,frames[0],frames[2],0,0)
    packet[-16:]=b'AFCARRIEDFIELD!!'
    files=by_vrom(base);v,r,owner_ram=0x8DEEC0,0x8E0870,0x80A10210
    owner=bytearray(files[v].extract(base));rel=bytearray(files[r].extract(base));locations=relocation_offsets(rel,len(owner))
    patches=[];removed=[]
    def patch(address,before,after,*,relocated=False):
        at=address-owner_ram
        if u32(owner,at)!=before or ((at in locations)!=relocated):
            raise ValueError(f'Changed carried creature field caller at {address:08X}')
        struct.pack_into('>I',owner,at,after);patches.append(dict(address=address,before=before,after=after))
        if relocated:removed.append(0x44000000|at)
    original_receipt=next(x for x in field['owners'] if x['name']=='insect')
    for i,(hi,lo) in enumerate(((0x80A10370,0x80A1038C),(0x80A10374,0x80A10394),(0x80A1145C,0x80A1146C))):
        for address,half in ((hi,(tables[i]['ram']+0x8000)>>16),(lo,tables[i]['ram']&65535)):
            old=next(x for x in original_receipt['patches'] if x['address']==address)['after']
            patch(address,old,(old&0xFFFF0000)|(half&65535))
    symbols=linked['symbols']
    patch(0x80A103D0,jump(field['compiled']['symbols']['af_v3_creature_graphics_load'],link=True),
        jump(symbols['af_carried_creature_graphics_load'],link=True))
    for address in (0x80A115C8,0x80A115F4,0x80A1162C):
        patch(address,jump(0x80A11264,link=True),jump(symbols['af_carried_insect_draw'],link=True),relocated=True)
    patch(0x80A10494,0x27BDFFE8,jump(symbols['af_carried_insect_destruct']))
    patch(0x80A10498,0xAFBF0014,0)
    count=u32(rel,16);words=list(struct.unpack_from('>'+str(count)+'I',rel,20))
    for word in removed:
        if words.count(word)!=1:raise ValueError('Missing native carried drawing relocation')
        words.remove(word)
    struct.pack_into('>I',rel,16,len(words));rel[20:20+count*4]=struct.pack('>'+str(len(words))+'I',*words)+bytes(4*len(removed))
    tree_raw[ram-tree_packet['ram']:end-tree_packet['ram']]=packet
    tree_record=next(r for r in records if r['id']==tree_packet['id'])
    tree_record['sha256']=sha256(tree_raw)
    tree_packet.update(sha256=sha256(tree_raw),crc32=zlib.crc32(tree_raw))
    receipt=dict(prepared=str(directory.relative_to(ROOT)),prepared_sha256=sha256((directory/'linked.json').read_bytes()),
        code=dict(linked,installed=True),packet=copy.deepcopy(tree_packet),previous_packet=tree_previous,
        ram=ram,bytes=len(packet),sha256=sha256(packet),
        art=dict(ram=art_ram,bytes=len(art),sha256=sha256(art),vrom=vrom,source_sha256=row['object_sha256']),
        tables=tables,frames=frames,info_ram=info_ram,redirects=redirects,
        owner=dict(vrom=v,reloc=r,ram=owner_ram,previous_sha256=sha256(files[v].extract(base)),
            sha256=sha256(owner),relocation_sha256=sha256(rel),patches=patches,removed_relocations=removed),
        additional_resident_bytes=0,reused_startup_padding_bytes=len(packet),
        native_gameplay_verified=False,installed=True,selectable=False,
        pending=['spirit capture/release menu and stack-aware net handover',
            'bind the actual Wisp event owner', 'independent carried selection'])
    d['field_creatures']=receipt
    paths=(*SOURCES,*prepared['compiled']['runtime_sources'],'tools/v3_creature_insects.py','tools/v3_creature_field.py',
        'overlays/v3/creature_carried.h','overlays/v3/creature_insects.h','tools/v3_room_goods.py','overlays/v3/surface_bootstrap.c')
    d['sources']={s:sha256((ROOT/s).read_bytes()) for s in paths}
    write_new(output/'carried-field.json',(json.dumps(receipt,indent=2)+'\n').encode())
    return e,{v:bytes(owner),r:bytes(rel)},dict(physical_resources=records),[
        (dict(resource,previous_sha256=previous_sha),bytes(updated)),
        (dict(tree_record,previous_sha256=tree_previous['sha256']),bytes(tree_raw))]


def install_creature_spawns(base,prior,output,directory):
    """Connect the actual carried-creature acre-entry consumer.

    Retain the complete installed ordinary manager and its behavioural choice.
    This does not enable a quest whose separate owner is still unfinished.
    """
    from aflib import CODE_VROM,verified_rom
    from v3_creature_spawns import insect_calendars
    from v3_creature_field import named_table
    from v3_console_disk_install import reservations
    import v3_physical_resources as physical
    e=copy.deepcopy(prior['equipment_resources']);d=e['carried_items']
    if (directory.resolve()!=ROOT/d['prepared'] or d.get('spawning') or
            not d.get('interactions') or d['ready_mask'] or d['selected_mask']):
        raise ValueError('Quest spawning requires the installed inactive carried batch')
    tree=e['scenery']['tree_effects'];previous=tree['packet']
    tree_data=base[previous['physical']:previous['physical']+previous['bytes']]
    ram,limit,end=0x807AC000,0x807ADFF0,0x807AE000
    if any(a<end and ram<b for a,b in reservations(prior)):
        raise ValueError('Quest code overlaps a retained Expansion Pak allocation')
    if sha256(tree_data)!=previous['sha256']:
        raise ValueError('Changed complete tree/carried startup packet')
    raw=bytearray(end-ram);raw[-16:]=b'AFCQ'*4
    insect=e['creature_insects'];old=insect['packet']
    if sha256(base[old['physical']:old['physical']+old['bytes']])!=old['sha256']:
        raise ValueError('Changed complete retained insect manager/services')
    field=d['field_creatures'];code=field['code'];offset=code['ram']-previous['ram']
    if sha256(tree_data[offset:offset+code['bytes']])!=code['sha256']:
        raise ValueError('Changed complete carried creature state providers')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    calendar,contract=insect_calendars(source)
    candidates=dict(insect['compiled']['symbols'])
    candidates.update(fqrand=0x8002C9AC,memset=0x8003B9B0,
        mCoBG_CheckWaterAttribute=0x8007620C,mCoBG_CheckHole_OrgAttr=0x8065AAE0)
    hole=old['physical']+0x8065AAE0-old['ram']
    if sha256(base[hole:hole+60])!='957704e5de4500b31fe7004475edf23cb7e39755bc0c939888010836327afdc3':
        raise ValueError('Changed complete retained native-terrain adapter')
    candidates.update({n:code['symbols'][n] for n in
        ('af_carried_spirit_common','af_carried_spirit_running','af_carried_creature_enabled')})
    calendar_at=candidates['af_insect_calendar']-old['ram']
    if base[old['physical']+calendar_at:old['physical']+calendar_at+len(calendar)]!=calendar:
        raise ValueError('Changed complete retained insect calendar/group sizes')
    row,row_source=named_table(source,'l_hitodama_time_table',8)
    if row!=struct.pack('>IBBH',40,3,100,0):
        raise ValueError('Changed complete donor spirit spawn row')
    files=by_vrom(base);original=verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    native=by_vrom(original)[CODE_VROM].extract(original)
    current=files[CODE_VROM].extract(base)
    at,end=0x80089440-CODE_RAM,0x80089538-CODE_RAM
    if current[at:end]!=native[at:end] or len(current[at:end])!=end-at:
        raise ValueError('Changed complete native lake lookup')
    candidates['af_carried_find_block']=0x80089440
    candidates['af_holiday_calendar_status']=e['npc_extra']['events']['calendar']['code']['symbols']['af_holiday_calendar_status']
    compiled_data,compiled=compile_part('creature_carried_spawns',output/'carried-spawns',
        extra_sources=('overlays/v3/creature_insect_spawns.c',),
        defines=('AF_INSECT_CARRIED','AF_INSECT_CARRIED_SPAWNS'),symbol_candidates=candidates)
    if ram+len(compiled_data)>limit:raise ValueError('Quest spawn code exceeds its checked reservation')
    manager=insect['manager'];vrom,reloc,owner_ram=0x821B40,0x8240D0,0x8092A030
    owner=bytearray(files[vrom].extract(base));rel=files[reloc].extract(base)
    address=0x8092AF0C;pos=address-owner_ram
    before=struct.pack('>2I',jump(candidates['af_v3_insect_spawn']),0)
    after=struct.pack('>2I',jump(compiled['symbols']['af_carried_insect_spawn']),0)
    if (owner[pos:pos+8]!=before or
            sha256(owner)!='235ba58583f0c644b6c6c28c1dc8c6c17e4c1f8f129ddb5639aaae07a706d69e' or
            sha256(rel)!=manager['reloc_sha256']):
        raise ValueError('Changed complete installed acre-entry manager')
    owner[pos:pos+8]=after
    raw[:len(compiled_data)]=compiled_data
    records=copy.deepcopy(prior['physical_resources'])
    resource=physical.allocate(base,records,raw,'carried-quest-GAFE01-r0',best_fit=True)
    records.append(resource)
    packet=dict(resource,ram=ram,storage='physical-ROM',crc32=zlib.crc32(raw))
    manager.update(owner_sha256=sha256(owner),target=compiled['symbols']['af_carried_insect_spawn'],
        after=after.hex(),installed=True)
    functions={r['symbol']:r for r in contract['source_functions']}
    source_names=('aSOI_check_hitodama_block_data','aSOI_check_countdown_event',
        'aSOI_check_hitodama_set_block','aSOI_ins_make_hitodama_range_data',
        'aSOI_ins_renew_check_range_table','aSOI_ins_decide_insect','aSOI_ins_make','aSOI_insect_set')
    receipt=dict(ram=ram,bytes=len(compiled_data),code=compiled,
        packet=copy.deepcopy(packet),source_row=row_source,
        source_functions=[functions[n] for n in source_names],calendar_sha256=sha256(calendar),
        native_lake_lookup=dict(address=at+CODE_RAM,end=end+CODE_RAM,sha256=sha256(current[at:end])),
        owner=dict(vrom=vrom,reloc=reloc,ram=owner_ram,previous_sha256=sha256(files[vrom].extract(base)),
            sha256=sha256(owner),reloc_sha256=sha256(rel),address=address,before=before.hex(),after=after.hex()),
        additional_resident_bytes=len(raw),saved_format_changed=False,native_gameplay_verified=False,
        installed=True,selectable=False,pending=['actual Wisp event owner','independent carried selection'])
    d['spawning']=receipt
    paths=('tools/v3_asset_loader.py','tools/v3_carried_runtime.py','tools/v3_creature_spawns.py',
        'overlays/v3/creature_carried_spawns.c','overlays/v3/creature_carried_spawns.ld',
        'overlays/v3/creature_insect_spawns.c','overlays/v3/creature_insect_spawns.h',
        'tools/v3_room_goods.py','overlays/v3/surface_bootstrap.c')
    d['sources'].update({s:sha256((ROOT/s).read_bytes()) for s in paths})
    write_new(output/'carried-spawns.json',(json.dumps(receipt,indent=2)+'\n').encode())
    return e,{vrom:bytes(owner)},dict(physical_resources=records),[
        (resource,bytes(raw))]


def install_quest_state(base,prior,core,output,directory):
    """Bind source hunt scheduling and real saved/common event ownership.

    Reuse the spirit packet's startup descriptor and all prepared resources.
    Admission remains off until the complete NPC/manager path is connected.
    """
    from v3_console_disk_install import reservations
    from v3_holiday_selection import refresh_receipts
    import v3_physical_resources as physical
    e=copy.deepcopy(prior['equipment_resources']);d=e['carried_items']
    if (directory.resolve()!=ROOT/d['prepared'] or d.get('quest') or not d.get('spawning') or
            d['ready_mask'] or d['selected_mask']):
        raise ValueError('Quest ownership requires the installed inactive spirit path')
    old=d['spawning']['packet'];ram=0x807AC000;save_ram=0x807AE000;end=0x807B4000
    raw=bytearray(base[old['physical']:old['physical']+old['bytes']])
    if (old['ram']!=ram or len(raw)!=0x2000 or sha256(raw)!=old['sha256'] or
            raw[-16:]!=b'AFCQ'*4 or any(a<end and save_ram<b for a,b in reservations(prior))):
        raise ValueError('Changed quest packet or overlapping extension')
    raw.extend(bytes(end-ram-len(raw)));raw[-16:]=b'AFCQ'*4
    storage=d['storage'];previous=copy.deepcopy(storage['code'])
    prefix_packet=d['packet'];prefix_sha=prefix_packet['sha256']
    prefix=bytearray(base[prefix_packet['physical']:prefix_packet['physical']+prefix_packet['bytes']])
    at=storage['ram']-prefix_packet['ram']
    if (sha256(prefix)!=prefix_sha or storage['save_format']!=16 or storage['wire_version']!=3 or
            sha256(prefix[at:at+storage['bytes']])!=previous['sha256']):
        raise ValueError('Changed complete format-16 save owner')
    links=dict(previous['link_symbols'],AF_HI_STORAGE_RAM=save_ram)
    saved,compiled=compile_part('holiday_item_storage',output/'carried-quest-storage',
        primary_source='overlays/v3/console_storage.c',
        extra_sources=('overlays/v3/save_compressed.c','overlays/v3/holiday_cards.c',
            'overlays/v3/carried_collection.c'),
        defines=tuple(f[2:] for f in previous['flags'] if f.startswith('-D'))+('AF_V3_CARRIED_QUEST=1',),
        link_symbols=links)
    if len(saved)>0x4000:raise ValueError('Complete quest save adapter exceeds its reservation')
    raw[save_ram-ram:save_ram-ram+len(saved)]=saved
    redirects=[];symbols=previous['symbols'];lo,hi=storage['ram'],storage['ram']+storage['bytes']
    bounds=sorted({v for v in symbols.values() if lo<=v<hi})
    for name,address in sorted(symbols.items()):
        if not name.startswith(('af_v3_','af_holiday_cards_','af_carried_')) or not lo<=address<hi:continue
        target=compiled['symbols'].get(name);stop=next((v for v in bounds if v>address),hi)
        if target is None or not save_ram<=target<save_ram+len(saved) or stop-address<8:
            raise ValueError('Missing or short public carried save entry: '+name)
        offset=address-prefix_packet['ram'];before=bytes(prefix[offset:offset+8])
        after=struct.pack('>2I',jump(target),0);prefix[offset:offset+8]=after
        redirects.append(dict(name=name,address=address,target=target,before=before.hex(),after=after.hex()))
    if len(redirects)!=36:raise ValueError('Changed complete public carried save entry inventory')
    native=[]
    for first,last,digest in (
        (0x80080080,0x80080200,'bf96a81786bddfa774c104c56d1d5f6c5b9b8e316471578860fa6debfd12ae40'),
        (0x8008033C,0x800804AC,'e3f773780ce82da3b43a46975c07e1c0c37815fbc95bca00f3b00ce8869adec3'),
        (0x800807E0,0x800808E0,'8eca4f6b67ca12f625f5ed69e1549c62e94e3f3cb766d2e61c8e3465a7cb7c73'),
        (0x800808E0,0x80080968,'c16bebef24cdc9944d87a0f77e2a3416582fba5e71cfef191b549043a96c9579')):
        if sha256(core[first-CODE_RAM:last-CODE_RAM])!=digest:
            raise ValueError('Changed native saved/common event service')
        native.append(dict(address=first,end=last,sha256=digest))
    candidates=dict(compiled['symbols'])
    candidates.update(af_cw_state=0x807B3F00,af_cw_native_rtc=0x80136FBC,fqrand=0x8002C9AC,
        af_cw_prior_calendar_before_cleanup=e['holiday_state']['code']['symbols']['af_holiday_calendar_before_cleanup'],
        af_cw_native_get_save=0x8008033C,af_cw_native_reserve_save=0x80080080,
        af_cw_native_get_common=0x800808E0,af_cw_native_reserve_common=0x800807E0,
        af_holiday_native_days=0x806F1500,af_holiday_native_index=0x804A2B00,
        af_holiday_native_count=0x80104F98,
        af_carried_quantity=d['code']['symbols']['af_carried_quantity'],
        af_carried_spirit_event_bind=d['field_creatures']['code']['symbols']['af_carried_spirit_event_bind'])
    quest,owner=compile_part('carried_quest',output/'carried-quest-state',
        extra_sources=('overlays/v3/holiday_native.c',),
        defines=('AF_V3_CARRIED_PROFILE=1','AF_V3_CARRIED_QUEST=1'),symbol_candidates=candidates)
    raw[0x807B2000-ram:0x807B2000-ram+len(quest)]=quest
    patches=[]
    for address,before,after in (
        (0x8007F630,struct.pack('>2I',jump(candidates['af_cw_prior_calendar_before_cleanup'],link=True),0),
         struct.pack('>2I',jump(owner['symbols']['af_cw_calendar_before_cleanup'],link=True),0)),
        (0x8007F640,struct.pack('>I',0x24110073),struct.pack('>I',0x24110074)),
        (0x8007F660,struct.pack('>I',0x24110073),struct.pack('>I',0x24110074))):
        offset=address-CODE_RAM
        if core[offset:offset+len(before)]!=before:raise ValueError('Changed daily event owner caller')
        core[offset:offset+len(after)]=after
        patches.append(dict(address=address,before=before.hex(),after=after.hex()))
    resources=copy.deepcopy(prior['physical_resources']);retired=[]
    try:replacement=physical.grow_backwards(base,resources,old['id'],bytes(raw))
    except ValueError as error:
        if str(error)!='No checked adjacent space for complete physical resource growth':raise
        # These retained predecessor copies have already been replaced by the
        # larger fishing/state packet. Verify their actual startup replacement
        # before reclaiming their physical space in the new output only.
        events=e['npc_extra']['events']
        staged,resources,retired=physical.retire_packet_copies(base,prior,(
            (events['transition']['original_packet'],e['holiday_fishing']['packet']),
            (events['decorations']['renderer']['original_packet'],e['holiday_fishing']['packet'])))
        resources=copy.deepcopy(resources)
        replacement=physical.allocate(staged,resources,bytes(raw),'carried-quest-state-GAFE01-r0',best_fit=True)
    resource={k:replacement[k] for k in ('id','physical','bytes','sha256')}
    if resource['id']==old['id']:
        resources[resources.index(next(r for r in resources if r['id']==old['id']))]=resource
    else:resources.append(resource)
    packet=dict(resource,ram=ram,crc32=zlib.crc32(raw),storage='physical-ROM')
    d['spawning']['packet']=copy.deepcopy(packet)
    refresh_receipts(e,resources,{prefix_packet['id']:prefix})
    storage['sha256']=storage['code']['sha256']=sha256(prefix[at:at+storage['bytes']])
    storage.update(active_code=copy.deepcopy(compiled),quest_redirects=redirects,save_format=17,wire_version=4)
    e['holiday_items']['controls']['storage'].update(active_code=copy.deepcopy(compiled),save_format=17,wire_version=4)
    e['console_storage'].update(save_format=17,card_runtime=copy.deepcopy(compiled))
    d['sha256']=sha256(prefix[RAM-prefix_packet['ram']:])
    d['saved_format_changed']=True
    d['quest']=dict(packet=copy.deepcopy(packet),code=owner,ram=0x807B2000,bytes=len(quest),
        storage=compiled,storage_ram=save_ram,redirects=redirects,core_patches=patches,native_services=native,
        state=dict(ram=0x807B3F00,bytes=56,common_bytes=44,native_marker_bytes=40),
        saved_event=dict(native_type=115,source_type=114,area=54,bytes=8),
        save_format=17,wire_version=4,date_offset=13,additional_resident_bytes=len(raw)-old['bytes'],
        availability_address=owner['symbols']['af_cw_available'],available=False,
        native_gameplay_verified=False,native_save_reload_verified=False,
        pending=['native NPC lifecycle/drawing','manager placement and callbacks',
            'official dialogue and full reward/cleanup routes','independent carried selection'])
    paths=(*STORAGE_SOURCES,'overlays/v3/holiday_native.c','overlays/v3/holiday_native.h',
        'overlays/v3/carried_quest.c','overlays/v3/carried_quest.h','overlays/v3/carried_quest.ld',
        'tools/v3_carried_runtime.py','tools/v3_asset_loader.py','tools/v3_furniture_install.py','tools/v3_room_goods.py')
    d['sources'].update({s:sha256((ROOT/s).read_bytes()) for s in paths})
    updates={k:copy.deepcopy(prior[k]) for k in ('save_codec','clothing','room_surfaces')}
    updates['save_codec'].update(format_version=17,active_storage_code=copy.deepcopy(compiled),
        card_storage_code=copy.deepcopy(compiled))
    ext=updates['clothing']['save_extension'];ext.update(format_version=17,active_storage_code=copy.deepcopy(compiled))
    ext['legacy_formats_read']=list(dict.fromkeys([*ext['legacy_formats_read'],'AFS3-v16']))
    updates['room_surfaces']['save']['disk_format_version']=17
    updates['save_warning']=('Format-17 experimental saves require this or a newer compatible build. '
        'Compatible older saves migrate forward. Removing required imports rejects loading. '
        'V2 and format-16-or-earlier V3 cannot load new saves. Keep backups. '
        'Native carried-item gameplay and save/reload remain unverified.')
    updates['physical_resources']=resources
    updates['retired_physical_resources']=retired
    prefix_resource=next(r for r in resources if r['id']==prefix_packet['id'])
    write_new(output/'carried-quest.json',(json.dumps(d['quest'],indent=2)+'\n').encode())
    return e,{},updates,[(dict(prefix_resource,previous_sha256=prefix_sha),bytes(prefix)),(replacement,bytes(raw))]


def install_quest_manager(base,prior,core,output,directory):
    """Connect the complete source quest manager through shared placement."""
    from types import SimpleNamespace
    from npc_mail_show import relocate_verified_data
    from v3_campsite_manager import RAM as owner_ram,VROM,RELOC,METADATA,CONTROL_COUNT
    from v3_registry import SPECIAL_NPCS
    e=copy.deepcopy(prior['equipment_resources']);d=e['carried_items'];q=d['quest'];p=q['packet']
    if (directory.resolve()!=ROOT/d['prepared'] or q.get('manager') or q['available'] or
            d['ready_mask'] or d['selected_mask'] or p!=d['spawning']['packet']):
        raise ValueError('Quest manager requires the installed inactive state/save path')
    raw=bytearray(base[p['physical']:p['physical']+p['bytes']]);start=q['ram']-p['ram']
    if (sha256(raw)!=p['sha256'] or sha256(raw[start:start+q['bytes']])!=q['code']['sha256'] or
            any(raw[start+q['bytes']:0x807B3F00-p['ram']]) or raw[-16:]!=b'AFCQ'*4):
        raise ValueError('Changed complete quest code or reserved padding')
    prepared=ROOT/'build/v3-carried-event-prepared-03'
    manifest=json.loads((prepared/'prepared.json').read_bytes())
    for name,digest in manifest['generated_sha256'].items():
        if sha256((prepared/name).read_bytes())!=digest:raise ValueError('Changed complete prepared quest source')
    for path,record in manifest['references'].items():
        data=(ROOT/'local/ac-decomp'/path).read_bytes()
        if len(data)!=record['bytes'] or sha256(data)!=record['sha256']:raise ValueError('Changed quest donor reference')
    identity=SPECIAL_NPCS['GAFE01-r0/npc/ev-ghost']
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    profile=source.raw('Ev_Ghost_Profile')
    if struct.unpack('>HHIHH6I',profile)!=(identity['donor_profile'],4<<8,0,identity['donor_name'],3,2480,0,0,0,0,0):
        raise ValueError('Changed complete source quest NPC profile')
    events=e['npc_extra']['events'];candidates=dict(q['code']['symbols'])
    candidates.update(events['placement']['bindings'])
    bindings=events['festivals']['bindings']
    candidates.update({name:bindings[name] for name in ('mPr_GetPossessionItemIdxWithCond','mPr_SetPossessionItem')})
    candidates.update(af_cw_native_private=bindings['af_hp_private'],af_cw_native_player=bindings['af_hp_player_index'])
    defs=('AF_V3_CARRIED_PROFILE=1','AF_V3_CARRIED_QUEST=1',f'AF_CW_NATIVE_NAME=0x{identity["name"]:X}',
        'mEv_get_save_area=af_cw_get_save','mEv_reserve_save_area=af_cw_reserve_save',
        'mEv_get_common_area=af_cw_get_common','mEv_reserve_common_area=af_cw_reserve_common',
        'mEv_check_keep=af_cw_check_keep','mEv_set_keep=af_cw_set_keep','mEv_clear_keep=af_cw_clear_keep')
    code,compiled=compile_part('carried_quest',output/'carried-quest-manager',
        extra_sources=('overlays/v3/holiday_native.c','overlays/v3/carried_manager.c',
            'overlays/v3/holiday_placement.c','overlays/v3/holiday_placement_native.c',
            str((prepared/'manager.c').relative_to(ROOT))),
        defines=defs,include_dirs=('overlays/v3',str(prepared.relative_to(ROOT))),symbol_candidates=candidates)
    if q['ram']+len(code)>q['state']['ram']:raise ValueError('Complete quest manager overlaps saved state')
    raw[start:0x807B3F00-p['ram']]=code.ljust(0x807B3F00-q['ram'],b'\0')
    # The current native control table is at the complete owner's tail. Append
    # one resident-callback row; all existing pointers/relocations stay in place.
    files=by_vrom(base);old=files[VROM].extract(base);oldrel=files[RELOC].extract(base)
    manager=copy.deepcopy(prior['campsite_manager']);table=manager['table'];count=manager['control_count']
    head=struct.unpack_from('>5I',oldrel)
    if (count!=73 or table-owner_ram+count*32!=len(old) or u32(old,CONTROL_COUNT-owner_ram)!=count or
            sha256(old)!=manager['output_sha256'] or sha256(oldrel)!=manager['relocation_sha256'] or
            head[:4]!=(len(old),0,0,0) or manager['today_pointer_capacity']<count+1):
        raise ValueError('Changed complete native event-control directory')
    callbacks=[compiled['symbols']['af_cw_manager_'+name] for name in ('start','stop','in','out')]
    data=bytearray(old);struct.pack_into('>I',data,CONTROL_COUNT-owner_ram,count+1)
    data.extend(struct.pack('>8I',115,*callbacks,0,0,0))
    reloc=bytearray(oldrel);struct.pack_into('>I',reloc,0,len(data))
    if len(data)+len(reloc)>0xC000 or VROM+len(data)>RELOC or owner_ram+len(data)>0x809670B0:
        raise ValueError('Complete Wisp control exceeds native owner allocation')
    for address in (0x801A0010,0x802F8010):
        before=relocate_verified_data(SimpleNamespace(ram=owner_ram,resident_bytes=len(old),sections=head),old,oldrel,address)
        after=relocate_verified_data(SimpleNamespace(ram=owner_ram,resident_bytes=len(data),
            sections=(len(data),0,0,0,head[4])),bytes(data),bytes(reloc),address)
        allowed=range(CONTROL_COUNT-owner_ram,CONTROL_COUNT-owner_ram+4)
        if (any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(before,after))) or
                after[len(old):]!=data[len(old):]):
            raise ValueError('Wisp owner changes unrelated relocated code or resident callbacks')
    at=METADATA-CODE_RAM
    if core[at:at+16]!=struct.pack('>4I',VROM,VROM+len(old),owner_ram,owner_ram+len(old)):
        raise ValueError('Changed complete native event-owner descriptor')
    core[at:at+16]=struct.pack('>4I',VROM,VROM+len(data),owner_ram,owner_ram+len(data))
    resizes=[dict(vrom=VROM,previous_bytes=len(old),previous_sha256=sha256(old),bytes=len(data),sha256=sha256(data))]
    manager.update(table_bytes=(count+1)*32,control_count=count+1,bytes=len(data),output_sha256=sha256(data),
        relocation_sha256=sha256(reloc),on_demand_growth=manager['on_demand_growth']+32)
    changes={VROM:bytes(data),RELOC:bytes(reloc)}
    q.update(code=compiled,bytes=len(code),availability_address=compiled['symbols']['af_cw_available'])
    q['manager']=dict(source=str(prepared.relative_to(ROOT)),source_functions=manifest['event_manager_functions'],
        generated_sha256=manifest['generated_sha256']['manager.c'],identity=identity,
        vrom=VROM,reloc=RELOC,ram=owner_ram,table=table,control_count=count+1,callbacks=callbacks,
        previous_sha256=sha256(old),sha256=sha256(data),relocation_sha256=sha256(reloc),
        original_controls_retained=count,margin=5,additional_resident_bytes=0,additional_owner_bytes=32,
        native_gameplay_verified=False,installed=True,npc_registered=False)
    manager['carried_owner']=copy.deepcopy(q['manager'])
    q['pending']=['native NPC lifecycle/drawing and identity registration','official dialogue and full reward/cleanup routes',
        'independent carried selection']
    paths=('tools/v3_carried_runtime.py','tools/v3_registry.py','tools/v3_furniture_install.py',
        'overlays/v3/carried_quest.ld','overlays/v3/carried_manager.c','overlays/v3/carried_event.h',
        'overlays/v3/holiday_placement.c','overlays/v3/holiday_placement.h','overlays/v3/holiday_placement_native.c')
    d['sources'].update({s:sha256((ROOT/s).read_bytes()) for s in paths})
    before=p['sha256'];p.update(sha256=sha256(raw),crc32=zlib.crc32(raw))
    d['spawning']['packet']=copy.deepcopy(p)
    resources=copy.deepcopy(prior['physical_resources'])
    resource=next(r for r in resources if r['id']==p['id']);resource['sha256']=p['sha256']
    write_new(output/'carried-quest-manager.json',(json.dumps(q['manager'],indent=2)+'\n').encode())
    return e,changes,dict(physical_resources=resources,campsite_manager=manager,runtime_owner_resizes=resizes),[
        (dict(resource,previous_sha256=before),bytes(raw))]


CARRIED_MESSAGE_FIRST=13082
CARRIED_FILTERS=((2,'entrust','entrust'),(4,'quest','unrestricted'),
    (5,'sell','sell'),(6,'give','give'),(8,'take','take'),(13,'exchange','exchange'))
CARRIED_FILTER_SOURCES=(
    (0x7FC5C,'mSM_check_item_for_furniture','1ef5e8e7d41d7215e93183104e5da2990b55c3606b5322057aaac70c50d5d897'),
    (0x7FCDC,'mSM_check_item_for_quest','7071cd8b7c76d7154d19b57a02d4af61e52c93e6f7ae60a020dcfe6263793eb2'),
    (0x7FD34,'mSM_check_item_for_sell','d3964c59de1ba1bc0ff79910c1cfa5c5cfeb9bcfaf78e4c8f99ba3c2466e9c46'),
    (0x7FDB4,'mSM_check_item_for_give','762bd26f3fa73b9bea5948f2b81de514670b001e57daebbc3fdcac8e0b9c152b'),
    (0x7FE1C,'mSM_check_item_for_take','5dbfd15329208746d59a42ca8ac9bb0823b1ff3d7e9965a2701d3bfa1def73af'),
    (0x7FF6C,'mSM_check_item_for_entrust','946d39e90c749ae9afd00cc2e4e46535d6fb92dda402965e767ff84c31a0a0d9'),
    (0x7FFEC,'mSM_check_item_for_exchange','a166e4ddaff91b177aec75f09c38355b53a93f2c1e36a84b6fc3eb14cd690bb2'),
    (0x80108,'mSM_check_item_for_curator','1d04c087f557d37a458ac3908646b19eaba84262d5f4694fc580150fec41f0b2'),
    (0x2820DC,'mTG_check_item_on_mail','131f59ea175cdbe0bf694549c4c8b62aa7b003abdbafea4b029d5ad23909ddcd'))


def capture_text(base,source):
    """Retain complete official capture dialogue, including the unused tail."""
    from gc_text import decode_gc
    from runtime_module import module_command_info
    from textcodec import encode,tokenize
    from textvalidate import expanded_bound
    from v3_camper_text import donor
    bank,_,decoder=donor();info=module_command_info(base);extra=[];rows=[];credits=[]
    for index,source_id in enumerate(range(0x2F03,0x2F09)):
        original=bank[source_id];data=encode(decode_gc(original,decoder),info)
        tokens=list(tokenize(data,info));bound=expanded_bound(data,info)
        if (not tokens or tokens[-1].data!=bytes((0x7F,0 if index==5 else 1)) or bound>1024 or
                any(t.kind=='cmd' and t.data[1] not in (0,1,3,5) for t in tokens) or
                sum(t.kind=='cmd' and t.data[1] in (0,1) for t in tokens)!=1):
            raise ValueError('Changed complete carried capture message commands')
        target=CARRIED_MESSAGE_FIRST+index;extra.append(data)
        rows.append(dict(id=target,source_id=source_id,sha256=sha256(data),source_sha256=sha256(original),
            bytes=len(data),expanded_bound=bound))
        credits.append(dict(id=f'message:{target:04X}',native_sha256=None,locales=dict(en=dict(
            credit='official',locator=['tools/v3_carried_runtime.py:capture_text',f'N64/message/{target:04X}'],
            source=dict(source='user-supplied GAFE01 revision 0 disc',reference_id=f'message:{source_id:04X}',
                reference_sha256=sha256(original)),
            adaptations=['Native encoding; retain official wording, line/page breaks, pauses, colours, and empty final record'],
            human_review='not_recorded',encoded_sha256=sha256(data)))))
    return extra,dict(first_id=CARRIED_MESSAGE_FIRST,count=len(extra),rows=rows,provenance_entries=credits)


def install_interactions(base,prior,core,output,directory):
    """Connect the category's remaining native menu/net consumers together."""
    from v3_submenu_tables import Owner
    from v3_equipment_runtime import PLAYER_VROM,PLAYER_RELOC,PLAYER_RAM
    from v3_creature_fish import rewrite
    from v3_balloon_release import menu_field_address
    from v3_camper_text import extend_bank
    from v3_event_text import MESSAGE,TABLE as MESSAGE_TABLE,CHOICE_TABLE,patch_bounds
    from text_provenance import validate
    e=copy.deepcopy(prior['equipment_resources']);d=e['carried_items'];p=d['packet']
    previous=d.get('interactions')
    if (d['ready_mask'] or d['selected_mask'] or
            directory.resolve()!=ROOT/d['prepared']):
        raise ValueError('Carried interactions require the checked inactive category')
    raw=bytearray(base[p['physical']:p['physical']+p['bytes']]);start=0x80772070-p['ram'];end=TABLE-p['ram']
    occupied=previous['bytes'] if previous else 0
    if (sha256(raw)!=p['sha256'] or any(raw[start+occupied:end]) or
            previous and (previous['ram']!=0x80772070 or not 0<occupied<=end-start or
                sha256(raw[start:start+occupied])!=previous['sha256'])):
        raise ValueError('Changed carried interaction reservation')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    donors=[]
    for at,name,digest in (
        (0x6BAD0,'mPlib_Get_space_putin_item_forHITODAMA','d6f1d8abebdcf9651f2dcbe02425c2e679425160a1def4c7e3b76d7736d9baf9'),
        (0x18386C,'Player_actor_Pull_net_demo_ct','8f79e4469656483e8012c73ca3d0a9ea4b0e125adb7038a4286a7c400304824a'),
        (0x183E7C,'Player_actor_setup_main_Notice_net','c8fcc50ea6e62db2d9cc58201b8daadfed563c76c955f1b1c99a4309df0dd4e5'),
        (0x287580,'mTG_release_proc','82abe20de0c744371c40da79fef7011e43605f7866e1a733c564ad2775817ab2'),
        ACTION_SOURCES[1],*CARRIED_FILTER_SOURCES):
        _,r=source.function(at)
        if r['symbol']!=name or r['sha256']!=digest:raise ValueError('Changed complete carried interaction source')
        donors.append(r)
    extra,text=capture_text(base,source)
    provenance=json.loads((ROOT/'translations/provenance.json').read_bytes());validate(provenance)
    indexed={r['id']:r for r in provenance['entries']}
    if any(indexed.get(r['id'])!=r for r in text['provenance_entries']):
        raise ValueError('Missing complete official capture-text provenance')
    files=by_vrom(base);tag=Owner(files[0x3950000].extract(base),files[0x3960000].extract(base),0x8086F310)
    player=files[PLAYER_VROM].extract(base);rel=files[PLAYER_RELOC].extract(base)
    old_symbols=previous['code']['symbols'] if previous else {}
    normalized=bytearray(player)
    ui=e['creature_fish']['world']['ui']['code']['symbols']
    calls=((0x808CD518,'af_carried_net_slot',0x800B3780),
        (0x808CD548,'af_carried_net_put',0x808B5584),
        (0x808CD070,'af_carried_net_message_call',ui['af_v3_creature_insect_message_call']))
    if previous:
        if (sha256(player)!=previous['player']['sha256'] or sha256(rel)!=previous['player']['reloc_sha256'] or
                sha256(tag.original)!=previous['tag']['owner_sha256'] or
                sha256(tag.relocation)!=previous['tag']['relocation_sha256']):
            raise ValueError('Changed complete carried interaction owners before refresh')
        for at,name,original in calls:
            if u32(player,at-PLAYER_RAM)!=jump(old_symbols[name],link=True):
                raise ValueError('Changed installed carried interaction caller')
            struct.pack_into('>I',normalized,at-PLAYER_RAM,jump(original,link=True))
    native=[]
    for at,size,digest in (
        (0x808CD4D4,240,'3a1e1ec1ad507749fb33a226b801b1094a41a92f04aaa33e23bc947b29103891'),
        (0x808B5584,104,'15b715e025943f86f35b030aedb3f7a300cc978748c1a17220e98378665e5334'),
        (0x808CCFDC,328,'23858e8fe9b0e123779291b41e0b580582e49d155a0bce1f108d9e7ba3719cf5')):
        # The message body already contains the retained full-name/UI adapter.
        data=normalized[at-PLAYER_RAM:at-PLAYER_RAM+size]
        if sha256(data)!=digest:raise ValueError(f'Changed complete carried native consumer {at:08X}')
        native.append(dict(address=at,bytes=size,sha256=digest))
    # Raw insect categories already reject mailing and furniture storage.
    # Preserve the complete native mail check and its two event-item callers.
    controls=e['holiday_items']['controls']['code']['symbols']
    mail=tag.original[0x80870AC4-tag.ram:0x80870B20-tag.ram]
    if (sha256(mail)!='a83397461ce7d08c96a45e692f7c5bc6b76c9b36a378ac78d11a0dcd11d0d506' or
            any(u32(tag.original,at-tag.ram)!=jump(controls['af_hi_mail_allowed'],link=True)
                for at in (0x808760AC,0x80876348))):
        raise ValueError('Changed retained native mail policy')
    links={n:d['code']['symbols'][n] for n in ('af_carried_quantity','af_carried_with_quantity')}
    links.update(af_carried_prior_action_menu=d['code']['symbols']['af_carried_menu_type'],
        af_carried_prior_insect_message=ui['af_v3_creature_insect_message'],af_carried_set_message=0x8007B5C0)
    filters=[]
    for index,name,predecessor in CARRIED_FILTERS:
        symbol='af_carried_filter_'+name;at=0x8010DD38+index*4
        target=controls['af_hi_filter_'+predecessor]
        before=old_symbols[symbol] if previous and previous.get('inventory_filters') else target
        if u32(core,at-CODE_RAM)!=before:
            raise ValueError('Changed carried inventory filter: '+name)
        links['af_carried_prior_filter_'+name]=target
        filters.append(dict(address=at,before=before,symbol=symbol,predecessor=target))
    code,compiled=compile_part('carried_interactions',output/'carried-interactions',
        extra_sources=('overlays/v3/carried_interactions.S',),link_symbols=links,
        defines=(f'AF_CARRIED_FIELD_ADDRESS=0x{menu_field_address(tag.original):08X}u',
            f'AF_CARRIED_SPIRIT_MESSAGE_FIRST={CARRIED_MESSAGE_FIRST}u'))
    if len(code)>end-start:raise ValueError('Carried interaction code exceeds existing padding')
    symbols=compiled['symbols'];raw[start:end]=code+bytes(end-start-len(code))
    for row in filters:
        row['after']=symbols[row['symbol']]
        struct.pack_into('>I',core,row['address']-CODE_RAM,row['after'])
    tag.patch(0x80875834,jump(old_symbols.get('af_carried_interaction_menu',links['af_carried_prior_action_menu']),link=True),
        jump(symbols['af_carried_interaction_menu'],link=True))
    old_release=old_symbols.get('af_carried_release',0x808739B0)
    release=[tag.ram+i for i in range(0,len(tag.original),4) if u32(tag.original,i)==old_release]
    if release!=[0x80878C80,0x808799E8]:raise ValueError('Changed complete native release consumers')
    for address in release:
        at=address-tag.ram;word=0x42000000|at
        if previous:
            if at in tag.locations:raise ValueError('Resident release pointer has a native relocation')
        else:
            if tag.locations.get(at)!=word:raise ValueError('Missing native release pointer relocation')
            tag.rows.remove(word)
        tag.patch(address,old_release,symbols['af_carried_release'])
    tag_data,tag_rel,tag_report=tag.finish()
    if len(tag_rel)>len(tag.relocation) or len(tag_data)!=len(tag.original):
        raise ValueError('Carried interactions unexpectedly resize the native menu')
    tag_rel=tag_rel[:-4]+bytes(len(tag.relocation)-len(tag_rel))+struct.pack('>I',len(tag.relocation))
    tag_report['relocation_sha256']=sha256(tag_rel)
    windows=[(at,(jump(old_symbols.get(name,original),link=True),),(jump(symbols[name],link=True),))
        for at,name,original in calls]
    player_data,player_rel,player_report=rewrite(player,rel,PLAYER_RAM,{},windows)
    if previous:
        from textbanks import Bank
        entries=Bank('carried',0,0,files[MESSAGE].extract(base),files[MESSAGE_TABLE].extract(base)).entries()
        if (entries[CARRIED_MESSAGE_FIRST:CARRIED_MESSAGE_FIRST+len(extra)]!=extra or
                text['rows']!=previous['text']['rows']):
            raise ValueError('Changed installed complete spirit dialogue')
        text=copy.deepcopy(previous['text'])
    else:
        payload,table=extend_bank(files[MESSAGE].extract(base),files[MESSAGE_TABLE].extract(base),extra,CARRIED_MESSAGE_FIRST)
        choices=prior['import_storage']['choice_vrom'];text['choice_vrom']=choices;text['resources']=[]
        for v,data in ((MESSAGE,payload),(MESSAGE_TABLE,table),(choices,files[choices].extract(base)),
                (CHOICE_TABLE,files[CHOICE_TABLE].extract(base))):
            filename=f'carried-text-{v:08X}.bin';write_new(output/filename,data)
            text['resources'].append(dict(vrom=v,file=filename,bytes=len(data),sha256=sha256(data),
                original_sha256=sha256(files[v].extract(base))))
        text['bounds']=patch_bounds(core,CARRIED_MESSAGE_FIRST,len(extra))
    records=copy.deepcopy(prior['physical_resources']);resource=next(r for r in records if r['id']==p['id'])
    old_sha=p['sha256'];resource['sha256']=sha256(raw);p.update(sha256=sha256(raw),crc32=zlib.crc32(raw))
    d['sha256']=sha256(raw[RAM-p['ram']:])
    e['npc_extra']['events']['festivals']['packet']=copy.deepcopy(p)
    receipt=dict(code=compiled,ram=0x80772070,bytes=len(code),sha256=sha256(code),
        donors=donors,native_consumers=native,tag=tag_report,inventory_filters=filters,
        retained_mail=dict(address=0x80870AC4,bytes=len(mail),sha256=sha256(mail),callers=[0x808760AC,0x80876348]),
        refresh=bool(previous),
        player=dict(player_report,vrom=PLAYER_VROM,reloc=PLAYER_RELOC,ram=PLAYER_RAM),text=text,
        additional_resident_bytes=0,native_gameplay_verified=False)
    d['interactions']=receipt
    d['field_creatures']['pending']=['bind the actual Wisp event owner','independent carried selection']
    paths=(*d['sources'],'tools/v3_creature_ui.py','tools/v3_event_text.py','overlays/v3/carried_interactions.c',
        'overlays/v3/carried_interactions.S','overlays/v3/carried_interactions.ld')
    d['sources']={s:sha256((ROOT/s).read_bytes()) for s in paths}
    write_new(output/'carried-interactions.json',(json.dumps(receipt,indent=2)+'\n').encode())
    return e,{0x3950000:tag_data,0x3960000:tag_rel,PLAYER_VROM:player_data,PLAYER_RELOC:player_rel},\
        dict(physical_resources=records),[(dict(resource,previous_sha256=old_sha),bytes(raw))]


def finish(image,base,prior,output,equipment):
    before=prior['equipment_resources'].get('carried_items',{}).get('interactions')
    now=equipment['carried_items'].get('interactions')
    if now and not before:
        from v3_event_text import install as install_text
        return install_text(image,base,output,now['text'],relocate=True,
            physical_resources=prior['physical_resources'],
            reserved_end=prior.get('resource_capacity',{}).get('reserved_physical_end',0))
    return image


def paper_catalogue(base,prior,e,core,compiled,resources):
    """Extend native paper rows/drawing without rebuilding unrelated catalogues."""
    from v3_submenu_tables import Owner,resize
    from v3_catalogue import VROM,RELOC,RAM as CAT_RAM,PARENT
    from v3_furniture_install import relocate_resource_plan
    files=by_vrom(base);cat=copy.deepcopy(prior['catalogue']);d=e['carried_items']
    owner=Owner(files[VROM].extract(base),files[RELOC].extract(base),CAT_RAM)
    if sha256(owner.original)!=cat['output_sha256'] or sha256(owner.relocation)!=cat['relocation_sha256']:
        raise ValueError('Changed complete catalogue owner')
    descriptor,table=0x808AF7CC,0x808AF580
    if (owner.original[descriptor-CAT_RAM:descriptor-CAT_RAM+8]!=struct.pack('>2I',table,64) or
            owner.original[table-CAT_RAM:table-CAT_RAM+128]!=struct.pack('>64H',*range(64)) or
            owner.locations.get(descriptor-CAT_RAM)!=0x42000000|(descriptor-CAT_RAM)):
        raise ValueError('Changed complete original paper catalogue')
    appended=owner.append(struct.pack('>65H',*range(64),67))
    owner.patch(descriptor,table,appended);owner.patch(descriptor+4,64,65)
    paper=d['paper'];binding=paper['bindings'][0]
    for address,label in ((0x808AE880,'background'),(0x808AE980,'lines')):
        target=(PAPER&0x1FFFFFFF)+paper['offsets'][binding[label]]
        owner.table(address,64,4,struct.pack('>I',target),pointer_offsets=(),expected_references=1)
    # The surface bridge already supplies the relocated original bit reader in
    # a2; redirect only its permanent tail call, preserving both relocations.
    entry=cat['code']['symbols']['af_v3_catalogue_bit']
    owner.patch(entry+8,jump(compiled['link_symbols']['af_carried_prior_catalogue_bit']),
        jump(compiled['symbols']['af_carried_catalogue_bit']))
    owner.patch(0x808A6B80,jump(0x808A6730,link=True),
        jump(compiled['symbols']['af_carried_paper_init'],link=True),remove_relocation=True)
    data,reloc,receipt=owner.finish();menu=bytearray(files[PARENT].extract(base))
    allocation=resize(menu,core,vrom=VROM,ram=CAT_RAM,offset=0x2C90,
        before=len(owner.original),after=len(data))
    d['menu_allocations'].append(allocation);e['pocket_icons']['owner_sha256']=sha256(menu)
    d['paper']['catalogue']=dict(receipt,descriptor=descriptor,list_address=appended,
        rows=65,native_rows=64,additional_index=67,additional_item=0x2043,
        drawing_style=64,vrom=VROM,reloc=RELOC,ram=CAT_RAM,
        code=compiled,
        additional_menu_bytes=allocation['additional_pool_bytes'],native_rendering_verified=False)
    cat.update(bytes=len(data),output_sha256=sha256(data),relocation_bytes=len(reloc),relocation_sha256=sha256(reloc))
    start=entry-CAT_RAM;cat['code']['sha256']=sha256(data[start:start+cat['code']['bytes']])
    changes={VROM:data,RELOC:reloc,PARENT:bytes(menu)}
    resizes=[dict(vrom=v,previous_bytes=files[v].size,previous_sha256=sha256(files[v].extract(base)),
        bytes=len(raw),sha256=sha256(raw)) for v,raw in changes.items() if len(raw)!=files[v].size]
    growth=[]
    for row in resizes:
        v=row['vrom'];_,record=relocate_resource_plan(base,files,v,changes[v],minimum_physical=0x100000,
            reservations=resources+growth,append_only=False,allow_compressed=True)
        growth.append(record)
    return changes,cat,resizes,growth
