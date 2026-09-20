"""Shared single-layer sound imports using verified existing native instruments.

Preserve the complete channel, note, pitch sweep, envelope, and padding. Only
internal pointers and equivalent instrument bindings change. Unsupported forms
fail; callers supply source sound IDs, not per-item audio implementations.
"""
import copy
import json
import struct

from aflib import CODE_RAM, by_vrom, sha256, u32
from v3_asset_loader import BLOB, ROOT
from v3_fire_audio import NATIVE_VROMS
from v3_villager_audio import (GC_SECTIONS, NATIVE_HEADERS, extended_envelope,
    extended_native_interpreter, header_entry, instrument, read_audio_donor, resource, span)
from v3_room_rig_runtime import SOURCES as ROOM_SOURCES

SOURCES=('tools/v3_sound_programs.py','tools/v3_villager_audio.py','tools/v3_furniture_install.py')+ROOM_SOURCES


def trigger_program(sequence, origin, limit):
    """Complete explicit-font trigger with timed notes and optional envelope.

    This category includes repeated notes, not only the one-note form. Unknown
    commands, unreachable bytes, incomplete dependencies, and zero times fail.
    """
    data=span(sequence,origin,limit-origin)
    if (not 0<=origin<limit<=min(len(sequence),65536) or len(data)<11 or
            data[0]!=0xEB or data[1]>3 or data[2]>125 or data[3]!=0x88 or
            struct.unpack_from('>H',data,4)[0]!=origin+7 or data[6]!=255):
        raise ValueError('Unsupported complete trigger channel')
    at=7;pointers=[4];envelope=None;decay=None;events=[]
    if data[at]==0xCB:
        envelope=struct.unpack('>H',span(data,at+1,2))[0]-origin
        decay=span(data,at+3,1)[0];pointers.append(at+1);at+=4
        if (origin+envelope)&1:raise ValueError('Unaligned trigger envelope')
    while at<len(data) and data[at]!=255:
        start=at;op=data[at];at+=1
        if not 0x40<=op<=0x7F:raise ValueError('Unsupported trigger note command')
        duration=span(data,at,1)[0];at+=1
        if duration&128:duration=(duration&127)*256+span(data,at,1)[0];at+=1
        velocity=span(data,at,1)[0];at+=1
        if not duration or velocity>127:raise ValueError('Invalid trigger duration or velocity')
        events.append(dict(offset=start,note=op&63,duration=duration,velocity=velocity))
    if not events or span(data,at,1)!=b'\xFF':raise ValueError('Unterminated trigger layer')
    at+=1;envelope_bytes=0
    if envelope is not None:
        if not at<=envelope<len(data) or any(data[at:envelope]):
            raise ValueError('Unaccounted trigger layer bytes')
        envelope_bytes=len(extended_envelope(data,envelope));at=envelope+envelope_bytes
    if len(data)-at>15 or any(data[at:]):raise ValueError('Unaccounted complete trigger tail')
    return dict(origin=origin,bytes=len(data),sha256=sha256(data),selector=data[1],instrument=data[2],
        pointers=pointers,envelope=envelope,envelope_bytes=envelope_bytes,decay=decay,events=events,
        duration=sum(e['duration'] for e in events))


def bind_trigger(data,description,offset,selector,instrument_index):
    origin=description['origin']
    if (trigger_program(bytes(origin)+data,origin,origin+len(data))!=description or
            not 0<=offset<=65536-len(data) or not 0<=selector<=3 or
            not 0<=instrument_index<=125 or description['envelope'] is not None and (offset-origin)&1):
        raise ValueError('Trigger binding exceeds its complete checked structure')
    result=bytearray(data);result[1:3]=bytes((selector,instrument_index))
    for at in description['pointers']:
        struct.pack_into('>H',result,at,offset+struct.unpack_from('>H',data,at)[0]-origin)
    trigger_program(bytes(offset)+result,offset,offset+len(result))
    return bytes(result)


