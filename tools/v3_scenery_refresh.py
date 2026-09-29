"""Refresh the complete shared tree renderer and its installed consumers.

No item-specific installer or art conversion: prepared families share four
seasonal banks, one runtime, and the existing category constructor.
"""
import copy
import struct
import zlib

from aflib import CODE_RAM, by_vrom, sha256, u32
from apply_translation import write_new
from v3_asset_loader import ROOT, BLOB, compile_part
from v3_furniture_pipeline import Source
from v3_import_storage import jump
import v3_scenery_runtime as scenery

RUNTIME_SOURCES=tuple('overlays/v3/scenery_'+name+'.c' for name in
    ('trees','daily','contents','world','interactions','player','field','effects'))


def replace_words(data,at,before,after):
    old=struct.pack('>'+str(len(before))+'I',*before)
    new=struct.pack('>'+str(len(after))+'I',*after)
    if len(old)!=len(new) or data[at:at+len(old)]!=old:
        raise ValueError(f'Changed installed scenery consumer at {at:X}')
    data[at:at+len(new)]=new


def word_diff(before,after):
    if len(before)!=len(after) or len(before)%4:
        raise ValueError('Scenery refresh cannot resize an initialized owner')
    return [dict(offset=p,before=u32(before,p),after=u32(after,p))
            for p in range(0,len(before),4) if before[p:p+4]!=after[p:p+4]]


def update_patches(receipt,data):
    """Retain original restoration evidence while rebinding current operands."""
    for name in ('patches','native_patches'):
        for row in receipt.get(name,[]):row['after']=u32(data,row['offset'])


def configuration(previous,old_code,rows):
    """Retain complete installed behaviour constants while changing ownership."""
    symbols=previous['code']['symbols'];ram=previous['ram']
    def values(name,fmt):
        at=symbols['af_v3_tree_'+name]-ram;n=struct.calcsize('>'+fmt)
        if not 0<=at<at+n<=len(old_code):raise ValueError('Tree constant exceeds installed packet')
        return struct.unpack_from('>'+fmt,old_code,at)
    at=symbols['af_v3_scenery_config']-ram
    if old_code[at:at+192]!=b''.join(struct.pack('>12I',*r['config']) for r in previous['owners']):
        raise ValueError('Changed complete installed scenery configuration')
    text='#include "scenery_trees.h"\nconst Scenery af_v3_scenery_config[4]={\n'
    text+=''.join(' {'+','.join(f'0x{v:X}u' for v in r['config'])+'},\n' for r in rows)+'};\n'
    rule=values('rule','8H12h4H')
    text+='const TreeRule af_v3_tree_rule={'+','.join(str(v) for v in rule[:8])+', {'
    text+=','.join('{'+','.join(str(v) for v in rule[i:i+2])+'}' for i in range(8,20,2))+'}, {'
    text+=','.join(str(v) for v in rule[20:])+'}};\n'
    daily=values('daily_config','6I2HI')
    text+='const TreeDaily af_v3_tree_daily_config={'+','.join(str(v)+'u' for v in daily)+'};\n'
    for ctype,name,fmt,shape,width in (
            ('u32','bury_offsets','4I','[4]',4),
            ('u16','content_tables','12H','[4][3]',3),
            ('TreeDrop','drops','68H','[17]',4),
            ('u16','cuts','16H','[8][2]',2),
            ('u32','player_masks','6I','[2][3]',3),
            ('u32','talk_offsets','4I','[4]',4),
            ('TreePosition','sparkle_offsets','12f','[4]',3)):
        data=values(name,fmt)
        terms=[f'{v:.1f}f' if isinstance(v,float) else f'0x{v:X}u' for v in data]
        nested=len(data)!=width
        fields=','.join('{'+','.join(terms[i:i+width])+'}' for i in range(0,len(terms),width)) if nested else ','.join(terms)
        text+=f'const {ctype} af_v3_tree_{name}{shape}={{'+fields+'};\n'
    return text


