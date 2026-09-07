#!/usr/bin/env python3
"""Exercise original NPC stored-letter show callers through the real window."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from display_names import HEADER as NAME_HEADER, VROM as NAME_VROM
from mail_catalog import templates, verify_registered
from mail_format import format_letter
from mail_record import pack
from mail_runtime_test_scenario import reference_fixtures
from mail_reader_test_scenario import scenario as reader_scenario
from npc_mail_show import OVERLAYS, source, relocated


def scenario(rom,native,module,fixtures):
    native = verified_rom(native)
    # Retain the complete reader installation/configuration checks.
    reader_scenario(rom,module,fixtures)
    files = by_vrom(rom)
    catalog = files[0x03000000].extract(rom)
    verify_registered(catalog)
    names = files[NAME_VROM].extract(rom)
    if len(names) != 2272 or names[:32] != NAME_HEADER:
        raise ValueError('NPC show requires complete English display names')
    name_index = next(i for i in range(216) if len(names[32+i*8:40+i*8].rstrip(b' ')) == 8)
    name = names[32+name_index*8:40+name_index*8]
    picked = {}
    for label,record,_,limitation in fixtures:
        if limitation or record.initial_capital: continue
        record = replace(record,catalog=2)
        letter = format_letter(record,templates(catalog,record))
        if record.kind not in picked or len(letter.body) > len(picked[record.kind][2].body):
            picked[record.kind] = label,record,letter
    if set(picked) != {0,1}: raise ValueError('NPC show requires both snapshot kinds')
    cases = []
    for label,record,letter in picked.values():
        mail = bytearray(164)
        mail[36:42] = bytes.fromhex('200101800439')
        mail[42:] = pack(record)
        header = letter.header[:letter.header_split]+name+letter.header[letter.header_split:]
        cases.append({'label':label,'mail':mail.hex(),'snapshot':True,'header':header.hex(),
                      'body':letter.body.hex(),'footer':letter.footer.hex()})
    body,footer = b'A stored ordinary letter.\xcdEvery line stays intact.',b'WRITER'
    mail = bytearray(164)
    mail[36:42] = bytes.fromhex('200101030400')
    mail[42:52] = b'To '.ljust(10,b' ')
    mail[52:148],mail[148:] = body.ljust(96,b' '),footer.ljust(16,b' ')
    cases.append({'label':'ordinary','mail':mail.hex(),'snapshot':False,
                  'body':body.hex(),'footer':footer.hex()})
    overlays = {}
    for key,spec in OVERLAYS.items():
        data,reloc = source(rom,key)
        for base in (0x801A0000,0x802F8010): relocated(spec,data,reloc,base)
        overlays[key] = {'data':data.hex(),'relocation':reloc.hex()}
    loader = native[0x800262D0-0x80025C60+0x1060:0x800263C0-0x80025C60+0x1060]
    if sha256(loader) != '2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Unexpected native overlay loader')
    code = files[CODE_VROM].extract(rom)
    guards = {f'{start:08X}':code[start-CODE_RAM:end-CODE_RAM].hex() for start,end in (
        (0x8009C384,0x8009C414),(0x8009C70C,0x8009C80C),
        (0x800A82C8,0x800A83F0),(0x800C4DB0,0x800C4E00))}
    request = {'overlays':overlays,'cases':cases,'loader':loader.hex(),'guards':guards,
               'identity':struct.pack('>HH6sBB',0xE000+name_index,0xEAAA,b'OLDTWN',3,0).hex(),
               'reader':module['symbols']['af_mail_reader'],
               'hooks':{key:module['symbols'][key] for key in ('af_mail_header_hook','af_mail_body_hook','af_mail_footer_hook')}}
    return [{'wait':2},{'save_state':True},{'pause_game_thread':True},
            {'test_npc_mail_show':request},{'load_state':True},{'resume':True},{'wait':2}]


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
    native,rom = args.native_rom.read_bytes(),args.rom.read_bytes()
    fixtures = reference_fixtures(native,args.gc_data,args.decomp,args.rel)
    actions = scenario(rom,native,json.loads(args.module.read_text()),fixtures)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'callers':3,'windows':9,'rom_sha256':sha256(rom)}))


if __name__ == '__main__': main()
