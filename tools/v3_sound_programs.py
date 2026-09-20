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


def shared_font_samples(donor_bank,native_bank,donor_wave,native_wave,metadata):
    """Compare complete native font data after resolving every sample address."""
    if metadata[3]!=255 or metadata[6:]!=bytes(2) or len(donor_bank) not in (len(native_bank),len(native_bank)+16):
        raise ValueError('Unsupported shared fanfare font layout')
    instruments,drums=metadata[4:6];samples=set();envelopes=set()
    def pointer(at,size):
        value=u32(native_bank,at)
        if value:
            span(native_bank,value,size)
            if value&3:raise ValueError('Unaligned shared font pointer')
        return value
    for i in range(instruments):
        at=pointer(8+i*4,32)
        if at:
            envelopes.add(pointer(at+4,4))
            samples.update(p for j in (8,16,24) if (p:=pointer(at+j,16)))
    drum_table=pointer(0,drums*4) if drums else 0
    if bool(drums)!=bool(drum_table):raise ValueError('Missing shared drum table')
    for i in range(drums):
        at=pointer(drum_table+i*4,16)
        if at:
            samples.add(pointer(at+4,16));envelopes.add(pointer(at+12,4))
    if not samples or 0 in samples or 0 in envelopes:raise ValueError('Missing shared font dependencies')
    # The complete native font must match the donor prefix, including its
    # envelopes, tuning, loops, predictors, instrument ranges, and drum rows.
    # Only wave offsets may differ; compare the entire addressed samples.
    normalized=bytearray(donor_bank[:len(native_bank)]);rows=[]
    for at in sorted(samples):
        flags,native_offset,loop,book=struct.unpack('>4I',span(native_bank,at,16))
        if not 0<flags<0x1000000 or not loop or not book:
            raise ValueError('Unsupported shared waveform')
        loops=u32(span(native_bank,loop,16),8);span(native_bank,loop,48 if loops else 16)
        order,count=struct.unpack('>2I',span(native_bank,book,8))
        if not 1<=order<=2 or not 1<=count<=16:raise ValueError('Unbounded shared ADPCM predictor')
        span(native_bank,book,8+16*order*count)
        donor_offset=u32(donor_bank,at+4)
        a,b=span(donor_wave,donor_offset,flags),span(native_wave,native_offset,flags)
        if a!=b:raise ValueError('Shared fanfare sample differs')
        struct.pack_into('>I',normalized,at+4,native_offset)
        rows.append(dict(header_offset=at,source_offset=donor_offset,native_offset=native_offset,
                         bytes=flags,sha256=sha256(a)))
    if normalized!=native_bank:raise ValueError('Shared fanfare font differs beyond sample addresses')
    return dict(source_bytes=len(donor_bank),native_bytes=len(native_bank),
        source_sha256=sha256(donor_bank),native_sha256=sha256(native_bank),
        source_trailing_hex=donor_bank[len(native_bank):].hex(),samples=rows,
        instrument_count=instruments,drum_count=drums,envelope_offsets=sorted(envelopes))


def reward_fanfares(image,code,source):
    """Retain existing native reward fanfares with source/native asset bindings."""
    raw,selector=source.function(0x16F878)
    if (len(raw)!=68 or sha256(raw)!='07a6b4d855a833c30e50d586a162884365c2256d9626caa7966aaec9eaad2fab'
            or selector['symbol']!='Player_actor_sound_Get_bgm_num_forDemoGetGoldenItem'):
        raise ValueError('Changed complete reward fanfare selector')
    ordered=[w&65535 for w in struct.unpack('>17I',raw) if w>>16==0x3860]
    if ordered!=[73,75,76,74]:raise ValueError('Changed reward fanfare order')
    dol,audio=read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    donor={k:span(audio,*struct.unpack_from('>II',header_entry(dol.read,0x800CE450,i)))
           for i,k in enumerate(('seq','bank','wave'))}
    read=lambda at,n:span(code,at-CODE_RAM,n)
    source_table=dol.read(0x800A9838,256);native_table=read(0x80113964,256)
    if (sha256(source_table)!='3627168080c7151cc4a4bd5d021735e17a591168a85dab4abfd9af16b833f0df'
            or sha256(native_table)!='d0ded694c8643bc28abf25d7cc743ce84ea73d022d8af60d08f8aae0033e5e53'):
        raise ValueError('Changed complete BGM selector table')
    rows=[]
    for bgm in ordered:
        gi,ni=source_table[bgm],native_table[bgm]
        g,gh=resource(dol.read,GC_SECTIONS,donor,'seq',gi)
        n,nh,physical=installed_resource(image,code,'seq',ni)
        if len(g) not in (len(n),len(n)+16) or g[:len(n)]!=n:
            raise ValueError('Native fanfare is not the complete common sequence')
        def bank_id(reader,base,index):
            offset=struct.unpack('>H',reader(base+index*2,2))[0];data=reader(base+offset,2)
            if data[0]!=1:raise ValueError('Unreviewed multi-font fanfare')
            return data[1]
        gb,nb=bank_id(dol.read,0x800CE490,gi),bank_id(read,0x80115D80,ni)
        gbank,gbh=resource(dol.read,GC_SECTIONS,donor,'bank',gb)
        nbank,nbh,_=installed_resource(image,code,'bank',nb)
        if gbh[8:]!=nbh[8:]:raise ValueError('Shared fanfare font metadata differs')
        gwave,_=resource(dol.read,GC_SECTIONS,donor,'wave',gbh[10])
        nwave,_,_=installed_resource(image,code,'wave',nbh[10])
        font=shared_font_samples(gbank,nbank,gwave,nwave,nbh[8:])
        rows.append(dict(bgm=bgm,source_sequence=gi,native_sequence=ni,source_bytes=len(g),native_bytes=len(n),
            source_sha256=sha256(g),native_sha256=sha256(n),source_trailing_hex=g[len(n):].hex(),
            native_physical=physical,source_bank=gb,native_bank=nb,font=font))
    return dict(selector=selector,type_bgms=ordered,rows=rows,source_table=0x800A9838,native_table=0x80113964,
        source_table_sha256=sha256(source_table),native_table_sha256=sha256(native_table),
        new_sequences=0,new_instruments=0,new_samples=0,native_resources_retained=True)


