#!/usr/bin/env python3
"""Build native save/export or fresh-start restore tests for English mail."""

import argparse
from dataclasses import replace
import json
from pathlib import Path

from aflib import by_vrom, sha256
from flash_mail import evidence, locations
from mail_catalog import templates, verify_registered
from mail_record import pack
from mail_runtime_test_scenario import reference_fixtures, output_bytes
from runtime_module import verify_test_module


def scenario(rom,module,fixtures,exported=None):
    verify_test_module(rom,module)
    request = evidence(rom)
    catalog = by_vrom(rom)[0x03000000].extract(rom)
    verify_registered(catalog)
    cases = {}
    for label,record,_,limitation in fixtures:
        if limitation or record.kind in cases: continue
        record = replace(record,catalog=2)
        cases[record.kind] = {'label':label,'wire':pack(record).hex(),
                             'output':output_bytes(record,templates(catalog,record)).hex()}
    if set(cases) != {0,1}: raise ValueError('FlashRAM fixtures require both snapshot kinds')
    request.update(rom_sha256=sha256(rom),cases=[cases[i] for i in (0,1)],
                   locations=locations(),restore=module['symbols']['af_mail_restore'])
    action = 'test_native_flash_mail_save'
    if exported is not None:
        if exported['rom_sha256'] != sha256(rom) or exported['locations'] != locations():
            raise ValueError('FlashRAM export must match the tested ROM and exact storage layout')
        request['export'] = exported
        action = 'test_native_flash_mail_read'
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},
            {action:request},{'load_state':True},{'resume':True},{'wait':2}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--module',type=Path,default=Path('build/runtime-module/module.json'))
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--gc-data',type=Path,default=Path('build/gamecube/files/forest_1st.arc.unpacked/data'))
    parser.add_argument('--decomp',type=Path,default=Path('local/ac-decomp'))
    parser.add_argument('--rel',type=Path,default=Path('build/gamecube/files/foresta.rel.szs.decoded'))
    parser.add_argument('--export',type=Path,help='Generate a read-only cold-start test from this verified export manifest')
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    fixtures = reference_fixtures(args.native_rom.read_bytes(),args.gc_data,args.decomp,args.rel)
    exported = json.loads(args.export.read_text()) if args.export else None
    actions = scenario(rom,json.loads(args.module.read_text()),fixtures,exported)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'mode':'read' if exported else 'save','actions':len(actions),
                      'mail_slots':len(locations()),'rom_sha256':sha256(rom)}))


if __name__ == '__main__': main()
