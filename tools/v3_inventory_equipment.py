"""Shared inventory-owner integration for installed static handheld categories."""
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


def records(source,equipment):
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
    for parent in parents['rows']:
        kind=kind_rows[parent['item_id']];world=parent['native_kind']
        source_kind=world-36
        if kinds.count(source_kind)!=1:raise ValueError('Ambiguous inventory equipment kind')
        iv_kind=kinds.index(source_kind);preview=iv_kind+1
        if preview<6 or preview>=COUNT or pointers[iv_kind*4][3]!=0x272454:
            raise ValueError('Unimplemented inventory held-drawing category')
        animation,_,shape,_,_,_=kind['fields']
        model=resources[shape];motion=motions[animation]
        if (model['kind']!='static-model' or model['type']!=0 or model['bytes']>4376
                or not kind['resource_ready'] or motion['bytes']>3848 or motion['type']>=5):
            raise ValueError('Inventory equipment exceeds installed loader/rig support')
        item=int(parent['item_id'],16)
        struct.pack_into('>HBB',selector,16+(item-0x2224)*4,item,preview,world)
        # Static models have no skeleton; the native loader skips item animation.
        rows.append(dict(id=parent['id'],item_id=parent['item_id'],source_kind=source_kind,
            source_preview_kind=iv_kind,preview_kind=preview,world_kind=world,
            fields=dict(player_animation=animation,player_pointer=motion['pointer'],
                item_animation=17,item_pointer=0,shape=shape,skeleton=0,part=motion['type']),
            model_bytes=model['bytes'],model_sha256=model['sha256'],
            animation_bytes=motion['bytes'],animation_sha256=motion['sha256'],selectable=False))
    if len({r['preview_kind'] for r in rows})!=len(rows):
        raise ValueError('Colliding native inventory preview kinds')
    return bytes(selector),dict(format='AFV3-INVENTORY-EQUIPMENT-1',rows=rows,
        source_functions=functions,source_kind_hex=kinds.hex(),
        source_draw_table=dict(symbol=name,offset=at,bytes=n,pointers=pointers),
        original_kinds=5,empty_kind=5,count=COUNT,profile_bits_enabled=0,
        ordinary_inventory_tested=False,save_reload_tested=False)


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
