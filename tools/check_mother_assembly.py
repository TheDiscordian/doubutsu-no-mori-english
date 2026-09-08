#!/usr/bin/env python3
"""Independently assemble the in-place Mom creator and both publication gates."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
from check_keyboard_assembly import IMAGE
from mother_letters import ROOT,START,POST,END,patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('build/mother-assembly'))
    args = parser.parse_args()
    module = json.loads((ROOT/'build/runtime-module/module.json').read_text())
    loader = int(module['symbols']['af_npc_mail_load'],16)
    native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    code = by_vrom(native)[CODE_VROM].extract(native)
    expected = patch(code[START-CODE_RAM:END-CODE_RAM],loader)
    source = ROOT/'overlays/mail_generation';digest = sha256((source/'mother_entry.s').read_bytes())
    out = args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    common = ['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
              '-v',f'{source}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*arguments):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*arguments],
                                capture_output=True,text=True,timeout=60)
        if result.returncode: raise ValueError(result.stdout+result.stderr)
        return result.stdout
    run('as','-EB','-mabi=32','-march=vr4300','-o','entry.o','/source/mother_entry.s')
    run('ld','-EB','-Ttext',f'0x{START:08X}','-e','mother_entry',
        f'--defsym=af_npc_mail_load=0x{loader:08X}','-o','entry.elf','entry.o')
    run('objcopy','-O','binary','-j','.text','entry.elf','entry.bin')
    data = (out/'entry.bin').read_bytes()
    ranges = ((START,POST),(0x800B90DC,0x800B910C),(0x800B9148,0x800B9150))
    for start,end in ranges:
        if data[start-START:end-START] != expected[start-START:end-START]:
            raise ValueError(f'Mom entry assembler mismatch at {start:08X}')
    if sha256((source/'mother_entry.s').read_bytes()) != digest:
        raise ValueError('Mom entry source changed during assembly')
    report = {'assembly_sha256':digest,'patch_sha256':sha256(expected),'toolchain_image':IMAGE,
              'creator_bytes':POST-START,'mailbox_gate_bytes':48,'queue_gate_bytes':8,'loader_ram':f'{loader:08X}'}
    (out/'entry.asm').write_text(run('objdump','-d','entry.elf'))
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__': main()
