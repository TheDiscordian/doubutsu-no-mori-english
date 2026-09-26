"""Prepare complete animated room particles through the shared model converter.

These resources remain unavailable until the native effect owner, emitter
callbacks, and complete sound programmes are installed together.
"""
import argparse
import json
import struct
from pathlib import Path

from aflib import by_vrom,sha256,u32
from apply_translation import write_new
from v3_asset_loader import ROOT,compile_part
from v3_furniture_pipeline import Source,prepare_models,compile_models
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
    bank=by_vrom(image)[0x1410000].extract(image)
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
