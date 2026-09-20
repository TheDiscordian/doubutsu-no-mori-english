"""Shared inventory-owner integration for complete static and animated equipment."""
import copy
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from v3_asset_loader import ROOT,BLOB,compile_part
from v3_equipment_runtime import RAM,GUARD
from v3_furniture_pipeline import Source
from v3_import_storage import END,jump
from v3_npc_clothing import guard_incoming

VROM,RELOC,OWNER_RAM=0x785700,0x7898C0,0x8087D480
SECTIONS=(15664,1008,160,1504)
CODE,TABLE,SELECTOR,SIZE=0x6000,0x6400,0x6C00,0x7000
COUNT=41  # Forty donor preview kinds plus retained native empty sentinel five.
MENU_VROM,MENU_RELOC,MENU_RAM=0x7749C0,0x7778B0,0x8085BAC0
TABLES=(('player_animation',0x80881310),('player_pointer',0x80881324),
        ('item_animation',0x80881338),('item_pointer',0x8088134C),
        ('shape',0x80881360),('skeleton',0x80881374),('part',0x80881388),('draw',0x8088149C))
FUNCTIONS=(
    (0x271204,720,'d583c128496f11539d83b42627ee113d532fa18c846184ee875ce7de02f098fc'),
    (0x2714D4,48,'1613d030e406ae1200a86da11ba0af97492defcacb18510310f2872bd508f70c'),
    (0x271504,88,'73040bcfb9c8197916f5d91459757f4852bd7656ea7bbf7a54475aafb8b35614'),
    (0x27155C,104,'4445bef6a00d60fb2c9373b26bee3a9242ba86c209d576df1d8b7beb952fc0ec'),
    (0x2715C4,36,'e8a6518ed598efcc859c75656cee77e9b32a81efd51854371016c6427cb54faf'),
    (0x2715E8,36,'c0c5b9d5dc16377d49a616337b9b10bc96a147b94419ce15f43f60afbdb3b283'),
    (0x27160C,40,'8034c6175aa00aa2f01e4f9789381d16d0c93ef779f86dcaeeac969d0527cc4d'),
    (0x271634,80,'8f2cd97ff226ed271f1341b599ab3ec832e932dd6bc2166661e15299ad274f58'),
    (0x271684,60,'dad8e86752d26fc767661f46a1a80f59e92778c439b2c54cf3f9b7045b989a23'),
    (0x2716FC,808,'896df698df4877431eda0f955ce962260ded4e0f62047c34528d0a42c9807029'),
    (0x272454,92,'0dc3803e01aa021475b87aecb8c592474abbb373d047f95972a9fb2df0cbfccb'),
    (0x272524,156,'7d0497e25b735edec49669876912fa0ba67d4c0a9609bd41cfff3075ef6ff353'))


