#!/usr/bin/env python3
"""Append the shared English grid to the exact complete native editor image."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

from aflib import sha256, verified_rom
from check_keyboard_assembly import IMAGE
from gc_text import decoder_tables
import apology_overlay as previous
from keyboard_grid import extract, keycap

ROOT=Path(__file__).resolve().parents[1]
RAM=previous.RAM
LIMIT=0x8000
IMPORTS={name:RAM+previous.APPROVED['symbols'][name] for name in
         ('af_apology_editor_init','af_apology_editor_destruct')}
IMPORTS.update(af_hboard_font_line=0x80090E98,af_hboard_code_width=0x8009028C,
    af_grid_get_button=0x80078D78,af_grid_get_trigger=0x80078DF4,
    af_grid_get_x=0x80078E28,af_grid_get_y=0x80078E5C)
HOOKS={0x80888484:('af_grid_editor_init',IMPORTS['af_apology_editor_init']),
       0x808867B8:('af_grid_editor_prepare',0x808851D8),
       0x808868D8:('af_grid_editor_input',0x808857F8),
       0x808882D8:('af_grid_editor_draw',0x80888024)}


def sources():
    paths=sorted((ROOT/'overlays/keyboard_grid').iterdir())
    paths += [ROOT/'overlays/hboard/editor.h',ROOT/'runtime/hboard_editor.h',
              ROOT/'tools/keyboard_grid.py']
    return {str(p.relative_to(ROOT)):sha256(p.read_bytes()) for p in paths if p.is_file()}


def jump(target):
    return 0x0C000000|((target>>2)&0x3FFFFFF)


def patched_prefix(data,symbols):
    if sha256(data)!=previous.APPROVED['overlay_sha256']:
        raise ValueError('Grid requires the complete apology editor')
    result=bytearray(data)
    for at,(name,target) in HOOKS.items():
        offset=symbols.get(name)
        if type(offset) is not int or offset&3 or not len(data)<=offset<LIMIT:
            raise ValueError('Missing bounded grid hook')
        if struct.unpack_from('>I',data,at-RAM)[0]!=jump(target):
            raise ValueError('Changed previous editor hook')
        struct.pack_into('>I',result,at-RAM,jump(RAM+offset))
    return bytes(result)


def relocations(original,inventory,size):
    sections=struct.unpack_from('>5I',original)
    if sections[:4]!=(previous.APPROVED['bytes'],0,0,0):
        raise ValueError('Unexpected complete apology relocation sections')
    rows=list(struct.unpack_from('>'+str(sections[4])+'I',original,20))
    for at in HOOKS:
        if rows.count(0x44000000|(at-RAM))!=1:
            raise ValueError('Missing native grid-hook relocation')
    seen=set()
    for at,kind,target,name in inventory:
        if at in seen or at&3 or not previous.APPROVED['bytes']<=at<=size-4 or kind not in (2,4,5,6):
            raise ValueError('Invalid grid relocation')
        seen.add(at)
        if RAM<=target<RAM+size:rows.append(0x40000000|kind<<24|at)
        elif IMPORTS.get(name)!=target or kind!=4:
            raise ValueError('Unexpected grid external import')
    if len({r&0xFFFFFF for r in rows})!=len(rows):raise ValueError('Duplicate grid relocation')
    length=(24+len(rows)*4+15)&~15
    return struct.pack('>5I',size,0,0,0,len(rows))+struct.pack('>'+str(len(rows))+'I',*rows)+bytes(length-24-len(rows)*4)+struct.pack('>I',length)


def build(native,directory,out):
    prior=(directory/'overlay.bin').read_bytes();rel=(directory/'relocation.bin').read_bytes()
    previous.validate(native,prior,rel,json.loads((directory/'overlay.json').read_text()))
    reference=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    keys,layout=extract(reference,symbols,decoder_tables(ROOT/'local/ac-decomp/tools/msg_tool.py')['CHAR_MAP'])
    cap=keycap(reference,symbols)
    source_hashes=sources();out=out.resolve();out.mkdir(parents=True,exist_ok=True)
    for name,data in (('previous.bin',prior),('keys.bin',keys),('keycap.bin',cap)):
        (out/name).write_bytes(data)
    (out/'imports.ld').write_text(''.join(f'{name} = 0x{value:08X};\n' for name,value in IMPORTS.items()))
    common=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
            '-v',f'{ROOT}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result=subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
                              capture_output=True,text=True,timeout=60)
        if result.returncode:raise ValueError('Grid '+tool+' failed: '+result.stdout+result.stderr)
        return result.stdout
    flags=['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls','-fno-pic',
           '-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector','-fno-merge-constants',
           '-mno-explicit-relocs','-mno-split-addresses','-fstack-usage','-Wall','-Wextra','-Werror',
           '-D_LANGUAGE_C','-DF3DEX_GBI_2','-I/source/upstream/af/lib/ultralib/include']
    for name in ('core','editor','draw'):
        run('gcc',*flags,'/source/overlays/keyboard_grid/'+name+'.c','-o',name+'.o')
    run('as','-EB','-mabi=32','-march=vr4300','-I/out','-o','prefix.o','/source/overlays/keyboard_grid/overlay.s')
    run('ld','-EB','--emit-relocs','-T','/source/overlays/keyboard_grid/overlay.ld','-Map=overlay.map',
        '-o','overlay.elf','prefix.o','core.o','editor.o','draw.o')
    if run('nm','--undefined-only','overlay.elf').strip():raise ValueError('Unresolved grid import')
    defined={}
    for line in run('nm','--defined-only','overlay.elf').splitlines():
        fields=line.split()
        if len(fields)==3:defined[fields[2]]=int(fields[0],16)
    exports={name:value-RAM for name,value in defined.items() if name.startswith('af_grid_') and name not in IMPORTS}
    run('objcopy','-O','binary','-j','.text','overlay.elf','overlay.bin')
    data=bytearray((out/'overlay.bin').read_bytes())
    if defined['__grid_end']!=RAM+len(data) or len(data)>LIMIT:raise ValueError('Grid linked bounds disagree')
    data[:len(prior)]=patched_prefix(prior,exports)
    elf_text=run('readelf','-rW','overlay.elf');inventory=previous.previous.elf_inventory(elf_text)
    relocation=relocations(rel,inventory,len(data))
    report={'version':1,'ram':RAM,'bytes':len(data),'overlay_sha256':sha256(data),
        'prefix_bytes':len(prior),'previous_sha256':sha256(prior),'previous_relocation_sha256':sha256(rel),
        'suffix_sha256':sha256(data[len(prior):]),'relocation_bytes':len(relocation),
        'relocation_sha256':sha256(relocation),'sources':source_hashes,'imports':IMPORTS,'symbols':exports,
        'elf_relocations':inventory,'code_end':defined['__grid_code_end']-RAM,
        'bss_start':defined['__grid_bss_start']-RAM,'toolchain_image':IMAGE,'flags':flags,
        'layout':layout,'keycap_sha256':sha256(cap),'compiler':run('gcc','--version').splitlines()[0],
        'stack_usage':{name:(out/(name+'.su')).read_text() for name in ('core','editor','draw')},
        'status':'Compiled grid candidate; complete cartridge installation and native checks pending'}
    if source_hashes!=sources():raise ValueError('Grid sources changed during build')
    (out/'overlay.bin').write_bytes(data);(out/'relocation.bin').write_bytes(relocation)
    (out/'overlay.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'elf-relocations.txt').write_text(elf_text)
    (out/'overlay.asm').write_text(run('objdump','-d','overlay.elf'))
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--previous',type=Path,default=ROOT/'build/apology-input-overlay')
    parser.add_argument('--output',type=Path,default=ROOT/'build/keyboard-grid-overlay')
    args=parser.parse_args()
    report=build(verified_rom(args.rom.read_bytes()),args.previous,args.output)
    print(json.dumps({k:report[k] for k in ('bytes','suffix_sha256','relocation_bytes','symbols','stack_usage')},indent=2))


if __name__=='__main__':main()
