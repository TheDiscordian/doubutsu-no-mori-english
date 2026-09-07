#!/usr/bin/env python3
"""Independently assemble the NPC failure gate and its test-only creator."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
from check_keyboard_assembly import IMAGE
from npc_mail_delivery import START,END,CREATOR_CALL,FAILURE_BRANCH,ARGUMENT_MOVE,patch,creator_fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--output',type=Path,default=Path('build/npc-mail-delivery-assembly'))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    code = by_vrom(rom)[CODE_VROM].extract(rom)
    expected = patch(code[START-CODE_RAM:END-CODE_RAM],0x802F8010)
    source = Path(__file__).resolve().parents[1]/'overlays/npc_mail_delivery'
    digest = sha256((source/'probe.s').read_bytes())
    out = args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    common = ['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
              '-v',f'{source}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*arguments):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*arguments],
                                capture_output=True,text=True,timeout=60)
        if result.returncode: raise RuntimeError(result.stdout+result.stderr)
        return result.stdout
    run('as','-EB','-mabi=32','-march=vr4300','-o','probe.o','/source/probe.s')
    run('ld','-EB','-Ttext',f'0x{START:08X}','-e',f'0x{START:08X}','-o','probe.elf','probe.o')
    for section in ('text','fixture'):
        run('objcopy','-O','binary','-j','.'+section,'probe.elf',section+'.bin')
    assembled = (out/'text.bin').read_bytes()
    for address in (CREATOR_CALL,FAILURE_BRANCH,ARGUMENT_MOVE):
        at = address-START
        if assembled[at:at+4] != expected[at:at+4]:
            raise ValueError(f'NPC failure-gate assembler mismatch at {address:08X}')
    fixture = (out/'fixture.bin').read_bytes()
    if fixture != creator_fixture(0x802F8010):
        raise ValueError('NPC creator fixture differs from independently assembled o32 code')
    if sha256((source/'probe.s').read_bytes()) != digest:
        raise ValueError('NPC gate assembly changed during compilation')
    (out/'probe.asm').write_text(run('objdump','-d','probe.elf'))
    report = {'gate_instructions':3,'fixture_bytes':len(fixture),'fixture_sha256':sha256(fixture),
              'assembly_sha256':digest,'toolchain_image':IMAGE,'production_hook_installed':False}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__': main()
