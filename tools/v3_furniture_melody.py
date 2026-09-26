"""Extend complete town-tune instrument tables and their font/sample resources."""
import copy
import json
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from v3_asset_loader import ROOT, BLOB
from v3_villager_audio import (GC_SECTIONS,NATIVE_HEADERS,header_entry,resource,span,
    read_audio_donor,extended_native_interpreter,extended_program,instrument)

NATIVE_SEQUENCE_SHA='d6ebf23d2ca69d15bd9f33733801c5963bb48422d79263f05d7641bbb65b86c0'
SOURCE_SEQUENCE_SHA='d307f4a001f6a88cb108164ab177faaf436e346f6ed6b6040839fe9a47541adc'
NATIVE_TABLES=(0x3A0E,0x3A2C,0x3A4A)
SOURCE_TABLES=(0x3A20,0x3A40,0x3A60)
TABLE_OPERANDS={0x3965:0,0x3982:2,0x39A9:1,0x39D2:1}
SOURCES=('tools/v3_furniture_melody.py',)


def melody_program(sequence, pointers, end):
    """Retain the complete header, all nineteen notes, and channel controls."""
    first,second,table=pointers
    if (second!=first+1 or table!=first+3 or
            not 0<=first<table<end<=len(sequence) or sequence[first]>127):
        raise ValueError('Unsupported complete town-melody header')
    offsets=struct.unpack('>19H',span(sequence,table,38))
    if offsets[0]!=table+38 or tuple(sorted(set(offsets)))!=offsets or offsets[-1]>=end:
        raise ValueError('Incomplete town-melody note table')
    tracks=[]
    for i,at in enumerate(offsets):
        limit=offsets[i+1] if i<18 else end
        data=span(sequence,at,limit-at)
        program=extended_program(data,selector=0)
        if program['bytes']!=len(data):raise ValueError('Unaccounted town-melody track bytes')
        program['normalized']=program['normalized'].hex()
        tracks.append(dict(offset=at-first,sha256=sha256(data),**program))
    return dict(origin=first,bytes=end-first,sha256=sha256(sequence[first:end]),
        header_hex=sequence[first:table].hex(),table_offset=table-first,tracks=tracks)


def bind_program(sequence,description,offset,mapping):
    origin=description['origin'];n=description['bytes'];raw=bytearray(span(sequence,origin,n))
    if melody_program(sequence,(origin,origin+1,origin+3),origin+n)!=description:
        raise ValueError('Changed complete melody program')
    if not 0<=offset<=65536-n:raise ValueError('Town-melody program exceeds 16-bit pointers')
    for i,track in enumerate(description['tracks']):
        at=track['offset'];instrument_id=track['instrument']
        if track['instruments']!=[instrument_id] or instrument_id not in mapping:
            raise ValueError('Town melody needs a complete multi-instrument adapter')
        struct.pack_into('>H',raw,description['table_offset']+i*2,offset+at)
        raw[at+2]=mapping[instrument_id]
    rebound=melody_program(bytes(offset)+raw,(offset,offset+1,offset+3),offset+n)
    for old,new in zip(description['tracks'],rebound['tracks'],strict=True):
        if any(old[key]!=new[key] for key in ('normalized','channel_controls','bytes','note_offset')):
            raise ValueError('Rebinding changes complete melody commands')
        events=copy.deepcopy(old['events'])
        for event in events:
            if 'instrument' in event:event['instrument']=mapping[event['instrument']]
        if events!=new['events']:raise ValueError('Rebinding changes town-melody notes or timing')
    return bytes(raw)


