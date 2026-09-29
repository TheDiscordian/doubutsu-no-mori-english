"""Compile the complete added-insect behaviour category against the N64 ABI.

The six pinned donor translation units stay in ignored output. Shared platform
accesses are rewritten explicitly; behaviour bodies and revision conditionals
are retained. A relocatable object is preparation, not installed gameplay: every
unresolved engine adapter is recorded, and none is replaced with a dummy body.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import struct
import subprocess

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom,u32
from apply_translation import write_new
from v3_asset_loader import ROOT, IMAGE
from v3_creature_field import named_table
from v3_creature_items import source_records
from v3_furniture_pipeline import Source
from v3_creature_save import SOURCES as SAVE_SOURCES

PROGRAMS = (
    ('tentou','aITT',3,'190408d3b79fb5573c0f0be83ef9a2317cf3526aacc4d20970cee9cad65f6b4b'),
    ('kera','aIKR',12,'a241fabdc24ccb4eadba3fa77b9d95d72eaf397e3832479ece05875fb7000824'),
    ('amenbo','aIAB',9,'8de9ecb7d51575ca8728adda9cd1a0e07d386f004a66d5d37717659822fb8ffb'),
    ('mino','aIMN',13,'8fe06ee0ef8c1ce72ea577568371e6665e2d78e86789d13f4f29f0e484d63a2b'),
    ('dango','aIDG',11,'86599c9c18f49aa8855bb628cc08f611b39635afeddf709f98f1ddc2bb25c84f'),
    ('ka','aIKA',10,'d46aa8b6a6835c05a9c71d9e96b4d1c5b2fb193fa0c73350a7a1c5cd2a208c08'),
)
CARRIED_PROGRAMS=(('hitodama','aIHD',8,
    'b3e7c0eab765fab1909a8a050e7fe6141a6237aa4e3e8ed4d4b50fba6c7ce0f2'),)
RUNTIME=('creature_insects','creature_insect_state','creature_insect_environment',
         'creature_insect_engine','creature_insect_collision','creature_insect_spawns',
         'creature_insect_manager','creature_insect_colony','creature_insect_colony_draw',
         'creature_insect_audio','creature_insect_effects','creature_insect_player',
         'creature_insect_mosquito','creature_insect_save','creature_insect_pool')
SOURCES=('tools/v3_creature_insects.py','overlays/v3/creature_insects.h',
         'tools/v3_creature_spawns.py','overlays/v3/creature_spawns.h',
         'tools/v3_creature_insect_pool.py',
         'overlays/v3/creature_insect_spawns.h',
         'overlays/v3/creature_insect_manager.h',
         'overlays/v3/creature_insect_colony.h',
         'tools/v3_furniture_art.py',
         'tools/v3_creature_insect_audio.py','tools/v3_sound_programs.py',
         'tools/v3_creature_insect_effects.py','overlays/v3/creature_insect_effects.h',
         'tools/v3_creature_insect_player.py','overlays/v3/creature_insect_player.h',
         'tools/v3_keyframes.py','tools/v3_equipment_runtime.py','translations/provenance.json',
         'overlays/v3/player_faces.c','overlays/v3/player_faces.ld',
         'overlays/v3/creature_insect_engine.h',
         'overlays/v3/creature_insect_collision.h',
         'overlays/v3/creature_insect_bindings.ld',
         'overlays/v3/creature_insects.ld',
         'overlays/v3/creature_insect_hooks.S',
         *(f'overlays/v3/{name}.c' for name in RUNTIME),*SAVE_SOURCES)
NATIVE_FUNCTIONS=(
    (0x80A10210,0x80A102B8,'ceceb00fbf78bfb02831e6f0073c38b968e03dac21b2a17c02a0f7cadbd835aa'),
    (0x80A10558,0x80A108AC,'c2f75fbcf8e4e2414740bc1455ee41ab4966832d69f3a222f9cc6daea563432e'),
    (0x80A10A20,0x80A10ADC,'496c0ae0944bd93c825563968f3dbd3cd510b0a837fab09a0bae39d538005d27'),
    (0x80A10E54,0x80A10EF4,'f1e47dc84b53062a8ce24ff6af22f6e87a186706e17d470865b573892ae85d5b'),
    (0x80A1102C,0x80A11264,'a32b9642d869accdfeca58522825f5d58c816b319572e4cb8b1482b2f1076c54'),
)
CONTROLLER_HOOKS=(
    (0x80A10254,8,'af_insect_hook_ctor',True),
    (0x80A102A0,8,'af_insect_hook_dtor',False),
    (0x80A10818,28,'af_insect_hook_init',False),
    (0x80A11090,8,'af_insect_hook_slot',False),
    (0x80A11230,8,'af_insect_hook_end',False),
)


def controller_contract(image,original):
    from v3_player_actions import native_references
    from v3_npc_clothing import guard_incoming
    files=by_vrom(image);retail=by_vrom(original)
    owner=files[0x8DEEC0].extract(image);rel=files[0x8E0870].extract(image)
    native=retail[0x8DEEC0].extract(original)
    sections=struct.unpack_from('>5I',rel)
    groups,_,records,locations,_=native_references(owner,rel,expected_sections=sections[:4])
    spans=[(address-0x80A10210,size) for address,size,_,_ in CONTROLLER_HOOKS]
    guard_incoming(owner,sections[0],0x80A10210,spans)
    covered={at for start,size in spans for at in range(start,start+size,4)}
    for high,lows in groups.items():
        if (high in covered or any(low in covered for low,_ in lows)) and (
                high not in covered or any(low not in covered for low,_ in lows)):
            raise ValueError('Partial native insect HI/LO replacement')
    hooks=[]
    for address,size,symbol,delay in CONTROLLER_HOOKS:
        at=address-0x80A10210
        before=owner[at:at+size]
        if before!=native[at:at+size]: raise ValueError('Changed controller hook span')
        hooks.append(dict(address=address,bytes=size,symbol=symbol,retain_delay=delay,before=before.hex()))
    core=files[CODE_VROM].extract(image);at=0x80070398-CODE_RAM
    if core[at:at+8]!=retail[CODE_VROM].extract(original)[at:at+8] or u32(core,at)!=0x0C01B4EC:
        raise ValueError('Changed native column-generation call')
    return dict(owner_sha256=sha256(owner),reloc_sha256=sha256(rel),sections=list(sections),
        hooks=hooks,removed_relocations=[locations[at] for at in sorted(covered) if at in locations],
        column_hook=dict(address=0x80070398,before=core[at:at+8].hex(),symbol='af_insect_columns'),
        installed=False)


def spawn_contract(image,original):
    from v3_npc_clothing import guard_incoming
    from v3_player_actions import native_references
    files=by_vrom(image);retail=by_vrom(original)
    owner=files[0x821B40].extract(image);rel=files[0x8240D0].extract(image)
    native=retail[0x821B40].extract(original);ram=0x8092A030
    sections=struct.unpack_from('>5I',rel)
    functions=[]
    for start,end in ((0x8092AE10,0x8092AF0C),(0x8092AF0C,0x8092B014)):
        raw=owner[start-ram:end-ram]
        if raw!=native[start-ram:end-ram] or len(raw)!=end-start:
            raise ValueError('Changed complete native insect spawning consumer')
        functions.append(dict(address=start,end=end,sha256=sha256(raw)))
    at=0x8092AF0C-ram
    if owner[at:at+8]!=bytes.fromhex('27BDFFC0 AFBF0024'):
        raise ValueError('Changed native insect manager prologue')
    guard_incoming(owner,sections[0],ram,[(at,8)])
    _,_,_,locations,_=native_references(owner,rel,expected_sections=sections[:4])
    if at in locations or at+4 in locations:
        raise ValueError('Unexpected relocated insect manager prologue')
    return dict(owner_vrom=0x821B40,reloc_vrom=0x8240D0,owner_ram=ram,
        owner_sha256=sha256(owner),reloc_sha256=sha256(rel),functions=functions,
        address=0x8092AF0C,before=owner[at:at+8].hex(),symbol='af_v3_insect_spawn',
        installed=False)


def install_spawn_manager(image,symbols,contract):
    from v3_import_storage import jump
    files=by_vrom(image);vrom=contract['owner_vrom'];ram=contract['owner_ram']
    owner=bytearray(files[vrom].extract(image));rel=files[contract['reloc_vrom']].extract(image)
    if sha256(owner)!=contract['owner_sha256'] or sha256(rel)!=contract['reloc_sha256']:
        raise ValueError('Changed prepared insect spawn owner')
    target=symbols[contract['symbol']]
    if target&3 or not 0x80000000<=target<0x80800000:
        raise ValueError('Insect manager target is not resident executable RAM')
    at=contract['address']-ram
    if owner[at:at+8]!=bytes.fromhex(contract['before']):
        raise ValueError('Changed insect manager entry')
    after=struct.pack('>II',jump(target),0);owner[at:at+8]=after
    return {vrom:bytes(owner)},dict(contract,target=target,after=after.hex())


def install_controller(image,symbols,contract):
    """Compose owner/core changes only; caller must place/load the complete code.

    This is not a standalone ROM builder and cannot satisfy unresolved services.
    Preserve every unrelated drawing/asset hook already in the supplied owner.
    """
    from v3_import_storage import jump
    files=by_vrom(image)
    owner=bytearray(files[0x8DEEC0].extract(image));rel=bytearray(files[0x8E0870].extract(image))
    core=bytearray(files[CODE_VROM].extract(image))
    if sha256(owner)!=contract['owner_sha256'] or sha256(rel)!=contract['reloc_sha256']:
        raise ValueError('Changed prepared insect controller')
    patches=[]
    for hook in [*contract['hooks'],dict(contract['column_hook'],bytes=8,retain_delay=True)]:
        target=symbols[hook['symbol']]
        if target&3 or not 0x80000000<=target<0x80800000:
            raise ValueError('Insect hook target is not resident executable RAM')
        data,ram=(core,CODE_RAM) if hook['address']<0x80800000 else (owner,0x80A10210)
        at=hook['address']-ram;before=bytes.fromhex(hook['before'])
        if data[at:at+hook['bytes']]!=before: raise ValueError('Changed insect hook input')
        after=struct.pack('>I',jump(target,link=True))+(before[4:8] if hook['retain_delay'] else bytes(4))
        after+=bytes(hook['bytes']-8);data[at:at+len(after)]=after
        patches.append(dict(hook,target=target,after=after.hex()))
    records=list(struct.unpack_from('>'+str(u32(rel,16))+'I',rel,20))
    for record in contract['removed_relocations']:
        if records.count(record)!=1: raise ValueError('Missing insect hook relocation')
        records.remove(record)
    struct.pack_into('>I',rel,16,len(records))
    rel[20:-4]=struct.pack('>'+str(len(records))+'I',*records)+bytes(len(rel)-24-4*len(records))
    return {CODE_VROM:bytes(core),0x8DEEC0:bytes(owner),0x8E0870:bytes(rel)},patches


def native_contract(image,prior):
    owner=by_vrom(image)[0x8DEEC0].extract(image)
    functions=[]
    for start,end,digest in NATIVE_FUNCTIONS:
        if sha256(owner[start-0x80A10210:end-0x80A10210])!=digest:
            raise ValueError(f'Changed native insect ABI dependency at {start:08X}')
        functions.append(dict(address=start,bytes=end-start,sha256=digest))
    # Current imports may alter unrelated code. Bind only unchanged complete
    # functions from the hash-verified Japanese source, not guessed GC addresses.
    original=verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    source_files=by_vrom(original);current_files=by_vrom(image)
    bindings=(ROOT/'overlays/v3/creature_insect_bindings.ld').read_text()
    symbols=''.join((ROOT/f'upstream/af/linker_scripts/jp/symbol_addrs_{part}.txt').read_text()
                    for part in ('boot','code','libultra'))
    starts=sorted(set(int(s,16) for s in re.findall(r'= (0x[0-9A-Fa-f]+); //[^\n]*\btype:func',symbols)))
    resident=[]
    for name,address in re.findall(r'(?m)^(\w+) = (0x[0-9A-Fa-f]+);',bindings):
        at=int(address,16)
        if at>=0x80100000: continue  # separately documented global fields
        if at not in starts: raise ValueError('Unknown native function: '+name)
        end=next(a for a in starts if a>at)
        vrom,ram=(0x1060,0x80025C60) if at<CODE_RAM else (CODE_VROM,CODE_RAM)
        before=source_files[vrom].extract(original)[at-ram:end-ram]
        current=current_files[vrom].extract(image)[at-ram:end-ram]
        expected=bytearray(before);adapters=[]
        if name=='af_insect_create_actor':
            # The existing additive descriptor chain handles CA/CB specially
            # and delegates native IDs, including unused B5, to actor_dlftbls.
            # Preserve it; do not restore the retail descriptor lookup.
            hooks=[*prior['campsite_exterior']['hooks'],
                *prior['equipment_resources']['player_actions']['balloon_actor']['patches']]
            for hook in hooks:
                if not at<=hook['address']<end:continue
                pos=hook['address']-at;old=bytes.fromhex(hook['before']);new=bytes.fromhex(hook['after'])
                if len(old)!=len(new) or expected[pos:pos+len(old)]!=old:
                    raise ValueError('Changed installed additive actor-descriptor chain')
                expected[pos:pos+len(new)]=new;adapters.append(hook)
            if len(adapters)!=2:raise ValueError('Missing installed actor-descriptor chain')
        if len(before)!=end-at or not before or current!=expected:
            raise ValueError('Changed native engine binding: '+name)
        resident.append(dict(symbol=name,address=at,end=end,sha256=sha256(current),
            **(dict(original_sha256=sha256(before),retained_adapters=adapters) if adapters else {})))
    return dict(rom_sha256=sha256(image),owner_vrom=0x8DEEC0,owner_ram=0x80A10210,
        engine_bindings=resident,collision_pipe_bytes=0x1C,
        controller=controller_contract(image,original),
        spawn_manager=spawn_contract(image,original),
        colony=colony_contract(image,original),
        intro_environment=intro_environment_contract(image,original),
        functions=functions,controller_bytes=0x8F8,slot_offset=0x174,slots=3,stride=0x280,
        offsets=dict(type=0x1CC,movement=0x1D0,animation=0x1DC,speed_step=0x1E8,
                     target_speed=0x1EC,patience=0x1F4,collision=0x1F8,item=0x21C,
                     flags=0x21E,life_time=0x220,alpha=0x258))


def intro_environment_contract(image,original):
    files=by_vrom(image);retail=by_vrom(original);rows=[]
    # Complete mode setter/getter/wall consumer and both owners of the native
    # demo clip. GC's separate demo_clip2 is not the adjacent native field.
    for vrom,ram,spans in (
        (CODE_VROM,CODE_RAM,((0x800741DC,0x800743EC),(0x800953B0,0x80095414),
                            (0x800B5CD4,0x800B5D34))),
        (0x8477A0,0x809529B0,((0x809529B0,0x80952ACC),
                            (0x8095308C,0x809531C8),(0x80953444,0x80953474))),
        (0x848600,0x80953820,((0x80953820,0x8095388C),)),
        (0x896A30,0x809B3220,((0x809B32BC,0x809B3324),)),
        (0x897450,0x809B3C40,((0x809B3CDC,0x809B3D44),)),
        (0x898220,0x809B4A10,((0x809B4AAC,0x809B4B14),)),
        (0x8991B0,0x809B59A0,((0x809B5A3C,0x809B5AA4),))):
        current=files[vrom].extract(image);before=retail[vrom].extract(original)
        for start,end in spans:
            raw=current[start-ram:end-ram]
            if not raw or raw!=before[start-ram:end-ram]:
                raise ValueError('Changed native insect intro/environment binding')
            rows.append(dict(vrom=vrom,ram=ram,address=start,end=end,sha256=sha256(raw)))
    return dict(functions=rows,demo_clip=0x80136F4C,block_mode_getter=0x800741F4,
        player_acre_mask=1,inset_units=1,reset_flag=0x80137908,
        second_demo_state='native-reset-event-flag',
        absent_native_sequences=['PresentDemo','BoatDemo'])


def colony_contract(image,original):
    from v3_npc_clothing import guard_incoming
    from v3_player_actions import native_references
    files=by_vrom(image);retail=by_vrom(original)
    core=files[CODE_VROM].extract(image);entry=0x80100C90+0xB5*0x20
    if core[entry-CODE_RAM:entry-CODE_RAM+0x20]!=bytes(0x20):
        raise ValueError('The native ground-colony actor slot is already occupied')
    owner=files[0x7AC420].extract(image);rel=files[0x7D9BA0].extract(image)
    native=retail[0x7AC420].extract(original);ram=0x808B2D50
    definitions=(ROOT/'upstream/af/linker_scripts/jp/symbol_addrs_overlays.txt').read_text()
    starts=sorted({int(at,16) for at in re.findall(r'= (0x[0-9A-Fa-f]+); // type:func',definitions)})
    functions=[]
    for start in (0x808B5C68,0x808B5D44,0x808B5DA4,0x808B8B54,0x808B8B90):
        end=next(at for at in starts if at>start);raw=owner[start-ram:end-ram]
        if raw!=native[start-ram:end-ram]: raise ValueError('Changed complete native net callback')
        functions.append(dict(address=start,end=end,sha256=sha256(raw)))
    # The complete callback setup span proves their relocated player slots.
    start,end=0x808DD570,0x808DD690
    if owner[start-ram:end-ram]!=native[start-ram:end-ram]:
        raise ValueError('Changed native net callback installation')
    functions.append(dict(address=start,end=end,sha256=sha256(owner[start-ram:end-ram])))
    start,end=0x808CCDFC,0x808CCE18;at=start-ram
    before=owner[at:end-ram]
    if before.hex()!='80820e6c8c830f245440000424030008046100020000000024030008':
        raise ValueError('Changed native swarm-to-insect identity selection')
    sections=struct.unpack_from('>5I',rel)
    guard_incoming(owner,sections[0],ram,[(at,len(before))])
    _,_,_,locations,_=native_references(owner,rel,expected_sections=sections[:4])
    if any(p in locations for p in range(at,at+len(before),4)):
        raise ValueError('Unexpected relocation in native net identity span')
    return dict(actor_id=0xB5,part=4,bank=3,table_address=entry,profile_offset=0x14,
        core_sha256=sha256(core),owner_vrom=0x7AC420,reloc_vrom=0x7D9BA0,owner_ram=ram,
        owner_sha256=sha256(owner),reloc_sha256=sha256(rel),functions=functions,
        address=start,before=before.hex(),symbol='af_insect_hook_net_index',installed=False)


def install_colony(image,symbols,contract):
    """Compose the resident actor and catch identity, retaining current hooks."""
    files=by_vrom(image);core=bytearray(files[CODE_VROM].extract(image))
    owner=bytearray(files[contract['owner_vrom']].extract(image))
    rel=files[contract['reloc_vrom']].extract(image)
    if (sha256(core)!=contract['core_sha256'] or sha256(owner)!=contract['owner_sha256'] or
            sha256(rel)!=contract['reloc_sha256']):
        raise ValueError('Changed prepared colony actor or catch owner')
    for name in ('af_insect_colony_profile',contract['symbol']):
        if symbols[name]&3 or not 0x80000000<=symbols[name]<0x80800000:
            raise ValueError('Colony profile/code must be resident native RAM')
    at=contract['table_address']-CODE_RAM
    if core[at:at+0x20]!=bytes(0x20):raise ValueError('Occupied colony profile slot')
    struct.pack_into('>I',core,at+0x14,symbols['af_insect_colony_profile'])
    pos=contract['address']-contract['owner_ram'];before=bytes.fromhex(contract['before'])
    if owner[pos:pos+len(before)]!=before:raise ValueError('Changed colony identity hook')
    after=struct.pack('>I',0x0C000000|(symbols[contract['symbol']]>>2&0x3FFFFFF))+bytes(len(before)-4)
    owner[pos:pos+len(before)]=after
    return {CODE_VROM:bytes(core),contract['owner_vrom']:bytes(owner)},dict(contract,
        profile=symbols['af_insect_colony_profile'],after=after.hex())


def colony_assets(source,cache):
    """Reuse the full material converter for a missing field actor dependency."""
    from map_artwork import compile_commands_batch
    from v3_furniture_pipeline import prepare_models,assemble_models
    from v3_furniture_scroll import evw_scroll,CATEGORY
    path=ROOT/'local/ac-decomp/src/actor/ac_ant.c'
    digest='08ba0ac986073c6c4464c42ba537b2f306f14caa748b7e4db25ea13f5ed4c673'
    if sha256(path.read_bytes())!=digest:raise ValueError('Changed pinned colony behaviour')
    functions=[]
    for at,rows in source.functions.items():
        if any(n.startswith('aANT_') or n in ('aINS_make_ant','aINS_check_birth_ant','aINS_chk_live_ant') for n,_ in rows):
            functions.append(source.function(at)[1])
    if len(functions)!=13:raise ValueError('Incomplete colony lifecycle source')
    animation,helpers=evw_scroll(source,source.symbol('act_ant_evw_anime')[0],source.function(0x339C)[1])
    row=animation['rows'][0]
    if (len(animation['rows'])!=1 or row['segment_address']!=0x08000000 or
            [(t['width'],t['height'],t['rate']) for t in row['tiles']]!=[(32,32,[2,1]),(32,32,[1,-2])]):
        raise ValueError('Changed complete colony scrolling layout')
    adapter=dict(category=CATEGORY,scrolling=dict(row,model='colony'),model_order=['colony'],
        model_arenas={'colony':'translucent'})
    descriptor=dict(kind='creature-ground-colony',callback_adapter=adapter,
        models={'colony':('act_antT_model',*source.symbol('act_antT_model'))})
    part=prepare_models(source,descriptor)
    identity=dict(rel_sha256=sha256(source.rel),source_sha256=digest,
        commands_sha256=sha256(part[5].encode()),body_sha256=sha256(part[1]),
        converter_sha256=sha256((ROOT/'tools/v3_furniture_art.py').read_bytes()))
    if cache.exists():
        report=json.loads((cache/'colony.json').read_text());asset=(cache/'colony.bin').read_bytes()
        if report['identity']!=identity or sha256(asset)!=report['object_sha256']:
            raise ValueError('Changed prepared colony asset cache')
        return asset,report
    cache.mkdir(parents=True)
    commands=cache/'commands.c';write_new(commands,part[5].encode())
    compiled=compile_commands_batch(cache/'compiled',[('colony',commands,part[6])])
    asset,offsets,models,sequence=assemble_models(part,compiled['colony'])
    if sequence is not None or sum(m['triangles'] for m in models)!=12:
        raise ValueError('Incomplete colony geometry')
    report=dict(identity=identity,functions=functions,scrolling=animation,scroll_helpers=helpers,
        descriptor=descriptor,resources=part[2],models=models,model_offset=offsets['colony'],
        object_bytes=len(asset),object_sha256=sha256(asset),native_rates=[r['rate'] for r in row['tiles']])
    write_new(cache/'colony.bin',asset)
    write_new(cache/'colony.json',(json.dumps(report,indent=2)+'\n').encode())
    return asset,report


def rewrite(text, *, carried=False):
    """Only known ABI expressions change; retain complete source actions."""
    changes={}
    def sub(label,pattern,replacement):
        nonlocal text
        text,n=re.subn(pattern,replacement,text)
        if n: changes[label]=n
    sub('includes',r'^#include[^\n]*\n','')
    # MULTILINE is intentionally explicit: the remaining includes may follow
    # source documentation rather than starting at byte zero.
    sub('includes_remaining',r'(?m)^#include[^\n]*\n','')
    sub('tile_extension',r'\binsect->ut_([xz])',r'af_insect_extra(insect)->ut_\1')
    sub('collision_range_extension',r'\binsect->bg_range',r'af_insect_extra(insect)->bg_range')
    sub('ball_position',r'Common_Get\(ball_pos\)',r'(*af_insect_ball_position())')
    sub('demo_state',r'Common_Get\(clip\)\.demo_clip != NULL \|\| Common_Get\(clip\)\.demo_clip2 != NULL',
        'af_insect_demo_active()')
    sub('effect_call',r'eEC_CLIP->effect_make_proc','af_insect_effect')
    sub('current_block',r'actorx->block_x == play->block_table\.block_x && actorx->block_z == play->block_table\.block_z',
        'af_insect_same_block(actorx, (GAME *)play)')
    sub('source_frame',r'play->game_frame','af_insect_source_frame((GAME *)play)')
    sub('game_base',r'&play->game','(GAME *)play')
    sub('net_state',r'mPlib_get_player_actor_main_index\(game\) != mPlayer_INDEX_PUTAWAY_NET',
        '!af_insect_putting_net_away(game)')
    if carried:
        sub('absolute_float',r'\bfabsf\b','af_carried_absf')
        sub('base_frame',r'game->frame_counter','af_carried_game_frame(game)')
        sub('net_state_equal',r'mPlib_get_player_actor_main_index\(game\) == mPlayer_INDEX_PUTAWAY_NET',
            'af_insect_putting_net_away(game)')
        sub('light_context',r'&play->global_light','af_carried_insect_light_context(game)')
        sub('spirit_event_type',r'\bmEv_gst_common_c\b','AfSpiritCommon')
        sub('spirit_event_common',r'mEv_get_common_area\(mEv_EVENT_GHOST, 55\)',
            'af_carried_spirit_common()')
        sub('spirit_event_status',r'mEv_check_status\(mEv_EVENT_GHOST, mEv_STATUS_RUN\)',
            'af_carried_spirit_running()')
        sub('spirit_event_acres',r'\bmEv_GHOST_HITODAMA_NUM\b','5')
        if re.search(r'\bmEv_|->global_light|->frame_counter|mPlib_get_player_actor_main_index',text):
            raise ValueError('Unconverted carried-creature event/light access')
    # Native pointers remain 32-bit. Host fixtures retain full pointer identity.
    sub('pointer_identity',r'\(u32\)(actorx|actor)\b',r'(uintptr_t)\1')
    sub('pointer_local',r'\bu32 (label|catch_label)\b',r'uintptr_t \1')
    if re.search(r'Common_Get|->block_table|->game_frame|eEC_CLIP|#include|->ut_[xz]',text):
        # Side-storage references are the only allowed ut_x/ut_z accesses.
        rest=re.sub(r'af_insect_extra\(insect\)->ut_[xz]','',text)
        if re.search(r'Common_Get|->block_table|->game_frame|eEC_CLIP|#include|->ut_[xz]',rest):
            raise ValueError('Unconverted GameCube platform access')
    header='creature_carried.h' if carried else 'creature_insects.h'
    return '#include "'+header+'"\n'+text,changes


def program_source(source,program,*,carried=False):
    """Bind every complete function once, shared by ordinary and quest insects."""
    name,prefix,kind,digest=program
    path=ROOT/f'local/ac-decomp/src/actor/ac_ins_{name}.c'
    data=path.read_bytes()
    if sha256(data)!=digest:raise ValueError('Changed pinned insect source: '+name)
    text=data.decode();converted,edits=rewrite(text,carried=carried)
    definitions=re.findall(r'\b(?:static|extern)\s+\w+\s+('+prefix+r'_\w+)\([^;]*?\)\s*\{',text)
    functions=[]
    for function in definitions:
        addresses=[at for at,names in source.functions.items() if any(n==function for n,_ in names)]
        if len(addresses)!=1:raise ValueError('Unbound complete donor function: '+function)
        functions.append(source.function(addresses[0])[1])
    if prefix+'_actor_init' not in definitions or prefix+'_actor_move' not in definitions:
        raise ValueError('Missing insect lifecycle')
    actual={n for names in source.functions.values() for n,_ in names if n.startswith(prefix+'_')}
    if actual!=set(definitions):raise ValueError('Incomplete source insect behaviour unit')
    encoded=converted.encode()
    return encoded,dict(name=name,kind=kind,source_file=str(path.relative_to(ROOT)),
        source_sha256=digest,generated_sha256=sha256(encoded),functions=functions,platform_edits=edits)


def prepare_carried(source,output,rows,*,reuse=None):
    """Prepare the carried creature category without rebuilding installed bugs."""
    from v3_creature_field import convert
    art=convert(source,output/'field',carried_rows=rows,reuse=reuse)
    programs=[]
    expected={r['program_type'] for r in art['objects']}
    if expected!={p[2] for p in CARRIED_PROGRAMS}:
        raise ValueError('Unresolved complete carried creature program')
    for program in CARRIED_PROGRAMS:
        data,receipt=program_source(source,program,carried=True)
        receipt['species']=[r['source_index'] for r in art['objects'] if r['program_type']==program[2]]
        write_new(output/(receipt['name']+'.c'),data)
        programs.append(receipt)
    report=dict(format='AFV3-CARRIED-CREATURES-1',field=art,programs=programs,
        source_substeps=2,native_actor_bytes=0x280,installed=False,selectable=False,
        pending=['native field tables, billboard drawing, controller and light bindings',
            'actual spirit capture/release menus and stack-aware net handover',
            'Wisp event state and independent carried selection'])
    write_new(output/'carried-creatures.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


def compile_carried(output,report):
    """Compile the complete category extension, retaining unresolved services.

    Existing insect programs/buffers are linked at their checked installed
    addresses by the eventual installer, not copied or regenerated here.
    """
    flags=['-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls',
        '-fno-pic','-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector',
        '-ffunction-sections','-fdata-sections','-fstack-usage','-Wall','-Wextra','-Werror',
        '-DAF_INSECT_CARRIED','-DAF_INSECT_REUSE_BUFFERS','-I/source/overlays/v3']
    commands=['set -eu'];objects=[]
    inputs=[(p['name'],p['name']+'.c',True) for p in report['programs']]
    runtime=('creature_carried','creature_carried_draw','creature_insects','creature_insect_state',
             'creature_insect_environment','creature_insect_pool')
    inputs += [(n,'/source/overlays/v3/'+n+'.c',False) for n in runtime]
    for name,path,donor in inputs:
        objects.append(name+'.o')
        commands.append(shlex.join(['/n64_toolchain/bin/mips64-elf-gcc',*flags,
            *(['-Wno-unused-variable','-Wno-unused-parameter'] if donor else []),
            '-c',path,'-o',name+'.o']))
    commands.append(shlex.join(['/n64_toolchain/bin/mips64-elf-ld','-EB','-r',*objects,
        '-o','carried-creatures.o']))
    commands.append('/n64_toolchain/bin/mips64-elf-nm --undefined-only carried-creatures.o')
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{output.resolve()}:/out','-w','/out',
        '--entrypoint','/bin/sh',IMAGE,'-c','\n'.join(commands)]
    result=subprocess.run(docker,capture_output=True,text=True,timeout=60)
    if result.returncode:raise ValueError('Carried creature compiler failed:\n'+result.stderr)
    report['compiled']=dict(file='carried-creatures.o',
        sha256=sha256((output/'carried-creatures.o').read_bytes()),flags=flags,toolchain=IMAGE,
        runtime_sources={f'overlays/v3/{n}.c':sha256((ROOT/f'overlays/v3/{n}.c').read_bytes()) for n in runtime},
        unbound_engine_adapters=[line.split()[-1] for line in result.stdout.splitlines()])
    write_new(output/'compiled.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


def link_carried(image,prior,output,report,ram,limit):
    """Bind complete code to retained insect services and checked native bodies.

    This prepares installation; it does not redirect active cartridge callers.
    The old program buffers are reused, not allocated a second time.
    """
    if ram&15 or limit&15 or not 0x80400000<=ram<limit<=0x80800000:
        raise ValueError('Invalid carried creature link reservation')
    tree=prior['equipment_resources']['scenery']['tree_effects'];tree_packet=tree['packet']
    retained_tree=image[tree_packet['physical']:tree_packet['physical']+tree_packet['bytes']]
    if (ram!=0x80784000 or limit!=0x80786400 or tree_packet['ram']!=0x80780000 or
            tree_packet['bytes']!=0x8000 or tree['code']['bytes']>0x4000 or
            sha256(retained_tree)!=tree_packet['sha256'] or any(retained_tree[0x4000:0x7000])):
        raise ValueError('Carried creature code requires checked unused tree startup padding')
    old=prior['equipment_resources']['creature_insects'];p=old['packet']
    raw=image[p['physical']:p['physical']+p['bytes']]
    if sha256(raw)!=p['sha256']:raise ValueError('Changed installed complete insect packet')
    retained=ROOT/old['prepared_directory'];local='/source/'+str(retained.relative_to(ROOT))
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{output.resolve()}:/out','-w','/out','--entrypoint','/bin/sh',IMAGE,'-c']
    commands=[shlex.join(['/n64_toolchain/bin/mips64-elf-objcopy','-O','binary',
        '-j','.text','-j','.rodata','-j','.data',local+'/programs.elf','retained-code.bin']),
        shlex.join(['/n64_toolchain/bin/mips64-elf-nm','-S','--defined-only',local+'/programs.elf'])]
    result=subprocess.run([*docker,'set -eu\n'+'\n'.join(commands)],capture_output=True,text=True,timeout=60)
    if result.returncode:raise ValueError(result.stderr)
    code=(output/'retained-code.bin').read_bytes()
    if len(code)>old['compiled']['bss_start']-p['ram']:
        raise ValueError('Retained insect symbols exceed the installed executable')
    symbols={};sizes={}
    for line in result.stdout.splitlines():
        fields=line.split();symbols[fields[-1]]=int(fields[0],16)
        if len(fields)==4:sizes[fields[-1]]=int(fields[1],16)
    buffer=symbols['programs'];buffer_size=6*0x1C00
    if not old['compiled']['bss_start']<=buffer<buffer+buffer_size<=p['ram']+old['compiled']['bytes']:
        raise ValueError('Retained native program buffers escape their allocation')
    symbols.update(af_insect_retained_program_buffers=buffer,
        af_carried_quantity=prior['equipment_resources']['carried_items']['code']['symbols']['af_carried_quantity'],
        af_carried_prior_graphics_load=prior['equipment_resources']['creature_field']['compiled']['symbols']['af_v3_creature_graphics_load'],
        af_carried_field_info=0x80786C00,af_carried_segments=0x801458A0)
    native={'Global_light_list_delete':0x8009BBEC,'Global_light_list_new':0x8009BB8C,
        'Light_point_ct':0x8009B23C,'add_calc_short_angle2':0x8009A974,'sqrtf':0x80033470,
        'search_position_angleY':0x8009A2F8,'search_position_distanceXZ':0x8009A2B0,
        'af_carried_matrix_put':0x800E0284,'af_carried_matrix_position':0x800E141C,
        'af_carried_matrix_translate':0x800E0314,'af_carried_matrix_scale':0x800E041C,
        'af_carried_matrix_x':0x800E0500,'af_carried_matrix_y':0x800E0698,'af_carried_matrix_z':0x800E0834,
        'af_carried_matrix_new':0x800E13C4,'af_carried_shadow':0x80059A94,'af_carried_fault':0x80029AB4,
        'memcpy':0x80034BF8}
    original=verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    before_files,current_files=by_vrom(original),by_vrom(image)
    definitions=''.join((ROOT/f'upstream/af/linker_scripts/jp/symbol_addrs_{part}.txt').read_text()
        for part in ('boot','code','libultra'))
    starts=sorted({int(x,16) for x in re.findall(r'= (0x[0-9A-Fa-f]+); //[^\n]*\btype:func',definitions)})
    checked=[]
    for name,start in native.items():
        if start not in starts:raise ValueError('Unknown native carried creature function')
        end=next(at for at in starts if at>start)
        vrom,base=(0x1060,0x80025C60) if start<CODE_RAM else (CODE_VROM,CODE_RAM)
        a=before_files[vrom].extract(original)[start-base:end-base]
        b=current_files[vrom].extract(image)[start-base:end-base]
        if not a or a!=b:raise ValueError('Changed complete native service: '+name)
        checked.append(dict(symbol=name,address=start,end=end,sha256=sha256(a)))
    symbols.update(native)
    needed=report['compiled']['unbound_engine_adapters']
    missing=set(needed)-symbols.keys()
    if missing:raise ValueError('Unbound carried creature services: '+', '.join(sorted(missing)))
    bindings={n:symbols[n] for n in needed}
    retained_functions=[]
    def retain(name,address):
        if not p['ram']<=address<p['ram']+len(code):return
        size=sizes.get(name,0);at=address-p['ram']
        if not size or at+size>len(code) or code[at:at+size]!=raw[at:at+size]:
            raise ValueError('Changed complete retained insect function: '+name)
        retained_functions.append(dict(symbol=name,address=address,bytes=size,sha256=sha256(raw[at:at+size])))
    for name,address in bindings.items():retain(name,address)
    commands=[shlex.join(['/n64_toolchain/bin/mips64-elf-ld','-EB',
        f'--defsym=AF_INSECT_RAM={ram}',f'--defsym=AF_INSECT_LIMIT={limit}',
        *[f'--defsym={n}={v}' for n,v in bindings.items()],
        '-T','/source/overlays/v3/creature_insects.ld','carried-creatures.o','-o','carried-creatures.elf']),
        '/n64_toolchain/bin/mips64-elf-objcopy -O binary -j .text -j .rodata -j .data carried-creatures.elf carried-code.bin',
        '/n64_toolchain/bin/mips64-elf-nm --defined-only --extern-only carried-creatures.elf']
    result=subprocess.run([*docker,'set -eu\n'+'\n'.join(commands)],capture_output=True,text=True,timeout=60)
    if result.returncode:raise ValueError(result.stderr)
    entries=[line.split() for line in result.stdout.splitlines()]
    linked={n:int(a,16) for a,k,n in entries}
    functions={n for a,k,n in entries if k=='T'}
    redirects=[]
    for name,address in linked.items():
        if ram<=address<limit and name in symbols and name in functions:
            retain(name,symbols[name])
            redirects.append(dict(symbol=name,previous=symbols[name],target=address))
    data=(output/'carried-code.bin').read_bytes();end=linked['af_insect_runtime_end'];bss=linked['af_insect_bss_start']
    if len(data)>bss-ram or not ram<bss<=end<=limit:raise ValueError('Invalid carried runtime sections')
    data+=bytes(end-ram-len(data));write_new(output/'carried-runtime.bin',data)
    report['linked']=dict(ram=ram,limit=limit,bytes=len(data),bss_start=bss,sha256=sha256(data),
        file='carried-runtime.bin',symbols=linked,bindings=bindings,native_services=checked,
        retained_program_buffers=dict(ram=buffer,bytes=buffer_size),
        retained_functions=retained_functions,required_redirects=redirects,
        predecessor=dict(ram=p['ram'],bytes=p['bytes'],sha256=p['sha256']),
        base_sha256=sha256(image),installed=False)
    write_new(output/'linked.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


def generate(source,output,native):
    from v3_creature_spawns import insect_calendars
    parents,identity=source_records(source)
    demo=[]
    for name in ('aRSD_actor_ct','aRSD_actor_dt','aRSD_first_set_init','aRSD_retire_npc_wait',
                 'aPRD_actor_ct','aPRD_actor_dt','aBTD_actor_ct','aBTD_actor_dt'):
        matches=[at for at,rows in source.functions.items() if any(n==name for n,_ in rows)]
        if len(matches)!=1:raise ValueError('Ambiguous donor demo-state owner: '+name)
        demo.append(source.function(matches[0])[1])
    native['intro_environment']['donor_functions']=demo
    raw,table=named_table(source,'aINS_program_type',41*4)
    rows=[r for r in parents if r['category']=='insect']
    if [r['source_index'] for r in rows]!=list(range(32,40)):
        raise ValueError('Changed complete added-insect category')
    kinds=[struct.unpack_from('>I',raw,r['source_index']*4)[0] for r in rows]
    if kinds!=[3,12,9,13,11,13,11,10]:
        raise ValueError('Changed donor insect program dispatch')
    programs=[]; generated={}
    for program in PROGRAMS:
        data,receipt=program_source(source,program)
        generated[receipt['name']+'.c']=data
        receipt['species']=[r['source_index'] for r,k in zip(rows,kinds,strict=True) if k==program[2]]
        programs.append(receipt)
    output.mkdir(parents=True,exist_ok=False)
    for name,data in generated.items():write_new(output/name,data)
    art,colony=colony_assets(source,output.parent/'colony-assets')
    write_new(output/'colony.bin',art)
    write_new(output/'colony.S',('''.section .rodata
.balign 16
.globl af_insect_colony_art
af_insect_colony_art:
.incbin "colony.bin"
.balign 4
.globl af_insect_colony_art_bytes
af_insect_colony_art_bytes:
.word '''+str(len(art))+'''
.globl af_insect_colony_model
af_insect_colony_model:
.word '''+str(colony['model_offset'])+'''
.globl af_insect_colony_rates
af_insect_colony_rates:
.byte '''+','.join(str(n) for row in colony['native_rates'] for n in row)+'\n').encode())
    calendar,spawn_report=insect_calendars(source)
    write_new(output/'insect-calendar.bin',calendar)
    write_new(output/'insect-calendar.S',(''' .section .rodata
.balign 4
.globl af_insect_calendar
af_insect_calendar:
.incbin "insect-calendar.bin"
.balign 4
.globl af_insect_calendar_bytes
af_insect_calendar_bytes:
.word '''+str(len(calendar))+'\n').encode())
    return dict(format='AFV3-CREATURE-INSECT-PROGRAMS-1',source=identity,dispatch=table,native_abi=native,
        spawning=spawn_report,colony=colony,
        rows=[dict(r,program=k) for r,k in zip(rows,kinds,strict=True)],programs=programs,
        source_version='GAFE01_00',donor_bugfixes=False,
        source_rate=60,native_rate=30,source_substeps=2,
        native_actor_bytes=0x174,native_insect_bytes=0x280,native_controller_slots=9,
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES},
        installed=False,selectable=False,native_execution_tested=False)


def compile_programs(output,report,link_ram=None,link_limit=None):
    """One compiler container for the whole category, without invented bindings."""
    flags=['-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls',
        '-fno-pic','-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector',
        '-ffunction-sections','-fdata-sections','-fstack-usage','-Wall','-Wextra','-Werror',
        '-I/source/overlays/v3']
    donor_flags=['-Wno-unused-parameter','-Wno-unused-variable']
    commands=[];objects=[]
    for name,_,_,_ in PROGRAMS:
        objects.append(name+'.o')
        commands.append(shlex.join(['/n64_toolchain/bin/mips64-elf-gcc',*flags,*donor_flags,
                                   '-c',name+'.c','-o',name+'.o']))
    for source in RUNTIME:
        objects.append(source+'.o')
        commands.append(shlex.join(['/n64_toolchain/bin/mips64-elf-gcc',*flags,'-c',
            '/source/overlays/v3/'+source+'.c','-o',source+'.o']))
    for source in report['persistent_seasons']['compilation']:
        name=source['file'];objects.append(name+'.o')
        commands.append(shlex.join(['/n64_toolchain/bin/mips64-elf-gcc',*flags,
            *['-D'+d for d in source['defines']],'-c',
            '/source/overlays/v3/'+name+'.c','-o',name+'.o']))
    objects.append('creature_insect_hooks.o')
    commands.append(shlex.join(['/n64_toolchain/bin/mips64-elf-gcc',*flags,'-c',
        '/source/overlays/v3/creature_insect_hooks.S','-o','creature_insect_hooks.o']))
    objects.append('insect-calendar.o')
    commands.append(shlex.join(['/n64_toolchain/bin/mips64-elf-gcc',*flags,'-c',
        'insect-calendar.S','-o','insect-calendar.o']))
    objects.append('colony.o')
    commands.append(shlex.join(['/n64_toolchain/bin/mips64-elf-gcc',*flags,'-c',
        'colony.S','-o','colony.o']))
    objects.append('field-audio.o')
    commands.append(shlex.join(['/n64_toolchain/bin/mips64-elf-gcc',*flags,'-c',
        'field-audio.S','-o','field-audio.o']))
    commands.append(shlex.join(['/n64_toolchain/bin/mips64-elf-ld','-EB','-r',
        *objects,'-o','programs.o']))
    commands.append('/n64_toolchain/bin/mips64-elf-nm --undefined-only programs.o')
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
            '-v',f'{ROOT}:/source:ro','-v',f'{output.resolve()}:/out','-w','/out',
            '--entrypoint','/bin/sh',IMAGE,'-ec','\n'.join(commands)]
    result=subprocess.run(docker,text=True,capture_output=True,timeout=60)
    if result.returncode: raise RuntimeError(result.stderr)
    required=sorted(line.split()[-1] for line in result.stdout.splitlines() if line.strip())
    bindings={name:int(value,16) for name,value in re.findall(r'^(\w+) = (0x[0-9A-Fa-f]+);',
        (ROOT/'overlays/v3/creature_insect_bindings.ld').read_text(),re.M)}
    bindings.update(report['persistent_seasons']['bindings'])
    undefined=sorted(set(required)-bindings.keys())
    report['compiled']=dict(object='programs.o',sha256=sha256((output/'programs.o').read_bytes()),
        bytes=(output/'programs.o').stat().st_size,toolchain=IMAGE,flags=flags,donor_flags=donor_flags,
        unbound_engine_adapters=undefined,engine_bindings={n:bindings[n] for n in required if n in bindings},
        stack_usage=''.join(p.read_text() for p in sorted(output.glob('*.su'))))
    if link_ram is not None:
        if undefined or link_ram&15 or not 0x80000000<=link_ram<link_limit<=0x80800000:
            raise ValueError('Unbound or invalid complete insect runtime placement')
        commands=[shlex.join(['/n64_toolchain/bin/mips64-elf-ld','-EB',
            f'--defsym=AF_INSECT_RAM={link_ram}',f'--defsym=AF_INSECT_LIMIT={link_limit}',
            *[f'--defsym={name}={address}' for name,address in report['persistent_seasons']['bindings'].items()],
            '-T','/source/overlays/v3/creature_insect_bindings.ld',
            '-T','/source/overlays/v3/creature_insects.ld','programs.o','-o','programs.elf']),
            '/n64_toolchain/bin/mips64-elf-objcopy -O binary -j .text -j .rodata -j .data programs.elf programs-code.bin',
            '/n64_toolchain/bin/mips64-elf-nm --defined-only programs.elf']
        result=subprocess.run([*docker[:-1],'\n'.join(commands)],text=True,capture_output=True,timeout=60)
        if result.returncode:raise RuntimeError(result.stderr)
        symbols={name:int(address,16) for address,kind,name in
            (line.split() for line in result.stdout.splitlines())
            if name.startswith('af_') or name=='require_state'}
        code=(output/'programs-code.bin').read_bytes();end=symbols['af_insect_runtime_end']
        if len(code)>symbols['af_insect_bss_start']-link_ram or end>link_limit:
            raise ValueError('Complete insect initialized data overlaps BSS')
        data=code+bytes(end-link_ram-len(code));write_new(output/'programs.bin',data)
        report['linked']=dict(ram=link_ram,bytes=len(data),sha256=sha256(data),symbols=symbols,
            file='programs.bin',bss_start=symbols['af_insect_bss_start'],bss_zeroed=True,
            cartridge_allocation_verified=False,installed=False)
    report['pending']=[
        'Install prepared mosquito actions, full motions/face timelines, and official message with the runtime',
        'Install complete prepared field sound resources together with the runtime',
        'Install prepared small-mud constructor bridge with the complete runtime',
        'Install prepared controller, spawn-manager, and directed-column hooks with the complete runtime',
        'Install prepared digging, rock-strike, and all-season tree-shake event producers',
        'Install prepared format-nine persistence and all stable save-entry redirects with the runtime',
        'Install prepared colony profile/catch hook and included art with complete runtime startup',
        'Install prepared two/eight wild-slot population alternatives and complete expanded controller',
        'Guarded packet placement/startup and optional/behaviour selections',
        'Connected native gameplay/save verification; existing unresolved fixtures are not reset']
    write_new(output/'programs.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--base-lock',type=Path,required=True)
    parser.add_argument('--link-ram',type=lambda x:int(x,0))
    parser.add_argument('--link-limit',type=lambda x:int(x,0))
    parser.add_argument('--carried-items',type=Path,
        help='Prepare only field creatures from the installed carried bundle; reuse all ordinary insects')
    parser.add_argument('--reuse-field',type=Path,help='Reuse the complete checked field objects without compiling graphics')
    args=parser.parse_args()
    if (args.link_ram is None)!=(args.link_limit is None):parser.error('Supply both link bounds')
    if args.reuse_field and not args.carried_items:parser.error('--reuse-field requires --carried-items')
    from v3_furniture_install import inputs
    image,prior=inputs(args.base_lock)
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    if args.carried_items:
        from v3_carried_items import records
        carried=prior['equipment_resources']['carried_items']
        if args.carried_items.resolve()!=ROOT/carried['prepared']:
            raise ValueError('Carried field preparation does not match the installed bundle')
        prepared=json.loads((args.carried_items/'items.json').read_bytes())
        rows,receipt=records(source,ROOT/'build/item-identity-megasheet.xlsx',prepared['installed_imports'])
        if prepared['rows']!=rows or any(prepared[k]!=json.loads(json.dumps(v)) for k,v in receipt.items()):
            raise ValueError('Changed complete carried source identity')
        report=compile_carried(args.output,prepare_carried(source,args.output,rows,reuse=args.reuse_field))
        if args.link_ram is not None:
            report=link_carried(image,prior,args.output,report,args.link_ram,args.link_limit)
        print(json.dumps(dict(programs=len(report['programs']),field=report['field']['counts'],
            unbound_engine_adapters=report['compiled']['unbound_engine_adapters'],installed=False),indent=2))
        return
    native=native_contract(image,prior)
    from v3_creature_insect_audio import write_prepared
    report=generate(source,args.output,native)
    report['field_audio']=write_prepared(image,prior,source,args.output/'field-audio')
    from v3_creature_insect_effects import contract as effect_contract
    report['field_effects']=effect_contract(image,prior,source)
    from v3_creature_insect_player import contract as player_contract,prepare_mosquito
    report['player_interactions']=player_contract(image,prior,source)
    report['mosquito_player']=prepare_mosquito(image,prior,source,args.output/'mosquito-player')
    from v3_creature_save import prepare_insects
    report['persistent_seasons']=prepare_insects(prior)
    from v3_creature_insect_pool import contract as pool_contract
    report['population']=pool_contract(image,source)
    write_new(args.output/'field-audio.S',b'''.section .rodata
.balign 4
.globl af_insect_trigger_words
af_insect_trigger_words:
.incbin "field-audio/bindings.bin"
.balign 4
.globl af_insect_tree_bee_query
af_insect_tree_bee_query:
'''+f".word {report['player_interactions']['bee_query']}\n".encode()+b'''.globl af_insect_mosquito_message
af_insect_mosquito_message:
'''+f".word {report['mosquito_player']['text']['id']}\n".encode()+b'''.balign 4
.globl af_insect_player_faces
af_insect_player_faces:
.incbin "mosquito-player/face-data.bin"
''')
    report=compile_programs(args.output,report,args.link_ram,args.link_limit)
    print(json.dumps(dict(programs=len(report['programs']),species=len(report['rows']),
        unbound_engine_adapters=report['compiled']['unbound_engine_adapters'],installed=False),indent=2))


if __name__=='__main__':main()
