"""Source-bound shared furniture movement sounds and native owner integration."""
import copy
import json
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from v3_asset_loader import ROOT,BLOB

TABLE,MAGIC,CAPACITY=0x804BBF20,0x41464D56,8
BRIDGE=0x804B1E50
OWNER,RELOC,RAM,FIRST,LAST,CALL=0x82D7F0,0x844400,0x80936710,0x8093EA60,0x8093EAD0,0x8093EAB8
NATIVE_SHA='671025d62868445852763f2098f5371f9a6cf5cbf67725aced53ac26cf8179c4'
SOURCES=('tools/v3_room_movement.py','tools/v3_sound_programs.py','tools/v3_furniture_scroll.py',
    'tools/v3_furniture_contact.py','tools/v3_room_rig_runtime.py','tools/v3_furniture_install.py',
    'overlays/v3/room_scroll.c','overlays/v3/room_scroll.h','overlays/v3/room_scroll.ld',
    'overlays/v3/room_rigs_bootstrap.c','overlays/v3/room_rigs_bootstrap.ld')


def source_contract(source,image,report):
    from v3_furniture_contact import floor_bindings,checked_floor_record
    from v3_registry import furniture_representation_identity
    raw,receipt=source.function(0x10EBAC)
    if (receipt['symbol']!='aMR_SetMoveSE' or len(raw)!=336 or
            sha256(raw)!='abfbf085e496f145dd9cbf3d95e1bf700452444240057befd571012643b8766d' or
            receipt['relocations']!={166:(6,1,6,48192),170:(4,1,6,48192),294:(6,1,6,48192),302:(4,1,6,48192)}):
        raise ValueError('Changed complete source room movement rule')
    helpers={}
    for at,name,digest in (
        (0x30,'aMR_GetContactInfoLayer1','db0a6978f69d604ba28b26684d101066aebdeb796c8c1972909e1f1062de4006'),
        (0x8C,'sAdo_OngenTrgStart','4fdc889bb1697c19c8f386d72b80585ea07706d9f26b328389766bec96f0f989'),
        (0x11C,'sAdo_FloorTrgStart','bb445ce0c2bec3a15875b8896f9a2cad894c241e84281d132951366622f0b51c')):
        word=u32(raw,at);delta=word&0x3FFFFFC
        if delta&0x2000000:delta-=0x4000000
        _,r=source.function(receipt['offset']+at+delta)
        if word&0xFC000003!=0x48000001 or r['symbol']!=name or r['sha256']!=digest:
            raise ValueError('Changed complete room movement helper')
        helpers[name]=r
    floors=floor_bindings(image,dict(source_floors=[u32(raw,at)&65535 for at in (0xB8,0xC0)]),report)
    if not all(checked_floor_record(r) for r in floors):raise ValueError('Movement needs complete floor bindings')
    rows=[]
    for mode,case,sounds in ((1,0x24,(0x88,0x98)),(2,0x18,(0x10C,))):
        source_index=u32(raw,case)&65535
        if not 1024<=source_index<1267:raise ValueError('Movement source identity exceeds donor furniture')
        item=0x3000+(source_index-1024)*4;index,target=furniture_representation_identity(item)
        rows.append(dict(source_item_id=f'{item:04X}',item_id=f'{target:04X}',runtime_index=index,
            mode=mode,source_sounds=[u32(raw,at)&65535 for at in sounds],
            floors=floors if mode==2 else [],states=list(range(1,5 if mode==2 else 8)),
            directions=[0] if mode==2 else [1,3],floor_fallback=mode==2))
    return dict(function=receipt,helpers=helpers,rows=rows,native_floor_argument_preserved=True)


def encode(rows):
    if not rows or len(rows)>CAPACITY or [r['runtime_index'] for r in rows]!=sorted({r['runtime_index'] for r in rows}):
        raise ValueError('Invalid shared movement table membership')
    result=bytearray(struct.pack('>4I',MAGIC,len(rows),12,0))
    for r in rows:
        index,mode=r['runtime_index'],r['mode'];a,b=r['sounds'];fa,fb=r['floors']
        if (not 1024<=index<2048 or mode not in (1,2) or not 0<a<0x500 or not 0<=b<0x500 or
                mode==1 and (not b or fa or fb) or mode==2 and (b or not 0<=fa<128 or not 0<=fb<128 or fa==fb)):
            raise ValueError('Invalid complete shared movement record')
        result.extend(struct.pack('>6H',index,mode,a,b,fa,fb))
    return bytes(result)


