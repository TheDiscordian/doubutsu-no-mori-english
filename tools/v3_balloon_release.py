"""Shared release/look/fall consumers for all selected balloon shapes."""
import copy
import json
import re
import struct
import zlib
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from v3_asset_loader import ROOT,compile_part
from v3_equipment_runtime import RAM,PLAYER_RAM,PLAYER_VROM,PLAYER_RELOC
from v3_furniture_pipeline import Source
from v3_import_storage import jump
from v3_npc_draw import relocation_offsets
from v3_npc_clothing import guard_incoming

GROUPS=(('balloon_release',0xE100,0xE800),('balloon_look',0xBAA0,0xBF00),
        ('balloon_fall',0x9BE0,0x9FF0))
SOURCES=('tools/v3_balloon_release.py','overlays/v3/balloon_release.h',
         'overlays/v3/balloon_menu.c','overlays/v3/balloon_menu.ld','overlays/v3/held_collection.ld',
         'translations/provenance.json',
         'overlays/v3/reward_exchange.c','overlays/v3/reward_exchange.ld',
         'overlays/v3/balloon_actor.h','overlays/v3/balloon_actor.ld','overlays/v3/held_rigs.ld')+tuple(
    'overlays/v3/'+name+suffix for name,_,_ in GROUPS for suffix in ('.c','.ld'))


def bindings(source,core,owner,original):
    sources=[]
    for start,end in ((0x18E96C,0x18F58C),(0x177F98,0x178340),(0x1706F0,0x170738),
                      (0x69C10,0x69C84),(0x28781C,0x287B88)):
        at=start
        while at<end:
            data,row=source.function(at);sources.append(row);at+=len(data)
        if at!=end:raise ValueError('Incomplete donor release/get-up function group')
    bounds=[]
    for name in ('symbol_addrs_code.txt','symbol_addrs_overlays.txt'):
        bounds.extend(int(a,16) for a in re.findall(r'= 0x([0-9A-Fa-f]+); // type:func',
            (ROOT/'upstream/af/linker_scripts/jp'/name).read_text()))
    native=[];files=by_vrom(original)
    for at in (0x8007D90C,0x80099A54,0x80099A94,0x8009A974,0x800B1C84,0x800B1F74,
               0x800DADC4,0x800E0008,0x808D71F8,0x808D72E0,0x808D7570,0x808D787C,
               0x808B846C,0x808B4924,0x808B3BD0,0x808C1064,0x808C32F4,0x808C33A0):
        data,ram,vrom=(owner,PLAYER_RAM,PLAYER_VROM) if at>=PLAYER_RAM else (core,CODE_RAM,CODE_VROM)
        end=min(x for x in bounds if x>at);raw=data[at-ram:end-ram]
        if raw!=files[vrom].extract(original)[at-ram:end-ram]:
            raise ValueError(f'Changed native release API {at:08X}')
        native.append(dict(entry=at,end=end,sha256=sha256(raw)))
    return dict(source_functions=sources,native_functions=native,source_steps_per_update=2,
        native_head_tracking_updates=30,native_minimum_release_updates=42,
        continuation_offset=0x13A4,fallen_shape_offset=0x13A8,equipped_offset=0x3EC,
        original_fish_insect_look_retained=True)