def paged_banks(base,resources,banks,data):
    """Deduplicate complete 4-KiB pages; each bank keeps its own final CRC."""
    from v3_physical_resources import allocate
    packet=bytearray(144*len(banks));pages={};layouts=[]
    for i,(season,bank) in enumerate(banks.items()):
        raw=data[season];offsets=[]
        for at in range(0,len(raw),4096):
            page=raw[at:at+4096]
            if page not in pages:pages[page]=len(packet);packet.extend(page)
            offsets.append(pages[page])
        if len(offsets)>32 or any(len(p)%16 for p in pages):raise ValueError('Scenery page dimensions exceed loader')
        struct.pack_into('>4I',packet,i*144,0x41465047,len(raw),4096,len(offsets))
        bank.update(packet_offset=i*144,page_offsets=offsets)
        layouts.append((i*144,offsets))
    resource=next((copy.deepcopy(r) for r in resources if r['id']=='shared-tree-families'),None)
    retained=resource is not None
    if not retained:resource=allocate(base,resources,packet,'shared-tree-families')
    elif resource['bytes']!=len(packet):raise ValueError('Changed retained tree page allocation')
    for at,offsets in layouts:
        struct.pack_into('>'+str(len(offsets))+'I',packet,at+16,
            *(resource['physical']+p for p in offsets))
    if retained and (sha256(packet)!=resource['sha256'] or
            base[resource['physical']:resource['physical']+resource['bytes']]!=packet):
        raise ValueError('Changed complete retained seasonal artwork')
    resource['sha256']=sha256(packet)
    for bank in banks.values():bank['vrom']=(resource['physical']+bank['packet_offset'])|0xC0000000
    return bytes(packet),resource


def seasonal_layout(base,equipment,module,core,banks):
    """Replace the old bank and constructor-owned BSS, not native actor state."""
    from v3_ground_categories import resize_installed
    ground=equipment['ground_categories'];previous=equipment['scenery'];files=by_vrom(base)
    cfg=ground['config_offset'];n=ground['config_bytes']
    if sha256(module[cfg:cfg+n])!=ground['config_sha256'] or n!=144:
        raise ValueError('Changed shared ground configuration')
    owners=[];changes={};growth=[]
    for i,(spec,old) in enumerate(zip(ground['owners'],previous['owners'],strict=True)):
        data,rel=(files[spec[k]].extract(base) for k in ('vrom','reloc'))
        cap=spec['capacity'];bank=banks[spec['role']]
        if (spec['role']!=old['role'] or old['bank_offset']<cap['table_offset']+cap['count']*8 or
                old['bank_offset']+old['bank_bytes']>cap['empty_offset'] or
                cap['parts_offset']!=cap['empty_offset']+32 or
                cap['parts_offset']+52*len(equipment['item_categories']['objects'])>cap['resident_bytes']):
            raise ValueError('Changed seasonal bank/category BSS ownership')
        actual=struct.unpack_from('>9I',module,cfg+i*36)
        expected=(spec['slot'],spec['constructor']-spec['ram'],spec['table']-spec['ram'],
            spec['count'],cap['count'],cap['table_offset'],cap['parts_offset'],cap['callback_offset'],cap['type_base'])
        if actual!=expected:raise ValueError('Changed complete ground owner configuration')
        total=cap['count']+32;table=(old['bank_offset']+bank['bytes']+15)&~15
        empty=table+total*8;parts=empty+32
        resident=(parts+52*len(equipment['item_categories']['objects'])+15)&~15
        capacity=dict(cap,count=total,table_offset=table,empty_offset=empty,parts_offset=parts,
            resident_bytes=resident,bss_bytes=resident-len(data),index_stride=total*2,
            actor_bytes=spec['actor']+total*8,actor_growth_bytes=total*8,
            stack_bytes=176+2*(total-spec['count']))
        enlarged,newrel,patches=resize_installed(data,rel,spec,capacity)
        descriptor=spec['allocation_descriptor']-CODE_RAM
        replace_words(core,descriptor,(spec['vrom'],spec['vrom']+len(data),spec['ram'],spec['ram']+cap['resident_bytes']),
                      (spec['vrom'],spec['vrom']+len(data),spec['ram'],spec['ram']+resident))
        newconfig=list(actual);newconfig[4:7]=[total,table,parts]
        struct.pack_into('>9I',module,cfg+i*36,*newconfig)
        if spec['role']=='xmas':
            address=ground['code']['symbols']['af_v3_ground_xmas_indices']-equipment['ram']
            replace_words(module,address,(0x3C1F0000|(spec['actor']>>16),0x37FF0000|(spec['actor']&65535),
                0x03F0F821,0x24110000|cap['count']),
                (0x3C1F0000|(spec['actor']>>16),0x37FF0000|(spec['actor']&65535),0x03F0F821,0x24110000|total))
        sceneconfig=list(old['config']);sceneconfig[3:9]=[bank['bytes'],bank['vrom'],bank['crc32'],table,total,cap['count']]
        row=copy.deepcopy(old);row.update(config=sceneconfig,bank_bytes=bank['bytes'],resident_bytes=resident,
            first_index=cap['count'],descriptor_count=len(bank['descriptors']),actor_bytes=capacity['actor_bytes'],
            before_sha256=sha256(data),before_reloc_sha256=sha256(rel),
            output_reloc_sha256=sha256(newrel),patches=patches)
        growth.append(dict(role=spec['role'],previous_resident_bytes=cap['resident_bytes'],resident_bytes=resident,
            additional_scene_bytes=resident-cap['resident_bytes']+capacity['actor_bytes']-cap['actor_bytes'],
            previous_table_count=cap['count'],table_count=total,stack_bytes=capacity['stack_bytes'],
            actor_index_bytes=capacity['actor_growth_bytes']))
        spec.update(capacity=capacity,output_sha256=sha256(enlarged),output_reloc_sha256=sha256(newrel),
                    capacity_patches=patches)
        update_patches(spec,enlarged)
        changes[spec['vrom']]=enlarged;changes[spec['reloc']]=newrel;owners.append(row)
    ground['config_sha256']=sha256(module[cfg:cfg+n])
    start=ground['code_offset'];ground['code']['sha256']=sha256(module[start:start+ground['code']['bytes']])
    return owners,changes,growth


