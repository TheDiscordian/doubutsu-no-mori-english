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

from aflib import by_vrom,sha256
from apply_translation import write_new
from v3_asset_loader import ROOT, IMAGE
from v3_creature_field import named_table
from v3_creature_items import source_records
from v3_furniture_pipeline import Source

PROGRAMS = (
    ('tentou','aITT',3,'190408d3b79fb5573c0f0be83ef9a2317cf3526aacc4d20970cee9cad65f6b4b'),
    ('kera','aIKR',12,'a241fabdc24ccb4eadba3fa77b9d95d72eaf397e3832479ece05875fb7000824'),
    ('amenbo','aIAB',9,'8de9ecb7d51575ca8728adda9cd1a0e07d386f004a66d5d37717659822fb8ffb'),
    ('mino','aIMN',13,'8fe06ee0ef8c1ce72ea577568371e6665e2d78e86789d13f4f29f0e484d63a2b'),
    ('dango','aIDG',11,'86599c9c18f49aa8855bb628cc08f611b39635afeddf709f98f1ddc2bb25c84f'),
    ('ka','aIKA',10,'d46aa8b6a6835c05a9c71d9e96b4d1c5b2fb193fa0c73350a7a1c5cd2a208c08'),
)
SOURCES=('tools/v3_creature_insects.py','overlays/v3/creature_insects.h',
         'overlays/v3/creature_insects.c','overlays/v3/creature_insect_state.c')
NATIVE_FUNCTIONS=(
    (0x80A10210,0x80A102B8,'ceceb00fbf78bfb02831e6f0073c38b968e03dac21b2a17c02a0f7cadbd835aa'),
    (0x80A10558,0x80A108AC,'c2f75fbcf8e4e2414740bc1455ee41ab4966832d69f3a222f9cc6daea563432e'),
    (0x80A10A20,0x80A10ADC,'496c0ae0944bd93c825563968f3dbd3cd510b0a837fab09a0bae39d538005d27'),
    (0x80A10E54,0x80A10EF4,'f1e47dc84b53062a8ce24ff6af22f6e87a186706e17d470865b573892ae85d5b'),
    (0x80A1102C,0x80A11264,'a32b9642d869accdfeca58522825f5d58c816b319572e4cb8b1482b2f1076c54'),
)


def native_contract(image):
    owner=by_vrom(image)[0x8DEEC0].extract(image)
    functions=[]
    for start,end,digest in NATIVE_FUNCTIONS:
        if sha256(owner[start-0x80A10210:end-0x80A10210])!=digest:
            raise ValueError(f'Changed native insect ABI dependency at {start:08X}')
        functions.append(dict(address=start,bytes=end-start,sha256=digest))
    return dict(rom_sha256=sha256(image),owner_vrom=0x8DEEC0,owner_ram=0x80A10210,
        functions=functions,controller_bytes=0x8F8,slot_offset=0x174,slots=3,stride=0x280,
        offsets=dict(type=0x1CC,movement=0x1D0,animation=0x1DC,speed_step=0x1E8,
                     target_speed=0x1EC,patience=0x1F4,collision=0x1F8,item=0x21C,
                     flags=0x21E,life_time=0x220,alpha=0x258))


def rewrite(text):
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
    # Native pointers remain 32-bit. Host fixtures retain full pointer identity.
    sub('pointer_identity',r'\(u32\)(actorx|actor)\b',r'(uintptr_t)\1')
    sub('pointer_local',r'\bu32 (label|catch_label)\b',r'uintptr_t \1')
    if re.search(r'Common_Get|->block_table|->game_frame|eEC_CLIP|#include|->ut_[xz]',text):
        # Side-storage references are the only allowed ut_x/ut_z accesses.
        rest=re.sub(r'af_insect_extra\(insect\)->ut_[xz]','',text)
        if re.search(r'Common_Get|->block_table|->game_frame|eEC_CLIP|#include|->ut_[xz]',rest):
            raise ValueError('Unconverted GameCube platform access')
    return '#include "creature_insects.h"\n'+text,changes


