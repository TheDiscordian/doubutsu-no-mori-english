"""Generate an isolated checkpoint probe of the compiled cursor correction.

The matching older ROM restores normally. Only the loaded controller code is
replaced with independently compiled/relocated instructions, after exact guards.
This is native correction evidence, not a claim that the new ROM was booted.
"""
import argparse
import json
from pathlib import Path
import struct

from aflib import sha256
from hboard_overlay import Image
from keyboard_grid_overlay import RAM,validate
from npc_mail_show import relocate_verified_data

ROOT=Path(__file__).resolve().parents[1]


def scenario():
    native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
    loaded=[]
    for name in ('keyboard-grid-overlay','keyboard-grid-cursor-aligned'):
        directory=ROOT/'build'/name
        data=(directory/'overlay.bin').read_bytes();reloc=(directory/'relocation.bin').read_bytes()
        validate(native,data,reloc,json.loads((directory/'overlay.json').read_text()))
        loaded.append(relocate_verified_data(Image(RAM,len(data),struct.unpack_from('>5I',reloc)),
                                             data,reloc,0x803AF450))
    old,new=loaded;start,end=0x5A80,0x5FD8
    if old[:start]!=new[:start] or old[end:]!=new[end:]:
        raise ValueError('Checkpoint correction would change live editor pointers or state')
    if sha256((ROOT/'build/combined-grid-native-02/test.bs1').read_bytes())!='7416357e9a824f38b418c79eae54afde84167b9ebf0715ca38eb5cf892c55a02':
        raise ValueError('Unexpected isolated empty-name checkpoint')
    address=f'{0x803AF450+start:08X}'
    actions=json.loads((ROOT/'tests/keyboard-grid-checkpoint-scenario.json').read_text())
    return actions[:1]+[
        {'read':[address,end-start],'expect':old[start:end].hex()},
        {'write':[address,new[start:end].hex()]},
        {'read':[address,end-start],'expect':new[start:end].hex()},
    ]+actions[1:]+[{'load_state':True}]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    with args.output.open('x') as target:json.dump(scenario(),target,indent=2);target.write('\n')
    print(args.output)


if __name__=='__main__':main()
