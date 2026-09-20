"""Shared player action tables and relocation-aware native dispatch.

Keep every original action. Reserve the donor's additional action indices with
their actual metadata, but null callbacks until their complete implementations
are installed. Shared category stages register complete actions and equipment
readers without claiming unfinished inventory/acquisition or adding choices.
"""
import copy
import re
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from v3_asset_loader import BLOB, ROOT, compile_part
from v3_equipment_runtime import RAM, SIZE, GUARD, PLAYER_RAM, PLAYER_VROM, PLAYER_RELOC
from v3_furniture_pipeline import Source
from v3_import_storage import END, jump
from v3_npc_draw import relocation_offsets
import v3_sound_programs as sound_programs

NATIVE_COUNT, COUNT = 105, 121
CODE_OFFSET, TABLE_OFFSET, MODULE_SIZE = 0x2000, 0x4000, 0x6000
CTOR, CTOR_SLOT, TEXT_SIZE = 0x808DD748, 0x80143900, 0x2AF00
# Source consumer, native consumer, native bound, native table, record width.
# These are engine categories, not individual item definitions.
CATEGORIES = (
    (0x164E9C,0x808B3370,0x808B3388,0x808DDE88,1),
    (0x164EEC,0x808B33B8,0x808B33D0,0x808DDEF4,1),
    (0x165030,0x808B34E8,0x808B3504,0x808DDF60,1),
    (0x1650DC,0x808B3584,0x808B359C,0x808DDFCC,1),
    (0x165124,0x808B35C8,0x808B35D8,0x808DE038,1),
    (0x1651AC,0x808B3648,0x808B3668,0x808DE0A4,1),
    (0x165440,0x808B3960,0x808B397C,0x808DE118,1),
    (0x1655DC,0x808B3A84,0x808B3AB4,0x808DE184,1),
    (0x165664,0x808B3B08,0x808B3B20,0x808DE1F0,1),
    (0x167F84,0x808B63B4,0x808B63C4,0x808DE56C,1),
    (0x167FC0,0x808B63EC,0x808B63FC,0x808DE5D8,1),
    (0x167FFC,0x808B6424,0x808B6434,0x808DE644,1),
    (0x169AC4,0x808B828C,0x808B82B8,0x808DE6F0,1),
    (0x16A170,0x808B8778,0x808B87A0,0x808DE75C,1),
    (0x16A1DC,0x808B87C8,0x808B87D8,0x808DE7C8,1),
    (0x16A5A4,0x808B8B00,0x808B8B24,0x808DE834,1),
    (0x16C7D8,0x808BAC20,0x808BAC70,0x808DF2BC,1),
    (0x16CFFC,0x808BB43C,0x808BB458,0x808DF328,1),
    (0x16EE78,0x808BBDE8,0x808BBE28,0x808DF3A0,1),
    (0x16DB2C,0x808BBF38,0x808BBF6C,0x808DF40C,1),
    (0x16E074,0x808BC308,0x808BC330,0x808DF49C,1),
    (0x16427C,0x808DDBD4,0x808DDBF4,0x808E00E4,1),
    (0x17199C,0x808BE620,0x808BE63C,0x808DF628,4),
    (0x163E98,0x808DD874,0x808DD8B4,0x808DFA54,4),
    (0x164008,0x808DD9B4,0x808DD9D4,0x808DFBF8,4),
    (0x164094,0x808DDA18,0x808DDA58,0x808DFD9C,4),
    (0x1641E8,0x808DDB5C,0x808DDB90,0x808DFF40,4),
)
DISPATCH = ((0x808BE658,2),(0x808DD8D0,2),(0x808DD9F4,2),
            (0x808DDAFC,25),(0x808DDBB0,2))
HELD_CATEGORIES=((0x173B38,0x808BF410,0x808BF424,0x808DF7F8,4),
                 (0x173BCC,0x808BF494,0x808BF4AC,0x808DF84C,4))
POLL_SITES=((0x808C12EC,0x808C1270,0x808C1370),
            (0x808C1CE4,0x808C1C48,0x808C1DB8),
            (0x808C2194,0x808C20F8,0x808C223C),
            (0x808C2A38,0x808C2994,0x808C2B78))
# This address is also the exclusive end of the PRECEDING eight-float array.
# The spatial-search loop compares its incrementing pointer against this end;
# moving that boundary to the new action table would overrun its stack buffer.
RETAINED_BOUNDARY = (0x808B99D0,0x808B99D8,0x808DF2BC)
SOURCES = ('tools/v3_player_actions.py','tools/v3_furniture_pipeline.py',
           'tools/v3_asset_loader.py','overlays/v3/startup.c',
           'overlays/v3/player_actions.S','overlays/v3/player_actions.c',
           'overlays/v3/player_actions.ld','overlays/v3/held_selection.c',
           'overlays/v3/held_items.c','overlays/v3/held_items.ld',
           'overlays/v3/held_icon.S',
           'tools/v3_handheld_items.py','tools/v3_inventory_equipment.py',
           'overlays/v3/inventory_equipment.c','overlays/v3/inventory_equipment.S',
           'overlays/v3/inventory_equipment.ld',
           'overlays/v3/held_rigs.c','overlays/v3/held_rigs.S',
           'overlays/v3/held_rigs.ld','overlays/v3/tool_controls.c',
           'overlays/v3/tool_motion.c','overlays/v3/tool_motion.S',
           'overlays/v3/tool_motion.ld','overlays/v3/tool_recovery.c') + sound_programs.SOURCES

SELECTION_OFFSET=0x5500
PARENT_CODE_OFFSET,PARENT_TABLE_OFFSET=0x3000,0x57F0
POCKET_ICON_OFFSET=0x3800
RIG_CODE_OFFSET,RIG_MODULE_SIZE=0xD000,0xE000
RIG_STATE_OFFSET,RIG_STATE_BYTES,RIG_PLAYER_SIZE=0x12D8,44,0x1310
BALLOON_MODULE_SIZE,BALLOON_STATE_OFFSET,BALLOON_STATE_BYTES=0xF000,0x1370,48
TOOL_MOTION_OFFSET=0x2A50


def refresh_tool_transitions(base,prior,blob,core,original,output):
    """Reuse family predicates and connect complete native fall/get-up setup."""
    from v3_npc_clothing import guard_incoming
    old=prior['equipment_resources'];actions=old['player_actions'];start=old['blob_offset']
    module=bytearray(blob[start:start+old['bytes']]);files=by_vrom(base)
    owner=bytearray(files[PLAYER_VROM].extract(base));rel=files[PLAYER_RELOC].extract(base)
    native=by_vrom(original)[PLAYER_VROM].extract(original)
    if (not actions.get('tool_motion') or actions.get('tool_transitions')
            or sha256(module)!=old['sha256'] or sha256(owner)!=actions['owner_sha256']
            or sha256(rel)!=actions['relocation_sha256']):
        raise ValueError('Tool transitions require the complete current motion adapter')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    specs=(
        (0x181878,152,'55fc16e02b1da0d11d183d8c757c6b8a3887d6640ea3c8c13b716f40959d18cb',0x808CB32C,0x808CB39C),
        (0x181C08,188,'57cd9bf4604734f438d82ed17cad3b897a396fcbc98cbe1a33277d165356bae5',0x808CB6BC,0x808CB74C),
        (0x182828,152,'fa202c92f3b781575a5ade65edf058eb6b0c6f23a2c24ca6e5e48355fd18484b',0x808CC108,0x808CC178),
        (0x1834DC,152,'f3c02733fed4281ad2e5b67017234e99230ab72f0faebcdda8760a7951e7301a',0x808CCCF4,0x808CCD64),
        (0x177924,240,'76fde36fbf55619f244b6d24cea2f2919baed7ca2f86e05ad19a2cec78c4a3c1',0x808C2C8C,0x808C2D4C),
        (0x177F98,428,'44ca596f5c0684acaa9d51a3148110bd2ed9cb5e78702db6bea0ed3ae17df7c4',0x808C320C,0x808C32CC))
    _,_,rows,locations,_=native_references(owner,rel)
    sources=[];consumers=[];patches=[];removed=[]
    for offset,n,digest,first,last in specs:
        raw,receipt=source.function(offset)
        if len(raw)!=n or sha256(raw)!=digest:raise ValueError('Changed complete source net transition')
        a,b=first-PLAYER_RAM,last-PLAYER_RAM
        if owner[a:b]!=native[a:b]:raise ValueError('Changed complete native net transition')
        sources.append(receipt);consumers.append(dict(entry=first,end=last,sha256=sha256(owner[a:b])))
        if len(sources)<=4:
            calls=[i for i in range(a,b,4) if u32(owner,i)==jump(0x808BD5C4,link=True)]
            if len(calls)!=1 or locations.get(calls[0],0)>>24!=0x44:
                raise ValueError('Net transition lacks one relocated visible-kind call')
            at=calls[0];after=jump(actions['tool_controls']['entry'],link=True)
            patches.append(dict(address=PLAYER_RAM+at,before=owner[at:at+4].hex(),after=struct.pack('>I',after).hex()))
            removed.append(locations[at]);consumers[-1]['call']=PLAYER_RAM+at
    previous=actions['tool_motion']['code'];at=TOOL_MOTION_OFFSET;n=previous['bytes']
    if sha256(module[at:at+n])!=previous['sha256'] or any(module[at+n:PARENT_CODE_OFFSET]):
        raise ValueError('Changed tool-motion code or occupied transition space')
    code,compiled=compile_part('tool_motion',output/'tool_motion',
        extra_sources=('overlays/v3/tool_motion.S','overlays/v3/tool_recovery.c'))
    if (code[:n]!=module[at:at+n] or len(code)>PARENT_CODE_OFFSET-at
            or any(compiled['symbols'].get(k)!=v for k,v in previous['symbols'].items())):
        raise ValueError('Tool recovery moves existing motion code/constants')
    windows=[]
    for entry,name in ((0x808C2C8C,'af_v3_tool_tumble'),(0x808C320C,'af_v3_tool_getup')):
        pos=entry-PLAYER_RAM;windows.append((pos,8))
        if any(x in locations for x in (pos,pos+4)):raise ValueError('Relocated recovery entry')
        patches.append(dict(address=entry,before=owner[pos:pos+8].hex(),
            after=struct.pack('>2I',jump(compiled['symbols'][name]),0).hex(),symbol=name))
    guard_incoming(owner,TEXT_SIZE,PLAYER_RAM,windows)
    for row in patches:
        pos=row['address']-PLAYER_RAM;replacement=bytes.fromhex(row['after'])
        owner[pos:pos+len(replacement)]=replacement
    kept=[r for r in rows if r not in removed];relocated=bytearray(rel)
    struct.pack_into('>I',relocated,16,len(kept))
    relocated[20:20+len(rows)*4]=struct.pack('>'+str(len(kept))+'I',*kept)+bytes(4*len(removed))
    module[at:PARENT_CODE_OFFSET]=code+bytes(PARENT_CODE_OFFSET-at-len(code))
    blob[start:start+len(module)]=module
    report=copy.deepcopy(old);current=report['player_actions']
    current.update(owner_sha256=sha256(owner),relocation_sha256=sha256(relocated),
        removed_relocations=current['removed_relocations']+len(removed))
    current['tool_motion']['code']=compiled
    current['tool_transitions']=dict(format='AFV3-TOOL-TRANSITIONS-1',code=compiled,
        source_functions=sources,native_consumers=consumers,patches=patches,removed_relocations=removed,
        actual_kinds_retained=True,priorities_retained=True,golden_effects_installed=False,
        balloon_release_installed=False,logical_imports_added=0,ordinary_gameplay_tested=False)
    report['player_motion'].update(owner_sha256=sha256(owner),reloc_sha256=sha256(relocated))
    report.update(sha256=sha256(module),crc32=zlib.crc32(module))
    return report,{PLAYER_VROM:bytes(owner),PLAYER_RELOC:bytes(relocated)}