def rebind(base,equipment,core,changes,owners,compiled,bootstrap):
    """Rebind all existing code callers, retaining unrelated newer owner edits."""
    import v3_scenery_player as player
    import v3_scenery_field as field
    files=by_vrom(base);previous=equipment['scenery'];old=previous['code']['symbols'];new=compiled['symbols']
    oldboot=previous['bootstrap']['symbols'];boot=bootstrap['symbols'];receipts=[]
    def call(data,at,name,link=True):
        replace_words(data,at,(jump(old[name],link=link),),(jump(new[name],link=link),))
    for i,row in enumerate(owners):
        data=bytearray(changes[row['vrom']]);rel=changes[row['reloc']]
        replace_words(data,u32(rel,0)+16,(oldboot['af_v3_scenery_'+row['role']],),(boot['af_v3_scenery_'+row['role']],))
        call(data,0x47A8,f'af_v3_scenery_type{i}',False)
        for at in previous['tree_states']['planting'][i]['calls']:call(data,at,f'af_v3_tree_bury{i}')
        for at,name in ((0x26B8,'af_v3_tree_drop_table'),(0x2784,'af_v3_tree_drop_item')):
            call(data,at,name)
        # The later insect importer owns the shake notification, then calls our
        # bee query through its checked data word. Preserve that notification.
        insect_hook=equipment['creature_insects']['compiled']['symbols']['af_insect_hook_tree']
        if u32(data,0x2960)!=jump(insect_hook,link=True):raise ValueError('Changed installed insect shake notification')
        for at in previous['interactions']['owners'][i]['calls']:call(data,at,f'af_v3_tree_cut{i}')
        call(data,previous['planting_sparkle']['owners'][i]['call'],f'af_v3_tree_plant_commit{i}')
        camera=previous['felling_camera']['owners'][i];name=f'af_v3_tree_talk{i}'
        for at,before,after in ((camera['hi'],(old[name]+0x8000)>>16,(new[name]+0x8000)>>16),
                                (camera['lo'],old[name]&65535,new[name]&65535)):
            opcode=u32(data,at)&0xFFFF0000;replace_words(data,at,(opcode|before,),(opcode|after,))
        row.update(before_sha256=sha256(files[row['vrom']].extract(base)),
            before_reloc_sha256=sha256(files[row['reloc']].extract(base)),
            output_sha256=sha256(data),patches=word_diff(files[row['vrom']].extract(base),data))
        spec=equipment['ground_categories']['owners'][i];spec['output_sha256']=sha256(data);update_patches(spec,data)
        changes[row['vrom']]=bytes(data)
    daily=previous['daily_growth'];data=bytearray(files[daily['vrom']].extract(base))
    for at,name,link in ((0x830,'near',True),(0x4ABC,'daily_plant',False),(0x28E0,'set_info',True),
            (0x296C,'reset_info',True),(0x2980,'thin',True),(0xC90,'record_content',True),
            (0xCCC,'record_content',True),(0x4AA8,'count_money',False),(0x4AD4,'count_money',False),
            (0xDF4,'count_eligible',True),(0x117C,'count_eligible',True),
            (0xE84,'change_content',True),(0x10BC,'change_content',True)):
        if link:call(data,at,'af_v3_tree_'+name)
        else:replace_words(data,at,(old['af_v3_tree_'+name],),(new['af_v3_tree_'+name],))
    replace_words(data,0x475C,(jump(oldboot['af_v3_tree_renew_dispatch']),0),
                  (jump(boot['af_v3_tree_renew_dispatch']),0))
    changes[daily['vrom']]=bytes(data)
    for name in ('daily_growth','hidden_contents','world_queries'):
        previous[name]['sha256']=sha256(data);update_patches(previous[name],data)
    previous['interactions']['daily_owner']['sha256']=sha256(data)
    update_patches(previous['interactions']['daily_owner'],data)
    for item in previous['tree_states']['core_consumers']:
        at=item['start']-CODE_RAM;name='af_v3_tree_'+item['name']+'_dispatch'
        replace_words(core,at,(jump(oldboot[name]),0),(jump(boot[name]),0))
        item['after']=bytes(core[at:at+8]).hex()
    for name,address,*_ in scenery.WORLD_NATIVE:
        at=address-CODE_RAM;symbol='af_v3_tree_'+name+'_dispatch'
        replace_words(core,at,(jump(oldboot[symbol]),0),(jump(boot[symbol]),0))
    for receipt in (previous['world_queries'],previous['interactions']['daily_owner']):
        for hook in receipt.get('core_hooks',[]):
            at=hook['offset'];hook['after']=bytes(core[at:at+len(bytes.fromhex(hook['after']))]).hex()
    data=bytearray(files[player.VROM].extract(base));a=player.GATE-player.RAM
    before=player.gate(oldboot['load'],old['af_v3_tree_player_query'])
    after=player.gate(boot['load'],new['af_v3_tree_player_query'])
    if data[a:a+len(before)]!=before or len(after)!=len(before):raise ValueError('Changed complete player tree gate')
    data[a:a+len(after)]=after;changes[player.VROM]=bytes(data)
    previous['player_queries'].update(sha256=sha256(data),gate_sha256=sha256(after));update_patches(previous['player_queries'],data)
    equipment['player_actions']['owner_sha256']=sha256(data);equipment['player_motion']['owner_sha256']=sha256(data)
    data=bytearray(files[field.VROM].extract(base));shared='af_v3_tree_query_dispatch'
    replace_words(data,field.SCAN-field.RAM,field.dispatch(old['af_v3_tree_insect_scan'],oldboot[shared]),
                  field.dispatch(new['af_v3_tree_insect_scan'],boot[shared]))
    name='af_v3_tree_insect_match'
    replace_words(data,field.GATE-field.RAM+28,
        (0x3C190000|((old[name]+0x8000)>>16),jump(oldboot[shared],link=True),0x27390000|(old[name]&65535)),
        (0x3C190000|((new[name]+0x8000)>>16),jump(boot[shared],link=True),0x27390000|(new[name]&65535)))
    changes[field.VROM]=bytes(data);previous['field_insects']['sha256']=sha256(data);update_patches(previous['field_insects'],data)
    at=previous['field_insects']['clear_entry']-CODE_RAM
    replace_words(core,at,field.dispatch(old['af_v3_tree_clear'],oldboot[shared]),field.dispatch(new['af_v3_tree_clear'],boot[shared]))
    for hook in previous['field_insects']['core_hooks']:
        p=hook['offset'];hook['after']=bytes(core[p:p+12]).hex()
    for vrom,data in sorted(changes.items()):
        if vrom in {o['reloc'] for o in owners}:continue
        before=files[vrom].extract(base)
        receipts.append(dict(vrom=vrom,before_sha256=sha256(before),sha256=sha256(data),patches=word_diff(before,data)))
    return receipts


