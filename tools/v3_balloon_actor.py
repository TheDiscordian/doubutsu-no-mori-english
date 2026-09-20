"""Shared complete flying-balloon actor, independent banks, and player lifetime."""
import copy
import re
import struct
import zlib
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from v3_asset_loader import BLOB,ROOT,compile_part
from v3_equipment_runtime import RAM,PLAYER_RAM,PLAYER_VROM,PLAYER_RELOC
from v3_furniture_pipeline import Source
from v3_import_storage import jump
from v3_npc_draw import relocation_offsets

CODE,END,PACKET=0x9300,0x9FF0,0xBA40
SOURCES=('tools/v3_balloon_actor.py','overlays/v3/balloon_actor.h','overlays/v3/balloon_actor.c',
         'overlays/v3/balloon_draw.c','overlays/v3/balloon_actor.ld','overlays/v3/reward_deferred.ld')


def bindings(source,core,owner,original):
    rows=[];body=bytearray();at=0xA3B2C
    while at<0xA42F0:
        raw,row=source.function(at);body.extend(raw);rows.append(row);at+=len(raw)
    if at!=0xA42F0 or sha256(body)!='1469a805bc3c0890b69f4d3b4c9d9e966c361c1f12c520e357e89d7667d14c3f':
        raise ValueError('Changed complete donor balloon actor')
    profile=source.data[0x12788:0x127AC]
    if profile.hex()!='00e605000000003022440003000004780000000000000000000000000000000000000000':
        raise ValueError('Changed complete donor balloon profile')
    links={p-0x12788:v for p,v in source.relocations.items() if 0x12788<=p<0x127AC}
    if links!={16:(1,1,1,0xA40E0),20:(1,1,1,0xA3B2C),24:(1,1,1,0xA403C),28:(1,1,1,0xA42C4)}:
        raise ValueError('Changed source actor callbacks')
    bounds=[]
    for name in ('symbol_addrs_code.txt','symbol_addrs_overlays.txt'):
        bounds.extend(int(a,16) for a in re.findall(r'= 0x([0-9A-Fa-f]+); // type:func',
            (ROOT/'upstream/af/linker_scripts/jp'/name).read_text()))
    entries=(0x80052228,0x800528D4,0x800530D8,0x800531F0,0x8005652C,0x8009A974,
             0x800B1C84,0x800588B8,0x800BD4E8,0x808BCC48,0x808DD748)
    files=by_vrom(original);native=[]
    for at in entries:
        data,ram,vrom=(owner,PLAYER_RAM,PLAYER_VROM) if at>=PLAYER_RAM else (core,CODE_RAM,CODE_VROM)
        last=min(x for x in bounds if x>at);raw=data[at-ram:last-ram]
        if raw!=files[vrom].extract(original)[at-ram:last-ram]:
            raise ValueError(f'Changed complete balloon API {at:08X}')
        native.append(dict(entry=at,end=last,sha256=sha256(raw)))
    return dict(source_functions=rows,source_profile=profile.hex(),source_profile_links=links,
                native_functions=native,source_category=5,native_category=4,source_steps_per_update=2,
                source_gravity=.2,native_half_step_gravity=.1,velocity_scale=.5)


