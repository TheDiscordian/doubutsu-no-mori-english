"""Prepare complete animated room particles through the shared model converter.

These resources remain unavailable until the native effect owner, emitter
callbacks, and complete sound programmes are installed together.
"""
import argparse
import copy
import json
import struct
from pathlib import Path

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from apply_translation import write_new
from v3_asset_loader import ROOT,BLOB,compile_part
from v3_furniture_pipeline import Source,prepare_models,compile_models,assemble_models
from v3_furniture_materials import CATEGORY

FUNCTIONS = (
    (0x2AE544,124,'126a16b5080f9c2d2d6bb35c5f9e72a3ed788b248c25f3a04197f1a63baff2cc'),
    (0x2AE5C0,436,'6ea2e3efcd70e5ec5ebd4222c71f7d35eaf874e60b3bb30663ec0db95380349a'),
    (0x2AE774,156,'5a11577c79e20b92254462e568bfe48ee2a75550b48968b49eec3b7304b0145a'),
    (0x2AE810,1024,'c65ef6b783d8172ea770e14d14a8210f449599f510d3f9c0b8cd4a85502834a6'),
    (0x2A3ED0,116,'0c5d2e56c5b920efcd2c8fe24bde94f34230fb894eba47fd4f64dfea974a4dad'),
    (0x2A3F44,780,'67faa56c5ed6026a5f5f776ce0d9f62cf075033aa74c6809c58e486850ba755c'),
    (0x2A4250,608,'1ac8f1d9b4e840154ecff7549574c17465635c06eb89d3653139fcb9671b8891'),
    (0x2A44B0,196,'0dcd5df00c8f09e90c50a3e278acab6cb2bdbed8f5fb76f983f78ffb623cb2c8'),
)
SOURCES=('tools/v3_room_particles.py','tools/v3_furniture_art.py','tools/v3_furniture_pipeline.py',
    'tools/v3_furniture_materials.py','overlays/v3/room_particles.c','overlays/v3/room_effects.h',
    'overlays/v3/room_effects.ld')


def sound_dependencies(source):
    contract=source_contract(source)
    return [dict(source_effect=122,sound_word=contract['projectile_source_sound'],source=contract)]


def runtime_defines(particles):
    rows=particles['objects'];word=particles['sound_word']
    if not 0<word<0x8000 or word==0xFFFF:
        raise ValueError('Particle callbacks require a complete installed positional sound')
    return ('AF_V3_ROOM_PARTICLES',f'AF_EFFECT_STEAM_TEXTURES=0x{rows["steam"]["base"]:X}u',
        f'AF_EFFECT_STEAM_MODEL=0x{rows["steam"]["models"]["dust"]:X}u',
        f'AF_EFFECT_STEAM_STEW=0x{rows["steam"]["models"]["stew"]:X}u',
        f'AF_EFFECT_PROJECTILE_MODEL=0x{rows["projectile"]["models"]["opaque"]:X}u',
        f'AF_EFFECT_PROJECTILE_SOUND=0x{word:X}u')


def native_contract(image,original,report=None):
    from v3_furniture_motion import native_contract as motion_contract,restore_embedded_dispatch
    # Reuse the checked native contact owner, frame cadence, and state mapping.
    runtime=report.get('equipment_resources',{}).get('room_rigs') if report else None
    contract=motion_contract(image,runtime);files=by_vrom(image);native=by_vrom(original)
    blocks=[]
    for name,vrom,ram,at,n in (
        ('random',0x1060,0x80025C60,0x8002C970,48),
        ('sine_cosine',CODE_VROM,CODE_RAM,0x80099A54,128),
        ('debug_initialization',CODE_VROM,CODE_RAM,0x8007A0C0,144),
        ('rotation_and_move',0x82D7F0,0x80936710,0x80944ED4,252)):
        raw=native[vrom].extract(original)[at-ram:at-ram+n]
        current=files[vrom].extract(image)
        if vrom==0x82D7F0 and runtime:current=restore_embedded_dispatch(current,runtime)
        if len(raw)!=n or current[at-ram:at-ram+n]!=raw:
            raise ValueError('Changed native particle binding: '+name)
        blocks.append(dict(name=name,address=at,bytes=n,sha256=sha256(raw)))
    # Rotation is written into the same native halfword before move dispatch.
    rotation=files[0x82D7F0].extract(image)
    if u32(rotation,0x80944F10-0x80936710)!=0xA60A0124:
        raise ValueError('Changed native furniture angle field')
    return dict(motion=contract,blocks=blocks,angle_offset=0x124,play_frame_offset=0x1EA0,
        debug_pointer=0x80138E50,debug_group=36,debug_register_base=0x14)