def refresh_tool_motion(base,prior,blob,core,original,output):
    """Connect action motions to complete net/rod rigs through shared setup."""
    from v3_npc_clothing import guard_incoming
    old=prior['equipment_resources'];actions=old['player_actions'];start=old['blob_offset']
    module=bytearray(blob[start:start+old['bytes']]);files=by_vrom(base)
    owner=bytearray(files[PLAYER_VROM].extract(base));rel=files[PLAYER_RELOC].extract(base)
    native_files=by_vrom(original);native=native_files[PLAYER_VROM].extract(original)
    if (not actions.get('tool_controls') or actions.get('tool_motion')
            or sha256(module)!=old['sha256'] or sha256(owner)!=actions['owner_sha256']
            or sha256(rel)!=actions['relocation_sha256']
            or CODE_OFFSET+actions['code']['bytes']>TOOL_MOTION_OFFSET
            or any(module[TOOL_MOTION_OFFSET:PARENT_CODE_OFFSET])):
        raise ValueError('Tool motions require the checked complete tool-control proposal')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    sources=[]
    for at,n,digest in (
        (0x169E5C,196,'b1c13a93ee0e9632ad9e8d6b706f12f9b169901d524514b54da89b35eba50cde'),
        (0x169F20,268,'45a25c5c34ced37de5ca38ec520cbe5bc9ee8787d1966b2538268548ea1498d1'),
        (0x1710D4,352,'7aa8f6cde60b847553056c7ec80c3eab6ef33f22490419bcffe2c62d153bbc5c'),
        (0x171B20,216,'6731aa36ac2e84707d6709a7f3f33162c1db9192ec2c06866371dd092727782e'),
        (0x172728,212,'01e1ea69910aecdaabe60499c6a02570d9d5deaa01ab4c8140ed3593f349ceac'),
        (0x171AAC,116,'09c5cfb93402bbd45fb3781050b3826ad883aa2080c0691ba07cdeca558e3389'),
        (0x1726B4,116,'39eef516e44d182bed159f1d580f028a5657ff2703bc99b151d585d89f9e3516')):
        raw,receipt=source.function(at)
        if len(raw)!=n or sha256(raw)!=digest:raise ValueError('Changed complete donor tool setup/drawing')
        sources.append(receipt)
    consumers=[]
    for first,last in ((0x808B84DC,0x808B8628),(0x808BDDB4,0x808BDEF0),
                       (0x808BDF6C,0x808BE000),(0x808BE670,0x808BE85C),
                       (0x808BE8C4,0x808BF360)):
        a,b=first-PLAYER_RAM,last-PLAYER_RAM
        if owner[a:b]!=native[a:b]:raise ValueError('Changed complete native tool setup/drawing')
        consumers.append(dict(entry=first,end=last,sha256=sha256(native[a:b])))
    native_core=native_files[CODE_VROM].extract(original)
    types=native_core[0x8010BF74-CODE_RAM:0x8010BF74-CODE_RAM+17]
    if types!=bytes((0,1,2,2,2,2,2,2,2,1,3,3,3,3,3,3,0)):
        raise ValueError('Changed native tool resource categories')
    resources={r['index']:r for r in old['records']};rigs=[];motion_map=[]
    for first,count,delta,typ,joints,models,shown in ((2,7,21,2,6,(21,22),3),(10,6,22,3,5,(30,31),4)):
        for index in range(first,first+count):
            r=resources[index+delta]
            if r['kind']!='animation' or r['type']!=typ or r['source']['joints']!=joints:
                raise ValueError('Incomplete source tool animation family')
            motion_map.append(dict(native=index,imported=index+delta,type=typ,sha256=r['sha256']))
        for index in models:
            r=resources[index];s=r['source']['skeleton']
            if (r['kind']!='animated-model' or r['type']!=1 or s['joints']!=joints
                    or s['shown_joints']!=shown or joints+1>old['player_joint_work']['vectors']
                    or r['bytes']+max(resources[i+delta]['bytes'] for i in range(first,first+count))>
                        old['animated_rigs']['allocation']['bank_bytes']):
                raise ValueError('Complete tool rig exceeds native skeleton or bank capacity')
            rigs.append(dict(index=index,joints=joints,shown_joints=shown,sha256=r['sha256']))
    # Both retained after-joint tables use the same source joint meanings.
    for at,expected in ((0x808DF7CC,(0,0,0,0x808BE6DC,0,0)),
                        (0x808DF7E4,(0,0,0,0,0x808BF1E8))):
        if struct.unpack_from('>'+str(len(expected))+'I',owner,at-PLAYER_RAM)!=expected:
            raise ValueError('Changed native tool joint callback layout')
    code,compiled=compile_part('tool_motion',output/'tool_motion',extra_sources=('overlays/v3/tool_motion.S',))
    if len(code)>PARENT_CODE_OFFSET-TOOL_MOTION_OFFSET:raise ValueError('Tool setup exceeds reservation')
    _,_,_,locations,_=native_references(owner,rel)
    hooks=((0x808B84DC,'af_v3_tool_action_setup',False,8),
           (0x808B856C,'af_v3_tool_moving_setup',False,8),
           (0x808BDEC4,'af_v3_tool_rod_lifetime',True,4))
    guard_incoming(owner,TEXT_SIZE,PLAYER_RAM,[(at-PLAYER_RAM,n) for at,_,_,n in hooks])
    patches=[]
    for address,name,link,n in hooks:
        at=address-PLAYER_RAM
        if any(i in locations for i in range(at,at+n,4)):raise ValueError('Relocated tool setup hook')
        before=bytes(owner[at:at+n]);after=struct.pack('>I',jump(compiled['symbols'][name],link=link))+bytes(n-4)
        if link and before!=bytes.fromhex('24010022'):raise ValueError('Changed rod lifetime predicate')
        owner[at:at+n]=after
        patches.append(dict(address=address,before=before.hex(),after=after.hex(),symbol=name))
    module[TOOL_MOTION_OFFSET:TOOL_MOTION_OFFSET+len(code)]=code
    blob[start:start+len(module)]=module
    report=copy.deepcopy(old);current=report['player_actions']
    current.update(owner_sha256=sha256(owner))
    current['tool_motion']=dict(format='AFV3-TOOL-MOTION-1',code=compiled,code_offset=TOOL_MOTION_OFFSET,
        source_functions=sources,native_consumers=consumers,patches=patches,motion_map=motion_map,rigs=rigs,
        native_drawers_retained=True,actual_kinds_retained=True,rod_lifetime_connected=True,
        golden_effects_installed=False,logical_imports_added=0,ordinary_gameplay_tested=False)
    report['player_motion'].update(owner_sha256=sha256(owner))
    report.update(sha256=sha256(module),crc32=zlib.crc32(module))
    return report,{PLAYER_VROM:bytes(owner)}


def refresh_tool_controls(base,prior,blob,core,original,output):
    """Extend shared input predicates without changing actual equipment IDs."""
    old=prior['equipment_resources'];actions=old['player_actions'];start=old['blob_offset']
    module=bytearray(blob[start:start+old['bytes']]);files=by_vrom(base)
    owner=bytearray(files[PLAYER_VROM].extract(base));rel=files[PLAYER_RELOC].extract(base)
    native=by_vrom(original)[PLAYER_VROM].extract(original)
    if (actions.get('tool_controls') or not old.get('inventory_preview',{}).get('balloon_drawer')
            or sha256(module)!=old['sha256'] or sha256(owner)!=actions['owner_sha256']
            or sha256(rel)!=actions['relocation_sha256']):
        raise ValueError('Tool controls require the complete current equipment module')
    previous=actions['code'];at=CODE_OFFSET;n=previous['bytes'];limit=PARENT_CODE_OFFSET
    if sha256(module[at:at+n])!=previous['sha256'] or any(module[at+n:limit]):
        raise ValueError('Changed action-code reservation before shared tool controls')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    specs=(
        ('Pickup',0x164324,152,'21df739a8363df4f676e21edb6256fedeb70b9a186e1fb7f5adda2b66ec65b68',0x808B2D50,0x808B2DE4),
        ('Axe',0x1643BC,124,'4fdabbae802568a90fec294d0bf9707a13b2bfb3288d9bee446ab6e06521e137',0x808B2DE4,0x808B2E4C),
        ('Net',0x164438,124,'667daedb17150ced36643148578bb42b10e7d884f8c2d7bbb88900c2ce540e2a',0x808B2E4C,0x808B2EB8),
        ('Rod',0x1644B4,124,'4462d5c6d71c2531e62915097da7c6a2e5b8e76b2431a6f255a8b4ca5ffac650',0x808B2EB8,0x808B2F24),
        ('Scoop',0x164530,124,'de3fb93262a497cfa23d2005eb3b23b17b1ad6ff3442a0bc07fc2303c78551ff',0x808B2F24,0x808B2F90),
        ('Shake_tree',0x1646DC,228,'986de9cd1b5a36444a1a2ada4f0c76fbc584ac90ad8596974b5964d1c37de5e0',0x808B3010,0x808B30B4))
    _,_,records,locations,_=native_references(owner,rel)
    sources=[];consumers=[];removed=[];patches=[]
    expected_call=jump(0x808BD5C4,link=True)
    for name,offset,size,digest,first,last in specs:
        raw,receipt=source.function(offset)
        if (receipt['symbol']!='Player_actor_CheckController_for'+name or len(raw)!=size or sha256(raw)!=digest):
            raise ValueError('Changed complete donor tool input predicate')
        a,b=first-PLAYER_RAM,last-PLAYER_RAM
        if owner[a:b]!=native[a:b]:raise ValueError('Changed complete native tool input predicate')
        calls=[i for i in range(a,b,4) if u32(owner,i)==expected_call]
        if len(calls)!=1 or locations.get(calls[0],0)>>24!=0x44:
            raise ValueError('Tool predicate lacks one native relocated kind call')
        call=calls[0];removed.append(locations[call]);sources.append(receipt)
        consumers.append(dict(symbol=receipt['symbol'],entry=first,end=last,
            sha256=sha256(owner[a:b]),call=PLAYER_RAM+call))
        patches.append(dict(offset=call,before=expected_call))
    # Append the common adapter while requiring every existing callback and
    # public reader address to stay fixed; no incidental rebinding is needed.
    code,compiled=compile_part('player_actions',output/'player_actions',
        primary_source='overlays/v3/player_actions.S',
        extra_sources=('overlays/v3/player_actions.c','overlays/v3/held_selection.c','overlays/v3/tool_controls.c'),
        defines=tuple(flag[2:] for flag in previous['flags'] if flag.startswith('-D')))
    if (len(code)>limit-at or code[:n]!=module[at:at+n] or
            any(compiled['symbols'].get(k)!=v for k,v in previous['symbols'].items())):
        raise ValueError('Shared tool controls move or change installed action code')
    target=compiled['symbols']['af_v3_player_control_kind']
    for row in patches:
        row['after']=jump(target,link=True)
        struct.pack_into('>I',owner,row['offset'],row['after'])
    remaining=[r for r in records if r not in removed]
    relocated=bytearray(rel);struct.pack_into('>I',relocated,16,len(remaining))
    relocated[20:20+len(records)*4]=struct.pack('>'+str(len(remaining))+'I',*remaining)+bytes(4*len(removed))
    module[at:limit]=code+bytes(limit-at-len(code))
    blob[start:start+len(module)]=module
    report=copy.deepcopy(old);current=report['player_actions']
    current.update(code=compiled,owner_sha256=sha256(owner),relocation_sha256=sha256(relocated),
        patches=current['patches']+patches,removed_relocations=current['removed_relocations']+len(removed))
    current['tool_controls']=dict(format='AFV3-TOOL-CONTROLS-1',source_functions=sources,
        consumers=consumers,patches=patches,removed_relocations=removed,entry=target,
        original_kinds=36,extended_kinds=79,actual_kind_retained=True,
        umbrella_spin_retained=True,profile_bits_enabled=0,logical_imports_added=0,
        golden_effects_installed=False,ordinary_gameplay_tested=False)
    report['player_motion'].update(owner_sha256=sha256(owner),reloc_sha256=sha256(relocated))
    report.update(sha256=sha256(module),crc32=zlib.crc32(module))
    return report,{PLAYER_VROM:bytes(owner),PLAYER_RELOC:bytes(relocated)}