def records(source,equipment,*,animated=False,balloon_callback=None):
    """Join actual inventory kinds/callbacks to installed equipment resources."""
    from v3_handheld_items import parent_records
    _,parents=parent_records(source,equipment)
    if parents['rows']!=equipment['parent_readers']['rows']:
        raise ValueError('Inventory preview requires the installed parent records')
    functions=[]
    for at,n,digest in FUNCTIONS:
        raw,receipt=source.function(at)
        if len(raw)!=n or sha256(raw)!=digest:
            raise ValueError('Changed complete donor inventory consumer')
        functions.append(receipt)
    mapping=functions[1];high=mapping['relocations'].get(22)
    if high!=(6,1,4,0xA258) or mapping['relocations'].get(26)!=(4,1,4,0xA258):
        raise ValueError('Changed donor inventory-kind table binding')
    start=source.sections[4][0]+high[3];kinds=source.rel[start:start+40]
    if sha256(kinds)!='3d9c15666f1f00a12cb72b146f2ed16e18c012038afb564c1b5eb8f6312fb5e3':
        raise ValueError('Changed complete donor inventory-kind map')
    draw=functions[-1];high=draw['relocations'].get(98)
    if high!=(6,1,5,0x80078) or draw['relocations'].get(102)!=(4,1,5,0x80078):
        raise ValueError('Changed donor inventory drawing-table binding')
    name,at,n=source.containing(high[3],exact=True)
    pointers={p-at:r for p,r in source.relocations.items() if at<=p<at+n}
    if (n!=40*4 or any(source.data[at:at+n]) or set(pointers)!=set(range(0,n,4))
            or any(r[:3]!=(1,True,1) for r in pointers.values())):
        raise ValueError('Incomplete or foreign inventory drawing callbacks')
    resources={r['index']:r for r in equipment['records']}
    motions={r['index']:r for r in equipment['player_motion']['records']}
    kind_rows={r['item_id']:r for r in equipment['kind_readers']['rows']}
    selector=bytearray(struct.pack('>4I',0x41464956,1,56,4)+bytes(56*4));rows=[]
    candidates=list(parents['rows'])
    if balloon_callback is None:
        balloon_callback=equipment.get('inventory_preview',{}).get('balloon_drawer',{}).get('address')
    if balloon_callback is not None and (not animated or not RAM+CODE<=balloon_callback<RAM+TABLE
            or not equipment.get('held_rig_actions',{}).get('balloon')):
        raise ValueError('Balloon preview requires the checked category and resident drawer')
    if animated:
        from v3_handheld_items import discover
        if not equipment.get('held_rig_actions',{}).get('loop_sound_installed'):
            raise ValueError('Animated inventory requires the complete installed rig actions')
        identities={r['item_id']:r for r in discover(source)['rows']}
        installed={r['item_id'] for r in candidates}
        for kind in kind_rows.values():
            if kind['item_main'] in ((21,22) if balloon_callback else (22,)) and kind['item_id'] not in installed:
                original=identities[kind['item_id']]
                candidates.append(dict(id=original['id'],item_id=kind['item_id'],native_kind=kind['native_kind']))
        raw,function=source.function(0x2723F4)
        if len(raw)!=96 or sha256(raw)!='12815662833de2f10cfbcfe2c16bc04cbf10cc5d5b8c0a37725ea780e9353c6a':
            raise ValueError('Changed complete source animated preview drawer')
        functions.append(function)
        if balloon_callback:
            for at in (0x272290,0x2722E8,0x272340):functions.append(source.function(at)[1])
    for parent in candidates:
        kind=kind_rows[parent['item_id']];world=parent['native_kind']
        source_kind=world-36
        if kinds.count(source_kind)!=1:raise ValueError('Ambiguous inventory equipment kind')
        iv_kind=kinds.index(source_kind);preview=iv_kind+1
        callback=pointers[iv_kind*4][3]
        balloon=bool(balloon_callback) and callback==0x272340
        rig=animated and (callback==0x2723F4 or balloon)
        callbacks=(0x272454,0x2723F4,0x272340) if balloon_callback else ((0x272454,0x2723F4) if animated else (0x272454,))
        if preview<6 or preview>=COUNT or callback not in callbacks:
            raise ValueError('Unimplemented inventory held-drawing category')
        animation,_,shape,item_animation,_,_=kind['fields']
        if balloon:
            # The complete pinned mIV_Get_player_item_anime_index consumer
            # maps source BALLOON_GYAZA (32) to BALLOON_WAIT (31) in menus.
            if item_animation!=17+32:raise ValueError('Changed source balloon animation remap')
            item_animation=17+31
        model=resources[shape];motion=motions[animation]
        if not kind['resource_ready'] or motion['bytes']>3848 or motion['type']>=5:
            raise ValueError('Inventory equipment exceeds installed loader/rig support')
        if rig:
            item_motion=resources[item_animation];skeleton=model['source']['skeleton']
            vectors=equipment['inventory_preview'].get('joint_work',{}).get('vectors',7)
            if (model['kind']!='animated-model' or model['type']!=1 or kind['item_main']!=(21 if balloon else 22)
                    or not 0<skeleton['shown_joints']<=min(skeleton['joints'],4)
                    or skeleton['joints']+1>vectors
                    or item_motion['kind']!='animation' or item_motion['type']!=(4 if balloon else 5)
                    or item_motion['source']['joints']!=skeleton['joints']
                    or model['bytes']+item_motion['bytes']>equipment['inventory_preview']['item_bank_bytes']):
                raise ValueError('Animated preview exceeds native bank or joint work capacity')
        elif model['kind']!='static-model' or model['type']!=0 or model['bytes']>4376:
            raise ValueError('Static preview exceeds installed loader support')
        item=int(parent['item_id'],16)
        struct.pack_into('>HBB',selector,16+(item-0x2224)*4,item,preview,world)
        # Static models have no skeleton; the native loader skips item animation.
        rows.append(dict(id=parent['id'],item_id=parent['item_id'],source_kind=source_kind,
            source_preview_kind=iv_kind,preview_kind=preview,world_kind=world,
            fields=dict(player_animation=animation,player_pointer=motion['pointer'],
                item_animation=item_animation if rig else 17,item_pointer=item_motion['pointer'] if rig else 0,
                shape=shape,skeleton=model['pointer'] if rig else 0,part=motion['type']),
            model_bytes=model['bytes'],model_sha256=model['sha256'],
            animation_bytes=motion['bytes'],animation_sha256=motion['sha256'],selectable=False))
        if rig:
            rows[-1].update(draw_callback=balloon_callback if balloon else 0x8087E098,item_animation_bytes=item_motion['bytes'],
                item_animation_sha256=item_motion['sha256'],joint_vectors=skeleton['joints']+1,
                source_frame_speed=.5 if balloon else 7.5,native_frame_speed=1.0 if balloon else 15.0)
    if len({r['preview_kind'] for r in rows})!=len(rows):
        raise ValueError('Colliding native inventory preview kinds')
    return bytes(selector),dict(format='AFV3-INVENTORY-EQUIPMENT-1',rows=rows,
        source_functions=functions,source_kind_hex=kinds.hex(),
        source_draw_table=dict(symbol=name,offset=at,bytes=n,pointers=pointers),
        original_kinds=5,empty_kind=5,count=COUNT,profile_bits_enabled=0,
        ordinary_inventory_tested=False,save_reload_tested=False)