def installed_sound(image,report,core):
    from v3_sound_programs import installed_resource
    audio=report['equipment_resources'].get('furniture_audio',{})
    rows=[r for r in audio.get('programs',[]) if r['source_sound_word']==0x44F]
    if len(rows)!=1:raise ValueError('Projectile requires its complete installed source sound')
    row=rows[0];sequence,_,_=installed_resource(image,core,'seq',199)
    at,n=row['offset'],row['bytes'];word=row['native_sound_word']
    table=struct.unpack_from('>H',sequence,0x188+(word>>8)*2)[0]
    if (not 0<word<0x8000 or sha256(sequence[at:at+n])!=row['sha256'] or
            struct.unpack_from('>H',sequence,table+(word&255)*2)[0]!=at or
            core[0x80113B84-CODE_RAM+(word&255)]!=row['trigger_priority']):
        raise ValueError('Changed complete projectile sound/dispatch binding')
    return copy.deepcopy(row)


def install(base,prior,blob,core,original,output,directory):
    from v3_furniture_install import owner_tail_storage
    from v3_resource_capacity import checked_limit
    from v3_room_rig_runtime import publish_packet
    from v3_room_effects import RAM,INSTALLED_GRAPHICS,restore_controller,extend_controller
    prepared=json.loads((directory/'particles.json').read_bytes())
    if prepared.get('format')!='AFV3-ROOM-PARTICLES-PREPARED-1':
        raise ValueError('Unknown complete particle preparation')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    source_data=source_contract(source)
    if prepared['source']!=json.loads(json.dumps(source_data)):
        raise ValueError('Changed complete particle source')
    result=copy.deepcopy(prior['equipment_resources']);effects=result['room_rigs']['effects']
    if effects.get('particles'):raise ValueError('Complete particles are already installed')
    files=by_vrom(base);old=effects['controller']
    owner,reloc=restore_controller(files[old['vrom']].extract(base),files[old['reloc']].extract(base),old)
    bank_vrom=effects['bank'].get('vrom',0x1410000)
    bank=files[bank_vrom].extract(base)
    if sha256(bank)!=effects['bank']['sha256'] or sha256(bank)!=prepared['bank']['previous_sha256']:
        raise ValueError('Changed complete particle graphics prefix')
    for kind,p in models(source).items():
        row=prepared['objects'][kind];path=(directory/row['file']).resolve()
        if not path.is_relative_to(directory):raise ValueError('Particle path escapes preparation')
        asset=path.read_bytes();body=p[1]
        if (asset[:len(body)]!=body or row['resources']!=p[2] or
                (directory/kind/'commands.c').read_text()!=p[5] or sha256(asset)!=row['object_sha256']):
            raise ValueError('Changed complete prepared particle body or emitter')
        compiled={r['layer']:asset[r['native_offset']:r['native_offset']+r['bytes']] for r in row['model_records']}
        actual,offsets,records,_=assemble_models(p,compiled)
        if actual!=asset or offsets!=row['model_offsets'] or records!=row['model_records']:
            raise ValueError('Changed complete particle model assembly')
        bank,appended=append_object(bank,asset,records)
        if any(row[k]!=v for k,v in appended.items()):raise ValueError('Changed particle graphics binding')
    if bank!=(directory/'effect-art-bank.bin').read_bytes() or sha256(bank)!=prepared['bank']['sha256']:
        raise ValueError('Changed full particle graphics bank')
    sound=installed_sound(base,prior,core)
    particles=dict(format='AFV3-ROOM-PARTICLES-1',objects=prepared['objects'],source=prepared['source'],
        native=native_contract(base,original,prior),sound=sound,sound_word=sound['native_sound_word'],
        prepared_directory=str(directory.relative_to(ROOT)),prepared_sha256=sha256((directory/'particles.json').read_bytes()),
        installed=True,native_execution_tested=False)
    start=(len(blob)+15)&~15
    if BLOB+start+256>checked_limit(base,prior):raise ValueError('Complete particle profiles exceed import storage')
    blob.extend(bytes(start+256-len(blob)))
    previous_profiles=copy.deepcopy(effects['profiles'])
    effects['profiles']=[dict(id=111+i,kind=kind,blob_offset=start+64*i,vrom=BLOB+start+64*i,bytes=64)
        for i,kind in enumerate(('flash','flash_controller','steam','projectile'))]
    effects['particles']=particles
    effects['bank'].update(bytes=len(bank),sha256=sha256(bank),vrom=INSTALLED_GRAPHICS,
        resource_vrom=INSTALLED_GRAPHICS+(effects['bank']['graphics'][0]&0xFFFFFF)+8,
        additional_rom_bytes=effects['bank']['additional_rom_bytes']+len(bank)-files[bank_vrom].size)
    publish_packet(result,blob,output,core=core)
    loader=compile_part('effect_loader',output/'effect_loader',
        defines=(f'AF_EFFECT_PROFILES=0x{BLOB+start:X}u','AF_EFFECT_COUNT=4u'))
    additions=[]
    for i,row in enumerate(effects['profiles']):
        ram=0x80700000+i*0x100
        graphics=(old['additions'][i]['graphics'] if i<2 else prepared['objects'][row['kind']]['graphics'])
        additions.append(dict(id=row['id'],overlay=[row['vrom'],row['vrom']+32,ram,ram+32,ram],graphics=graphics,unique=0))
    changed,fixed,controller=extend_controller(owner,reloc,additions,loader=loader,graphics_vrom=INSTALLED_GRAPHICS)
    descriptor=0x801010B0-CODE_RAM;before=bytes.fromhex(old['descriptor']['after'])
    if core[descriptor:descriptor+32]!=before or files[old['reloc']].index!=files[old['vrom']].index+1:
        raise ValueError('Changed complete installed effect owner binding')
    after=struct.pack('>8I',old['vrom'],old['vrom']+len(changed),RAM,RAM+len(changed),0,RAM+0x36A0,0,0)
    core[descriptor:descriptor+32]=after
    changes={old['vrom']:changed,old['reloc']:fixed,bank_vrom:bank}
    moves=owner_tail_storage(base,files,list(changes.items()),minimum_end=files[BLOB].pstart+len(blob))
    growth=[]
    for move in moves:
        v=move['vrom']
        target=INSTALLED_GRAPHICS if v==bank_vrom else v
        if any(e.vstart<target+move['bytes'] and target<e.vend for key,e in files.items() if key!=v):
            raise ValueError('Expanded particle resource overlaps live virtual data')
        growth.append(dict(vrom=v,target_vrom=target,physical=move['physical'],previous_physical=files[v].pstart,
            bytes=move['bytes'],previous_bytes=files[v].size,sha256=move['sha256'],
            previous_sha256=move['original_sha256'],relocated=True,relocated_blockers=[]))
    controller.update(installed=True,vrom=old['vrom'],reloc=old['reloc'],ram=RAM,
        descriptor=dict(address=0x801010B0,before=before.hex(),after=after.hex()))
    particles.update(previous_profiles=previous_profiles,resource_growth=growth)
    effects.update(controller=controller,additional_scene_bytes=controller['additional_scene_bytes'],resource_growth=growth)
    effects['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    write_new(output/'particles.json',(json.dumps(particles,indent=2,sort_keys=True)+'\n').encode())
    return result,changes,dict(resource_growth=growth)


def source_contract(source):
    functions=[]
    for offset,size,digest in FUNCTIONS:
        raw,row=source.function(offset)
        if len(raw)!=size or sha256(raw)!=digest:
            raise ValueError('Changed complete source particle callback')
        functions.append(row)
    profiles=[]
    for symbol,group in (('iam_ef_soba_yuge',FUNCTIONS[:4]),('iam_ef_killer',FUNCTIONS[4:])):
        at,n=source.symbol(symbol);raw=source.raw(symbol)
        refs={p-at:row for (section,p),row in source.section_relocations.items()
              if section==5 and at<=p<at+n}
        if (raw!=bytes(16)+bytes.fromhex('fffe00ffc47a0cff') or
                refs!={i*4:(1,1,1,f[0]) for i,f in enumerate(group)}):
            raise ValueError('Changed complete particle profile')
        profiles.append(dict(symbol=symbol,offset=at,bytes=n,sha256=sha256(raw),functions=refs))
    data=[]
    for symbol,wanted in (
        ('eSoba_Yuge_2tile_texture_idx','0000000000000000000000000001000100010101010201020102020202030203020303030303030303030303'),
        ('eSoba_Yuge_prim_f','0000000000004080c0004080c0004080c00000000000')):
        raw=source.raw(symbol)
        if raw.hex()!=wanted:raise ValueError('Changed complete particle animation table')
        data.append(dict(symbol=symbol,offset=source.symbol(symbol)[0],bytes=len(raw),sha256=sha256(raw)))
    # Preserve a receipt for every referenced constant, including debug values,
    # bounds, damping, and interpolation endpoints. The checked REL owns them.
    constants=[]
    addresses=sorted({row[3] for f in functions for row in f['relocations'].values() if row[2]==4 and row[1]==1})
    for at in addresses:
        raw=source.rel[source.sections[4][0]+at:source.sections[4][0]+at+4]
        constants.append(dict(offset=at,hex=raw.hex()))
    return dict(functions=functions,profiles=profiles,tables=data,constants=constants,
        source_ticks_per_native_update=2,steam_ticks=44,projectile_ticks=360,
        source_effect_ids=[113,122],native_effect_ids=[113,114],projectile_source_sound=0x44F,
        native_scene_widths={6:6,20:4,21:6,22:8},debug_group=36,
        steam_debug_registers=[0x32,0x34,0x35,0x36,0x37,0x38,0x39])


def models(source):
    """Supply complete typed material frames, never hand-converted item art."""
    table,n=source.symbol('eSoba_Yuge_texture_table');refs=source.pointers(table,n)
    if n!=16 or any(source.data[table:table+n]) or set(refs)!=set(range(table,table+n,4)):
        raise ValueError('Incomplete steam texture table')
    frames=[]
    for i in range(4):
        name,at,size=source.containing(refs[table+i*4],exact=True)
        if (name!=f'ef_dust01_{i}' or size!=128 or source.pointers(at,size)):
            raise ValueError('Changed complete steam texture bank')
        frames.append(dict(symbol=name,donor_offset=at,bytes=size,source_sha256=sha256(source.raw(name))))
    def model(name):return source.containing(source.symbol(name)[0],exact=True)
    steam=dict(models=dict(dust=model('ef_dust01_modelT'),stew=model('ef_dust01_stew_modelT')),
        callback_adapter=dict(category=CATEGORY,material_frames=[
            dict(kind='texture',segment_address=i<<24,frames=frames) for i in (8,9)]))
    projectile=dict(models=dict(opaque=model('act_killer_model')))
    return {key:prepare_models(source,descriptor) for key,descriptor in
            (('steam',steam),('projectile',projectile))}


def append_object(bank,asset,models):
    """Rebase a complete converted object into the native shared effect bank."""
    if len(bank)&7 or not asset or len(asset)>3584 or len(asset)&15:
        raise ValueError('Particle object exceeds native graphics-pool capacity')
    start=len(bank);base=start+8;data=bytearray(asset);fixups=[]
    for row in models:
        at,n=row['native_offset'],row['bytes']
        if at&7 or n&7 or not 0<=at<=len(data)-n or sha256(data[at:at+n])!=row['output_sha256']:
            raise ValueError('Changed complete converted particle model')
        for p in range(at,at+n,8):
            a,b=struct.unpack_from('>II',data,p)
            if a>>24 in (0x01,0xFD,0xDE) and b>>24==6:
                if b&0xFFFFFF>=len(asset):raise ValueError('Particle pointer escapes complete object')
                struct.pack_into('>I',data,p+4,b+base);fixups.append(dict(offset=p+4,before=b,after=b+base))
    bank=bank+bytes(8)+data
    return bank,dict(graphics=[0x06000000+start,0x06000000+len(bank)],bytes=len(data),
        object_sha256=sha256(asset),installed_sha256=sha256(data),fixups=fixups,
        base=0x06000000+base,models={r['layer']:0x06000000+base+r['native_offset'] for r in models})


def prepare(output,base_lock):
    from v3_furniture_install import inputs
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):
        raise ValueError('Choose a fresh ignored particle preparation directory')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    image,report=inputs(base_lock);contract=source_contract(source);prepared=models(source)
    installed=report['equipment_resources']['room_rigs']['effects']
    bank=by_vrom(image)[installed['bank'].get('vrom',0x1410000)].extract(image)
    if sha256(bank)!=installed['bank']['sha256']:raise ValueError('Changed installed native effect bank')
    before=sha256(bank);output.mkdir(parents=True);rows={}
    for kind,p in prepared.items():
        directory=output/kind;directory.mkdir()
        asset,offsets,records,_=compile_models(directory,p)
        bank,row=append_object(bank,asset,records)
        row.update(resources=p[2],model_records=records,file=kind+'/object.bin',model_offsets=offsets)
        if kind=='steam':
            textures=[r for r in p[2] if r['kind']=='texture']
            if [r['native_offset'] for r in textures]!=[0,128,256,384]:
                raise ValueError('Steam frame bank is not complete and contiguous')
        write_new(directory/'object.bin',asset);rows[kind]=row
    write_new(output/'effect-art-bank.bin',bank)
    definitions=(f'AF_EFFECT_STEAM_TEXTURES=0x{rows["steam"]["base"]:X}u',
        f'AF_EFFECT_STEAM_MODEL=0x{rows["steam"]["models"]["dust"]:X}u',
        f'AF_EFFECT_STEAM_STEW=0x{rows["steam"]["models"]["stew"]:X}u',
        f'AF_EFFECT_PROJECTILE_MODEL=0x{rows["projectile"]["models"]["opaque"]:X}u',
        'AF_EFFECT_PROJECTILE_SOUND=0xFFFFu')
    # FFFF is an explicitly unresolved preparation binding, never a release
    # fallback. Installation must supply the complete imported sound word.
    _,code=compile_part('room_effects',output/'callbacks',defines=definitions,
        extra_sources=('overlays/v3/room_particles.c',))
    result=dict(format='AFV3-ROOM-PARTICLES-PREPARED-1',source=contract,objects=rows,code=code,
        bank=dict(bytes=len(bank),sha256=sha256(bank),previous_sha256=before),
        base_sha256=sha256(image),sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES},
        installed=False,selectable_imports_added=0,unresolved_sound_binding=True,
        pending=['complete sound installation','effect owner/profile extension',
                 'shared furniture emitters','focused installed native integration'])
    write_new(output/'particles.json',(json.dumps(result,indent=2,sort_keys=True)+'\n').encode())
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--base-lock',type=Path,required=True)
    args=parser.parse_args();r=prepare(args.output,args.base_lock)
    print(json.dumps(dict(objects={k:v['bytes'] for k,v in r['objects'].items()},
        callback_bytes=r['code']['bytes'],installed=False)))