def refresh_balloon_actions(base,prior,blob,core,original,output):
    """Extend the shared held categories; inventory/parents remain independent."""
    old=prior['equipment_resources'];rigs=old['held_rig_actions'];position=old['blob_offset']
    module=bytearray(blob[position:position+old['bytes']]);files=by_vrom(base)
    owner=bytearray(files[PLAYER_VROM].extract(base));rel=files[PLAYER_RELOC].extract(base)
    native_files=by_vrom(original);native_owner=native_files[PLAYER_VROM].extract(original)
    native_core=native_files[CODE_VROM].extract(original)
    if (rigs.get('balloon') or not rigs.get('loop_sound_installed') or old['bytes']!=RIG_MODULE_SIZE
            or sha256(module)!=old['sha256'] or old['ram']!=RAM
            or sha256(owner)!=old['player_motion']['owner_sha256']
            or sha256(rel)!=old['player_motion']['reloc_sha256']
            or old.get('player_joint_work',{}).get('vectors',0)<8
            or old['inventory_preview'].get('joint_work',{}).get('vectors',0)<8
            or struct.unpack_from('>4I',module,len(module)-16)!=(GUARD,)*4
            or RAM+BALLOON_MODULE_SIZE>prior['furniture']['bank_pool']['start']):
        raise ValueError('Balloon actions require the complete current eight-vector rig module')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    names=('Player_actor_Item_Get_goal_balloon_lean_angle','Player_actor_Item_Setup_main_balloon_normal',
        'Player_actor_Item_set_balloon_lean_angle','Player_actor_Item_CulcAnimation_balloon_normal',
        'Player_actor_Item_Movement_balloon_normal','Player_actor_Item_PlayAnimation_balloon_normal',
        'Player_actor_Item_main_balloon_normal','Player_actor_Item_draw_balloon_Before',
        'Player_actor_Item_draw_balloon_After','Player_actor_Item_draw_balloon',
        'Player_actor_draw_After_hand','Player_actor_Set_now_item_main_index','Player_actor_Item_Setup_main',
        'Player_actor_SetupItem_Base0')
    functions=[]
    for name in names:
        matches=[at for at,rows in source.functions.items() if any(n==name for n,_ in rows)]
        if len(matches)!=1:raise ValueError('Missing complete source balloon callback: '+name)
        functions.append(source.function(matches[0])[1])
    rows=[r for r in old['kind_readers']['rows'] if r['item_main']==21]
    resources={r['index']:r for r in old['records']}
    if (sorted(r['native_kind'] for r in rows)!=list(range(91,99))
            or any(not r['resource_ready'] or r['selectable'] or
                   resources[r['fields'][2]]['kind']!='animated-model' or
                   resources[r['fields'][2]]['source']['profile']['skeleton']['joints']!=7
                   for r in rows)):
        raise ValueError('Incomplete source balloon category or rig resources')
    consumers=[]
    for first,last in ((0x808BFA84,0x808BFAC4),(0x808BD81C,0x808BD880)):
        a,b=first-PLAYER_RAM,last-PLAYER_RAM
        if owner[a:b]!=native_owner[a:b]:raise ValueError('Changed complete native hand/animation consumer')
        consumers.append(dict(start=first,end=last,sha256=sha256(owner[a:b])))
    symbols=(ROOT/'upstream/af/linker_scripts/jp/symbol_addrs_code.txt').read_text()
    bounds=sorted(int(a,16) for a in re.findall(r'= 0x([0-9A-Fa-f]+); // type:func',symbols))
    for first in (0x80099A94,0x8009A974,0x8009AD98,0x800E0260,0x800E0314,
                  0x800E041C,0x800E0500,0x800E0834,0x800588B8,0x80051AE4):
        last=min(a for a in bounds if a>first);a,b=first-CODE_RAM,last-CODE_RAM
        if core[a:b]!=native_core[a:b]:raise ValueError('Changed native balloon API')
        consumers.append(dict(start=first,end=last,sha256=sha256(core[a:b])))
    # The adjacent source is one checked audio sequence, not unowned padding.
    # Relocate it intact through its actual native header before growing code.
    sequence=old['sound_programs']['sequence']
    data,entry,physical=sound_programs.installed_resource(base,core,'seq',sequence['index'])
    first=position+len(module);last=first+sequence['bytes']
    if (sequence['blob_offset']!=first or physical!=files[BLOB].pstart+first
            or sha256(data)!=sequence['sha256'] or entry.hex()!=sequence['header_after']
            or blob[first:last]!=data or len(data)<BALLOON_MODULE_SIZE-len(module)
            or any(e.pstart<physical+len(data) and physical<(e.pend or e.pstart+e.size)
                   for v,e in files.items() if v!=BLOB and e.pstart!=0xFFFFFFFF)):
        raise ValueError('Rig expansion lacks exclusively owned adjacent sequence storage')
    blob.extend(bytes(-len(blob)%16));destination=len(blob);blob.extend(data)
    if BLOB+len(blob)>END:raise ValueError('Moved sequence exceeds import storage')
    new_physical=files[BLOB].pstart+destination;header=bytearray(entry)
    struct.pack_into('>I',header,0,new_physical-files[sound_programs.NATIVE_VROMS['seq']].pstart)
    address=sequence['header_address'];a=address-CODE_RAM
    if core[a:a+len(entry)]!=entry:raise ValueError('Changed native sequence header')
    core[a:a+len(entry)]=header
    blob[first:last]=bytes(len(data))
    report=copy.deepcopy(old)
    report['sound_programs']['sequence'].update(blob_offset=destination,physical=new_physical,
        vrom=BLOB+destination,header_before=entry.hex(),header_after=header.hex())
    relocation=dict(previous=copy.deepcopy(sequence),current=copy.deepcopy(report['sound_programs']['sequence']))
    # Only the allocation size changes; original actor callbacks/identity remain.
    allocation=rigs['player_allocation'];a=allocation['address']-CODE_RAM
    profile=bytearray(core[a-12:a+20]);before=u32(profile,12)
    struct.pack_into('>I',profile,12,allocation['original_bytes'])
    if (before!=BALLOON_STATE_OFFSET or before!=allocation['bytes']
            or profile!=native_core[a-12:a+20]):raise ValueError('Changed complete player allocation')
    struct.pack_into('>I',core,a,BALLOON_STATE_OFFSET+BALLOON_STATE_BYTES)
    sid=rigs['loop_sound']['native_sound_id']
    code,compiled=compile_part('held_rigs',output/'held_rigs',extra_sources=('overlays/v3/held_rigs.S',),
        defines=(f'AF_V3_PINWHEEL_SOUND=0x{sid:02X}','AF_V3_BALLOON'))
    previous=rigs['code'];a=RIG_CODE_OFFSET
    if (sha256(module[a:a+previous['bytes']])!=previous['sha256']
            or any(module[a+previous['bytes']:-16])
            or compiled['symbols']['af_v3_held_setup']!=previous['symbols']['af_v3_held_setup']
            or len(code)>BALLOON_MODULE_SIZE-RIG_CODE_OFFSET-32):
        raise ValueError('Changed rig code/entry or overlapping balloon code')
    module[a:]=code+bytes(BALLOON_MODULE_SIZE-a-len(code)-16)+struct.pack('>4I',*([GUARD]*4))
    dispatch=report['player_actions']['held_dispatch']
    for table,action in zip(dispatch['tables'],('main','draw')):
        at,n=table['offset'],table['bytes']
        old_name=f'af_v3_held_pinwheel_{action}';new_name=f'af_v3_held_balloon_{action}'
        if (sha256(module[at:at+n])!=table['sha256'] or u32(module,at+84)
                or u32(module,at+88)!=previous['symbols'][old_name]
                or table['source_callbacks']['21']['symbol']!=f'Player_actor_Item_{action}_balloon'+('_normal' if action=='main' else '')):
            raise ValueError('Changed shared balloon/pinwheel dispatch')
        struct.pack_into('>2I',module,at+84,compiled['symbols'][new_name],compiled['symbols'][old_name])
        table.update(sha256=sha256(module[at:at+n]),enabled_imported_indices=[21,22,23])
    dispatch.update(enabled_imported_indices=[21,22,23],disabled_indices=[])
    hook=report['held_rig_actions']['loop_sound']['hook'];at=hook['address']-CODE_RAM
    if core[at:at+4]!=bytes.fromhex(hook['after']):raise ValueError('Changed live level-volume hook')
    target=compiled['symbols']['af_v3_held_loop_volume'];after=struct.pack('>I',jump(target,link=True))
    core[at:at+4]=after;hook.update(after=after.hex(),target=target)
    entry=0x808BFA84;a=entry-PLAYER_RAM
    from v3_npc_clothing import guard_incoming
    guard_incoming(owner,TEXT_SIZE,PLAYER_RAM,[(a,8)])
    if any(at in relocation_offsets(rel,len(owner)) for at in (a,a+4)):
        raise ValueError('Unexpected hand callback entry relocation')
    before=bytes(owner[a:a+8]);after=struct.pack('>2I',jump(compiled['symbols']['af_v3_held_hand_position']),0)
    owner[a:a+8]=after;blob[position:position+len(module)]=module
    report.update(bytes=len(module),sha256=sha256(module),crc32=zlib.crc32(module),
        additional_resident_bytes=len(module)-old['bytes'])
    report['player_motion']['owner_sha256']=sha256(owner)
    report['player_actions']['owner_sha256']=sha256(owner)
    current=report['held_rig_actions'];current.update(code=compiled,category_indices=[21,22],
        native_kinds=sorted(current['native_kinds']+[r['native_kind'] for r in rows]))
    current['player_allocation']['bytes']=BALLOON_STATE_OFFSET+BALLOON_STATE_BYTES
    current['loop_sound']['level_ram']=RAM+BALLOON_MODULE_SIZE-32
    current['balloon']=dict(source_functions=functions,native_consumers=consumers,
        state_offset=BALLOON_STATE_OFFSET,state_bytes=BALLOON_STATE_BYTES,
        hand_hook=dict(entry=entry,before=before.hex(),after=after.hex()),
        frame_fields=dict(start=0xA18,end=0xA1C,duration=0xA20,speed=0xA24,current=0xA28,mode=0xA2C),
        source_steps_per_update=2,sequence_relocation=relocation,
        edge_alpha='Native RDP alpha coverage; no GameCube-only GX threshold opcode',
        inventory_preview_installed=False,parent_selection_enabled=False,ordinary_gameplay_tested=False)
    return report,{PLAYER_VROM:bytes(owner)}


def refresh_rig_sound(base,prior,blob,core,original,output):
    """Complete sustained equipment audio through the shared level dispatcher."""
    old=prior['equipment_resources'];position=old['blob_offset'];rigs=old['held_rig_actions']
    module=bytearray(blob[position:position+old['bytes']]);files=by_vrom(base)
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    if (rigs.get('loop_sound_installed') or old['bytes']!=RIG_MODULE_SIZE or sha256(module)!=old['sha256']
            or sha256(files[PLAYER_VROM].extract(base))!=old['player_motion']['owner_sha256']):
        raise ValueError('Loop sound requires the checked complete held-rig module')
    raw,function=source.function(0x16FA24);_,level=source.function(0x2BE6A4)
    ro=source.sections[4][0]
    if (function['sha256']!='970100344688651b241662123d4dabeeb9eef4a907f3c6df991a4391c3c64883'
            or u32(raw,0x88)&0xFFFF0000!=0x38800000 or source.rel[ro+27636:ro+27640]!=struct.pack('>f',44)
            or level['relocations'].get(12)!=(10,0,4,0x80015614)):
        raise ValueError('Changed source speed-controlled equipment sound')
    sid=u32(raw,0x88)&65535
    from v3_villager_audio import read_audio_donor
    dol,_=read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    if sha256(dol.read(0x8000E004,0x224))!='a4392efc099e7c12edcfa95951351a62de3528916665acc31e83b7ade6253032':
        raise ValueError('Changed source level-volume implementation')
    original_core=by_vrom(original)[CODE_VROM].extract(original);start,end=0x800F76CC,0x800F7810
    if core[start-CODE_RAM:end-CODE_RAM]!=original_core[start-CODE_RAM:end-CODE_RAM]:
        raise ValueError('Changed complete native level-volume consumer')
    hook=0x800F77A0;at=hook-CODE_RAM;before=bytes(core[at:at+4])
    if before!=struct.pack('>I',jump(0x800EEDFC,link=True)):
        raise ValueError('Changed ordinary native level-volume call')
    sounds=sound_programs.install_level(base,prior,blob,core,[sid])
    compiled_code,compiled=compile_part('held_rigs',output/'held_rigs',extra_sources=('overlays/v3/held_rigs.S',),
                                      defines=(f'AF_V3_PINWHEEL_SOUND=0x{sid:02X}',))
    previous=rigs['code'];a=RIG_CODE_OFFSET
    if (sha256(module[a:a+previous['bytes']])!=previous['sha256'] or any(module[a+previous['bytes']:-16])
            or compiled['symbols']['af_v3_held_setup']!=previous['symbols']['af_v3_held_setup']
            or len(compiled_code)>RIG_MODULE_SIZE-RIG_CODE_OFFSET-32):
        raise ValueError('Changed rig code, entry point, or loop-state reservation')
    module[a:-16]=compiled_code+bytes(len(module)-16-a-len(compiled_code))
    report=copy.deepcopy(old)
    for table,name in zip(report['player_actions']['held_dispatch']['tables'],
                           ('af_v3_held_pinwheel_main','af_v3_held_pinwheel_draw')):
        at,n=table['offset'],table['bytes']
        if sha256(module[at:at+n])!=table['sha256'] or u32(module,at+88)!=previous['symbols'][name]:
            raise ValueError('Changed held-rig callback binding')
        struct.pack_into('>I',module,at+88,compiled['symbols'][name])
        table['sha256']=sha256(module[at:at+n])
    target=compiled['symbols']['af_v3_held_loop_volume'];after=struct.pack('>I',jump(target,link=True))
    core[hook-CODE_RAM:hook-CODE_RAM+4]=after
    blob[position:position+len(module)]=module
    report.update(sha256=sha256(module),crc32=zlib.crc32(module),sound_programs=sounds,additional_resident_bytes=0)
    report['held_rig_actions'].update(code=compiled,loop_sound_installed=True,
        loop_sound=dict(source_functions=[function,level],source_volume=dict(address=0x8000E004,bytes=0x224,
            sha256=sha256(dol.read(0x8000E004,0x224))),native_sound_id=sid,level_ram=RAM+RIG_MODULE_SIZE-32,
            native_volume_consumer=dict(start=start,end=end,sha256=sha256(original_core[start-CODE_RAM:end-CODE_RAM])),
            hook=dict(address=hook,before=before.hex(),after=after.hex(),target=target),
            native_frame_speed_divisor=88,source_frame_speed_divisor=44,native_expiry_retained=True,
            native_pause_fade_pan_reverb_retained=True,physical_audio_played=False))
    return report,{}


