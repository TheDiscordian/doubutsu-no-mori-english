"""Bind a complete floor-sound category to verified native programs and fonts."""
import copy
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from v3_asset_loader import ROOT, compile_part
from v3_sound_programs import (bind_trigger, trigger_program, installed_resource,
    install_audio_resources, permanent_budget)
from v3_surface_items import RAM, BOOT, BOOT_END
from v3_villager_audio import (read_audio_donor, header_entry, resource, span,
    GC_SECTIONS, instrument, extended_envelope)

SOURCES=('tools/v3_surface_audio.py','tools/v3_sound_programs.py',
    'tools/v3_surface_runtime.py','tools/v3_furniture_install.py')
NATIVE_TABLE_SHA='4b0c696020afdc533cfb4a6b3e799b5f297900fbc4f979e1e59671d69410b6be'
DONOR_TABLE_SHA='104e7f8b0fac4806301b2366491aefc715f6d6ecf39d731a7a8ae1d98c38f8ef'
FUNCTIONS=((0x800F9064,0xB4,'97f036137fb39704d741f348f407ea90f0db82bce4fee7dfa764c3c0304172ce'),
    (0x800F9170,0x70,'679cc0d9ada71971d83f49a962d6e09b0d80ae9bbed8b6f403c93d925b66689c'),
    (0x800FA520,0x60,'585c804b7ee0f7ddab1f5c6029be98b225ea157dea63681c1a78dc02d5534e52'))


def program(sequence,origin):
    """Read a complete supported program; exclude only trailing unused padding."""
    if span(sequence,origin,4)[0]!=0xEB:raise ValueError('Not an explicit-font trigger')
    at=origin+7;envelope=None
    if span(sequence,at,1)==b'\xcb':
        envelope=struct.unpack_from('>H',sequence,at+1)[0];at+=4
    while span(sequence,at,1)!=b'\xff':
        if not 0x40<=sequence[at]<=0x7F:raise ValueError('Unsupported complete note program')
        at+=1;at+=2 if span(sequence,at,1)[0]&128 else 1;at+=1
    at+=1
    if envelope is not None:at=envelope+len(extended_envelope(sequence,envelope))
    description=trigger_program(sequence,origin,at)
    return sequence[origin:at],description