def extend_instruments(native_bank,native_wave,native_count,donors):
    """Grow a complete instrument-only font once for a batch of source records.

    The pointer table grows independently of existing data placement. Every live
    bank pointer moves together; wave offsets and tuning words do not. Identical
    instruments and complete subordinate resources are reused across the batch.
    """
    if not donors or not 0<native_count<=126 or native_bank[:8]!=bytes(8):
        raise ValueError('Expected a nonempty instrument-only font batch')
    identities={};before={}
    for index in range(native_count):
        if not u32(native_bank,8+4*index):continue
        identity=instrument(native_bank,native_wave,index,native_count,extended=True)
        before[index]=identity;identities.setdefault(json.dumps(identity,sort_keys=True),index)
    ordered=sorted(donors,key=lambda d:(d['bank_id'],d['instrument']))
    keys=[(d['bank_id'],d['instrument']) for d in ordered]
    if len(set(keys))!=len(keys):raise ValueError('Duplicate source instrument identity')
    mappings=[];missing=[];count=native_count
    for row in ordered:
        identity=instrument(row['bank'],row['wave'],row['instrument'],row['instrument_count'],extended=True)
        key=json.dumps(identity,sort_keys=True);target=identities.get(key)
        if target is None:
            if count>=126:raise ValueError('Complete font exceeds native instrument capacity')
            target=count;count+=1;identities[key]=target;missing.append((row,target,identity))
        mappings.append(dict(source_bank=row['bank_id'],source_instrument=row['instrument'],
            native_instrument=target,identity=identity,reused=target<native_count))
    first=(8+native_count*4+15)&~15;new_first=(8+count*4+15)&~15;shift=new_first-first
    if first>len(native_bank) or any(native_bank[8+native_count*4:first]):
        raise ValueError('Instrument table overlaps nonempty original data')
    result=bytearray(native_bank[:first]+bytes(shift)+native_bank[first:]);waves=bytearray(native_wave)
    pointers={};cache={};wave_cache={}
    def pointer(at):
        target=u32(native_bank,at)
        if target:
            if target<first or target>=len(native_bank) or target&3:
                raise ValueError('Native font dependency overlaps its pointer table or escapes data')
            pointers[at]=target
        return target
    for index in before:
        at=pointer(8+index*4);envelope=pointer(at+4)
        cache.setdefault(('envelope',extended_envelope(native_bank,envelope)),envelope+shift)
        for field in (8,16,24):
            sample=pointer(at+field)
            if not sample:continue
            loop=pointer(sample+8);book=pointer(sample+12)
            loop_data=span(native_bank,loop,48 if u32(native_bank,loop+8) else 16)
            order,n=struct.unpack('>2I',span(native_bank,book,8));book_data=span(native_bank,book,8+16*order*n)
            cache.setdefault(('loop',loop_data),loop+shift);cache.setdefault(('book',book_data),book+shift)
            wave=span(native_wave,u32(native_bank,sample+4),u32(native_bank,sample))
            wave_cache.setdefault(wave,u32(native_bank,sample+4))
    for at,target in pointers.items():
        struct.pack_into('>I',result,at+(shift if at>=first else 0),target+shift)
    def append(data,kind):
        key=kind,bytes(data)
        if key not in cache:
            result.extend(bytes(-len(result)%16));cache[key]=len(result);result.extend(data)
        return cache[key]
    for row,target,identity in missing:
        bank,wave=row['bank'],row['wave'];original=span(bank,u32(bank,8+row['instrument']*4),32)
        inst=bytearray(original)
        struct.pack_into('>I',inst,4,append(extended_envelope(bank,u32(inst,4)),'envelope'))
        for field in (8,16,24):
            at=u32(original,field)
            if not at:continue
            sample=bytearray(span(bank,at,16));length,start,loop,book=struct.unpack('>4I',sample)
            full_wave=span(wave,start,length)
            if full_wave not in wave_cache:
                waves.extend(bytes(-len(waves)%16));wave_cache[full_wave]=len(waves);waves.extend(full_wave)
            loop_data=span(bank,loop,48 if u32(bank,loop+8) else 16)
            order,n=struct.unpack('>2I',span(bank,book,8))
            struct.pack_into('>3I',sample,4,wave_cache[full_wave],append(loop_data,'loop'),
                             append(span(bank,book,8+16*order*n),'book'))
            struct.pack_into('>I',inst,field,append(sample,'sample'))
        struct.pack_into('>I',result,8+target*4,append(inst,'instrument'))
    result.extend(bytes(-len(result)%16));waves.extend(bytes(-len(waves)%16))
    for index in range(native_count):
        if index in before:
            if instrument(result,waves,index,count,extended=True)!=before[index]:
                raise ValueError('Font extension changes an existing complete instrument')
        elif u32(result,8+index*4):raise ValueError('Font extension populates an original empty slot')
    for row in mappings:
        if instrument(result,waves,row['native_instrument'],count,extended=True)!=row['identity']:
            raise ValueError('Font extension changes a complete donor instrument')
    return bytes(result),bytes(waves),dict(native_instrument_count=native_count,instrument_count=count,
        original_data_start=first,original_data_shift=shift,imports=mappings,
        font_growth_bytes=len(result)-len(native_bank),wave_growth_bytes=len(waves)-len(native_wave))