def looping_layer(data, origin, *, prefix=False):
    """Complete single-layer sustained note, custom envelope, and timed loop."""
    start=4 if prefix else 0
    span(data,0,start+11)
    if not 0<=origin<=65536-len(data):raise ValueError('Loop exceeds sequence address space')
    if prefix and (span(data,0,1)!=b'\xEB' or data[1]>3 or data[2]>125 or data[3]!=0xC4):
        raise ValueError('Unsupported explicit loop bank')
    if (span(data,start,1)!=b'\x88' or span(data,start+3,2)!=b'\xFF\xC6'
            or struct.unpack_from('>H',data,start+1)[0]!=origin+start+4):
        raise ValueError('Incomplete single-layer loop channel')
    instrument_index=span(data,start+5,1)[0]
    if instrument_index>125 or span(data,start+6,1)!=b'\xCB':
        raise ValueError('Unsupported loop instrument/envelope')
    envelope=struct.unpack('>H',span(data,start+7,2))[0]-origin
    decay=span(data,start+9,1)[0];at=start+10;mode=at
    if span(data,at,1)!=b'\xC4':raise ValueError('Missing sustained-note mode')
    note=span(data,at+1,1)[0];at+=2
    if not 0x40<=note<=0x7F:raise ValueError('Unsupported loop note')
    duration=span(data,at,1)[0];at+=1
    if duration&128:duration=(duration&127)*256+span(data,at,1)[0];at+=1
    velocity=span(data,at,1)[0];at+=1
    loop=struct.unpack('>H',span(data,at+1,2))[0]-origin
    if (not duration or velocity>127 or span(data,at,1)!=b'\xFB'
            or loop not in (mode,mode+1)):
        raise ValueError('Loop target or timed event is incomplete')
    pointers=[start+1,start+7,at+1];at+=3
    if (origin+envelope)&1 or not at<=envelope<len(data) or any(data[at:envelope]):
        raise ValueError('Loop envelope alignment or padding changed')
    env=extended_envelope(data,envelope,minimum_steps=1);end=envelope+len(env)
    if len(data)-end>15 or any(data[end:]):raise ValueError('Unaccounted loop tail')
    return dict(origin=origin,bytes=len(data),sha256=sha256(data),instrument=instrument_index,
        pointers=pointers,instrument_offset=start+5,envelope=envelope,envelope_bytes=len(env),
        decay=decay,note=note&63,duration=duration,velocity=velocity,loop=loop)


def bind_loop(data,description,offset,instrument_index,selector=0):
    if (looping_layer(data,description['origin'])!=description or offset&1
            or not 0<=offset<=65536-len(data)-4 or not 0<=instrument_index<=125
            or not 0<=selector<=3):raise ValueError('Loop binding exceeds checked structure')
    output=bytearray(bytes((0xEB,selector,instrument_index,0xC4))+data)
    for at in description['pointers']:
        pointer=struct.unpack_from('>H',data,at)[0]
        struct.pack_into('>H',output,at+4,offset+4+pointer-description['origin'])
    output[description['instrument_offset']+4]=instrument_index
    looping_layer(output,offset,prefix=True)
    return bytes(output)


