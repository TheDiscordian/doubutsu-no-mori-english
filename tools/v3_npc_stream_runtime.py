"""Bind streamed NPC drawing to both existing native NPC/accessory paths.

Preparation compiles a relocatable object. The additive actor installation must
provide its record lookup and checked code allocation before applying the hooks.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

from aflib import by_vrom,sha256
from apply_translation import write_new
from toolchain import IMAGE
from v3_accessory_runtime import OWNERS
from v3_furniture_install import inputs
from v3_import_catalog import ROOT
from v3_npc_draw import relocation_offsets
from v3_villager_art import DRAW_STRIDE

SOURCES=('tools/v3_npc_stream_runtime.py','overlays/v3/npc_stream_draw.c',
    'overlays/v3/npc_stream_draw.h')


def native_records(source,art,name,model_bank,texture_bank):
    """Create draw/stream records for identities already reserved by a caller.

    This function allocates no identity or bank. Voice 255 is the existing
    expanded-voice marker; the actor installer must bind the returned full voice.
    """
    if (not 0xD000<=name<0xF000 or not 0<=model_bank<0x8000 or
            not 0<=texture_bank<0x8000 or model_bank==texture_bank):
        raise ValueError('Invalid native NPC identity or separate object banks')
    for path,digest in art['sources'].items():
        if sha256((ROOT/path).read_bytes())!=digest:raise ValueError('Changed streamed artwork source')
    index=art['draw_index'];table=source.raw('npc_draw_data_tbl')
    row=table[index*DRAW_STRIDE:(index+1)*DRAW_STRIDE]
    if len(row)!=DRAW_STRIDE or sha256(row)!=art['donor_draw_sha256']:
        raise ValueError('Changed donor streamed draw record')
    if (row[0x5F:0x62]!=bytes(3) or row[0x68:]!=bytes.fromhex('ffffffff') or
            len(art['eye_offsets']) not in (0,8) or len(art['mouth_offsets']) not in (0,6) or
            not art['eye_offsets'] and art['mouth_offsets'] or
            art['body_offset']+4096>art['texture_bytes'] or art['texture_bytes']>0x1620):
        raise ValueError('Unbound streamed NPC flags, accessory, or complete texture bank')
    offsets=art['eye_offsets']+art['mouth_offsets']
    if any(x<32 or x&7 or x+256>art['texture_bytes'] for x in offsets):
        raise ValueError('NPC expression leaves the complete texture bank')
    draw=bytearray(100)
    struct.pack_into('>HHIII',draw,0,model_bank,texture_bank,art['skeleton'],
        0x06000000+art['body_offset'],0x06000000)
    for first,values in ((16,art['eye_offsets']),(48,art['mouth_offsets'])):
        for i,offset in enumerate(values):struct.pack_into('>I',draw,first+i*4,0x06000000+offset)
    # Temporary native atlas eye/mouth loads may share TMEM zero: the streamed
    # lists load every actual material afterwards. Clothing is not referenced.
    draw[0x54:0x5F]=row[0x54:0x5F];draw[0x5F]=255;draw[0x60:]=row[0x64:0x68]
    stream=struct.pack('>18H',name,art['texture_bytes'],art['body_offset'],len(art['mouth_offsets']),
        *(art['eye_offsets'] or [0]*8),*(art['mouth_offsets'] or [0]*6))
    voice=struct.unpack_from('>H',row,0x62)[0]
    return bytes(draw),stream,voice


def patch_owners(base,target=None):
    """Check both complete renderers, preserving all six args and the delay slot."""
    if target is not None and (target&3 or not 0x80400000<=target<0x80800000):
        raise ValueError('Streamed NPC helper needs a checked resident code address')
    files=by_vrom(base);changes={};records=[]
    for vrom,reloc,ram,start,end,call,_,digest in OWNERS:
        owner=files[vrom].extract(base);data=bytearray(owner)
        at=call-ram;function=bytearray(data[start-ram:end-ram])
        if (data[at:at+8]!=bytes.fromhex('0c11cc40afa80014') or
                at in relocation_offsets(files[reloc].extract(base),len(data))):
            raise ValueError('NPC skeleton call no longer chains through the installed accessory wrapper')
        struct.pack_into('>I',function,call-start,0x0C014C36)
        if sha256(function)!=digest:raise ValueError('Changed complete native NPC drawing layout')
        if target is not None:
            struct.pack_into('>I',data,at,0x0C000000|(target>>2&0x3FFFFFF))
            changes[vrom]=bytes(data)
        records.append(dict(vrom=vrom,ram=ram,call=call,native_function_sha256=digest,
            chained_helper=0x80473100,actor_body=0x74C,actor_palette=0x750,
            actor_eyes=0x754,actor_mouths=0x774,eye_pattern=0x710,mouth_pattern=0x71C,
            delay_slot='afa80014',relocations_unchanged=True))
    return changes,records


def compile_object(output):
    compiler='/n64_toolchain/bin/mips64-elf-'
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{output.resolve()}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        return subprocess.run(docker+[compiler+tool,IMAGE,*args],check=True,
            capture_output=True,text=True,timeout=60).stdout
    flags=['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls','-fno-pic',
        '-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector','-ffunction-sections',
        '-fdata-sections','-fstack-usage','-Wall','-Wextra','-Werror']
    run('gcc',*flags,'/source/overlays/v3/npc_stream_draw.c','-o','draw.o')
    imports=sorted(line.split()[-1] for line in run('nm','--undefined-only','draw.o').splitlines())
    if imports!=['af_v3_npc_stream_record']:raise ValueError('Unexpected streamed drawing dependency')
    return dict(sha256=sha256((output/'draw.o').read_bytes()),compiler_image=IMAGE,
        flags=flags,imports=imports,stack_usage=(output/'draw.su').read_text(),linked=False)


def prepare(lock,output):
    base,report=inputs(lock);_,owners=patch_owners(base)
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):raise ValueError('Use a fresh ignored output')
    output.mkdir(parents=True)
    r=dict(format='AFV3-NPC-STREAM-DRAW-1',base_sha256=sha256(base),base_abi=report['runtime_abi'],
        owners=owners,kernel=compile_object(output),runtime_installed=False,
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    write_new(output/'draw.json',(json.dumps(r,indent=2)+'\n').encode());return r


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--lock',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();r=prepare(args.lock,args.output)
    print(json.dumps(dict(kernel=r['kernel'],runtime_installed=r['runtime_installed']),indent=2))