def prepare(source,image,report):
    from v3_sound_programs import prepare_triggers
    contract=source_contract(source,image,report)
    resources,audio=prepare_triggers(image,report,[sid for r in contract['rows'] for sid in r['source_sounds']])
    audio.update(format='AFV3-ROOM-MOVEMENT-PREPARED-1',contract=contract,furniture=contract['rows'],
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()),
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    files={'font.bin':resources['font'],'wave.bin':resources['wave'],**resources['fragments']}
    audio['files']={name:dict(bytes=len(data),sha256=sha256(data)) for name,data in files.items()}
    return resources,audio,files


def prepare_audio(image,report,source,output,selected=()):
    from apply_translation import write_new
    if selected:raise ValueError('Prepare the complete shared room movement category together')
    _,audio,files=prepare(source,image,report)
    output.mkdir(parents=True,exist_ok=False)
    for name,data in files.items():write_new(output/name,data)
    write_new(output/'audio.json',(json.dumps(audio,indent=2)+'\n').encode())
    return audio


def checked_owner(image,entry=None):
    from v3_npc_draw import relocation_offsets
    data=by_vrom(image)[OWNER].extract(image);rel=by_vrom(image)[RELOC].extract(image)
    body=bytearray(data[FIRST-RAM:LAST-RAM]);at=CALL-FIRST
    before=struct.pack('>2I',0x0C034779,0x24A50008)
    expected=before if entry is None else struct.pack('>2I',0x0C000000|(entry>>2&0x3FFFFFF),0x24A50008)
    if body[at:at+8]!=expected:raise ValueError('Changed native movement call binding')
    body[at:at+8]=before
    if sha256(body)!=NATIVE_SHA or relocation_offsets(rel,len(data))&set(range(CALL-RAM,CALL-RAM+8,4)):
        raise ValueError('Changed complete native movement owner or relocation')
    return data


