"""Shared field behaviour readers for the complete nine-fish import category.

Use the installed field packet's reserved code/table padding. Retain native
owner sizes, original fish values, golden-rod hooks, and the physical art pool.
"""
import copy
import struct
import zlib

from aflib import by_vrom,sha256,u32
from v3_asset_loader import ROOT,BLOB,compile_part
from v3_creature_field import table
from v3_creature_field_native import RAM,SIZE,retarget
from v3_player_actions import native_references
from v3_npc_clothing import guard_incoming

CODE,TABLE=0x400,0x2400
OWNERS={
    'river':(0x828C50,0x82B0C0,0x809317D0,
        '85a358c89e3e3ad65b232ac351d66c0d403af50d2fb26675c500e0a763680af2',
        '9fe44ba3f7e621b7982e76db31a67b478a59052ac26b20c49ededacd4cc9be13'),
    'sea':(0x9591D0,0x95B1E0,0x80A98F60,
        '2bc8610c8e4827a92cf434ae42ecd60ad1328b1b78ce643d795ca4b658bdab62',
        '2dcd8988d864ff438ad31a2027f3a7a9fdb1d432b2fa73d5ea3ec1c6d6888329'),
}
SOURCES=('tools/v3_creature_fish.py','overlays/v3/creature_fish.c',
    'overlays/v3/creature_fish.S','overlays/v3/creature_fish.ld')
WORLD_RAM,WORLD_SIZE,WORLD_TABLE=0x8064A000,0x4000,0x3000
WORLD_SOURCES=SOURCES+('tools/v3_creature_spawns.py','overlays/v3/creature_spawns.c',
    'overlays/v3/creature_spawns.h','overlays/v3/creature_water.c','overlays/v3/creature_water.h',
    'overlays/v3/creature_patrol.c','overlays/v3/creature_patrol.S','overlays/v3/creature_world.ld',
    'tools/v3_asset_loader.py','tools/v3_room_goods.py','tools/v3_furniture_pipeline.py',
    'tools/v3_furniture_install.py','overlays/v3/surface_bootstrap.c')


def parameters(source):
    rows=[];receipts=[]
    sea=((0x76D10,'aGKK_speed'),(0x76D30,'aGKK_back_speed'),(0x76D50,'aGKK_touch_count'),
         (0x76D60,'aGKK_touch_distance'),(0x76D80,'aGKK_shadow_scale'),(0x76E18,'rr$483'),
         (0x76E48,'hosei$546'),(0x76E94,'gomi$768'),(0x76EB4,'eff_arg$802'),(0x76EC4,'rr$803'))
    for index,(at,name,kind) in enumerate(((0x769C0,'aGTT_speed','f'),(0x769E0,'aGTT_back_speed','f'),
            (0x76A00,'aGTT_touch_count','h'),(0x76A10,'aGTT_touch_distance','f'),
            (0x76A30,'aGYO_shadow_scale','f'),(0x76AC8,'rr$475','f'),
            (0x76AF8,'hosei$548','f'),(0x76B1C,'gomi$776','I'),
            (0x76B3C,'eff_arg$811','h'),(0x76B4C,'rr$812','f'))):
        raw,receipt=table(source,at,16 if kind=='h' else 32,name)
        values=list(struct.unpack('>8'+kind,raw));receipts.append(receipt)
        sea_raw,sea_receipt=table(source,sea[index][0],len(raw),sea[index][1])
        if sea_raw!=raw:raise ValueError('River/coastal source size behaviours disagree')
        receipts.append(sea_receipt)
        if name=='gomi$776':
            if any(v not in (41,42,43) for v in values):raise ValueError('Changed source rubbish identities')
            values=[v-9 for v in values]
        elif name=='aGYO_shadow_scale':
            rate=struct.unpack('>f',struct.pack('>f',0.02))[0]
            values=[v*rate for v in values]
        rows.append(struct.pack('>8'+('f' if kind=='f' else 'I'),*values))
    # These two switches are in source code, not donor data arrays.
    rows += [struct.pack('>8f',17,17,22,22,22,22,22,22),
             struct.pack('>8I',3,3,3,3,2,2,2,2)]
    return b''.join(rows),receipts


def rewrite(owner,reloc,ram,targets,windows):
    """Retarget full tables, then checked windows with exact relocation removal."""
    image,fixed,receipt=retarget(owner,reloc,ram,targets,[])
    image=bytearray(image);sections=struct.unpack_from('>4I',fixed)
    groups,_,records,locations,_=native_references(image,fixed,expected_sections=sections)
    spans=[(address-ram,len(before)*4) for address,before,_ in windows]
    guard_incoming(owner,sections[0],ram,spans)
    removed=set();changed=set();covered=set()
    for address,before,after in windows:
        at=address-ram
        if len(after)!=len(before) or struct.unpack_from('>'+str(len(before))+'I',image,at)!=before:
            raise ValueError(f'Changed fish behaviour window at {address:08X}')
        for i,word in enumerate(after):
            offset=at+i*4
            if offset in covered:raise ValueError('Overlapping fish behaviour windows')
            covered.add(offset)
            if word!=u32(image,offset):
                changed.add(offset)
                if offset in locations:removed.add(locations[offset])
            receipt['patches'].append(dict(address=ram+offset,before=u32(image,offset),after=word))
            struct.pack_into('>I',image,offset,word)
    for hi,refs in groups.items():
        affected=[p in changed for p in (hi,*(lo for lo,_ in refs))]
        if any(affected) and not all(affected):raise ValueError('Fish window splits a native relocation group')
    keep=[r for r in records if r not in removed]
    fixed=(struct.pack('>5I',*sections,len(keep))+struct.pack('>'+str(len(keep))+'I',*keep)
           +bytes(len(reloc)-24-4*len(keep))+struct.pack('>I',len(reloc)))
    native_references(image,fixed,expected_sections=sections)
    receipt.update(sha256=sha256(image),reloc_sha256=sha256(fixed),
        removed_relocations=sorted(set(receipt['removed_relocations'])|removed))
    return bytes(image),fixed,receipt


