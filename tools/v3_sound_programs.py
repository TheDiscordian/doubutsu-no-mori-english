"""Shared single-layer sound imports using verified existing native instruments.

Preserve the complete channel, note, pitch sweep, envelope, and padding. Only
internal pointers and equivalent instrument bindings change. Unsupported forms
fail; callers supply source sound IDs, not per-item audio implementations.
"""
import copy
import struct

from aflib import CODE_RAM, by_vrom, sha256, u32
from v3_asset_loader import BLOB, ROOT
from v3_fire_audio import NATIVE_VROMS
from v3_villager_audio import (GC_SECTIONS, NATIVE_HEADERS, extended_envelope,
    extended_native_interpreter, header_entry, instrument, read_audio_donor, resource, span)

SOURCES=('tools/v3_sound_programs.py','tools/v3_villager_audio.py')


def single_layer(sequence, origin, limit):
    """Parse a complete explicit-bank, one-note channel with custom ADSR."""
    if not 0 <= origin < limit <= len(sequence):raise ValueError('Invalid sound program span')
    data=span(sequence,origin,limit-origin)
    if len(data)<15 or data[0]!=0xEB or data[1]>3 or data[2]>125 or data[3]!=0x88 or data[6]!=0xFF:
        raise ValueError('Unsupported single-layer sound channel')
    layer=struct.unpack_from('>H',data,4)[0]-origin
    if layer!=7 or data[layer]!=0xCB:raise ValueError('Incomplete sound layer or envelope command')
    envelope=struct.unpack_from('>H',data,layer+1)[0]-origin
    if (origin+envelope)&1:raise ValueError('Unaligned sound envelope')
    decay=data[layer+3];at=layer+4;sweep=None
    if data[at]==0xC7:
        mode,target,time=span(data,at+1,3)
        # The special sweep form has a one-byte time. Its mode/target/time
        # stay intact, rather than turning a pitch sweep into a fixed note.
        if not mode&128 or not 1<=mode&127<=5 or target>127 or not time:
            raise ValueError('Unsupported sound pitch sweep')
        sweep=dict(mode=mode,target=target,time=time);at+=4
    note=span(data,at,1)[0];at+=1
    if not 0x40<=note<=0x7F:raise ValueError('Unsupported sound note form')
    duration=span(data,at,1)[0];at+=1
    if duration&128:
        duration=(duration&127)*256+span(data,at,1)[0];at+=1
    velocity=span(data,at,1)[0];at+=1
    if not duration or velocity>127 or span(data,at,1)!=b'\xff':
        raise ValueError('Invalid single-note sound event')
    at+=1
    if not at<=envelope< len(data) or any(data[at:envelope]):
        raise ValueError('Unaccounted sound layer bytes')
    env=extended_envelope(data,envelope);end=envelope+len(env)
    if len(data)-end>15 or any(data[end:]):raise ValueError('Unaccounted sound program tail')
    return dict(origin=origin,bytes=len(data),sha256=sha256(data),selector=data[1],instrument=data[2],
        pointers=[4,layer+1],layer=layer,envelope=envelope,envelope_bytes=len(env),decay=decay,
        note=note&63,duration=duration,velocity=velocity,sweep=sweep)


def bind_program(data,description,offset,instrument_index):
    origin=description['origin']
    if (single_layer(bytes(origin)+data,origin,origin+len(data))!=description
            or not 0<=offset<=65536-len(data) or (offset-origin)&1
            or not 0<=instrument_index<=125):
        raise ValueError('Sound program binding exceeds its verified structure')
    result=bytearray(data);result[2]=instrument_index
    for at in description['pointers']:
        pointer=struct.unpack_from('>H',data,at)[0]
        struct.pack_into('>H',result,at,offset+pointer-origin)
    single_layer(bytes(offset)+result,offset,offset+len(result))
    return bytes(result)