def grow_joint_work(base,prior,blob,core,original,output):
    """Grow the inventory's own complete work arrays and submenu reservation."""
    from v3_npc_draw import relocation_offsets
    old=prior['equipment_resources'];preview=old['inventory_preview']
    files,native=by_vrom(base),by_vrom(original)
    owner=bytearray(files[VROM].extract(base));rel=bytearray(files[RELOC].extract(base))
    module=blob[old['blob_offset']:old['blob_offset']+old['bytes']]
    previous=preview.get('joint_work');vectors=old['player_joint_work']['vectors']
    sections=struct.unpack_from('>5I',rel)
    if (sha256(owner)!=preview['owner_sha256'] or sha256(rel)!=preview['relocation_sha256']
            or sha256(module)!=old['sha256'] or not preview.get('animated_rigs_installed')
            or sections[:3]!=SECTIONS[:3] or not 7<vectors<=16
            or previous and vectors<=previous['vectors']):
        raise ValueError('Changed inventory work owner or unsupported capacity')
    normalized=bytearray(owner)
    for patch in preview['patches']+[preview['animation_speed_hook']]:
        at=patch['address']-OWNER_RAM
        if u32(normalized,at)!=patch['after']:raise ValueError('Changed installed inventory consumer')
        struct.pack_into('>I',normalized,at,patch['before'])
    if previous:
        if sections[3]!=previous['bss_bytes']:raise ValueError('Changed previous inventory BSS size')
        for patch in previous['patches']:
            at=patch['address']-OWNER_RAM
            if u32(normalized,at)!=patch['after']:raise ValueError('Changed installed inventory work pointer')
            struct.pack_into('>I',normalized,at,patch['before'])
    elif sections[3]!=SECTIONS[3]:raise ValueError('Changed native inventory BSS size')
    original_owner=native[VROM].extract(original)
    first,last=0x8087D5A4-OWNER_RAM,0x8087DAA0-OWNER_RAM
    if normalized[first:last]!=original_owner[first:last]:
        raise ValueError('Changed complete native inventory initializer')
    targets={0x8087D9AC:0x2BE,0x8087D9BC:0x294}
    found={OWNER_RAM+i:u32(normalized,i)&65535 for i in range(0,sections[0],4)
           if u32(normalized,i)>>26==9 and u32(normalized,i)>>21&31 and u32(normalized,i)&65535 in (0x294,0x2BE)}
    if found!=targets:raise ValueError('Unreviewed inventory work-pointer consumer')
    start=previous['joint_offset'] if previous else sections[3]
    length=vectors*6;bss=(start+2*length+15)&~15
    offsets={0x294:start,0x2BE:start+length};patches=[]
    relocations=relocation_offsets(rel,len(owner))
    for address,old_offset in targets.items():
        at=address-OWNER_RAM;word=u32(normalized,at)
        if at in relocations or offsets[old_offset]>=32768:raise ValueError('Invalid inventory work pointer')
        changed=word&0xFFFF0000|offsets[old_offset];struct.pack_into('>I',owner,at,changed)
        patches.append(dict(address=address,before=word,after=changed))
    struct.pack_into('>I',rel,12,bss)
    old_resident=sum(sections[:4]);resident=sum(sections[:3])+bss
    menu=bytearray(files[MENU_VROM].extract(base));native_menu=native[MENU_VROM].extract(original)
    entries=[i for i in range(0,len(menu)-31,4) if u32(menu,i)==VROM]
    if entries!=[0x2A10,0x2A30]:raise ValueError('Changed complete inventory allocation-owner table')
    metadata=[]
    for at in entries:
        before=bytes(menu[at:at+32]);normal=bytearray(before)
        if struct.unpack_from('>4I',normal)!=(VROM,VROM+len(owner),OWNER_RAM,OWNER_RAM+old_resident):
            raise ValueError('Changed inventory owner allocation')
        struct.pack_into('>I',normal,12,OWNER_RAM+sum(SECTIONS))
        if normal!=native_menu[at:at+32]:raise ValueError('Changed inventory lifecycle or metadata')
        struct.pack_into('>I',menu,at+12,OWNER_RAM+resident)
        metadata.append(dict(offset=at,before=before.hex(),after=menu[at:at+32].hex()))
    # The shared loader advances each inventory allocation by ALIGN64(size).
    # Both menu identities use the same owner, one in each mutually exclusive
    # menu path. Grow the common maximum by its complete aligned difference.
    extra=((resident+63)&~63)-((old_resident+63)&~63)
    pool_at=0x800C4B10-CODE_RAM;pool_before=u32(core,pool_at)
    if pool_before>>16!=0x25CE or extra<=0 or (pool_before&65535)+extra>=65536:
        raise ValueError('Inventory growth exceeds checked submenu immediate')
    pool_after=pool_before+extra
    if (pool_before^pool_after)&0x8000:raise ValueError('Submenu growth crosses a signed immediate boundary')
    struct.pack_into('>I',core,pool_at,pool_after)
    # Bind the allocation/rounding consumer itself, not just the metadata.
    # Locate the complete loader through the native symbol map.
    import re
    text=(ROOT/'upstream/af/linker_scripts/jp/symbol_addrs_overlays.txt').read_text()
    match=re.search(r'^mSM_ovl_prog_seg = 0x([0-9A-Fa-f]+);',text,re.M)
    if not match:raise ValueError('Missing native submenu allocation function')
    address=int(match[1],16)
    bounds=sorted(int(x,16) for x in re.findall(r'= 0x([0-9A-Fa-f]+); // type:func',text))
    loader_first=address-MENU_RAM;loader_last=min(x for x in bounds if x>address)-MENU_RAM
    if menu[loader_first:loader_last]!=native_menu[loader_first:loader_last]:
        raise ValueError('Changed complete submenu allocation consumer')
    receipt=dict(vectors=vectors,previous_vectors=previous['vectors'] if previous else 7,
        joint_offset=start,morph_offset=start+length,array_bytes=length,previous_bss_bytes=sections[3],
        bss_bytes=bss,previous_resident_bytes=old_resident,resident_bytes=resident,
        additional_bss_bytes=bss-sections[3],additional_pool_bytes=extra,patches=patches,
        metadata=metadata,pool_patch=dict(address=CODE_RAM+pool_at,before=pool_before,after=pool_after),
        initializer=dict(start=OWNER_RAM+first,end=OWNER_RAM+last,sha256=sha256(owner[first:last])),
        allocation_consumer=dict(start=MENU_RAM+loader_first,end=MENU_RAM+loader_last,
                                 sha256=sha256(menu[loader_first:loader_last])),
        saved_format_changed=False,preview_records_changed=False)
    report=copy.deepcopy(old);report['inventory_preview'].update(joint_work=receipt,
        owner_sha256=sha256(owner),relocation_sha256=sha256(rel))
    report['additional_resident_bytes']=0
    return report,{VROM:bytes(owner),RELOC:bytes(rel),MENU_VROM:bytes(menu)}


