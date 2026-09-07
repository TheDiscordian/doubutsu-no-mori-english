#!/usr/bin/env python3
"""Build complete-record native send tests for an identical-ROM town checkpoint."""

import argparse
from dataclasses import replace
import json
from pathlib import Path

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from mail_catalog import templates, verify_registered
from mail_format import format_letter
from mail_grading import RAM as GRADE_RAM, VROM as GRADE_VROM
from mail_grade_model import grade,legacy_grade
from mail_npc import ENTRIES, POST_CALL
from mail_record import pack
from mail_runtime_test_scenario import reference_fixtures
from runtime_module import verify_test_module


def scenario(rom,module,overlay,fixtures):
    verify_test_module(rom,module)
    files = by_vrom(rom)
    code = files[CODE_VROM].extract(rom)
    for address,_,_,_,symbol,_ in ENTRIES:
        target = int(module['symbols'][symbol],16)
        if code[address-CODE_RAM:address-CODE_RAM+8] != (0x08000000|((target&0x0FFFFFFF)>>2)).to_bytes(4,'big')+b'\0'*4:
            raise ValueError('NPC send scenario requires both installed entry hooks')
    post_target = int(module['symbols']['af_mail_post_send'],16)
    if code[POST_CALL-CODE_RAM:POST_CALL-CODE_RAM+4] != (0x0C000000|((post_target&0x0FFFFFFF)>>2)).to_bytes(4,'big'):
        raise ValueError('NPC send scenario requires the post-office failure guard')
    grading = files[GRADE_VROM].extract(rom)
    if sha256(grading) != overlay['overlay_sha256']: raise ValueError('Wrong scoring overlay')
    at = int(overlay['symbols']['af_mail_prefixes']['address'],16)-GRADE_RAM
    prefixes = grading[at:at+1606]
    if sha256(prefixes) != overlay['reference']['sha256']: raise ValueError('Wrong scoring prefixes')
    catalog = files[0x03000000].extract(rom)
    verify_registered(catalog)
    selected = {}
    for label,record,_,limitation in fixtures:
        if limitation or record.initial_capital: continue
        record = replace(record,catalog=2)
        body = format_letter(record,templates(catalog,record)).body
        scores = (grade(body,prefixes)[-1],*legacy_grade(body,prefixes)[:2])
        key = (record.kind,scores[0])
        if key not in selected or len(body)>selected[key][0]:
            selected[key] = (len(body),label,record,scores)
    cases = []
    if ({key[0] for key in selected} != {0,1} or {key[1] for key in selected} != {0,1,2}
            or any(row[0] <= 96 for row in selected.values())):
        raise ValueError('NPC send witnesses must cover both record kinds, all reply grades, and long bodies')
    for _,label,record,scores in selected.values():
        mail = bytearray(164)
        mail[0x26:0x2A] = bytes((1,128,4,0))
        mail[0x2A:] = pack(record)
        for visitor,quest,present in ((False,False,0),(False,True,0),(False,True,0x2001),(True,False,0)):
            mail[0x24:0x26] = present.to_bytes(2,'big')
            cases.append({'label':f'{label}:visitor={int(visitor)}:quest={int(quest)}:gift={present:04X}',
                          'mail':mail.hex(),'scores':scores,'visitor':visitor,'quest':quest})
    # Ordinary letters exercise both original-entry trampolines with no cached score.
    for body in (b'x'*96,b'Hello there! I hope you have a great day. Please write back soon!'):
        mail = bytearray(164)
        mail[0x26:0x2A] = bytes((1,0,4,0))
        mail[0x2A:] = b' '*122
        mail[0x34:0x94] = body.ljust(96,b' ')
        body = bytes(mail[0x34:0x94])
        scores = (grade(body,prefixes)[-1],*legacy_grade(body,prefixes)[:2])
        cases.append({'label':f'ordinary:{scores[0]}','mail':mail.hex(),'scores':scores,'quest':True})
    for offset in (0x26,0x2A,0x2D,163):
        mail = bytearray.fromhex(cases[0]['mail'])
        mail[offset] = 255 if offset == 0x26 else mail[offset]^1
        cases.append({'label':f'reject:{offset:02X}','mail':mail.hex(),'reject':True})
    cases += [{**case,'post_office':True,'label':'post-office:'+case['label']}
              for case in (cases[0],cases[4],*cases[-4:])]
    ranges = [(start,end) for start,end,*_ in ENTRIES]+[
        (0x8007D2B8,0x8007D318),(0x8007D6E0,0x8007D734),(0x8009C70C,0x8009C80C),
        (0x800B795C,0x800B7998),(0x800A86E8,0x800A8868),(0x800BBB30,0x800BBBEC),
        (0x800A6C84,0x800A6CE4),(0x80117AE8,0x80117AEC)]
    ranges += [(0x800B690C,0x800B6AC8),(0x8009C384,0x8009C3EC)]
    request = {'context':module['symbols']['af_mail_npc_context'],'cases':cases,
               'guards':{f'{start:08X}':code[start-CODE_RAM:end-CODE_RAM].hex() for start,end in ranges}}
    return [{'wait':2},{'save_state':True},{'pause_game_thread':True},{'test_npc_mail_sends':request},
            {'load_state':True},{'resume':True},{'wait':2}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--module',type=Path,default=Path('build/runtime-module/module.json'))
    parser.add_argument('--overlay',type=Path,default=Path('build/mail-grading/overlay.json'))
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--gc-data',type=Path,default=Path('build/gamecube/files/forest_1st.arc.unpacked/data'))
    parser.add_argument('--decomp',type=Path,default=Path('local/ac-decomp'))
    parser.add_argument('--rel',type=Path,default=Path('build/gamecube/files/foresta.rel.szs.decoded'))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    fixtures = reference_fixtures(args.native_rom.read_bytes(),args.gc_data,args.decomp,args.rel)
    actions = scenario(rom,json.loads(args.module.read_text()),json.loads(args.overlay.read_text()),fixtures)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'cases':len(actions[3]['test_npc_mail_sends']['cases']),
                      'rom_sha256':sha256(rom)}))


if __name__ == '__main__': main()
