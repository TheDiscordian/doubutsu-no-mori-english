#!/usr/bin/env python3
"""Build the English grader in the native on-demand mail-check overlay space."""

import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from check_keyboard_assembly import IMAGE
from mail_grading import ROOT, RAM, SIZE, RELOC_SIZE, load_prefixes, source_hashes, relocate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--rel', type=Path, default=Path('build/gamecube/files/foresta.rel.szs.decoded'))
    parser.add_argument('--symbols', type=Path, default=Path('local/ac-decomp/config/GAFE01_00/foresta/symbols.txt'))
    parser.add_argument('--output', type=Path, default=Path('build/mail-grading'))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    prefixes, reference = load_prefixes(args.rel.read_bytes(), args.symbols.read_text())
    sources = source_hashes()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out/'prefixes.bin').write_bytes(prefixes)
    fado = ROOT/'upstream/af/tools/fado'
    fado_sources = sorted((fado/'src').glob('*.c'))+[fado/'lib/fairy/fairy.c',fado/'lib/fairy/fairy_print.c',
                                                    fado/'lib/vc_vector/vc_vector.c']
    fado_inputs = sorted(set(fado_sources) | set((fado/'include').rglob('*.h'))
                        | set((fado/'lib').rglob('*.h'))
                        | {fado/'src/version.inc',fado/'lib/fairy/fairy_data.inc'})
    # Build the provided relocation generator locally; no system installation.
    subprocess.run(['gcc','-std=c11','-O2','-I'+str(fado/'include'),'-I'+str(fado/'lib'),
                    *(str(p) for p in fado_sources),'-o',str(out/'fado')], check=True, timeout=60)
    common = ['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
              '-v',f'{ROOT}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
                                capture_output=True,text=True,timeout=60)
        if result.returncode: raise RuntimeError(result.stdout+result.stderr)
        return result.stdout
    flags = ['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls','-fno-pic',
             '-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector','-fno-merge-constants',
             '-mno-explicit-relocs','-mno-split-addresses','-fstack-usage','-Wall','-Wextra','-Werror',
             '-I/source/runtime']
    run('gcc',*flags,'/source/overlays/mail_check/grade.c','-o','grade.o')
    for name in ('entry','prefixes'):
        run('as','-EB','-mabi=32','-march=vr4300','-I/out','-o',name+'.o','/source/overlays/mail_check/'+name+'.s')
    result = subprocess.run([str(out/'fado'),'entry.o','grade.o','prefixes.o','-n','af_mail_check','-o','relocation.s'],
                            cwd=out,capture_output=True,text=True,timeout=60)
    (out/'fado.log').write_text(result.stdout+result.stderr)
    if result.returncode: raise RuntimeError(result.stdout+result.stderr)
    run('as','-EB','-mabi=32','-march=vr4300','-o','relocation.o','relocation.s')
    run('ld','-EB','-T','/source/overlays/mail_check/overlay.ld','-Map=overlay.map','-o','overlay.elf',
        'entry.o','grade.o','prefixes.o','relocation.o')
    if run('nm','--undefined-only','overlay.elf').strip(): raise ValueError('Undefined mail-check symbols')
    run('objcopy','-O','binary','-j','.text','-j','.data','-j','.rodata','overlay.elf','overlay.bin')
    run('objcopy','-O','binary','--set-section-flags','.ovl=alloc,load,readonly,data,contents',
        '-j','.ovl','overlay.elf','relocation.bin')
    data, reloc = (out/'overlay.bin').read_bytes(),(out/'relocation.bin').read_bytes()
    used, reloc_used = len(data),len(reloc)
    if used > SIZE or reloc_used > RELOC_SIZE: raise ValueError('English checker exceeds native allocations')
    data = data.ljust(SIZE,b'\0')
    # Native DMA records keep their exact original lengths. The relocation
    # loader uses explicit section sizes; only its trailing size word changes.
    if len(reloc) < 24 or struct.unpack_from('>I',reloc,len(reloc)-4)[0] != len(reloc):
        raise ValueError('Unexpected Fado relocation trailer')
    reloc = reloc[:-4].ljust(RELOC_SIZE-4,b'\0')+struct.pack('>I',RELOC_SIZE)
    for base in (0x801A0000,0x802F8010):
        relocate(data,reloc,base)
    (out/'overlay.bin').write_bytes(data)
    (out/'relocation.bin').write_bytes(reloc)
    (out/'overlay.asm').write_text(run('objdump','-d','overlay.elf'))
    symbols = {}
    for line in run('nm','-S','--defined-only','overlay.elf').splitlines():
        parts = line.split()
        if len(parts) == 4: symbols[parts[3]] = {'address':parts[0].upper(),'bytes':int(parts[1],16),'type':parts[2]}
        elif len(parts) == 3: symbols[parts[2]] = {'address':parts[0].upper(),'type':parts[1]}
    if source_hashes() != sources: raise ValueError('Mail-check sources changed during compilation')
    code = by_vrom(rom)[CODE_VROM].extract(rom)
    report = {'source_sha256':sha256(rom),'sources':sources,'reference':reference,
              'overlay_sha256':sha256(data),'relocation_sha256':sha256(reloc),
              'linked_bytes':used,'allocation_bytes':SIZE,'relocation_used_bytes':reloc_used,
              'relocation_bytes':RELOC_SIZE,'symbols':symbols,'compiler_flags':flags,'toolchain_image':IMAGE,
              'stack_usage':(out/'grade.su').read_text(),
              'native_grade_sha256':sha256(code[0x800A86C4-CODE_RAM:0x800A86E8-CODE_RAM]),
              'fado_sources':{p.relative_to(fado).as_posix():sha256(p.read_bytes()) for p in fado_inputs},
              'status':'English scoring with bounded prefix tables; native execution and full mail integration require validation'}
    (out/'overlay.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__': main()