def installed_resource(image,code,kind,index):
    files=by_vrom(image)
    read=lambda at,n:span(code,at-CODE_RAM,n)
    entry=header_entry(read,NATIVE_HEADERS[kind],index)
    if entry[8]!=2:raise ValueError('Sound requires ROM-backed audio')
    offset,n=struct.unpack_from('>2I',entry)
    physical=(files[NATIVE_VROMS[kind]].pstart+offset)&0xFFFFFFFF
    if (not n or physical+n>len(image) or not any(e.pstart!=0xFFFFFFFF and not e.pend
            and e.pstart<=physical<=e.pstart+e.size-n for e in files.values())):
        raise ValueError('Installed sound resource escapes its complete ROM owner')
    return image[physical:physical+n],entry,physical


def permanent_budget(code):
    read=lambda at,n:span(code,at-CODE_RAM,n)
    total,fixed,capacity=struct.unpack('>3I',read(0x80119A44,12))
    if (total,fixed,capacity)!=(0x47E00,0x1DC00,0x1AC00):
        raise ValueError('Changed current audio allocation contract')
    for at,want in ((0x800D28D8,0x34847E00),(0x800D28F8,0x34A57E00)):
        if u32(code,at-CODE_RAM)!=want:raise ValueError('Audio heap arguments disagree with capacity')
    rows=[]
    for kind,base in NATIVE_HEADERS.items():
        count=struct.unpack('>H',read(base,2))[0]
        for index in range(count):
            entry=header_entry(read,base,index);n=u32(entry,4)
            if n and entry[9]==0:
                if entry[8]!=2:raise ValueError('Unsupported permanent sound medium')
                rows.append(dict(kind=kind,index=index,bytes=n,conservative_allocation=(n+31)&-32))
    required=sum(r['conservative_allocation'] for r in rows)
    if required>capacity:raise ValueError('Sound sequence exceeds current permanent audio capacity')
    return dict(capacity=capacity,conservative_required=required,conservative_spare=capacity-required,
        all_permanent_resources=rows,heap_changed=False)


