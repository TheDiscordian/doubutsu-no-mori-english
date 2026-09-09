#!/usr/bin/env python3
"""Independent score entry, status return, and cleanup/scheduler assembly."""

import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

from academy_score_letters import ROOT,entry_patch,scheduler_patch
from aflib import sha256
from check_keyboard_assembly import IMAGE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('build/academy-score-assembly'))
    args = parser.parse_args();out = args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    module = json.loads((ROOT/'build/runtime-module/module.json').read_text());loader = int(module['symbols']['af_npc_mail_load'],16)
    source = ROOT/'overlays/mail_generation';digest = sha256((source/'academy_score_entry.s').read_bytes())
    common = ['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
              '-v',f'{source}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*arguments):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*arguments],
                                capture_output=True,text=True,timeout=60)
        if result.returncode: raise ValueError(result.stdout+result.stderr)
        return result.stdout
    run('as','-EB','-mabi=32','-march=vr4300','-o','entry.o','/source/academy_score_entry.s')
    run('ld','-EB','-Ttext','0x80925E48','--section-start=.scheduler=0x8009CF28','-e','academy_score_entry',
        f'--defsym=af_npc_mail_load=0x{loader:08X}','-o','entry.elf','entry.o')
    run('objcopy','-O','binary','-j','.text','entry.elf','entry.bin')
    run('objcopy','-O','binary','-j','.scheduler','entry.elf','scheduler.bin')
    data,scheduler = (out/'entry.bin').read_bytes(),(out/'scheduler.bin').read_bytes()
    values = {0x80925E48:entry_patch(loader),0x809281C8:struct.pack('>3I',0x2C810004,0x50200072,0x00001825)}
    for at,value in values.items():
        if data[at-0x80925E48:at-0x80925E48+len(value)] != value:
            raise ValueError(f'Independent score assembly mismatch at {at:08X}')
    at,value = scheduler_patch()
    if scheduler[:len(value)] != value: raise ValueError('Independent score scheduler assembly mismatch')
    values[at] = value
    if sha256((source/'academy_score_entry.s').read_bytes()) != digest: raise ValueError('Score assembly changed during comparison')
    report = {'assembly_sha256':digest,'toolchain_image':IMAGE,
              'patches':[{'ram':f'{at:08X}','bytes':len(value),'sha256':sha256(value)} for at,value in values.items()]}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(out/'entry.asm').write_text(run('objdump','-d','entry.elf'))
    print(json.dumps(report,indent=2))


if __name__ == '__main__': main()
