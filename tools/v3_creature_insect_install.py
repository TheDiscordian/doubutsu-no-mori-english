"""Install the connected insect runtime, resources, player actions, and saves.

All eight optional identities and their resources are installed together; this
is not a per-species build stage. Native gameplay acceptance remains unverified.
"""
import copy
import json
import struct
import zlib

from aflib import CODE_VROM,by_vrom,sha256,verified_rom
from apply_translation import write_new
from v3_asset_loader import ROOT,BLOB
from v3_console_disk_install import reservations
from v3_furniture_capacity import checked as checked_capacity
from v3_creature_insects import install_controller,install_spawn_manager,install_colony
from v3_creature_insect_pool import install as install_pool
from v3_creature_insect_player import install as install_player,compose_mosquito
from v3_creature_insect_effects import install as install_effects
from v3_creature_insect_audio import install as install_audio
from v3_creature_save import compose_insects
from v3_event_text import patch_bounds,install as install_text
import v3_physical_resources as physical

SOURCES=('tools/v3_creature_insect_install.py','tools/v3_furniture_install.py',
    'tools/v3_creature_choices.py','tools/v3_creature_selection.py','tools/v3_furniture_pipeline.py',
    'tools/v3_room_goods.py','overlays/v3/surface_bootstrap.c','overlays/v3/surface_bootstrap.ld')
RAM=0x80656000
GUARD=bytes.fromhex('41464947')*4