def refresh_rigs(base,prior,blob,core,original,output):
    """Connect every installed supported rig through the existing preview tables."""
    old=prior['equipment_resources'];preview=old['inventory_preview'];offset=old['blob_offset']
    module=bytearray(blob[offset:offset+old['bytes']]);files=by_vrom(base)
    owner=files[VROM].extract(base);rel=files[RELOC].extract(base)
    extend=bool(preview.get('animated_rigs_installed'))
    if ((extend and (preview.get('balloon_drawer') or not old.get('held_rig_actions',{}).get('balloon')))
            or sha256(module)!=old['sha256']
            or sha256(owner)!=preview['owner_sha256'] or sha256(rel)!=preview['relocation_sha256']):
        raise ValueError('Animated previews require the checked current inventory module')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    selector,generated=records(source,old,animated=True)
    indices=sorted(r['preview_kind'] for r in generated['rows'] if r.get('draw_callback'))
    if not indices or indices!=list(range(indices[0],indices[-1]+1)):
        raise ValueError('Animated preview speed category is not a complete contiguous donor range')
    _,init=source.function(0x2716FC);constant=init['relocations'].get(610)
    if (constant!=(4,1,4,41608) or
            source.rel[source.sections[4][0]+41608:source.sections[4][0]+41612]!=struct.pack('>f',7.5)):
        raise ValueError('Changed donor animated inventory speed')
    native=by_vrom(original)[VROM].extract(original)
    first,last=0x8087E098-OWNER_RAM,0x8087E108-OWNER_RAM
    if (owner[first:last]!=native[first:last] or
            sha256(owner[first:last])!='aa2407b27fc7dd177028984f1a08d34b8fe47d5e7ca196641ca41d624cb2df0a'):
        raise ValueError('Changed native null-callback skeleton drawer')
    defines=(
        f'AF_V3_HELD_SELECTED=0x{old["player_actions"]["code"]["symbols"]["af_v3_player_selected_equipment"]:08X}u',
        f'AF_V3_INVENTORY_RIG_FIRST={indices[0]}',f'AF_V3_INVENTORY_RIG_COUNT={len(indices)}')
    if extend:defines+=('AF_V3_INVENTORY_BALLOON',)
    code,compiled=compile_part('inventory_equipment',output/'inventory_equipment',
        extra_sources=('overlays/v3/inventory_equipment.S',),defines=defines)
    if extend:
        selector,generated=records(source,old,animated=True,
            balloon_callback=compiled['symbols']['af_v3_inventory_balloon_draw'])
        retained={r['item_id']:r for r in preview['rows']}
        if any(retained.get(r['item_id'],r)!=r for r in generated['rows']):
            raise ValueError('Preview expansion changes an existing category binding')
    added=[r for r in generated['rows'] if r['item_id'] not in {p['item_id'] for p in preview['rows']}]
    if not added:raise ValueError('No new complete preview category')
    previous=preview['code'];n=previous['bytes']
    if (sha256(module[CODE:CODE+n])!=previous['sha256'] or any(module[CODE+n:TABLE])
            or len(code)>TABLE-CODE):raise ValueError('Changed or overlapping inventory code reservation')
    stable_symbols=['af_v3_inventory_item_kind','af_v3_inventory_static_draw','af_v3_inventory_dispatch']
    if extend:stable_symbols.append('af_v3_inventory_rig_init')
    for symbol in stable_symbols:
        if compiled['symbols'][symbol]!=previous['symbols'][symbol]:
            raise ValueError('Animated preview changed an installed inventory entry')
    receipt=copy.deepcopy(preview);receipt.update(generated)
    for table in receipt['tables']:
        at,n=table['offset'],table['bytes'];data=bytearray(module[at:at+n])
        if sha256(data)!=table['sha256']:raise ValueError('Changed complete inventory table')
        for row in added:
            p=row['preview_kind']*4
            if any(data[p:p+4]):raise ValueError('Animated preview slot is already occupied')
            value=row['draw_callback'] if table['role']=='draw' else row['fields'][table['role']]
            struct.pack_into('>I',data,p,value)
        module[at:at+n]=data;table['sha256']=sha256(data)
    if sha256(module[SELECTOR:SELECTOR+preview['selector_bytes']])!=preview['selector_sha256']:
        raise ValueError('Changed inventory selector')
    module[SELECTOR:SELECTOR+len(selector)]=selector
    module[CODE:TABLE]=code+bytes(TABLE-CODE-len(code))
    hook=0x8087DA64;at=hook-OWNER_RAM
    expected=preview['animation_speed_hook']['after'] if extend else jump(0x80052584,link=True)
    if u32(owner,at)!=expected:raise ValueError('Changed native skeleton initializer call')
    words=struct.unpack_from('>5I',rel)
    if any((r&0xFFFFFF)==at for r in struct.unpack_from('>'+str(words[4])+'I',rel,20)):
        raise ValueError('Unexpected initializer JAL relocation')
    patched=bytearray(owner);after=jump(compiled['symbols']['af_v3_inventory_rig_init'],link=True)
    struct.pack_into('>I',patched,at,after)
    receipt.update(code=compiled,selector_sha256=sha256(selector),selector_bytes=len(selector),
        animated_rigs_installed=True,owner_sha256=sha256(patched),previous_owner_sha256=sha256(owner),
        animated_rig_indices=indices,additional_resident_bytes=0,
        animated_drawer=dict(start=OWNER_RAM+first,end=OWNER_RAM+last,sha256=sha256(owner[first:last])),
        animation_speed_hook=preview['animation_speed_hook'] if extend else dict(
            address=hook,before=u32(owner,at),after=after,source_speed=7.5,native_speed=15.0))
    if extend:
        native_core=by_vrom(original)[CODE_VROM].extract(original)
        first_api,last_api=0x80058620,0x80058810
        if core[first_api-CODE_RAM:last_api-CODE_RAM]!=native_core[first_api-CODE_RAM:last_api-CODE_RAM]:
            raise ValueError('Changed complete native inventory reflection API')
        receipt['balloon_drawer']=dict(address=compiled['symbols']['af_v3_inventory_balloon_draw'],
            preview_indices=sorted(r['preview_kind'] for r in added),source_frame_speed=.5,native_frame_speed=1,
            reflection_origin=[0,0,0],reflection_eye=[0,0,1],
            reflection_light=[-.5773502691896257,.5773502691896257,.5773502691896257],
            native_reflection_api=0x80058620,native_skeleton_api=0x800530D8,
            reflection_api_sha256=sha256(core[first_api-CODE_RAM:last_api-CODE_RAM]),
            source_animation_remap=dict(outdoor=32,inventory=31,native_outdoor=49,native_inventory=48),
            edge_alpha='Native RDP coverage, without GameCube-only GX threshold commands')
        receipt['balloon_drawer']['source_functions']=generated['source_functions'][-3:]
    blob[offset:offset+len(module)]=module
    report=copy.deepcopy(old);report.update(inventory_preview=receipt,sha256=sha256(module),
        crc32=zlib.crc32(module),additional_resident_bytes=0)
    if extend:report['held_rig_actions']['balloon']['inventory_preview_installed']=True
    return report,{} if extend else {VROM:bytes(patched)}


