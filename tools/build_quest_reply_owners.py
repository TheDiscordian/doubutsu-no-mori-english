#!/usr/bin/env python3
"""Build quest reply creation and failure-gated copying in existing native slots."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import CODE_VROM,by_vrom,sha256,verified_rom
from check_keyboard_assembly import IMAGE
from quest_reply_letters import ROOT,START,sources,verify_code,validate


def build(native,module,out):
    verify_code(by_vrom(verified_rom(native))[CODE_VROM].extract(native))
    source_hashes = sources();out.mkdir(parents=True,exist_ok=True)
    loader = int(module['symbols']['af_npc_mail_load'],16)
    common = ['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
              '-v',f'{ROOT}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
                                capture_output=True,text=True,timeout=60)
        if result.returncode: raise ValueError('Quest reply '+tool+' failed: '+result.stdout+result.stderr)
        return result.stdout
    run('as','-EB','-mabi=32','-march=vr4300','-o','owners.o','/source/overlays/mail_generation/quest_reply_entry.s')
    run('ld','-EB','-Ttext',f'0x{START:08X}','-e','quest_reply_entry',
        f'--defsym=af_npc_mail_load=0x{loader:08X}','-o','owners.elf','owners.o')
    if run('nm','--undefined-only','owners.elf').strip(): raise ValueError('Unresolved quest reply owner helper')
    run('objcopy','-O','binary','-j','.text','owners.elf','owners.bin')
    data = (out/'owners.bin').read_bytes();symbols = {}
    for line in run('nm','--defined-only','owners.elf').splitlines():
        fields = line.split()
        if len(fields)==3 and fields[2] in ('quest_reply_entry','quest_reply_end','quest_reply_gate','quest_reply_gate_end'):
            symbols[fields[2]] = int(fields[0],16)
    report = {'version':1,'sha256':sha256(data),'module_sha256':module['module_sha256'],
              'sources':source_hashes,'loader_ram':loader,'symbols':symbols,'toolchain_image':IMAGE}
    validate(data,report,module)
    (out/'owners.asm').write_text(run('objdump','-d','owners.elf'))
    (out/'owners.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--module',type=Path,default=ROOT/'build/shop-notice-runtime/module.json')
    parser.add_argument('--output',type=Path,default=ROOT/'build/quest-reply-owners')
    args = parser.parse_args()
    print(json.dumps(build(args.rom.read_bytes(),json.loads(args.module.read_text()),args.output.resolve()),indent=2))


if __name__=='__main__': main()