def install(base,prior,blob,core,original,output):
    old=prior['equipment_resources'];actions=old['player_actions'];files=by_vrom(base)
    start=old['blob_offset'];module=bytearray(blob[start:start+old['bytes']])
    owner=bytearray(files[PLAYER_VROM].extract(base));rel=files[PLAYER_RELOC].extract(base)
    if (not actions.get('reward_exchange') or actions.get('balloon_actor') or old['bytes']!=0x12000
            or sha256(module)!=old['sha256'] or sha256(owner)!=actions['owner_sha256']
            or sha256(rel)!=actions['relocation_sha256'] or any(module[CODE:END])
            or any(module[PACKET:PACKET+0x60])):
        raise ValueError('Flying balloon requires the complete checked exchange proposal')
    for row in old['item_categories']['objects']:
        if row['offset']+row['object_bytes']>CODE:
            raise ValueError('Flying balloon overlaps complete category artwork')
    deferred=actions['reward_exchange']['codes']['reward_deferred']
    if deferred['offset']+deferred['code']['bytes']>PACKET:
        raise ValueError('Flying balloon descriptor overlaps deferred reward code')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    evidence=bindings(source,core,owner,original)
    apis=[]
    for at,name in ((0x800B12C8,'pointer'),(0x800B131C,'size'),(0x800B1650,'vrom')):
        hook=next(r for r in old['hooks'] if r['entry']==at)
        if (hook['helper']!='af_v3_equipment_'+name or
                core[at-CODE_RAM:at-CODE_RAM+8].hex()!=hook['after']):
            raise ValueError('Changed installed balloon resource API')
        apis.append(copy.deepcopy(hook))
    evidence['resource_apis']=apis
    resources=[]
    for index in range(40,50):
        row=next(r for r in old['records'] if r['index']==index)
        data=blob[row['blob_offset']:row['blob_offset']+row['bytes']]
        if len(data)!=row['bytes'] or sha256(data)!=row['sha256']:
            raise ValueError('Changed full balloon resource')
        p=row['pointer']-0x6000000
        if index<48 and (row['type']!=1 or len(data)>5728 or data[p:p+2]!=b'\x07\x04'):
            raise ValueError('Balloon model exceeds complete bank/joint/matrix capacity')
        if index>=48 and (row['type']!=4 or len(data)>1440):
            raise ValueError('Balloon motion exceeds complete bank capacity')
        resources.append(copy.deepcopy(row))
    code,compiled=compile_part('balloon_actor',output/'balloon_actor',extra_sources=('overlays/v3/balloon_draw.c',))
    symbols=compiled['symbols']
    if len(code)>END-CODE or symbols['af_v3_player_selected_equipment']!=actions['code']['symbols']['af_v3_player_selected_equipment']:
        raise ValueError('Balloon code exceeds storage or changes shared selection')
    module[CODE:CODE+len(code)]=code
    packet=bytearray(0x60)
    struct.pack_into('>8I',packet,0,0,0,0,0,0,RAM+PACKET+0x20,0,0)
    struct.pack_into('>HHIHH6I',packet,0x20,0xCB,4<<8,0x30,0x2244,3,0x2080,
        *[symbols['af_v3_balloon_'+n] for n in ('ct','dt','main','draw')],0)
    packet[0x50:]=b'AFBL'*4
    module[PACKET:PACKET+len(packet)]=packet
    patches=[]
    def patch(data,ram,vrom,at,before,after):
        off=at-ram
        if bytes(data[off:off+len(before)])!=before or len(before)!=len(after):
            raise ValueError(f'Changed balloon hook {at:08X}')
        data[off:off+len(after)]=after
        patches.append(dict(vrom=vrom,ram=ram,address=at,before=before.hex(),after=after.hex()))
    patch(core,CODE_RAM,CODE_VROM,0x80057E4C,struct.pack('>I',jump(0x804A0360,link=True)),
          struct.pack('>I',jump(symbols['af_v3_balloon_descriptor'],link=True)))
    allocation=old['held_rig_actions']['player_allocation']
    if allocation['bytes']!=0x13A0:raise ValueError('Unexpected player extension lifetime')
    patch(core,CODE_RAM,CODE_VROM,allocation['address'],struct.pack('>I',0x13A0),struct.pack('>I',0x13B0))
    patch(owner,PLAYER_RAM,PLAYER_VROM,0x808DD79C,struct.pack('>I',jump(0x808BCC48,link=True)),
          struct.pack('>I',jump(symbols['af_v3_balloon_player_init'],link=True)))
    # Only the ctor's displaced JAL loses its internal relocation. Native actor
    # descriptors, callbacks, and the no-demo sentinel retain their identities.
    off=0x808DD79C-PLAYER_RAM;count=u32(rel,16)
    rows=list(struct.unpack_from('>'+str(count)+'I',rel,20));removed=[r for r in rows if r==(0x44000000|off)]
    if len(removed)!=1 or off not in relocation_offsets(rel,len(owner)):
        raise ValueError('Missing unique relocated player-init call')
    kept=[r for r in rows if r not in removed];updated=bytearray(rel)
    struct.pack_into('>I',updated,16,len(kept))
    updated[20:20+count*4]=struct.pack('>'+str(len(kept))+'I',*kept)+bytes(4)
    report=copy.deepcopy(old);current=report['player_actions']
    current.update(owner_sha256=sha256(owner),relocation_sha256=sha256(updated),
                   removed_relocations=current['removed_relocations']+1)
    current['balloon_actor']=dict(code=compiled,offset=CODE,end=END,bindings=evidence,resources=resources,
        packet_offset=PACKET,packet_bytes=len(packet),packet_sha256=sha256(packet),actor_id=0xCB,
        actor_bytes=0x2080,player_pointer_offset=0x13A0,player_bytes=0x13B0,
        additional_scene_bytes=0x2090,patches=patches,removed_relocations=removed,
        complete_actor_installed=True,ordinary_release_installed=False,tumble_loss_installed=False,
        draw_uses_complete_source_models=True,saved_format_changed=False,ordinary_gameplay_tested=False)
    report['held_rig_actions']['player_allocation']['bytes']=0x13B0
    report['player_motion'].update(owner_sha256=sha256(owner),reloc_sha256=sha256(updated))
    report.update(sha256=sha256(module),crc32=zlib.crc32(module),additional_resident_bytes=0)
    blob[start:start+len(module)]=module
    return report,{PLAYER_VROM:bytes(owner),PLAYER_RELOC:bytes(updated)}
