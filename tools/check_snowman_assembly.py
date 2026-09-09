#!/usr/bin/env python3
"""Independently assemble the Snowman selection wrapper and receipt gate."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import sha256
from check_keyboard_assembly import IMAGE
from snowman_actor import ROOT,RAM,START,patches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--actor',type=Path,default=Path('build/snowman-actor'))
    parser.add_argument('--output',type=Path,default=Path('build/snowman-assembly'))
    args = parser.parse_args()
    module = json.loads((ROOT/'build/runtime-module/module.json').read_text())
    actor = json.loads((args.actor/'overlay.json').read_text())
    source = ROOT/'overlays/mail_generation';digest = sha256((source/'snowman_entry.s').read_bytes())
    out = args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    common = ['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
              '-v',f'{source}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*arguments):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*arguments],
                                capture_output=True,text=True,timeout=60)
        if result.returncode: raise ValueError(result.stdout+result.stderr)
        return result.stdout
    run('as','-EB','-mabi=32','-march=vr4300','-o','entry.o','/source/snowman_entry.s')
    run('ld','-EB','-Ttext',f'0x{START:08X}','-e','snowman_entry',
        '--defsym=af_mail_generation_capital=0x'+module['symbols']['af_mail_generation_capital'],
        f'--defsym=af_snowman_create=0x{RAM+actor["symbols"]["af_snowman_create"]:08X}',
        '-o','entry.elf','entry.o')
    run('objcopy','-O','binary','-j','.text','entry.elf','entry.bin')
    data = (out/'entry.bin').read_bytes();expected = patches(module,actor['symbols'])
    for at,value in expected.items():
        if data[at-START:at-START+len(value)]!=value: raise ValueError(f'Snowman assembly differs at {at:08X}')
    if sha256((source/'snowman_entry.s').read_bytes())!=digest: raise ValueError('Snowman assembly source changed')
    report = {'assembly_sha256':digest,'toolchain_image':IMAGE,
              'patches':[{'ram':f'{at:08X}','bytes':len(v),'sha256':sha256(v)} for at,v in expected.items()]}
    (out/'entry.asm').write_text(run('objdump','-d','entry.elf'))
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__': main()