def install_level(image,prior,blob,code,source_ids):
    """Extend the existing shared level dispatcher with equivalent native fonts."""
    if not source_ids or len(set(source_ids))!=len(source_ids):raise ValueError('Empty or duplicate level sound batch')
    read=lambda at,n:span(code,at-CODE_RAM,n)
    interpreter=extended_native_interpreter(read)
    dol,audio=read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    donor={k:span(audio,*struct.unpack_from('>II',header_entry(dol.read,0x800CE450,i)))
           for i,k in enumerate(('seq','bank','wave'))}
    source,_=resource(dol.read,GC_SECTIONS,donor,'seq',242)
    if sha256(source)!='790526e46582305f94eb05851337ccab5b8aa248c451e98f99f2d65965ab2a22':
        raise ValueError('Changed complete donor level sequence')
    installed=prior['equipment_resources']['sound_programs'];current=installed['sequence']
    sequence,entry,physical=installed_resource(image,code,'seq',199)
    table=struct.unpack_from('>H',sequence,0x179)[0]
    if (sha256(sequence)!=current['sha256'] or physical!=current['physical']
            or entry.hex()!=current['header_after'] or table!=0x4D20
            or sequence[0x178]!=0xC2):raise ValueError('Changed shared level sound dispatch')
    starts=struct.unpack_from('>128H',source,0x2E02)
    source_map=struct.unpack('>H',dol.read(0x800CE490+242*2,2))[0]
    native_map=struct.unpack('>H',read(0x80115D80+199*2,2))[0]
    source_banks=dol.read(0x800CE490+source_map,5);native_banks=read(0x80115D80+native_map,5)
    if source_banks!=bytes((4,2,155,154,153)) or native_banks!=bytes((4,2,141,140,139)):
        raise ValueError('Changed default level sound banks')
    sb,nb=source_banks[-1],native_banks[-1]
    donor_bank,db=resource(dol.read,GC_SECTIONS,donor,'bank',sb)
    native_bank,nbe,_=installed_resource(image,code,'bank',nb)
    if db[11]!=255 or nbe[11]!=255:raise ValueError('Unsupported multi-wave level font')
    donor_wave,_=resource(dol.read,GC_SECTIONS,donor,'wave',db[10])
    native_wave,_,_=installed_resource(image,code,'wave',nbe[10])
    result=bytearray(sequence);rows=copy.deepcopy(installed['imports']);before=permanent_budget(code)
    for sid in sorted(source_ids):
        if not 68<=sid<128:raise ValueError('Level sound must use an added slot')
        old_pointer=struct.unpack_from('>H',sequence,table+sid*2)[0]
        if span(sequence,old_pointer,1)!=b'\xFF':raise ValueError('Level sound slot is occupied')
        origin=starts[sid];limit=min(p for p in starts if p>origin)
        data=span(source,origin,limit-origin);description=looping_layer(data,origin)
        identity=instrument(donor_bank,donor_wave,description['instrument'],db[12],extended=True)
        matches=[i for i in range(nbe[12]) if instrument(native_bank,native_wave,i,nbe[12],extended=True)==identity]
        if not matches:raise ValueError('Level sound lacks its complete native instrument')
        target=description['instrument'] if description['instrument'] in matches else matches[0]
        result.extend(bytes(len(result)&1));at=len(result);bound=bind_loop(data,description,at,target)
        result.extend(bound);struct.pack_into('>H',result,table+sid*2,at)
        rows.append(dict(kind='level',source_sound_id=sid,native_sound_id=sid,source_program=description,
            source_bank=sb,native_bank=nb,native_instrument=target,instrument_identity=identity,
            offset=at,bytes=len(bound),sha256=sha256(bound),source_table=0x2E02,native_table=table,
            original_table_pointer=old_pointer,new_instrument=False,new_sample=False))
    result.extend(bytes(-len(result)%16));blob.extend(bytes(-len(blob)%16));position=len(blob);blob.extend(result)
    new_physical=by_vrom(image)[BLOB].pstart+position;new_entry=bytearray(entry)
    struct.pack_into('>2I',new_entry,0,new_physical-by_vrom(image)[NATIVE_VROMS['seq']].pstart,len(result))
    address=NATIVE_HEADERS['seq']+16+199*16;code[address-CODE_RAM:address-CODE_RAM+16]=new_entry
    return dict(format='AFV3-SHARED-SOUND-PROGRAMS-1',imports=rows,interpreter=interpreter,
        sequence=dict(index=199,blob_offset=position,physical=new_physical,vrom=BLOB+position,
            bytes=len(result),sha256=sha256(result),header_address=address,header_before=entry.hex(),
            header_after=new_entry.hex(),retained_bytes=len(sequence)),previous_sequence=copy.deepcopy(current),
        before_budget=before,after_budget=permanent_budget(code),sound_resources_installed=True,
        native_synthesis_tested=False,physical_audio_played=False)


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
