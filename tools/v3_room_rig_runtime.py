"""Install complete shared room rigs without enabling unfinished parent imports."""
import copy
import json
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from v3_asset_loader import ROOT,BLOB,compile_part
from v3_equipment_runtime import RAM as EQUIPMENT_RAM,retired_module_space
from v3_furniture_pipeline import Source,prepare,room_aliases,PreparedAssets
from v3_furniture_rigs import CATEGORY,CLOCK_CATEGORY,STORAGE_CATEGORY,HIT_CATEGORY,BILLBOARD_CATEGORY,ROLLING_CATEGORY,JOINT_CATEGORY,MATERIAL_RIG_CATEGORY,suffix
import v3_furniture_joint_rigs as joints
import v3_furniture_roofs as roofs
from v3_registry import (furniture_representation_identity,ROOM_ALIAS_REGISTRY_VERSION,
                         furniture_identity,furniture_source,furniture_source_index)
from v3_import_storage import ROWS,ITEMS,slot,END
from v3_tent_model import native_contract
from v3_resource_capacity import checked_limit

RAM,TABLE,VTABLE,LIMIT,CAPACITY = 0x804B1800,0x804B1E00,0x804B1FA0,0x804B1FE0,24
MAGIC=0x41465231
PACKET_RAM,PACKET_TABLE,PACKET_BYTES,PACKET_CAPACITY=0x804B8000,0x804B9000,8192,128
EXTENDED_RAM,EXTENDED_TABLE,EXTENDED_BYTES=0x804C8000,0x804CC000,20480
WIDE_RAM,WIDE_TABLE,WIDE_BYTES=0x804D0000,0x804D8000,36864
PACKET_MAGIC=0x41465232
SOUND_TABLE,SOUND_VTABLE,SOUND_MAGIC,SOUND_CAPACITY=0x804B9C10,0x804B1FC0,0x41465331,64
MATERIAL_TABLE,MATERIAL_VTABLE,MATERIAL_MAGIC,MATERIAL_CAPACITY=0x804B9E20,0x804B1E10,0x41464D31,11
SOURCES=('tools/v3_room_rig_runtime.py','tools/v3_asset_loader.py','tools/v3_furniture_rigs.py','tools/v3_keyframes.py',
    'tools/v3_furniture_pipeline.py','tools/v3_furniture_install.py','tools/v3_registry.py','tools/v3_equipment_runtime.py',
    'tools/v3_display_aliases.py','tools/v3_held_catalogue.py',
    'tools/v3_resource_capacity.py','tools/v3_furniture_materials.py','tools/v3_furniture_scroll.py','tools/v3_furniture_contact.py','tools/v3_sound_programs.py','tools/v3_room_movement.py',
    'tools/v3_furniture_behaviours.py','overlays/v3/furniture_behaviours.c','overlays/v3/furniture_behaviours.S','overlays/v3/furniture_behaviours.ld',
    'overlays/v3/room_scroll.c','overlays/v3/room_scroll.h','overlays/v3/room_scroll.ld',
    'overlays/v3/room_materials.c','overlays/v3/room_materials.h',
    'overlays/v3/room_rigs.c','overlays/v3/room_rigs.h','overlays/v3/room_rigs.ld','overlays/v3/room_billboards.c',
    'overlays/v3/held_rigs.ld','overlays/v3/room_rigs_packet.ld',
    'overlays/v3/room_rigs_bootstrap.c','overlays/v3/room_rigs_bootstrap.ld',
    'tools/v3_furniture_motion.py','overlays/v3/room_motion.h','overlays/v3/room_rigs_extended.ld',
    'tools/v3_room_effects.py','overlays/v3/room_effects.c','overlays/v3/room_effects.h',
    'overlays/v3/room_rigs_wide.ld','overlays/v3/room_joints.c','tools/v3_furniture_joint_rigs.py',
    'tools/v3_furniture_needle.py','tools/v3_room_carry.py','tools/v3_room_carry_native.py',
    'overlays/v3/room_needle.c','overlays/v3/room_needle.h')
from v3_furniture_reactions import SOURCES as REACTION_SOURCES
SOURCES+=REACTION_SOURCES
from v3_furniture_static import SOURCES as STATIC_SOURCES
SOURCES+=STATIC_SOURCES
from v3_room_particles import SOURCES as PARTICLE_SOURCES
SOURCES+=PARTICLE_SOURCES
SOURCES+=roofs.SOURCES


def checked_hit_condition(base,report,trigger,sound,audio):
    from v3_room_effects import conditional_binding
    expected=conditional_binding(base,report,trigger)
    if expected:
        program=next((r for r in audio['programs'] if r['source_sound_word']==expected['source_system_word']),None)
        if program is None:raise ValueError('Missing complete conditional system sound')
        expected['native_system_word']=program['native_sound_word']
    if sound.get('conditional')!=expected:
        raise ValueError('Changed complete hit-rig wall/effect/system-sound binding')


def packet_layout(runtime):
    packet=runtime['packet'];ram=packet['ram'];table=runtime['table_ram'];size=packet['bytes']
    if (ram,table,size) not in ((PACKET_RAM,PACKET_TABLE,PACKET_BYTES),
            (EXTENDED_RAM,EXTENDED_TABLE,EXTENDED_BYTES),(WIDE_RAM,WIDE_TABLE,WIDE_BYTES)):
        raise ValueError('Unknown complete room packet layout')
    return ram,table,size


def motion_binding(source,base,report,rows):
    from v3_furniture_motion import native_contract
    from v3_room_movement import checked_binding
    contract=native_contract(base);sounds=checked_binding(source,base,report)
    ids=[r['source_item_id'] for r in rows if r.get('mode')==5]
    if any(sounds.get(donor,{}).get('mode')!=1 for donor in ids):
        raise ValueError('Rolling motion needs its complete movement sound integration')
    return dict(native=contract,movement={donor:sounds[donor] for donor in ids})


