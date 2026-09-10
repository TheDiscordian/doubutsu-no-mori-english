#!/usr/bin/env python3
"""Focused silent native proof of the startup-installed borrowed-phrase call."""
import argparse
import json
from pathlib import Path
import struct
from aflib import verified_rom
from text_extension import verify_installation


def scenario(native, built, report):
    verify_installation(built, verified_rom(native), report)
    if not report['text_extension'].get('borrowed'): raise ValueError('Borrowed phrase variant required')
    actor, animal, buffer = 0x8019B600, 0x8019B800, 0x8019B010
    guard = b'CATCH-GUARD-0123'
    assert len(guard) == 16
    actor_data = bytearray(0x178);actor_data[2]=3
    struct.pack_into('>I',actor_data,0x174,animal)
    actions = [{'wait':8}, {'read':['80000318',4], 'expect':'00400000'},
               {'save_state':True}, {'pause_game_thread':True}]
    def write(at,data): actions.append({'write':[f'{at:08X}',data.hex()]})
    def check(at,data): actions.append({'read':[f'{at:08X}',len(data)],'expect':data.hex()})
    def call(at,args,result): actions.append({'call':{'address':f'{at:08X}','arguments':args,'expect_return':result}})
    write(actor,actor_data)
    actions.append({'read':['801953C4',4]})
    check(0x801953C8,bytes.fromhex('02c02025'))
    def phrase(npc,saved,expected,choice=False,actor_pointer=actor):
        data = bytearray(0x528);struct.pack_into('>H',data,0,npc);data[0x4E5:0x4E9]=saved
        write(animal,data)
        width = 20 if choice else 1024
        payload = b'>\x7f\x1c!'
        before = payload.ljust(width,b' ')
        text = b'>'+expected+b'!'
        if choice: after = text.ljust(width,b' ')
        else:
            # The native insertion preserves bytes outside the active length.
            after = bytearray(before);after[:len(text)] = text
        write(buffer-16,guard+before+guard)
        if choice: call(0x80065CF8,[buffer,20,actor_pointer],len(expected)+2)
        else: call(0x801952F4,[actor_pointer,buffer,0x1,len(payload)],len(expected)+2)
        check(buffer-16,guard+after+guard)
        check(actor,actor_data);check(animal,data)
    for npc,expected in ((0xE014,b'zzzzzz'),(0xE0C5,b'bingo'),(0xE000,b'zzzzzz')):
        phrase(npc,bytes.fromhex('d0902020'),expected)
        phrase(npc,bytes.fromhex('d0902020'),expected,choice=True)
    phrase(0xE000,b'Yup!',b'Yup!')
    phrase(0xE000,b'Yup!',b'Yup!',choice=True)
    write(0x80194920,bytes(4))
    phrase(0xE000,bytes.fromhex('d0902020'),bytes.fromhex('d090'),choice=True)
    write(0x80194920,struct.pack('>I',0x02E00000))
    phrase(0xE000,bytes.fromhex('d0902020'),b'',actor_pointer=0)
    check(0x8019C8D0,bytes.fromhex('AF32C0DE'*4))
    actions += [{'load_state':True},{'resume':True},{'wait':2}]
    check(actor,bytes(0x178));check(animal,bytes(0x528))
    return actions


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,default=Path('build/borrowed-catchphrases-pilot'))
    parser.add_argument('--output',type=Path,default=Path('build/borrowed-catchphrases-scenario.json'))
    args=parser.parse_args()
    actions=scenario(Path('local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                     (args.build/'animal-forest-halfwidth.z64').read_bytes(),json.loads((args.build/'build.json').read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'calls':sum('call' in a for a in actions),
                      'assertions':sum('expect' in a for a in actions)}))


if __name__ == '__main__':main()
