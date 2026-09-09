#!/usr/bin/env python3
"""Independently assemble and compare the secret-letter native wrapper."""
import json
import os
import subprocess
from aflib import sha256
from check_keyboard_assembly import IMAGE
from secret_actor import ROOT,RAM,START,END,wrapper


def main():
    module = json.loads((ROOT/'build/shop-notice-runtime/module.json').read_text())
    actor = json.loads((ROOT/'build/secret-actor/overlay.json').read_text())
    out = ROOT/'build/secret-assembly';out.mkdir(parents=True,exist_ok=True)
    source = ROOT/'overlays/mail_generation';digest = sha256((source/'secret_entry.s').read_bytes())
    common = ['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
              '-v',f'{source}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],capture_output=True,text=True,timeout=60)
        if result.returncode: raise ValueError(result.stdout+result.stderr)
        return result.stdout
    run('as','-EB','-mabi=32','-march=vr4300','-o','entry.o','/source/secret_entry.s')
    run('ld','-EB','-Ttext',f'0x{START:08X}','-e','secret_entry',
        '--defsym=af_mail_generation_capital=0x'+module['symbols']['af_mail_generation_capital'],
        f'--defsym=af_secret_create=0x{RAM+actor["symbols"]["af_secret_create"]:08X}',
        '-o','entry.elf','entry.o')
    run('objcopy','-O','binary','-j','.text','entry.elf','entry.bin')
    actual = (out/'entry.bin').read_bytes()
    if actual[:END-START]!=wrapper(module,actor['symbols']): raise ValueError('Secret wrapper assembly differs')
    if sha256((source/'secret_entry.s').read_bytes())!=digest: raise ValueError('Secret wrapper source changed')
    report = {'source_sha256':digest,'wrapper_sha256':sha256(actual[:END-START]),'bytes':END-START,'toolchain_image':IMAGE}
    (out/'entry.asm').write_text(run('objdump','-d','entry.elf'))
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__': main()
