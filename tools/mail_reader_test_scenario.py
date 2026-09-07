#!/usr/bin/env python3
"""Open complete reference snapshots and verify every native page's glyph quads."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from mail_catalog import VROM as CATALOG_VROM, CONFIG_OFFSET, templates, verify_registered
from mail_format import format_letter
from mail_record import pack
from mail_runtime_test_scenario import reference_fixtures
from mail_view_patch import CALLS, SNAPSHOT_CALLS
from mail_viewer import RAM, VROM
from runtime_layout import TEST_RETURN, GUARD_ADDRESS, GUARD_WORD
from runtime_module import MODULE_VROM, verify_test_module


def scenario(rom,module,cases):
    verify_test_module(rom,module)
    files = by_vrom(rom)
    board = files[VROM].extract(rom)
    for address,_,symbol in CALLS+SNAPSHOT_CALLS:
        target = int(module['symbols'][symbol],16)
        if struct.unpack_from('>I',board,address-RAM)[0] != 0x0C000000|((target&0x0FFFFFFF)>>2):
            raise ValueError('Full letter test requires every installed snapshot-reader call')
    catalog = files[CATALOG_VROM].extract(rom)
    verify_registered(catalog)
    if files[MODULE_VROM].extract(rom)[CONFIG_OFFSET:CONFIG_OFFSET+4] != CATALOG_VROM.to_bytes(4,'big'):
        raise ValueError('Full letter test requires the configured immutable catalog')
    # Long classic body, long classic footer, and largest composite witness.
    picked = {}
    for label,record,_,limitation in cases:
        if record.initial_capital or limitation:
            continue
        record = replace(record,catalog=2)
        letter = format_letter(record,templates(catalog,record))
        for key,score in ((('body',record.kind),len(letter.body)),(('footer',record.kind),len(letter.footer))):
            if key not in picked or score > picked[key][0]:
                picked[key] = (score,(label,record,letter))
    selected = {value[1][0]:value[1] for value in picked.values()}
    if not 2 <= len(selected) <= 4:
        raise ValueError('Unexpected full-letter witness selection')
    actions = [{'wait':2},{'save_state':True}]
    source = TEST_RETURN+0x200
    probes = [(label,record,letter,None,None) for label,record,letter in selected.values()]
    # Use the original name/identity setter, not a guessed saved name. The
    # recipient's complete display name comes from the installed English bank.
    names = files[0x02C00000].extract(rom)
    if len(names) != 2272 or names[:32] != struct.pack('>8I',0x41464E4E,1,8,280,216,64,0,0):
        raise ValueError('NPC letter windows require the complete display-name resource')
    name_ids = [index for index in range(216) if len(names[32+index*8:40+index*8].rstrip(b' ')) == 8]
    if len(name_ids) < 2: raise ValueError('Missing eight-byte villager-name witnesses')
    for npc_index,(label,record,letter) in zip((name_ids[0],name_ids[-1]),(picked[('body',0)][1],picked[('body',1)][1])):
        probes.append(('npc:'+label,record,letter,None,npc_index))
    first = next(iter(selected.values()))
    probes += [('bad_checksum',first[1],None,'checksum',None),
               ('unknown_catalog',replace(first[1],catalog=3),None,'catalog',None)]
    for index,(label,record,letter,error,npc_index) in enumerate(probes):
        mail = bytearray(164)
        mail[:6] = b'READER'
        mail[0x12:0x18] = b'WRITER'
        mail[0x26:0x2A] = bytes([0,128,4,0])
        mail[0x2A:] = pack(record)
        if error == 'checksum': mail[0x32] ^= 1
        name = b'READER' if npc_index is None else names[32+npc_index*8:40+npc_index*8].rstrip(b' ')
        header = b'' if error else letter.header[:letter.header_split]+name+letter.header[letter.header_split:]
        body = b'Unable to read this letter.' if error else letter.body
        footer = b'' if error else letter.footer
        actions += [{'pause_game_thread':True},
                    {'snapshot_submenu':True,'expect_submenu':{'program':0,'move_index':0}},
                    {'write':[f'{source:08X}',mail.hex()]}]
        if npc_index is not None:
            identity = struct.pack('>HH6sBB',0xE000+npc_index,0xEAAA,b'OLDTWN',3,0)
            native = files[CODE_VROM].extract(rom)
            actions += [{'read':['8009C70C',0x74],'expect':native[0x8009C70C-CODE_RAM:0x8009C780-CODE_RAM].hex()},
                        {'write':[f'{TEST_RETURN+0x100:08X}',identity.hex()]},
                        {'call':{'address':'8009C70C','arguments':[source,TEST_RETURN+0x100]}}]
        actions += [
                    {'open_test_mail':f'{source:08X}','snapshot_probe':True,'mail_open_mode':2 if index == 3 else 1},
                    {'resume':True},{'wait':8},
                    {'snapshot_submenu':True,'expect_submenu':{'program':12,'move_index':3,'board_state':2,
                       'board_mode':1,'source':f'{source:08X}','body_length':0,'footer_length':0,'header_length':0}},
                    {'read_all_mail_pages':{'reader':module['symbols']['af_mail_reader'],
                       'hook':module['symbols']['af_mail_header_hook'],'status':2 if error else 1,
                       'header':header.hex(),'body':body.hex(),'footer':footer.hex(),'reference':label}},
                    {'key':('b','a','Return')[index%3],'duration':0.12},{'wait':5},
                    {'snapshot_submenu':True,'expect_submenu':{'program':0,'move_index':0}},
                    {'assert_test_mail_unchanged':True}]
    actions += [{'read':[f'{GUARD_ADDRESS:08X}',16],'expect':f'{GUARD_WORD:08X}'*4},
                {'load_state':True},{'resume':True},{'wait':2},
                {'read':[f'{source:08X}',4],'expect':'00000000'}]
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--module',type=Path,default=Path('build/runtime-module/module.json'))
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--gc-data',type=Path,default=Path('build/gamecube/files/forest_1st.arc.unpacked/data'))
    parser.add_argument('--decomp',type=Path,default=Path('local/ac-decomp'))
    parser.add_argument('--rel',type=Path,default=Path('build/gamecube/files/foresta.rel.szs.decoded'))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    cases = reference_fixtures(args.native_rom.read_bytes(),args.gc_data,args.decomp,args.rel)
    rom = args.rom.read_bytes()
    actions = scenario(rom,json.loads(args.module.read_text()),cases)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'rom_sha256':sha256(rom),
                      'letters':sum('read_all_mail_pages' in a for a in actions)}))


if __name__ == '__main__':
    main()