def prepare(image,report):
    from v3_sound_programs import installed_resource,extend_instruments
    if sha256(image)!=report['output_sha256']:
        raise ValueError('Town melody requires the checked current cartridge')
    if report['equipment_resources'].get('furniture_melody_audio'):
        raise ValueError('Complete town-melody extension is already installed')
    code=by_vrom(image)[CODE_VROM].extract(image)
    interpreter=extended_native_interpreter(lambda at,n:span(code,at-CODE_RAM,n))
    native,seq_header,_=installed_resource(image,code,'seq',203)
    dol,audio=read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    donor={k:span(audio,*struct.unpack_from('>II',header_entry(dol.read,0x800CE450,i)))
           for i,k in enumerate(('seq','bank','wave'))}
    source,_=resource(dol.read,GC_SECTIONS,donor,'seq',246)
    if sha256(native)!=NATIVE_SEQUENCE_SHA or sha256(source)!=SOURCE_SEQUENCE_SHA:
        raise ValueError('Changed complete native/source town-melody sequence')
    gm=struct.unpack('>H',dol.read(0x800CE490+246*2,2))[0]
    nm=struct.unpack_from('>H',code,0x80115D80-CODE_RAM+203*2)[0]
    if dol.read(0x800CE490+gm,3)!=b'\x02\x02\x00' or span(code,0x80115D80-CODE_RAM+nm,3)!=b'\x02\x02\x00':
        raise ValueError('Changed native/source melody font mapping')
    # The source adds one entry to each of the three instrument tables. Keep
    # every native entry and add the complete source program, not a sound alias.
    descriptions=[]
    for index in range(15,16):
        pointers=tuple(struct.unpack_from('>H',source,at+index*2)[0] for at in SOURCE_TABLES)
        description=melody_program(source,pointers,0x4B55)
        descriptions.append(dict(index=index,**description))
    source_bank,bh=resource(dol.read,GC_SECTIONS,donor,'bank',0)
    source_wave,_=resource(dol.read,GC_SECTIONS,donor,'wave',bh[10])
    bank,nh,_=installed_resource(image,code,'bank',0)
    wave,wh,_=installed_resource(image,code,'wave',nh[10])
    if bh[10:14]!=bytes((0,255,72,0)) or nh[10:14]!=bytes((0,255,71,0)):
        raise ValueError('Changed complete town-melody font category')
    instruments=sorted({i for d in descriptions for t in d['tracks'] for i in t['instruments']})
    font,waves,layout=extend_instruments(bank,wave,nh[12],[dict(bank_id=0,
        instrument=i,instrument_count=bh[12],bank=source_bank,wave=source_wave)
        for i in instruments],minimum_envelope_steps=1)
    mapping={row['source_instrument']:row['native_instrument'] for row in layout['imports']}
    result=bytearray(native);tables=[]
    for at in NATIVE_TABLES:
        offset=len(result);result.extend(span(native,at,30)+bytes(2))
        tables.append(dict(previous_offset=at,offset=offset,previous_count=15,count=16))
    programs=[]
    for description in descriptions:
        result.extend(bytes(len(result)&1));at=len(result)
        source_description={k:v for k,v in description.items() if k!='index'}
        data=bind_program(source,source_description,at,mapping);result.extend(data)
        for table,delta in zip(tables,(0,1,3),strict=True):
            struct.pack_into('>H',result,table['offset']+description['index']*2,at+delta)
        programs.append(dict(index=description['index'],offset=at,bytes=len(data),sha256=sha256(data),
            source=source_description))
    for operand,index in TABLE_OPERANDS.items():
        if result[operand-1]!=0xB2 or struct.unpack_from('>H',result,operand)[0]!=NATIVE_TABLES[index]:
            raise ValueError('Changed complete native melody table consumer')
        struct.pack_into('>H',result,operand,tables[index]['offset'])
    result.extend(bytes(-len(result)%16))
    metadata=dict(format='AFV3-FURNITURE-MELODY-PREPARED-1',base_sha256=sha256(image),
        source_sequence_sha256=sha256(source),native_sequence_sha256=sha256(native),
        interpreter=interpreter,tables=tables,table_operands={str(k):v for k,v in TABLE_OPERANDS.items()},
        programs=programs,layout=layout,installed_instruments=list(range(16)),
        previous=dict(sequence_header=seq_header.hex(),font_header=nh.hex(),wave_header=wh.hex(),
            font_sha256=sha256(bank),wave_sha256=sha256(wave)),runtime_installed=False)
    return dict(sequence=bytes(result),font=font,wave=waves),metadata


