"""Install the complete donor freshwater patrol without moving retained code."""
import copy
import struct
import zlib

from aflib import by_vrom,sha256,u32
from v3_asset_loader import ROOT,compile_part
from v3_furniture_pipeline import Source
from v3_player_actions import native_references

RAM,END,GUARD=0x80653920,0x80654000,0xAF465750
TAIL,TAIL_END=0x80654B70,0x80654F00
SOURCES=('tools/v3_freshwater_movement.py','overlays/v3/creature_freshwater.c',
    'overlays/v3/creature_freshwater.S','overlays/v3/creature_freshwater.ld',
    'tools/v3_asset_loader.py','tools/v3_furniture_install.py','tools/v3_creature_choices.py')
DONOR=(
    ('aGTT_swim',0x233CAC,'a1c9e334e8e67c9dc233a75f357c2f34362ccbb1bb08736267ed8d357f29d551'),
    ('aGTT_wait',0x233BBC,'6c56c3c90969cde9f6fe6f627879a79e28c975ef2fdf6bde6addb92a46d7a1f6'),
    ('aGTT_escape',0x23466C,'df7e02c862a888a74ead47fed515490678dc75840596a26fae9b92a9453b5adc'),
    ('aGTT_swim_init',0x234748,'4f1d711b6ced6895b786945e04715e5e800348352c4a3f04ff7b358460f4195d'),
    ('aGTT_wait_init',0x2349C4,'9d5f250802ab6e0cef9e0061205dcf2e0bcc76f710e658a513538d31ce61f9ff'),
    ('aGTT_escape_init',0x234A64,'22bb8cc5f188c2bd75519e1400074fcd27ac073fc0eba50f3b8a137505cec546'),
    ('aGTT_swim_speed_check',0x2333D8,'76f5006220cecc5fbf18ed97ba53ac4b05120b84383b4777115b827c55243ac2'),
    ('aGTT_swim_speed_change',0x233464,'9762d0db93a1a6ec6d7d664a8cc6d3c22c36afb6e173cf7945135832f3b93e57'),
    ('aGTT_chase_s_angle',0x233238,'6d1d8eeadb006a5fc2dca12b519282f80ca7396f2068d141640726480a6cbd4f'),
    ('aGTT_speed_reset',0x232D38,'26404ecfb8e1a36e471da7fbc1f6a6907d28251a11926fddd2f4855fd56fb53c'),
    ('aGTT_flow_direction',0x2335E0,'f995059708707cee6be9cb5520a43ad129bd4c7e1de71928873be1daa3a5ae1f'),
    ('aGTT_Get_flow_angle_rv',0x2335B4,'8352e39549fa10755e2d34bb3c4fa09b62637271ef16b75a12951656108d0dce'),
    ('aGTT_Get_flow_angle',0x233578,'fe879549c39e82491ff20796954b46fe7c3c0643d0b946ddef19457d3b6a57ac'),
    ('aGYO_check_wall',0x2339D0,'047d6056834bf344152ac81a4a8089cd8d253dc5b63dd1d79903cacddad6d371'),
    ('aGTT_player_near',0x23387C,'28ed484a0e4e9f0e8a0aef4a6631aab9cb6b07fd16220690bf19792d9f9d11a9'),
    ('aGTT_search_Uki',0x2336BC,'e3991342a29f1e5f842fa94844bd8ebe1af97dd0359051633e7b40c34ca66b06'),
    ('aGTT_setupAction',0x234A84,'c2d300b9d324c891a47a07f9849917105955b52fa71bee7706cd26985538ef74'),
    ('chase_angle',0x4A984,'eb8171c03f477f64f8fd04968e08e23e50db763d3bf2576f2fb4c401266e1bba'),
    ('chase_f',0x4AAA8,'5b4fc1946bec852671e647ef64a9fc0ebe668093b833923f3ae42bb64eb31b54'),
)
BINDINGS=((0x80933B78,0x8093353C,'swim_init'),(0x80933B7C,0x80933790,'wait_init'),
    (0x80933B80,0x8093380C,'escape_init'),(0x80933B94,0x80932994,'swim'),
    (0x80933B98,0x809328A8,'wait'),(0x80933B9C,0x809334A8,'escape'))
# Complete retained native services. Field layouts and player enums are native;
# the search service retains the installed golden-rod angles and size tables.
SERVICES=(('flow',0x8093214C,0x80932188),('flow_reverse',0x80932188,0x809321B8),
    ('flow_direction',0x809321B8,0x80932238),
    ('wall',0x809325CC,0x809326A0),('player_near',0x8093246C,0x809325CC),
    ('search',0x80932298,0x8093246C),('setup',0x8093382C,0x80933874))


def source_contract():
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    functions=[]
    for name,at,digest in DONOR:
        code,proof=source.function(at)
        if proof['symbol']!=name or sha256(code)!=digest:
            raise ValueError('Changed complete freshwater donor function: '+name)
        functions.append(proof)
    return functions