def install(image,prior,blob,code,source_ids):
    """Register a batch in vacant group-one slots without copying instruments."""
    if not source_ids or len(set(source_ids))!=len(source_ids):raise ValueError('Empty or duplicate sound batch')
    read=lambda at,n:span(code,at-CODE_RAM,n)
    interpreter=extended_native_interpreter(read)
    for opcode,handler in ((0xC7,0x800F3994),(0xCB,0x800F3A34)):
        if u32(read(0x801184B8+(opcode-0xC1)*4,4),0)!=handler:
            raise ValueError('Changed native sound sweep/envelope handler')
    dol,audio=read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    donor={k:span(audio,*struct.unpack_from('>II',header_entry(dol.read,0x800CE450,i)))
           for i,k in enumerate(('seq','bank','wave'))}
    source,_=resource(dol.read,GC_SECTIONS,donor,'seq',242)
    if sha256(source)!='790526e46582305f94eb05851337ccab5b8aa248c451e98f99f2d65965ab2a22':
        raise ValueError('Changed complete donor sound sequence')
    sequence,entry,physical=installed_resource(image,code,'seq',199)
    installed=prior.get('equipment_resources',{}).get('sound_programs')
    current=installed['sequence'] if installed else prior['fire_sound']['resources']['seq']
    if (sha256(sequence)!=current['sha256'] or physical!=current['physical']
            or entry.hex()!=current['header_after']):raise ValueError('Changed current sound sequence')
    table=struct.unpack_from('>H',sequence,0x18A)[0]
    count=prior['speed_bag_sound']['sequence_group_one_count']
    if count!=106 or table!=0x4C30:raise ValueError('Changed complete native sound group-one table')
    donor_table=struct.unpack_from('>H',source,0x18A)[0]
    if donor_table!=0x294:raise ValueError('Changed donor group-one table')
    starts={struct.unpack_from('>H',source,donor_table+i*2)[0] for i in range(128)}
    result=bytearray(sequence);rows=[];before=permanent_budget(code)
    for sid in sorted(source_ids):
        index=sid&255
        if sid>>8!=1 or not 97<=index<count:raise ValueError('Sound needs a supported vacant group-one slot')
        old_pointer=struct.unpack_from('>H',result,table+index*2)[0]
        if span(result,old_pointer,1)!=b'\xff':raise ValueError('Sound slot already contains a program')
        origin=struct.unpack_from('>H',source,donor_table+index*2)[0]
        ends=[at for at in starts if at>origin]
        if not ends:raise ValueError('Sound program lacks a complete donor boundary')
        limit=min(ends)
        desc=single_layer(source,origin,limit);program=source[origin:limit]
        source_map=struct.unpack('>H',dol.read(0x800CE490+242*2,2))[0]
        native_map=struct.unpack('>H',read(0x80115D80+199*2,2))[0]
        source_banks=dol.read(0x800CE490+source_map,5);native_banks=read(0x80115D80+native_map,5)
        if source_banks[0]!=4 or native_banks[0]!=4:raise ValueError('Changed sequence sound-font mapping')
        sb=source_banks[4-desc['selector']];nb=native_banks[4-desc['selector']]
        donor_bank,db=resource(dol.read,GC_SECTIONS,donor,'bank',sb)
        native_bank,nbe,_=installed_resource(image,code,'bank',nb)
        if db[11]!=255 or nbe[11]!=255:raise ValueError('Multiple-wavebank sound instrument needs another category')
        donor_wave,_=resource(dol.read,GC_SECTIONS,donor,'wave',db[10])
        native_wave,_,_=installed_resource(image,code,'wave',nbe[10])
        identity=instrument(donor_bank,donor_wave,desc['instrument'],db[12],extended=True)
        matches=[i for i in range(nbe[12]) if instrument(native_bank,native_wave,i,nbe[12],extended=True)==identity]
        if not matches:raise ValueError('Sound requires an uninstalled instrument/sample dependency')
        ni=desc['instrument'] if desc['instrument'] in matches else matches[0]
        source_priority=dol.read(0x800A9A90+index,1)
        if read(0x80113B84+index,1)!=source_priority:raise ValueError('Sound slot changes source trigger priority')
        result.extend(bytes((len(result)^origin)&1));offset=len(result)
        bound=bind_program(program,desc,offset,ni);result.extend(bound)
        struct.pack_into('>H',result,table+index*2,offset)
        rows.append(dict(source_sound_id=sid,native_sound_id=sid,source_program=desc,
            source_bank=sb,native_bank=nb,native_instrument=ni,instrument_identity=identity,
            offset=offset,bytes=len(bound),sha256=sha256(bound),trigger_priority=source_priority[0],
            original_table_pointer=old_pointer,new_instrument=False,new_sample=False))
    result.extend(bytes(-len(result)%16))
    blob.extend(bytes(-len(blob)%16));position=len(blob);blob.extend(result)
    files=by_vrom(image);new_physical=files[BLOB].pstart+position
    new_entry=bytearray(entry)
    struct.pack_into('>2I',new_entry,0,new_physical-files[NATIVE_VROMS['seq']].pstart,len(result))
    address=NATIVE_HEADERS['seq']+16+199*16
    code[address-CODE_RAM:address-CODE_RAM+16]=new_entry
    after=permanent_budget(code)
    return dict(format='AFV3-SHARED-SOUND-PROGRAMS-1',imports=rows,interpreter=interpreter,
        sequence=dict(index=199,blob_offset=position,physical=new_physical,vrom=BLOB+position,
            bytes=len(result),sha256=sha256(result),header_address=address,
            header_before=entry.hex(),header_after=new_entry.hex(),retained_bytes=len(sequence)),
        previous_sequence=copy.deepcopy(current),before_budget=before,after_budget=after,
        sound_resources_installed=True,native_synthesis_tested=False,physical_audio_played=False)