def prepare_batch(image,report,source,inventory,output,selected):
    from apply_translation import write_new
    resources,result=prepare(image,report)
    members=[]
    for row in inventory['rows']:
        if row['item_id'] not in selected:continue
        profile=row['profile'];adapter=profile['callback_adapter']
        if (not row['asset_ready'] or adapter['category']!='static-interaction' or adapter['mode']!=2 or
                adapter['parameter'] not in result['installed_instruments']):
            raise ValueError('Unsupported complete furniture melody selection')
        members.append(dict(item_id=row['item_id'],name=row['name'],profile_sha256=profile['profile_sha256'],callback=adapter))
    if {r['item_id'] for r in members}!=set(selected) or not members:
        raise ValueError('Missing or empty complete melody selection')
    result.update(furniture=members,source_rel_sha256=sha256(source.rel),
        source_symbols_sha256=sha256(source.symbols.encode()))
    result['files']={name+'.bin':dict(bytes=len(data),sha256=sha256(data)) for name,data in resources.items()}
    output.mkdir(parents=True,exist_ok=False)
    for name,data in resources.items():write_new(output/(name+'.bin'),data)
    write_new(output/'audio.json',(json.dumps(result,indent=2)+'\n').encode())
    return result


def install(image,prior,blob,code,directory,prepared):
    from v3_sound_programs import (installed_resource,audio_archive,permanent_budget,grow_permanent_heap)
    from v3_furniture_pipeline import Source
    from v3_resource_capacity import checked_limit
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    if (not directory.is_relative_to(ROOT/'build') or
            prepared['source_rel_sha256']!=sha256(source.rel) or
            prepared['source_symbols_sha256']!=sha256(source.symbols.encode())):
        raise ValueError('Changed prepared furniture-melody source')
    for row in prepared['furniture']:
        profile=source.profile(int(row['item_id'],16))
        if (row['profile_sha256']!=profile['profile_sha256'] or
                row['callback']!=json.loads(json.dumps(profile['callback_adapter']))):
            raise ValueError('Changed complete furniture-melody callback')
    resources,expected=prepare(image,prior)
    if any(prepared[k]!=json.loads(json.dumps(v)) for k,v in expected.items()):
        raise ValueError('Changed complete prepared town-melody dependency')
    if prepared['files']!={k+'.bin':dict(bytes=len(v),sha256=sha256(v)) for k,v in resources.items()}:
        raise ValueError('Incomplete prepared melody files')
    for name,data in resources.items():
        if (directory/(name+'.bin')).read_bytes()!=data:raise ValueError('Changed prepared melody resource')
    result=copy.deepcopy(prior['equipment_resources']);before=permanent_budget(code)
    records={};physical_base=by_vrom(image)[BLOB].pstart
    for label,kind,index in (('sequence','seq',203),('font','bank',0),('wave','wave',0)):
        old,header,_=installed_resource(image,code,kind,index)
        data=resources[label];blob.extend(bytes(-len(blob)%16));at=len(blob);blob.extend(data)
        if BLOB+len(blob)>checked_limit(image,prior):raise ValueError('Complete melody resources exceed import reservation')
        physical=physical_base+at;archive=audio_archive(image,code,kind)
        new=bytearray(header);struct.pack_into('>2I',new,0,(physical-archive.pstart)&0xFFFFFFFF,len(data))
        if kind=='bank':new[12]=expected['layout']['instrument_count']
        address=NATIVE_HEADERS[kind]+16+index*16;code[address-CODE_RAM:address-CODE_RAM+16]=new
        records[label]=dict(index=index,blob_offset=at,physical=physical,vrom=BLOB+at,bytes=len(data),
            sha256=sha256(data),header_address=address,header_before=header.hex(),header_after=new.hex(),previous_sha256=sha256(old))
    growth,patches=grow_permanent_heap(code);after=permanent_budget(code)
    result['furniture_melody_audio']=dict(format='AFV3-FURNITURE-MELODY-AUDIO-1',
        furniture=prepared['furniture'],programs=expected['programs'],tables=expected['tables'],
        table_operands=expected['table_operands'],layout=expected['layout'],**records,
        installed_instruments=expected['installed_instruments'],source_sequence_sha256=SOURCE_SEQUENCE_SHA,
        native_sequence_sha256=NATIVE_SEQUENCE_SHA,interpreter=expected['interpreter'],
        before_budget=before,after_budget=after,audio_heap_growth=growth,heap_patches=patches,
        runtime_installed=True,native_synthesis_tested=False,physical_audio_played=False)
    # The samples are streamed from a complete external resource. Neither the
    # shared wave archive nor its native base-load instructions move.
    for key in ('sound_programs','furniture_audio','furniture_level_audio'):
        if key in result:result[key]['after_budget']=copy.deepcopy(after)
    fire=copy.deepcopy(prior['fire_sound'])
    header=next(r for r in fire['wave_headers'] if r['index']==0)
    header.update(before=header['after'],after=records['wave']['header_after'],
        physical_before=header['physical'],physical=records['wave']['physical'],
        bytes=records['wave']['bytes'],external_resource_retained=True)
    fire.update(after_budget=copy.deepcopy(after),
        heap_settings=list(struct.unpack_from('>3I',code,0x80119A44-CODE_RAM)))
    return result,{},dict(fire_sound=fire)