def prepare_triggers(image,report,sound_words):
    """Prepare one complete font/wave expansion plus source-derived trigger programs.

    No sound IDs, headers, allocations, or cartridge bytes are installed here.
    Native dispatch and priority bindings remain mandatory integration work.
    """
    from aflib import CODE_VROM
    if sha256(image)!=report['output_sha256'] or not sound_words:
        raise ValueError('Trigger preparation requires the checked current cartridge')
    if any(type(v) is not int or not 0<=v<=65535 for v in sound_words):
        raise ValueError('Invalid full source trigger word')
    code=by_vrom(image)[CODE_VROM].extract(image)
    interpreter=extended_native_interpreter(lambda at,n:span(code,at-CODE_RAM,n))
    dol,audio=read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    donor={k:span(audio,*struct.unpack_from('>II',header_entry(dol.read,0x800CE450,i)))
           for i,k in enumerate(('seq','bank','wave'))}
    source,_=resource(dol.read,GC_SECTIONS,donor,'seq',242)
    if sha256(source)!='790526e46582305f94eb05851337ccab5b8aa248c451e98f99f2d65965ab2a22':
        raise ValueError('Changed complete donor trigger sequence')
    source_map=struct.unpack('>H',dol.read(0x800CE490+242*2,2))[0]
    source_banks=dol.read(0x800CE490+source_map,5)
    native_map=struct.unpack_from('>H',code,0x80115D80-CODE_RAM+199*2)[0]
    native_banks=span(code,0x80115D80-CODE_RAM+native_map,5)
    if source_banks!=bytes((4,2,155,154,153)) or native_banks!=bytes((4,2,141,140,139)):
        raise ValueError('Changed trigger font selection')
    tables={1:(0x294,128),4:(0x394,107)};starts=set()
    for group,(at,count) in tables.items():
        if struct.unpack_from('>H',source,0x188+group*2)[0]!=at:
            raise ValueError('Changed complete source trigger table')
        starts.update(struct.unpack_from('>'+str(count)+'H',source,at))
    donors={};programs=[]
    for word in sorted(set(sound_words)):
        sid=word&0x7FFF;group,index=sid>>8,sid&255
        if group not in tables or index>=tables[group][1]:raise ValueError('Unsupported source trigger group/index')
        table,_=tables[group];origin=struct.unpack_from('>H',source,table+index*2)[0]
        ends=[at for at in starts if at>origin]
        if not ends:raise ValueError('Trigger lacks a complete source program boundary')
        limit=min(ends);description=trigger_program(source,origin,limit)
        sb=source_banks[4-description['selector']];key=sb,description['instrument']
        if key not in donors:
            bank,header=resource(dol.read,GC_SECTIONS,donor,'bank',sb)
            if header[11]!=255 or header[13]:raise ValueError('Unsupported trigger font dependencies')
            wave,_=resource(dol.read,GC_SECTIONS,donor,'wave',header[10])
            donors[key]=dict(bank_id=sb,instrument=description['instrument'],instrument_count=header[12],bank=bank,wave=wave)
        programs.append(dict(sound_word=word,source_sound_id=sid,singleton=bool(word&0x8000),
            source_bank=sb,source_program=description,source_data=source[origin:limit]))
    bank,bank_header,bank_physical=installed_resource(image,code,'bank',native_banks[3])
    if bank_header[11]!=255 or bank_header[13]:raise ValueError('Target is not an instrument-only font')
    wave,wave_header,wave_physical=installed_resource(image,code,'wave',bank_header[10])
    font,waves,layout=extend_instruments(bank,wave,bank_header[12],list(donors.values()))
    targets={(r['source_bank'],r['source_instrument']):r['native_instrument'] for r in layout['imports']}
    fragments={}
    for row in programs:
        desc=row['source_program'];target=targets[row['source_bank'],desc['instrument']]
        offset=desc['origin']&1 if desc['envelope'] is not None else 0
        data=bind_trigger(row.pop('source_data'),desc,offset,1,target)
        filename=f"trigger-{row['sound_word']:04X}.bin";fragments[filename]=data
        row.update(native_selector=1,native_instrument=target,fragment_file=filename,
            fragment_origin=offset,bytes=len(data),sha256=sha256(data),dispatch_binding_required=True)
    budget=permanent_budget(code)
    font_allocation=((len(font)+31)&~31)-((len(bank)+31)&~31)
    return dict(font=font,wave=waves,fragments=fragments),dict(format='AFV3-TRIGGER-AUDIO-PREPARED-1',
        base_sha256=sha256(image),source_sequence_sha256=sha256(source),native_interpreter=interpreter,
        font_index=native_banks[3],wave_index=bank_header[10],layout=layout,programs=programs,
        previous=dict(font_sha256=sha256(bank),wave_sha256=sha256(wave),font_header=bank_header.hex(),
            wave_header=wave_header.hex(),font_physical=bank_physical,wave_physical=wave_physical),
        permanent_audio_before=budget,additional_font_allocation=font_allocation,
        additional_capacity_for_font_only=max(0,font_allocation-budget['conservative_spare']),
        sequence_growth_not_included=True,runtime_installed=False,
        dispatch_and_priority_installed=False,allocation_installed=False,callback_installed=False,
        native_synthesis_tested=False,physical_audio_played=False)