def install(base,prior,blob,output,directory,core):
    directory=directory.resolve()
    if not directory.is_relative_to(ROOT/'build'):raise ValueError('Insect preparation is not an ignored local build')
    prepared=json.loads((directory/'programs.json').read_bytes())
    linked=copy.deepcopy(prepared['linked']);raw=(directory/linked['file']).read_bytes()
    if (prepared['format']!='AFV3-CREATURE-INSECT-PROGRAMS-1' or
            prepared['native_abi']['rom_sha256']!=sha256(base) or
            prepared['compiled']['unbound_engine_adapters'] or
            len(raw)!=linked['bytes'] or sha256(raw)!=linked['sha256'] or
            linked['ram']!=RAM or len(raw)&15 or
            not RAM<linked['bss_start']<=RAM+len(raw) or any(raw[linked['bss_start']-RAM:])):
        raise ValueError('Changed complete linked insect preparation')
    for path,digest in prepared['sources'].items():
        if sha256((ROOT/path).read_bytes())!=digest:raise ValueError('Stale compiled insect dependency: '+path)
    checked_capacity(base,prior)
    packet=raw+GUARD;end=RAM+len(packet)
    if (end>0x807DA800 or any(a<end and RAM<b for a,b in reservations(prior)) or
            prior['equipment_resources'].get('creature_insects')):
        raise ValueError('Insect runtime overlaps an existing resident reservation')
    records=copy.deepcopy(prior.get('physical_resources',[]))
    record=physical.allocate(base,records,packet,'creature-insects-GAFE01-r0')
    records.append(record)
    linked.update(cartridge_allocation_verified=True,installed=True)
    symbols=linked['symbols'];files=by_vrom(base)
    original=verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    start,last=0x80026500-0x80025C60,0x800266C4-0x80025C60
    pi=files[0x1060].extract(base)[start:last]
    if pi!=by_vrom(original)[0x1060].extract(original)[start:last]:
        raise ValueError('Changed complete physical-ROM startup transfer')
    changes,controller=install_controller(base,symbols,prepared['native_abi']['controller'])
    changes,population=install_pool(base,prepared['population'],changes)

    def merge(additions):
        for vrom,data in additions.items():
            if vrom not in changes:changes[vrom]=data;continue
            original=files[vrom].extract(base);current=bytearray(changes[vrom])
            if len(current)!=len(original) or len(data)!=len(original):
                raise ValueError('Overlapping resized insect owners')
            for at,(before,after) in enumerate(zip(original,data,strict=True)):
                if before==after:continue
                if current[at] not in (before,after):raise ValueError('Conflicting connected insect owner writes')
                current[at]=after
            changes[vrom]=bytes(current)

    added,manager=install_spawn_manager(base,symbols,prepared['native_abi']['spawn_manager']);merge(added)
    added,colony=install_colony(base,symbols,prepared['native_abi']['colony']);merge(added)
    changes,player=install_player(base,symbols,prepared['player_interactions'],changes)
    added,effects=install_effects(base,symbols,prepared['field_effects']);merge(added)
    if core!=files[CODE_VROM].extract(base):raise ValueError('Core changed before connected insect composition')
    core[:]=changes.pop(CODE_VROM)
    equipment,audio_changes,updates=install_audio(base,prior,blob,core,directory/'field-audio',prepared['field_audio'])
    merge(audio_changes)
    mosquito=prepared['mosquito_player'];motions=[]
    for row in mosquito['records']:
        data=(directory/'mosquito-player'/row['file']).read_bytes()
        if sha256(data)!=row['sha256'] or len(data)!=row['bytes']:raise ValueError('Changed complete player motion')
        blob.extend(bytes(-len(blob)%16));at=len(blob);blob.extend(data)
        motions.append(dict(row,vrom=BLOB+at,blob_offset=at,storage='import-blob'))
    at=equipment['blob_offset'];module=blob[at:at+equipment['bytes']]
    module,equipment,response,updated_core=compose_mosquito(equipment,module,symbols,mosquito,
        directory/'mosquito-player',motions,core)
    blob[at:at+len(module)]=module;core[:]=updated_core
    response['text']=copy.deepcopy(response['text'])
    response['text']['bound_patches']=patch_bounds(core,mosquito['text']['first_id'],mosquito['text']['count'])
    for row in response['text']['resources']:
        data=(directory/'mosquito-player'/row['file']).read_bytes()
        if len(data)!=row['bytes'] or sha256(data)!=row['sha256']:raise ValueError('Changed official mosquito text')
        write_new(output/row['file'],data)
    updates.update(compose_insects(prior,equipment,blob,prepared['persistent_seasons'],linked))
    updates['physical_resources']=records
    write_new(output/'insect-runtime.bin',packet)
    equipment['insect_field_audio']['runtime_installed']=True
    equipment['creature_insects']=dict(format='AFV3-CREATURE-INSECTS-1',compiled=linked,
        prepared_directory=str(directory.relative_to(ROOT)),prepared_sha256=sha256((directory/'programs.json').read_bytes()),
        packet=dict(ram=RAM,bytes=len(packet),physical=record['physical'],sha256=sha256(packet),
                    crc32=zlib.crc32(packet),storage='physical-ROM',guard=GUARD.hex()),
        physical_resource=record,controller=controller,population=population,manager=manager,
        startup_transfer=dict(address=0x80026500,bytes=len(pi),sha256=sha256(pi)),
        colony=colony,player=player,effects=effects,mosquito=response,
        spawning=prepared['spawning'],intro_environment=prepared['native_abi']['intro_environment'],
        additional_resident_bytes=len(packet),additional_scene_bytes=population['additional_scene_bytes'],
        installed=True,selectable=False,web_patcher_enabled=False,native_execution_tested=False,
        pending=['Optional per-species and population-choice composition',
                 'Connected native gameplay/save checks; existing unresolved failures remain open'],
        sources={p:sha256((ROOT/p).read_bytes()) for p in (*prepared['sources'],*SOURCES)})
    population.update(installed=True,runtime_installation_required=False)
    response['runtime_installation_required']=False
    equipment['creature_fish']['world']['save']['insect_seasons']['runtime_installation_required']=False
    from v3_creature_choices import INSECT_CHOICE
    from v3_creature_selection import connect_insects
    insects=equipment['creature_insects']
    mode=symbols[INSECT_CHOICE['symbol']]
    if not RAM<=mode<linked['bss_start'] or raw[mode-RAM:mode-RAM+4]!=bytes(4):
        raise ValueError('Missing compiled insect population selector')
    insects['behaviour_choice']=dict(INSECT_CHOICE,ram=mode,default='N64',values=dict(N64=0,GameCube=1))
    added,scoring=connect_insects(base,prior,equipment,blob);merge(added);updates.update(scoring)
    insects.update(selectable=True,pending=['Connected native gameplay/save checks; existing unresolved failures remain open'])
    updates['save_runtime'].update(profile_hex=blob[0x20:0xE0].hex(),profile_sha256=sha256(blob[0x20:0xE0]))
    return equipment,changes,updates,[(record,packet)]


def finish(image,base,prior,output,equipment,physical_records):
    text=equipment['creature_insects']['mosquito']['text']
    return install_text(image,base,output,text,relocate=True,physical_resources=physical_records,
        reserved_end=prior.get('resource_capacity',{}).get('reserved_physical_end',0))