def install(base,prior,blob,core,original,output):
    old=prior['equipment_resources'];actions=old['player_actions'];files=by_vrom(base)
    start=old['blob_offset'];module=bytearray(blob[start:start+old['bytes']])
    owner=bytearray(files[PLAYER_VROM].extract(base));rel=files[PLAYER_RELOC].extract(base)
    if (not actions.get('balloon_actor') or actions.get('balloon_release') or old['bytes']!=0x12000
            or sha256(module)!=old['sha256'] or sha256(owner)!=actions['owner_sha256']
            or sha256(rel)!=actions['relocation_sha256']):
        raise ValueError('Balloon release requires the checked complete flying actor')
    flying=actions['balloon_actor'];rig=old['held_rig_actions']
    if (flying['offset']+flying['code']['bytes']>0x9BE0 or flying['player_bytes']!=0x13B0 or
            flying['packet_offset']+flying['packet_bytes']!=0xBAA0 or
            rig['code_offset']+rig['code']['bytes']>0xE100):
        raise ValueError('Balloon consumers overlap retained code/state')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    evidence=bindings(source,core,owner,original);codes={};symbols={}
    dependencies={k:v for part in (flying['code'],actions['tool_motion']['code'],actions['code'],
        actions['reward_actions']['requests'],actions['reward_exchange']['codes']['reward_deferred']['code'])
        for k,v in part['symbols'].items()}
    for name,at,end in GROUPS:
        if any(module[at:end]):raise ValueError('Balloon consumer storage is occupied')
        data,compiled=compile_part(name,output/name)
        if len(data)>end-at:raise ValueError('Balloon consumer exceeds checked reservation')
        for key,value in compiled['symbols'].items():
            if key in dependencies and dependencies[key]!=value:raise ValueError('Changed shared dependency: '+key)
            if key in symbols and symbols[key]!=value:raise ValueError('Inconsistent balloon consumer symbol: '+key)
            symbols[key]=value
        module[at:at+len(data)]=data;codes[name]=dict(offset=at,end=end,code=compiled)
    previous_exchange=actions['reward_exchange']['codes']['reward_exchange']
    at,n,end=previous_exchange['offset'],previous_exchange['code']['bytes'],previous_exchange['end']
    if sha256(module[at:at+n])!=previous_exchange['code']['sha256'] or any(module[at+n:end]):
        raise ValueError('Changed complete prior exchange code or occupied suffix')
    code,compiled=compile_part('reward_exchange',output/'reward_exchange',defines=('AF_V3_BALLOON_RELEASE',))
    if at+len(code)>end:raise ValueError('Balloon exchange exceeds checked category reservation')
    for key,value in compiled['symbols'].items():
        if not key.startswith('af_v3_'):continue
        prior_value=symbols.get(key,previous_exchange['code']['symbols'].get(key))
        if prior_value is not None and prior_value!=value:raise ValueError('Changed exchange public dependency: '+key)
    module[at:end]=code+bytes(end-at-len(code))
    codes['reward_exchange']=dict(offset=at,end=end,code=compiled)
    prior_deferred=actions['reward_exchange']['codes']['reward_deferred']['code']['symbols']
    prior_recovery=actions['tool_motion']['code']['symbols']
    plans=((0x808D78D0,(jump(0x808D7570,link=True),),(jump(symbols['af_v3_balloon_look'],link=True),)),
           (0x808D7814,(jump(prior_deferred['af_v3_reward_release_transition']),0),
                        (jump(symbols['af_v3_balloon_release_transition']),0)),
           (0x808C320C,(jump(prior_recovery['af_v3_tool_getup']),0),(jump(symbols['af_v3_balloon_getup']),0)),
           (0x808C33A0,(0x27BDFFE8,0xAFBF0014),(jump(symbols['af_v3_balloon_getup_transition']),0)))
    guard_incoming(owner,u32(rel,0),PLAYER_RAM,[(a-PLAYER_RAM,4*len(b)) for a,b,_ in plans])
    slots=relocation_offsets(rel,len(owner));patches=[]
    removed=[0x44000000|(0x808D78D0-PLAYER_RAM)]
    for at,before,after in plans:
        off=at-PLAYER_RAM;n=4*len(before)
        if struct.unpack_from('>'+str(len(before))+'I',owner,off)!=before:
            raise ValueError('Changed native balloon consumer hook')
        expected={off} if at==0x808D78D0 else set()
        if slots&set(range(off,off+n,4))!=expected:raise ValueError('Unexpected balloon consumer relocation')
        data=struct.pack('>'+str(len(after))+'I',*after)
        patches.append(dict(vrom=PLAYER_VROM,ram=PLAYER_RAM,address=at,before=owner[off:off+n].hex(),after=data.hex()))
        owner[off:off+n]=data
    count=u32(rel,16);rows=list(struct.unpack_from('>'+str(count)+'I',rel,20))
    if any(rows.count(r)!=1 for r in removed):raise ValueError('Missing unique balloon Look relocation')
    kept=[r for r in rows if r not in removed];updated=bytearray(rel)
    struct.pack_into('>I',updated,16,len(kept))
    updated[20:20+count*4]=struct.pack('>'+str(len(kept))+'I',*kept)+bytes(4*len(removed))
    report=copy.deepcopy(old);current=report['player_actions'];callbacks=[]
    mappings={0x808DD874:('af_v3_reward_release_submenu','af_v3_balloon_submenu'),
              0x808DDA18:('af_v3_reward_release_setup','af_v3_balloon_release_setup')}
    for row in current['tables']:
        if row['native_entry'] not in mappings:continue
        at,n=row['offset'],row['bytes'];before,name=mappings[row['native_entry']];slot=at+4*81
        if sha256(module[at:at+n])!=row['sha256'] or u32(module,slot)!=prior_deferred[before]:
            raise ValueError('Changed shared creature callback table')
        callbacks.append(dict(action=81,consumer=row['native_entry'],offset=slot,before=u32(module,slot),after=symbols[name]))
        struct.pack_into('>I',module,slot,symbols[name]);row['sha256']=sha256(module[at:at+n])
    if len(callbacks)!=2:raise ValueError('Incomplete balloon action registration')
    current.update(owner_sha256=sha256(owner),relocation_sha256=sha256(updated),
                   removed_relocations=current['removed_relocations']+len(removed))
    current['balloon_release']=dict(codes=codes,bindings=evidence,patches=patches,callbacks=callbacks,
        removed_relocations=removed,release_action_installed=True,tumble_loss_installed=True,
        ordinary_menu_release_installed=False,exchange_release_installed=True,
        saved_format_changed=False,additional_scene_bytes=0,ordinary_gameplay_tested=False)
    current['balloon_actor']['tumble_loss_installed']=True
    current['reward_exchange']['codes']['reward_exchange']=copy.deepcopy(codes['reward_exchange'])
    current['reward_exchange']['balloon_release_installed']=True
    report['player_motion'].update(owner_sha256=sha256(owner),reloc_sha256=sha256(updated))
    report.update(sha256=sha256(module),crc32=zlib.crc32(module),additional_resident_bytes=0)
    blob[start:start+len(module)]=module
    return report,{PLAYER_VROM:bytes(owner),PLAYER_RELOC:bytes(updated)}