def furniture_trigger(source,profile):
    """Recognize move-only triggers with ordinary or complete custom drawing."""
    adapter=profile.get('callback_adapter',{})
    functions=adapter.get('functions',{})
    if adapter.get('category')=='switch-trigger-sound':
        if set(functions)!={'move'}:raise ValueError('Changed ordinary trigger lifecycle')
        # Source.profile already verifies and annotates this direct callback.
        return {k:copy.deepcopy(adapter[k]) for k in ('helpers','sound_word','excluded_states',
            'state_offset','switch_offset','switch_value','position_offset','runtime_installed')}
    elif adapter.get('category')=='material-frame-assets':
        if set(functions)!={'move','draw'}:return None
    else:return None
    # Callback validation annotates its receipt. Keep prepared graphics
    # descriptors unchanged when another subsystem inspects their behaviour.
    return source.switch_sound_callback(copy.deepcopy(functions['move']))


def prepare_furniture_audio(image,report,source,inventory,output,selected=(),category=None):
    """Select a shared furniture behaviour once and prepare all its audio dependencies."""
    from apply_translation import write_new
    installed={r['item_id'] for r in report['equipment_resources'].get('furniture_audio',{}).get('furniture',[])}
    rows=[];triggers={}
    for r in inventory['rows']:
        if (r['installed'] or r['item_id'] in installed or not r.get('asset_ready') or
                selected and r['item_id'] not in selected or category is not None and category not in r['categories']):continue
        trigger=furniture_trigger(source,r.get('profile',{}))
        if trigger is not None:rows.append(r);triggers[r['item_id']]=trigger
    if not rows or selected and set(selected)!={r['item_id'] for r in rows}:
        raise ValueError('Unsupported or empty furniture audio selection')
    resources,result=prepare_triggers(image,report,[triggers[r['item_id']]['sound_word'] for r in rows])
    result['furniture']=[dict(item_id=r['item_id'],name=r['name'],
        profile_sha256=r['profile']['profile_sha256'],callback=r['profile']['callback_adapter'],
        trigger=triggers[r['item_id']]) for r in rows]
    result['source_rel_sha256']=sha256(source.rel)
    result['source_symbols_sha256']=sha256(source.symbols.encode())
    result['sources']={p:sha256((ROOT/p).read_bytes()) for p in SOURCES+('tools/v3_furniture_pipeline.py',)}
    output.mkdir(parents=True,exist_ok=False)
    files={'font.bin':resources['font'],'wave.bin':resources['wave'],**resources['fragments']}
    result['files']={name:dict(bytes=len(data),sha256=sha256(data)) for name,data in files.items()}
    for name,data in files.items():write_new(output/name,data)
    write_new(output/'audio.json',(json.dumps(result,indent=2)+'\n').encode())
    return result


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


def permanent_budget(code,*,require_fit=True):
    read=lambda at,n:span(code,at-CODE_RAM,n)
    total,fixed,capacity=struct.unpack('>3I',read(0x80119A44,12))
    growth=total-0x47E00
    if (not 0<=growth<0x8200 or growth%0x400 or
            (fixed,capacity)!=(0x1DC00+growth,0x1AC00+growth)):
        raise ValueError('Changed current audio allocation contract')
    for at,want in ((0x800D28CC,0x3C040004),(0x800D28E4,0x3C050004),
                    (0x800D28D8,0x34840000|(total&65535)),(0x800D28F8,0x34A50000|(total&65535))):
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
    if require_fit and required>capacity:raise ValueError('Sound sequence exceeds current permanent audio capacity')
    return dict(capacity=capacity,conservative_required=required,conservative_spare=capacity-required,
        all_permanent_resources=rows,heap_changed=bool(growth))


def grow_permanent_heap(code):
    """Grow only the fixed/permanent allocation, preserving all session pools."""
    before=permanent_budget(code,require_fit=False)
    growth=(max(0,-before['conservative_spare'])+0x3FF)&~0x3FF
    if not growth:return 0,[]
    settings=struct.unpack_from('>3I',code,0x80119A44-CODE_RAM)
    after=tuple(n+growth for n in settings)
    if after[0]>=0x50000:raise ValueError('Audio allocation exceeds reviewed malloc instruction range')
    patches=[]
    for at,data in ((0x80119A44,struct.pack('>3I',*after)),
                    (0x800D28D8,struct.pack('>I',0x34840000|(after[0]&65535))),
                    (0x800D28F8,struct.pack('>I',0x34A50000|(after[0]&65535)))):
        old=bytes(code[at-CODE_RAM:at-CODE_RAM+len(data)])
        code[at-CODE_RAM:at-CODE_RAM+len(data)]=data
        patches.append(dict(address=at,before=old.hex(),after=data.hex()))
    permanent_budget(code)
    return growth,patches