def install(base,prior,blob,output,core=None):
    from v3_furniture_pipeline import Source
    e=copy.deepcopy(prior['equipment_resources']);field=e.get('creature_field')
    if e.get('creature_fish',{}).get('world',{}).get('spawn_manager_installed'):
        return connect_catches(base,prior,blob,output,core)
    if e.get('creature_fish',{}).get('world'):return install_manager(base,prior,blob,output)
    if e.get('creature_fish'):return install_world(base,prior,blob,output)
    if not field:raise ValueError('Fish world readers require installed field frames')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    files=by_vrom(base);p=field['packet'];at=p['blob_offset'];packet=bytearray(blob[at:at+SIZE])
    if (sha256(packet)!=p['sha256'] or any(packet[CODE:0x1000]) or
            any(packet[TABLE:SIZE-16])):raise ValueError('Changed or occupied reserved field code/table space')
    arrays,donor=parameters(source)
    source_functions=[source.function(address)[1] for address in
        (0x234BB0,0x234E50,0x235488,0x235648,0x235E40,0x235F74,0x2361B0,0x2363A4)]
    identities=next(t['ram'] for t in field['tables'] if t['name']=='fish-capture-identities')
    code,compiled=compile_part('creature_fish',output/'creature_fish',
        extra_sources=('overlays/v3/creature_fish.S',),defines=(f'AF_FISH_IDENTITIES=0x{identities:X}',))
    if len(code)>0x1000-CODE:raise ValueError('Fish world code exceeds retained padding')
    packet[CODE:CODE+len(code)]=code;packet[TABLE:TABLE+len(arrays)]=arrays
    tables={t['name']:t for t in field['tables']};params=tables['fish-release-params']['ram']
    symbols=compiled['symbols']
    def jump(name,link=True):return (0x0C000000 if link else 0x08000000)|(symbols['af_v3_fish_'+name]>>2&0x3FFFFFF)
    owners={}
    for name,spec in OWNERS.items():
        v,r,ram,digest,rdigest=spec;data=files[v].extract(base);reloc=files[r].extract(base)
        if sha256(data)!=digest or sha256(reloc)!=rdigest:raise ValueError('Changed complete fish behaviour owner')
        owners[name]=(data,reloc,ram,v,r)
    for name in ('fish','release'):
        old=next(o for o in field['owners'] if o['name']==name)
        data=files[old['vrom']].extract(base);reloc=files[old['reloc']].extract(base)
        if sha256(data)!=old['sha256'] or sha256(reloc)!=old['reloc_sha256']:
            raise ValueError('Changed installed fish field owner')
        owners[name]=(data,reloc,old['ram'],old['vrom'],old['reloc'])
    targets={n:{} for n in owners};windows={n:[] for n in owners}
    def raw(name,address,count):
        data,_,ram,_,_=owners[name];return data[address-ram:address-ram+count]
    def window(name,address,before,after):
        windows[name].append((address,tuple(before),tuple(after)))
    for name,table_at,donor_at in (('river',0x80933960,0x76858),('sea',0x80A9AD50,0x76BA8)):
        if raw(name,table_at,288)!=packet[params-RAM:params-RAM+288]:
            raise ValueError('Native field/release parameter prefixes disagree')
        complete,receipt=table(source,donor_at,360,'gyoei_type');donor.append(receipt)
        for row in field['rows']:
            if row['category']!='fish':continue
            size,search,bite=struct.unpack_from('>HHI',complete,row['source_index']*8)
            if struct.unpack_from('>HHI',packet,params-RAM+row['actor_index']*8)!=(size,search,(10,11,12,15,45)[bite]):
                raise ValueError('Source field/release parameters disagree')
        targets[name].update({table_at+i:params+i for i in (0,2,4)})
    for address,row,kind in ((0x80933A80,0,'f'),(0x80933A98,1,'f'),(0x80933AB0,2,'h'),
            (0x80933ABC,3,'f'),(0x80933AD4,4,'f'),(0x80933B14,5,'f'),(0x80933B2C,6,'f'),
            (0x80933B48,7,'I'),(0x80933B60,9,'f')):
        data=arrays[row*32:row*32+28]
        if row==4:data=source.data[0x76A30:0x76A30+28]
        if kind=='h':data=struct.pack('>7h',*struct.unpack('>7I',data))
        n=12 if kind=='h' else 24
        if raw('river',address,n)!=data[:n]:raise ValueError('Changed native/source size category prefix')
        if row in (2,4):
            offset=TABLE+len(arrays);arrays+=data+bytes(-len(data)%4)
            packet[offset:TABLE+len(arrays)]=arrays[offset-TABLE:]
        else:offset=TABLE+row*32
        targets['river'][address]=RAM+offset
    window('river',0x80932564,(0x2F010006,0x1020000F,0x0018C080),(jump('river_ripple'),0,0))
    window('river',0x80933070,(0x2DA10006,0x10200022,0x000D6880),(jump('river_splash'),0,0))
    for name,address in (('river',0x80931CBC),('sea',0x80A9940C)):
        window(name,address,(0x0C015F89,),(jump('make_release'),))
    # Source size-dependent sea constants. These bridges retain every original
    # fish value, including the N64 salmon's different speed and shadow scale.
    for address,before,label in (
        (0x80A99008,(0x3C0180AA,0xC420AF34),'initial_scale'),
        (0x80A9A8C8,(0x3C0180AA,0xC420AF58),'comeback_scale'),
        (0x80A99A74,(0x3C0141B0,0x44815000),'escape_distance'),
        (0x80A9A134,(0x3C014170,0x44813000),'near_distance'),
        (0x80A9A2D0,(0x3C014170,0x44814000),'touch_distance'),
        (0x80A9A2D8,(0x3C013FA0,0x44815000),'touch_speed'),
        (0x80A9A484,(0x3C0180AA,0xC432AF4C),'back_speed'),
        (0x80A991F8,(0x24010006,0x46000086),'splash_kind'),
        (0x80A9A46C,(0,0x25F80013),'touch_count')):
        window('sea',address,before,(jump(label),0))
    for address,before,label in ((0x80A9924C,(0xE7A40018,0xE7A6001C),'splash_radius'),
                                  (0x80A9A560,(0xE7A40018,0xE7A6001C),'bite_radius')):
        window('sea',address,before,(jump(label),before[0]))
    for address,before,label in ((0x80A99C7C,(0x0C2A650B,0x24060002),'ripple'),
                                  (0x80A9A600,(0x0C2A6463,0x24060006),'splash')):
        window('sea',address,before,(jump(label),0))
    window('sea',0x80A9A3A4,(0x2401001F,0x240F0022,0x15C10003,0x24180021,
        0x10000002,0xAE0F01D4,0xAE1801D4),(jump('trash'),0,0,0,0,0,0))
    for address,before,label in ((0x80A99680,(0x27BDFFE8,0xAFBF0014),'position'),
                                  (0x80A9AADC,(0x8C8E01D4,0x2401001F),'near_init')):
        window('sea',address,before,(jump(label,False),0))
    window('fish',0x80A5B72C,(0x8E0201D4,0x24010023,0x240D0016,0x54410006,
        0x2401001F,0x3C0280A6,0xAE0D01D4,0x10000008,0x2442C8D0,0x2401001F,
        0x14410003,0x3C0280A6,0x10000003,0x2442C8D0,0x3C0280A6,0x2442C8BC),
        (0x8E0201D4,jump('dispatch'),0,0x1040000A,0,0x10000005,0,0,0,0,0,
         0x3C0280A6,0x10000003,0x2442C8D0,0x3C0280A6,0x2442C8BC))
    old_release=field['compiled']['symbols']['af_v3_creature_release_index']
    window('release',0x80A7A934,(0x0C000000|(old_release>>2&0x3FFFFFF),),(jump('release_index'),))
    changes={};receipts=[]
    for name,(data,reloc,ram,v,r) in owners.items():
        # Size is a halfword at 1D8, followed by unused padding. No current
        # owner reads or writes the origin-marker byte used by the constructor.
        if name!='release':
            text_size=u32(reloc,0)
            if any((u32(data,i)>>26 in range(32,64)) and (u32(data,i)&65535) in (0x1DA,0x1DB)
                   for i in range(0,text_size,4)):
                raise ValueError('Occupied native fish origin marker')
        new,fixed,receipt=rewrite(data,reloc,ram,targets[name],windows[name])
        changes[v]=new;changes[r]=fixed
        receipts.append(dict(receipt,name=name,vrom=v,reloc=r,ram=ram,
            original_sha256=sha256(data),original_reloc_sha256=sha256(reloc),targets=targets[name]))
        if name in ('fish','release'):
            original=next(o for o in field['owners'] if o['name']==name)
            by_address={q['address']:q for q in original['patches']}
            for patch in receipt['patches']:
                if patch['address'] in by_address:by_address[patch['address']]['after']=patch['after']
                else:original['patches'].append(patch)
            original.update(sha256=sha256(new),reloc_sha256=sha256(fixed),
                removed_relocations=sorted(set(original['removed_relocations'])|set(receipt['removed_relocations'])))
    if TABLE+len(arrays)>SIZE-16:raise ValueError('Fish world tables exceed retained padding')
    blob[at:at+SIZE]=packet;p.update(sha256=sha256(packet),crc32=zlib.crc32(packet))
    e['creature_fish']=dict(format='AFV3-CREATURE-FISH-WORLD-1',compiled=compiled,
        packet_ram=RAM,code_offset=CODE,table_ram=RAM+TABLE,table_bytes=len(arrays),table_sha256=sha256(arrays),
        owners=receipts,source_tables=donor,source_functions=source_functions,origin_marker_offset=0x1DA,
        installed=True,additional_resident_bytes=0,additional_scene_bytes=0,selectable=False,
        native_execution_tested=False,pending=['spawn readers','source coastal patrol/shore behaviour choice',
            'pocket icons','collection/profile persistence','ordinary gameplay'],
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    return e,changes


def install_world(base,prior,blob,output):
    """Continue the same category with real patrol alternatives and spawn code.

    Calendars/selection are installed together with the terrain consumers. The
    manager and saved season binding remain explicit pending work, not enabled
    fish. The mode word is zero until the private composer can resolve choices.
    """
    from v3_furniture_pipeline import Source
    from v3_console_disk_install import reservations
    from v3_creature_spawns import calendars
    from aflib import verified_rom
    e=copy.deepcopy(prior['equipment_resources']);fish=e['creature_fish']
    if fish.get('world'):raise ValueError('Fish world category is already installed')
    if any(a<WORLD_RAM+WORLD_SIZE and WORLD_RAM<b for a,b in reservations(prior)):
        raise ValueError('Fish world packet overlaps a retained allocation')
    if WORLD_RAM+WORLD_SIZE>0x807DA800:raise ValueError('Fish world exceeds Expansion Pak reservation')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    original=verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    data,calendar=calendars(source,original)
    code,compiled=compile_part('creature_world',output/'creature_world',
        primary_source='overlays/v3/creature_patrol.c',extra_sources=(
            'overlays/v3/creature_water.c','overlays/v3/creature_spawns.c','overlays/v3/creature_patrol.S'))
    if len(code)>WORLD_TABLE or WORLD_TABLE+len(data)>WORLD_SIZE-16:
        raise ValueError('Complete world code/calendar exceeds packet bounds')
    packet=bytearray(WORLD_SIZE);packet[:len(code)]=code
    packet[WORLD_TABLE:WORLD_TABLE+len(data)]=data;packet[-16:]=struct.pack('>4I',*([0xAF465748]*4))
    old=next(o for o in fish['owners'] if o['name']=='sea')
    files=by_vrom(base);owner=files[old['vrom']].extract(base);reloc=files[old['reloc']].extract(base)
    if sha256(owner)!=old['sha256'] or sha256(reloc)!=old['reloc_sha256']:
        raise ValueError('Changed complete installed coastal behaviour owner')
    sections=struct.unpack_from('>4I',reloc)
    _,absolute,records,locations,_=native_references(owner,reloc,expected_sections=sections)
    updated=bytearray(owner);patches=[];removed=set()
    bindings=((0x80A9AE9C,0x80A9A9A4,'swim_init'),(0x80A9AEA0,0x80A9AC0C,'wait_init'),
              (0x80A9AEA4,0x80A9AC88,'escape_init'),(0x80A9AEB8,0x80A99F58,'swim'),
              (0x80A9AEBC,0x80A99E6C,'wait'),(0x80A9AEC0,0x80A9A910,'escape'))
    for address,before,name in bindings:
        at=address-old['ram'];after=compiled['symbols']['af_v3_patrol_'+name]
        if u32(updated,at)!=before or absolute.get(at)!=before:
            raise ValueError('Changed full coastal patrol callback table')
        struct.pack_into('>I',updated,at,after);removed.add(locations[at])
        patches.append(dict(address=address,before=before,after=after))
    keep=[r for r in records if r not in removed]
    fixed=(struct.pack('>5I',*sections,len(keep))+struct.pack('>'+str(len(keep))+'I',*keep)
           +bytes(len(reloc)-24-4*len(keep))+struct.pack('>I',len(reloc)))
    native_references(updated,fixed,expected_sections=sections)
    receipt=dict(name='sea',vrom=old['vrom'],reloc=old['reloc'],ram=old['ram'],sections=list(sections),
        original_sha256=sha256(owner),original_reloc_sha256=sha256(reloc),
        sha256=sha256(updated),reloc_sha256=sha256(fixed),patches=patches,removed_relocations=sorted(removed))
    # Keep the complete original functions: the N64 alternative calls these
    # through the actor's actual relocated program buffer.
    old.update(sha256=sha256(updated),reloc_sha256=sha256(fixed))
    old['patches'].extend(patches);old['removed_relocations']=sorted(set(old['removed_relocations'])|removed)
    mode=compiled['symbols']['af_v3_fish_patrol_mode']
    if u32(packet,mode-WORLD_RAM)!=0:raise ValueError('Unapproved source patrol mode default')
    names=('aGKK_swim','aGKK_swim2','aGKK_swim3','aGKK_swim4','aGKK_wait','aGKK_escape',
           'aGKK_swim_init','aGKK_swim2_init','aGKK_swim3_init','aGKK_swim4_init',
           'aGKK_wait_init','aGKK_escape_init','aGKK_check_wall','aGKK_check_offing',
           'aGKK_check_uki','mCoBG_CheckSandUt_ForFish','Actor_position_move','chase_angle')
    callbacks=[]
    for name in names:
        found=[at for at,rows in source.functions.items() if any(n==name for n,_ in rows)]
        if len(found)!=1:raise ValueError('Missing full world source consumer: '+name)
        callbacks.append(source.function(found[0])[1])
    blob.extend(bytes(-len(blob)%16));offset=len(blob);blob.extend(packet)
    fish['world']=dict(format='AFV3-FISH-WORLD-1',compiled=compiled,calendar=calendar,
        calendar_ram=WORLD_RAM+WORLD_TABLE,source_functions=callbacks,owners=[receipt],
        packet=dict(ram=WORLD_RAM,bytes=WORLD_SIZE,blob_offset=offset,vrom=BLOB+offset,
            sha256=sha256(packet),crc32=zlib.crc32(packet)),
        patrol_mode=dict(ram=mode,value=0,values={'N64':0,'GameCube':1},scope='imported coastal fish',
            browser_selection_installed=False),patrol_callbacks_installed=True,spawn_manager_installed=False,
        native_execution_tested=False,hardware_tested=False)
    fish.update(sources={p:sha256((ROOT/p).read_bytes()) for p in WORLD_SOURCES},
        additional_resident_bytes=WORLD_SIZE,
        pending=['spawn manager and saved seasons','behaviour-choice composition','pocket icons',
                 'collection/profile persistence','ordinary gameplay'])
    return e,{old['vrom']:bytes(updated),old['reloc']:fixed}


def install_manager(base,prior,blob,output):
    """Continue calendars through native creation and complete-category saving."""
    from v3_console_disk_install import reservations
    from v3_import_storage import jump
    import v3_creature_save as saves
    e=copy.deepcopy(prior['equipment_resources']);fish=e['creature_fish'];world=fish['world']
    if world.get('spawn_manager_installed'):raise ValueError('Fish spawn manager is already installed')
    p=world['packet'];at=p['blob_offset'];oldpacket=bytes(blob[at:at+p['bytes']])
    if (p['ram']!=WORLD_RAM or p['bytes']!=WORLD_SIZE or at+p['bytes']!=len(blob) or
            sha256(oldpacket)!=p['sha256'] or zlib.crc32(oldpacket)!=p['crc32']):
        raise ValueError('Creature world growth requires the verified resource tail')
    size=0xB000
    if any(a<WORLD_RAM+size and WORLD_RAM+WORLD_SIZE<b for a,b in reservations(prior)):
        raise ValueError('Creature world/save growth overlaps a retained reservation')
    if WORLD_RAM+size>0x807DA800 or 0x8046C000+saves.STATE_BYTES>0x8046D000:
        raise ValueError('Creature persistence exceeds checked memory bounds')
    code,compiled=compile_part('creature_world',output/'creature_world',
        primary_source='overlays/v3/creature_patrol.c',defines=(f'AF_FISH_CALENDAR_BYTES={world["calendar"]["bytes"]}',),
        extra_sources=('overlays/v3/creature_water.c','overlays/v3/creature_spawns.c',
            'overlays/v3/creature_patrol.S','overlays/v3/creature_manager.c','overlays/v3/creature_manager.S'))
    if len(code)>WORLD_TABLE:raise ValueError('Connected fish manager overlaps calendars')
    packet=bytearray(oldpacket+bytes(size-len(oldpacket)))
    packet[:WORLD_TABLE]=code+bytes(WORLD_TABLE-len(code))
    packet[-16:]=struct.pack('>4I',*([0xAF465748]*4))
    record,updates=saves.install(prior,e,blob,compiled,packet,output)
    files=by_vrom(base);changes={};owners=[]
    sea=next(o for o in fish['owners'] if o['name']=='sea')
    owner=files[sea['vrom']].extract(base);raw=bytearray(owner)
    if sha256(owner)!=sea['sha256']:raise ValueError('Changed complete coastal callbacks')
    patches=[]
    for row in world['owners'][0]['patches']:
        name=next(n for n,a in world['compiled']['symbols'].items() if a==row['after'] and n.startswith('af_v3_patrol_'))
        off=row['address']-sea['ram'];target=compiled['symbols'][name]
        if u32(raw,off)!=row['after']:raise ValueError('Changed coastal callback target')
        struct.pack_into('>I',raw,off,target)
        patches.append(dict(address=row['address'],before=row['after'],after=target))
    sea['patches'].extend(patches);sea['sha256']=sha256(raw);changes[sea['vrom']]=bytes(raw)
    owners.append(dict(name='sea',vrom=sea['vrom'],ram=sea['ram'],original_sha256=sha256(owner),
        sha256=sha256(raw),patches=patches))
    vrom,reloc,ram=0x8253C0,0x827BE0,0x8092DBC0
    owner=files[vrom].extract(base);rel=files[reloc].extract(base)
    if sha256(owner)!=world['calendar']['native_owner_sha256']:
        raise ValueError('Changed complete native fish spawn manager')
    sections=struct.unpack_from('>4I',rel)
    _,_,_,locations,_=native_references(owner,rel,expected_sections=sections)
    entry=0x8092ECAC;off=entry-ram
    if owner[off:off+8]!=struct.pack('>2I',0x27BDFFB0,0xAFB00020) or off in locations or off+4 in locations:
        raise ValueError('Changed relocation-free native spawn prologue')
    after=struct.pack('>2I',jump(compiled['symbols']['af_v3_fish_spawn']),0)
    raw=bytearray(owner);raw[off:off+8]=after;changes[vrom]=bytes(raw)
    owners.append(dict(name='spawn',vrom=vrom,reloc=reloc,ram=ram,sections=list(sections),
        original_sha256=sha256(owner),sha256=sha256(raw),reloc_sha256=sha256(rel),
        patches=[dict(address=entry,before=owner[off:off+8].hex(),after=after.hex())]))
    blob[at:]=packet
    p.update(bytes=size,sha256=sha256(packet),crc32=zlib.crc32(packet))
    world.update(compiled=compiled,manager_owners=owners,save=record,spawn_manager_installed=True,
        native_execution_tested=False,spawn_mode=dict(ram=compiled['symbols']['af_v3_fish_spawn_mode'],
            value=0,browser_selection_installed=False,source_calendar_connected=True,
            native_additive_policy_installed=False,native_acre_protection_retained=True))
    world['patrol_mode']['ram']=compiled['symbols']['af_v3_fish_patrol_mode']
    sources=(*WORLD_SOURCES,*saves.SOURCES,'overlays/v3/creature_manager.c','overlays/v3/creature_manager.S')
    fish.update(sources={path:sha256((ROOT/path).read_bytes()) for path in sources},
        additional_resident_bytes=size-WORLD_SIZE,
        pending=['native additive spawning and behaviour-choice composition','pocket icons',
            'catch/collection UI readers','ordinary gameplay'])
    return e,changes,updates


def pocket_icons(source,equipment,packet,regions,descriptor_offset):
    """Convert the complete creature icon category into verified unused padding."""
    from title_assets import pack4,untile
    from v3_villager_art import native_palette
    from v3_creature_items import source_records
    rows,_=source_records(source)
    if rows!=equipment['creature_items']['rows']:raise ValueError('Changed complete creature parent records')
    tables={};receipts=[]
    parent,n=source.symbol('item_tex_data_table$779');bindings=source.pointers(parent,n)
    if n!=64:raise ValueError('Changed complete icon category map')
    for kind,name,count,category in (('fish','fish_tex_table$766',40,3),('insect','insect_tex_table$776',45,13)):
        start,size=source.symbol(name);pointers=source.pointers(start,size)
        if (size!=count*8 or source.data[start:start+size]!=bytes(size) or
                set(pointers)!=set(range(start,start+size,4)) or bindings.get(parent+category*4)!=start):
            raise ValueError('Changed complete creature icon/category binding')
        tables[kind]=(start,pointers)
        receipts.append(dict(symbol=name,offset=start,bytes=size,pointers=pointers))
    functions=[]
    for at,n,digest in ((0x27DDCC,1364,'6d4d8f5f7c64617bb068d63f77b0b776010670245f113ef466e9494b712c7738'),
                        (0x27E320,672,'e357f68f7a995bf8f989c6fb7da6ad47f803b151b1ab9c34662eae8f0b9f1814')):
        data,function=source.function(at)
        if len(data)!=n or sha256(data)!=digest:raise ValueError('Changed complete source icon drawing consumer')
        functions.append(function)
    cursors=[(a+31)&~31 for a,b in regions];resources=[];offsets={};descriptors=[]
    table=bytearray(struct.pack('>4I',0x41464350,1,17,8)+bytes(17*8))
    if descriptor_offset&31 or any(packet[descriptor_offset:descriptor_offset+len(table)]):
        raise ValueError('Creature icon descriptors overlap occupied data')
    def store(data):
        for i,(_,end) in enumerate(regions):
            pos=cursors[i]
            if pos+len(data)<=end:
                if any(packet[pos:pos+len(data)]):raise ValueError('Creature icons overlap retained packet code/data')
                packet[pos:pos+len(data)]=data;cursors[i]=(pos+len(data)+31)&~31
                return pos
        raise ValueError('Complete creature icons exceed checked packet padding')
    for i,row in enumerate(rows):
        start,pointers=tables[row['category']];pair=[]
        for lane,kind,n in ((0,'palette',64),(4,'texture',512)):
            target=pointers[start+row['source_index']*8+lane]
            name,begin,size=source.containing(target,exact=True)
            if begin!=target or size!=n or source.pointers(target,n):
                raise ValueError('Incomplete creature CI4 icon or dual palette')
            key=(target,kind)
            if key not in offsets:
                raw=source.data[target:target+n]
                data=(native_palette(raw[:32])+native_palette(raw[32:]) if kind=='palette'
                      else pack4(untile(raw,32,32,4)))
                pos=store(data);offsets[key]=WORLD_RAM+pos
                resources.append(dict(symbol=name,source_offset=target,kind=kind,bytes=n,
                    offset=pos,ram=WORLD_RAM+pos,sha256=sha256(data),source_sha256=sha256(raw)))
            pair.append(offsets[key])
        struct.pack_into('>2I',table,16+i*8,*pair)
        descriptors.append(dict(item_id=row['item_id'],source_item_id=row['source_item_id'],
            descriptor_ram=WORLD_RAM+descriptor_offset+16+i*8,palette=pair[0],texture=pair[1]))
    packet[descriptor_offset:descriptor_offset+len(table)]=table
    return dict(rows=descriptors,resources=resources,source_tables=receipts,source_functions=functions,
        table_ram=WORLD_RAM+descriptor_offset,table_bytes=len(table),table_sha256=sha256(table),
        resource_bytes=sum(r['bytes'] for r in resources),width=32,height=32,palettes_per_icon=2,
        format_native='CI4/RGBA5551',native_drawing_tested=False)


def connect_catches(base,prior,blob,output,core):
    """Continue the category through native catches and completion consumers.

    Reuse the current world/save allocation and every converted resource. No
    species-specific installer, new saved layout, or additional DMA is needed.
    """
    from aflib import CODE_RAM,CODE_VROM
    from v3_import_storage import jump
    from v3_equipment_runtime import PLAYER_VROM,PLAYER_RELOC,PLAYER_RAM
    import v3_creature_save as saves
    e=copy.deepcopy(prior['equipment_resources']);fish=e['creature_fish'];world=fish['world']
    if world.get('pocket_icons'):raise ValueError('Creature pocket consumers are already connected')
    files=by_vrom(base)
    if core is None or bytes(core)!=files[CODE_VROM].extract(base):
        raise ValueError('Catch integration requires the complete checked native core')
    p=world['packet'];at=p['blob_offset'];packet=bytearray(blob[at:at+p['bytes']])
    if p['ram']!=WORLD_RAM or p['bytes']!=0xB000 or sha256(packet)!=p['sha256'] or zlib.crc32(packet)!=p['crc32']:
        raise ValueError('Changed complete connected world/save packet')
    save=world['save'];oldcompiled=world['compiled'];oldsymbols=oldcompiled['symbols']
    stable=e['console_storage']['compiled']['symbols']
    icon_offset=(0x4000+save['codec']['bytes']+31)&~31
    code,compiled=compile_part('creature_world',output/'creature_world',
        primary_source='overlays/v3/creature_patrol.c',defines=saves.DEFINES+(
            f'AF_FISH_CALENDAR_BYTES={world["calendar"]["bytes"]}',),
        extra_sources=('overlays/v3/creature_water.c','overlays/v3/creature_spawns.c',
            'overlays/v3/creature_patrol.S','overlays/v3/creature_manager.c',
            'overlays/v3/creature_manager.S','overlays/v3/creature_collection.c',
            'overlays/v3/creature_icon.c','overlays/v3/creature_icon.S'),
        link_symbols={
            'AF_CREATURE_ITEM_TYPE':e['creature_items']['code']['symbols']['af_v3_creature_item_type'],
            'AF_CREATURE_SAVE_COLLECT':save['codec']['symbols']['af_v3_save_collect_extended'],
            'AF_CREATURE_REQUIRE_STATE':stable['af_v3_require_save_state'],
            'AF_CREATURE_SAVE_HALT':stable['af_v3_save_halt'],
            'AF_CREATURE_ICONS':WORLD_RAM+icon_offset})
    if len(code)>WORLD_TABLE:raise ValueError('Connected creature consumers overlap calendars')
    symbols=compiled['symbols'];packet[:WORLD_TABLE]=code+bytes(WORLD_TABLE-len(code))
    # The saved season helper calls this shared core. Preserve its complete
    # binding; a moved core requires a deliberate helper relink, not stale code.
    if symbols['af_v3_spawn_terms']!=oldsymbols['af_v3_spawn_terms']:
        raise ValueError('Connected world moves the retained saved-season dependency')
    changes={};owners=[]
    sea=next(o for o in fish['owners'] if o['name']=='sea')
    raw=bytearray(files[sea['vrom']].extract(base));before=bytes(raw)
    if sha256(raw)!=sea['sha256']:raise ValueError('Changed complete coastal owner')
    patches=[]
    for row in world['manager_owners'][0]['patches']:
        name=next(n for n,a in oldsymbols.items() if a==row['after'] and n.startswith('af_v3_patrol_'))
        pos=row['address']-sea['ram'];target=symbols[name]
        if u32(raw,pos)!=row['after']:raise ValueError('Changed installed coastal callback')
        struct.pack_into('>I',raw,pos,target)
        patches.append(dict(address=row['address'],before=row['after'],after=target))
    sea['patches'].extend(patches);sea['sha256']=sha256(raw);changes[sea['vrom']]=bytes(raw)
    owners.append(dict(name='sea',vrom=sea['vrom'],ram=sea['ram'],original_sha256=sha256(before),
        sha256=sha256(raw),patches=patches))
    spawn=next(o for o in world['manager_owners'] if o['name']=='spawn')
    raw=bytearray(files[spawn['vrom']].extract(base));before=bytes(raw)
    if sha256(raw)!=spawn['sha256']:raise ValueError('Changed installed spawn owner')
    pos=0x8092ECAC-spawn['ram'];expected=struct.pack('>2I',jump(oldsymbols['af_v3_fish_spawn']),0)
    if raw[pos:pos+8]!=expected:raise ValueError('Changed installed spawn entry')
    after=struct.pack('>2I',jump(symbols['af_v3_fish_spawn']),0);raw[pos:pos+8]=after
    changes[spawn['vrom']]=bytes(raw)
    owners.append(dict(spawn,original_sha256=sha256(before),sha256=sha256(raw),
        patches=[dict(address=0x8092ECAC,before=expected.hex(),after=after.hex())]))

    jal=lambda name:0x0C000000|(symbols[name]>>2&0x3FFFFFF)
    windows=[]
    for address,expected,after in (
        (0x808CCE18,'8dce6fd8241800010078c8048dcf0ac001f94026250900012d290001ac890d14',
            (0x00602825,jal('af_v3_creature_last_insect'),0,0x00402025)),
        (0x808CD568,'3c0280138c426fd824190001007948048c580ac003095025ac4a0ac0',
            (0x00E02025,0x00602825,jal('af_v3_creature_notice_insect'),0,0x00403825)),
        (0x808CF704,'28e10020102000113c05801324a56ea08ca801382418000100f818048d090abc01235026254b00012d6b0001ac8b00148ca201388c4c0abc01836825ac4d0abc',
            (0x02002025,0x00E02825,jal('af_v3_creature_notice_fish'),0))):
        raw=bytes.fromhex(expected);words=struct.unpack('>'+str(len(raw)//4)+'I',raw)
        windows.append((address,words,after+(0,)*(len(words)-len(after))))
    raw=files[PLAYER_VROM].extract(base);reloc=files[PLAYER_RELOC].extract(base)
    normalized=bytearray(raw)
    if world.get('catch_records_installed'):
        old=next(o for o in world['manager_owners'] if o['name']=='player_catches')
        if sha256(raw)!=old['sha256'] or sha256(reloc)!=old['reloc_sha256'] or old['removed_relocations']:
            raise ValueError('Changed installed catch consumer/relocations')
        for patch in old['patches']:
            pos=patch['address']-PLAYER_RAM
            if u32(normalized,pos)!=patch['after']:raise ValueError('Changed installed catch call')
            struct.pack_into('>I',normalized,pos,patch['before'])
    data,fixed,receipt=rewrite(bytes(normalized),reloc,PLAYER_RAM,{},windows)
    for patch in receipt['patches']:patch['before']=u32(raw,patch['address']-PLAYER_RAM)
    receipt.update(name='player_catches',vrom=PLAYER_VROM,reloc=PLAYER_RELOC,ram=PLAYER_RAM,
        original_sha256=sha256(raw),original_reloc_sha256=sha256(reloc))
    changes[PLAYER_VROM]=data;changes[PLAYER_RELOC]=fixed;owners.append(receipt)

    core_before=bytes(core);patches=[]
    if world.get('catch_records_installed'):
        old=next(o for o in world['manager_owners'] if o['name']=='completion')
        if sha256(core)!=old['sha256']:raise ValueError('Changed installed completion owner')
        for patch in old['patches']:
            pos=patch['address']-CODE_RAM
            if core[pos:pos+8].hex()!=patch['after']:raise ValueError('Changed installed completion entry')
            core[pos:pos+8]=bytes.fromhex(patch['before'])
    for address,size,digest,name in (
        (0x800B9E44,76,'d538e61f701de16c39d5e16da01d4010b11239055690f4d25fb0a839a23303f9','af_v3_creature_start_complete'),
        (0x800BA054,72,'7d1e68fc3f347558fd7560399a3402a17543f4cfeb7acd1ae00f478c313da9c4','af_v3_creature_fish_talk'),
        (0x800BA09C,72,'b89f49facdd38fdfc1cfc6f74005fb0ab2e4377a2ee2a81a2df0d6a982ff2f25','af_v3_creature_insect_talk')):
        pos=address-CODE_RAM
        if sha256(core[pos:pos+size])!=digest:raise ValueError('Changed native completion consumer')
        guard_incoming(core,len(core),CODE_RAM,[(pos,8)])
        old=core_before[pos:pos+8];new=struct.pack('>2I',jump(symbols[name]),0)
        core[pos:pos+8]=new
        patches.append(dict(address=address,before=old.hex(),after=new.hex(),function_sha256=digest))
    owners.append(dict(name='completion',vrom=CODE_VROM,ram=CODE_RAM,
        original_sha256=sha256(core_before),sha256=sha256(core),patches=patches))
    from v3_furniture_pipeline import Source
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    icons=pocket_icons(source,e,packet,[(len(code),WORLD_TABLE),
        (icon_offset+16+17*8,0x6000),(0x6000+save['runtime']['bytes'],0xA000),
        (0xA000+save['helpers']['bytes'],0xAFF0)],icon_offset)
    from v3_furniture_icon import VROM as MENU,RELOC as MENU_RELOC,RAM as MENU_RAM
    raw=files[MENU].extract(base);reloc=files[MENU_RELOC].extract(base)
    # Other categories legitimately resize menu allocations outside this draw
    # function. Verify the entire drawing consumer and its installed hooks,
    # rather than treating an old category's whole-owner receipt as current.
    normalized=bytearray(raw)
    for address,expected,original in (
        (0x8085C880,struct.pack('>2I',jump(0x8046AB00),0),bytes.fromhex('00194b0324010001')),
        (0x8085C954,bytes.fromhex(e['pocket_icons']['hook']['after']),bytes.fromhex('3c0f808625efdd68'))):
        pos=address-MENU_RAM
        if normalized[pos:pos+8]!=expected:raise ValueError('Changed installed shared icon hook')
        normalized[pos:pos+8]=original
    if (sha256(normalized[0x8085C7B8-MENU_RAM:0x8085CE18-MENU_RAM])!=e['pocket_icons']['native_consumer_sha256'] or
            sha256(reloc)!=e['pocket_icons']['relocation_sha256']):
        raise ValueError('Changed complete shared pocket icon consumer/relocations')
    data,fixed,receipt=rewrite(raw,reloc,MENU_RAM,{},[(0x8085C968,
        (0x3C198086,0x0338C821,0x8F39E460,0x000248C0,0x8FA400CC,0x03292821),
        (jump(symbols['af_v3_creature_icon_hook']),0,0,0,0,0))])
    receipt.update(name='pocket_icons',vrom=MENU,reloc=MENU_RELOC,ram=MENU_RAM,
        original_sha256=sha256(raw),original_reloc_sha256=sha256(reloc))
    changes[MENU]=data;changes[MENU_RELOC]=fixed;owners.append(receipt)
    e['pocket_icons'].update(owner_sha256=sha256(data),relocation_sha256=sha256(fixed))
    blob[at:at+p['bytes']]=packet;p.update(sha256=sha256(packet),crc32=zlib.crc32(packet))
    world.update(compiled=compiled,manager_owners=owners,catch_records_installed=True,pocket_icons=icons,
        collection_ui_installed=False,native_execution_tested=False)
    world['patrol_mode']['ram']=symbols['af_v3_fish_patrol_mode']
    world['spawn_mode'].update(ram=symbols['af_v3_fish_spawn_mode'],native_additive_policy_installed=True,
        native_opportunity_weight=100,values={'N64':0,'GameCube':1})
    fish.update(additional_resident_bytes=0,
        sources={path:sha256((ROOT/path).read_bytes()) for path in (*fish['sources'],
            'overlays/v3/creature_collection.c','overlays/v3/creature_icon.c','overlays/v3/creature_icon.S')},
        pending=['behaviour-choice composition','collection UI','ordinary gameplay'])
    return e,changes