def rebind_insect_query(base,equipment,records,compiled):
    insect=equipment['creature_insects'];packet=insect['packet'];before=packet['sha256']
    raw=bytearray(base[packet['physical']:packet['physical']+packet['bytes']])
    if sha256(raw)!=before:raise ValueError('Changed complete insect packet')
    address=insect['compiled']['symbols']['af_insect_tree_bee_query'];at=address-packet['ram']
    name='af_v3_tree_bee_query';old=equipment['scenery']['code']['symbols'][name];new=compiled['symbols'][name]
    replace_words(raw,at,(old,),(new,))
    packet.update(sha256=sha256(raw),crc32=zlib.crc32(raw))
    insect['compiled']['sha256']=sha256(raw[:insect['compiled']['bytes']])
    insect['physical_resource']['sha256']=packet['sha256']
    record=next(r for r in records if r['id']==insect['physical_resource']['id'])
    if record['sha256']!=before:raise ValueError('Changed insect physical ownership')
    record['sha256']=packet['sha256']
    # The common builder publishes the complete startup table from this updated
    # packet. Do not edit a second copy of its bootstrap receipt here.
    receipt=dict(address=address,before=old,after=new,packet_sha256=packet['sha256'])
    return (dict(record,previous_sha256=before),bytes(raw)),receipt