def install_profiles(base,prior,blob,core,original,output,directories):
    """Bind complete implemented categories to ordinary, unselected item slots.

    Acquisition, catalogue, and scoring activation remain explicit later stages.
    Existing model storage is reused; no partial graphics or per-item list enters
    this adapter. The selected-profile bits remain unchanged throughout.
    """
    from apply_translation import write_new
    from v3_furniture_install import profile,provenance_patch
    from v3_furniture_pipeline import identity_rows,name_metadata
    from v3_import_storage import ROWS_RAM
    from v3_furniture_materials import (CATEGORY as MATERIAL_CATEGORY,initializer_lifecycle,checked_initializer,
        steam_lifecycle,checked_steam,switched_lifecycle,checked_switched)
    import v3_furniture_reactions as reactions
    from v3_furniture_scroll import (CATEGORY as SCROLL_CATEGORY,VTABLE as SCROLL_VTABLE,
                                    draw_only_lifecycle,checked_runtime,checked_lifecycle,profile_lifecycle)
    from v3_sound_programs import furniture_trigger,checked_furniture_loops
    from v3_furniture_behaviours import install_initial_switch,checked_initial_switch
    import v3_furniture_static as static
    result=copy.deepcopy(prior['equipment_resources']);runtime=result['room_rigs']
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    retained=bind_profiles(source,base,prior)
    placement=checked_initial_switch(base,prior,blob);owner_changes={};updates={}
    directories=[d.resolve() for d in directories]
    cache=PreparedAssets(source,directories)
    identities=identity_rows(ROOT/'build/item-identity-megasheet.xlsx',include_unmapped_legacy=True)
    module=blob[result['blob_offset']:result['blob_offset']+result['bytes']]
    packet=runtime['packet'];at=packet['blob_offset']
    if (sha256(module)!=result['sha256'] or sha256(blob[at:at+packet['bytes']])!=packet['sha256'] or
            module[VTABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM+20].hex()!=runtime['vtable_hex'] or
            module[SOUND_VTABLE-EQUIPMENT_RAM:SOUND_VTABLE-EQUIPMENT_RAM+20].hex()!=runtime.get('sound_vtable_hex')):
        raise ValueError('Changed complete shared room category runtime')
    rigs={r['source_item_id']:r for r in runtime['rows']}
    sounds={r['source_item_id']:r for r in runtime.get('sound_rows',[])}
    materials={r['source_item_id']:r for r in runtime.get('material_rows',[])}
    scrolling=checked_runtime(result,blob)
    contracts,_=checked_furniture_loops(base,core,result,source) if result.get('furniture_level_audio') else ({},{})
    from v3_furniture_contact import checked_contracts
    contracts.update(checked_contracts(source,base,prior))
    old=copy.deepcopy(prior.get('staged_furniture',dict(format='AFV3-STAGED-FURNITURE-PROFILES-1',rows=[],sources=[])))
    if old['format']!='AFV3-STAGED-FURNITURE-PROFILES-1':raise ValueError('Unknown staged furniture format')
    occupied=set();staged=[];evidence=[];deferred=[];material_code_changed=False
    limit=checked_limit(base,prior)
    for directory in directories:
        if not directory.is_relative_to(ROOT/'build'):raise ValueError('Profiles require ignored prepared artwork')
        raw=(directory/'art.json').read_bytes();art=json.loads(raw)
        if art['format']!='AFV3-AUTO-FURNITURE-PREPARED-ASSETS-1':raise ValueError('Expected complete prepared furniture category')
        evidence.append(dict(directory=str(directory.relative_to(ROOT)),sha256=sha256(raw)))
        for row in art['objects']:
            donor=row['item_id'];item=int(donor,16);prepared_row=prepare(source,item)
            descriptor=prepared_row[0];category=descriptor.get('callback_adapter',{}).get('category')
            if (category not in (CLOCK_CATEGORY,STORAGE_CATEGORY,HIT_CATEGORY,BILLBOARD_CATEGORY,ROLLING_CATEGORY,JOINT_CATEGORY,MATERIAL_RIG_CATEGORY,roofs.CATEGORY,'switch-trigger-sound',static.CATEGORY,MATERIAL_CATEGORY,SCROLL_CATEGORY) or
                    donor in occupied or item not in identities or
                    row['profile']!=json.loads(json.dumps(descriptor)) or
                    row['native_profile_scalar_hex']!=descriptor['scalar_hex']):
                raise ValueError('Unsupported, duplicate, or changed complete room category')
            reused=cache.reuse(source,donor,prepared_row)
            if reused is None:raise ValueError('Missing complete prepared profile artwork')
            data=(directory/row['object_file']).read_bytes()
            if len(data)!=row['object_bytes'] or sha256(data)!=row['object_sha256']:
                raise ValueError('Changed complete prepared profile object')
            occupied.add(donor)
            if donor in retained:
                binding=retained[donor];at=binding['room_runtime']['vrom']-BLOB
                if (binding['object_bytes']!=len(data) or binding['object_sha256']!=sha256(data) or
                        blob[at:at+len(data)]!=data):raise ValueError('Changed retained ordinary profile artwork')
                continue
            initial=initializer_lifecycle(source,descriptor) if category==MATERIAL_CATEGORY else None
            reaction=reactions.source_lifecycle(source,descriptor) if category==MATERIAL_CATEGORY and initial is None else None
            if reaction:initial=reaction
            colour=reactions.colour_lifecycle(source,descriptor) if category==MATERIAL_CATEGORY and initial is None else None
            if colour:
                if json.loads(json.dumps(contracts.get(donor)))!=json.loads(json.dumps(colour)):
                    raise ValueError('Player-colour material requires its complete installed audio')
                initial=colour
            steam=steam_lifecycle(source,descriptor) if category==MATERIAL_CATEGORY and initial is None else None
            if steam:
                if json.loads(json.dumps(contracts.get(donor)))!=json.loads(json.dumps(steam)):
                    raise ValueError('Periodic material requires its complete installed audio')
                initial=steam
            switched=switched_lifecycle(source,descriptor) if category==MATERIAL_CATEGORY and initial is None else None
            if switched:
                if contracts.get(donor)!=switched:
                    raise ValueError('Switched material requires its complete installed loop and clicks')
                if placement is None:
                    placement,owner_changes,updates=install_initial_switch(base,prior,blob,source,output)
                initial=switched
            if category==MATERIAL_CATEGORY:
                installed=materials.get(donor)
                if installed and initial and not installed.get('lifecycle_installed'):
                    if reaction and not runtime.get('reactions'):
                        runtime['reactions']=reactions.prepare_installation(source,base,prior)
                    if colour and not runtime.get('colours'):
                        runtime['colours']=reactions.prepare_colours(base,prior)
                    installed.update(lifecycle=5 if switched else 4 if steam else 3 if colour else 2 if reaction else 1,
                        state_offset=initial['source_sound_id'] if colour or steam or switched else initial['native_face'] if reaction else initial['native_offset'],
                        material_lifecycle=json.loads(json.dumps(initial)) if reaction or colour or steam or switched else initial,lifecycle_installed=True)
                    material_code_changed=True
                if not installed or not installed.get('lifecycle_installed'):
                    deferred.append(dict(source_item_id=donor,reason='Material lifecycle remains incomplete'))
                    continue
            if category==SCROLL_CATEGORY:
                lifecycle=draw_only_lifecycle(descriptor,source)
                if lifecycle is None and donor in scrolling:
                    lifecycle=checked_lifecycle(source,descriptor,scrolling[donor],runtime['scrolling'],contracts)
                if lifecycle is None:
                    from v3_furniture_contact import prepare_lifecycle
                    pending=prepare_lifecycle(source,descriptor,base,prior)
                    deferred.append(dict(source_item_id=donor,
                        reason='Contact/floor lifecycle requires additive room-surface imports' if pending and not
                            pending['dependencies_complete'] else 'Scrolling lifecycle remains incomplete',
                        **({'lifecycle_dependencies':pending} if pending else {})))
                    continue
                if lifecycle.get('start_disabled') and placement is None:
                    placement,owner_changes,updates=install_initial_switch(base,prior,blob,source,output)
                if not profile_lifecycle(descriptor,lifecycle,placement):
                    deferred.append(dict(source_item_id=donor,reason=
                        'Shared room movement sounds remain incomplete' if lifecycle.get('category')=='contact-floor-alpha'
                        else 'Native start-disabled placement remains incomplete'))
                    continue
            if category==JOINT_CATEGORY:
                initial=joints.lifecycle(source,descriptor)
                if initial is None:raise ValueError('Joint-rig native lifecycle remains incomplete')
                if initial.get('parent_required'):
                    from v3_furniture_needle import native_contract as needle_contract
                    if runtime.get('needle_contract')!=needle_contract(base,prior):
                        raise ValueError('Missing complete needle carrying binding')
                if initial['start_disabled'] and placement is None:
                    placement,owner_changes,updates=install_initial_switch(base,prior,blob,source,output)
                if not joints.profile_lifecycle(descriptor,initial,placement):
                    raise ValueError('Missing complete joint-rig fresh-placement binding')
                if initial['source_sound_id'] is not None and contracts.get(donor)!=initial:
                    raise ValueError('Joint rig needs its complete installed source loop/click audio')
            if category==roofs.CATEGORY:
                initial=roofs.lifecycle(descriptor)
                if runtime.get('roof_contract')!=roofs.native_contract(source,base):
                    raise ValueError('Missing complete native house-colour selection')
            index,destination=furniture_identity(item);i=slot(destination)
            if index!=1024+i:
                raise ValueError('Parent/display aliases require their shared parent adapter')
            if any(identities[item][1].get(k)!='-' for k in ('C','H','CG','CJ')):
                raise ValueError('Staged identity needs native correspondence review')
            if (any(blob[ROWS+i*80:ROWS+(i+1)*80]) or any(blob[ITEMS+i*32:ITEMS+(i+1)*32]) or
                    blob[0x40+i//8]&(1<<(i&7))):raise ValueError('Profile staging overwrites an existing or selected identity')
            if category==static.CATEGORY:
                adapter=descriptor['callback_adapter']
                installed=copy.deepcopy(sounds[donor]) if adapter['mode'] in (1,4) else dict(
                    source_item_id=donor,item_id=f'{destination:04X}',runtime_index=index,
                    profile_installed=False,parent_selectable=False)
                installed.update(mode=adapter['mode'],parameter=adapter['parameter'])
                if adapter['mode']==3:installed['native_sound_word']=adapter['level_sound']['source_sound_id']
                static.checked_audio(descriptor,installed,result)
                blob.extend(bytes(-len(blob)%16));vrom=BLOB+len(blob);blob.extend(data)
                if vrom+len(data)>limit:raise ValueError('Complete static models exceed checked import reservation')
                vtable=SOUND_VTABLE;reused_asset=False
                installed.update(blob_offset=vrom-BLOB,vrom=vrom,bytes=len(data),sha256=sha256(data),source=row)
                runtime.setdefault('static_rows',[]).append(installed)
                runtime['static_rows'].sort(key=lambda r:r['runtime_index'])
                runtime.setdefault('static',{})['native']=static.native_contract(base)
                if adapter['mode'] in (1,4):sounds[donor]['profile_installed']=True
                material_code_changed=True
            elif category==SCROLL_CATEGORY:
                installed=scrolling.get(donor)
                if (not installed or installed['profile_installed'] or
                        {k:v for k,v in installed['source'].items() if k!='reused_artwork'}!=
                        {k:v for k,v in row.items() if k!='reused_artwork'} or
                        installed['bytes']!=len(data) or installed['sha256']!=sha256(data)):
                    raise ValueError('Prepared scrolling resource is not completely installed')
                vrom=installed['vrom'];vtable=SCROLL_VTABLE;reused_asset=True
                installed.update(lifecycle_installed=True,lifecycle=json.loads(json.dumps(lifecycle)))
            elif category in (CLOCK_CATEGORY,STORAGE_CATEGORY,HIT_CATEGORY,BILLBOARD_CATEGORY,ROLLING_CATEGORY,JOINT_CATEGORY,MATERIAL_RIG_CATEGORY,roofs.CATEGORY):
                installed=rigs.get(donor)
                if (not installed or installed['profile_installed'] or
                        {k:v for k,v in installed['source'].items() if k!='reused_artwork'}!=
                        {k:v for k,v in row.items() if k!='reused_artwork'} or
                        installed['bytes']!=len(data) or installed['sha256']!=sha256(data) or
                        blob[installed['blob_offset']:installed['blob_offset']+len(data)]!=data):
                    raise ValueError('Prepared rig is not completely installed in the current runtime')
                vrom=installed['vrom'];vtable=VTABLE;reused_asset=True
                if category in (BILLBOARD_CATEGORY,MATERIAL_RIG_CATEGORY) and contracts.get(donor)!=descriptor['callback_adapter']['level_sound']:
                    raise ValueError('Animated material rig needs its complete installed source loop audio')
                if category==HIT_CATEGORY:
                    audio=result.get('furniture_audio',{})
                    audio_row=next((r for r in audio.get('furniture',[]) if r['item_id']==donor),None)
                    sound=sounds.get(donor);trigger=furniture_trigger(source,descriptor)
                    if (not audio_row or audio_row['callback']!=json.loads(json.dumps(descriptor['callback_adapter'])) or
                            not sound or sound['source_sound_word']!=trigger['sound_word'] or
                            not all(audio.get(k) for k in ('runtime_installed','dispatch_and_priority_installed',
                                'allocation_installed','callback_installed'))):
                        raise ValueError('Hit rig needs its complete installed source audio')
                    checked_hit_condition(base,prior,trigger,sound,audio)
                    sound['profile_installed']=True
            elif category==MATERIAL_CATEGORY and initial:
                installed=materials[donor]
                if switched:checked_switched(source,descriptor,installed,contracts,placement)
                elif steam:checked_steam(source,descriptor,installed,contracts,runtime.get('effects',{}))
                elif colour:reactions.checked_colour_lifecycle(source,descriptor,installed,contracts)
                elif reaction:reactions.checked_lifecycle(source,descriptor,installed)
                else:checked_initializer(source,descriptor,installed)
                if (installed['profile_installed'] or
                        {k:v for k,v in installed['source'].items() if k!='reused_artwork'}!=
                        {k:v for k,v in row.items() if k!='reused_artwork'} or
                        installed['bytes']!=len(data) or installed['sha256']!=sha256(data) or
                        blob[installed['blob_offset']:installed['blob_offset']+len(data)]!=data):
                    raise ValueError('Material initializer lacks its complete installed renderer/assets')
                vrom=installed['vrom'];vtable=MATERIAL_VTABLE;reused_asset=True
            else:
                installed=sounds.get(donor);audio=result.get('furniture_audio',{})
                audio_row=next((r for r in audio.get('furniture',[]) if r['item_id']==donor),None)
                if (not installed or installed['profile_installed'] or not audio_row or
                        audio_row['callback']!=json.loads(json.dumps(descriptor['callback_adapter'])) or
                        not all(audio.get(k) for k in ('runtime_installed','dispatch_and_priority_installed',
                            'allocation_installed','callback_installed'))):
                    raise ValueError('Sound furniture lacks its complete installed audio/callback')
                if category==MATERIAL_CATEGORY:
                    installed=materials[donor]
                    trigger=furniture_trigger(source,descriptor)
                    if (trigger is None or installed.get('move_category')!='switch-trigger-sound' or
                            installed['profile_installed'] or
                            {k:v for k,v in installed['source'].items() if k!='reused_artwork'}!=
                            {k:v for k,v in row.items() if k!='reused_artwork'} or
                            installed['bytes']!=len(data) or installed['sha256']!=sha256(data) or
                            blob[installed['blob_offset']:installed['blob_offset']+len(data)]!=data or
                            sounds[donor]['source_sound_word']!=trigger['sound_word']):
                        raise ValueError('Material profile lacks its complete drawing/trigger lifecycle')
                    vrom=installed['vrom'];vtable=MATERIAL_VTABLE;reused_asset=True
                    sounds[donor]['profile_installed']=True
                else:
                    blob.extend(bytes(-len(blob)%16));vrom=BLOB+len(blob);blob.extend(data)
                    if vrom+len(data)>limit:raise ValueError('Complete sound models exceed checked import reservation')
                    vtable=SOUND_VTABLE;reused_asset=False
                installed.update(blob_offset=vrom-BLOB,vrom=vrom,bytes=len(data),sha256=sha256(data),source=row)
            generated=copy.deepcopy(row);generated['room_runtime']=dict(vtable=vtable,vrom=vrom)
            if initial:generated['room_lifecycle']=initial
            if switched:generated['room_placement']=placement
            if category==JOINT_CATEGORY and initial['start_disabled']:generated['room_placement']=placement
            if category==SCROLL_CATEGORY:generated['room_lifecycle']=lifecycle
            if category==SCROLL_CATEGORY and lifecycle.get('start_disabled'):generated['room_placement']=placement
            native=profile(generated,vrom,limit=limit)
            if len(native)!=68:raise ValueError('Incomplete ordinary furniture profile')
            names=name_metadata(source,item,identities[item])
            if destination!=item:
                names.update(item_id=f'{destination:04X}',runtime_index=index,donor_item_id=donor,
                             donor_runtime_index=furniture_source_index(item))
            price=struct.unpack_from('>H',source.raw('ftr_price_table'),furniture_source_index(item)*2)[0]
            record=struct.pack('>HHHBB',index,destination,price,descriptor['size_code'],0)+names['name'].encode().ljust(16,b' ')+bytes(8)
            profile_record=struct.pack('>HHI',index,destination,0)+native+bytes(4)
            blob[ROWS+i*80:ROWS+(i+1)*80]=profile_record
            blob[ITEMS+i*32:ITEMS+(i+1)*32]=record
            installed.update(profile_installed=True,parent_selectable=False)
            staged.append(dict(**names,category=category,price=price,size_code=descriptor['size_code'],
                object_vrom=vrom,object_bytes=len(data),object_sha256=sha256(data),reused_asset=reused_asset,
                profile_ram=ROWS_RAM+i*80+8,profile_hex=native.hex(),profile_record_sha256=sha256(profile_record),
                item_record_sha256=sha256(record),source_profile_sha256=descriptor['profile_sha256'],
                room_runtime=generated['room_runtime'],profile_installed=True,item_record_installed=True,
                **({'room_lifecycle':initial} if initial else {}),
                **({'room_placement':placement} if generated.get('room_placement') else {}),
                selected=False,acquisition_installed=False,catalogue_installed=False,scoring_installed=False))
    if not staged:raise ValueError('Empty complete furniture profile batch')
    if material_code_changed:publish_packet(result,blob,output,core=core)
    if runtime.get('colours') and not prior['equipment_resources']['room_rigs'].get('colours'):
        changed=reactions.install_colour_hooks(base,result)
        if set(changed)&set(owner_changes):raise ValueError('Overlapping native colour owner changes')
        owner_changes.update(changed)
    old['rows']=sorted(old['rows']+staged,key=lambda r:r['runtime_index']);old['sources'].extend(evidence)
    old.update(profile_bits_changed=False,additional_resident_bytes=
        (1024 if runtime.get('reactions') and not prior['equipment_resources']['room_rigs'].get('reactions') else 0)+
        (256 if runtime.get('colours') and not prior['equipment_resources']['room_rigs'].get('colours') else 0))
    if deferred or old.get('deferred_resources'):
        combined={r['source_item_id']:r for r in old.get('deferred_resources',[])+deferred}
        for donor in set(retained)|{f'{furniture_source(row)[0]:04X}' for row in old['rows']}:
            combined.pop(donor,None)
        old['deferred_resources']=sorted(combined.values(),key=lambda r:r['source_item_id'])
    patch=provenance_patch(staged)
    if patch:write_new(output/'provenance.patch',patch.encode())
    return result,owner_changes,dict(staged_furniture=old,**updates)


def bind_profiles(source,base,report):
    """Expose checked installed lifecycles to the ordinary category importer.

    Staged records remain inactive. This removes only the lifecycle prerequisite;
    normal acquisition, catalogue, scoring, and selection checks still apply.
    """
    from v3_furniture_install import profile
    from v3_furniture_capacity import checked as checked_model_capacity
    source.model_bank_capacity=checked_model_capacity(base,report)
    from v3_furniture_materials import (CATEGORY as MATERIAL_CATEGORY,initializer_lifecycle,checked_initializer,
        steam_lifecycle,checked_steam,switched_lifecycle,checked_switched)
    import v3_furniture_reactions as reactions
    from v3_furniture_scroll import CATEGORY as SCROLL_CATEGORY,VTABLE as SCROLL_VTABLE,checked_lifecycle,checked_runtime
    from v3_sound_programs import furniture_trigger,checked_furniture_loops
    from v3_furniture_behaviours import checked_initial_switch,initial_switch_source
    import v3_furniture_static as static
    source.runtime_profiles={}
    staged=report.get('staged_furniture',{})
    activated=[r for r in report['furniture']['imports'] if r.get('room_runtime')]
    if not staged and not activated:return source.runtime_profiles
    if staged and staged['format']!='AFV3-STAGED-FURNITURE-PROFILES-1':
        raise ValueError('Unknown staged furniture profile format')
    blob=by_vrom(base)[BLOB].extract(base);e=report['equipment_resources'];runtime=e['room_rigs']
    packet=runtime['packet'];raw=blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']]
    packet_ram,table_ram,_=packet_layout(runtime)
    module=blob[e['blob_offset']:e['blob_offset']+e['bytes']]
    if (sha256(blob)!=report['blob_sha256'] or sha256(raw)!=packet['sha256'] or
            sha256(module)!=e['sha256'] or raw[table_ram-packet_ram:]!=encode_packet(runtime['rows'],runtime['sound_rows'],runtime.get('material_rows',[])) or
            module[VTABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM+20].hex()!=runtime['vtable_hex'] or
            module[SOUND_VTABLE-EQUIPMENT_RAM:SOUND_VTABLE-EQUIPMENT_RAM+20].hex()!=runtime['sound_vtable_hex'] or
            blob[0x20:0xE0].hex()!=report['save_runtime']['profile_hex']):
        raise ValueError('Changed installed furniture lifecycle, packet, or selection')
    if runtime.get('material_rows') and module[MATERIAL_VTABLE-EQUIPMENT_RAM:MATERIAL_VTABLE-EQUIPMENT_RAM+20].hex()!=runtime['material_vtable_hex']:
        raise ValueError('Changed installed material draw dispatch')
    reaction_runtime=reactions.checked_binding(source,base,report)
    colour_runtime=reactions.checked_colours(base,report)
    limit=checked_limit(base,report)
    # A rig's audio dependency has its own sound row; retain the complete model
    # binding when an identity occurs in both tables.
    bindings={r['source_item_id']:r for r in runtime['sound_rows']+runtime['rows']+runtime.get('material_rows',[])}
    bindings.update(checked_runtime(e,blob))
    bindings.update(static.checked_binding(base,report,blob))
    if e.get('furniture_melody_audio'):
        from v3_furniture_melody import checked_binding as checked_melodies
        checked_melodies(base,report)
    placement=checked_initial_switch(base,report,blob)
    if placement and report['furniture_initial_switch']['source']!=json.loads(json.dumps(initial_switch_source(source))):
        raise ValueError('Changed source fresh-placement contract')
    contracts,_=checked_furniture_loops(base,by_vrom(base)[CODE_VROM].extract(base),e,source) if e.get('furniture_level_audio') else ({},{})
    from v3_furniture_contact import checked_contracts
    contracts.update(checked_contracts(source,base,report))
    if any(r.get('mode')==4 for r in runtime['rows']):
        if runtime.get('billboard_contract')!=billboard_contract(base,report):
            raise ValueError('Changed installed billboard helper bindings')
    if any(r.get('mode')==5 for r in runtime['rows']):
        if runtime.get('motion_contract')!=motion_binding(source,base,report,runtime['rows']):
            raise ValueError('Changed installed rolling motion bindings')
    if any(r.get('mode')==6 for r in runtime['rows']):
        if runtime.get('joint_contract')!=joints.native_contract(base):
            raise ValueError('Changed installed joint-rig native bindings')
    if any(r.get('mode')==6 and r.get('first')==4 for r in runtime['rows']):
        from v3_furniture_needle import native_contract as needle_contract
        if runtime.get('needle_contract')!=needle_contract(base,report):
            raise ValueError('Changed installed needle carrying bindings')
    if any(r.get('mode')==7 for r in runtime['rows']):
        if runtime.get('roof_contract')!=roofs.native_contract(source,base):
            raise ValueError('Changed installed house-colour selection')
    for row,enabled in [(r,False) for r in staged.get('rows',[])]+[(r,True) for r in activated]:
        item=int(row['item_id'],16);donor=f'{furniture_source(row)[0]:04X}';i=slot(item);binding=bindings.get(donor)
        if (donor in source.runtime_profiles or not binding or not binding['profile_installed'] or
                row['runtime_index']!=1024+i or binding['runtime_index']!=1024+i or
                bool(blob[0x40+i//8]&(1<<(i&7)))!=enabled):
            raise ValueError('Changed furniture profile identity or activation')
        descriptor=prepare(source,int(donor,16))[0];art=copy.deepcopy(binding['source']);vrom=binding['vrom']
        category=descriptor['callback_adapter']['category']
        expected_vtable=(MATERIAL_VTABLE if category==MATERIAL_CATEGORY else SOUND_VTABLE if category in ('switch-trigger-sound',static.CATEGORY)
                         else SCROLL_VTABLE if category==SCROLL_CATEGORY else VTABLE)
        if category==static.CATEGORY:static.checked_audio(descriptor,binding,e)
        if category==roofs.CATEGORY:
            lifecycle=roofs.lifecycle(descriptor)
            if binding.get('roof_lifecycle')!=lifecycle:
                raise ValueError('Incomplete installed roof-palette lifecycle')
            art['room_lifecycle']=lifecycle
        if category==JOINT_CATEGORY:
            joint_lifecycle=joints.lifecycle(source,descriptor)
            if (joint_lifecycle is None or binding.get('joint_lifecycle')!=json.loads(json.dumps(joint_lifecycle)) or
                    joint_lifecycle['source_sound_id'] is not None and contracts.get(donor)!=joint_lifecycle):
                raise ValueError('Incomplete installed joint lifecycle/audio')
            art['room_lifecycle']=joint_lifecycle
            if joint_lifecycle['start_disabled']:art['room_placement']=placement
        if category==SCROLL_CATEGORY:
            lifecycle=checked_lifecycle(source,descriptor,binding,runtime['scrolling'],contracts)
            if lifecycle is None:
                raise ValueError('Incomplete installed scrolling lifecycle')
            art['room_lifecycle']=lifecycle
            if lifecycle.get('start_disabled'):art['room_placement']=placement
        if category==MATERIAL_CATEGORY and initializer_lifecycle(source,descriptor):
            art['room_lifecycle']=checked_initializer(source,descriptor,binding)
            ct=int.from_bytes(bytes.fromhex(runtime['material_vtable_hex'])[:4],'big')
            if ct!=runtime['bootstrap']['symbols']['af_v3_room_boot_ct']:
                raise ValueError('Missing native material constructor dispatch')
        elif category==MATERIAL_CATEGORY and reactions.source_lifecycle(source,descriptor):
            if reaction_runtime is None:
                raise ValueError('Timed material lacks its complete controller/runtime integration')
            art['room_lifecycle']=reactions.checked_lifecycle(source,descriptor,binding)
            callbacks=struct.unpack('>5I',bytes.fromhex(runtime['material_vtable_hex']))
            symbols=runtime['bootstrap']['symbols']
            if callbacks[:2]!=(symbols['af_v3_room_boot_ct'],symbols['af_v3_room_boot_sound_mv']):
                raise ValueError('Missing complete timed-material lifecycle dispatch')
        elif category==MATERIAL_CATEGORY and reactions.colour_lifecycle(source,descriptor):
            if colour_runtime is None:raise ValueError('Material lacks native player-colour integration')
            art['room_lifecycle']=reactions.checked_colour_lifecycle(source,descriptor,binding,contracts)
            callbacks=struct.unpack('>5I',bytes.fromhex(runtime['material_vtable_hex']))
            symbols=runtime['bootstrap']['symbols']
            if callbacks[:2]!=(symbols['af_v3_room_boot_ct'],symbols['af_v3_room_boot_sound_mv']):
                raise ValueError('Missing complete player-colour material dispatch')
        elif category==MATERIAL_CATEGORY and steam_lifecycle(source,descriptor):
            art['room_lifecycle']=checked_steam(source,descriptor,binding,contracts,runtime.get('effects',{}))
            callbacks=struct.unpack('>5I',bytes.fromhex(runtime['material_vtable_hex']))
            if callbacks[1]!=runtime['bootstrap']['symbols']['af_v3_room_boot_sound_mv']:
                raise ValueError('Missing periodic material movement dispatch')
        elif category==MATERIAL_CATEGORY and switched_lifecycle(source,descriptor):
            art['room_lifecycle']=checked_switched(source,descriptor,binding,contracts,placement)
            art['room_placement']=placement
            callbacks=struct.unpack('>5I',bytes.fromhex(runtime['material_vtable_hex']))
            if callbacks[1]!=runtime['bootstrap']['symbols']['af_v3_room_boot_sound_mv']:
                raise ValueError('Missing switched material movement dispatch')
        elif category==MATERIAL_CATEGORY:
            trigger=furniture_trigger(source,descriptor)
            sound=next((r for r in runtime['sound_rows'] if r['source_item_id']==donor),None)
            if (not binding.get('lifecycle_installed') or binding.get('move_category')!='switch-trigger-sound' or
                    trigger is None or sound is None or not sound['profile_installed'] or
                    sound['source_sound_word']!=trigger['sound_word']):
                raise ValueError('Incomplete installed material/trigger lifecycle')
        if category==HIT_CATEGORY:
            trigger=furniture_trigger(source,descriptor)
            sound=next((r for r in runtime['sound_rows'] if r['source_item_id']==donor),None)
            audio=next((r for r in e.get('furniture_audio',{}).get('furniture',[]) if r['item_id']==donor),None)
            if (sound is None or not sound['profile_installed'] or not audio or
                    sound['source_sound_word']!=trigger['sound_word'] or
                    audio['callback']!=json.loads(json.dumps(descriptor['callback_adapter']))):
                raise ValueError('Incomplete installed hit-rig audio/behaviour')
            checked_hit_condition(base,report,trigger,sound,e['furniture_audio'])
        if category in (BILLBOARD_CATEGORY,MATERIAL_RIG_CATEGORY) and contracts.get(donor)!=descriptor['callback_adapter']['level_sound']:
            raise ValueError('Incomplete installed animated-material audio/behaviour')
        if category==MATERIAL_RIG_CATEGORY:
            parameters=art['rig'];offset=parameters['material_offset']
            if (binding.get('mode')!=8 or binding.get('first')!=0x06000000+offset or binding.get('last') or
                    blob[vrom-BLOB+offset:vrom-BLOB+offset+32].hex()!=parameters['material_hex'] or
                    '-DAF_V3_ROOM_MATERIAL_RIG' not in runtime['code']['flags']):
                raise ValueError('Incomplete installed rig material selector or dispatch')
        art['room_runtime']=dict(vtable=expected_vtable,vrom=vrom)
        at=vrom-BLOB;n=art['object_bytes'];native=profile(art,vrom,limit=limit)
        current=blob[ROWS+i*80:ROWS+(i+1)*80];record=blob[ITEMS+i*32:ITEMS+(i+1)*32]
        expected=struct.pack('>HHI',1024+i,item,int(enabled))+native+bytes(4)
        if (art['profile']!=json.loads(json.dumps(descriptor)) or row['room_runtime']!=art['room_runtime'] or
                category in (MATERIAL_CATEGORY,JOINT_CATEGORY,roofs.CATEGORY) and row.get('room_lifecycle')!=json.loads(json.dumps(art.get('room_lifecycle'))) or
                row.get('room_placement')!=art.get('room_placement') or
                not 0<=at<at+n<=len(blob) or sha256(blob[at:at+n])!=art['object_sha256'] or
                current!=expected or record[:8]!=struct.pack('>HHHBB',1024+i,item,row['price'],descriptor['size_code'],int(enabled)) or
                record[8:24]!=row['name'].encode().ljust(16,b' ') or
                sha256(record)!=row['record_sha256' if enabled else 'item_record_sha256'] or
                not enabled and (sha256(current)!=row['profile_record_sha256'] or row['selected'])):
            raise ValueError('Changed complete installed furniture profile, artwork, or item record')
        source.runtime_profiles[donor]=dict(room_runtime=art['room_runtime'],
            source_profile_sha256=descriptor['profile_sha256'],category=descriptor['callback_adapter']['category'],
            object_sha256=art['object_sha256'],object_bytes=n,profile_hex=native.hex(),staged=not enabled,
            **({k:art[k] for k in ('room_lifecycle','room_placement') if k in art}))
    return source.runtime_profiles


def reuse_profile(source,row,asset,blob,*,limit):
    """Promote a checked inactive record without duplicating its complete model."""
    from v3_furniture_install import profile
    binding=getattr(source,'runtime_profiles',{}).get(f'{furniture_source(row)[0]:04X}')
    if binding is None:return None
    i=slot(int(row['item_id'],16));vrom=binding['room_runtime']['vrom'];at=vrom-BLOB
    native=profile(row,vrom,limit=limit)
    if (not binding['staged'] or row.get('room_runtime')!=binding['room_runtime'] or
            len(asset)!=binding['object_bytes'] or sha256(asset)!=binding['object_sha256'] or
            blob[at:at+len(asset)]!=asset or native.hex()!=binding['profile_hex'] or
            blob[ROWS+i*80:ROWS+(i+1)*80]!=struct.pack('>HHI',row['runtime_index'],int(row['item_id'],16),0)+native+bytes(4) or
            blob[ITEMS+i*32:ITEMS+(i+1)*32]!=struct.pack('>HHHBB',row['runtime_index'],int(row['item_id'],16),row['price'],row['size_code'],0)+row['name'].encode().ljust(16,b' ')+bytes(8)):
        raise ValueError('Changed staged record or model during ordinary furniture promotion')
    return vrom,native


def prepared_categories(source,directories):
    """Use the normal complete-art cache for all implemented room rig categories."""
    rows=[];assets={};evidence=[]
    for directory in directories:
        directory=directory.resolve()
        if not directory.is_relative_to(ROOT/'build'):raise ValueError('Room rigs require ignored prepared assets')
        cache=PreparedAssets(source,[directory]);raw=(directory/'art.json').read_bytes();art=json.loads(raw)
        if art['format']!='AFV3-AUTO-FURNITURE-PREPARED-ASSETS-1':raise ValueError('Expected complete prepared room rigs')
        for row in art['objects']:
            donor=row['item_id'];item=int(donor,16);prepared_row=prepare(source,item)
            profile=prepared_row[0];adapter=profile.get('callback_adapter',{});category=adapter.get('category')
            if category not in (CLOCK_CATEGORY,STORAGE_CATEGORY,HIT_CATEGORY,BILLBOARD_CATEGORY,ROLLING_CATEGORY,JOINT_CATEGORY,MATERIAL_RIG_CATEGORY,roofs.CATEGORY):
                raise ValueError('Unimplemented additional room-rig category')
            if (row['profile']!=json.loads(json.dumps(profile)) or donor in assets or
                    row['native_profile_scalar_hex']!=profile['scalar_hex'] or
                    category!=roofs.CATEGORY and (profile['skeleton']['joints']>(6 if category==ROLLING_CATEGORY else 8) or
                    category not in (BILLBOARD_CATEGORY,JOINT_CATEGORY) and
                    any(r.get('draw_stream') for r in profile['skeleton']['rows']))):
                raise ValueError('Changed room-rig profile or native work capacity')
            cache.reuse(source,donor,prepared_row)
            data=(directory/row['object_file']).read_bytes()
            if len(data)>9216:raise ValueError('Complete rig exceeds room bank')
            index,destination=furniture_representation_identity(item)
            if category==roofs.CATEGORY:
                rows.append(dict(source_item_id=donor,item_id=f'{destination:04X}',runtime_index=index,
                    bytes=len(data),sha256=sha256(data),category=category,mode=7,first=12,last=0,
                    skeleton=0,animation=0,joints=0,shown=0,source=row,
                    roof_lifecycle=roofs.lifecycle(profile),profile_installed=False,parent_selectable=False))
                assets[donor]=data
                continue
            rig=row['rig']
            if category==CLOCK_CATEGORY:
                mode=1;first=adapter['clock']['hour_joint'];last=adapter['clock']['minute_joint']
            elif category==STORAGE_CATEGORY:
                mode=2;first=int(adapter['constants']['start_frame']['hex'],16)
                last=int(adapter['constants']['end_frame']['hex'],16)
            elif category==HIT_CATEGORY:
                mode=3;hit=adapter.get('hit')
                first=2 if hit and hit.get('endpoint_only') else 1 if hit else 0
                last=struct.unpack('>I',struct.pack('>f',hit['playback_speed']))[0] if hit else 0
                if hit and hit not in (dict(idle_only=True,playback_speed=.25,stop_at_endpoint=True,clear_initial_pulse=False),
                                      dict(endpoint_only=True,playback_speed=.5,clear_initial_pulse=False)):
                    raise ValueError('Unknown complete stopped-hit policy')
            elif category==BILLBOARD_CATEGORY:
                mode=4;first=0x06000000+rig['billboard_offset'];last=0
            elif category==ROLLING_CATEGORY:
                mode=5;first=struct.unpack('>I',struct.pack('>f',adapter['rolling']['duration']))[0];last=0
            elif category==MATERIAL_RIG_CATEGORY:
                mode=8;first=0x06000000+rig['material_offset'];last=0
            else:
                lifecycle=joints.lifecycle(source,profile)
                if lifecycle is None:raise ValueError('Unimplemented complete joint-rig lifecycle')
                mode=6;first=lifecycle['mode'];last=0
                if lifecycle['source_sound_id'] is not None:
                    first|=lifecycle['source_sound_id']<<8
                    on,off=lifecycle['switch_clicks'];last=on<<16|off
            rows.append(dict(source_item_id=donor,item_id=f'{destination:04X}',runtime_index=index,
                bytes=len(data),sha256=sha256(data),category=category,mode=mode,first=first,last=last,
                skeleton=0x06000000+rig['skeleton_offset'],animation=0x06000000+rig['animation_offset'],
                joints=rig['skeleton']['joints'],shown=rig['skeleton']['shown_joints'],source=row,
                profile_installed=False,parent_selectable=False,
                **({'joint_lifecycle':json.loads(json.dumps(lifecycle))} if category==JOINT_CATEGORY else {})))
            assets[donor]=data
        evidence.append(dict(directory=str(directory.relative_to(ROOT)),sha256=sha256(raw),
                             source_rel_sha256=sha256(source.rel)))
    if not rows:raise ValueError('Empty additional room-rig batch')
    return sorted(rows,key=lambda r:r['runtime_index']),assets,evidence


def encode_materials(rows):
    if (not rows or len(rows)>MATERIAL_CAPACITY or
            [r['runtime_index'] for r in rows]!=sorted({r['runtime_index'] for r in rows})):
        raise ValueError('Unordered, duplicate, or excessive material records')
    table=bytearray(struct.pack('>4I',MATERIAL_MAGIC,len(rows),40,0))
    for r in rows:
        index,n,mode,segment=r['runtime_index'],r['bytes'],r['mode'],r['segment']
        frames,models=r['frame_offsets'],r['model_offsets'];size=r['frame_bytes']
        divisor,state,kind=r['divisor'],r['state_offset'],r['kind'];lifecycle=r.get('lifecycle',0)
        if (not 1024<=index<2048 or not 32<=n<=9216 or n&15 or mode not in (0,1,2,3) or
                segment not in (8,9) or not 1<=len(frames)<=8 or not 1<=len(models)<=4 or
                kind not in (0,1) or not 0<size<=n or kind==0 and size!=32 or
                mode==2 and (state!=0x1A4 or len(frames)!=2 or divisor) or
                lifecycle not in (0,1,2,3,4,5) or lifecycle==1 and mode!=0 or lifecycle==2 and mode!=2 or
                lifecycle in (3,4) and (mode!=(1 if lifecycle==3 else 0) or not 0<=state<=127) or
                lifecycle==5 and (mode!=3 or not 0<=state<=127) or
                mode!=2 and (lifecycle not in (3,4,5) and state!=(0x1A4 if lifecycle else 0) or not 0<divisor<=65535) or
                mode==1 and (len(frames)!=4 or divisor!=10) or
                mode==3 and (len(frames)!=5 or divisor!=6 or kind!=1 or lifecycle not in (0,5)) or
                any(p&7 or not 0<=p<=n-size for p in frames) or
                any(p&7 or not 0<=p<=n-8 for p in models)):
            raise ValueError('Invalid complete material selector, resources, or native bounds')
        table.extend(struct.pack('>HH4B2H4H8HH2B',index,n,mode,segment,len(frames),len(models),divisor,size,
            *(models+[0]*(4-len(models))),*(frames+[0]*(8-len(frames))),state,kind,lifecycle))
    return bytes(table)


def encode_packet(rows,sound_rows=(),material_rows=()):
    if not rows or len(rows)>PACKET_CAPACITY:raise ValueError('Room-rig packet capacity exceeded')
    if [r['runtime_index'] for r in rows]!=sorted({r['runtime_index'] for r in rows}):
        raise ValueError('Unordered or duplicate room-rig records')
    table=bytearray(struct.pack('>4I',PACKET_MAGIC,len(rows),24,0))
    for r in rows:
        if r.get('mode')==7:
            if (r['runtime_index']!=1024+slot(int(r['item_id'],16)) or not 800<=r['bytes']<=9216 or
                    r['bytes']%16 or any(r[k] for k in ('skeleton','animation','joints','shown','last')) or r['first']!=12):
                raise ValueError('Invalid complete selected-palette record')
            table.extend(struct.pack('>HHIIBBBBII',r['runtime_index'],r['bytes'],0,0,0,0,7,0,12,0))
            continue
        encode([r])  # Retain the complete existing object/pointer/work-area checks.
        mode,first,last=r.get('mode',0),r.get('first',0),r.get('last',0)
        if (mode not in (0,1,2,3,4,5,6,8) or mode==0 and (first or last) or
                mode==6 and (first,last) not in ((1,0),(2,0),(4,0),(0x5103,0x00160017)) or
                mode==3 and (first,last) not in ((0,0),(1,0x3E800000),(2,0x3F000000)) or
                mode==1 and not (0<first<r['joints'] and 0<last<r['joints'] and first!=last) or
                mode==4 and (last or first&3 or not 0x06000000<=first<=0x06000000+r['bytes']-16) or
                mode==8 and (last or first&3 or not 0x06000000<=first<=0x06000000+r['bytes']-32) or
                mode==5 and (last or not 0x3F800000<=first<=0x47000000) or
                mode==2 and not 0x3F800000<=first<last<=0x43800000):
            raise ValueError('Invalid complete room-rig behaviour parameters')
        table.extend(struct.pack('>HHIIBBBBII',r['runtime_index'],r['bytes'],r['skeleton'],r['animation'],
                                 r['joints'],r['shown'],mode,0,first,last))
    if sound_rows:
        if (len(sound_rows)>SOUND_CAPACITY or
                [r['runtime_index'] for r in sound_rows]!=sorted({r['runtime_index'] for r in sound_rows})):
            raise ValueError('Unordered, duplicate, or excessive room-sound records')
        table.extend(bytes(SOUND_TABLE-PACKET_TABLE-len(table)))
        table.extend(struct.pack('>4I',SOUND_MAGIC,len(sound_rows),8,0))
        for r in sound_rows:
            word=r['native_sound_word']
            if (not 1024<=r['runtime_index']<2048 or not 0<=word<=65535 or
                    word&0x80 or (word&0x7FFF)>>8 not in (0,1,4)):
                raise ValueError('Invalid room sound identity or full native sound word')
            conditional=r.get('conditional')
            extra=0
            if conditional:
                if (conditional['wall']!=76 or conditional['effect']!=112 or
                        conditional['native_system_word']&0xFF80!=0x8100):
                    raise ValueError('Unbound room sound/effect condition')
                extra=conditional['wall']<<24|conditional['effect']<<16|conditional['native_system_word']
            table.extend(struct.pack('>HHI',r['runtime_index'],word,extra))
    if material_rows:
        table.extend(bytes(MATERIAL_TABLE-PACKET_TABLE-len(table)))
        table.extend(encode_materials(material_rows))
    if len(table)>PACKET_BYTES-(PACKET_TABLE-PACKET_RAM):raise ValueError('Shared room table exceeds packet')
    return bytes(table).ljust(PACKET_BYTES-(PACKET_TABLE-PACKET_RAM),b'\0')


def extended_contract(base,core,original):
    """Native storage owns its existing state machine, audio, and room interaction."""
    current=by_vrom(base)[0x82D7F0].extract(base);native=by_vrom(original)[0x82D7F0].extract(original)
    a,b=0x8094630C-0x80936710,0x809465CC-0x80936710
    if sha256(native[a:b])!='3453821b77da92ff7456b8c495c9c9cbb2e6372ce303400bec0e2d08473fb37e':
        raise ValueError('Changed complete native storage state machine')
    expected=bytearray(native[a:b])
    # The installed shared profile table is the only change to the native helper.
    struct.pack_into('>I',expected,0x24,0x3C188047)
    struct.pack_into('>I',expected,0x30,0x8F180010)
    c,d=0x80939050-0x80936710,0x8093919C-0x80936710
    if (current[a:b]!=expected or current[c:d]!=native[c:d] or
            sha256(native[c:d])!='829a1b5c83b3284fe2e0174932f22be1ad56e184b4540017259fe6b229ed381a'):
        raise ValueError('Changed native room clip registration or storage profile binding')
    n=by_vrom(original)[CODE_VROM].extract(original);a,b=0x80052228-CODE_RAM,0x80053170-CODE_RAM
    if core[a:b]!=n[a:b]:raise ValueError('Changed native complete keyframe APIs')
    return dict(storage_owner_vrom=0x82D7F0,storage_helper=0x8094630C,
        storage_helper_sha256=sha256(expected),clip_registration_sha256=sha256(native[c:d]),
        room_clip=0x80136F2C,open_close_offset=0x34,hour=0x80136FC6,minute=0x80136FC4,
        keyframe_api_sha256=sha256(n[a:b]),native_storage_speed=1.0,source_storage_speed=0.5)


def billboard_contract(base,report):
    """Verify the retained native camera-facing helpers and their dependencies."""
    from v3_fire import ENGINE,RAM as FIRE_RAM
    from v3_import_storage import PACKAGE,PACKAGE_RAM
    files=by_vrom(base);blob=files[BLOB].extract(base);receipt=report['fire']['code']
    at=PACKAGE+FIRE_RAM-PACKAGE_RAM
    if (receipt['bytes']!=1240 or receipt['sha256']!='172bdb4e01ea1061c31bfec1c2017a8fa3eb253d790a1163eac1056c5413da9b' or
            sha256(blob[at:at+1240])!=receipt['sha256'] or receipt['symbols']['fire_before']!=0x80483810 or
            receipt['symbols']['fire_after']!=0x80483B00):
        raise ValueError('Changed complete installed camera-facing helpers')
    blocks=[]
    for name,address,n,digest in ENGINE:
        vrom,ram=(0x1060,0x80025C60) if name=='osWritebackDCache' else (CODE_VROM,CODE_RAM)
        data=files[vrom].extract(base)[address-ram:address-ram+n]
        if sha256(data)!=digest:raise ValueError('Changed native billboard dependency: '+name)
        blocks.append(dict(name=name,address=address,bytes=n,sha256=digest))
    return dict(code_sha256=receipt['sha256'],before=0x80483810,after=0x80483B00,blocks=blocks,
        actor_scale=0x714,billboard=0x1E5C,room_frame=0x1EA0,preview_frame=0xA0)


def publish_packet(equipment,blob,output,*,core=None):
    """Compile shared behaviour once and publish it through the stable room vtable."""
    runtime=equipment['room_rigs'];packet=runtime['packet'];at=packet['blob_offset']
    packet_ram,table_ram,packet_bytes=packet_layout(runtime)
    table_delta=table_ram-PACKET_TABLE
    sound_rows=runtime.get('sound_rows',[]);material_rows=runtime.get('material_rows',[])
    static_rows=runtime.get('static_rows',[]);static_sources=()
    if static_rows:
        from v3_furniture_static import table_source
        assembly,static_data=table_source(static_rows,output/'room_static_bank')
        static_sources=('overlays/v3/room_static.c',assembly)
    reactions=runtime.get('reactions');reaction_sources=();colours=runtime.get('colours')
    if reactions:
        from v3_furniture_reactions import wave_source
        if core is None or packet_ram not in (EXTENDED_RAM,WIDE_RAM) or not any(r.get('lifecycle')==2 for r in material_rows):
            raise ValueError('Reaction publication requires complete lifecycle, main code, and extended packet')
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        wave,_,receipt=wave_source(source,output/'room_reaction_bank')
        if reactions['bank']!=json.loads(json.dumps(receipt)):
            raise ValueError('Changed complete reaction wave source')
        reaction_sources=('overlays/v3/room_reactions.c','overlays/v3/room_rumble.c',wave)
    elif any(r.get('lifecycle')==2 for r in material_rows):
        raise ValueError('Timed material requires its complete reaction engine')
    if colours and (packet_ram not in (EXTENDED_RAM,WIDE_RAM) or not any(r.get('lifecycle')==3 for r in material_rows)):
        raise ValueError('Colour publication requires its complete lifecycle and extended packet')
    if not colours and any(r.get('lifecycle')==3 for r in material_rows):
        raise ValueError('Colour material requires its complete player engine')
    switched=any(r.get('lifecycle')==5 for r in material_rows)
    defines=('AF_V3_ROOM_RIG_PACKET',)+(('AF_V3_ROOM_TRIGGER_SOUND',) if sound_rows or reactions or colours or static_rows or switched else ())
    if switched:defines+=('AF_V3_ROOM_SWITCHED_MATERIAL',)
    if static_rows:defines+=('AF_V3_ROOM_STATIC',)
    if reactions:defines+=('AF_V3_ROOM_REACTIONS',)
    if colours:defines+=('AF_V3_ROOM_COLOURS',)
    if material_rows:defines+=('AF_V3_ROOM_MATERIALS',)
    billboard=any(r.get('mode')==4 for r in runtime['rows'])
    if billboard:defines+=('AF_V3_ROOM_BILLBOARD',)
    if any(r.get('mode')==8 for r in runtime['rows']):defines+=('AF_V3_ROOM_MATERIAL_RIG',)
    if any(r.get('mode')==5 for r in runtime['rows']):defines+=('AF_V3_ROOM_ROLLING',)
    joint=any(r.get('mode')==6 for r in runtime['rows'])
    if joint:defines+=('AF_V3_ROOM_JOINT',)
    roof=any(r.get('mode')==7 for r in runtime['rows'])
    if roof:
        if not runtime.get('roof_contract'):raise ValueError('Selected palettes require a checked native selector')
        defines+=('AF_V3_SELECTED_PALETTE','AF_V3_SHARED_PALETTE_FADE')
    needle=any(r.get('mode')==6 and r.get('first')==4 for r in runtime['rows'])
    if needle:
        from v3_room_carry_native import checked_packet
        carrying=checked_packet(equipment,blob)
        if any(runtime.get('needle_contract',{}).get('carrying',{}).get(k)!=v for k,v in carrying.items()):
            raise ValueError('Needle packet has no checked carrying contract')
        exports=carrying['exports']
        defines+=('AF_V3_ROOM_NEEDLE',f'AF_CARRY_PARENT=0x{exports["af_v3_carry_parent"]:X}u',
                  f'AF_CARRY_ANGLE=0x{exports["af_v3_carry_angle"]:X}u')
    effects=runtime.get('effects')
    particles=effects.get('particles') if effects else None
    if effects:
        if packet_ram not in (EXTENDED_RAM,WIDE_RAM):raise ValueError('Effect callbacks require the expanded room packet')
        defines+=('AF_V3_ROOM_EFFECTS',f'AF_EFFECT_FLASH_MODEL=0x{effects["bank"]["model"]:X}u')
    if particles:
        from v3_room_particles import runtime_defines
        defines+=runtime_defines(particles)
    defines+=(f'ROOM_RIG_TABLE_RAM=0x{table_ram:X}u',f'ROOM_SOUND_TABLE_RAM=0x{SOUND_TABLE+table_delta:X}u',
              f'ROOM_MATERIAL_TABLE_RAM=0x{MATERIAL_TABLE+table_delta:X}u')
    part={PACKET_RAM:'room_rigs_packet',EXTENDED_RAM:'room_rigs_extended',WIDE_RAM:'room_rigs_wide'}[packet_ram]
    code,compiled=compile_part(part,output/'room_rigs_packet',
        primary_source='overlays/v3/room_rigs.c',defines=defines,
        extra_sources=(('overlays/v3/room_materials.c',) if material_rows else ())+
            (('overlays/v3/room_billboards.c',) if billboard else ())+
            (('overlays/v3/room_joints.c',) if joint else ())+
            (('overlays/v3/room_needle.c',) if needle else ())+
            (('overlays/v3/room_palettes.c',) if roof else ())+
            (('overlays/v3/room_effects.c',) if effects else ())+reaction_sources+
            (('overlays/v3/room_particles.c',) if particles else ())+\
            (('overlays/v3/room_colours.c',) if colours else ())+static_sources)
    table=encode_packet(runtime['rows'],sound_rows,material_rows)
    data=code.ljust(table_ram-packet_ram,b'\0')+table
    if len(code)>table_ram-packet_ram or len(data)!=packet_bytes or not zlib.crc32(data):
        raise ValueError('Room code/table exceeds owned packet or has an invalid cache identity')
    symbols=compiled['symbols'];entries=[symbols['af_v3_room_rig_'+role] for role in ('ct','mv','dw')]
    if static_rows:
        address=symbols['af_v3_room_static_table'];start=address-packet_ram
        if start<0 or code[start:start+len(static_data)]!=static_data:
            raise ValueError('Static behaviour table escapes the immutable shared packet')
        runtime['static'].update(address=address,bytes=len(static_data),sha256=sha256(static_data))
    if any(p&3 or not packet_ram<=p<packet_ram+len(code) for p in entries):
        raise ValueError('Room lifecycle entry escapes packet')
    sound_defines=()
    if sound_rows or reactions or colours or static_rows:
        entry=symbols['af_v3_room_sound_mv']
        if entry&3 or not packet_ram<=entry<packet_ram+len(code):raise ValueError('Room sound entry escapes packet')
        sound_defines=(f'AF_ROOM_SOUND_MV=0x{entry:X}u',)
    material_defines=()
    if material_rows:
        entry=symbols['af_v3_room_material_dw']
        if entry&3 or not packet_ram<=entry<packet_ram+len(code):raise ValueError('Material entry escapes packet')
        material_defines=(f'AF_ROOM_MATERIAL_DW=0x{entry:X}u',)
    scroll_defines=()
    if runtime.get('scrolling'):
        from v3_furniture_scroll import publish as publish_scroll
        scroll_defines=publish_scroll(equipment,blob,output)
    boot,bootstrap=compile_part('room_rigs_bootstrap',output/'room_rigs_bootstrap',defines=(
        f'AF_ROOM_RAM=0x{packet_ram:X}u',f'AF_ROOM_VROM=0x{BLOB+at:X}u',f'AF_ROOM_BYTES={packet_bytes}u',f'AF_ROOM_CRC=0x{zlib.crc32(data):X}u',
        *(f'AF_ROOM_{role.upper()}=0x{entry:X}u' for role,entry in zip(('ct','mv','dw'),entries)),*sound_defines,*material_defines,*scroll_defines,
        *(('AF_ROOM_EFFECTS',) if effects else ()),*(('AF_ROOM_REACTIONS',) if reactions else ()),
        *(('AF_ROOM_COLOURS',) if colours else ())))
    start=equipment['blob_offset'];module=bytearray(blob[start:start+equipment['bytes']])
    if sha256(module)!=equipment['sha256']:raise ValueError('Changed installed equipment before room publication')
    entries=[bootstrap['symbols']['af_v3_room_boot_'+role] for role in ('ct','mv','dw')]
    if len(boot)>TABLE-RAM or any(p&3 or not RAM<=p<RAM+len(boot) for p in entries):
        raise ValueError('Room bootstrap escapes stable reservation')
    vtable=struct.pack('>5I',*entries,0,0)
    module[RAM-EQUIPMENT_RAM:TABLE-EQUIPMENT_RAM]=boot+bytes(TABLE-RAM-len(boot))
    if runtime.get('format')=='AFV3-ROOM-RIGS-2' and runtime.get('bootstrap'):
        expected=bytearray(VTABLE-TABLE)
        if colours and colours.get('bridge_hex'):
            from v3_furniture_reactions import COLOUR_BRIDGE,COLOUR_BRIDGE_END
            expected[COLOUR_BRIDGE-TABLE:COLOUR_BRIDGE_END-TABLE]=bytes.fromhex(colours['bridge_hex']).ljust(
                COLOUR_BRIDGE_END-COLOUR_BRIDGE,b'\0')
        if effects and effects.get('bootstrap_loader'):
            from v3_room_effects import LOADER_BRIDGE
            struct.pack_into('>I',expected,LOADER_BRIDGE-TABLE,effects['bootstrap_loader'])
        expected[MATERIAL_VTABLE-TABLE:MATERIAL_VTABLE-TABLE+20]=bytes.fromhex(runtime.get('material_vtable_hex','00'*20))
        if runtime.get('scrolling'):
            from v3_furniture_scroll import VTABLE as SCROLL_VTABLE
            expected[SCROLL_VTABLE-TABLE:SCROLL_VTABLE-TABLE+20]=bytes.fromhex(runtime['scrolling'].get('vtable_hex','00'*20))
            if runtime['scrolling'].get('movement',{}).get('bridge_hex'):
                from v3_room_movement import BRIDGE
                expected[BRIDGE-TABLE:BRIDGE-TABLE+8]=bytes.fromhex(runtime['scrolling']['movement']['bridge_hex'])
        if module[TABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM]!=expected:
            raise ValueError('Occupied room cache/material vtable reservation')
    module[TABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM]=bytes(VTABLE-TABLE)
    if effects:
        from v3_room_effects import LOADER_BRIDGE,rebind_profiles
        entry=bootstrap['symbols']['af_v3_room_boot_load']
        if entry&3 or not RAM<=entry<RAM+len(boot):raise ValueError('Effect loader escapes room bootstrap')
        struct.pack_into('>I',module,LOADER_BRIDGE-EQUIPMENT_RAM,entry)
        effects['bootstrap_loader']=entry
        rebind_profiles(effects,blob,symbols,code_bounds=(packet_ram,table_ram))
    if scroll_defines:
        from v3_furniture_scroll import VTABLE as SCROLL_VTABLE
        lifecycle=bool(runtime['scrolling'].get('lifecycle_rows'))
        entries=[bootstrap['symbols']['af_v3_room_boot_scroll_'+role] if role=='dw' or lifecycle else 0
                 for role in ('ct','mv','dw','dt')]
        if any(p and (p&3 or not RAM<=p<RAM+len(boot)) for p in entries):raise ValueError('Scroll bootstrap escapes reservation')
        scroll_vtable=struct.pack('>5I',*entries,0)
        module[SCROLL_VTABLE-EQUIPMENT_RAM:SCROLL_VTABLE-EQUIPMENT_RAM+20]=scroll_vtable
        runtime['scrolling'].update(vtable=SCROLL_VTABLE,vtable_hex=scroll_vtable.hex(),cache_ram=TABLE+4)
        if runtime['scrolling'].get('movement'):
            from v3_room_movement import BRIDGE
            target=bootstrap['symbols']['af_v3_room_boot_scroll_move_sound']
            bridge=struct.pack('>2I',0x08000000|(target>>2&0x3FFFFFF),0)
            module[BRIDGE-EQUIPMENT_RAM:BRIDGE-EQUIPMENT_RAM+8]=bridge
            runtime['scrolling']['movement'].update(entry=BRIDGE,helper_entry=target,bridge_hex=bridge.hex())
    if material_rows:
        entry=bootstrap['symbols']['af_v3_room_boot_material_dw']
        if entry&3 or not RAM<=entry<RAM+len(boot):raise ValueError('Material bootstrap escapes reservation')
        move=bootstrap['symbols']['af_v3_room_boot_sound_mv'] if reactions or colours or any(r.get('lifecycle') in (4,5) or r.get('move_category')=='switch-trigger-sound' for r in material_rows) else 0
        create=bootstrap['symbols']['af_v3_room_boot_ct'] if any(r.get('lifecycle') for r in material_rows) else 0
        material_vtable=struct.pack('>5I',create,move,entry,0,0)
        module[MATERIAL_VTABLE-EQUIPMENT_RAM:MATERIAL_VTABLE-EQUIPMENT_RAM+20]=material_vtable
        runtime.update(material_vtable=MATERIAL_VTABLE,material_vtable_hex=material_vtable.hex(),material_table=MATERIAL_TABLE+table_delta)
    module[VTABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM+20]=vtable
    if sound_rows or static_rows:
        entry=bootstrap['symbols']['af_v3_room_boot_sound_mv']
        if entry&3 or not RAM<=entry<RAM+len(boot):raise ValueError('Room sound bootstrap escapes reservation')
        before=module[SOUND_VTABLE-EQUIPMENT_RAM:SOUND_VTABLE-EQUIPMENT_RAM+20]
        if before!=bytes.fromhex(runtime.get('sound_vtable_hex','00'*20)):
            raise ValueError('Occupied room sound vtable reservation')
        sound_vtable=struct.pack('>5I',0,entry,0,0,0)
        module[SOUND_VTABLE-EQUIPMENT_RAM:SOUND_VTABLE-EQUIPMENT_RAM+20]=sound_vtable
        runtime.update(sound_vtable=SOUND_VTABLE,sound_vtable_hex=sound_vtable.hex(),sound_table=SOUND_TABLE+table_delta)
    if colours:
        from v3_furniture_reactions import publish_colours
        publish_colours(equipment,module,dict(packet,crc32=zlib.crc32(data)),symbols,output)
    blob[at:at+len(data)]=data;blob[start:start+len(module)]=module
    packet.update(sha256=sha256(data),crc32=zlib.crc32(data))
    if reactions:
        from v3_furniture_reactions import publish_bridge
        publish_bridge(core,reactions,packet,symbols,output)
    runtime.update(code=compiled,bootstrap=bootstrap,table_sha256=sha256(table),
                   vtable_hex=vtable.hex(),catalogue_index_supported=True)
    equipment.update(sha256=sha256(module),crc32=zlib.crc32(module))


def extend(base,prior,blob,core,original,output,directories):
    old=prior['equipment_resources'];runtime=old['room_rigs'];start=old['blob_offset']
    module=blob[start:start+old['bytes']];scenery=old['scenery']
    if (sha256(module)!=old['sha256'] or EQUIPMENT_RAM+old['bytes']>PACKET_RAM or
            scenery['ram']+scenery['additional_fixed_resident_bytes']>PACKET_RAM or
            PACKET_RAM+PACKET_BYTES>prior['furniture']['bank_pool']['start'] or
            module[VTABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM+20]!=bytes.fromhex(runtime['vtable_hex'])):
        raise ValueError('Changed room module/vtable or occupied packet reservation')
    is_packet=runtime['format']=='AFV3-ROOM-RIGS-2'
    if is_packet:
        packet=runtime['packet'];boot=runtime['bootstrap']
        packet_layout(runtime)
        if sha256(blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']])!=packet['sha256']:
            raise ValueError('Changed complete installed room packet')
    elif runtime['format']=='AFV3-ROOM-RIGS-1':
        boot=runtime['code']
        if module[TABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM]!=encode(runtime['rows']):
            raise ValueError('Changed complete installed room records')
    else:raise ValueError('Unknown room runtime format')
    if (sha256(module[RAM-EQUIPMENT_RAM:RAM-EQUIPMENT_RAM+boot['bytes']])!=boot['sha256'] or
            any(module[RAM-EQUIPMENT_RAM+boot['bytes']:TABLE-EQUIPMENT_RAM])):
        raise ValueError('Changed complete room lifecycle reservation')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    rows,assets,evidence=prepared_categories(source,directories)
    occupied={r['item_id'] for r in runtime['rows']}
    for r in runtime['rows']:
        if sha256(blob[r['blob_offset']:r['blob_offset']+r['bytes']])!=r['sha256']:
            raise ValueError('Changed installed complete room artwork')
    for r in rows:
        i=slot(int(r['item_id'],16))
        if r.get('mode')==3 and r.get('first')==2:
            from v3_room_effects import conditional_binding
            conditional_binding(base,prior,r['source']['profile']['callback_adapter']['trigger'])
        if (r['item_id'] in occupied or any(blob[ROWS+i*80:ROWS+(i+1)*80]) or
                any(blob[ITEMS+i*32:ITEMS+(i+1)*32]) or blob[0x40+i//8]&(1<<(i&7))):
            raise ValueError('Additional room category collides with an installed identity')
    all_rows=sorted(copy.deepcopy(runtime['rows'])+rows,key=lambda r:r['runtime_index']);encode_packet(all_rows)
    rolling=any(r.get('mode')==5 for r in all_rows)
    wide=any(r.get('mode')==6 for r in all_rows) or is_packet and runtime['packet']['ram']==WIDE_RAM
    large=wide or rolling or is_packet and runtime['packet']['ram']==EXTENDED_RAM
    packet_ram,table_ram,packet_bytes=((WIDE_RAM,WIDE_TABLE,WIDE_BYTES) if wide else
        (EXTENDED_RAM,EXTENDED_TABLE,EXTENDED_BYTES) if large else (PACKET_RAM,PACKET_TABLE,PACKET_BYTES))
    new_packet=not is_packet or runtime['packet']['ram']!=packet_ram
    if large:
        # The password packet ends at the new reservation's start; the model
        # pool remains above it. Other resident category packets stay intact.
        password=old.get('passwords',{})
        if (not password or password['ram']+password['bytes']>packet_ram or
                packet_ram+packet_bytes>prior['furniture']['bank_pool']['start']):
            raise ValueError('Expanded room packet overlaps an existing owner')
    needed=sum(len(d) for d in assets.values())+(packet_bytes if new_packet else 0)
    reuse=retired_module_space(base,prior,blob,needed)
    contract=extended_contract(base,core,original)
    billboard=any(r.get('mode')==4 for r in all_rows)
    billboard_binding=billboard_contract(base,prior) if billboard else None
    if reuse:
        cursor=reuse['blob_offset']
    else:
        cursor=(len(blob)+15)&~15
        if BLOB+cursor+needed>checked_limit(base,prior):
            raise ValueError('Complete room category exceeds checked cartridge reservation')
        blob.extend(bytes(cursor+needed-len(blob)))
    result=copy.deepcopy(old);installed=result['room_rigs']
    if billboard_binding:installed['billboard_contract']=billboard_binding
    if rolling:installed['motion_contract']=motion_binding(source,base,prior,all_rows)
    if any(r.get('mode')==6 for r in all_rows):installed['joint_contract']=joints.native_contract(base)
    if any(r.get('mode')==7 for r in all_rows):installed['roof_contract']=roofs.native_contract(source,base)
    if any(r.get('mode')==6 and r.get('first')==4 for r in all_rows):
        from v3_furniture_needle import native_contract as needle_contract
        installed['needle_contract']=needle_contract(base,prior)
    if new_packet:
        installed['packet']=dict(ram=packet_ram,bytes=packet_bytes,blob_offset=cursor,vrom=BLOB+cursor)
        cursor+=packet_bytes
    for r in rows:
        data=assets[r['source_item_id']];at=cursor;cursor+=len(data)
        blob[at:cursor]=data;r.update(blob_offset=at,vrom=BLOB+at)
    installed.update(format='AFV3-ROOM-RIGS-2',categories=sorted(set(runtime.get('categories',[]))|
        {CATEGORY,CLOCK_CATEGORY,STORAGE_CATEGORY}|{r['category'] for r in rows}),rows=all_rows,
        table_ram=table_ram,capacity=PACKET_CAPACITY,ram=packet_ram,extended_native_contract=contract,
        additional_resident_bytes=packet_bytes if new_packet else 0,
        artwork_bytes=runtime['artwork_bytes']+sum(len(d) for d in assets.values()))
    installed.setdefault('additional_sources',[]).extend(evidence)
    installed.setdefault('reservations',[]).append(reuse or dict(
        blob_offset=cursor-needed,bytes=needed,appended=True))
    publish_packet(result,blob,output,core=core)
    result['additional_resident_bytes']=installed['additional_resident_bytes']
    return result,{}


def prepared(source,directory):
    """Verify the category's complete prepared data without recompiling graphics."""
    directory=directory.resolve();raw=(directory/'art.json').read_bytes();art=json.loads(raw)
    if (not directory.is_relative_to(ROOT/'build') or art['format']!='AFV3-AUTO-FURNITURE-PREPARED-ASSETS-1'
            or art['source_rel_sha256']!=sha256(source.rel)
            or art['source_symbols_sha256']!=sha256(source.symbols.encode())):
        raise ValueError('Changed complete prepared room-rig source')
    aliases={r['display_item_id']:r for r in room_aliases(source)['rows'] if r['room_placement_uses_display']}
    rows=[];assets={};seen=set()
    for row in art['objects']:
        donor=row['item_id'];item=int(donor,16)
        if donor in seen or donor not in aliases:raise ValueError('Unreviewed or duplicate room-rig parent')
        seen.add(donor);alias=aliases[donor]
        descriptor,body,resources,_,models,commands,sections=prepare(source,item)
        rig=descriptor.get('callback_adapter',{})
        if (rig.get('category')!=CATEGORY or row['profile']!=json.loads(json.dumps(descriptor))
                or row['resources']!=resources or row.get('room_alias')!=alias
                or descriptor['skeleton']['joints']>6 or
                any(r.get('draw_stream') for r in descriptor['skeleton']['rows'])
                or row['native_profile_scalar_hex']!=descriptor['scalar_hex']):
            raise ValueError('Changed complete room-rig category or native work capacity')
        path=(directory/row['object_file']).resolve()
        if path.parent!=directory:raise ValueError('Room asset escapes prepared directory')
        data=path.read_bytes();artwork=(len(body)+sum(n for _,n in sections)+15)&~15
        tail,receipt=suffix(source,descriptor,row['model_offsets'],start=artwork)
        if (len(data)!=row['object_bytes'] or sha256(data)!=row['object_sha256']
                or len(data)>9216 or data[:len(body)]!=body or data[artwork:]!=tail
                or row['rig']!=json.loads(json.dumps(receipt))
                or (directory/donor/'commands.c').read_text()!=commands
                or len(row['models'])!=len(sections) or set(row['model_offsets'])!=set(models)):
            raise ValueError('Changed complete room-rig resource or emitter input')
        cursor=len(body)
        for model,(label,size) in zip(row['models'],sections):
            if (model['layer']!=label or model['native_offset']!=cursor or row['model_offsets'][label]!=cursor
                    or model['bytes']!=size or model['source_sha256']!=models[label]['source_sha256']
                    or sha256(data[cursor:cursor+size])!=model['output_sha256']):
                raise ValueError('Changed complete room-rig drawing commands')
            cursor+=size
        if any(data[cursor:artwork]):raise ValueError('Changed room-rig alignment padding')
        index,destination=furniture_representation_identity(item)
        records=dict(source_item_id=donor,parent_item_id=alias['parent_item_id'],
            item_id=f'{destination:04X}',runtime_index=index,bytes=len(data),sha256=sha256(data),
            skeleton=0x06000000+receipt['skeleton_offset'],animation=0x06000000+receipt['animation_offset'],
            joints=receipt['skeleton']['joints'],shown=receipt['skeleton']['shown_joints'],
            source=row,profile_installed=False,parent_selectable=False)
        rows.append(records);assets[donor]=data
    if not rows or len(rows)>CAPACITY or set(aliases)!=seen:
        raise ValueError('Prepared room-rig bundle omits a complete source category')
    rows.sort(key=lambda r:r['runtime_index'])
    if len({r['runtime_index'] for r in rows})!=len(rows):raise ValueError('Colliding room-rig destinations')
    return rows,assets,dict(directory=str(directory.relative_to(ROOT)),sha256=sha256(raw),
        source_rel_sha256=sha256(source.rel),registry_version=ROOM_ALIAS_REGISTRY_VERSION)


def encode(rows):
    if not rows or len(rows)>CAPACITY:raise ValueError('Room-rig record capacity exceeded')
    indices=[r['runtime_index'] for r in rows]
    if indices!=sorted(set(indices)):raise ValueError('Unordered or duplicate room-rig records')
    table=bytearray(struct.pack('>4I',MAGIC,len(rows),16,0))
    for r in rows:
        if (r['runtime_index']!=1024+slot(int(r['item_id'],16)) or
                not 32<=r['bytes']<=9216 or r['bytes']%16 or
                not 1<=r['shown']<=r['joints']<=(6 if r.get('mode',0) in (0,5) else 8) or
                any(p&3 or not 0x06000000<=p<=0x06000000+r['bytes']-n for p,n in
                    ((r['skeleton'],8),(r['animation'],20)))):
            raise ValueError('Invalid complete room-rig record')
        table.extend(struct.pack('>HHIIHH',r['runtime_index'],r['bytes'],r['skeleton'],r['animation'],r['joints'],r['shown']))
    return bytes(table).ljust(VTABLE-TABLE,b'\0')


def install(base,prior,blob,core,original,output,directory):
    directories=list(directory) if isinstance(directory,(list,tuple)) else [directory]
    if prior['equipment_resources'].get('room_rigs'):
        return extend(base,prior,blob,core,original,output,directories)
    if len(directories)!=1:raise ValueError('Initial room runtime requires one complete category')
    directory=directories[0]
    old=prior['equipment_resources'];start=old['blob_offset'];offset=RAM-EQUIPMENT_RAM
    module=bytearray(blob[start:start+old['bytes']])
    if (old.get('room_rigs') or not old.get('inventory_preview',{}).get('balloon_drawer') or
            sha256(module)!=old['sha256'] or len(module)!=0xF000 or
            any(module[offset:LIMIT-EQUIPMENT_RAM]) or
            old['held_rig_actions']['code']['bytes']>RAM-0x804B0000):
        raise ValueError('Room rigs require the checked unused module reservation')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    rows,assets,evidence=prepared(source,directory)
    for r in rows:
        i=slot(int(r['item_id'],16))
        if any(blob[ROWS+i*80:ROWS+(i+1)*80]) or any(blob[ITEMS+i*32:ITEMS+(i+1)*32]) or blob[0x40+i//8]&(1<<(i&7)):
            raise ValueError('Room-rig reservation collides with installed data or a selected identity')
    contract=native_contract(original,base,expected_sha=sha256(base))
    native=by_vrom(original)[CODE_VROM].extract(original)
    # Complete native construction/initialization/play/draw code owns at most
    # (joints+1) work vectors. The last two morph vectors remain callback-owned.
    first,last=0x80052228,0x80053170
    if core[first-CODE_RAM:last-CODE_RAM]!=native[first-CODE_RAM:last-CODE_RAM]:
        raise ValueError('Changed complete native keyframe ownership or rendering APIs')
    contract=dict(blocks=contract['blocks'],actor_bytes=0x740,keyframe=0x134,joint=0x1A4,morph=0x1DA,
        work_vectors=7,state=0x204,state_bytes=8,matrix=0x210,matrix_bank_bytes=0x280,
        keyframe_api_sha256=sha256(core[first-CODE_RAM:last-CODE_RAM]))
    code,compiled=compile_part('room_rigs',output/'room_rigs')
    if len(code)>TABLE-RAM:raise ValueError('Room-rig code escapes its reservation')
    needed=sum(len(d) for d in assets.values());reuse=retired_module_space(base,prior,blob,needed)
    cursor=reuse['blob_offset'] if reuse else len(blob)
    for r in rows:
        data=assets[r['source_item_id']];cursor=(cursor+15)&~15;at=cursor;cursor+=len(data)
        if reuse:
            if cursor>reuse['blob_offset']+reuse['bytes']:raise ValueError('Room rigs exceed reusable resource bounds')
            blob[at:cursor]=data
        else:
            if BLOB+cursor>END:raise ValueError('Complete room rigs exceed checked ROM storage')
            blob.extend(bytes(at-len(blob)));blob.extend(data)
        r.update(blob_offset=at,vrom=BLOB+at)
    table=encode(rows);entries=[compiled['symbols']['af_v3_room_rig_'+r] for r in ('ct','mv','dw')]
    if any(p&3 or not RAM<=p<RAM+len(code) for p in entries):raise ValueError('Room-rig vtable escapes code')
    vtable=struct.pack('>5I',*entries,0,0)
    module[offset:offset+len(code)]=code
    module[TABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM]=table
    module[VTABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM+len(vtable)]=vtable
    report=copy.deepcopy(old)
    report['room_rigs']=dict(format='AFV3-ROOM-RIGS-1',category=CATEGORY,rows=rows,source=evidence,
        code=compiled,ram=RAM,table_ram=TABLE,table_sha256=sha256(table),capacity=CAPACITY,
        vtable=VTABLE,vtable_hex=vtable.hex(),native_contract=contract,retired_space=reuse,
        artwork_bytes=needed,additional_resident_bytes=0,saved_format_changed=False,
        profile_bits_enabled=0,ordinary_room_tested=False,hardware_tested=False)
    report.update(sha256=sha256(module),crc32=zlib.crc32(module),additional_resident_bytes=0)
    blob[start:start+len(module)]=module
    return report,{}


def refresh_code(equipment,blob,output,*,core=None):
    """Retain full room resources while connecting an additional native consumer."""
    runtime=equipment['room_rigs']
    if runtime['format']=='AFV3-ROOM-RIGS-2':
        packet=runtime['packet'];at=packet['blob_offset']
        packet_layout(runtime)
        if sha256(blob[at:at+packet['bytes']])!=packet['sha256']:raise ValueError('Changed complete room packet')
        return publish_packet(equipment,blob,output,core=core)
    old=runtime['code'];start=equipment['blob_offset']
    module=bytearray(blob[start:start+equipment['bytes']]);at=RAM-EQUIPMENT_RAM
    if (sha256(module)!=equipment['sha256'] or sha256(module[at:at+old['bytes']])!=old['sha256'] or
            any(module[at+old['bytes']:TABLE-EQUIPMENT_RAM]) or
            module[VTABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM+20]!=bytes.fromhex(runtime['vtable_hex'])):
        raise ValueError('Changed complete installed room lifecycle reservation')
    code,compiled=compile_part('room_rigs',output/'room_rigs')
    entries=[compiled['symbols']['af_v3_room_rig_'+role] for role in ('ct','mv','dw')]
    if len(code)>TABLE-RAM or any(p&3 or not RAM<=p<RAM+len(code) for p in entries):
        raise ValueError('Changed room lifecycle bounds')
    table=struct.pack('>5I',*entries,0,0)
    module[at:TABLE-EQUIPMENT_RAM]=code+bytes(TABLE-RAM-len(code))
    module[VTABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM+20]=table
    runtime.update(code=compiled,vtable_hex=table.hex(),catalogue_index_supported=True)
    equipment.update(sha256=sha256(module),crc32=zlib.crc32(module))
    blob[start:start+len(module)]=module