def generate(source,output,native):
    parents,identity=source_records(source)
    raw,table=named_table(source,'aINS_program_type',41*4)
    rows=[r for r in parents if r['category']=='insect']
    if [r['source_index'] for r in rows]!=list(range(32,40)):
        raise ValueError('Changed complete added-insect category')
    kinds=[struct.unpack_from('>I',raw,r['source_index']*4)[0] for r in rows]
    if kinds!=[3,12,9,13,11,13,11,10]:
        raise ValueError('Changed donor insect program dispatch')
    programs=[]; generated={}
    for name,prefix,kind,digest in PROGRAMS:
        path=ROOT/f'local/ac-decomp/src/actor/ac_ins_{name}.c'
        data=path.read_bytes()
        if sha256(data)!=digest: raise ValueError('Changed pinned insect source: '+name)
        text=data.decode();converted,edits=rewrite(text)
        functions=[]
        definitions=re.findall(r'\b(?:static|extern)\s+\w+\s+('+prefix+r'_\w+)\([^;]*?\)\s*\{',text)
        for function in definitions:
            addresses=[at for at,names in source.functions.items() if any(n==function for n,_ in names)]
            if len(addresses)!=1: raise ValueError('Unbound complete donor function: '+function)
            functions.append(source.function(addresses[0])[1])
        if prefix+'_actor_init' not in definitions or prefix+'_actor_move' not in definitions:
            raise ValueError('Missing insect lifecycle')
        generated[name+'.c']=converted.encode()
        programs.append(dict(name=name,kind=kind,source_file=str(path.relative_to(ROOT)),
            source_sha256=digest,generated_sha256=sha256(generated[name+'.c']),
            functions=functions,platform_edits=edits,
            species=[r['source_index'] for r,k in zip(rows,kinds,strict=True) if k==kind]))
    output.mkdir(parents=True,exist_ok=False)
    for name,data in generated.items():write_new(output/name,data)
    return dict(format='AFV3-CREATURE-INSECT-PROGRAMS-1',source=identity,dispatch=table,native_abi=native,
        rows=[dict(r,program=k) for r,k in zip(rows,kinds,strict=True)],programs=programs,
        source_version='GAFE01_00',donor_bugfixes=False,
        source_rate=60,native_rate=30,source_substeps=2,
        native_actor_bytes=0x174,native_insect_bytes=0x280,native_controller_slots=3,
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES},
        installed=False,selectable=False,native_execution_tested=False)


def compile_programs(output,report):
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
    for source in ('creature_insects','creature_insect_state'):
        objects.append(source+'.o')
        commands.append(shlex.join(['/n64_toolchain/bin/mips64-elf-gcc',*flags,'-c',
            '/source/overlays/v3/'+source+'.c','-o',source+'.o']))
    commands.append(shlex.join(['/n64_toolchain/bin/mips64-elf-ld','-EB','-r',*objects,'-o','programs.o']))
    commands.append('/n64_toolchain/bin/mips64-elf-nm --undefined-only programs.o')
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
            '-v',f'{ROOT}:/source:ro','-v',f'{output.resolve()}:/out','-w','/out',
            '--entrypoint','/bin/sh',IMAGE,'-ec','\n'.join(commands)]
    result=subprocess.run(docker,text=True,capture_output=True,timeout=60)
    if result.returncode: raise RuntimeError(result.stderr)
    undefined=sorted(line.split()[-1] for line in result.stdout.splitlines() if line.strip())
    report['compiled']=dict(object='programs.o',sha256=sha256((output/'programs.o').read_bytes()),
        bytes=(output/'programs.o').stat().st_size,toolchain=IMAGE,flags=flags,donor_flags=donor_flags,
        unbound_engine_adapters=undefined,
        stack_usage=''.join(p.read_text() for p in sorted(output.glob('*.su'))))
    report['pending']=[
        'Native adapter bindings, including collision, sound/effects, and mosquito player response',
        'Controller initialization, destruction, source-rate update, and catch-range dispatch',
        'Digging, rock-strike, and tree-shake event producers',
        'Complete insect calendar/terrain spawning and ant ground-colony actor',
        'Guarded packet placement/startup and optional selection promotion',
        'Connected native gameplay/save verification; existing unresolved fixtures are not reset']
    write_new(output/'programs.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--base-lock',type=Path,required=True)
    args=parser.parse_args()
    from v3_furniture_install import inputs
    image,_=inputs(args.base_lock)
    native=native_contract(image)
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    report=compile_programs(args.output,generate(source,args.output,native))
    print(json.dumps(dict(programs=len(report['programs']),species=len(report['rows']),
        unbound_engine_adapters=report['compiled']['unbound_engine_adapters'],installed=False),indent=2))


if __name__=='__main__':main()