def checked_binding(source,image,report):
    """Rebind installed dispatch, complete programs, and actual instruments."""
    from v3_sound_programs import prepare_triggers,bind_trigger,trigger_program,installed_resource
    equipment=report['equipment_resources'];rig=equipment['room_rigs'];scroll=rig.get('scrolling',{})
    movement=scroll.get('movement')
    if movement is None:return {}
    files=by_vrom(image);blob=files[BLOB].extract(image);core=files[CODE_VROM].extract(image)
    module=blob[equipment['blob_offset']:equipment['blob_offset']+equipment['bytes']]
    packet=blob[scroll['packet']['blob_offset']:scroll['packet']['blob_offset']+scroll['packet']['bytes']]
    source_rule=source_contract(source,image,report);encoded=encode(movement['rows'])
    body=checked_owner(image,BRIDGE)[FIRST-RAM:LAST-RAM]
    code=scroll['code'];boot=rig['bootstrap'];helper=boot['symbols']['af_v3_room_boot_scroll_move_sound']
    bridge=struct.pack('>2I',0x08000000|(helper>>2&0x3FFFFFF),0)
    if (movement['format']!='AFV3-ROOM-MOVEMENT-1' or movement['entry']!=BRIDGE or
            movement['helper_entry']!=helper or movement['bridge_hex']!=bridge.hex() or
            module[BRIDGE-equipment['ram']:BRIDGE-equipment['ram']+8]!=bridge or
            movement['owner_function_sha256']!=sha256(body) or
            movement['source']!=json.loads(json.dumps(source_rule)) or
            packet[TABLE-0x804BA000:TABLE-0x804BA000+len(encoded)]!=encoded or
            sha256(encoded)!=movement['table_sha256'] or sha256(packet[:code['bytes']])!=code['sha256'] or
            '-DAF_V3_ROOM_MOVEMENT=1' not in code['flags']):
        raise ValueError('Changed complete shared room movement installation')
    for r in movement['native_contract']:
        if sha256(core[r['address']-CODE_RAM:r['address']-CODE_RAM+r['bytes']])!=r['sha256']:
            raise ValueError('Changed native movement sound consumer')
    resources,audio=prepare_triggers(image,report,[s for r in source_rule['rows'] for s in r['source_sounds']])
    original={r['sound_word']:r for r in audio['programs']};mapping={}
    sequence,header,physical=installed_resource(image,core,'seq',199)
    record=equipment['sound_programs']['sequence']
    if sha256(sequence)!=record['sha256'] or header.hex()!=record['header_after'] or physical!=record['physical']:
        raise ValueError('Changed movement sound sequence')
    for r in movement['programs']:
        source_word=r['source_sound_word'];p=original[source_word]
        raw=resources['fragments'][p['fragment_file']];origin=p['fragment_origin']
        desc=trigger_program(bytes(origin)+raw,origin,origin+len(raw))
        bound=bind_trigger(raw,desc,r['offset'],p['native_selector'],p['native_instrument'])
        word=r['native_sound_word'];group,index=(word&0x7FFF)>>8,word&255
        table=struct.unpack_from('>H',sequence,0x188+group*2)[0]
        if (source_word in mapping or r['source_program']!=p['source_program'] or
                r['native_instrument']!=p['native_instrument'] or r['bytes']!=len(bound) or
                sha256(bound)!=r['sha256'] or sequence[r['offset']:r['offset']+len(bound)]!=bound or
                struct.unpack_from('>H',sequence,table+index*2)[0]!=r['offset'] or
                core[0x80113B84-CODE_RAM+index]!=r['trigger_priority']):
            raise ValueError('Changed complete movement sound program or instrument')
        mapping[source_word]=word
    if set(mapping)!=set(original):raise ValueError('Incomplete movement audio category')
    expected=[]
    for r in source_rule['rows']:
        expected.append(dict(source_item_id=r['source_item_id'],item_id=r['item_id'],runtime_index=r['runtime_index'],
            mode=r['mode'],sounds=[mapping[s] for s in r['source_sounds']]+([0] if r['mode']==2 else []),
            floors=[f['native_index'] for f in r['floors']] if r['floors'] else [0,0]))
    if movement['rows']!=sorted(expected,key=lambda r:r['runtime_index']):
        raise ValueError('Movement records differ from complete source rules')
    return {r['source_item_id']:dict(r,entry=BRIDGE,owner_function_sha256=sha256(body)) for r in movement['rows']}