def refresh_rigs(base,prior,blob,core,original,output):
    """Install one shared animated-held category, without enabling its parents."""
    from v3_npc_clothing import guard_incoming
    old=prior['equipment_resources'];offset=old['blob_offset']
    module=bytearray(blob[offset:offset+old['bytes']]);files=by_vrom(base)
    owner=bytearray(files[PLAYER_VROM].extract(base));reloc=files[PLAYER_RELOC].extract(base)
    native_files=by_vrom(original);native_owner=native_files[PLAYER_VROM].extract(original)
    native_core=native_files[CODE_VROM].extract(original)
    if (not old.get('animated_rigs') or old.get('held_rig_actions') or old['bytes']!=RIG_CODE_OFFSET
            or sha256(module)!=old['sha256'] or old['ram']!=RAM
            or sha256(owner)!=old['player_motion']['owner_sha256']
            or sha256(reloc)!=old['player_motion']['reloc_sha256']
            or struct.unpack_from('>4I',module,len(module)-16)!=(GUARD,)*4
            or RAM+RIG_MODULE_SIZE>prior['furniture']['bank_pool']['start']):
        raise ValueError('Animated-held actions require the complete checked rig module')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    functions=[]
    for name in ('Player_actor_SetupItem_Base0','Player_actor_SetupItem_Base_windmill',
                 'Player_actor_SetupItem_Base1','Player_actor_SetupItem_Base3',
                 'Player_actor_Item_windmill_CulcParam','Player_actor_Item_windmill_CulcRotationSpeed',
                 'Player_actor_Item_main_windmill_normal','Player_actor_Item_draw_windmill_After_kaza1_fan',
                 'Player_actor_Item_draw_windmill_After','Player_actor_Item_draw_windmill',
                 'mPlib_check_player_actor_main_index_AllWade','mEnv_GetWindPowerF_Windmill'):
        matches=[at for at,rows in source.functions.items() if any(n==name for n,_ in rows)]
        if len(matches)!=1:raise ValueError('Missing complete animated-held source function: '+name)
        functions.append(source.function(matches[0])[1])
    report=copy.deepcopy(old);dispatch=report['player_actions']['held_dispatch']
    rows=[row for row in report['kind_readers']['rows'] if row['item_main']==22]
    resources={r['index']:r for r in old['records']}
    if (sorted(r['native_kind'] for r in rows)!=list(range(99,107))
            or any(not r['resource_ready'] or r['selectable'] or r['fields'][1]!=22
                   or resources[r['fields'][2]]['type']!=1 for r in rows)
            or [t['source_callbacks']['22']['symbol'] for t in dispatch['tables']]!=[
                'Player_actor_Item_main_windmill_normal','Player_actor_Item_draw_windmill']):
        raise ValueError('Changed rig category bindings or incomplete resources')
    # Keep the complete native setup/load/draw consumers and core APIs pinned to
    # the verified original, not only the instructions replaced by this adapter.
    consumers=[]
    owner_ranges=((0x808B83B4,0x808B846C),(0x808B846C,0x808B8628),
                  (0x808BD81C,0x808BD880),(0x808BD934,0x808BDACC),
                  (0x808BDDB4,0x808BDF48),(0x808BE788,0x808BE85C))
    for first,last in owner_ranges:
        a,b=first-PLAYER_RAM,last-PLAYER_RAM
        if owner[a:b]!=native_owner[a:b]:raise ValueError('Changed native rig initialization or drawing')
        consumers.append(dict(start=first,end=last,sha256=sha256(owner[a:b])))
    symbols=(ROOT/'upstream/af/linker_scripts/jp/symbol_addrs_code.txt').read_text()
    bounds=sorted(int(a,16) for a in re.findall(r'= 0x([0-9A-Fa-f]+); // type:func',symbols))
    apis=(0x80099A54,0x800E0008,0x8009A570,0x8009895C,0x80098980,0x800B6074,
          0x800E020C,0x800E0244,0x800E02AC,0x800E0698,0x800E13C4,0x800E14D4,
          0x800E1AA0,0x800530D8)
    for first in apis:
        last=min(x for x in bounds if x>first);a,b=first-CODE_RAM,last-CODE_RAM
        if core[a:b]!=native_core[a:b]:raise ValueError('Changed native animated-held API')
        consumers.append(dict(start=first,end=last,sha256=sha256(core[a:b])))
    # All three normal/rod-aware setup callers enter the same complete base.
    entry=0x808B83B4;at=entry-PLAYER_RAM
    callers=[PLAYER_RAM+i for i in range(0,TEXT_SIZE,4) if u32(owner,i)==jump(entry,link=True)]
    if callers!=[0x808B84C4,0x808B85D0,0x808B8610]:
        raise ValueError('Changed shared rig setup callers')
    guard_incoming(owner,TEXT_SIZE,PLAYER_RAM,[(at,8)])
    relocations=relocation_offsets(reloc,len(owner))
    if (owner[at:at+8]!=bytes.fromhex('27bdffd0afb00024')
            or any(i in relocations for i in (at,at+4))):
        raise ValueError('Changed shared rig setup prologue')
    profile=0x8010BCE0-CODE_RAM
    if (core[profile:profile+32]!=native_core[profile:profile+32]
            or u32(core,profile+12)!=RIG_STATE_OFFSET):
        raise ValueError('Changed complete player allocation profile')
    code,compiled=compile_part('held_rigs',output/'held_rigs',extra_sources=('overlays/v3/held_rigs.S',))
    if len(code)>RIG_MODULE_SIZE-RIG_CODE_OFFSET-16:raise ValueError('Animated-held code exceeds reservation')
    module.extend(bytes(RIG_MODULE_SIZE-len(module)))
    module[RIG_CODE_OFFSET:RIG_CODE_OFFSET+len(code)]=code
    struct.pack_into('>4I',module,RIG_MODULE_SIZE-16,*([GUARD]*4))
    for table,name in zip(dispatch['tables'],('af_v3_held_pinwheel_main','af_v3_held_pinwheel_draw')):
        at,n=table['offset'],table['bytes']
        if sha256(module[at:at+n])!=table['sha256'] or u32(module,at+22*4):
            raise ValueError('Changed or occupied shared held callback slot')
        struct.pack_into('>I',module,at+22*4,compiled['symbols'][name])
        table.update(sha256=sha256(module[at:at+n]),enabled_imported_indices=[22,23])
    at=entry-PLAYER_RAM;before=bytes(owner[at:at+8]);after=struct.pack('>II',jump(compiled['symbols']['af_v3_held_setup']),0)
    owner[at:at+8]=after
    struct.pack_into('>I',core,profile+12,RIG_PLAYER_SIZE)
    blob.extend(bytes(-len(blob)%16));position=len(blob);blob.extend(module)
    if BLOB+len(blob)>END:raise ValueError('Animated-held module exceeds shared ROM storage')
    report.update(bytes=len(module),vrom=BLOB+position,blob_offset=position,
        sha256=sha256(module),crc32=zlib.crc32(module),additional_resident_bytes=len(module)-old['bytes'])
    report['player_motion']['owner_sha256']=sha256(owner)
    report['player_actions'].update(owner_sha256=sha256(owner),relocation_sha256=sha256(reloc))
    dispatch.update(enabled_imported_indices=[22,23],disabled_indices=[21])
    report['held_rig_actions']=dict(format='AFV3-HELD-RIG-ACTIONS-1',code=compiled,code_offset=RIG_CODE_OFFSET,
        source_functions=functions,native_consumers=consumers,setup_callers=callers,
        setup_hook=dict(entry=entry,before=before.hex(),after=after.hex(),continuation=entry+8),
        player_allocation=dict(address=0x8010BCEC,original_bytes=RIG_STATE_OFFSET,bytes=RIG_PLAYER_SIZE,
                               state_offset=RIG_STATE_OFFSET,state_bytes=RIG_STATE_BYTES),
        category_indices=[22],native_kinds=[r['native_kind'] for r in rows],source_steps_per_update=2,
        loop_sound_installed=False,inventory_preview_installed=False,logical_imports_added=0,
        ordinary_gameplay_tested=False,save_format_changed=False)
    return report,{PLAYER_VROM:bytes(owner)}


def refresh_pocket_icons(base,prior,blob,core,original,output):
    """Install shared source-discovered pocket artwork and its native reader."""
    from v3_handheld_items import pocket_icons
    from v3_npc_clothing import guard_incoming
    import v3_furniture_icon as icon
    old=prior['equipment_resources'];at=old['blob_offset']
    module=bytearray(blob[at:at+old['bytes']])
    if old.get('pocket_icons') or sha256(module)!=old['sha256']:
        raise ValueError('Pocket icon readers already installed or module changed')
    parents=old['parent_readers'];existing=parents['code']
    if (sha256(module[PARENT_CODE_OFFSET:PARENT_CODE_OFFSET+existing['bytes']])!=existing['sha256']
            or any(module[PARENT_CODE_OFFSET+existing['bytes']:TABLE_OFFSET])):
        raise ValueError('Pocket icon reservation overlaps existing equipment code/data')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    data,receipt=pocket_icons(source,old,RAM+POCKET_ICON_OFFSET,TABLE_OFFSET-POCKET_ICON_OFFSET)
    files,native=by_vrom(base),by_vrom(original)
    owner=bytearray(files[icon.VROM].extract(base));rel=files[icon.RELOC].extract(base)
    sections=struct.unpack_from('>5I',rel)
    if sections!=icon.SECTIONS or sha256(rel)!=icon.RELOC_SHA:
        raise ValueError('Changed native pocket icon owner relocations')
    restored=bytearray(owner)
    if struct.unpack_from('>2I',restored,icon.START-icon.RAM)!=(jump(0x8046AB00),0):
        raise ValueError('Changed installed furniture icon reader')
    struct.pack_into('>2I',restored,icon.START-icon.RAM,0x00194B03,0x24010001)
    first,last=0x8085C7B8-icon.RAM,0x8085CE18-icon.RAM
    native_owner=native[icon.VROM].extract(original)
    if restored[first:last]!=native_owner[first:last]:
        raise ValueError('Changed complete native inventory icon selection/drawing')
    hook=0x8085C954-icon.RAM
    if struct.unpack_from('>2I',owner,hook)!=(0x3C0F8086,0x25EFDD68):
        raise ValueError('Changed native tool descriptor lookup')
    guard_incoming(bytes(owner),sections[0],icon.RAM,[(hook,8)])
    records=list(struct.unpack_from('>'+str(sections[4])+'I',rel,20))
    removed=[0x45000000|hook,0x46000000|(hook+4)]
    if any(records.count(word)!=1 for word in removed):
        raise ValueError('Missing native tool descriptor HI/LO relocations')
    code,compiled=compile_part('held_items',output/'held_items',
        extra_sources=('overlays/v3/held_icon.S',),defines=('AF_V3_POCKET_ICONS',
            f'AF_V3_HELD_SELECTED=0x{old["player_actions"]["code"]["symbols"]["af_v3_player_selected_equipment"]:08X}u'))
    if (len(code)>POCKET_ICON_OFFSET-PARENT_CODE_OFFSET
            or compiled['symbols']['af_v3_held_item_price']!=RAM+PARENT_CODE_OFFSET+0x100
            or compiled['symbols']['af_v3_held_item_icon']!=RAM+PARENT_CODE_OFFSET+0x200):
        raise ValueError('Pocket icon code exceeds its fixed parent-reader allocation')
    target=compiled['symbols']['af_v3_held_icon_hook']
    before=bytes(owner[hook:hook+8]);struct.pack_into('>2I',owner,hook,jump(target),0)
    kept=[word for word in records if word not in removed]
    relocation=struct.pack('>5I',*sections[:4],len(kept))+struct.pack('>'+str(len(kept))+'I',*kept)
    relocation+=bytes(len(rel)-len(relocation)-4)+struct.pack('>I',len(rel))
    module[PARENT_CODE_OFFSET:PARENT_CODE_OFFSET+existing['bytes']]=bytes(existing['bytes'])
    module[PARENT_CODE_OFFSET:PARENT_CODE_OFFSET+len(code)]=code
    module[POCKET_ICON_OFFSET:POCKET_ICON_OFFSET+len(data)]=data
    receipt.update(code=compiled,code_offset=PARENT_CODE_OFFSET,table_offset=POCKET_ICON_OFFSET,
        owner_vrom=icon.VROM,owner_ram=icon.RAM,owner_sha256=sha256(owner),
        native_consumer_sha256=sha256(native_owner[first:last]),
        previous_owner_sha256=sha256(files[icon.VROM].extract(base)),
        relocation_vrom=icon.RELOC,relocation_sha256=sha256(relocation),
        removed_relocations=removed,hook=dict(address=icon.RAM+hook,target=target,
            before=before.hex(),after=owner[hook:hook+8].hex()),
        original_umbrella_branch_retained=True,missing_imports_draw_nothing=True,
        saved_format_changed=False,additional_resident_bytes=0,native_tested=False)
    report=copy.deepcopy(old);report['pocket_icons']=receipt
    report['parent_readers']['code']=compiled
    report.update(sha256=sha256(module),crc32=zlib.crc32(module))
    blob[at:at+len(module)]=module
    return report,{icon.VROM:bytes(owner),icon.RELOC:relocation}