def menu_native_bindings(prior,core,tag,original):
    """Check complete native helpers, including the two established V3 hooks."""
    bounds=[]
    for name in ('symbol_addrs_code.txt','symbol_addrs_overlays.txt'):
        bounds.extend(int(a,16) for a in re.findall(r'= 0x([0-9A-Fa-f]+); // type:func',
            (ROOT/'upstream/af/linker_scripts/jp'/name).read_text()))
    furniture=prior['furniture_menu'];wrapped=prior['equipment_resources']['wrapped_presents']
    site=next(r for r in furniture['sites'] if r['start']==0x80875688)
    pocket=next(r for r in wrapped['hooks'] if r['address']==0x800B8B18)
    hooks={0x80875610:(site['start'],struct.pack('>2I',site['first'],site['second']),
                         struct.pack('>2I',jump(furniture['code']['symbols'][site['symbol']]),0)),
           0x800B8B08:(pocket['address'],bytes.fromhex(pocket['before']),bytes.fromhex(pocket['after']))}
    if hooks[0x800B8B08][2]!=struct.pack('>2I',jump(wrapped['code']['symbols']['af_v3_present_pocket']),0):
        raise ValueError('Changed installed pocket-item hook binding')
    native=[];files=by_vrom(original)
    for at in (0x8086F910,0x8086F4AC,0x80871760,0x80871570,0x80875610,0x800B8B08):
        data,ram,vrom=(tag,0x8086F310,0x777AE0) if at>=0x8086F310 else (core,CODE_RAM,CODE_VROM)
        end=min(x for x in bounds if x>at);raw=data[at-ram:end-ram]
        expected=bytearray(files[vrom].extract(original)[at-ram:end-ram])
        if at in hooks:
            address,before,after=hooks[at];off=address-at
            if expected[off:off+len(before)]!=before:raise ValueError('Changed original menu helper hook')
            expected[off:off+len(before)]=after
        if raw!=expected:raise ValueError(f'Changed complete balloon-menu native API {at:08X}')
        native.append(dict(entry=at,end=end,sha256=sha256(raw)))
    return native


def menu_field_address(tag):
    """Derive the live field byte from the complete native selector's loads."""
    ram=0x8086F310
    a,b,c=(u32(tag,p-ram) for p in (0x80875618,0x8087561C,0x80875698))
    if (a,b,c)!=(0x3C0A8013,0x254A6EA0,0x914F0001):
        raise ValueError('Changed native menu field-address instructions')
    return ((a&65535)<<16)+struct.unpack('>h',struct.pack('>H',b&65535))[0]+(c&65535)