def install(image,prior,blob,code,original,output,directory,prepared):
    from v3_furniture_pipeline import Source
    from v3_sound_programs import (installed_resource,register_triggers,install_audio_resources,
        permanent_budget)
    from v3_villager_audio import read_audio_donor
    from v3_room_rig_runtime import publish_packet
    if prepared['base_sha256']!=sha256(image):raise ValueError('Movement audio needs its checked current base')
    if prior['equipment_resources']['room_rigs']['scrolling'].get('movement'):
        raise ValueError('Shared movement sounds already installed')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    resources,audio,files=prepare(source,image,prior)
    if json.loads(json.dumps(audio))!=prepared or any((directory/name).read_bytes()!=data for name,data in files.items()):
        raise ValueError('Changed complete prepared movement sound resources')
    owner=bytearray(checked_owner(image));native=by_vrom(original)[CODE_VROM].extract(original)
    native_contract=[]
    for first,last in ((0x800D1D58,0x800D1D94),(0x800D1DE4,0x800D1E20),(0x800FA354,0x800FA498)):
        body=native[first-CODE_RAM:last-CODE_RAM]
        if code[first-CODE_RAM:last-CODE_RAM]!=body:raise ValueError('Changed positioned sound consumer')
        native_contract.append(dict(address=first,bytes=len(body),sha256=sha256(body)))
    # These complete native layer handlers implement transposition, continuous
    # notes, and timed pitch sweeps used by the rolling sound.
    for opcode in (0xC2,0xC4,0xC7):
        pointer=0x801184B8+(opcode-0xC1)*4-CODE_RAM
        if code[pointer:pointer+4]!=native[pointer:pointer+4]:raise ValueError('Changed sound layer handler dispatch')
    result=copy.deepcopy(prior['equipment_resources']);previous=result['furniture_audio']
    sequence,header,physical=installed_resource(image,code,'seq',199)
    old=result['sound_programs']['sequence']
    if sha256(sequence)!=old['sha256'] or header.hex()!=old['header_after'] or physical!=old['physical']:
        raise ValueError('Changed complete installed movement sequence')
    counts={r['group']:r['previous_count'] for r in previous['tables']}
    counts[0]=result['sound_programs']['surface_batch']['movement_table']['count']
    if counts[0]!=81:raise ValueError('Changed complete installed floor movement table')
    dol,_=read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    priority=bytes(code[0x80113B84-CODE_RAM:0x80113B84-CODE_RAM+128])
    new_sequence,programs,tables=register_triggers(sequence,audio['programs'],resources['fragments'],counts,
        priority,dol.read(0x800A9A90,128),previous=previous)
    seq,bank,wave,changes,growth,heap,patches,budget,fire=install_audio_resources(
        image,prior,blob,code,new_sequence,resources,audio)
    mapping={r['source_sound_word']:r['native_sound_word'] for r in programs};rows=[]
    for r in audio['contract']['rows']:
        rows.append(dict(source_item_id=r['source_item_id'],item_id=r['item_id'],runtime_index=r['runtime_index'],
            mode=r['mode'],sounds=[mapping[s] for s in r['source_sounds']]+([0] if r['mode']==2 else []),
            floors=[f['native_index'] for f in r['floors']] if r['floors'] else [0,0]))
    rows.sort(key=lambda r:r['runtime_index']);encode(rows)
    scroll=result['room_rigs']['scrolling']
    scroll['movement']=dict(format='AFV3-ROOM-MOVEMENT-1',source=audio['contract'],rows=rows,
        programs=programs,table_ram=TABLE,table_sha256=sha256(encode(rows)),native_contract=native_contract,
        owner_vrom=OWNER,call_address=CALL,additional_resident_bytes=0,native_execution_tested=False)
    publish_packet(result,blob,output)
    entry=BRIDGE
    struct.pack_into('>I',owner,CALL-RAM,0x0C000000|(entry>>2&0x3FFFFFF));changes[OWNER]=bytes(owner)
    scroll['movement'].update(entry=entry,owner_function_sha256=sha256(owner[FIRST-RAM:LAST-RAM]))
    # The source-bound contact receipt gains its separately implemented owner
    # behaviour. Updating metadata does not change the packed alpha record.
    bindings={r['source_item_id']:dict(r,entry=entry,owner_function_sha256=sha256(owner[FIRST-RAM:LAST-RAM])) for r in rows}
    for r in scroll['rows']:
        if r.get('lifecycle',{}).get('category')=='contact-floor-alpha':
            r['lifecycle']['movement']=bindings[r['source_item_id']]
    for r in scroll['lifecycle_rows']:
        if r['mode']==3:r['source']['movement']=bindings[r['source_item_id']]
    after=permanent_budget(code);shared=result['sound_programs']
    shared.update(previous_sequence=copy.deepcopy(old),sequence=seq,after_budget=after,native_synthesis_tested=False)
    shared.setdefault('trigger_batches',[]).append(dict(programs=programs,tables=tables))
    group_zero=next(r for r in tables if r['group']==0)
    movement=shared['surface_batch']['movement_table']
    movement.update(offset=group_zero['offset'],count=128)
    previous.update(sequence=seq,font=bank,wave=wave,tables=tables,layout=audio['layout'],after_budget=after)
    previous['programs']=sorted({r['source_sound_word']:r for r in previous['programs']+programs}.values(),key=lambda r:r['source_sound_word'])
    previous.setdefault('batches',[]).append(dict(category='room-movement',programs=programs,heap_growth=heap))
    result['furniture_level_audio'].update(sequence=copy.deepcopy(seq),font=copy.deepcopy(bank),wave=copy.deepcopy(wave),after_budget=after)
    result['furniture_audio']['audio_heap_growth']=heap
    surfaces=copy.deepcopy(prior['room_surfaces'])
    surfaces['sound'].update(sequence=copy.deepcopy(seq),movement_table=copy.deepcopy(movement),after_budget=after)
    result['additional_resident_bytes']=0
    return result,changes,dict(fire_sound=fire,room_surfaces=surfaces,resource_growth=[growth] if growth else [])