def refresh_parent_readers(base,prior,blob,core,original,output):
    """Connect parent metadata without new equipment-specific installers."""
    from v3_handheld_items import parent_records
    old=prior['equipment_resources'];actions=old['player_actions'];at=old['blob_offset']
    module=bytearray(blob[at:at+old['bytes']])
    if old.get('parent_readers') or sha256(module)!=old['sha256']:
        raise ValueError('Parent readers already installed or equipment module changed')
    existing=actions['code']
    if (existing['bytes']>PARENT_CODE_OFFSET-CODE_OFFSET
            or sha256(module[CODE_OFFSET:CODE_OFFSET+existing['bytes']])!=existing['sha256']
            or any(module[CODE_OFFSET+existing['bytes']:TABLE_OFFSET])):
        raise ValueError('Parent reader code overlaps existing action code')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    table,receipt=parent_records(source,old)
    if PARENT_TABLE_OFFSET+len(table)>MODULE_SIZE-16 or any(module[PARENT_TABLE_OFFSET:PARENT_TABLE_OFFSET+len(table)]):
        raise ValueError('Parent metadata overlaps an existing equipment resource')
    code,compiled=compile_part('held_items',output/'held_items',defines=(
        f'AF_V3_HELD_SELECTED=0x{existing["symbols"]["af_v3_player_selected_equipment"]:08X}u',))
    if (len(code)>TABLE_OFFSET-PARENT_CODE_OFFSET
            or compiled['symbols']['af_v3_held_item_price']!=RAM+PARENT_CODE_OFFSET+0x100):
        raise ValueError('Parent reader public entries or allocation changed')
    module[PARENT_CODE_OFFSET:PARENT_CODE_OFFSET+len(code)]=code
    module[PARENT_TABLE_OFFSET:PARENT_TABLE_OFFSET+len(table)]=table
    receipt.update(code=compiled,code_offset=PARENT_CODE_OFFSET,table_offset=PARENT_TABLE_OFFSET,
        table_ram=RAM+PARENT_TABLE_OFFSET,native_tested=False)
    report=copy.deepcopy(old);report['parent_readers']=receipt
    report.update(sha256=sha256(module),crc32=zlib.crc32(module))
    blob[at:at+len(module)]=module
    return report,{}


def control_bindings(source,owner,core,original,prior):
    """Bind the complete donor flow and every native API used by its adapter."""
    functions=(0x164628,0x169484,0x169544,0x19623C,0x1962B0,0x196468,
               0x166460,0x166650,0x175A3C,0x175B0C,0x175E90,
               0x175CDC,0x1767F8,0x176E6C,0x1777FC)
    frame_functions={'Player_actor_Movement_Swing_fan','Player_actor_CulcAnimation_Swing_fan',
        'Player_actor_SetSound_Swing_fan','Player_actor_SearchAnimation_Swing_fan',
        'Player_actor_ObjCheck_Swing_fan','Player_actor_BGcheck_Swing_fan',
        'Player_actor_main_Swing_fan','Player_actor_sound_uchiwa',
        'Player_actor_Movement_Base_Braking','Player_actor_set_sound_common1',
        'Player_actor_set_sound_common2'}
    extra=[at for at,rows in source.functions.items() if any(n in frame_functions for n,_ in rows)]
    if len(extra)!=len(frame_functions):raise ValueError('Missing complete donor per-frame dependency')
    functions+=tuple(sorted(extra))
    receipts=[source.function(at)[1] for at in functions]
    if [r['symbol'] for r in receipts[:6]]!=[
            'Player_actor_CheckController_forFan','Player_actor_CheckAbleSpeed_forItem',
            'Player_actor_CheckAndRequest_main_fan_all','Player_actor_request_main_swing_fan_all',
            'Player_actor_setup_main_Swing_fan','Player_actor_request_proc_index_fromSwing_fan']:
        raise ValueError('Changed complete donor fan control functions')
    # Action metadata consumers have already been redirected to the complete
    # tables. Undo only their recorded instructions for original API comparison.
    restored=bytearray(owner)
    for row in prior['player_actions']['patches']:
        at=row['offset']
        if u32(restored,at)!=row['after']:raise ValueError('Changed installed player action patch')
        struct.pack_into('>I',restored,at,row['before'])
    files=by_vrom(original);native_owner=files[PLAYER_VROM].extract(original)
    native_core=files[CODE_VROM].extract(original)
    boundaries=[]
    for name in ('symbol_addrs_code.txt','symbol_addrs_overlays.txt'):
        boundaries.extend(int(a,16) for a in re.findall(r'= 0x([0-9A-Fa-f]+); // type:func',
            (ROOT/'upstream/af/linker_scripts/jp'/name).read_text()))
    code=(ROOT/'overlays/v3/player_actions.c').read_text()
    entries=sorted({int(a,16) for a in re.findall(r'FN\(0x([0-9A-F]+)u,',code)}|{0x808C1118})
    native=[]
    for entry in entries:
        end=min(a for a in boundaries if a>entry)
        data,expected,base=(restored,native_owner,PLAYER_RAM) if entry>=PLAYER_RAM else (core,native_core,CODE_RAM)
        value=data[entry-base:end-base]
        if not value or value!=expected[entry-base:end-base]:
            raise ValueError(f'Changed native player control API {entry:08X}')
        native.append(dict(entry=entry,end=end,bytes=len(value),sha256=sha256(value)))
    rodata=source.sections[4][0]
    if (source.rel[rodata+23256:rodata+23260]!=struct.pack('>f',0.5)
            or u32(restored,0x808C1174-PLAYER_RAM)!=0x3C013F80
            or u32(restored,0x808C1180-PLAYER_RAM)!=0x44814000
            or u32(restored,0x808C11AC-PLAYER_RAM)!=0xE7A80018):
        raise ValueError('Changed donor/native WAIT animation speed binding')
    return dict(source_functions=receipts,native_functions=native,
        fan_action=109,fan_kind_first=107,fan_kind_count=8,
        swing_animation=270,lower_animation=0,part_mask=4,frame_speed=1.0,
        timing=dict(donor_frame_speed=0.5,native_frame_speed=1.0,
            donor_wait_speed_constant=23256,native_wait_initializer=0x808C1118,
            native_braking=0x808B3C74,source_frame_events_retained=True),
        request_union_offset=0xD58,initializer=0x808B4A44,
        wait_signature='game, morph, flags, priority',
        donor_wait_delay_consumed=False,poll_hooks_installed=False,
        action_callbacks_installed=False,ordinary_gameplay_tested=False)


def refresh_frame_flow(base,prior,blob,core,original,output):
    """Add the complete per-frame category and its shared sound dependencies."""
    old=prior['equipment_resources'];actions=old['player_actions'];at=old['blob_offset']
    module=bytearray(blob[at:at+old['bytes']]);files=by_vrom(base)
    if (old['bytes']!=MODULE_SIZE or sha256(module)!=old['sha256']
            or actions['enabled_imported_actions'] or actions.get('fan_frame_flow')
            or sha256(files[PLAYER_VROM].extract(base))!=actions['owner_sha256']
            or sha256(files[PLAYER_RELOC].extract(base))!=actions['relocation_sha256']):
        raise ValueError('Per-frame integration requires checked disabled action tables')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    bindings=control_bindings(source,files[PLAYER_VROM].extract(base),core,original,old)
    raw,receipt=source.function(0x16FA00)
    if u32(raw,8)&0xFFFF0000!=0x38800000 or u32(raw,16)!=0x4BFFF6B9:
        raise ValueError('Changed source sound-ID argument or positional sound call')
    sid=u32(raw,8)&65535
    sounds=sound_programs.install(base,prior,blob,core,[sid])
    native_sid=sounds['imports'][0]['native_sound_id']
    previous=actions['code'];n=previous['bytes']
    if (sha256(module[CODE_OFFSET:CODE_OFFSET+n])!=previous['sha256']
            or any(module[CODE_OFFSET+n:TABLE_OFFSET])):
        raise ValueError('Changed shared action-code reservation')
    code,compiled=compile_part('player_actions',output/'player_actions',
        primary_source='overlays/v3/player_actions.S',extra_sources=('overlays/v3/player_actions.c',),
        defines=(f'AF_V3_FAN_SOUND=0x{native_sid:04X}',))
    if len(code)>TABLE_OFFSET-CODE_OFFSET or code[:68]!=module[CODE_OFFSET:CODE_OFFSET+68]:
        raise ValueError('Per-frame adapter changes original shared dispatch')
    for name in ('af_v3_player_action_v0','af_v3_player_action_t9'):
        if compiled['symbols'][name]!=previous['symbols'][name]:
            raise ValueError('Per-frame adapter moves installed dispatch')
    module[CODE_OFFSET:TABLE_OFFSET]=code+bytes(TABLE_OFFSET-CODE_OFFSET-len(code))
    blob[at:at+len(module)]=module
    report=copy.deepcopy(old)
    report.update(sha256=sha256(module),crc32=zlib.crc32(module),sound_programs=sounds)
    report['player_actions'].update(code=compiled,fan_control_flow=bindings,
        fan_frame_flow=dict(source_sound=receipt,native_sound_id=native_sid,
            sound_frame=1.5,native_braking=True,main_callback_compiled=True,
            action_callbacks_installed=False,poll_hooks_installed=False,
            ordinary_gameplay_tested=False))
    return report,{}


