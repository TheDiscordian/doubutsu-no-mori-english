"""Exact native treasure transaction bridges and guarded patch construction."""

import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from check_keyboard_assembly import IMAGE

ROOT=Path(__file__).resolve().parents[1]
START, END=0x800A5E58, 0x800A5F08
SYMBOLS={'af_notice_owner_bridge':START, 'af_notice_place_enter':START+136,
         'af_notice_deposit_bridge':START+152}
RANGES=((START, END, '6311fb617183d51ba98866c308e525dc54cbbc8d41e6e168505b5ab7c9d9ab57'),
        (0x800A5F08,0x800A62EC,'e548281b85424af417431715461bd63d5806f4e15151fb90c0b263039917e53f'),
        (0x8008EA5C,0x8008ECA0,'3009f5d79b645a51c8c86bac40ac88a41e8e3181a5885b72194db969fea6f766'),
        (0x800A3E34,0x800A3F70,'c98de5761cb2d728ad36c720331480b947db4d6d465ba68b43a598ed1c846373'),
        (0x80072610,0x800727D8,'f4d337b99523a97c1d805a83bdfb51a0dd33f2792fa08d2ae3d2fdfed152c9b8'),
        (0x800A5DF4,START,'30b9e8a9e87197805686063dcce6358f76261b9ea876cd412b7faf7a21762af6'))


def call(target): return 0x0C000000|((target>>2)&0x3FFFFFF)
def jump(target): return 0x08000000|((target>>2)&0x3FFFFFF)


def source_hashes():
    paths=('overlays/notice/treasure_owner.s','tools/notice_treasure_owner.py')
    return {name:sha256((ROOT/name).read_bytes()) for name in paths}


def expected(loader):
    # Independent words bind the complete fixed bridge, both phase returns,
    # all stack offsets, undo writes, and the two placement forwarding thunks.
    words=[0x27BDFF20,0xAFBF00DC,0x3C084146,0x35084E52,0xAFA800C8,
           0x27A800E0,0xAFA800CC,0x001F4202,0x31080003,0xAFA000D0,
           0xA3A800D0,0x240800F4,0xA3A800D3,0xAFA00010,0xAFA00014,
           0x27A40020,0x02C02825,0x27A600C8,0x00003825,call(loader),0,
           0x8FBF00DC,0x33E80100,0x15000008,0,0x14400006,0x8FA801B0,
           0x8FA901B4,0x97AA01B8,0xA50A0000,0x97AA01BA,0xA52A0000,
           0x03E00008,0x27BD00E0,
           0xAFA40098,0xAFA700A4,jump(0x8008EA94),0,
           0x8FB900A4,0x8FB800A8,0x03200008,0xAFB80018,0,0]
    return struct.pack('>44I',*words)


def verify_code(code):
    for lo,hi,digest in RANGES:
        if sha256(code[lo-CODE_RAM:hi-CODE_RAM])!=digest:
            raise ValueError('Changed native treasure owner, placement, or deposit source')


def validate(data,report,module):
    loader=int(module['symbols']['af_npc_mail_load'],16)
    if (loader!=0x80197BB4 or module['module_sha256']!='493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6'
            or report.get('version')!=1 or report.get('module_sha256')!=module['module_sha256']
            or report.get('loader_ram')!=loader or report.get('symbols')!=SYMBOLS
            or report.get('sources')!=source_hashes() or report.get('sha256')!=sha256(data)
            or data!=expected(loader)):
        raise ValueError('Changed native treasure transaction bridges')


def patch(code,data,report,module):
    verify_code(code); validate(data,report,module)
    changed=bytearray(code)
    changed[START-CODE_RAM:END-CODE_RAM]=data
    edits={0x800A6170:call(START), 0x800A6214:0, 0x800A62A0:call(START),
           0x8008EA8C:jump(SYMBOLS['af_notice_place_enter']),
           0x8008EC44:call(SYMBOLS['af_notice_deposit_bridge'])}
    edits.update({at:0 for at in range(0x800A62A8,0x800A62C0,4)})
    for at,word in edits.items(): struct.pack_into('>I',changed,at-CODE_RAM,word)
    return bytes(changed)


def build(native,module,out):
    verify_code(by_vrom(verified_rom(native))[CODE_VROM].extract(native))
    sources=source_hashes(); out.mkdir(parents=True,exist_ok=True)
    loader=int(module['symbols']['af_npc_mail_load'],16)
    common=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
            '-v',f'{ROOT}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result=subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
                              capture_output=True,text=True,timeout=60)
        if result.returncode: raise ValueError(result.stdout+result.stderr)
        return result.stdout
    run('as','-EB','-mabi=32','-march=vr4300','-o','owners.o','/source/overlays/notice/treasure_owner.s')
    run('ld','-EB','-Ttext',f'0x{START:X}','-e','af_notice_owner_bridge',
        f'--defsym=af_npc_mail_load=0x{loader:X}','-o','owners.elf','owners.o')
    if run('nm','--undefined-only','owners.elf').strip(): raise ValueError('Unresolved treasure owner import')
    run('objcopy','-O','binary','-j','.text','owners.elf','owners.bin')
    data=(out/'owners.bin').read_bytes(); symbols={}
    for line in run('nm','--defined-only','owners.elf').splitlines():
        parts=line.split()
        if len(parts)==3 and parts[2] in SYMBOLS: symbols[parts[2]]=int(parts[0],16)
    report={'version':1,'sha256':sha256(data),'sources':sources,'symbols':symbols,
            'loader_ram':loader,'module_sha256':module['module_sha256'],'toolchain_image':IMAGE}
    (out/'owners.asm').write_text(run('objdump','-d','owners.elf'))
    validate(data,report,module)
    (out/'owners.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--module',type=Path,default=ROOT/'build/notice-treasure-runtime/module.json')
    parser.add_argument('--output',type=Path,default=ROOT/'build/noticeboard-treasure/owners')
    args=parser.parse_args()
    print(json.dumps(build(args.rom.read_bytes(),json.loads(args.module.read_text()),args.output.resolve()),indent=2))


if __name__=='__main__': main()
