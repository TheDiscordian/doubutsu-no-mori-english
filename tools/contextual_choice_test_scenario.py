#!/usr/bin/env python3
"""Check contextual labels, selected text, and original native branch handlers."""

import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, verified_rom
from contextual_choices import canonical_candidate, load_contextual_choices, unique_menu, validate_labels
from english_runtime import ChoiceLayout
from font import make_halfwidth
from message_alias_test_scenario import scenario as message_scenario
from reference_matches import load_matches
from runtime_module import MODULE_VROM, module_command_info
from textbanks import Bank, banks
from textcodec import encode, tokenize

CONNECTED = '1378 1379 186D 187A 1872 1CE2 26D0 26D3 23B5 23B6 0B64 0B65 1C94 1C97 2472 2476'.split()
DRAFT_IDS = ['message:'+n for n in ('186E','187B','1880','1CE3')]
SHAPE_ID = 'message:2C8F'


def native_choice_width(payload, advances):
    # mFont_GetStringWidth rounds its sum up to an even pixel count.
    # Retail 8009031C..80090328 tests bit zero and adds one when set.
    return (sum(advances.get(c,12) for c in payload)+1)&~1


def scenario(rom, source_rom, edits):
    source_rom = verified_rom(source_rom)
    info = module_command_info(source_rom)
    sources = {b.name: b.entries() for b in banks(source_rom)}
    matches = load_matches(Path(__file__).resolve().parents[1]/'translations/reference_matches.json')
    approvals = load_contextual_choices(matches)
    files = by_vrom(rom)
    messages = Bank('message',0x02000000,0x00CF9000,
        files[0x02000000].extract(rom),files[0x00CF9000].extract(rom)).entries()
    labels = Bank('select',0x02400000,0x00D06000,
        files[0x02400000].extract(rom),files[0x00D06000].extract(rom)).entries()
    layout = ChoiceLayout(*struct.unpack_from('>4I',files[MODULE_VROM].extract(rom),40))
    if layout.capacity != 20 or len(labels) != 460:
        raise ValueError('Contextual-choice scenario requires the complete twenty-byte pilot')
    by_id = {r['id']:r for r in edits}
    ids = sorted(set(approvals)|set(DRAFT_IDS)|{'message:'+n for n in CONNECTED}|{SHAPE_ID})
    actions = message_scenario(rom,edits,info,message_ids=ids)
    ending = actions[-5:];actions=actions[:-5]
    _, font = make_halfwidth(source_rom)
    advances = {int(k,16):v for k,v in font['advance_by_glyph'].items()}
    # The original branch handlers read the singleton's selected index at
    # 80142640. Native determination writes Choice+80, hence this same object.
    choice, window, data, index, staging, insertion = (
        0x801425C0,0x8019B000,0x8019B400,0x8019B380,0x8019B800,0x8019BB00)
    def write(address,value):actions.append({'write':[f'{address:08X}',value.hex()]})
    def read(address,value):actions.append({'read':[f'{address:08X}',len(value)],'expect':value.hex()})
    def call(address,args,result=None):
        entry={'address':f'{address:08X}','arguments':args}
        if result is not None:entry['expect_return']=result
        actions.append({'call':entry})
    cases=[]
    for id in [*sorted(approvals),SHAPE_ID]:
        number=int(id[8:],16);entry=messages[number]
        if id in approvals:
            canonical_candidate(id,sources['message'][number],entry,approvals,info)
            validate_labels(approvals[id],by_id,sources['select'],info)
        menu=unique_menu(entry,info)
        choice_ids=[int.from_bytes(menu.data[i:i+2],'big') for i in range(2,len(menu.data),2)]
        if id==SHAPE_ID and choice_ids != [0xCD,0xCE,0xCF,0xD0]:
            raise ValueError('Shape-game choices changed')
        branches=[t for t in tokenize(entry,info) if t.kind=='cmd' and 0x0f<=t.data[1]<=0x12]
        if id in approvals and sorted(t.data[1] for t in branches) != list(range(0x0f,0x0f+len(choice_ids))):
            raise ValueError('Expected exactly one native branch for every reviewed answer')
        write(window,bytes(0x330));write(window+12,struct.pack('>I',data))
        call(0x8009E558,[data,number,0],1)
        read(data,struct.pack('>4I',1,number,len(entry),0)+entry)
        write(choice,bytes(0x90));write(layout.rows,b'G'*160)
        payloads=[]
        for position,label_id in enumerate(choice_ids):
            label=labels[label_id]
            if label != encode(by_id[f'select:{label_id:04X}']['translation'],info):
                raise ValueError('Built label differs from its complete candidate')
            write(staging+position*32,b'G'*32)
            call(0x80065D90,[choice,staging+position*32,label_id,0])
            read(staging+position*32,label.ljust(20,b' ')+b'G'*12)
            payloads.append(label.rstrip(b' '))
        arguments=[choice]
        for position in range(4):
            arguments.extend((staging+position*32,20) if position<len(choice_ids) else (0,0))
        call(0x80065278,arguments)
        read(choice+0x5C,struct.pack('>4I',*[len(p) for p in payloads],*[0]*(4-len(payloads))))
        read(choice+0x7C,struct.pack('>I',len(payloads)))
        expected_rows=b''.join(p+b'G'*(32-len(p)) for p in payloads)+b'G'*(32*(5-len(payloads)))
        read(layout.rows,expected_rows)
        call(0x80065348,[choice],max(native_choice_width(p,advances) for p in payloads))
        for selection,payload in enumerate(payloads):
            write(choice+0x84,struct.pack('>I',selection));write(layout.selected,b'G'*32)
            call(0x80066130,[choice])
            read(choice+0x78,struct.pack('>3I',len(payload),len(payloads),selection))
            read(layout.selected,payload+b'G'*(32-len(payload)))
            write(insertion,b'X\x7f\x2eY'+b' '*60)
            # Selected length belongs to this same global Choice's parent,
            # not to the separate scratch window used for branch dispatch.
            call(0x8009F3A8,[choice-0x1B0,insertion,1,4],len(payload)+2)
            read(insertion,b'X'+payload+b'Y')
            target=None
            if id in approvals:
                write(window+0x2C4,b'\xff'*4)
                for token in branches:
                    write(index,struct.pack('>I',token.offset))
                    call(0x800A21C0,[window,index],0)
                    read(index,struct.pack('>I',token.offset+len(token.data)))
                    if token.data[1]==0x0f+selection:target=int.from_bytes(token.data[2:],'big')
                read(window+0x2C4,struct.pack('>I',target))
            cases.append({'id':id,'selection':selection,'label_id':choice_ids[selection],'target':target})
    return actions+ending,ids,cases


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--source-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--translations',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();rom=args.rom.read_bytes()
    actions,ids,cases=scenario(rom,args.source_rom.read_bytes(),json.loads(args.translations.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'rom_sha256':sha256(rom),'actions':len(actions),'messages':ids,'cases':cases,'output':str(args.output)}))


if __name__=='__main__':main()
