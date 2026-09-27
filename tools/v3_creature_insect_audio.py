"""Bind the complete added-insect sound category through shared audio machinery.

No individual species installer, substitute sounds, or new audio engine. The
prepared resources and runtime routing must be installed together by the creature
builder. Preparing this packet alone does not enable an import.
"""
import copy
import json
import re
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
from apply_translation import write_new
from v3_asset_loader import ROOT
import v3_sound_programs as sounds

FORMAT='AFV3-INSECT-FIELD-AUDIO-PREPARED-1'
LEVELS=(0x45,0x4F)
TRIGGERS=(0x6A,0x438)
SOURCES=('tools/v3_creature_insect_audio.py','tools/v3_sound_programs.py',
         'tools/v3_room_creature_audio.py','overlays/v3/creature_insect_audio.c')


def source_calls():
    from v3_creature_insects import PROGRAMS
    constants=dict(NA_SE_25=0x25,NA_SE_26=0x26,NA_SE_MOLE_CRICKET_HIDE=0x44,
        NA_SE_MOLE_CRICKET_OUT=0x45,NA_SE_KA_BUZZ=0xCF,NA_SE_6A=0x6A,NA_SE_438=0x438)
    rows=[];levels=set();triggers=set()
    def number(word):
        return constants[word] if word in constants else int(word,0)
    for name,_,_,digest in PROGRAMS:
        path=ROOT/f'local/ac-decomp/src/actor/ac_ins_{name}.c';data=path.read_bytes()
        if sha256(data)!=digest:raise ValueError('Changed complete insect sound caller')
        text=data.decode()
        level=[number(s.strip()) for s in re.findall(r'sAdo_OngenPos\([^,]+,([^,]+),',text)]
        trigger=[number(s.strip()) for s in re.findall(r'sAdo_OngenTrgStart\(([^,]+),',text)]
        if len(level)!=text.count('sAdo_OngenPos(') or len(trigger)!=text.count('sAdo_OngenTrgStart('):
            raise ValueError('Unresolved insect sound call')
        rows.append(dict(program=name,source_sha256=digest,positioned=level,triggers=trigger))
        levels.update(level);triggers.update(trigger)
    if levels!={0x25,0x26,0x44,0x45,0xCF} or triggers!=set(TRIGGERS):
        raise ValueError('Incomplete insect field sound category')
    return rows


def native_contract(image,prior,source):
    from v3_room_creature_audio import checked_binding
    if not checked_binding(source,image,prior):
        raise ValueError('Hidden insect sound requires the complete installed chirp scheduler')
    native=verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    before=by_vrom(native)[CODE_VROM].extract(native);code=by_vrom(image)[CODE_VROM].extract(image)
    functions=[]
    # Complete coordinate wrapper, positioned dispatch, trigger dispatch, and
    # queued-level selector. The last retains bit 80 at +12 before selecting 7F.
    for first,last in ((0x800D197C,0x800D1D08),(0x800D1D08,0x800D1D94),
                       (0x800F7870,0x800F7A24),(0x800F9C60,0x800FA0AC),
                       (0x800FA354,0x800FA498),(0x800F6BF8,0x800F6FCC)):
        at=first-CODE_RAM;raw=code[at:last-CODE_RAM]
        if not raw or raw!=before[at:last-CODE_RAM]:
            raise ValueError('Changed complete field-sound native consumer')
        functions.append(dict(address=first,end=last,sha256=sha256(raw)))
    return dict(functions=functions,positioned=0x800D1D08,trigger=0x800D1D58,
        hidden_chirp=0x800D24EC,hidden_source_id=0x44,high_bit_mode=0x80,
        scheduler=copy.deepcopy(prior['equipment_resources']['creature_audio']['table']))


def shared_levels(image,code,dol,donor):
    """Prove full 25/26 channels and addressed instruments, not numeric aliases."""
    source,_=sounds.resource(dol.read,sounds.GC_SECTIONS,donor,'seq',242)
    sequence,_,_=sounds.installed_resource(image,code,'seq',199)
    sb,sh=sounds.resource(dol.read,sounds.GC_SECTIONS,donor,'bank',153)
    sw,_=sounds.resource(dol.read,sounds.GC_SECTIONS,donor,'wave',sh[10])
    nb,nh,_=sounds.installed_resource(image,code,'bank',139)
    nw,_,_=sounds.installed_resource(image,code,'wave',nh[10])
    starts=struct.unpack_from('>96H',source,0x2E02)
    table=struct.unpack_from('>H',sequence,0x179)[0]
    native_starts=struct.unpack_from('>128H',sequence,table);rows=[]
    for sid in (0x25,0x26):
        at=starts[sid];end=min(p for p in starts if p>at);raw=source[at:end]
        description=sounds.looping_layer(raw,at);target=native_starts[sid]
        converted=bytearray(raw)
        for pointer in description['pointers']:
            old=struct.unpack_from('>H',raw,pointer)[0]
            struct.pack_into('>H',converted,pointer,target+old-at)
        if sounds.span(sequence,target,len(raw))!=converted:
            raise ValueError('Shared insect sound changes its complete source program')
        index=description['instrument']
        identity=sounds.instrument(sb,sw,index,sh[12],extended=True)
        if sounds.instrument(nb,nw,index,nh[12],extended=True)!=identity:
            raise ValueError('Shared insect sound changes its full instrument or samples')
        rows.append(dict(sound=sid,source=description,native_offset=target,
            native_sha256=sha256(converted),instrument_identity=identity))
    return rows