def install(base,prior,blob,core,module,output):
    del core,module
    e=copy.deepcopy(prior['equipment_resources']);fish=e['creature_fish'];world=fish['world']
    if world.get('freshwater') or not world.get('behaviour_choices'):
        raise ValueError('Freshwater movement requires its completed category and unmodified native alternative')
    p=world['packet'];raw=bytearray(blob[p['blob_offset']:p['blob_offset']+p['bytes']])
    start=RAM-p['ram'];end=END-p['ram']
    if (sha256(raw)!=p['sha256'] or zlib.crc32(raw)!=p['crc32'] or
            p['ram']!=0x8064A000 or world['compiled']['bytes']>start or
            world['save']['codec'].get('cartridge_allocation_verified') is not True or
            max(r['ram']+r['bytes'] for r in world['pocket_icons']['resources'])>RAM or
            world['ui']['code_ram']<END or any(raw[start:end]) or
            world['ui']['code_ram']+world['ui']['code']['bytes']>TAIL or
            world['ui']['grid']['ram']<TAIL_END or any(raw[TAIL-p['ram']:TAIL_END-p['ram']])):
        raise ValueError('Freshwater movement overlaps retained world code, icons, or creature profiles')
    row=next(r for r in fish['owners'] if r['name']=='river');files=by_vrom(base)
    data=files[row['vrom']].extract(base);rel=files[row['reloc']].extract(base)
    if (row['ram']!=0x809317D0 or sha256(data)!=row['sha256'] or sha256(rel)!=row['reloc_sha256'] or
            sha256(data)!='242a5116e30f3b8d5945e5dbf767777dee765df578292e9faeb0b636c23d0bf4' or
            sha256(rel)!='14aa0f811c218b87efb7588fad8c48f3f619cf225ee37bbdd46e21a501b5ba5f'):
        raise ValueError('Changed complete native freshwater owner or original instructions')
    functions=source_contract();symbols=world['compiled']['symbols']
    code,compiled=compile_part('creature_freshwater',output/'creature_freshwater',
        extra_sources=('overlays/v3/creature_freshwater.S',),link_symbols={n:symbols[n] for n in
            ('af_patrol_random','af_patrol_random2','af_patrol_sin',
             'af_patrol_chase_angle','af_patrol_chase_float')})
    symbols=compiled['symbols']
    if (symbols['af_fresh_main_end']>END-16 or symbols['af_fresh_tail_start']!=TAIL or
            symbols['af_fresh_tail_end']>TAIL_END-16 or len(code)!=symbols['af_fresh_tail_end']-RAM):
        raise ValueError('Freshwater movement exceeds authenticated world padding')
    fragments=[]
    for a,b in ((RAM,symbols['af_fresh_main_end']),(TAIL,symbols['af_fresh_tail_end'])):
        part=code[a-RAM:b-RAM];raw[a-p['ram']:b-p['ram']]=part
        fragments.append(dict(ram=a,bytes=len(part),sha256=sha256(part)))
    for end_ram in (END,TAIL_END):
        raw[end_ram-p['ram']-16:end_ram-p['ram']]=struct.pack('>4I',*([GUARD]*4))
    sections=struct.unpack_from('>4I',rel)
    _,absolute,records,locations,_=native_references(data,rel,expected_sections=sections)
    updated=bytearray(data);patches=[];removed=set()
    for address,before,name in BINDINGS:
        at=address-row['ram'];after=compiled['symbols']['af_v3_freshwater_'+name]
        if u32(data,at)!=before or absolute.get(at)!=before:
            raise ValueError('Changed complete freshwater callback tables')
        struct.pack_into('>I',updated,at,after);removed.add(locations[at])
        patches.append(dict(address=address,before=before,after=after))
    keep=[r for r in records if r not in removed]
    fixed=(struct.pack('>5I',*sections,len(keep))+struct.pack('>'+str(len(keep))+'I',*keep)
        +bytes(len(rel)-24-4*len(keep))+struct.pack('>I',len(rel)))
    native_references(updated,fixed,expected_sections=sections)
    retained=[dict(name=n,address=a,bytes=b-a,sha256=sha256(data[a-row['ram']:b-row['ram']]))
        for n,a,b in SERVICES]
    world['freshwater']=dict(format='AFV3-FRESHWATER-PATROL-1',installed=True,
        code=dict(compiled,ram=RAM,fragments=fragments),source_functions=functions,retained_services=retained,
        callbacks=patches,relocation=dict(before=rel.hex(),after=fixed.hex()),
        reservations=[dict(ram=a,bytes=b-a,guard=b-16,guard_value=GUARD)
            for a,b in ((RAM,END),(TAIL,TAIL_END))],
        original_owner_sha256=sha256(data),original_reloc_sha256=sha256(rel),
        saved_layout_changed=False,additional_resident_bytes=0,native_execution_tested=False,
        sources={path:sha256((ROOT/path).read_bytes()) for path in SOURCES})
    blob[p['blob_offset']:p['blob_offset']+p['bytes']]=raw
    p.update(sha256=sha256(raw),crc32=zlib.crc32(raw))
    fish['sources'].update(world['freshwater']['sources'])
    # Choice composition installs all six pointers and their matching relocation
    # records together. The pinned N64 owner, including its tables, stays exact.
    return e,{},{},[]
