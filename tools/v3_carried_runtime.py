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