def refresh_held_dispatch(base,prior,blob,core,original,output):
    """Use the shared callback-table format for complete held-item categories."""
    old=prior['equipment_resources'];actions=old['player_actions'];at=old['blob_offset']
    module=bytearray(blob[at:at+old['bytes']]);files=by_vrom(base)
    owner=files[PLAYER_VROM].extract(base);reloc=files[PLAYER_RELOC].extract(base)
    if (old['bytes']!=MODULE_SIZE or sha256(module)!=old['sha256']
            or actions.get('held_dispatch') or actions['enabled_imported_actions']
            or sha256(owner)!=actions['owner_sha256'] or sha256(reloc)!=actions['relocation_sha256']):
        raise ValueError('Held dispatch requires the checked complete action module')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    bindings=control_bindings(source,owner,core,original,old)
    start=(TABLE_OFFSET+actions['table_bytes']+15)&-16
    data,tables,patches,removed,records,locations=expanded_tables(source,owner,reloc,
        categories=HELD_CATEGORIES,native_count=21,count=24,table_offset=start,
        magic=0x41465049,complete_bound_scan=False)
    native=by_vrom(original)[PLAYER_VROM].extract(original)
    for row,end in zip(tables,(0x808BF494,0x808BF6C8)):
        begin=row['native_entry']
        if owner[begin-PLAYER_RAM:end-PLAYER_RAM]!=native[begin-PLAYER_RAM:end-PLAYER_RAM]:
            raise ValueError('Changed complete native held-item dispatcher')
        row.update(native_end=end,native_consumer_sha256=sha256(owner[begin-PLAYER_RAM:end-PLAYER_RAM]))
    n=actions['code']['bytes']
    if (sha256(module[CODE_OFFSET:CODE_OFFSET+n])!=actions['code']['sha256']
            or any(module[CODE_OFFSET+n:TABLE_OFFSET]) or any(module[start:start+len(data)])):
        raise ValueError('Shared held-code/table reservation is not empty and verified')
    pointer=old['code']['symbols']['af_v3_equipment_pointer']
    sid=actions['fan_frame_flow']['native_sound_id']
    code,compiled=compile_part('player_actions',output/'player_actions',
        primary_source='overlays/v3/player_actions.S',extra_sources=('overlays/v3/player_actions.c',),
        defines=(f'AF_V3_FAN_SOUND=0x{sid:04X}',f'AF_V3_HELD_POINTER=0x{pointer:08X}u'))
    if len(code)>TABLE_OFFSET-CODE_OFFSET or code[:68]!=module[CODE_OFFSET:CODE_OFFSET+68]:
        raise ValueError('Held dispatcher changes installed action entry points')
    # A fan has no independent equipment animation update. Reuse the verified
    # original zero-return callback, not another item's gameplay behaviour.
    no_update=u32(owner,tables[0]['native_table']-PLAYER_RAM+4)
    noop=owner[no_update-PLAYER_RAM:no_update-PLAYER_RAM+20]
    if noop!=bytes.fromhex('afa40000afa500040000102503e0000800000000'):
        raise ValueError('Original static held-item callback is no longer a no-op')
    extra=[source.function(x)[1] for x in (0x173A7C,0x173A84,0x17150C)]
    ro=source.sections[4][0];angles=source.rel[ro+27744:ro+27750]
    if (angles!=native[0x808DF598-PLAYER_RAM:0x808DF59E-PLAYER_RAM]
            or source.rel[ro+27752:ro+27756]!=struct.pack('>f',0.2)
            or owner[0x808BE140-PLAYER_RAM:0x808BE184-PLAYER_RAM]!=native[0x808BE140-PLAYER_RAM:0x808BE184-PLAYER_RAM]):
        raise ValueError('Fan net-angle reset does not match the original native reset')
    for row,callback in zip(tables,(no_update,compiled['symbols']['af_v3_player_draw_static_item'])):
        index=row['offset']-start
        struct.pack_into('>I',data,index+23*4,callback)
        row.update(sha256=sha256(data[index:index+row['bytes']]),enabled_imported_indices=[23])
    for entry,register,name in ((0x808BF470,3,'af_v3_player_action_v1'),
                                (0x808BF66C,25,'af_v3_player_action_t9')):
        offset=entry-PLAYER_RAM;before=u32(owner,offset)
        if before!=register<<21|0xF809 or offset in locations:
            raise ValueError('Changed held-item indirect call')
        patches.append(dict(offset=offset,before=before,after=jump(compiled['symbols'][name],link=True)))
    patched=bytearray(owner)
    for row in patches:
        if u32(patched,row['offset'])!=row['before']:raise ValueError('Changed held-item patch input')
        struct.pack_into('>I',patched,row['offset'],row['after'])
    kept=[r for r in records if r not in {locations[x] for x in removed}]
    fixed=bytearray(reloc);struct.pack_into('>I',fixed,16,len(kept))
    fixed[20:-4]=struct.pack('>'+str(len(kept))+'I',*kept)+bytes(len(fixed)-24-len(kept)*4)
    module[CODE_OFFSET:TABLE_OFFSET]=code+bytes(TABLE_OFFSET-CODE_OFFSET-len(code))
    module[start:start+len(data)]=data;blob[at:at+len(module)]=module
    report=copy.deepcopy(old);report.update(sha256=sha256(module),crc32=zlib.crc32(module))
    report['player_motion'].update(owner_sha256=sha256(patched),reloc_sha256=sha256(fixed))
    report['player_actions'].update(code=compiled,fan_control_flow=bindings,
        owner_sha256=sha256(patched),relocation_sha256=sha256(fixed),
        patches=actions['patches']+patches,removed_relocations=actions['removed_relocations']+len(removed),
        held_dispatch=dict(format='AFV3-HELD-CALLBACK-TABLES-1',native_count=21,count=24,
            table_offset=start,table_bytes=len(data),tables=tables,source_functions=extra,
            native_zero_callback=no_update,native_zero_callback_sha256=sha256(noop),
            equipment_pointer=pointer,source_rod_flag_cleared=True,
            balloon_state_installed=False,net_reset=dict(entry=0x808BE140,angles_hex=angles.hex(),
                sha256=sha256(native[0x808BE140-PLAYER_RAM:0x808BE184-PLAYER_RAM]),installed=False),
            enabled_imported_indices=[23],disabled_indices=[21,22],ordinary_equipped_fan_tested=False))
    return report,{PLAYER_VROM:bytes(patched),PLAYER_RELOC:bytes(fixed)}


def fan_action_audit(source,owner,core,original):
    """Bind the remaining core limits without expanding unrelated native tables."""
    files=by_vrom(original);native_core=files[CODE_VROM].extract(original)
    native_owner=files[PLAYER_VROM].extract(original)
    bounds=lambda data:{CODE_RAM+i for i in range(0,len(data)-3,4)
        if u32(data,i)>>26 in (10,11) and u32(data,i)&65535==NATIVE_COUNT}
    expected={0x80093954,0x800B3398,0x800B5AF4}
    if bounds(core)!=expected or bounds(native_core)!=expected:
        raise ValueError('Changed outside-owner native action-limit inventory')
    receipts=[]
    for start,end in ((0x80093878,0x800939B8),(0x800B3330,0x800B33AC),(0x800B5AB8,0x800B5B1C)):
        data=core[start-CODE_RAM:end-CODE_RAM]
        if data!=native_core[start-CODE_RAM:end-CODE_RAM]:
            raise ValueError('Changed complete core action-limit consumer')
        receipts.append(dict(entry=start,end=end,sha256=sha256(data)))
    start,end=0x808B91CC,0x808B9248
    callback=owner[start-PLAYER_RAM:end-PLAYER_RAM]
    if (callback!=native_owner[start-PLAYER_RAM:end-PLAYER_RAM]
            or [u32(owner,x-PLAYER_RAM)&65535 for x in (0x808B9208,0x808B9210,0x808B9218,0x808B9220)]!=[7,8,9,10]
            or u32(owner,0x808DD640-PLAYER_RAM)!=0x273991CC
            or u32(owner,0x808DD668-PLAYER_RAM)!=0xAE191278):
        raise ValueError('Changed equipment-change callback or its complete return set')
    gc_table=source.rel[source.sections[4][0]+7912:source.sections[4][0]+7912+COUNT]
    if len(gc_table)!=COUNT or gc_table[109]!=0:
        raise ValueError('Fan needs a non-default core event-position rule')
    return dict(native_105_bounds=sorted(expected),native_functions=receipts,
        source_functions=[source.function(x)[1] for x in (0x6B424,0x6DCDC,0x16AD54)],
        resource_size_bound=0x80093954,resource_size_bound_is_action_limit=False,
        equipment_change_callback=dict(entry=start,end=end,sha256=sha256(callback),
            returns=[-1,7,8,9,10],actor_slot=0x1278),
        event_position=dict(source_table_offset=7912,source_sha256=sha256(gc_table),
            source_fan_value=0,native_out_of_range_value=0),core_changes_required=False)


def refresh_selection(base,prior,blob,core,original,output):
    """Connect selected equipment and passive visibility through shared records."""
    from v3_handheld_items import selection_records
    old=prior['equipment_resources'];actions=old['player_actions'];at=old['blob_offset']
    module=bytearray(blob[at:at+old['bytes']]);files=by_vrom(base)
    owner=files[PLAYER_VROM].extract(base);reloc=files[PLAYER_RELOC].extract(base)
    if (sha256(module)!=old['sha256'] or sha256(owner)!=actions['owner_sha256']
            or sha256(reloc)!=actions['relocation_sha256'] or actions.get('equipment_selection')):
        raise ValueError('Changed shared action/selection base')
    native_owner=by_vrom(original)[PLAYER_VROM].extract(original)
    first,last=0x808BD3F8,0x808BD668
    value=owner[first-PLAYER_RAM:last-PLAYER_RAM]
    if value!=native_owner[first-PLAYER_RAM:last-PLAYER_RAM]:
        raise ValueError('Changed complete native equipment/scene/visibility selectors')
    table_start=0x808E0274-PLAYER_RAM
    if owner[table_start:table_start+144]!=native_owner[table_start:table_start+144]:
        raise ValueError('Changed native equipment item switch')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    table,selection=selection_records(source,old)
    if SELECTION_OFFSET+len(table)>MODULE_SIZE-16 or any(module[SELECTION_OFFSET:SELECTION_OFFSET+len(table)]):
        raise ValueError('Equipment selection table overlaps an installed resource')
    profile=bytes.fromhex(prior['save_runtime']['profile_hex'])
    if len(profile)!=192 or blob[0x20:0xE0]!=profile:
        raise ValueError('Changed actual selected import profile')
    if any(profile[r['profile_byte']]&r['profile_mask'] for r in selection['rows']):
        raise ValueError('Prepared equipment identity already occupies a selected profile bit')
    previous=actions['code'];n=previous['bytes']
    if sha256(module[CODE_OFFSET:CODE_OFFSET+n])!=previous['sha256'] or any(module[CODE_OFFSET+n:TABLE_OFFSET]):
        raise ValueError('Changed complete shared action-code reservation')
    code,compiled=compile_part('player_actions',output/'player_actions',
        primary_source='overlays/v3/player_actions.S',
        extra_sources=('overlays/v3/player_actions.c','overlays/v3/held_selection.c'),
        defines=(f'AF_V3_FAN_SOUND=0x{actions["fan_frame_flow"]["native_sound_id"]:04X}',
                 f'AF_V3_HELD_POINTER=0x{old["code"]["symbols"]["af_v3_equipment_pointer"]:08X}u',
                 'AF_V3_HELD_SELECTION=1'))
    if code[:80]!=module[CODE_OFFSET:CODE_OFFSET+80] or len(code)>TABLE_OFFSET-CODE_OFFSET:
        raise ValueError('Selection rebuild moves a shared dispatcher or exceeds its code bound')
    module[CODE_OFFSET:TABLE_OFFSET]=code+bytes(TABLE_OFFSET-CODE_OFFSET-len(code))
    module[SELECTION_OFFSET:SELECTION_OFFSET+len(table)]=table
    report=copy.deepcopy(old);current=report['player_actions'];symbols=compiled['symbols']
    # Rebind installed callbacks and poll calls by their actual symbols, not
    # their incidental locations in the preceding C link.
    names={'Player_actor_setup_main_Swing_fan':'af_v3_player_fan_setup',
           'Player_actor_main_Swing_fan':'af_v3_player_fan_main'}
    for entry in current['fan_activation']['callbacks']:
        if entry['source'] not in names:continue
        row=next(r for r in current['tables'] if r['native_entry']==entry['consumer'])
        if (sha256(module[row['offset']:row['offset']+row['bytes']])!=row['sha256']
                or u32(module,entry['offset'])!=entry['target']):
            raise ValueError('Changed complete registered action callback')
        entry['target']=symbols[names[entry['source']]]
        struct.pack_into('>I',module,entry['offset'],entry['target'])
        row['sha256']=sha256(module[row['offset']:row['offset']+row['bytes']])
    draw=current['held_dispatch']['tables'][1];start=draw['offset'];n=draw['bytes']
    if sha256(module[start:start+n])!=draw['sha256']:raise ValueError('Changed held drawing table')
    struct.pack_into('>I',module,start+23*4,symbols['af_v3_player_draw_static_item'])
    draw['sha256']=sha256(module[start:start+n])
    patched=bytearray(owner);patches=current['patches']
    for call,*_ in POLL_SITES:
        row=next(r for r in patches if r['offset']==call-PLAYER_RAM)
        if u32(patched,row['offset'])!=row['after']:raise ValueError('Changed registered input poll')
        row['after']=jump(symbols['af_v3_player_handheld_poll'],link=True)
        struct.pack_into('>I',patched,row['offset'],row['after'])
    _,_,_,locations,_=native_references(owner,reloc)
    hooks=[]
    for entry,name,expected in (
            (0x808BD430,'af_v3_player_equipment_select',(0x2DE10024,0x1020004F)),
            (0x808BD638,'af_v3_player_equipment_passive',(0x28A30002,0x38640001))):
        offset=entry-PLAYER_RAM
        if struct.unpack_from('>2I',owner,offset)!=expected or any(offset+i in locations for i in (0,4)):
            raise ValueError('Changed native selection branch or relocation')
        for i,after in enumerate((jump(symbols[name]),0)):
            patches.append(dict(offset=offset+i*4,before=expected[i],after=after))
            struct.pack_into('>I',patched,offset+i*4,after)
        hooks.append(dict(entry=entry,symbol=name,target=symbols[name],before=struct.pack('>2I',*expected).hex()))
    selection.update(table_offset=SELECTION_OFFSET,table_ram=RAM+SELECTION_OFFSET,hooks=hooks,
        native_consumers=dict(start=first,end=last,sha256=sha256(value)),
        original_switch_sha256=sha256(owner[table_start:table_start+144]),
        scene_rules_retained=True,hidden_and_force_visible_retained=True,
        native_selection_tested=False,ordinary_equipped_fan_tested=False)
    current.update(code=compiled,equipment_selection=selection,owner_sha256=sha256(patched))
    current['fan_activation']['inventory_selection_installed']=True
    report['kind_readers']['selector_changed']=True
    report['player_motion']['owner_sha256']=sha256(patched)
    blob[at:at+len(module)]=module
    report.update(sha256=sha256(module),crc32=zlib.crc32(module))
    return report,{PLAYER_VROM:bytes(patched)}