def install(base,prior,blob,core,original,output,art_path):
    """Install complete prepared families through the existing scenery route."""
    from map_artwork import compile_commands
    equipment=copy.deepcopy(prior['equipment_resources']);previous=equipment['scenery'];start=equipment['blob_offset']
    module=bytearray(blob[start:start+equipment['bytes']]);code_at=previous['blob_offset']
    old_code=bytes(blob[code_at:code_at+previous['bytes']]);capacity=previous['additional_fixed_resident_bytes']
    if (not previous.get('planting_sparkle') or capacity!=12288 or
            sha256(module)!=equipment['sha256'] or sha256(old_code)!=previous['sha256'] or
            equipment['carried_items']['ready_mask'] or equipment['carried_items']['selected_mask'] or
            scenery.RUNTIME_RAM+capacity>prior['furniture']['bank_pool']['start']):
        raise ValueError('Changed complete installed tree-family dependencies')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    gold=scenery.prepared(source,ROOT/previous['art_directory']);carried=scenery.prepared(source,art_path)
    if carried[0]['category']!='carried-trees':raise ValueError('Shared tree refresh needs complete carried families')
    art,assets,palettes=scenery.merge_categories((gold,carried));lights=scenery.native_lights(base)
    wrappers=compile_commands(output/'palette',ROOT/'overlays/v3/scenery_palette.c',
        (('palette',64),('palette6',64),('palette7',64)))
    wrappers={8:wrappers['palette'],6:wrappers['palette6'],7:wrappers['palette7']}
    bank_data={};banks={}
    for season in scenery.SEASONS:
        data,receipt=scenery.pack_bank(art,assets,palettes,season,wrappers,
            light_loop=lights['offset'] if season=='xmas' else 0)
        receipt.update(crc32=zlib.crc32(data));bank_data[season]=data;banks[season]=receipt
        write_new(output/f'scenery-{season}.bin',data)
    packet,resource=paged_banks(base,prior['physical_resources'],banks,bank_data)
    retained=previous.get('families')
    if retained:
        if (retained['packet']!=resource or any(retained.get(k)!=v for k,v in carried[3].items()) or
                list(banks.values())!=previous['banks']):
            raise ValueError('Changed installed tree-family artwork dependency')
        owners=copy.deepcopy(previous['owners']);changes={};growth=[];files=by_vrom(base)
        for row,ground in zip(owners,equipment['ground_categories']['owners'],strict=True):
            for key,checksum in (('vrom','output_sha256'),('reloc','output_reloc_sha256')):
                raw=files[row[key]].extract(base)
                if sha256(raw)!=ground[checksum] or sha256(raw)!=row[checksum]:
                    raise ValueError('Changed installed shared seasonal owner')
                changes[row[key]]=raw
            cap=ground['capacity']
            growth.append(dict(role=row['role'],previous_resident_bytes=cap['resident_bytes'],resident_bytes=cap['resident_bytes'],
                additional_scene_bytes=0,previous_table_count=cap['count'],table_count=cap['count'],
                stack_bytes=cap['stack_bytes'],actor_index_bytes=cap['actor_growth_bytes']))
    else:owners,changes,growth=seasonal_layout(base,equipment,module,core,banks)
    config=configuration(previous,old_code,owners)
    config='#include "'+('../'*len(output.relative_to(ROOT).parts))+'overlays/v3/scenery_trees.h"\n'+config.split('\n',1)[1]
    path=output/'scenery-config.c';write_new(path,config.encode())
    code,compiled=compile_part('scenery',output/'scenery',extra_sources=(*RUNTIME_SOURCES,str(path.relative_to(ROOT))),
        defines=('AF_V3_TREE_FELLING','AF_V3_SCENERY_FAMILIES'),
        link_symbols={'af_carried_category':equipment['carried_items']['code']['symbols']['af_carried_category']})
    reservation=previous['reservations'][0]
    if len(code)>capacity or code_at+len(code)>reservation['blob_offset']+reservation['bytes']:
        raise ValueError('Shared tree code exceeds existing owned reservation')
    symbols=compiled['symbols'];defines=['AF_V3_SCENERY_WORLD','AF_V3_SCENERY_TREES','AF_V3_SCENERY_DAILY',
        f'AF_SCENERY_VROM=0x{BLOB+code_at:X}u',f'AF_SCENERY_BYTES={len(code)}u',f'AF_SCENERY_CRC=0x{zlib.crc32(code):X}u']
    for name in ('grow','stump','column','dig','npc','renew'):
        symbol='af_v3_tree_'+('renew_native' if name=='renew' else name)
        defines.append(f'AF_SCENERY_{name.upper()}=0x{symbols[symbol]:X}')
    boot,bootstrap=compile_part('scenery_bootstrap',output/'scenery_bootstrap',defines=tuple(defines))
    a,b=scenery.BOOT_RAM-equipment['ram'],scenery.BOOT_END-equipment['ram'];n=previous['bootstrap']['bytes']
    if (sha256(module[a:a+n])!=previous['bootstrap']['sha256'] or any(module[a+n:b]) or
            len(boot)>b-a-4 or bootstrap['symbols']['af_v3_native_tree_grow']!=0x804ADFC0 or
            bootstrap['symbols']['af_v3_native_tree_stump']!=0x804ADFD0):
        raise ValueError('Changed shared bootstrap/cache/fallback allocation')
    bindings=rebind(base,equipment,core,changes,owners,compiled,bootstrap)
    records=copy.deepcopy(prior['physical_resources'])
    insect_write,insect_binding=rebind_insect_query(base,equipment,records,compiled)
    module[a:b]=boot.ljust(b-a,b'\0');blob[code_at:code_at+len(code)]=code
    blob[start:start+len(module)]=module
    previous.update(owners=owners,banks=list(banks.values()),code=compiled,bytes=len(code),sha256=sha256(code),
        crc32=zlib.crc32(code),bootstrap=bootstrap,config_sha256=sha256(config.encode()),
        additional_scene_resident_bytes=max(g['additional_scene_bytes'] for g in growth),
        families=dict(format='AFV3-TREE-FAMILIES-1',art_directory=str(art_path.resolve().relative_to(ROOT)),
            **carried[3],packet=resource,allocation=growth,bindings=bindings,native_lights=lights,
            prepared_art_reused=True,field_behaviours_complete=False,native_render_tested=False,
            selectors=[0x223B,0x2807,0x290A],insect_query=insect_binding))
    previous['reservations'][0]['used_bytes']=code_at+len(code)-reservation['blob_offset']
    previous['tree_states']['shared_packet_bytes']=len(code)
    equipment.update(sha256=sha256(module),crc32=zlib.crc32(module),additional_resident_bytes=0)
    updates=dict(physical_resources=records if retained else [*records,resource])
    return equipment,changes,updates,[insect_write]+([] if retained else [(resource,packet)])
