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
PLANT_BLOCK=bytes.fromhex('8fa4003c144100032445df44100000022405080030a5ffff')
PREVIEW_BLOCK=bytes.fromhex('28412901142000052841290a10200003240c006810000005a60c00102401290014410002240d0800a60d0010')


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


def family_contract(source,base,core,art,previous):
    """Extend the already checked tree tables to both complete carried families."""
    from v3_scenery import resource
    from v3_scenery_player import CAMERA
    rules=scenery.tree_rules(source)
    growth=list(struct.iter_unpack('>hh',bytes.fromhex(rules['tables']['growth']['hex'])))
    stumps=bytes.fromhex(rules['tables']['stumps']['hex'])
    families=[]
    for first,count,hidden,hidden_count,selected,plant,kind,start in (
            (0x854,8,0,0,0x2807,0x2807,1,65),(0x85D,5,0x78,3,0x290A,0x290A,2,73)):
        fields=[first,count,hidden,hidden_count,selected,plant,0,kind]
        stages=growth[start:start+count]
        cuts=[struct.unpack_from('>H',stumps,i*8+kind*2)[0] for i in range(4)]
        families.append(dict(fields=fields,growth=stages,stumps=cuts))
    drops=resource(source,0x4549C,size=168);cuts=resource(source,0x45550,size=332)
    for name,table in (('drop_sources',drops),('cut_sources',cuts)):
        if previous['interactions'][name][0]!=table:raise ValueError('Changed complete shared drop/cut source')
    drop_rows=list(struct.iter_unpack('>4H',bytes.fromhex(drops['hex'])))
    cut_rows=[r for r in struct.iter_unpack('>2H',bytes.fromhex(cuts['hex']))
              if 0x854<=r[0]<=0x868 or 0x78<=r[0]<=0x82]
    if len(drop_rows)!=21 or len(cut_rows)!=23:raise ValueError('Incomplete tree-family interactions')
    functions=[]
    for at,size,digest in (
            (0x1A0498,44,'e0d8d890cf0167d2df64316f8de69342eb1af0d45ac16fd1e9d55b2f6cad58a3'),
            (0x1A04C4,44,'4d35b7520e89072bbf85b95600891b59ef47c88fa6ff7c96678c0d78e4978ef5'),
            (0x1A0510,44,'6d3e1edccb33fc459a3bc9df05e472b80c9d8c3520737fe55fe32678214e705d'),
            (0x1A053C,44,'aa72cee589a1c96bbcdfd7205d87070d3807f4c69423a9fef19d5e07423f8fd9'),
            (0x1A21F8,448,'731870db02a97ce68efb8c5a22d1db1c595bc895efc9ae2da68ba9794e91ef09'),
            (0x2173C,72,'c6246a8c4e2f4f87268f9378a0c3592b5449fb65af8b3af445c6f69d9f9c5069'),
            (0x216C4,120,'a7fb5a6efe3ee8ad7cf61aeab00d99ce50adcf6128e424f8af7e1efda203ecb1'),
            (0x2850AC,536,'3e0fa1ad8153028dbb42e80af6aaf577721bc9c3f447d64c86921cc9fc0b243b'),
            (0x1417A8,648,'8106f13bdd87ed083c7a005d9e18d102f91b00854911d342bea54726653c268d'),
            (0x148B2C,648,'e85502b7559f16a63f7b54b6a03c683c13536eecfd7051eacf4fdb2cfa3a11d1'),
            (0x150624,648,'e3e0f58e754aa83ddfe57ad711bc81c78a138504f7cc2d56370ea558e25977ad'),
            (0x157A3C,648,'f7389c9f079818c4160c499a5a8820e4cc3e87aedf89067895028f0dc47dcc09')):
        raw,receipt=source.function(at)
        if len(raw)!=size or sha256(raw)!=digest:raise ValueError('Changed complete source tree-region rule')
        functions.append(receipt)
    native=[]
    for address,size,digest in (
            (0x80088B3C,132,'b851cae30382f57df68b758ced1acf64126814117033ab175e996fee27f3e1a4'),
            (0x80071B78,164,'c611d50c6b3dbb7369e97b0190a8e6475f7ba6bc61f5f60b1e7dd213e3cd76a3')):
        if sha256(core[address-CODE_RAM:address-CODE_RAM+size])!=digest:
            raise ValueError('Changed complete native tree-region query')
        native.append(dict(address=address,bytes=size,sha256=digest))
    owner=by_vrom(base)[previous['daily_growth']['vrom']].extract(base)
    # Complete native cell loop establishes block_x/z at 20/24 and x/z at 28/2C.
    # Its coordinate/terrain calls and all loop bounds remain untouched.
    loop=owner[0x2624:0x2818]
    if (len(loop)!=500 or sha256(loop)!='11ce088c742b4df8c77277008ccdf9b2da59e13ead7e89713c280064dea71775'
            or u32(loop,0x94)!=jump(0x80088B3C,link=True)):
        raise ValueError('Changed native growth-cell coordinates')
    masks=[];camera=[]
    for role,address,*_ in CAMERA:
        raw,receipt=source.function(address)
        if receipt!=next(r['source'] for r in previous['felling_camera']['owners'] if r['role']==role):
            raise ValueError('Changed complete camera source predicate')
        # All four pinned predicates cover medium/large/full palms and cedars,
        # including fruit and Xmas lights. Source bindings identify shared rows.
        wanted=set(range(0x856,0x85C))|set(range(0x85F,0x862))|{0x78,0x79,0x7A,0x82}
        wanted|={0x865,0x866,0x867,0x868,0x7F,0x80,0x81}
        keys={r['descriptor'] for r in art['bindings'] if r['season']==role and int(r['foreground_id'],16) in wanted}
        season=[r for r in art['descriptors'] if r['season']==role];row=[0,0,0]
        for i,d in enumerate(season):
            if d['key'] in keys:row[{'gold':0,'palm':1,'cedar':2}[d['family']]]|=1<<i
        if [v.bit_count() for v in row]!=[3,4,4 if role=='xmas' else 3]:
            raise ValueError('Incomplete camera family descriptor mapping')
        masks.append(row);camera.append(receipt)
    return dict(rule_bytes=56,gold=rules,carried=families,drops=drop_rows,cuts=cut_rows,
        regional_source=functions,regional_native=native,native_cell_loop_sha256=sha256(loop),
        camera_source=camera,camera_masks=masks,coastal_block_z=6,cedar_minimum_height=100.0)


