"""Connect the complete prepared Nook code-entry, text, font, and gift path."""
import argparse
import copy
import json
from pathlib import Path
import struct

from aflib import CODE_RAM,by_vrom,sha256,u32
from apply_translation import write_new
from v3_asset_loader import ROOT,BLOB
from v3_nook_font import VROM as FONT,bind_module
from v3_nook_native import SHOPS

SOURCES=('tools/v3_nook_install.py','tools/v3_nook_dialogue.py','tools/v3_nook_font.py',
    'tools/v3_nook_native.py','tools/v3_password_runtime.py','tools/v3_event_text.py',
    'tools/v3_sound_programs.py','tools/v3_resource_capacity.py',
    'tools/v3_furniture_install.py','translations/provenance.json')


def bundle(lock,runtime,font,dialogue,audio,out):
    """Retain checked, already converted resources in one ignored preparation."""
    from v3_furniture_install import inputs
    image,prior=inputs(lock)
    if out.exists() or not out.resolve().is_relative_to(ROOT/'build'):
        raise ValueError('Use a fresh ignored Nook preparation')
    out.mkdir(parents=True)
    equipment=json.loads((runtime/'equipment.json').read_bytes())
    native=json.loads((runtime/'native.json').read_bytes())
    font_report=json.loads((font/'profile.json').read_bytes())
    text=json.loads((dialogue/'dialogue.json').read_bytes())
    sound=json.loads((audio/'audio.json').read_bytes())
    for name,digest in native['source'].items():
        if sha256((ROOT/name).read_bytes())!=digest:raise ValueError('Changed prepared Nook source: '+name)
    for name,digest in font_report['source'].items():
        if sha256((ROOT/name).read_bytes())!=digest:raise ValueError('Changed prepared Nook font source: '+name)
    files={}
    def retain(source,target):
        data=source.read_bytes();destination=out/target
        destination.parent.mkdir(parents=True,exist_ok=True)
        write_new(destination,data)
        files[target]=dict(bytes=len(data),sha256=sha256(data))
    retain(runtime/'equipment.json','equipment.json');retain(runtime/'native.json','native.json')
    for name in SHOPS:
        for filename in ('installed.bin','installed-relocation.bin','installed.json'):
            retain(runtime/'native'/name/filename,'native/'+name+'/'+filename)
    for filename in ('font.bin','relocation.bin','pixels.bin','profile.json'):
        retain(font/filename,'font/'+filename)
    for row in text['resources']:retain(dialogue/row['file'],'dialogue/'+row['file'])
    retain(dialogue/'dialogue.json','dialogue/dialogue.json')
    for name in sound['files']:retain(audio/name,'audio/'+name)
    retain(audio/'audio.json','audio/audio.json')
    # Whole motions are unchanged native programs, verified against source
    # curves and headers as one batch rather than guessed animation numbers.
    from v3_furniture_pipeline import Source
    from v3_holiday_participants import native_motions
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    motions=native_motions(source,image,{'nook.c':'aNPC_ANIM_TRANSFER1 aNPC_ANIM_TRANS_WAIT1 aNPC_ANIM_WAIT1'})
    if any(r.get('imported') for r in motions) or {r['name']:r['native']['index'] for r in motions}!={
            'aNPC_ANIM_TRANSFER1':26,'aNPC_ANIM_TRANS_WAIT1':27,'aNPC_ANIM_WAIT1':5}:
        raise ValueError('Nook handover requires additional motion conversion')
    report=dict(format='AFV3-NOOK-PREPARED-1',base_sha256=sha256(image),base_lock=json.loads(lock.read_bytes()),
        files=files,motions=motions,source={p:sha256((ROOT/p).read_bytes()) for p in SOURCES},
        installed=False,native_execution_tested=False,ordinary_gameplay_tested=False)
    write_new(out/'prepared.json',(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode())
    return report


def install(base,prior,blob,core,module,original,output,directory,lock):
    from v3_furniture_install import relocate_resource_plan
    from v3_password_runtime import refresh
    from v3_event_text import patch_bounds
    from v3_holiday_dialogue import check_provenance
    from v3_sound_programs import install_audio_resources,permanent_budget
    prepared=json.loads((directory/'prepared.json').read_bytes())
    if (prepared['format']!='AFV3-NOOK-PREPARED-1' or prepared['base_sha256']!=sha256(base) or
            prior['equipment_resources']['passwords'].get('acquisition_installed')):
        raise ValueError('Nook preparation needs its exact incomplete predecessor')
    for name,digest in prepared['source'].items():
        if sha256((ROOT/name).read_bytes())!=digest:raise ValueError('Changed connected Nook source: '+name)
    for name,row in prepared['files'].items():
        data=(directory/name).read_bytes()
        if len(data)!=row['bytes'] or sha256(data)!=row['sha256']:raise ValueError('Changed complete prepared Nook resource')
    previous=json.loads((directory/'equipment.json').read_bytes())['passwords']
    # Refresh the map and runtime through their ordinary builder. Prepared
    # native imports must still name these exact linked functions.
    equipment=refresh(base,prior,blob,original,output,ROOT/'build/v3-password-policy-prepared-03',lock)
    password=equipment['passwords']
    if any(password[k]!=previous[k] for k in ('sha256','crc32','parts','code','bootstrap')):
        raise ValueError('Prepared Nook owners no longer bind the current password engine')
    files=by_vrom(base);changes={};records=copy.deepcopy(prior['physical_resources']);writes=[];growth=[]
    native=json.loads((directory/'native.json').read_bytes());shops=copy.deepcopy(prior['shop_actors'])
    relocation_targets={}
    for name,(_,_,_) in SHOPS.items():
        row=native['owners'][name];old=shops['owners'][name]
        owner=(directory/'native'/name/'installed.bin').read_bytes()
        relocation=(directory/'native'/name/'installed-relocation.bin').read_bytes()
        if (sha256(owner)!=row['overlay_sha256'] or sha256(relocation)!=row['relocation_sha256'] or
                row['previous_sha256']!=old['output_sha256'] or
                row['previous_relocation_sha256']!=old['relocation_sha256']):
            raise ValueError('Changed complete Nook native append')
        changes.update({old['vrom']:owner,row['previous_reloc_vrom']:relocation})
        target=row['previous_reloc_vrom']
        if any(e.vstart<target+len(relocation) and target<e.vend
                for v,e in files.items() if v!=target):
            # The native loader uses the following directory entry, not an
            # assumed image-end identity. Move that complete relocation file
            # to the shop's reserved relocation range when it grows.
            target=old['vrom']+0x10000
        relocation_targets[row['previous_reloc_vrom']]=target
        row['installed_reloc_vrom']=target
        old.update(output_sha256=sha256(owner),relocation_sha256=sha256(relocation),
            allocation_bytes=len(owner),reloc=target,nook_code_entry=row)
        for consumer in equipment['carried_items']['paper']['quantities']['native_consumers']:
            if consumer['name']=='shop-'+name:
                consumer.update(installed_reloc=target)
                consumer['owner'].update(bytes=len(owner),owner_sha256=sha256(owner),relocation_sha256=sha256(relocation))
    for descriptor in native['descriptors']:
        at=descriptor['address']-CODE_RAM
        if struct.unpack_from('>4I',core,at)!=tuple(descriptor['before']):
            raise ValueError('Changed Nook native allocation before installation')
        struct.pack_into('>4I',core,at,*descriptor['after'])
    font=json.loads((directory/'font/profile.json').read_bytes())
    font_data=(directory/'font/font.bin').read_bytes();font_rel=(directory/'font/relocation.bin').read_bytes()
    pixels=(directory/'font/pixels.bin').read_bytes();joined=font_data+font_rel
    if (sha256(joined)!=font['blob_sha256'] or sha256(pixels)!=font['physical_resource']['sha256']):
        raise ValueError('Changed complete Nook font owner or source pixels')
    if (font['pixels_ram']<password['ram']+password['bytes'] or font['pixels_ram']&15 or
            font['pixels_end']!=font['pixels_ram']+len(pixels) or
            font['pixels_end']>0x80800000 or
            font['pixel_allocation_bytes']!=0):
        raise ValueError('Nook glyphs overlap the password packet or furniture banks')
    title=font['title_buffer'];start=title['function']-CODE_RAM
    from v3_console_disk_install import reservations
    for owner_first,owner_last in reservations(prior):
        for first,last in ((font['pixels_ram'],font['pixels_end']),(title['ram'],title['end'])):
            if first<owner_last and owner_first<last:
                raise ValueError('Nook resident buffers overlap a retained RAM reservation')
    if (title['ram']<font['pixels_end'] or title['ram']&15 or
            title['end']!=title['ram']+title['resource_bytes'] or
            title['end']>0x80800000 or
            sha256(core[start:start+title['bytes']])!=title['sha256'] or
            sha256(files[title['resource_vrom']].extract(base))!=title['resource_sha256']):
        raise ValueError('Changed complete native title-buffer binding or Expansion Pak bounds')
    bind_module(module,joined,font);changes[FONT]=joined
    records.append(font['physical_resource']);writes.append((font['physical_resource'],pixels))
    text=json.loads((directory/'dialogue/dialogue.json').read_bytes());check_provenance(text)
    # The complete message bank ends at the current reward startup packet.
    # Move that unchanged packet, not megabytes of retained dialogue. Every
    # shared alias and the ordinary bootstrap use the replacement receipt.
    import v3_physical_resources as physical
    from v3_event_text import MESSAGE
    bank=files[MESSAGE];bank_after=bank.pstart+next(r['bytes'] for r in text['resources'] if r['vrom']==MESSAGE)
    blocked=[r for r in prior['physical_resources'] if r['physical']<bank_after and
        bank.pstart+bank.size<r['physical']+r['bytes']]
    packet_moves=[]
    if blocked:
        carried=equipment['carried_items'];quest=carried['quest'];old=quest['packet']
        if len(blocked)!=1 or any(blocked[0][k]!=old[k] for k in ('id','physical','bytes','sha256')):
            raise ValueError('Nook text growth encounters an unbound physical owner')
        original_packet=dict(blocked[0]);raw=base[old['physical']:old['physical']+old['bytes']]
        staged=bytearray(base)
        if any(staged[font['physical_resource']['physical']:font['physical_resource']['physical']+len(pixels)]):
            raise ValueError('Nook font pixels overlap a live predecessor')
        staged[font['physical_resource']['physical']:font['physical_resource']['physical']+len(pixels)]=pixels
        new=physical.allocate(staged,records,raw,old['id']+'-relocation',best_fit=True,
            excluded_spans=((bank.pstart,bank_after),(files[BLOB].pstart,files[BLOB].pstart+len(blob))))
        new['id']=old['id'];records[records.index(original_packet)]=new
        for parent in (quest,quest['npc'],quest['rewards'],carried['spawning'],carried['paper']['quantities']):
            p=parent['packet']
            if any(p[k]!=original_packet[k] for k in ('id','physical','bytes','sha256')):
                raise ValueError('Changed shared reward startup packet alias')
            parent['packet']=dict(p,**new)
        writes.append((new,raw));packet_moves.append(dict(previous=original_packet,replacement=dict(new)))
    text['choice_vrom']=prior['import_storage']['choice_vrom']
    text['hooks']=patch_bounds(core,text['first_id'],text['count'])
    at=0x80065544-CODE_RAM;before=0x2A010000|text['first_choice'];after=0x2A010000|(text['first_choice']+text['choice_count'])
    if u32(core,at)!=before:raise ValueError('Changed Nook native choice-reader bound')
    struct.pack_into('>I',core,at,after);text['hooks'].append(dict(address=at+CODE_RAM,before=before,after=after))
    for row in text['resources']:
        data=(directory/'dialogue'/row['file']).read_bytes();target='nook/dialogue/'+row['file']
        (output/target).parent.mkdir(parents=True,exist_ok=True)
        write_new(output/target,data);row.update(file=target,original_sha256=row.pop('previous_sha256'))
    audio=json.loads((directory/'audio/audio.json').read_bytes())
    seq,font_audio,wave,audio_changes,audio_growth,heap_growth,heap_patches,budget,fire=install_audio_resources(
        base,prior,blob,core,(directory/'audio/nook-sequence.bin').read_bytes(),
        {k:(directory/f'audio/nook-{k}.bin').read_bytes() for k in ('font','wave')},audio)
    if set(changes)&set(audio_changes):raise ValueError('Nook owner and audio resources overlap')
    changes.update(audio_changes)
    if audio_growth:growth.append(audio_growth)
    blockers=set(audio_growth.get('relocated_blockers',[])) if audio_growth else set()
    for v,data in changes.items():
        if any(r['vrom']==v for r in growth):continue
        if len(data)==files[v].size and not files[v].pend and v not in blockers:continue
        _,row=relocate_resource_plan(base,files,v,data,minimum_physical=0x100000,
            reservations=records+growth,append_only=False,allow_compressed=True,
            target_vrom=relocation_targets.get(v,v),
            excluded_spans=((files[BLOB].pstart,files[BLOB].pstart+len(blob)),))
        growth.append(row)
    shared=equipment['sound_programs'];programs=audio['registered_programs'];tables=audio['registered_tables']
    shared.update(previous_sequence=copy.deepcopy(shared['sequence']),sequence=seq,
        before_budget=budget,after_budget=permanent_budget(core),native_synthesis_tested=False)
    shared.setdefault('trigger_batches',[]).append(dict(programs=programs,tables=tables))
    for key in ('furniture_audio','furniture_level_audio'):
        if key in equipment:equipment[key].update(sequence=copy.deepcopy(seq),font=copy.deepcopy(font_audio),
            wave=copy.deepcopy(wave),after_budget=copy.deepcopy(shared['after_budget']))
    equipment['furniture_audio'].update(programs=sorted(equipment['furniture_audio']['programs']+programs,
        key=lambda r:r['source_sound_word']),tables=tables,layout=audio['layout'],
        priority_table_sha256=sha256(core[0x80113B84-CODE_RAM:0x80113B84-CODE_RAM+128]))
    audio.update(installed=True,sequence=seq,font=font_audio,wave=wave,heap_growth=heap_growth,heap_patches=heap_patches)
    text['installed']=True
    password.update(keyboard_installed=True,name_conversion_installed=True,acquisition_installed=True,
        native_execution_tested=False,ordinary_gameplay_tested=False)
    password['conversation']['native_bindings_installed']=True
    report=dict(format='AFV3-NOOK-INSTALLED-1',installed=True,native=native,dialogue=text,font=font,audio=audio,
        motions=prepared['motions'],additional_shop_bytes=sum(r['bytes']-r['previous_bytes'] for r in native['owners'].values()),
        additional_system_font_bytes=0,additional_font_owner_bytes=font['additional_allocation_bytes'],
        additional_resident_font_bytes=font['additional_resident_bytes'],
        additional_resident_title_bytes=title['resource_bytes'],
        additional_password_bytes=0,saved_format_changed=False,saved_profile_changed=False,
        native_execution_tested=False,ordinary_gameplay_tested=False,source=prepared['source'],
        shared_session_gift_count=True,complete_names_and_code_rows=True)
    equipment['passwords']['nook']=report
    updates=dict(shop_actors=shops,fire_sound=fire,physical_resources=records,resource_growth=growth,
        relocated_physical_resources=packet_moves)
    write_new(output/'nook/installed.json',(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode())
    return equipment,changes,updates,writes


def finish(image,base,output,equipment,records):
    from v3_event_text import install as install_text
    report=equipment['passwords']['nook']
    return install_text(image,base,output,report['dialogue'],relocate=True,
        physical_resources=records,reserved_end=by_vrom(base)[BLOB].pstart+by_vrom(base)[BLOB].size)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-lock',type=Path,required=True);parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--font',type=Path,required=True);parser.add_argument('--dialogue',type=Path,required=True)
    parser.add_argument('--audio',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();r=bundle(a.base_lock,a.runtime,a.font,a.dialogue,a.audio,a.output)
    print(json.dumps(dict(format=r['format'],files=len(r['files']),base_sha256=r['base_sha256'])))