def rebind_wave_header(equipment,code):
    """Keep external melody samples bound when the shared archive moves later."""
    audio=equipment.get('furniture_melody_audio')
    if audio is None:return
    record=audio['wave'];address=NATIVE_HEADERS['wave']+16
    header=span(code,address-CODE_RAM,16)
    hi,lo=struct.unpack('>2I',span(code,0x800D28DC-CODE_RAM,8))
    if hi&0xFFFF0000!=0x3C0E0000 or lo&0xFFFF0000!=0x25CE0000:
        raise ValueError('Changed native wave base instructions')
    base=((hi&65535)<<16)+(lo&65535)-(65536 if lo&32768 else 0)
    offset,size=struct.unpack_from('>2I',header)
    if ((base+offset)&0xFFFFFFFF)!=record['physical'] or size!=record['bytes'] or header[8:]!=bytes.fromhex(record['header_after'])[8:]:
        raise ValueError('External town-melody samples moved or changed unexpectedly')
    if header.hex()!=record['header_after']:
        record.update(header_before=record['header_after'],header_after=header.hex())


def checked_binding(image,report):
    from v3_sound_programs import installed_resource
    audio=report['equipment_resources'].get('furniture_melody_audio')
    if audio is None:return None
    code=by_vrom(image)[CODE_VROM].extract(image);resources={}
    for name,kind,index in (('sequence','seq',203),('font','bank',0),('wave','wave',0)):
        data,header,physical=installed_resource(image,code,kind,index);record=audio[name]
        if (sha256(data)!=record['sha256'] or len(data)!=record['bytes'] or physical!=record['physical'] or
                header.hex()!=record['header_after']):
            raise ValueError('Changed complete installed town-melody resource')
        resources[name]=data
    sequence=resources['sequence'];restored=bytearray(sequence[:21664])
    for operand,index in TABLE_OPERANDS.items():
        table=audio['tables'][index]
        if (struct.unpack_from('>H',sequence,operand)[0]!=table['offset'] or
                span(sequence,table['offset'],30)!=span(sequence,NATIVE_TABLES[index],30)):
            raise ValueError('Town-melody extension changes an existing instrument')
        struct.pack_into('>H',restored,operand,NATIVE_TABLES[index])
    if sha256(restored)!=NATIVE_SEQUENCE_SHA:raise ValueError('Changed original town-melody sequence')
    for row in audio['programs']:
        if sha256(span(sequence,row['offset'],row['bytes']))!=row['sha256']:
            raise ValueError('Changed installed complete melody program')
        for table,delta in zip(audio['tables'],(0,1,3),strict=True):
            if struct.unpack_from('>H',sequence,table['offset']+row['index']*2)[0]!=row['offset']+delta:
                raise ValueError('Changed complete melody program table binding')
    for row in audio['layout']['imports']:
        identity=instrument(resources['font'],resources['wave'],row['native_instrument'],
            audio['layout']['instrument_count'],extended=True,minimum_envelope_steps=1)
        if identity!=row['identity']:raise ValueError('Changed imported complete melody instrument')
    if extended_native_interpreter(lambda at,n:span(code,at-CODE_RAM,n))!=audio['interpreter']:
        raise ValueError('Changed complete melody interpreter')
    return audio
