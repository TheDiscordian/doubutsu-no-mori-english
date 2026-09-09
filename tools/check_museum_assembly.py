#!/usr/bin/env python3
"""Independently assemble the museum creator and both native receipt gates."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import CODE_VROM,by_vrom,sha256,verified_rom
from check_keyboard_assembly import IMAGE
from museum_letters import ROOT,START,patches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('build/museum-assembly'))
    args = parser.parse_args()
    module = json.loads((ROOT/'build/runtime-module/module.json').read_text())
    loader = int(module['symbols']['af_npc_mail_load'],16)
    native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    expected = patches(by_vrom(native)[CODE_VROM].extract(native),loader)
    source = ROOT/'overlays/mail_generation';digest = sha256((source/'museum_entry.s').read_bytes())
    out = args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    common = ['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
              '-v',f'{source}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*arguments):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*arguments],
                                capture_output=True,text=True,timeout=60)
        if result.returncode: raise ValueError(result.stdout+result.stderr)
        return result.stdout
    run('as','-EB','-mabi=32','-march=vr4300','-o','entry.o','/source/museum_entry.s')
    run('ld','-EB','-Ttext',f'0x{START:08X}','-e','museum_entry',
        f'--defsym=af_npc_mail_load=0x{loader:08X}','-o','entry.elf','entry.o')
    run('objcopy','-O','binary','-j','.text','entry.elf','entry.bin')
    data = (out/'entry.bin').read_bytes()
    for at,value in expected.items():
        if data[at-START:at-START+len(value)]!=value:
            raise ValueError(f'Museum assembler mismatch at {at:08X}')
    if sha256((source/'museum_entry.s').read_bytes())!=digest:
        raise ValueError('Museum assembly source changed during comparison')
    report = {'assembly_sha256':digest,'toolchain_image':IMAGE,'loader_ram':f'{loader:08X}',
              'patches':[{'ram':f'{at:08X}','bytes':len(value),'sha256':sha256(value)} for at,value in expected.items()]}
    (out/'entry.asm').write_text(run('objdump','-d','entry.elf'))
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__': main()