def prepare(image,prior):
    if sha256(image)!=prior['output_sha256']:raise ValueError('Unchecked surface audio base')
    code=by_vrom(image)[CODE_VROM].extract(image)
    sequence,_,_=installed_resource(image,code,'seq',199)
    if sha256(sequence)!=prior['equipment_resources']['sound_programs']['sequence']['sha256']:
        raise ValueError('Changed complete current sound sequence')
    dol,audio=read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    sources={k:span(audio,*struct.unpack_from('>II',header_entry(dol.read,0x800CE450,i)))
        for i,k in enumerate(('seq','bank','wave'))}
    source,_=resource(dol.read,GC_SECTIONS,sources,'seq',242)
    if sha256(source)!='790526e46582305f94eb05851337ccab5b8aa248c451e98f99f2d65965ab2a22':
        raise ValueError('Changed complete donor effects sequence')
    native_table=span(code,0x80113A64-CODE_RAM,146);donor_table=dol.read(0x800A9938,190)
    if sha256(native_table)!=NATIVE_TABLE_SHA or sha256(donor_table)!=DONOR_TABLE_SHA:
        raise ValueError('Changed complete floor selector tables')
    native_map=struct.unpack_from('>H',code,0x80115D80-CODE_RAM+199*2)[0]
    donor_map=struct.unpack('>H',dol.read(0x800CE490+242*2,2))[0]
    nb=span(code,0x80115D80-CODE_RAM+native_map,5);gb=dol.read(0x800CE490+donor_map,5)
    if nb!=bytes((4,2,141,140,139)) or gb!=bytes((4,2,155,154,153)):
        raise ValueError('Changed complete SFX font maps')
    nfonts={};identities={};gfonts={}
    for selector in range(3):
        bank,header,_=installed_resource(image,code,'bank',nb[4-selector])
        wave,_,_=installed_resource(image,code,'wave',header[10]);nfonts[selector]=(bank,wave,header)
        for i in range(header[12]):
            if u32(bank,8+i*4):
                identities[selector,i]=instrument(bank,wave,i,header[12],extended=True)
    def native_binding(desc):
        selector=desc['selector'];index=desc['instrument']
        if selector not in gfonts:
            b,h=resource(dol.read,GC_SECTIONS,sources,'bank',gb[4-selector])
            w,_=resource(dol.read,GC_SECTIONS,sources,'wave',h[10]);gfonts[selector]=(b,w,h)
        b,w,h=gfonts[selector];identity=instrument(b,w,index,h[12],extended=True)
        matches=[key for key,value in identities.items() if value==identity]
        if not matches:raise ValueError('Floor category needs an additional complete instrument')
        target=(selector,index) if (selector,index) in matches else min(matches)
        return target,identity
    def pointers(seq,group,count):
        table=struct.unpack_from('>H',seq,0x188+group*2)[0]
        return table,list(struct.unpack('>'+str(count)+'H',span(seq,table,count*2)))
    n0,np0=pointers(sequence,0,80);n3,np3=pointers(sequence,3,73)
    g0,gp0=pointers(source,0,128);g3,gp3=pointers(source,3,81)
    if (n0,n3,g0,g3)!=(0x194,0x2F6A,0x194,0x3C20):
        raise ValueError('Changed source/native complete floor dispatch tables')
    # The native step selector uses offsets 0,9,...,63; the donor uses 0,10,...,70.
    # Its nine-stride final column is reserved/silent, with complete unused grass
    # programs still present in the sequence. Other live programs stay unchanged.
    silent=np3[0]
    if sequence[silent]!=255 or any(np3[i]!=silent for i in range(9,73,9)):
        raise ValueError('Native reserved footstep slots are occupied')
    available_programs={}
    for at in range(len(sequence)-10):
        if sequence[at]!=0xEB or sequence[at+3]!=0x88 or sequence[at+6]!=255:continue
        try:raw,desc=program(sequence,at)
        except (ValueError,struct.error):continue
        available_programs[at]=(raw,desc)
    result=bytearray(sequence);rows=[];bindings=[];drag_pointers=np0[:]
    native_priority=span(code,0x80113B84-CODE_RAM,128);donor_priority=dol.read(0x800A9A90,128)
    surface_rows=sorted((r for r in prior['room_surfaces']['rows'] if r['kind']=='floor'),
        key=lambda r:r['destination_index'])
    selectors=sorted({struct.unpack_from('>H',donor_table,r['source_index']*2)[0] for r in surface_rows})
    resolved={}
    for selector in selectors:
        if not 27<=selector<=35:raise ValueError('New floor needs another shared sound category')
        mapping=dict(source_selector=selector,walking=[],movement=None)
        for variant in range(8):
            src_id=0x2E6+selector+10*variant;dst_id=0x2E6+selector+9*variant
            origin=gp3[src_id&255];raw,desc=program(source,origin)
            (ns,ni),identity=native_binding(desc)
            matches=[at for at,(data,_) in available_programs.items()
                if (at-origin)%2==0 or desc['envelope'] is None
                if len(data)==len(raw) and bind_trigger(raw,desc,at,ns,ni)==data]
            old=np3[dst_id&255]
            if old!=silent:
                if old not in matches:raise ValueError('Complete native footstep differs from donor')
                target=old
            else:
                if not matches:raise ValueError('Missing complete native footstep program')
                target=min(matches);struct.pack_into('>H',result,n3+(dst_id&255)*2,target)
                bindings.append(dict(index=dst_id&255,before=old,after=target))
            if native_priority[dst_id&255]!=donor_priority[src_id&255]:
                raise ValueError('Footstep priority differs across platforms')
            mapping['walking'].append(dict(source_sound_id=src_id,native_sound_id=dst_id,
                source_program=desc,native_offset=target,native_selector=ns,native_instrument=ni,
                instrument_identity=identity,program_sha256=sha256(available_programs[target][0]),
                reused_unreferenced_program=old==silent))
        raw,desc=program(source,gp0[selector]);(ns,ni),identity=native_binding(desc)
        matches=[i for i,at in enumerate(np0) if at in available_programs
            and ((at-desc['origin'])%2==0 or desc['envelope'] is None)
            and bind_trigger(raw,desc,at,ns,ni)==available_programs[at][0]
            and native_priority[i]==donor_priority[selector]]
        if matches:target=selector if selector in matches else min(matches);offset=np0[target];reused=True
        else:
            target=len(drag_pointers)
            if target>=128 or native_priority[target]!=donor_priority[selector]:
                raise ValueError('No new movement slot with matching complete priority')
            result.extend(bytes((len(result)^desc['origin'])&1) if desc['envelope'] is not None else b'')
            offset=len(result);result.extend(bind_trigger(raw,desc,offset,ns,ni));drag_pointers.append(offset);reused=False
        mapping['movement']=dict(source_sound_id=selector,native_sound_id=target,source_program=desc,
            native_offset=offset,native_selector=ns,native_instrument=ni,instrument_identity=identity,
            program_sha256=sha256(result[offset:offset+len(raw)]),reused_program=reused)
        resolved[selector]=mapping;rows.append(mapping)
    result.extend(bytes(len(result)&1));table=len(result)
    result.extend(struct.pack('>'+str(len(drag_pointers))+'H',*drag_pointers))
    struct.pack_into('>H',result,0x188,table);result.extend(bytes(-len(result)%16))
    if len(result)>65536:raise ValueError('Surface audio exceeds native pointer capacity')
    walk=list(struct.unpack('>73H',native_table))+[27]*183
    movement=walk[:];imports=[]
    for row in surface_rows:
        index=row['destination_index'];selector=struct.unpack_from('>H',donor_table,row['source_index']*2)[0]
        if not 73<=index<78:raise ValueError('Unregistered additive surface audio identity')
        walk[index]=selector;movement[index]=resolved[selector]['movement']['native_sound_id']
        imports.append(dict(item_id=row['destination_item_id'],index=index,source_index=row['source_index'],
            source_selector=selector,native_walk_selector=walk[index],native_movement_sound=movement[index]))
    if len(imports)!=5:raise ValueError('Incomplete five-floor sound category')
    font,wave,header=nfonts[1]
    metadata=dict(font_index=nb[3],wave_index=header[10],layout=dict(instrument_count=header[12]))
    return dict(sequence=bytes(result),font=font,wave=wave,
        walk=struct.pack('>256H',*walk),movement=struct.pack('>256H',*movement)),dict(
        format='AFV3-SURFACE-AUDIO-1',source_sequence_sha256=sha256(source),
        previous_sequence_sha256=sha256(sequence),source_floor_table_sha256=sha256(donor_table),
        native_floor_table_sha256=sha256(native_table),selectors=rows,imports=imports,
        footstep_bindings=bindings,movement_table=dict(previous_offset=n0,previous_count=80,offset=table,count=len(drag_pointers)),
        additional_instruments=0,additional_wave_bytes=0,sequence_growth=len(result)-len(sequence),
        native_synthesis_tested=False,physical_audio_played=False),metadata


