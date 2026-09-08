#!/usr/bin/env python3
"""Build complete source capture and generation in a relocatable native overlay."""

import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess

from aflib import sha256
from check_keyboard_assembly import IMAGE
from npc_mail_capture import RAM,source_hashes,creator_imports,relocate,verified_resources
from runtime_layout import MODULE_RAM,LINKED_LIMIT


def build(module,words,aliases,out,*,mother_letters=False,departed_letters=False,villager_events=False):
    root = Path(__file__).resolve().parents[1]
    verified_resources(words,aliases)
    variants = dict(mother_letters=mother_letters,departed_letters=departed_letters,villager_events=villager_events)
    sources = source_hashes(**variants);out.mkdir(parents=True,exist_ok=True)
    (out/'words.bin').write_bytes(words);(out/'aliases.bin').write_bytes(aliases)
    fado = root/'upstream/af/tools/fado'
    fado_sources = sorted((fado/'src').glob('*.c'))+[fado/'lib/fairy/fairy.c',fado/'lib/fairy/fairy_print.c',fado/'lib/vc_vector/vc_vector.c']
    fado_inputs = sorted(set(fado_sources)|set((fado/'include').rglob('*.h'))|set((fado/'lib').rglob('*.h'))
                         |{fado/'src/version.inc',fado/'lib/fairy/fairy_data.inc'})
    fado_hashes = {p.relative_to(fado).as_posix():sha256(p.read_bytes()) for p in fado_inputs}
    subprocess.run(['gcc','-std=c11','-O2','-I'+str(fado/'include'),'-I'+str(fado/'lib'),
                    *(str(p) for p in fado_sources),'-o',str(out/'fado')],check=True,capture_output=True,timeout=60)
    common = ['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
              '-v',f'{root}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
                                capture_output=True,text=True,timeout=60)
        if result.returncode: raise ValueError(f'NPC capture {tool} failed: '+result.stdout+result.stderr)
        return result.stdout
    imports = {name:int(module['symbols'][name],16) for name in creator_imports(villager_events=villager_events)}
    if any(value&3 or not MODULE_RAM+0x300 <= value < MODULE_RAM+min(module['linked_bytes'],LINKED_LIMIT)
           for value in imports.values()): raise ValueError('NPC capture imports are outside resident code')
    flags = ['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls','-fno-pic',
             '-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector','-fno-merge-constants',
             '-mno-explicit-relocs','-mno-split-addresses','-fstack-usage','-Wall','-Wextra','-Werror']
    names = ('digest','npc_capture','generate','npc_creator')+(('mother_creator',) if mother_letters else ())
    if departed_letters: names += ('departed_creator',)
    if villager_events: names += ('villager_event_creator',)
    for name in names:
        run('gcc',*flags,'/source/overlays/mail_generation/'+name+'.c','-o',name+'.o')
    run('as','-EB','-mabi=32','-march=vr4300','-I/out','-o','sources.o','/source/overlays/mail_generation/sources.s')
    objects = [name+'.o' for name in names]+['sources.o']
    result = subprocess.run([str(out/'fado'),*objects,'-n','af_npc_capture','-o','relocation.s'],
                            cwd=out,capture_output=True,text=True,timeout=60)
    (out/'fado.log').write_text(result.stdout+result.stderr)
    if result.returncode: raise ValueError(result.stdout+result.stderr)
    run('as','-EB','-mabi=32','-march=vr4300','-o','relocation.o','relocation.s')
    linker = 'system_capture.ld' if mother_letters else 'capture.ld'
    if departed_letters: linker = 'departed_capture.ld'
    if villager_events: linker = 'villager_event_capture.ld'
    run('ld','-EB','--emit-relocs','-T','/source/overlays/mail_generation/'+linker,'-Map=overlay.map',
        *(f'--defsym={name}=0x{value:08X}' for name,value in imports.items()),
        '-o','overlay.elf',*objects,'relocation.o')
    if run('nm','--undefined-only','overlay.elf').strip(): raise ValueError('Undefined NPC capture symbol')
    run('objcopy','-O','binary','-j','.text','-j','.data','-j','.rodata','overlay.elf','overlay.bin')
    run('objcopy','-O','binary','--set-section-flags','.ovl=alloc,load,readonly,data,contents',
        '-j','.ovl','overlay.elf','relocation.bin')
    data,reloc = (out/'overlay.bin').read_bytes(),(out/'relocation.bin').read_bytes()
    # Independently compare Fado's inventory with the linked ELF's internal
    # relocations. Missing complete HI/LO pairs must not escape jump-only checks.
    elf_relocs = run('readelf','-rW','overlay.elf')
    expected_relocs = []
    for line in elf_relocs.splitlines():
        match = re.fullmatch(r'\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_MIPS_(26|HI16|LO16)\s+([0-9a-fA-F]+)\s+(\S+)\s*',line)
        if not match: continue
        at,kind,target,name = int(match[1],16),match[2],int(match[3],16),match[4]
        if RAM <= target < RAM+len(data):
            expected_relocs.append(0x40000000|({'26':4,'HI16':5,'LO16':6}[kind]<<24)|(at-RAM))
        elif name not in imports or target != imports[name] or kind != '26':
            raise ValueError('Unapproved ELF NPC capture import')
    count = struct.unpack_from('>I',reloc,16)[0]
    if tuple(expected_relocs) != struct.unpack_from('>'+str(count)+'I',reloc,20):
        raise ValueError('Native NPC capture relocation inventory differs from linked ELF')
    for base in (0x801A0000,0x802F8010,0x80400000-len(data)):
        relocate(data,reloc,base,imports.values())
    symbols = {}
    for line in run('nm','--defined-only','overlay.elf').splitlines():
        parts = line.split()
        if len(parts) == 3: symbols[parts[2]] = int(parts[0],16)
    if symbols['__capture_start'] != RAM or symbols['__capture_end'] != RAM+len(data):
        raise ValueError('NPC capture linked image bounds disagree')
    for symbol,resource in (('af_npc_word_data',words),('af_npc_alias_data',aliases)):
        at = symbols[symbol]-RAM
        if data[at:at+len(resource)] != resource: raise ValueError('Linked NPC capture resource differs')
    if source_hashes(**variants) != sources or fado_hashes != {p.relative_to(fado).as_posix():sha256(p.read_bytes()) for p in fado_inputs}:
        raise ValueError('NPC capture source changed during compilation')
    report = {'version':1,'ram':RAM,'bytes':len(data),'relocation_bytes':len(reloc),
              'overlay_sha256':sha256(data),'relocation_sha256':sha256(reloc),
              'sources':sources,'module_sha256':module['module_sha256'],'imports':imports,
              'word_sha256':sha256(words),'alias_sha256':sha256(aliases),
              'symbols':{name:value-RAM for name,value in symbols.items() if name.startswith('af_') and RAM <= value < RAM+len(data)},
              'compiler':run('gcc','--version').splitlines()[0],'flags':flags,'toolchain_image':IMAGE,
              'stack_usage':{name:(out/(name+'.su')).read_text() for name in names},
              'fado_sources':fado_hashes,'status':'Complete capture/generation code; gameplay publication not installed'}
    if mother_letters: report['mother_letters'] = True
    if departed_letters: report['departed_letters'] = True
    if villager_events: report['villager_events'] = True
    (out/'overlay.asm').write_text(run('objdump','-d','overlay.elf'))
    (out/'elf-relocations.txt').write_text(elf_relocs)
    (out/'overlay.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--module',type=Path,default=Path('build/runtime-module/module.json'))
    parser.add_argument('--words',type=Path,default=Path('build/npc-mail-words/words.bin'))
    parser.add_argument('--aliases',type=Path,default=Path('build/npc-mail-names/aliases.bin'))
    parser.add_argument('--output',type=Path,default=Path('build/npc-mail-capture'))
    parser.add_argument('--mother-letters',action='store_true',help='Add complete Mom-letter dispatch without changing the resident loader')
    parser.add_argument('--departed-letters',action='store_true',help='Add complete departed-villager letters; requires --mother-letters')
    parser.add_argument('--villager-events',action='store_true',help='Add complete villager-event letters; requires --departed-letters')
    args = parser.parse_args()
    if args.departed_letters and not args.mother_letters: parser.error('--departed-letters requires --mother-letters')
    if args.villager_events and not args.departed_letters: parser.error('--villager-events requires --departed-letters')
    print(json.dumps(build(json.loads(args.module.read_text()),args.words.read_bytes(),args.aliases.read_bytes(),args.output.resolve(),
                           mother_letters=args.mother_letters,departed_letters=args.departed_letters,
                           villager_events=args.villager_events),indent=2))


if __name__ == '__main__': main()