def configuration(previous,old_code,rows,families=None):
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
    expanded=previous.get('families',{}).get('behaviour',{}).get('rule_bytes')==56
    rule=values('rule','8H16h4H' if expanded else '8H12h4H')
    end=24 if expanded else 20
    text+='const TreeRule af_v3_tree_rule={'+','.join(str(v) for v in rule[:8])+', {'
    text+=','.join('{'+','.join(str(v) for v in rule[i:i+2])+'}' for i in range(8,end,2))+'}, {'
    text+=','.join(str(v) for v in rule[end:])+'}};\n'
    if families:
        def record(r):
            return '{'+','.join(str(v) for v in r['fields'])+',{'+','.join(
                '{'+','.join(str(v) for v in pair)+'}' for pair in r['growth'])+'},{'+','.join(str(v) for v in r['stumps'])+'}}'
        text+='const TreeRule af_v3_tree_carried_rules[2]={'+','.join(record(r) for r in families['carried'])+'};\n'
        text+='const u32 af_v3_tree_camera_masks[4][3]={'+','.join(
            '{'+','.join(str(v)+'u' for v in row)+'}' for row in families['camera_masks'])+'};\n'
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
        if families and name in ('drops','cuts'):
            data=sum((tuple(r) for r in families[name]),())
            shape='[21]' if name=='drops' else '[23][2]'
        else:data=values(name,fmt)
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
    planting=previous.get('families',{}).get('planting_menu')
    def call(data,at,name,link=True):
        replace_words(data,at,(jump(old[name],link=link),),(jump(new[name],link=link),))
    for i,row in enumerate(owners):
        data=bytearray(changes[row['vrom']]);rel=changes[row['reloc']]
        replace_words(data,u32(rel,0)+16,(oldboot['af_v3_scenery_'+row['role']],),(boot['af_v3_scenery_'+row['role']],))
        call(data,0x47A8,f'af_v3_scenery_type{i}',False)
        for at in previous['tree_states']['planting'][i]['calls']:call(data,at,f'af_v3_tree_bury{i}')
        for at,name in ((0x26B8,'af_v3_tree_drop_table'),(0x2784,'af_v3_tree_drop_item')):
            call(data,at,name)
        replace_words(data,0x26BC,(0x97A4005A if previous.get('families',{}).get('behaviour') else 0,),(0x97A4005A,))
        def preview_words(target):return (jump(target,link=True),0x00402025,0xA6020010,*([0]*8))
        before=preview_words(old['af_v3_tree_plant_preview']) if planting else struct.unpack('>11I',PREVIEW_BLOCK)
        from v3_npc_clothing import guard_incoming
        guard_incoming(bytes(data),u32(rel,0),row['ram'],[(0x2064,44)])
        replace_words(data,0x2064,before,preview_words(new['af_v3_tree_plant_preview']))
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
    # The direct planting action keeps its full original search, placement,
    # warnings, inventory removal, sound, and close-window branches. Only the
    # six-word item-to-foreground conversion changes; its lazy gate is resident.
    tag_vrom,tag_ram,at=0x3950000,0x8086F310,0x80872978-0x8086F310
    data=bytearray(files[tag_vrom].extract(base));rel=files[0x3960000].extract(base)
    tag=equipment['carried_items']['actions']['tag']
    if sha256(data)!=tag['owner_sha256'] or sha256(rel)!=tag['relocation_sha256']:
        raise ValueError('Changed complete native planting action owner')
    restored=bytearray(data)
    def plant_words(target,gate):
        return (0x3C190000|((target+0x8000)>>16),0x27390000|(target&65535),
                jump(gate,link=True),0x00402025,0x00402825,0x8FA4003C)
    before=plant_words(old['af_v3_tree_plant_seed'],oldboot[shared]) if planting else struct.unpack('>6I',PLANT_BLOCK)
    restored[at:at+24]=PLANT_BLOCK
    if sha256(restored[0x8087287C-tag_ram:0x80872A38-tag_ram])!='8573fa0b9987b24324b85b4a8f16e4bbaad5a7850fae5ae3dac0c13b0a37c4eb':
        raise ValueError('Changed complete native planting action')
    from v3_npc_clothing import guard_incoming
    from v3_npc_draw import relocation_offsets
    guard_incoming(bytes(restored),u32(rel,0),tag_ram,[(at,24)])
    if set(range(at,at+24,4))&set(relocation_offsets(rel,len(data))):
        raise ValueError('Unexpected relocation in planting conversion')
    after=plant_words(new['af_v3_tree_plant_seed'],boot[shared]);replace_words(data,at,before,after)
    if not planting:
        tag['patches'].extend(dict(address=tag_ram+at+i*4,before=word,after=after[i]) for i,word in enumerate(before))
    else:
        for patch in tag['patches']:patch['after']=u32(data,patch['address']-tag_ram)
    tag['owner_sha256']=sha256(data);changes[tag_vrom]=bytes(data)
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
    if (not previous.get('planting_sparkle') or capacity not in (12288,20480) or
            sha256(module)!=equipment['sha256'] or sha256(old_code)!=previous['sha256'] or
            equipment['carried_items']['ready_mask'] or equipment['carried_items']['selected_mask']):
        raise ValueError('Changed complete installed tree-family dependencies')
    from v3_console_disk_install import reservations
    ram,end=0x8077B000,0x80780000
    existing=copy.deepcopy(prior);existing['equipment_resources'].pop('scenery')
    if any(a<end and ram<b for a,b in reservations(existing)):
        raise ValueError('Tree-family code overlaps an existing memory reservation')
    if (previous['ram'],capacity) not in ((scenery.RUNTIME_RAM,12288),(ram,end-ram)):
        raise ValueError('Unknown prior tree runtime allocation')
    capacity=end-ram
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
    behaviour=family_contract(source,base,core,art,previous)
    config=configuration(previous,old_code,owners,behaviour)
    config='#include "'+('../'*len(output.relative_to(ROOT).parts))+'overlays/v3/scenery_trees.h"\n'+config.split('\n',1)[1]
    path=output/'scenery-config.c';write_new(path,config.encode())
    code,compiled=compile_part('scenery',output/'scenery',extra_sources=(*RUNTIME_SOURCES,str(path.relative_to(ROOT))),
        defines=('AF_V3_TREE_FELLING','AF_V3_SCENERY_FAMILIES','AF_V3_TREE_FAMILIES'),
        link_symbols={'af_carried_category':equipment['carried_items']['code']['symbols']['af_carried_category'],
            'af_scenery_runtime_ram':ram,'af_scenery_runtime_end':end})
    if previous.get('physical_dma'):
        # Installed tree-effect callers retain this absolute export. New
        # scenery source dispatches physical reads directly, but must not erase
        # the adapter while an unchanged effect packet still calls it.
        adapter=previous['physical_dma'];at=adapter['ram']-ram;n=adapter['code']['bytes']
        retained=old_code[at:at+n]
        if len(code)>at or len(retained)!=n or sha256(retained)!=adapter['code']['sha256']:
            raise ValueError('Shared tree refresh overlaps its retained physical DMA export')
        code=code.ljust(at,b'\0')+retained
        compiled.update(bytes=len(code),sha256=sha256(code),retained_physical_dma=adapter['code'])
        compiled['symbols']['af_v3_paged_dma']=adapter['code']['symbols']['af_v3_paged_dma']
    reservation=previous['reservations'][0]
    if len(code)>capacity or code_at+len(code)>reservation['blob_offset']+reservation['bytes']:
        raise ValueError('Shared tree code exceeds existing owned reservation')
    symbols=compiled['symbols'];defines=['AF_V3_SCENERY_WORLD','AF_V3_SCENERY_TREES','AF_V3_SCENERY_DAILY',
        f'AF_SCENERY_RAM=0x{ram:X}u',f'AF_SCENERY_VROM=0x{BLOB+code_at:X}u',
        f'AF_SCENERY_BYTES={len(code)}u',f'AF_SCENERY_CRC=0x{zlib.crc32(code):X}u']
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
        ram=ram,additional_fixed_resident_bytes=capacity,memory=dict(ram=ram,bytes=capacity),
        crc32=zlib.crc32(code),bootstrap=bootstrap,config_sha256=sha256(config.encode()),
        additional_scene_resident_bytes=max(g['additional_scene_bytes'] for g in growth),
        families=dict(format='AFV3-TREE-FAMILIES-1',art_directory=str(art_path.resolve().relative_to(ROOT)),
            **carried[3],packet=resource,allocation=growth,bindings=bindings,native_lights=lights,
            prepared_art_reused=True,field_behaviours_complete=False,native_render_tested=False,
            behaviour=behaviour,
            selectors=[0x223B,0x2807,0x290A],insect_query=insect_binding))
    previous['families']['planting_menu']=dict(vrom=0x3950000,ram=0x8086F310,address=0x80872978,
        bytes=24,preview_offset=0x2064,preview_bytes=44,original_action_sha256=
        '8573fa0b9987b24324b85b4a8f16e4bbaad5a7850fae5ae3dac0c13b0a37c4eb',native_tested=False)
    previous['reservations'][0]['used_bytes']=code_at+len(code)-reservation['blob_offset']
    previous['tree_states']['shared_packet_bytes']=len(code)
    equipment.update(sha256=sha256(module),crc32=zlib.crc32(module),additional_resident_bytes=0)
    updates=dict(physical_resources=records if retained else [*records,resource])
    return equipment,changes,updates,[insect_write]+([] if retained else [(resource,packet)])