def install(base,prior,blob,core,original,output):
    from v3_player_actions import native_references
    old=prior['equipment_resources'];offset=old['blob_offset']
    module=bytearray(blob[offset:offset+old['bytes']])
    if (old.get('inventory_preview') or old['bytes']!=CODE or sha256(module)!=old['sha256']
            or RAM+SIZE>prior['furniture']['bank_pool']['start']):
        raise ValueError('Changed inventory-preview module or reservation')
    files,native=by_vrom(base),by_vrom(original)
    owner=files[VROM].extract(base);rel=files[RELOC].extract(base)
    original_owner=native[VROM].extract(original)
    if (sha256(owner)!='ff3fd977b79afd74cecefc96fc8d16980c63e50b78c32889baeccebcfa54609e'
            or sha256(rel)!='293144ece2c17e612c32ea2ad4ff8b588c6f2e1ad7a1450869ef6499e4e47eab'):
        raise ValueError('Changed complete current inventory owner/relocations')
    # These complete native consumers also bind constructor BSS ownership,
    # model/animation banks, main-state switches, and original render timing.
    consumers=[]
    for first,last in ((0x8087D51C,0x8087E628),(0x80881030,0x80881144)):
        a,b=first-OWNER_RAM,last-OWNER_RAM
        if owner[a:b]!=original_owner[a:b]:raise ValueError('Changed native inventory equipment consumer')
        consumers.append(dict(start=first,end=last,sha256=sha256(owner[a:b])))
    native_core=native[CODE_VROM].extract(original)
    bank=0x8010DDD0+35*8-CODE_RAM
    bounds=struct.unpack_from('>2I',core,bank)
    if core[bank:bank+8]!=native_core[bank:bank+8] or bounds[1]-bounds[0]<4376:
        raise ValueError('Inventory item bank cannot hold complete imported models')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    selector,receipt=records(source,old)
    code,compiled=compile_part('inventory_equipment',output/'inventory_equipment',
        extra_sources=('overlays/v3/inventory_equipment.S',),defines=(
            f'AF_V3_HELD_SELECTED=0x{old["player_actions"]["code"]["symbols"]["af_v3_player_selected_equipment"]:08X}u',))
    if len(code)>TABLE-CODE:raise ValueError('Inventory preview code exceeds reservation')
    groups,absolute,relocations,locations,slots=native_references(owner,rel,expected_sections=SECTIONS)
    patched=bytearray(owner);tables=[];data=bytearray();removed=set();patches=[]
    def patch(at,word):
        patches.append(dict(address=OWNER_RAM+at,before=u32(patched,at),after=word))
        struct.pack_into('>I',patched,at,word)
    for role,target in TABLES:
        first=target-OWNER_RAM;values=list(struct.unpack_from('>5I',owner,first))+[0]*(COUNT-5)
        for row in receipt['rows']:
            values[row['preview_kind']]=(compiled['symbols']['af_v3_inventory_static_draw']
                                        if role=='draw' else row['fields'][role])
        at=TABLE+len(data);address=RAM+at;raw=struct.pack('>'+str(COUNT)+'I',*values)
        data.extend(raw);pairs=[]
        for hi,lows in groups.items():
            if any(target<=p<target+20 for _,p in lows):
                if any(p!=target for _,p in lows):raise ValueError('Shared or interior inventory table reference')
                pairs.extend((hi,lo) for lo,_ in lows)
        if len(pairs)!=1 or any(target<=p<target+20 for p in absolute.values()):
            raise ValueError('Incomplete inventory table reference coverage')
        for hi,lo in pairs:
            for p,part in ((hi,(address+0x8000)>>16),(lo,address&65535)):
                if p in removed:raise ValueError('Overlapping inventory references')
                patch(p,u32(owner,p)&0xFFFF0000|part);removed.add(p)
        tables.append(dict(role=role,native=target,ram=address,offset=at,bytes=len(raw),
            sha256=sha256(raw),native_sha256=sha256(owner[first:first+20]),
            references=[(OWNER_RAM+a,OWNER_RAM+b) for a,b in pairs]))
    entry=0x8087D51C-OWNER_RAM;dispatch=0x8087E610-OWNER_RAM
    guard_incoming(owner,SECTIONS[0],OWNER_RAM,[(entry,8)])
    if (u32(owner,entry)!=0x3C0E8013 or u32(owner,entry+4)!=0x8DCE6FD8
            or u32(owner,dispatch)!=0x0320F809 or dispatch in slots):
        raise ValueError('Changed inventory kind entry or callback call')
    if any(p in locations for p in (entry,entry+4)):
        raise ValueError('Unexpected relocation of the fixed player-private pointer')
    patch(entry,jump(compiled['symbols']['af_v3_inventory_item_kind']));patch(entry+4,0)
    patch(dispatch,jump(compiled['symbols']['af_v3_inventory_dispatch'],link=True))
    kept=[r for r in relocations if r not in {locations[p] for p in removed}]
    relocation=bytearray(rel);struct.pack_into('>I',relocation,16,len(kept))
    relocation[20:-4]=struct.pack('>'+str(len(kept))+'I',*kept)+bytes(len(rel)-24-len(kept)*4)
    if TABLE+len(data)>SELECTOR or SELECTOR+len(selector)>SIZE-16:
        raise ValueError('Inventory preview tables overlap reserved data')
    module.extend(bytes(SIZE-len(module)));module[CODE:CODE+len(code)]=code
    module[TABLE:TABLE+len(data)]=data;module[SELECTOR:SELECTOR+len(selector)]=selector
    struct.pack_into('>4I',module,SIZE-16,*([GUARD]*4))
    blob.extend(bytes(-len(blob)%16));position=len(blob);blob.extend(module)
    if BLOB+len(blob)>END:raise ValueError('Inventory preview exceeds import storage')
    receipt.update(code=compiled,code_offset=CODE,tables=tables,selector_offset=SELECTOR,
        selector_sha256=sha256(selector),selector_bytes=len(selector),patches=patches,
        removed_relocations=[locations[p] for p in sorted(removed)],owner_vrom=VROM,
        owner_sha256=sha256(patched),previous_owner_sha256=sha256(owner),
        relocation_vrom=RELOC,relocation_sha256=sha256(relocation),
        native_consumers=consumers,item_bank_bytes=bounds[1]-bounds[0],
        native_bss_address=0x80881640,native_bss_pointer_offset=0x106DC,
        saved_format_changed=False,additional_resident_bytes=SIZE-old['bytes'])
    report=copy.deepcopy(old);report['inventory_preview']=receipt
    report.update(bytes=SIZE,vrom=BLOB+position,blob_offset=position,
        sha256=sha256(module),crc32=zlib.crc32(module),additional_resident_bytes=SIZE-old['bytes'])
    return report,{VROM:bytes(patched),RELOC:bytes(relocation)}