def install_menu(base,prior,blob,core,original,output):
    """Append one shared menu category; preserve all 44 native menu definitions."""
    from v3_player_actions import native_references
    from npc_mail_show import relocate_verified_data
    from catalogue_names import Image
    from text_provenance import validate
    old=prior['equipment_resources'];actions=old['player_actions'];files=by_vrom(base)
    start=old['blob_offset'];module=bytearray(blob[start:start+old['bytes']])
    vrom,rvrom,ram=0x3950000,0x3960000,0x8086F310
    owner_vrom=0x7749C0;owner_ram=0x8085BAC0
    data=bytearray(files[vrom].extract(base));rel=files[rvrom].extract(base)
    menu=bytearray(files[owner_vrom].extract(base));before=bytes(data)
    if (not actions.get('balloon_release',{}).get('exchange_release_installed') or actions.get('balloon_menu')
            or sha256(module)!=old['sha256'] or old['bytes']!=0x12000 or any(module[0xCBF0:0xCFF0])
            or len(data)!=44384 or old['collection']['code']['bytes']>0x1F0
            or sha256(data)!=actions['reward_exchange']['owner_sha256']
            or sha256(rel)!=actions['reward_exchange']['relocation_sha256']):
        raise ValueError('Balloon menu requires complete checked release/exchange and tag owners')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    functions=[source.function(a)[1] for a in (0x28772C,0x28A884,0x69C10,0x27F9A0,0x27F5F4,0x282E54)]
    label=source.raw('mTG_tag_word_fly')
    links={at-0x82DDC:row for at,row in source.relocations.items() if 0x82DDC<=at<0x82DE8}
    if (label!=b'Let Go          '+bytes(4) or
            source.relocations.get(0x82A60)!=(1,1,1,0x28772C) or
            links!={0:(1,1,5,0x82884),4:(1,1,5,0x82A50),8:(1,1,5,0x828E8)}):
        raise ValueError('Changed complete donor balloon menu and handler')
    credit=dict(id='v3/ui/balloon/let-go',native_sha256=None,locales=dict(en=dict(
        credit='official',locator=['tools/v3_balloon_release.py:install_menu','N64/tag/menu/44/1'],
        source=dict(source='user-supplied GAFE01 revision 0 disc',reference_resource='foresta.rel',
                    reference_symbol='mTG_tag_word_fly',data_offset='00082A50',reference_sha256=sha256(label[:16])),
        human_review='not_recorded',encoded_sha256=sha256(label[:16]))))
    catalogue=json.loads((ROOT/'translations/provenance.json').read_bytes());validate(catalogue)
    if [r for r in catalogue['entries'] if r['id']==credit['id']]!=[credit]:
        raise ValueError('Missing or conflicting official balloon-menu credit')
    field_address=menu_field_address(before)
    code,compiled=compile_part('balloon_menu',output/'balloon_menu',
        defines=(f'AF_V3_MENU_FIELD_ADDRESS=0x{field_address:08X}u',))
    if len(code)>0x400 or compiled['symbols']['af_v3_balloon_queue']!=0x804B1680:
        raise ValueError('Balloon menu exceeds space or changes installed queue')
    module[0xCBF0:0xCBF0+len(code)]=code
    table=0x80878F08;count=44;table_at=len(data);new_table=ram+table_at
    table_data=bytes(data[table-ram:table-ram+count*8]);words_at=table_at+(count+1)*8;label_at=words_at+12
    data.extend(table_data+struct.pack('>2I',ram+words_at,3))
    # Grab and Quit retain the actual translated label objects and native callbacks.
    p=u32(data,table-ram+8)
    grab,drop,quit_word=struct.unpack_from('>3I',data,p-ram)
    if (data[grab-ram:grab-ram+16]!=b'Grab            ' or
            data[quit_word-ram:quit_word-ram+16]!=b'Quit            ' or
            struct.unpack_from('>I',data,0x80876D04-ram)[0]!=0x8DF90010):
        raise ValueError('Changed complete translated label layout')
    data.extend(struct.pack('>3I',grab,ram+label_at,quit_word))
    data.extend(label[:16]+struct.pack('>I',compiled['symbols']['af_v3_balloon_menu_fly']))
    data.extend(bytes(-len(data)%16))
    groups,absolute,rows,locations,slots=native_references(before,rel,expected_sections=(len(before),0,0,0))
    pairs=[];patches=[];delta=new_table-table
    def patch(at,value):
        off=at-ram;old_word=u32(data,off)
        struct.pack_into('>I',data,off,value)
        patches.append(dict(address=at,before=old_word,after=value))
    for hi,lows in groups.items():
        matched=[(lo,target) for lo,target in lows if table<=target<table+count*8]
        if not matched:continue
        if len(matched)!=len(lows):raise ValueError('Tag table shares an unrelated high half')
        high={(target+delta+0x8000)>>16&65535 for _,target in lows}
        if len(high)!=1:raise ValueError('Expanded tag table needs a split high half')
        patch(ram+hi,u32(data,hi)&0xFFFF0000|next(iter(high)))
        for lo,target in lows:
            patch(ram+lo,u32(data,lo)&0xFFFF0000|(target+delta)&65535)
            pairs.append((ram+hi,ram+lo,target))
    if len(pairs)!=16 or any(table<=value<table+count*8 for value in absolute.values()):
        raise ValueError('Changed complete menu table reference inventory')
    # Every selector call must use the additive wrapper. Its native fallback stays intact.
    calls=[ram+i for i in range(0,len(before),4) if u32(before,i) in (jump(0x80875610,link=True),jump(0x80875610),0x80875610)]
    if calls!=[0x80875834] or locations.get(0x80875834-ram)!=0x44000000|(0x80875834-ram):
        raise ValueError('Changed complete native menu selector call inventory')
    patch(0x80875834,jump(compiled['symbols']['af_v3_balloon_menu_type'],link=True))
    rows.remove(locations[0x80875834-ram])
    for i in range(count):
        off=table-ram+i*8
        if u32(before,off):
            if locations.get(off)!=0x42000000|off:raise ValueError('Unrelocated original tag row')
            rows.append(0x42000000|(table_at+i*8))
    rows.extend(0x42000000|at for at in (table_at+count*8,words_at,words_at+4,words_at+8))
    if len({v&0xFFFFFF for v in rows})!=len(rows):raise ValueError('Duplicate extended tag relocation')
    length=(24+len(rows)*4+15)&~15
    updated=(struct.pack('>5I',len(data),0,0,0,len(rows))+struct.pack('>'+str(len(rows))+'I',*rows)+
             bytes(length-24-len(rows)*4)+struct.pack('>I',length))
    metadata=[]
    entries=[i for i in range(0,len(menu)-31,4) if u32(menu,i)==vrom]
    if entries!=[0x2CB0]:raise ValueError('Changed complete tag allocation owner inventory')
    for at in entries:
        old_row=bytes(menu[at:at+32])
        if struct.unpack_from('>4I',old_row)!=(vrom,vrom+len(before),ram,ram+len(before)):
            raise ValueError('Changed native tag allocation bounds')
        struct.pack_into('>4I',menu,at,vrom,vrom+len(data),ram,ram+len(data))
        metadata.append(dict(offset=at,before=old_row.hex(),after=menu[at:at+32].hex()))
    extra=((len(data)+63)&~63)-((len(before)+63)&~63)
    pool_at=0x800C4B10-CODE_RAM;pool_word=u32(core,pool_at);pool_after=pool_word+extra
    if pool_word>>16!=0x25CE or extra<=0 or (pool_word^pool_after)&0xFFFF8000:
        raise ValueError('Tag growth exceeds checked shared submenu allocation')
    struct.pack_into('>I',core,pool_at,pool_after)
    native=menu_native_bindings(prior,core,before,original)
    references=[]
    for address in (0x80200010,0x80340010):
        loaded=relocate_verified_data(Image(ram,len(data),struct.unpack_from('>5I',updated)),data,updated,address)
        expected=relocate_verified_data(Image(ram,len(before),struct.unpack_from('>5I',rel)),before,rel,address)
        if loaded[table_at:table_at+count*8]!=expected[table-ram:table-ram+count*8]:
            raise ValueError('Extended label table does not preserve native menu pointers')
        references.append(dict(base=address,sha256=sha256(loaded)))
    report=copy.deepcopy(old)
    resize=[dict(vrom=v,previous_bytes=files[v].size,previous_sha256=sha256(files[v].extract(base)),
                 bytes=len(value),sha256=sha256(value)) for v,value in ((vrom,data),(rvrom,updated))]
    receipt=dict(code=compiled,offset=0xCBF0,end=0xCFF0,source_functions=functions,
        source_menu_links=links,source_label_sha256=sha256(label),provenance_entry=credit,
        native_functions=native,field_address=field_address,
        table_offset=table_at,table_bytes=(count+1)*8,old_table=table,native_count=count,
        menu_type=count,words_offset=words_at,label_offset=label_at,patches=patches,table_references=pairs,
        owner_sha256=sha256(data),relocation_sha256=sha256(updated),relocated_images=references,
        metadata=metadata,owner_resizes=resize,additional_pool_bytes=extra,
        pool_patch=dict(address=0x800C4B10,before=pool_word,after=pool_after),
        ordinary_menu_installed=True,ordinary_gameplay_tested=False,saved_format_changed=False)
    report['player_actions']['balloon_menu']=receipt
    report['player_actions']['balloon_release']['ordinary_menu_release_installed']=True
    report['player_actions']['balloon_actor']['ordinary_release_installed']=True
    report['player_actions']['reward_exchange'].update(owner_sha256=sha256(data),relocation_sha256=sha256(updated))
    report.update(sha256=sha256(module),crc32=zlib.crc32(module),additional_resident_bytes=0)
    blob[start:start+len(module)]=module
    return report,{vrom:bytes(data),rvrom:updated,owner_vrom:bytes(menu)}