def register_triggers(sequence,programs,fragments,counts,native_priority,source_priority,*,previous=None):
    """Extend whole dispatch tables while preserving shared cross-group priorities."""
    if (len(native_priority)!=128 or len(source_priority)!=128 or set(counts)!={1,4} or
            any(type(n) is not int or not 0<n<=128 for n in counts.values())):
        raise ValueError('Unsupported complete trigger dispatch contract')
    result=bytearray(sequence);tables={};rows=[];used=set();retained={}
    if previous is not None:
        retained={r['source_sound_word']:r for r in previous['programs']}
        if len(retained)!=len(previous['programs']):raise ValueError('Duplicate retained source trigger')
        tables={r['group']:copy.deepcopy(r) for r in previous['tables']}
        if set(tables)!=set(counts) or len(tables)!=len(previous['tables']):raise ValueError('Incomplete retained trigger tables')
        for group,count in sorted(counts.items()):
            table=tables[group]
            if (table['count']!=128 or table['previous_count']!=count or
                    struct.unpack_from('>H',sequence,0x188+group*2)[0]!=table['offset']):
                raise ValueError('Changed retained trigger table binding')
            original=list(struct.unpack('>'+str(count)+'H',span(sequence,table['previous_offset'],count*2)))
            if any(p>=len(sequence) for p in original) or sequence[original[0]]!=255:
                raise ValueError('Changed original trigger pointers or terminator')
            expected=original+[original[0]]*(128-count)
            for row in retained.values():
                word=row['native_sound_word'];g,index=(word&0x7FFF)>>8,word&255
                if g!=group:continue
                if (not count<=index<128 or (g,index) in used or
                        native_priority[index]!=row['trigger_priority'] or
                        (word&0x8000)!=(row['source_sound_word']&0x8000) or
                        sha256(span(sequence,row['offset'],row['bytes']))!=row['sha256']):
                    raise ValueError('Changed retained complete trigger or native identity')
                used.add((g,index));expected[index]=row['offset']
            if span(sequence,table['offset'],256)!=struct.pack('>128H',*expected):
                raise ValueError('Occupied or changed retained trigger dispatch slot')
        if len(used)!=len(retained):raise ValueError('Retained trigger has unsupported native group')
    for group,count in sorted(counts.items()):
        if not 0<count<=128:raise ValueError('Invalid native trigger table count')
        if previous is not None:continue
        old=struct.unpack_from('>H',sequence,0x188+group*2)[0]
        pointers=list(struct.unpack('>'+str(count)+'H',span(sequence,old,count*2)))
        if any(p>=len(sequence) for p in pointers) or sequence[pointers[0]]!=255:
            raise ValueError('Changed native trigger terminator or program bounds')
        pointers.extend([pointers[0]]*(128-count))
        result.extend(bytes(len(result)&1));at=len(result)
        result.extend(struct.pack('>128H',*pointers))
        struct.pack_into('>H',result,0x188+group*2,at)
        tables[group]=dict(group=group,previous_offset=old,previous_count=count,offset=at,count=128)
    for row in sorted(programs,key=lambda r:r['sound_word']):
        source_word=row['sound_word'];sid=source_word&0x7FFF;group,index=sid>>8,sid&255
        if group not in counts or index>=128 or source_word in used:
            raise ValueError('Unsupported or duplicate trigger identity')
        used.add(source_word);priority=source_priority[index];count=counts[group]
        raw=fragments[row['fragment_file']];origin=row['fragment_origin']
        if len(raw)!=row['bytes'] or sha256(raw)!=row['sha256']:raise ValueError('Changed complete prepared trigger')
        desc=trigger_program(bytes(origin)+raw,origin,origin+len(raw))
        if source_word in retained:
            old=retained[source_word]
            bound=bind_trigger(raw,desc,old['offset'],row['native_selector'],row['native_instrument'])
            if (old['source_program']!=row['source_program'] or old['trigger_priority']!=priority or
                    old['native_instrument']!=row['native_instrument'] or
                    span(sequence,old['offset'],old['bytes'])!=bound):
                raise ValueError('Reused trigger differs from complete current source')
            rows.append(copy.deepcopy(old));continue
        available=[i for i in range(count,128) if native_priority[i]==priority and (group,i) not in used]
        if not available:raise ValueError('No vacant native trigger with matching source priority')
        target=index if index in available else available[0];used.add((group,target))
        native_word=(source_word&0x8000)|(group<<8)|target
        result.extend(bytes((len(result)^origin)&1));at=len(result)
        bound=bind_trigger(raw,desc,at,row['native_selector'],row['native_instrument']);result.extend(bound)
        struct.pack_into('>H',result,tables[group]['offset']+target*2,at)
        rows.append(dict(source_sound_word=source_word,native_sound_word=native_word,
            source_sound_id=sid,native_sound_id=native_word&0x7FFF,trigger_priority=priority,
            singleton=bool(source_word&0x8000),offset=at,bytes=len(bound),sha256=sha256(bound),
            source_program=row['source_program'],native_bank=140,native_instrument=row['native_instrument']))
    result.extend(bytes(-len(result)%16))
    if len(result)>65536:raise ValueError('Complete trigger sequence exceeds native pointer capacity')
    return bytes(result),rows,list(tables.values())