def patch_consumers(code):
    contracts=[]
    # All table indices are explicitly truncated by the existing u8 readers.
    # Each replacement table has 256 rows, retaining all original special rooms.
    for address,size,digest in FUNCTIONS+((0x800F8E24,0x1A0,'d1f0859dd60b8cf63e142f03a27cc206438e61773cfa7e09a9f8898fb1c61981'),):
        if sha256(span(code,address-CODE_RAM,size))!=digest:
            raise ValueError('Changed complete native surface audio consumer')
        contracts.append(dict(address=address,bytes=size,sha256=digest))
    patches=[]
    for address,old,new in ((0x800F9098,0x3C048011,0x3C04804C),(0x800F90A0,0x94843A64,0x9484FA00),
        (0x800F91A4,0x3C048011,0x3C04804C),(0x800F91AC,0x94843A64,0x9484FA00),
        (0x800FA550,0x3C048011,0x3C04804C),(0x800FA560,0x94843A64,0x9484FC00)):
        if u32(code,address-CODE_RAM)!=old:raise ValueError('Changed native floor selector load')
        struct.pack_into('>I',code,address-CODE_RAM,new)
        patches.append(dict(address=address,before=f'{old:08x}',after=f'{new:08x}'))
    return contracts,patches


def install(base,prior,blob,core,output):
    surface=copy.deepcopy(prior['room_surfaces']);items=surface['items']
    if not surface.get('scoring') or surface.get('sound'):raise ValueError('Invalid surface audio stage')
    resources,receipt,audio=prepare(base,prior)
    contracts,patches=patch_consumers(core)
    seq,bank,wave,changes,growth,heap_growth,heap_patches,before,fire=install_audio_resources(
        base,prior,blob,core,resources['sequence'],resources,audio)
    equipment=copy.deepcopy(prior['equipment_resources']);shared=equipment['sound_programs']
    shared.update(previous_sequence=copy.deepcopy(shared['sequence']),sequence=seq,
        after_budget=permanent_budget(core),native_synthesis_tested=False)
    shared['surface_batch']=dict(sequence=seq,footstep_bindings=receipt['footstep_bindings'],
        movement_table=receipt['movement_table'])
    for key in ('furniture_audio','furniture_level_audio'):
        if key in equipment:equipment[key].update(sequence=copy.deepcopy(seq),font=copy.deepcopy(bank),
            wave=copy.deepcopy(wave),after_budget=copy.deepcopy(shared['after_budget']))
    at=items['blob_offset'];packet=bytearray(blob[at:at+items['bytes']])
    if len(packet)!=0x4000 or sha256(packet)!=items['sha256'] or zlib.crc32(packet)!=items['crc32']:
        raise ValueError('Changed complete surface packet')
    tables=[]
    for kind,offset in (('walk',0x3A00),('movement',0x3C00)):
        data=resources[kind]
        if len(data)!=512 or any(packet[offset:offset+512]):raise ValueError('Surface audio table storage occupied')
        packet[offset:offset+512]=data
        tables.append(dict(kind=kind,offset=offset,ram=RAM+offset,bytes=512,sha256=sha256(data)))
    ea=equipment['blob_offset'];ep=bytearray(blob[ea:ea+equipment['bytes']])
    if sha256(ep)!=equipment['sha256'] or zlib.crc32(ep)!=equipment['crc32']:
        raise ValueError('Changed complete equipment bootstrap packet')
    ba=BOOT-equipment['ram'];be=BOOT_END-equipment['ram'];crc=zlib.crc32(packet)
    boot,bc=compile_part('surface_bootstrap',output/'surface_bootstrap',defines=(
        f'AF_SURFACE_ITEMS_VROM=0x{items["vrom"]:X}u',f'AF_SURFACE_ITEMS_CRC=0x{crc:X}u',
        f'AF_SURFACE_ITEMS_BYTES=0x{len(packet):X}u'))
    if len(boot)>be-ba:raise ValueError('Surface sound bootstrap exceeds reservation')
    ep[ba:be]=boot+bytes(be-ba-len(boot));blob[ea:ea+len(ep)]=ep;blob[at:at+len(packet)]=packet
    items.update(sha256=sha256(packet),crc32=crc,additional_resident_bytes=0);items['bootstrap']['code']=bc
    equipment.update(sha256=sha256(ep),crc32=zlib.crc32(ep),surface_bootstrap=items['bootstrap'])
    receipt.update(tables=tables,native_consumers=contracts,consumer_patches=patches,sequence=seq,
        before_budget=before,after_budget=permanent_budget(core),audio_heap_growth=heap_growth,
        heap_patches=heap_patches,runtime_installed=True,saved_format_changed=False)
    surface['sound']=receipt;surface['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    return changes,dict(room_surfaces=surface,equipment_resources=equipment,fire_sound=fire,
        resource_growth=[growth] if growth else [],saved_format_changed=False)
