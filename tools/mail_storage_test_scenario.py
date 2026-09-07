#!/usr/bin/env python3
"""Create controlled mail metadata/storage tests for a matching town checkpoint."""

import argparse
from dataclasses import replace
import json
from pathlib import Path

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from mail_catalog import templates, verify_registered
from mail_format import format_letter
from mail_record import pack
from mail_runtime_test_scenario import reference_fixtures
from mail_storage import FUNCTIONS, evidence
from runtime_module import verify_test_module


def scenario(rom,module,fixtures):
    verify_test_module(rom,module)
    evidence(rom)
    code = by_vrom(rom)[CODE_VROM].extract(rom)
    catalog = by_vrom(rom)[0x03000000].extract(rom)
    verify_registered(catalog)
    letters = {}
    for _,record,_,limitation in fixtures:
        if limitation or record.kind in letters: continue
        record = replace(record,catalog=2)
        format_letter(record,templates(catalog,record))
        mail = bytearray(164)
        mail[36:42] = bytes.fromhex('200101800439')
        mail[42:] = pack(record)
        letters[record.kind] = mail.hex()
    if set(letters) != {0,1}: raise ValueError('Storage fixtures require both record kinds')
    request = {'letters':[letters[k] for k in (0,1)],
               'guards':{f'{start:08X}':code[start-CODE_RAM:end-CODE_RAM].hex()
                         for start,end,_ in FUNCTIONS.values()}}
    return [{'wait':2},{'save_state':True},{'pause_game_thread':True},
            {'test_mail_storage':request},{'load_state':True},{'resume':True},{'wait':2}]


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
    rom = args.rom.read_bytes()
    fixtures = reference_fixtures(args.native_rom.read_bytes(),args.gc_data,args.decomp,args.rel)
    actions = scenario(rom,json.loads(args.module.read_text()),fixtures)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'letters':2,'rom_sha256':sha256(rom)}))


if __name__ == '__main__': main()