def activate_fan_action(base,prior,blob,core,original,output):
    """Publish implemented callbacks and ordinary polling, not inventory choices."""
    old=prior['equipment_resources'];actions=old['player_actions'];at=old['blob_offset']
    module=bytearray(blob[at:at+old['bytes']]);files=by_vrom(base)
    owner=files[PLAYER_VROM].extract(base);reloc=files[PLAYER_RELOC].extract(base)
    if (sha256(module)!=old['sha256'] or actions['enabled_imported_actions']
            or not actions.get('held_dispatch') or actions.get('fan_activation')
            or sha256(owner)!=actions['owner_sha256'] or sha256(reloc)!=actions['relocation_sha256']):
        raise ValueError('Fan activation requires the complete tested held/action dependencies')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    audit=fan_action_audit(source,owner,core,original)
    bindings=control_bindings(source,owner,core,original,old)
    n=actions['code']['bytes']
    if sha256(module[CODE_OFFSET:CODE_OFFSET+n])!=actions['code']['sha256'] or any(module[CODE_OFFSET+n:TABLE_OFFSET]):
        raise ValueError('Changed action code before callback activation')
    code,compiled=compile_part('player_actions',output/'player_actions',
        primary_source='overlays/v3/player_actions.S',extra_sources=('overlays/v3/player_actions.c',),
        defines=(f'AF_V3_FAN_SOUND=0x{actions["fan_frame_flow"]["native_sound_id"]:04X}',
                 f'AF_V3_HELD_POINTER=0x{old["code"]["symbols"]["af_v3_equipment_pointer"]:08X}u'))
    if len(code)>TABLE_OFFSET-CODE_OFFSET or code[:80]!=module[CODE_OFFSET:CODE_OFFSET+80]:
        raise ValueError('Action rebuild changes an installed dispatcher')
    module[CODE_OFFSET:TABLE_OFFSET]=code+bytes(TABLE_OFFSET-CODE_OFFSET-len(code))
    symbols=compiled['symbols'];report=copy.deepcopy(old);tables=report['player_actions']['tables']
    held_draw=report['player_actions']['held_dispatch']['tables'][1]
    start=held_draw['offset'];n=held_draw['bytes']
    if sha256(module[start:start+n])!=held_draw['sha256']:raise ValueError('Changed complete held draw table')
    struct.pack_into('>I',module,start+23*4,symbols['af_v3_player_draw_static_item'])
    held_draw['sha256']=sha256(module[start:start+n])
    callbacks={'Player_actor_setup_main_Swing_fan':symbols['af_v3_player_fan_setup'],
               'Player_actor_main_Swing_fan':symbols['af_v3_player_fan_main'],
               'Player_actor_Item_net_CulcJointAngle_dummy_net_reset':0x808BE140}
    installed=[]
    for row in tables:
        if row['width']!=4:continue
        start=row['offset'];n=row['bytes']
        if sha256(module[start:start+n])!=row['sha256'] or u32(module,start+109*4):
            raise ValueError('Changed previously disabled fan callback slot')
        callback=row['source_callbacks'].get('109')
        if callback:
            name=callback['symbol']
            if name not in callbacks:raise ValueError('Unimplemented source fan callback')
            struct.pack_into('>I',module,start+109*4,callbacks[name])
            installed.append(dict(consumer=row['native_entry'],source=name,target=callbacks[name],
                offset=start+109*4))
            row['sha256']=sha256(module[start:start+n])
    if len(installed)!=3:raise ValueError('Incomplete source fan callback set')
    native=by_vrom(original)[PLAYER_VROM].extract(original)
    umbrella=jump(0x808B7DD8,link=True)
    original_calls={PLAYER_RAM+i for i in range(0,TEXT_SIZE,4) if u32(native,i)==umbrella}
    expected={x[0] for x in POLL_SITES}|{0x808DCAA0}
    if original_calls!=expected:raise ValueError('Changed complete umbrella polling inventory')
    _,_,records,locations,_=native_references(owner,reloc)
    patched=bytearray(owner);patches=[];removed=set();consumers=[]
    for call,start,end in POLL_SITES:
        value=owner[start-PLAYER_RAM:end-PLAYER_RAM]
        offset=call-PLAYER_RAM;record=locations.get(offset)
        if (value!=native[start-PLAYER_RAM:end-PLAYER_RAM] or u32(owner,offset)!=umbrella
                or record is None or record>>24&63!=4
                or u32(owner,offset+4)!=0x24050004
                or u32(owner,offset+8)!=jump(0x808BA7BC,link=True)):
            raise ValueError('Changed complete ordinary poll consumer or call relocation')
        after=jump(symbols['af_v3_player_handheld_poll'],link=True)
        struct.pack_into('>I',patched,offset,after)
        patches.append(dict(offset=offset,before=umbrella,after=after));removed.add(record)
        consumers.append(dict(entry=start,end=end,call=call,sha256=sha256(value)))
    kept=[r for r in records if r not in removed]
    fixed=bytearray(reloc);struct.pack_into('>I',fixed,16,len(kept))
    fixed[20:-4]=struct.pack('>'+str(len(kept))+'I',*kept)+bytes(len(fixed)-24-len(kept)*4)
    blob[at:at+len(module)]=module
    report.update(sha256=sha256(module),crc32=zlib.crc32(module))
    report['player_motion'].update(owner_sha256=sha256(patched),reloc_sha256=sha256(fixed))
    bindings.update(action_callbacks_installed=True,poll_hooks_installed=True)
    report['player_actions'].update(code=compiled,owner_sha256=sha256(patched),relocation_sha256=sha256(fixed),
        patches=actions['patches']+patches,removed_relocations=actions['removed_relocations']+len(removed),
        fan_control_flow=bindings,enabled_imported_actions=[109],fan_action_installed=True,
        disabled_indices=[i for i in range(NATIVE_COUNT,COUNT) if i!=109],
        fan_activation=dict(audit=audit,callbacks=installed,poll_consumers=consumers,
            retained_umbrella_repeat_call=0x808DCAA0,inventory_selection_installed=False,
            crossed_release_events_preserved=True,wrapped_end_event_preserved=True,
            logical_imports_added=0,ordinary_equipped_fan_tested=False))
    report['player_actions']['fan_frame_flow'].update(action_callbacks_installed=True,poll_hooks_installed=True)
    report['player_actions']['held_dispatch']['net_reset']['installed']=True
    return report,{PLAYER_VROM:bytes(patched),PLAYER_RELOC:bytes(fixed)}


def refresh_controls(base,prior,blob,core,original,output):
    """Extend the existing action code in place; keep incomplete actions off."""
    old=prior['equipment_resources'];actions=old['player_actions'];at=old['blob_offset']
    module=bytearray(blob[at:at+old['bytes']])
    if (old['bytes']!=MODULE_SIZE or sha256(module)!=old['sha256']
            or old['ram']!=RAM or old['vrom']!=BLOB+at
            or actions['enabled_imported_actions'] or actions.get('fan_control_flow')):
        raise ValueError('Control integration requires the unchanged shared action tables')
    files=by_vrom(base);owner=files[PLAYER_VROM].extract(base)
    if (sha256(owner)!=actions['owner_sha256'] or
            sha256(files[PLAYER_RELOC].extract(base))!=actions['relocation_sha256']):
        raise ValueError('Changed player action owner or relocations')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    bindings=control_bindings(source,owner,core,original,old)
    previous=actions['code'];n=previous['bytes']
    if (sha256(module[CODE_OFFSET:CODE_OFFSET+n])!=previous['sha256']
            or any(module[CODE_OFFSET+n:TABLE_OFFSET])):
        raise ValueError('Changed player action code reservation')
    code,compiled=compile_part('player_actions',output/'player_actions',
        primary_source='overlays/v3/player_actions.S',extra_sources=('overlays/v3/player_actions.c',))
    if len(code)>TABLE_OFFSET-CODE_OFFSET or code[:n]!=module[CODE_OFFSET:CODE_OFFSET+n]:
        raise ValueError('Player control extension changed original dispatch code')
    for name in ('af_v3_player_action_v0','af_v3_player_action_t9'):
        if compiled['symbols'][name]!=previous['symbols'][name]:
            raise ValueError('Player control extension moved installed dispatch')
    module[CODE_OFFSET:TABLE_OFFSET]=code+bytes(TABLE_OFFSET-CODE_OFFSET-len(code))
    blob[at:at+len(module)]=module
    report=copy.deepcopy(old)
    report.update(sha256=sha256(module),crc32=zlib.crc32(module))
    report['player_actions'].update(code=compiled,fan_control_flow=bindings)
    return report,{}