def prepare(image,prior,source):
    code=by_vrom(image)[CODE_VROM].extract(image)
    callers=source_calls();native=native_contract(image,prior,source)
    loop_resources={}
    sequence,levels=sounds.prepare_levels(image,prior,code,list(LEVELS),font_resources=loop_resources)
    resources,triggers=sounds.prepare_triggers(image,prior,list(TRIGGERS))
    # This category's loop instruments already exist in the expanded font.
    # The trigger converter retains their indices while appending its additions.
    # Check identities, including all sample data, before sharing the final font.
    count=levels['layout']['instrument_count']
    for index in range(count):
        if sounds.instrument(loop_resources['font'],loop_resources['wave'],index,count,extended=True)!=\
                sounds.instrument(resources['font'],resources['wave'],index,
                    triggers['layout']['instrument_count'],extended=True):
            raise ValueError('Combined field audio changes a required instrument')
    previous=prior['equipment_resources']['furniture_audio']
    dol,audio=sounds.read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    donor={k:sounds.span(audio,*struct.unpack_from('>II',sounds.header_entry(dol.read,0x800CE450,i)))
           for i,k in enumerate(('seq','bank','wave'))}
    priority=sounds.span(code,0x80113B84-CODE_RAM,128)
    sequence,programs,tables=sounds.register_triggers(sequence,triggers['programs'],resources['fragments'],
        {r['group']:r['previous_count'] for r in previous['tables']},
        priority,dol.read(0x800A9A90,128),previous=previous)
    mapping={r['source_sound_word']:r['native_sound_word'] for r in programs}
    config=struct.pack('>2H',*[mapping[word] for word in TRIGGERS])
    files={'sequence.bin':sequence,'font.bin':resources['font'],'wave.bin':resources['wave'],
           'bindings.bin':config,**resources['fragments']}
    report=dict(format=FORMAT,base_sha256=sha256(image),callers=callers,native=native,
        shared_levels=shared_levels(image,code,dol,donor),levels=levels,triggers=triggers,
        programs=programs,tables=tables,priority_table_sha256=sha256(priority),
        files={n:dict(bytes=len(d),sha256=sha256(d)) for n,d in files.items()},
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES},
        resources_installed=False,runtime_installed=False,native_synthesis_tested=False,
        physical_audio_played=False)
    return files,report


def write_prepared(image,prior,source,output):
    files,report=prepare(image,prior,source)
    output.mkdir(parents=True,exist_ok=False)
    for name,data in files.items():write_new(output/name,data)
    write_new(output/'audio.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


def install(image,prior,blob,code,directory,prepared):
    """Shared resource installer; controller installation remains the caller's job."""
    from v3_furniture_pipeline import Source
    if not directory.is_relative_to(ROOT/'build') or prepared['format']!=FORMAT:
        raise ValueError('Unbound insect field audio preparation')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    data,expected=prepare(image,prior,source)
    if prepared!=json.loads(json.dumps(expected)) or any((directory/n).read_bytes()!=d for n,d in data.items()):
        raise ValueError('Changed complete insect field audio preparation')
    seq,bank,wave,changes,growth,heap_growth,patches,before,fire=sounds.install_audio_resources(
        image,prior,blob,code,data['sequence.bin'],dict(font=data['font.bin'],wave=data['wave.bin']),
        prepared['triggers'])
    result=copy.deepcopy(prior['equipment_resources']);shared=result['sound_programs']
    shared.update(previous_sequence=copy.deepcopy(shared['sequence']),sequence=seq,
        imports=shared['imports']+prepared['levels']['programs'],
        before_budget=before,after_budget=sounds.permanent_budget(code),native_synthesis_tested=False)
    shared.setdefault('trigger_batches',[]).append(dict(programs=prepared['programs'],tables=prepared['tables']))
    for key in ('furniture_audio','furniture_level_audio'):
        if key in result:
            result[key].update(sequence=copy.deepcopy(seq),font=copy.deepcopy(bank),wave=copy.deepcopy(wave),
                after_budget=copy.deepcopy(shared['after_budget']))
    trigger=result['furniture_audio']
    trigger.update(programs=sorted(trigger['programs']+prepared['programs'],key=lambda p:p['source_sound_word']),
        tables=prepared['tables'],layout=prepared['triggers']['layout'])
    result['insect_field_audio']=dict(prepared_sha256=sha256((directory/'audio.json').read_bytes()),
        callers=prepared['callers'],native=prepared['native'],programs=prepared['programs'],
        levels=prepared['levels']['programs'],bindings_hex=data['bindings.bin'].hex(),
        sequence=seq,font=bank,wave=wave,resource_growth=growth,
        audio_heap_growth=heap_growth,heap_patches=patches,resources_installed=True,
        runtime_installed=False,native_synthesis_tested=False,physical_audio_played=False)
    return result,changes,dict(fire_sound=fire,resource_growth=[growth] if growth else [])
