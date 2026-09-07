#!/usr/bin/env python3
"""Execute English reply, complete-body, and distinct quest grading on N64."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from mail_grading import VROM, RELOC_VROM, RAM, relocate
from mail_grade_model import grade,legacy_grade
from runtime_layout import TEST_RETURN, TEST_STACK, GUARD_ADDRESS, GUARD_WORD
from runtime_module import verify_test_module

OUT,COUNT,BODY,MEMORY = (TEST_RETURN+offset for offset in (0x40,0xA0,0x100,0x600))
LOW_STACK = TEST_STACK-0x600
EDGE = b'EDGE'*4


def scenario(rom,module,overlay):
    verify_test_module(rom,module)
    files = by_vrom(rom)
    code, data, reloc = (files[vrom].extract(rom) for vrom in (CODE_VROM,VROM,RELOC_VROM))
    if sha256(data) != overlay['overlay_sha256'] or sha256(reloc) != overlay['relocation_sha256']:
        raise ValueError('Unexpected native scoring overlay')
    relocate(data,reloc,0x80208000)
    target = int(module['symbols']['af_mail_grade_native'],16)
    if struct.unpack_from('>2I',code,0x800A86C4-CODE_RAM) != (0x08000000|((target&0x0FFFFFFF)>>2),0):
        raise ValueError('English reply scoring hook is not installed')
    offset = int(overlay['symbols']['af_mail_prefixes']['address'],16)-RAM
    prefixes = data[offset:offset+1606]
    if sha256(prefixes) != overlay['reference']['sha256']:
        raise ValueError('Unexpected loaded English prefix tables')
    if BODY+1024+16 > MEMORY or MEMORY+176 >= LOW_STACK: raise ValueError('Mail grading fixtures overlap')
    actions = [{'wait':8},{'save_state':True},{'pause_game_thread':True}]
    def write(address,data): actions.append({'write':[f'{address:08X}',data.hex()]})
    def read(address,data): actions.append({'read':[f'{address:08X}',len(data)],'expect':data.hex()})
    def call(address,args,expected):
        actions.append({'call':{'address':f'{address:08X}','arguments':args,'expect_return':expected & 0xFFFFFFFF}})
    write(LOW_STACK,EDGE)
    write(TEST_STACK+0x30,EDGE)
    texts = [b'',b'x'*96,b'Hello.',b'Hello there! I hope you are having a lovely day. Please come over and visit soon!',
             b'The cat can see the dog. The dog can see the cat.',b' abcde',b'.'+b'x'*76,b'a'*95+b'.']
    offsets = struct.unpack_from('>27H',prefixes)
    for letter in range(26):
        index = offsets[letter]
        texts.append(bytes([65+letter])+prefixes[54+index*2:56+index*2]+b'!')
    for i,text in enumerate(texts):
        body = text.ljust(96,b' ')
        expected = grade(body,prefixes)
        write(BODY-16,EDGE+body+EDGE)
        call(0x800A86C4,[BODY],expected[-1])
        if i < 8:
            write(OUT-16,EDGE+b'?'*36+EDGE)
            call(int(module['symbols']['af_mail_grade_body'],16),[OUT,BODY,96],1)
            read(OUT-16,EDGE+struct.pack('>8iI',*expected)+EDGE)
            rank,length,words,rate = legacy_grade(body,prefixes)
            write(COUNT-16,EDGE+b'?'*4+EDGE)
            call(0x8009C900,[COUNT,BODY,0],rate)
            read(COUNT-16,EDGE+struct.pack('>I',words)+EDGE)
            call(0x800A8614,[COUNT,BODY],rank)
            read(COUNT-16,EDGE+struct.pack('>I',length)+EDGE)
            for present in (0,0x2001):
                quest_rank = (2 if length >= 49 else 1 if length >= 17 else 0)+(3 if rank else 0)+(6 if present else 0)
                call(0x800BBAB0,[BODY,present],quest_rank)
            memory = bytearray(b'!'*176)
            memory[0x29] = 0x99
            write(MEMORY,bytes(memory))
            call(0x800A86E8,[MEMORY,BODY],expected[-1])
            if expected[-1] < 2: memory[0x29] = (memory[0x29]&~0x40)|0x20|(expected[-1]<<6)
            read(MEMORY,bytes(memory[:0xAA]))
            read(MEMORY+0xAE,bytes(memory[0xAE:]))
        read(BODY-16,EDGE+body+EDGE)
        read(LOW_STACK,EDGE)
        read(TEST_STACK+0x30,EDGE)
    for text in (b'',b'x'*192,b'Hello! '+b'x'*230,b' aB.'*256):
        expected = grade(text,prefixes)
        write(BODY-16,EDGE+text+EDGE)
        write(OUT-16,EDGE+b'?'*36+EDGE)
        call(int(module['symbols']['af_mail_grade_body'],16),[OUT,BODY,len(text)],1)
        read(OUT-16,EDGE+struct.pack('>8iI',*expected)+EDGE)
        read(BODY-16,EDGE+text+EDGE)
    for args in ([0,BODY,1],[OUT,0,1],[OUT,BODY,1025],[OUT,BODY,0xFFFFFFFF]):
        write(OUT-16,EDGE+b'?'*36+EDGE)
        call(int(module['symbols']['af_mail_grade_body'],16),args,0)
        read(OUT-16,EDGE+b'?'*36+EDGE)
    call(0x800A86C4,[0],2)
    read(LOW_STACK,EDGE)
    read(TEST_STACK+0x30,EDGE)
    read(GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    actions += [{'load_state':True},{'resume':True},{'wait':2}]
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--module',type=Path,default=Path('build/runtime-module/module.json'))
    parser.add_argument('--overlay',type=Path,default=Path('build/mail-grading/overlay.json'))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    actions = scenario(rom,json.loads(args.module.read_text()),json.loads(args.overlay.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'calls':sum('call' in a for a in actions),
                      'assertions':sum('expect' in a for a in actions),'rom_sha256':sha256(rom)},indent=2))


if __name__ == '__main__': main()