def install_furniture(image,prior,blob,code,original,output,directory):
    """Install the complete prepared sound category and its shared room callback."""
    from aflib import CODE_VROM
    from v3_furniture_install import append_resource_plan,relocate_resource_plan
    from v3_furniture_pipeline import Source
    from v3_registry import furniture_representation_identity
    import v3_room_rig_runtime as room
    directory=directory.resolve();raw=(directory/'audio.json').read_bytes();prepared=json.loads(raw)
    if (not directory.is_relative_to(ROOT/'build') or prepared['format']!='AFV3-TRIGGER-AUDIO-PREPARED-1'
            or prepared['base_sha256']!=sha256(image)):
        raise ValueError('Furniture audio needs its checked current base')
    previous=prior['equipment_resources'].get('furniture_audio')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    if (prepared['source_rel_sha256']!=sha256(source.rel) or
            prepared['source_symbols_sha256']!=sha256(source.symbols.encode())):
        raise ValueError('Changed furniture source resources')
    furniture=prepared['furniture'];seen={int(r['item_id'],16) for r in previous['furniture']} if previous else set()
    triggers={}
    for row in furniture:
        item=int(row['item_id'],16);profile=source.profile(item)
        if (item in seen or row['profile_sha256']!=profile['profile_sha256'] or
                row['callback']!=json.loads(json.dumps(profile.get('callback_adapter',{})))):
            raise ValueError('Changed complete furniture sound callback')
        trigger=furniture_trigger(source,profile)
        if trigger is None or row.get('trigger',json.loads(json.dumps(trigger)))!=json.loads(json.dumps(trigger)):
            raise ValueError('Changed shared furniture trigger behaviour')
        seen.add(item);triggers[row['item_id']]=trigger
    resources,audio=prepare_triggers(image,prior,[r['sound_word'] for r in triggers.values()])
    for key in ('programs','layout','previous','font_index','wave_index','source_sequence_sha256'):
        if json.loads(json.dumps(audio[key]))!=prepared[key]:raise ValueError('Changed complete prepared audio identity')
    all_data={'font.bin':resources['font'],'wave.bin':resources['wave'],**resources['fragments']}
    if set(prepared['files'])!=set(all_data):raise ValueError('Incomplete prepared audio files')
    for name,data in all_data.items():
        if ((directory/name).read_bytes()!=data or
                prepared['files'][name]!=dict(bytes=len(data),sha256=sha256(data))):
            raise ValueError('Changed complete prepared sound dependency')
    files=by_vrom(image);native=by_vrom(original)[CODE_VROM].extract(original)
    contracts=[]
    for first,last in ((0x800D1D58,0x800D1D94),(0x800FA354,0x800FA498),(0x800F6BF8,0x800F6FCC)):
        old=span(native,first-CODE_RAM,last-first)
        if span(code,first-CODE_RAM,last-first)!=old:raise ValueError('Changed native positioned-trigger dispatcher')
        contracts.append(dict(address=first,bytes=last-first,sha256=sha256(old)))
    sequence,entry,physical=installed_resource(image,code,'seq',199)
    old_sequence=prior['equipment_resources']['sound_programs']['sequence']
    if (sha256(sequence)!=old_sequence['sha256'] or physical!=old_sequence['physical'] or
            entry.hex()!=old_sequence['header_after'] or
            struct.unpack_from('>H',sequence,0x192)[0]!=0x3DA or
            previous is None and (struct.unpack_from('>H',sequence,0x18A)[0]!=0x4C30 or
                struct.unpack_from('>H',sequence,0x190)[0]!=0x33E or
                prior['speed_bag_sound']['sequence_group_one_count']!=106)):
        raise ValueError('Changed complete current trigger tables')
    dol,_=read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    priority=span(code,0x80113B84-CODE_RAM,128)
    if previous:
        for key,kind,index in (('font','bank',audio['font_index']),('wave','wave',audio['wave_index']),('sequence','seq',199)):
            data,header,physical=installed_resource(image,code,kind,index);record=previous[key]
            if (record['sha256']!=sha256(data) or record['header_after']!=header.hex() or
                    record['physical']!=physical):raise ValueError('Changed retained complete furniture audio resource')
        if (sha256(priority)!=previous['priority_table_sha256'] or prior['speed_bag_sound']['sequence_group_one_count']!=128 or
                previous['format']!='AFV3-FURNITURE-TRIGGER-AUDIO-1'):
            raise ValueError('Changed retained furniture audio dispatch contract')
    new_sequence,programs,tables=register_triggers(sequence,audio['programs'],resources['fragments'],
        {r['group']:r['previous_count'] for r in previous['tables']} if previous else {1:106,4:78},
        priority,dol.read(0x800A9A90,128),previous=previous)
    before_budget=permanent_budget(code)
    def store(kind,index,data,*,count=None):
        old,header,_=installed_resource(image,code,kind,index)
        blob.extend(bytes(-len(blob)%16));at=len(blob);blob.extend(data)
        physical=files[BLOB].pstart+at;new_header=bytearray(header)
        struct.pack_into('>2I',new_header,0,(physical-files[NATIVE_VROMS[kind]].pstart)&0xFFFFFFFF,len(data))
        if count is not None:new_header[12]=count
        address=NATIVE_HEADERS[kind]+16+index*16
        code[address-CODE_RAM:address-CODE_RAM+16]=new_header
        return dict(index=index,blob_offset=at,physical=physical,vrom=BLOB+at,bytes=len(data),
            sha256=sha256(data),header_address=address,header_before=header.hex(),header_after=new_header.hex(),
            previous_sha256=sha256(old))
    seq=store('seq',199,new_sequence)
    bank=store('bank',audio['font_index'],resources['font'],count=audio['layout']['instrument_count'])
    wave,header,physical=installed_resource(image,code,'wave',audio['wave_index'])
    wave_owner=files[NATIVE_VROMS['wave']];old_waves=wave_owner.extract(image)
    if (physical+len(wave)!=wave_owner.pstart+len(old_waves) or
            resources['wave'][:len(wave)]!=wave or sha256(old_waves)!=prior['fire_sound']['wave_file']['sha256']):
        raise ValueError('Wave append changes a current complete resource')
    new_waves=old_waves+resources['wave'][len(wave):]
    relocatable={r['vrom']:r['output_sha256'] for r in prior['equipment_resources']['wrapped_presents']['consumers']}
    relocatable.update({r['vrom']:r['sha256'] for r in prior['equipment_resources']['player_actions']['balloon_menu']['owner_resizes']})
    # Later batches may reach complete scenery owners already moved behind
    # the wave archive. Their loaders use logical VROM/relocation identities,
    # not physical cartridge positions. Accept only installed owner receipts;
    # the shared append planner verifies their complete bytes before moving.
    scenery=prior['equipment_resources'].get('scenery',{})
    for category in ('daily_growth','field_insects'):
        owner=scenery.get(category)
        if owner:
            relocatable.update({owner['vrom']:owner['sha256'],owner['reloc']:owner['reloc_sha256']})
    if new_waves==old_waves:changes,growth={},None
    else:
        try:changes,growth=append_resource_plan(image,files,NATIVE_VROMS['wave'],new_waves,relocatable)
        except ValueError as error:
            changes,growth=relocate_resource_plan(image,files,NATIVE_VROMS['wave'],new_waves,
                minimum_physical=0x3000000)
            growth['in_place_rejection']=str(error)
    wave_base=growth['physical'] if growth else wave_owner.pstart
    # The native initializer uses unsigned ADDU to turn header offsets into
    # physical addresses. Moving the complete wave archive must also retain
    # external waveform resources and change the actual base-load instructions.
    if span(code,0x800EA944-CODE_RAM,12)!=bytes.fromhex('8CD800100305C821ACD90010'):
        raise ValueError('Changed unsigned native audio header initialization')
    old_load=struct.pack('>2I',0x3C0E0000|((wave_owner.pstart+0x8000)>>16),0x25CE0000|(wave_owner.pstart&65535))
    new_load=struct.pack('>2I',0x3C0E0000|((wave_base+0x8000)>>16),0x25CE0000|(wave_base&65535))
    if span(code,0x800D28DC-CODE_RAM,8)!=old_load:raise ValueError('Changed native wave archive base')
    code[0x800D28DC-CODE_RAM:0x800D28DC-CODE_RAM+8]=new_load
    header_count=struct.unpack_from('>H',code,NATIVE_HEADERS['wave']-CODE_RAM)[0]
    if header_count!=6:raise ValueError('Changed native wave resource count')
    wave_headers=[]
    for index in range(header_count):
        address=NATIVE_HEADERS['wave']+16+index*16
        before=bytes(code[address-CODE_RAM:address-CODE_RAM+16]);offset,length=struct.unpack_from('>2I',before)
        if not length or before[8:10]!=bytes((2,4)):raise ValueError('Changed native streamed-wave contract')
        outside=not 0<=offset<=len(old_waves)-length
        old_physical=(wave_owner.pstart+offset)&0xFFFFFFFF
        if outside:
            data,_,actual=installed_resource(image,code,'wave',index)
            if actual!=old_physical or index==audio['wave_index']:raise ValueError('Invalid external wave binding')
            new_physical=old_physical
        else:new_physical=wave_base+offset
        size=len(resources['wave']) if index==audio['wave_index'] else length
        after=bytearray(before);struct.pack_into('>2I',after,0,(new_physical-wave_base)&0xFFFFFFFF,size)
        code[address-CODE_RAM:address-CODE_RAM+16]=after
        wave_headers.append(dict(index=index,address=address,before=before.hex(),after=after.hex(),
            physical_before=old_physical,physical=new_physical,bytes=size,external_resource_retained=outside))
    selected=wave_headers[audio['wave_index']]
    wave_record=dict(index=audio['wave_index'],physical=selected['physical'],
        vrom=wave_owner.vstart+physical-wave_owner.pstart,bytes=len(resources['wave']),
        sha256=sha256(resources['wave']),header_address=selected['address'],header_before=header.hex(),header_after=selected['after'])
    heap_growth,patches=grow_permanent_heap(code)
    result=copy.deepcopy(prior['equipment_resources']);runtime=result['room_rigs']
    packet=runtime['packet'];at=packet['blob_offset']
    packet_data=blob[at:at+packet['bytes']]
    if (sha256(packet_data)!=packet['sha256'] or packet_data[4096:]!=room.encode_packet(
            runtime['rows'],runtime.get('sound_rows',[]),runtime.get('material_rows',[]))):
        raise ValueError('Changed complete shared room packet')
    old_sound_rows=runtime.get('sound_rows',[])
    expected_members={r['item_id'] for r in previous['furniture']} if previous else set()
    if {r['source_item_id'] for r in old_sound_rows}!=expected_members:
        raise ValueError('Changed retained furniture sound membership')
    mapping={r['source_sound_word']:r for r in programs};sound_rows=[]
    for row in furniture:
        index,destination=furniture_representation_identity(int(row['item_id'],16))
        sound_rows.append(dict(source_item_id=row['item_id'],item_id=f'{destination:04X}',runtime_index=index,
            source_sound_word=triggers[row['item_id']]['sound_word'],
            native_sound_word=mapping[triggers[row['item_id']]['sound_word']]['native_sound_word'],
            profile_installed=False,parent_selectable=False))
        if row['callback']['category']=='material-frame-assets':
            material=next((r for r in runtime.get('material_rows',[]) if r['source_item_id']==row['item_id']),None)
            if (material is None or material['source']['profile']!=json.loads(json.dumps(source.profile(int(row['item_id'],16)))) or
                    sha256(blob[material['blob_offset']:material['blob_offset']+material['bytes']])!=material['sha256']):
                raise ValueError('Trigger lifecycle requires its complete installed material renderer/assets')
            material.update(lifecycle_installed=True,move_category='switch-trigger-sound')
    runtime['sound_rows']=sorted(old_sound_rows+sound_rows,key=lambda r:r['runtime_index'])
    room.publish_packet(result,blob,output)
    shared=result['sound_programs'];shared['previous_sequence']=copy.deepcopy(old_sequence);shared['sequence']=seq
    shared.setdefault('trigger_batches',[]).append(dict(programs=programs,tables=tables))
    shared.update(after_budget=permanent_budget(code),native_synthesis_tested=False)
    result['furniture_audio']=dict(format='AFV3-FURNITURE-TRIGGER-AUDIO-1',prepared_sha256=sha256(raw),
        furniture=sorted((previous['furniture'] if previous else [])+furniture,key=lambda r:r['item_id']),
        programs=sorted({r['source_sound_word']:r for r in (previous['programs'] if previous else [])+programs}.values(),
            key=lambda r:r['source_sound_word']),tables=tables,layout=audio['layout'],
        sequence=seq,font=bank,wave=wave_record,native_dispatch=contracts,
        singleton_guard=dict(callback=True,native_dispatcher_supports_flag=False,slots=6,ram=0x80113C34,stride=32),
        priority_table_sha256=sha256(priority),before_budget=before_budget,after_budget=permanent_budget(code),
        audio_heap_growth=heap_growth,heap_patches=patches,resource_growth=growth,
        runtime_installed=True,dispatch_and_priority_installed=True,allocation_installed=True,callback_installed=True,
        profiles_installed=False,ordinary_acquisition_tested=False,native_synthesis_tested=False,physical_audio_played=False)
    result['furniture_audio']['batches']=(copy.deepcopy(previous.get('batches',[])) if previous else [])+[
        dict(prepared_sha256=sha256(raw),source_items=[r['item_id'] for r in furniture],
             programs=programs,heap_growth=heap_growth,resource_growth=growth)]
    fire=copy.deepcopy(prior['fire_sound'])
    fire['resources'].update(seq=seq,bank=bank,wave=wave_record)
    fire['wave_file'].update(physical=wave_base,bytes=len(new_waves),sha256=sha256(new_waves))
    if wave_base!=wave_owner.pstart:
        fire['wave_file'].update(old_physical=wave_owner.pstart,retains_old_allocation=True)
    fire['wave_headers']=wave_headers
    fire['heap_settings']=list(struct.unpack_from('>3I',code,0x80119A44-CODE_RAM))
    fire['after_budget']=permanent_budget(code)
    speed=copy.deepcopy(prior['speed_bag_sound']);speed['sequence_group_one_count']=128
    return result,changes,dict(fire_sound=fire,speed_bag_sound=speed,resource_growth=[growth] if growth else [])


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