def source_tables(source,categories=CATEGORIES,count=COUNT):
    """Resolve complete action tables through their actual donor consumers."""
    spans = {}
    for name,at,n in re.findall(
            r'^(\S+) = \.rodata:0x([0-9A-Fa-f]+);[^\n]* size:0x([0-9A-Fa-f]+) ',
            source.symbols,re.M):
        spans.setdefault(int(at,16),[]).append((name,int(n,16)))
    result=[]
    for donor,entry,bound,table,width in categories:
        raw,receipt=source.function(donor)
        if raw!=source.rel[source.sections[1][0]+donor:source.sections[1][0]+donor+receipt['bytes']]:
            raise ValueError('Action consumer does not match the checked donor')
        targets={r[3] for r in receipt['relocations'].values() if r[:3] in ((6,1,4),(4,1,4))
                 and len(spans.get(r[3],[]))==1 and spans[r[3]][0][1]==count*width}
        if len(targets)!=1:raise ValueError('Missing or ambiguous complete donor action table')
        target=targets.pop();n=count*width;base=source.sections[4][0]+target
        value=source.rel[base:base+n]
        references={k:v for k,v in receipt['relocations'].items() if v[1:]==(1,4,target)}
        if (len(value)!=n or {v[0] for v in references.values()}!={4,6}
                or sum(v[0]==4 for v in references.values())!=sum(v[0]==6 for v in references.values())):
            raise ValueError('Incomplete donor action table address binding')
        pointers={at-target:r for (section,at),r in source.section_relocations.items()
                  if section==4 and target<=at<target+n}
        callbacks={}
        if width==4:
            if any(value) or any(at%4 or row[:3]!=(1,1,1) for at,row in pointers.items()):
                raise ValueError('Invalid or external donor action callback')
            for at,row in pointers.items():
                _,callback=source.function(row[3]);callbacks[at//4]=callback
        elif pointers:
            raise ValueError('Unexpected pointer inside byte action metadata')
        result.append(dict(consumer=receipt,table_symbol=spans[target][0][0],
            source_section=4,source_offset=target,source_bytes=n,source_sha256=sha256(value),
            source_hex=value.hex() if width==1 else None,source_callbacks=callbacks,
            native_entry=entry,native_bound=bound,native_table=table,width=width))
    return result


def native_references(owner,reloc,*,expected_sections=(TEXT_SIZE,9488,880,0)):
    """Resolve all native table references, including multiple low consumers."""
    slots=relocation_offsets(reloc,len(owner));sections=struct.unpack_from('>5I',reloc)
    if sections[:4]!=expected_sections:raise ValueError('Changed complete owner dimensions')
    rows=list(struct.unpack_from('>'+str(sections[4])+'I',reloc,20))
    high={};groups={};absolute={};locations={}
    for record in rows:
        section,kind,offset=record>>30,record>>24&63,record&0xFFFFFF
        at=sum(sections[:section-1])+offset;word=u32(owner,at);locations[at]=record
        if kind==5:
            if word>>26!=15:raise ValueError('Changed native player high-half relocation')
            high[word>>16&31]=at;groups[at]=[]
        elif kind==6:
            reg=word>>21&31
            if reg not in high:raise ValueError('Unpaired native player table reference')
            hi=high[reg]
            target=((u32(owner,hi)&65535)<<16)+struct.unpack('>h',struct.pack('>H',word&65535))[0]
            groups[hi].append((at,target))
        elif kind==2:absolute[at]=word
    return groups,absolute,rows,locations,slots


def expanded_tables(source,owner,reloc,*,categories=CATEGORIES,native_count=NATIVE_COUNT,
                    count=COUNT,table_offset=TABLE_OFFSET,magic=0x41465041,complete_bound_scan=True):
    """Build full-capacity tables; unimplemented extra actions cannot dispatch."""
    groups,absolute,rows,locations,slots=native_references(owner,reloc)
    observed={PLAYER_RAM+i for i in range(0,TEXT_SIZE,4)
              if u32(owner,i)>>26 in (10,11) and u32(owner,i)&65535==native_count}
    if complete_bound_scan and observed!={r[2] for r in categories}:
        raise ValueError('Player action bound inventory changed')
    if not {r[2] for r in categories}<=observed:raise ValueError('Changed category callback limit')
    tables=source_tables(source,categories,count);data=bytearray(struct.pack('>4I',magic,1,count,len(tables)))
    removed=set();patches=[]
    for table in tables:
        target,width=table['native_table'],table['width'];n=native_count*width
        old=owner[target-PLAYER_RAM:target-PLAYER_RAM+n]
        if len(old)!=n:raise ValueError('Truncated original action table')
        pairs=[]
        for hi,lows in groups.items():
            if any(target<=address<target+n for _,address in lows):
                if any(address!=target for _,address in lows):
                    raise ValueError('Shared unrelated high half or interior action reference')
                for lo,address in lows:
                    if (PLAYER_RAM+hi,PLAYER_RAM+lo,address)==RETAINED_BOUNDARY:
                        if (u32(owner,hi)!=0x3C04808E or u32(owner,lo)!=0x2484F2BC
                                or u32(owner,0x808B99DC-PLAYER_RAM)!=0x2442F29C
                                or u32(owner,0x808B99F8-PLAYER_RAM)!=0x24420004
                                or u32(owner,0x808B9A00-PLAYER_RAM)!=0x0044082B):
                            raise ValueError('Changed spatial-search array-end reference')
                        continue
                    pairs.append((hi,lo))
        if (len(pairs)!=(2 if table['native_entry']==0x808DDA18 else 1)
                or any(target<=v<target+n for v in absolute.values())):
            raise ValueError('Changed complete native action reference inventory')
        data.extend(bytes(-len(data)%4));offset=table_offset+len(data);address=RAM+offset
        if width==1:
            value=old+bytes.fromhex(table['source_hex'])[native_count:]
        else:
            for at,pointer in enumerate(struct.unpack('>'+str(native_count)+'I',old)):
                location=target-PLAYER_RAM+4*at
                if pointer:
                    if not PLAYER_RAM<=pointer<PLAYER_RAM+TEXT_SIZE or pointer%4 or location not in slots:
                        raise ValueError('Unrelocated or external original action callback')
                elif location in slots:raise ValueError('Relocated null original action callback')
            value=old+bytes((count-native_count)*4)
        data.extend(value)
        for hi,lo in pairs:
            for at,part in ((hi,(address+0x8000)>>16),(lo,address&65535)):
                if at in removed:raise ValueError('Overlapping extended action table references')
                before=u32(owner,at);patches.append(dict(offset=at,before=before,after=before&0xFFFF0000|part))
                removed.add(at)
        at=table['native_bound']-PLAYER_RAM;before=u32(owner,at)
        if at in slots:raise ValueError('Relocated action limit instruction')
        patches.append(dict(offset=at,before=before,after=before&0xFFFF0000|count))
        table.update(offset=offset,ram=address,bytes=len(value),sha256=sha256(value),
            native_sha256=sha256(old),references=[(PLAYER_RAM+a,PLAYER_RAM+b) for a,b in pairs])
    if table_offset+len(data)>MODULE_SIZE-16:raise ValueError('Action tables exceed their reservation')
    return data,tables,patches,removed,rows,locations


def install(base,prior,blob,core,original,output):
    old=prior.get('equipment_resources',{})
    if (old.get('player_actions',{}).get('tool_motion') and
            not old['player_actions'].get('tool_transitions')):
        return refresh_tool_transitions(base,prior,blob,core,original,output)
    if (old.get('player_actions',{}).get('tool_controls') and
            not old['player_actions'].get('tool_motion')):
        return refresh_tool_motion(base,prior,blob,core,original,output)
    if (old.get('inventory_preview',{}).get('balloon_drawer') and
            not old.get('player_actions',{}).get('tool_controls')):
        return refresh_tool_controls(base,prior,blob,core,original,output)
    if (old.get('inventory_preview',{}).get('animated_rigs_installed') and
            old.get('player_joint_work',{}).get('vectors',7)>
            old['inventory_preview'].get('joint_work',{}).get('vectors',7)):
        from v3_inventory_equipment import grow_joint_work
        return grow_joint_work(base,prior,blob,core,original,output)
    if (old.get('inventory_preview',{}).get('joint_work',{}).get('vectors',0)>=8
            and not old.get('held_rig_actions',{}).get('balloon')):
        return refresh_balloon_actions(base,prior,blob,core,original,output)
    if (old.get('held_rig_actions',{}).get('balloon') and
            not old.get('inventory_preview',{}).get('balloon_drawer')):
        from v3_inventory_equipment import refresh_rigs as inventory_rigs
        return inventory_rigs(base,prior,blob,core,original,output)
    if old.get('held_rig_actions',{}).get('loop_sound_installed') and not old['inventory_preview'].get('animated_rigs_installed'):
        from v3_inventory_equipment import refresh_rigs as inventory_rigs
        return inventory_rigs(base,prior,blob,core,original,output)
    if old.get('held_rig_actions') and not old['held_rig_actions'].get('loop_sound_installed'):
        return refresh_rig_sound(base,prior,blob,core,original,output)
    if old.get('animated_rigs') and not old.get('held_rig_actions'):
        return refresh_rigs(base,prior,blob,core,original,output)
    if old.get('player_actions'):
        if old.get('pocket_icons'):
            from v3_inventory_equipment import install as inventory_equipment
            return inventory_equipment(base,prior,blob,core,original,output)
        if old.get('parent_readers'):
            return refresh_pocket_icons(base,prior,blob,core,original,output)
        if old['player_actions'].get('equipment_selection'):
            return refresh_parent_readers(base,prior,blob,core,original,output)
        if old['player_actions'].get('fan_activation'):
            return refresh_selection(base,prior,blob,core,original,output)
        if old['player_actions'].get('held_dispatch'):
            return activate_fan_action(base,prior,blob,core,original,output)
        if old['player_actions'].get('fan_frame_flow'):
            return refresh_held_dispatch(base,prior,blob,core,original,output)
        if old['player_actions'].get('fan_control_flow'):
            return refresh_frame_flow(base,prior,blob,core,original,output)
        return refresh_controls(base,prior,blob,core,original,output)
    if not old.get('kind_readers') or old.get('player_actions') or old.get('bytes')!=SIZE:
        raise ValueError('Action tables require the complete, unextended equipment-kind module')
    at=old['blob_offset'];module=bytearray(blob[at:at+SIZE])
    if sha256(module)!=old['sha256'] or old['ram']!=RAM or old['vrom']!=BLOB+at:
        raise ValueError('Changed installed equipment module')
    if RAM+MODULE_SIZE>prior['furniture']['bank_pool']['start']:
        raise ValueError('Extended equipment code overlaps native furniture model banks')
    files=by_vrom(base);native=by_vrom(original)
    owner=files[PLAYER_VROM].extract(base);reloc=files[PLAYER_RELOC].extract(base)
    native_owner=native[PLAYER_VROM].extract(original);native_reloc=native[PLAYER_RELOC].extract(original)
    if sha256(owner)!=old['player_motion']['owner_sha256'] or reloc!=native_reloc:
        raise ValueError('Changed player owner or original relocations')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    data,tables,patches,removed,rows,locations=expanded_tables(source,native_owner,native_reloc)
    # Compare complete consumers, not just their changed instructions. Current
    # kind/resource adapters live outside these action consumers.
    boundaries=sorted(set(int(a,16) for a in re.findall(r'= 0x([0-9A-Fa-f]+); // type:func',
        (ROOT/'upstream/af/linker_scripts/jp/symbol_addrs_overlays.txt').read_text())))
    for table in tables:
        entry=table['native_entry'];end=min(x for x in boundaries if x>entry)
        a,b=entry-PLAYER_RAM,end-PLAYER_RAM
        if owner[a:b]!=native_owner[a:b]:raise ValueError('Changed complete native action consumer')
        table.update(native_end=end,native_consumer_sha256=sha256(owner[a:b]))
        a=table['native_table']-PLAYER_RAM;n=NATIVE_COUNT*table['width']
        if owner[a:a+n]!=native_owner[a:a+n]:raise ValueError('Changed original action metadata')
    code,compiled=compile_part('player_actions',output/'player_actions',primary_source='overlays/v3/player_actions.S')
    if len(code)>TABLE_OFFSET-CODE_OFFSET:raise ValueError('Player action code exceeds table boundary')
    for entry,register in DISPATCH:
        at=entry-PLAYER_RAM;before=u32(owner,at)
        if before!=register<<21|0xF809 or at in locations:
            raise ValueError('Changed native action indirect call')
        helper='af_v3_player_action_t9' if register==25 else 'af_v3_player_action_v0'
        patches.append(dict(offset=at,before=before,after=jump(compiled['symbols'][helper],link=True)))
    patched=bytearray(owner)
    for row in patches:
        at=row['offset']
        if u32(patched,at)!=row['before']:raise ValueError('Changed native action patch input')
        struct.pack_into('>I',patched,at,row['after'])
    # Remove only table-address relocations; original tables, callback pointers,
    # unrelated constants, and native calls retain their original relocations.
    kept=[record for record in rows if record not in {locations[x] for x in removed}]
    new_reloc=bytearray(reloc);struct.pack_into('>I',new_reloc,16,len(kept))
    new_reloc[20:-4]=struct.pack('>'+str(len(kept))+'I',*kept)+bytes(len(reloc)-24-len(kept)*4)
    module.extend(bytes(MODULE_SIZE-len(module)))
    module[CODE_OFFSET:CODE_OFFSET+len(code)]=code
    module[TABLE_OFFSET:TABLE_OFFSET+len(data)]=data
    struct.pack_into('>4I',module,MODULE_SIZE-16,*([GUARD]*4))
    blob.extend(bytes(-len(blob)%16));position=len(blob);blob.extend(module)
    if BLOB+len(blob)>END:raise ValueError('Extended actions exceed import ROM storage')
    report=copy.deepcopy(old)
    report.update(bytes=MODULE_SIZE,vrom=BLOB+position,blob_offset=position,
        sha256=sha256(module),crc32=zlib.crc32(module),additional_resident_bytes=MODULE_SIZE-SIZE)
    report['player_motion']['owner_sha256']=sha256(patched)
    report['player_motion']['reloc_sha256']=sha256(new_reloc)
    report['player_actions']=dict(format='AFV3-PLAYER-ACTION-TABLES-1',
        native_count=NATIVE_COUNT,count=COUNT,tables=tables,code=compiled,
        table_offset=TABLE_OFFSET,table_bytes=len(data),code_offset=CODE_OFFSET,
        patches=sorted(patches,key=lambda r:r['offset']),removed_relocations=len(removed),
        owner_sha256=sha256(patched),relocation_sha256=sha256(new_reloc),
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()),
        disabled_indices=list(range(NATIVE_COUNT,COUNT)),enabled_imported_actions=[],
        constructor_ram=CTOR,constructor_slot=CTOR_SLOT,
        logical_imports_added=0,ordinary_actions_tested=False,fan_action_installed=False)
    return report,{PLAYER_VROM:bytes(patched),PLAYER_RELOC:bytes(new_reloc)}
